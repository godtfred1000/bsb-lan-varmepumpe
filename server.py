"""Pi web server and opt-in service supervisor. Configuration is local and atomic."""
import copy
import hmac
import json
import mimetypes
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit, parse_qs
from urllib.request import Request, urlopen

from config import DEFAULT, atomic, public, validate, host
from runtime import render
from collector import collect, query
from transport import request
from network import local_hosts

HERE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('BSB_DATA','./data'))
LOCK=threading.RLock()

class Application:
    def __init__(self, data=DATA, workers=True):
        self.data=Path(data); self.data.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.data=self.data.resolve()
        key=self.data/'setup-key'
        if not key.exists():
            fd=os.open(key,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(32)+'\n')
        self.key=key.read_text().strip()
        webhook=self.data/'shelly-key'
        if not webhook.exists():
            fd=os.open(webhook,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(32)+'\n')
        self.shelly_key=webhook.read_text().strip(); self.last_shelly=0
        self.config=None; self.children={}; self.retry={}; self.stopping=False; self.restart=False
        config=self.data/'config.json'
        if config.exists():
            self.config=validate(json.loads(config.read_text()))
            target=self.data/'target.json'
            previous=json.loads(target.read_text()) if target.exists() else None
            current=[self.config['bsb_host'],self.config['bsb_port']]
            if previous is not None and previous!=current:
                # Only change private controller state after the old process tree has stopped.
                for relative in ('pause-auto/private/state.json','summer-profile/private/config.json'):
                    file=self.data/'controllers'/relative
                    if file.exists():file.replace(file.with_name('previous-target-'+str(time.time_ns())+'.json'))
            self.web,self.runtime=render(self.config,self.data)
            atomic(target,current)
        else:
            self.web=self.data/'web';self.runtime=self.data/'runtime'
        self.workers=workers; self.last_collect=0; self.last_tick=0
        self.health={}

    def save(self, value):
        previous=self.config
        new=validate(value,previous)
        # Existing detached summer/holiday transactions must finish on the old target.
        operation=self.data/'controllers/summer-profile/private/operation.json'
        if operation.exists() and json.loads(operation.read_text()).get('status') in ('queued','running'):
            raise RuntimeError('BUSY')
        if any(self.children.get(name) and self.children[name].poll() is None for name in ('summer-profile','pause-auto')):
            raise RuntimeError('BUSY')
        if previous:
            backups=self.data/'backups';backups.mkdir(exist_ok=True,mode=0o700)
            atomic(backups/('config-'+time.strftime('%Y%m%dT%H%M%S')+'-'+secrets.token_hex(3)+'.json'),previous)
        atomic(self.data/'config.json',new)
        # Existing process tree keeps its immutable configuration until restart.
        self.restart=True

    def command(self, relative):
        return [sys.executable,str(self.runtime/relative)]

    def supervise(self):
        while not self.stopping and not self.restart:
            with LOCK:
                if self.restart:break
            # Slow IO must not monopolize the configuration lock; changes restart all tasks first.
            if self.config and self.workers:
                if self.config['flags']['heatpump'] and time.monotonic()-self.last_collect >= 30:
                    self.last_collect=time.monotonic()
                    with LOCK:
                        if self.restart:break
                        try: collect(self.config,self.data);self.health['logger']={'ok':True,'updated':int(time.time())}
                        except Exception:self.health['logger']={'ok':False,'updated':int(time.time())}
                if time.monotonic()-self.last_tick >= 60:
                    self.last_tick=time.monotonic()
                    with LOCK:
                        if self.restart:break
                        for name,enabled in [('summer-profile',self.config['flags']['schedule_controls']),('pause-auto',self.config['flags']['auto_pause'])]:
                            old=self.children.get(name)
                            if enabled and (old is None or old.poll() is not None):
                                self.children[name]=self.launch(self.command(name+'/service.py' if name=='summer-profile' else name+'/controller.py')+['--tick'],name)
                if self.config['flags']['shelly'] and time.monotonic()-self.last_shelly>=120:
                    self.last_shelly=time.monotonic()
                    with LOCK:
                        if self.restart:break
                        try:forward_shelly(self.config,json.loads((self.data/'shelly/reading.json').read_text()))
                        except Exception:pass
            time.sleep(.25)

    def launch(self,command,name):
        env=os.environ.copy();env.update(TZ=self.config['timezone'],KV8_BOOT_ID=boot_id(),BSB_DATA=str(self.data.resolve()),PYTHONPATH=str(HERE))
        log=self.data/'service-logs';log.mkdir(exist_ok=True,mode=0o700)
        with (log/(name+'.log')).open('ab') as stream:
            return subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,start_new_session=True)

    def stop(self):
        self.stopping=True
        for process in self.children.values():
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
        deadline=time.monotonic()+12
        for process in self.children.values():
            try:process.wait(timeout=max(.1,deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass

def boot_id():
    try:return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except OSError:return 'pi-'+str(os.getpid())

def forward_shelly(config, reading):
    if not config['flags']['shelly'] or not config['flags']['controls']:raise ValueError('DISABLED')
    if reading.get('target')!=config['bsb_host'] or reading.get('port')!=config['bsb_port']:raise ValueError('TARGET')
    if not 0 <= time.time()-reading['at'] <= 7800:raise ValueError('STALE')
    temperature=reading['temperature']
    if type(temperature) not in (int,float) or not 0<=temperature<=40:raise ValueError('TEMPERATURE')
    request('I10000='+str(temperature),config)

def last_complete_sample(path):
    with path.open('rb') as f:
        f.seek(0,2);size=f.tell();f.seek(max(0,size-65536));data=f.read()
    for line in reversed(data.split(b'\n')[:-1]):
        if line.startswith(b'Tidspunkt: ') and b' | Kompressor: ' in line:return line+b'\n'
    raise ValueError('NO_COMPLETE_SAMPLE')

def handler(app):
    class Handler(BaseHTTPRequestHandler):
        server_version='BSB-Heatpump'
        def setup(self):
            super().setup();self.connection.settimeout(20)
        def log_message(self,*args): pass  # Never log credentials or webhook query strings.
        def reply(self,status,body,kind='application/json; charset=utf-8',headers=None):
            if not isinstance(body,bytes): body=json.dumps(body,ensure_ascii=True).encode()
            self.send_response(status)
            for k,v in {'Content-Type':kind,'Content-Length':str(len(body)),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',**(headers or {})}.items():self.send_header(k,v)
            self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def origin(self):return self.headers.get('Origin')=='http://'+self.headers.get('Host','')
        def authorized(self):return hmac.compare_digest(self.headers.get('X-Setup-Key','').encode(),app.key.encode())
        def read_body(self,limit=131072):
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=limit:raise ValueError()
                return self.rfile.read(n)
            except Exception:raise ValueError('SIZE')
        def allowed_host(self):
            raw=self.headers.get('Host','')
            try:
                parts=urlsplit('http://'+raw)
                if parts.username or parts.password or parts.path or not parts.hostname:return False
                hostname=host(parts.hostname)
                if app.config:return hostname in local_hosts() | {app.config['server_host'], 'localhost','127.0.0.1'}
                # Initial setup has no chosen hostname yet. It still requires the random setup key to save/read configuration.
                return True
            except ValueError:return False
        def do_GET(self):self.route()
        def do_POST(self):self.route()
        def route(self):
            if not self.allowed_host():return self.reply(403,{'error':'HOST'})
            self.path_only=urlsplit(self.path).path
            if self.path_only.startswith('/setup/api/'):
                if not self.authorized():return self.reply(401,{'error':'KEY'})
                if self.path_only=='/setup/api/config' and self.command=='GET':
                    return self.reply(200,{'configured':app.config is not None,'config':public(app.config or copy.deepcopy(DEFAULT)),
                        'shelly_url':'http://'+app.config['server_host']+':8088/shelly/temp?key='+app.shelly_key+'&temp=${ev.tC}' if app.config and app.config['flags']['shelly'] else None})
                if self.path_only=='/setup/api/health' and self.command=='GET':
                    return self.reply(200,{'services':app.health,'configured':bool(app.config)})
                if self.path_only=='/setup/api/config' and self.command=='POST':
                    if not self.origin():return self.reply(403,{'error':'ORIGIN'})
                    if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply(415,{'error':'CONTENT_TYPE'})
                    try:
                        data=json.loads(self.read_body())
                        with LOCK:app.save(data)
                        return self.reply(202,{'saved':True,'restarting':True})
                    except RuntimeError:return self.reply(409,{'error':'BUSY'})
                    except (ValueError,TypeError,KeyError) as exc:return self.reply(400,{'error':str(exc) if isinstance(exc,ValueError) else 'CONFIG'})
                return self.reply(404,{'error':'NOT_FOUND'})
            if self.path_only in ('/varmepumpe','/varmepumpe/'):
                return self.reply(302,b'',headers={'Location':'/'})
            if self.path_only in ('/setup','/setup/','/setup/setup.js','/setup/setup.css'):
                if self.command!='GET':return self.reply(405,{})
                name={'/setup':'index.html','/setup/':'index.html'}.get(self.path_only,Path(self.path_only).name)
                return self.file(HERE/'ui'/name)
            if self.path_only=='/api/health' and self.command=='GET':return self.reply(200,{'ok':True,'configured':bool(app.config)})
            if not app.config:
                return self.reply(302,b'',headers={'Location':'/setup/'})
            if app.restart:return self.reply(503,{'error':'RESTARTING'})
            if self.path_only=='/pi/config' and self.command=='GET':return self.reply(200,{'flags':app.config['flags']})
            if self.path_only=='/client.js' and self.command=='GET':return self.file(HERE/'ui/client.js')
            if self.path_only=='/cgi-bin/heatpump-latest' and self.command=='GET':
                try:return self.reply(200,last_complete_sample(app.data/'log/bsb.log'),'text/plain; charset=utf-8')
                except (OSError,ValueError):return self.reply(503,{'error':'NO_SAMPLE'})
            if self.path_only=='/pi/client.js' and self.command=='GET':return self.file(HERE/'ui/client.js')
            if self.path_only.startswith('/bsb/'):
                return self.bsb()
            if self.path_only=='/shelly/temp':return self.shelly()
            if self.path_only.startswith('/cgi-bin/'):
                return self.cgi()
            if self.command!='GET':return self.reply(405,{})

            if self.path_only in ('/bsb.log','/feil.log'):
                return self.file(app.data/'log'/self.path_only[1:])
            if self.path_only=='/index.html' and not app.config['flags']['heatpump']:return self.reply(404,{'error':'DISABLED'})
            try:
                if self.path_only not in ('/','/index.html','/kurver.html','/logg.html','/feil.html','/sprak.js','/undersider-sprak.js','/mobil.css','/summer.js','/compressor-daily.js','/compressor-daily.css','/auto-pause.js','/holiday.json','/mode.json','/pause.json','/dhw.json'):
                    return self.reply(404,{})
                path=(app.web/self.path_only.lstrip('/')).resolve()
                if not path.is_relative_to(app.web.resolve()):raise ValueError()
                if path.is_dir():path=path/'index.html'
                return self.file(path)
            except ValueError:return self.reply(404,{})
        def file(self,path):
            try:body=path.read_bytes()
            except (OSError,ValueError):return self.reply(404,{'error':'NOT_FOUND'})
            return self.reply(200,body,mimetypes.guess_type(path)[0] or 'application/octet-stream')
        def bsb(self):
            config=app.config
            if not config['flags']['heatpump']:return self.reply(404,{'error':'DISABLED'})
            command=self.path[5:]
            write=command.startswith(('S','I'))
            if write:
                if self.command!='POST' or not self.origin() or self.headers.get('X-KV8-Control')!='1':return self.reply(403,{'error':'ORIGIN'})
                if not config['flags']['controls']:return self.reply(403,{'error':'READ_ONLY'})
                if not re.fullmatch(r'S(?:700=[0-3]|10019=1|710=(?:1[89]|2[0-8])(?:\.[0-9])?)',command):return self.reply(400,{'error':'PARAMETER'})
                if command.startswith('S710=') and float(command[5:])>28:return self.reply(400,{'error':'VALUE'})
            elif self.command!='GET' or not re.fullmatch(r'JQ=[0-9]+(?:\.[0-9]+)?(?:,[0-9]+(?:\.[0-9]+)?)*',command):return self.reply(400,{'error':'PARAMETER'})
            try:
                with LOCK:
                    if app.restart:return self.reply(503,{})
                    body=request(command,config);kind='application/json' if command.startswith('JQ=') else 'text/plain'
                return self.reply(200,body,kind)
            except Exception:return self.reply(502,{'error':'BSB_UNAVAILABLE'})
        def shelly(self):
            if self.command!='GET' or not app.config['flags']['shelly']:return self.reply(404,{})
            args=parse_qs(urlsplit(self.path).query)
            if not hmac.compare_digest(args.get('key',[''])[0].encode(),app.shelly_key.encode()):return self.reply(403,{})
            raw=args.get('temp',[''])[0]
            if not re.fullmatch(r'[0-9]{1,2}(?:\.[0-9]{1,2})?',raw) or not 0<=float(raw)<=40:return self.reply(400,{'error':'TEMPERATURE'})
            try:
                with LOCK:
                    if app.restart:return self.reply(503,{})
                    reading={'temperature':float(raw),'at':time.time(),'target':app.config['bsb_host'],'port':app.config['bsb_port']}
                    atomic(app.data/'shelly/reading.json',reading)
                    forward_shelly(app.config,reading);app.last_shelly=time.monotonic()
                return self.reply(200,{'ok':True})
            except Exception:return self.reply(502,{'error':'BSB_UNAVAILABLE'})
        def cgi(self):
            path=self.path_only[len('/cgi-bin/'):];name,_,info=path.partition('/')
            feature={'compressor-daily':'heatpump','pause-status':'heatpump',
                     'summer-profile':'heatpump','pause-auto':'heatpump'}.get(name,'INVALID')
            if feature=='INVALID' or (feature and not app.config['flags'][feature]):return self.reply(404,{'error':'DISABLED'})
            if self.command not in ('GET','POST'):return self.reply(405,{})
            if self.command=='POST':
                if not self.origin():return self.reply(403,{'error':'ORIGIN'})
                if ((name=='summer-profile' and not app.config['flags']['schedule_controls']) or (name=='pause-auto' and not app.config['flags']['auto_pause'])):return self.reply(403,{'error':'READ_ONLY'})
            if name=='pause-auto' and not app.config['flags']['auto_pause']:
                return self.reply(200,{'enabled':False,'fresh':False})
            if name=='pause-status':
                try:return self.reply(200,query(app.config,['2843']))
                except Exception:return self.reply(502,{})
            env=os.environ.copy();env.update(REQUEST_METHOD=self.command,PATH_INFO='/'+info if info else '',
                QUERY_STRING=urlsplit(self.path).query,CONTENT_TYPE=self.headers.get('Content-Type',''),
                CONTENT_LENGTH=self.headers.get('Content-Length','0'),HTTP_HOST=self.headers.get('Host',''),
                HTTP_ORIGIN=self.headers.get('Origin',''),HTTP_X_CSRF_TOKEN=self.headers.get('X-CSRF-Token',''),
                BSB_DATA=str(app.data.resolve()),PYTHONPATH=str(HERE),TZ=app.config['timezone'],KV8_OFFSET=datetime.now().astimezone().strftime('%z'),KV8_BOOT_ID=boot_id())
            try:
                body=self.read_body(8192) if self.command=='POST' else b''
                with LOCK:
                    if app.restart:return self.reply(503,{})
                    result=subprocess.run(['sh',str(app.web/'cgi-bin'/name)],input=body,env=env,capture_output=True,timeout=70)
                raw=result.stdout.replace(b'\r\n',b'\n');head,sep,payload=raw.partition(b'\n\n')
                if not sep:raise ValueError()
                status=200;kind='application/json'
                for line in head.decode().split('\n'):
                    if line.lower().startswith('status:'):status=int(line.split()[1])
                    if line.lower().startswith('content-type:'):kind=line.partition(':')[2].strip()
                if name=='compressor-daily' and status==200:
                    d=json.loads(payload);d['timezone']=app.config['timezone'];payload=json.dumps(d).encode()
                return self.reply(status,payload,kind)
            except Exception:return self.reply(502,{'error':'CGI_UNAVAILABLE'})
    return Handler

def main():
    os.umask(0o077)
    app=Application()
    os.environ['TZ']=app.config['timezone'] if app.config else 'Europe/Oslo'
    if hasattr(time,'tzset'):time.tzset()
    server=ThreadingHTTPServer((os.environ.get('BSB_BIND','0.0.0.0'),int(os.environ.get('BSB_PORT','8088'))),handler(app));server.daemon_threads=True
    stop=threading.Event()
    def shutdown(*_):stop.set()
    signal.signal(signal.SIGTERM,shutdown);signal.signal(signal.SIGINT,shutdown)
    web=threading.Thread(target=server.serve_forever,daemon=True);web.start()
    supervisor=threading.Thread(target=app.supervise,daemon=True);supervisor.start()
    print('BSB Heatpump: open /setup/; setup key is in the data directory.',flush=True)
    while not stop.wait(.25) and not app.restart:pass
    app.stop();server.shutdown();server.server_close();supervisor.join(timeout=12)

if __name__=='__main__':main()

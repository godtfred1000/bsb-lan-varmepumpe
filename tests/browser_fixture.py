"""Synthetic local test harness. No hardware and no public interface."""
import sys,os,json,threading,tempfile,time
from pathlib import Path
from datetime import datetime,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from http.server import ThreadingHTTPServer
from config import DEFAULT,atomic
from server import Application,handler
from collector import collect,line
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_server import FakeBSB
import copy
os.environ['TZ']='Europe/Oslo'
if hasattr(time,'tzset'):time.tzset()
with tempfile.TemporaryDirectory() as name:
 root=Path(name)
 bsb=ThreadingHTTPServer(('127.0.0.1',0),FakeBSB)
 threading.Thread(target=bsb.serve_forever,daemon=True).start()
 c=copy.deepcopy(DEFAULT);c.update(server_host='127.0.0.1',bsb_host='127.0.0.1',bsb_port=bsb.server_port)
 c['flags'].update(controls=True,schedule_controls=True,auto_pause=True)
 atomic(root/'config.json',c)
 app=Application(root,workers=False)
 collect(c,root)
 # Enough synthetic log history for graph zoom and daily-statistics rendering.
 with (root/'log/bsb.log').open('w') as f:
  for i in range(1500):
   on=i%24<16;counter=100+i//24
   d={p:{'error':0,'value':v,'desc':'Comfort'} for p,v in {'8400':str(int(on)),'8451':str(counter),'8413':'20' if on else '0','8700':'12','8412':'32','8410':'28','8411':'34','8740':'21.8','8830':'50','710':'22','8006':'46','8003':'0','6700':'0','8402':'1' if i%48<10 else '0','8403':'0','5811':'3.0','5813':'3.0'}.items()}
   f.write(line(d,datetime.now()-timedelta(seconds=(1499-i)*30)))
 srv=ThreadingHTTPServer(('127.0.0.1',0),handler(app));srv.daemon_threads=True
 print(json.dumps({'base':'http://127.0.0.1:'+str(srv.server_port),'key':app.key}),flush=True)
 srv.serve_forever()


"""Integration against a loopback fake BSB. Never contacts a real heat pump."""
import copy,json,os,tempfile,threading,time,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from unittest.mock import patch
from datetime import datetime
from config import DEFAULT,validate,atomic
from collector import collect,line
from server import Application,handler,forward_shelly,last_complete_sample
from transport import request
import network
class FakeBSB(BaseHTTPRequestHandler):
 calls=[];redirect=False;broken=False
 def log_message(self,*args):pass
 def do_GET(self):
  self.calls.append(self.path)
  if self.redirect:self.send_response(302);self.send_header('Location','http://127.0.0.1:1/');self.end_headers();return
  if self.broken:self.send_error(503);return
  params=self.path.partition('/JQ=')[2].split(',')
  data={p:{'error':0,'value':'0','desc':'Off'} for p in params}
  for p,v in {'8400':'1','8451':'101','8413':'20','8700':'12','700':'1','2843':'30','5811':'3.0','5813':'3.0','642':'---','643':'---','712':'19','648':'0'}.items():
   if p in data:data[p]['value']=v
  for p in params:
   if p.startswith('501'):data[p].update(value='06:00-22:00',dataType_name='TIMEPROG')
  body=json.dumps(data).encode();self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.bsb=ThreadingHTTPServer(('127.0.0.1',0),FakeBSB);threading.Thread(target=cls.bsb.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):cls.bsb.shutdown();cls.bsb.server_close()
 def config(self,**flags):
  d=copy.deepcopy(DEFAULT);d.update(server_host='127.0.0.1',bsb_host='127.0.0.1',bsb_port=self.bsb.server_port);d['flags'].update(flags);return validate(d)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);FakeBSB.calls=[];FakeBSB.redirect=False;FakeBSB.broken=False
 def tearDown(self):self.tmp.cleanup()
 def web(self,config=None):
  if config:atomic(self.root/'config.json',config)
  app=Application(self.root,workers=False);srv=ThreadingHTTPServer(('127.0.0.1',0),handler(app));srv.daemon_threads=True
  threading.Thread(target=srv.serve_forever,daemon=True).start();self.addCleanup(srv.server_close);self.addCleanup(srv.shutdown)
  self.base='http://127.0.0.1:'+str(srv.server_port);return app
 def http(self,path,body=None,headers=None):
  try:
   with urlopen(Request(self.base+path,data=body,headers=headers or {}),timeout=10) as r:return r.status,r.read()
  except HTTPError as e:return e.code,e.read()
 def test_setup_requires_key_and_origin(self):
  a=self.web();self.assertEqual(self.http('/setup/')[0],200);self.assertEqual(self.http('/setup/api/config')[0],401)
  h={'X-Setup-Key':a.key,'Content-Type':'application/json'};payload=json.dumps(self.config()).encode()
  self.assertEqual(self.http('/setup/api/config',payload,h)[0],403)
  h['Origin']=self.base;self.assertEqual(self.http('/setup/api/config',payload,h)[0],202);self.assertTrue(a.restart)
  self.assertEqual((self.root/'config.json').stat().st_mode&0o777,0o600);self.assertEqual(FakeBSB.calls,[])
 def test_readonly_and_static_allowlist(self):
  a=self.web(self.config());collect(a.config,self.root)
  for path in ['/','/kurver.html','/logg.html','/feil.html','/client.js','/bsb.log','/mode.json','/cgi-bin/heatpump-latest','/cgi-bin/compressor-daily']:
   self.assertEqual(self.http(path)[0],200,path)
  for path in ['/config.json','/../config.json','/cgi-bin/mower-account','/startside/','/controllers/summer-profile/private/csrf.json']:
   self.assertEqual(self.http(path)[0],404,path)
  h={'Origin':self.base,'X-KV8-Control':'1'}
  for cmd in ['S700=1','S710=22','S10019=1','S2843=30']:
   self.assertIn(self.http('/bsb/'+cmd,b'{}',h)[0],(400,403))
  self.assertTrue(all(x.startswith('/JQ=') for x in FakeBSB.calls))
 def test_control_allowlist_origin_and_read_proxy(self):
  self.web(self.config(controls=True));h={'Origin':self.base,'X-KV8-Control':'1'}
  self.assertEqual(self.http('/bsb/S700=1',b'{}',h)[0],200)
  self.assertEqual(self.http('/bsb/S710=22.4',b'{}',h)[0],200)
  self.assertEqual(self.http('/bsb/S700=1')[0],403)
  self.assertEqual(self.http('/bsb/S700=1',b'{}',{'Origin':'http://other','X-KV8-Control':'1'})[0],403)
  for cmd in ['S1600=0','S710=28.9','S2843=30','I10000=22','JQ=700/http://other']:
   self.assertIn(self.http('/bsb/'+cmd,b'{}',h)[0],(400,403))
  self.assertEqual(self.http('/bsb/JQ=8400,8451')[0],200)
  self.assertEqual(FakeBSB.calls[:2],['/S700=1','/S710=22.4'])
 def test_no_false_stop_or_heater_power_as_state(self):
  row=line({'8400':{'error':1},'8451':{'error':0,'value':'9'},'5811':{'error':0,'value':'3.0'},'8402':{'error':0,'value':'0'}})
  self.assertIn('Kompressor: Ukjent',row);self.assertIn('Elvarme1: 0',row);self.assertIn('Elvarme1kW: 3.0',row)
 def test_shelly_optin_staleness_target_and_range(self):
  cfg=self.config(controls=True,shelly=True);reading=dict(at=time.time(),temperature=21.7,target=cfg['bsb_host'],port=cfg['bsb_port'])
  forward_shelly(cfg,reading);self.assertEqual(FakeBSB.calls,['/I10000=21.7'])
  for r in [{**reading,'at':time.time()-7801},{**reading,'temperature':float('nan')},{**reading,'target':'elsewhere'},{**reading,'temperature':41}]:
   with self.assertRaises(ValueError):forward_shelly(cfg,r)
  with self.assertRaises(ValueError):forward_shelly(self.config(),reading)
 def test_shelly_endpoint_key_and_validation(self):
  a=self.web(self.config(controls=True,shelly=True))
  self.assertEqual(self.http('/shelly/temp?temp=22')[0],403)
  self.assertEqual(self.http('/shelly/temp?key='+a.shelly_key+'&temp=41')[0],400)
  self.assertEqual(self.http('/shelly/temp?key='+a.shelly_key+'&temp=22.1')[0],200)
  self.assertEqual(FakeBSB.calls,['/I10000=22.1'])
 def test_current_address_changes_are_accepted(self):
  self.web(self.config())
  with patch('server.local_hosts',return_value={'100.90.80.70'}):
   self.assertEqual(self.http('/api/health',headers={'Host':'100.90.80.70:8088'})[0],200)
   self.assertEqual(self.http('/api/health',headers={'Host':'100.90.80.71:8088'})[0],403)
 def test_bsb_redirect_refused(self):
  FakeBSB.redirect=True
  with self.assertRaises(ValueError):request('JQ=700',self.config())
 def test_credentials_stay_private(self):
  c=self.config();c.update(bsb_username='user',bsb_password='synthetic-test-secret');a=self.web(c)
  status,body=self.http('/setup/api/config',headers={'X-Setup-Key':a.key});self.assertEqual(status,200);self.assertNotIn(b'synthetic-test-secret',body)
  status,body=self.http('/config.json');self.assertEqual(status,404);self.assertNotIn(b'synthetic-test-secret',body)
 def test_latest_ignores_incomplete_tail(self):
  p=self.root/'sample';row=line({});p.write_text(row+'Tidspunkt: unfinished');self.assertEqual(last_complete_sample(p),row.encode())
 def test_transport_optional_writers(self):
  c=self.config(controls=True)
  for cmd in ['S2843=30','S642=','S501=05:00-08:00_16:00-19:00','I10000=21']:
   with self.assertRaises(ValueError):request(cmd,c)
  c['flags'].update(auto_pause=True,schedule_controls=True,shelly=True)
  for cmd in ['S2843=30','S642=','S501=05:00-08:00_16:00-19:00','I10000=21']:
   request(cmd,c)
  with self.assertRaises(ValueError):request('S2843=40',c)
 def test_config_validation(self):
  for delta in [{'bsb_host':'http://example'},{'bsb_port':True},{'timezone':'made-up'},{'flags':{'controls':False,'auto_pause':True}},{'server_host':'1.2.3.4;rm'}]:
   with self.assertRaises(ValueError):validate({**self.config(),**delta})
 def test_render_preserves_historical_logs(self):
  a=self.web(self.config());p=self.root/'log/bsb.log';p.write_text('synthetic historical line\n');Application(self.root,workers=False);self.assertEqual(p.read_text(),'synthetic historical line\n')
if __name__=='__main__':unittest.main()

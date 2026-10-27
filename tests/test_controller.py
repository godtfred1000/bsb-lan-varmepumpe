import os
os.environ.setdefault('BSB_DATA','/tmp/bsb-test')
import importlib.util,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('a','controllers/pause-auto/controller.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def step(state,temp,pause,t,boot='one',wall=None):return a.evaluate(state,temp,pause,100000+t if wall is None else wall,2000+t,boot)
# Strict threshold; exactly 40 minutes, never early, in both directions.
for temp,current,want in [(10.1,20,30),(9.9,30,20)]:
 s={}
 for t in range(0,2400,60):
  s,desired=step(s,temp,current,t);assert desired is None
 s,desired=step(s,temp,current,2400);assert desired==want
# Recrossing/equality interrupts the entire candidate period.
s={}
for t in range(0,1801,60):s,_=step(s,11,20,t)
s,d=step(s,9,20,1860);assert s['elapsed']==0 and d is None
s,d=step(s,11,20,1920);assert s['elapsed']==0 and d is None
s,d=step(s,10,20,1980);assert s['side']=='equal' and d is None
s,d=step(s,11,20,2040);assert s['elapsed']==0
# A gap, reboot, clock jump, failed read, or reversed time cannot satisfy the 40 minute hold.
for kind in ['gap','reboot','clock','error','backwards']:
 s={}
 for t in range(0,2400,60):s,_=step(s,11,20,t)
 if kind=='gap':s,d=step(s,11,20,2600)
 elif kind=='reboot':s,d=step(s,11,20,2400,boot='two')
 elif kind=='clock':s,d=step(s,11,20,2400,wall=110000)
 elif kind=='error':s['error']='READ_FAILED';s['since_mono']=None;s,d=step(s,11,20,2400)
 else:s,d=step(s,11,20,2200)
 assert d is None and s['elapsed']==0,kind
# When actual setting already matches temperature, no write is needed even after the hold.
s={}
for t in range(0,2700,60):s,d=step(s,12,30,t);assert d is None and s['phase']=='matched'
# Network side effects in isolated sandbox: only 2843 and no repeat on failed verification.
with tempfile.TemporaryDirectory() as root:
 a.ROOT=Path(root);events=[];a.event=lambda name,**kw:events.append(name)
 writes=[];values=[(12.0,20),(12.0,30)];a.read_values=lambda:values.pop(0);a.write_pause=lambda v:writes.append(v)
 import os,time
 os.environ['KV8_BOOT_ID']='one'
 wall=time.time();mono=time.monotonic()
 a.atomic(a.ROOT/'state.json',{'boot':'one','updated':wall-60,'mono':mono-60,'since_mono':mono-2400,'side':'above','since':wall-2400})
 a.tick();assert writes==[30] and a.load()['pause']==30 and not a.load().get('pending')
 a.read_values=lambda:(12.0,30);a.tick();assert writes==[30]
 # Request reaches device but readback fails; reconcile next tick without issuing another write.
 a.atomic(a.ROOT/'state.json',{'boot':'one','updated':wall-60,'mono':mono-60,'since_mono':mono-2400,'side':'above','since':wall-2400})
 call=[0]
 def intermittent():
  call[0]+=1
  if call[0]>1:raise OSError()
  return 12,20
 a.read_values=intermittent;a.tick();assert a.load().get('pending') and writes==[30,30]
 a.read_values=lambda:(12,30);a.tick();assert not a.load().get('pending') and writes==[30,30]
 # A sensor outage retains current pause but loses the qualifying interval.
 a.read_values=lambda:(_ for _ in ()).throw(OSError());a.tick();assert a.load()['pause']==30 and a.load()['elapsed']==0
 a.read_values=lambda:(12,20);a.tick();assert a.load()['elapsed']==0 and writes==[30,30]
print('PASS 40 minutes both ways, exact threshold, recrossing, equality, sensor failures, reboot/gaps/clock jumps, no unnecessary write, write verification and uncertain-write recovery')
# Exercise the real writer allowlist and parameter path without network access.
spec2=importlib.util.spec_from_file_location('real','controllers/pause-auto/controller.py');real=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(real)
paths=[];real.fetch=lambda p:paths.append(p)
real.write_pause(20);real.write_pause(30);assert paths==['S2843=20','S2843=30']
for invalid in [0,8,15,25,40,'20',None]:
 try:real.write_pause(invalid);assert False
 except ValueError:pass
assert len(paths)==2
print('PASS: real writer allowlist only S2843=20 or S2843=30')

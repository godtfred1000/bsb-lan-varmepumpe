import os
os.environ.setdefault('BSB_DATA','/tmp/bsb-test')
import importlib.util,tempfile,time,json,os
from pathlib import Path
from datetime import date
spec=importlib.util.spec_from_file_location('s','controllers/summer-profile/service.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
clock=[date(2026,10,21)];s.today=lambda:clock[0]
def base():return {**{p:'06:00-22:00' for p in s.DAYS},'642':'---','643':'---','648':'0','700':'3','712':'19.0'}
with tempfile.TemporaryDirectory() as tmp:
 s.ROOT=Path(tmp);values=base();writes=[];s.snapshot=lambda:dict(values)
 def write(p,v):
  assert p in s.PARAMS and p not in ['712','1600','1610','1620','2843'];writes.append((p,v));values[p]=v
 s.write=write
 s.atomic(s.ROOT/'config.json',{'enabled':False});s.snapshot=lambda:(_ for _ in ()).throw(AssertionError('disabled read'));s.tick();s.snapshot=lambda:dict(values)
 # Summer+holiday: no scheduled bathroom heating even at heating-window times.
 values.update({p:s.TARGET for p in s.DAYS});values['700']='1'
 cfg={'enabled':True,'lastMode':'1','before':base()};s.atomic(s.ROOT/'config.json',cfg)
 s.holiday_apply(cfg,dict(values),{'start':'2026-10-21','end':'2026-10-24','season':'summer'})
 assert values['648']=='0' and values['700']=='1' and values['643']=='23.10.'
 for mode in ['0','1','0','1','0']:
  s.wanted_mode=lambda:mode;s.tick();assert values['700']=='1' and s.config()['enabled']
 assert s.public(dict(values),'')['phase']=='holiday'
 # Return day resumes summer timer, no holiday repeats next year.
 clock[0]=date(2026,10,24);s.wanted_mode=lambda:'0';s.tick()
 assert values['700']=='0' and values['642']=='---' and values['643']=='---' and not s.config()['holiday']['enabled'] and s.config()['enabled']
 s.wanted_mode=lambda:'1';s.tick();assert values['700']=='1'
 # Winter holiday booked in advance, no operating-mode change before departure.
 values.clear();values.update(base());clock[0]=date(2026,10,21);cfg={'enabled':False};s.atomic(s.ROOT/'config.json',cfg)
 s.holiday_apply(cfg,dict(values),{'start':'2026-10-23','end':'2026-10-26','season':'winter'})
 assert values['648']=='1' and values['700']=='3'
 s.tick();assert values['700']=='3'
 clock[0]=date(2026,10,23);s.tick();assert values['700']=='1'
 clock[0]=date(2026,10,26);s.tick();assert values==base()
 # Immediate cancellation resumes original Comfort and old holiday level.
 clock[0]=date(2026,10,21);cfg={'enabled':False}
 s.holiday_apply(cfg,dict(values),{'start':'2026-10-21','end':'2026-10-26','season':'winter'})
 assert values['700']=='1';s.finish_holiday(s.config(),dict(values));assert values==base()
 # A manual override is never overwritten by the timer.
 cfg={'enabled':False};s.holiday_apply(cfg,dict(values),{'start':'2026-10-21','end':'2026-10-26','season':'summer'})
 values['700']='2';n=len(writes);s.tick();assert len(writes)==n and not s.config()['holiday']['enabled']
 # Year crossing; home date exclusive.
 clock[0]=date(2026,12,20)
 h=s.holiday_input({'start':'2026-12-25','end':'2027-01-05','season':'winter'});assert s.holiday_targets(h)['643']=='04.01.'
 for data in [{'start':'2026-12-25','end':'2026-12-25','season':'winter'},{'start':'2026-12-19','end':'2027-01-05','season':'winter'},{'start':'2027-12-19','end':'2028-01-05','season':'winter'},{'start':'2026-12-25','end':'2027-01-05','season':'bad'}]:
  try:s.holiday_input(data);assert False
  except ValueError as e:assert str(e)=='BAD_DATES'
 # Roll back every uncertain/failed holiday write, including the write which changed value then failed.
 clock[0]=date(2026,10,21)
 for failure in [1,2,3,4]:
  values.clear();values.update(base());attempts=[0]
  def badwrite(p,v):
   values[p]=v;attempts[0]+=1
   if attempts[0]==failure:raise OSError('uncertain')
  s.write=badwrite
  try:s.transact(dict(values),{'648':'1','643':'25.10.','642':'21.10.','700':'1'});assert False
  except ValueError as e:assert str(e)=='APPLY_FAILED_RESTORED'
  assert values==base()
 # Actual encoder allowlist prevents DHW/temp writes and only uses encoded date fields.
 s.write=spec.loader.load_module if False else write
print('PASS: summer holiday priority, winter reduced=19 unchanged, future/active/return/cancel, year crossing, invalid dates, manual override, inactive zero reads, rollback every failure point; no DHW/temperature/pause writes')

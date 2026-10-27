import os
os.environ.setdefault('BSB_DATA','/tmp/bsb-test')
import importlib.util,time,os
from datetime import datetime
os.environ['TZ']='CET-1CEST,M3.5.0,M10.5.0/3';time.tzset()
spec=importlib.util.spec_from_file_location('s','controllers/compressor-daily/stats.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
def epoch(ts):return time.mktime(datetime.fromisoformat(ts).timetuple())
def sample(ts,on,count,mod=None,status='46'):
 line=f'Tidspunkt: {ts} | Kompressor: {"På" if on else "Av"} | Kompressorstarter: {count} | Modulering: {16 if on else 0 if mod is None else mod} % | Driftstatus: {status}\n'
 return s.parse(line)
def calc(rows,at):return s.calculate(rows,epoch(at))
# Complete real run, two short Off dips with unchanged counter, proper stop held >120s.
r=[sample('2026-10-21 23:59:40',False,100),sample('2026-10-22 00:00:20',True,101),sample('2026-10-22 00:01:00',True,101),sample('2026-10-22 00:01:40',False,101),sample('2026-10-22 00:02:20',True,101),sample('2026-10-22 00:03:00',False,101),sample('2026-10-22 00:03:40',False,101),sample('2026-10-22 00:04:20',True,101),sample('2026-10-22 00:05:00',False,101),sample('2026-10-22 00:05:40',False,101),sample('2026-10-22 00:06:20',False,101),sample('2026-10-22 00:07:10',False,101)]
d,a=calc(r,'2026-10-22 00:07:10');assert d['today']['starts']==1 and d['today']['stops']==1 and d['today']['average_seconds']==280,(d,a)
# Pending live tail: no immediate false stop and no unconfirmed last counter spike.
d,a=calc(r[:4],'2026-10-22 00:01:40');assert d['today']['stops']==0
r2=r+[sample('2026-10-22 00:07:50',True,99999)];d,a=calc(r2,'2026-10-22 00:07:50');assert d['today']['starts']==1
r2+=[sample('2026-10-22 00:08:30',True,101)];d,a=calc(r2,'2026-10-22 00:08:30');assert d['today']['starts']==1
# Crossing midnight: starts belong to the actual start day, full completed runtime to stop day.
r=[sample('2026-10-21 23:58:00',False,100),sample('2026-10-21 23:58:40',True,101),sample('2026-10-21 23:59:20',True,101),sample('2026-10-22 00:00:00',True,101),sample('2026-10-22 00:00:40',False,101),sample('2026-10-22 00:03:00',False,101)]
d,a=calc(r,'2026-10-22 00:03:00');assert d['today']['starts']==0 and d['yesterday']['starts']==1 and d['today']['stops']==1 and d['today']['average_seconds']==120
before,_=calc(r,'2026-10-21 23:59:59');assert before['today']['starts']==1 and before['today']['stops']==0
# Real fast restart is confirmed by 8451, so it must not be filtered.
r=[sample('2026-10-22 00:00:00',True,100),sample('2026-10-22 00:00:40',False,100),sample('2026-10-22 00:01:20',True,101),sample('2026-10-22 00:02:00',True,101)]
d,a=calc(r,'2026-10-22 00:02:00');assert d['today']['starts']==1 and d['today']['stops']==1
# Defrost and Av with nonzero modulation are not compressor stops.
r=[sample('2026-10-22 00:00:00',True,100)]+[sample(f'2026-10-22 00:0{i}:00',False,100,status='193') for i in range(1,5)]+[sample('2026-10-22 00:05:00',True,100)]
d,a=calc(r,'2026-10-22 00:05:00');assert d['today']['starts']==0 and d['today']['stops']==0
# Missing data does not invent completed runtime; no samples means unknown, not zero.
d,a=calc([],'2026-10-22 12:00:00');assert d['today']['starts'] is None
# Reset is marked incomplete and not counted as thousands of starts.
r=[sample('2026-10-22 00:00:00',True,50000),sample('2026-10-22 00:01:00',True,0),sample('2026-10-22 00:02:00',True,0)]
d,a=calc(r,'2026-10-22 00:02:00');assert d['today']['starts']==0 and d['today']['partial']
# Local calendar date is independent of UTC; DST fall day is 25 hours.
assert epoch('2026-10-26 00:00:00')-epoch('2026-10-25 00:00:00')==25*3600
print('PASS: counter validation, false stop filter, live tail, midnight, cross-midnight runtime, fast real restart, defrost, missing data, reset and DST')

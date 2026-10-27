"""Read-only daily compressor statistics from the existing BSB log."""
import json, os, re, sys, time
from datetime import datetime, date, timedelta

if hasattr(time,'tzset'):time.tzset()
DEBOUNCE=120
MAX_GAP=180
DEFROST={'125','192','193','194','195'}

def parse(line):
    if not line.endswith('\n'):return None
    fields={}
    for part in line.split('|'):
        k,sep,v=part.strip().partition(':')
        if sep:fields[k]=v.strip()
    try:
        stamp=fields['Tidspunkt'];dt=datetime.strptime(stamp,'%Y-%m-%d %H:%M:%S')
        t=time.mktime(dt.timetuple())
    except (KeyError,ValueError,OverflowError):return None
    c=fields.get('Kompressorstarter','')
    counter=int(c) if re.fullmatch(r'\d{1,10}',c) else None
    raw=fields.get('Kompressor')
    state=True if raw=='På' else False if raw=='Av' else None
    mod=fields.get('Modulering','').split(' ')[0]
    try:mod=float(mod)
    except ValueError:mod=None
    # The logger maps missing 8400 to Av. A missing modulation value cannot confirm a stop.
    if state is False and (mod is None or mod>0 or fields.get('Driftstatus') in DEFROST):state=None
    return {'t':t,'stamp':stamp,'day':stamp[:10],'counter':counter,'state':state}

def read_rows(source,now):
    cutoff=(date.fromtimestamp(now)-timedelta(days=3)).isoformat()
    rows=[];previous=None
    for line in source:
        if not line.startswith('Tidspunkt: '):continue
        if line[11:21]<cutoff:
            previous=line;continue
        if previous:
            r=parse(previous)
            if r:rows.append(r)
            previous=None
        r=parse(line)
        if r and r['t']<=now:rows.append(r)
    if not rows and previous:
        r=parse(previous)
        if r and r['t']<=now:rows.append(r)
    return rows

def calculate(rows,now):
    day=date.fromtimestamp(now);yesterday=day-timedelta(days=1)
    days={d.isoformat():{'date':d.isoformat(),'starts':0,'stops':0,'average_seconds':None,'completed_runs':0,'partial':False} for d in [day,yesterday]}
    audit={'starts':[],'stops':[],'runs':[]};pending=False
    rows=[r for r in rows if r['t']<=now]
    # Duplicate/out-of-order samples cannot create extra events.
    clean=[]
    for r in rows:
        if clean and r['t']<=clean[-1]['t']:continue
        clean.append(r)
    rows=clean
    def partial(d):
        if d in days:days[d]['partial']=True
    if not rows:
        return {'today':{**days[day.isoformat()],'starts':None,'stops':None},'yesterday':{**days[yesterday.isoformat()],'starts':None,'stops':None},'last_sample':None,'pending':False,'stale':True,'counter':None},audit
    for d in days:
        midnight=time.mktime(datetime.fromisoformat(d).timetuple())
        if not any(r['t']<=midnight and r['counter'] is not None for r in rows):partial(d)
    # Counter increments must persist into the next valid reading. A one-sample spike/dip is ignored.
    valid=[(i,r) for i,r in enumerate(rows) if r['counter'] is not None]
    starts={};start_reliable={};baseline=None
    for n,(i,r) in enumerate(valid):
        if baseline is None:baseline=r;continue
        diff=r['counter']-baseline['counter']
        if diff==0:baseline=r;continue
        following=valid[n+1][1] if n+1<len(valid) else None
        if following is None:
            pending=True;continue
        confirmed=following['counter']>=r['counter'] if diff>0 else following['counter']==r['counter']
        if not confirmed:continue
        interval=r['t']-baseline['t']
        if diff<0:
            partial(r['day']);baseline=r;continue
        if diff>max(1,int(interval//60)+1):partial(r['day']);continue
        starts[i]=diff
        start_reliable[i]=diff==1 and interval<=MAX_GAP
        audit['starts'].append({'at':r['stamp'],'count':diff,'counter':r['counter']})
        if r['day'] in days:days[r['day']]['starts']+=diff
        if interval>MAX_GAP:
            partial(r['day'])
            if baseline['day']!=r['day']:partial(baseline['day'])
        baseline=r
    # Use the same 120-second look-ahead rule as logg.html, plus confirmation at the live tail.
    stops=set();state=None
    for i,r in enumerate(rows):
        current=r['state']
        if current is None:continue
        if state is None:state=current;continue
        if state and not current:
            counter=r['counter'];previous=rows[i-1]['counter'] if i else None
            short=False;confirmed=False
            for ni in range(i+1,len(rows)):
                nxt=rows[ni]
                dt=nxt['t']-r['t']
                if dt>DEBOUNCE:
                    confirmed=True;break
                if ni in starts:
                    confirmed=True;break
                if nxt['state'] is True and (counter is None or nxt['counter'] is None or nxt['counter']==counter):
                    short=True;break
            if short:continue
            if not confirmed:
                pending=True;continue
            if i in starts:continue
            stops.add(i);audit['stops'].append({'at':r['stamp']})
            if r['day'] in days:days[r['day']]['stops']+=1
        state=current
    # Average only complete, counter-confirmed runs which STOPPED today; include their full duration across midnight.
    opened=bool(rows[0]['state']);started=None;reliable=False;last_stop=-1
    totals={d:[] for d in days}
    for i,r in enumerate(rows):
        if i and r['t']-rows[i-1]['t']>MAX_GAP:reliable=False
        if i in stops:
            if opened and started is not None and reliable and r['t']>=started:
                seconds=int(r['t']-started)
                audit['runs'].append({'stop':r['stamp'],'seconds':seconds})
                if r['day'] in totals:totals[r['day']].append(seconds)
            elif r['day'] in days:partial(r['day'])
            opened=False;started=None;last_stop=i
        if i in starts:
            missing_stop=opened and started is not None
            if missing_stop:partial(r['day'])
            opened=True;started=r['t'];reliable=start_reliable[i] and not missing_stop
            # 8400 and 8451 are read sequentially. Use a preceding On edge only when close and after the last stop.
            for j in range(i-1,max(last_stop,i-4),-1):
                if r['t']-rows[j]['t']>DEBOUNCE or rows[j]['state'] is False:break
                if rows[j]['state'] is True:started=rows[j]['t']
    for d,a in totals.items():
        days[d]['completed_runs']=len(a)
        if a:days[d]['average_seconds']=round(sum(a)/len(a))
    last=rows[-1]
    if last['day']<day.isoformat():partial(day.isoformat())
    if last['day']<yesterday.isoformat():partial(yesterday.isoformat())
    return {'today':days[day.isoformat()],'yesterday':days[yesterday.isoformat()],
            'last_sample':last['stamp'],'pending':pending,'stale':now-last['t']>MAX_GAP,
            'counter':next((r['counter'] for r in reversed(rows) if r['counter'] is not None),None)},audit

def main():
    if os.environ.get('REQUEST_METHOD','GET')!='GET':
        print('Status: 405 Method Not Allowed\r\nContent-Type: application/json\r\n\r\n{"error":"METHOD"}');return
    try:
        now=time.time()
        with os.fdopen(3,'r',encoding='utf-8',errors='replace',closefd=False) as source:
            stat=os.fstat(3);key=[stat.st_size,stat.st_mtime_ns,date.fromtimestamp(now).isoformat()]
            cache='/tmp/compressor-daily-cache.json';data=None
            try:
                with open(cache) as f:c=json.load(f)
                if c['key']==key and now-c['at']<15:data=c['data']
            except (OSError,ValueError,KeyError):pass
            if data is None:
                data,_=calculate(read_rows(source,now),now)
                try:
                    with open(cache+'.tmp','w') as f:json.dump({'key':key,'at':now,'data':data},f)
                    os.replace(cache+'.tmp',cache)
                except OSError:pass
        data.update(generated=int(now),timezone='Europe/Oslo')
        print('Content-Type: application/json; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n\r\n'+json.dumps(data))
    except Exception:
        print('Status: 503 Service Unavailable\r\nContent-Type: application/json\r\nCache-Control: no-store\r\n\r\n{"error":"LOG_UNAVAILABLE"}')

if __name__=='__main__':main()

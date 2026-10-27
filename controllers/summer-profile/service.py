"""Manually enabled summer timer; only HC1 mode and schedule writes."""
import fcntl, hashlib, json, os, re, secrets, subprocess, sys, time
from pathlib import Path
from datetime import date, timedelta
from urllib.request import urlopen
from urllib.parse import quote
from http import HTTPStatus
from http.client import IncompleteRead

if hasattr(time,'tzset'):time.tzset()

ROOT=Path(os.environ['BSB_DATA'])/'controllers/summer-profile/private'
DAYS=['501']+['501.%d'%n for n in range(1,7)]
PARAMS=DAYS+['648','643','642','700']
READ_PARAMS=PARAMS+['712']
TARGET='05:00-08:00_16:00-19:00'
EXPECTED=[('05:00','08:00'),('16:00','19:00')]

def atomic(path,value):
    tmp=path.with_suffix('.tmp')
    fd=os.open(tmp,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f)
    os.replace(tmp,path)

def fetch(path):
    from transport import request
    return request(path)

def periods(value):
    if not isinstance(value,str):raise ValueError('BAD_SCHEDULE')
    tokens=value.replace('_',' ').split()
    if not 1<=len(tokens)<=3:raise ValueError('BAD_SCHEDULE')
    out=[];disabled=False
    for token in tokens:
        if token=='##:##-##:##':disabled=True;continue
        if disabled:raise ValueError('BAD_SCHEDULE')
        m=re.fullmatch(r'((?:[01]\d|2[0-3]):[0-5]\d)-((?:[01]\d|2[0-3]):[0-5]\d|24:00)',token)
        if not m or m[1]>=m[2]:raise ValueError('BAD_SCHEDULE')
        out.append((m[1],m[2]))
    if not out:raise ValueError('BAD_SCHEDULE')
    return out

def snapshot():
    result=json.loads(fetch('JQ='+','.join(READ_PARAMS)))
    clean={}
    for p in READ_PARAMS:
        d=result.get(p,{})
        if d.get('error')!=0 or not isinstance(d.get('value'),str):raise ValueError('READ_FAILED')
        if p in DAYS:
            if d.get('dataType_name')!='TIMEPROG':raise ValueError('READ_FAILED')
            periods(d['value'])
        elif p in ['642','643']:holiday_date(d['value'])
        elif p=='648' and d['value'] not in ['0','1']:raise ValueError('READ_FAILED')
        elif p=='712':float(d['value'])
        elif p=='700' and d['value'] not in ['0','1','2','3']:raise ValueError('READ_FAILED')
        clean[p]=d['value']
    return clean

def holiday_date(value):
    if value=='---':return None
    match=re.fullmatch(r'(\d{1,2})\.(\d{1,2})\.',value.strip())
    if not match:raise ValueError('READ_FAILED')
    day,month=map(int,match.groups());date(2000,month,day)
    return '%02d.%02d.'%(day,month)

def today():return date(*time.localtime()[:3])

def holiday_input(data):
    try:
        start=date.fromisoformat(data['start']);end=date.fromisoformat(data['end'])
        if start.isoformat()!=data['start'] or end.isoformat()!=data['end']:raise ValueError()
        if not today()<=start<=today()+timedelta(days=365) or not 1<=(end-start).days<=365 or end>today()+timedelta(days=365):raise ValueError()
        if data['season'] not in ['summer','winter']:raise ValueError()
        return {'start':start.isoformat(),'end':end.isoformat(),'season':data['season']}
    except (ValueError,KeyError,TypeError):raise ValueError('BAD_DATES')

def holiday_targets(h):
    # Return day is exclusive: normal heating resumes at 00:00 on that day.
    return {'642':date.fromisoformat(h['start']).strftime('%d.%m.'),
            '643':(date.fromisoformat(h['end'])-timedelta(days=1)).strftime('%d.%m.'),
            '648':'0' if h['season']=='summer' else '1'}

def holiday_phase(h):
    if not h.get('enabled'):return 'none'
    now=today().isoformat()
    return 'scheduled' if now<h['start'] else 'active' if now<h['end'] else 'ended'

def same(p,value,target):
    return periods(value)==periods(target) if p in DAYS else holiday_date(value)==holiday_date(target) if p in ['642','643'] else value==target

def revision(values):
    normalized={p:periods(values[p]) if p in DAYS else values[p] for p in PARAMS}
    return hashlib.sha256(json.dumps(normalized,sort_keys=True).encode()).hexdigest()

def write(p,value):
    if p not in PARAMS:raise ValueError('FORBIDDEN_PARAMETER')
    if p in DAYS:value='_'.join(a+'-'+b for a,b in periods(value))
    elif p in ['642','643']:value='' if value=='---' else holiday_date(value)
    elif p=='648' and value not in ['0','1']:raise ValueError('BAD_MODE')
    elif p=='700' and value not in ['0','1','2','3']:raise ValueError('BAD_MODE')
    # A failed write is not blindly repeated. Verify via a fresh read instead.
    fetch('S'+p+'='+quote(value,safe=':_-'))

def config():
    try:return json.loads((ROOT/'config.json').read_text())
    except (OSError,ValueError):return {'enabled':False}

def wanted_mode(now=None):
    now=now or time.localtime()
    minute=now.tm_hour*60+now.tm_min
    return '1' if 300<=minute<480 or 960<=minute<1140 else '0'

def schedule_matches(values):
    return all(periods(values[p])==EXPECTED for p in DAYS)

def disable(cfg,reason):
    cfg.update(enabled=False,reason=reason)
    atomic(ROOT/'config.json',cfg)

def suspend(cfg,reason):
    cfg.update(enabled=False,reason=reason)
    if cfg.get('holiday',{}).get('enabled'):
        cfg['holiday'].update(enabled=False,reason=reason)
    atomic(ROOT/'config.json',cfg)

def finish_holiday(cfg,values):
    h=cfg['holiday']
    targets={'642':'---','643':'---','648':h['beforeLevel']}
    targets['700']=wanted_mode() if cfg.get('enabled') else h['resumeMode']
    transact(values,targets)
    h.update(enabled=False,reason='ENDED')
    cfg['lastMode']=targets['700'];cfg.pop('pending',None)
    atomic(ROOT/'config.json',cfg)

def holiday_apply(cfg,before,data):
    if cfg.get('holiday',{}).get('enabled') or before['642']!='---' or before['643']!='---':raise ValueError('CONFLICT')
    h={**holiday_input(data),'enabled':True,'resumeMode':before['700'],'beforeLevel':before['648']}
    targets=holiday_targets(h)
    if holiday_phase(h)=='active':targets['700']='1'
    transact(before,targets)
    cfg.update(lastMode=targets.get('700',before['700']),holiday=h)
    atomic(ROOT/'config.json',cfg)

def tick():
    cfg=config()
    if not cfg.get('enabled') and not cfg.get('holiday',{}).get('enabled'):return
    with open(ROOT/'lock','a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        cfg=config();h=cfg.get('holiday',{})
        if not cfg.get('enabled') and not h.get('enabled'):return
        try:
            values=snapshot()
            if cfg.get('enabled') and not schedule_matches(values):return suspend(cfg,'MANUAL_CHANGE')
            if h.get('enabled') and not all(same(p,values[p],v) for p,v in holiday_targets(h).items()):return suspend(cfg,'MANUAL_CHANGE')
            pending=cfg.get('pending')
            if pending:
                if values['700']==pending['to']:
                    cfg['lastMode']=pending['to'];cfg.pop('pending',None)
                    atomic(ROOT/'config.json',cfg)
                elif values['700']==pending['from']:return suspend(cfg,'TIMER_FAILED')
                else:return suspend(cfg,'MANUAL_CHANGE')
            if values['700']!=cfg['lastMode']:return suspend(cfg,'MANUAL_CHANGE')
            phase=holiday_phase(h)
            if phase=='ended':return finish_holiday(cfg,values)
            # Native holiday level 648 overrides the day schedule while 700 is Auto.
            desired='1' if phase=='active' else wanted_mode() if cfg.get('enabled') else values['700']
            if desired==values['700']:return
            cfg['pending']={'from':values['700'],'to':desired}
            atomic(ROOT/'config.json',cfg)
            try:write('700',desired)
            except Exception:pass
            after=snapshot()
            if after['700']!=desired:return suspend(cfg,'TIMER_FAILED')
            cfg['lastMode']=desired;cfg.pop('pending',None)
            atomic(ROOT/'config.json',cfg)
        except Exception:return


def public(values,csrf):
    cfg=config()
    active=bool(cfg.get('enabled') and schedule_matches(values) and values['700']==cfg.get('lastMode'))
    return {'active':active,'enabled':bool(cfg.get('enabled')),
            'phase':'holiday' if holiday_phase(cfg.get('holiday',{}))=='active' else 'heating' if values['700']=='1' else 'off',
            'holiday':{**{k:v for k,v in cfg.get('holiday',{}).items() if k in ['enabled','start','end','season','reason']},'phase':holiday_phase(cfg.get('holiday',{}))},
            'holidayValues':{p:values[p] for p in ['642','643','648']},'reduced':values['712'],
            'reason':cfg.get('reason'),'canRestore':bool(cfg.get('before')),
            'mode':int(values['700']),'days':[values[p] for p in DAYS],
            'revision':revision(values),'csrf':csrf,'checked':int(time.time()),'operation':operation()}

def operation():
    try:
        d=json.loads((ROOT/'operation.json').read_text())
        return {k:d[k] for k in ('id','status','error') if k in d}
    except (OSError,ValueError):return None

def worker(jobid):
    with open(ROOT/'lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        job=json.loads((ROOT/'operation.json').read_text())
        if job.get('id')!=jobid or job.get('status')!='queued':return
        job['status']='running';atomic(ROOT/'operation.json',job)
        try:
            before=snapshot()
            if revision(before)!=job['revision']:raise ValueError('CONFLICT')
            cfg=config()
            action=job.get('action')
            h=cfg.get('holiday',{})
            if action=='holiday_apply':holiday_apply(cfg,before,job['holiday'])
            elif action=='holiday_cancel':
                if h.get('enabled'):finish_holiday(cfg,before)
                else:transact(before,{'642':'---','643':'---'})
            else:
                if h.get('enabled') or before['642']!='---' or before['643']!='---':raise ValueError('CONFLICT')
                if action=='restore':
                    if not cfg.get('before'):raise ValueError('CONFLICT')
                    disable(cfg,'STOPPED')
                    transact(before,{p:cfg['before'][p] for p in DAYS+['700']})
                else:
                    if cfg.get('enabled'):raise ValueError('CONFLICT')
                    desired={p:TARGET for p in DAYS};desired['700']=wanted_mode()
                    transact(before,desired)
                    cfg.update(enabled=True,before=before,lastMode=desired['700'])
                    atomic(ROOT/'config.json',cfg)
            job['status']='done'
        except Exception as e:
            job['status']='error';job['error']=str(e) if str(e) in ['CONFLICT','APPLY_FAILED_RESTORED','APPLY_FAILED_CHECK'] else 'READ_FAILED'
        atomic(ROOT/'operation.json',job)

def transact(before,targets):
    atomic(ROOT/('before-%d.json'%time.time_ns()),{'time':int(time.time()),'values':before})
    attempted=[]
    try:
        for p in PARAMS: # Change the operating mode only after all seven days are verified.
            if p not in targets:continue
            desired=targets[p]
            if same(p,before[p],desired):continue
            attempted.append((p,desired))
            write(p,desired)
            after=snapshot()
            if not same(p,after[p],desired):raise ValueError('NOT_CONFIRMED')
        after=snapshot()
        if not all(same(p,after[p],targets[p]) for p in targets):raise ValueError('NOT_CONFIRMED')
        return after
    except Exception:
        restored=True
        for p,desired in reversed(attempted):
            try:
                current=snapshot()
                if same(p,current[p],before[p]):continue
                if not same(p,current[p],desired):restored=False;continue
                write(p,before[p])
                if not same(p,snapshot()[p],before[p]):restored=False
            except Exception:restored=False
        raise ValueError('APPLY_FAILED_RESTORED' if restored else 'APPLY_FAILED_CHECK')

def respond(code,data):
    sys.stdout.write('Status: %d %s\r\nContent-Type: application/json; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n\r\n'%(code,HTTPStatus(code).phrase))
    sys.stdout.write(json.dumps(data,ensure_ascii=True))

def main():
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o700)
    # Exclusive lock also protects first-time token creation and parameter writes.
    with open(ROOT/'lock','a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            op=operation()
            if os.environ.get('REQUEST_METHOD')=='GET' and op and op['status'] in ['queued','running']:
                csrf=json.loads((ROOT/'csrf.json').read_text())['csrf']
                return respond(200,{'busy':True,'active':False,'operation':op,'csrf':csrf,'checked':int(time.time())})
            return respond(409,{'error':'BUSY'})
        tokenfile=ROOT/'csrf.json'
        try:csrf=json.loads(tokenfile.read_text())['csrf']
        except (OSError,ValueError,KeyError):csrf=secrets.token_urlsafe(32);atomic(tokenfile,{'csrf':csrf})
        method=os.environ.get('REQUEST_METHOD')
        try:
            if method=='GET':return respond(200,public(snapshot(),csrf))
            if method!='POST':return respond(405,{'error':'METHOD'})
            host=os.environ.get('HTTP_HOST','')
            if os.environ.get('HTTP_ORIGIN')!='http://'+host:
                return respond(403,{'error':'ORIGIN'})
            if os.environ.get('CONTENT_TYPE')!='application/json':return respond(415,{'error':'CONTENT_TYPE'})
            size=int(os.environ.get('CONTENT_LENGTH','0'))
            if not 1<=size<=4096:return respond(413,{'error':'SIZE'})
            data=json.loads(sys.stdin.buffer.read(size))
            if not isinstance(data,dict) or not isinstance(data.get('csrf'),str) or not secrets.compare_digest(data['csrf'],csrf):return respond(403,{'error':'CSRF'})
            if data.get('action') not in ['apply','restore','holiday_apply','holiday_cancel']:return respond(400,{'error':'ACTION'})
            op=operation()
            if op and op['status'] in ['queued','running']:return respond(409,{'error':'BUSY'})
            holiday=holiday_input(data) if data['action']=='holiday_apply' else None
            before=snapshot()
            if data.get('revision')!=revision(before):return respond(409,{'error':'CONFLICT'})
            job={'id':secrets.token_hex(12),'status':'queued','revision':revision(before),'action':data['action']}
            if holiday:job['holiday']=holiday
            atomic(ROOT/'operation.json',job)
            try:
                subprocess.Popen([sys.executable,__file__,'--apply',job['id']],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
            except Exception:
                atomic(ROOT/'operation.json',{**job,'status':'error','error':'READ_FAILED'});raise
            return respond(202,{'accepted':True,'operation':operation()})
        except ValueError as e:return respond(502,{'error':str(e) if str(e) in ['APPLY_FAILED_RESTORED','APPLY_FAILED_CHECK','BAD_DATES'] else 'READ_FAILED'})
        except Exception:return respond(502,{'error':'READ_FAILED'})

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--apply' and re.fullmatch('[0-9a-f]{24}',sys.argv[2]):worker(sys.argv[2])
    elif len(sys.argv)==2 and sys.argv[1]=='--tick':tick()
    else:main()

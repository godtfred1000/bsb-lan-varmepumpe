"""Automatic minimum compressor OFF time. Only writes 2843=20 or 2843=30."""
import fcntl,json,math,os,sys,time
from pathlib import Path
from urllib.request import urlopen
from http.client import IncompleteRead
ROOT=Path(os.environ['BSB_DATA'])/'controllers/pause-auto/private'
HOLD=40*60
MAX_GAP=150

def atomic(path,data):
    tmp=path.with_suffix('.tmp')
    fd=os.open(tmp,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as f:json.dump(data,f)
    os.replace(tmp,path)

def load():
    try:return json.loads((ROOT/'state.json').read_text())
    except (OSError,ValueError):return {}

def fetch(path):
    from transport import request
    return request(path)

def read_values():
    data=json.loads(fetch('JQ=8700,2843'))
    for p in ['8700','2843']:
        if data.get(p,{}).get('error')!=0:raise ValueError('READ_FAILED')
    temperature=float(data['8700']['value']);raw=str(data['2843']['value'])
    if not math.isfinite(temperature) or not -80<=temperature<=80 or not raw.isdigit():raise ValueError('READ_FAILED')
    return temperature,int(raw)

def write_pause(value):
    if value not in [20,30]:raise ValueError('FORBIDDEN_VALUE')
    fetch('S2843='+str(value))

def event(kind,**data):
    fd=os.open(ROOT/'events.jsonl',os.O_CREAT|os.O_APPEND|os.O_WRONLY,0o600)
    with os.fdopen(fd,'a') as f:f.write(json.dumps(dict(at=int(time.time()),event=kind,**data))+'\n')

def evaluate(previous,temperature,pause,wall,mono,boot):
    """Pure decision: no network and no pump writes."""
    state=dict(previous)
    contiguous=(state.get('boot')==boot and 0<mono-state.get('mono',-1)<=MAX_GAP
                and abs((wall-state.get('updated',0))-(mono-state.get('mono',0)))<=10
                and not state.get('error'))
    side='above' if temperature>10 else 'below' if temperature<10 else 'equal'
    target=30 if side=='above' else 20 if side=='below' else None
    if not contiguous or state.get('side')!=side or side=='equal':
        state['since_mono']=mono;state['since']=wall
    elapsed=max(0,int(mono-state.get('since_mono',mono)))
    state.update(updated=wall,mono=mono,boot=boot,temperature=temperature,pause=pause,
                 side=side,target=target,elapsed=min(HOLD,elapsed),error=None)
    state['phase']='equal' if side=='equal' else 'matched' if pause==target else 'waiting'
    desired=target if target is not None and pause!=target and elapsed>=HOLD else None
    return state,desired

def tick():
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o700)
    with open(ROOT/'lock','a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        before=load();wall=time.time();mono=time.monotonic();boot=os.environ.get('KV8_BOOT_ID','unknown')
        try:temperature,pause=read_values()
        except Exception:
            state=dict(before);state.update(error='READ_FAILED',phase='paused',since_mono=None,elapsed=0,attempted_at=wall)
            if before.get('error')!='READ_FAILED':event('read_failed')
            atomic(ROOT/'state.json',state);return
        # After an uncertain previous write, read back before making any new decision.
        pending=before.get('pending')
        if pending:
            confirmed=pause==pending['to']
            event('write_confirmed' if confirmed else 'write_not_confirmed',**pending,observed=pause)
            before.pop('pending',None)
            if not confirmed:before.update(error='WRITE_FAILED',since_mono=None)
        state,desired=evaluate(before,temperature,pause,wall,mono,boot)
        if desired is None:
            atomic(ROOT/'state.json',state);return
        pending={'from':pause,'to':desired,'temperature':temperature}
        state.update(pending=pending,phase='checking')
        atomic(ROOT/'state.json',state) # Write-ahead journal survives power loss.
        event('write_requested',**pending)
        try:write_pause(desired)
        except Exception:pass # Never repeat an uncertain command blindly.
        try:temperature_after,pause_after=read_values()
        except Exception:
            state.update(error='VERIFY_FAILED',phase='paused',elapsed=0,since_mono=None)
            atomic(ROOT/'state.json',state);return
        state.pop('pending',None)
        state['pause']=pause_after
        if pause_after==desired:
            state.update(phase='matched',error=None)
            event('write_confirmed',**pending)
        else:
            state.update(error='WRITE_FAILED',phase='paused',elapsed=0,since_mono=None)
            event('write_not_confirmed',**pending,observed=pause_after)
        atomic(ROOT/'state.json',state)

def public(state,now=None):
    now=time.time() if now is None else now
    fields=['temperature','pause','side','target','elapsed','phase','error','updated','since']
    data={k:state.get(k) for k in fields}
    data.update(enabled=True,threshold=10,hold_seconds=HOLD,
                fresh=bool(state.get('updated') and 0<=now-state['updated']<=MAX_GAP and not state.get('error')))
    return data

def main():
    method=os.environ.get('REQUEST_METHOD','GET')
    if method!='GET':
        print('Status: 405 Method Not Allowed\r\nContent-Type: application/json\r\n\r\n{"error":"METHOD"}');return
    print('Content-Type: application/json; charset=utf-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n\r\n'+json.dumps(public(load())))

if __name__=='__main__':
    if sys.argv[1:]==['--tick'] and not os.environ.get('REQUEST_METHOD'):tick()
    else:main()

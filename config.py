"""Local configuration. Installing starts in read-only mode."""
import ipaddress,json,os,re,secrets,tempfile
from pathlib import Path
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
FLAGS=('heatpump','controls','schedule_controls','auto_pause','shelly')
DEFAULT=dict(server_host='',bsb_host='',bsb_port=80,bsb_username='',bsb_password='',timezone='Europe/Oslo',
             flags=dict(heatpump=True,controls=False,schedule_controls=False,auto_pause=False,shelly=False))
def host(value,optional=False):
    if optional and value=='':return ''
    if not isinstance(value,str) or not 1<=len(value)<=253:raise ValueError('ADDRESS')
    try:
        ip=ipaddress.ip_address(value)
        if ip.version!=4 or ip.is_multicast or ip.is_unspecified:raise ValueError('ADDRESS')
        return str(ip)
    except ValueError:
        if re.fullmatch(r'[0-9.]+',value):raise ValueError('ADDRESS')
        if not all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',p) for p in value.split('.')):raise ValueError('ADDRESS')
        return value.lower()
def validate(data,previous=None):
    if not isinstance(data,dict) or set(data)-set(DEFAULT):raise ValueError('CONFIG')
    flags=data.get('flags',{})
    if not isinstance(flags,dict) or set(flags)-set(FLAGS) or any(type(v)is not bool for v in flags.values()):raise ValueError('FLAGS')
    flags={k:flags.get(k,DEFAULT['flags'][k]) for k in FLAGS}
    if any(flags[k] for k in FLAGS if k not in ('heatpump','controls')) and not flags['controls']:raise ValueError('CONTROL_DEPENDENCY')
    if flags['controls'] and not flags['heatpump']:raise ValueError('CONTROL_DEPENDENCY')
    if not flags['heatpump']:raise ValueError('HEATPUMP_REQUIRED')
    port=data.get('bsb_port',80)
    if type(port)is not int or not 1<=port<=65535:raise ValueError('PORT')
    tz=data.get('timezone','Europe/Oslo')
    if not isinstance(tz,str):raise ValueError('TIMEZONE')
    try:ZoneInfo(tz)
    except (ZoneInfoNotFoundError,ValueError):raise ValueError('TIMEZONE')
    creds={}
    for k in ('bsb_username','bsb_password'):
        v=data.get(k,(previous or {}).get(k,''))
        # Blank password in the settings form preserves a saved credential.
        if k=='bsb_password' and v=='' and previous:v=previous.get(k,'')
        if not isinstance(v,str) or len(v)>256 or any(ord(c)<32 for c in v):raise ValueError('CREDENTIAL')
        creds[k]=v
    if ':' in creds['bsb_username']:raise ValueError('CREDENTIAL')
    return dict(server_host=host(data.get('server_host','')),bsb_host=host(data.get('bsb_host','')),bsb_port=port,timezone=tz,flags=flags,**creds)
def public(config):
    out=json.loads(json.dumps(config));out['bsb_password']='';out['has_password']=bool(config.get('bsb_password'));return out

def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

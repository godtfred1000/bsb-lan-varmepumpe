"""Accept this server's own addresses, including a newly assigned Tailscale IP."""
import json,socket,subprocess,time
_cache=(0,set())
def local_hosts():
    global _cache
    now=time.monotonic()
    if now-_cache[0]<2:return set(_cache[1])
    values={'127.0.0.1','localhost',socket.gethostname(),socket.gethostname()+'.local'}
    try:
        data=json.loads(subprocess.check_output(['ip','-j','-4','addr','show'],timeout=2,text=True,stderr=subprocess.DEVNULL))
        values.update(a['local'] for i in data for a in i.get('addr_info',[]) if a.get('family')=='inet')
    except (OSError,ValueError,subprocess.SubprocessError):
        try:values.update(socket.gethostbyname_ex(socket.gethostname())[2])
        except OSError:pass
    _cache=(now,values);return set(values)

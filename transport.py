"""Fixed, configured BSB endpoint. No redirects and no credentials in URLs or logs."""
import base64,json,os,re
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler,ProxyHandler
from urllib.error import HTTPError
from config import validate
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('BSB_REDIRECT_REFUSED')

def request(command,config=None):
    if config is None:config=validate(json.loads((Path(os.environ['BSB_DATA'])/'config.json').read_text()))
    # Controllers have a small, explicit write vocabulary. Never forward arbitrary URLs.
    read=bool(re.fullmatch(r'JQ=[0-9]+(?:\.[0-9]+)?(?:,[0-9]+(?:\.[0-9]+)?)*',command))
    manual=bool(re.fullmatch(r'S(?:700=[0-3]|710=(?:1[89]|2[0-8])(?:\.[0-9])?|10019=1)',command))
    pause=bool(re.fullmatch(r'S2843=(?:20|30)',command))
    shelly=bool(re.fullmatch(r'I10000=(?:[0-9]|[1-3][0-9]|40)(?:\.[0-9]+)?',command))
    schedule=bool(re.fullmatch(r'S(?:501(?:\.[1-6])?|642|643|648|700)=[A-Za-z0-9_%:.,#-]*',command))
    flags=config['flags']
    if not read:
        if not flags['controls']:raise ValueError('READ_ONLY')
        if manual:pass
        elif pause and flags['auto_pause']:pass
        elif shelly and flags['shelly'] and 0<=float(command.split('=')[1])<=40:pass
        elif schedule and flags['schedule_controls']:pass
        else:raise ValueError('PARAMETER_DISABLED')
    if not(read or manual or pause or shelly or schedule):raise ValueError('PARAMETER')
    if manual and command.startswith('S710=') and float(command.split('=')[1])>28:raise ValueError('VALUE')
    headers={}
    if config.get('bsb_username'):
        raw=(config['bsb_username']+':'+config.get('bsb_password','')).encode()
        headers['Authorization']='Basic '+base64.b64encode(raw).decode()
    opener=build_opener(ProxyHandler({}),NoRedirect())
    url='http://'+config['bsb_host']+':'+str(config['bsb_port'])+'/'+command
    with opener.open(Request(url,headers=headers),timeout=8) as response:
        body=response.read(1048577)
        if len(body)>1048576:raise ValueError('RESPONSE_SIZE')
        return body

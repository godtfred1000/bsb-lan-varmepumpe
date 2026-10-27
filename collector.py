"""Portable read-only logger using the existing Norwegian log field names."""
import json
import os
from datetime import datetime
from pathlib import Path
from transport import request
from config import atomic

FIELDS = [('Turtemp','8412',' C'),('Returtemp','8410',' C'),('Settpunkt','8411',' C'),
          ('Modulering','8413',' %'),('Temperaturdifferanse','8425',' C'),('Kompressorstarter','8451',''),
          ('Utetemperatur','8700',' C'),('Tanktemperatur','8830',' C'),('Ønsket romtemperatur','710',' C'),
          ('Stuetemperatur','8740',' C'),('Driftstatus','8006',''),('DHWstatus','8003',''),
          ('DHWtekst','8003','desc'),('Feil','6700',''),('Feiltekst','6700','desc'),
          ('Elvarme1','8402',''),('Elvarme2','8403',''),('Elvarme1kW','5811',''),('Elvarme2kW','5813','')]
PARAMS = sorted({'8400','642','643','700','2843','10018'} | {p for _,p,_ in FIELDS},key=int)

def query(config, parameters):
    value = json.loads(request('JQ='+','.join(parameters), config))
    if not isinstance(value,dict): raise ValueError('INVALID_RESPONSE')
    return value

def value(data, param, key='value'):
    item = data.get(param,{})
    if not isinstance(item,dict) or str(item.get('error','')) != '0': return '---'
    raw = item.get(key)
    if not isinstance(raw,(int,float,str)) or isinstance(raw,bool): return '---'
    return str(raw).replace('|',' ').replace('\r',' ').replace('\n',' ')[:300]

def line(data, now=None):
    compressor = {'0':'Av','1':'På'}.get(value(data,'8400'),'Ukjent')
    fields = ['Tidspunkt: '+(now or datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),'Kompressor: '+compressor]
    for label, param, suffix in FIELDS:
        fields.append(label+': '+value(data,param,'desc' if suffix=='desc' else 'value')+('' if suffix=='desc' else suffix))
    return ' | '.join(fields)+'\n'

def collect(config, root):
    data = query(config,PARAMS)
    # No response with missing compressor/counter data is converted into a false stop.
    if value(data,'8400') == '---' and value(data,'8451') == '---': raise ValueError('NO_MEASUREMENTS')
    root=Path(root); row=line(data)
    with (root/'log/bsb.log').open('a') as stream:
        stream.write(row); stream.flush(); os.fsync(stream.fileno())
    for file,params in [('holiday.json',['642','643']),('mode.json',['700']),('pause.json',['2843']),('dhw.json',['10018'])]:
        atomic(root/'web'/file,{p:data.get(p,{}) for p in params})
    if value(data,'6700') not in ('0','---'):
        with (root/'log/feil.log').open('a') as stream: stream.write(row)
    return row

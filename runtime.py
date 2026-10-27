"""Render only heat-pump source files. Data and credentials never go in the web root."""
from pathlib import Path
import shlex,sys,shutil
HERE=Path(__file__).resolve().parent

def render(config,data):
    data=Path(data).resolve();web=data/'web';runtime=data/'runtime';log=data/'log'
    for p in (web,runtime,log,data/'shelly'):
        p.mkdir(parents=True,exist_ok=True,mode=0o700)
    (log/'bsb.log').touch(exist_ok=True)
    for name in ('summer-profile','pause-auto'):
        (data/'controllers'/name/'private').mkdir(parents=True,exist_ok=True,mode=0o700)
    for p in (HERE/'web').iterdir():
        if p.is_file():shutil.copy2(p,web/p.name)
    for p in (HERE/'controllers').rglob('*.py'):
        target=runtime/p.relative_to(HERE/'controllers');target.parent.mkdir(parents=True,exist_ok=True,mode=0o700);shutil.copy2(p,target)
    cgi=web/'cgi-bin';cgi.mkdir(exist_ok=True,mode=0o700)
    def wrapper(name,command):
        p=cgi/name;p.write_text('#!/bin/sh\n'+command+'\n');p.chmod(0o700)
    py=shlex.quote(sys.executable)
    for name,script in [('summer-profile','service.py'),('pause-auto','controller.py'),('compressor-daily','stats.py')]:
        cmd='exec '+py+' '+shlex.quote(str(runtime/name/script))
        if name=='compressor-daily':cmd+=' 3< '+shlex.quote(str(log/'bsb.log'))
        wrapper(name,cmd)
    return web,runtime

#!/usr/bin/env python3
"""Restart after an atomic settings save; normal termination exits cleanly."""
import os,subprocess,sys,signal
from pathlib import Path
child=None
stopping=False
def stop(*args):
 global stopping
 stopping=True
 if child is not None:child.terminate()
for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,stop)
while not stopping:
 child=subprocess.Popen([sys.executable,str(Path(__file__).with_name('server.py'))])
 code=child.wait()
 if code!=0:sys.exit(code)

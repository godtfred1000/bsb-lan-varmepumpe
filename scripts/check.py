#!/usr/bin/env python3
"""Offline release checks. No connection to any real BSB-LAN."""
from pathlib import Path
import os,re,subprocess,sys,py_compile,tempfile
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
for p in ROOT.rglob('*.py'):
 if 'data' not in p.relative_to(ROOT).parts:py_compile.compile(str(p),doraise=True)
for test in ['test_controller.py','test_holiday.py','test_stats.py']:
 subprocess.run([sys.executable,str(ROOT/'tests'/test)],check=True)
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_server.py','-v'],check=True)
for p in [*(ROOT/'web').glob('*.js'),*(ROOT/'ui').glob('*.js')]:
 if __import__('shutil').which('node'):subprocess.run(['node','--check',str(p)],check=True)
for p in ROOT.rglob('*'):
 if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts or p.suffix not in ('.py','.js','.html','.md','.json'):continue
 s=p.read_text()
 if p.name!='check.py' and re.search(r'192\.168\.3\.(?:1|5|170)(?![0-9])|100\.102\.170\.34|Klostervegen8',s):
  raise SystemExit('House-specific data in '+str(p.relative_to(ROOT)))
 if p.suffix in ('.js','.html') and re.search('[\u0e00-\u0e7f]',s):raise SystemExit('Removed-language content in '+str(p))
print('PASS: syntax, offline controller and HTTP tests, and house-data/language checks')

#!/usr/bin/env python3
"""Native Raspberry Pi OS / Debian installer. Never contacts the heat pump."""
import datetime,os,pwd,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
INSTALL=Path('/opt/bsb-lan-varmepumpe')
DATA=Path('/var/lib/bsb-lan-varmepumpe')
UNIT=Path('/etc/systemd/system/bsb-lan-varmepumpe.service')
FILES=['server.py','run.py','collector.py','config.py','transport.py','network.py','runtime.py','web','ui','controllers']
SERVICE='''[Unit]
Description=BSB-LAN heat pump monitoring and opt-in controls
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=bsb-web
Group=bsb-web
WorkingDirectory=/opt/bsb-lan-varmepumpe
Environment=BSB_DATA=/var/lib/bsb-lan-varmepumpe
Environment=BSB_PORT=8088
ExecStart=/usr/bin/python3 /opt/bsb-lan-varmepumpe/server.py
Restart=always
RestartSec=2
UMask=0077
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/var/lib/bsb-lan-varmepumpe
[Install]
WantedBy=multi-user.target
'''
def main():
    if sys.version_info<(3,11):raise SystemExit('Python 3.11 or newer is required.')
    if sys.platform!='linux' or os.geteuid()!=0:raise SystemExit('Run sudo python3 install.py on Raspberry Pi OS / Debian.')
    if SOURCE==INSTALL:raise SystemExit('Run the installer from the newly downloaded source directory, not /opt.')
    if not shutil.which('systemctl'):raise SystemExit('This installer requires systemd.')
    for name in FILES:
        if not (SOURCE/name).exists():raise SystemExit('Missing source: '+name)
    if not INSTALL.exists():
        import socket
        with socket.socket() as s:
            try:s.bind(('0.0.0.0',8088))
            except OSError:raise SystemExit('Port 8088 is already used. Existing services were not changed.')
    existed=UNIT.exists()
    if existed:subprocess.run(['systemctl','stop','bsb-lan-varmepumpe'],check=True)
    backup=Path('/var/backups/bsb-lan-varmepumpe');backup.mkdir(parents=True,exist_ok=True,mode=0o700)
    if INSTALL.exists() or DATA.exists():
        dest=backup/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.tar.gz')
        with tarfile.open(dest,'w:gz') as f:
            for p in (INSTALL,DATA,UNIT):
                if p.exists():f.add(p,arcname=str(p).lstrip('/'))
        dest.chmod(0o600);print('Backup:',dest)
    try:account=pwd.getpwnam('bsb-web')
    except KeyError:
        subprocess.run(['useradd','--system','--home-dir',str(DATA),'--shell','/usr/sbin/nologin','bsb-web'],check=True);account=pwd.getpwnam('bsb-web')
    INSTALL.mkdir(exist_ok=True,mode=0o755);DATA.mkdir(exist_ok=True,mode=0o700)
    for name in FILES:
        src=SOURCE/name;dst=INSTALL/name
        if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        else:shutil.copy2(src,dst)
    for p in [DATA,*DATA.rglob('*')]:
        if p.is_symlink():continue
        os.chown(p,account.pw_uid,account.pw_gid);p.chmod(0o700 if p.is_dir() else 0o600)
    UNIT.write_text(SERVICE)
    subprocess.run(['systemctl','daemon-reload'],check=True)
    subprocess.run(['systemctl','enable','--now','bsb-lan-varmepumpe'],check=True)
    print('Installed. Open http://PI-ADDRESS:8088/setup/')
    print('Read setup key locally with: sudo cat /var/lib/bsb-lan-varmepumpe/setup-key')
if __name__=='__main__':main()

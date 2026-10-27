# Installation (English)

A standalone Raspberry Pi web interface for BSB-LAN. Languages: **Norwegian, German and English**.

The supplied parameter profile is for **Fujitsu Waterstage / Atlantic Alfea with a Siemens controller**. Other BSB-LAN installations may have different parameters. Monitoring and logging are enabled by default; every control feature is opt-in. Confirm the [parameter map](PARAMETERS.md) before enabling writes.

1. Use Raspberry Pi OS Bookworm or newer with Python 3.11+. Configure BSB-LAN separately and ensure the Pi can reach it.
2. Download this repository as ZIP, extract it on the Pi, open a terminal in that folder and run `sudo python3 install.py`.
3. Open `http://PI-ADDRESS:8088/setup/`. Read the setup key locally: `sudo cat /var/lib/bsb-lan-varmepumpe/setup-key`.
4. Enter your Pi hostname/IP, your BSB-LAN hostname/IP and its port (usually 80). Do not include `http://` or a path. Enter optional BSB-LAN Basic Authentication credentials and your IANA time zone. Leave controls disabled on the first run.
5. Save and wait for the service restart. Open `http://PI-ADDRESS:8088/`. Historical readings accumulate from now on.

The installer creates a dedicated system user and systemd service. No Docker or Node is needed. Updates back up the existing source and private data before replacing source files. Data, credentials and log history remain in `/var/lib/bsb-lan-varmepumpe/` and must never be uploaded to GitHub.

Optional controls use parameters 700, 710 and 10019. Summer/holiday control uses heating circuit 1, not individual rooms. The fixed summer windows are 05–08 and 16–19 every day. Automatic compressor pause uses 2843: 30 minutes above 10 °C and 20 minutes below 10 °C after 40 minutes of stable measurements. **40 minutes is the qualification period, not the selected pause.** Shelly is optional; its last fresh reading is forwarded every 120 seconds, with a maximum age of 7800 seconds.

Use a trusted LAN or VPN such as Tailscale. Do not expose port 8088 directly to the internet. Setup is key protected; enabled controls do not have separate user authentication. The Pi must stay powered for server schedules and sensor forwarding. If it stops, the heat pump retains its last mode. A new Tailscale address is accepted automatically once you open it; an old app bookmark is not automatically rediscovered.

Software tests use only a fake loopback BSB-LAN and synthetic data. This distribution has not been physically tested on other heat pump models. For a temporary run without installation, use `python3 run.py`; settings and logs are then stored in `data/`.

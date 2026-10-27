'use strict';
const langs=["no", "de", "en"];
const rows={
title:["Oppsett av varmepumpesiden", "Wärmepumpe einrichten", "Heat pump setup"],
intro:["Legg inn dine egne adresser. Status og logging er på; styring er av til du velger det.", "Eigene Adressen eingeben. Überwachung und Protokollierung sind aktiviert; die Steuerung bleibt bis zur Freigabe ausgeschaltet.", "Enter your own addresses. Monitoring and logging are enabled; controls remain off until you enable them."],
unlock:["Lås opp oppsettet", "Einstellungen entsperren", "Unlock settings"],
keyHelp:["Oppsettsnøkkelen står i data/setup-key på serveren. Nøkkelen lagres bare i denne fanen.", "Der Einrichtungsschlüssel steht in data/setup-key auf dem Server. Er bleibt nur in diesem Tab gespeichert.", "Find the setup key in data/setup-key on the server. It is kept only in this tab."],
key:["Oppsettsnøkkel", "Einrichtungsschlüssel", "Setup key"],connect:["Lås opp", "Entsperren", "Unlock"],
network:["Adresser og tidssone", "Adressen und Zeitzone", "Addresses and time zone"],
server:["Adressen til Raspberry Pi", "Adresse des Raspberry Pi", "Raspberry Pi address"],
bsb:["Adressen til BSB-LAN", "BSB-LAN-Adresse", "BSB-LAN address"],
port:["BSB-LAN-port", "BSB-LAN-Port", "BSB-LAN port"],timezone:["Tidssone", "Zeitzone", "Time zone"],
username:["BSB-LAN-brukernavn (valgfritt)", "BSB-LAN-Benutzername (optional)", "BSB-LAN username (optional)"],
password:["BSB-LAN-passord (tomt felt beholder lagret passord)", "BSB-LAN-Passwort (leer lassen, um das gespeicherte Passwort zu behalten)", "BSB-LAN password (leave blank to keep saved password)"],
addressHelp:["Skriv IP-adresse eller vertsnavn, uten http:// og uten portnummer. Tailscale-adresser følger Pi-en automatisk.", "IP-Adresse oder Hostname ohne http:// und Portnummer eingeben. Tailscale-Adressen folgen dem Pi automatisch.", "Enter an IP address or hostname, without http:// or a port number. Tailscale addresses follow the Pi automatically."],
services:["Funksjoner", "Funktionen", "Features"],
controls:["Aktiver manuelle knapper", "Manuelle Steuerung aktivieren", "Enable manual controls"],
schedule_controls:["Aktiver sommer- og ferieprogram", "Sommer- und Ferienprogramm aktivieren", "Enable summer and holiday schedules"],
auto_pause:["Aktiver automatisk kompressorpause", "Automatische Verdichterpause aktivieren", "Enable automatic compressor pause"],
shelly:["Send Shelly-romtemperatur til BSB-LAN", "Shelly-Raumtemperatur an BSB-LAN senden", "Send Shelly room temperature to BSB-LAN"],
controlHelp:["Aktiver styring bare når parametrene passer din varmepumpe. Automatisk pause bruker 2843: 30 minutter over 10 °C, 20 minutter under 10 °C, etter 40 minutters stabile målinger.", "Die Steuerung erst nach Prüfung der Wärmepumpenparameter aktivieren. Die automatische Pause verwendet 2843: 30 Minuten über 10 °C, 20 Minuten unter 10 °C, nach 40 Minuten stabiler Messwerte.", "Enable controls only after checking your heat pump parameters. Automatic pause uses 2843: 30 minutes above 10 °C, 20 minutes below 10 °C, after 40 minutes of stable readings."],
summerHelp:["Sommerprogrammet bruker varmekrets 1 kl. 05–08 og 16–19. Det velger ikke hvilke rom som får varme. Åpne gulvkurser bestemmer dette. Ferieprogrammet samordnes med sommerprogrammet.", "Das Sommerprogramm heizt Heizkreis 1 von 05–08 und 16–19 Uhr. Es wählt keine Räume aus; die geöffneten Heizkreise bestimmen dies. Ferien- und Sommerprogramm werden aufeinander abgestimmt.", "The summer schedule heats circuit 1 at 05–08 and 16–19. It does not select rooms; open heating loops determine this. Holiday and summer schedules are coordinated."],
shellyHelp:["Shelly er valgfritt. Når aktivert, vises en personlig webhook-adresse her. Siste ferske måling sendes hvert 2. minutt; målinger eldre enn 2 timer og 10 minutter sendes ikke.", "Shelly ist optional. Nach dem Aktivieren erscheint hier die persönliche Webhook-Adresse. Der letzte aktuelle Messwert wird alle 2 Minuten gesendet; Werte älter als 2 Stunden und 10 Minuten werden nicht gesendet.", "Shelly is optional. When enabled, your personal webhook URL appears here. The last fresh reading is forwarded every 2 minutes; readings older than 2 hours 10 minutes are not sent."],
save:["Lagre og start tjenesten på nytt", "Speichern und Dienst neu starten", "Save and restart service"],open:["Åpne varmepumpesiden", "Wärmepumpenseite öffnen", "Open heat pump page"],
saved:["Lagret. Tjenesten starter på nytt. Åpne varmepumpesiden om noen sekunder.", "Gespeichert. Der Dienst startet neu. Die Wärmepumpenseite in wenigen Sekunden öffnen.", "Saved. Service is restarting. Open the heat pump page in a few seconds."],
error:["Kunne ikke fullføre. Kontroller nøkkelen, adressene og funksjonsvalgene.", "Vorgang fehlgeschlagen. Schlüssel, Adressen und ausgewählte Funktionen prüfen.", "Could not complete. Check the key, addresses and selected features."]};
let language=localStorage.getItem('varmepumpe_sprak')||'no',key='';
if(!langs.includes(language))language='no';
const $=s=>document.querySelector(s),form=$('#settings');
function t(k){return rows[k][langs.indexOf(language)];}
for(const name of ['controls','schedule_controls','auto_pause','shelly']){const l=document.createElement('label');l.className='check';const c=document.createElement('input');c.type='checkbox';c.name=name;const span=document.createElement('span');span.dataset.t=name;l.append(c,span);$('#flags').append(l);}
function translate(){document.documentElement.lang=language==='no'?'nb':language;$('#language').value=language;document.querySelectorAll('[data-t]').forEach(n=>n.textContent=t(n.dataset.t));}
$('#language').onchange=()=>{language=$('#language').value;localStorage.setItem('varmepumpe_sprak',language);translate();};translate();
function deps(){const on=form.elements.controls.checked;for(const n of ['schedule_controls','auto_pause','shelly']){form.elements[n].disabled=!on;if(!on)form.elements[n].checked=false;}}
form.elements.controls.onchange=deps;
async function api(data){const r=await fetch('/setup/api/config',{method:data?'POST':'GET',headers:{'X-Setup-Key':key,...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{})});if(!r.ok)throw Error();return r.json();}
$('#connect').onclick=async()=>{key=$('#setup-key').value.trim();try{const d=await api(),c=d.config;for(const n of ['server_host','bsb_host','bsb_username','bsb_password','bsb_port','timezone'])form.elements[n].value=c[n]??'';if(!d.configured)form.elements.server_host.value=location.hostname;for(const n of ['controls','schedule_controls','auto_pause','shelly'])form.elements[n].checked=c.flags[n];deps();form.hidden=false;$('#login').hidden=true;$('#message').textContent='';if(d.shelly_url){$('#webhook').textContent=d.shelly_url;$('#webhook').hidden=false;}}catch{$('#message').textContent=t('error');key='';}};
form.onsubmit=async e=>{e.preventDefault();const data={};for(const n of ['server_host','bsb_host','bsb_username','bsb_password','timezone'])data[n]=form.elements[n].value.trim();data.bsb_password=form.elements.bsb_password.value;data.bsb_port=Number(form.elements.bsb_port.value);data.flags={heatpump:true};for(const n of ['controls','schedule_controls','auto_pause','shelly'])data.flags[n]=form.elements[n].checked;$('#save').disabled=true;try{await api(data);$('#message').textContent=t('saved');}catch{$('#message').textContent=t('error');}finally{$('#save').disabled=false;}};

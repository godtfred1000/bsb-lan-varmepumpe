(() => {
'use strict';
const root=document.querySelector('#compressor-daily');if(!root)return;
const languages=["no", "de", "en"];
const labels={
 details:["Om tallene", "Zu diesen Zahlen", "About these figures"],
 hours:["t", "Std.", "h"],
 minutes:["min", "Min.", "min"],
 title:["Kompressordrift per døgn", "Verdichterbetrieb pro Tag", "Daily compressor operation"],
 starts:["🟢 Starter i dag", "🟢 Starts heute", "🟢 Starts today"],
 stops:["🔴 Stopp i dag", "🔴 Stopps heute", "🔴 Stops today"],
 yesterday:["Starter i går", "Starts gestern", "Starts yesterday"],
 average:["Snitt kjøretid i dag", "Ø Laufzeit heute", "Average run time today"],
 note:["Snittet gjelder fullførte kjøringer som stoppet i dag. Pågående kjøring er ikke med. Startteller 8451 bekrefter starter; korte statusfall filtreres bort.", "Der Durchschnitt umfasst abgeschlossene Läufe, die heute endeten. Der aktuelle Lauf ist nicht enthalten. Zähler 8451 bestätigt Starts; kurze fehlerhafte Statusabfälle werden herausgefiltert.", "The average covers completed runs that stopped today. The current run is excluded. Counter 8451 confirms starts; brief status drops are filtered out."],
 waiting:["Ingen fullført kjøring ennå", "Noch kein abgeschlossener Lauf", "No completed run yet"],
 loading:["Leser døgnstatistikk …", "Tagesstatistik wird geladen …", "Loading daily statistics …"],
 failed:["Kunne ikke lese døgnstatistikken.", "Tagesstatistik konnte nicht gelesen werden.", "Could not read daily statistics."],
 partial:["Ufullstendig datagrunnlag. ≥ betyr minst dette antallet. Snittet bruker bare kjøringer med kjent start og stopp.", "Unvollständige Daten. ≥ bedeutet mindestens diese Anzahl. Der Durchschnitt berücksichtigt nur Läufe mit bekanntem Start und Stopp.", "Incomplete data. ≥ means at least this count. The average uses only runs with a known start and stop."],
 stale:["Loggen er ikke oppdatert. Tallene gjelder siste måling.", "Das Protokoll ist nicht aktuell. Die Zahlen beziehen sich auf die letzte Messung.", "The log is not up to date. Figures reflect the last sample."],
 pending:["Siste statusendring venter på bekreftelse.", "Die letzte Statusänderung wartet auf Bestätigung.", "The latest status change awaits confirmation."],
 updated:["Siste måling: ", "Letzte Messung: ", "Last sample: "]
};
let data=null,busy=false,failed=false;
function t(key){return labels[key][Math.max(0,languages.indexOf(document.querySelector('#language')?.value||'no'))];}
function dayKey(){const p=new Intl.DateTimeFormat('en-GB',{timeZone:data?.timezone||'Europe/Oslo',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());const v=k=>p.find(x=>x.type===k).value;return `${v('year')}-${v('month')}-${v('day')}`;}
function number(day,key){return day?.[key]==null?'—':(day.partial?'≥ ':'')+day[key];}
function duration(seconds){if(seconds==null)return '—';const minutes=Math.round(seconds/60);return minutes>=60?`${Math.floor(minutes/60)} ${t('hours')} ${minutes%60} ${t('minutes')}`:`${minutes} ${t('minutes')}`;}
function render(){
 root.querySelectorAll('[data-daily-text]').forEach(n=>n.textContent=t(n.dataset.dailyText));
 const valid=data?.today?.date===dayKey();
 root.querySelector('#daily-starts').textContent=valid?number(data.today,'starts'):'—';
 root.querySelector('#daily-stops').textContent=valid?number(data.today,'stops'):'—';
 root.querySelector('#daily-yesterday').textContent=valid?number(data.yesterday,'starts'):'—';
 root.querySelector('#daily-average').textContent=valid?duration(data.today.average_seconds):'—';
 const info=[];
 if(!valid)info.push(t(failed?'failed':'loading'));
 else{
  if(data.today.average_seconds==null)info.push(t('waiting'));
  if(data.today.partial||data.yesterday.partial)info.push(t('partial'));
  if(data.stale)info.push(t('stale'));else if(data.pending)info.push(t('pending'));
  if(data.last_sample)info.push(t('updated')+data.last_sample.slice(11));
 }
 root.querySelector('#daily-info').textContent=info.join(' ');
}
async function refresh(){
 if(busy||document.hidden)return;busy=true;
 try{
 const r=await fetch('/cgi-bin/compressor-daily?_='+Date.now(),{cache:'no-store',signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw Error('READ');const d=await r.json();
 if(!d.today||!d.yesterday)throw Error('DATA');data=d;failed=false;
 }catch(_){failed=true;data=null;}finally{busy=false;render();}
}
document.querySelector('#language')?.addEventListener('change',render);
document.addEventListener('visibilitychange',()=>{if(!document.hidden){render();refresh();}});
setInterval(refresh,30000);
setInterval(()=>{if(data?.today?.date!==dayKey()&&data){data=null;render();refresh();}},1000);
render();refresh();
})();

(() => {
'use strict';
const root=document.querySelector('#pausecontrol');if(!root)return;
const languages=["no", "de", "en"];
const texts={
 title:["⏱️ Automatisk kompressorpause", "⏱️ Automatische Verdichterpause", "⏱️ Automatic compressor pause"],
 rule:["Over 10 °C i 40 minutter → 30 min pause. Under 10 °C i 40 minutter → 20 min pause.", "Über 10 °C für 40 Minuten → 30 Min. Pause. Unter 10 °C für 40 Minuten → 20 Min. Pause.", "Above 10 °C for 40 minutes → 30 min pause. Below 10 °C for 40 minutes → 20 min pause."],
 current:["Minimumspause nå: {pause} min", "Aktuelle Mindestpause: {pause} Min.", "Current minimum pause: {pause} min"],
 last:["Sist bekreftet minimumspause: {pause} min", "Zuletzt bestätigte Mindestpause: {pause} Min.", "Last confirmed minimum pause: {pause} min"],
 outdoor:["Utetemperatur: {temperature} °C.", "Außentemperatur: {temperature} °C.", "Outdoor temperature: {temperature} °C."],
 matched:["Pausen passer temperaturen. Automatisk styring er aktiv.", "Die Pause passt zur Temperatur. Die automatische Steuerung ist aktiv.", "The pause matches the temperature. Automatic control is active."],
 above:["Over 10 °C: {elapsed} av 40 minutter. Bytter til 30 min når ventetiden er fullført.", "Über 10 °C: {elapsed} von 40 Minuten. Danach Wechsel auf 30 Min.", "Above 10 °C: {elapsed} of 40 minutes. Changes to 30 min when the wait is complete."],
 below:["Under 10 °C: {elapsed} av 40 minutter. Bytter til 20 min når ventetiden er fullført.", "Unter 10 °C: {elapsed} von 40 Minuten. Danach Wechsel auf 20 Min.", "Below 10 °C: {elapsed} of 40 minutes. Changes to 20 min when the wait is complete."],
 equal:["Akkurat 10 °C: gjeldende pause beholdes. Ventetiden starter på nytt når temperaturen går over eller under grensen.", "Genau 10 °C: Die aktuelle Pause bleibt erhalten. Die Wartezeit beginnt beim Über- oder Unterschreiten der Grenze neu.", "Exactly 10 °C: the current pause is retained. The wait restarts when the temperature goes above or below the threshold."],
 paused:["Måling mangler eller er for gammel. Lagret pause beholdes, og 40 minutters ventetid starter på nytt ved sikre målinger.", "Ein Messwert fehlt oder ist zu alt. Die gespeicherte Pause bleibt erhalten; die Wartezeit von 40 Minuten beginnt mit verlässlichen Messwerten neu.", "A reading is missing or too old. The saved pause is retained; the 40-minute wait restarts with reliable readings."],
 verify:["Endringen er ikke bekreftet. Automaten kontrollerer innstillingen ved neste måling.", "Die Änderung ist nicht bestätigt. Die Steuerung prüft die Einstellung beim nächsten Messwert.", "The change is not confirmed. The controller checks the setting at the next reading."],
 loading:["Leser automatisk pausestyring …", "Automatische Pausensteuerung wird gelesen …", "Reading automatic pause control …"],
 note:["Raspberry Pi styrer dette også når siden er lukket. Kryssing av temperaturgrensen, manglende målinger eller omstart nullstiller ventetiden. En kompressor som går, blir ikke stoppet av denne funksjonen.", "Raspberry Pi steuert dies auch bei geschlossener Webseite. Ein Grenzwertwechsel, fehlende Messwerte oder ein Neustart setzen die Wartezeit zurück. Diese Funktion stoppt keinen laufenden Verdichter.", "Raspberry Pi controls this even with the page closed. Crossing the threshold, missing readings or a restart resets the wait. This function does not stop a running compressor."]
};
let data=null,busy=false;
function t(key,args={}){return texts[key][Math.max(0,languages.indexOf(document.querySelector('#language')?.value||'no'))].replace(/\{(\w+)\}/g,(_,k)=>args[k]??'');}
function render(){
 root.querySelectorAll('[data-auto-pause-text]').forEach(n=>n.textContent=t(n.dataset.autoPauseText));
 const value=root.querySelector('#auto-pause-value'),status=root.querySelector('#auto-pause-state');
 if(!data){value.textContent='—';status.textContent=t('loading');return;}
 value.textContent=Number.isInteger(data.pause)?t(data.fresh?'current':'last',{pause:data.pause}):'—';
 if(!data.fresh){status.textContent=t(data.error==='VERIFY_FAILED'||data.error==='WRITE_FAILED'?'verify':'paused');return;}
 const temperature=Number(data.temperature).toLocaleString(document.querySelector('#language')?.value==='no'?'nb-NO':document.querySelector('#language')?.value||'en',{maximumFractionDigits:1});
 const message=data.phase==='equal'?'equal':data.phase==='matched'?'matched':data.side==='above'?'above':'below';
 status.textContent=t('outdoor',{temperature})+' '+t(message,{elapsed:Math.floor((data.elapsed||0)/60)});
}
async function refresh(){
 if(busy||document.hidden)return;busy=true;
 try{const r=await fetch('/cgi-bin/pause-auto?_='+Date.now(),{cache:'no-store',signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error();const d=await r.json();if(d.enabled!==true)throw Error();data=d;}
 catch(_){data={...data,fresh:false};}
 finally{busy=false;render();}
}
document.querySelector('#language')?.addEventListener('change',render);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
render();refresh();setInterval(refresh,30000);
})();

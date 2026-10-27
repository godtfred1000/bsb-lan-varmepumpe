(() => {
'use strict';
const root=document.querySelector('#summer-profile');if(!root)return;
const langs=["no", "de", "en"],rows={
 title:["☀️ Sommerprogram", "☀️ Sommerprogramm", "☀️ Summer programme"],
 schedule:["Alle dager: 05:00–08:00 og 16:00–19:00.", "Täglich: 05:00–08:00 und 16:00–19:00.", "Every day: 05:00–08:00 and 16:00–19:00."],
 note:["Romoppvarming i tidsrommene. Utenom: av med frostbeskyttelse. Varmtvann er uendret. Raspberry Pi-en må være på; bytte skjer innen omtrent ett minutt.", "Raumheizung in diesen Zeiträumen. Außerhalb: aus, mit Frostschutz. Warmwasser bleibt unverändert. Der Raspberry Pi muss eingeschaltet bleiben; das Umschalten dauert bis zu etwa einer Minute.", "Space heating during these periods. Outside: off with frost protection. Hot water is unchanged. The Raspberry Pi must stay on; switching takes up to about one minute."],
 apply:["Aktiver sommerprogram", "Sommerprogramm aktivieren", "Activate summer programme"],
 restore:["Avslutt og gjenopprett forrige oppsett", "Beenden und vorherige Einstellungen wiederherstellen", "End and restore previous settings"],
 active:["Sommerprogram aktivt – romoppvarming tillatt nå.", "Sommerprogramm aktiv – Raumheizung ist jetzt freigegeben.", "Summer programme active – space heating allowed now."],
 off:["Sommerprogram aktivt – romoppvarming av nå. Varmtvann er tilgjengelig.", "Sommerprogramm aktiv – Raumheizung ist jetzt aus. Warmwasser ist verfügbar.", "Summer programme active – space heating off now. Hot water is available."],
 MANUAL_CHANGE:["Sommerprogrammet er stoppet fordi innstillingene ble endret manuelt.", "Sommerprogramm gestoppt, weil Einstellungen manuell geändert wurden.", "Summer programme stopped because settings were changed manually."],
 TIMER_FAILED:["Tidsbyttet ble ikke bekreftet. Sommerprogrammet er stoppet. Kontroller driftsmodus.", "Die zeitgesteuerte Änderung wurde nicht bestätigt. Sommerprogramm gestoppt. Betriebsart prüfen.", "The timed change was not confirmed. Summer programme stopped. Check operating mode."],
 inactive:["Sommerprogram er ikke valgt.", "Kein Sommerprogramm ausgewählt.", "Summer programme is not selected."],
 loading:["Kontrollerer tidsprogram …", "Zeitprogramm wird geprüft …", "Checking schedule …"],
 busy:["Lagrer og kontrollerer innstillingene …", "Einstellungen werden gespeichert und geprüft …", "Saving and checking settings …"],
 failed:["Kunne ikke lese innstillingene. Prøv Oppdater.", "Einstellungen konnten nicht gelesen werden. Bitte aktualisieren.", "Could not read settings. Try Refresh."],
 CONFLICT:["Innstillingene er endret siden sist. Kontroller dem og trykk igjen.", "Die Einstellungen wurden seit der letzten Prüfung geändert. Bitte prüfen und erneut drücken.", "Settings changed since the last check. Review them and press again."],
 APPLY_FAILED_RESTORED:["Sommerprogrammet ble ikke bekreftet. Forrige oppsett er gjenopprettet.", "Das Sommerprogramm wurde nicht bestätigt. Die vorherigen Einstellungen wurden wiederhergestellt.", "The summer programme was not confirmed. The previous settings were restored."],
 APPLY_FAILED_CHECK:["Endringen ble ikke fullført. Kontroller tidsprogram og driftsmodus på varmepumpen før du prøver igjen.", "Die Änderung wurde nicht abgeschlossen. Zeitprogramm und Betriebsart der Wärmepumpe vor einem erneuten Versuch prüfen.", "The change did not complete. Check the heat pump schedule and operating mode before trying again."],
 uncertain:["Resultatet er ikke bekreftet. Kontroller status før du prøver igjen.", "Das Ergebnis ist nicht bestätigt. Vor einem erneuten Versuch den Status prüfen.", "The result is not confirmed. Check status before trying again."],
 BUSY:["En oppdatering pågår. Vent litt og prøv igjen.", "Eine Aktualisierung läuft. Bitte kurz warten und erneut versuchen.", "An update is in progress. Wait briefly and try again."]
};
Object.assign(rows,{
 holidayTitle:["🏖️ Ferieprogram", "🏖️ Ferienprogramm", "🏖️ Holiday programme"],
 holidayNote:["Ferie har prioritet over sommerprogrammets badetider. Ved hjemkomst gjenopptas sommerprogrammet eller forrige driftsmodus. Varmtvannsinnstillingene beholdes. Raspberry Pi-en må være på.", "Das Ferienprogramm hat Vorrang vor den Heizzeiten des Sommerprogramms. Nach der Rückkehr werden das Sommerprogramm oder die vorherige Betriebsart fortgesetzt. Warmwasser bleibt unverändert. Der Raspberry Pi muss eingeschaltet bleiben.", "Holiday takes priority over the summer heating periods. On return, the summer programme or previous operating mode resumes. Hot water settings are unchanged. The Raspberry Pi must stay on."],
 seasonLabel:["Velg ferieinnstilling", "Ferieneinstellung wählen", "Choose holiday setting"],
 summerHoliday:["☀️ Sommerferie – Protection", "☀️ Sommerferien – Schutzbetrieb", "☀️ Summer holiday – Protection"],
 winterHoliday:["❄️ Vinterferie – Reduced", "❄️ Winterferien – Reduziert", "❄️ Winter holiday – Reduced"],
 summerLevel:["Romoppvarming av hele ferien, med frostbeskyttelse. Ingen badetider.", "Raumheizung während der gesamten Ferien aus, mit Frostschutz. Keine Heizzeiten für Badezimmer.", "Space heating off throughout the holiday, with frost protection. No bathroom heating periods."],
 winterLevel:["Redusert romtemperatur hele ferien: {temp} °C (parameter 712). Temperaturen endres ikke.", "Reduzierte Raumtemperatur während der gesamten Ferien: {temp} °C (Parameter 712). Der Temperatursollwert bleibt unverändert.", "Reduced room temperature throughout the holiday: {temp} °C (parameter 712). The temperature setting is unchanged."],
 departureLabel:["Avreise – fra kl. 00:00", "Abreise – ab 00:00 Uhr", "Departure – from 00:00"],
 returnLabel:["Hjemkomst – vanlig drift fra kl. 00:00", "Rückkehr – Normalbetrieb ab 00:00 Uhr", "Return – normal operation from 00:00"],
 holidayOn:["Lagre ferieprogram", "Ferienprogramm speichern", "Save holiday programme"],
 holidayOff:["Avbryt ferie og gjenoppta vanlig drift", "Ferien beenden und Normalbetrieb fortsetzen", "Cancel holiday and resume normal operation"],
 holidayScheduled:["Ferie lagret: {start} → {end}. {season}.", "Ferien gespeichert: {start} → {end}. {season}.", "Holiday saved: {start} → {end}. {season}."],
 holidayActive:["Ferie aktiv: {start} → {end}. {season}. Sommerens badetider er satt på pause.", "Ferien aktiv: {start} → {end}. {season}. Die Badezimmer-Heizzeiten des Sommerprogramms sind ausgesetzt.", "Holiday active: {start} → {end}. {season}. Summer bathroom heating periods are paused."],
 holidayNone:["Ingen ferie lagret.", "Keine Ferien gespeichert.", "No holiday saved."],
 holidayExternal:["Et annet ferieprogram finnes på varmepumpen. Avbryt det før du lagrer et nytt her.", "In der Wärmepumpe ist bereits ein anderes Ferienprogramm hinterlegt. Dieses vor dem Speichern eines neuen Programms hier beenden.", "Another holiday programme exists on the heat pump. Cancel it before saving a new one here."],
 BAD_DATES:["Velg avreise fra i dag og hjemkomst etter avreise, innen de neste 365 dagene.", "Abreise ab heute und Rückkehr nach der Abreise wählen, innerhalb der nächsten 365 Tage.", "Choose departure today or later and return after departure, within the next 365 days."],
 holidayPaused:["Sommerprogrammet er satt på pause av ferieprogrammet.", "Sommerprogramm durch das Ferienprogramm ausgesetzt.", "Summer programme paused by the holiday programme."]
});
let value=null,received=0,busy=false,checking=false,message='loading',dirty=false,initialized=false;
const holiday=document.querySelector('#holiday-profile'),start=document.querySelector('#holidayStart'),end=document.querySelector('#holidayEnd'),season=document.querySelector('#holidaySeason');
function t(key,args={}){const lang=document.querySelector('#language')?.value||'no';return (rows[key]||rows.failed)[Math.max(0,langs.indexOf(lang))].replace(/\{(\w+)\}/g,(_,k)=>args[k]??'');}
function render(){
 root.querySelectorAll('[data-summer-text]').forEach(n=>n.textContent=t(n.dataset.summerText));
 holiday.querySelectorAll('[data-profile-text]').forEach(n=>n.textContent=t(n.dataset.profileText));
 const fresh=value&&Date.now()-received<90000,working=busy||value?.busy,h=value?.holiday||{},managed=!!h.enabled;
 const external=value?.holidayValues&&(value.holidayValues['642']!=='---'||value.holidayValues['643']!=='---')&&!managed;
 const button=root.querySelector('#summer-apply'),restore=root.querySelector('#summer-restore');
 button.disabled=working||checking||!fresh||!!value?.enabled||managed||external;
 button.setAttribute('aria-pressed',String(!!(fresh&&!working&&value.active)));button.classList.toggle('selected',!!(fresh&&!working&&value.active));
 restore.hidden=!value?.canRestore;restore.disabled=working||checking||!fresh||managed||external;
 root.querySelector('[role=status]').textContent=t(working?'busy':message||(fresh?(value.active?(value.phase==='holiday'?'holidayPaused':value.phase==='off'?'off':'active'):(rows[value.reason]?value.reason:'inactive')):'failed'));
 document.querySelector('#holidayOn').disabled=working||checking||!fresh||managed||external;
 document.querySelector('#holidayOff').disabled=working||checking||!fresh||!(managed||external);
 [start,end,season].forEach(n=>n.disabled=working||managed);
 document.querySelector('#holiday-level').textContent=t(season.value==='summer'?'summerLevel':'winterLevel',{temp:value?.reduced??'…'});
 document.querySelector('#holiday-status').textContent=t(working?'busy':message||(fresh?(managed?(h.phase==='active'?'holidayActive':'holidayScheduled'):(rows[h.reason]?h.reason:external?'holidayExternal':'holidayNone')):'failed'),{start:h.start,end:h.end,season:t(h.season==='summer'?'summerHoliday':'winterHoliday')});
}
async function read(){const r=await fetch('/cgi-bin/summer-profile?_='+Date.now(),{cache:'no-store',signal:AbortSignal.timeout(15000)});const d=await r.json();if(!r.ok||typeof d.active!=='boolean')throw Error();value=d;received=Date.now();if(!d.busy&&!dirty){const h=d.holiday||{};start.value=h.enabled?h.start:'';end.value=h.enabled?h.end:'';if(h.enabled)season.value=h.season;else if(!initialized)season.value=d.enabled?'summer':'winter';initialized=true;}}
async function refresh(){if(busy||checking||document.hidden)return;checking=true;try{await read();message=value.operation?.status==='error'?value.operation.error:'';}catch(_){value=null;message='failed';}finally{checking=false;render();if(value?.busy)setTimeout(refresh,1500);}}
async function run(action){
 if(busy||checking||!value)return;
 const payload=action==='holiday_apply'?{start:start.value,end:end.value,season:season.value}:{};
 busy=true;message='';const controls=[...document.querySelectorAll('#controls button')].map(n=>[n,n.disabled]);controls.forEach(([n])=>n.disabled=true);render();
 try{
  await read();
  const r=await fetch('/cgi-bin/summer-profile',{method:'POST',headers:{'Content-Type':'application/json'},cache:'no-store',signal:AbortSignal.timeout(115000),body:JSON.stringify({action,csrf:value.csrf,revision:value.revision,...payload})});
  const d=await r.json();if(!r.ok)throw Error(d.error||'uncertain');if(d.accepted!==true||!d.operation?.id)throw Error('uncertain');
  let complete=false;
  for(let attempt=0;attempt<120;attempt++){
   await new Promise(resolve=>setTimeout(resolve,1500));await read();
   if(value.operation?.id!==d.operation.id)throw Error('uncertain');
   if(value.operation.status==='error')throw Error(value.operation.error||'uncertain');
   if(value.operation.status==='done'){
    if(action==='apply'?!value.active:action==='restore'?value.enabled:action==='holiday_apply'?!value.holiday?.enabled:value.holiday?.enabled)throw Error('uncertain');
    complete=true;dirty=false;await read();break;
   }
  }
  if(!complete)throw Error('uncertain');message='';
 }catch(e){message=rows[e.message]?e.message:'uncertain';value=null;try{await read();}catch(_){} }
 finally{busy=false;controls.forEach(([n,disabled])=>n.disabled=disabled);render();}
}
root.querySelector('#summer-apply').addEventListener('click',()=>run('apply'));
root.querySelector('#summer-restore').addEventListener('click',()=>run('restore'));
document.querySelector('#holidayOn').addEventListener('click',()=>run('holiday_apply'));
document.querySelector('#holidayOff').addEventListener('click',()=>run('holiday_cancel'));
[start,end,season].forEach(n=>n.addEventListener('input',()=>{dirty=true;render();}));
document.querySelector('#language')?.addEventListener('change',render);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
render();refresh();setInterval(refresh,30000);
})();

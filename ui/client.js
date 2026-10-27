'use strict';
const rawFetch=window.fetch.bind(window);
window.fetch=(input,init)=>{if(typeof input==='string'&&/^\/bsb\/[SI]/.test(input)){init={...init,method:'POST',mode:'same-origin',headers:{...init?.headers,'X-KV8-Control':'1'}};}return rawFetch(input,init);};
document.addEventListener('DOMContentLoaded',async()=>{
 const flags=await rawFetch('/pi/config').then(r=>r.json()).then(d=>d.flags).catch(()=>({}));
 for(const id of ['summer-profile','holiday-profile']){const e=document.getElementById(id);if(e&&!flags.schedule_controls)e.hidden=true;}
 const pause=document.getElementById('pausecontrol');if(pause&&!flags.auto_pause)pause.hidden=true;
 for(const b of document.querySelectorAll('button[onclick]'))if(/setMode|changeTemp|\/bsb\/[SI]|bsbWrite/.test(b.getAttribute('onclick')))b.disabled=!flags.controls;
 const link=document.createElement('a');link.href='/setup/';link.textContent='⚙️';link.style.cssText='position:fixed;bottom:16px;right:16px;z-index:50;padding:10px 15px;background:#fff;color:#143f35;border-radius:50%;box-shadow:0 2px 12px #0003';
 const label=()=>{const i=Math.max(0,["no", "de", "en"].indexOf(document.querySelector('#language')?.value||localStorage.getItem('varmepumpe_sprak')||'no'));link.setAttribute('aria-label',["Oppsett", "Einstellungen", "Settings"][i]);};label();document.querySelector('#language')?.addEventListener('change',label);document.body.append(link);
});

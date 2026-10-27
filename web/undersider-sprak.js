/* Only visible text and canvas text. Log parsing and control code stay intact. */
(function () {
  "use strict";
  const langs = ["no", "de", "en"];
  let lang = "no";
  try { const saved = localStorage.getItem("varmepumpe_sprak"); if (langs.includes(saved)) lang = saved; } catch (_) {}
  const dictionary = [
["Varmepumpe – Feilhistorikk", "Wärmepumpe – Fehlerverlauf", "Heat pump – error history"],
["Laster feilhistorikk...", "Fehlerverlauf wird geladen...", "Loading error history..."],
["Ingen registrerte feil.", "Keine Fehler erfasst.", "No errors recorded."],
["Tidspunkt:", "Zeitpunkt:", "Timestamp:"],
["Kompressorstarter:", "Verdichterstarts:", "Compressor starts:"],
["Kompressor:", "Verdichter:", "Compressor:"],
["Turtemp:", "Vorlauftemperatur:", "Flow temperature:"],
["Returtemp:", "Rücklauftemperatur:", "Return temperature:"],
["Settpunkt:", "Sollwert:", "Setpoint:"],
["Temperaturdifferanse:", "Temperaturdifferenz:", "Temperature difference:"],
["Stuetemperatur:", "Wohnzimmertemperatur:", "Living room temperature:"],
["Utetemperatur:", "Außentemperatur:", "Outdoor temperature:"],
["Tanktemperatur:", "Speichertemperatur:", "Tank temperature:"],
["Ønsket romtemperatur:", "Gewünschte Raumtemperatur:", "Desired room temperature:"],
["Modulering:", "Modulation:", "Modulation:"],
["Feiltekst:", "Fehlertext:", "Error description:"],
["Driftstatus:", "Betriebsstatus:", "Operating status:"],
["DHWstatus:", "Warmwasserstatus:", "DHW status:"],
["DHWtekst:", "Warmwasserbeschreibung:", "DHW description:"],
["Elvarme1kW:", "Heizstab 1 kW:", "Heater 1 kW:"],
["Elvarme2kW:", "Heizstab 2 kW:", "Heater 2 kW:"],
["Elvarme1:", "Heizstab 1:", "Heater 1:"],
["Elvarme2:", "Heizstab 2:", "Heater 2:"],
    ["Elektriske varmeelementer", "Elektrische Heizstäbe", "Electric heaters"],
    ["Varmeelement", "Heizstab", "Electric heater"],
    ["aktiv ved første sikre måling", "bei der ersten gültigen Messung bereits aktiv", "active at first valid reading"],
    ["måling avbrutt", "Messung unterbrochen", "readings interrupted"],
    ["startet", "eingeschaltet", "switched on"],
    ["stoppet", "ausgeschaltet", "switched off"],
    ["Registrert driftstid:", "Erfasste Laufzeit:", "Recorded run time:"],
    ["Samlet registrert driftstid:", "Gesamte erfasste Laufzeit:", "Total recorded run time:"],
    ["Strømforbruk (estimat):", "Stromverbrauch (Schätzung):", "Electricity use (estimate):"],
    ["Samlet strømforbruk (estimat):", "Gesamter Stromverbrauch (Schätzung):", "Total electricity use (estimate):"],
    ["Konfigurert effekt:", "Konfigurierte Leistung:", "Configured power:"],
    ["Ukjent effekt", "Leistung unbekannt", "Unknown power"],
    ["Ukjent", "Unbekannt", "Unknown"],
    ["Status ved siste måling:", "Status bei der letzten Messung:", "Status at last reading:"],
    ["Siste måling:", "Letzte Messung:", "Last reading:"],
    ["Aktiv periode ved siste måling", "Aktive Laufzeit bei der letzten Messung", "Active period at last reading"],
    ["Ingen registrerte elementmålinger ennå.", "Noch keine Heizstab-Messwerte erfasst.", "No heater readings recorded yet."],
    ["Ufullstendig periode – bare observerte intervaller er med.", "Unvollständiger Zeitraum – nur beobachtete Intervalle werden berücksichtigt.", "Incomplete period – only observed intervals are included."],
    ["Ufullstendig – effekt mangler for deler av perioden.", "Unvollständig – für einen Teil des Zeitraums fehlt die Leistung.", "Incomplete – power is missing for part of the period."],
    ["Strømforbruket er et estimat fra konfigurert effekt og registrert driftstid, ikke en strømmåling. Intervaller over 120 sekunder og manglende status utelates. Korte innkoblinger mellom målinger kan mangle.", "Der Stromverbrauch wird aus konfigurierter Leistung und erfasster Laufzeit geschätzt, nicht gemessen. Intervalle über 120 Sekunden und fehlende Statuswerte werden ausgelassen. Kurze Einschaltungen zwischen Messungen können fehlen.", "Electricity use is estimated from configured power and recorded run time, not metered. Intervals over 120 seconds and missing status are excluded. Brief activations between readings may be missed."],
    ["Varmtvannsoppvarming startet", "Warmwasserbereitung gestartet", "Hot water heating started"],
    ["Varmtvannsoppvarming ferdig", "Warmwasserbereitung beendet", "Hot water heating complete"],
    ["← Tilbake til Varmepumpe", "← Zurück zur Wärmepumpe", "← Back to heat pump"],
    ["← Tilbake til varmepumpa", "← Zurück zur Wärmepumpe", "← Back to heat pump"],
    ["Kompressorlogg", "Verdichterprotokoll", "Compressor log"],
    ["Temperaturkurver", "Temperaturverläufe", "Temperature graphs"],
    ["Vis alle målinger", "Alle Messwerte anzeigen", "Show all readings"],
    ["Vis bare start/stopp", "Nur Starts/Stopps anzeigen", "Show only starts/stops"],
    ["Laster logg...", "Protokoll wird geladen...", "Loading log..."],
    ["Ingen start/stopp-hendelser funnet.", "Keine Start/Stopp-Ereignisse gefunden.", "No start/stop events found."],
    ["Avriming ferdig", "Abtauung beendet", "Defrost complete"],
    ["Avriming startet", "Abtauung gestartet", "Defrost started"],
    ["Kompressor startet", "Verdichter gestartet", "Compressor started"],
    ["Kompressor stoppet", "Verdichter gestoppt", "Compressor stopped"],
    ["Varighet:", "Dauer:", "Duration:"],
    ["Pausetid:", "Pausenzeit:", "Pause time:"],
    ["Kjøretid:", "Laufzeit:", "Run time:"],
    ["Feil", "Fehler", "Error"],
    ["PÅ", "EIN", "ON"],
    ["AV", "AUS", "OFF"],
    ["Tur", "Vorlauf", "Flow"],
    ["Retur", "Rücklauf", "Return"],
    ["Sett", "Sollwert", "Setpoint"],
    ["Stue", "Raum", "Room"],
    ["Ute", "Außen", "Outdoor"],
    ["Tank", "Speicher", "Tank"],
    ["Mod", "Modulation", "Modulation"],
    ["6 timer", "6 Stunden", "6 hours"],
    ["24 timer", "24 Stunden", "24 hours"],
    ["7 dager", "7 Tage", "7 days"],
    ["30 dager", "30 Tage", "30 days"],
    ["Ikke nok loggdata ennå.", "Noch nicht genügend Protokolldaten vorhanden.", "Not enough log data yet."],
    ["Kunne ikke lese loggen.", "Protokoll konnte nicht gelesen werden.", "Could not read the log."],
    [" t ", " Std. ", " h "],
    [" min", " Min.", " min"],
    [" sek", " Sek.", " sec"]
  ];
  const entries = new Map(dictionary.map(row => [row[0], row]));
  const escape = s => s.replace(/[.*+?^$\{\}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(dictionary.map(row => row[0]).sort((a,b)=>b.length-a.length).map(escape).join("|"), "g");
  const translate = raw => String(raw).replace(regex, key => entries.get(key)[langs.indexOf(lang)]);
  const states = new WeakMap();
  function paintNode(node) {
    if (!node.parentElement || node.parentElement.closest("script,style,#subpage-language-control")) return;
    const current = node.nodeValue;
    let state = states.get(node);
    if (!state || current !== state.rendered) {
      state = {raw: current, rendered: current};
      states.set(node, state);
    }
    const rendered = translate(state.raw);
    state.rendered = rendered;
    if (node.nodeValue !== rendered) node.nodeValue = rendered;
  }
  function paintTree(root) {
    if (root.nodeType === Node.TEXT_NODE) return paintNode(root);
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    if (root.nodeType === Node.ELEMENT_NODE && root.closest("script,style,#subpage-language-control")) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) paintNode(walker.currentNode);
  }
  const originalTitle = document.title;
  let emptyCanvas = null;
  const fillText = CanvasRenderingContext2D.prototype.fillText;
  const fillRect = CanvasRenderingContext2D.prototype.fillRect;
  function legendSlot(context) {
    return Math.min(75, Math.max(1, (context.canvas.clientWidth - 63) / 5));
  }
  CanvasRenderingContext2D.prototype.fillRect = function (x,y,w,h) {
    if (y === 8 && w === 16 && h === 4 && x >= 48) {
      x = 48 + ((x - 48) / 75) * legendSlot(this);
    }
    return fillRect.call(this,x,y,w,h);
  };
  CanvasRenderingContext2D.prototype.fillText = function (text, ...args) {
    const raw = String(text);
    if (raw === "Ikke nok loggdata ennå." || raw === "Kunne ikke lese loggen.") {
      emptyCanvas = {context: this, raw, args};
    } else if (entries.has(raw)) emptyCanvas = null;
    if (["Tur","Retur","Ute","Tank","Stue"].includes(raw) && args[1] === 14) {
      const slot = legendSlot(this);
      args[0] = 48 + ((args[0] - 69) / 75) * slot + 19;
      args[2] = Math.max(1,slot - 22);
      // The original renderer leaves textAlign from the date ticks behind.
      const align = this.textAlign;
      this.textAlign = "left";
      const result = fillText.call(this,translate(raw),...args);
      this.textAlign = align;
      return result;
    }
    return fillText.call(this, translate(raw), ...args);
  };
  function redrawChart() {
    // Call the existing renderer with its current selection; do not parse data.
    if (typeof window.showHours !== "function") return;
    if (emptyCanvas) {
      const {context,raw,args} = emptyCanvas;
      context.clearRect(0,0,context.canvas.width,context.canvas.height);
      context.fillText(raw,...args);
      return;
    }
    const button = document.querySelector(".controls button.active");
    const match = button && button.getAttribute("onclick").match(/showHours\((\d+),/);
    if (match) window.showHours(Number(match[1]),button);
  }
  function paint() {
    paintTree(document.body);
    document.title = translate(originalTitle);
    document.documentElement.lang = lang === "no" ? "nb" : lang;
  }
  function init() {
    const control = document.createElement("div");
    control.id = "subpage-language-control";
    control.style.cssText = "text-align:right;max-width:900px;margin:0 auto 12px";
    const chooser = document.createElement("select");
    chooser.id = "subpage-language";
    chooser.style.cssText = "padding:10px;border-radius:8px;font-size:15px";
    chooser.setAttribute("aria-label","Norsk / Deutsch / English");
    ["🇳🇴 Norsk", "🇩🇪 Deutsch", "🇬🇧 English"].forEach((name,i) => {
      const option = document.createElement("option");
      option.value = langs[i]; option.textContent = name; chooser.append(option);
    });
    chooser.value = lang;
    control.append(chooser); document.body.prepend(control);
    chooser.addEventListener("change",()=> {
      lang = langs.includes(chooser.value) ? chooser.value : "no";
      try { localStorage.setItem("varmepumpe_sprak",lang); } catch (_) {}
      paint(); redrawChart();
    });
    window.addEventListener("storage",event => {
      if (event.key !== "varmepumpe_sprak" || !langs.includes(event.newValue)) return;
      lang=event.newValue;chooser.value=lang;paint();redrawChart();
    });
    paint();
    new MutationObserver(records => {
      for(const record of records) {
        if(record.type === "characterData") {
          const state=states.get(record.target);
          if(!state || record.target.nodeValue!==state.rendered)paintNode(record.target);
        } else for(const node of record.addedNodes) paintTree(node);
      }
    }).observe(document.body,{subtree:true,childList:true,characterData:true});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});
  else init();
})();

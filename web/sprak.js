/* Presentation only. No BSB requests, control values or log writes. */
(function () {
  "use strict";
  const languages = ["no", "de", "en"];
  const storageKey = "varmepumpe_sprak";
  const rows = {
    pauseFailed: ["Kunne ikke bekrefte endringen. Prøv Oppdater.", "Die Änderung konnte nicht bestätigt werden. Bitte aktualisieren.", "Could not confirm the change. Try Refresh."],
    pauseUnknown: ["Minimumspause er ikke bekreftet.", "Die Mindestpause ist nicht bestätigt.", "Minimum off time is not confirmed."],
    pauseSending: ["Sender og kontrollerer innstillingen …", "Einstellung wird gesendet und geprüft …", "Sending and verifying the setting …"],
    pauseUnit: ["min", "Min.", "min"],
    pauseCurrent: ["Gjeldende minimumspause: ", "Aktuelle Mindestpause: ", "Current minimum off time: "],
    homeBack: ["← Varmepumpe", "← Wärmepumpe", "← Varmepumpe"],
    settings: ["⚙️ Innstillinger", "⚙️ Einstellungen", "⚙️ Settings"],
    title: ["🔥 Varmepumpe Fujitsu", "🔥 Fujitsu-Wärmepumpe", "🔥 Fujitsu heat pump"],
    refresh: ["🔄 Oppdater", "🔄 Aktualisieren", "🔄 Refresh"],
    compressor: ["Kompressor", "Verdichter", "Compressor"],
    status: ["Varmepumpestatus", "Wärmepumpenstatus", "Heat pump status"],
    flow: ["Tur", "Vorlauf", "Flow"],
    return: ["Retur", "Rücklauf", "Return"],
    setpoint: ["Settpunkt", "Sollwert", "Setpoint"],
    room: ["Stuetemperatur", "Wohnzimmertemperatur", "Living room temperature"],
    tank: ["Tanktemperatur", "Speichertemperatur", "Tank temperature"],
    outdoor: ["Utetemperatur", "Außentemperatur", "Outdoor temperature"],
    starts: ["Starter", "Starts", "Starts"],
    modulation: ["Modulering", "Modulation", "Modulation"],
    desired: ["Ønsket romtemperatur", "Gewünschte Raumtemperatur", "Desired room temperature"],
    mode: ["Driftsmodus", "Betriebsart", "Operating mode"],
    auto: ["Auto", "Automatik", "Auto"],
    comfort: ["Komfort", "Komfort", "Comfort"],
    reduced: ["Redusert", "Reduziert", "Reduced"],
    protection: ["Frostsikring", "Frostschutz", "Frost protection"],
    pause: ["⏱️ Kompressorpause", "⏱️ Verdichterpause", "⏱️ Compressor pause"],
    winter: ["❄️ Vinter – 20 min", "❄️ Winter – 20 Min.", "❄️ Winter – 20 min"],
    summer: ["☀️ Sommer – 30 min", "☀️ Sommer – 30 Min.", "☀️ Summer – 30 min"],
    dhw: ["🚿 Varmtvann", "🚿 Warmwasser", "🚿 Hot water"],
    dhwNow: ["🚿 Varm opp tappevann nå", "🚿 Warmwasser jetzt aufheizen", "🚿 Heat domestic hot water now"],
    dhwHeating: ["🔥 Varmer tappevann", "🔥 Warmwasser wird aufgeheizt", "🔥 Heating domestic hot water"],
    dhwStarted: ["✓ Varmtvannsoppvarming startet", "✓ Warmwasserbereitung gestartet", "✓ Hot water heating started"],
    holiday: ["🏖️ Ferie", "🏖️ Ferien", "🏖️ Holiday"],
    noHoliday: ["Ingen ferie aktiv", "Keine Ferien aktiv", "No active holiday"],
    departure: ["Avreise", "Abreise", "Departure"],
    arrival: ["Hjemkomst", "Rückkehr", "Return date"],
    holidayOn: ["Aktiver ferie", "Ferien aktivieren", "Activate holiday"],
    holidayOff: ["Avbryt ferie", "Ferien abbrechen", "Cancel holiday"],
    graphs: ["📈 Temperaturkurver", "📈 Temperaturverläufe", "📈 Temperature graphs"],
    logs: ["Vis hele loggen", "Vollständiges Protokoll anzeigen", "View full log"],
    errors: ["Vis feilhistorikk", "Fehlerverlauf anzeigen", "View error history"],
    footer: ["Styring av varmepumpe Fujitsu Waterstage", "Steuerung der Fujitsu Waterstage Wärmepumpe", "Fujitsu Waterstage heat pump control"],
    author: ["Bygget av Hansen IT Support", "Erstellt von Hansen IT Support", "Created by Hansen IT Support"],
    activeMode: ["Aktiv modus: ", "Aktive Betriebsart: ", "Active mode: "],
    loading: ["Leser...", "Wird geladen...", "Loading..."],
    holidaySet: ["Ferie satt: ", "Ferien eingestellt: ", "Holiday set: "],
    cancelled: ["Ferie avbrutt", "Ferien abgebrochen", "Holiday cancelled"],
    selectDates: ["Velg både avreise og hjemkomst", "Abreise und Rückkehr auswählen", "Select both departure and return dates"],
    dateOrder: ["Hjemkomst må være etter avreise", "Die Rückkehr muss nach der Abreise liegen", "Return must be after departure"],
    modeSet: ["Driftsmodus satt til ", "Betriebsart eingestellt auf ", "Operating mode set to "],
    until: [" til ", " bis ", " to "],
    on: ["På", "Ein", "On"],
    off: ["Av", "Aus", "Off"],
    noError: ["Ingen feil", "Kein Fehler", "No error"],
    error: ["Feil ", "Fehler ", "Error "],
    defrost: ["Avriming", "Abtauung", "Defrosting"],
    defrostDone: ["Avriming ferdig", "Abtauung beendet", "Defrost complete"],
    standby: ["Standby / Frostsikring", "Bereitschaft / Frostschutz", "Standby / Frost protection"]
  };
  let lang = "no";
  let index = 0;
  const source = new WeakMap();
  const dynamicSelector = "#komp, #feil, #aktivmodus, #holidayStatus, #dhwButton, #pauseStatus";
  const t = key => rows[key][index];
  const aliases = {
    Automatic: "auto", Auto: "auto", Comfort: "comfort", Komfort: "comfort",
    Reduced: "reduced", Redusert: "reduced", Protection: "protection",
    Frostsikring: "protection", "Standby / Frostsikring": "standby"
  };
  function modeName(value) {
    return aliases[value] ? t(aliases[value]) : value;
  }
  function translateDynamic(id, raw) {
    if (id === "pauseStatus") {
      for (const key of ["pauseSending", "pauseUnknown", "pauseFailed"]) if (raw === rows[key][0]) return t(key);
      const match = raw.match(/^Gjeldende minimumspause: (\d+) min$/);
      if (match) return t("pauseCurrent") + match[1] + " " + t("pauseUnit");
    }
    if (id === "komp") {
      return raw === "På" ? t("on") : raw === "Av" ? t("off") : raw;
    }
    if (id === "aktivmodus" && raw.startsWith("Aktiv modus: ")) {
      const value = raw.slice("Aktiv modus: ".length);
      return t("activeMode") + (value === "Leser..." ? t("loading") : modeName(value));
    }
    if (id === "holidayStatus") {
      if (raw === "Ingen ferie aktiv") return t("noHoliday");
      const match = raw.match(/^(🏖️ )?Ferie satt: (.*)$/);
      if (match) return (match[1] || "") + t("holidaySet") + match[2];
    }
    if (id === "dhwButton") {
      for (const key of ["dhwNow", "dhwHeating", "dhwStarted"]) {
        if (raw === rows[key][0] || raw === rows[key][0] + "!") {
          return t(key) + (raw.endsWith("!") ? "!" : "");
        }
      }
    }
    if (id === "feil") {
      for (const key of ["noError", "defrostDone", "defrost"]) {
        if (raw === rows[key][0]) return t(key);
      }
      if (raw.startsWith("Feil ")) {
        // Keep error codes and technical descriptions exactly as reported.
        return t("error") + raw.slice(5);
      }
    }
    return raw;
  }
  function paintDynamic(el, forceCapture) {
    const current = el.textContent;
    let state = source.get(el);
    if (!state || forceCapture || current !== state.rendered) {
      state = { raw: current, rendered: current };
      source.set(el, state);
    }
    const translated = translateDynamic(el.id, state.raw);
    state.rendered = translated;
    if (current !== translated) el.textContent = translated;
    rememberText(el);
  }
  function paintStatic(el) {
    const key = el.getAttribute("data-i18n");
    if (rows[key] && el.textContent !== t(key)) el.textContent = t(key);
  }
  function paint() {
    document.querySelectorAll("[data-i18n]").forEach(paintStatic);
    document.querySelectorAll(dynamicSelector).forEach(el => paintDynamic(el, false));
    document.title = t("title").replace(/^🔥 /, "");
    document.documentElement.lang = lang === "no" ? "nb" : lang;
  }
  function translateMessage(raw) {
    raw = String(raw);
    for (const key of ["selectDates", "dateOrder", "cancelled"]) {
      if (raw === rows[key][0]) return t(key);
    }
    if (raw.startsWith(rows.modeSet[0])) {
      return t("modeSet") + modeName(raw.slice(rows.modeSet[0].length));
    }
    const match = raw.match(/^Ferie satt: (\d{4}-\d{2}-\d{2}) til (\d{4}-\d{2}-\d{2})$/);
    if (match) return t("holidaySet") + match[1] + t("until") + match[2];
    return raw;
  }
  function init() {
    const chooser = document.getElementById("language");
    if (!chooser) return;
    try {
      const saved = localStorage.getItem(storageKey);
      if (languages.includes(saved)) lang = saved;
    } catch (_) { /* Translation still works when storage is blocked. */ }
    index = languages.indexOf(lang);
    chooser.value = lang;
    chooser.setAttribute("aria-label", "Norsk / Deutsch / English");
    chooser.addEventListener("change", function () {
      lang = languages.includes(chooser.value) ? chooser.value : "no";
      index = languages.indexOf(lang);
      try { localStorage.setItem(storageKey, lang); } catch (_) {}
      paint();
    });
    const nativeAlert = window.alert.bind(window);
    window.alert = function (message) { return nativeAlert(translateMessage(message)); };
    // Existing update() compatibility: it may call oversettSide after a refresh.
    window.oversettSide = paint;
    paint();
    const observer = new MutationObserver(records => {
      const dynamic = new Map();
      const staticNodes = new Set();
      for (const record of records) {
        const target = record.target.nodeType === Node.ELEMENT_NODE
          ? record.target : record.target.parentElement;
        if (!target || target.closest("script, style, #language")) continue;
        const field = target.closest(dynamicSelector);
        if (field) {
          // A producer replaces textContent with a NEW text node. Capture even
          // when the fresh Norwegian text equals the previous translation.
          const producerWrite = record.type === "childList" &&
            Array.from(record.addedNodes).some(node => !ownTextNodes.has(node));
          dynamic.set(field, (dynamic.get(field) || false) || producerWrite);
        }
        const label = target.closest("[data-i18n]");
        if (label) staticNodes.add(label);
        if (record.type === "childList") {
          for (const node of record.addedNodes) {
            if (node.nodeType !== Node.ELEMENT_NODE) continue;
            if (node.matches(dynamicSelector)) dynamic.set(node, true);
            node.querySelectorAll(dynamicSelector).forEach(el => dynamic.set(el, true));
            if (node.matches("[data-i18n]")) staticNodes.add(node);
            node.querySelectorAll("[data-i18n]").forEach(el => staticNodes.add(el));
          }
        }
      }
      dynamic.forEach((force, el) => {
        paintDynamic(el, force);
        rememberText(el);
      });
      staticNodes.forEach(paintStatic);
    });
    document.querySelectorAll(dynamicSelector).forEach(rememberText);
    observer.observe(document.body, {subtree: true, childList: true, characterData: true});
  }
  const ownTextNodes = new WeakSet();
  function rememberText(el) {
    for (const node of el.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) ownTextNodes.add(node);
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, {once: true});
  } else init();
})();

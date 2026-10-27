# Parameterprofil

Denne versjonen har én fast parameterprofil for Fujitsu Waterstage / Atlantic Alfea med Siemens-regulator. Det finnes ikke automatisk identifikasjon eller en universell parameteroversetter.

| Parameter | Bruk | Tilgang |
|---|---|---|
| 8400 | Kompressor på/av | Lesing |
| 8410 / 8412 | Retur / tur | Lesing |
| 8411 / 8413 / 8425 | Settpunkt / modulering / temperaturdifferanse | Lesing |
| 8451 | Kumulativ kompressorstartteller | Lesing |
| 8700 / 8740 / 8830 | Ute / rom / tanktemperatur | Lesing |
| 8006 / 8003 / 6700 | Drift / varmtvann / feil | Lesing |
| 8402 / 8403 | Elektriske varmeelementers driftsstatus | Lesing |
| 5811 / 5813 | Konfigurert kW per element, ikke driftsstatus | Lesing |
| 700 | Driftsmodus 0–3 | Valgfri skriving |
| 710 | Romtemperatur 18–28 °C | Valgfri skriving |
| 10018 / 10019 | Varmtvannsstatus / start av oppvarming | Lesing / valgfri skriving |
| 2843 | Minimum kompressorpause, 20 eller 30 min | Valgfri automatikk |
| 501 / 501.1–501.6 | Ukeprogram varmekrets 1 | Valgfritt sommerprogram |
| 642 / 643 / 648 | Ferie start/slutt og nivå | Valgfritt ferieprogram |
| 712 | Redusert romtemperatur (beholdes) | Lesing |
| I10000 | Innrapportering av romtemperatur som vises i 8740 | Valgfri Shelly |

Ukjente eller ugyldige målinger logges som `---`/`Ukjent`, aldri som en sikker av-status. Statistikken bruker persistente starttellerendringer og filtrerer korte statusfall. Kompressorstopp bekreftes først etter minst 120 sekunder med gyldige målinger. Manglende historikk gir `≥` eller ukjente tall; ingen historikk konstrueres.

Elforbruk vises som estimat, ikke strømmåling. Lange hull eller manglende effekt/status tas ikke med. Korte elementaktiveringer mellom målinger kan mangle.

Dette prosjektet dokumenterer sin egen parameterbruk. Din BSB-LANs parameterbeskrivelser og regulatorens dokumentasjon må bekrefte at den samme profilen gjelder før styring aktiveres.

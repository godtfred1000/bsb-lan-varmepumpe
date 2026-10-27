# Shelly H&T (valgfritt)

1. Legg Shelly på samme nettverk som Pi-en og verifiser at den rapporterer temperatur.
2. I varmepumpesidens oppsett: aktiver manuelle kontroller og «Send Shelly-romtemperatur til BSB-LAN». Lagre, vent på omstart og lås opp oppsettet igjen.
3. Kopier den personlige webhook-adressen som vises. Den inneholder en nøkkel. Del den ikke offentlig.
4. I Shelly-innstillingene oppretter du en temperaturhandling/webhook. Bruk adressen og Shellys temperaturvariabel `${ev.tC}`. Dette er den uttrykksformen som er brukt med H&T Gen3; kontroller variabelstøtten i din firmware.
5. Verifiser at romtemperatur 8740 følger en ny måling. Tjenesten skriver via `I10000` bare når dette er aktivert.

Pi-en videresender den siste gyldige målingen ved mottak og deretter hvert 120. sekund. Den ber ikke Shelly måle på nytt hvert 120. sekund. H&T Gen3 på USB sender vanligvis med flere minutters mellomrom; på batteri kan det gå inntil omtrent to timer. Målinger må være 0–40 °C og maksimalt 7800 sekunder gamle.

Webhook-adressen må bruke Pi-ens lokale adresse, slik at Shelly kan nå den uten Tailscale. Ved endring av lokal Pi-adresse må handlingen i Shelly oppdateres. Det er ingen automatisk endring av Shelly-konfigurasjonen.

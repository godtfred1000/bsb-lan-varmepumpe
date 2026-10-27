# BSB-LAN Varmepumpe

En selvstendig varmepumpeside for **Raspberry Pi og BSB-LAN**, bygget av Hansen IT Support. Ingen avhengighet til andre smarthustjenester, brukerkontoer i skyen eller en bestemt ruter.

**Språk: Norsk · Deutsch · English.** [English installation guide](docs/INSTALL-EN.md) · [Deutsche Anleitung](docs/INSTALL-DE.md)

## Hva får du?

- Status, temperaturer og logger som oppdateres automatisk.
- Temperaturkurver med panorering og zoom på mobil og PC.
- Kompressorstarter og stopp per kalenderdøgn, kontrollert mot startteller 8451. Korte falske stopp og avriming filtreres i døgnstatistikken.
- El-element 1 og 2: start, stopp, driftstid og **estimert** kWh basert på registrert driftstid og konfigurert effekt.
- Valgfrie knapper for driftsmodus, romtemperatur og varmtvannsoppvarming.
- Valgfritt samordnet sommer- og ferieprogram.
- Valgfri automatisk minimum kompressorpause, med 40 minutters kvalifisering.
- Valgfri Shelly H&T-romtemperatur sendt til BSB-LAN hvert 2. minutt så lenge målingen er fersk.
- Et oppsettsskjema der du legger inn dine egne adresser. Ingen private adresser, nøkler eller historiske målinger følger med.

## Passer det min varmepumpe?

Første versjon bruker **parameteroppsettet fra Fujitsu Waterstage / Atlantic Alfea med Siemens-regulator**. BSB-LAN alene betyr ikke at alle parametrene er like. Andre regulatorer kan mangle funksjoner eller bruke andre parametre. Kontroller [parameteroversikten](docs/PARAMETERS.md) mot din BSB-LAN før du aktiverer styring.

**Ny installasjon er bare status og logging.** Installasjonen skriver ingen innstillinger til varmepumpen. Manuell styring, sommer/ferie, automatisk pause og Shelly må velges i oppsettet. Det følger ikke med noen aktiv sommerplan, ferieperiode eller romtemperatur fra en annen bolig.

## Enkel installasjon på Raspberry Pi

Du trenger Raspberry Pi OS Bookworm eller nyere, Python 3.11+, nettverk og en ferdig konfigurert BSB-LAN som kan nås fra Pi-en. Prosjektet installerer ikke BSB-LAN-firmware.

1. Last ned repoet som ZIP: **Code → Download ZIP** på GitHub. Pakk ut på Pi-en.
2. Åpne Terminal i den utpakkede mappen og kjør:

   ```sh
   sudo python3 install.py
   ```

3. Åpne `http://PI-ADRESSE:8088/setup/` i nettleseren.
4. Finn oppsettsnøkkelen med:

   ```sh
   sudo cat /var/lib/bsb-lan-varmepumpe/setup-key
   ```

5. Lim inn nøkkelen i skjemaet. Legg inn Pi-adresse, BSB-LAN-adresse og eventuelt BSB-LAN-brukernavn/passord. La styring være av første gang. Trykk **Lagre og start tjenesten på nytt**.
6. Åpne `http://PI-ADRESSE:8088/`. Første måling kommer normalt innen omtrent 30 sekunder. Historikk bygges opp fra installasjonstidspunktet.

Installasjonen bruker en egen systembruker `bsb-web`, starter automatisk etter omstart og kontrollerer at port 8088 er ledig ved førstegangsinstallasjon. Ingen Docker, Node eller skyabonnement er nødvendig for drift.

## Før styring aktiveres

Kontroller parametrene i din egen BSB-LAN. Innstillinger uten støtte blir ikke universelt gjort kompatible av dette prosjektet.

- **Manuelle knapper:** driftsmodus 700, romtemperatur 710 (18–28 °C), varmtvannsstart 10019. Skriv tilgang må være tillatt i BSB-LAN.
- **Sommer/ferie:** varmekrets 1 og parametrene 501, 501.1–501.6, 642, 643, 648 og 700 må passe regulatoren. Tidene er 05–08 og 16–19 hver dag. Programmet velger ikke bad eller rom; åpne gulvkurser/romstyringen avgjør hvor varmen går. Varmtvannsinnstillingene endres ikke. Pi-en må være på for de tidsstyrte byttene.
- **Automatisk pause:** 2843 må støtte 20 og 30 minutter. Over 10 °C ute sammenhengende i 40 minutter velges 30 minutter; under 10 °C i 40 minutter velges 20. Nøyaktig 10 °C beholder innstillingen. **40 minutter er kvalifiseringstiden, ikke kompressorpausen.** Omstart, målefeil og brudd starter kvalifiseringen på nytt.
- **Shelly:** støtten er valgfri; du kan bruke varmepumpesiden uten en Shelly-sensor. Se [Shelly-veiledningen](docs/SHELLY.md).

## Tilgang fra mobilen

Bruk Pi-ens lokale IP-adresse hjemme. Med Tailscale på Pi og telefon kan du åpne Pi-ens Tailscale-adresse med port 8088. Prosjektet installerer eller endrer ikke Tailscale.

Alle varmepumpelenker er relative. Tjenesten godtar Pi-ens aktuelle nettverksadresser, inkludert en ny Tailscale-adresse. Dette oppdaterer **ikke automatisk et gammelt bokmerke eller adressen i en separat mobilapp**. Har selve inngangsadressen endret seg, må du åpne den nye adressen eller bruke et vertsnavn som virker i ditt nettverk.

Dette er en tjeneste for et betrodd lokalnett/VPN. Oppsettsnøkkelen beskytter innstillinger; vanlig visning og aktiverte styringsknapper har ikke egen brukerinnlogging. Ikke videresend port 8088 direkte til internett.

## Oppdatering, sikkerhetskopi og gjenoppretting

Kjør `sudo python3 install.py` fra en ny nedlastet kildekopi. Eksisterende kode, konfigurasjon og logg sikkerhetskopieres til `/var/backups/bsb-lan-varmepumpe/` før oppdatering. Installereren beholder data i `/var/lib/bsb-lan-varmepumpe/`.

Den private datamappen inneholder passord, oppsettsnøkkel, webhook-nøkkel, kontrollertilstand og historikk. Kopier den sikkert til din egen backup; legg den aldri på GitHub. Se [drift og gjenoppretting](docs/OPERATIONS.md), særlig før bytte til en annen BSB-LAN.

## Prøve uten installasjon

Python 3.11+ på Linux/macOS:

```sh
python3 run.py
```

Åpne `http://localhost:8088/setup/`. Nøkkelen ligger i `data/setup-key`. Ingen systemtjenester eller ruterinnstillinger endres. For andre porter: `BSB_PORT=8188 python3 run.py`.

## Tester

```sh
python3 scripts/check.py
```

Testene bruker bare en simulert BSB-LAN på loopback og syntetiske målinger. De tester blant annet skrivebegrensninger, innlogging til oppsett, feilaktig Origin, nøkkelbeskyttet Shelly-webhook, gamle målinger, loggformat, dobbeltelling, falske stopp, avriming, midnatt, sommertid, sommer/ferie og endret Tailscale-adresse. Nettlesertester kjøres separat med Playwright; se `tests/browser.cjs`.

Dette er en videreutvikling av en løsning brukt på en Fujitsu/Atlantic-installasjon. Denne distribusjonsversjonen er testet med simulert utstyr, og er ikke fysisk verifisert på andre varmepumper.

MIT-lisens. Uoffisielt prosjekt, ikke et produkt fra Fujitsu, Atlantic, Siemens eller BSB-LAN.

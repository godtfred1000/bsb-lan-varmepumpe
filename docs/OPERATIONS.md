# Drift

- Kode: `/opt/bsb-lan-varmepumpe/`
- Private data og historikk: `/var/lib/bsb-lan-varmepumpe/`
- Tjeneste: `bsb-lan-varmepumpe.service`
- Visning og oppsett: port 8088. Ingen andre serverporter trengs.
- Samplingsmål: 30 sekunder. Nettverksfeil kan gi hull; hull blir ikke oppdiktede målinger.
- Sommer/ferie og automatisk pause vurderes hvert minutt. Shelly videresendes hvert 120. sekund når aktivert og fersk.

Se tjenestestatus med `systemctl status bsb-lan-varmepumpe` og tjenesteloggen med `journalctl -u bsb-lan-varmepumpe`. Tjenesten logger ikke passord eller webhook-URL-er.

## Om Pi-en slås av

Varmepumpens egen regulator fortsetter med sist lagrede innstillinger. Pi-ens logging, Shelly-videresending og tidsstyrte bytter stopper. Dette er særlig viktig når sommerprogrammet bruker Protection/Automatic: den sist valgte modusen blir stående til regulatoren eller en bruker endrer den. Aktiver derfor bare slik styring når du kjenner konsekvensene av at serveren kan falle ut.

## Oppdatering

Installereren stopper eksisterende prosjektjeneste og tar en privat `.tar.gz`-backup av kode, enhetsfil og data. Den erstatter kun prosjektets egne kildefiler og starter tjenesten igjen. Den endrer ikke nginx, ruter, Wi-Fi, Tailscale eller varmepumpen under installasjonen. Hvis eksisterende automatikker allerede var aktivert, fortsetter de etter oppstart med lagret konfigurasjon.

## Ny varmepumpe / annen BSB-LAN

Bytt aldri et aktivt kontrollsystem til en annen pumpe med gamle programmer. Slå først av sommer/ferie og andre automatikker, og kontroller varmepumpens aktuelle driftsmodus. Bytt deretter BSB-adresse i oppsettet. Kontroller at styring er deaktivert før den nye profilen testes.

Tjenesten arkiverer automatisk pause- og sommerkonfigurasjon når det registrerte BSB-målet endres, slik at en gammel aktiv plan ikke følger med. Historiske loggdata slettes ikke automatisk; bruk en ny datamappe for å unngå å blande starttellere fra to forskjellige pumper.

## Gjenoppretting

Stopp tjenesten. Ta en kopi av nåværende data før gjenoppretting. Pakk ut den valgte private backupen med administratorrettigheter til de opprinnelige stiene. Last systemd på nytt og start tjenesten. Bekreft nettverksadresse, parameterprofil og hvilke automatikker som var aktivert i backupen før start. Gjenoppretting av eldre innstillinger er en aktiv handling; ikke kjør gamle og nye kontroller parallelt.

## Begrensninger

Dette er et enkelt lokalt webgrensesnitt, ikke et system med brukerkontoer eller tilgangsroller. Bare oppsettsendringer krever oppsettsnøkkel. Manuelle knapper som du har aktivert, kan brukes av andre som har tilgang til siden. Bruk et betrodd nett/VPN.

HTTP Basic Authentication til BSB-LAN er valgfritt. Passord ligger kun i privat konfigurasjon og vises ikke fra API. Det er ikke implementert støtte for et ekstra BSB-LAN-passordsegment i URL-stien eller egendefinerte proxybaner. Alle tidsberegninger bruker valgt IANA-tidssone. En mobil som bruker en annen tidssone, kan presentere grafens datomerking lokalt; døgnstatistikken beregnes på serveren.

Loggene roteres ikke automatisk i første versjon. Følg med på ledig lagringsplass og ta sikkerhetskopier av `log/bsb.log`. Graf og full logg laster historikken; forsiden leser bare siste komplette linje. Loggen holdes utenfor Git.

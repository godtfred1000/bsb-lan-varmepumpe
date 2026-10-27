# Installation (Deutsch)

Eigenständige Raspberry-Pi-Weboberfläche für BSB-LAN. Sprachen: **Norwegisch, Deutsch und Englisch**.

Das mitgelieferte Parameterprofil ist für **Fujitsu Waterstage / Atlantic Alfea mit Siemens-Regler** ausgelegt. Andere BSB-LAN-Anlagen können andere Parameter haben. Überwachung und Protokollierung sind standardmäßig aktiv, sämtliche Steuerungsfunktionen zunächst aus. Vor dem Freischalten die [Parameterübersicht](PARAMETERS.md) mit dem eigenen Regler vergleichen.

1. Raspberry Pi OS Bookworm oder neuer mit Python 3.11+ verwenden. BSB-LAN separat einrichten und die Erreichbarkeit vom Pi prüfen.
2. Dieses Repository als ZIP herunterladen, auf dem Pi entpacken und im entpackten Verzeichnis `sudo python3 install.py` ausführen.
3. `http://PI-ADRESSE:8088/setup/` öffnen. Den Einrichtungsschlüssel lokal lesen: `sudo cat /var/lib/bsb-lan-varmepumpe/setup-key`.
4. Eigene Pi-Adresse, BSB-LAN-Adresse und Port (normalerweise 80) eingeben. Keine URL-Pfade und kein `http://` eintragen. Optional Benutzername/Passwort für BSB-LAN Basic Authentication und eine IANA-Zeitzone eingeben. Die Steuerung beim ersten Start ausgeschaltet lassen.
5. Speichern, den Dienstneustart abwarten und `http://PI-ADRESSE:8088/` öffnen. Historische Daten werden ab jetzt gesammelt.

Der Installer legt einen eigenen Systembenutzer und einen systemd-Dienst an. Docker und Node sind nicht erforderlich. Updates sichern vorhandenen Code und private Daten, bevor Quelldateien ersetzt werden. Einstellungen, Passwörter und Protokolle bleiben in `/var/lib/bsb-lan-varmepumpe/` und gehören nicht auf GitHub.

Die optionalen manuellen Knöpfe verwenden 700, 710 und 10019. Sommer-/Feriensteuerung gilt für Heizkreis 1, nicht für einzelne Räume. Die festen Sommerzeiten sind täglich 05–08 und 16–19 Uhr. Die automatische Verdichterpause verwendet 2843: 30 Minuten bei über 10 °C, 20 Minuten bei unter 10 °C, jeweils nach 40 Minuten stabilen Messwerten. **Die 40 Minuten sind die Bestätigungszeit, nicht die Verdichterpause.** Shelly ist optional; der letzte aktuelle Messwert wird alle 120 Sekunden gesendet, bei höchstens 7800 Sekunden Alter.

Nur im vertrauenswürdigen LAN/VPN, etwa Tailscale, betreiben. Port 8088 nicht direkt ins Internet weiterleiten. Einrichtungsschlüssel schützen die Einstellungen; freigegebene Steuerungsknöpfe haben keine zusätzliche Benutzeranmeldung. Für Zeitprogramme und Sensorweiterleitung muss der Pi laufen. Bei Ausfall behält die Wärmepumpe die letzte Betriebsart. Eine neue Tailscale-Adresse wird beim Öffnen akzeptiert; alte App-Lesezeichen werden nicht automatisch neu gefunden.

Die Softwaretests verwenden ausschließlich eine simulierte BSB-LAN auf Loopback und künstliche Messwerte. Diese Distributionsversion wurde nicht an anderen Wärmepumpenmodellen physisch geprüft. Zum vorübergehenden Testen ohne Installation `python3 run.py` starten; Daten liegen dann in `data/`.

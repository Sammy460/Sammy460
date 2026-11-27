# PhoneDeck – altes Handy als Stream-Deck für den PC

Das Handy hängt per USB am PC und zeigt große Buttons (Apps starten, Media-Tasten, Hotkeys …).

- **PC aus** → USB-Strom weg → Handy wartet kurz und **schaltet sich komplett aus** (Root nötig).
- **PC an** → USB-Strom da → Handy **bootet von selbst** → PhoneDeck öffnet sich sofort.

```
pc-server/   Python-Server für den PC (Buttons in deck.json)
android/     Android-App (Kiosk-Vollbild, Strom-Wächter, Autostart)
handy-tools/ Skripte fuer Auto-Boot beim Einstecken (Root/Magisk)
```

## 1. PC (Windows)

1. Python installieren (python.org, Haken bei „Add to PATH“).
2. `pc-server/autostart_einrichten.bat` doppelklicken. Danach startet der Server bei jedem PC-Start automatisch.
3. Einmal von Hand starten: `python pc-server\server.py`. Die angezeigte IP merken.
4. Windows-Firewall-Abfrage: **Privates Netzwerk erlauben**.

Buttons änderst du in `pc-server/deck.json`. Änderungen gelten sofort nach dem nächsten Laden am Handy.

| `type`   | Feld      | Beispiel |
|----------|-----------|----------|
| `url`    | `target`  | `"https://youtube.com"`, `"steam://open/main"` |
| `open`   | `target`  | `"C:\\Programme\\OBS\\obs64.exe"` oder eine Datei |
| `run`    | `command` | `"explorer"`, `"shutdown /s /t 0"` |
| `hotkey` | `keys`    | `"ctrl+shift+m"`, `"volume mute"`, `"play/pause media"` |
| `text`   | `text`    | `"gg wp"` |
| `multi`  | `actions` | Liste von Aktionen nacheinander |

## 2. Handy

1. APK holen: GitHub → **Actions** → „Android APK bauen“ → neuester Lauf → Artifact **PhoneDeck-apk**. Entpacken und `app-debug.apk` auf dem Handy installieren.
2. App öffnen. Die PC-IP und den Port `8765` eintragen. Handy und PC müssen im selben WLAN sein.
3. In den Einstellungen die Punkte 1–4 abarbeiten. Bei Punkt 4 wählst du PhoneDeck als Startbildschirm, dann öffnet es nach jedem Boot garantiert.
4. Den Haken bei „Handy ausschalten, wenn PC-Strom weg ist“ setzen.

Einstellungen später: das **⚙ oben rechts lange drücken**.

## 3. Komplett aus/an – was dafür nötig ist

Ohne diese drei Punkte funktioniert der automatische Aus-/An-Zyklus nicht. Android-Apps können das Handy sonst weder ausschalten noch einschalten.

**a) Root (zum Ausschalten).** Das Handy muss gerootet sein (z.B. Magisk). Bei „Root testen“ den Magisk-Dialog mit „Erlauben“ bestätigen. Ohne Root bleibt das Handy an. Der Bildschirm geht dann nur normal aus und beim Einstecken wieder an.

**b) Auto-Boot beim Einstecken (zum Einschalten).** Normal zeigt ein ausgeschaltetes Handy beim Laden nur das Akku-Symbol. Umstellen:
- Pixel, Motorola, manche Xiaomi/OnePlus: Handy in den Bootloader starten, dann am PC:
  `fastboot oem off-mode-charge 0`
  Rückgängig: `fastboot oem off-mode-charge 1`
- Andere Geräte (gerootet): ein Magisk-Modul „auto boot on charge“ für dein Modell suchen. Es ersetzt die Lade-Animation durch einen Neustart.

**c) PC muss USB-Strom wirklich abschalten.** Viele PCs liefern auch ausgeschaltet noch Strom an USB. Dann merkt das Handy nichts. Abhilfe:
- Im BIOS **„ErP“ / „EuP“ aktivieren** oder „USB Power in S5“ / „USB Charging“ deaktivieren.
- Windows: „Schnellstart“ deaktivieren (Systemsteuerung → Energieoptionen → „Auswählen, was beim Drücken des Netzschalters geschehen soll“).
- Sonst einen anderen USB-Port probieren (oft liefern die hinteren Ports keinen Strom mehr).

**Tipp:** Keine Bildschirmsperre (PIN/Muster) auf dem Handy setzen. Sonst wartet es nach dem Boot auf die Entsperrung.

## Anleitung Redmi 9A (MIUI 12, Android 10)

> ⚠️ Beim Entsperren des Bootloaders (Schritt 2) wird das Handy **komplett gelöscht**. Mach vorher ein Backup.

1. **Vorbereiten:** Am Handy unter Einstellungen → Über das Telefon 7× auf „MIUI-Version“ tippen. Dann unter Zusätzliche Einstellungen → Entwickleroptionen „OEM-Entsperrung“ und „USB-Debugging“ einschalten. Unter „Mi-Entsperrstatus“ deinen Mi-Account verknüpfen (dafür muss die SIM aktiv sein).
2. **Bootloader entsperren:** Das Handy im Fastboot-Modus starten (aus, dann Lautstärke runter + Power halten). Am PC das offizielle **Mi Unlock Tool** ausführen. Meist verlangt es eine Wartezeit von 168 Stunden. Danach das Tool erneut starten und entsperren.
3. **Root mit Magisk:** Die Fastboot-ROM `12.0.18.0.QCDEUXM` für „dandelion“ (Redmi 9A, EEA) herunterladen und daraus die `boot.img` nehmen. Die Datei aufs Handy kopieren und in der **Magisk-App** mit Installieren → Datei patchen bearbeiten. Die gepatchte Datei zurück auf den PC kopieren, dann im Fastboot-Modus:
   ```
   fastboot flash boot magisk_patched-XXXX.img
   fastboot reboot
   ```
4. **Auto-Boot beim Einstecken:** Den Ordner `handy-tools/` nach `/sdcard/phonedeck/` aufs Handy kopieren. Dann am PC:
   ```
   adb shell su -c sh /sdcard/phonedeck/autoboot_einrichten.sh
   ```
   Das Skript sichert die Boot-Partition nach `/sdcard/phonedeck/boot_backup.img`. **Kopier dieses Backup auf den PC.** Danach fügt es per Magisk `overlay.d` eine Regel ein: Startet das Handy im Lade-Modus, bootet es stattdessen normal.
   Falls das Handy danach nicht mehr startet: im Fastboot-Modus `fastboot flash boot boot_backup.img` ausführen.
5. **MIUI-Extras für die App:** In der App „Sicherheit“ → Autostart → PhoneDeck einschalten. Unter Einstellungen → Apps → PhoneDeck → Energiesparmodus „Keine Einschränkungen“ wählen. In der App-Übersicht PhoneDeck mit dem Schloss-Symbol sperren.

## Ablauf

```
PC fährt runter ─► USB-Strom weg ─► App wartet 15 s (einstellbar) ─► su reboot -p ─► Handy aus
PC startet      ─► USB-Strom an  ─► Handy bootet (off-mode-charge 0) ─► PhoneDeck startet
                                    └► zeigt „Warte auf PC …“, bis der Server läuft ─► Buttons
```

Kommt der Strom innerhalb der Wartezeit zurück (z.B. beim PC-Neustart), wird das Ausschalten abgebrochen.

## Ohne WLAN, nur USB (optional)

Mit aktivem USB-Debugging am PC `adb reverse tcp:8765 tcp:8765` ausführen. In der App dann die IP `127.0.0.1` eintragen. Nach jedem Boot muss der Befehl erneut laufen, darum ist WLAN einfacher.

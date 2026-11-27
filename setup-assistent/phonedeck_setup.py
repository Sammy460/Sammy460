"""PhoneDeck Einrichtungs-Assistent (Windows).

Fuehrt Schritt fuer Schritt durch: Werkzeuge laden, Handy pruefen,
Bootloader entsperren, Root (Magisk), Auto-Boot, App installieren, PC-Autostart.
"""

import io
import json
import os
import queue
import shutil
import socket
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
import webbrowser
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---------------------------------------------------------------- Pfade

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

TOOLS = APP_DIR / "tools"
PT = TOOLS / "platform-tools"
ADB = PT / "adb.exe"
FASTBOOT = PT / "fastboot.exe"
MAGISK_APK = TOOLS / "Magisk.apk"
BACKUP_DIR = APP_DIR / "backup"


def find(*names):
    """Sucht eine Datei/Ordner neben der EXE oder im Repo (Entwicklung)."""
    for base in (APP_DIR, APP_DIR.parent, APP_DIR.parent / "pc-server"):
        for n in names:
            p = base / n
            if p.exists():
                return p
    return None


PLATFORM_TOOLS_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
MAGISK_API = "https://api.github.com/repos/topjohnwu/Magisk/releases/latest"
MI_UNLOCK_URL = "https://en.miui.com/unlock/download_en.html"
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
PKG = "de.phonedeck"

# ---------------------------------------------------------------- Helfer

log_q = queue.Queue()


def log(msg=""):
    log_q.put(str(msg))


def run(cmd, timeout=120, check=False):
    log("> " + " ".join(str(c) for c in cmd))
    try:
        p = subprocess.run(
            [str(c) for c in cmd], capture_output=True, text=True,
            timeout=timeout, creationflags=NO_WINDOW,
        )
    except FileNotFoundError:
        raise RuntimeError("Werkzeug fehlt – zuerst Schritt 1 ausfuehren.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Zeitueberschreitung.")
    out = (p.stdout + p.stderr).strip()
    if out:
        log(out)
    if check and p.returncode != 0:
        raise RuntimeError(f"Befehl fehlgeschlagen (Code {p.returncode}).")
    return p.returncode, out


def adb(*args, **kw):
    return run([ADB, *args], **kw)


def shell(cmd, **kw):
    return adb("shell", cmd, **kw)[1]


def fastboot(*args, **kw):
    return run([FASTBOOT, *args], **kw)


def download(url, dest):
    log(f"Lade {url} …")
    req = urllib.request.Request(url, headers={"User-Agent": "PhoneDeck-Setup"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    Path(dest).write_bytes(data)
    log(f"  {len(data) // 1024} KB gespeichert.")
    return data


def require_device():
    _, out = adb("devices")
    lines = [l for l in out.splitlines()[1:] if l.strip()]
    if not lines:
        raise RuntimeError("Kein Handy gefunden. USB-Kabel und USB-Debugging pruefen.")
    if "unauthorized" in lines[0]:
        raise RuntimeError("Am Handy die USB-Debugging-Abfrage bestaetigen ('Immer erlauben').")
    if "device" not in lines[0]:
        raise RuntimeError("Handy nicht bereit: " + lines[0])


def wait_fastboot(seconds=90):
    log("Warte auf Fastboot-Modus …")
    end = time.time() + seconds
    while time.time() < end:
        _, out = fastboot("devices", timeout=15)
        if "fastboot" in out:
            return
        time.sleep(3)
    raise RuntimeError("Handy nicht im Fastboot-Modus. Treiber installiert? (Mi Unlock bringt ihn mit)")


def has_root():
    return "uid=0" in shell("su -c id", timeout=40)


def pc_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return ""


def ask(title, text):
    """Ja/Nein-Dialog aus einem Hintergrund-Thread."""
    result = queue.Queue()
    root.after(0, lambda: result.put(messagebox.askyesno(title, text)))
    return result.get()


def info(title, text):
    done = queue.Queue()
    root.after(0, lambda: done.put(messagebox.showinfo(title, text)))
    done.get()


def pick_file(title, types):
    result = queue.Queue()
    root.after(0, lambda: result.put(filedialog.askopenfilename(title=title, filetypes=types)))
    return result.get()

# ---------------------------------------------------------------- Schritte


def step_tools():
    TOOLS.mkdir(exist_ok=True)
    if not ADB.exists():
        data = download(PLATFORM_TOOLS_URL, TOOLS / "pt.zip")
        zipfile.ZipFile(io.BytesIO(data)).extractall(TOOLS)
        (TOOLS / "pt.zip").unlink()
    log("ADB/Fastboot bereit.")
    if not MAGISK_APK.exists():
        req = urllib.request.Request(MAGISK_API, headers={"User-Agent": "PhoneDeck-Setup"})
        rel = json.load(urllib.request.urlopen(req, timeout=30))
        asset = next(a for a in rel["assets"] if a["name"].endswith(".apk"))
        download(asset["browser_download_url"], MAGISK_APK)
    log("Magisk bereit.")
    if not find("PhoneDeck.apk"):
        log("WARNUNG: PhoneDeck.apk liegt nicht neben dem Assistenten.")
    log("✅ Schritt 1 fertig.")


def step_check():
    require_device()
    dev = shell("getprop ro.product.device")
    model = shell("getprop ro.product.model")
    android = shell("getprop ro.build.version.release")
    boot = shell("getprop ro.boot.verifiedbootstate")
    log(f"Modell: {model} ({dev}), Android {android}")
    log("Bootloader: " + ("ENTSPERRT ✅" if boot == "orange" else "gesperrt 🔒 (Schritt 3)"))
    if boot == "orange":
        log("Root: " + ("JA ✅" if has_root() else "nein (Schritt 4)"))
    if dev != "dandelion":
        log("Hinweis: Anleitung ist fuer Redmi 9A (dandelion) gemacht.")
    log("✅ Pruefung fertig.")


def step_unlock():
    if not ask("Bootloader entsperren",
               "ACHTUNG: Beim Entsperren wird das Handy KOMPLETT GELOESCHT.\n\n"
               "Vorher am Handy:\n"
               "• Entwickleroptionen → 'OEM-Entsperrung' an\n"
               "• Entwickleroptionen → 'Mi-Entsperrstatus' → Mi-Account verknuepfen\n\n"
               "Weiter: Mi-Unlock-Seite oeffnen und Handy in Fastboot starten?"):
        return
    webbrowser.open(MI_UNLOCK_URL)
    require_device()
    adb("reboot", "bootloader")
    wait_fastboot()
    info("Mi Unlock",
         "Handy ist im Fastboot-Modus.\n\n"
         "1. Mi Unlock Tool (wurde im Browser geoeffnet) herunterladen und starten.\n"
         "2. Mit Mi-Account anmelden → 'Unlock'.\n"
         "3. Meldet es eine Wartezeit (meist 168 h): warten, dann nochmal.\n\n"
         "Nach dem Entsperren: Handy neu einrichten, USB-Debugging wieder an, dann Schritt 4.")


def extract_from_rom(rom, names):
    """Holt boot.img/vbmeta.img aus Fastboot-ROM (.tgz) oder nimmt boot.img direkt."""
    out = {}
    if rom.lower().endswith(".img"):
        out["boot.img"] = Path(rom)
        return out
    log("Entpacke ROM (kann dauern) …")
    with tarfile.open(rom) as tf:
        for m in tf:
            base = m.name.rsplit("/", 1)[-1]
            if base in names and "/images/" in m.name:
                dest = TOOLS / base
                with tf.extractfile(m) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                out[base] = dest
                log(f"  {base} gefunden.")
    return out


def step_root_prepare():
    require_device()
    if shell("getprop ro.boot.verifiedbootstate") != "orange":
        raise RuntimeError("Bootloader ist noch gesperrt (Schritt 3).")
    rom = pick_file("Fastboot-ROM (.tgz) oder boot.img waehlen",
                    [("ROM oder boot.img", "*.tgz *.tar *.img"), ("Alle", "*.*")])
    if not rom:
        return
    files = extract_from_rom(rom, {"boot.img", "vbmeta.img"})
    if "boot.img" not in files:
        raise RuntimeError("Keine boot.img in der Datei gefunden.")
    adb("install", "-r", MAGISK_APK, check=True, timeout=180)
    shell("rm -f /sdcard/Download/magisk_patched*")
    adb("push", files["boot.img"], "/sdcard/Download/boot.img", check=True)
    shell("monkey -p com.topjohnwu.magisk -c android.intent.category.LAUNCHER 1")
    info("In Magisk patchen",
         "Magisk ist am Handy geoeffnet.\n\n"
         "1. Bei 'Magisk' auf 'Installieren' tippen\n"
         "2. 'Datei auswaehlen und patchen'\n"
         "3. Download → boot.img → 'LOS'\n"
         "4. Warten bis 'All done!'\n\n"
         "Danach hier 'Gepatcht flashen' klicken.")


def step_root_flash():
    require_device()
    name = shell("ls -t /sdcard/Download/magisk_patched* 2>/dev/null | head -n 1")
    if not name.startswith("/sdcard"):
        raise RuntimeError("Kein magisk_patched-Image gefunden. Erst in Magisk patchen.")
    local = TOOLS / "magisk_patched.img"
    adb("pull", name, local, check=True)
    if not ask("Flashen", "Gepatchtes Boot-Image jetzt aufs Handy flashen?"):
        return
    adb("reboot", "bootloader")
    wait_fastboot()
    vbmeta = TOOLS / "vbmeta.img"
    if vbmeta.exists():
        fastboot("--disable-verity", "--disable-verification", "flash", "vbmeta", vbmeta, check=True)
    fastboot("flash", "boot", local, check=True)
    fastboot("reboot")
    info("Root", "Handy startet neu. Danach Magisk-App oeffnen – evtl. fragt sie nach\n"
                 "'Zusaetzliches Setup' → OK (startet nochmal neu).\n\nDann Schritt 5.")


def step_autoboot():
    require_device()
    if not has_root():
        raise RuntimeError("Kein Root. Am Handy die Magisk-Anfrage fuer 'Shell' erlauben "
                           "oder zuerst Schritt 4.")
    tools = find("handy-tools")
    if not tools:
        raise RuntimeError("Ordner handy-tools fehlt neben dem Assistenten.")
    if not ask("Auto-Boot", "Boot-Image wird geaendert (Backup wird vorher gesichert).\nFortfahren?"):
        return
    shell("mkdir -p /sdcard/phonedeck")
    for f in tools.iterdir():
        adb("push", f, "/sdcard/phonedeck/" + f.name, check=True)
    code, out = adb("shell", "su -c 'sh /sdcard/phonedeck/autoboot_einrichten.sh'", timeout=180)
    BACKUP_DIR.mkdir(exist_ok=True)
    adb("pull", "/sdcard/phonedeck/boot_backup.img", BACKUP_DIR / "boot_backup.img")
    if code != 0 or "Fertig" not in out:
        raise RuntimeError("Skript fehlgeschlagen – siehe Log. Am Handy wurde nichts geflasht, "
                           "falls 'Fertig' fehlt.")
    log(f"Backup liegt in {BACKUP_DIR}. Wiederherstellen: fastboot flash boot boot_backup.img")
    log("✅ Auto-Boot eingerichtet. Test: Handy aus, Kabel rein → bootet.")


def grant_root_to_app():
    """Erlaubt PhoneDeck dauerhaft Root in Magisk (sonst kommt die Abfrage erst beim Ausschalten)."""
    out = shell(f"dumpsys package {PKG} | grep userId=")
    uid = "".join(c for c in out.split("userId=")[-1].split()[0] if c.isdigit()) if "userId=" in out else ""
    if uid:
        sql = f"REPLACE INTO policies (uid,policy,until,logging,notification) VALUES({uid},2,0,1,1)"
        code, _ = adb("shell", f"su -c \"magisk --sqlite '{sql}'\"", timeout=40)
        if code == 0:
            log("Root fuer PhoneDeck erlaubt ✅")
            return
    log("Bitte in der App: ⚙ lange druecken → 'Root testen' → in Magisk 'Erlauben'.")


def step_app():
    require_device()
    apk = find("PhoneDeck.apk", "app-debug.apk")
    if not apk:
        apk = pick_file("PhoneDeck.apk waehlen", [("APK", "*.apk")])
        if not apk:
            return
    adb("install", "-r", apk, check=True, timeout=180)
    root_ok = has_root()
    shell(f"appops set {PKG} SYSTEM_ALERT_WINDOW allow")
    shell(f"dumpsys deviceidle whitelist +{PKG}")
    shell(f"cmd package set-home-activity {PKG}/.MainActivity")
    shell(f"dpm set-active-admin {PKG}/.AdminReceiver")  # Standby: Bildschirm sofort aus
    ip = pc_ip()
    log(f"PC-IP: {ip}")
    shell(f"am start -n {PKG}/.MainActivity --es host {ip} --ei port 8765 "
          f"--ez shutdown {'true' if root_ok else 'false'} --ei delay 15")
    if root_ok:
        grant_root_to_app()
    else:
        log("Kein Root: Standby-Modus – PC aus = Bildschirm aus, PC an = Deck sofort da.")
    shell("am start -n com.miui.securitycenter/com.miui.permcenter.autostart.AutoStartManagementActivity")
    info("MIUI", "Am Handy ist die Autostart-Liste offen:\n'PhoneDeck' einschalten.\n\n"
                 "Ausserdem: Einstellungen → Apps → PhoneDeck → Energiesparmodus →\n"
                 "'Keine Einschraenkungen'.\n\n"
                 "Und: keine Bildschirmsperre (PIN/Muster) verwenden.")
    log("✅ App eingerichtet.")


def step_pc():
    server = find("PhoneDeck-Server.exe")
    startup = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
    if server:
        cmd = f'start "" "{server}"'
    else:
        script = find("server.py")
        if not script:
            raise RuntimeError("PhoneDeck-Server.exe nicht gefunden.")
        cmd = f'start "" pythonw "{script}"'
    startup.mkdir(parents=True, exist_ok=True)
    (startup / "PhoneDeck.bat").write_text(f"@echo off\r\n{cmd}\r\n", encoding="utf-8")
    log(f"Autostart: {startup / 'PhoneDeck.bat'}")
    subprocess.Popen(cmd, shell=True, cwd=str(APP_DIR))
    log("Server gestartet. Windows-Firewall fragt evtl.: 'Private Netzwerke' erlauben.")
    log("✅ PC eingerichtet. Buttons aendern: deck.json neben dem Assistenten.")


def step_restore():
    img = BACKUP_DIR / "boot_backup.img"
    if not img.exists():
        img = Path(pick_file("Backup boot_backup.img waehlen", [("Image", "*.img")]) or "")
        if not img.is_file():
            return
    if not ask("Wiederherstellen", f"{img}\n\nHandy muss im Fastboot-Modus sein\n"
                                   "(aus → Lautstaerke runter + Power).\nJetzt flashen?"):
        return
    wait_fastboot()
    fastboot("flash", "boot", img, check=True)
    fastboot("reboot")
    log("✅ Backup zurueckgespielt.")

# ---------------------------------------------------------------- GUI

STEPS = [
    ("1. Werkzeuge laden", "ADB, Fastboot und Magisk herunterladen.", [("Laden", step_tools)]),
    ("2. Handy pruefen", "Handy per USB anschliessen, USB-Debugging an "
                         "(Einstellungen → Ueber das Telefon → 7× MIUI-Version tippen).",
     [("Pruefen", step_check)]),
    ("3. Bootloader entsperren", "Einmalig, mit Mi Unlock Tool. LOESCHT DAS HANDY. "
                                 "Xiaomi verlangt meist 7 Tage Wartezeit.",
     [("Starten", step_unlock)]),
    ("4. Root (Magisk)", "Fastboot-ROM 12.0.18.0.QCDEUXM fuer Redmi 9A (dandelion) oder boot.img waehlen.",
     [("Vorbereiten", step_root_prepare), ("Gepatcht flashen", step_root_flash)]),
    ("5. Auto-Boot beim Einstecken", "Handy faehrt hoch, sobald der PC Strom gibt.",
     [("Einrichten", step_autoboot)]),
    ("6. PhoneDeck-App", "App installieren, als Startbildschirm setzen, PC-Adresse eintragen.",
     [("Installieren", step_app)]),
    ("7. PC-Autostart", "Server startet mit Windows.", [("Einrichten", step_pc)]),
    ("Notfall", "Auto-Boot rueckgaengig: Boot-Backup zurueckspielen.",
     [("Backup flashen", step_restore)]),
]

busy = threading.Lock()


def start(fn, buttons):
    if not busy.acquire(blocking=False):
        messagebox.showwarning("Moment", "Es laeuft noch ein Schritt.")
        return

    def worker():
        root.after(0, lambda: [b.config(state="disabled") for b in buttons])
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            log(f"❌ {e}")
            root.after(0, lambda: messagebox.showerror("Fehler", str(e)))
        finally:
            busy.release()
            root.after(0, lambda: [b.config(state="normal") for b in buttons])

    threading.Thread(target=worker, daemon=True).start()


def pump_log():
    while not log_q.empty():
        logbox.insert("end", log_q.get() + "\n")
        logbox.see("end")
    root.after(150, pump_log)


root = tk.Tk()
root.title("PhoneDeck Einrichtung")
root.geometry("760x720")

ttk.Label(root, text="PhoneDeck – Handy als Stream-Deck",
          font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
ttk.Label(root, text="Schritte der Reihe nach ausfuehren. Handy per USB anschliessen.").pack(
    anchor="w", padx=14)

frame = ttk.Frame(root)
frame.pack(fill="x", padx=10, pady=8)
all_buttons = []
for title, desc, actions in STEPS:
    box = ttk.LabelFrame(frame, text=title)
    box.pack(fill="x", pady=3)
    ttk.Label(box, text=desc, wraplength=500).pack(side="left", padx=8, pady=4, fill="x", expand=True)
    for label, fn in reversed(actions):
        b = ttk.Button(box, text=label)
        b.pack(side="right", padx=4, pady=4)
        all_buttons.append(b)
        b.config(command=lambda f=fn: start(f, all_buttons))

logbox = tk.Text(root, height=12, bg="#111", fg="#ddd", font=("Consolas", 9))
logbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
log(f"Ordner: {APP_DIR}")
pump_log()
root.mainloop()

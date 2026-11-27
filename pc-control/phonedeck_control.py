"""PhoneDeck Control – ein Fenster fuer alles.

- Startet den Server (im selben Programm).
- Verbindet das Handy per Kabel (adb reverse) automatisch.
- Buttons bearbeiten (Hinzufuegen, Aendern, Loeschen, Farbe, Aktion).
- Autostart mit Windows einrichten.

Beim Start laeuft alles von selbst los: Server an, Handy verbinden.
"""

import json
import os
import socket
import sys
import threading
import time
import urllib.request
import zipfile
import io
import subprocess
from http.server import ThreadingHTTPServer
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk, colorchooser

import server  # server.py im selben Ordner / mitgebaut

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

PORT = 8765
PKG = "de.phonedeck"
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
PT_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

# Server-Pfade auf diesen Ordner biegen
server.CONFIG = APP_DIR / "deck.json"
# Eigener web-Ordner neben der EXE hat Vorrang (fuer eigene Anpassungen),
# sonst der mitgebaute.
if (APP_DIR / "web").exists():
    server.WEB = APP_DIR / "web"
elif getattr(sys, "frozen", False):
    server.WEB = Path(getattr(sys, "_MEIPASS", APP_DIR)) / "web"
else:
    server.WEB = APP_DIR.parent / "pc-server" / "web"

DEFAULT_DECK = {
    "title": "PhoneDeck", "columns": 4,
    "buttons": [
        {"label": "YouTube", "icon": "▶️", "color": "#c4302b",
         "action": {"type": "url", "target": "https://youtube.com"}},
        {"label": "Explorer", "icon": "📁", "color": "#d9a400",
         "action": {"type": "run", "command": "explorer"}},
        {"label": "Play/Pause", "icon": "⏯️", "color": "#333",
         "action": {"type": "hotkey", "keys": "play/pause media"}},
        {"label": "Stumm", "icon": "🔇", "color": "#333",
         "action": {"type": "hotkey", "keys": "volume mute"}},
    ],
}

ACTION_TYPES = {
    "Webseite/Link öffnen (url)": "url",
    "Programm/Datei öffnen (open)": "open",
    "Befehl ausführen (run)": "run",
    "Tastenkürzel (hotkey)": "hotkey",
    "Text tippen (text)": "text",
}
FIELD_FOR = {"url": "target", "open": "target", "run": "command",
             "hotkey": "keys", "text": "text"}
HINT_FOR = {
    "url": "z.B. https://youtube.com  oder  steam://open/main",
    "open": "z.B. C:\\Programme\\OBS\\obs64.exe",
    "run": "z.B. explorer   oder   shutdown /s /t 0",
    "hotkey": "z.B. ctrl+shift+m   volume up   play/pause media",
    "text": "z.B. gg wp",
}


def log(msg):
    LOGQ.append(str(msg))


LOGQ = []


# ------------------------------------------------- Deck laden/speichern

def load_deck():
    try:
        return json.loads(server.CONFIG.read_text(encoding="utf-8"))
    except Exception:
        save_deck(DEFAULT_DECK)
        return json.loads(json.dumps(DEFAULT_DECK))


def save_deck(deck):
    server.CONFIG.write_text(json.dumps(deck, indent=2, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------- Server

def start_server():
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    log(f"Server laeuft auf Port {PORT}.")
    return httpd


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
        return ip
    except OSError:
        return "127.0.0.1"


# ------------------------------------------------- adb / Handy

def find_adb():
    for p in (APP_DIR / "tools" / "platform-tools" / "adb.exe",
              Path(os.environ.get("USERPROFILE", "")) / "pt" / "platform-tools" / "adb.exe"):
        if p.exists():
            return p
    # herunterladen
    try:
        data = urllib.request.urlopen(PT_URL, timeout=60).read()
        zipfile.ZipFile(io.BytesIO(data)).extractall(APP_DIR / "tools")
        p = APP_DIR / "tools" / "platform-tools" / "adb.exe"
        if p.exists():
            return p
    except Exception as e:  # noqa: BLE001
        log(f"ADB-Download fehlgeschlagen: {e}")
    return None


def adb(adb_path, *args, timeout=25):
    try:
        p = subprocess.run([str(adb_path), *args], capture_output=True, text=True,
                           timeout=timeout, creationflags=NO_WINDOW)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def connect_phone():
    """Kabel-Verbindung: adb reverse + App oeffnen. Laeuft im Hintergrund weiter."""
    adb_path = find_adb()
    if not adb_path:
        log("ADB nicht gefunden.")
        return False
    code, out = adb(adb_path, "devices")
    serials = [l.split("\t")[0] for l in out.splitlines()[1:] if "\tdevice" in l]
    if not serials:
        log("Kein Handy per USB. USB-Debugging an?")
        return False
    done = False
    for serial in serials:
        sel = ["-s", serial]
        # Nur Geraete mit installierter App ansprechen
        _, has = adb(adb_path, *sel, "shell", "pm", "path", PKG)
        if "package:" not in has:
            continue
        adb(adb_path, *sel, "reverse", "tcp:8765", "tcp:8765")
        adb(adb_path, *sel, "shell", "am", "start", "-n", f"{PKG}/.MainActivity",
            "--es", "host", "127.0.0.1", "--ei", "port", "8765")
        log(f"Handy verbunden ({serial}).")
        done = True
    if not done:
        log("App auf keinem Handy gefunden. PhoneDeck installiert?")
    return done


def connect_loop():
    """Haelt die Kabel-Verbindung: setzt reverse neu, wenn Handy wiederkommt."""
    while True:
        try:
            connect_phone()
        except Exception as e:  # noqa: BLE001
            log(f"Verbinden: {e}")
        time.sleep(5)


# ------------------------------------------------- Autostart

def startup_bat():
    return Path(os.environ.get("APPDATA", "")) / \
        "Microsoft/Windows/Start Menu/Programs/Startup/PhoneDeck.bat"


def set_autostart(on):
    bat = startup_bat()
    if on:
        exe = sys.executable if getattr(sys, "frozen", False) else f'pythonw "{__file__}"'
        bat.parent.mkdir(parents=True, exist_ok=True)
        bat.write_text(f'@echo off\r\nstart "" {exe}\r\n', encoding="utf-8")
        log(f"Autostart an: {bat}")
    elif bat.exists():
        bat.unlink()
        log("Autostart aus.")


# ------------------------------------------------- GUI

class App:
    def __init__(self, root):
        self.root = root
        self.deck = load_deck()
        root.title("PhoneDeck Control")
        root.geometry("820x620")

        top = ttk.Frame(root); top.pack(fill="x", padx=10, pady=8)
        self.status = ttk.Label(top, text="Server: …   Handy: …", font=("Segoe UI", 10, "bold"))
        self.status.pack(side="left")
        self.auto = tk.BooleanVar(value=startup_bat().exists())
        ttk.Checkbutton(top, text="Mit Windows starten", variable=self.auto,
                        command=lambda: set_autostart(self.auto.get())).pack(side="right")
        ttk.Button(top, text="Handy verbinden", command=connect_phone).pack(side="right", padx=6)

        mid = ttk.Frame(root); mid.pack(fill="both", expand=True, padx=10)
        left = ttk.LabelFrame(mid, text="Buttons")
        left.pack(side="left", fill="both", expand=True)
        self.listbox = tk.Listbox(left, font=("Segoe UI", 11))
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        row = ttk.Frame(left); row.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(row, text="Neu", command=self.add).pack(side="left")
        ttk.Button(row, text="Löschen", command=self.delete).pack(side="left", padx=4)
        ttk.Button(row, text="▲", width=3, command=lambda: self.move(-1)).pack(side="left")
        ttk.Button(row, text="▼", width=3, command=lambda: self.move(1)).pack(side="left")

        right = ttk.LabelFrame(mid, text="Bearbeiten")
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.vars = {}
        self._field(right, "Beschriftung", "label")
        self._field(right, "Symbol (Emoji)", "icon")
        colrow = ttk.Frame(right); colrow.pack(fill="x", padx=8, pady=4)
        ttk.Label(colrow, text="Farbe").pack(side="left")
        self.vars["color"] = tk.StringVar()
        ttk.Entry(colrow, textvariable=self.vars["color"], width=10).pack(side="left", padx=6)
        ttk.Button(colrow, text="wählen", command=self.pick_color).pack(side="left")

        ttk.Label(right, text="Aktion").pack(anchor="w", padx=8, pady=(10, 0))
        self.type_var = tk.StringVar()
        self.type_box = ttk.Combobox(right, textvariable=self.type_var, state="readonly",
                                     values=list(ACTION_TYPES.keys()))
        self.type_box.pack(fill="x", padx=8)
        self.type_box.bind("<<ComboboxSelected>>", lambda e: self.update_hint())
        self.vars["value"] = tk.StringVar()
        ttk.Entry(right, textvariable=self.vars["value"]).pack(fill="x", padx=8, pady=4)
        self.hint = ttk.Label(right, text="", foreground="#888", wraplength=320)
        self.hint.pack(anchor="w", padx=8)
        ttk.Button(right, text="Übernehmen", command=self.apply).pack(anchor="w", padx=8, pady=8)

        gridrow = ttk.Frame(right); gridrow.pack(fill="x", padx=8, pady=4)
        ttk.Label(gridrow, text="Spalten").pack(side="left")
        self.cols = tk.StringVar(value=str(self.deck.get("columns", 4)))
        ttk.Entry(gridrow, textvariable=self.cols, width=4).pack(side="left", padx=6)
        ttk.Button(gridrow, text="Speichern & aufs Handy",
                   command=self.save_all).pack(side="left", padx=6)

        self.logbox = tk.Text(root, height=6, bg="#111", fg="#ddd", font=("Consolas", 9))
        self.logbox.pack(fill="x", padx=10, pady=(0, 10))

        self.refresh_list()
        self.pump()

    def _field(self, parent, label, key):
        f = ttk.Frame(parent); f.pack(fill="x", padx=8, pady=4)
        ttk.Label(f, text=label, width=16).pack(side="left")
        self.vars[key] = tk.StringVar()
        ttk.Entry(f, textvariable=self.vars[key]).pack(side="left", fill="x", expand=True)

    def refresh_list(self):
        self.listbox.delete(0, "end")
        for b in self.deck["buttons"]:
            self.listbox.insert("end", f"{b.get('icon','')}  {b.get('label','')}")

    def on_select(self, _=None):
        i = self.sel()
        if i is None:
            return
        b = self.deck["buttons"][i]
        self.vars["label"].set(b.get("label", ""))
        self.vars["icon"].set(b.get("icon", ""))
        self.vars["color"].set(b.get("color", "#333333"))
        act = b.get("action", {})
        t = act.get("type", "url")
        for name, code in ACTION_TYPES.items():
            if code == t:
                self.type_var.set(name)
        self.vars["value"].set(act.get(FIELD_FOR.get(t, "target"), ""))
        self.update_hint()

    def sel(self):
        s = self.listbox.curselection()
        return s[0] if s else None

    def update_hint(self):
        t = ACTION_TYPES.get(self.type_var.get(), "url")
        self.hint.config(text=HINT_FOR.get(t, ""))

    def pick_color(self):
        c = colorchooser.askcolor(self.vars["color"].get() or "#333333")
        if c and c[1]:
            self.vars["color"].set(c[1])

    def apply(self):
        i = self.sel()
        if i is None:
            messagebox.showinfo("Hinweis", "Links einen Button auswählen oder 'Neu'.")
            return
        t = ACTION_TYPES.get(self.type_var.get(), "url")
        self.deck["buttons"][i] = {
            "label": self.vars["label"].get(),
            "icon": self.vars["icon"].get(),
            "color": self.vars["color"].get() or "#333333",
            "action": {"type": t, FIELD_FOR[t]: self.vars["value"].get()},
        }
        self.refresh_list()
        self.listbox.selection_set(i)
        self.save_all(silent=True)

    def add(self):
        self.deck["buttons"].append({
            "label": "Neu", "icon": "⭐", "color": "#444444",
            "action": {"type": "url", "target": "https://"},
        })
        self.refresh_list()
        self.listbox.selection_set("end")
        self.on_select()

    def delete(self):
        i = self.sel()
        if i is None:
            return
        del self.deck["buttons"][i]
        self.refresh_list()
        self.save_all(silent=True)

    def move(self, d):
        i = self.sel()
        if i is None:
            return
        j = i + d
        if 0 <= j < len(self.deck["buttons"]):
            b = self.deck["buttons"]
            b[i], b[j] = b[j], b[i]
            self.refresh_list()
            self.listbox.selection_set(j)
            self.save_all(silent=True)

    def save_all(self, silent=False):
        try:
            self.deck["columns"] = int(self.cols.get())
        except ValueError:
            pass
        save_deck(self.deck)
        if not silent:
            log("Gespeichert. Handy lädt beim nächsten Tippen neu.")

    def pump(self):
        while LOGQ:
            self.logbox.insert("end", LOGQ.pop(0) + "\n")
            self.logbox.see("end")
        ip = local_ip()
        self.status.config(text=f"Server läuft (Port {PORT})   PC-IP {ip}   Handy per Kabel")
        self.root.after(400, self.pump)


def main():
    load_deck()
    start_server()
    threading.Thread(target=connect_loop, daemon=True).start()
    if getattr(sys, "frozen", False):
        set_autostart(True)  # beim ersten EXE-Start gleich Autostart an
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

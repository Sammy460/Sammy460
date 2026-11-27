"""PhoneDeck PC-Server.

Zeigt die Buttons aus deck.json als Webseite an (die das Handy anzeigt)
und fuehrt beim Druecken die passende Aktion auf dem PC aus.

Start:  python server.py         (Konsole sichtbar)
        pythonw server.py        (ohne Fenster, z.B. im Autostart)
"""

import json
import os
import socket
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if getattr(sys, "frozen", False):  # als EXE (PyInstaller)
    BASE = Path(sys.executable).resolve().parent
    WEB = Path(getattr(sys, "_MEIPASS", BASE)) / "web"
else:
    BASE = Path(__file__).resolve().parent
    WEB = BASE / "web"
CONFIG = BASE / "deck.json"
PORT = int(os.environ.get("PHONEDECK_PORT", "8765"))

if sys.stdout is None:  # EXE ohne Konsole
    sys.stdout = sys.stderr = open(os.devnull, "w")

try:  # optional: fuer Tastenkombinationen, Media-Tasten und Text
    import keyboard  # type: ignore
except Exception:  # noqa: BLE001
    keyboard = None


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def run_action(action):
    kind = action.get("type")
    if kind == "multi":
        for sub in action.get("actions", []):
            run_action(sub)
    elif kind == "url":
        webbrowser.open(action["target"])
    elif kind == "open":
        target = os.path.expandvars(action["target"])
        if sys.platform == "win32":
            os.startfile(target)  # noqa: S606
        else:
            subprocess.Popen(["xdg-open", target])
    elif kind == "run":
        subprocess.Popen(os.path.expandvars(action["command"]), shell=True)  # noqa: S602
    elif kind in ("hotkey", "text"):
        if keyboard is None:
            raise RuntimeError("Modul 'keyboard' fehlt: pip install keyboard")
        if kind == "hotkey":
            keyboard.send(action["keys"])
        else:
            keyboard.write(action["text"])
    else:
        raise ValueError(f"Unbekannter Aktionstyp: {kind}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # leiser loggen
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, ctype):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_file(WEB / "index.html", "text/html; charset=utf-8")
        elif self.path == "/api/ping":
            self.send_json({"ok": True})
        elif self.path == "/api/deck":
            try:
                cfg = load_config()
            except Exception as e:  # noqa: BLE001
                self.send_json({"error": f"deck.json fehlerhaft: {e}"}, 500)
                return
            # Aktionen bleiben auf dem PC, das Handy bekommt nur die Optik
            cfg["buttons"] = [
                {k: v for k, v in b.items() if k != "action"}
                for b in cfg.get("buttons", [])
            ]
            self.send_json(cfg)
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        if not self.path.startswith("/api/press/"):
            self.send_json({"error": "not found"}, 404)
            return
        try:
            idx = int(self.path.rsplit("/", 1)[1])
            button = load_config()["buttons"][idx]
            run_action(button["action"])
            self.send_json({"ok": True})
        except Exception as e:  # noqa: BLE001
            print("Fehler:", e)
            self.send_json({"ok": False, "error": str(e)}, 500)


def local_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(ips) or ["127.0.0.1"]


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("PhoneDeck-Server laeuft.")
    for ip in local_ips():
        print(f"  Im Handy eintragen: {ip}  Port {PORT}")
    print("  Per USB (adb reverse): 127.0.0.1  Port", PORT)
    if keyboard is None:
        print("  Hinweis: 'pip install keyboard' fuer Hotkeys/Media-Tasten.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

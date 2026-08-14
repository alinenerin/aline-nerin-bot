from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from ly_core import reply_for, LyMemory

memory = LyMemory()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"Ly core test online")
            return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path != "/test/reply":
            self.send_response(404); self.end_headers(); return
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            result = reply_for(body.get("text", ""), memory, body.get("conversation_id", "test"))
            payload = json.dumps(result.__dict__, ensure_ascii=False).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(payload)
        except Exception:
            self.send_response(400); self.end_headers()

    def log_message(self, *_): pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(__import__('os').environ.get("PORT", "10000"))), Handler).serve_forever()

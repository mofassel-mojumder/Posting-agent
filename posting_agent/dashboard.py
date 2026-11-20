"""Local dashboard. Stdlib only, no Flask needed.

Run: python -m posting_agent.dashboard
Open: http://localhost:8765
Only on this computer. No login, no external access.
"""
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ALLOWED_DESTINATIONS = ["facebook_page", "instagram", "facebook_personal", "linkedin_personal"]

from . import audit, inbox, scheduler
from .config import load_config

BASE_DIR = Path(__file__).resolve().parent.parent
TZ = ZoneInfo("Asia/Dhaka")
HTML = (Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8")


def _parse_multipart(body, boundary):
    """Parse multipart/form-data with stdlib only. Returns (fields, files).

    fields: {name: [str, ...]}, files: {name: (filename, content_type, bytes)}
    """
    fields = {}
    files = {}
    marker = b"--" + boundary
    for part in body.split(marker):
        if not part or part in (b"--", b"--\r\n", b"\r\n"):
            continue
        if part.startswith(b"\r\n"):
            part = part[2:]
        if part.endswith(b"\r\n"):
            part = part[:-2]
        if part == b"--" or not part:
            continue
        head, sep, content = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        headers = {}
        for line in head.decode("utf-8", "replace").split("\r\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()
        disp = headers.get("content-disposition", "")
        name = None
        filename = None
        for chunk in disp.split(";"):
            chunk = chunk.strip()
            if chunk.startswith("name="):
                name = chunk[5:].strip().strip('"')
            elif chunk.startswith("filename="):
                filename = chunk[9:].strip().strip('"')
        if not name:
            continue
        if filename is not None:
            files[name] = (filename, headers.get("content-type", ""), content)
        else:
            fields.setdefault(name, []).append(content.decode("utf-8", "replace"))
    return fields, files


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the console quiet
        pass

    def _handle_upload(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json({"error": "multipart form data lagbe"}, code=400)
            return
        boundary = None
        for chunk in content_type.split(";"):
            chunk = chunk.strip()
            if chunk.startswith("boundary="):
                boundary = chunk[9:].strip().strip('"').encode("utf-8")
        if not boundary:
            self._send_json({"error": "boundary pawa jay ni"}, code=400)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_UPLOAD_BYTES + 1024 * 1024:
            self._send_json({"error": "file onek boro, 100 MB er kom hote hobe"}, code=413)
            return
        body = self.rfile.read(length)
        fields, files = _parse_multipart(body, boundary)
        caption = (fields.get("caption", [""])[0] or "").strip()
        date = (fields.get("date", [""])[0] or "").strip()
        slot = (fields.get("slot", [""])[0] or "").strip()
        media_url = (fields.get("media_url", [""])[0] or "").strip()
        destinations = [d for d in fields.get("destinations", []) if d in ALLOWED_DESTINATIONS]
        if "media" not in files or not files["media"][2]:
            self._send_json({"error": "chobi ba video dite hobe"}, code=400)
            return
        if not caption:
            self._send_json({"error": "caption likhte hobe"}, code=400)
            return
        if slot not in ("14:00", "20:00"):
            self._send_json({"error": "somoy sudhu 14:00 ba 20:00 hote hobe"}, code=400)
            return
        try:
            post_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            self._send_json({"error": "tarikh thik noy, YYYY-MM-DD hote hobe"}, code=400)
            return
        if post_date < datetime.now(TZ).date():
            self._send_json({"error": "tarikh ajker ba samner hote hobe"}, code=400)
            return
        if not destinations:
            self._send_json({"error": "ontoto ekta jayga bachhte hobe"}, code=400)
            return
        filename, _ctype, data = files["media"]
        if len(data) > MAX_UPLOAD_BYTES:
            self._send_json({"error": "file onek boro, 100 MB er kom hote hobe"}, code=413)
            return
        suffix = Path(filename).suffix.lower()
        if suffix not in inbox.MEDIA_EXTS:
            self._send_json({"error": "file type cholbe na, chobi (jpg/png) ba video (mp4/mov) dite hobe"}, code=400)
            return
        base = "%s-%s" % (date, slot.replace(":", ""))
        post_id = base
        n = 2
        while (inbox.INBOX_DIR / post_id).exists():
            post_id = "%s-%d" % (base, n)
            n += 1
        folder = inbox.INBOX_DIR / post_id
        folder.mkdir(parents=True, exist_ok=False)
        (folder / ("media" + suffix)).write_bytes(data)
        (folder / "caption.txt").write_text(caption, encoding="utf-8")
        (folder / "post.json").write_text(
            json.dumps({"date": date, "slot": slot, "destinations": destinations}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if media_url:
            (folder / "media_url.txt").write_text(media_url, encoding="utf-8")
        audit.log_event(post_id, "dashboard", "uploaded", "Dashboard upload form theke post joma deoa hoyeche")
        self._send_json({"ok": True, "post_id": post_id})

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            cfg = load_config()
            state_file = BASE_DIR / "scheduler.state"
            state = state_file.read_text(encoding="utf-8").strip() if state_file.exists() else "running"
            self._send_json(
                {
                    "dry_run": cfg["dry_run"],
                    "slots": cfg["slots"],
                    "scheduler": state,
                    "now": datetime.now(TZ).isoformat(timespec="seconds"),
                    "posts": inbox.list_posts(),
                    "log": audit.read_log(100),
                }
            )
        else:
            self._send_json({"error": "not found"}, code=404)

    def do_POST(self):
        if self.path == "/api/upload":
            self._handle_upload()
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except ValueError:
            data = {}
        if self.path == "/api/state":
            state = data.get("state", "stopped")
            if state not in ("running", "stopped"):
                state = "stopped"
            (BASE_DIR / "scheduler.state").write_text(state, encoding="utf-8")
            self._send_json({"scheduler": state})
        elif self.path == "/api/run-once":
            results = scheduler.run_once()
            self._send_json({"results": results})
        elif self.path == "/api/manual-done":
            post_id = data.get("post_id", "")
            dest = data.get("destination", "")
            posts = {p["id"]: p for p in inbox.list_posts()}
            post = posts.get(post_id)
            if not post:
                self._send_json({"error": "post not found"}, code=404)
                return
            status = dict(post["status"])
            status.setdefault("destinations", {})[dest] = "manual_done"
            inbox.save_status(post_id, status)
            audit.log_event(post_id, dest, "manual_done", "User posted it manually from the dashboard")
            self._send_json({"ok": True})
        else:
            self._send_json({"error": "not found"}, code=404)


def main():
    print("Dashboard: http://localhost:8765")
    print("Press Ctrl+C to stop.")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()


if __name__ == "__main__":
    main()

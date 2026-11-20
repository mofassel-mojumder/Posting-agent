"""Audit log. Every attempt is recorded per destination, separately.

A dry-run entry is never recorded as posted. A failed entry is never
retried automatically. The log is the proof of what happened.
"""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "logs" / "audit.log"
TZ = ZoneInfo("Asia/Dhaka")


def log_event(post_id, destination, status, detail=""):
    """status: queued, dry_run, posted, manual_ready, manual_done, failed, skipped"""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "time_dhaka": datetime.now(TZ).isoformat(timespec="seconds"),
        "post_id": post_id,
        "destination": destination,
        "status": status,
        "detail": detail,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_log(limit=100):
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except ValueError:
            out.append({"time_dhaka": "", "post_id": "", "destination": "", "status": "bad_line", "detail": line})
    return out

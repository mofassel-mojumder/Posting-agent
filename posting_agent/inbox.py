"""Content inbox. One folder per post.

Layout:
  inbox/<post_id>/
    caption.txt      - the exact caption, as he wrote it
    media.jpg / media.png / media.mp4  - the picture or video he provided
    media_url.txt    - optional, a public URL for the media (needed for Instagram)
    post.json        - {"date": "2026-11-19", "slot": "20:00",
                       "destinations": ["facebook_page", "instagram",
                                        "facebook_personal", "linkedin_personal"]}
    status.json      - written by the agent, never by hand

A post is due when its date is today and now is within 30 minutes
after its slot time. A destination already in status.json is never
posted again.
"""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
INBOX_DIR = BASE_DIR / "inbox"
TZ = ZoneInfo("Asia/Dhaka")
MEDIA_EXTS = {".jpg", ".jpeg", ".png", ".mp4", ".mov"}


def list_posts():
    posts = []
    if not INBOX_DIR.exists():
        return posts
    for folder in sorted(INBOX_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        meta_path = folder / "post.json"
        caption_path = folder / "caption.txt"
        if not meta_path.exists() or not caption_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        media = None
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in MEDIA_EXTS:
                media = f
                break
        thumbnail = None
        for name in ("thumbnail.png", "thumbnail.jpg", "thumbnail.jpeg"):
            p = folder / name
            if p.exists():
                thumbnail = p
                break
        status = {}
        status_path = folder / "status.json"
        if status_path.exists():
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
            except ValueError:
                status = {}
        media_url = ""
        url_path = folder / "media_url.txt"
        if url_path.exists():
            media_url = url_path.read_text(encoding="utf-8").strip()
        posts.append(
            {
                "id": folder.name,
                "folder": str(folder),
                "caption": caption_path.read_text(encoding="utf-8"),
                "media": str(media) if media else None,
                "thumbnail": str(thumbnail) if thumbnail else None,
                "media_url": media_url,
                "date": meta.get("date", ""),
                "slot": meta.get("slot", ""),
                "destinations": meta.get("destinations", []),
                "status": status,
            }
        )
    return posts


def save_status(post_id, status):
    folder = INBOX_DIR / post_id
    (folder / "status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def is_due(post, now=None):
    """Due when date is today and now is within 30 minutes after the slot.

    The 30 minute window is for GitHub Actions: a scheduled cron can
    start a few minutes late, so a post must still count as due a
    little after its slot. After 30 minutes the slot is missed, and
    the post is not posted late by hours.
    """
    from datetime import timedelta

    now = now or datetime.now(TZ)
    if post["date"] != now.strftime("%Y-%m-%d"):
        return False
    try:
        hour, minute = (int(x) for x in post["slot"].split(":"))
    except ValueError:
        return False
    slot_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return slot_time <= now < slot_time + timedelta(minutes=30)


def create_post(post_id, date, slot, destinations, caption, media_src=None):
    """Helper for tests and for the dashboard. Media is copied, never moved."""
    import shutil

    folder = INBOX_DIR / post_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "caption.txt").write_text(caption, encoding="utf-8")
    (folder / "post.json").write_text(
        json.dumps(
            {"date": date, "slot": slot, "destinations": destinations},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if media_src:
        src = Path(media_src)
        shutil.copy2(src, folder / ("media" + src.suffix.lower()))
    return folder

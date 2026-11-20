"""Publishers. Honest and safe by design.

AUTO (official Meta Graph API, only when a real token is in .env):
  - Facebook Page: photo or video upload, direct file upload works.
  - Instagram: Graph API needs a PUBLIC URL for the media file. A local
    file alone cannot be posted to Instagram through the API. If no
    media_url.txt is supplied, Instagram is reported as blocked with
    that reason, never faked as posted.

MANUAL (no official API exists in v1, so nothing is automated):
  - Personal Facebook profile: there is no official API for personal
    profile posting. Draft-ready only.
  - LinkedIn personal profile: personal profile automation is the
    highest suspension risk, so v1 never posts to it automatically.
    Draft-ready only. Official API posting is only for a LinkedIn
    Company Page, which is not in scope for v1.

DRY-RUN is the default. With DRY_RUN=true, or with no token, no HTTP
call is made to Meta at all. The audit log records "dry_run", not "posted".
"""
import json
from pathlib import Path

import requests

GRAPH_BASE = "https://graph.facebook.com/v21.0"
VIDEO_EXTS = {".mp4", ".mov"}


class PublishResult:
    def __init__(self, ok, status, detail="", post_url=""):
        self.ok = ok
        self.status = status  # posted, dry_run, manual_ready, failed, blocked
        self.detail = detail
        self.post_url = post_url


def _is_video(media_path):
    return media_path and Path(media_path).suffix.lower() in VIDEO_EXTS


def post_facebook_page(cfg, post):
    """Post to the Facebook Page through the Meta Graph API."""
    env = cfg["env"]
    token = env.get("META_PAGE_ACCESS_TOKEN", "")
    page_id = env.get("META_PAGE_ID", "")
    caption = post["caption"]
    if cfg["dry_run"] or not token or not page_id:
        reason = "dry_run" if cfg["dry_run"] else "no_token_or_page_id"
        return PublishResult(
            True, "dry_run", f"DRY RUN ({reason}): would POST to Graph API /{page_id or 'PAGE_ID'}/photos or /videos"
        )
    try:
        if _is_video(post["media"]):
            url = f"{GRAPH_BASE}/{page_id}/videos"
            with open(post["media"], "rb") as f:
                r = requests.post(
                    url,
                    data={"description": caption, "access_token": token},
                    files={"source": f},
                    timeout=120,
                )
        else:
            url = f"{GRAPH_BASE}/{page_id}/photos"
            with open(post["media"], "rb") as f:
                r = requests.post(
                    url,
                    data={"message": caption, "access_token": token},
                    files={"source": f},
                    timeout=120,
                )
        data = r.json()
        if r.status_code in (200, 201) and "id" in data:
            return PublishResult(True, "posted", f"Graph API id {data['id']}", f"https://www.facebook.com/{data['id']}")
        return PublishResult(False, "failed", f"Graph API HTTP {r.status_code}: {json.dumps(data)[:300]}")
    except Exception as exc:  # noqa: BLE001 - report the error, never hide it
        return PublishResult(False, "failed", f"Graph API error: {exc}")


def post_instagram(cfg, post):
    """Post to Instagram through the Meta Graph API.

    Step 1: create a media container with a public media URL.
    Step 2: publish the container. Both steps are real API calls.
    Without a public URL this cannot run, and v1 says so plainly.
    """
    env = cfg["env"]
    token = env.get("META_PAGE_ACCESS_TOKEN", "")
    ig_id = env.get("META_INSTAGRAM_USER_ID", "")
    media_url = post.get("media_url", "")
    if not media_url:
        return PublishResult(
            False,
            "blocked",
            "Instagram needs a public URL for the media (Graph API rule). "
            "Put the public link in media_url.txt, or post this one manually from the dashboard.",
        )
    if cfg["dry_run"] or not token or not ig_id:
        reason = "dry_run" if cfg["dry_run"] else "no_token_or_ig_id"
        return PublishResult(
            True, "dry_run", f"DRY RUN ({reason}): would create container at /{ig_id or 'IG_ID'}/media then publish it"
        )
    try:
        payload = {
            "image_url": media_url,
            "caption": post["caption"],
            "access_token": token,
        }
        if _is_video(post["media"]):
            payload = {
                "media_type": "REELS",
                "video_url": media_url,
                "caption": post["caption"],
                "access_token": token,
            }
        r = requests.post(f"{GRAPH_BASE}/{ig_id}/media", data=payload, timeout=60)
        data = r.json()
        if r.status_code not in (200, 201) or "id" not in data:
            return PublishResult(False, "failed", f"Container HTTP {r.status_code}: {json.dumps(data)[:300]}")
        container_id = data["id"]
        r2 = requests.post(
            f"{GRAPH_BASE}/{ig_id}/media_publish",
            data={"creation_id": container_id, "access_token": token},
            timeout=60,
        )
        data2 = r2.json()
        if r2.status_code in (200, 201) and "id" in data2:
            return PublishResult(True, "posted", f"Graph API id {data2['id']}")
        return PublishResult(False, "failed", f"Publish HTTP {r2.status_code}: {json.dumps(data2)[:300]}")
    except Exception as exc:  # noqa: BLE001 - report the error, never hide it
        return PublishResult(False, "failed", f"Graph API error: {exc}")


def manual_pack(cfg, post, destination):
    """Draft-ready pack for Personal Facebook and LinkedIn.

    Nothing is posted. The dashboard shows the caption to copy, the
    media file to download, and the site to open.
    """
    if destination == "linkedin_personal":
        site = "https://www.linkedin.com/feed/"
        label = "LinkedIn personal profile"
    else:
        site = "https://www.facebook.com/"
        label = "Personal Facebook profile"
    return PublishResult(
        True,
        "manual_ready",
        f"{label}: manual step. Copy the caption, use the media file, open {site} and post it yourself. "
        "No official API posts to a personal profile in v1, on purpose.",
    )

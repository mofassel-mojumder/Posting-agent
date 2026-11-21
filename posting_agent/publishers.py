"""Publishers. Honest and safe by design.

AUTO (official Meta Graph API, only when a real token is in .env):
  - Facebook Page: photo or video upload, direct file upload works.
  - Instagram: Graph API needs a PUBLIC URL for the media file. A local
    file alone cannot be posted to Instagram through the API. If no
    media_url.txt is supplied, Instagram is reported as blocked with
    that reason, never faked as posted.

AUTO (official LinkedIn API, only when a real token is in .env):
  - LinkedIn personal profile: POST /v2/ugcPosts with scope
    w_member_social. Text, image (assets registerUpload) and video
    (Videos API initializeUpload, upload, then poll until AVAILABLE)
    are supported. Only 2 posts per day, the same limit as the rest
    of the agent. No connection requests, no messages, no likes, no
    comments, no scraping: posting only, by hand for everything else.
    If LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN is missing, the
    post is reported manual_ready, never faked as posted.

MANUAL (no official API exists, so nothing is automated):
  - Personal Facebook profile: there is no official API for personal
    profile posting. Draft-ready only.

DRY-RUN is the default. With DRY_RUN=true, or with no token, no HTTP
call is made to Meta or LinkedIn at all. The audit log records
"dry_run", not "posted".
"""
import json
import time
from pathlib import Path

import requests

GRAPH_BASE = "https://graph.facebook.com/v21.0"
LINKEDIN_BASE = "https://api.linkedin.com/v2"
LINKEDIN_REST = "https://api.linkedin.com/rest"
VIDEO_EXTS = {".mp4", ".mov"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


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


def _linkedin_caption(post):
    """LinkedIn caption. Use caption-linkedin.txt when the post folder
    has one (LinkedIn captions often differ from the Facebook one),
    otherwise use the normal caption."""
    folder = Path(post.get("folder", "")) if post.get("folder") else None
    if folder:
        alt = folder / "caption-linkedin.txt"
        if alt.exists():
            text = alt.read_text(encoding="utf-8").strip()
            if text:
                return text
    return post["caption"]


def _linkedin_headers(token, rest=False):
    headers = {"Authorization": f"Bearer {token}"}
    if rest:
        headers["LinkedIn-Version"] = "202611"
        headers["Content-Type"] = "application/json"
    else:
        headers["X-Restli-Protocol-Version"] = "2.0.0"
        headers["Content-Type"] = "application/json"
    return headers


def _upload_linkedin_image(token, author, media_path):
    """Upload an image to LinkedIn (assets registerUpload). Returns the
    asset URN, or raises on any failure. No faking: a failed upload
    is reported as a failure by the caller."""
    r = requests.post(
        f"{LINKEDIN_BASE}/assets?action=registerUpload",
        headers=_linkedin_headers(token),
        json={
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author,
                "serviceRelationships": [
                    {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                ],
            }
        },
        timeout=60,
    )
    data = r.json()
    if r.status_code not in (200, 201):
        raise RuntimeError(f"registerUpload HTTP {r.status_code}: {json.dumps(data)[:300]}")
    value = data.get("value", {})
    upload_url = value.get("uploadMechanism", {}).get(
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
    ).get("uploadUrl", "")
    asset = value.get("asset", "")
    if not upload_url or not asset:
        raise RuntimeError(f"registerUpload gave no upload URL or asset: {json.dumps(data)[:300]}")
    with open(media_path, "rb") as f:
        r2 = requests.put(upload_url, headers={"Authorization": f"Bearer {token}"}, data=f, timeout=120)
    if r2.status_code not in (200, 201):
        raise RuntimeError(f"image upload HTTP {r2.status_code}: {r2.text[:300]}")
    return asset


def _upload_linkedin_video(token, author, media_path, thumbnail_path=None):
    """Upload a video with the LinkedIn Video API.

    Step 1: initializeUpload, which returns a video URN, the video part
    upload instructions, an upload token, and (when a thumbnail is given)
    a thumbnail upload URL.
    Step 2: PUT the thumbnail bytes to the thumbnail upload URL, if any.
    Step 3: PUT each video part (LinkedIn splits files into ~4 MB parts)
    to its own upload URL, keeping the ETag of every part.
    Step 4: finalizeUpload with the upload token and the part ETags, when
    the upload is multi-part.
    Step 5: poll the video until its status is AVAILABLE.
    Returns the video URN, or raises on any failure.
    """
    size = Path(media_path).stat().st_size
    want_thumbnail = bool(thumbnail_path) and Path(thumbnail_path).exists()
    r = requests.post(
        f"{LINKEDIN_REST}/videos?action=initializeUpload",
        headers=_linkedin_headers(token, rest=True),
        json={
            "initializeUploadRequest": {
                "owner": author,
                "fileSizeBytes": size,
                "uploadCaptions": False,
                "uploadThumbnail": want_thumbnail,
            }
        },
        timeout=60,
    )
    data = r.json()
    if r.status_code not in (200, 201):
        raise RuntimeError(f"initializeUpload HTTP {r.status_code}: {json.dumps(data)[:300]}")
    value = data.get("value", {})
    video_urn = value.get("video", "")
    instructions = value.get("uploadInstructions", [])
    upload_token = value.get("uploadToken", "")
    if not video_urn or not instructions:
        raise RuntimeError(f"initializeUpload gave no video URN or upload instructions: {json.dumps(data)[:300]}")
    if want_thumbnail:
        thumb_url = value.get("thumbnailUploadUrl", "")
        if not thumb_url:
            raise RuntimeError("initializeUpload gave no thumbnailUploadUrl even though uploadThumbnail was true")
        with open(thumbnail_path, "rb") as f:
            r_thumb = requests.put(
                thumb_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "media-type-family": "STILLIMAGE",
                    "Content-Type": "application/octet-stream",
                },
                data=f,
                timeout=60,
            )
        if r_thumb.status_code not in (200, 201):
            raise RuntimeError(f"thumbnail upload HTTP {r_thumb.status_code}: {r_thumb.text[:300]}")
    etags = []
    with open(media_path, "rb") as f:
        for inst in instructions:
            url = inst.get("uploadUrl", "")
            if not url:
                raise RuntimeError("initializeUpload gave an upload instruction with no uploadUrl")
            first = int(inst.get("firstByte", 0))
            last = int(inst.get("lastByte", size - 1))
            f.seek(first)
            chunk = f.read(last - first + 1)
            r_part = requests.put(
                url, headers={"Authorization": f"Bearer {token}"}, data=chunk, timeout=300
            )
            if r_part.status_code not in (200, 201):
                raise RuntimeError(
                    f"video part upload HTTP {r_part.status_code}: {r_part.text[:300]}"
                )
            etag = r_part.headers.get("ETag") or r_part.headers.get("etag")
            if etag:
                etags.append(etag)
    if upload_token and len(instructions) > 1 and etags:
        r_fin = requests.post(
            f"{LINKEDIN_REST}/videos?action=finalizeUpload",
            headers=_linkedin_headers(token, rest=True),
            json={
                "finalizeUploadRequest": {
                    "video": video_urn,
                    "uploadToken": upload_token,
                    "uploadedPartIds": etags,
                }
            },
            timeout=60,
        )
        if r_fin.status_code not in (200, 201):
            raise RuntimeError(f"finalizeUpload HTTP {r_fin.status_code}: {r_fin.text[:300]}")
    video_id = video_urn.rsplit(":", 1)[-1]
    for _ in range(60):
        r3 = requests.get(
            f"{LINKEDIN_REST}/videos/{video_id}",
            headers=_linkedin_headers(token, rest=True),
            timeout=60,
        )
        data3 = r3.json()
        if r3.status_code in (200, 201) and data3.get("status") == "AVAILABLE":
            return video_urn
        if r3.status_code in (200, 201) and data3.get("status") in ("FAILED", "PROCESSING_FAILED"):
            raise RuntimeError(f"video processing failed: {json.dumps(data3)[:300]}")
        time.sleep(5)
    raise RuntimeError("video did not become AVAILABLE in time, post was not created")


def post_linkedin(cfg, post):
    """Post to the LinkedIn personal profile through the official API.

    Scope needed: w_member_social. Token lives 60 days, then it must
    be renewed on LinkedIn Developers and put in GitHub Secrets again.
    Without a token or a person URN, this returns manual_ready, so the
    dashboard shows the caption to copy and the user posts by hand.
    In dry-run mode nothing is sent to LinkedIn at all.
    """
    env = cfg["env"]
    token = env.get("LINKEDIN_ACCESS_TOKEN", "")
    author = env.get("LINKEDIN_PERSON_URN", "")
    caption = _linkedin_caption(post)
    if cfg["dry_run"]:
        return PublishResult(
            True, "dry_run", "DRY RUN: would POST to LinkedIn /v2/ugcPosts as " + (author or "PERSON_URN")
        )
    if not token or not author:
        return PublishResult(
            True,
            "manual_ready",
            "LinkedIn personal profile: manual step, no LinkedIn token or person URN in .env. "
            "Copy the caption, use the media file, open https://www.linkedin.com/feed/ and post it yourself.",
        )
    try:
        media = None
        category = "NONE"
        if post.get("media"):
            suffix = Path(post["media"]).suffix.lower()
            if suffix in IMAGE_EXTS:
                asset = _upload_linkedin_image(token, author, post["media"])
                media = [{"status": "READY", "media": asset}]
                category = "IMAGE"
            elif suffix in VIDEO_EXTS:
                video_urn = _upload_linkedin_video(token, author, post["media"], post.get("thumbnail"))
                media = [{"status": "READY", "media": video_urn}]
                category = "VIDEO"
            else:
                return PublishResult(False, "failed", f"LinkedIn cannot post media type {suffix}")
        body = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": caption},
                    "shareMediaCategory": category,
                    "media": media or [],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        r = requests.post(
            f"{LINKEDIN_BASE}/ugcPosts", headers=_linkedin_headers(token), json=body, timeout=60
        )
        data = r.json()
        if r.status_code in (200, 201) and "id" in data:
            post_id = data["id"]
            url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id.startswith("urn:li:share:") else "https://www.linkedin.com/feed/"
            return PublishResult(True, "posted", f"LinkedIn id {post_id}", url)
        return PublishResult(False, "failed", f"LinkedIn HTTP {r.status_code}: {json.dumps(data)[:300]}")
    except Exception as exc:  # noqa: BLE001 - report the error, never hide it
        return PublishResult(False, "failed", f"LinkedIn error: {exc}")


def manual_pack(cfg, post, destination):
    """Draft-ready pack for Personal Facebook.

    Nothing is posted. The dashboard shows the caption to copy, the
    media file to download, and the site to open.
    """
    return PublishResult(
        True,
        "manual_ready",
        "Personal Facebook profile: manual step. Copy the caption, use the media file, "
        "open https://www.facebook.com/ and post it yourself. "
        "No official API posts to a personal profile, on purpose.",
    )

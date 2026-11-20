"""Scheduler. Checks due posts, posts at the slot time, stops on first error.

A post is due only within 30 minutes after its slot, so a late
GitHub Actions cron still works, but a post is never posted hours late.

Rules, enforced here and nowhere else:
  - Max 2 posts per day, 1 per slot (slots come from config.yaml).
  - A destination already recorded in status.json is never posted again.
  - Delay between destinations: 60 to 120 seconds in live mode.
    In dry-run or test mode the delay is skipped so tests are fast.
  - On the first failed or blocked destination, stop that post at once.
    Do not try the next destination. Do not retry automatically.
  - A dry-run result is recorded as dry_run, never as posted.
"""
import random
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import audit, inbox, publishers
from .config import load_config

TZ = ZoneInfo("Asia/Dhaka")
DEST_ORDER = ["facebook_page", "instagram", "facebook_personal", "linkedin_personal"]


def _delay(cfg):
    if cfg["dry_run"]:
        return
    d = cfg.get("delay_between_destinations_seconds") or {"min": 60, "max": 120}
    time.sleep(random.randint(int(d.get("min", 60)), int(d.get("max", 120))))


def run_once(cfg=None, now=None):
    """One scheduler pass. Returns a list of per-post results."""
    cfg = cfg or load_config()
    now = now or datetime.now(TZ)
    results = []
    posts_today = 0
    for post in inbox.list_posts():
        if post["date"] != now.strftime("%Y-%m-%d"):
            continue
        if post["slot"] not in cfg["slots"]:
            audit.log_event(post["id"], "all", "skipped", f"slot {post['slot']} is not in config slots {cfg['slots']}")
            results.append({"post_id": post["id"], "status": "skipped", "reason": "slot not in config"})
            continue
        if not inbox.is_due(post, now):
            continue
        if post["status"].get("failed"):
            # A post that stopped on an error is never retried automatically.
            # The user must fix the problem and delete status.json to retry it by hand.
            continue
        posts_today += 1
        if posts_today > int(cfg.get("max_posts_per_day", 2)):
            audit.log_event(post["id"], "all", "skipped", "daily limit reached (max 2 posts per day)")
            results.append({"post_id": post["id"], "status": "skipped", "reason": "daily limit"})
            continue
        results.append(_run_post(cfg, post))
    return results


def _run_post(cfg, post):
    status = dict(post["status"])
    status.setdefault("destinations", {})
    done = status["destinations"]
    for dest in DEST_ORDER:
        if dest not in post["destinations"]:
            continue
        if done.get(dest) in ("posted", "dry_run", "manual_ready", "manual_done"):
            continue
        if dest == "facebook_page":
            result = publishers.post_facebook_page(cfg, post)
        elif dest == "instagram":
            result = publishers.post_instagram(cfg, post)
        elif dest in ("facebook_personal", "linkedin_personal"):
            result = publishers.manual_pack(cfg, post, dest)
        else:
            result = publishers.PublishResult(False, "failed", f"unknown destination {dest}")
        audit.log_event(post["id"], dest, result.status, result.detail)
        done[dest] = result.status
        status["destinations"] = done
        status["last_run"] = datetime.now(TZ).isoformat(timespec="seconds")
        inbox.save_status(post["id"], status)
        if result.status in ("failed", "blocked"):
            # Stop on first error. No next destination, no automatic retry.
            # Mark the post failed so later passes skip it too.
            status["failed"] = True
            status["error_destination"] = dest
            status["error_detail"] = result.detail
            inbox.save_status(post["id"], status)
            return {"post_id": post["id"], "status": "stopped_on_error", "destination": dest, "detail": result.detail}
        _delay(cfg)
    return {"post_id": post["id"], "status": "done", "destinations": done}


def run_loop(cfg=None, interval_seconds=60):
    """Run forever, one pass per minute. Stop with Ctrl+C or the dashboard stop button."""
    cfg = cfg or load_config()
    state_file = Path(cfg["base_dir"]) / "scheduler.state"
    print("Posting Agent v1 running. Slots:", cfg["slots"], "Dry run:", cfg["dry_run"])
    print("Stop with Ctrl+C, or the Stop button on the dashboard.")
    while True:
        if state_file.exists() and state_file.read_text(encoding="utf-8").strip() == "stopped":
            print("Scheduler stopped from dashboard. Waiting...")
            time.sleep(interval_seconds)
            continue
        run_once(cfg)
        time.sleep(interval_seconds)

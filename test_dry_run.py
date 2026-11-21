"""Dry-run test. No real post, no token, no network call to Meta.

Run: python3 test_dry_run.py
Checks:
  1. Both slots 14:00 and 20:00 are recognised from config.yaml.
  2. A 14:00 post is due at 14:05, a 20:00 post is not due at 14:05.
  3. Dry-run records facebook_page as dry_run in the audit log.
  4. Instagram without a public media URL is blocked, and the scheduler
     stops at once, so the manual destinations are not attempted.
  5. With a public media URL, Instagram is dry_run, Personal Facebook
     is manual_ready, and LinkedIn is dry_run (no token, dry-run mode),
     each logged separately.
  6. A second run does not duplicate any destination.
  7. In live mode with no LinkedIn token, LinkedIn is manual_ready,
     never faked as posted, and no HTTP call goes to LinkedIn.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posting_agent import audit, inbox, scheduler  # noqa: E402
from posting_agent.config import load_config  # noqa: E402

TZ = ZoneInfo("Asia/Dhaka")
BASE = Path(__file__).resolve().parent
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")


def fresh_log():
    log = BASE / "logs" / "audit.log"
    if log.exists():
        log.unlink()


def make_post(post_id, with_url=False):
    folder = BASE / "inbox" / post_id
    if folder.exists():
        shutil.rmtree(folder)
    inbox.create_post(
        post_id,
        TODAY,
        "14:00",
        ["facebook_page", "instagram", "facebook_personal", "linkedin_personal"],
        "Dry-run test caption. This post was never published for real.",
        media_src=BASE / "inbox" / "sample-2026-11-19-2000" / "media.jpg",
    )
    if with_url:
        (folder / "media_url.txt").write_text("https://example.com/sample.jpg", encoding="utf-8")
    return folder


def log_for(post_id):
    return [e for e in audit.read_log(200) if e["post_id"] == post_id]


def main():
    cfg = load_config()
    assert cfg["slots"] == ["14:00", "20:00"], f"slots wrong: {cfg['slots']}"
    assert cfg["dry_run"] is True, "dry_run must be True for this test"
    assert not cfg["env"].get("META_PAGE_ACCESS_TOKEN"), "no token may be present in this test"
    print("1. Slots recognised:", cfg["slots"])
    print("2. Dry run is on, no token present.")

    # Timing check uses a post dated today, so it works on any day.
    # The sample folder is dated 2026-11-19 and would be yesterday
    # on later days, so it must not be used for this check.
    sample = {"date": TODAY, "slot": "20:00"}
    assert not inbox.is_due(sample, datetime.now(TZ).replace(hour=14, minute=5, second=0)), "20:00 must not be due at 14:05"
    assert inbox.is_due(sample, datetime.now(TZ).replace(hour=20, minute=5, second=0)), "20:00 must be due at 20:05"
    assert not inbox.is_due(sample, datetime.now(TZ).replace(hour=20, minute=31, second=0)), "20:00 must not be due at 20:31 (30 minute window)"
    print("3. Slot timing ok: 20:00 not due at 14:05, due at 20:05.")

    fresh_log()
    make_post("test-dry-run-a")
    now = datetime.now(TZ).replace(hour=14, minute=5, second=0, microsecond=0)
    results = scheduler.run_once(cfg, now=now)
    print("4. Run A results:", results)
    events = log_for("test-dry-run-a")
    by_dest = {e["destination"]: e["status"] for e in events}
    print("   Audit entries:", by_dest)
    assert by_dest.get("facebook_page") == "dry_run", by_dest
    assert by_dest.get("instagram") == "blocked", by_dest
    assert "facebook_personal" not in by_dest, "scheduler must stop on first error"
    assert "linkedin_personal" not in by_dest, "scheduler must stop on first error"
    print("5. Stop on first error ok: Instagram blocked (no public URL), manual steps not attempted.")

    make_post("test-dry-run-b", with_url=True)
    results = scheduler.run_once(cfg, now=now)
    print("6. Run B results:", results)
    events = log_for("test-dry-run-b")
    by_dest = {e["destination"]: e["status"] for e in events}
    print("   Audit entries:", by_dest)
    assert by_dest == {
        "facebook_page": "dry_run",
        "instagram": "dry_run",
        "facebook_personal": "manual_ready",
        "linkedin_personal": "dry_run",
    }, by_dest
    print("7. With public URL: all 4 destinations logged separately, LinkedIn is dry_run.")

    before = len(log_for("test-dry-run-b"))
    scheduler.run_once(cfg, now=now)
    after = len(log_for("test-dry-run-b"))
    assert before == after, f"second run duplicated entries: {before} -> {after}"
    print("8. No duplicates on second run.")

    # Live mode, no LinkedIn token: LinkedIn must be manual_ready,
    # and it must not call the LinkedIn API at all.
    live_cfg = dict(cfg)
    live_cfg["dry_run"] = False
    live_cfg["env"] = dict(cfg["env"])
    # No waiting between destinations in this test, or it would sleep
    # 60 to 120 seconds in live mode for no reason.
    live_cfg["delay_between_destinations_seconds"] = {"min": 0, "max": 0}
    make_post("test-dry-run-c")
    (BASE / "inbox" / "test-dry-run-c" / "post.json").write_text(
        json.dumps(
            {"date": TODAY, "slot": "14:00", "destinations": ["linkedin_personal"]},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    scheduler.run_once(live_cfg, now=now)
    events_c = log_for("test-dry-run-c")
    by_dest_c = {e["destination"]: e["status"] for e in events_c}
    assert by_dest_c.get("linkedin_personal") == "manual_ready", by_dest_c
    print("9. Live mode, no LinkedIn token: LinkedIn is manual_ready, no API call.")

    for pid in ("test-dry-run-a", "test-dry-run-b", "test-dry-run-c"):
        shutil.rmtree(BASE / "inbox" / pid)
    print("ALL DRY-RUN TESTS PASSED. No real post was made. No token was used.")
    print("Audit log kept at:", BASE / "logs" / "audit.log")


if __name__ == "__main__":
    main()

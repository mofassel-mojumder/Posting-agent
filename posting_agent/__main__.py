"""Run the Posting Agent.

  python -m posting_agent            - scheduler loop, one pass per minute
  python -m posting_agent --once     - one pass only, then stop
  python -m posting_agent dashboard  - local dashboard on http://localhost:8765

Dry-run is the default. Nothing posts for real until .env has a real
Meta token and DRY_RUN=false. See README.md first.
"""
import argparse

from .config import load_config
from .scheduler import run_loop, run_once


def main():
    parser = argparse.ArgumentParser(prog="posting_agent")
    parser.add_argument("--once", action="store_true", help="one scheduler pass, then stop")
    parser.add_argument("command", nargs="?", default="", help="dashboard")
    args = parser.parse_args()
    if args.command == "dashboard":
        from .dashboard import main as dashboard_main

        dashboard_main()
        return
    cfg = load_config()
    print("Posting Agent v1")
    print("Slots:", cfg["slots"], "| Dry run:", cfg["dry_run"], "| Max per day:", cfg.get("max_posts_per_day"))
    if args.once:
        results = run_once(cfg)
        print("Results:", results)
    else:
        run_loop(cfg)


if __name__ == "__main__":
    main()

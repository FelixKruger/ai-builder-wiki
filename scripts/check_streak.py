#!/usr/bin/env python3
"""
Prove the daily automation is actually producing contributions.

The wiki updating is not the same thing as the contribution graph turning
green — for three months this repo committed every single day while the graph
stayed empty, because every commit was authored by `github-actions[bot]` and
GitHub only counts commits authored by an address linked to your account.

This script queries GitHub's real contribution calendar (the same data behind
the graph on your profile) and reports the current streak and any gaps.

Usage:
    python scripts/check_streak.py                # last 30 days
    python scripts/check_streak.py --days 90
    python scripts/check_streak.py --user someone

Requires the `gh` CLI, authenticated (`gh auth login`).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

DEFAULT_USER = "FelixKruger"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_calendar(user: str, days: int) -> list[tuple[str, int]]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    proc = subprocess.run(
        [
            "gh", "api", "graphql",
            "-f", f"query={QUERY}",
            "-F", f"login={user}",
            "-F", f"from={start.strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "-F", f"to={end.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"gh api failed:\n{proc.stderr}", file=sys.stderr)
        sys.exit(2)

    data = json.loads(proc.stdout)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    out = []
    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            out.append((day["date"], day["contributionCount"]))
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=DEFAULT_USER)
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()

    cal = fetch_calendar(args.user, args.days)
    if not cal:
        print("No calendar data returned.")
        return 2

    today = date.today().isoformat()
    # Today is still in progress — judge the streak from yesterday backwards.
    closed = [(d, c) for d, c in cal if d < today]

    streak = 0
    for d, c in reversed(closed):
        if c > 0:
            streak += 1
        else:
            break

    gaps = [d for d, c in closed if c == 0]
    covered = sum(1 for _, c in closed if c > 0)
    today_count = next((c for d, c in cal if d == today), 0)

    print(f"Contribution check for @{args.user} - last {len(closed)} complete days\n")

    # Compact calendar strip: # = contributed, . = empty, ? = today (in progress)
    strip = "".join("#" if c > 0 else ("." if d < today else "?") for d, c in cal)
    print(f"  {cal[0][0]}  {strip}  {cal[-1][0]}")
    print("  legend: # contributed   . empty   ? today (still in progress)\n")

    print(f"  current streak : {streak} day(s)")
    print(f"  days covered   : {covered}/{len(closed)}")
    print(f"  today ({today}) : {today_count} contribution(s)"
          + ("" if today_count else "  <- not yet; the 17:00 UTC safety net still has time"))

    if gaps:
        print(f"\n  {len(gaps)} day(s) with no contribution:")
        for d in gaps[-14:]:
            print(f"    {d}")
        if len(gaps) > 14:
            print(f"    ... and {len(gaps) - 14} earlier")

    print()
    if covered == len(closed):
        print("PASS - every completed day in the window has at least one contribution.")
        return 0
    print(f"INCOMPLETE - {len(gaps)} day(s) missing. If these predate the automation "
          f"fix, they are expected; days after it are a real failure worth investigating "
          f"in the Actions log.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env /usr/bin/python3
"""Exit 0 if #ext-{{PRODUCT_LOWER}}-experiment-announcements has a message newer than the stored timestamp, else 1.

Usage:
  SLACK_TOKEN=xoxb-... check_new_experiments.py          # check only
  SLACK_TOKEN=xoxb-... check_new_experiments.py --mark   # store newest ts (run after a round)

Token needs channels:history and the bot must be a member of the channel.
Exit 2 = error (treat as "do not run a round"; the error is on stderr).
"""
import json, os, sys, urllib.parse, urllib.request
from decimal import Decimal
from pathlib import Path

CHANNEL = "SLACK_ID"
STATE = Path(__file__).with_name(".experiment-reporter-last-ts")


def newest_ts(token):
    q = urllib.parse.urlencode({"channel": CHANNEL, "limit": 1})
    req = urllib.request.Request(
        f"https://slack.com/api/conversations.history?{q}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    if not data.get("ok"):
        raise RuntimeError(f"Slack error: {data.get('error')}")
    msgs = data["messages"]
    return msgs[0]["ts"] if msgs else None


def main():
    token = os.environ.get("SLACK_TOKEN")
    if not token:
        sys.exit("SLACK_TOKEN is not set")
    try:
        newest = newest_ts(token)
    except Exception as e:  # network or API failure must not start a round
        print(e, file=sys.stderr)
        return 2
    if newest is None:
        return 1
    if "--mark" in sys.argv:
        STATE.write_text(newest)
        print(f"marked {newest}")
        return 0
    last = STATE.read_text().strip() if STATE.exists() else None
    if last is None or Decimal(newest) > Decimal(last):
        print(f"new work: newest {newest}, last seen {last}")
        return 0
    print("no new work")
    return 1


if __name__ == "__main__":
    sys.exit(main())

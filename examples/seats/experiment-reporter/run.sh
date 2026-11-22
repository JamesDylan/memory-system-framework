#!/bin/bash
# Gate, then one capped headless round. Needs SLACK_TOKEN (gate), SLACK_BOT_TOKEN and SLACK_TEAM_ID (seat). Tokens come from the env, never from a file.
set -u
cd "$(dirname "$0")"
. ./seat.conf
MODEL="${SEAT_MODEL:-$MODEL}"
case "$MODEL" in claude-*|haiku|sonnet|opus) ;; *) echo "bad MODEL: $MODEL" >&2; exit 1;; esac   # stop a typo costing a run
set -a; . "$HOME/.config/experiment-reporter.env"; set +a   # secrets live outside the repo
export SLACK_TOKEN="$SLACK_BOT_TOKEN"   # the gate script reads this name
export VAULT="$(cd ../../.. && pwd)"   # vault root, found from this script's folder (2_AREAS/Agents/<seat>/, the cwd after the cd above)
CHECK="$VAULT/2_AREAS/{{ORG}}/_metrics/check_new_experiments.py"

# Post one line to the output channel. Link previews off. Never fails the script.
post() {
  python3 - "$1" <<'PY' || true
import json, os, sys, urllib.request
body = json.dumps({"channel": os.environ.get("REPORTER_OUT_CHANNEL", "SLACK_ID"), "text": sys.argv[1],
                   "unfurl_links": False, "unfurl_media": False}).encode()
req = urllib.request.Request("https://slack.com/api/chat.postMessage", body, {
    "Authorization": "Bearer " + os.environ["SLACK_BOT_TOKEN"], "Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req, timeout=15)).get("ok"))
PY
}
alert() { post ":warning: experiment-reporter: $1 Check ~/.config/experiment-reporter.log and ~/.config/experiment-reporter.launchd.log."; }

rm -f .out/note.txt
/usr/bin/python3 "$CHECK"; rc=$?
[ "$rc" -eq 1 ] && exit 0                              # no new work: no model run
[ "$rc" -ne 0 ] && { alert "the gate failed (exit $rc), so no round ran."; exit 0; }   # Slack or token error: tell a person

claude -p "The vault is $VAULT. Do one round as set out in AGENTS.md, then stop." \
  --model "$MODEL" \
  --permission-mode dontAsk \
  --tools "$TOOLS" \
  --strict-mcp-config --mcp-config seat.mcp.json \
  --add-dir "$VAULT" \
  --output-format stream-json --verbose \
  --max-turns "$MAX_TURNS" --max-budget-usd "$MAX_BUDGET_USD" < /dev/null > "$HOME/.config/experiment-reporter.log" 2>&1  # full tool trace, outside the repo
crc=$?

# Mark the messages as seen only after a good round (a note exists), so a failed round retries on the next run.
if [ ! -s .out/note.txt ]; then
  alert "the round failed (exit $crc, no note written). The same messages will be retried on the next run."
  exit 0
fi
/usr/bin/python3 "$CHECK" --mark >/dev/null   # stores the exact ts (the seat stores a rounded one)

# The launcher posts the note. A quiet round is marked as seen but not posted.
NOTE="$(cat .out/note.txt)"
[ "$NOTE" = "No experiment updates." ] || post "$NOTE"

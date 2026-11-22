#!/bin/bash
# Gate, then one capped headless round. Settings are in seat.conf. Secrets come from the env file, never from the repo.
set -u
cd "$(dirname "$0")"
SEAT="$(basename "$PWD")"
VAULT="__VAULT__"
. ./seat.conf
MODEL="${SEAT_MODEL:-$MODEL}"
case "$MODEL" in claude-*|haiku|sonnet|opus) ;; *) echo "bad MODEL: $MODEL" >&2; exit 1;; esac   # stop a typo costing a run
set -a; . "$HOME/.config/$SEAT.env" || exit 1; set +a   # needs SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL
mkdir -p .out; rm -f .out/note.txt
./gate.sh || exit 0   # no new work or gate error: no model run
claude -p "Do one round as set out in AGENTS.md, then stop." \
  --model "$MODEL" \
  --permission-mode dontAsk \
  --tools "$TOOLS" \
  --strict-mcp-config --mcp-config seat.mcp.json \
  --add-dir "$VAULT" \
  --output-format stream-json --verbose \
  --max-turns "$MAX_TURNS" --max-budget-usd "$MAX_BUDGET_USD" < /dev/null > "$HOME/.config/$SEAT.log" 2>&1   # full trace, outside the repo

# Mark the work as seen only after a good round (a note exists), so a failed round retries next time.
[ -s .out/note.txt ] && ./gate.sh --mark

# The launcher posts the note; the seat never posts itself. Unfurl is off so link previews do not fill the channel.
[ -s .out/note.txt ] && /usr/bin/python3 - <<'PY'
import json, os, urllib.request
note = open(".out/note.txt").read().strip()
body = json.dumps({"channel": os.environ["SEAT_OUT_CHANNEL"], "text": note,
                   "unfurl_links": False, "unfurl_media": False}).encode()
req = urllib.request.Request("https://slack.com/api/chat.postMessage", body, {
    "Authorization": "Bearer " + os.environ["SLACK_BOT_TOKEN"], "Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req, timeout=15)).get("ok"))
PY

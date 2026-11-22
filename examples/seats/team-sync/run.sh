#!/bin/bash
# Gate, then one capped headless round. Settings are in seat.conf. Secrets come from the env file, never from the repo.
set -u
cd "$(dirname "$0")"
export VAULT="$(cd ../../.. && pwd)"   # vault root, found from this script's folder (2_AREAS/Agents/<seat>/, the cwd after the cd above)
. ./seat.conf
MODEL="${SEAT_MODEL:-$MODEL}"
case "$MODEL" in claude-*|haiku|sonnet|opus) ;; *) echo "bad MODEL: $MODEL" >&2; exit 1;; esac
# Same Google access, Slack bot, channel and owner as meeting-ingest. The bot also needs canvases:read and canvases:write.
set -a; . "$HOME/.config/meeting-ingest.env" || exit 1; set +a
export SEAT_DIR="$PWD"
mkdir -p .out; rm -f .out/canvas.md
./canvas.py collect   # publish or discard the draft {{OWNER}} decided on in Slack; no model
../meeting-ingest/gate.py || exit 0   # no new team meeting, or gate error: no model run
claude -p "Do one round as set out in AGENTS.md, then stop." \
  --model "$MODEL" \
  --permission-mode dontAsk \
  --tools "$TOOLS" \
  --strict-mcp-config --mcp-config seat.mcp.json \
  --add-dir "$VAULT" \
  --output-format stream-json --verbose \
  --max-turns "$MAX_TURNS" --max-budget-usd "$MAX_BUDGET_USD" < /dev/null > "$HOME/.config/team-sync.log" 2>&1

# Post first (it reads the meeting header in .in/), then mark seen: a failed round or post retries next time,
# up to MAX_FAILS rounds per meeting (law 5); then the meeting is given up and {{OWNER}} is warned.
if [ -s .out/canvas.md ] && ./canvas.py post; then ../meeting-ingest/gate.py --mark; else
  dead="$(../meeting-ingest/gate.py --fail)"
  [ -n "$dead" ] && ../meeting-ingest/review.py warn ":warning: team-sync gave up on meeting notes $dead after $MAX_FAILS failed rounds. See ~/.config/team-sync.log."
fi

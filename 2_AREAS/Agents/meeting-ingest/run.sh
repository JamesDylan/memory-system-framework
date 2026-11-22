#!/bin/bash
# Gate, then one capped headless round. Settings are in seat.conf. Secrets come from the env file, never from the repo.
set -u
cd "$(dirname "$0")"
SEAT="$(basename "$PWD")"
export VAULT="$(cd ../../.. && pwd)"   # vault root, found from this script's folder (2_AREAS/Agents/<seat>/, the cwd after the cd above)
. ./seat.conf
MODEL="${SEAT_MODEL:-$MODEL}"
case "$MODEL" in claude-*|haiku|sonnet|opus) ;; *) echo "bad MODEL: $MODEL" >&2; exit 1;; esac   # stop a typo costing a run
set -a; . "$HOME/.config/$SEAT.env" || exit 1; set +a   # needs SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL (#second-brain ID), SEAT_OWNER_ID ({{OWNER}}'s Slack user ID), GOOGLE_*
mkdir -p .out/pending; rm -f .out/note.txt
./review.py collect   # stage 3: apply {{OWNER}}'s Slack decisions from earlier rounds; runs every time, no model
../dispatcher/run.sh   # one queued job ({{OWNER}}'s "project <Name>" reply); no open job, no model run. Own log and caps.
./gate.py || exit 0   # no new work or gate error: no model run
claude -p "Do one round as set out in AGENTS.md, then stop." \
  --model "$MODEL" \
  --permission-mode dontAsk \
  --tools "$TOOLS" \
  --strict-mcp-config --mcp-config seat.mcp.json \
  --add-dir "$VAULT" \
  --output-format stream-json --verbose \
  --max-turns "$MAX_TURNS" --max-budget-usd "$MAX_BUDGET_USD" < /dev/null > "$HOME/.config/$SEAT.log" 2>&1   # full trace, outside the repo

# Mark the work as seen only after a good round (a note exists), so a failed round retries next time.
[ -s .out/note.txt ] && ./gate.py --mark

# The launcher posts the note and each new diff (as thread replies); the seat never posts itself. Link previews off.
[ -s .out/note.txt ] && ./review.py post

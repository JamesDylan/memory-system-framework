#!/bin/bash
# Gate (an open job), then one capped headless round for that job, then finish (hub script, Slack reply, commit). No job: no model run.
set -u
cd "$(dirname "$0")"
export VAULT="$(cd ../../.. && pwd)"   # vault root, found from this script's folder (2_AREAS/Agents/<seat>/, the cwd after the cd above)
. ./seat.conf
MODEL="${SEAT_MODEL:-$MODEL}"
case "$MODEL" in claude-*|haiku|sonnet|opus) ;; *) echo "bad MODEL: $MODEL" >&2; exit 1;; esac
# shortcut: shares meeting-ingest's env (same bot, channel, owner); give it its own dispatcher.env when a second seat queues jobs.
set -a; . "$HOME/.config/meeting-ingest.env" || exit 1; set +a
mkdir -p .out; rm -f .out/note.txt .out/created.txt
JOB="$(./dispatch.py next)" || exit 0   # claims the oldest open job; none: no model run
export DISPATCH_JOB="$JOB"               # guard.py reads the job's name from it
../seat-qmd.sh || exit 1   # qmd search: shared vault only, never private notes
claude -p "Run the job in $JOB as set out in AGENTS.md, then stop." \
  --model "$MODEL" \
  --permission-mode dontAsk \
  --tools "$TOOLS" \
  --strict-mcp-config --mcp-config seat.mcp.json \
  --add-dir "$VAULT" \
  --output-format stream-json --verbose \
  --max-turns "$MAX_TURNS" --max-budget-usd "$MAX_BUDGET_USD" < /dev/null > "$HOME/.config/dispatcher.log" 2>&1
./dispatch.py finish "$JOB"

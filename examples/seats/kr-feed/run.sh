#!/bin/bash
# Weekly kr-feed round. No model. Secrets come from the env file, never from the repo.
set -u
cd "$(dirname "$0")"
export VAULT="$(cd ../../.. && pwd)"   # vault root, found from this script's folder (2_AREAS/Agents/<seat>/, the cwd after the cd above)
set -a; . "$HOME/.config/kr-feed.env" || exit 1; set +a   # PRODUCTBOARD_TOKEN, SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL (#second-brain ID), SEAT_OWNER_ID ({{OWNER}}'s Slack user ID)
./feed.py collect   # apply or drop last week's proposal first
./feed.py propose

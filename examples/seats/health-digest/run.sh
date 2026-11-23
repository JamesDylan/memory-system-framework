#!/bin/bash
# Weekly health-digest round. No model. Same entry point for both clocks (launchd and GitHub Actions).
# Secrets come from the env file on a Mac, or from the Actions secret and variable; never from the repo.
set -u
cd "$(dirname "$0")"
export VAULT="$(cd ../../.. && pwd)"   # vault root, found from this script's folder (2_AREAS/Agents/<seat>/)
ENVF="$HOME/.config/health-digest.env"   # SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL
[ -f "$ENVF" ] && { set -a; . "$ENVF"; set +a; }
exec python3 ./digest.py "$@"   # --dry-run prints instead of posting; --selftest needs no network

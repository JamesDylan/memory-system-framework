#!/bin/bash
# The clock's check. Two modes:
#   ./gate.sh          exit 0 only if there is new work since the stored mark. No model runs otherwise.
#   ./gate.sh --mark   store the newest item as seen. run.sh calls this after a round that wrote a note.
# Replace this stub. Until then the seat never runs.
[ "${1:-}" = "--mark" ] && exit 0
exit 1

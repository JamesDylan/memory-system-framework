#!/bin/bash
# Run by a seat's run.sh before its model round. The seat's qmd MCP uses the `seats` index (seat.mcp.json),
# which must hold the shared vault only. Stop the round if it holds the private vault; else refresh it.
# The index is set up by .scripts/qmd-bootstrap.sh.
if qmd --index seats collection list 2>/dev/null | grep -q memory_private; then
  echo "seat-qmd: the seats index holds memory_private; no model run" >&2; exit 1
fi
(qmd --index seats update && qmd --index seats embed) >/dev/null 2>&1   # stale search beats no run
exit 0

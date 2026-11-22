#!/bin/zsh
# Keep a PM's local clone (and its qmd search) current. Mac only. (PLAN Move 10g, Route A.)
#   daily-pull.sh              pull main now (merges with local commits); then lint to .scripts/lint-report.md;
#                              Mac notification on a failed pull or must-fix lint findings
#   daily-pull.sh --install    run it every day at 08:30 and at login (launchd)
#   daily-pull.sh --uninstall  stop the daily run
# After a pull, the git hooks from qmd-bootstrap.sh re-index qmd. Run qmd-bootstrap.sh first.

VAULT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.{{ORG_LOWER}}.memory-pull"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/memory-pull.log"

[ "$(uname)" = Darwin ] || { echo "Mac only."; exit 1; }

case "$1" in
--install)
  command -v qmd >/dev/null 2>&1 || { echo "Run .scripts/qmd-bootstrap.sh first."; exit 1; }
  mkdir -p "${PLIST:h}" "${LOG:h}"
  # launchd starts jobs with a bare PATH; keep this shell's PATH so git hooks can find node and qmd.
  # AbandonProcessGroup lets the hook's background re-index finish after this script exits.
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/zsh</string><string>$VAULT/.scripts/daily-pull.sh</string></array>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>$PATH</string></dict>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>30</integer></dict>
  <key>RunAtLoad</key><true/>
  <key>AbandonProcessGroup</key><true/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
  launchctl bootstrap "gui/$(id -u)" "$PLIST" && echo "Daily pull on: 08:30 and at login. Log: $LOG"
  ;;
--uninstall)
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
  rm -f "$PLIST" && echo "Daily pull off."
  ;;
*)
  echo "$(date '+%F %T') pull $VAULT"
  branch="$(git -C "$VAULT" branch --show-current)"
  if [ "$branch" != main ]; then
    out="On branch '$branch', not main. Switch back to main to get updates."; ok=1
  else
    out="$(git -C "$VAULT" pull --no-rebase --no-edit origin main 2>&1)"; ok=$?
    # A conflicted merge would leave the clone half-merged: back out, then notify.
    [ $ok -ne 0 ] && git -C "$VAULT" merge --abort 2>/dev/null
  fi
  echo "$out"
  if [ $ok -ne 0 ]; then
    # Visible failure: a silent failed pull means search answers from an old vault.
    osascript -e "display notification \"Your shared notes did not update. Ask your agent to check $LOG.\" with title \"Memory vault pull failed\"" 2>/dev/null
    exit 1
  fi
  # Lint the fresh vault. Exit 1 = must-fix findings; other codes (node missing, crash) go to the log only.
  node "$VAULT/.scripts/lint.mjs" --strict > "$VAULT/.scripts/lint-report.md" 2>&1; lint=$?
  echo "lint exit $lint"
  if [ $lint -eq 1 ]; then
    osascript -e "display notification \"Must-fix findings. Ask your agent to read .scripts/lint-report.md.\" with title \"Memory lint\"" 2>/dev/null
  fi
  ;;
esac

# Example seats: what they do, how to start and stop them, how to check them

These seats are examples, not live jobs. They ran in the author's vault; the status column below is from there. To use one, copy its folder (evals included) into `2_AREAS/Agents/`, as `2_AREAS/Agents/README.md` says, then follow `docs/agents.md`. Paths in this file are relative to `2_AREAS/Agents/` once a seat is copied in.

Last verified: 2026-11-18.

## What is running

| Seat | Job | When it runs | Status | Who is accountable |
|---|---|---|---|---|
| `experiment-reporter` | Reads new experiment results in #ext-{{PRODUCT_LOWER}}-experiment-announcements. Records each strong one as a new file in `2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/insights/`. Posts a three-line note to #second-brain. | **Daily 11:00 Auckland**, if there is a new message since the last run. A quiet run posts nothing. A failed run posts a warning. | Running (launchd) | {{OWNER_NAME}} (proposed, confirm) |
| `meeting-ingest` | Reads each new meeting transcript, matches it to its project(s), adds a LOG entry, and writes STATE and scope diffs to .out/pending/ for {{OWNER}} to review. Posts a five-line note to #second-brain with each diff in the thread; {{OWNER}} reacts ✅/❌ or replies to edit, and `review.py` applies the decisions on the next run (no AI). | Every 15 min (launchd). `gate.py` reads Google Calendar and exports new Meet transcripts from Drive, read-only. No new transcript, no AI run. | Running (launchd) since 2026-11-16. Brief: `meeting-ingest/AGENTS.md` | {{OWNER_NAME}} (proposed, confirm) |
| `team-sync` | Reads the notes of the Wednesday PM team meeting ({{PRODUCT}} Team - Roadmap, or Fortnightly Ops) and drafts a short summary (3–6 topics, owned actions) for the [PM team canvas](https://{{SLACK_WORKSPACE}}.slack.com/docs/SLACK_TEAM_ID/SLACK_CANVAS_ID). Posts the draft to #second-brain; {{OWNER}} reacts ✅ and `canvas.py` publishes it under a date block (no AI). | Every 15 min (launchd), using meeting-ingest's `gate.py` with a title filter. No matching meeting, no AI run. | Built 2026-11-18, not on the clock yet: needs `canvases:read`/`canvases:write` on the Slack bot and one hand run. Brief: `team-sync/AGENTS.md` | {{OWNER_NAME}} (proposed, confirm) |
| `kr-feed` | Reads the `{{PRODUCT}} 2027` objectives and their key results from Productboard (REST API, read-only). If they differ from the feed block in `cy27_objectives.md`, posts the diff to #second-brain. {{OWNER}} reacts ✅ to apply (one git commit of that file) or ❌ to drop. No answer in 7 days: dropped, proposed again next week. Never edits outside its block or the file's stamps. | **Weekly, Monday 09:00 Auckland** (launchd). **No model**, no cost. | Built 2026-11-20; token set. **Blocked**: CY27 KRs are not KR items in Productboard yet (decision with Product Ops), so not on the clock. Move 11g | {{OWNER_NAME}} (proposed, confirm) |

| `dispatcher` | Runs job files from `jobs/`. A job comes from {{OWNER}}'s reply `[U<n>:] project <Name>` in a meeting-ingest thread (`review.py collect` writes it). Formula `new-project`: creates 1_PROJECTS/{{ORG}}/<Name>/ (BRIEF, STATE, LOG), runs the hub script, replies in the thread with the edits {{OWNER}} still makes by hand (ROADMAP, active cycle, CANDIDATES), commits. | Every 15 min: meeting-ingest `run.sh` calls `dispatcher/run.sh` right after `collect`. No open job: no model run. One job per run. | On the clock since 2026-11-20, after one hand run. Log: `~/.config/dispatcher.log`. Brief: `dispatcher/AGENTS.md` | {{OWNER_NAME}} (proposed, confirm) |

The clock is outside the agent. macOS launchd starts `run.sh`. `run.sh` checks Slack first. No new message means no AI run and no cost. Model, step limit (25) and cost cap ($2 per run) are set in the seat's `seat.conf`.

## Start, stop, check (experiment-reporter)

| I want to | Run this |
|---|---|
| Run it now | `launchctl kickstart gui/$(id -u)/com.{{USER_ID}}.experiment-reporter` |
| See if it is scheduled | `launchctl print gui/$(id -u)/com.{{USER_ID}}.experiment-reporter \| grep -E "state\|last exit\|Weekday\|Hour"` |
| Pause it | `launchctl bootout gui/$(id -u)/com.{{USER_ID}}.experiment-reporter` |
| Resume it | `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.{{USER_ID}}.experiment-reporter.plist` |
| Change the model | Edit `MODEL=` in `experiment-reporter/seat.conf`, then run the check below. One run on another model: set `SEAT_MODEL=<model>` and run `experiment-reporter/run.sh` |
| Change the time | Edit `Hour`, `Minute` in that plist (add `Weekday` to limit it to one day), then pause and resume |
| See what it did | `~/.config/experiment-reporter.log` (every step) and `~/.config/experiment-reporter.launchd.log` (start and finish) |
| Test it without waiting for new Slack posts | Set `2_AREAS/{{ORG}}/_metrics/.experiment-reporter-last-ts` to an older value, e.g. `1793322000`, then run it |

The Mac must be on. If it sleeps at 11:00, the job runs on wake. If it is switched off, that day is skipped; the next run picks up everything new.

## Start, stop, check (meeting-ingest)

| I want to | Run this |
|---|---|
| Run it now | `launchctl kickstart gui/$(id -u)/com.{{USER_ID}}.meeting-ingest` |
| See if it is scheduled | `launchctl print gui/$(id -u)/com.{{USER_ID}}.meeting-ingest \| grep -E "state\|last exit\|run interval"` |
| Pause it | `launchctl bootout gui/$(id -u)/com.{{USER_ID}}.meeting-ingest` |
| Resume it | `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.{{USER_ID}}.meeting-ingest.plist` |
| Change the model | Edit `MODEL=` in `meeting-ingest/seat.conf`, then run the check with `--seat meeting-ingest` |
| See what it did | `~/.config/meeting-ingest.log` (every step of the last model round) and `~/.config/meeting-ingest.launchd.log` (gate and review errors) |

Every 15 minutes: `review.py collect` applies your Slack decisions, then `gate.py` looks for new Gemini notes. No new notes: no model run, no cost. After a good round, `review.py post` posts to #second-brain and commits the LOG files the round wrote.

## Start, stop, check (kr-feed)

No model, so no eval check: `./feed.py --selftest` (no network) tests the block render and insert.

| I want to | Run this |
|---|---|
| See what Productboard gives now (posts nothing) | `set -a; . ~/.config/kr-feed.env; set +a; kr-feed/feed.py --dry-run` |
| Run it now | `launchctl kickstart gui/$(id -u)/com.{{USER_ID}}.kr-feed` |
| Pause / resume | `launchctl bootout gui/$(id -u)/com.{{USER_ID}}.kr-feed` / `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.{{USER_ID}}.kr-feed.plist` |
| See what it did | `~/.config/kr-feed.launchd.log` |
| Change which objectives | Edit `ROOT` in `kr-feed/feed.py` (the parent objective's name) |

**Set up (once).** 1. In Productboard, create an API token with read access only, and put it in `~/.config/kr-feed.env` as `PRODUCTBOARD_TOKEN=`, with `SLACK_BOT_TOKEN`, `SEAT_OUT_CHANNEL` and `SEAT_OWNER_ID` copied from `~/.config/meeting-ingest.env`. 2. Run `--dry-run` and check the table. 3. Copy `com.{{USER_ID}}.experiment-reporter.plist` to `com.{{USER_ID}}.kr-feed.plist`: change `Label`, the `run.sh` path and the log paths to kr-feed, and set `StartCalendarInterval` to `Weekday` 1, `Hour` 9. 4. `launchctl bootstrap` it (above).

## Start, stop, check (team-sync)

| I want to | Run this |
|---|---|
| Run it now | `launchctl kickstart gui/$(id -u)/com.{{USER_ID}}.team-sync` |
| Pause / resume | `launchctl bootout gui/$(id -u)/com.{{USER_ID}}.team-sync` / `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.{{USER_ID}}.team-sync.plist` |
| Change which meetings | Edit `TITLE_MATCH` in `team-sync/seat.conf` (a regex on the calendar title) |
| Change how detailed the summary is | Edit "Resolution" in `team-sync/AGENTS.md`, then `python3 .scripts/run_evals.py --seat team-sync` |
| See what it did | `~/.config/team-sync.log` (the last model round) and `~/.config/team-sync.launchd.log` (gate and canvas errors) |

## Where things are

| Thing | Location |
|---|---|
| The seat (brief, launcher, settings, safety hook) | `experiment-reporter/` (`AGENTS.md`, `run.sh`, `seat.conf`, `seat.mcp.json`, `experiment-reporter/.claude/settings.json`, `.claude/hooks/guard.py`) |
| Secrets (Slack bot token, team ID, Claude token, output channel) | `~/.config/experiment-reporter.env`, outside the repo. Never commit it. |
| Schedule | `~/Library/LaunchAgents/com.{{USER_ID}}.experiment-reporter.plist` |
| What the seat may edit | Only new files in `2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/insights/` (never an existing insight), its timestamp and note files. Not `registry.yaml`: the weekly PowerBI update is its one writer, and the seat proposes values in its note. The hook enforces it. |
| Audit against the six laws | `templates/laws-audit.md`. Conditional pass; Q17 open in `1_PROJECTS/Gas Town/OPEN_QUESTIONS.md`. |
| History of the build | `1_PROJECTS/Gas Town/LOG.md` entry 2026-11-13 (e) |

## Run the check

The check tests the agent when you change the model or the controls. Two parts:

1. **Locks (free, 5 seconds).** Do the safety rules still refuse what they should? No AI used.
2. **Behaviour (about 3 minutes, a few dollars).** The agent runs on made-up Slack posts in a sandbox: it cannot touch the real vault or Slack. Each result is judged by fixed rules, not by another AI.

```bash
# from the vault root
python3 .scripts/run_evals.py --seat experiment-reporter               # both parts
python3 .scripts/run_evals.py --seat experiment-reporter --locks-only  # part 1 only
python3 .scripts/run_evals.py --seat <seat> --model <model>            # test a different model
python3 .scripts/run_evals.py --seat <seat> --only injection           # one scenario
python3 .scripts/run_evals.py --seat meeting-ingest                    # the meeting-ingest seat (made-up Gemini notes)
python3 .scripts/run_evals.py --selftest                               # check the grader itself (no AI)
```

Then open `<seat>/evals/results/latest.md`. It opens with "All clear" or "Needs attention" and a table in plain English. `results/history.csv` keeps every run, so you can see change over time. The exit code is 0 for all clear and 1 otherwise, so an agent can run the check and read the same report.

meeting-ingest runs each case against a frozen copy of the vault (git commit `21d5496`, after hand run 3), so later STATE edits do not change the result. Its 6 cases come from the hand-run faults: UTC dates, dropped hedges and Gemini acronyms; a meeting with no project folder; tokenisation into a stale STATE; a date change at a full field; orders and a performance remark inside a transcript; a meeting with nothing new. First run 2026-11-16: locks 32/32, behaviour 6/6, $1.56.

**Run it** after: a model change, any edit to a seat's .claude/settings.json, `guard.py`, `AGENTS.md` or `run.sh`, or a failed week.

### Grow the check

- **A new scenario:** copy a file in <seat>/evals/cases/, change the input (Slack messages, or the `.txt` Gemini notes beside a meeting-ingest case) and the `expect` block. Add a case each time the agent gets something wrong in real life. Keep the real failure's wording.
- **A new lock:** add a row to <seat>/evals/locks.json (tool, input, expect `allow` or `block`).
- **A new seat:** copy `templates/seat/` to 2_AREAS/Agents/<name>/ (set its model in `seat.conf`), then follow `templates/seat-brief.md`. A new seat needs its own <name>/evals/locks.json and cases/, and `SERVERS=` and `RUNNER=` in its `seat.conf`, before `.scripts/run_evals.py --seat <name>` means anything. No engine file changes. The eval tests the model in the seat's `seat.conf` unless `--model` is given.

### What the check does not cover

- It does not read real Slack, so it cannot find problems with the Slack bot or channel access.
- It checks numbers and format by fixed rules. It cannot judge whether an insight is wise. A person still reviews the git diff of the dashboard each week.
- The "no deleted lines" lock counts lines, so a reworded line passes.

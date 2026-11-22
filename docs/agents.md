# Agents: set up, run, test and build

This guide covers the scheduled agents ("seats") in `2_AREAS/Agents/`. A new vault has none: the seats below ship as examples in `examples/seats/`, and you copy in the ones you want. A person can follow it, or you can hand it to your own agent:

> Read `docs/agents.md` and set up the `<seat>` seat in this vault. Do one step at a time and show me each command before you run it. Never write a secret into the repo: tell me which file to open and which line to add, and I will paste the value myself.

Paths are relative to the shared vault (the folder `init-vault.py` built), not to this framework folder.

## What is where

| Thing | Where | In git? |
|---|---|---|
| Example seats to copy from | `examples/seats/<seat>/` | Yes (engine) |
| Your seats: brief, launcher, gate, settings, safety hook | `2_AREAS/Agents/<seat>/` | Yes |
| A seat's evals: locks and behaviour cases | `2_AREAS/Agents/<seat>/evals/` | Yes. `evals/results/` is written locally |
| The eval runner | `.scripts/run_evals.py` (engine) | Yes |
| Jobs the dispatcher runs | `2_AREAS/Agents/jobs/` | Yes, one file per job |
| Template for a new seat | `templates/seat/`, `templates/seat-brief.md` | Yes |
| Safety audit before a seat goes on a clock | `templates/laws-audit.md` | Yes |
| What runs in this vault | `2_AREAS/Agents/README.md` | Yes |
| Operating notes for each example seat (start, stop, check) | `examples/seats/README.md` | Yes |
| **Secrets** (tokens, channel IDs) | `~/.config/<seat>.env` | **No. Never** |
| **The clock** (macOS launchd job) | `~/Library/LaunchAgents/com.<you>.<seat>.plist`, made from `templates/seat/launchd.plist` | No |
| Logs | `~/.config/<seat>.log` (last model round), `~/.config/<seat>.launchd.log` (gate and launcher) | No |
| Run state (what was seen, pending diffs, drafts) | `2_AREAS/Agents/<seat>/.out/` | No (gitignored) |

Everything outside the vault is per person and per machine. This guide is how you recreate it.

## The example seats

| Seat | Job | Reads | Env file | Clock |
|---|---|---|---|---|
| `meeting-ingest` | Logs each new meeting to its projects and drafts STATE changes for ✅ in Slack | Google Calendar and Meet transcripts in Drive (read-only) | `meeting-ingest.env` | Every 15 min |
| `dispatcher` | Runs job files created by your Slack replies (first formula: `new-project`) | Job files, the vault | Shares `meeting-ingest.env` | Called by `meeting-ingest/run.sh` |
| `team-sync` | Drafts the team-meeting summary for a Slack canvas | Meeting notes (through meeting-ingest's gate) | Shares `meeting-ingest.env` | Every 15 min |
| `experiment-reporter` | Files each strong experiment result as an insight | One Slack channel | `experiment-reporter.env` | Daily |
| `kr-feed` | Proposes key-result changes from Productboard. No model | Productboard API (read-only) | `kr-feed.env` | Weekly |

Start with one seat. `meeting-ingest` gives the most value; `kr-feed` is the cheapest (no model at all).

## Set up a seat

### 1. Before you start

- macOS (the clock is launchd). Python 3 at `/usr/bin/python3`. Node, and `qmd` for search.
- Claude Code installed, with `claude` on your PATH.
- The vault built with `init-vault.py` and committed to git.
- The seat copied in, evals included: `cp -R examples/seats/<seat> 2_AREAS/Agents/` (from the vault root). Paths below are relative to the vault root.
- Seats that call another seat need it copied in too: `team-sync` runs `meeting-ingest`'s gate (without it, every round exits quietly), and `meeting-ingest` calls `dispatcher`.

### 2. Make the accounts and tokens (you, not your agent)

| Needed by | What | How |
|---|---|---|
| Every seat that runs a model | `CLAUDE_CODE_OAUTH_TOKEN` | Run `claude setup-token` and copy the token |
| Every seat that posts | A Slack app with a bot user | Create an app at api.slack.com. Bot scopes: `channels:history`, `groups:history`, `chat:write`, `reactions:read`. For `team-sync` also `canvases:read` and `canvases:write`. Install it and copy the bot token (`xoxb-…`) as `SLACK_BOT_TOKEN`. Invite the bot to every channel a seat reads or posts to |
| Every seat that posts | `SEAT_OUT_CHANNEL`, `SEAT_OWNER_ID` | The ID of the channel where seats post notes (one private channel works well), and your own Slack user ID. Only replies from this user are read as commands |
| `meeting-ingest`, `team-sync` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` | An OAuth client in Google Cloud with read-only scopes `calendar.readonly` and `drive.readonly`, and a refresh token for your account. The seat never sees these: only the gate script uses them to export new transcripts |
| `experiment-reporter` | `SLACK_TEAM_ID` | Your Slack workspace ID |
| `kr-feed` | `PRODUCTBOARD_TOKEN` | A Productboard API token with read access only |

### 3. Write the env file

Create `~/.config/<seat>.env` (outside the repo) with one `NAME=value` line per secret from step 2, then lock it down:

```bash
chmod 600 ~/.config/<seat>.env
```

### 4. Fill the values that sit in code

The export replaces your organisation's IDs with markers. Search the seat for them and put your own values in:

```bash
grep -rn "SLACK_ID\|SLACK_TEAM_ID\|SLACK_CANVAS_ID" 2_AREAS
```

- `experiment-reporter`: the channel it reads (`IN_CH` in `.claude/hooks/guard.py`, `CHANNEL` in `2_AREAS/<Org>/_metrics/check_new_experiments.py`, and the brief). Use the same ID in `experiment-reporter/evals/locks.json` so the lock still tests the real channel.
- `team-sync`: `CANVAS_ID` in `seat.conf` and the team ID in `canvas.py`. `TITLE_MATCH` in `seat.conf` picks which meetings it summarises.
- Read the brief (`AGENTS.md`) once. It names your channels, projects and the person who approves.

### 5. Check it before it runs

```bash
/usr/bin/python3 2_AREAS/Agents/<seat>/.claude/hooks/guard.py --selftest   # the safety hook
python3 .scripts/run_evals.py --locks-only --seat <seat>                    # free, seconds: do the locks still refuse?
python3 .scripts/run_evals.py --seat <seat>                                 # a few dollars: behaviour on made-up input, in a sandbox
```

Scripts with their own self-check: `dispatcher/dispatch.py`, `meeting-ingest/gate.py`, `meeting-ingest/review.py`, `team-sync/canvas.py` and `kr-feed/feed.py`, each with `--selftest`.

### 6. One run by hand

```bash
2_AREAS/Agents/<seat>/run.sh
```

Read the note it posts and the git diff it leaves. Fix the brief or the gate before you go on.

### 7. Put it on a clock

```bash
SEAT=<seat>; DIR="$(pwd -P)/2_AREAS/Agents/$SEAT"; PL=~/Library/LaunchAgents/com.$(whoami).$SEAT.plist
sed -e "s#__SEAT__#$SEAT#g" -e "s#__SEATDIR__#$DIR#g" -e "s#__USER__#$(whoami)#g" -e "s#__HOME__#$HOME#g" templates/seat/launchd.plist > "$PL"
```

Edit the schedule in that file (every 15 minutes, or a time of day), then load it:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.$(whoami).<seat>.plist
```

`dispatcher` needs no clock: `meeting-ingest/run.sh` calls it. Do the [safety audit](../templates/laws-audit.md) before any seat goes on a clock.

## Run it day to day

| I want to | Run this |
|---|---|
| Run it now | `launchctl kickstart gui/$(id -u)/com.$(whoami).<seat>` |
| See if it is scheduled | `launchctl print gui/$(id -u)/com.$(whoami).<seat> \| grep -E "state\|last exit"` |
| Pause it | `launchctl bootout gui/$(id -u)/com.$(whoami).<seat>` |
| Resume it | `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.$(whoami).<seat>.plist` |
| Change the model | `MODEL=` in `<seat>/seat.conf`, then rerun the evals. One run on another model: `SEAT_MODEL=<model> <seat>/run.sh` |
| Change the cost cap | `MAX_BUDGET_USD` and `MAX_TURNS` in `<seat>/seat.conf` |
| See what it did | `~/.config/<seat>.log` and `~/.config/<seat>.launchd.log` |

The Mac must be on. A run missed while asleep happens on wake. A gate that finds no new work stops before any model runs, so a quiet day costs nothing.

## Evals

Every seat that runs a model has two kinds of check in `2_AREAS/Agents/<seat>/evals/`:

- **Locks** (`locks.json`): a list of tool calls the safety hook must allow or block. Free and fast, no model. A lock with `"needs_file": true` is about an existing file; the runner makes a stand-in when your vault has none.
- **Behaviour cases** (`cases/`): made-up input (Slack posts or meeting notes). The seat runs on it in a sandbox copy of the vault, and fixed rules grade what it did. No model grades another model.

```bash
python3 .scripts/run_evals.py --seat <seat>                     # one seat, both parts
python3 .scripts/run_evals.py --seat <seat> --locks-only        # part 1 only
python3 .scripts/run_evals.py --seat <seat> --model <model>     # try another model
python3 .scripts/run_evals.py --seat <seat> --only <case-name>  # one case
python3 .scripts/run_evals.py --selftest                        # check the grader itself
```

The runner finds everything from the seat's folder: `seat.conf` says which MCP servers the seat may have (`SERVERS=`, checked against `seat.mcp.json`) and how its cases run (`RUNNER=`: `slack` for made-up Slack posts, `notes` for meeting notes against the vault, `team-notes` for team-meeting notes to a draft; empty for locks only). A seat with no `evals/locks.json` gets only the settings checks. `--agents-dir <dir>` points it at another folder of seats.

The report is `<seat>/evals/results/latest.md`. It opens with "All clear" or "Needs attention". `results/history.csv` keeps every run. Exit 0 means all clear, so an agent can run the check and act on it.

**Rerun after** a model change, any edit to a seat's `AGENTS.md`, `run.sh`, `settings.json` or `guard.py`, or a bad week.

**Grow it.** Each time a seat gets something wrong in real life, copy a case, change the input to the real failure's wording, and set what it should have done. Add a lock row for each new thing the hook must refuse.

## Build a new seat

1. Pick the manual job that costs you most. It needs a gate a script can check, one place to write, and an output a person can approve.
2. Copy `templates/seat/` (or the closest example in `examples/seats/`) to `2_AREAS/Agents/<name>/` and follow `templates/seat-brief.md`: fill the placeholders, write the brief, the gate and the hook.
3. Choose the cheapest model that passes (`seat.conf`), and set the turn limit and cost cap.
4. Add `<name>/evals/locks.json` and `<name>/evals/cases/`, and set `SERVERS=` and `RUNNER=` in its `seat.conf`. No engine file changes.
5. Pass the evals, do one hand run, pass the [safety audit](../templates/laws-audit.md), then put it on a clock (step 7 above).
6. Add a row to `2_AREAS/Agents/README.md`.

## Limits

- macOS only, and one machine per person: seats run while that Mac is on. Where seats run for a whole team is still open.
- `dispatcher` and `team-sync` share `meeting-ingest`'s env file (same bot, channel and owner).
- The evals do not touch real Slack, so they cannot find a missing bot scope or channel invite. The hand run in step 6 does.

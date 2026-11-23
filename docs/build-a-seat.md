# Build a seat

How to turn one manual job into a scheduled agent (a "seat"). To set up and run a seat that already exists, see [agents.md](agents.md). Commands run from the vault root.

## 1. Pick the job

Pick the manual job that costs you most. It needs three things: new work a script can detect (the gate), one place to write (the drawer), and an output a person can approve. If it has none of these, keep doing it by hand.

## 2. Make the seat

```bash
python3 .scripts/new-seat.py <name> --runner slack|notes
```

`<name>` is kebab-case. `--runner` says how its behaviour cases run: `slack` for made-up Slack posts, `notes` for meeting notes against the vault. It copies `templates/seat/` to `2_AREAS/Agents/<name>/`, fills in its paths and your user name (including a ready `launchd.plist`), sets `SERVERS=` and `RUNNER=` in `seat.conf`, writes the standard locks to `evals/locks.json` and an empty `evals/cases/`, proves the locks hold, and adds a stub row to `2_AREAS/Agents/README.md`. No engine file changes.

Or copy the closest example from `examples/seats/` instead.

## 3. Write the brief, the gate and the hook

Follow [templates/seat-brief.md](../templates/seat-brief.md). It covers the brief (`AGENTS.md`), the gate (`gate.sh`), the drawer files in the hook and settings, where secrets go, and how to choose the model, turn limit and cost cap in `seat.conf`. Its checklist must be done before the seat goes on a clock.

## 4. Evals

What locks and behaviour cases are, and how to run them: [agents.md](agents.md#evals). For a new seat:

- **Locks.** `new-seat.py` wrote the standard ones. Add a row to `evals/locks.json` for each drawer file the seat may edit and each new thing it must refuse.
- **Cases.** `evals/cases/` starts empty, so the behaviour eval means nothing yet. Copy a case from the closest example seat and change the input and the `expect` block. Add one for each fault you saw in the hand runs.

```bash
python3 .scripts/run_evals.py --seat <name>
```

## 5. Search sees the shared vault only

A seat's qmd MCP must use the `seats` index (`"--index", "seats"` in `seat.mcp.json`), which `.scripts/qmd-bootstrap.sh` builds without the private collection. `run.sh` calls `../seat-qmd.sh` right before the model round: it stops the round if that index holds the private collection. `new-seat.py` sets this up and pins it with two locks. Do not remove them.

## 6. Audit, hand run, clock

1. Do the safety audit: copy [templates/laws-audit.md](../templates/laws-audit.md) and fill it in. "It is in the prompt" counts as no.
2. Run it by hand three times (`2_AREAS/Agents/<name>/run.sh`). Read the note it posts and the git diff it leaves. Change the brief, not the output.
3. Put it on a clock: [agents.md](agents.md#7-put-it-on-a-clock).
4. Fill in its row in `2_AREAS/Agents/README.md`.

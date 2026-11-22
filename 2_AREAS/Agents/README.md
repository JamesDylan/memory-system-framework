# Agents: the seats that run in this vault

Each folder here is one seat: a scheduled agent with a brief, a launcher, a gate, settings, a safety hook and its own evals. A new vault has none. Nothing here runs until you put a seat on a clock.

Update this file when a seat is added, rescheduled or stopped.

## What is running

| Seat | Job | When it runs | Status | Who is accountable |
|---|---|---|---|---|

## Add a seat

Start from an example in `examples/seats/` (or from `templates/seat/` for a new job). From the vault root:

```bash
cp -R examples/seats/<seat> 2_AREAS/Agents/
python3 .scripts/run_evals.py --seat <seat> --locks-only   # free, seconds: do the locks hold?
```

The seat brings its evals with it: locks.json and cases/ in its evals folder. `seat.conf` tells the eval runner which MCP servers the seat may have (`SERVERS=`) and how its cases run (`RUNNER=`), so no engine file changes. Then follow [docs/agents.md](../../docs/agents.md): tokens, env file, one hand run, the safety audit, the clock. Add a row to the table above.

`examples/seats/README.md` has the operating notes (start, stop, check) for each example seat.

## Run the check

```bash
python3 .scripts/run_evals.py --seat <seat> --locks-only   # part 1: locks, no AI
python3 .scripts/run_evals.py --seat <seat>                # part 2 too: behaviour on made-up input, a few dollars
```

The report is latest.md in the seat's evals/results folder; history.csv beside it keeps every run.

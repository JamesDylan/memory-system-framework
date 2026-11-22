# 04. The machinery: Gas City and Beads

**Last Updated:** 2026-11-12 | **Type:** external reference (not {{ORG}} fact) | **Source:** see `README.md` in this folder

His town runs on Gas City. You do not need Gas City to apply the method. You do need to understand its design, because it is the tested answer to problems you will hit after five seats.

Read this file for the ideas. Decide on adoption using the section "Should you run it".

## What Gas City is

An open-source (MIT) orchestrator for teams of coding agents: Claude Code, Codex, Gemini and others. You hand it work. It breaks the work into tasks, runs agents on them in parallel, gates each step on review and tracks everything in a dashboard.

It was extracted from Steve Yegge's earlier Gas Town. The main change: the orchestrator has zero built-in roles. No hardcoded "mayor" or "reviewer". Every role is configuration.

## Three pieces of plumbing

| Piece | What it does |
|---|---|
| Orchestrator | Runs formulas, moves each work graph forward, keeps running agents in line with config. |
| Bead store | Durable work. Every unit of work is a bead that survives an agent crash. |
| Event bus | Emits activity so people and agents can watch. |

The orchestrator acts on sessions (start, stop, restart). It reads progress from the store and the event bus. Agents do not call it back. The loop closes through shared state. That is why work survives a crash on either side.

## Six primitives

| Primitive | Question | What it is |
|---|---|---|
| Agent | Who | A configured worker: name, provider, prompt template, scope. The prompt is its whole behaviour. |
| Bead | What | One unit of work: ID, title, status, type. Status moves open, in progress, closed. |
| Formula | How | A written-down method. A file of steps and dependencies. |
| Rig | Where | An external project, usually a git repo. |
| Pack | Configures | A directory that declares agents, formulas and orders. Shareable. |
| Event | Observe | An append-only record of what happened. |

## The ideas worth copying

### 1. Work lives outside the session

Sessions are disposable. Work is not. If an agent dies, its beads stay open and a fresh agent picks up the same work.

For this vault: already true. State lives in canonical files, not in a chat.

### 2. Everything is one kind of record

Tasks, mail between agents, running sessions and batches are all beads. They differ only by type. One query interface covers all of them.

For this vault: action files already do this for work items. Mail has no record type yet.

### 3. Dependencies do the scheduling

A bead with an open blocker is invisible to agents until the blocker closes. Ordering happens without a central scheduler. `bd ready` returns only work with no open blockers.

For this vault: a stage's Inputs table plays this role. A stage does not start until its inputs exist.

### 4. Agents never reference each other

No function calls, no shared memory, no handles. Agents coordinate through the store in two ways:

- **Mail.** A persistent message. Survives a crash. Stays unread until processed. Does not wake the recipient by default.
- **Slung work.** A delegated task routed to a role, not to a specific session.

The sender names a destination. The system routes it. The sender does not know if one reviewer exists or five.

For this vault: skills already chain through files in the inbox, not through each other.

### 5. A formula is the method, written once

A formula is how a job gets done, written down instead of steered live in a prompt. Applying it turns the steps into beads. From then on the run is independent of the file and of any session.

A typical build formula: decompose, fan out, review (loop until it passes), gap analysis, fix gaps, check, ship.

For this vault: an ICM pipeline is the same idea. A stage contract is a formula step. See `MAPPING.md` in this project.

### 6. Orders decide when

An order pairs a trigger with an action. The orchestrator checks every 30 seconds.

| Trigger | Fires when |
|---|---|
| Cooldown | An interval has passed since the last run. |
| Cron | Wall-clock time matches. |
| Condition | A shell command exits 0. |
| Event | A named event appears on the bus. |
| Manual | Only when run by hand. |

The action is either a formula (agent work) or an exec script (no agent, no model). Exec orders are the default choice for mechanical work.

For this vault: this is the "clock" in formal terms. The condition trigger is the script gate. Most of his two dozen jobs are exec orders. The scheduled lint is the one exec order here today.

### 7. Loops are bounded by the engine

Review and retry loops have a maximum attempt count enforced by the orchestrator, not by the prompt. This is law 5 implemented in code.

### 8. Roles are prompts

A "reviewer" or "planner" is the prompt you wrote. Adding a behaviour means editing a pack, a formula, an order or a prompt. It never means new platform code.

## Gas Town roles and what they became

| Gas Town role | What it did | In Gas City |
|---|---|---|
| Mayor | Planner and coordinator. The human's point of contact. | A configured agent with a coordinating prompt. |
| Deacon | Watchdog. Stall detection, restart. | Orchestrator health patrol and thresholds. |
| Witness | Lifecycle observer. | Events and waits. |
| Refinery | Post-processes agent output. | A workflow step, not a standing role. |
| Polecat | Short-lived on-demand worker. | A scalable pool of identical agents. |
| Crew | Persistent named workers. | Persistent named agent config. |
| Dog | Integration and messaging relay. | Exec orders. Most relay work needs no model. |

The translation rule from the Gas City docs: before adding an agent, ask if an exec order can do it. Usually it can.

## Beads

Beads (`bd`) is the work tracker underneath. A dependency-aware graph of issues stored in Dolt, a version-controlled SQL database.

Core loop:

1. `bd create` makes a bead.
2. `bd dep add` links it to its blockers.
3. `bd ready` lists work with no open blockers.
4. `bd update <id> --claim` takes a bead atomically.
5. `bd close` finishes it and releases what it blocked.

Also useful: `bd remember "insight"` stores a durable project fact that is injected into later sessions. Old closed tasks are summarised to save context.

Gas City can also run on a plain file store (`GC_BEADS=file`) with no Dolt.

## Where Yegge's own town failed

From his August 2026 essay. Self-reported, no controlled comparison.

- His Gas Town worked on one model version and fell apart on the next. The newer model kept wanting to adjust the harness instead of doing the work. He says the town effectively burned down.
- It never reliably ran overnight. It needed too much manual effort to keep going.
- It was meant to be a reusable harness. He only ever used it to build itself.

What he did next:

- Built a bespoke harness for one application, still on Beads. His argument: build the harness into each application instead of adopting a general framework.
- Fixed lifecycle per work item: one model designs, a cheaper one implements, the first reviews.
- Capped the design crew at 18 agents. More overwhelmed the workers and his laptop.
- Kept a backlog of over 700 designed items so workers could run unattended.
- About 45 scheduled units support the agents. His rule is "crons watch, models act".
- Split knowledge by lifetime: long-lived doctrine, system docs, work history, short operational notes, and skills for recurring procedures.
- Reported about $87k a month of API-equivalent usage.

Lessons that carry over to product ops:

1. **The harness is not the product.** A town that mostly maintains itself has failed. Measure work delivered, not town activity.
2. **Model changes break harnesses.** Briefs tuned to one model version need re-testing on the next. Keep seats simple so this is cheap.
3. **Balance producers and consumers.** Messengers that produce more findings than people can decide on create a queue. This is the level 3 catch.
4. **Scripts watch, models act.** Same rule in both towns, reached independently.
5. **Separate knowledge by how long it lives.** Strategy, state and log should not sit in one file.

## Should you run it

Gas City is built for coding agents working on git repositories. It assumes a terminal, tmux, a logged-in agent CLI and repos to act on.

| Situation | Recommendation |
|---|---|
| One to five seats that read and write notes | Do not run it. A scheduler plus a folder is enough. |
| Seats hand work to each other and loops need ceilings | Borrow the design. Implement mail and work items as files. |
| A build crew turns issues into draft pull requests | This is what it is for. It needs engineering ownership. |
| Company environment with security review | It runs operator-configured shell commands. Treat it as infrastructure, with review. |

Starting point if you want to try it on a personal project:

```bash
brew install gascity
gc init ~/my-city --template gascity --default-provider claude
gc rig add ~/some-repo
gc sling some-repo/claude "task text" --on mol-do-work
```

The dashboard is at `http://127.0.0.1:8372/`. Tutorials 01 to 07 at docs.gascity.com cover cities, agents, sessions, communication, formulas, beads and orders.

## The minimum version without Gas City

Four folders and a scheduler reproduce the core:

| Gas City concept | File-based equivalent |
|---|---|
| Agent | `seats/<name>/BRIEF.md` |
| Bead | A markdown file with `status`, `owner`, `needs` in the header |
| Mail | `mail/<recipient>/<date>-<from>.md`, moved to `read/` when processed |
| Formula | A checklist file listing steps, owner seat, input, output and ceiling |
| Order | A scheduled job that runs a gate script, then wakes the seat |
| Event | An append-only `LOG.md` |

This is enough up to about level 4.

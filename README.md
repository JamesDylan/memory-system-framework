# An Agentic Memory System That Shares Context Within A Team

**A shared memory for a product team that agents keep current, check and correct. People decide. Agents maintain.**

A product team's knowledge is spread across Slack, meetings, documents, tickets and people's heads. Every time you ask an AI agent for help, it starts from nothing, or from whatever you paste in. This framework gives that knowledge one home that the whole team shares. Scheduled agents feed it, file into it, check it against the original sources and fix what drifts. Every agent and every person starts from the same accurate picture.

You can run all of it by hand, one prompt at a time, and add agents one job at a time. Every job below works both ways.

> **This repo is the engine, not a vault.** It holds the scripts, rules, agent skills and agent templates. It holds no notes and no data. One setup command builds the vaults (folders of plain Markdown notes) that the engine runs on.
>
> **The agent layer is here.** The scheduled agents and the dispatcher ship as examples in `examples/seats/`, each with its evals; the eval runner is `.scripts/run_evals.py`. A new vault starts with an empty `2_AREAS/Agents/`: copy in the seats you want. Each one runs in the author's vault. To set them up on your own machine, follow **[docs/agents.md](docs/agents.md)**, or hand that guide to your agent.

## Why use it

| | What you get | Status |
|---|---|---|
| 1 | **Cheaper, sharper agents.** Agents read one small, current file instead of re-reading Slack, Drive and old threads every time. Answers cost less, arrive faster and come with a source. | Working today |
| 2 | **Context that maintains itself.** Agents on a schedule pull in what changed, propose updates in Slack for a ✅ or ❌, and flag what has gone stale. Your job shrinks to deciding. | Partly built |
| 3 | **One truth for the whole team.** The shared vault is a git repo. Everyone, and every agent, works from the same facts. Agents change it only through checked pull requests. Personal notes stay in a separate private vault. | Working today |
| 4 | **Projects become harnesses.** Each project holds its sources, decisions and current state. Agent work on that project starts from the right information and writes what it learns back. | Piloting |
| 5 | **Shared skills and pipelines.** The team shares one set of agent skills. Pipelines run discovery, write requirements and report experiments, stage by stage, from the project's own facts. | Planned |

## How it runs

```text
 ORIGINALS       Slack · meetings · Drive · Jira · Productboard · BI dashboards
     │   agents capture on a clock (no new input: no model run, no cost)
     ▼
 INBOX           raw input, kept and never deleted
     │   agents route each fact to its one home and propose the change
     ▼
 YOU             ✅ or ❌ in Slack, or in a review card in your agent
     │
     ▼
 KNOWLEDGE       one file per fact: project STATE, decisions, metrics, concepts
     │   pipelines read only what they need ─────────►  WORK: discovery, PRD, experiments
     │                                                      │  learnings promoted back,
     │   ◄──────────────────────────────────────────────────┘  for your ✅
     ▼
 QUALITY LOOP    scripts check structure daily; agents check facts against
                 their source weekly; fixes arrive as PRs; your "no" becomes a rule
```

Four rules keep it safe to automate:

- **One fact, one file.** Each fact has exactly one home, so an agent never has to pick between two copies.
- **Capture is messy; filing is deliberate.** Raw input lands in an inbox first. Only approved facts reach the real notes.
- **Agents propose; people decide.** Pulls, syncs, fixes and drafts are automatic. Scope, bets, approvals and judgment about people stay with a person.
- **Plain Markdown and git.** It works in Obsidian, any editor and any agent that can read files. Every change is a diff you can read and revert.

## Every job, by hand or by agent

| Job | By hand | With agents |
|---|---|---|
| **Capture** Slack, meetings, docs | Paste into `_private/0_INBOX/`, or ask your agent to "run my daily Slack review" | Meeting agent picks up each new transcript within 15 minutes. Daily Slack pull. Spec sync from Drive *(next)* |
| **File** each fact in its home | Ask your agent to "process my inbox" (`ingest`) | The capturing agent routes it and drafts the change itself |
| **Approve** changes | Review cards in your agent | ✅ or ❌ on the agent's Slack thread. Reply to edit. A script applies your decision, no model needed |
| **Start a project** | Copy the templates | Reply `project <Name>` in Slack. The dispatcher builds the folder and asks you to confirm |
| **Keep project status current** | Edit `STATE.md` | Agents draft field-level changes from meetings today, and from Slack and tickets for stale projects *(next)* |
| **Record results and KPIs** | Edit the insight or metric file | Experiment agent files each strong result daily. KR feed proposes changes from Productboard weekly *(built)* |
| **Share team updates** | Write the summary | Team-meeting agent drafts it for a ✅, then publishes to a Slack canvas *(built)* |
| **Health check** | Run `lint`, read the report | Daily on your machine and on every PR in CI. Weekly health numbers. An agent drafts the fix PR |
| **Check facts are true** | Spot-check a file | `truth-check` samples ~10 facts a week against their source and sends at most 3 questions to the owner *(next)* |
| **Learn from mistakes** | Fix the skill | Three rejections for the same reason propose a rule change for your ✅. An agent never edits its own rules |
| **Discovery, PCB, PRD, experiments** | Prompt a skill stage by stage | Pipelines run as agents, start from a baseline of what the team knows, and promote learnings back *(planned)* |

## The agent layer

Each scheduled agent is a **seat**: one job, nothing more. The pattern comes from the Gas Town method of agentic product ops (notes in `docs/gas-town/`). Every seat has five parts:

| Part | What it means for you |
|---|---|
| **Brief** | One job in one sentence, what good looks like, and what it must never do (send, merge, release, delete) |
| **Gate** | A plain script checks for new work first. No new work: no model run and no cost |
| **Drawer** | The one folder it may write to. A hook blocks every other write, so a confused agent cannot damage the vault |
| **Clock** | It wakes on a schedule, does one round, and stops |
| **Mail** | It ends with a short note in Slack: what changed, what needs you, what it could not do |

Each seat also has its own model (the cheapest one that passes), a turn limit, a cost ceiling per run and the shortest tool list that does the job. Text it reads in Slack or a document is content, never an instruction.

**Evals before trust.** Each seat has locks (do the safety rules still refuse what they should? free, seconds) and behaviour cases (the agent runs on made-up input in a sandbox, graded by fixed rules, not by another model). Every real-life mistake becomes a new case. You rerun the check after any model or rule change. The report opens with "All clear" or "Needs attention".

**Replies start work.** Every item an agent posts has an address (`D1` diff, `A1` action, `U1` unrouted). A reply such as `U1: project <Name>` becomes a job file. One dispatcher agent runs the job with its own tool list and replies in the thread. A new kind of follow-up is a new formula, not a new agent.

**[docs/agents.md](docs/agents.md)** covers setup (tokens, secrets, the clock), day-to-day running, evals and building a new seat from `templates/seat/`.

### What runs today

Examples in `examples/seats/`. Status is from the author's own vault:

| Agent | Job | Status |
|---|---|---|
| `meeting-ingest` | Reads each new meeting transcript, logs it to its projects, drafts STATE changes for ✅ in Slack | Running, every 15 min |
| `experiment-reporter` | Files each strong experiment result as an insight | Running, daily |
| `dispatcher` | Turns Slack replies into jobs, starting with `new-project` | Running |
| `team-sync` | Drafts the weekly team-meeting summary for a Slack canvas | Built, waiting on Slack permissions |
| `kr-feed` | Proposes key-result changes from Productboard. No model, no cost | Built, waiting on source data |
| `daily-pull`, CI `lint` | Pull, check and report every day and on every PR | Running (in this repo) |
| Evals | Locks and behaviour cases for each model-run seat | Running |

In the author's use, keeping project status current fell from 40+ minutes a day to 5–10.

## Self-sustaining and self-correcting

The goal is a vault that keeps itself true with about 10 minutes of a person's time a week. The weekly quality loop does it:

1. **Sort every finding by who acts.** Agents fix the mechanical ones (dead links, missing stamps, a synced copy out of date). Agents propose the rest for the owner's ✅. Only real judgment reaches a person, at most 3 asks per owner per week.
2. **Check facts against the source.** An agent samples facts each week and marks each one supported, contradicted or unclear. The result is the **truth rate**.
3. **Corrections become tests.** Each correction you make becomes a test question with the right answer. Each project has 10 or more, run weekly.
4. **Track numbers, not lists.** One health file holds truth rate, test score, fresh sources, upkeep minutes and cost per question. The weekly digest leads with them.
5. **Rules improve from rejections.** The same reason for a "no", three times in ten sessions, proposes one rule change.
6. **Prune.** Each month, checks and agents that led to no action are demoted or removed, so the system gets simpler as it grows.

**Guard measures.** The system must not get better at the cost of these: truth rate 90% or more, test score 8 of 10 or more, owner upkeep 10 minutes a week or less, cost per question falling or flat, and no disproved idea coming back without new evidence.

## One ecosystem: memory, agents and pipelines

Three parts work together. None is rebuilt by the others.

| Part | Gives | Where |
|---|---|---|
| **The memory system** | Shared facts, one home each, with sources and stamps | This engine, and the vaults it builds |
| **The agents (seats)** | Work on a clock, with hard limits, locks and evals | `examples/seats/` in this engine; `2_AREAS/Agents/` in a vault |
| **The pipelines** | Discovery, PCB, one-pager and PRD stages, a prototype kit and a "twin" of the product on made-up data | The team's discovery lab repo |

Joined, they work like this:

- **Pipelines run as seats.** A stage starts by itself when its gate is mechanical (the previous output exists and passes its checks). A person starts it when the gate is judgment. You see only the decisions.
- **Every pipeline starts from memory.** A first stage writes a one-page baseline from what the team already knows, including ideas already disproved. You write a one-line hypothesis before you read it.
- **Every pipeline ends in memory.** A last stage proposes its decisions and learnings back to the vault for your ✅, so the next piece of work starts ahead.
- **Designs stay buildable.** Agents build designs in the twin. A check confirms each design uses only services that exist in production.
- **One validation system.** Seats and pipeline stages share one report shape, so a change cannot ship with a broken contract or a removed safety rule.
- **One engine for many PMs.** A fix to the seat template or the checks reaches every PM's agents. Nobody needs the author to set them up.

## Roadmap

The order is fixed by evidence: each stage starts when the one before it shows a measured result.

| Stage | What it adds | Outcome for you | Status |
|---|---|---|---|
| **Measure** | Baseline cost and time per task; weekly health numbers; skill scorecards; typed, sourced facts | You can see whether the system is getting more accurate and cheaper | Mostly done |
| **Project harness pilot** | One project where facts come from listed sources, not hand copies. Specs sync from Drive. A weekly truth check | Answers follow the live spec, and accuracy is a number, not a feeling | In progress |
| **Next agents** | `truth-check` (truth rate for the pilot), `state-refresh` (stale project pages refreshed from Slack and tickets), `spec-sync` (Drive copies kept current) | Project pages stay current without anyone copying status by hand | Next |
| **Pipelines** | One stage template with its own checks and evals. Memory upkeep, discovery and the experiment loop rebuilt as stages and run as seats | Discovery starts from what the team knows, and costs less per run | Planned |
| **Active layer** | New projects start from a template and a baseline. "Help me write the PRD" routes to the right pipeline in any AI tool. Process gates checked in CI, with a visible skip | No project starts from a blank page | Planned |
| **Scale and automate** | Every live project on the harness. All agents maintain the vault through PRs. Routine facts auto-apply once proven safe. Changed skills replayed against past sessions before they go live. Monthly pruning | A week passes with no manual run, and the system gets simpler as it grows | Planned |

What keeps it cheap and accurate along the way:

- **Scripts before models.** Gates, checks, health numbers and applying your ✅ are plain scripts. A model runs only where judgment is needed.
- **Evals before trust.** No seat goes on a clock without locks, cases and a safety audit. Auto-apply waits for a proven clean rate.
- **Hard limits.** Every agent has a turn limit, a cost ceiling, a short tool list and one folder it may write to.
- **Uses the access you already have.** Skills and agents use the connectors your agent already has: Slack, Google Drive, Productboard and others.
- **A tool earns its place.** A new agent or source is added only when it replaces a manual job with a measured cost.

## How to use it

1. **Set up once.** Run `init-vault.py` (see [Set up](#set-up)). It builds two vaults with the PARA folders (Projects, Areas, Resources, Archive):

   ```text
   memory_system/            shared vault: a git repo your team can read
     1_PROJECTS/<Org>/       one folder per initiative: BRIEF, STATE, LOG
     2_AREAS/<Org>/          ongoing context: strategy, people, metrics
     3_RESOURCES/            concepts, processes, and the AI Skills (engine)
     4_ARCHIVE/              finished work and source documents
     _private/  ->           link to the private vault below

   memory_private/           private vault: your machine only
     0_INBOX/                every raw input lands here first
     1_PROJECTS/Actions/     your own to-dos
     2_AREAS/                your team, your career
     3_RESOURCES/AI Skills/  skills that touch private data
     4_ARCHIVE/
   ```

2. **Every day, capture and file.**
   - *By hand:* drop raw material in `_private/0_INBOX/`, or ask your agent to "run my daily Slack review". Then ask it to "process my inbox". The `ingest` skill files each fact and shows you the changes to approve.
   - *With agents:* seats capture meetings and Slack on a clock and post their proposed changes to Slack. You react ✅ or ❌.
3. **When you need an answer:** ask your agent, in any tool. It searches first, reads the one canonical file, cites the source, and tells you if the answer may be out of date.
4. **Every week, keep it healthy.**
   - *By hand:* read the lint report and fix what it flags.
   - *With agents:* CI writes the health numbers and drafts a fix PR. You answer the few questions only you can answer.
5. **Add agents one job at a time.** Pick the manual job that costs you most, build a seat for it from `templates/seat/`, pass its evals and safety audit, then put it on a clock.

## The model

| Layer | Holds | Where |
|---|---|---|
| Engine | Scripts, lint, search config, skills, schemas | This repo. Copied into the shared vault |
| Organisation | Company context, project status, concepts, processes | Shared vault. A git repo your team can read |
| Private | People and coaching notes, career, inbox, raw captures, your own actions | Private vault. Your machine only |

Both vaults use the same PARA shape: `0_INBOX` (private only), `1_PROJECTS`, `2_AREAS`, `3_RESOURCES`, `4_ARCHIVE`.

The private vault is a separate folder. It is mounted inside the shared vault as `_private/`, a gitignored symlink. All paths in docs and skills are relative to the shared vault, so a private path starts with `_private/`.

## Rules the engine enforces

1. **One canonical file per fact.** `memory_index.md` maps each fact type to its file. A copy anywhere else is wrong.
2. **Routing.** A fact about the product, the company or a project goes to the shared vault. A fact about a person's performance, about you, or raw capture goes to `_private/`.
3. **Raw input lands in `_private/0_INBOX/`.** The `ingest` skill routes it. Only the extracted fact reaches a canonical file. The source is archived, never deleted.
4. **Propose, then apply.** Changes to a project's `STATE.md` are proposed as diffs (`diff-propose`) and applied only after you approve.
5. **One-way links.** Private files may point at shared files. Shared content must not point at a private file.
6. **Stamps.** Operational files carry `Last touched` and `Last verified accurate`. They mean different things. Lint checks both.

## Project schema

Each project folder has three files with three rhythms:

| File | Holds | Changes |
|---|---|---|
| `BRIEF.md` | Why, scope, success | Rarely |
| `STATE.md` | Right now, next decision, blocker, risks, last 3 events | Weekly. A snapshot with field budgets, not a history |
| `LOG.md` | Dated history | Append-only |

Templates are in `templates/`.

## Parts

| Part | File | Does |
|---|---|---|
| Lint, mechanical | `.scripts/lint.mjs`, `.scripts/lint.config.json` (engine), `.scripts/lint.config.org.json` (this vault) | Dead pointers, staleness, missing stamps, orphan skills, inbox age, index drift, deployed-skill drift, run integrity, STATE budgets, private boundary, engine drift. No model |
| Lint, scheduled | `.scripts/daily-pull.sh` (installs one launchd job) | Daily pull, then lint, with a notification on must-fix findings (macOS) |
| Lint, CI | `.github/workflows/lint.yml`, `.scripts/scorecard.mjs`, `.scripts/health.mjs` | Lint on each PR; weekly health row, optional agent fix PR and Slack digest. Each part is skipped until its secret is set |
| Lint, judgment | `3_RESOURCES/AI Skills/lint/` | Conflicts and semantic staleness. Needs an agent |
| Search | `.scripts/qmd-bootstrap.sh`, `templates/qmd-index.template.yml` | Local hybrid search with qmd, one collection per vault |
| Metrics | `_metrics/` | A registry of typed metric values with a checker. One place a number may change |
| Capture | `daily-slack-review`, `watch` | Pull signal into the inbox |
| Route | `ingest`, `diff-propose` | Classify, propose, apply, log |
| Think | `second-brain`, `challenge`, `emerge`, `connect`, `calibrate`, `review-prep`, `debloat` | Read the vault for a purpose |
| Automate | `examples/seats/` (seats, dispatcher, their evals), `.scripts/run_evals.py`, `2_AREAS/Agents/` (your seats), `templates/seat/` (incl. `launchd.plist`), `templates/seat-brief.md`, `templates/laws-audit.md`. Guide: [docs/agents.md](docs/agents.md) | Scheduled agents with one job each, their own model, cost cap, tool list and write folder. Each posts a short note for a person to approve |
| Publish | `.scripts/export-framework.py` | Export the engine with no organisation data |

`watch`, `calibrate` and `debloat` ship in `private/` and install into the private vault (`_private/3_RESOURCES/AI Skills/`), because they read or write private data.

Per-person values (your chat user ID, direct reports, watch list) live in `_private/ME.md`. Organisation values live in `ORG.md`. Skills read them.

## Set up

Needs Python 3 and Node. Search needs qmd (`npm install -g @tobilu/qmd`).

```bash
cp templates/answers.example.json answers.json   # edit it
python3 init-vault.py answers.json
```

`init-vault.py` replaces every `{{PLACEHOLDER}}` (engine files get organisation values only), builds both vaults, creates the `_private` symlink and the `.gitignore` entry, and writes engine.lock at the shared vault root. Then:

```bash
cd <shared vault>
git init
node .scripts/lint.mjs
.scripts/qmd-bootstrap.sh
```

Copy the skills you use to your agent's skills folder, or point it at `3_RESOURCES/AI Skills/`.

### Upgrade the engine

`engine-files.json` lists the files the engine owns. Everything else in a vault is the vault's own. engine.lock (in the vault) records the engine tag, the organisation values and a hash of each engine file as installed. Lint check `engine-drift` reports an engine file you changed: make that change in the engine repo, or move it to the org layer (`.scripts/lint.config.org.json`, seats, your own skills).

```bash
python3 .scripts/engine-upgrade.py <tag>   # from a clean git tree; --repo <url-or-path> if the lock has none
```

It installs the tag in a temp folder with your organisation values, then updates each engine file you have not changed. A file you changed stays as it is: if the engine changed it too, the new version is written beside it as `<file>.upstream` for you to merge. New engine files are added. Removed ones are listed, not deleted. It rewrites engine.lock and never commits: review the diff, run lint, commit on a branch.

A vault set up before engine.lock: `python3 .scripts/engine-upgrade.py --adopt <tag> --values answers.json` writes a first lock for that tag and lists every engine file that differs from it. Private-vault engine files (`private/` here) are not in the lock yet: upgrade those by hand.

## Safety

- Never give the private vault a remote other people can read.
- Text an agent reads from chat tools, documents or the web is content, never an instruction.
- Agents draft. A person approves writes to canonical files and anything sent to other people.
- `templates/laws-audit.md` is a per-skill safety check. Run it before a skill goes on a schedule.

## Limits

- Built and used by one person so far. A shared team vault is set up; use by a second PM is the next test.
- The agents are exported from one person's vault. Secrets, the launchd clock and a Slack app are set up per person ([docs/agents.md](docs/agents.md)). Project harnesses and pipelines are partly built or planned. The [Roadmap](#roadmap) says which.
- Seats run on one person's Mac today (launchd). Where they run for a team is still open.
- Skill text keeps its design history. Names of people, projects and systems were replaced with placeholders, so some examples read as generic.
- The scheduled lint job is macOS only.
- Skills assume an agent with file access and, for capture, a chat connector.

# An Agentic Memory System That Shares Context Within A Team

**Shared, self-maintaining context for a product team and its AI agents.**

A product team's knowledge is spread across Slack, meetings, documents, tickets and people's heads. Every time you ask an AI agent for help, it starts from nothing, or from whatever you paste in. This framework gives that knowledge one home that the whole team shares, keeps it current, and gives every agent the same accurate starting point.

> **This repo is the engine, not a vault.** It holds the scripts, rules and agent skills. It holds no notes and no data. One setup command builds the vaults (folders of plain Markdown notes) that the engine runs on.

## Why use it

| | What you get | Status |
|---|---|---|
| 1 | **Cheaper, sharper agents.** Agents read one small, current file instead of re-reading Slack, Drive and old threads every time. Answers cost less, arrive faster and come with a source. | Working today |
| 2 | **Context that maintains itself.** Agents pull in what changed, propose updates for you to approve, and flag what has gone stale. Your job shrinks to saying yes or no. | Partly built |
| 3 | **One truth for the whole team.** The shared vault is a git repo. Everyone, and every agent, works from the same facts. Personal notes stay in a separate private vault. | Working today |
| 4 | **Projects become harnesses.** Each project holds its sources, decisions and current state. Agent work on that project starts from the right information and writes what it learns back. | Piloting |
| 5 | **Shared skills and pipelines.** The team shares one set of agent skills. Pipelines can run discovery, write requirements and report experiments, step by step, from the project's own facts. | Planned |

### 1. Cheaper, sharper agents

- **Ask "where is project X now?"** and get one current answer, with its source, from one file.
- **Search first, read one file.** Local search finds the right note, so an agent reads a few thousand words, not a week of Slack.
- **Right model for the job.** Scheduled agents name their model and a cost ceiling per run. Routine jobs run on the cheapest model that passes its checks.
- **Measured, not assumed.** A weekly health row tracks freshness and upkeep, so you can see whether it pays for itself. In the author's use, keeping project status current fell from 40+ minutes a day to 5–10.

### 2. Context that maintains itself

- **Capture runs on its own.** Slack and meeting notes are pulled into an inbox every day.
- **The agent files; you approve.** Each fact goes to its one home as a proposed change. You approve or reject it in a review card.
- **Problems surface early.** A daily check finds stale pages, broken links, numbers that disagree and facts with no owner, and names who should fix each one.
- **It learns from your "no".** When you reject the same kind of change three times, it proposes a rule so it stops making that mistake.
- **Built today:** daily capture, filing with approval, daily and CI checks, the health row. **Next:** agents that refresh stale project pages and check facts against their source each week (see [Roadmap](#roadmap)).

### 3. One truth for the whole team

- **Host it on GitHub.** The shared vault is a normal git repo. Changes arrive as pull requests, checked before they merge.
- **Same answer for everyone.** A new PM, a stakeholder's question or an agent in any tool gets the same facts, from the same file.
- **Private stays private.** Notes about people, your career and raw captures live in a private vault on your machine. A check stops shared notes from pointing at private ones.
- **No lock-in.** Plain Markdown works in Obsidian, any editor, and any agent that can read files.

### 4. Projects become harnesses

- **Every project has a fixed shape:** why and scope (`BRIEF`), where it stands now (`STATE`), what happened (`LOG`), and its decisions and open questions as small sourced facts.
- **Sources are listed.** Each project names its originals (specs, channels, tickets), so an agent knows where every fact came from and where to check it.
- **Agent work stays on track.** An agent working on a project reads that project's facts first and writes back what it learned, instead of drifting or starting from scratch.

### 5. Shared skills and pipelines

- **One skill set for the team.** Skills for capture, filing, health checks, review prep and challenging a plan live in the vault, so everyone's agent works the same way.
- **Uses the access you already have.** Skills use the connectors your agent already has (Slack, Google Drive, Productboard and others). No new integrations to buy.
- **Pipelines that start from what the team knows.** Discovery, requirements and experiment pipelines read the project's facts first and promote what they learn back into the vault, so the next piece of work starts ahead.

## Roadmap

The order is fixed by evidence: each stage starts when the one before it shows a measured result.

| Stage | What it adds | Outcome for you | Status |
|---|---|---|---|
| **Measure** | Baseline cost and time per task; weekly health numbers; skill scorecards; typed, sourced facts | You can see whether the system is getting more accurate and cheaper | Mostly done |
| **Project harness pilot** | One project where facts come from listed sources, not hand copies. Specs sync from Google Drive. A weekly truth check samples facts against their source | Answers follow the live spec, and accuracy is a number, not a feeling | In progress |
| **Self-maintaining agents** | Scheduled agents with a fixed job, model and cost cap: `truth-check`, `state-refresh`, `spec-sync`. Each has evals and posts a short note for approval in Slack | Project pages stay current without anyone copying status by hand | Next |
| **Pipelines** | One template for every pipeline stage, with its own checks and evals. Discovery, memory upkeep and experiment loops built on it | Discovery starts from what the team knows, and costs less per run | Planned |
| **Active layer** | New projects start from a template and a baseline brief. Agents route "help me write the PRD" to the right pipeline. Process gates checked in CI | No project starts from a blank page, in any AI tool | Planned |
| **Scale and automate** | Every live project on the harness. Agents maintain the vault through pull requests. Routine facts auto-apply once proven safe. Changed skills are replayed against past sessions before they go live. Unused checks and skills are pruned monthly | The system gets cheaper and simpler as it grows, not heavier | Planned |

What keeps it cheap and accurate along the way:

- **Scripts before models.** Structure checks, health numbers and scorecards are plain scripts. A model runs only where judgment is needed.
- **Evals before trust.** Each scheduled agent has test cases and a pass bar before it runs on its own. Auto-apply waits for a proven clean rate.
- **Hard limits.** Every agent has a turn limit, a cost ceiling, a short tool list and one folder it may write to.
- **A tool earns its place.** A new agent or source is added only when it replaces a manual job with a measured cost.

## How it works

- **One fact, one file.** Each fact has exactly one home, so there is never a "which copy is right?" question. An index maps each type of fact to its file.
- **Capture is messy; filing is deliberate.** Raw input goes to an inbox first. Only checked facts move into the real notes.
- **The agent proposes; you approve.** Nothing important changes without a person saying yes.
- **Checks are automatic.** Scripts check structure every day, without an AI. An agent checks meaning only when asked.
- **Plain Markdown.** It works in Obsidian, in any editor and with any AI agent that can read files. You are not locked in.

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

2. **Every day:** drop raw material in `_private/0_INBOX/`, then ask your agent to "process my inbox". The `ingest` skill files each fact and shows you the changes to approve.
3. **When you need an answer:** ask your agent. It searches first, reads the one canonical file, and tells you if the answer may be out of date.
4. **Every week:** read the lint report and fix what it flags.

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
| Lint, mechanical | `.scripts/lint.mjs`, `.scripts/lint.config.json` | Dead pointers, staleness, missing stamps, orphan skills, inbox age, index drift, deployed-skill drift, run integrity, STATE budgets, private boundary. No model |
| Lint, scheduled | `.scripts/daily-pull.sh` (installs one launchd job) | Daily pull, then lint, with a notification on must-fix findings (macOS) |
| Lint, CI | `.github/workflows/lint.yml`, `.scripts/scorecard.mjs`, `.scripts/health.mjs` | Lint on each PR; weekly health row, optional agent fix PR and Slack digest. Each part is skipped until its secret is set |
| Lint, judgment | `3_RESOURCES/AI Skills/lint/` | Conflicts and semantic staleness. Needs an agent |
| Search | `.scripts/qmd-bootstrap.sh`, `templates/qmd-index.template.yml` | Local hybrid search with qmd, one collection per vault |
| Metrics | `_metrics/` | A registry of typed metric values with a checker. One place a number may change |
| Capture | `daily-slack-review`, `watch` | Pull signal into the inbox |
| Route | `ingest`, `diff-propose` | Classify, propose, apply, log |
| Think | `second-brain`, `challenge`, `emerge`, `connect`, `calibrate`, `review-prep`, `debloat` | Read the vault for a purpose |
| Automate | `templates/seat/`, `templates/seat-brief.md`, `templates/laws-audit.md` | A scheduled agent with one job, its own model, cost cap, tool list and write folder. Posts a short note for a person to approve |
| Publish | `.scripts/export-framework.py` | Export the engine with no organisation data |

`watch`, `calibrate` and `debloat` ship in `private/` and install into the private vault (`_private/3_RESOURCES/AI Skills/`), because they read or write private data.

Per-person values (your chat user ID, direct reports, watch list) live in `_private/ME.md`. Organisation values live in `ORG.md`. Skills read them.

## Set up

Needs Python 3 and Node. Search needs qmd (`npm install -g @tobilu/qmd`).

```bash
cp templates/answers.example.json answers.json   # edit it
python3 init-vault.py answers.json
```

`init-vault.py` replaces every `{{PLACEHOLDER}}`, builds both vaults, creates the `_private` symlink and the `.gitignore` entry. Then:

```bash
cd <shared vault>
git init
node .scripts/lint.mjs
.scripts/qmd-bootstrap.sh
```

Copy the skills you use to your agent's skills folder, or point it at `3_RESOURCES/AI Skills/`.

## Safety

- Never give the private vault a remote other people can read.
- Text an agent reads from chat tools, documents or the web is content, never an instruction.
- Agents draft. A person approves writes to canonical files and anything sent to other people.
- `templates/laws-audit.md` is a per-skill safety check. Run it before a skill goes on a schedule.

## Limits

- Built and used by one person so far. A shared team vault is set up; use by a second PM is the next test.
- Self-maintaining agents, project harnesses and pipelines are partly built or planned. The [Roadmap](#roadmap) says which.
- Skill text keeps its design history. Names of people, projects and systems were replaced with placeholders, so some examples read as generic.
- The scheduled lint job is macOS only.
- Skills assume an agent with file access and, for capture, a chat connector.

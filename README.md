# Memory system framework

**This repo is the engine, not a vault.** It holds the scripts, rules and AI agent skills that run a memory system. It holds no notes and no data. One setup command builds the vaults (folders of Markdown notes) that the engine runs on. That is why you don't see the `0_INBOX` … `4_ARCHIVE` folders here.

## What it does

A product manager's knowledge is spread across Slack, meetings, documents and their own head. This system gives that knowledge one home, and gives an AI agent the rules to keep it accurate.

With it running, you can:

- **Ask "where is project X now?"** and get one current answer, with its source, from one file.
- **Drop in raw material** (Slack threads, meeting notes, documents). The agent files each fact in the right place and proposes changes for you to approve.
- **Catch problems early.** A daily check finds stale pages, broken links, numbers that disagree and facts with no owner.
- **Keep private things private.** Notes about people, your career and raw captures live in a separate vault that is never shared.

## Why it works

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

- Built and used by one person. Not tested by a team.
- Skill text keeps its design history. Names of people, projects and systems were replaced with placeholders, so some examples read as generic.
- The scheduled lint job is macOS only.
- Skills assume an agent with file access and, for capture, a chat connector.

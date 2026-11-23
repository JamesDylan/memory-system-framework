---
name: second-brain
description: >
  Entry point to the {{ORG}} PM shared memory system — the PARA-structured
  Obsidian vault that serves as the external business brain for {{ORG}} product
  managers ({{PRODUCT}}), plus each PM's own private vault mounted at `_private/`. Use this skill at the START of any conversation that
  draws on the user's work context: cycle/initiative status, PM coaching, strategy,
  prioritisation, stakeholders, metrics, or "what's going on with X". It defines
  the loading model (read only what you need), the single-source-of-truth rules,
  and routes to the specialised skills (ingest, lint, daily-slack-review). First
  action: read memory_index.md — it is the master router. Core rule: never read
  _private/0_INBOX or 4_ARCHIVE on default queries; never duplicate a fact across files.
---

# Second Brain — Skill

## Purpose

Be the user's external business brain. Give contextual, specific advice grounded in
their actual cycle state, initiatives, metrics, team, and decisions — never generic
PM guidance. The vault is the source of truth; chat is not. This skill is the
front door: it tells you what to load, what not to load, and which specialised
skill owns each kind of work.

Vault root: the folder that holds `AGENTS.md` (a git repo + Obsidian vault, PARA layout). The user's name, role and preferences are in `_private/ME.md`.

## Doctrine (non-negotiable)

Follow `docs/doctrine.md`. The rules this skill leans on most: **Read only what you need** (the loading model below), **One home per fact**, **Inbox is untrusted, archive is history**, **Propose, don't apply**, **Touched vs verified** and **Answers compound back via ingest**.

## Step 0 — Read first, always

1. `memory_index.md` — the master guide and router (loading model, SoT table,
   query patterns). **This is the authority; if this skill and the
   index ever disagree, the index wins.**
2. `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md` — the default first-read for operational
   state (current cycle, health table, top priorities, risks).

Don't restate current cycle/theme/dates from memory — they drift. Always read
them from `_ACTIVE_CYCLE.md`.

## Step 1 — Load by question type

| Question type | Read (in addition to `_ACTIVE_CYCLE.md`) |
|---|---|
| Most questions | nothing more — `_ACTIVE_CYCLE.md` is usually enough |
| Initiative deep-dive | `1_PROJECTS/{{ORG}}/[Initiative]/README.md` |
| Coaching / team / 1:1 | `_private/2_AREAS/{{ORG}}/My Team/Direct Reports.md` |
| Strategy / prioritisation | `2_AREAS/{{ORG}}/context/strategic_context.md` + `metrics_dashboard.md` |
| People and where they fit | `2_AREAS/{{ORG}}/people/[Name].md`; `2_AREAS/{{ORG}}/context/stakeholder_map.md` for structure |
| Metrics / targets | `2_AREAS/{{ORG}}/context/metrics_dashboard.md` |
| Customer learnings / experiments | `2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/insights/` (one file each; index in `{{ORG_LOWER}}_data/learning_insights.md`) |
| The user's role / career | Context file and OKR file named in `_private/ME.md` |
| Catch-up after a gap | `CHANGELOG.md` first, then `_ACTIVE_CYCLE.md` |
| H2 ideas / roadmap | `2_AREAS/{{ORG}}/_H2 Roadmap/CANDIDATES.md` + `ROADMAP.md` |

Do **not** load `strategic_context.md`, `stakeholder_map.md`, `Direct Reports.md`,
or the `cycle_dashboard_*.json` on every conversation — only when the question
calls for them.

## Step 2 — Delegate to the specialised skill

This skill orchestrates; it does not do their jobs.

| If the user says… | Hand off to |
|---|---|
| "ingest this", "process my inbox", "file this", "capture this", drops raw notes/feedback/ideas | **`ingest`** — routes _private/0_INBOX → the one canonical home |
| "lint the wiki", "what's stale", weekly health check | **`lint`** — dead pointers, staleness, SoT violations, orphans |
| "run my Slack review", daily/weekly sync | **`daily-slack-review`** |
| "challenge this", "poke holes", "red-team this", "what am I missing" | **`challenge`** — red-teams a proposal using vault history |
| "what patterns are emerging", "connect the dots across the month" | **`emerge`** — surfaces unnamed patterns in the recent window |
| "connect X and Y", "non-obvious link between…", "cross-pollinate" | **`connect`** — bridges domains via semantic search |
| "prep [PM]'s review", "prep my review", "assemble my OKR2 evidence", "what's the evidence for [competency]", promotion/raise case | **`review-prep`** — queries the performance-evidence graph, follows pointers to canonical wins, drafts WHAT/HOW/LEARN (PM) or decision-first (the user) |

When delegating, stop and let that skill's doctrine drive. Don't half-do an
ingest from inside a status conversation.

The last three (`challenge`, `emerge`, `connect`) are the **Thinking layer** —
generative, read-only skills. They reason over the vault but never mutate
canonical files; any insight worth keeping compounds back via `ingest`.

## Step 3 — Editing canonical files

When a fact changes, update its **single source of truth** (per the SoT table in
`memory_index.md`), not wherever it's mentioned.

1. Identify the canonical file from the SoT table.
2. Make a targeted edit (change fields, don't rewrite the file).
3. Stamp `Last touched`; stamp `Last verified accurate` only if the user confirms.
4. Append a dated bullet to `CHANGELOG.md` noting what changed and why.
5. Read back what you wrote to confirm it landed and didn't clobber neighbours.

## Pushback rules (calibrated to the user)

- **Generic PM advice when the vault has specifics:** refuse. Go read the actual
  initiative/metric/person and answer from that.
- **Turning an uncommitted idea straight into a project folder:** refuse. It's a
  candidate in `CANDIDATES.md` until committed to a cycle (that's `ingest`'s rule).
- **Same fact wanting two homes:** refuse the duplicate. Pick canonical, make the
  other a pointer.
- **Restating cycle/theme/status from memory:** don't. Read `_ACTIVE_CYCLE.md`.
- **Reading _private/0_INBOX or 4_ARCHIVE to answer a normal question:** don't. They're
  untrusted / historical.

## What this skill does NOT do

- Does not process the inbox (that's `ingest`), run the health check (`lint`), or
  pull Slack (`daily-slack-review`).
- Does not replace `memory_index.md` — it points at it. Keep the index as the
  authoritative router; this skill is the operating discipline around it.
- Does not touch projects outside `memory_system` — the wider workspace
  is separate and out of scope here.

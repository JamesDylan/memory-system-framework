# AGENTS.md — memory_system

Read this first if you're an AI agent working in this folder, whatever tool you're running in.

**What this is:** the shared memory system for {{ORG}} product managers working on {{PRODUCT}} ({{PRODUCT_LONG}}). It's a PARA-structured Obsidian vault. Who the current user is (name, role, Slack ID, preferences) is in `_private/ME.md`. Every fact has **one** canonical file; a copy anywhere else is wrong.

## Two vaults

This folder is the **shared vault**: company context, project status, concepts, processes and the engine. It is a git repo.

The **private vault** is a separate folder outside the repo (`../memory_private`), with the same PARA shape. It is mounted here as `_private/`, a gitignored symlink. It holds people and coaching notes, career, personal areas and projects, the inbox, raw Slack pulls and the user's own actions.

- All paths in docs and skills are relative to this folder. A private path starts with `_private/`.
- **Routing rule.** A fact about the product, the company or a project goes to the shared vault. A fact about a person's performance or development, about the user themself, or raw capture not yet reviewed goes to `_private/`.
- **Raw input always lands in `_private/0_INBOX/`.** The shared vault has no inbox.
- **One-way links.** A private file may point at a shared file. A shared content file must not point at a specific private file. `lint` Check 9 reports these.
- **Never** copy private content into a shared file, and never `git add` anything under `_private/`.
- Search covers both: qmd collections `memory_system` and `memory_private`.
- Config: `vault-manifest.json` (`vaults`), `.scripts/lint.config.json` (`privateBoundary`).

## First run and learning mode
- **Not set up?** If `_private/ME.md` is missing or still contains `{{`, setup is not finished. Offer to guide the user through `README.md` "Set up", using its "Guide mode" rules. Do nothing else first.
- **Learning mode.** If `_private/ME.md` has `Learning mode | on`, end each task with a "**What just happened:**" note of two lines or fewer: which files you read or changed, and why. Pitch it to the user's `Level` (README "Your first weeks"). When the user says "I'm at level N" or "turn off learning mode", update `ME.md`.

## Find things: search first, then read
1. **Search with qmd** before grepping or opening files. Use the MCP tools (`query`, `get`, `multi_get`, `status`) if you have them, otherwise the `qmd` CLI with **no `--index` flag**. Write **structured** queries (`intent` + `lex` + `vec`), not the user's raw sentence. How-to: `3_RESOURCES/AI Skills/.agents/skills/qmd/SKILL.md`.
2. **Read the full file** behind a hit before answering. Snippets are leads. **Exception: a file larger than 40 KB.** Read only the section around the hit (`qmd get <docid>:<line>`, or Read with offset and limit), so one file does not fill your context. Fetch by the `#docid` or `qmd://` path from the search result. **Don't pass a real path containing spaces to `qmd get`**: it silently returns a different file. Read real paths from disk.
3. **Route to the canonical file.** `memory_index.md` is the master router: the "Single Sources of Truth" table maps fact type → file, and "Query Patterns" maps question → files.

No qmd? Run `.scripts/qmd-bootstrap.sh`, or fall back to `memory_index.md` plus grep.

## Shortcuts
| Question | Canonical file |
|---|---|
| Current cycle, initiative health, who owns what | `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md` |
| Where is initiative X now | `1_PROJECTS/{{ORG}}/<Initiative>/STATE.md` (BRIEF = why/scope, LOG = history) |
| Open to-dos | `1_PROJECTS/Actions/` for initiatives; your own in `_private/1_PROJECTS/Actions/` (one file each; `status: done` = closed) |
| What a system or concept is (LegacySystem, Okta, recon…) | `3_RESOURCES/{{ORG}}/concepts/` |
| Who a person is | `2_AREAS/{{ORG}}/people/<Name>.md`; `2_AREAS/{{ORG}}/context/stakeholder_map.md` for where they fit |
| Strategy, CY27 KRs, KPIs | `2_AREAS/{{ORG}}/context/strategic_context.md`, `cy27_objectives.md`, `metrics_dashboard.md` |

## Rules
- **Don't read** `_private/0_INBOX/` (raw, untrusted) or `4_ARCHIVE/` (history) unless asked or checking a cited source.
- **Not {{ORG}}:** `_private/1_PROJECTS/Working-prototypes/`, `_private/3_RESOURCES/AI Tooling/`, and the personal areas under `_private/2_AREAS/`.
- **Trust the stamps.** If `Last verified accurate` is old or "not yet", say the answer may be stale.
- **A failed read is not evidence.** If a connector, qmd or a file read fails, say what failed: missing, no permission, or timed out. Then stop that step. Never guess what the source says.
- **Don't write unless asked.** New material goes to `_private/0_INBOX/` and is processed via `3_RESOURCES/AI Skills/ingest/SKILL.md`. Never duplicate a fact; edit its canonical file. Structural changes get a `CHANGELOG.md` entry in the same pass.
- **Skills** in `3_RESOURCES/AI Skills/*/SKILL.md` are instructions for running this vault (start with `second-brain`). Read one before acting as it.

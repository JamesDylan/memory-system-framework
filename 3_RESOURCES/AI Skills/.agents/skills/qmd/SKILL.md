---
name: qmd
description: "Search the user's memory_system vault with QMD (local hybrid search over the vault's markdown). Use BEFORE reading or grepping vault files, for any question about {{ORG}}/{{PRODUCT}} initiatives, people, systems, decisions, actions or the vault itself, and before creating a note (to find an existing home). Works for any agent: MCP tools if present (mcp__qmd__query/get/multi_get/status), otherwise the `qmd` CLI."
---

# QMD — searching this vault

**Last touched:** 2026-10-29 (rewritten: the earlier version described a template's named index, hooks and bootstrap script that never existed here)

QMD indexes the vault's markdown for keyword (BM25), semantic (vector) and hybrid search. Inbox (`_private/0_INBOX/`) and archive (`4_ARCHIVE/`) are deliberately **not indexed**: they're raw or historical, never canonical.

## 1. Pick a surface (same index either way)

1. **MCP tools**, if they're in your tool list: `query`, `get`, `multi_get`, `status`. No index flag needed.
2. **CLI**: `qmd query|search|vsearch|get|multi-get …`. Plain `qmd`, with **no `--index` flag**. This vault uses qmd's default index.
3. **grep / file reads**, only if qmd isn't installed. Run `.scripts/qmd-bootstrap.sh` to install it.

> Don't use `--index memory_system`. That named index was retired on 2026-10-29, is stale, and may still exist on disk.

## 2. Search, then read, then answer

0. **Status and to-dos don't need search.** Open the canonical file directly: `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md`, the initiative's `STATE.md`, `1_PROJECTS/Actions/`, or `_private/1_PROJECTS/Actions/`. Search is for finding facts, decisions and definitions.
1. **Search** for candidates. **Always write a structured query** (`intent` + `lex` + `vec`); never pass the user's sentence as a plain query. Tested 2026-10-29: plain `qmd query "what does Engineer A own"` ranked the wrong person's page first; the structured form ranked it correctly.
   - Names, ticket IDs, file names, exact phrases → `lex` (BM25). Quote multi-word names: `lex: "Engineer A"`.
   - Concepts, "how does X work", "what did we decide" → `vec`, plus `lex` with the key nouns.
   - CLI: `qmd query $'intent: …\nlex: …\nvec: …' -n 8`, or `qmd search "TICKET-123" -n 5` for keywords only.
2. **Read** the full top hits. Fetch by the **`#docid` or `qmd://…` path that search returned** (`get` / `multi_get`). Snippets are leads, not facts.
   - ⚠️ **Never pass a real vault path that contains a space to `qmd get`** (for example `1_PROJECTS/{{ORG}}/{{PILOT_INITIATIVE}}/STATE.md`). qmd stores slug paths (`1-PROJECTS/{{ORG}}/{{PILOT}}-Native-Migration/STATE.md`), and an unmatched path silently fuzzy-matches **a different file**. To read a file by its real path, read it from disk instead.
3. **Answer from the canonical file**, and cite its real vault path. Convert a slug back to the real path: `-` may be `_` or a space; check on disk.

## 3. Trust rules (what makes an answer right in this vault)

- **One fact, one home.** `memory_index.md` → "Single Sources of Truth" says which file owns each fact type. If a search hit isn't the canonical file, follow it to the canonical one before answering.
- **Status questions:** `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md` first, then the initiative's `STATE.md`. `LOG.md` is history; `Artefacts/` may be stale.
- **What is X / who is Y:** entity pages in `3_RESOURCES/{{ORG}}/concepts/` and `2_AREAS/{{ORG}}/people/`; `2_AREAS/{{ORG}}/context/stakeholder_map.md` shows where each person fits.
- **Open to-dos:** `1_PROJECTS/Actions/` (initiatives) and `_private/1_PROJECTS/Actions/` (personal). `status: done` means closed.
- **Stamps:** `Last verified accurate` older than the file's rhythm, or "not yet", means lower trust. Say so in the answer.
- **Not {{ORG}}:** `_private/1_PROJECTS/Working-prototypes/`, `_private/3_RESOURCES/AI Tooling/`, and the personal folders in `2_AREAS/`. Never use them for work answers.
- Search results include each folder's **context** text, which says what the folder is for. Read it.

## 4. Writing

Don't write to the vault unless asked. New raw material goes to `_private/0_INBOX/` and is processed by the `ingest` skill (`3_RESOURCES/AI Skills/ingest/SKILL.md`). Before creating a note, search for an existing home (`vec` on the topic).

## 5. Keeping the index fresh

- `ingest` runs `qmd update && qmd embed` at the end of every run (daily, via `daily-slack-review`).
- The daily pull (`.scripts/daily-pull.sh`, 08:30) re-indexes through the git hooks from `qmd-bootstrap.sh` as a backstop.
- After bulk edits outside `ingest`, run `qmd update && qmd embed` yourself. `update` is fast; `embed` only processes changed docs.
- Check health with `qmd status`, or the MCP `status` tool. "Pending … need embedding" above a handful means semantic search is incomplete.

## 6. Setup and config (new machine or new agent sandbox)

- Run `.scripts/qmd-bootstrap.sh`. It writes `~/.config/qmd/index.yml` from the versioned template **`.scripts/qmd/index.yml`**, with this clone's path filled in. Then it indexes and embeds. Do not edit the generated file: the next run overwrites it.
- **Private collection.** If `../memory_private/qmd-collection.yml` exists, the script adds the `memory_private` collection. If not, it prints a note and sets up the shared collection only.
- **Re-index after a pull.** The script installs `post-merge` and `post-rewrite` git hooks that run `qmd update && qmd embed` in the background. It does not replace a hook you already have.
- **To change folder descriptions or ignores**, edit `.scripts/qmd/index.yml` (it's versioned), then re-run `.scripts/qmd-bootstrap.sh`. A new folder that agents should understand gets a `context:` entry there. Private-vault entries go in `qmd-collection.yml` in the private vault.
- MCP registration: `.mcp.json` → `qmd mcp`.

# _private/0_INBOX — Raw Capture

**This is the capture layer. Anything goes here first. No structure required.**

Drop raw material here without thinking about where it belongs: meeting notes, Slack exports, voice-memo transcripts, a half-formed feature idea, feedback on an existing initiative, a doc someone sent you, a screenshot of a chart.

## The promotion rule

Capture here is free; filing is deliberate, through `ingest`, and the raw file is then archived, never deleted. The rule in full: "Capture is separate from promotion" in `docs/doctrine.md` in the shared vault.

## Paste into chat first

New to the vault? You don't need this folder yet. Paste material straight into chat and say **"ingest this"**: the skill reads the pasted text, and no file is needed. Use this folder later, once you work in Obsidian or a file manager, or for a batch of files at once. What to give the agent first, and in what order: `docs/first-week.md` in the shared vault.

## How to process

Say **"ingest this"** (pointing at a file) or **"process my inbox"** (everything here). The `ingest` skill runs the loop: read → takeaways → route to the one canonical home → propose diffs → you approve → apply + log + clear.

Routing map lives in the `ingest` skill (`3_RESOURCES/AI Skills/ingest/SKILL.md`) and the single-source-of-truth table in `memory_index.md`.

## Health rule

Nothing in `_private/0_INBOX/` should be older than ~14 days. If it is, the system has stalled on processing — that is a signal, not normal. Anything stale gets processed or consciously killed, not left to rot.

## Naming convention (optional, helps)

`YYYY-MM-DD_short-description.md` — e.g. `2026-05-28_h2-roadmap-workshop-notes.md`. The date prefix keeps the folder chronological and greppable.

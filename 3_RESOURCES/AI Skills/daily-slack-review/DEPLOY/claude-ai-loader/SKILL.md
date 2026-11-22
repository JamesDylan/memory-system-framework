---
name: daily-slack-review
description: >
  Run the user's daily {{PRODUCT}} Slack review. Use this skill whenever the user asks for a
  Slack review, daily standup brief, morning brief, "what did I miss", "catch me
  up on Slack", "run my daily review", or any variation of reviewing recent Slack
  activity. This is a loader only — it holds no procedure of its own. The
  procedure lives in the user's vault and must be read before doing anything.
---

# daily-slack-review — loader

**This file contains no instructions for running the review.** It exists only to
point at the one copy that does. Do not infer, reconstruct, or improvise the
procedure from the description above.

## What to do

1. Read `3_RESOURCES/AI Skills/daily-slack-review/SKILL.md` in the user's vault via
   the Filesystem connector. Absolute path:
   <your-path>/memory_system/3_RESOURCES/AI Skills/daily-slack-review/SKILL.md
2. Follow it exactly as written, including its Step 4 — write both inbox files,
   emit the provenance footer, hand off to `ingest`.

## If the vault file is unreachable

Stop. Say so plainly and do nothing else:

> "The daily-slack-review procedure lives in the vault and I can't reach it —
> the Filesystem connector isn't available in this session. Enable it, or run
> the review from Claude Code instead. I'm not going to improvise the review
> from memory, because a plausible-looking improvised brief is exactly the
> failure this loader exists to prevent."

**Do not fall back to running the review from general knowledge of what it
should contain.** An improvised run produces output that looks correct and
silently corrupts the downstream `ingest` → `diff-propose` chain. Failing loudly
is the intended behaviour, not a degraded one.

## Why this file is a stub

A full copy of the procedure deployed here diverged from the vault three times
(6, 10, 11 Aug 2026) and was still diverged on 12 Aug after being recorded as
fixed. An uploaded package cannot be diffed against the vault from this machine,
so drift here is undetectable by any local check. A stub cannot drift, because
it carries nothing to drift from. `lint.mjs` Check 6 (`mode: "pointer"`) enforces
that this file stays short and keeps naming its vault source.

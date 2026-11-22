---
name: emerge
description: >
  Surface unnamed patterns and recurring themes across the user's recent vault
  activity — the Thinking-layer "emerge" operation. Use this skill whenever
  the user says "what patterns are emerging", "what's emerging", "what themes am I
  not seeing", "connect the dots across the last month", "what keeps coming up",
  "surface patterns", "what's the meta-story", or wants a synthesis pass over
  recent notes rather than an answer to a specific question. It scans the recent
  window (CHANGELOG, initiative LOGs, learning_insights, daily notes, Slack
  reviews) for repeated signals that don't yet have a name, and proposes naming
  them. First action: read memory_index.md. Core rule: a pattern needs at least
  three independent pieces of evidence from different files/dates — two is a
  coincidence; cite the evidence for every pattern.
---

# Emerge — Skill

## Purpose

Find the themes the user is living but hasn't named yet. Individual notes capture
events; this skill reads across them to spot the recurring signal — the risk
that keeps reappearing under different labels, the customer complaint surfacing
in three initiatives, the coaching issue common to two PMs. It names the
pattern and shows the evidence, so a fuzzy sense becomes a nameable thing the user can
act on.

This is a **Thinking-layer** skill (Layer 2). It reads and synthesises; it does
not mutate canonical files. Named patterns compound back via `ingest`.

## Doctrine (non-negotiable)

1. **Three-evidence rule.** A pattern needs ≥3 independent observations from
   different files or dates. Two is a coincidence; one is an anecdote. Cite the
   evidence for each pattern — file + date/context.
2. **Name the unnamed, don't restate the known.** Skip patterns already named in
   a canonical file (a known risk, a tracked theme). The value is the thing not
   yet labelled.
3. **Bounded window.** Default to the last ~30 days unless the user sets a window.
   Emergence is about the recent signal, not all-time history.
4. **Evidence over eloquence.** A well-evidenced boring pattern beats a
   beautiful ungrounded one. No pattern-matching for its own sake.
5. **Answers compound back.** A confirmed pattern gets filed via `ingest` — as a
   learning, a risk, or a candidate — so it stops being re-discovered every
   month (Doctrine 6).

## Step 0 — Read first

1. `memory_index.md` — the router (tells you which files carry recent activity).
2. `CHANGELOG.md` — last ~30 days, the spine of recent activity.

## Step 1 — Set the window and the corpus

Default window: last 30 days. Confirm or adjust if the user specifies. Assemble the
recent corpus using QMD (`mcp__qmd`) and `multi_get` globs:

- `CHANGELOG.md` (recent entries) — the change spine.
- Initiative `LOG.md`s touched in the window.
- `2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/learning_insights.md` — recent learnings/experiments.
- Recent daily notes / Slack review outputs / `_private/0_INBOX` items (read-only here —
  emerge is allowed to *look* at inbox for raw signal, but never promotes it
  directly; that's `ingest`).
- `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md` — current risks/priorities, to check what's
  already named.

## Step 2 — Cluster and name

Group the recent signal into candidate patterns. For each, check: is this
already named in a canonical file? If yes, drop it (or note "already tracked").
If no and it clears the three-evidence rule, it's a candidate pattern.

Look specifically for:
- The same problem appearing across **multiple initiatives** under different names.
- A customer/VOC signal recurring in different contexts.
- A team/coaching theme common to **more than one PM**.
- A risk materialising in slow motion across several dated entries.
- A decision the user keeps re-making (a sign of an unresolved root cause).

## Step 3 — Produce the synthesis

```
# Emerging Patterns — [window, e.g. last 30 days]

## Named patterns (≥3 evidence, not yet in the vault)
### 1. [Proposed name for the pattern]
- What it is: [one line]
- Evidence: [fact + source/date] · [fact + source/date] · [fact + source/date]
- So what: [why it matters / what it implies]
- Suggested home: [learning_insights.md / a risk in _ACTIVE_CYCLE / a candidate]

## Weak signals (2 evidence — watch, don't name yet)
- [signal] → [the third data point that would confirm it]

## Already tracked (surfaced but not new)
- [pattern] → already lives in [file]
```

End with **one question worth sitting with** — the meta-observation the patterns
point at together.

## Step 4 — Compound back (offer, don't force)

For each named pattern the user confirms is real, offer to file it via `ingest` to
its canonical home. A pattern that stays in chat gets rediscovered next month;
filed, it becomes something the system knows.

## Pushback rules (calibrated to the user)

- **If a "pattern" has <3 evidence:** call it a weak signal, don't inflate it.
  Name what the third data point would be.
- **If the pattern is already tracked:** say so and move on — don't pad the
  report with things the user already knows.
- **If the user wants a specific answer, not a synthesis:** this is the wrong skill;
  hand back to `second-brain` for a targeted read.

## What this skill does NOT do

- Does not auto-generate synthesis pages into the vault (that's the bloat trap
  the general PKM tools fall into). It proposes; `ingest` files, on approval.
- Does not promote `_private/0_INBOX` items — it may read them as signal, but promotion is
  `ingest`'s job.
- Does not edit canonical files or make decisions.

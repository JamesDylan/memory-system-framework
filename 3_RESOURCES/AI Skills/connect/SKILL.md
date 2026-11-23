---
name: connect
description: >
  Bridge two ideas, initiatives, or domains to generate non-obvious connections
  — the Thinking-layer "connect" operation. Use this skill whenever the user says
  "connect these", "what's the link between X and Y", "how does this relate to",
  "bridge these domains", "find the non-obvious connection", "cross-pollinate",
  "what does X have to do with Y", or wants to spark ideas by colliding parts of
  the vault that don't normally touch. It uses semantic search to find
  related-but-distant material and proposes concrete links, transferable
  patterns, and ideas. First action: read memory_index.md. Core rule: propose
  connections grounded in real vault content on both sides — the value is a
  useful non-obvious link, not a forced or trivial one.
---

# Connect — Skill

## Purpose

Generate ideas by deliberately colliding parts of the vault that don't normally
meet. The user's knowledge is siloed by PARA structure — initiatives, learnings,
strategy, career all live apart. This skill bridges them: takes a concept,
initiative, or problem and finds the related-but-distant material elsewhere,
then proposes transferable patterns and concrete ideas. It's the "borrow the
solution from another domain" move.

This is a **Thinking-layer** skill (Layer 2). It reads and reasons across the
vault; it does not mutate canonical files. Useful connections compound back via
`ingest`.

## Doctrine (non-negotiable)

1. **Both sides grounded.** A connection links two real things in the vault. If
   one side is invented, it's not a connection — it's a suggestion, and it
   should say so.
2. **Non-obvious over trivial.** "These two initiatives both involve customers"
   is not a connection. The value is the link the user wouldn't have made — a pattern
   that transfers, a solution from one domain that fits another.
3. **Concrete over abstract.** End at "so you could do X", not "these are
   thematically related". A connection that doesn't imply an action is
   incomplete.
4. **Semantic search is the engine.** Use QMD `vec`/`hyde` to find distant-but-
   related material — that's exactly what keyword search misses.
5. **Answers compound back.** A connection worth keeping (a new candidate, a
   transferable learning) gets filed via `ingest` (doctrine: Answers compound back via ingest).

## Step 0 — Read first

1. `memory_index.md` — the router + the map of what lives where.
2. Whatever canonical file(s) define the **anchor** — the thing the user wants to
   connect from (an initiative README, a learning, a strategy section).

## Step 1 — Establish the anchor(s)

Two modes:
- **Two named things** ("connect the migration and churn prevention") — read
  both anchors.
- **One thing, open-ended** ("what connects to the 5th-booking inflection") —
  read the one anchor, then let semantic search find the far side.

State the anchor(s) back in a sentence so the user can correct the framing.

## Step 2 — Find the distant relatives

Use QMD (`mcp__qmd`) — lead with `vec` and `hyde`, since the whole point is
finding material that doesn't share keywords:

- Search the anchor's core ideas semantically across the vault.
- Deliberately reach into *other* PARA branches — a strategy idea that echoes a
  coaching theme, a customer learning that mirrors a career-development pattern,
  a solved problem in one initiative that maps onto an open one.
- Note the strength of each hit (`minScore` to filter noise) and, more
  importantly, *why* it's related despite living far away.

## Step 3 — Propose the connections

```
# Connections — [anchor(s)]

## The non-obvious links
### 1. [Anchor A] ↔ [distant thing B]
- The link: [what they share that isn't surface-level]
- Grounded in: [fact/source A] · [fact/source B]
- So you could: [concrete, actionable idea this connection implies]

### 2. …

## Transferable patterns
- [A pattern/solution that worked in one place] → could apply to [the other]
  because [why]. Source: [file].

## Reaches (flagged as speculative)
- [connection where one side is thinner / more of a hunch]
```

End with the **single most promising thread** to pull, and why.

## Step 4 — Compound back (offer, don't force)

If a connection produced something durable — a genuinely new feature idea, a
transferable learning worth recording — offer to file it via `ingest` (a new
`CANDIDATES.md` entry, a note in `learning_insights.md`). The connection that
stays in chat is forgotten; filed, it's a seed.

## Pushback rules (calibrated to the user)

- **If the connection is trivial** (shared surface theme, no transfer): don't
  serve it. A weak connection dilutes the strong ones.
- **If one side isn't really in the vault:** say so — it's a suggestion drawing
  on outside knowledge, not a vault connection. Keep the distinction honest.
- **If the user wants a status answer, not idea generation:** wrong skill; hand
  back to `second-brain`.

## What this skill does NOT do

- Does not force connections to hit a quota. Two strong links beat six weak ones.
- Does not edit canonical files or auto-create candidates — `ingest` does that on
  approval.
- Does not replace `emerge`: `emerge` finds patterns *within* recent activity;
  `connect` bridges *across* domains regardless of recency.

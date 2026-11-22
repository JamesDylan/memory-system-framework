---
name: challenge
description: >
  Red-team a proposal, decision, or plan using the user's own vault history — the
  Thinking-layer "challenge" operation. Use this skill whenever the user says
  "challenge this", "poke holes in this", "steelman the opposite", "argue
  against this", "what am I missing", "red-team this", "stress-test this
  decision", "should I really do X", or brings a proposal/plan/bet and wants it
  pressure-tested rather than validated. It loads the relevant cycle state,
  strategy, past decisions, and learnings, then builds the strongest case
  AGAINST the proposal grounded in their actual history — prior contradicting
  decisions, past failures, stakeholder realities, and metric truths — not
  generic devil's advocacy. First action: read memory_index.md. Core rule:
  every objection must cite a real vault fact; no generic "have you considered"
  filler.
---

# Challenge — Skill

## Purpose

Be the disciplined internal critic the user can't fully be for their own ideas.
Given a proposal, decision, or plan, build the strongest evidence-backed case
*against* it using what the vault actually knows — past decisions, prior
failures, customer learnings, stakeholder positions, and metric realities. The
goal is not to kill the idea; it's to surface the objections the user would otherwise hit
three weeks in. The user decides what survives.

This is a **Thinking-layer** skill (Layer 2). It reads and reasons; it does not
mutate canonical files. Its output compounds back via `ingest` if it's worth
keeping (Doctrine 6).

## Doctrine (non-negotiable)

1. **Every objection cites a real vault fact.** A challenge with no source is
   noise. If you can't ground it in a decision, learning, metric, stakeholder
   position, or risk that's actually in the vault, either go find the fact or
   flag it as an unverified hunch — don't dress it as knowledge.
2. **Argue against, honestly.** Steelman the opposition. Don't hedge every
   objection into mush. The user wants the real case against, not "on the other
   hand" both-sidesing.
3. **Read only what the proposal touches.** Use the loading model — don't pull
   the whole vault. Let the proposal's domain pick the files.
4. **Don't decide for them.** Surface the strongest objections and their
   severity. The go/no-go is their.
5. **Answers compound back.** If the challenge produces a durable insight (a
   risk worth tracking, a learning, a candidate that should change), offer to
   file it via `ingest` — don't let it vanish into chat.

## Step 0 — Read first

1. `memory_index.md` — the router + SoT table (tells you where the relevant
   truth lives).
2. `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md` — current cycle state, priorities, risks
   (what this proposal competes with and what must not fail).

## Step 1 — Pin down the proposal

State back, in one or two sentences, the exact proposal you're challenging and
the decision it implies. If it's vague ("we should do more discovery"), ask one
sharpening question first — you can't challenge a moving target.

## Step 2 — Pull the relevant history

Use QMD (`mcp__qmd` — lex for exact terms, vec/hyde for themes) plus targeted
reads to gather the evidence base the proposal touches:

- **Contradicting past decisions** — `CHANGELOG.md` and initiative `LOG.md`s: has
  the user decided the opposite before, and why?
- **Prior failures / learnings** — `2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/learning_insights.md`:
  has something like this been tried? What happened?
- **Strategy fit** — `2_AREAS/{{ORG}}/context/strategic_context.md`: does it serve
  the stated objectives, or is it a shiny distraction?
- **Metric reality** — `2_AREAS/{{ORG}}/context/metrics_dashboard.md`: do the
  numbers support the premise, or contradict it?
- **Stakeholder friction** — `2_AREAS/{{ORG}}/context/stakeholder_map.md` and
  `_private/2_AREAS/{{ORG}}/context/stakeholder_notes.md`: who pushes back, and
  what do they care about?
- **Opportunity cost** — `_ACTIVE_CYCLE.md` + `ROADMAP.md`: what does this
  displace? What's the "instead of" cost?

## Step 3 — Build the challenge

Produce a scannable, ranked case against. Lead with the objections most likely
to actually bite.

```
# Challenge — [proposal, in one line]

## The strongest case against
1. [objection] — grounded in [file/fact]. Why it bites: [consequence].
2. …

## History says
- [past decision/failure/learning that contradicts or warns] → [source]

## Opportunity cost
- Doing this instead of: [what it displaces] → [source]

## What would have to be true for this to work
- [the assumptions the proposal is betting on — name them explicitly]

## Where the challenge is weak
- [objections you couldn't ground — flag as hunches, not facts]

## Verdict aid (not a decision)
- Kill / de-risk / proceed-with-eyes-open — and the single biggest thing to
  resolve first.
```

## Step 4 — Compound back (offer, don't force)

If the challenge surfaced something durable — a real risk, a learning, a
candidate whose status should change — offer to file it via `ingest` to the
right canonical home (a risk in `_ACTIVE_CYCLE.md`, a learning in
`learning_insights.md`, a status change in `CANDIDATES.md`). The user approves the
routing; `ingest` does the writing.

## Pushback rules (calibrated to the user)

- **If the user wants validation, not a challenge:** name it. "You asked me to
  challenge this — do you want the case against, or a sanity check that it's
  sound?" Then give the one the user actually wants.
- **If the proposal is too vague to challenge:** sharpen it first, don't
  manufacture objections against a strawman.
- **If your objections are generic PM platitudes:** stop. Go read the actual
  initiative/metric/decision and object from that, or say you don't have the
  evidence.

## What this skill does NOT do

- Does not edit canonical files. It reasons; `ingest` writes.
- Does not make the decision — it arms the user to make it.
- Does not challenge from memory. Cycle/strategy/metric facts come from the
  vault, read fresh (they drift).

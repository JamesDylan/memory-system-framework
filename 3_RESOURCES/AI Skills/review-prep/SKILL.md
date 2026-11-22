---
name: review-prep
description: >
  Assemble evidence-based performance material from the performance-evidence
  graph (competency backlinking) — the judgment layer on top of
  `Competency_Evidence.base`. Use this skill whenever the user says "prep [PM]'s
  review", "prep my review", "assemble my OKR evidence", "evidence for OKR2",
  "what's the evidence for [competency]", "build the case for [PM]'s promotion /
  raise", "draft [PM]'s performance summary", "what have I got on [PM] this
  cycle", "pull my wins for the skip-level lead", or is preparing for an annual/quarterly
  review, a monthly the skip-level lead 1:1, or a remuneration conversation. It runs the
  evidence-card query, follows each card's `source:` pointer to the canonical
  fact, checks coverage against the competency set (naming the gaps), and drafts
  the narrative in the house frameworks — WHAT/HOW/LEARN for a PM,
  recommendation → rationale → asks (decision-first) for the user's own OKR review.
  First action: read this skill's Performance-Evidence Graph section and
  the relevant competency notes. Core rule: read-only — it never invents
  evidence, never restates a metric the card didn't point to, and any keeper
  synthesis compounds back via `ingest`, never by mutating a canonical file
  directly.
---

# Review-Prep — Skill

## Purpose

Turn a performance review from a memory-scramble into a query. The evidence
already exists as backlinks in the performance-evidence graph; this skill reads
the graph, follows the pointers to the real wins, judges coverage, and drafts the
review narrative in the format the audience expects. It is the Phase-2 judgment
layer that sits on top of the zero-token `Competency_Evidence.base` (Phase 1) —
the same procedural/judgment split as `lint`.

It prepares; the user decides. It drafts; it never files. Anything worth keeping
goes back through `ingest`.

## Doctrine (non-negotiable)

1. **Evidence is grounded, never invented.** Every claim in the draft traces to
   an evidence card and, through its `source:`, to a canonical fact. No card →
   no claim. If the graph is thin, the honest output is "thin evidence here",
   not a fabricated win.
2. **Read the canonical fact, don't trust the card body.** The card body is a
   one-line pointer; the real metric/outcome lives at `source:`. Follow the link
   and read it before you state a number. Never restate a figure the card only
   gestured at.
3. **Read-only.** This skill does not edit competency notes, evidence cards,
   `Direct Reports.md`, `career_development.md`, or reviews. Drafts land in chat
   (or, if the user wants them kept, a candidate for `ingest`).
4. **Gaps are findings.** A competency with zero evidence — or a development goal
   with no evidence toward it — is the most valuable thing the query surfaces.
   Name it explicitly; don't paper over it.
5. **Single source of truth holds.** Judgment about a person lives in
   `Direct Reports.md`; OKR status lives in `career_development.md`. This skill
   reads them and the graph; it does not duplicate them into a new home.

## Step 0 — Read first

1. The **Performance-Evidence Graph** section at the end of this file
   (the model + the two SoT rules; moved here from `memory_index.md` 2026-11-21).
2. `_private/2_AREAS/Career/Competency_Evidence.base` — the view definitions (what's
   queryable and how it groups).
3. The relevant **competency notes** (the link-targets for the subject).

## Step 1 — Scope the ask

Confirm two things before querying:

- **Subject:** a PM (team review) or the user (own OKR review).
- **Frame:** which competencies / OKR / period. Default period = current cycle
  unless the user names an annual/quarterly window.

## Step 2 — Run the query (mechanically, like Phase 1)

Read the evidence cards for the subject (filter `type: evidence` +
`person: [subject]`, optionally by date window). Group by `competency` — a card
tagged with two competencies belongs under both. For a PM, also pull any
`type: dev-goal` notes for them and the competency each ladders to.

If Obsidian is open, this is literally the `Competency_Evidence.base` view
(*Team — by PM*, *My OKR Evidence*, or *By Competency*). Headless, read the card
files directly.

## Step 3 — Follow the pointers and judge (the Phase-2 half)

For each card, open its `source:` and read the canonical fact. Then judge:

- **Strength per competency:** how much real evidence, how strong, how recent.
- **Coverage gaps:** which competencies have no evidence this period; which
  development goals have no evidence toward them (the empty-state signal).
- **Pattern:** what the evidence says as a whole — a strength to name, a
  dependency to break, a dev area that has or hasn't moved. Cross-check against
  the coaching notes in `Direct Reports.md` (PM) or the watch items in
  the context file named in `_private/ME.md` (the user) — does the evidence confirm or contradict them?

## Step 4 — Draft in the house framework

**For a PM** — use the performance framework from
`Annual Performance Reviews.md`:

- **WHAT** — individual contribution + leadership contribution (did they help the
  team get better?), each backed by cited evidence.
- **HOW** — the guiding principles (BGB / BAGH / Win Together), backed by the
  HOW-anchored competency evidence.
- **LEARN** — what they learned / where they grew; tie to their development
  goals and whether evidence moved.
- End with **gaps + the development conversation** (the empty competencies).

**For the user's own review** — decision-first, per the context file named in `_private/ME.md`:

- **Recommendation → rationale → asks**, evidence laddered to the OKR/KR.
- Apply the "Watch items" in `_private/ME.md` (for example, name the user's own
  contribution explicitly).
- Flag any KR with thin evidence as a gap to close before the the skip-level lead review.

Keep it structured and bulleted. Cite the canonical source for every claim so
The user can open it.

## Step 5 — Offer to compound it back

If a draft or a surfaced gap is worth keeping (e.g. a new coaching observation,
a dev-goal update, a win that wasn't yet carded), **propose routing it through
`ingest`** — do not write it yourself. A review draft itself is usually
ephemeral; the *insight* it exposes is what compounds back.

## Pushback rules (calibrated to the user)

- **"Just write the review" when the graph is thin:** refuse to pad it. Report
  the thin coverage as the finding — that's the signal to go capture evidence,
  not to invent it.
- **Restating a number from memory or a card body:** don't. Open the `source:`
  and read the canonical fact, or say the source is missing.
- **Attributing a team win to make a PM (or the user) look good:** don't inflate.
  Represent what the evidence actually supports; for the user, apply the
  "Watch items" in `_private/ME.md`.
- **Editing `Direct Reports.md` / `career_development.md` mid-prep:** don't. This
  skill is read-only; changes go through `ingest` on the user's approval.

## Doctrine alignment

- Phase-2 judgment layer over the Phase-1 Base — the `obsidian-mind`
  procedural/judgment split, same as `lint`.
- Enforces single source of truth (Doctrine 1) by reading canonical facts through
  pointers and never creating a second home for them.
- "Answers compound back" (Doctrine 6): keeper insight re-enters via `ingest`.

## What this skill does NOT do

- Does not invent, infer, or embellish evidence that isn't in the graph.
- Does not edit competency notes, evidence cards, or canonical files (read-only).
- Does not create evidence cards — that's `ingest`'s job when a win is captured.
- Does not make the final review call or the remuneration decision — it assembles
  the material and names the gaps; the user decides.

## Performance-Evidence Graph (competency backlinking)

Turns a performance review into a query instead of a memory-scramble. Two use
cases: the user's own OKRs, and evidence-based reviews for a lead's PMs. Three note
types, all of which obey single-source-of-truth by **holding no facts**:

| Note type | Where | Role | SoT status |
|---|---|---|---|
| **Competency** | `_private/2_AREAS/Career/Competencies/` (OKR-aligned) · `My Team/Competencies/` (shared: skills-matrix axes + HOW guiding principles) | Link-target / anchor — definition only | Holds **no facts** |
| **Evidence card** | `_private/2_AREAS/Career/Evidence/` · `My Team/Evidence/` | The backlink — `type: evidence` frontmatter (person, competency links, nature, date, source, kr) + a one-line pointer body | Holds **no facts** — pointer only |
| **Development goal** | `My Team/Development Goals/[PM]/` | A target on a shared competency for a period | Holds the goal + target |

**Aggregation:** `_private/2_AREAS/Career/Competency_Evidence.base` (procedural, zero-token
view; groups cards by competency / PM / OKR) + each competency note's native
Linked Mentions. A `review-prep` judgment skill is the planned Phase-2 layer.

**Two hard rules (enforced by `lint` judgment pass):**
1. An evidence card body is a **pointer only** — never restate the metric/outcome.
   The number lives once, in its canonical home (`learning_insights.md`, a
   `LOG.md`, or a coaching note), which the card links via `source:`.
2. A competency note holds **definitions only** — per-person judgment stays in
   `Direct Reports.md`; OKR status stays in `career_development.md`.

Evidence cards are created by `ingest` when a win is captured — the user never
hand-writes one.

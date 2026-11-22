---
name: diff-propose
version: 2026-11-22.1
description: >
  Pure propose-and-present function for Move 3 (Slack→STATE automation). Takes
  raw signal (Slack export or ingest content) plus one or more target STATE.md
  files and returns proposed field-level diffs with source attribution and a
  confidence tag — then presents them via an interactive review widget it owns
  itself, so any caller gets consistent review UI without reimplementing it.
  Does not apply diffs, does not touch CHANGELOG, does not decide
  approve/reject — the calling skill applies the user's decisions. Called by
  `ingest` only (refactored 2026-08-11 — `daily-slack-review` no longer calls
  this directly; see `ingest/SKILL.md` Step 2c). If you are Claude and a
  diff-propose call is needed, it is because `ingest` reached its
  pilot-initiative routing step, not because the user asked for diffs directly.
---

# diff-propose — Skill

## Purpose

Turn raw signal into candidate STATE.md edits the user can approve in seconds,
without duplicating extraction logic inside `daily-slack-review` and `ingest`
separately (Principle 1 — single source of truth applied to logic, not just
facts). This skill is the only place field-mapping and confidence-scoring
logic lives.

## What this skill does NOT do

- Does not apply any diff. Output is proposals only.
- Does not touch `CHANGELOG.md`, `diff-log.md`, `diff-sessions.md`, or `last
  touched`/`last verified accurate` stamps — those are the calling skill's
  job, after the user's decision.
- Does not propose changes to `BRIEF.md` or `LOG.md`. STATE.md fields only.
- Does not auto-apply anything regardless of confidence tier. Confidence is
  scored for later validation (Move 3.1 decision point), not acted on now.
- Does not fabricate a field placement for signal that doesn't clearly map to
  one. Ambiguous signal goes to `unrouted`, not to the nearest-sounding field.
- **Does present diffs for review itself** (see below) — this is the one thing
  that changed 2026-08-11. Presentation moved here from the calling skill so
  it doesn't have to be rebuilt per-caller.

## Input contract

```json
{
  "signal": "<raw text: Slack messages/threads, or ingest file content>",
  "targets": [
    { "initiative": "<name>", "state_content": "<full current STATE.md text>" }
  ]
}
```

- `signal` may reference zero, one, or multiple target initiatives in a single
  call — the calling skill decides which STATE files are in scope for the
  session (e.g. the active pilot), not this skill.
- `state_content` must be the STATE.md content as it exists right now, not a
  cached or remembered version — diffs are computed against current text.

## Output contract

```json
{
  "diffs": [
    {
      "initiative": "<name>",
      "field": "<one of: Right now | Next decision needed | Blocker | Risks | Last 3 material events>",
      "op": "replace | retire",
      "current_value": "<verbatim current field text>",
      "proposed_value": "<full replacement text for that field, within its budget>",
      "log_entry": "<what leaves STATE in this diff, written for LOG.md — or null if nothing leaves>",
      "confidence": "direct | inferred",
      "contradicts_current": true | false,
      "source_quote": "<attributed, ≤15 words, paraphrase if longer>",
      "source_link": "<slack permalink, or ingest filename + date>",
      "source_flags": ["stale", "transcript" and/or "disagree", or empty — see "Document sources" and "Source discipline" below]
    }
  ],
  "unrouted": [
    { "signal_excerpt": "<short excerpt>", "reason": "<why nothing was proposed>" }
  ]
}
```

- Diffs are **whole-field replacements**, never partial in-string edits. The
  calling skill performs the actual `edit_file` call against the full field.
- One diff per (initiative, field) pair per call. If a single source message
  touches two initiatives, or two fields of the same initiative, emit two
  separate diff objects — never merge.

## STATE is a snapshot, not a history (added 2026-10-29)

**Why this exists.** Over the pilot, the pilot initiative's `STATE.md` grew from 5,344 to 12,055
words. Every diff was a "whole-field replacement" in form, but in practice each
`proposed_value` was the old field plus a new dated sub-bullet. Resolved risks
stayed in place with strikethrough, and `Last touched` turned into a changelog.
Each diff looked fine on its own while the file stopped being readable, and the
88% approval rate hid it. STATE answers "what is true now". LOG answers "what
happened". A diff that keeps history in STATE is wrong even if every fact in it
is right.

**Two operations:**

- **`replace`** — rewrite the field so it says what is true *now*. The new
  fact supersedes the old one; it is not added below it. If the rewrite drops
  anything worth keeping (the old value, the reasoning, who said what), put it
  in `log_entry`.
- **`retire`** — remove an item that is no longer live: a risk closed, a
  decision made, a blocker cleared, an event pushed out of the last 3.
  `proposed_value` is the field without it. `log_entry` records what was
  retired and why. Retiring is how STATE stays small; propose it whenever the
  signal shows an item is resolved, even if nothing new replaces it.

**Never put these in `proposed_value`:** "Update (date)" sub-bullets under an
existing item, "Original entry" or history paragraphs, strikethrough or
"CLOSED"/"resolved" items, or more than one source link per item. Each of
those means the content belongs in `log_entry`. One exception: an item whose
sources disagree names both (see "Source discipline").

**Field budgets.** The original 200-word cap was never enforced and doesn't fit
a programme the size of the pilot initiative, so the budget is per field:

| Field | Budget |
|---|---|
| Right now | ≤ 6 bullets, ≤ 40 words each |
| Next decision needed | ≤ 6 bullets, ≤ 40 words each (decision, owner, by when) |
| Blocker | ≤ 3 bullets, or "none" |
| Risks | ≤ 12 one-line risks, ≤ 30 words each (🔴/🟡 + ID + one line + owner) |
| Last 3 material events | exactly 3, one line each |

If a `replace` would push a field over budget, propose a `retire` of the
least-live item in the same run. Don't exceed the budget and leave it for later.

**`Last touched`** is one date plus at most one short clause. Replace it; never
append. The change history is in LOG and CHANGELOG.

## Confidence rubric (apply literally, don't eyeball it)

- **`direct`** — the proposed value is stated as fact, in a single source
  passage, by someone with authority over that fact (the owner, PM, or someone
  reporting a decision/completed work they made or witnessed directly).
- **`inferred`** — anything else: implied, secondhand, hedged ("might", "sounds
  like", "probably"), or reconstructed by combining two or more separate
  messages/threads.
- **Hard rule:** if producing the proposed value required combining signal from
  more than one message or thread, tag `inferred` — even if each individual
  message read as confident. Confidence describes the evidence chain, not the
  tone of any single message in it.

### Document sources (added 2026-10-29)

Applies when the signal is anything other than live Slack: docs, decks, board
exports, inbox captures, meeting notes. Diffs from these were 39% clean against
88% for live Slack. The edits corrected stale or wrong documents (9/10 inbox
fragment, 10/14 draft design doc, 10/27 deck), plus one Gemini mis-transcription
(8/14).

- **Source-date check.** Put the source's own date (doc, deck or meeting date,
  not the ingest date) in `source_link`. If it's older than the newest date in
  the current field value, or older than 7 days, tag `inferred` and add
  `"stale"` to `source_flags`.
- **Gemini transcripts and notes.** Names, IDs and ticket numbers that appear
  only in the transcript are `inferred`; add `"transcript"` to `source_flags`.
  Gemini mishears names (8/14: "Rene" for Partner contact A).

### Source discipline (added 2026-11-22, PLAN S2.6, approved by the owner, `_private/ME.md`)

Applies to every diff, from any signal.

- **Name the source of a claim about a person.** A claim about a person, an
  owner, an approval or a decision names its source in `proposed_value` (who
  said it, where, and the date). If the signal gives no source, write
  "unclear" in place of the source. Do not write an inference as a fact.
- **Show both sources when they disagree.** If two sources give different
  values for the same fact, `proposed_value` states both, each with its source
  and date. Do not choose one. Add `"disagree"` to `source_flags`, put both
  links in `source_link`, and tag `inferred`.
- Why: Risks and Next decision needed are the fields where an inference most
  often reads like a fact.

## Contradiction handling

- If the proposed value conflicts with the current field's content (not just
  extends it — actually conflicts), set `contradicts_current: true` and keep
  `current_value` populated so the reviewer sees exactly what's being
  overturned, not just what's being added.
- Never suppress a diff because it contradicts current state. Surface it —
  the user decides, this skill doesn't resolve conflicts.
- A statement that merely updates a stale-but-not-wrong field (e.g. "still
  waiting on X" restating an existing blocker) is not a contradiction — it's
  either no diff at all (see noise suppression below) or a `direct`
  confirmation depending on whether it adds new information.

## Noise suppression (the failure mode this skill must not have)

Before emitting a diff, check: does this signal add information the field
doesn't already contain? If the signal is a near-duplicate of an existing
pattern already reflected in the field or the initiative's LOG (same root
cause, same shape, no new owner/date/resolution), do not emit a diff. Route it
to `unrouted` with reason `"duplicate of established pattern, no new
information"`.

**No reword-only diffs (added 2026-11-22, PLAN S2.6).** Compare the facts in
`proposed_value` with the facts in `current_value`: names, owners, dates,
numbers, status, IDs. If they are the same and only the words are different,
do not emit the diff. Route it to `unrouted` with reason `"reword only, no new
fact"`. A diff that also retires an item or adds a fact is not reword-only.

This is not the same as ignoring real recurrence — if a recurring pattern
crosses a threshold worth surfacing (e.g. it's now unresolved for materially
longer, or a new instance adds a new data point like a new market or a named
owner), that IS new information and gets a diff. The test is informational
delta, not surface-level similarity.

## Routing rules

- **Route to the initiative that owns the SURFACE being measured, not the one that owns the underlying SERVICE. (added 2026-08-14)**

  **The test, applied before every diff:** *which PM would be accountable if this went wrong?* If the answer is not the target initiative's owner, the routing is wrong — re-route or mark `unrouted`. Do not proceed on the basis that the topic sounds like the initiative.

  **The incident this exists to prevent.** On 14 Aug, two of four proposed pilot-initiative diffs were rejected by the user as misrouted, and both failed the same way. (1) The Demand API v3 excluding to/from city codes for flight, car and hotel search — belongs to search widgets, not the pilot initiative, even though the pilot carries its own Demand API milestone. (2) New registration endpoints being slower than the BBM flow — belongs to Onboarding Personalisation, not the pilot, even though the endpoints are migration-adjacent.

  Both facts were correct and both were scored `direct`, correctly. **The confidence rubric worked; the routing rules didn't.** Signal was anchored on shared vocabulary ("Demand API", "endpoint migration") rather than on which team owns the thing being measured. Confidence tells you how good the evidence is, never whether the diff landed in the right file — do not read a `direct` tag as reassurance about placement.

  Corollary: an initiative owning a *service* does not own every consequence of that service changing. Consuming surfaces have their own owners and their own deadlines, and folding them in makes them inherit the owning initiative's sequencing and lose their own.

- A signal maps to a field only if it's specific enough to write a concrete
  replacement value. "Pricing stuff is a mess" is not specific enough for
  `Blocker` or `Risks` — it's `unrouted`.
- Thread replies are first-class signal, not secondary. Historically the
  weakest coverage point in `daily-slack-review` — treat reply content with
  the same routing rigor as parent messages, including when the reply is where
  the actual decision or fact lives and the parent is generic.
- Never invent a field. If none of the five STATE fields fit, it's `unrouted`
  — do not create a sixth field or repurpose an adjacent one.

## Failure modes — handle explicitly

| Symptom | Action |
|---|---|
| Signal empty or entirely off-topic for all targets | Return `diffs: []`, `unrouted: []`. Don't force output — tell the caller plainly, e.g. "No STATE diffs proposed this run." |
| Same fact appears in signal for two different targets by mistake (e.g. wrong initiative name in the message) | Route to the initiative the content is actually about, not the one literally named, if unambiguous; otherwise `unrouted` with reason noted. |
| Signal is *about* a service a target initiative owns, but the impact lands on a surface another team owns | **`unrouted`**, reason `"service-owner vs surface-owner ambiguity — needs an owner decision"`. Do not default to the service owner. This is the 14 Aug failure class; see Routing rules. |
| `state_content` for a target is missing/empty | Skip that target, note in `unrouted` — don't guess at a baseline to diff against. |

## Presenting diffs for review

This skill owns its own review UI — the calling skill hands over signal and
targets, and gets back both the diffs *and* an interactive widget already
rendered for the user, ready for their decision. The calling skill's only remaining
job is parsing their reply and applying it (see the calling skill's own apply
step — currently `ingest` Step 4).

1. If `diffs` is empty: state plainly, e.g. "No STATE diffs proposed this run
   for <initiative>." Don't fabricate content to look useful.
2. If diffs exist, render them as an interactive widget, not a markdown block:
   - Call `visualize:read_me` with `modules: ["interactive"]` once per session
     before the first `visualize:show_widget` call (silently — don't narrate it).
   - Build one card per diff: id, initiative, field, op badge
     (replace/retire), confidence badge (direct/inferred), a `contradicts
     current` badge when true, a badge per `source_flags` entry ("may be
     stale: source dated …", "transcript", "sources disagree"), the current and proposed values, the
     `log_entry` (labelled "moves to LOG") when present, the field's word
     count before → after, source quote + link, and three per-card controls
     (Approve / Reject / Edit, with a textarea for Edit).
   - **Reason chips (added 2026-10-29, PLAN Evals E1).** Choosing Reject or
     Edit on a card reveals one single-select chip row, from this fixed list
     and no other: `stale source`, `wrong fact`, `wrong field/initiative`,
     `missing context`, `wording`, `duplicate`. Reject also gets an optional
     one-line note field. Submit stays disabled until every rejected or
     edited card has a chip. It's one click, and it's what turns "why did it
     fail" into counts (E2 scorecard). Don't add chips ad hoc; a new reason
     is a PLAN change, because it breaks comparability across versions.
   - One submit button constructs a single message string —
     `approve <ids> / reject <id> [<chip>]: <note> / edit <id> [<chip>]: <text>`
     — and calls `sendPrompt()` with it. This is the message contract the
     calling skill's apply step parses. One `reject` segment per rejected diff
     (the `: <note>` is omitted when the note is empty), one `edit` segment per
     edited diff, all joined with ` / `.
   - **Fallback:** if `visualize:show_widget` errors (has happened before —
     infrastructure error), fall back to the plain markdown block below and
     tell the user the widget failed, so the user knows why the user is typing instead of
     clicking:

```
## PILOT DIFF PROPOSALS (Move 3)

**PILOT-1** [replace] [confidence: direct] [field: Risks]
Current: "..."
Proposed: "..."
Moves to LOG: "..."
Source: <≤15-word quote> — <channel/thread link or date>

**PriceMismatch-1** [confidence: inferred] [contradicts current] [field: Blocker]
...
```

3. Wait for the user's reply (either the widget's `sendPrompt` or a typed reply)
   before anything is applied — applying is the calling skill's job, not this
   skill's. Reply syntax, the same either way:
   `approve PILOT-1,3 / reject PILOT-2 [duplicate] / edit PILOT-4 [stale source]: <replacement text>`
   In a typed reply the chip is optional (it's logged as `none`), and several
   rejects can share one chip (`reject PILOT-2,5 [wording]`). The fallback block
   should list the six chips under the diffs so the user can copy one.
   Anything not explicitly mentioned stays **pending, not approved** — silence
   never means approve.

## Versioning

The `version:` in this file's frontmatter (`YYYY-MM-DD.N`) is stamped on every
`diff-sessions.md` row by `ingest` Step 4. Bump it in the same edit as any
change to how diffs are generated, scored, routed or presented, so the E2
scorecard can compare one version against the next. Typo and wording fixes to
this file don't need a bump.

## Validated against

Fixture set + expected outputs: `evals/fixtures.md`. Results log:
`evals/results.md`. 7/7 passed 2026-08-11, before wiring. Fixtures 8 (reword
only) and 9 (source discipline) added 2026-11-22; not run yet. Fixtures test the
diff-generation logic only, not the widget — the widget has been used live
since 2026-08-11 but has no automated eval of its own.

**Called by `ingest` (Step 2c)** for the pilot initiatives (named in `ORG.md`, row "`diff-propose` pilot initiative";
a second pilot was dropped 2026-10-29). `daily-slack-review` no longer calls this
directly — it hands off to `ingest`, which decides when a diff-propose call is
needed. Current sub-move status is tracked in exactly one place —
`1_PROJECTS/memory-system-upgrade/PLAN.md` (Move 3 section) — not restated
here. **Session count and outcome tallies** (how many times this skill has
actually run, and with what result) are tracked in exactly one other place —
`diff-sessions.md`, in this same folder, appended to by `ingest` Step 4 — not
restated here either.

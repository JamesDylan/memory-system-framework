---
name: calibrate
description: >
  Score the user's past decisions against what actually happened, and propose the
  doctrine updates that follow — the Thinking-layer "calibrate" operation, the
  missing half of the judgment loop (emerge finds patterns in events; calibrate
  finds patterns in the user's errors). Use this skill whenever the user says
  "calibrate", "score my decisions", "was I right about", "judgment retro",
  "review my past calls", "how's my calibration", or after a milestone lands
  ("Phase 2 is live — score the decisions that got us here"). Default window:
  the last quarter, or the decision-set behind a named milestone. First action:
  read memory_index.md, then this skill's corpus list. Core rules: judge the
  decision on the information available AT THE TIME, never on the outcome alone
  (no resulting); a decision with no recorded expectation is UNSCOREABLE, and
  every unscoreable is itself a finding; verdicts are proposed, the user rules.
---

# Calibrate — Skill

## Purpose

Close the judgment loop. The vault is excellent at **recording** decisions (ADRs
with rejected alternatives, CHANGELOG, D-numbers, planning tickets) and has machinery
for finding patterns in events (`emerge`) and stress-testing decisions before
they're made (`grilling`, `challenge`). Nothing revisits decisions **after**
reality has voted. This skill does: it walks past decisions, compares the
expectation at decision time with what happened, issues a verdict, and proposes
the doctrine update each verdict implies.

Why it exists: the user's judgment is being installed in systems that run
without them (skills, agents, delegates). The judgment being installed is the
asset; this skill is how the asset improves. A judgment error
found by calibrate once is a doctrine update; the same error found twice is a
calibration failure of this skill itself.

This is a **Thinking-layer** skill (Layer 2). It reads and synthesises; it does
not mutate canonical files. Confirmed verdicts and doctrine updates compound
back via `ingest`.

## Doctrine (non-negotiable)

1. **No resulting.** Judge the decision on the information available at the
   time, not the outcome. A good decision can lose; a bad decision can win.
   Every verdict must separate *process* (was the reasoning sound given what was
   known?) from *outcome* (what happened?). The four cells matter:
   good-process/good-outcome (keep), good-process/bad-outcome (bad luck — do NOT
   change doctrine reflexively), bad-process/good-outcome (**the dangerous one**
   — got away with it; still fix the process), bad-process/bad-outcome (fix).
2. **Unscoreable is a finding, not a skip.** A decision with no recorded
   expectation cannot be scored — and that's the flywheel: every unscoreable
   decision generates the prescription "next time, one line: *I expect X by Y*."
   Report the scoreable-rate every run; the goal is that it climbs.
3. **Hindsight quarantine.** Before reading the outcome, state what was known
   and expected at decision time (from the ADR/LOG entry itself, not memory).
   Only then read forward. If the decision record doesn't say what was expected,
   see rule 2 — do not reconstruct the expectation from the outcome.
4. **Too-early is honest.** If reality hasn't voted yet, verdict is OPEN with a
   named revisit date. Don't force a score.
5. **Every verdict proposes its consequence.** FAILED → which rule/doctrine
   changes, where it lives. HELD → does any hedge/caveat get retired? A verdict
   with no consequence is trivia.
6. **The user rules on every verdict.** Verdicts are proposals. Doctrine updates
   are filed via `ingest` only after the user confirms — same as `emerge`.
7. **Calibration over accuracy.** The interesting question is not "how often
   right" but "in which *direction* wrong" — over-optimistic on timelines?
   over-trusting of recorded fixes? too quick to add rules? Name the bias, not
   just the score.

## Step 0 — Read first

1. `memory_index.md` — the router.
2. The user's own inquiry notes in their private vault, if they keep any.
3. `CHANGELOG.md` for the window — the decision spine.

## Step 1 — Set the window and assemble the decision corpus

Default: **last quarter**, or the decision-set behind a named milestone if the user
gives one. The corpus, via QMD / `multi_get`:

- **ADRs** — any project `docs/adr/`.
- **CHANGELOG.md** entries that record a decision (not routine filing).
- **Initiative decisions** — `STATE.md` D-numbers, `LOG.md` dated calls,
  `Artefacts/05 Decision & Open Questions Log.md` style files.
- **Closed planning tickets** (`~/vaults/prd-repo/tickets/`).
- **Goal notes** in the user's private goals file — targets are predictions.
- **Evidence cards** in the user's private vault — decisions already deemed
  review-worthy.

Filter to *decisions* — a chosen path with a rejected alternative. Status
updates and filings are not decisions.

## Step 2 — Score each decision

For each, in this order (hindsight quarantine):

1. **Reconstruct decision-time state:** what was chosen, what was rejected, what
   was expected, by when. From the record only.
2. **If no expectation recorded → UNSCOREABLE.** Log it; prescribe the missing
   prediction line; move on.
3. **Read forward:** what does the vault/repo/reality say happened?
4. **Verdict:**
   - **HELD** — expectation met; reasoning stands.
   - **FAILED** — expectation not met. Sub-classify: *process* (the reasoning
     was faulty given what was known) or *luck* (sound reasoning, world moved).
   - **SURVIVED** — outcome fine but reasoning was faulty (got away with it).
     Treat as seriously as FAILED.
   - **OPEN** — too early; set revisit date.
   - **UNSCOREABLE** — no recorded expectation.
5. **Consequence:** the doctrine update, rule retirement, or new stop-and-ask
   boundary the verdict implies — and its canonical home.

## Step 3 — Produce the calibration report

```
# Calibration Report — [window]

## Scoreboard
Decisions found: N · Scoreable: N (x%) · HELD / FAILED / SURVIVED / OPEN / UNSCOREABLE

## Verdicts
### [Decision, date, source]
- Expected: [from the record] · Happened: [evidence]
- Verdict: [HELD/FAILED(process|luck)/SURVIVED/OPEN(date)]
- Consequence: [doctrine update + home, or "none — keep"]

## Calibration read (the direction of error)
[Named bias(es) across the window, with the verdicts that evidence them.
 e.g. "Recorded-as-fixed is trusted without verification — 3 instances."]

## Unscoreables → prediction debt
[Each one + the one-line prediction that would have made it scoreable.]

## Scoreable-rate trend
[This run vs. previous runs — is prediction discipline improving?]
```

End with **one sentence on the biggest single doctrine change the window
supports** — the update that would have prevented the most damage.

## Step 4 — Compound back (offer, don't force)

For each verdict the user confirms: file the consequence via `ingest` — an ADR
amendment, a skill-file edit, a `learning_insights.md` entry, a new stop-and-ask
line. A confirmed SURVIVED or FAILED(process) with no filed consequence is the
skill failing at its own purpose. Log the run (date, scoreboard, named biases)
in this folder's `runs.md` so the next run can compare.

## Scenarios — how and when to use it

**A. The quarterly pass (default).** End of quarter / cycle rollover: "calibrate
last quarter." Full corpus sweep. Pairs naturally with cycle planning — doctrine
updates land before the next cycle's decisions are made.

**B. The milestone autopsy.** A milestone lands (e.g. {{PILOT}} Phase 2 go-live): "Phase 2 is live — calibrate the
decisions that got us here." Corpus is that initiative's D-numbers/ADRs only.
Runs while memory is fresh and feeds the retro (retro artefacts get
their "what I'd decide differently" section from here, evidenced).

**C. The single-decision check.** "Was I right about the heat-pump port?" One decision,
scored properly — decision-time state first, then outcome, then verdict. Guards
against the user resulting on themself after a visible win or loss.

**D. The pre-decision base-rate pull.** Before a new decision of a familiar
shape: "calibrate my track record on timeline estimates / on trusting vendor
claims." Not a scoring run — a retrieval of past verdicts of that class, so the
new decision starts from the user's actual base rate, not their self-image.

**E. The delegate audit (advanced, once runs.md has history).** The legend is
installing judgment in systems (skills, PMs, agents). Periodically score the
*delegates'* calls the same way — did `ingest` route correctly, did a PM's
independent decision hold, did an agent's autonomous action survive review?
Divergence between the user's calibration and a delegate's shows exactly where the
captured judgment is thinnest.

## Improving this skill over time

- **It measures itself.** Two health metrics, reported every run: scoreable-rate
  (is prediction discipline spreading through ADRs/LOGs?) and repeat-error rate
  (a bias named in a previous run that recurs = the filed doctrine update didn't
  take — investigate why, don't just re-file).
- **The verdict taxonomy is amendable.** If a decision doesn't fit
  HELD/FAILED/SURVIVED/OPEN/UNSCOREABLE, that's a candidate new verdict — amend
  this file via `ingest`, don't force the fit.
- **Grow eval fixtures like `diff-propose` did.** Once a few runs exist, keep
  2–3 known decision records + agreed verdicts in `evals/` here; a future run
  that scores them differently has drifted.
- **Tighten the corpus list as the vault evolves.** New decision homes (new
  initiative logs, new project ADR folders) get added to Step 1; that list going
  stale is a `lint` finding.
- **Watch the failure mode this vault already knows:** a deployed/registered
  copy of this skill diverging from this vault copy (CHANGELOG 2026-08-11/12/17
  — the skill-drift family). This file is the source of truth.

## Pushback rules (calibrated to the user)

- **If the user is resulting** — declaring a decision good/bad from the outcome
  alone — name the quadrant and re-score on process. Especially after wins.
- **If a FAILED(luck) tempts a new rule:** push back. Adding doctrine after bad
  luck is how constitutions bloat. Rule changes need a *process* fault.
- **If the same bias appears a third time** (per emerge's three-evidence rule):
  stop proposing the same doctrine edit and escalate — the question becomes
  "why doesn't the fix stick?", which is usually structural, not textual.
- **If the user wants comfort, not calibration:** say so. A run with zero FAILED /
  SURVIVED verdicts and a low scoreable-rate is not a clean bill of health — it
  means the records aren't falsifiable yet.

## What this skill does NOT do

- Does not judge decisions made without the information to do better — no
  hindsight penalties.
- Does not edit canonical files or ADRs itself — verdict consequences route via
  `ingest` after the user confirms.
- Does not score in-flight decisions (that's `grilling`/`challenge`, pre-hoc).
- Does not replace initiative retros — it feeds them the evidenced "would I
  decide it the same way" section.

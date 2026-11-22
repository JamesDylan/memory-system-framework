---
name: lint
description: Health-check the user's memory system (the Karpathy LLM-wiki "lint" operation), split into a deterministic script pass and an agent judgment pass. Use this skill when the user says "lint the wiki", "lint the memory system", "health check the system", "find gaps", "what's stale", "audit the memory system", "weekly vault review", or "what needs cleaning up". Also run as the weekly review step. The mechanical checks (dead pointers, staleness, missing stamps, unverified content, orphan skills, inbox age, index drift, deployed-skill drift, STATE field budgets) run as a zero-token script — `node .scripts/lint.mjs`; the agent only does the judgment half (single-source-of-truth conflicts, semantic staleness, missing structure, what to investigate next). It proposes fixes; it never auto-applies or deletes without explicit confirmation.
---
# Lint — Skill

## Purpose

Keep the wiki healthy as it grows. Reading and thinking aren't the maintenance
burden — bookkeeping is (cross-references, staleness, consistency). This skill
does the bookkeeping audit and surfaces what needs attention. It proposes; the user
disposes.

## The two-phase model (procedural / judgment split)

Inspired by the `obsidian-mind` split: **deterministic work belongs in a script,
judgment belongs in the agent.** This exists because the old all-agent lint
burned enough tokens that the user avoided running it. Now:

- **Phase 1 — mechanical (zero agent tokens).** `node .scripts/lint.mjs` does
  every check a machine can do: dead pointers, staleness vs. rhythm thresholds,
  missing stamps, unverified content, orphan skills, inbox age, index↔changelog
  drift, deployed-skill drift, STATE field budgets. Run it as often as you like (manually or on a
  schedule) — it costs nothing.
- **Phase 2 — judgment (agent, only when asked).** The agent does *only* what
  needs interpretation: single-source-of-truth conflicts, semantic staleness
  (dates fresh but content wrong), missing structure, and the 2–3 questions
  worth investigating next. It reads the Phase 1 report first so it never
  re-does mechanical work.

## When to run

- **Phase 1 script:** weekly minimum; ideally scheduled (cron/launchd). Also
  after any big ingest or structural move (moves create dead pointers — the
  `_H2 Roadmap` relocation is the canonical example). Cheap enough to run daily.
- **Phase 2 judgment:** weekly (the "Weekly Vault" review: set focus, find gaps,
  plan the week), or whenever the Phase 1 report flags something that needs a
  human/agent call.

---

## Phase 1 — Run the script

```bash
node .scripts/lint.mjs            # markdown report to stdout
node .scripts/lint.mjs --json     # machine-readable (for scheduling/automation)
node .scripts/lint.mjs --strict   # exit 1 if any 🔴 — use in cron to trigger an alert
```

Policy lives in two files (staleness rhythms/thresholds, verification
thresholds, which operational files and path patterns are under the freshness
check, scanned directories and recognised extensions for dead pointers, inbox
age, skill-registration exemptions, deployed-skill mirrors, run-integrity jobs).
`.scripts/lint.config.json` is the engine's: defaults, and a `_comment` on each
knob saying what it means. `lint.config.org.json` (next to it in `.scripts/`) is this vault's own,
and lint merges it over the engine file: objects merge key by key, and an array
or value there replaces the engine's (to extend an engine list, copy it there and
add to it). Put every vault-specific setting in the org file (pilot STATEs in
`stateBudgets.strictFiles`, your own operational files, refresh contracts,
excluded sources, deployed skills, scheduled jobs); change the engine file only
for a default every vault should get. Never hard-code policy in the script. A
malformed org file stops lint with an error.

**What the script checks (do NOT re-do these by hand):**

1. **Dead pointers** — every vault path referenced in `memory_index.md`, the
   skill files, and every .md under `deadPointerDirs` (`1_PROJECTS`, `2_AREAS`)
   resolves to a real file/dir. Recognised extensions come from
   `pointerExtensions`. (Resolves bare-filename shorthand by basename, partial
   paths by suffix; skips external/system paths.)
2. **Staleness** — each operational file is within its rhythm's freshness window
   (weekly 10d / biweekly 21d / monthly 40d / quarterly 100d). The file set is
   `operationalFiles` **plus** anything matching `operationalGlobs` — project
   `STATE.md` files are covered by pattern, so a new initiative folder is in scope
   the day it is created rather than the day someone remembers to register it.
   A file whose frontmatter has `health: paused` (or `on_hold`) is skipped and
   only counted: a paused initiative is not expected to change.
3. **Missing stamps** — operational files with no `Last Updated` / `Last touched`
   / `Last verified accurate` date, or a `Last verified accurate` label carrying
   no parseable date.
4. **Unverified content** — fresh by edit, stale by confirmation. See the section
   below; this one has a specific correct response and a specific wrong one.
5. **Orphan skills** — a `SKILL.md` on disk not registered in `memory_index.md`.
6. **Inbox age** — `_private/0_INBOX/` items older than 14 days (by filename date or mtime).
7. **Index drift** — `memory_index.md` "Last Updated" lagging the newest
   `CHANGELOG.md` entry.
8. **Deployed-skill drift** — each configured deployed skill copy still matches
   its vault source. See the section below. (This list numbers *findings*; the
   script's own internal check numbering differs — this one is Check 6 in
   `lint.mjs`.)
9. **STATE field budgets** (`state-budget`, Check 8 in `lint.mjs`, added
   2026-10-29) — bullets per field, words per bullet, nested bullets and an
   appended `Last touched`, against the budgets in `diff-propose/SKILL.md`.
   🔴 for diff-propose pilot files (`stateBudgets.strictFiles`), 🟡 for other `1_PROJECTS/{{ORG}}/*/STATE.md`.
   Policy is `stateBudgets` in the lint config; pilot `strictFiles` go in the org file.
10. **Refresh contracts** (`source-newer`, `contract-overdue`, `contract`; in
   Check 2, added 2026-11-20, Move 11f). `refreshContracts` in `lint.config.org.json`
   gives each slow file its source, how often the source publishes
   (`sourceEveryDays`) and who confirms the file. `source-newer`: the first date
   on the `Source as of` line is older than `sourceEveryDays` + `sourceGraceDays`,
   so a newer edition is due (lint cannot see the source; read it to check).
   `contract-overdue`: `Last verified accurate` is "not yet" or older than the
   file's verification window. The finding names the confirmer. A contracted file
   gets these findings in place of the plain staleness and `unverified` ones.
11. **Not filled in yet** (`not-filled`, Check 13, added 2026-11-22, F1.3). A
   new vault's to-do list, in its own report section ("📝 Not filled in yet — do
   these first") and JSON key (`findings.todo`): never must-fix or should-fix, so
   CI and `health.mjs` ignore it. It lists blank or `(set X)` fields in the
   `| Key | Value |` tables of `ORG.md` and `_private/ME.md`, a cycle file with no
   cycle name or dates, every file with the stub marker line (`> Not filled in yet.`),
   and template text (`[name]`, `TBD`, `<your name>`) left in operational files.
   A file with the marker gets no staleness findings until the line is deleted.
   Policy is `notFilled` in `lint.config.json`.
12. **Engine drift** (`engine-drift`, Check 14, added 2026-11-22, F1.6). Should-fix
   for each engine file whose sha256 differs from engine.lock ("edit this upstream,
   or move it to the org layer"), each lock-listed file that is missing, and each
   `<file>.upstream` left by `engine-upgrade.py` (an unresolved upgrade conflict).
   No lock (the engine repo itself, or a vault set up before F1.6): one green line.

### The `unverified` finding (added 2026-08-10)

Fires when a file is **fresh by edit but stale by confirmation** — `Last touched`
inside its rhythm threshold, `Last verified accurate` outside the looser
`verificationThresholdsDays` (weekly 14d / biweekly 28d / monthly 45d /
quarterly 110d).

The two stamps mean different things:

| Stamp | Means | Checked against |
|---|---|---|
| `Last touched` / `Last Updated` | Someone edited it | `stalenessThresholdsDays` |
| `Last verified accurate` | Someone confirmed the content is still true | `verificationThresholdsDays` |

**The bug this replaced.** Until 2026-08-10 the script took the latest date on any
line matching *either* label. Both labels routinely share one line
(`**Last touched:** X | **Last verified accurate:** Y`), so the fresher date won
and the file reported clean. A file could be edited daily and go unverified for
months while lint called it healthy every week — worse than no check, because it
emitted a green light with the same shape as a real one. **Treat any pre-2026-08-10
green staleness result on a dual-stamped file as unverified.**

### Stamp schema for shared context (Move 11c, 2026-11-20)

Every file in `requireVerified` (`2_AREAS/{{ORG}}/context/`, `2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/`) starts with this block, under the H1:

```
**Last Updated:** YYYY-MM-DD
**Last verified accurate:** YYYY-MM-DD | not yet (<what is not checked>)
**Source as of:** <source and its date>
**Owner:** <team or role that maintains it>. Source owner: <who owns the facts>
**Review Cycle:** <rhythm>
```

- **Owner** is a team or role, never one PM's name, so a new PM knows who to ask.
- **Source as of** is the date of the newest source behind the content, not the edit date. Put that date first on the line (YYYY-MM-DD, "20 May 2026" or "June 2026"): refresh contracts read the first date.
- **Not yet** counts as unverified. A file in `requireVerified` with no `Last verified accurate` label is reported as `missing-stamp`.
- `registry.yaml` has no prose stamps. Lint uses its newest `as_of` as both dates, checked on the weekly rhythm.

**Responding to an `unverified` finding — two valid responses, and only two:**
re-read the file and move the stamp, or state plainly *in the file* what was not
checked. Moving the stamp because the file was edited is precisely the overclaim
this check exists to detect.

### Deployed-skill drift (Check 6 in `lint.mjs`, added 2026-08-10)

Diffs each configured deployed skill copy against its vault source.

**Why it exists.** The vault lints itself; nothing checked the copies that
actually run. Three incidents established the gap before it was closed: the 6 Aug
unattended run executing a drifted prompt rather than the named skill; the 7 Aug
finding that nothing checks a scheduled job runs the skill it is named after; and
the 10 Aug discovery that the deployed `daily-slack-review` differed from its
vault source on three points — stale channel-list path, retired pre-flight call,
missing Output-contract section.

**Behaviour when unconfigured is deliberate.** With `deployedSkillMirrors` empty,
the check reports **its own absence** as an amber finding rather than passing
silently. An integrity check that goes quiet when unconfigured is
indistinguishable from one that is working — which is how this gap survived three
incidents.

**The prerequisite is a decision, not a config entry.** Before populating the
mirrors, settle whether the vault is authoritative for deployed skills (sync from
it, and a diff is a 🔴) or documentation only (drop the check and stop treating
vault edits as behaviour changes). It is currently treated as the former while
behaving as the latter. Tracked in a private action.

If Phase 1 is all the user needs (just wanted the mechanical report), stop here.

## Phase 2 — Agent judgment pass (only what the script can't do)

Read the Phase 1 report first, then read `memory_index.md` (SoT table) and
`CHANGELOG.md` (last ~30 days). Then check only these:

### A. Single-source-of-truth violations (the highest-value judgment check)
Spot-check the known drift-prone facts (the Failure 3 family): PM↔initiative
mapping, each PM's product area, leave/availability status, initiative health.
If the same fact appears in two files with **different values**, flag it and name
which is canonical per the index. (A script can't tell that two prose statements
disagree — this is why it's here.)

#### 🔴 Hard rule: lint flags conflicts. Lint never resolves them by overwrite. (added 2026-08-14)

When two files carry different values for the same fact, the response is to mark
**both** as disputed and escalate to the user. It is **not** to pick the one that
looks right and overwrite the other.

**The incident this exists to prevent.** On 20 Jul a judgment pass found churn at
19.2% in `_ACTIVE_CYCLE.md` and 3.2% in `metrics_dashboard.md`, called the latter
"an order of magnitude off", and replaced the value — keeping the existing
**monthly** label. On 14 Aug the user confirmed 19.2% is an **annual** figure. The two
numbers had never disagreed: 3.2% monthly compounds to roughly 32% annual. They
were measuring different periods, and the pass resolved a unit mismatch by
deleting one side of the evidence that a mismatch existed.

It then survived four weeks and propagated into the Critical alerts,
`strategic_context.md` twice, and a CHANGELOG entry that repeated the
"order-of-magnitude" framing as established fact. **A visible conflict invites
checking; a single confident number invites none.** Overwriting made the vault
look healthier and be less correct.

**Correct handling of a value conflict:**
1. Leave both values in place. Add a `⚠️ DISPUTED` note to each, naming the other
   file and the specific discrepancy.
2. State what would settle it and who can settle it.
3. Escalate to the user. Do not choose.
4. Only after the user rules does one value become canonical and the other a pointer.

**Before assuming a bad value, check the unit.** Two figures for the same metric
differing by roughly **10–30x** are far more likely a period mismatch
(monthly vs annual) than an error — that ratio *is* monthly-to-annual
compounding. Same for 1000x (absolute vs thousands) and ~100x (rate vs
percentage). Check period, denominator and unit before concluding anything is
wrong.

**This rule binds the agent, not just the script.** The 20 Jul overwrite was a
judgment-pass action, which is exactly why it isn't a `lint.mjs` change.

### B. Semantic staleness
For files the script reports as *fresh by date*, sanity-check whether the content
is actually still true (e.g. a metric that's been superseded, an initiative whose
status changed but the stamp was bumped without a real review). The script sees
dates; you see meaning.

The `unverified` finding is the script's partial handle on this — it detects
edited-without-reconfirming, but only where a `Last verified accurate` stamp
exists. Files carrying only `Last Updated` remain fully your problem. When you do
confirm a file end-to-end, say so explicitly so the stamp can move honestly; when
you only checked part of it, say which part.

### C. Missing / wrong structure
- Candidate hygiene (`CANDIDATES.md`): `exploring` with no movement in 30 days →
  decide or park; `parked`/`killed` with no reason → add it; `committed` that
  hasn't graduated to a `1_PROJECTS/{{ORG}}/[Name]/` folder → graduate or correct.
- Initiatives in the `_ACTIVE_CYCLE.md` health table with no project folder /
  missing BRIEF/STATE/LOG.
- Project folders not referenced anywhere.
- **Performance-evidence graph SoT purity:** an evidence card (`type: evidence`)
  whose body restates a metric/outcome instead of just pointing via `source:` →
  flag (the number must live once, in its canonical home). A competency note that
  has accreted per-person judgment or OKR status (belongs in `Direct Reports.md` /
  `career_development.md`) → flag.

### C2. user-owned commitments, and stale dates inside fresh files (added 2026-08-14)

Two checks the mechanical pass structurally cannot do, because in both cases the
file is *inside* its freshness window while the content is wrong.

**Overdue or flagged user-owned actions.** Scan `1_PROJECTS/Actions/` and `_private/1_PROJECTS/Actions/` for
`owner:` equal to the Name in `_private/ME.md` and `status: open`, with either a `due` date in the past or
a `flag_from` date reached. **Raise these unprompted — do not wait to be asked.**
Where an action carries its own escalation ladder, follow what the file says rather
than improvising a tone.

Why this sits in the judgment pass: roughly five of every six action files are
user-owned, and nothing currently surfaces when their own commitments age out. The
vault will report a file stale in 14 days and say nothing about a `now`-priority
action that has not moved in five weeks. Precedent: `Actions/pilot-decision-framework.md` has
been `now` since 8 Jul with no movement and has never been flagged by anything.

**Stale target dates inside freshly-edited files.** When an initiative, owner or
scope changes, every date that referenced the old version becomes suspect — and
invisible, because the file's own stamp keeps moving.

**The incident:** a goals file carried a key result due 30 Jun, a date set when the
owned initiative was a different one. The initiative changed on 3 Jul; the date did
not move with it. On 14 Aug it was reported as "45 days overdue" and pressed three
times before the user corrected it. The file had been edited repeatedly and was never
flagged once, because **it was never stale by any measure the vault has.**

So: when a Phase 2 pass sees an initiative, owner or scope change inside the last
~60 days, re-check every date that referenced the previous state. And before
calling anything overdue, **trace the date to its source** — a STATE milestone, a
decision ID, a deck — rather than trusting the field. A precise date is not an
authoritative one.

### C3. Repeated reason chips (added 2026-11-15, PLAN Move 9 R2)
Since 2026-11-22 (PLAN S2.3), `lint.mjs` Check 12 (`rejection-loop`) counts the
chips in `diff-sessions.md` and reports a should-fix finding with the chip and
the sessions. In this pass, write the one rule change for each such finding.
Also read any stage or seat feedback.md that exists (the script does not). For
`diff-sessions.md` (Reasons and Versions columns): if one reason chip
occurs 3 or more times in the last 10 sessions of one skill version, propose
**one** change to that skill's or stage's rules. Name the chip, the sessions and
the rule to change. The user approves it like any other fix. Never edit the
skill yourself in this pass. Fewer than 10 versioned sessions: count what
exists and say the sample is small.

### D. What to think about next
End with **2–3 suggested questions or sources worth investigating** — lint is
also a prompt for what to think about next, not only what to clean.

## Phase 2 report format

```
# Lint — Judgment Pass — [date]
(mechanical findings: see `node .scripts/lint.mjs`)

## 🔴 SoT violations / trust-breakers
- [finding] → canonical is [file]; proposed fix

## 🔴 user-owned commitments overdue or flagged
- [action file] — [due / flag_from date] — [what the file's escalation ladder says]

## 🟡 Semantic staleness / structure
- [finding] → proposed fix

## 🟡 Repeated reason chips
- [chip] ×[n] in [skill@version] sessions [dates] → proposed rule change

## 🟢 Questions worth investigating next
- [2–3 prompts]
```

## Step — Apply only what the user approves

- Propose fixes; apply only the ones the user greenlights, one file at a time, verify
  each (re-read after write).
- **Never delete** a file without explicit confirmation — surface deletion
  candidates, let the user decide.
- **Never resolve a value conflict by overwrite** — see the hard rule under
  Phase 2A. Conflicting numbers get marked disputed and escalated, never
  silently reconciled.
- Log applied fixes to `CHANGELOG.md` under today's date.
- If the lint touched the upgrade itself, update its `STATE.md`.

## Changing `lint.mjs` — verify against a fixture first (added 2026-08-10)

Any change to the script is tested against a throwaway fixture reproducing the
failure **before** it is written to the vault. This is not ceremony. On 10 Aug the
first patched build caught the dead pointer but **silently passed** the unverified
case — both regexes matched the shared stamp line and each claimed both dates.
Reading the diff would not have found it. An unverified lint fix produces a check
that looks correct, reports green, and does not work: the same failure class as
the bug being fixed.

Minimum fixture: a file with both stamps on one line, one of them lagging; a
dangling non-.md pointer; one healthy control file.

## Doctrine alignment

- This is the "Lint" operation from the Karpathy LLM-wiki pattern (Ingest →
  Query → Lint), now with the `obsidian-mind` procedural/judgment split.
- It automates the *mechanical* maintenance layer (Doctrine 5) in a script and
  reserves the agent for judgment — the split is what makes frequent linting
  affordable.
- It enforces single source of truth (Doctrine 1) and visible staleness
  (Doctrine 4) by detecting violations of both.

## What this skill does NOT do

- Does not auto-apply fixes or delete files.
- The script does not make judgment calls (SoT conflicts, semantic staleness) —
  that's deliberately the agent's job.
- Does not add heavier tooling (QMD/Graphify) beyond the lint script. At the
  scale where even the judgment pass gets slow, that's the Move 6 trigger — note
  it, don't pre-empt it.

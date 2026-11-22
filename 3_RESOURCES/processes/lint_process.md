# Memory System Lint — Process

## Purpose
Keep the memory system healthy as it grows without burning agent tokens on mechanical checks. Two-phase model: a zero-token script catches everything a machine can catch; the agent is reserved for judgment calls a script can't make (SoT conflicts, semantic staleness, what to think about next).

This doc is the *operational* reference — when to run it, what the automation already does, where output lands. The skill itself (`3_RESOURCES/AI Skills/lint/SKILL.md`) is the canonical definition of what each check does and how the agent should reason about Phase 2. Don't duplicate check logic here — if the two ever disagree, the SKILL.md wins and this doc is wrong.

## The Two Phases

| Phase | Who | Cost | What it catches |
|---|---|---|---|
| 1 — Mechanical | `.scripts/lint.mjs` | Zero agent tokens | Dead pointers, staleness vs. rhythm thresholds, missing stamps, unverified content, orphan skills, inbox age, index↔changelog drift, deployed-skill drift |
| 2 — Judgment | Agent (Claude), on request | Agent tokens | Single-source-of-truth conflicts, semantic staleness (dates fresh but content wrong), missing/wrong structure, 2–3 questions worth investigating next |

Phase 1 runs automatically every Monday 08:00 via launchd — see Automation below. Phase 2 only runs when the owner (`_private/ME.md`) explicitly asks Claude to lint / review / do the weekly vault check.

## Running Phase 1 Manually

```bash
cd <your-path>/memory_system
node .scripts/lint.mjs            # markdown report to stdout
node .scripts/lint.mjs --json     # machine-readable
node .scripts/lint.mjs --strict   # exit 1 if any 🔴 finding (used by the cron wrapper)
```

Policy (staleness and verification thresholds, which files and path patterns are checked, scanned dirs and recognised extensions for dead pointers, inbox age, skill exemptions, deployed-skill mirrors) lives in `.scripts/lint.config.json` — edit that, never hard-code policy into the script. The config carries `_comment` fields recording why each knob exists; extend them rather than replacing them.

## Coverage — what Phase 1 actually scans (revised 2026-08-10)

Three blind spots were closed on 10 Aug. All three were **configuration scope, not script failure** — the checks ran correctly against a set that excluded the files that mattered.

| Check | Before | Now |
|---|---|---|
| Dead pointers — sources | `memory_index.md` + SKILL.md files only | plus every `.md` under `deadPointerDirs` (`1_PROJECTS`, `2_AREAS`) |
| Dead pointers — extensions | hardcoded `md,json,sh,mjs,base,canvas,ps1` | `pointerExtensions` in config; `html`, `csv` added |
| Staleness — file set | hand-listed `operationalFiles` (10 context files) | plus `operationalGlobs` — `1_PROJECTS/{{ORG}}/*/STATE.md` weekly, `1_PROJECTS/*/STATE.md` biweekly |
| Stamps | one collapsed value | `touched` and `verified` parsed separately, per-label |
| Deployed skills | not checked | Check 6 in `lint.mjs` |

**The case that prompted this.** A dangling `Artefacts/2026-07-31_phase2-scope-open-items.html` reference sat in the pilot initiative's `STATE.md` for 10 days. **Two independent gaps had to line up for it to survive**: `STATE.md` was not a scanned source, *and* `.html` was not a recognised extension. Either one alone would have caught it. This is why it read as a discipline failure and was not one.

**Why globs, not a longer list.** `operationalFiles` was hand-maintained, so a new initiative folder went unchecked until someone remembered to register it — the same failure mode the check exists to detect, one level up. Patterns mean a new `STATE.md` is in scope the day it is created.

**Changing the script.** Any edit to `lint.mjs` is verified against a fixture reproducing the failure before it is written to the vault — see the SKILL.md section of the same name for why this is a requirement rather than a nicety.

## Running Phase 2 (Judgment Pass) with Claude

Ask Claude to "lint the memory system," "run the weekly vault review," or "what's stale" — this auto-triggers the `lint` skill (see `memory_index.md` query-patterns table). Claude will:
1. Read the latest `.scripts/lint-report.md` (Phase 1 output) first — never re-derives mechanical findings.
2. Read `memory_index.md` (SoT table) and recent `CHANGELOG.md` entries.
3. Check only what the script can't: SoT violations, semantic staleness, structural gaps, evidence-card purity.
4. Propose fixes. Nothing gets applied without explicit sign-off, one file at a time.
5. Log any approved fixes to `CHANGELOG.md` under today's date.

## Reviewing Output

- **Phase 1 report:** `.scripts/lint-report.md` — overwritten on every daily pull. 🔴 = must fix, 🟡 = should fix, 🟢 = healthy.
- **Phase 2 report:** produced inline in the Claude conversation, in the format specified in the `lint` SKILL.md (`# Lint — Judgment Pass — [date]`). Not auto-saved anywhere — if a finding is worth keeping, it should graduate into `CHANGELOG.md` (if it's a fix) or the relevant canonical file (if it's a structural correction), not live only in chat history.
- **macOS notification:** the daily automated run shows a `Memory lint` notification only if there is a 🔴. Treat a red notification as a same-day action item, not a someday-item — it means a pointer is dead or a canonical file is missing, which degrades every subsequent Claude session until fixed.

## Automation (already running — don't rebuild)

- **Runner:** `.scripts/daily-pull.sh`. After a successful pull it runs `lint.mjs --strict`, writes the report, and shows a notification only when there are must-fix findings.
- **Scheduler:** one launchd job, `com.{{ORG_LOWER}}.memory-pull`, 08:30 daily and at login. Install with `.scripts/daily-pull.sh --install`.
- **Log:** `~/Library/Logs/memory-pull.log`.

To check the automation is installed and running:
```bash
launchctl list | grep memory-pull
```
If that returns nothing, run `.scripts/daily-pull.sh --install`.

## Cadence

- **Phase 1:** daily (automated, with the pull), also after any big ingest or structural move — moves create dead pointers.
- **Phase 2:** weekly, as part of the broader vault review, or whenever Phase 1 flags something needing a judgment call.

## Escalation

A 🔴 in Phase 1 means something load-bearing is broken (dead pointer in the index, a missing operational file, a deployed skill that has diverged from its vault source) — fix same-day, don't let it compound into a session where Claude is reasoning from a broken map. 🟡 findings can queue for the weekly Phase 2 pass.

**One 🟡 that should not be left to queue indefinitely: `unverified`.** It means a file is being actively edited while nobody has confirmed the rest of it is still true. Two valid responses — re-read and move the `Last verified accurate` stamp, or write into the file what was not checked. Bumping the stamp because the file was edited is the overclaim the check was built to detect, and it converts a working check back into the broken one it replaced.

**Trust note on historical reports.** Before 2026-08-10 the script collapsed `Last touched` and `Last verified accurate` into a single value, taking whichever was fresher. Any green staleness result from before that date, on a file carrying both stamps, should be treated as unverified rather than as evidence the file was fine.

---
Last Updated: 2026-08-10

---
name: ingest
version: 2026-11-23.1
description: >
  Process raw material from _private/0_INBOX into the user's memory system using the
  Karpathy LLM-wiki pattern: capture messy, promote deliberately, keep one
  source of truth per fact. Use this skill whenever the user says "ingest this",
  "process my inbox", "process the inbox", "file this", "add this to the
  system", "capture this", or drops a file/notes/feedback and asks where it
  goes. Also triggers when the user brings in new feature ideas, feedback on existing
  initiatives, or H2 roadmap input. Also invoked automatically at the end of
  `daily-slack-review`, same session, against that day's two inbox files.
  First action: read this skill's routing map and memory_index.md. Core rule:
  never auto-create a project folder for an uncommitted idea; route to the ONE
  canonical home; propose diffs before applying; for the two Move 3 pilot
  initiatives specifically, delegate STATE diffs to `diff-propose` rather than
  diffing ad hoc (Step 2c); log and clear the inbox file when done.
---

# Ingest — Skill

## Purpose

Turn raw inputs into clean, single-source-of-truth knowledge without the user
having to think about filing. This is Move 5 of the memory-system-upgrade
(Karpathy LLM-wiki ingest pipeline). The discipline is the product — no tool
replaces the routing judgment.

## Doctrine (non-negotiable — from the upgrade PLAN)

1. **Capture is separate from promotion.** Raw lands in `_private/0_INBOX/`. It only
   graduates after the insight is extracted and merged into a canonical file.
2. **Single source of truth.** Every fact has exactly one home. Route to one
   place. If the same fact would land in two files, one must be a pointer.
3. **Don't promote prematurely.** An uncommitted feature idea is NOT an
   initiative. It goes to the candidate backlog, never a new project folder.
4. **Visible staleness.** Stamp `Last verified accurate` / `Last touched` when
   you touch an operational file.
5. **Propose, don't overwrite.** Show the user the diffs. The user approves. Then apply.

---

## Step 0 — Read first

1. This skill (the routing map below).
2. `memory_index.md` — the single-source-of-truth table IS the master router.
3. If the input concerns an existing initiative, that initiative's `STATE.md`
   and `LOG.md` before proposing changes.
4. If the input looks like a **win, experiment result, decision, or notable
   coaching observation**, also read the **Performance-Evidence Graph** section
   of `memory_index.md` and the relevant competency notes — it may spawn an
   evidence card (Step 2b).
5. If the input concerns **a pilot initiative** (named in `ORG.md`, row "`diff-propose` pilot initiative") specifically — the Move 3
   pilot initiative — also read
   `3_RESOURCES/AI Skills/diff-propose/SKILL.md`. STATE diffs for it go
   through that skill, not the ad hoc diffing in Step 3 (see Step 2c).

## Step 1 — Read the raw input and give takeaways

Read the inbox file (or the thing the user pasted). Tell them, in 3–5 bullets, what
the material actually contains and what's worth keeping. Don't file silently —
the user should see your read before you route.

## Step 2 — Classify and route

For each distinct piece of signal, decide its type and route to the ONE home:

| If the signal is… | Route to | As |
|---|---|---|
| **New feature / initiative idea** (not committed) | `2_AREAS/{{ORG}}/_H2 Roadmap/CANDIDATES.md` | A candidate entry using the schema there. **Do NOT create a project folder.** |
| **Feedback / update on an EXISTING initiative** | That initiative's `LOG.md` (always, dated) + `STATE.md` (only if it changes health, current work, next decision, or a risk) | Dated LOG entry; targeted STATE field edits. **Exception: the pilot initiatives — don't diff STATE.md yourself, see Step 2c.** LOG.md entry still happens here as normal either way. |
| **Decision, constraint or open question** for an initiative that has a `[Name]/facts/` folder (today: Example Initiative C) | `1_PROJECTS/{{ORG}}/[Name]/facts/[type]-[slug].md` (PLAN S3.3) | New file from `templates/FACT.template.md`: `as_of` = the source's date, `source` = the original, `verified: not yet` (only the approver sets a date). A changed fact: propose a `status` change on the old file plus a new fact; never edit the old claim. Do not also write it into STATE. The LOG entry links the fact file |
| **Roadmap / prioritisation / sequencing input** | `2_AREAS/{{ORG}}/_H2 Roadmap/ROADMAP.md` | Update relevant tier (Now/Next/Later/Not-in-H2) or open-decisions |
| **Strategy / VOC / competitive** | `2_AREAS/{{ORG}}/context/strategic_context.md` | Targeted edit |
| **CY27 themes, objectives, KRs, KPIs** | `2_AREAS/{{ORG}}/context/cy27_objectives.md` | Targeted edit |
| **Metric / KPI value** | `2_AREAS/{{ORG}}/_metrics/registry.yaml` first (`METRICS_PROTOCOL.md`), then the row in `2_AREAS/{{ORG}}/context/metrics_dashboard.md` (KPI tables only) | Targeted edit |
| **Experiment result** (with or without a number) | New file in `2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/insights/` (`section: Experiment Results`), plus a row in the `learning_insights.md` index | New file |
| **Stakeholder role or ownership change** | The person's page in `2_AREAS/{{ORG}}/people/` (plus `stakeholder_map.md` if group or role changed). Notes on how to work with them go to `_private/2_AREAS/{{ORG}}/context/stakeholder_notes.md` | Targeted edit |
| **PM coaching observation / team** | `_private/2_AREAS/{{ORG}}/My Team/Direct Reports.md` (individual) or `team_development.md` (team-level) | Targeted edit |
| **Customer learning / segment behaviour / deck analysis** | New file in `2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/insights/` (`section: Customer Insights` or `Metric Analyses`), plus a row in the `learning_insights.md` index | New file |
| **Any open action/to-do** — initiative-linked or standalone, needs a reply/DRI/decision/ticket | `1_PROJECTS/Actions/` if `category` is an initiative; `_private/1_PROJECTS/Actions/` if personal or `category: "none"` (new `type: action` file per item) | New file using the schema in any existing action file; reflected automatically in that folder's `Actions.base`. Shared actions carry no coaching notes, personal OKR framing or judgements about how a person performs |
| **Company-level context** | `2_AREAS/{{ORG}}/context/company_context.md` | Targeted edit |
| **Doesn't fit / unclear** | Leave in `_private/0_INBOX/` | Flag to the user, ask one routing question |

**Metric numbers, in any file you write:** never write a bare number. Link to the metric, or put `<!--m:id-->` (its id in `2_AREAS/{{ORG}}/_metrics/registry.yaml`) after the number. See `METRICS_PROTOCOL.md`.

**Promotion of a candidate → project folder** happens only when the user says it's
committed to a cycle. At that point: create `1_PROJECTS/{{ORG}}/[Name]/` with
`BRIEF.md` + `STATE.md` + `LOG.md` (Move 2 schema), run
`python3 .scripts/make-initiative-hubs.py` (creates the `[Name]/[Name].md` hub
that action `category` links resolve to), remove the entry from
`CANDIDATES.md`, add to `ROADMAP.md` "Now", reflect in `_ACTIVE_CYCLE.md`.

**First run: a vault with no initiatives yet.** If `_ACTIVE_CYCLE.md` still
ends `> Not filled in yet.` and the only initiative folder is the example one
init created (the pilot named in `ORG.md`, its files ending in the same
marker), current-work signal has no home. Don't leave it in the inbox:
1. Ask whether the pasted material is the current cycle plan. If yes, propose
   `_ACTIVE_CYCLE.md` content from it (cycle name and dates, one Health row per
   initiative, priorities, risks) as a Step 3 diff.
2. Ask which listed initiatives are committed to this cycle. An initiative the
   user confirms is committed, so promote it as above (files from
   `templates/BRIEF.template.md`, `templates/STATE.template.md` and
   `templates/LOG.template.md`), with
   the user's OK on each folder. Anything not confirmed is a candidate and goes
   to `CANDIDATES.md`.
3. Leave the example initiative's folder alone. Once real initiatives exist,
   ask whether one should replace it as the pilot in `ORG.md`.

The fill order for a new vault is in `docs/first-week.md`.

## Step 2b — Emit an evidence card (performance-evidence graph)

After routing a signal to its canonical home, ask: **does this evidence a
competency?** If it's a genuinely review-worthy **win, experiment result,
decision held, defect caught, or notable coaching observation** that demonstrates
a competency — for the user (an OKR) or a PM (a shared competency) — also drop a thin
**evidence card**. This is what turns a future review into a query, and it means
The user never hand-writes a card.

**Only card review-worthy signal** — a metric moved, a scope decision held, a
narrative owned, a defect caught early, a goal advanced. NOT routine status
updates, FYIs, or noise: carding those is exactly the bloat trap the graph is
built to avoid.

**How (a pure pointer — never restate the fact):**

1. Confirm the competency note exists — `_private/2_AREAS/Career/Competencies/` (the user) or
   `_private/2_AREAS/{{ORG}}/My Team/Competencies/` (PMs). If none fits, **propose adding one
   to the shared library first** (the user's call); don't tag a target that doesn't
   exist.
2. Create the card:
   - The user → `_private/2_AREAS/Career/Evidence/[YYYY-MM-DD] [slug].md`
   - PM → `_private/2_AREAS/{{ORG}}/My Team/Evidence/[YYYY-MM-DD] [PM] [slug].md`
   - Frontmatter:
     ```yaml
     type: evidence
     person: "Full Name"
     competency:
       - "[[Competency Note]]"      # one or more; wikilinks (drives Base + Linked Mentions)
     nature: win | decision | learning | feedback
     date: YYYY-MM-DD
     kr: "OKR2 KR1 — ..."           # the user only; omit for PMs
     source: "[[canonical#anchor]]" # the fact's ONE home
     ```
   - Body: **one pointer line** ending "→ see source." Never restate the
     metric/outcome — it lives once, at `source:`.
3. The card is proposed as a diff in Step 3 like any other edit and logged in
   Step 4. Aggregation (`Competency_Evidence.base` + the competency note's Linked
   Mentions) is automatic once the card exists.

See the **Performance-Evidence Graph** section of `memory_index.md` for the model
and the two SoT rules.

## Step 2c — Pilot initiatives: delegate STATE diffs to `diff-propose`

**Scope:** the pilot initiatives named in `ORG.md` only. A second pilot was dropped as the
second pilot on 2026-10-29 (too little signal; its STATE goes back to the
ad hoc Step 2/3 flow). Every other initiative keeps using the ad hoc STATE
editing in Step 2/3 above — don't expand this scope without an explicit
decision to do so (that's a Move 3 rollout question, not something to drift
into one initiative at a time).

When routing identifies feedback/update signal touching this initiative that could
change a STATE field:

1. Read that initiative's current `STATE.md` if not already read in Step 0.
2. Call the `diff-propose` skill (`3_RESOURCES/AI Skills/diff-propose/SKILL.md`)
   with `signal` = the raw content for that initiative (from the inbox raw
   file if this run came from `daily-slack-review`, or the pasted/uploaded
   content otherwise) and `targets` = the current STATE.md content.
3. `diff-propose` presents its own interactive widget (or markdown fallback)
   directly — don't rebuild that presentation here, and don't fold its output
   into this skill's own Step 3 diff list. It's a separate, self-contained
   review exchange.
4. Wait for the user's reply before Step 4 applies anything for this
   initiative. Everything else routed in this same `ingest` run (actions,
   candidates, non-pilot STATE edits, evidence cards) can still be proposed
   and applied via the normal Step 3/4 flow in parallel — the pilot delegation
   doesn't block the rest of the inbox.

**Pushback:** if a STATE diff is about to be proposed ad hoc for a pilot
initiative, stop — that routes around the exact mechanism
the pilot exists to test. Use `diff-propose` instead.

## Step 3 — Propose diffs

For each target file, show the specific before/after edit. Group by file. Keep
edits tight — change fields, don't rewrite whole files. The user reviews and
approves or corrects.

**Source discipline (added 2026-11-22, PLAN S2.6).** The same rules as
`diff-propose` ("No reword-only diffs" and "Source discipline"):
- **No reword-only edits.** If an edit has the same facts as the current text
  and only the words are different, do not propose it.
- **Name the source.** A claim about a person, an owner, an approval or a
  decision names its source (who, where, date). If there is no source, write
  "unclear".
- **Show both when sources disagree.** Write both values, each with its source
  and date. Do not choose one without telling the user.

**This step covers everything except pilot-initiative STATE diffs** — those
were already presented via `diff-propose`'s own widget in Step 2c, not
restated here.

## Step 4 — Apply, log, clear

Once approved:
1. Apply the edits (`edit_file` for targeted changes, one file at a time).
   This includes decisions made via `diff-propose`'s widget/typed reply for
   the pilot initiative (Step 2c) — see the pilot-specific handling
   below, which differs slightly from the general case.
2. Stamp `Last touched` (and `Last verified accurate` only if the user confirms the
   file is now fully current).
3. Append one bullet per affected file to `CHANGELOG.md` under today's date,
   noting what changed and the source.
4. Clear the inbox file(s) by **moving them to the matching type folder under `4_ARCHIVE/sources/`. Never
   delete a source** (changed 2026-10-29). Raw sources are the evidence behind
   every canonical fact. Without them a claim can't be re-checked, which is
   what made the pilot's ground-truth audit depend on the user's memory alone.
   - Type folders: `_private/4_ARCHIVE/sources/slack/` (Slack briefs and raw signal),
     `4_ARCHIVE/sources/meetings/` (meeting notes, Gemini transcripts, 1:1s),
     `4_ARCHIVE/sources/docs/` (documents others wrote: PRDs, proposals, PCBs,
     goal docs), `4_ARCHIVE/sources/decks/` (slide decks and their text
     exports), `4_ARCHIVE/sources/data/` (analyses, metrics pulls,
     spreadsheets), `4_ARCHIVE/sources/notes/` (the user's own notes, memos and
     feedback the user captured), `_private/4_ARCHIVE/sources/other/`.
   - Rename to `YYYY-MM-DD_short-kebab-title.ext`, using the source's own date
     (meeting date, doc date), not the ingest date. Exception: keep
     `daily-slack-review` names unchanged (`YYYY-MM-DD_slack-review.md`,
     `YYYY-MM-DD_slack-review-raw.md`), because `lint.mjs` run-integrity finds them by
     that suffix.
   - Cite the source by its archived path in the LOG/CHANGELOG entry, so every
     promoted fact points back to its evidence.
   - If this run came from `daily-slack-review`, move both the brief and raw
     files together.
   - Only delete a raw file if the user explicitly asks (e.g. it contains a
     secret or something that shouldn't be kept). Confirm first.

**Pilot-initiative diffs from `diff-propose` (Step 2c) — apply per decision:**

- **`approve <id>`:** Apply `proposed_value` as a full replacement of that
  field in the initiative's STATE.md. This applies to both `replace` and
  `retire` ops. If the diff has a `log_entry`, append it to the initiative's
  `LOG.md` in the same pass, under a dated heading. Nothing a diff removes
  from STATE may be lost: it goes to LOG or it doesn't leave STATE. Replace
  `Last touched` with today's date (one date, at most one short clause; never
  append to it). Never bump `Last verified accurate`. One CHANGELOG bullet,
  same as any other edit.
- **Before applying, check the field budget** (`diff-propose/SKILL.md`, "STATE
  is a snapshot, not a history"). If an approved `proposed_value` still goes
  over its field's budget, or contains "Update (date)" sub-bullets,
  strikethrough or closed items, say so in the confirm line. Don't silently
  apply bloat.
- **`reject <id> [<chip>]: <note>`:** Don't touch STATE.md. Append one line to that
  initiative's `diff-log.md` (create alongside its STATE/BRIEF/LOG if it
  doesn't exist yet): date, confidence tier, field, the rejected value,
  "rejected — <chip>", and the user's note if the user gave one. No CHANGELOG entry —
  nothing canonical changed.
- **`edit <id> [<chip>]: <replacement text>`:** Apply the replacement text (not the
  original `proposed_value`) as the field value. Same stamping, `log_entry` and
  CHANGELOG treatment as approve; source noted as "user-edited from proposed diff."
- **Reason chips** are the fixed list in `diff-propose/SKILL.md` ("Presenting
  diffs for review"). A typed reply without one is logged as `none`; don't
  guess a chip on the user's behalf.
- **Unmentioned diffs:** no action, not carried over or re-shown next run — if
  still relevant, new signal will likely surface it again, or the user can raise
  it directly.

**Log the session, regardless of outcome.** Append one row to
`3_RESOURCES/AI Skills/diff-propose/diff-sessions.md` (date, initiative,
trigger, proposed/approved/edited/rejected/pending counts, one-line note,
plus the **Direct A/E/R** and **Inferred A/E/R** columns: the same outcomes split
by each diff's `confidence` tier, plus **Versions** (`diff-propose` / `ingest`
`version:` from each SKILL.md frontmatter, read at run time, e.g.
`2026-10-29.1 / 2026-10-29.1`) and **Reasons** (chip counts across edits and
rejects, e.g. `stale source ×2, duplicate ×1`; `—` if there were none)) and
update its "Running totals" and
"Confidence-tier totals" tables in the same edit. Log the tier for every
decided diff, not just rejections; without the approved/edited denominator,
confidence-tier validity can't be computed (gap found 2026-10-29). Do this even if every diff
was rejected, left pending, or `diffs` came back empty — a session with
nothing applied is still a session, and undercounting these is exactly the gap
found 2026-09-16 (the user had run diff-propose 4 times on the pilot; CHANGELOG/LOG.md
skimming alone suggested 2). This is the one place session count is
authoritative — don't let it silently stop being updated.

**Minutes per day, once a week.** If `diff-sessions.md` "Minutes per day" has
no row for the current week (Monday–Sunday), ask the user one line after the
confirm: "Roughly how many minutes a day on Slack review + STATE updates this
week?" Log their answer as a row there. If the user skips it, don't ask again until the
next session. This is the Move 3 go/no-go metric; nothing else records it.

**Version and session-log changes:** bump this file's `version:` in the same
edit as any change to Steps 2c, 3 or 4 (see `diff-propose/SKILL.md`,
"Versioning").

Confirm back in one line per pilot decision, e.g.: "Applied PILOT-1 to Risks.
Rejected PILOT-2 (logged). Applied PILOT-3 with your edit."

## Step 5 — Verify

Read back what you wrote to each canonical file. Confirm the edit landed
correctly and didn't clobber adjacent content. (The Q1 archive compaction
mistake came from skipping this.)

Then refresh search so the next agent finds today's edits: run
`qmd update && qmd embed` (default index, no `--index` flag). If qmd isn't
installed or the run fails, say so in one line; don't block on it. (Added
2026-10-29; see `3_RESOURCES/AI Skills/.agents/skills/qmd/SKILL.md`.)

---

## Pushback rules (calibrated to the user)

- **If the user wants a new idea turned straight into a project folder:** refuse.
  "That's premature promotion — it's a candidate until it's committed to a
  cycle. It goes in CANDIDATES.md. We promote it to a folder when you commit."
- **If the same fact wants to live in two files:** refuse the duplicate. Pick
  the canonical home, make the other a pointer.
- **If the user pastes a huge raw doc and says 'just save it in context/':** no. That
  is the Growth Loops mistake. It lands in `_private/0_INBOX/`, gets processed, and only
  the extracted insight graduates.
- **If the inbox has items >14 days old:** surface it. Don't process silently
  around stale items — name that processing has slipped.
- **If a routine update or FYI wants an evidence card:** refuse. Only
  review-worthy signal gets carded — the graph is for evidence, not activity.
- **If an evidence card would restate the metric:** refuse. The card body is a
  pointer; the number lives once, at `source:`.

## What this skill does NOT do

- Does not automate the user's judgment. Routing for genuinely ambiguous signal is
  a conversation, not a guess.
- Does not touch `BRIEF.md` from ingest (BRIEF is immutable after sign-off).
- Does not card routine updates, and never restates a fact inside an evidence
  card — cards are pointers to a review-worthy win, nothing more (Step 2b).
- Does not add tooling (QMD/Graphify). That's Move 6, deferred.

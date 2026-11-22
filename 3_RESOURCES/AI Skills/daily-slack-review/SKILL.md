---
name: daily-slack-review
version: 2026-11-13.1
description: >
  Run the user's daily {{PRODUCT}} Slack review. Use this skill whenever the user asks for a
  Slack review, daily standup brief, morning brief, "what did I miss", "catch me
  up on Slack", "run my daily review", or any variation of reviewing recent Slack
  activity. This skill reads the user's preferred channel list from the memory system,
  pulls the last 2 days of messages from each channel plus DMs and mentions, and
  produces a structured brief covering actions, decisions, blockers, stakeholder
  gaps, performance signals, strategic intel, PM team performance, and priority
  shifts. Writes both the brief and the raw pulled signal to _private/0_INBOX, then
  automatically hands off to the `ingest` skill in the same session (refactored
  2026-08-11 — this skill no longer diffs, shows a review widget, or applies
  anything itself; see `ingest` + `diff-propose`). Always use this skill at the
  start of each session when the user is beginning their workday or asking what
  happened recently.
compatibility: "Uses the official Slack connector (Anthropic Slack MCP) — tools named slack_read_channel, slack_search_public_and_private, slack_read_thread, slack_read_user_profile, etc. No local server, tokens, or setup: the connector must be authorized in Claude (connector settings). If the slack_* tools are not available, the connector isn't enabled for this session."
---

# Daily {{PRODUCT}} Slack Review

## Purpose
Pull the last 2 days of Slack activity across the user's {{PRODUCT}} channel list, DMs, and
mentions, and produce a structured daily brief to start their workday.

**Read `_private/ME.md` first.** It holds the owner's Slack user ID, direct reports,
watch list and OKR file. Org-level values (channel list, product) are in `ORG.md`.
Below, `<OWNER_SLACK_ID>` means the Slack user ID from `_private/ME.md`.

---

## Step 0 — Confirm the Slack connector is available

Before pulling anything, make ONE cheap call to confirm the connector is live:

```
slack_read_user_profile()        # no args → returns the current user
```

**If the `slack_*` tools aren't present, or this call errors:**
Stop. Do not attempt the review. Output:

> "The Slack connector isn't available in this session. Enable/authorize the
> official Slack connector in Claude's connector settings, then re-run."

No tokens, cache files, or diagnostic scripts are involved anymore — the old
`slack-mcp-server` (korotovsky) setup was retired. If the connector is authorized,
this call returns immediately and we proceed.

---

## Step 1 — Load the channel list

Read the channel list from the memory system:

```
3_RESOURCES/{{ORG}}/{{ORG}} Slack Channels.md
```

It contains ~36 channels as `[#channel-name](https://{{SLACK_WORKSPACE}}.slack.com/archives/CHANNEL_ID)`.
Extract the channel ID (the `C…` code after `/archives/`) from each URL.

**Do NOT enumerate the workspace** to discover channels — it has 3000+ channels.
Always use the pre-extracted IDs from this file. If a channel ID ever returns
`channel_not_found`, fall back to `slack_search_channels(query="<name>")` for that
one channel only.

---

## Step 2 — Pull messages

Compute the time window as Unix timestamps:
- **`oldest`** = start of 2 days ago (yesterday + the day before). If today is
  **Monday**, use the previous **Friday** (covers Fri–Mon).
- Leave `latest` unset (defaults to now).

**Channels** — for each extracted channel ID, call:

```
slack_read_channel(channel_id=<C…>, oldest=<unix ts>, limit=100)
```

Run sequentially. Many channels return empty — expected, don't skip any. If a
single channel errors (archived, rate-limited), log it and continue.

**DMs & mentions** — use search with Slack modifiers (no boolean operators; run
separate searches and merge):

```
slack_search_public_and_private(query="to:me after:<YYYY-MM-DD>", sort="timestamp")
slack_search_public_and_private(query="from:<@OWNER_SLACK_ID> after:<YYYY-MM-DD>", sort="timestamp")
```

The first catches messages/mentions directed at the user (including DMs); the second
catches their own recent activity for context. Paginate with the returned `cursor`
up to 2 pages each.

**Threads — read systematically, not selectively.** `slack_read_channel` results include a `reply_count` (or `thread_ts`) field per message. For **every** message where `reply_count > 0`, read the thread:

```
slack_read_thread(channel_id=<C…>, message_ts="<parent ts>")
```

**Do not pre-filter based on whether the parent message looks important.** This was the actual coverage gap, not an edge case: parent messages are frequently generic ("standup notes attached," a plain question, a filler status line) while the real decision, confirmation, or resolution lives entirely in a reply. Judging thread-worthiness from the parent alone misses exactly the messages worth reading — if the parent already told you everything, the thread wouldn't matter as much anyway.

**Volume exception:** if a channel window has an unusually high number of threaded messages (rough guide: >15 threads in one channel for the 2-day window), read all top-level messages first, prioritise threads on messages that mention the user, a DR, or a tracked initiative by name, and note in the output that thread coverage was volume-limited for that channel so it's visible rather than silently incomplete.

---

## Step 3 — Analyse and produce output

Analyse all messages collected. Apply these filters:

- Ignore empty channels (no output needed).
- Ignore bot/automated messages unless they contain incidents, experiment
  announcements, or support escalations.
- Focus on messages that involve the user directly (mentions, DMs) or affect {{PRODUCT}}
  initiatives the user owns.

Produce the output in **exactly this format**:

---

# {{PRODUCT}} DAILY SLACK REVIEW — [DATE RANGE]

## 1. IMMEDIATE ACTIONS (This Week)

- [Action item with context and deadline]
- Tag each with: `[Initiative] [Stakeholder] [Channel/DM]`
- Flag urgent items with ⚠️

## 2. DECISIONS NEEDED

- [Decision required, who's blocked, what context they need]

## 3. ACTIVE BLOCKERS & RISKS

- [Issue, owner, impact on timeline]

## 4. STAKEHOLDER ENGAGEMENT GAPS

- [Who hasn't been updated, what they need to know]

## 5. PERFORMANCE SIGNALS

**Positive:**
- [Evidence of progress, experiment results, user wins, team effectiveness]

**Negative:**
- [Incidents, complaints, delays, quality issues]

## 6. STRATEGIC INTEL

- [Market moves, {{PARTNER}} partnership developments, competitive signals]

## 7. PM TEAM PERFORMANCE

- [Evidence of PM effectiveness or coaching opportunities]
- [Delegation working / not working]

## 8. RECOMMENDED PRIORITY SHIFTS

- [Based on activity, what should move up or down the user's priority list]

---

## Style Rules

- Direct and factual. No filler words.
- Bullet points throughout.
- Include Slack message links or channel names for key items where available.
- Quantify where possible (e.g. "3 unanswered questions in #ext-{{PRODUCT_LOWER}}-support").
- If a section has nothing to report, write "Nothing flagged."
- Keep each bullet to 1–3 sentences max.

---

## Coaching Layer (apply to every output)

After producing the review, apply these filters before finalising:

1. **Skip-level exposure**: Flag any unanswered questions or signals from anyone
   on the watch list in `_private/ME.md` that the user hasn't responded to. These go in
   section 1 as ⚠️ items.

2. **Delegation check**: If an action item is something a direct report (listed in
   `_private/ME.md`) could own, note it with `[Delegate?]` tag.

3. **OKR filter**: For each item in section 8 (Priority Shifts), note which OKR
   it maps to. The OKR file is named in `_private/ME.md` — read
   it if you haven't already in this session.

4. **Avoidance pattern**: If the bulk of activity is process/tooling work and
   there are overdue exec-presence tasks (listed in `_private/ME.md`),
   call this out at the end of section 8.

---

## Step 4 — Write to inbox, then hand off to `ingest`

The review is raw capture, not canonical content. This skill's job ends once
both files below are written and `ingest` has been handed the baton — no
diffing, no widget, no apply logic happens here anymore (moved to `ingest` +
`diff-propose`, refactored 2026-08-11 to remove duplicate diff-generation paths).

**4a. Write two files to `_private/0_INBOX/`:**

1. `_private/0_INBOX/YYYY-MM-DD_slack-review.md` — the 8-section brief from Step 3.
   Filename and structure are invariant (see below).
2. `_private/0_INBOX/YYYY-MM-DD_slack-review-raw.md` — the raw signal collected in
   Step 2: every message and thread reply actually pulled, with channel,
   author, timestamp, and permalink where available. Group by channel; no
   fixed section structure required. This is what `ingest` (and, via `ingest`,
   `diff-propose`) works from — the summarized brief drops exact quotes and
   thread structure that field-level diffing needs.

Use today's date for both. This is the same intake path the memory system
uses for all raw inputs — do NOT write directly to canonical files from this
skill.

**4a-i. Provenance footer (mandatory, on the brief file AND in chat).**

Append this block as the last lines of `YYYY-MM-DD_slack-review.md`, and print
the same line in the chat response:

```
---
_Run provenance — skill `daily-slack-review` v<version from this file's frontmatter> ·
source `<absolute path of the SKILL.md actually being followed>` ·
channels pulled <n>/<total in channel list> · threads read <n> ·
thread-limited channels: <list or none> · raw file: written ·
ingest handoff: started | skipped (<reason>)_
```

**Why this is not optional.** It is the only runtime evidence of *which copy of
this skill executed*. A stale deployed copy cannot emit a current version string
and will emit no footer at all — which is exactly what `lint.mjs` Check 7 looks
for. Three prior drift incidents (6 Aug, 10 Aug, 11 Aug) were all invisible at
run time because the output of a drifted copy looked plausible. Report the real
numbers; a footer with invented counts is worse than none.

**4b. Hand off to `ingest`, same session:**
Once both files are written, immediately read and follow
`3_RESOURCES/AI Skills/ingest/SKILL.md` against today's two files — don't wait
for the user to ask separately. This is the boundary: this skill pulls and
captures; `ingest` classifies, routes, and (for the two Move 3 pilot
initiatives) calls `diff-propose` for STATE diffs. If the user explicitly says to
skip this (e.g. "just show me the brief, don't ingest yet"), stop after 4a.

### Output contract — how to tell whether this skill actually ran

This skill has **no knowledge of the vault's project structure and does not need
any.** It captures signal; `ingest` routes it. Therefore:

- **Never** address output to `1_PROJECTS/...` paths, name projects as targets,
  or instruct anyone to "create a note if one doesn't exist". That is `ingest`'s
  job and it has the information to do it. A review that guesses at project
  structure produces a routing table nobody can trust and a second, invisible
  project registry that has to be maintained by hand.
- **Never** ask for a project list to be supplied to this skill as context. Same
  reason — it creates the duplicate registry, and it violates single-source-of-truth.

**Three invariants define a valid run of the brief file specifically.** Any
output that breaks any one of them was not produced by this skill, regardless of
what the scheduled job is named:

1. Filename is exactly `_private/0_INBOX/YYYY-MM-DD_slack-review.md`.
2. Body is the eight numbered sections in Step 3, in order.
3. The file ends with the Step 4a-i provenance footer, carrying a version
   string that matches this file's frontmatter `version:` field.

**Absence is also a failure.** Invariants 1–3 only catch a *malformed* run. A
run that never happened — or one executed by a drifted copy that writes no
file at all — produces nothing to inspect, which is how the 10–12 Aug
divergence stayed invisible. `lint.mjs` Check 7 covers that case by flagging
the absence of a recent valid brief; do not treat "no findings in chat" as
evidence the pipeline ran.

The raw file (...-slack-review-raw.md) is a separate artifact with no fixed
structure and is not covered by these invariants — don't apply them to it,
and don't fold it into the brief file as a ninth section.

**If you are reading a review file that breaks either invariant:** the scheduled
job has drifted onto a different prompt. Fix the job to invoke this skill; do not
patch the output. Precedent: `_private/0_INBOX/20260806{{PRODUCT_LOWER}}memoryupdate.md` (6 Aug 2026) —
wrong filename, project-block structure, and a `create a note if one doesn't
exist yet` instruction. Diagnosed 7 Aug during ingest.

---

## Failure modes — handle these explicitly

| Symptom | Action |
|---|---|
| `slack_*` tools missing / `slack_read_user_profile()` errors in Step 0 | Stop. Output the "connector not available" message (see Step 0). |
| A single channel returns `channel_not_found` | Try `slack_search_channels` for that one channel; else log and continue. |
| A single channel call fails (rate-limited, archived) | Log and continue with remaining channels. |
| DM/mention search returns no results | Note it in output but proceed — channel data alone is still valuable. |
| Total messages > 500 | Focus analysis on highest-activity channels and DMs involving the user. Bulk-summarise low-activity channels. |
| A channel has >15 threaded messages in the window | Read all top-level messages; prioritise thread reads by relevance (the user/DR/tracked-initiative mentions); note in output that thread coverage was volume-limited for that channel. |

---

## Notes

- Designed to run at the start of each workday. Output always lands in `_private/0_INBOX/`
  (two files — brief + raw), then hands off to `ingest` in the same session.
- Channel list lives in `3_RESOURCES/{{ORG}}/{{ORG}} Slack Channels.md` — to add or
  remove channels, edit that file. The skill picks up changes automatically next run.
- Uses the official Slack connector; there are no local caches or tokens to manage.
- **Diffing, review widget, and apply/log for Move 3 pilot initiatives live in
  `ingest` + `diff-propose` now, not here** (refactored 2026-08-11 — see
  `ingest/SKILL.md` Step 2c and `diff-propose/SKILL.md`). This skill no longer
  calls `diff-propose` directly.

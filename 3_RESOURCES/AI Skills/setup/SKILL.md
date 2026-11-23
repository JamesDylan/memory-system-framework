---
name: setup
version: 2026-11-23.1
description: >
  First-run setup: a short interview that builds the user's two vaults from this
  engine checkout. Use this skill when the user says "set me up", "set up the
  memory system", "install", "first run", or when AGENTS.md finds setup is not
  finished (the private ME.md is missing or still holds `{{`). It asks the core
  five facts, then a yes/no for each optional part, looks up Slack IDs through a
  Slack connector when there is one, shows every value for approval, writes the
  answers file, runs init-vault.py and lint, and ends with the "not filled in yet"
  list. Content (goals, OKRs, plans) never goes in the interview; it goes to
  `ingest` afterwards.
---

# Setup — Skill

## Purpose

Build a working pair of vaults without the user editing JSON. You ask, they answer,
you write the answers file and run the engine's own scripts. Nothing here is new
machinery: this skill only drives `init-vault.py` and `.scripts/lint.mjs`.

Run it from the engine checkout (the folder with `init-vault.py`). The vaults are
built in new, empty folders elsewhere.

## Interview rules

1. **Every question is one of three kinds**, and you say which:
   - **fact**: answer now ("What is your role?").
   - **yes/no**: do you have or want this ("Do you have direct reports?").
   - **later**: every question accepts "later". A later value is left unset, so
     `init-vault.py` writes `(set KEY)` and lint lists it under "Not filled in yet".
2. **Never ask for content.** Goals, OKRs, plans, strategy, notes: ask only whether
   they exist (yes/no). Their text goes through `ingest` after setup.
3. **Never ask the user to type an ID.** Slack user and channel IDs come from a
   Slack connector. No connector: mark them "to look up later".
4. **One part at a time.** Open each part with a progress line, `Part 3 of 8: Slack`.
   Ask the detail questions of an optional part only after a yes.
5. **Free text is fine.** If the user answers several questions in one sentence,
   fill what you can and ask only what is still open.
6. **Propose, then write.** Nothing is written until the user approves the full
   list of values (Step 2).

## Step 1 — The interview (8 parts)

Keep a list of answers as you go. The key in brackets is the answers-file key.

**Part 1 of 8: You** (all facts)
1. Your full name? [`OWNER_NAME`] The first word becomes the short name [`OWNER`]
   unless they say otherwise.
2. Your role or job title? [`ROLE`]
3. Your company, as you want it in folder names (one word is best)? [`ORG`]
4. Your product or product area, short name? [`PRODUCT`] And its full name, or
   later? [`PRODUCT_LONG`]
5. Your manager's name, or later? [`MANAGER`]

**Part 2 of 8: Where the vaults go** (yes/no)
- "I'll put your shared vault at `~/vaults/<company in lower case>/memory_system`
  and your private vault beside it at `.../memory_private`. OK?" Yes: use those.
  No: ask for one parent folder (fact) and use the same two names inside it.
  [`SHARED_VAULT_PATH`, `PRIVATE_VAULT_PATH`] Both folders must be new or empty.

**Part 3 of 8: Slack** (yes/no)
- "Do you use Slack for work, and do you want a daily Slack brief?"
- Yes, and you have a Slack connector:
  - Look up the user by name or email. Take their user ID [`OWNER_SLACK_ID`] and
    the workspace name, the part before `.slack.com` [`SLACK_WORKSPACE`].
  - List the channels they belong to, most active first. Let them pick by name
    (they can search the list). Keep each picked channel's name and ID for Step 4.
  - Show what you found and ask "Is this you?" (yes/no) before you use it.
- Yes, no connector: ask the workspace name (fact, or later). Mark the user ID and
  the channel list "to look up later". Do not ask for IDs.
- No: leave the Slack keys unset.

**Part 4 of 8: Direct reports** (yes/no)
- "Do you manage anyone directly?" Yes: their names (fact). No: note "none".

**Part 5 of 8: Watch list** (yes/no)
- "Are there people whose unanswered questions you want raised first in your daily
  brief?" Yes: names, and a short why for each if they want one (fact).

**Part 6 of 8: Main initiative** (fact or later)
- "What is the main initiative you are working on right now?" [`PILOT_INITIATIVE`,
  and `PILOT` = the same name or a short form]. Later: leave unset; init creates an
  "Example Initiative" folder you can rename.
- "Is there one partner company your product works through?" Name [`PARTNER`], or
  no (write `none`), or later.

**Part 7 of 8: Personal goals** (yes/no)
- "Do you have personal goals for your year written down somewhere?" (What you
  want from your own year.) Yes: note it for Step 5. Do not ask for the goals.

**Part 8 of 8: Company OKRs** (yes/no)
- "Does your company or team have OKRs or objectives you are measured on?" Yes:
  note it for Step 5. Do not ask for them.

## Step 2 — Show the values for approval

Show one table: every answers-file key with its value, then the extras that go into
the vault after init (manager, direct reports, watch list, Slack channels). Mark
each later value `later` and each missing ID `to look up later`. Ask "Write these?"
(yes/no). On a correction, change that value and show the table again.

## Step 3 — Write the answers file and build the vaults

Write **answers.json** in the parent folder of the two vaults, not in this engine
checkout (it holds personal values and must never be committed). Its shape is
`templates/answers.example.json`, plus `ROLE` and `MANAGER`. Leave out every key
whose value is later; `init-vault.py` fills those with `(set KEY)`. Paths may start
with `~`. Example:

```json
{
  "ORG": "Acme", "PRODUCT": "Widgets", "OWNER_NAME": "Sam Example",
  "ROLE": "Senior Product Manager", "MANAGER": "Alex Lead",
  "SLACK_WORKSPACE": "acme", "OWNER_SLACK_ID": "U00000000",
  "SHARED_VAULT_PATH": "~/vaults/acme/memory_system",
  "PRIVATE_VAULT_PATH": "~/vaults/acme/memory_private"
}
```

Then run, from this engine checkout (`<parent>` is the vaults' parent folder):

```bash
python3 init-vault.py <parent>/answers.json
cd <parent>/memory_system && git init -q
```

If `init-vault.py` stops with "is not empty", ask for another folder (fact) and go
back to Step 2. If it fails any other way, show the error and stop.

## Step 4 — Fill in what the answers file does not carry

All edits are in the new vaults. Each is a small, targeted edit.

- **Direct reports.** In the private ME.md, under `## Direct reports`, put one
  `- Name` line per report, or `None`. If none, the private Direct Reports.md stub
  stays, unfilled and harmless: add its path to `notFilled.skip` in
  the vault's lint.config.org.json (in .scripts) so lint stops listing it. That array replaces the
  engine's, so copy the engine's list with it:
  `"notFilled": { "skip": ["templates/**", "_private/2_AREAS/<ORG>/My Team/Direct Reports.md"] }`.
- **Watch list.** In ME.md, one `| Name | why |` row per person under `## Watch list`.
- **Slack channels.** If channels were picked, replace the example line in
  the channel list file, `<ORG> Slack Channels` under 3_RESOURCES/<ORG>, with one line per channel:
  `- [#name](https://<workspace>.slack.com/archives/<channel ID>)`.

## Step 5 — Lint, then hand over

```bash
cd <parent>/memory_system && node .scripts/lint.mjs
```

- The summary line must show **0 must-fix**. If not, show the must-fix findings and
  fix only what this setup caused; report anything else.
- Show the "Not filled in yet" section of the report as the user's to-do list, and
  add the items marked "to look up later" that lint cannot see (Slack channels).
- If they said yes to personal goals or OKRs: "Drop the document in
  the inbox of the new vault (0_INBOX in the private vault) and say *process my inbox*. `ingest` files
  personal goals in your private career file and company OKRs in the shared
  strategy and objectives files."
- Tell them to open the new shared vault, not this checkout, from now on, and to read
  docs/first-week.md there for the first week.
- Search (optional): `.scripts/qmd-bootstrap.sh` in the new vault, if qmd is installed.

## Never

- Commit or push anything, in the engine or the new vaults.
- Write the answers file inside a vault or this engine checkout.
- Ask for content, passwords or tokens, or guess an ID.
- Overwrite a folder that has content.

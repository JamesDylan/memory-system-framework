# Your first week: what to put in first

A new vault is mostly empty files that end `> Not filled in yet.` Until you fill them, your agent has nothing to answer from. This page says what to give it first, in what order, and where each thing ends up.

Paths are relative to the shared vault (the folder the `setup` skill or `init-vault.py` built). Setting up: [setup.md](setup.md).

## Paste into chat first

Start by pasting material straight into chat and saying **"ingest this"**. You don't need to save a file, fill in a template or know where anything goes. The `ingest` skill reads what you pasted, tells you what it found, proposes the edits file by file, and changes nothing until you say yes.

Paste the raw thing: the plan, the doc, the notes. Don't rewrite it into the templates yourself. Sorting it into the right files is the agent's job.

The inbox folder (`_private/0_INBOX/`) is for later: once you use Obsidian or a file manager, or when you have a pile of files to add at once. Drop them there and say **"process my inbox"**.

## The fill order

Do these in order. Each step gives the next one something to attach to.

| # | What to paste | What the agent does with it | Where it lands |
|---|---|---|---|
| 1 | **The current cycle or quarter plan.** The list of what the team is working on now, with owners if you have them. | Fills in the cycle's name and dates, one health row per initiative, the top priorities and the risks. It asks which items are committed for this cycle: only those become initiatives. The rest are ideas. | `1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md`. Ideas go to `2_AREAS/{{ORG}}/_H2 Roadmap/CANDIDATES.md` |
| 2 | **One document per live initiative.** A PRD, one-pager or epic description. One at a time. | Creates the initiative's folder (with your OK) and fills in why it exists and its scope, then where it stands now. | `1_PROJECTS/{{ORG}}/<Initiative>/BRIEF.md` (why and scope) and `STATE.md` (where it is now) |
| 3 | **Your last one or two meeting notes.** Raw notes or a transcript. | Adds a dated entry to each initiative the meeting touched, updates its status if something changed, and proposes a to-do file for each open action. | The initiative's `LOG.md` (and `STATE.md` if needed). To-dos in `1_PROJECTS/Actions/`, or `_private/1_PROJECTS/Actions/` for your own |
| 4 | **OKRs, metrics and stakeholders.** The objectives doc, a recent metrics pull, an org chart or list of who owns what. | Writes the objectives and key results, records each metric value with its date, and adds a page per person plus where they fit. | `2_AREAS/{{ORG}}/context/cy27_objectives.md`; metric values in `2_AREAS/{{ORG}}/_metrics/registry.yaml`, then `metrics_dashboard.md`; people in `2_AREAS/{{ORG}}/people/` and `2_AREAS/{{ORG}}/context/stakeholder_map.md` |

After step 1, ask your agent **"what's in my active cycle?"** You should get a real answer.

## What to expect

- **You approve every change.** Each step ends with proposed edits. Say yes, correct them, or say no.
- **Ideas stay ideas.** An idea nobody has committed to does not get a folder. It is one line in `CANDIDATES.md` until you say it is in a cycle.
- **The example initiative.** `init-vault.py` creates one example initiative folder so the skills have something to point at. Once your real initiatives exist, the agent can help you swap it out.
- **See what is still empty.** Run `node .scripts/lint.mjs`. Its to-do list names every file that still ends `> Not filled in yet.`

## Learning mode

A new vault starts with learning mode on (`Learning mode | on` in the private ME.md). Your agent ends each task with a two-line "What just happened:" note: which files it read or changed, and why. The `Level` in ME.md sets how much it explains:

| Level | The note |
|---|---|
| 1 | Names each file and what it is for, in plain words. For your first week |
| 2 | Names the files and the rule that sent the change there |
| 3 | One line, only when something unusual happened |

Say "I'm at level 2" or "turn off learning mode" and your agent updates ME.md.

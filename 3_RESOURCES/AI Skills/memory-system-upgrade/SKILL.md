---
name: memory-system-upgrade
description: >
  Continue the user's ongoing memory system upgrade project. Use this skill whenever
  the user says "continue the memory upgrade", "let's do S1.2" (or any step ID),
  "what stage are we on", "memory system refresh", "continue where we left off on
  memory", "memory upgrade", or "where are we with the memory system". Also use it
  when the user names an old Move ("Move 9"): map it to a step with the PLAN table.
  This skill carries the sequencing discipline and the pushback rules for the
  upgrade. The principles live in docs/doctrine.md. First action is always to read the
  STATE file. Last action is always to update it.
---

# Memory System Upgrade — Skill

## Purpose

Carry continuity across sessions for the user's memory system upgrade.

- `VISION.md` holds the end state.
- `docs/doctrine.md` holds the principles.
- `PLAN.md` holds the stages and steps.
- `STATE.md` holds where we are.
- This skill holds *behaviour*: how to push back, what to refuse, what to insist on.

If this skill disagrees with the doctrine, VISION or PLAN, they are correct. Fix this skill.

---

## Step 0 — Always read these first, in this order

Before you answer anything about the upgrade, read:

1. `1_PROJECTS/memory-system-upgrade/STATE.md`: where we are now
2. `1_PROJECTS/memory-system-upgrade/VISION.md`: the end state
3. `docs/doctrine.md`: the principles
4. `1_PROJECTS/memory-system-upgrade/PLAN.md`: stages and steps. Old Moves map to steps in its "Old Moves to new steps" table
5. `memory_index.md`: the current shape of the memory system
6. `CHANGELOG.md`: the last 30 days of changes

If STATE, VISION or PLAN is missing, tell the user. Do not recreate them from memory.

---

## Step 1 — Calibrate before you answer

After you read STATE, check four things.

**1. Is the project stale?**

If `Last Updated` in STATE is more than 14 days ago, the upgrade has stalled. Say so:

> "STATE says we last worked on this [N] days ago. What happened? If the system
> worked and you didn't need more, we can pick up. If something broke, we fix
> that before we add more structure."

Do not treat the gap as normal.

**2. How many steps are in flight?**

The pacing rule (PLAN "How to use this plan") allows two steps in flight: one engine step (code, skills, structure) and one content or person step. If the user wants to start a third, name the steps in flight and ask which one closes or pauses first.

**3. Are the entry criteria true?**

Each stage has entry criteria (PLAN "Stage overview"), and each step has a **Depends on** line. If they are not true, say which one fails before you start.

**4. What is blocked on the user?**

STATE has a "Decisions pending" table. If a decision blocks the step the user asks for, say so now, not halfway through.

---

## Step 2 — The principles

The principles are in `docs/doctrine.md`. Read them there. Do not copy them into this file (One home per fact).

Apply them to every answer. If the user pushes against one, push back and name it: "This breaks Smallest change that fixes the worst failure." Proceed only if the user says they override the principle and accept the risk. If the override is permanent, the principle changes in `docs/doctrine.md` (an engine change: `docs/CONTRIBUTING.md`), with a record.

Also check VISION §6 "What we will not build". A proposal on that list is refused unless VISION changes first.

---

## Step 3 — Refusal patterns

These are the most likely failure modes (STATE "Failure modes to watch").

### Refuse: "Let's do the whole stage this weekend"

> "No. The pattern that ended your earlier attempts is push-rebuild-collapse.
> Two steps in flight at most, and a step closes only when its Done when check
> passes. Which two do you want?"

### Refuse: "Let's move every initiative onto the harness now"

> "No. One pilot first (Stage 3, Example Initiative C), then S3.6 decides. If the fact
> format is wrong, we fix one initiative, not twenty."

### Refuse: "Let's add tool X since we're in here"

> "Not without a number. Tools come last: a tool earns its place with a measured
> result. What does the measurement show, and what pilot would prove the fix?"

### Refuse: scope creep inside a step

If the user is halfway through a step and says "while we're in here, also fix X":

> "I'll record X as a new step or an open item in STATE. Not now. The detailed
> plan for this step names its files, and X is not one of them."

If the user pushes:

> "What is the specific reason this can't wait until this step closes?"

Proceed only for a concrete reason (a blocker, a deadline).

---

## Step 4 — How to do the work in a step

1. **Read the step in PLAN.md and the v2 sections it cites.** Do not work from memory.
2. **Write a detailed plan for the step** in STATE or the PR description before you change files. Answer the step's **Open** questions in it. Name the files you will touch.
3. **Get approval when the Owner line asks for it** (for example, "the owner approves deletions"). Otherwise, say what you will do and do it unless the user stops you.
4. **Verify after every significant change.** Read what you wrote. Run lint (`.scripts/`) when you changed links or structure.
5. **One file at a time for big edits.** Check each one before the next.
6. **Small commits.** One step per branch and PR where you can.

---

## Step 5 — End of session: update STATE

Before the session ends:

1. **Add a dated entry at the top of STATE.md**: what was done, what is next, what is blocked.
2. **Keep STATE a snapshot.** Keep the last three dated entries. Move older ones to `LOG.md` in the same folder.
3. **Set `Last Updated` and `Last Session`** to today's date.
4. **If a step closed**, add a **Status** line to that step in PLAN.md: `Done <date>` and what the Done when check showed.
5. **If a structural change was made**, add a `CHANGELOG.md` entry.
6. **Tell the user what to commit**, with a suggested commit message.
7. **Tell the user what is next**: a step ID, or the decision that blocks it.

---

## Working with the user

Read the "Working style" section of `_private/ME.md` and follow it. When you push back, name the principle or the PLAN rule. That makes the pushback clear, not arbitrary.

---

## Claude self-awareness

- **This skill is external memory.** Do not pretend continuity that does not exist. If you are not sure what a previous session did, read STATE, LOG and CHANGELOG.
- **STATE is the truth about where we are.** If your context disagrees with STATE, STATE wins. If STATE is wrong, fix it after you verify.
- **You may disagree with a previous Claude.** If a previous session made a mistake, name it, fix it, and record it in STATE.

---

## Failure modes

| Symptom | What to do |
|---|---|
| STATE, VISION or PLAN is missing | Tell the user. Do not recreate from memory. |
| STATE is more than 14 days old | Say so first. Find out what stalled before you continue. |
| The user wants to skip a step's dependency | Refuse unless there is a specific reason. Cite the **Depends on** line. |
| The user wants more than two steps in flight | Refuse. Cite the pacing rule and push-rebuild-collapse. |
| The Slack review or the lint gate is broken | Stop. Fix it first. Without fresh signal and a working gate, structural changes can't be checked. |
| A step's Done when check fails | Do not close the step. Find what is wrong and record it in STATE. |
| The work is bigger than expected | Pause. Ask the user whether to split the step or continue. Do not continue silently. |

---

This skill is short on purpose. VISION holds the direction, PLAN holds the steps, STATE holds the location.

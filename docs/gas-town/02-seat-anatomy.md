# 02. Anatomy of a seat

**Last Updated:** 2026-11-12 | **Type:** external reference (not {{ORG}} fact) | **Source:** see `README.md` in this folder

A seat is one agent with one job. Every seat in his town has the same four parts. This is the reusable unit. Everything else is this pattern repeated.

## The four parts

| Part | What it is | Rule |
|---|---|---|
| **Brief** | The system prompt. One job, house rules, and what it never does. | One sentence for the job. If it needs two, it is two seats. |
| **Drawer** | The one note or folder the seat owns in the vault. | It reads the rest. It cannot change what it does not own. |
| **Clock** | The schedule. Wake, do one round, sleep. | A script checks for new work first. No new work, no model run. |
| **Mail** | A short note at the end of every round, to the Mayor or to you. | Five lines at most: what changed, what needs a decision, what could not be done and why. |

## Why each part exists

**Brief.** A narrow job gives a narrow failure surface. The brief also states what a good round looks like: what the output is, where it goes, how long it is, and what you would be annoyed to find missing. If you cannot describe a good result in three sentences, the agent cannot produce one.

**Drawer.** Single-writer ownership. Two agents never edit the same note, so there are no conflicts and every line has one accountable author. Other seats read it. This is also how seats cooperate without talking: the messenger writes a ranked list in its drawer, the prototyper reads it.

**Clock.** A seat that runs only when you talk to it is level 1. The clock is what removes you from the loop. The script gate matters as much as the schedule. It keeps cost down and stops the agent inventing work on a quiet day.

**Mail.** The seat reports up, not sideways. Mail is the interface between a seat and the person or agent accountable for it. Keeping it to five lines is what makes ten seats readable.

## House rules in every brief

From his template:

- Say where every claim came from. Link the source.
- If nothing is new, say so in one line and stop.
- If unsure, write the question down for a person. Do not guess.
- A "you never" line: send, merge, release, delete, contact customers.

The second rule is the least obvious and the most useful. Agents fill silence. A seat told to produce a weekly note will produce one in a week where nothing happened. His example mail line: "Weekly note: public holiday, nothing released."

## How to commission a seat

From `starter/first-job.md`:

1. Write the brief.
2. Run it by hand three times in the chatbot you already have.
3. Fix the brief each time, not the output.
4. Only then put it on a clock.

Step 3 is the discipline. Editing the output teaches the system nothing.

## Choosing the first job

List what you did last week that was one of these:

- Read a lot of something and summarised it.
- Moved information from one place to another.
- Checked whether something had changed.
- Wrote a first draft that someone else changed anyway.

Pick the one that passes all four tests:

| Test | Reason |
|---|---|
| It recurs every week. | A one-off is not worth a brief. |
| It needs reading and drafting only. | Early seats do not send, merge or release. |
| A wrong answer is cheap and obvious. | Wrong answers will happen. Start where you would spot them. |
| You can describe a good result in three sentences. | Otherwise the agent cannot either. |

## His town as of November 2026

**Seats.** A Mayor plus twelve seats. The README names: messenger, prototyper, engineer, prioritiser, groomer, chronicler, chief of staff, product marketing, growth, marketing, SOC 2 steward, and a build crew that takes a GitHub issue in and puts a draft pull request out.

| Seat | Job |
|---|---|
| Messenger | Reads signals on a schedule, files findings, ranks what customers need. |
| Prototyper | Builds clickable versions of the top problems in the twin. |
| Engineer | Feasibility review, ready check, splits oversized issues. |
| Prioritiser | Ranks the backlog. Flags urgent bugs. |
| Groomer | Ready checks and leftovers. |
| Chronicler | Keeps the weekly product note current. Every line links to its source. Runs 8:30 and 4:30 on weekdays. |
| Chief of staff | Who is working on what. |
| Product marketing | Explainer videos, help docs. |
| Growth | Revenue ideas. |
| Marketing | Drafts follow-ups. |
| SOC 2 steward | Compliance status. |
| Build crew | GitHub issue in, draft pull request out. |

**Scripts.** About two dozen scheduled jobs. Plain Python on a clock. From slide 29:

| Job | Schedule |
|---|---|
| Issue intake | Every 15 min |
| PR fix loop | Every 30 min |
| Conflict merge | Every two hours |
| Vault autosync | Hourly |
| PostHog snapshot | 07:00 |
| Release notes | 07:15 |
| Instrumentation gap | 07:30 |
| Event watchdog | 07:45 |
| Slack progress post | 08:00 and 16:00 |
| Slack intake | 09:00 and 17:00 |
| Discovery sweep | Monday 06:00 |
| Wake a seat | On its day |

Most of the system is deterministic code. Models run at the edges where judgment is needed. This follows Anthropic's guidance to use workflows before agents.

**Connectors.** Slack, GitHub, Help Scout, PostHog, Maze, Monday, Google Drive, Gmail, Calendar, Figma, Rollbar, Datadog. Plus one read-only system API on the product that returns no personal data.

**Runtime.** Gas City, the open-source orchestrator. See `04-machinery.md`.

## One day of the messenger

Monday 26 October:

- 6:40am. Usage checked, two notes updated.
- 8:56am. Weekly note started, team update drafted.
- 9:20am. A usage finding written up, ticket filed.
- 9:24am. Odd usage patterns noted.
- 1:42pm. A finding re-checked with fresh data.
- 4:42pm. Weekly note: public holiday, nothing released.

Six rounds. Each is small. None needed a person.

## The seat chain

His example of seats feeding each other through the vault:

- Monday 9:00. Messenger ranks customer needs. Top of the list: coaches sign off without writing feedback. 36% write feedback. The bar is 45%.
- Monday 11:30. Prototyper reads the list, picks the top item, builds a clickable fix.
- Then the engineer exchange described in `01-thesis.md`.
- Then a person decides: test, take forward or stop.

The handoff works because each seat has a known drawer. No seat calls another directly at levels 3 and 4. They read each other's output.

## The Mayor is a seat too

Same four parts. Its job is to make sure nothing gets stuck. It does three things:

- **One agent to talk to.** You talk to the Mayor. The Mayor talks to the others.
- **Hands out work.** Plans each job and routes it to a seat or the build crew.
- **Remembers.** Records decisions and lessons so the next session knows them.

Its drawer is the decision log and the routing record. Its mail goes to you.

Build it last. A Mayor with two seats under it adds a layer and saves nothing.

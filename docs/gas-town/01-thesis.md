# 01. The thesis

**Last Updated:** 2026-11-12 | **Type:** external reference (not {{ORG}} fact) | **Source:** see `README.md` in this folder

## The situation he describes

Marius Wium is Head of Product at RedSeed, Christchurch. The team is three developers, one designer, one product manager and him.

The developers adopted coding agents. Merged pull requests per month on the main product:

| 2025 | Sep 51 | Oct 42 | Nov 46 | Dec 88 |
|---|---|---|---|---|
| **2026** | Jan 79 | Feb 37 | Mar 73 | Apr 167 |
| | May 356 | Jun 302 | Jul 181 | Aug 207 |
| | Sep 183 | Oct 190 | | |

Baseline is about 50. The peak is 356. The steady state is about 190. That is roughly 4x sustained, with a spike to 7x while the obvious backlog was cleared.

Then the plateau. The team could build almost anything. The question became what to build next. Delivery stopped being the constraint. Deciding became the constraint.

## Three responses, two of which fail

The talk is framed as a game with three choices.

**1. Say yes to everything and build it fast.** Fails. You then launch and own everything. Support drowns, sales cannot keep up, and nobody can say what the product is for. Building got cheap. Owning did not.

**2. Read every signal and explore every idea yourself.** Fails. Even with help, a few ideas get explored at a time and everything else waits. You become the queue for a fleet of robots. You burn out.

**3. Learn from the developers and apply it to product operations.** This is the path.

## What the developers actually did

The developers climbed a ladder (credited to Steve Yegge):

1. Autocomplete
2. Agent asks permission
3. Agent has full permissions
4. Agent fills the screen
5. Command line only
6. Three agents
7. Ten agents
8. A manager of agents

The pattern across the steps: **attention is the bottleneck.** The developers stopped watching the robots. They shaped what went in and checked what came out.

The quest is to do the same for product work. He calls it agentic product ops: extend the software factory to the rest of the town. That means deciding what to build and telling people about it. People still decide.

## The six levels for product

Each level gives the machine more of the work with less watching. Each has a catch. The catch is what pushes you to the next level.

| Level | Name | What it does | Examples from his town | The catch |
|---|---|---|---|---|
| 1 | Chatbot | Drafts, questions and compares ideas when asked. | `/clarify-intent` (fuzzy idea in, spec with gotchas out). `/ux-heuristic-eval` (ten heuristics, findings rated 0 to 4). `/git-release` (release notes and test checklist from merged PRs). | It only moves while you talk to it. There is one of you. |
| 2 | Vault | Holds strategy, evidence and decisions in one shared place. Includes ideas that were stopped. | Product strategy (seven questions, the evidence, what we will not do). Current cycle (what is live, merged, who waits on what). Backlog (parked work and why). | It is only as fresh as you keep it. Four days off and it is stale. |
| 3 | Messenger | Reads support, Slack, forums and usage on a schedule. Files findings in the vault. | "What shipped" in plain words for account managers. Slack digest of decisions and requests. Usage watcher (found 85% of rage clicks on Home hit the carousel arrows). | Soon there is more than anyone can read. Every idea still waits for you. |
| 4 | Prototyper | Builds clickable versions of the top problems in a copy of the product on made-up data. | `/mock-feature` (one sentence to on-screen). Scenario switch (coach mode, mobile, empty states). `/restyle-issue`. | A painted front. Nobody has checked what is behind it. |
| 5 | Engineer | Checks each prototype against the real code while change is cheap. Readies the ticket. | Feasibility review (cost, and a smaller way to learn). Ready check on every open issue. Split a bundle into parts. | Agents break. Credits run out, connectors stop, loops repeat. You fix them. |
| 6 | Mayor | Runs the other agents and reads every report. You talk to one agent. | Hands out work. Records decisions and lessons. Sends you only what needs a decision. | What is left on your desk is the judgment. |

Notes on the levels:

- Levels 1 to 3 only read and write notes. Nothing is sent, merged or released.
- Level 2 is the foundation. The vault is shared memory. People and agents both read and write it. Every note links to others.
- Level 4 depends on the "twin": a clickable copy of the product's screens on made-up data. He calls it his biggest gain and says it is not a one-week job. Start with the three most-visited screens.
- Level 4 has a fixed decision step. Every prototype ends in one of three outcomes: **test** (put it in front of a few users), **take forward** (merge it, the engineer works out the build), or **stop** (close with a reason, and the town remembers).
- At level 5 agents start talking to each other. His example: the prototyper asks the engineer if #52 is buildable. The engineer returns four ways to make it cheaper. The prototyper takes all four. Cost drops to a fifth. One open question is settled. The engineer closes with a note to the Mayor. Elapsed time: 63 minutes, no human.

## The Mayor's output

His example of one morning. Five reports arrive from marketing, groomer, engineer, prioritiser and prototyper. The Mayor handles them and sends him three lines:

1. Review prototypes #48, #49 and #52.
2. Sign off a video.
3. Look at two urgent bugs before Monday.

That is the product: five reports in, three decisions out.

## What it costs

- Three or four top-tier Claude plans (Max 20x), plus team accounts for everyone else.
- Duplicated work.
- Moments of "what is it doing?".
- About a year of building alongside the day job.

## What the talk does not claim

- No productivity number for the product side. The PR chart measures delivery, not product ops.
- No claim that this works at a larger company. He says it is one implementation for one small company.
- No claim that judgment is automated. The golden law says the opposite.

## The closing instruction

1. Find one job a machine could have done last week.
2. Give it away this week.
3. Spend the hour talking to customers.

Point 3 matters. The returned time has a named destination. Without one, the inbox takes it.

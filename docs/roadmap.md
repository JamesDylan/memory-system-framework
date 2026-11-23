# Roadmap

Where the engine is going, and how each job works today by hand and with agents. Which seats run in the author's vault: `examples/seats/README.md`.

## Stages

The order is fixed by evidence: each stage starts when the one before it shows a measured result.

| Stage | What it adds | Outcome for you | Status |
|---|---|---|---|
| **Measure** | Baseline cost and time per task; weekly health numbers; skill scorecards; typed, sourced facts | You can see whether the system is getting more accurate and cheaper | Mostly done |
| **Project harness pilot** | One project where facts come from listed sources, not hand copies. Specs sync from Drive. A weekly truth check | Answers follow the live spec, and accuracy is a number, not a feeling | In progress |
| **Next agents** | `truth-check` (truth rate for the pilot), `state-refresh` (stale project pages refreshed from Slack and tickets), `spec-sync` (Drive copies kept current) | Project pages stay current without anyone copying status by hand | Next |
| **Pipelines** | One stage template with its own checks and evals. Memory upkeep, discovery and the experiment loop rebuilt as stages and run as seats | Discovery starts from what the team knows, and costs less per run | Planned |
| **Active layer** | New projects start from a template and a baseline. "Help me write the PRD" routes to the right pipeline in any AI tool. Process gates checked in CI, with a visible skip | No project starts from a blank page | Planned |
| **Scale and automate** | Every live project on the harness. All agents maintain the vault through PRs. Routine facts auto-apply once proven safe. Changed skills replayed against past sessions before they go live. Monthly pruning | A week passes with no manual run, and the system gets simpler as it grows | Planned |

What keeps it cheap and accurate along the way:

- **Scripts before models.** Gates, checks, health numbers and applying your ✅ are plain scripts. A model runs only where judgment is needed.
- **Auto-apply waits** for a proven clean rate.
- **Uses the access you already have.** Skills and agents use the connectors your agent already has: Slack, Google Drive, Productboard and others.
- The rest are rules in [doctrine.md](doctrine.md): "Hard limits for scheduled agents" and "Tools come last".

## Every job, by hand or by agent

| Job | By hand | With agents |
|---|---|---|
| **Capture** Slack, meetings, docs | Paste into `_private/0_INBOX/`, or ask your agent to "run my daily Slack review" | Meeting agent picks up each new transcript within 15 minutes. Daily Slack pull. Spec sync from Drive *(next)* |
| **File** each fact in its home | Ask your agent to "process my inbox" (`ingest`) | The capturing agent routes it and drafts the change itself |
| **Approve** changes | Review cards in your agent | ✅ or ❌ on the agent's Slack thread. Reply to edit. A script applies your decision, no model needed |
| **Start a project** | Copy the templates | Reply `project <Name>` in Slack. The dispatcher builds the folder and asks you to confirm |
| **Keep project status current** | Edit `STATE.md` | Agents draft field-level changes from meetings today, and from Slack and tickets for stale projects *(next)* |
| **Record results and KPIs** | Edit the insight or metric file | Experiment agent files each strong result daily. KR feed proposes changes from Productboard weekly *(built)* |
| **Share team updates** | Write the summary | Team-meeting agent drafts it for a ✅, then publishes to a Slack canvas *(built)* |
| **Health check** | Run `lint`, read the report | Daily on your machine and on every PR in CI. Weekly health numbers. An agent drafts the fix PR |
| **Check facts are true** | Spot-check a file | `truth-check` samples ~10 facts a week against their source and sends at most 3 questions to the owner *(next)* |
| **Learn from mistakes** | Fix the skill | Three rejections for the same reason propose a rule change for your ✅. An agent never edits its own rules |
| **Discovery, PCB, PRD, experiments** | Prompt a skill stage by stage | Pipelines run as agents, start from a baseline of what the team knows, and promote learnings back *(planned)* |

## Self-sustaining and self-correcting

The goal is a vault that keeps itself true with about 10 minutes of a person's time a week. The weekly quality loop does it:

1. **Sort every finding by who acts.** Agents fix the mechanical ones (dead links, missing stamps, a synced copy out of date). Agents propose the rest for the owner's ✅. Only real judgment reaches a person, at most 3 asks per owner per week.
2. **Check facts against the source.** An agent samples facts each week and marks each one supported, contradicted or unclear. The result is the **truth rate**.
3. **Corrections become tests.** Each correction you make becomes a test question with the right answer. Each project has 10 or more, run weekly.
4. **Track numbers, not lists.** One health file holds truth rate, test score, fresh sources, upkeep minutes and cost per question. The weekly digest leads with them.
5. **Rules improve from rejections.** The same reason for a "no", three times in ten sessions, proposes one rule change.
6. **Prune.** Each month, checks and agents that led to no action are demoted or removed, so the system gets simpler as it grows.

**Guard measures.** The system must not get better at the cost of these: truth rate 90% or more, test score 8 of 10 or more, owner upkeep 10 minutes a week or less, cost per question falling or flat, and no disproved idea coming back without new evidence.

## One ecosystem: memory, agents and pipelines

Three parts work together. None is rebuilt by the others.

| Part | Gives | Where |
|---|---|---|
| **The memory system** | Shared facts, one home each, with sources and stamps | This engine, and the vaults it builds |
| **The agents (seats)** | Work on a clock, with hard limits, locks and evals | `examples/seats/` in this engine; `2_AREAS/Agents/` in a vault |
| **The pipelines** | Discovery, PCB, one-pager and PRD stages, a prototype kit and a "twin" of the product on made-up data | The team's discovery lab repo |

Joined, they work like this:

- **Pipelines run as seats.** A stage starts by itself when its gate is mechanical (the previous output exists and passes its checks). A person starts it when the gate is judgment. You see only the decisions.
- **Every pipeline starts from memory.** A first stage writes a one-page baseline from what the team already knows, including ideas already disproved. You write a one-line hypothesis before you read it.
- **Every pipeline ends in memory.** A last stage proposes its decisions and learnings back to the vault for your ✅, so the next piece of work starts ahead.
- **Designs stay buildable.** Agents build designs in the twin. A check confirms each design uses only services that exist in production.
- **One validation system.** Seats and pipeline stages share one report shape, so a change cannot ship with a broken contract or a removed safety rule.
- **One engine for many PMs.** A fix to the seat template or the checks reaches every PM's agents. Nobody needs the author to set them up.

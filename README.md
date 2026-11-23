# An Agentic Memory System That Shares Context Within A Team

**A shared memory for a product team that agents keep current, check and correct. People decide. Agents maintain.**

A product team's knowledge is spread across Slack, meetings, documents, tickets and people's heads. Every time you ask an AI agent for help, it starts from nothing, or from whatever you paste in. This framework gives that knowledge one home that the whole team shares. Scheduled agents feed it, file into it, check it against the original sources and fix what drifts. Every agent and every person starts from the same accurate picture.

You can run all of it by hand, one prompt at a time, and add agents one job at a time. Every job works both ways: [see the list](docs/roadmap.md#every-job-by-hand-or-by-agent).

> **This repo is the engine, not a vault.** It holds the scripts, rules, agent skills and agent templates. It holds no notes and no data. Setup builds the vaults (folders of plain Markdown notes) that the engine runs on.

## Why use it

| | What you get | Status |
|---|---|---|
| 1 | **Cheaper, sharper agents.** Agents read one small, current file instead of re-reading Slack, Drive and old threads every time. Answers cost less, arrive faster and come with a source. | Working today |
| 2 | **Context that maintains itself.** Agents on a schedule pull in what changed, propose updates in Slack for a ✅ or ❌, and flag what has gone stale. Your job shrinks to deciding. | Partly built |
| 3 | **One truth for the whole team.** The shared vault is a git repo. Everyone, and every agent, works from the same facts. Agents change it only through checked pull requests. Personal notes stay in a separate private vault. | Working today |
| 4 | **Projects become harnesses.** Each project holds its sources, decisions and current state. Agent work on that project starts from the right information and writes what it learns back. | Piloting |
| 5 | **Shared skills and pipelines.** The team shares one set of agent skills. Pipelines run discovery, write requirements and report experiments, stage by stage, from the project's own facts. | Planned |

## How it runs

```text
 ORIGINALS       Slack · meetings · Drive · Jira · Productboard · BI dashboards
     │   agents capture on a clock (no new input: no model run, no cost)
     ▼
 INBOX           raw input, kept and never deleted
     │   agents route each fact to its one home and propose the change
     ▼
 YOU             ✅ or ❌ in Slack, or in a review card in your agent
     │
     ▼
 KNOWLEDGE       one file per fact: project STATE, decisions, metrics, concepts
     │   pipelines read only what they need ─────────►  WORK: discovery, PRD, experiments
     │                                                      │  learnings promoted back,
     │   ◄──────────────────────────────────────────────────┘  for your ✅
     ▼
 QUALITY LOOP    scripts check structure daily; agents check facts against
                 their source weekly; fixes arrive as PRs; your "no" becomes a rule
```

It works in Obsidian, any editor and any agent that can read files. Every change is a diff you can read and revert. In the author's use, keeping project status current fell from 40+ minutes a day to 5–10.

## Quickstart (5 minutes)

Needs Python 3, Node and git.

1. Clone this repo.
2. Open the folder in Claude Code, or any agent that can read files and run commands.
3. Say **"set me up"**. The `setup` skill (`3_RESOURCES/AI Skills/setup/SKILL.md`) asks a few questions, builds your shared and private vaults in new folders, and runs lint.
4. Open the new shared vault and follow [docs/first-week.md](docs/first-week.md).

## Docs

| I want to | Read |
|---|---|
| Set up by hand, add search, upgrade the engine | [docs/setup.md](docs/setup.md) |
| Fill a new vault in its first week | [docs/first-week.md](docs/first-week.md) |
| Know the rules every skill and agent follows | [docs/doctrine.md](docs/doctrine.md) |
| Run scheduled agents (seats): tokens, clocks, evals | [docs/agents.md](docs/agents.md) |
| Build a new seat | [docs/build-a-seat.md](docs/build-a-seat.md) |
| See what each example seat does and its status | [examples/seats/README.md](examples/seats/README.md) |
| Change the engine or upstream a fix from a vault | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| See where it is going, and every job by hand or by agent | [docs/roadmap.md](docs/roadmap.md) |
| See what changed in each engine tag | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| Work in a vault as an agent | [AGENTS.md](AGENTS.md) |

## Limits

- Built and used by one person so far. A shared team vault is set up; use by a second PM is the next test.
- Seats run on one person's Mac today (launchd), and each needs its own secrets and Slack app. Where seats run for a team is still open.
- Project harnesses and pipelines are partly built or planned ([roadmap](docs/roadmap.md)).
- Skill text keeps its design history. Names of people, projects and systems were replaced with placeholders, so some examples read as generic.
- The scheduled lint job is macOS only. Skills assume an agent with file access and, for capture, a chat connector.

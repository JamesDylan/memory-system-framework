# 03. The laws

**Last Updated:** 2026-11-12 | **Type:** external reference (not {{ORG}} fact) | **Source:** see `README.md` in this folder

More work for the town means more ways for it to be wrong. Each law answers one specific danger.

The test for every answer: if the answer is "it is in the prompt", the answer is no.

## The six laws

| # | Danger | Law |
|---|---|---|
| 1 | An agent that can see customer data can leak it. | Isolated from production. One API in: read-only, no personal data. |
| 2 | An agent that can do everything will, eventually. | Each agent gets only the access its job needs. Builders get none. |
| 3 | A rule in a prompt is a suggestion. | Enforced in code, not only in the prompt. |
| 4 | An agent will ship what it should not. | People merge, release and send. Agents only draft. |
| 5 | Two agents can argue forever, and bill you for it. | Every loop has a ceiling. Past it, a person takes over. |
| 6 | Everything they read can talk back. | Treat them, and everything they read, as malicious. |

**The golden law.** Agents prepare the evidence. People stay responsible for the outcomes. "People" means product, design and engineering together.

## What each law means in practice

### Law 1. Isolated from production

- The agent has no production credentials and no database access.
- There is one door: an API that is read-only.
- Personal data is removed or masked before the agent sees it. Not after.
- Prototypes run in the twin on made-up data.

### Law 2. Least access

- List every tool and key each seat has. Remove what its job does not use.
- Agents that write code cannot message people and cannot read customer data.
- Access is per seat, not per town. The messenger reads Slack. The prototyper does not.

### Law 3. Enforced in code

- For every "never" in a brief, check whether a tool exists that would let the agent do it anyway. If so, remove the tool.
- Long sessions drift from their rules. Restart sessions before they get long enough to forget.
- Permissions live in the connector scope, the API key, the file system and the tool list. The prompt only explains them.

### Law 4. People merge, release and send

- Every output arrives as a draft: draft pull request, unassigned issue, unsent email, note in a drawer.
- Each kind of draft has a named person.
- This is the law that keeps the golden law true. A draft with no owner is abandoned work.

### Law 5. Every loop has a ceiling

- Set a maximum number of rounds for any review or retry.
- At the ceiling the seat waits for a person. It does not try something else.
- Work out the most this could cost in a bad week. Write the number down.

### Law 6. Treat everything as malicious

This is Simon Willison's lethal trifecta. An agent is dangerous when it has all three of:

1. Access to private data.
2. Exposure to untrusted content.
3. A way to send data out.

Any two is acceptable. All three is a breach waiting to happen.

Untrusted content is anything written by outsiders: support tickets, forum posts, web pages, inbound email, customer feedback, pull request text. A support ticket can contain instructions. An agent that reads it may follow them.

The practical design rule: for each seat, decide which leg it will not have.

| Seat type | Private data | Untrusted content | Way out | Safe |
|---|---|---|---|---|
| Messenger reading support tickets | Vault | Yes | No (writes to drawer only) | Yes |
| Chronicler reading internal Slack and PRs | Vault | Low | No | Yes |
| Marketing drafter | Strategy notes | No | Draft only, human sends | Yes |
| Agent that reads inbound email and can send email | Inbox | Yes | Yes | **No** |

## How Gas City applies the same idea

Gas City's trust model, which his town runs on, is a useful second reference:

- City config, packs and scripts are trusted operator code. Review them like shell scripts.
- Work item titles, descriptions, mail, variables and PR text are untrusted data. They are never joined into shell commands. They are passed as environment, JSON, stdin or arguments.
- The orchestrator strips secret-looking environment variables before running helper commands. A secret reaches a command only when config passes it on purpose.

The lesson for a smaller build: keep a hard line between instructions (what you wrote) and content (what the agent read). Content never becomes a command.

## Audit checklist

Run this for each seat before it goes on a clock. A blank copy is in the `templates` folder of this project (`laws-audit.md`).

**Law 1**
- Can it reach production data? Through what, exactly?
- Is that door read-only?
- Is personal data removed before the agent sees it?

**Law 2**
- What tools and keys does it have? Which does this job use?
- Can any code-writing agent message people or read customer data?

**Law 3**
- For each "never": is there a tool that would allow it anyway?
- Do long sessions restart?

**Law 4**
- Does everything arrive as a draft?
- Is there a named person for each kind of draft?

**Law 5**
- What is the retry or review ceiling?
- What happens at the ceiling?
- What is the worst-case weekly cost?

**Law 6**
- Does it read anything written by outsiders?
- Does it also have private data and a way to send things out?

**Golden law**
- Who is accountable for this seat's output? Write the name.

## Extra laws for a larger company

His town is six people at one small company. At an enterprise with a commercial partner, add these. They are my additions, not his.

1. **Data stays on approved infrastructure.** Company Slack, email and partner data do not leave company-approved tools. A personal server or device is outside that boundary.
2. **Partner data has its own rule.** Check what the partner agreement allows before any agent reads partner-shared material.
3. **Security and legal know.** A scheduled agent with read access to company systems is a new system. Get it reviewed once, early.
4. **The vault has an access model.** A shared vault read by agents and people needs the same permissions thinking as any other knowledge base.

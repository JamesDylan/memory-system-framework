# Laws audit template

Adapted from `starter/laws-checklist.md` in https://github.com/mariuscwium/pac26. One copy per seat. Complete before the seat goes on a clock.

If an answer is "it is in the prompt", the answer is no.

Seat: ____________  Date: ____________  Audited by: ____________

## Law 1. Isolated from production

| Question | Answer |
|---|---|
| Can it reach production data? Through what? | |
| Is that door read-only? | |
| Is personal data removed before the agent sees it? | |

## Law 2. Least access

| Question | Answer |
|---|---|
| Every tool and key it has | |
| Which of them this job uses | |
| Removed | |
| Can it message people or read customer data without needing to? | |

## Law 3. Enforced in code

| "Never" in the brief | Is there a tool that would allow it anyway? | Fix |
|---|---|---|
| | | |
| | | |

Do sessions restart each round? ____

## Law 4. People merge, release and send

| Output | Arrives as a draft? | Named person |
|---|---|---|
| | | |

## Law 5. Every loop has a ceiling

| Question | Answer |
|---|---|
| Maximum rounds for any retry or review | |
| What happens at the ceiling | |
| Worst-case cost in a bad week | |

## Law 6. Treat everything as malicious

| Leg | Yes or no | Detail |
|---|---|---|
| Reads content written by outsiders | | |
| Has access to private data | | |
| Has a way to send things out | | |

Three yeses is a fail. Remove one leg.

## Company additions

| Question | Answer |
|---|---|
| Does all data stay on approved infrastructure? | |
| Does it read partner-shared material? Is that allowed? | |
| Has security reviewed this class of agent? | |

## Golden law

Accountable person for this seat's output: ____________

Result: pass / fail. If fail, what changes: ____________

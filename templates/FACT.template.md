---
type: decision
claim: "[One sentence that is true or false. Name the subject.]"
source: "[Original document, meeting or message, its owner and date, with its link or ID. Add the vault file that holds the copy.]"
as_of: YYYY-MM-DD
verified: not yet
status: active
---

# [Short name of the claim]

[Optional. Why this is true, who said it, what it depends on. Two to five lines.]

<!--
Typed fact (PLAN S2.4). One file per fact in <Initiative>/facts/<type>-<slug>.md.
Lint check 11 reads the frontmatter. Rules are in .scripts/lint.config.json "facts".

type      decision | constraint | open-question
status    decision: active | superseded
          constraint: active | retired
          open-question: open | answered | dropped
claim     The fact itself. For an open question, the question.
source    Where the claim comes from. Quote the original, not a summary of it.
as_of     The date the source states the claim (not the date you wrote this file).
verified  A date only when the fact is verified, else "not yet".
          Verified means a person checked, or a source can be pointed to directly
          (i.e. a metric, Slack message, Google Doc) that states the fact or confirms
          it correct. ({{OWNER}}, 2026-11-22.)
          Pointable: a Slack permalink, a Google Doc/Drive link with its section, a
          metric (metric:<registry id> or a dashboard link), a Jira or Productboard
          item. Put that link or ID in source. For a person check, write
          "Checked by <Name>, <date>" in source.
          Not enough: a vault summary, LOG prose, meeting notes with no link, or an
          agent's reading. A copy in <Initiative>/sources/ counts only when it names
          its original link and the original states the claim.
          Lint flags a dated verified whose source has no link, ID or "Checked by".
          A live fact (active, open) is flagged when verified is older than:
          decision 180 days, constraint 90 days, open-question 30 days.

To close a fact, change status. Do not delete the file. When a decision replaces
another, set the old one to superseded and name the new file in its body.
When an open question is answered, set it to answered and add a decision fact.
-->

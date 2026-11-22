# Mail note template

One file per round. Five lines of content at most. Path: `mail/<recipient>/<YYYY-MM-DD>-<HHMM>-<seat>.md`. Move to `mail/read/` when processed.

```markdown
---
from: [seat]
to: [mayor | owner]
date: [YYYY-MM-DD HH:MM]
round: [ran | nothing new | failed]
---
Changed: [what changed, with link]
Decide: [what needs a person, by when] | none
Blocked: [what could not be done, and why] | none
```

## Rules

- "Nothing new" is a valid note. One line.
- A decision line states the decision, not the background.
- A blocked line names the cause: credit, connector, permission, unclear input.
- No note means the seat did not run. Silence is a failure signal.

## Example

```markdown
---
from: chronicler
to: owner
date: 2026-11-17 08:31
round: ran
---
Changed: STATE.md updated for I2. Two items moved to live. [links]
Decide: Risk is amber on the auth dependency. Confirm or change by Thursday.
Blocked: Could not read the wiki page. Permission denied.
```

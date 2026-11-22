# How to use the metrics registry

Plain instructions. Only needed if you plan to update it by hand. 

---

## The idea, in three sentences

**One file holds every number.** That is `registry.yaml`.

**Every other document quotes those numbers, with a small tag attached** so the quote
can be traced back:  `19.2% <!--m:churn.company.annual-->`

**A script checks the quotes still match the registry** and tells you which file and
line to fix. It never edits your documents. It only tells you.

That is the whole system. Everything below is detail.

---

# PART 1 — Setup (about 15 minutes, once)

### Step 1. Install the one dependency

```bash
pip3 install pyyaml
```

### Step 2. Make it one word to run

```bash
# run from the vault root: $PWD is filled in when you run echo
echo "alias metrics='python3 $PWD/2_AREAS/{{ORG}}/_metrics/check_metrics.py --root $PWD'" >> ~/.zshrc
source ~/.zshrc
```

Now `metrics` runs the checker from anywhere.

### Step 3. Run it and look at the output

```bash
metrics
```

You will see a small handful of errors and more warnings. **This is expected** — it is the
backlog of existing problems, not something you broke. Do not try to fix them yet.

**Today is done.**

---

# PART 2 — Initial Review (about an hour, once)

Work through the backlog. You do not have to do it in one sitting, and nothing breaks
if you leave it.

Run `metrics` and you will see three kinds of line. Here is what each means and what
to do.

### Kind 1: `ERROR [forbidden]` — text that should no longer exist

```
context/strategic_context.md
   202  ERROR  [forbidden] superseded text "Monthly Signups"
        ↳ This figure is WEEKLY.
```

**What to do:** open that file at that line and fix the label.

```diff
- | Monthly Signups | ~7,000 |
+ | Registered companies per week | ~11,200 <!--m:acq.registered_companies.weekly_4wk--> |
```

Two changes: the *label* is now correct, and the *number* carries a tag. Once tagged,
any future change to the registry will point straight back here.

### Kind 2: `warn [untagged]` — a correct number with no tag

```
   97  warn  [untagged] untagged copy of churn.company.annual: "19.2%"
        ↳ add a marker:  19.2% <!--m:churn.company.annual-->
```

**What to do:** paste the marker in, exactly as shown, right after the number.

```diff
- | **Annual** Churn Rate | 19.2% | 19.2% (CY26 plan) |
+ | **Annual** Churn Rate | 19.2% <!--m:churn.company.annual--> | 19.2% (CY26 plan) |
```

The rendered document looks identical — HTML comments do not display in Obsidian
preview. You are only adding a trail.

### Kind 3: `ERROR [assertion]` — numbers that cannot all be true

```
registry.yaml
    -  ERROR [assertion] users_per_org_consistency: Average users per org (1.2) is
       arithmetically impossible alongside 15% of orgs having 3+ users...
```

**What to do:** this one is not a text fix — it is a question for DSA. Leave it firing
until it is answered. A permanently visible open question is the point.

### Where to start

```bash
metrics --quiet | grep ERROR
```

Errors first, warnings later. The warnings are safe to leave for weeks.

---

# PART 3 — Every week (about 5 minutes)

**This is the ongoing job. It is the only thing you must actually maintain.**

When the weekly PowerBI report lands, feed in the numbers that moved.

### Which report row maps to which id

| Weekly report row                    | Registry id                            |
| ------------------------------------ | -------------------------------------- |
| Registered Companies                 | `acq.registered_companies.weekly`      |
| Registered Companies (4-week avg)    | `acq.registered_companies.weekly_4wk`  |
| Registration Conversion Rate         | `acq.marketing_site_conversion`        |
| Newly Activated Companies            | `act.newly_activated_companies.weekly` |
| Reactivated Companies                | `act.reactivated_companies.weekly`     |
| Gross Bookings – Business            | `book.gross_bookings_business.weekly`  |
| Visiting Users                       | `book.visiting_users.weekly`           |
| Stay Search Booker Conversion Rate   | `conv.stay_search_booker`              |
| Users That End Visiting {{PARTNER}}         | `book.users_end_visiting_partner.weekly`  |
| Booking Companies                    | `comp.booking_companies.weekly`        |
| Retained Companies                   | `comp.retained_companies.weekly`       |
| Purchase Frequency                   | `book.purchase_frequency`              |
| Deregistered Companies               | `churn.deregistered_companies.weekly`  |
| Churned Companies                    | `churn.companies.weekly`               |
| Sticky Companies – Example Project | `deepen.sticky_companies_corporate`    |

### The command

`--set` can be repeated, so the whole week's update is one command, not one per
metric — and the checker now runs automatically straight after, so there's no
separate second step either:

```bash
metrics --asof 2026-09-04 --note "w/e 4 Sep PowerBI" \
  --set acq.registered_companies.weekly=1200 \
  --set act.newly_activated_companies.weekly=340 \
  --set churn.companies.weekly=90 \
  --set book.gross_bookings_business.weekly=5000
```

Only include the rows that actually moved. `--asof` and `--note` apply to every
`--set` in that command. Output shows what changed, then lists every document
containing a stale copy of any of those numbers. Fix those. Done.

Add `--no-check` if you just want to update the registry without running the
check straight after.

### Easiest: paste the report and let Claude do the mapping

You don't have to build that command by hand. Paste the weekly PowerBI table into
a chat with Claude Code in this vault and say "update the metrics" — Claude reads
the row → id table above, builds the `--set` flags itself, runs the command, and
tells you what's left to fix in prose. That's the whole weekly job.

### What happens automatically

- `as_of` is stamped, so staleness tracking stays honest
- The old value is appended to `_metrics/history.csv`, so you have a trail
- Nothing else in the registry is touched

### You can also just edit the file

`--set` is a convenience. Opening `registry.yaml` and changing `value:` and `as_of:`
by hand does exactly the same thing, minus the history entry.

---

# PART 4 — How document writing changes

Barely. Three small habits.

### Habit 1: look the number up in the registry, not in another document

Copying from another doc is how a stale number gets a second life. `metrics --list`
prints everything on one screen.

### Habit 2: put the tag in when you write the number

```markdown
Annual company churn is 19.2% <!--m:churn.company.annual--> and worsening.
```

If you forget, the checker will catch it and hand you the exact string to paste.

### Habit 3: use the registry's full name

The registry `name` field already contains the period and the denominator. Use it.

| Instead of | Write |
|---|---|
| "activation rate" | "28-day company activation rate" |
| "churn" | "annual company churn rate" |
| "conversion" | "stay search to booker conversion" |
| "signups" | "registered companies per week" |

This one rule would have prevented nine of the twenty-three problems we found.

### What does not change

You still write numbers inline. You still write prose normally. You do not have to
tag every number in the vault — only ones that exist in the registry, and only as you
touch each file.

---

# PART 5 — When you need a metric that isn't there

Open `registry.yaml` and copy any existing entry as a template:

```yaml
  - id: act.invite_acceptance_rate          # dot-separated, lowercase
    name: Team invite acceptance rate       # must state period + denominator
    value: 34
    unit: percent
    period: point                           # weekly | monthly | annual | daily | point
    denominator: invites sent               # WHO or WHAT is being divided by
    altitude: user                          # user | company | cohort | booking
    as_of: 2026-09-04
    source: Weekly PowerBI report — Activation
    owner: PM B
    status: ok                              # ok | provisional | disputed | superseded | stale
    note: "Anything a future reader needs to not misuse this."
```

Then run `metrics`. If you left a required field blank it will say so.

**Optional extras**, worth adding when a number has a history:

```yaml
    aliases:                     # strings to hunt for untagged copies of
      - {pattern: "34%", near: "invite|acceptance"}
    forbidden:                   # text that should never appear again
      - {pattern: "invite conversion", why: "Renamed — it measured a different step."}
```

The `near:` part matters for short values like `34%` — without it you get false hits
everywhere.

---

# PART 6 — When it gets noisy

### A history table is being flagged

Sections titled *Update History*, *Changelog*, *Change Log* or *Revision History* are
skipped already. For anything else:

```markdown
<!--metrics-ignore-->                                  skips this one line
<!--metrics-ignore-start-->  ...  <!--metrics-ignore-end-->    skips a block
```

### Too many staleness warnings

Either re-confirm the number, or set `status: stale` so you have acknowledged it.
If the window is too tight, change `stale_after_days` in the config block at the top
of `registry.yaml`.

### An alias is firing everywhere

Its pattern is too loose. Add or tighten `near:`.

### You want to skip a whole folder

Add it to `exclude_globs` in the config block.

---

# PART 7 — Cheat sheet

```bash
metrics                              # check everything
metrics --quiet | grep ERROR         # just the errors
metrics --list                       # every metric on one screen
metrics --list --status disputed     # the open conflicts — your October worklist
metrics --set <id>=<value>           # update one number, then auto-runs the check
metrics --set <id1>=<v1> --set <id2>=<v2> --asof 2026-09-04 --note "why"   # weekly batch
metrics --set <id>=<value> --no-check                                     # skip the auto-check
```

Tag format, always the same:

```
<number> <!--m:<id>-->
```

---

# What to expect over time

| When | Effort | What you get |
|---|---|---|
| Today | 15 min | Installed, protocol loaded into chat context |
| This week | ~1 hour | Backlog cleared, existing copies tagged |
| Each week | 5 min | Registry current, drift listed automatically |
| Each month | 10 min | `--list --status stale` reviewed |
| Each quarter | 20 min | `disputed` entries pushed to resolution |

**Nothing breaks if you skip a week.** The checker is a mirror, not a gate. It tells
you what is out of date whenever you next ask it.

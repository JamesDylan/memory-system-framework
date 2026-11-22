# Metrics Protocol

> Paste this section into `3_RESOURCES/{{ORG}}/{{PRODUCT_LOWER}}-context.md` so every chat session
> loads it. It is short on purpose — a protocol nobody reads is not a protocol.

---

## The one rule

**Never write a new metric value into a document. Update the registry.**

The registry is `2_AREAS/{{ORG}}/_metrics/registry.yaml`. It is the only file where a
number is allowed to change. Everything else carries *marked copies* that a script
verifies.

**One writer for registry values: the weekly PowerBI update.** Other agents (for
example experiment-reporter) do not write `registry.yaml`. They propose new values in
their note, and the weekly update applies them. `registry.yaml` cannot merge two
writers' edits safely; `history.csv` can (union merge in `.gitattributes`).

```
19.2% <!--m:churn.company.annual-->
```

A human reads `19.2%`. The checker reads the marker. Nothing else changes.

---

## If you are given a new number

Run these from the vault root (`{{SHARED_VAULT_PATH}}`), using `/usr/bin/python3` —
not bare `python3`, which on this machine has no PyYAML and can't install it (Homebrew's
Python blocks `pip install` under PEP 668).

1. Update the registry — by hand, or with `--set` (repeatable, so a whole week's
   changes are one command):
   ```bash
   /usr/bin/python3 2_AREAS/{{ORG}}/_metrics/check_metrics.py --root . \
     --set churn.company.annual=18.4 --note "Sept DSA refresh"
   ```
   This stamps `as_of`, appends the old value to `_metrics/history.csv`, and then
   runs the full check automatically — no separate step 2 needed.

2. Fix every file and line it lists. **This is the step that has been skipped every
   time so far** — the July 2026 churn correction updated the canonical file and left
   four stale copies elsewhere, which is why it did not hold.

You never have to search the vault. The checker searches it for you, against a fixed
set of ~40 known values, in about a second.

---

## If you are writing a document that cites a metric

- Look the value up in the registry. Do not copy it from another document — that is
  how a stale number gets a second life.
- **Never write a bare number.** Link to the metric, or put `<!--m:id-->` (the
  registry id) after the number. This applies to STATE files and insights too. A
  bare copy is not checked, so it goes wrong without warning when the registry changes.
- Use the registry's `name` field, which already carries the period and denominator.
  Write "28-day company activation rate (cohort)", not "activation rate".

---

## Naming rule

**Every metric name states its period and its denominator.** Nine of the twenty-three
contradictions found in August 2026 disappear under this rule alone.

| Don't | Do |
|---|---|
| Monthly Signups | Registered companies per week |
| Activation rate | 28-day company activation rate (cohort) |
| Churn | Annual company churn rate |
| Conversion | Stay search to booker conversion rate |
| Newly activated | Newly activated companies per week (flow) |

The distinction that keeps biting us: a **cohort** rate follows one registration week
forward. A **flow** count sums everyone who crossed the line this week regardless of
when they registered. They are different numbers and neither is wrong.

---

## Status values

| Status | Meaning |
|---|---|
| `ok` | Current and trusted |
| `provisional` | Single unverified source — do not use externally |
| `disputed` | Conflicts with another figure; the conflict is documented in `note` |
| `superseded` | Kept so the checker can flag it wherever it still appears |
| `stale` | Needs re-confirmation |

Mark a metric `disputed` rather than quietly picking a side. The dispute is the
information — `churn.company.annual` has been disputed since June and stating that
is more useful than publishing a number nobody can defend.

---

## What the checker will not catch

- Copies of values that are **not in the registry**. Add metrics as they appear.
- **Definition collisions** — one word covering two things. The registry makes them
  visible (two entries, two denominators) but cannot resolve them for you.
- **Wrong numbers that are internally consistent.** Assertions catch a few of these;
  judgement catches the rest.

---

## Escapes

History tables legitimately record superseded values. Sections titled *Update History*,
*Changelog*, *Change Log* or *Revision History* are skipped automatically. For anything
else:

```
<!--metrics-ignore-->                 skip this line
<!--metrics-ignore-start-->  ...  <!--metrics-ignore-end-->
```

---

## Monthly rhythm

| When | What |
|---|---|
| Weekly report lands | `--set` the handful that moved, run the checker, fix what it lists |
| Monthly | `--list --status stale` and re-confirm or retire |
| Before any external doc | Run the checker; do not ship with errors outstanding |
| Quarterly | Review `disputed` entries — an unresolved dispute over two quarters is a decision nobody is making |

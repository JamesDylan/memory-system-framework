# {{PRODUCT}} metrics registry

Three files that keep one number true across the whole vault.

```
_metrics/
  registry.yaml       # single source of truth — the only file where values change
  check_metrics.py    # verifier: drift, untagged copies, superseded text, staleness, assertions
  history.csv         # append-only log, written by --set
  METRICS_PROTOCOL.md # the rules, for pasting into {{PRODUCT_LOWER}}-context.md
```

## Install

```bash
mkdir -p {{SHARED_VAULT_PATH}}/2_AREAS/{{ORG}}/_metrics
cp registry.yaml check_metrics.py METRICS_PROTOCOL.md \
   {{SHARED_VAULT_PATH}}/2_AREAS/{{ORG}}/_metrics/
pip3 install pyyaml          # only dependency
```

Run it from the vault root:

```bash
cd {{SHARED_VAULT_PATH}}
python3 2_AREAS/{{ORG}}/_metrics/check_metrics.py --root .
```

Add an alias so it is one word:

```bash
echo "alias metrics='python3 {{SHARED_VAULT_PATH}}/2_AREAS/{{ORG}}/_metrics/check_metrics.py --root {{SHARED_VAULT_PATH}}'" >> ~/.zshrc
```

## The weekly loop

`--set` repeats, and the checker now runs automatically right after — one command
for the whole week, not one per metric plus a separate check:

```bash
metrics --asof 2026-09-04 --note "w/e 4 Sep" \
  --set acq.registered_companies.weekly=1200 \
  --set churn.companies.weekly=90
```

Output lists every file:line that now disagrees. Fix what it lists. That is the
whole workflow. (Or just paste the PowerBI table into a Claude Code chat in this
vault — it builds the command and runs it for you; see HOW_TO_USE.md Part 3.)

## Other commands

```bash
metrics --list                      # every metric, value, period, status, as_of
metrics --list --status disputed    # the ones with an open conflict
metrics --json                      # machine-readable, for a git hook or CI
```

Exit code is 1 when errors exist, so it drops straight into a pre-commit hook:

```bash
# .git/hooks/pre-commit
python3 2_AREAS/{{ORG}}/_metrics/check_metrics.py --root . --quiet || {
  echo "metric drift — fix or use <!--metrics-ignore-->"; exit 1; }
```

## Checks it runs

| Check | Catches |
|---|---|
| `drift` | A marked copy whose value no longer matches the registry |
| `period` | A monthly/annual/weekly word next to a value of a different period |
| `untagged` | An unmarked copy of a known value, found by scanning for the value itself |
| `forbidden` | Superseded text that should no longer appear anywhere |
| `magnitude` | Same digits, different order of magnitude — a k/M mix-up |
| `stale` | A metric not re-confirmed inside the staleness window |
| `assertion` | Numbers that are individually plausible but cannot all be true |
| `schema` | A metric missing its period, denominator or altitude |

## Seeded state

39 metrics, covering the four flywheel gears, the switcher cohort, plan targets and
the partnership-facing value stats. Seven are marked `disputed` and carry the conflict
in their `note` — those are the ones to resolve before October.

Five assertions are live. One currently fails: average users per organisation (1.2)
is arithmetically impossible alongside 15% of organisations having 3+ users. That is
not a bug in the checker.

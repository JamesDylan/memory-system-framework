# Contributing to the engine

How to change the engine, and how a change made in a vault gets back here. The rules the engine enforces are in [doctrine.md](doctrine.md).

## What the engine owns

`engine-files.json` lists every file the engine owns. `init-vault.py` installs them into a vault, engine.lock records a hash of each, and `engine-upgrade.py` replaces them on upgrade. Every other file in a vault is the vault's own, and an upgrade never touches it.

| Part | Files | Does |
|---|---|---|
| Lint, mechanical | `.scripts/lint.mjs`, `.scripts/lint.config.json` | Dead pointers, staleness, missing stamps, orphan skills, inbox age, index drift, deployed-skill drift, run integrity, STATE budgets, private boundary, engine drift. No model |
| Lint, scheduled | `.scripts/daily-pull.sh` (installs one launchd job) | Daily pull, then lint, with a notification on must-fix findings (macOS) |
| Lint, CI | `.github/workflows/lint.yml`, `.scripts/scorecard.mjs`, `.scripts/health.mjs` | Lint on each PR; weekly health row, optional agent fix PR and Slack digest. Each part is skipped until its secret is set |
| Lint, judgment | `3_RESOURCES/AI Skills/lint/` | Conflicts and semantic staleness. Needs an agent |
| Search | `.scripts/qmd-bootstrap.sh`, `templates/qmd-index.template.yml` | Local hybrid search with qmd, one collection per vault |
| Metrics | `_metrics/` | A registry of typed metric values with a checker. One place a number may change |
| Skills | `3_RESOURCES/AI Skills/` (capture: `daily-slack-review`; route: `ingest`, `diff-propose`; think: `second-brain`, `challenge`, `emerge`, `connect`, `review-prep`; run: `setup`, `lint`, `memory-system-upgrade`), and `private/` (`watch`, `calibrate`, `debloat`, installed into the private vault and not in engine.lock yet, so upgraded by hand) | What agents do in a vault |
| Seats | `examples/seats/`, `templates/seat/`, `templates/seat-brief.md`, `templates/laws-audit.md`, `.scripts/new-seat.py`, `.scripts/run_evals.py` | Example scheduled agents, the seat template and the eval runner |
| Install and upgrade | `engine-files.json`, `.scripts/engine-upgrade.py`; `init-vault.py` stays in the engine checkout and is not copied into a vault | Build vaults, record the lock, upgrade |
| Publish | `.scripts/export-framework.py` | Export the engine from a vault with no organisation data |
| Docs | `README.md`, `AGENTS.md`, `docs/` | This file among them. The engine changelog is `docs/CHANGELOG.md`, because a vault's root CHANGELOG.md is its own |

## What the vault owns (the org layer)

- **Lint settings:** `.scripts/lint.config.org.json`, merged over the engine's `lint.config.json` (how the merge works: the `_comment` in `templates/lint.config.org.template.json`).
- **Seats:** the seats a vault runs live in `2_AREAS/Agents/`, copied from `examples/seats/` or made with `new-seat.py`.
- **Org-only skills:** a skill only your organisation uses lives in the vault, outside the engine's skill list.
- **Content:** everything in the PARA folders, `memory_index.md`, the vault's CHANGELOG.md, ORG.md, and the private vault.

If lint check `engine-drift` reports an engine file you changed in a vault, the change belongs either here (upstream it) or in the org layer (move it).

## Upstream a change from a vault

1. Make the change in a checkout of this repo, on a branch, not only in your vault. Engine files hold organisation placeholders (the keys in `ORG_KEYS` in `init-vault.py`, each written in double braces), never your organisation's values. They should not hold person placeholders (an owner's name or user ID): those are never filled in engine files. Some examples and scripts still do (known debt); don't add more.
2. Run the organisation-terms check (below) and the self-tests.
3. Add a line for your change under **Unreleased** in `docs/CHANGELOG.md`, then open a pull request on this repo. CI must pass.
4. After merge, the maintainer tags a release.
5. In the vault: `python3 .scripts/engine-upgrade.py <tag>` ([setup.md](setup.md#upgrade-the-engine)). Your local edit now matches upstream, so the drift report clears.

## The organisation-terms check

Before any push to this repo, scan every changed file for your organisation's own terms: company, product, partner, customer, people and system names. Match on word boundaries, so a short term does not hit inside another word. Any hit blocks the push: replace it with a placeholder or plain words.

For example, with your organisation's term file (one term per line) kept outside this repo:

```bash
git diff --name-only origin/main | xargs grep -n -i -w -F -f ~/path/to/org-terms.txt   # any output blocks the push
```

Your organisation keeps its term list outside this repo. Never commit the list here, not even in a test: the list itself names the organisation.

## Tags and upgrades

A vault installs from a tag and upgrades from tag to tag. Each tag gets a section in `docs/CHANGELOG.md` that says what a vault gains and anything it must do by hand. A new engine file must be covered by `engine-files.json`, or upgrades will not ship it.

## Self-tests

Every script has `--selftest`. It writes only to temp folders, needs no network and no secrets, and exits 0 when all is well. A new script gets one, and CI runs it.

```bash
python3 init-vault.py --selftest        # builds a fresh vault from the example answers and lints it
node .scripts/lint.mjs --selftest
python3 .scripts/engine-upgrade.py --selftest
python3 .scripts/new-seat.py --selftest
python3 .scripts/run_evals.py --selftest
```

The full list CI runs is in `.github/workflows/lint.yml`.

## CI

`.github/workflows/lint.yml` runs on every pull request:

- **lint:** runs lint on the pull request and on its base with the same rules, and fails only on a must-fix finding the pull request adds. The old backlog does not block it.
- **fresh-vault:** builds a vault from `templates/answers.example.json` (`init-vault.py --selftest`, 0 must-fix), runs every engine self-test, and makes a seat with `new-seat.py` in that fresh vault.

A `weekly` job (Monday, or by hand; each part is skipped until its secret is set) appends a health row, drafts a fix pull request and posts a digest.

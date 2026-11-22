# Engine changelog

Changes to the engine, by tag. A vault's own changes go in its root CHANGELOG.md; this file is the engine's, and `engine-upgrade.py` brings it along.

## v0.1.0 — 2026-11-23

The first tagged engine. A vault can now be installed from a tag, know which engine files it has changed, and upgrade.

- **Install leaves nothing broken.** A fresh vault from the example answers lints with 0 must-fix. Every file the index, skills and lint point at exists as a stub ending `> Not filled in yet.` (#7).
- **"Not filled in yet" lint section.** Starter text, stubs and unfilled ME/ORG fields are listed as what to do first, not as errors (#8).
- **Organisation and person values split.** Engine files carry only organisation placeholders, filled at install. Person and instance values live in `_private/ME.md` and content templates (#5).
- **Lint config layering.** The engine owns `.scripts/lint.config.json`; each vault's own settings go in `.scripts/lint.config.org.json`, merged over it (#9).
- **Seats are examples.** Seats live in `examples/seats/`; copy one into `2_AREAS/Agents/` to run it. `.scripts/run_evals.py` finds seats by folder and reads `SERVERS=` and `RUNNER=` from each `seat.conf` (#6, #11).
- **engine.lock and upgrades.** `init-vault.py` writes `engine.lock`; `.scripts/engine-upgrade.py <tag>` upgrades engine files you have not changed and never overwrites your edits or files; lint Check 14 `engine-drift` shows what differs (#10, #12).
- **CI builds a fresh vault** on every pull request and runs every engine self-test.
- MIT licence (#1). Self-tests write to temp folders (#2).

Known gaps: engine files installed into the private vault are not in the lock yet (upgrade them by hand). The `notes` eval runner still pins a commit from the vault it came from.

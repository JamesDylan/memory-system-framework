# Set up

How to build your vaults from this engine, turn on search, and upgrade the engine later. Commands run from the engine checkout unless a step says "in the vault".

Needs Python 3, Node and git. Search is optional and needs qmd (`npm install -g @tobilu/qmd`).

## Guided: say "set me up"

Open the engine checkout in Claude Code (or any agent that can read files and run commands) and say **"set me up"**. The `setup` skill (`3_RESOURCES/AI Skills/setup/SKILL.md`) asks a few questions, shows you every value for approval, writes the answers file outside the checkout, builds both vaults and runs lint. It ends with the list of files still to fill in.

## By hand

```bash
cp templates/answers.example.json ../answers.json   # edit it; keep it out of any repo
python3 init-vault.py ../answers.json
```

The answers file holds:

| Key | What | Needed |
|---|---|---|
| `ORG`, `PRODUCT` | Company and product short names, as you want them in folder names | Yes |
| `OWNER_NAME` | Your full name. `OWNER` (short name) defaults to its first word | Yes |
| `SHARED_VAULT_PATH`, `PRIVATE_VAULT_PATH` | Two new or empty folders | Yes |
| `PRODUCT_LONG`, `PARTNER`, `ROLE`, `MANAGER` | Full product name, a partner company, your role and manager | No |
| `OWNER_SLACK_ID`, `SLACK_WORKSPACE` | Your Slack user ID and workspace (the part before `.slack.com`) | No |
| `USER_ID` | Your login name. Defaults to the current user. Only some example seat briefs use it | No |
| `PILOT_INITIATIVE`, `PILOT`, `SECOND_PILOT` | Your main initiative. Defaults to an example folder you can rename | No |

A key you leave out is written as `(set KEY)`, and lint lists it under "Not filled in yet". Three have defaults instead: `OWNER` (first word of your name), `USER_ID` (your login) and `PILOT_INITIATIVE` ("Example Initiative").

`init-vault.py` replaces every `{{PLACEHOLDER}}` (engine files get organisation values only), builds both vaults, creates the `_private` symlink and its `.gitignore` entry, and writes engine.lock at the shared vault root. It refuses a folder that already has content. Then, in the vault:

```bash
git init
node .scripts/lint.mjs          # 0 must-fix; the "Not filled in yet" list is your to-do list
```

Copy the skills you use to your agent's skills folder, or point it at `3_RESOURCES/AI Skills/`.

## What you get: two vaults

```text
memory_system/            shared vault: a git repo your team can read
  1_PROJECTS/<Org>/       one folder per initiative: BRIEF, STATE, LOG
  2_AREAS/<Org>/          ongoing context: strategy, people, metrics
  3_RESOURCES/            concepts, processes, and the AI Skills (engine)
  4_ARCHIVE/              finished work and source documents
  _private/  ->           link to the private vault below

memory_private/           private vault: your machine only
  0_INBOX/                every raw input lands here first
  1_PROJECTS/Actions/     your own to-dos
  2_AREAS/                your team, your career
  3_RESOURCES/AI Skills/  skills that touch private data
  4_ARCHIVE/
```

| Layer | Holds | Where |
|---|---|---|
| Engine | Scripts, lint, search config, skills, schemas | This repo, copied into the shared vault |
| Organisation | Company context, project status, concepts, processes | Shared vault. A git repo your team can read |
| Private | People and coaching notes, career, inbox, raw captures, your own actions | Private vault. Your machine only |

The private vault is mounted inside the shared vault as `_private/`, a gitignored symlink. All paths in docs and skills are relative to the shared vault, so a private path starts with `_private/`. Which fact goes where: [doctrine](doctrine.md), "Route by whose fact it is".

Per-person values (your chat user ID, direct reports, watch list) live in the private ME.md. Organisation values live in ORG.md. Skills read them.

`watch`, `calibrate` and `debloat` ship in `private/` and install into the private vault's `3_RESOURCES/AI Skills/`, because they read or write private data.

## Search (qmd)

In the vault (the script needs zsh, the macOS default shell):

```bash
.scripts/qmd-bootstrap.sh
```

It builds one qmd collection per vault (`memory_system`, and `memory_private` when the private vault sits beside the shared one as `../memory_private`), a separate `seats` index with the shared vault only for scheduled agents, and git hooks that re-index after every pull. The first run downloads about 1 GB of local models. It is safe to re-run. Without qmd, agents fall back to `memory_index.md` and grep.

## What to do first

Read [first-week.md](first-week.md): what to paste in first, in what order, and where it lands.

## Upgrade the engine

`engine-files.json` lists the files the engine owns. Everything else in a vault is the vault's own. engine.lock (in the vault) records the engine tag, the organisation values and a hash of each engine file as installed. An engine file you changed in the vault shows up in lint check `engine-drift`: [CONTRIBUTING.md](CONTRIBUTING.md) says where that change belongs.

In the vault, from a clean git tree:

```bash
python3 .scripts/engine-upgrade.py <tag>   # --repo <url-or-path> if the lock has none
```

It installs the tag in a temp folder with your organisation values, then updates each engine file you have not changed. A file you changed stays as it is: if the engine changed it too, the new version is written beside it as `<file>.upstream` for you to merge. New engine files are added. Removed ones are listed, not deleted. An engine file you deleted stays deleted, and the lock records that. If a new engine file would land on a file of your own, yours is left alone and listed as a name clash to rename. It rewrites engine.lock and never commits: review the diff, run lint, commit on a branch.

A vault set up before engine.lock: `python3 .scripts/engine-upgrade.py --adopt <tag> --values answers.json` writes a first lock for that tag and lists every engine file that differs from it. Private-vault engine files (`private/` here) are not in the lock yet: upgrade those by hand.

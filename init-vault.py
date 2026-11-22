#!/usr/bin/env python3
"""Turn this framework checkout into a working pair of vaults.

Usage:  python3 init-vault.py answers.json

Reads the answers, replaces every {{PLACEHOLDER}} in file contents and file
names, then builds the shared vault (this engine plus a PARA skeleton) and the
private vault, and mounts the private vault in the shared one as _private/.
Run it once, from the framework folder. It refuses to write into a folder that
already has content.
"""
import datetime, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {".git", "node_modules"}
TEXT_EXT = (".md", ".json", ".yml", ".yaml", ".py", ".mjs", ".sh", ".plist", ".base", ".txt", ".canvas", ".js", ".toml")
# template -> destination, relative to the shared vault ("P:" = private vault)
PLACE = [
    ("templates/memory_index.template.md", "memory_index.md"),
    ("templates/CHANGELOG.template.md", "CHANGELOG.md"),
    ("templates/ACTIVE_CYCLE.template.md", "1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md"),
    ("templates/slack-channels.template.md", "3_RESOURCES/{{ORG}}/{{ORG}} Slack Channels.md"),
    ("templates/metrics-registry.template.yaml", "2_AREAS/{{ORG}}/_metrics/registry.yaml"),
    ("templates/qmd-index.template.yml", ".scripts/qmd/index.yml"),
    ("templates/qmd-collection.template.yml", "P:qmd-collection.yml"),
    ("ORG.template.md", "ORG.md"),
    ("ME.template.md", "P:ME.md"),
    ("0_INBOX/README.md", "P:0_INBOX/README.md"),
    ("templates/private-AGENTS.template.md", "P:AGENTS.md"),
]
MOVE_DIRS = [("_metrics", "2_AREAS/{{ORG}}/_metrics"), ("private/3_RESOURCES/AI Skills", "P:3_RESOURCES/AI Skills")]
SHARED_DIRS = ["1_PROJECTS/{{ORG}}", "1_PROJECTS/Actions", "2_AREAS/{{ORG}}/context", "2_AREAS/{{ORG}}/people", "2_AREAS/{{ORG}}/_H2 Roadmap",
               "3_RESOURCES/{{ORG}}/concepts", "3_RESOURCES/processes", "4_ARCHIVE/sources", "4_ARCHIVE/projects"]
PRIVATE_DIRS = ["0_INBOX", "1_PROJECTS/Actions", "2_AREAS/{{ORG}}/My Team", "2_AREAS/Career", "3_RESOURCES", "4_ARCHIVE/sources/slack"]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    a = json.load(open(sys.argv[1], encoding="utf-8"))
    for k in ("ORG", "PRODUCT", "OWNER_NAME", "SHARED_VAULT_PATH", "PRIVATE_VAULT_PATH"):
        if not a.get(k):
            sys.exit(f"answers file is missing {k}")
    a.setdefault("OWNER", a["OWNER_NAME"].split()[0])
    a.setdefault("USER_ID", re.sub(r"\W", "", a["OWNER_NAME"]).lower())
    a.setdefault("HOME", os.path.expanduser("~"))
    a.setdefault("ORG_LOWER", a["ORG"].lower())
    a.setdefault("PRODUCT_LOWER", a["PRODUCT"].lower())
    a.setdefault("TODAY", datetime.date.today().isoformat())
    for k in ("PRODUCT_LONG", "PARTNER", "OWNER_SLACK_ID", "SLACK_WORKSPACE", "PILOT_INITIATIVE", "PILOT", "SECOND_PILOT"):
        a.setdefault(k, f"(set {k})")
    shared = os.path.abspath(os.path.expanduser(a["SHARED_VAULT_PATH"]))
    private = os.path.abspath(os.path.expanduser(a["PRIVATE_VAULT_PATH"]))
    a["SHARED_VAULT_PATH"], a["PRIVATE_VAULT_PATH"] = shared, private
    for d in (shared, private):
        if os.path.isdir(d) and os.listdir(d):
            sys.exit(f"{d} is not empty. Choose an empty or new folder.")
    fill = lambda s: re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: str(a.get(m.group(1), m.group(0))), s)

    # 1. copy the engine into the shared vault, filling names and contents
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            src = os.path.join(root, f)
            rel = os.path.relpath(src, HERE)
            if rel in ("answers.json", "init-vault.py") or rel == os.path.relpath(os.path.abspath(sys.argv[1]), HERE):
                continue
            dst = os.path.join(shared, fill(rel))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if f.endswith(TEXT_EXT):
                open(dst, "w", encoding="utf-8").write(fill(open(src, encoding="utf-8").read()))
            else:
                shutil.copyfile(src, dst)
            shutil.copymode(src, dst)

    # 2. skeletons
    for d in SHARED_DIRS:
        os.makedirs(os.path.join(shared, fill(d)), exist_ok=True)
    for d in PRIVATE_DIRS:
        os.makedirs(os.path.join(private, fill(d)), exist_ok=True)

    # 3. put templates and engine folders where the skills expect them
    where = lambda dst: os.path.join(private, fill(dst[2:])) if dst.startswith("P:") else os.path.join(shared, fill(dst))
    for src, dst in MOVE_DIRS:
        s, d = os.path.join(shared, src), where(dst)
        if os.path.isdir(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.move(s, d)
    for src, dst in PLACE:
        s, d = os.path.join(shared, src), where(dst)
        if os.path.isfile(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.move(s, d)

    # the shared vault has no inbox, and the private/ staging folder is empty once moved
    for empty in ("0_INBOX", "private/3_RESOURCES", "private"):
        p = os.path.join(shared, empty)
        if os.path.isdir(p) and not os.listdir(p):
            os.rmdir(p)

    # 4. mount the private vault and keep it out of git
    link = os.path.join(shared, "_private")
    os.symlink(os.path.relpath(private, shared), link)
    with open(os.path.join(shared, ".gitignore"), "a", encoding="utf-8") as g:
        g.write("\n# Private vault mount (local only, never tracked)\n/_private\n.scripts/lint-report.md\n.scripts/lint-launchd.log\n")

    left = []
    for root, dirs, files in os.walk(shared):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f.endswith(TEXT_EXT):
                p = os.path.join(root, f)
                if re.search(r"\{\{(?!PLACEHOLDERS?\}\})[A-Z_]+\}\}", open(p, encoding="utf-8").read()):
                    left.append(os.path.relpath(p, shared))
    print(f"Shared vault:  {shared}\nPrivate vault: {private}\nMounted at:    {link}")
    if left:
        print("Placeholders still unfilled in:", *left, sep="\n  ")
    print("\nNext: cd into the shared vault, run `git init`, `node .scripts/lint.mjs`, and `.scripts/qmd-bootstrap.sh`.\n"
          "Fill in ORG.md and _private/ME.md. Never give the private vault a shared remote.")


if __name__ == "__main__":
    main()

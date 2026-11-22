#!/usr/bin/env python3
"""Turn this framework checkout into a working pair of vaults.

Usage:  python3 init-vault.py answers.json
        python3 init-vault.py --selftest   (builds the example into a temp folder and lints it; needs node)

Reads the answers, replaces every {{PLACEHOLDER}} in file contents and file
names, then builds the shared vault (this engine plus a PARA skeleton) and the
private vault, and mounts the private vault in the shared one as _private/.
Run it once, from the framework folder. It refuses to write into a folder that
already has content.
"""
import datetime, getpass, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {".git", "node_modules"}
TEXT_EXT = (".md", ".json", ".yml", ".yaml", ".py", ".mjs", ".sh", ".plist", ".base", ".txt", ".canvas", ".js", ".toml", ".conf")
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
               "2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/insights",
               "3_RESOURCES/{{ORG}}/concepts", "3_RESOURCES/processes", "4_ARCHIVE/projects"] + ["4_ARCHIVE/sources/" + d for d in ("meetings", "docs", "decks", "data", "notes")]
PRIVATE_DIRS = ["0_INBOX", "1_PROJECTS/Actions", "2_AREAS/{{ORG}}/My Team", "2_AREAS/{{ORG}}/context", "2_AREAS/Career/Competencies",
                "2_AREAS/Career/Evidence", "3_RESOURCES", "4_ARCHIVE/sources/slack", "4_ARCHIVE/sources/other"]
# Files the index, skills and lint point at that a new vault has no content for yet: path -> what goes there.
# Every operationalFiles path in .scripts/lint.config.json is stubbed too. "> Not filled in yet." is the
# marker lint uses to list what to fill in next; keep it exact.
MARKER = "> Not filled in yet."
STUBS = {
    "2_AREAS/{{ORG}}/context/strategic_context.md": "Strategy, targets and current bets for {{PRODUCT}}.",
    "2_AREAS/{{ORG}}/context/metrics_dashboard.md": "The headline numbers this week and what moved them.",
    "2_AREAS/{{ORG}}/context/stakeholder_map.md": "Who matters outside the team, what they own, and where they fit.",
    "2_AREAS/{{ORG}}/context/company_context.md": "{{ORG}} as a company: market, results, structure.",
    "2_AREAS/{{ORG}}/context/cy27_objectives.md": "This year's objectives and key results.",
    "2_AREAS/{{ORG}}/_H2 Roadmap/CANDIDATES.md": "Uncommitted ideas. One line each until one is promoted to a project folder.",
    "2_AREAS/{{ORG}}/_H2 Roadmap/ROADMAP.md": "Now, Next, Later and Not-this-half tiers, plus open sequencing decisions.",
    "2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/learning_insights.md": "What experiments and data have taught the team. One insight per entry, with its source.",
    "3_RESOURCES/{{ORG}}/{{PRODUCT_LOWER}}-context.md": "Standing context for chat sessions about {{PRODUCT}}, including the metrics protocol.",
    "3_RESOURCES/AI Skills/diff-propose/diff-sessions.md": "One row per diff-propose session: date, initiative, proposed, approved, rejected, minutes.",
    "P:2_AREAS/{{ORG}}/My Team/Direct Reports.md": "One section per direct report: focus, coaching notes, open threads. Leave as is if you have none.",
    "P:2_AREAS/{{ORG}}/context/stakeholder_notes.md": "Your own notes on how to work with each stakeholder.",
    "P:2_AREAS/{{ORG}}/context/team_development.md": "Team-level development themes and coaching observations.",
    "P:2_AREAS/Career/career_development.md": "Your own goals, OKRs and development plan.",
    "P:2_AREAS/Career/Annual Performance Reviews.md": "Past reviews and their outcomes, newest first.",
}
# Non-Markdown files that only need to exist in a known starting shape.
RAW = {
    "2_AREAS/{{ORG}}/_metrics/history.csv": "changed_at,id,old_value,new_value,as_of,note\n",
    "1_PROJECTS/Actions/Actions.base": "# Open shared actions. " + MARKER + "\nfilters:\n  and:\n    - file.inFolder(\"1_PROJECTS/Actions\")\n    - 'status != \"done\"'\nviews:\n  - type: table\n    name: Open\n",
    "P:2_AREAS/Career/Competency_Evidence.base": "# Evidence cards by competency. " + MARKER + "\nfilters:\n  and:\n    - file.inFolder(\"2_AREAS/Career/Evidence\")\nviews:\n  - type: table\n    name: By Competency\n",
}


def stub(path, what):
    title = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
    return (f"# {title[:1].upper() + title[1:]}\n\n**Last Updated:** {{{{TODAY}}}}\n**Last verified accurate:** not yet (not filled in)\n"
            f"**Source as of:** none yet\n**Owner:** (team or role)\n**Review Cycle:** (rhythm)\n\n{what}\n\n{MARKER}\n")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    a = json.load(open(sys.argv[1], encoding="utf-8"))
    for k in ("ORG", "PRODUCT", "OWNER_NAME", "SHARED_VAULT_PATH", "PRIVATE_VAULT_PATH"):
        if not a.get(k):
            sys.exit(f"answers file is missing {k}")
    a.setdefault("OWNER", a["OWNER_NAME"].split()[0])
    a.setdefault("USER_ID", getpass.getuser())  # matches $(whoami) in the seat launchd labels
    a.setdefault("HOME", os.path.expanduser("~"))
    a.setdefault("ORG_LOWER", a["ORG"].lower())
    a.setdefault("PRODUCT_LOWER", a["PRODUCT"].lower())
    a.setdefault("TODAY", datetime.date.today().isoformat())
    a.setdefault("PILOT_INITIATIVE", "Example Initiative")  # init creates its folder, so ORG.md never names a missing one
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

    # 3b. stubs, so nothing the index, skills or lint name is missing
    cfg = json.load(open(os.path.join(shared, ".scripts/lint.config.json"), encoding="utf-8"))
    for f in cfg.get("operationalFiles", []):
        p = f["path"]
        p = "P:" + p[len("_private/"):] if p.startswith("_private/") else p
        if p.endswith(".md") and p not in STUBS:
            STUBS[p] = "Listed as an operational file in the lint config, so lint checks it for staleness."
    pilot = "1_PROJECTS/{{ORG}}/{{PILOT_INITIATIVE}}/"
    files = {p: stub(p, w) for p, w in STUBS.items()}
    files.update(RAW)
    for name in ("BRIEF", "STATE", "LOG"):  # the example pilot initiative, from the project templates
        t = open(os.path.join(shared, f"templates/{name}.template.md"), encoding="utf-8").read()
        t = t.replace("[Project]", "{{PILOT_INITIATIVE}}").replace("**Last verified accurate:** [YYYY-MM-DD]", "**Last verified accurate:** not yet")
        files[pilot + name + ".md"] = t.replace("[YYYY-MM-DD]", "{{TODAY}}") + f"\n{MARKER}\n"
    files[pilot + "diff-log.md"] = stub(pilot + "diff-log.md", "Every diff-propose proposal for this initiative and its outcome, newest first.")
    for p, text in files.items():
        d = where(p)
        if not os.path.exists(d):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            open(d, "w", encoding="utf-8").write(fill(text))

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


def selftest():
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as t:
        a = json.load(open(os.path.join(HERE, "templates/answers.example.json"), encoding="utf-8"))
        a.update(SHARED_VAULT_PATH=os.path.join(t, "shared"), PRIVATE_VAULT_PATH=os.path.join(t, "private"))
        json.dump(a, open(os.path.join(t, "answers.json"), "w"))
        subprocess.run([sys.executable, __file__, os.path.join(t, "answers.json")], check=True, stdout=subprocess.DEVNULL)
        shared = os.path.join(t, "shared")
        home = os.path.join(t, "home")  # empty HOME, as in CI: no installed skills to compare with
        os.makedirs(home)
        out = subprocess.run(["node", ".scripts/lint.mjs", "--json"], cwd=shared, capture_output=True, text=True, env={**os.environ, "HOME": home}).stdout
        found = json.loads(out)["findings"]
        assert not found["red"], [f["msg"] for f in found["red"]]  # a new vault has nothing must-fix
        assert not [f for f in found["amber"] if "strategic_context.md" in f["msg"]], "a stub is listed as not filled in, not should-fix"
        assert [f for f in found["amber"] if f["check"] == "run-integrity" and "never run" in f["msg"]], "never run is should-fix"
        todo = " ".join(f["msg"] for f in found["todo"])
        assert "strategic_context.md" in todo and "_ACTIVE_CYCLE.md" in todo and "_private/ME.md`: fill in Role" in todo, todo
        assert MARKER in open(os.path.join(shared, "2_AREAS/Acme/context/strategic_context.md"), encoding="utf-8").read()
        assert os.path.isfile(os.path.join(shared, "1_PROJECTS/Acme", a["PILOT_INITIATIVE"], "STATE.md"))
        for root, _, files in os.walk(shared):
            for f in files:
                if f.endswith(".conf"):
                    assert "{{" not in open(os.path.join(root, f), encoding="utf-8").read(), f
    print("init-vault selftest: ok")


if __name__ == "__main__":
    selftest() if sys.argv[1:] == ["--selftest"] else main()

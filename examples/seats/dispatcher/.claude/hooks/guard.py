#!/usr/bin/env /usr/bin/python3
"""PreToolUse guard for dispatcher. Exit 2 blocks the call. Run with --selftest to check it.
Writes: only the note, and BRIEF/STATE/LOG.md inside the one new project folder the job names (DISPATCH_JOB)."""
import json, os, re, sys

SEAT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))  # <seat>/.claude/hooks/guard.py
V = os.path.dirname(os.path.dirname(os.path.dirname(SEAT)))  # vault root: <vault>/2_AREAS/Agents/<seat>
ORG_DIR = "1_PROJECTS/{{ORG}}"  # a plain string: inside an f-string, {{ORG}} would become {ORG}
NOTE = SEAT + "/.out/note.txt"  # run.sh posts it; the seat never posts itself


def job_name():
    """The project name from the job file run.sh claimed. No job: no project writes."""
    j = os.environ.get("DISPATCH_JOB", "")
    if not os.path.realpath(j).startswith(os.path.dirname(SEAT) + "/jobs/"):
        return None
    m = re.search(r'^name: "(.+)"$', open(j).read(), re.M) if os.path.isfile(j) else None
    return m and m.group(1)


def check(tool, a, name, created):
    """Return a reason to block, or None. created: files this round wrote (may be edited again)."""
    raw = a.get("file_path") or a.get("path") or ""
    p = os.path.realpath(raw) if raw else ""
    priv = os.path.realpath(V + "/_private")
    if tool in ("Read", "Glob", "Grep"):
        if "_private" in raw or "_private" in a.get("pattern", "") or p == priv or p.startswith(priv + "/") or "/4_ARCHIVE" in p:
            return "no _private or 4_ARCHIVE reads"
        if tool != "Read" and not raw:
            return "give an explicit path"
    if tool in ("Edit", "MultiEdit", "Write"):
        if p == NOTE:
            return None
        if not name:
            return "no claimed job"
        allowed = {f"{V}/{ORG_DIR}/{name}/{f}.md" for f in ("BRIEF", "STATE", "LOG")}
        if p not in allowed:
            return f"edit not allowed: {p}"
        if os.path.exists(p) and p not in created:
            return "file exists: the dispatcher creates a project, it never overwrites one"
    if tool == "Bash":
        return "no shell"
    if tool.startswith("mcp__slack__"):
        return "slack tool not allowed"
    return None


def selftest():
    import shutil, tempfile
    global V
    V = os.path.realpath(tempfile.mkdtemp())  # temp vault root, so the test never writes into the real vault
    proj = f"{V}/{ORG_DIR}/Example Project"
    assert check("Write", {"file_path": NOTE, "content": "x"}, None, set()) is None
    assert check("Write", {"file_path": proj + "/BRIEF.md", "content": "x"}, None, set())  # no job
    assert check("Write", {"file_path": proj + "/BRIEF.md", "content": "x"}, "Example Project", set()) is None
    assert check("Write", {"file_path": proj + "/notes.md", "content": "x"}, "Example Project", set())
    assert check("Write", {"file_path": V + "/1_PROJECTS/{{ORG}}/{{PILOT_INITIATIVE}}/STATE.md", "content": "x"}, "Example Project", set())
    made = V + "/1_PROJECTS/{{ORG}}/zz-selftest-project"  # an existing project
    os.makedirs(made)
    open(made + "/STATE.md", "w").close()
    try:
        assert check("Write", {"file_path": made + "/STATE.md", "content": "x"}, "zz-selftest-project", set())  # exists
    finally:
        shutil.rmtree(V)
    assert check("Edit", {"file_path": V + "/1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md"}, "Example Project", set())
    assert check("Write", {"file_path": f"{V}/{ORG_DIR}/Example Project/../X/LOG.md"}, "Example Project", set())
    assert check("Read", {"file_path": V + "/_private/ME.md"}, None, set())
    assert check("Glob", {"pattern": "*.md"}, None, set())
    assert check("Bash", {"command": "ls"}, None, set())
    os.environ["DISPATCH_JOB"] = tempfile.mktemp()  # outside jobs/: refused
    assert job_name() is None
    print("ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    ev = json.load(sys.stdin)
    log = SEAT + "/.out/created.txt"  # files this round created, so the seat can fix its own draft
    created = set(open(log).read().split("\n")) if os.path.exists(log) else set()
    why = check(ev["tool_name"], ev["tool_input"], job_name(), created)
    if why:
        print("blocked: " + why, file=sys.stderr)
        sys.exit(2)
    if ev["tool_name"] == "Write":
        with open(log, "a") as f:
            f.write(os.path.realpath(ev["tool_input"]["file_path"]) + "\n")

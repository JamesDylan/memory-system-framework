#!/usr/bin/env /usr/bin/python3
"""PreToolUse guard for meeting-ingest. Exit 2 blocks the call. Run with --selftest to check it."""
import fnmatch, json, os, sys

SEAT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))  # <seat>/.claude/hooks/guard.py
V = os.path.dirname(os.path.dirname(os.path.dirname(SEAT)))  # vault root: <vault>/2_AREAS/Agents/<seat>
NOTE = SEAT + "/.out/note.txt"  # the launcher posts this file; the seat never posts itself
LOGS = V + "/1_PROJECTS/{{ORG}}/*/LOG.md"  # add-only: the line check below blocks removals
PENDING = SEAT + "/.out/pending/*.json"  # new diff files for {{OWNER}} to review


def lines(s):
    return len(s.splitlines())


def check(tool, a):
    """Return a reason to block, or None."""
    raw = a.get("file_path") or a.get("path") or ""
    p = os.path.realpath(raw) if raw else ""
    priv = os.path.realpath(V + "/_private")  # symlink: compare the raw path and the resolved one
    if tool in ("Read", "Glob", "Grep"):
        if "/_private" in raw or "_private" in a.get("pattern", "") or p == priv or p.startswith(priv + "/"):
            return "no _private reads"
        if tool != "Read" and not raw:
            return "give an explicit path"  # cwd may resolve anywhere; force a vault or seat path
    if tool in ("Edit", "MultiEdit", "Write"):
        if p == NOTE:
            return None
        if fnmatch.fnmatch(p, PENDING) and "/" not in p[len(SEAT + "/.out/pending/"):]:
            return None
        if not fnmatch.fnmatch(p, LOGS) or p.count("/") != LOGS.count("/"):
            return f"edit not allowed: {p}"
        if not os.path.exists(p):
            return "no new LOG files: that would create a project folder"
        # shortcut: line count only; a reworded line passes, so a person still reviews the git diff.
        if tool == "Edit" and lines(a["new_string"]) < lines(a["old_string"]):
            return "edit removes lines"
        if tool == "MultiEdit" and any(lines(e["new_string"]) < lines(e["old_string"]) for e in a["edits"]):
            return "edit removes lines"
        if tool == "Write" and os.path.exists(p) and lines(a["content"]) < lines(open(p).read()):
            return "write removes lines"
    if tool == "Bash":
        return "no shell"  # allow one exact checker command here if the seat needs one
    if tool.startswith("mcp__slack__"):
        return "slack tool not allowed"  # allow named read tools and one channel id here
    return None


def selftest():
    import shutil, tempfile
    global V, LOGS
    V = os.path.realpath(tempfile.mkdtemp())  # temp vault root, so the test never writes into the real vault
    LOGS = V + "/1_PROJECTS/{{ORG}}/*/LOG.md"
    assert check("Write", {"file_path": NOTE, "content": "x"}) is None
    assert check("Edit", {"file_path": V + "/README.md", "old_string": "", "new_string": "x"})
    proj = V + "/1_PROJECTS/{{ORG}}/zz-selftest-project"
    log = proj + "/LOG.md"
    os.makedirs(proj)
    open(log, "w").close()
    try:
        assert check("Edit", {"file_path": log, "old_string": "a", "new_string": "a\nb"}) is None
        assert check("Edit", {"file_path": log, "old_string": "a\nb", "new_string": "a"})
        assert check("Edit", {"file_path": proj + "/STATE.md", "old_string": "a", "new_string": "a\nb"})
        assert check("Edit", {"file_path": proj + "/sub/LOG.md", "old_string": "a", "new_string": "a\nb"})
    finally:
        shutil.rmtree(V)
    assert check("Write", {"file_path": SEAT + "/.out/pending/2026-11-14-x.json", "content": "{}"}) is None
    assert check("Write", {"file_path": SEAT + "/.out/pending/done/x.json", "content": "{}"})
    assert check("Write", {"file_path": V + "/1_PROJECTS/{{ORG}}/No Such Project/LOG.md", "content": "x"})
    assert check("Grep", {"pattern": "x", "path": V + "/_private"})
    assert check("Glob", {"pattern": "_private/**", "path": V})
    assert check("Glob", {"pattern": "*.md"})
    assert check("Glob", {"pattern": "*/STATE.md", "path": V + "/1_PROJECTS/{{ORG}}"}) is None
    assert check("Bash", {"command": "ls"})
    assert check("Read", {"file_path": V + "/_private/x.md"})
    assert check("mcp__slack__slack_post_message", {"channel_id": "C0"})
    print("ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    ev = json.load(sys.stdin)
    why = check(ev["tool_name"], ev["tool_input"])
    if why:
        print("blocked: " + why, file=sys.stderr)
        sys.exit(2)

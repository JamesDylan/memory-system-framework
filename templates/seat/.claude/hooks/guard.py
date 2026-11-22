#!/usr/bin/env /usr/bin/python3
"""PreToolUse guard for a seat. Exit 2 blocks the call. Run with --selftest to check it."""
import json, os, sys

V = "__VAULT__"
NOTE = "__SEATDIR__/.out/note.txt"  # the launcher posts this file; the seat never posts itself
EDIT = set()  # drawer files the seat may edit (absolute paths)


def lines(s):
    return len(s.splitlines())


def check(tool, a):
    """Return a reason to block, or None."""
    p = os.path.realpath(a.get("file_path", "")) if a.get("file_path") else ""
    priv = os.path.realpath(V + "/_private")  # symlink: compare the raw path and the resolved one
    if tool == "Read" and ("/_private" in a.get("file_path", "") or p == priv or p.startswith(priv + "/")):
        return "no _private reads"
    if tool in ("Edit", "MultiEdit", "Write"):
        if p == NOTE:
            return None
        if p not in EDIT:
            return f"edit not allowed: {p}"
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
    assert check("Write", {"file_path": NOTE, "content": "x"}) is None
    assert check("Edit", {"file_path": V + "/README.md", "old_string": "", "new_string": "x"})
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

#!/usr/bin/env /usr/bin/python3
"""PreToolUse guard for team-sync. Exit 2 blocks the call. Run with --selftest to check it."""
import json, os, sys

SEAT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))  # <seat>/.claude/hooks/guard.py
V = os.path.dirname(os.path.dirname(os.path.dirname(SEAT)))  # vault root: <vault>/2_AREAS/Agents/<seat>
DRAFT = SEAT + "/.out/canvas.md"  # the only file the seat writes; canvas.py publishes it after {{OWNER}} approves
READ_OK = (SEAT + "/.in", V + "/2_AREAS/{{ORG}}")


def check(tool, a):
    """Return a reason to block, or None."""
    raw = a.get("file_path") or a.get("path") or ""
    p = os.path.realpath(raw) if raw else ""
    if tool in ("Read", "Glob", "Grep"):
        if not raw:
            return "give an explicit path"
        if "_private" in raw + a.get("pattern", "") or ".." in a.get("pattern", ""):
            return "no _private reads"
        if not any(p == r or p.startswith(r + "/") for r in READ_OK):
            return f"read not allowed: {p}"
        return None
    if tool in ("Edit", "MultiEdit", "Write"):
        return None if p == DRAFT else f"edit not allowed: {p}"
    return f"tool not allowed: {tool}"  # no shell, no Slack, nothing else


def selftest():
    assert check("Write", {"file_path": DRAFT, "content": "x"}) is None
    assert check("Write", {"file_path": SEAT + "/.out/other.md", "content": "x"})
    assert check("Edit", {"file_path": V + "/1_PROJECTS/{{ORG}}/{{PILOT_INITIATIVE}}/LOG.md", "old_string": "a", "new_string": "a\nb"})
    assert check("Read", {"file_path": SEAT + "/.in/2026-11-18-x.txt"}) is None
    assert check("Read", {"file_path": V + "/2_AREAS/{{ORG}}/context/stakeholder_map.md"}) is None
    assert check("Read", {"file_path": V + "/_private/ME.md"})
    assert check("Read", {"file_path": V + "/2_AREAS/{{ORG}}/../../_private/ME.md"})
    assert check("Read", {"file_path": V + "/1_PROJECTS/{{ORG}}/_ACTIVE_CYCLE.md"})
    assert check("Glob", {"pattern": "*.md"})
    assert check("Glob", {"pattern": "../../_private/**", "path": V + "/2_AREAS/{{ORG}}"})
    assert check("Grep", {"pattern": "x", "path": V + "/2_AREAS/{{ORG}}/people"}) is None
    assert check("Bash", {"command": "ls"})
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

#!/usr/bin/env /usr/bin/python3
"""PreToolUse guard for experiment-reporter. Exit 2 blocks the call. Run with --selftest to check it."""
import json, os, re, sys

SEAT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))  # <seat>/.claude/hooks/guard.py
V = os.path.dirname(os.path.dirname(os.path.dirname(SEAT)))  # vault root: <vault>/2_AREAS/Agents/<seat>
M = V + "/2_AREAS/{{ORG}}/_metrics"
INSIGHTS = V + "/2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/insights"  # one file per insight: the seat creates new files, never edits one. Not registry.yaml: the weekly PowerBI update is its one writer; the seat proposes values in its note
TS = M + "/.experiment-reporter-last-ts"
NOTE = SEAT + "/.out/note.txt"  # run.sh posts this file; the seat never posts itself
CHECKER = "/usr/bin/python3 " + M + "/check_metrics.py"
IN_CH = "SLACK_ID"
OUT_CH = os.environ.get("REPORTER_OUT_CHANNEL", "SLACK_ID")  # set a private test channel while trialling


def lines(s):
    return len(s.splitlines())


def check(tool, a):
    """Return a reason to block, or None."""
    p = os.path.realpath(a.get("file_path", "")) if a.get("file_path") else ""
    priv = os.path.realpath(V + "/_private")  # symlink: compare the raw path and the resolved one
    if tool == "Read" and ("/_private" in a.get("file_path", "") or p == priv or p.startswith(priv + "/")):
        return "no _private reads"
    if tool in ("Edit", "MultiEdit", "Write"):
        if p in (TS, NOTE):
            return None
        if os.path.dirname(p) != INSIGHTS or not p.endswith(".md"):
            return f"edit not allowed: {p}"
        if tool != "Write" or os.path.exists(p):
            return "insights: write a new file only; never change an existing insight"
    if tool == "Bash":
        c = a.get("command", "")
        if not c.startswith(CHECKER) or re.search(r"[;&|<>`\n]|\$\(", c):
            return "only the metrics checker may run"
    if tool in ("mcp__slack__slack_get_channel_history", "mcp__slack__slack_get_thread_replies") \
            and a.get("channel_id") != IN_CH:
        return f"read only {IN_CH}"
    if tool.startswith("mcp__slack__") and tool not in (
            "mcp__slack__slack_get_channel_history",
            "mcp__slack__slack_get_thread_replies"):
        return "slack tool not allowed"
    return None


def selftest():
    new = INSIGHTS + "/zz-selftest-new-insight.md"
    assert not os.path.exists(new)
    assert check("Write", {"file_path": new, "content": "x"}) is None
    assert check("Edit", {"file_path": new, "old_string": "a", "new_string": "a\nb"})
    existing = INSIGHTS + "/zz-selftest-existing.md"  # made here so the test runs in any vault, even an empty one
    os.makedirs(INSIGHTS, exist_ok=True)
    open(existing, "w").close()
    try:
        assert check("Write", {"file_path": existing, "content": "x"})
    finally:
        os.remove(existing)
    assert check("Write", {"file_path": INSIGHTS + "/sub/x.md", "content": "x"})
    assert check("Write", {"file_path": V + "/2_AREAS/{{ORG}}/{{ORG_LOWER}}_data/learning_insights.md", "content": "x"})
    assert check("Edit", {"file_path": V + "/README.md", "old_string": "", "new_string": "x"})
    assert check("Write", {"file_path": TS, "content": "1"}) is None
    assert check("Edit", {"file_path": M + "/registry.yaml", "old_string": "a", "new_string": "a\nb"})
    assert check("Bash", {"command": CHECKER + " --root " + V}) is None
    assert check("Bash", {"command": CHECKER + "; rm -rf /"})
    assert check("Bash", {"command": "ls"})
    assert check("Read", {"file_path": V + "/_private/x.md"})
    assert check("mcp__slack__slack_post_message", {"channel_id": OUT_CH})  # posting is run.sh's job
    assert check("Write", {"file_path": NOTE, "content": "x"}) is None
    assert check("mcp__slack__slack_get_channel_history", {"channel_id": "not-the-input-channel"})
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

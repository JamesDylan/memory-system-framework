#!/usr/bin/env python3
"""health-digest: post the vault health line and the top 3 lint findings (must-fix first) to Slack. No model.
  ./digest.py             run lint and health in the vault, post to SEAT_OUT_CHANNEL
  ./digest.py --dry-run   print the message, post nothing
  ./digest.py --selftest  no network
Env: VAULT (vault root; run.sh sets it), SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL."""
import json, os, subprocess, sys, tempfile, urllib.error, urllib.request

TOP = 3
esc = lambda t: str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")  # Slack's three control characters


def message(health, lint):
    """Health line, the lint counts, then the TOP findings: every must-fix before any should-fix."""
    f = lint["findings"]
    ranked = [("🔴", x) for x in f["red"]] + [("🟡", x) for x in f["amber"]]
    lines = [esc(health.strip()), f"*Lint:* {len(f['red'])} must-fix · {len(f['amber'])} should-fix" + ("" if ranked else " · nothing to fix")]
    lines += [f"{i}. {icon} {esc(x['msg'])}" + (f" _Fix: {esc(x['fix'])}_" if x.get("fix") else "") for i, (icon, x) in enumerate(ranked[:TOP], 1)]
    return "\n".join(lines)


def node(vault, *args):
    try:
        r = subprocess.run(["node", *args], cwd=vault, capture_output=True, text=True)
    except OSError as e:  # no node on PATH, or the vault folder is missing
        raise RuntimeError(f"{args[0]}: {e}") from e
    if r.returncode:
        err = r.stderr.splitlines()
        why = next((l for l in err if "Error" in l or l.startswith("lint:")), err[-1] if err else f"exit {r.returncode}")
        raise RuntimeError(f"{args[0]}: {why.strip()}")
    return r.stdout


def build(vault):
    # --shared: the digest goes to a channel, so private-vault findings never enter it.
    lint = node(vault, ".scripts/lint.mjs", "--shared", "--json")
    with tempfile.NamedTemporaryFile("w", suffix=".json") as t:
        t.write(lint); t.flush()
        health = node(vault, ".scripts/health.mjs", t.name)
    return message(health, json.loads(lint))


def post(text):
    token, channel = os.environ.get("SLACK_BOT_TOKEN"), os.environ.get("SEAT_OUT_CHANNEL")
    if not (token and channel):
        sys.exit("health-digest: set SLACK_BOT_TOKEN and SEAT_OUT_CHANNEL (~/.config/health-digest.env, or the Actions secret and variable)")
    body = json.dumps({"channel": channel, "text": text, "unfurl_links": False, "unfurl_media": False}).encode()
    req = urllib.request.Request("https://slack.com/api/chat.postMessage", body, {
        "Authorization": "Bearer " + token, "Content-Type": "application/json; charset=utf-8"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=15))
    except (urllib.error.URLError, ValueError) as e:  # HTTPError is a URLError
        sys.exit(f"health-digest: could not reach Slack: {e}")
    if not r.get("ok"):
        sys.exit("health-digest: Slack said " + r.get("error", "not ok"))


def selftest():
    ok = lambda c, m: c or sys.exit("selftest FAIL: " + m)
    health = "*Vault health 2026-11-23:* STATEs in budget 3/5 · sources fresh 4/9\n"
    lint = {"findings": {
        "red": [{"check": "dead-pointer", "msg": "`a.md` is missing", "fix": "Fix the path"}, {"check": "state-budget", "msg": "`B/STATE.md` over budget"}],
        "amber": [{"check": "stale", "msg": "`c.md` 20d old"}, {"check": "stale", "msg": "`d.md` 30d old"}],
        "green": [], "todo": []}}
    m = message(health, lint).split("\n")
    ok(m[0] == health.strip(), "health line leads")
    ok(m[1] == "*Lint:* 2 must-fix · 2 should-fix", m[1])
    ok(m[2:] == ["1. 🔴 `a.md` is missing _Fix: Fix the path_", "2. 🔴 `B/STATE.md` over budget", "3. 🟡 `c.md` 20d old"], "top 3, must-fix first: %r" % m[2:])
    lint["findings"]["red"] = []
    ok(message(health, lint).split("\n")[2].startswith("1. 🟡 `c.md`"), "should-fix when no must-fix")
    lint["findings"]["amber"] = []
    ok(message(health, lint).split("\n")[1:] == ["*Lint:* 0 must-fix · 0 should-fix · nothing to fix"], "clean vault")
    try:
        node("/nonexistent-health-digest-vault", ".scripts/lint.mjs")
        ok(False, "a missing vault must raise")
    except RuntimeError as e:
        ok(failed(e).startswith("*Vault health:* not computed (.scripts/lint.mjs: "), failed(e))
    lint["findings"]["red"] = [{"msg": "`a & b` <x>"}]
    ok(message(health, lint).split("\n")[2] == "1. 🔴 `a &amp; b` &lt;x&gt;", "escapes & < >")
    print("selftest ok")


def failed(e):
    return f"*Vault health:* not computed ({esc(e)}). Run `node .scripts/lint.mjs` in the vault."


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--selftest":
        selftest(); sys.exit()
    if arg not in ("", "--dry-run"):
        sys.exit(__doc__)
    vault = os.environ.get("VAULT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    try:
        text = build(vault)
    except (RuntimeError, ValueError) as e:  # still post, so a broken lint is seen rather than silent
        text = failed(e)
    print(text) if arg == "--dry-run" else post(text)
    sys.exit(text.startswith("*Vault health:* not computed"))

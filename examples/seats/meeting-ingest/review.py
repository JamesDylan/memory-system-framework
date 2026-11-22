#!/usr/bin/env /usr/bin/python3
"""Stage 3 of meeting-ingest: {{OWNER}} reviews diffs in Slack, this script applies them. No model.
  ./review.py post      post a summary of the unposted pending files to SEAT_OUT_CHANNEL, each diff and action list as a thread reply
  ./review.py collect   read {{OWNER}}'s reactions and replies; apply decided diffs; close finished files
  ./review.py --selftest
Decisions count only from SEAT_OWNER_ID ({{OWNER}}'s Slack user ID). On each diff message:
  ✅ approve · ❌ reject · reply in the thread "D2: <new text>" to replace the added lines · "D2 [wrong fact]" adds a reason.
Env: SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL, SEAT_OWNER_ID. Bot scopes: chat:write, reactions:read, channels:history."""
import datetime, glob, html, json, os, re, shutil, subprocess, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.environ.get("VAULT", os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # <vault>/2_AREAS/Agents/meeting-ingest
PENDING, NOTE, LEDGER = HERE + "/.out/pending", HERE + "/.out/note.txt", HERE + "/decisions.jsonl"
SESSIONS = "3_RESOURCES/AI Skills/diff-propose/diff-sessions.md"
CHIPS = ["stale source", "wrong fact", "wrong field/initiative", "missing context", "wording", "duplicate"]
YES, NO = {"white_check_mark", "heavy_check_mark", "+1", "ballot_box_with_check"}, {"x", "no_entry", "-1", "no_entry_sign"}
BUDGET = {"Right now": 6, "Next decision needed": 6, "Blocker": 3, "Risks": 12, "Last 3 material events": 3}  # bullets, from diff-propose
STALE_DAYS = 7  # an undecided diff after this stays pending for good; the file closes
TODAY = datetime.date.today().isoformat()


def slack(method, **params):
    """Slack Web API. GET for reads, POST JSON for writes. Raises on ok=false."""
    h = {"Authorization": "Bearer " + os.environ["SLACK_BOT_TOKEN"]}
    if method.startswith(("chat.", "canvases.")):  # canvases.* (team-sync) take JSON bodies too
        req = urllib.request.Request("https://slack.com/api/" + method, json.dumps(params).encode(),
                                     h | {"Content-Type": "application/json; charset=utf-8"})
    else:
        req = urllib.request.Request("https://slack.com/api/" + method + "?" + urllib.parse.urlencode(params), headers=h)
    r = json.load(urllib.request.urlopen(req, timeout=20))
    if not r.get("ok"):
        raise RuntimeError(f"{method}: {r.get('error')}")
    return r


def say(text, thread=None):
    return slack("chat.postMessage", channel=os.environ["SEAT_OUT_CHANNEL"], text=text, thread_ts=thread,
                 unfurl_links=False, unfurl_media=False)["ts"]


def link(path, text):
    """Obsidian link: the vault is not on GitHub, and every reviewer has it open in Obsidian."""
    return f"<obsidian://open?vault={urllib.parse.quote(os.path.basename(VAULT))}&file={urllib.parse.quote(path)}|{text}>"


def state_link(init):
    return link(f"1_PROJECTS/{{ORG}}/{init}/STATE.md", init)


def changes(d):
    """(lines removed, lines added) between current and proposed field text; unchanged lines are not shown."""
    cur, new = d["current_value"].splitlines(), d["proposed_value"].splitlines()
    return [l for l in cur if l.strip() and l not in new], [l for l in new if l.strip() and l not in cur]


def edited(d, text):
    """{{OWNER}}'s edit replaces only the added lines; the rest of the proposed field stays."""
    added, out = changes(d)[1], []
    for l in d["proposed_value"].splitlines():
        if l not in added:
            out.append(l)
        elif text not in out:
            out.append(text)
    return "\n".join(out if text in out else out + [text])


def card(did, d):
    flags = ["needs {{OWNER}}" if d.get("needs_james") else "fact update", d.get("confidence", "inferred")]
    flags += ["contradicts current"] * bool(d.get("contradicts_current")) + d.get("source_flags", [])
    gone, added = changes(d)
    count = lambda v: sum(bool(re.match(r"\s*(-|\*|\d+\.) ", l)) for l in v.splitlines())
    size = f"{count(d['current_value'])} → {count(d['proposed_value'])} bullets (limit {BUDGET[d['field']]})" if d["field"] in BUDGET else ""
    q = lambda ls: "\n".join(">" + l for l in ls) or ">(nothing)"
    return (f"*{did}* · {state_link(d['initiative'])} › STATE.md › *{d['field']}* · {size}\n_{' · '.join(flags)}_\n"
            f"*Remove:*\n{q(gone)}\n*Add:*\n{q(added)}\n"
            f"*Why:* {d['source_quote']} ({d['source_link']})\n"
            f"✅ approve · ❌ reject · reply `{did}: <new text>` to change what is added")


def summary(ps):
    """The top-level message: which meetings, what needs {{OWNER}}, anything that has no home."""
    out = ["*Meeting notes reviewed*", f"{len(ps)} meeting{'s' * (len(ps) != 1)} read:"]
    out += [f"• {p.get('title', p['meeting'])} → " + (", ".join(map(state_link, p.get("projects", []))) or "no project") for p in ps]
    out.append("*For you*")
    per = {}
    for p in ps:
        for d in p["diffs"]:
            per[d["initiative"]] = per.get(d["initiative"], 0) + 1
    out += [f"• {n} change{'s' * (n != 1)} to {state_link(i)} to review" for i, n in per.items()]
    acts = sum(u["reason"].startswith("action for {{OWNER}}") for p in ps for u in p.get("unrouted", []))
    out += [f"• {acts} new action{'s' * (acts != 1)} with your name on them"] * bool(acts)
    for p in ps:
        other = [u for u in p.get("unrouted", []) if not u["reason"].startswith(("action for {{OWNER}}", "duplicate"))]
        if any(u["reason"].startswith("no project folder") for u in other):
            out.append(f"• *To note:* {p.get('title', p['meeting'])} has no project folder. Create one or tell me where to route the notes.")
        out += [f"• *To note:* {u['signal_excerpt']} ({u['reason']})" for u in other if not u["reason"].startswith("no project folder")]
    if len(out) == len(ps) + 3:
        out.append("• nothing to decide")
    return "\n".join(out + ["_Details are in the thread._"])


def post():
    files = [f for f in sorted(glob.glob(PENDING + "/*.json")) if "slack" not in json.load(open(f))]
    if not os.path.exists(NOTE) and not files:
        return 0
    if files:
        parent = say(summary([json.load(open(f)) for f in files]))
    else:  # no pending files: the seat's one-line note ("Meetings read, no project changes.")
        say(open(NOTE).read().strip())
        return 0
    k = n = 0
    for f in files:
        p = json.load(open(f))
        p["slack"] = {"channel": os.environ["SEAT_OUT_CHANNEL"], "parent": parent, "posted": TODAY, "ids": {}}
        for d in p["diffs"]:
            k += 1
            p["slack"]["ids"][f"D{k}"] = {"ts": say(card(f"D{k}", d), parent), "i": p["diffs"].index(d)}
        uid = {}  # every unrouted item gets an ID so a verb reply can name it ("U3: project <Name>")
        for i, u in enumerate(p.get("unrouted", [])):
            n += 1
            uid[f"U{n}"] = i
        p["slack"]["items"] = uid
        what = lambda u: (u["reason"][len("action for {{OWNER}}"):].lstrip(": ") if u["reason"].startswith("action for {{OWNER}}") else u["reason"]) or u["signal_excerpt"]
        lines = lambda pick: "\n".join(f"• *{k}* {what(u)} — _{u['signal_excerpt']}_" for k, i in uid.items() for u in [p["unrouted"][i]] if pick(u))
        acts = lines(lambda u: u["reason"].startswith("action for {{OWNER}}"))
        if acts:  # no decision needed in Slack; a list so they are not lost in the JSON
            say(f"*Actions for you* ({p.get('title', p['meeting'])}):\n" + acts, parent)
        homeless = lines(lambda u: not u["reason"].startswith(("action for {{OWNER}}", "duplicate")))
        if homeless:
            say(f"*No home yet* ({p.get('title', p['meeting'])}):\n{homeless}\n"
                f"Reply `U<n>: project <Name>` to create a project folder (only for work committed to a cycle).", parent)
        json.dump(p, open(f, "w"), indent=2, ensure_ascii=False)
    # The seat's own LOG entries from this round, so a clock round leaves no loose edits.
    # shortcut: commits the whole LOG file, so {{OWNER}}'s own unsaved edits to the same LOG go in too; fine while he is the only writer.
    commit(sorted({f"1_PROJECTS/{{ORG}}/{x}/LOG.md" for f in files for x in json.load(open(f)).get("projects", [])}),
           f"meeting-ingest: LOG entries from meetings ({TODAY})")
    return 0


REPLY = re.compile(r"^\s*(D\d+)\s*(?:\[([^\]]+)\])?\s*(?::\s*(.*))?$", re.S)


def decisions(p, owner):
    """{diff id: (action, chip, text)} from the owner's reactions and thread replies. Ambiguous → absent."""
    s, out, notes = p["slack"], {}, {}
    for m in slack("conversations.replies", channel=s["channel"], ts=s["parent"], limit=200).get("messages", []):
        if m.get("user") != owner or m.get("ts") == s["parent"]:
            continue
        g = REPLY.match(html.unescape(m.get("text", "")))
        if g and g.group(1) in s["ids"]:
            chip = g.group(2) if g.group(2) in CHIPS else None
            text = (g.group(3) or "").strip().strip("`").strip()
            notes[g.group(1)] = (chip, text, g.group(2) if not chip else "")
    for did, v in s["ids"].items():
        if v.get("done"):
            continue
        msg = slack("reactions.get", channel=s["channel"], timestamp=v["ts"], full="true")["message"]
        mine = {r["name"].split("::")[0] for r in msg.get("reactions", []) if owner in r.get("users", [])}
        chip, text, extra = notes.get(did, (None, "", ""))
        if text:
            out[did] = ("edit", chip, text)
        elif mine & YES and not mine & NO:
            out[did] = ("approve", None, "")
        elif mine & NO and not mine & YES:
            out[did] = ("reject", chip, extra)
    return out


VERB = re.compile(r"^\s*(?:(U\d+)\s*:\s*)?project\s*:?\s+(.+?)\s*$", re.I | re.S)
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 &()',.-]{1,59}$")  # becomes a folder name: no slash, no leading dot
JOBS = os.path.dirname(HERE) + "/jobs"


def verbs(p, owner, changed):
    """Owner replies "[U3:] project <Name>" in the thread → one job file for the dispatcher seat. Each reply once."""
    s = p["slack"]
    seen = s.setdefault("verbs", [])
    for m in slack("conversations.replies", channel=s["channel"], ts=s["parent"], limit=200).get("messages", []):
        if m.get("user") != owner or m["ts"] == s["parent"] or m["ts"] in seen:
            continue
        g = VERB.match(html.unescape(m.get("text", "")).strip("`"))
        if not g:
            continue
        seen.append(m["ts"])
        uid, name = g.group(1), g.group(2).strip().strip("`\"'")
        items = s.get("items", {})
        if uid and uid not in items:
            say(f"Not queued: {uid} is not an item in this thread.", s["parent"]); continue
        if not NAME.match(name) or os.path.exists(f"{VAULT}/1_PROJECTS/{{ORG}}/{name}"):
            say(f"Not queued: `{name}` is not a valid new folder name, or the folder exists.", s["parent"]); continue
        us = [p["unrouted"][items[uid]]] if uid else p.get("unrouted", [])
        os.makedirs(JOBS, exist_ok=True)
        path = f"{JOBS}/{TODAY}-new-project-{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')}.md"
        open(path, "w").write(
            f'---\ntype: job\nformula: new-project\nname: "{name}"\nstatus: open\nrequested_by: {owner}\nraised: {TODAY}\n'
            f'source_channel: {s["channel"]}\nsource_thread: "{s["parent"]}"\nmeeting: "{p["meeting"]}"\n---\n\n'
            f"# new-project: {name}\n\nRequested in Slack by the owner. Context from meeting-ingest ({p.get('title', p['meeting'])}):\n\n"
            + "".join(f"- {u['signal_excerpt']} ({u['reason']})\n" for u in us))
        changed.add(path)
        say(f"Queued: new-project `{name}`. The dispatcher picks it up on the next run.", s["parent"])


def under_header(t, block):
    """Return t with block as the newest entry: below the '# ' heading's first '---' line (skips frontmatter)."""
    i = t.index("\n---\n", re.search(r"^# ", t, re.M).start()) + 5
    return t[:i] + "\n" + block + "\n---\n" + t[i:]


def apply_one(d, action, chip, text, changed):
    """Return 'applied' or 'conflict'. Edits STATE (and LOG); rejects go to diff-log.md."""
    proj = f"{VAULT}/1_PROJECTS/{{ORG}}/{d['initiative']}"
    if action == "reject":
        with open(proj + "/diff-log.md", "a") as f:
            f.write(f"- {TODAY} · {d['confidence']} · {d['field']} · rejected — {chip or 'none'}"
                    f"{': ' + text if text else ''} · was: {d['proposed_value'][:300]!r} · meeting-ingest\n")
        changed.add(proj + "/diff-log.md")
        return "applied"
    st = proj + "/STATE.md"
    t = open(st).read()
    if t.count(d["current_value"]) != 1:
        return "conflict"  # STATE changed since the seat read it; never guess where the new text goes
    t = t.replace(d["current_value"], edited(d, text) if action == "edit" else d["proposed_value"])
    t = re.sub(r"\*\*Last touched:\*\* [^|\n]*", f"**Last touched:** {TODAY} (meeting-ingest, Slack review) ", t, 1)
    log = None
    if d.get("log_entry"):  # build the LOG text first: a failure here must not leave STATE half-applied
        log = under_header(open(proj + "/LOG.md").read(), f"## {TODAY} — Meeting diff applied ({d['field']})\n\n{d['log_entry']} "
                           f"Source: {d['source_link']}." + (" User-edited from proposed diff." if action == "edit" else "") + "\n")
    open(st, "w").write(t)
    changed.add(st)
    if log:
        open(proj + "/LOG.md", "w").write(log)
        changed.add(proj + "/LOG.md")
    return "applied"


def bump_tables(rows):
    """rows: [(initiative, tier, kind, outcome, chip)] for one closed file. Updates diff-sessions.md tables."""
    path = f"{VAULT}/{SESSIONS}"
    t = open(path).read()
    ver = lambda s: re.search(r"^version:\s*(\S+)", open(f"{VAULT}/3_RESOURCES/AI Skills/{s}/SKILL.md").read(), re.M).group(1)
    for init in dict.fromkeys(r[0] for r in rows):
        rs = [r for r in rows if r[0] == init]
        c = lambda o, tier=None: sum(1 for r in rs if r[3] == o and (tier is None or r[1] == tier))
        a, e, x, pend = c("approve"), c("edit"), c("reject"), c("pending") + c("conflict")
        tiers = {tier: f"{c('approve', tier)}/{c('edit', tier)}/{c('reject', tier)}" for tier in ("direct", "inferred")}
        why = ", ".join(f"{k} ×{v}" for k, v in sorted({r[4]: sum(1 for q in rs if q[4] == r[4]) for r in rs if r[4]}.items())) or "—"
        row = (f"| {TODAY} | {init} | meeting-ingest (Slack review) | {len(rs)} | {a} | {e} | {x} | {pend} | "
               f"Applied by review.py. | {tiers['direct']} | {tiers['inferred']} | {ver('diff-propose')} / {ver('ingest')} | {why} |")
        last = [l for l in t.splitlines() if re.match(r"\| \d{4}-\d\d-\d\d \|", l) and l.count("|") >= 14][-1]
        t = t.replace(last, last + "\n" + row, 1)
        m = re.search(rf"^\| {re.escape(init)} \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|$", t, re.M)
        nums = [len(rs), a, e, x, pend, 1]
        if m:
            v = [int(g) for g in m.groups()]
            new = [v[0] + 1, v[1] + nums[0], v[2] + a, v[3] + e, v[4] + x, v[5] + pend, v[6] + 1]
            t = t.replace(m.group(0), f"| {init} | " + " | ".join(map(str, new)) + " |")
        else:
            anchor = re.search(r"^\| Initiative \| Sessions .*\n\|[-|]+\|\n", t, re.M)
            t = t[:anchor.end()] + f"| {init} | 1 | {len(rs)} | {a} | {e} | {x} | {pend} | 1 |\n" + t[anchor.end():]
        for tier in ("direct", "inferred"):
            m = re.search(rf"^\| {tier} \| (\d+) \| (\d+) \| (\d+) \| .*$", t, re.M)
            if m:
                v = [int(m.group(1)) + c("approve", tier), int(m.group(2)) + c("edit", tier), int(m.group(3)) + c("reject", tier)]
                n = sum(v)
                t = t.replace(m.group(0), f"| {tier} | {v[0]} | {v[1]} | {v[2]} | {round(100 * v[0] / n) if n else 0}% (n={n}) |")
    led = [json.loads(l) for l in open(LEDGER)] if os.path.exists(LEDGER) else []
    for kind, label in (("fact", "fact update (`needs_james: false`)"), ("james", "needs {{OWNER}}")):
        k = [r for r in led if r["kind"] == kind and r["outcome"] in ("approve", "edit", "reject")]
        a = sum(r["outcome"] == "approve" for r in k)
        last30, last10 = k[-30:], k[-10:]
        rate = f"{round(100 * sum(r['outcome'] == 'approve' for r in last30) / len(last30))}% (last {len(last30)})" if k else "—"
        wf = sum(r.get("chip") == "wrong fact" for r in last10)
        t = re.sub(rf"^\| meeting-ingest \| {re.escape(label)} \|.*$",
                   f"| meeting-ingest | {label} | {len(k)} | {a} | {sum(r['outcome'] == 'edit' for r in k)} | "
                   f"{sum(r['outcome'] == 'reject' for r in k)} | {rate} | {wf} |", t, 1, re.M)
    facts = [r for r in led if r["kind"] == "fact" and r["outcome"] in ("approve", "edit", "reject")]
    met = len(facts) >= 30 and sum(r["outcome"] == "approve" for r in facts[-30:]) >= 27 \
        and not any(r.get("chip") == "wrong fact" for r in facts[-10:])
    t = re.sub(r"(\*\*Auto-apply gate \(fact updates row only\):\*\*.*?\.) (Not met|MET)\.", rf"\1 {'MET' if met else 'Not met'}.", t, 1)
    open(path, "w").write(t)
    return path


def changelog(lines):
    path = f"{VAULT}/CHANGELOG.md"
    t, head = open(path).read(), f"## {TODAY} — Meeting diffs applied (review.py)"
    bullets = "".join(f"- {l}\n" for l in lines)
    if head in t:
        i = t.index(head) + len(head) + 2
    else:
        i = t.index("\n---\n") + 6
        bullets = head + "\n\n" + bullets + "\n"
    open(path, "w").write(t[:i] + bullets + t[i:])
    return path


def collect():
    owner, changed, msgs = os.environ["SEAT_OWNER_ID"], set(), []
    for f in sorted(glob.glob(PENDING + "/done/*.json")):  # closed threads still take verbs for a week
        p = json.load(open(f))
        if "slack" in p and (datetime.date.today() - datetime.date.fromisoformat(p["slack"]["posted"])).days < STALE_DAYS:
            verbs(p, owner, changed)
            json.dump(p, open(f, "w"), indent=2, ensure_ascii=False)
    for f in sorted(glob.glob(PENDING + "/*.json")):
        p = json.load(open(f))
        if "slack" not in p:
            continue
        verbs(p, owner, changed)
        s, done_now = p["slack"], []
        for did, (action, chip, text) in decisions(p, owner).items():
            d = p["diffs"][s["ids"][did]["i"]]
            res = apply_one(d, action, chip, text, changed)
            s["ids"][did].update(done=True, outcome=action if res == "applied" else "conflict", chip=chip)
            done_now.append(f"{did} {s['ids'][did]['outcome']}")
            with open(LEDGER, "a") as led:
                led.write(json.dumps({"date": TODAY, "meeting": p["meeting"], "initiative": d["initiative"],
                                      "field": d["field"], "kind": "james" if d.get("needs_james") else "fact",
                                      "tier": d.get("confidence"), "outcome": s["ids"][did]["outcome"], "chip": chip}) + "\n")
            changed.add(LEDGER)
            if res == "applied" and action != "reject":
                msgs.append(f"{d['initiative']} STATE: {d['field']} {'edited by {{OWNER}}' if action == 'edit' else 'approved'} "
                            f"(meeting-ingest, {p['meeting']}).")
        if done_now:
            say("Done: " + ", ".join(done_now) + ". Conflict = STATE changed since; not applied.", s["parent"])
        age = (datetime.date.today() - datetime.date.fromisoformat(s["posted"])).days
        if all(v.get("done") for v in s["ids"].values()) or age >= STALE_DAYS:
            rows = [(p["diffs"][v["i"]]["initiative"], p["diffs"][v["i"]].get("confidence"), None,
                     v.get("outcome", "pending"), v.get("chip")) for v in s["ids"].values()]
            changed.add(bump_tables(rows))
            os.makedirs(PENDING + "/done", exist_ok=True)
            json.dump(p, open(f, "w"), indent=2, ensure_ascii=False)
            shutil.move(f, PENDING + "/done/" + os.path.basename(f))
        else:
            json.dump(p, open(f, "w"), indent=2, ensure_ascii=False)
    if msgs:
        changed.add(changelog(msgs))
    commit(sorted(c for c in changed if c.startswith(VAULT + "/") and "/.out/" not in c), f"meeting-ingest: apply Slack review decisions ({TODAY})")
    return 0


def commit(paths, msg):
    """Commit only these vault files, and only those with changes. NO_GIT=1 (self-test) skips it."""
    if not paths or os.environ.get("NO_GIT"):
        return
    paths = [l[3:].strip('"') for l in subprocess.run(["git", "-C", VAULT, "status", "--porcelain", "--", *paths],
                                                       capture_output=True, text=True, check=True).stdout.splitlines()]
    if paths:
        subprocess.run(["git", "-C", VAULT, "add", "--", *paths], check=True)
        subprocess.run(["git", "-C", VAULT, "commit", "-q", "-m", msg, "--", *paths], check=True)


def selftest():
    import tempfile
    global VAULT, PENDING, NOTE, LEDGER, JOBS, slack
    tmp = tempfile.mkdtemp()
    VAULT, PENDING, NOTE, LEDGER, JOBS = tmp, tmp + "/pending", tmp + "/note.txt", tmp + "/decisions.jsonl", tmp + "/jobs"
    os.makedirs(tmp + "/1_PROJECTS/{{ORG}}/Proj")
    os.makedirs(PENDING)
    for s in ("diff-propose", "ingest"):
        os.makedirs(f"{tmp}/3_RESOURCES/AI Skills/{s}")
        open(f"{tmp}/3_RESOURCES/AI Skills/{s}/SKILL.md", "w").write("---\nversion: 1.0\n---\n")
    open(tmp + "/1_PROJECTS/{{ORG}}/Proj/STATE.md", "w").write(
        "# Proj\n\n**Last touched:** 2026-01-01 | **Last verified accurate:** x\n\n## Right now\n\nOld A.\n\n## Risks\n\nOld B.\n\n## Pointers\n")
    open(tmp + "/1_PROJECTS/{{ORG}}/Proj/LOG.md", "w").write("---\ntype: log\n---\n\n# Proj — LOG\n\nIntro.\n\n---\n\n## old\n")
    open(tmp + "/CHANGELOG.md", "w").write("# Changelog\n\nIntro.\n\n---\n\n## 2026-01-01 — x\n")
    open(f"{tmp}/{SESSIONS}", "w").write(
        "| Date | Initiative | Trigger | Proposed | Approved | Edited | Rejected | Pending | Note | Direct A/E/R | Inferred A/E/R | Versions (dp / ingest) | Reasons |\n|---|\n"
        "| 2026-01-01 | Old | t | 1 | 1 | 0 | 0 | 0 | n | 0/0/0 | 1/0/0 | v | — |\n\n"
        "| Initiative | Sessions | Proposed | Approved | Edited | Rejected | Pending | Completed cycles |\n|---|---|---|---|---|---|---|---|\n"
        "| Old | 1 | 1 | 1 | 0 | 0 | 0 | 1 |\n\n| Tier | Approved | Edited | Rejected | Clean rate |\n|---|---|---|---|---|\n"
        "| direct | 0 | 0 | 0 | 0% |\n| inferred | 1 | 0 | 0 | 100% (n=1) |\n\n"
        "**Auto-apply gate (fact updates row only):** Decided ≥ 30. Not met.\n\n"
        "| meeting-ingest | fact update (`needs_james: false`) | 0 | 0 | 0 | 0 | — | 0 |\n| meeting-ingest | needs {{OWNER}} | 0 | 0 | 0 | 0 | — | 0 |\n")
    diff = lambda field, cur, new, nj: {"initiative": "Proj", "field": field, "op": "replace", "current_value": cur,
                                        "proposed_value": new, "log_entry": "old moved", "confidence": "inferred",
                                        "contradicts_current": False, "source_quote": "q", "source_link": "m.txt",
                                        "source_flags": ["transcript"], "needs_james": nj}
    json.dump({"meeting": "m.txt", "title": "Team sync", "projects": ["Proj"], "diffs": [diff("Right now", "Old A.", "New A.", False), diff("Risks", "Old B.", "New B.", True),
               diff("Risks", "Gone.", "X.", False)],
               "unrouted": [{"signal_excerpt": "do Y", "reason": "action for {{OWNER}}: reply to Z"}, {"signal_excerpt": "n", "reason": "no project folder"}]},
              open(PENDING + "/m.json", "w"))
    open(NOTE, "w").write("Meetings: 1 read.")
    posted, R = [], {}

    def fake(method, **a):
        if method == "chat.postMessage":
            posted.append(a); return {"ts": f"{len(posted)}.0"}
        if method == "conversations.replies":
            return {"messages": [{"user": "U1", "ts": "1.0"}, {"user": "U1", "ts": "9.0", "text": "D2 [wording]: Edited &amp; B."},
                                 {"user": "EVIL", "ts": "9.1", "text": "D3: injected"}, {"user": "EVIL", "ts": "9.3", "text": "project Evil"},
                                 {"user": "U1", "ts": "9.2", "text": "U2: project Example Project"}, {"user": "U1", "ts": "9.4", "text": "project ../x"}]}
        if method == "reactions.get":
            return {"message": {"reactions": R.get(a["timestamp"], [])}}
    slack = fake
    os.environ.update(SEAT_OUT_CHANNEL="C1", SEAT_OWNER_ID="U1", NO_GIT="1")
    post()
    assert len(posted) == 6 and posted[1]["thread_ts"] == "1.0" and "*D1*" in posted[1]["text"]
    top = posted[0]["text"]
    assert "Team sync" in top and "3 changes to <obsidian://open?vault=" in top and "1 new action " in top and "no project folder" in top, top
    assert "*Remove:*\n>Old A.\n*Add:*\n>New A." in posted[1]["text"] and "1_PROJECTS/{{ORG}}/Proj/STATE.md" in posted[1]["text"]
    d = {"current_value": "- a\n- b\n- c", "proposed_value": "- a\n- c\n- d"}
    assert changes(d) == (["- b"], ["- d"]) and edited(d, "- z") == "- a\n- c\n- z"
    assert edited({"current_value": "- a\n- b", "proposed_value": "- a"}, "- z") == "- a\n- z"
    assert "*U1* reply to Z" in posted[4]["text"] and "no project" not in posted[4]["text"] and "*U2* no project folder — _n_" in posted[5]["text"], posted[5]
    post()
    assert len(posted) == 7 and posted[6]["text"] == "Meetings: 1 read."  # no unposted files: the note alone
    R["2.0"] = [{"name": "white_check_mark", "users": ["U1"]}]
    R["4.0"] = [{"name": "white_check_mark", "users": ["EVIL"]}]  # someone else's reaction does not count
    collect()
    st = open(VAULT + "/1_PROJECTS/{{ORG}}/Proj/STATE.md").read()
    assert "New A." in st and "Edited & B." in st and "X." not in st and "2026-01-01" not in st.split("## Right")[0], st
    assert open(VAULT + "/1_PROJECTS/{{ORG}}/Proj/LOG.md").read().index("Meeting diff applied") > \
        open(VAULT + "/1_PROJECTS/{{ORG}}/Proj/LOG.md").read().index("# Proj — LOG")
    jobs = glob.glob(JOBS + "/*.md")
    assert len(jobs) == 1 and 'name: "Example Project"' in open(jobs[0]).read() and "- n (no project folder)" in open(jobs[0]).read(), jobs
    assert sum("Not queued" in m["text"] for m in posted) == 1  # "../x" refused; EVIL ignored
    assert os.path.exists(PENDING + "/m.json")  # D3 undecided: file stays open
    assert under_header("# P — LOG\n\nx\n\n---\n\n## old\n", "## new\n") == "# P — LOG\n\nx\n\n---\n\n## new\n\n---\n\n## old\n"
    R["4.0"] = [{"name": "x", "users": ["U1"]}]
    collect()
    assert len(glob.glob(JOBS + "/*.md")) == 1  # each reply queues once
    assert os.path.exists(PENDING + "/done/m.json") and "Proj/STATE.md" not in open(VAULT + "/1_PROJECTS/{{ORG}}/Proj/diff-log.md").read()
    t = open(f"{VAULT}/{SESSIONS}").read()
    assert "| Proj | 1 | 3 | 1 | 1 | 1 | 0 | 1 |" in t and "| inferred | 2 | 1 | 1 | 50% (n=4) |" in t, t
    assert "| meeting-ingest | fact update (`needs_james: false`) | 2 | 1 | 0 | 1 | 50% (last 2) | 0 |" in t, t
    assert "| meeting-ingest | needs {{OWNER}} | 1 | 0 | 1 | 0 | 0% (last 1) | 0 |" in t, t
    assert "Meeting diffs applied" in open(VAULT + "/CHANGELOG.md").read()
    print("ok")


if __name__ == "__main__":
    os.makedirs(PENDING, exist_ok=True)
    cmd = (sys.argv + [""])[1]
    if cmd == "--selftest":
        selftest(); sys.exit(0)
    try:
        sys.exit({"post": post, "collect": collect}[cmd]())
    except KeyError:
        sys.exit(__doc__)
    except Exception as ex:  # Slack down, bad token: log and stop; the next run retries
        print(f"review error: {ex}", file=sys.stderr)
        sys.exit(1)

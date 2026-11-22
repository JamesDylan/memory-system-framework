#!/usr/bin/env /usr/bin/python3
"""kr-feed (PLAN Move 11g): keep the Productboard block in cy27_objectives.md true to Productboard. No model.
  ./feed.py collect    apply or drop the open proposal from {{OWNER}}'s reaction (✅ apply · ❌ drop; expires after 7 days)
  ./feed.py propose    read {{PRODUCT}} 2027 objectives and KRs from Productboard; if the block differs, post the diff to Slack
  ./feed.py --dry-run  print the block Productboard gives now, post nothing
  ./feed.py --selftest
The feed owns only the text between the two markers. It never edits the rest of the file or its stamps.
Env: PRODUCTBOARD_TOKEN (read-only, entities:read), SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL, SEAT_OWNER_ID."""
import datetime, difflib, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE + "/../meeting-ingest")
import review  # reuse its Slack client, reaction sets and git commit; review.VAULT honours the VAULT env

ROOT = "{{PRODUCT}} 2027"  # the Productboard objective whose children are the CY27 product objectives
KR_FILE = "2_AREAS/{{ORG}}/context/cy27_objectives.md"
START, END = "<!-- kr-feed:start -->", "<!-- kr-feed:end -->"
PROPOSAL = HERE + "/.out/proposal.json"
EXPIRE_DAYS = 7
API = "https://api.productboard.com/v2/entities"


def pb_list(kind, parent=None):
    """All entities of one type (optionally under one parent), following links.next. Raises on HTTP errors, so a bad token stops the run."""
    url, out = API + "?" + urllib.parse.urlencode({"type[]": kind} | ({"parent[id]": parent} if parent else {})), []
    while url:
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ["PRODUCTBOARD_TOKEN"],
                                                   "Accept": "application/json"})
        r = json.load(urllib.request.urlopen(req, timeout=30))
        out += r.get("data", [])
        url = (r.get("links") or {}).get("next")
    return out


def fetch():
    """(child objectives of ROOT, {objective id: its KRs}). Uses the parent[id] filter: an entity's own
    relationships list is paged, and its parent link is often past the first page (20 Nov hand run)."""
    root = [o["id"] for o in pb_list("objective") if (o.get("fields") or {}).get("name", "").strip() == ROOT]
    if len(root) != 1:
        raise RuntimeError(f"expected one objective named {ROOT!r}, found {len(root)}")
    kids = pb_list("objective", root[0])
    return kids, {o["id"]: pb_list("keyResult", o["id"]) for o in kids}


def num(v):
    return "?" if v is None else f"{v:,.0f}" if float(v).is_integer() else f"{v:,}"


def render(kids, krs):
    """The block, from raw API entities. Sorted by name so the order never makes a diff."""
    f = lambda e: e.get("fields") or {}
    live = lambda e: not f(e).get("archived")
    rows = []
    for o in sorted(filter(live, kids), key=lambda o: f(o).get("name", "")):
        mine = sorted(filter(live, krs.get(o["id"], [])), key=lambda k: f(k).get("name", ""))
        cells = []
        for k in mine:
            p = next((v for v in f(k).values() if isinstance(v, dict) and "targetValue" in v), None)  # progress field; key name not documented
            vals = f" ({num(p.get('startValue'))} → {num(p.get('targetValue'))}, now {num(p.get('currentValue'))})" if p and p.get("targetValue") is not None else ""
            cells.append(f"{f(k)['name'].strip()}{vals} · {(f(k).get('status') or {}).get('name', 'no status')}")
        name = f(o)["name"].strip().replace("|", "/")
        rows.append(f"| {name} | {(f(o).get('status') or {}).get('name', '')} | {'<br>'.join(cells).replace('|', '/') or 'none in Productboard yet'} |")
    return "\n".join([
        f"## Productboard: {ROOT} objectives and KRs (feed)", "",
        "_Written by `kr-feed` from Productboard after its reviewer approves each change in #second-brain. Do not edit by hand: change Productboard. The tables above are from the decks._", "",
        "| Objective | Status | Key results (start → target, now current · status) |", "|---|---|---|", *rows])


def current_block(text):
    """Text between the markers, or None when the file has no block yet."""
    if START not in text:
        return None
    return text.split(START, 1)[1].split(END, 1)[0].strip("\n")


def put_block(text, block):
    if START in text:
        head, rest = text.split(START, 1)
        return head + START + "\n" + block + "\n" + END + rest.split(END, 1)[1]
    anchor = "\n---\n\n## Update History"  # first run: insert above the file's history table
    new = f"\n{START}\n{block}\n{END}\n"
    return text.replace(anchor, new + anchor, 1) if anchor in text else text.rstrip("\n") + "\n" + new


def diff_text(old, new):
    lines = [l for l in difflib.unified_diff((old or "").splitlines(), new.splitlines(), lineterm="", n=0) if not l.startswith(("---", "+++", "@@"))]
    return "\n".join(lines[:40]) + ("\n…" if len(lines) > 40 else "")


def path():
    return os.path.join(review.VAULT, KR_FILE)


def propose():
    if os.path.exists(PROPOSAL):
        return print("kr-feed: a proposal is still open; no new one")
    block = render(*fetch())
    old = current_block(open(path()).read())
    if old == block:
        return print("kr-feed: Productboard matches the file")
    link = review.link(KR_FILE, "cy27_objectives.md")
    ts = review.say(f"*kr-feed* · Productboard changed for *{ROOT}*. Proposed change to {link} (feed block only):\n"
                    f"```{diff_text(old, block)}```\n✅ apply · ❌ drop · no answer in {EXPIRE_DAYS} days: dropped, proposed again next week")
    os.makedirs(os.path.dirname(PROPOSAL), exist_ok=True)
    json.dump({"ts": ts, "channel": os.environ["SEAT_OUT_CHANNEL"], "date": review.TODAY, "old": old, "block": block}, open(PROPOSAL, "w"))


def collect():
    if not os.path.exists(PROPOSAL):
        return
    p, owner = json.load(open(PROPOSAL)), os.environ["SEAT_OWNER_ID"]
    msg = review.slack("reactions.get", channel=p["channel"], timestamp=p["ts"], full="true")["message"]
    mine = {r["name"].split("::")[0] for r in msg.get("reactions", []) if owner in r.get("users", [])}
    yes, no = bool(mine & review.YES), bool(mine & review.NO)
    if yes and not no:
        text = open(path()).read()
        if current_block(text) != p["old"]:  # someone edited the block since the proposal: never overwrite blind
            review.say("kr-feed: the feed block changed after the proposal, so it was not applied. A new proposal comes next run.", p["ts"])
        else:
            open(path(), "w").write(put_block(text, p["block"]))
            review.commit([KR_FILE], f"kr-feed: Productboard {ROOT} objectives and KRs ({review.TODAY})")
            review.say("Applied.", p["ts"])
    elif no and not yes:
        review.say("Dropped.", p["ts"])
    elif (datetime.date.today() - datetime.date.fromisoformat(p["date"])).days < EXPIRE_DAYS:
        return  # undecided (or both reactions): wait
    os.remove(PROPOSAL)


def selftest():
    obj = lambda i, n, st="Upcoming", **x: {"id": i, "fields": {"name": n, "status": {"name": st}, **x}}
    kids = [obj("b", "Grow companies"), obj("a", "Acquisition"), obj("g", "Gone", archived=True)]
    krs = {"a": [obj("k", "Activated companies", "On track", progress={"startValue": 4000000.0, "targetValue": 6000000.0, "currentValue": None}),
                 obj("j", "Old KR", archived=True)]}
    b = render(kids, krs)
    ok = lambda c, m: c or sys.exit("selftest FAIL: " + m)
    ok(b.index("| Acquisition") < b.index("| Grow companies"), "sorted by name")
    ok("Activated companies (4,000,000 → 6,000,000, now ?) · On track" in b, "KR with progress")
    ok("| Grow companies | Upcoming | none in Productboard yet |" in b, "objective with no KR")
    ok("Gone" not in b and "Old KR" not in b, "archived left out")
    doc = "# T\n\nbody\n\n---\n\n## Update History\n| x |\n"
    once = put_block(doc, b)
    ok(current_block(once) == b and once.index(START) < once.index("## Update History"), "first insert above history")
    twice = put_block(once, b + "\n| new |")
    ok(current_block(twice) == b + "\n| new |" and twice.count(START) == 1 and twice.endswith("| x |\n"), "replace keeps the rest")
    ok(current_block(doc) is None and diff_text(None, "a") == "+a", "no block yet")
    print("selftest ok")


if __name__ == "__main__":
    cmd = {"collect": collect, "propose": propose, "--selftest": selftest,
           "--dry-run": lambda: print(render(*fetch()))}.get(sys.argv[1] if len(sys.argv) > 1 else "")
    if not cmd:
        sys.exit(__doc__)
    try:
        cmd()
    except Exception as ex:  # Productboard or Slack down, bad token: log and stop; the next run retries
        print(f"kr-feed error: {ex}", file=sys.stderr)
        sys.exit(1)

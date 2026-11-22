#!/usr/bin/env /usr/bin/python3
"""The clock's check. No model runs here.
  ./gate.py            find transcripts attached to recent calendar events, not yet seen; export them to .in/. Exit 0 if any.
  ./gate.py --mark     record this batch as seen. run.sh calls this after a round that wrote a note.
  ./gate.py --fail     count a round that wrote no note. A transcript that fails MAX_FAILS rounds is marked seen
                       (no more retries) and its file id printed, so run.sh can warn {{OWNER}} (law 5).
  ./gate.py --selftest check the picking logic offline.
Read-only Google access (calendar.readonly, drive.readonly) from GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
GOOGLE_REFRESH_TOKEN in ~/.config/meeting-ingest.env. The seat itself has no Google access; it reads .in/ only."""
import json, os, re, shutil, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.environ.get("SEAT_DIR") or os.path.dirname(os.path.abspath(__file__))  # team-sync runs this gate with its own SEAT_DIR
SEEN, BATCH, IN, FAILS = HERE + "/.out/seen.txt", HERE + "/.out/.batch", HERE + "/.in", HERE + "/.out/fails.txt"
CONF = dict(re.findall(r'^(\w+)=(\'[^\']*\'|"[^"]*"|\S+)', open(HERE + "/seat.conf").read(), re.M))  # quoted values may hold spaces
LOOKBACK_H, MAX_MEETINGS = int(CONF.get("LOOKBACK_HOURS", 48)), int(CONF.get("MAX_MEETINGS", 3))
MIN_ATTENDEES = int(CONF.get("MIN_ATTENDEES", 3))
MAX_FAILS = int(CONF.get("MAX_FAILS", 2))  # retry ceiling per transcript (law 5)
TITLE_MATCH = CONF.get("TITLE_MATCH", "").strip("'\"")  # optional: only meetings whose title matches this regex (case-insensitive)
DOC = "application/vnd.google-apps.document"


def pick(events, seen, title=None):
    """Return [(event, attachment)] for meetings with a transcript not yet seen, oldest first, one file per meeting."""
    title = TITLE_MATCH if title is None else title
    out = []
    for e in events:
        if title and not re.search(title, e.get("summary", ""), re.I):
            continue
        people = [a for a in e.get("attendees", []) if not a.get("resource")]
        if any(a.get("self") and a.get("responseStatus") == "declined" for a in people):
            continue
        # 1:1s get Gemini notes too. Keep them out of .in/ entirely, not just out of the output.
        if len(people) < MIN_ATTENDEES:
            continue
        docs = [a for a in e.get("attachments", []) if a.get("mimeType") == DOC and a.get("fileId")]
        # Meet attaches "Transcript" and "Notes by Gemini". Prefer the full transcript; fall back to the notes.
        best = [a for a in docs if "transcript" in a.get("title", "").lower()] or \
               [a for a in docs if "notes by gemini" in a.get("title", "").lower()]
        if best and best[0]["fileId"] not in seen:
            out.append((e, best[0]))
    return out


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "meeting"


def api(url, token, raw=False):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode() if raw else json.load(r)


def token():
    body = urllib.parse.urlencode({k: os.environ[v] for k, v in (
        ("client_id", "GOOGLE_CLIENT_ID"), ("client_secret", "GOOGLE_CLIENT_SECRET"),
        ("refresh_token", "GOOGLE_REFRESH_TOKEN"))} | {"grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", body, timeout=15))["access_token"]


def gate():
    now = datetime.now(timezone.utc)
    t = token()
    q = urllib.parse.urlencode({"timeMin": (now - timedelta(hours=LOOKBACK_H)).isoformat(), "timeMax": now.isoformat(),
                                "singleEvents": "true", "orderBy": "startTime", "supportsAttachments": "true",
                                "maxResults": 250})
    events = api("https://www.googleapis.com/calendar/v3/calendars/primary/events?" + q, t).get("items", [])
    seen = set(open(SEEN).read().split()) if os.path.exists(SEEN) else None
    found = pick(events, seen or set())
    if seen is None:  # first run: no backlog. Everything visible now counts as seen.
        open(SEEN, "w").write("".join(a["fileId"] + "\n" for _, a in found))
        return 1
    found = found[:MAX_MEETINGS]  # cost ceiling per round; the rest wait for the next run
    shutil.rmtree(IN, ignore_errors=True)
    os.makedirs(IN)
    for e, a in found:
        text = api(f"https://www.googleapis.com/drive/v3/files/{a['fileId']}/export?mimeType=text/plain", t, raw=True)
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        head = (f"Meeting: {e.get('summary', '')}\nStart: {start}\nAttendees: "
                + ", ".join(x.get("email", "") for x in e.get("attendees", [])) + f"\nSource: {a['title']}\n\n")
        open(f"{IN}/{start[:10]}-{slug(e.get('summary', ''))}.txt", "w").write(head + text)
    open(BATCH, "w").write("".join(a["fileId"] + "\n" for _, a in found))
    return 0 if found else 1


def mark():
    if os.path.exists(BATCH):
        open(SEEN, "a").write(open(BATCH).read())
        os.remove(BATCH)
    shutil.rmtree(IN, ignore_errors=True)
    return 0


def fail():
    """A round wrote no note. Count one failure per transcript in the batch; give up on any that reached MAX_FAILS."""
    if not os.path.exists(BATCH):
        return 0
    batch = open(BATCH).read().split()
    open(FAILS, "a").write("".join(f + "\n" for f in batch))
    fails = open(FAILS).read().split()
    dead = [f for f in batch if fails.count(f) >= MAX_FAILS]
    if dead:
        open(SEEN, "a").write("".join(f + "\n" for f in dead))
        print(" ".join(dead))
    return 0


def selftest():
    tr = {"mimeType": DOC, "fileId": "T", "title": "Standup - Transcript"}
    gn = {"mimeType": DOC, "fileId": "G", "title": "Standup - Notes by Gemini"}
    team = [{"email": f"p{i}@x"} for i in range(4)]
    me_no = team + [{"self": True, "responseStatus": "declined"}]
    room = [{"email": "room@x", "resource": True}]
    ev = lambda att, who=team, title="Standup": {"summary": title, "attachments": att, "attendees": who}
    assert [a["fileId"] for _, a in pick([ev([gn, tr])], set())] == ["T"]
    assert [a["fileId"] for _, a in pick([ev([gn])], set())] == ["G"]
    assert pick([ev([tr])], {"T"}) == []
    assert pick([ev([tr], me_no)], set()) == []
    assert pick([ev([{"mimeType": "application/pdf", "fileId": "P", "title": "Transcript"}])], set()) == []
    assert pick([ev([gn], team[:2] + room)], set()) == []  # 1:1 in a room: the room does not count
    assert len(pick([ev([gn], team[:3])], set())) == 1
    rd = "{{PRODUCT}} Team - Roadmap|Fortnightly Ops"
    assert len(pick([ev([gn], title="{{PRODUCT}} Product Team - Fortnightly Ops meeting")], set(), rd)) == 1
    assert pick([ev([gn], title="Grow Users - Roadmap")], set(), rd) == []
    assert slug("CH: Release 3 / Standup!") == "ch-release-3-standup"
    import tempfile, io, contextlib  # retry ceiling: a transcript is given up after MAX_FAILS failed rounds
    global SEEN, BATCH, FAILS
    keep, d = (SEEN, BATCH, FAILS), tempfile.mkdtemp()
    SEEN, BATCH, FAILS = d + "/seen", d + "/batch", d + "/fails"
    try:
        runs = []
        for _ in range(MAX_FAILS):
            open(BATCH, "w").write("A\nB\n")
            with contextlib.redirect_stdout(io.StringIO()) as out:
                fail()
            runs.append(out.getvalue().split())
        assert runs[-1] == ["A", "B"] and all(r == [] for r in runs[:-1]), runs
        assert open(SEEN).read().split() == ["A", "B"]
    finally:
        SEEN, BATCH, FAILS = keep
    print("ok")


if __name__ == "__main__":
    os.makedirs(HERE + "/.out", exist_ok=True)
    if "--selftest" in sys.argv:
        selftest(); sys.exit(0)
    try:
        sys.exit(mark() if "--mark" in sys.argv else fail() if "--fail" in sys.argv else gate())
    except Exception as ex:  # no network, expired token: no model run, and say why in the launchd log
        print(f"gate error: {ex}", file=sys.stderr)
        sys.exit(1)

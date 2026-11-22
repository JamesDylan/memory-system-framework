#!/usr/bin/env /usr/bin/python3
"""Stage 2 of team-sync: {{OWNER}} approves the draft in Slack, this script publishes it to the canvas. No model.
  ./canvas.py post      post .out/canvas.md to SEAT_OUT_CHANNEL for review (run.sh calls it after a good round)
  ./canvas.py collect   read {{OWNER}}'s decision: ✅ publishes the draft, a reply in a code block publishes that text, ❌ discards
  ./canvas.py --selftest
Env: SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL, SEAT_OWNER_ID. Bot scopes: chat:write, reactions:read, channels:history, canvases:read, canvases:write."""
import datetime, glob, html, json, os, re, shutil, sys

HERE = os.environ.get("SEAT_DIR") or os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE + "/../meeting-ingest")
import review  # Slack helper, owner reactions vocabulary

CANVAS = re.search(r"^CANVAS_ID=(\S+)", open(HERE + "/seat.conf").read(), re.M).group(1)
DRAFT, DRAFTS = HERE + "/.out/canvas.md", HERE + "/.out/drafts"
INTRO = "Please feel free to add to this list"  # the canvas intro paragraph; summaries go directly below it, newest first
CANVAS_URL = f"https://{{SLACK_WORKSPACE}}.slack.com/docs/SLACK_TEAM_ID/{CANVAS}"
STALE_DAYS = 7
TODAY = datetime.date.today()


def meeting():
    """(title, YYYY-MM-DD) from the header gate.py wrote; the Start date is local time, unlike Gemini's UTC date."""
    head = open(sorted(glob.glob(HERE + "/.in/*.txt"))[0]).read(2000)
    return re.search(r"^Meeting: (.*)$", head, re.M).group(1), re.search(r"^Start: (\d{4}-\d\d-\d\d)", head, re.M).group(1)


LABEL = "**Discussion topics:**"


def to_md(s):
    """A Slack reply back to canvas markdown. A reply in a code block is taken as typed."""
    s = html.unescape(s).strip()
    if s.startswith("```") and s.endswith("```"):
        s = s[3:-3].strip()
        return s if s.startswith(LABEL) else LABEL + "\n\n" + s  # a pasted edit often starts at the first bullet
    s = re.sub(r"<@(U\w+)(\|[^>]*)?>", r"![](@\1)", s)
    s = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"[\2](\1)", s)
    s = re.sub(r"<(https?://[^>]+)>", r"\1", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"**\1**", s)
    s = re.sub(r"^(\s*)◦ ", r"\1  - ", s, flags=re.M)
    return re.sub(r"^(\s*)• ", r"\1- ", s, flags=re.M)


def post():
    title, date = meeting()
    text = open(DRAFT).read().strip()
    ts = review.say(f"*Canvas draft* · {title} · {date}\n✅ publish to <{CANVAS_URL}|the PM team canvas> · ❌ discard · "
                    f"or reply in this thread with the full new text in a code block to publish that instead\n```\n{text}\n```")
    os.makedirs(DRAFTS, exist_ok=True)
    json.dump({"title": title, "date": date, "text": text, "ts": ts, "channel": os.environ["SEAT_OUT_CHANNEL"],
               "posted": TODAY.isoformat()}, open(f"{DRAFTS}/{date}.json", "w"), indent=2, ensure_ascii=False)
    return 0


def publish(text, date, title):
    found = review.slack("canvases.sections.lookup", canvas_id=CANVAS, criteria={"contains_text": INTRO}).get("sections", [])
    if len(found) != 1:  # never guess where the summary goes
        raise RuntimeError(f"canvas intro found {len(found)} times; not published")
    review.slack("canvases.edit", canvas_id=CANVAS, changes=[{"operation": "insert_after", "section_id": found[0]["id"],
                 "document_content": {"type": "markdown", "markdown": f"{heading(date, title)}\n\n{text}\n"}}])


def heading(date, title):
    # shortcut: plain bold text; the API rejects slack_date chips (canvas_editing_failed, tested 2026-11-18). Retry if Slack adds them.
    return f"**{datetime.date.fromisoformat(date):%a %-d %b %Y} · {title}**"


def close(f, d, why):
    review.say(why, d["ts"])
    os.makedirs(DRAFTS + "/done", exist_ok=True)
    json.dump(d, open(f, "w"), indent=2, ensure_ascii=False)
    shutil.move(f, DRAFTS + "/done/" + os.path.basename(f))


def collect():
    owner = os.environ["SEAT_OWNER_ID"]
    for f in sorted(glob.glob(DRAFTS + "/*.json")):
        d = json.load(open(f))
        msgs = review.slack("conversations.replies", channel=d["channel"], ts=d["ts"], limit=200).get("messages", [])
        # A reply in a code block is {{OWNER}}'s own text: approval and edit in one. Other replies (questions) are ignored.
        edits = [m["text"] for m in msgs if m.get("user") == owner and m.get("ts") != d["ts"]
                 and html.unescape(m.get("text", "")).strip().startswith("```")]
        text = to_md(edits[-1]) if edits else d["text"]
        msg = review.slack("reactions.get", channel=d["channel"], timestamp=d["ts"], full="true")["message"]
        mine = {r["name"].split("::")[0] for r in msg.get("reactions", []) if owner in r.get("users", [])}
        if d.get("published") or (not mine & review.NO and (edits or mine & review.YES)):
            if not d.get("published"):
                publish(text, d["date"], d["title"])
                d.update(published=TODAY.isoformat(), text=text)
                json.dump(d, open(f, "w"), indent=2, ensure_ascii=False)  # before the reply: a failed reply must not publish twice
            close(f, d, f"Published to <{CANVAS_URL}|the canvas>.")
        elif mine & review.NO and not mine & review.YES:
            close(f, d, "Discarded. Nothing was published.")
        elif (TODAY - datetime.date.fromisoformat(d["posted"])).days >= STALE_DAYS:
            close(f, d, f"No decision after {STALE_DAYS} days. Dropped; nothing was published.")
    return 0


def selftest():
    import tempfile
    global DRAFT, DRAFTS, HERE
    tmp = tempfile.mkdtemp()
    HERE, DRAFT, DRAFTS = tmp, tmp + "/canvas.md", tmp + "/drafts"
    os.makedirs(tmp + "/.in")
    open(tmp + "/.in/2026-11-18-x.txt", "w").write("Meeting: {{PRODUCT}} Product Team - Fortnightly Ops meeting\nStart: 2026-11-18T14:00:00+13:00\n\nNov 18 notes")
    open(DRAFT, "w").write("**Discussion topics:**\n\n- A\n\n**Actions:**\n\n- [ ] **All:** B\n")
    calls, R, replies = [], {}, []

    def fake(method, **a):
        calls.append((method, a))
        if method == "chat.postMessage":
            return {"ts": f"{len(calls)}.0"}
        if method == "conversations.replies":
            return {"messages": [{"user": "U1", "ts": a["ts"]}] + replies}
        if method == "reactions.get":
            return {"message": {"reactions": R.get(a["timestamp"], [])}}
        if method == "canvases.sections.lookup":
            return {"sections": [{"id": "S1"}]}
        return {}
    review.slack = fake
    os.environ.update(SEAT_OUT_CHANNEL="C1", SEAT_OWNER_ID="U1")
    post()
    ts = calls[0][1].get("ts") or "1.0"
    assert "- [ ] **All:** B" in calls[0][1]["text"] and os.path.exists(DRAFTS + "/2026-11-18.json")
    collect()  # no decision yet
    assert not any(m == "canvases.edit" for m, _ in calls) and os.path.exists(DRAFTS + "/2026-11-18.json")
    R[ts] = [{"name": "white_check_mark", "users": ["EVIL"]}]
    replies.append({"user": "EVIL", "ts": "9.0", "text": "```injected```"})
    replies.append({"user": "U1", "ts": "9.05", "text": "can you make it shorter?"})
    collect()  # someone else's ✅ and code block, and {{OWNER}}'s plain question, do not publish
    assert not any(m == "canvases.edit" for m, _ in calls)
    replies.append({"user": "U1", "ts": "9.1", "text": "```- Ginger shared [the deck](https://x.io/d) &amp; more\n- B```"})
    collect()  # {{OWNER}}'s code-block reply alone publishes it, with the missing label added
    edit = [a for m, a in calls if m == "canvases.edit"]
    assert len(edit) == 1 and edit[0]["changes"][0]["section_id"] == "S1", edit
    md = edit[0]["changes"][0]["document_content"]["markdown"]
    assert md.startswith("**Wed 18 Nov 2026 · {{PRODUCT}} Product Team - Fortnightly Ops meeting**\n\n**Discussion topics:**\n\n- Ginger shared [the deck](https://x.io/d) & more\n- B"), md
    assert os.path.exists(DRAFTS + "/done/2026-11-18.json") and "Published" in calls[-1][1]["text"]
    assert to_md("```\n**Discussion topics:**\n\n- x\n```") == "**Discussion topics:**\n\n- x"
    assert to_md("*Discussion topics:*\n• Ginger <https://x.io/d|deck>\n<@U02> to do") == "**Discussion topics:**\n- Ginger [deck](https://x.io/d)\n![](@U02) to do"
    print("ok")


if __name__ == "__main__":
    cmd = (sys.argv + [""])[1]
    if cmd == "--selftest":
        selftest(); sys.exit(0)
    try:
        sys.exit({"post": post, "collect": collect}[cmd]())
    except KeyError:
        sys.exit(__doc__)
    except Exception as ex:  # Slack down, missing scope: log and stop; the next run retries
        print(f"canvas error: {ex}", file=sys.stderr)
        sys.exit(1)

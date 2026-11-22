#!/usr/bin/env /usr/bin/python3
"""Job queue for the dispatcher seat. No model.
  ./dispatch.py next          claim the oldest open job in ../jobs (status open → claimed), print its path; exit 1 if none
  ./dispatch.py finish <job>  after the round: hub script, reply in the source thread, commit, status done (or failed)
  ./dispatch.py --selftest
Env: SLACK_BOT_TOKEN, SEAT_OUT_CHANNEL (via review.py)."""
import glob, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE) + "/meeting-ingest")
import review  # shortcut: reuses meeting-ingest's Slack, link and commit helpers; move them to a shared module at the third seat

JOBS, NOTE = os.path.dirname(HERE) + "/jobs", HERE + "/.out/note.txt"


def field(t, k):
    m = re.search(rf'^{k}: "?(.*?)"?$', t, re.M)
    return m and m.group(1)


def set_status(path, s):
    t = open(path).read()
    open(path, "w").write(re.sub(r"^status: \S+$", f"status: {s}", t, 1, re.M))


def next_job():
    for j in sorted(glob.glob(JOBS + "/*.md")):
        t = open(j).read()
        if field(t, "status") == "open" and field(t, "formula") == "new-project":
            set_status(j, "claimed")  # a crashed round leaves it claimed, not retried in a loop of paid runs
            print(j)
            return 0
    return 1


def finish(j):
    j = os.path.abspath(j)  # git runs from the vault root
    t = open(j).read()
    name, thread = field(t, "name"), field(t, "source_thread")
    rel = f"1_PROJECTS/{{ORG}}/{name}"
    files = [f"{review.VAULT}/{rel}/{f}.md" for f in ("BRIEF", "STATE", "LOG")]
    note = open(NOTE).read().strip() if os.path.exists(NOTE) else ""
    if not all(map(os.path.exists, files)) or not note:
        set_status(j, "failed")
        review.say(f"⚠️ new-project `{name}` failed: the round did not write all three files and a note. Log: ~/.config/dispatcher.log", thread)
        return 1
    subprocess.run(["/usr/bin/python3", f"{review.VAULT}/.scripts/make-initiative-hubs.py"], check=True, capture_output=True)
    set_status(j, "done")
    review.say(f"Created {review.link(rel + '/STATE.md', name)} (BRIEF, STATE, LOG, hub). Review the git diff.\n{note}", thread)
    review.commit([*files, f"{review.VAULT}/{rel}/{name}.md", j], f"dispatcher: new-project {name} ({review.TODAY})")
    return 0


def selftest():
    import tempfile
    global JOBS
    JOBS = tempfile.mkdtemp()
    open(JOBS + "/a.md", "w").write('---\ntype: job\nformula: new-project\nname: "X"\nstatus: done\n---\n')
    open(JOBS + "/b.md", "w").write('---\ntype: job\nformula: new-project\nname: "Y Z"\nstatus: open\n---\n')
    assert next_job() == 0 and field(open(JOBS + "/b.md").read(), "status") == "claimed"
    assert next_job() == 1  # claimed is not picked again
    assert field(open(JOBS + "/b.md").read(), "name") == "Y Z"
    print("ok")


if __name__ == "__main__":
    cmd = (sys.argv + [""])[1]
    if cmd == "--selftest":
        selftest(); sys.exit(0)
    if cmd == "next":
        sys.exit(next_job())
    if cmd == "finish" and len(sys.argv) == 3:
        sys.exit(finish(sys.argv[2]))
    sys.exit(__doc__)

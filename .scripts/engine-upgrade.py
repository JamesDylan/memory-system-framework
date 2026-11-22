#!/usr/bin/env python3
"""Upgrade this vault's engine files to another engine tag, using engine.lock.

Usage (from anywhere; the vault is the folder above .scripts/):
  python3 .scripts/engine-upgrade.py <tag> [--repo <url-or-path>] [--allow-dirty]
  python3 .scripts/engine-upgrade.py --adopt <tag> --values <answers.json> [--repo <url-or-path>] [--allow-dirty]
  python3 .scripts/engine-upgrade.py --selftest

Clones the tag (shallow) into a temp folder and installs it there with the engine's own
init-vault.py and the lock's organisation values, so the fill rules live in one place.
Then, for each engine file (shared vault only):
  unchanged here, changed upstream     -> replaced
  changed here, unchanged upstream     -> local edit kept
  changed here and upstream            -> conflict: upstream copy written to <file>.upstream
  new upstream (or missing here)       -> added
  gone upstream                        -> listed, not deleted, dropped from the lock
It rewrites engine.lock (a conflict keeps its old hash, so lint still shows the drift) and
never commits. It refuses to run on a dirty git tree unless --allow-dirty.
--adopt writes a first lock for a vault that has none (hashes from the filled tag) and lists
every engine file that differs from the tag. --values is a JSON with the organisation values
(ORG and PRODUCT at least; same keys as templates/answers.example.json).
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = "engine.lock"


def sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except FileNotFoundError:
        return None


def run(*cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"engine-upgrade: {' '.join(cmd[:3])} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def build(tag, repo, values, tmp):
    """Install the tag into tmp with these organisation values. Returns (shared vault dir, its lock)."""
    run("git", "clone", "-q", "--depth", "1", "--branch", tag, repo, os.path.join(tmp, "src"))
    # person values are required by init but never written into engine files
    a = {**values, "OWNER_NAME": "Engine Upgrade", "SHARED_VAULT_PATH": os.path.join(tmp, "shared"), "PRIVATE_VAULT_PATH": os.path.join(tmp, "private")}
    json.dump(a, open(os.path.join(tmp, "answers.json"), "w"))
    run(sys.executable, os.path.join(tmp, "src", "init-vault.py"), os.path.join(tmp, "answers.json"))
    shared = os.path.join(tmp, "shared")
    if not os.path.isfile(os.path.join(shared, LOCK)):
        sys.exit(f"engine-upgrade: {tag} writes no {LOCK}; it predates engine.lock, so it cannot be used here")
    return shared, json.load(open(os.path.join(shared, LOCK), encoding="utf-8"))


def write_lock(vault, tag, repo, values, files):
    lock = {"engine": tag, "repo": repo, "values": values, "files": dict(sorted(files.items()))}
    open(os.path.join(vault, LOCK), "w", encoding="utf-8").write(json.dumps(lock, indent=2) + "\n")


def upgrade(vault, tag, repo=None, allow_dirty=False, adopt_values=None):
    """Returns a dict of lists: replaced, kept, conflict, added, removed, (adopt) differs."""
    have = os.path.isfile(os.path.join(vault, LOCK))
    if adopt_values is None and not have:
        sys.exit(f"engine-upgrade: no {LOCK} in {vault}. Use --adopt <tag> --values <answers.json> first.")
    if adopt_values is not None and have:
        sys.exit(f"engine-upgrade: {vault} already has {LOCK}; --adopt is for a vault with none.")
    if not allow_dirty:
        r = subprocess.run(["git", "-C", vault, "status", "--porcelain"], capture_output=True, text=True)
        if r.returncode or r.stdout.strip():
            sys.exit("engine-upgrade: the vault's git tree is dirty (or not a git repo). Commit first, or pass --allow-dirty.")
    old = json.load(open(os.path.join(vault, LOCK), encoding="utf-8")) if have else {"values": adopt_values, "files": {}}
    repo = repo or old.get("repo")
    if not repo:
        sys.exit("engine-upgrade: no repo in the lock; pass --repo <url-or-path>")
    if os.path.isdir(repo):
        repo = os.path.abspath(repo)
    with tempfile.TemporaryDirectory() as tmp:
        up_dir, up = build(tag, repo, old["values"], tmp)
        upf, oldf = up["files"], old["files"]
        out = {k: [] for k in ("replaced", "kept", "conflict", "added", "removed", "differs")}
        if adopt_values is not None:  # a first lock: hashes from the filled tag, local files untouched
            out["differs"] = [p for p in sorted(upf) if sha(os.path.join(vault, p)) != upf[p]]
            write_lock(vault, tag, repo, up["values"], upf)
            return out
        files = {}
        for p in sorted(set(upf) | set(oldf)):
            here, new, was = sha(os.path.join(vault, p)), upf.get(p), oldf.get(p)
            take = lambda: (os.makedirs(os.path.dirname(os.path.join(vault, p)) or vault, exist_ok=True),
                            shutil.copy2(os.path.join(up_dir, p), os.path.join(vault, p)))
            if new is None:
                out["removed"].append(p)  # not deleted; no longer engine-owned, so out of the lock
            elif here is None:
                take(); out["added"].append(p); files[p] = new
            elif here == new:
                files[p] = new  # already what upstream has
            elif was is not None and here == was:
                take(); out["replaced"].append(p); files[p] = new
            elif was is not None and new == was:
                out["kept"].append(p); files[p] = was
            else:  # changed here and upstream (or new upstream but a different local file is in the way)
                shutil.copy2(os.path.join(up_dir, p), os.path.join(vault, p + ".upstream"))
                out["conflict"].append(p); files[p] = was or new
        write_lock(vault, tag, repo, old["values"], files)
        return out


def report(tag, out, adopt=False):
    if adopt:
        print(f"Adopted engine {tag}: wrote {LOCK}. {len(out['differs'])} engine file(s) differ from the filled tag:")
        print(*("  " + p for p in out["differs"]), sep="\n")
        return
    print(f"Engine upgraded to {tag}. Nothing committed.")
    for k, what in (("replaced", "Replaced"), ("added", "Added"), ("kept", "Local edit kept (upstream unchanged)"),
                    ("conflict", "Conflict: upstream copy in <file>.upstream; merge it, then delete the .upstream file"),
                    ("removed", "Removed upstream (not deleted here; delete it if you do not need it)")):
        print(f"\n{what}: {len(out[k])}")
        print(*("  " + p for p in out[k]), sep="\n") if out[k] else None
    print("\nNext: review `git diff`, run `node .scripts/lint.mjs`, then commit on a branch.")


def selftest():
    """Two tags of a tiny engine, a trial vault, every case in the table above. No network."""
    def write(base, rel, text):
        os.makedirs(os.path.dirname(os.path.join(base, rel)) or base, exist_ok=True)
        open(os.path.join(base, rel), "w").write(text)
    init = '''import json, os, re, sys, hashlib
a = json.load(open(sys.argv[1])); here = os.path.dirname(os.path.abspath(__file__)); s = a["SHARED_VAULT_PATH"]
v = {"ORG": a["ORG"], "PRODUCT": a["PRODUCT"]}; files = {}
for f in sorted(os.listdir(os.path.join(here, "eng"))):
    t = re.sub(r"\\{\\{([A-Z]+)\\}\\}", lambda m: v.get(m.group(1), m.group(0)), open(os.path.join(here, "eng", f)).read())
    os.makedirs(os.path.join(s, "eng"), exist_ok=True); open(os.path.join(s, "eng", f), "w").write(t)
    files["eng/" + f] = hashlib.sha256(t.encode()).hexdigest()
json.dump({"engine": "dev", "repo": "", "values": v, "files": files}, open(os.path.join(s, "engine.lock"), "w"))
'''
    git = lambda d, *a: run("git", "-c", "user.name=t", "-c", "user.email=t@t", *a, cwd=d)
    with tempfile.TemporaryDirectory() as t:
        eng, vault = os.path.join(t, "engine"), os.path.join(t, "vault")
        os.makedirs(eng); git(eng, "init", "-q")
        write(eng, "init-vault.py", init)
        for f, txt in {"same": "same {{ORG}}", "repl": "v1", "keep": "v1", "conf": "v1", "gone": "v1", "miss": "v1"}.items():
            write(eng, "eng/" + f, txt)
        git(eng, "add", "-A"); git(eng, "commit", "-qm", "1"); git(eng, "tag", "t1")
        for f, txt in {"repl": "v2 {{PRODUCT}}", "conf": "v2", "new": "new"}.items():
            write(eng, "eng/" + f, txt)
        os.remove(os.path.join(eng, "eng/gone"))
        git(eng, "add", "-A"); git(eng, "commit", "-qm", "2"); git(eng, "tag", "t2")
        # trial vault: adopt t1 (local "keep" already edited), then edit "conf", delete "miss"
        os.makedirs(vault); git(vault, "init", "-q")
        a = os.path.join(t, "values.json"); json.dump({"ORG": "Acme", "PRODUCT": "Widgets"}, open(a, "w"))
        for f in ("same", "repl", "keep", "conf", "gone", "miss"):
            write(vault, "eng/" + f, {"same": "same Acme", "keep": "local"}.get(f, "v1"))
        out = upgrade(vault, "t1", eng, allow_dirty=True, adopt_values=json.load(open(a)))
        assert out["differs"] == ["eng/keep"], out
        lock = json.load(open(os.path.join(vault, LOCK)))
        assert lock["engine"] == "t1" and lock["values"] == {"ORG": "Acme", "PRODUCT": "Widgets"} and len(lock["files"]) == 6, lock
        write(vault, "eng/conf", "local")
        os.remove(os.path.join(vault, "eng/miss"))
        git(vault, "add", "-A"); git(vault, "commit", "-qm", "vault")
        write(vault, "dirt", "x")
        try:
            upgrade(vault, "t2", eng); raise AssertionError("dirty tree accepted")
        except SystemExit as e:
            assert "dirty" in str(e), e
        os.remove(os.path.join(vault, "dirt"))
        out = upgrade(vault, "t2")  # repo from the lock
        rd = lambda f: open(os.path.join(vault, f)).read()
        assert out["replaced"] == ["eng/repl"] and rd("eng/repl") == "v2 Widgets", out
        assert out["kept"] == ["eng/keep"] and rd("eng/keep") == "local", out
        assert out["conflict"] == ["eng/conf"] and rd("eng/conf") == "local" and rd("eng/conf.upstream") == "v2", out
        assert sorted(out["added"]) == ["eng/miss", "eng/new"] and rd("eng/new") == "new", out
        assert out["removed"] == ["eng/gone"] and rd("eng/gone") == "v1", out
        lock2 = json.load(open(os.path.join(vault, LOCK)))
        assert lock2["engine"] == "t2" and "eng/gone" not in lock2["files"], lock2
        assert lock2["files"]["eng/conf"] == lock["files"]["eng/conf"], "a conflict keeps its old hash, so drift still shows"
        assert lock2["files"]["eng/keep"] == lock["files"]["eng/keep"] and lock2["files"]["eng/repl"] == sha(os.path.join(vault, "eng/repl"))
        try:
            upgrade(os.path.join(t, "engine"), "t2", allow_dirty=True); raise AssertionError("no lock accepted")
        except SystemExit as e:
            assert "no engine.lock" in str(e), e
    print("engine-upgrade selftest: ok")


def main(argv):
    if argv == ["--selftest"]:
        return selftest()
    opt = lambda k: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else None
    allow = "--allow-dirty" in argv
    if "--adopt" in argv:
        tag, vals = opt("--adopt"), opt("--values")
        if not tag or not vals:
            sys.exit(__doc__)
        values = json.load(open(vals, encoding="utf-8"))
        for k in ("ORG", "PRODUCT"):
            if not values.get(k):
                sys.exit(f"engine-upgrade: {vals} is missing {k}")
        report(tag, upgrade(ROOT, tag, opt("--repo"), allow, adopt_values=values), adopt=True)
    else:
        if not argv or argv[0].startswith("-"):
            sys.exit(__doc__)
        report(argv[0], upgrade(ROOT, argv[0], opt("--repo"), allow))


if __name__ == "__main__":
    main(sys.argv[1:])

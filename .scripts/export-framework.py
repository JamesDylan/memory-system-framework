#!/usr/bin/env python3
"""Export the portable framework of this vault. No organisation data.

Usage:
  python3 .scripts/export-framework.py <target-dir>           # copy + scrub report
  python3 .scripts/export-framework.py <target-dir> --check   # report only, copy nothing

Fail closed. Only files matched by 'include', 'remap' or 'remapDirs' in
.scripts/framework-export.json are copied. The target must be outside the vault.
Organisation and personal values are replaced with {{PLACEHOLDERS}} ('substitutions').
Exit 1 while any copied file still matches an organisation term after that. Do not push
the target until the exit code is 0.
"""
import fnmatch, json, os, re, shutil, sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(VAULT, ".scripts", "framework-export.json"), encoding="utf-8"))
SKIP_DIRS = {".git", ".claude", ".obsidian", "node_modules", "4_ARCHIVE"}


def match(path, patterns):
    return any(fnmatch.fnmatch(path, p) or path == p for p in patterns)


def vault_files():
    # os.walk does not follow the _private symlink, so walk only the private folders named in remapDirs.
    roots = [VAULT] + [os.path.join(VAULT, p) for p in CFG.get("remapDirs", {}) if p.startswith("_private/")]
    for root, dirs, files in (w for r in roots for w in os.walk(r)):
        rel_root = os.path.relpath(root, VAULT)
        dirs[:] = [d for d in dirs if not (rel_root == "." and d in SKIP_DIRS)]
        for f in files:
            yield os.path.normpath(os.path.join(rel_root, f)).replace(os.sep, "/")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    if not args:
        sys.exit(__doc__)
    target = os.path.abspath(os.path.expanduser(args[0]))
    if target == VAULT or target.startswith(VAULT + os.sep):
        sys.exit("Target must be outside the vault.")

    plan = {}
    for rel in vault_files():
        if rel in CFG["remap"]:
            plan[rel] = CFG["remap"][rel]
            continue
        pre = max((p for p in CFG.get("remapDirs", {}) if rel.startswith(p)), key=len, default=None)
        if pre is not None and not match(rel, CFG["exclude"]):
            plan[rel] = CFG["remapDirs"][pre] + rel[len(pre):]
        elif match(rel, CFG["include"]) and not match(rel, CFG["exclude"]):
            plan[rel] = rel
    # walk does not follow the private mount; take remap sources by direct path.
    for src, dst in CFG["remap"].items():
        if src not in plan and os.path.isfile(os.path.join(VAULT, src)):
            plan[src] = dst
    missing = [p for p in list(CFG["remap"]) + [i for i in CFG["include"] if "*" not in i] if p not in plan]

    subs = [(re.compile(a), b) for a, b in CFG.get("substitutions", [])]
    def scrub(text):
        for rx, rep in subs:
            text = rx.sub(rep, text)
        return text
    plan = {src: scrub(dst) for src, dst in plan.items()}
    terms = [re.compile(t) for t in CFG["orgTerms"]]
    hits, path_hits = {}, []
    for src, dst in sorted(plan.items()):
        if any(t.search(dst) for t in terms):
            path_hits.append(dst)
        try:
            text = open(os.path.join(VAULT, src), encoding="utf-8").read()
        except UnicodeDecodeError:
            hits[dst] = [(0, "binary file: check by hand")]
            continue
        text = scrub(text)
        found = [(n, line.strip()[:160]) for n, line in enumerate(text.splitlines(), 1)
                 if any(t.search(line) for t in terms)]
        if found:
            hits[dst] = found
        if not check:
            out = os.path.join(target, dst)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write(text)
            shutil.copymode(os.path.join(VAULT, src), out)

    total = sum(len(v) for v in hits.values())
    lines = ["# Scrub report", "",
             f"Files in export: {len(plan)}. Files with organisation terms: {len(hits)}. Lines to fix: {total}.",
             "", "The export is not safe to push while this number is above zero.", ""]
    if path_hits:
        lines += ["## Paths that name the organisation", ""] + [f"- `{p}`" for p in path_hits] + [""]
    if missing:
        lines += ["## Listed in the manifest but not found", ""] + [f"- `{p}`" for p in missing] + [""]
    lines += ["## Needs a blank template (never copied)", ""] + [f"- `{p}`" for p in CFG["needsTemplate"]] + [""]
    lines += ["## Lines to fix, by file", ""]
    for dst, found in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        lines += [f"### `{dst}` ({len(found)})", ""] + [f"- L{n}: {t}" for n, t in found] + [""]
    report = "\n".join(lines)
    # The report quotes organisation detail, so it is written beside the target, not inside it.
    report_path = target.rstrip("/") + ".SCRUB_REPORT.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    open(report_path, "w", encoding="utf-8").write(report)
    print(f"{'Checked' if check else 'Copied'} {len(plan)} files. {len(hits)} files, {total} lines still carry organisation terms.")
    print(f"Report: {report_path}")
    sys.exit(1 if (total or path_hits) else 0)


if __name__ == "__main__":
    main()

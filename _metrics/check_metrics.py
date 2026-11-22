#!/usr/bin/env python3
"""
check_metrics.py — keeps one number true across a whole vault.

The problem this solves: prose needs numbers inline to be readable, so copies
are unavoidable. What is avoidable is copies you cannot *find*. Every copy
carries a marker tying it to the registry, and this script tells you, in
seconds, exactly which file and line has drifted.

    Marker convention:   19.2% <!--m:churn.company.annual-->

Usage
    python3 check_metrics.py                          # check the vault
    python3 check_metrics.py --root <vault root>
    python3 check_metrics.py --set churn.company.annual=18.4
    python3 check_metrics.py --set acq.registered_companies.weekly=1200 --asof 2026-09-04
    python3 check_metrics.py --set id1=v1 --set id2=v2 --asof 2026-09-04   # weekly batch;
                                                                            # auto-runs the check after
    python3 check_metrics.py --list --status disputed
    python3 check_metrics.py --json                    # machine-readable, for CI

Exit codes:  0 clean · 1 errors found · 2 bad invocation
No third-party dependencies beyond PyYAML.
"""

import argparse, csv, datetime as dt, json, math, os, re, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required:  pip3 install pyyaml")

MARKER_RE = re.compile(r"<!--\s*m:([A-Za-z0-9_.\-]+)\s*-->")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
IGNORE_LINE_RE = re.compile(r"<!--\s*metrics-ignore\s*-->")
FENCE_ON_RE = re.compile(r"<!--\s*metrics-ignore-start\s*-->")
FENCE_OFF_RE = re.compile(r"<!--\s*metrics-ignore-end\s*-->")
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")  # a marker inside `code` is an example, not a copy
VALUE_BEFORE_RE = re.compile(
    r"(?P<val>[~≈≥≤<>]?\s*(?:NZ\$|US\$|AU\$|EUR|€|\$|£)?\s*"
    r"-?\d[\d,\s]*(?:\.\d+)?\s*(?:[kKmMbB]\b|%|pp)?)\s*$"
)
SCALE = {"k": 1e3, "m": 1e6, "b": 1e9}
REQUIRED = ["id", "name", "value", "unit", "period", "denominator",
            "altitude", "as_of", "source", "owner", "status"]

RED, YEL, BLU, DIM, BOLD, OFF = "\033[31m", "\033[33m", "\033[34m", "\033[2m", "\033[1m", "\033[0m"


def colour(on):
    if not on:
        globals().update(RED="", YEL="", BLU="", DIM="", BOLD="", OFF="")


# ---------------------------------------------------------------- value parsing
def parse_value(raw):
    """'~7,000' -> 7000.0 · '19.2%' -> 19.2 · 'NZ$120.9M' -> 120900000.0"""
    if raw is None:
        return None
    s = str(raw).strip()
    s = re.sub(r"^[~≈≥≤<>\s]+", "", s)
    s = re.sub(r"^(NZ\$|US\$|AU\$|EUR|€|\$|£)\s*", "", s, flags=re.I)
    s = s.replace(",", "").replace(" ", "")
    mult = 1.0
    m = re.search(r"([kKmMbB])$", s)
    if m:
        mult = SCALE[m.group(1).lower()]
        s = s[: m.start()]
    s = s.rstrip("%").replace("pp", "")
    try:
        return float(s) * mult
    except ValueError:
        return None


def mantissa(x):
    if x == 0:
        return 0.0
    return abs(x) / (10 ** math.floor(math.log10(abs(x))))


def compare(doc_val, reg_val, tol=1e-9):
    """-> 'match' | 'magnitude' | 'drift'"""
    if doc_val is None or reg_val is None:
        return "drift"
    if abs(doc_val - reg_val) <= tol * max(1.0, abs(reg_val)):
        return "match"
    if abs(mantissa(doc_val) - mantissa(reg_val)) <= 1e-6:
        return "magnitude"
    return "drift"


def period_window(text, start, end):
    """Text around a marker for the period guard, cut at the nearest '|' on each
    side so a table row's other columns (e.g. "+80% YoY") do not leak in."""
    lo = max(max(0, start - 90), text.rfind("|", 0, start) + 1)
    bar = text.find("|", end)
    hi = min(end + 40, bar if bar != -1 else len(text))
    return text[lo:hi]


assert period_window("| a | 528 X | +80% YoY |", 10, 11) == " 528 X "
assert period_window("annual 5 X", 9, 10) == "annual 5 X"


# ---------------------------------------------------------------- findings
class Finding:
    def __init__(self, sev, code, path, line, msg, hint=""):
        self.sev, self.code, self.path, self.line, self.msg, self.hint = \
            sev, code, str(path), line, msg, hint

    def as_dict(self):
        return dict(severity=self.sev, code=self.code, file=self.path,
                    line=self.line, message=self.msg, hint=self.hint)


# ---------------------------------------------------------------- vault walk
def live_lines(lines, ignore_sections):
    """Yield (lineno, text) skipping historical/changelog sections and fenced blocks.

    History tables legitimately record superseded values — linting them would
    punish exactly the audit trail we want people to keep.
    """
    pats = [re.compile(p, re.I) for p in (ignore_sections or [])]
    skipping_section, skip_level, fenced = False, 0, False
    for ln, text in enumerate(lines, 1):
        if FENCE_OFF_RE.search(text):
            fenced = False
            continue
        if FENCE_ON_RE.search(text):
            fenced = True
            continue
        h = HEADING_RE.match(text)
        if h:
            level, title = len(h.group(1)), h.group(2)
            if skipping_section and level <= skip_level:
                skipping_section = False
            if any(p.search(title) for p in pats):
                skipping_section, skip_level = True, level
                continue
        if fenced or skipping_section or IGNORE_LINE_RE.search(text):
            continue
        yield ln, text


def gather_files(root, cfg):
    inc = cfg.get("scan_globs", ["**/*.md"])
    exc = cfg.get("exclude_globs", [])
    seen, out = set(), []
    for g in inc:
        for p in Path(root).glob(g):
            if not p.is_file() or p in seen:
                continue
            rel = p.relative_to(root).as_posix()
            if any(Path(rel).match(x) or rel.startswith(x.rstrip("*/")) for x in exc):
                continue
            seen.add(p)
            out.append(p)
    return sorted(out)


# ---------------------------------------------------------------- checks
def check_schema(metrics):
    out = []
    for m in metrics:
        mid = m.get("id", "<no id>")
        for f in REQUIRED:
            if m.get(f) in (None, ""):
                out.append(Finding("ERROR", "schema", "registry.yaml", 0,
                    f"{mid}: missing required field '{f}'",
                    "period, denominator and altitude are mandatory — that rule is what kills most drift."))
    return out


# Same windows as stalenessThresholdsDays in .scripts/lint.config.json.
STALE_DAYS_BY_PERIOD = {"weekly": 10, "monthly": 40, "quarterly": 100, "annual": 100, "point": 100}


def check_staleness(metrics, days, today=None):
    """days is the fallback window for a period not in STALE_DAYS_BY_PERIOD."""
    out, today = [], today or dt.date.today()
    for m in metrics:
        try:
            age = (today - dt.date.fromisoformat(str(m["as_of"]))).days
        except Exception:
            out.append(Finding("WARN", "as_of", "registry.yaml", 0,
                               f"{m['id']}: unparseable as_of '{m.get('as_of')}'"))
            continue
        if age > STALE_DAYS_BY_PERIOD.get(str(m.get("period", "")).lower(), days):
            out.append(Finding("WARN", "stale", "registry.yaml", 0,
                f"{m['id']} last confirmed {age} days ago ({m['as_of']}) — re-confirm or mark status: stale",
                f"source: {m.get('source','?')}"))
    return out


def check_markers(files, by_id, root, period_words, ignore_sections):
    out = []
    for p in files:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        rel = p.relative_to(root).as_posix()
        for ln, text in live_lines(lines, ignore_sections):
            # Blank out every marker's own comment text (same length, so offsets
            # still line up) before window-slicing for the period guard below —
            # otherwise a neighbouring marker's id (e.g. "...churn.company.annual")
            # can leak a period word into another marker's window, and a window
            # boundary can even slice a marker in half, leaving a stray fragment.
            masked_text = MARKER_RE.sub(lambda mm: " " * len(mm.group(0)), text)
            code_masked = CODE_SPAN_RE.sub(lambda mm: " " * len(mm.group(0)), text)
            for mk in MARKER_RE.finditer(code_masked):
                mid = mk.group(1)
                if mid not in by_id:
                    out.append(Finding("ERROR", "unknown-id", rel, ln,
                        f"marker <!--m:{mid}--> has no entry in the registry",
                        "add it to registry.yaml or fix the id"))
                    continue
                m = by_id[mid]
                before = text[: mk.start()]
                vm = VALUE_BEFORE_RE.search(before)
                if not vm:
                    out.append(Finding("ERROR", "no-value", rel, ln,
                        f"marker for {mid} has no value immediately before it",
                        "convention: <value> <!--m:id-->"))
                    continue
                doc_raw = vm.group("val").strip()
                verdict = compare(parse_value(doc_raw), parse_value(m["value"]))
                if verdict == "drift":
                    out.append(Finding("ERROR", "drift", rel, ln,
                        f"{mid}: doc says {doc_raw}, registry says {m['value']} ({m['unit']})",
                        f"registry as_of {m['as_of']} · {m.get('source','')}"))
                elif verdict == "magnitude":
                    out.append(Finding("WARN", "magnitude", rel, ln,
                        f"{mid}: doc says {doc_raw}, registry says {m['value']} — same digits, different magnitude",
                        f"unit is '{m['unit']}' — check for a k/M mix-up"))
                # period guard
                reg_period = str(m.get("period", "")).lower()
                window = period_window(masked_text, mk.start(), mk.end()).lower()
                for per, words in (period_words or {}).items():
                    if per == reg_period or not words:
                        continue
                    for w in words:
                        if w in window:
                            out.append(Finding("ERROR", "period", rel, ln,
                                f"{mid} is {reg_period}, but the text around it says '{w}'",
                                "this is the exact failure that produced the monthly/annual churn mislabel"))
                            break
                    else:
                        continue
                    break
    return out


def _near_ok(text, hit, near_re):
    if not near_re:
        return True
    lo, hi = max(0, hit.start() - 90), min(len(text), hit.end() + 90)
    return bool(near_re.search(text[lo:hi]))


def check_untagged_and_forbidden(files, metrics, root, ignore_sections):
    out = []
    alias_specs, forbid_specs = [], []
    for m in metrics:
        for a in m.get("aliases") or []:
            spec = {"pattern": a} if isinstance(a, str) else dict(a)
            try:
                spec["re"] = re.compile(spec["pattern"], re.I)
            except re.error as e:
                out.append(Finding("ERROR", "regex", "registry.yaml", 0,
                                   f"{m['id']}: bad alias pattern — {e}"))
                continue
            spec["near_re"] = re.compile(spec["near"], re.I) if spec.get("near") else None
            spec["metric"] = m
            alias_specs.append(spec)
        for f in m.get("forbidden") or []:
            spec = {"pattern": f} if isinstance(f, str) else dict(f)
            spec["re"] = re.compile(re.escape(spec["pattern"]) if spec.get("literal", True)
                                    else spec["pattern"], re.I)
            spec["metric"] = m
            forbid_specs.append(spec)

    for p in files:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        rel = p.relative_to(root).as_posix()
        for ln, text in live_lines(lines, ignore_sections):
            for spec in forbid_specs:
                for hit in spec["re"].finditer(text):
                    out.append(Finding("ERROR", "forbidden", rel, ln,
                        f"superseded text \"{hit.group(0)}\" — {spec['metric']['id']}",
                        spec.get("why", "")))
                    break
            tagged_spans = [(mk.start(), mk.end()) for mk in MARKER_RE.finditer(text)]
            for spec in alias_specs:
                for hit in spec["re"].finditer(text):
                    if not _near_ok(text, hit, spec["near_re"]):
                        continue
                    if any(s - 60 <= hit.end() <= e for s, e in tagged_spans):
                        continue
                    out.append(Finding("WARN", "untagged", rel, ln,
                        f"untagged copy of {spec['metric']['id']}: \"{hit.group(0)}\"",
                        f"add a marker:  {hit.group(0)} <!--m:{spec['metric']['id']}-->"))
                    break
    return out


def check_assertions(assertions, by_id):
    out = []
    ns = {m["id"].replace(".", "_").replace("-", "_"): parse_value(m["value"])
          for m in by_id.values()}
    safe = {"__builtins__": {}, "abs": abs, "min": min, "max": max, "round": round}
    for a in assertions or []:
        try:
            ok = bool(eval(a["expr"], safe, ns))
        except Exception as e:
            out.append(Finding("WARN", "assert-error", "registry.yaml", 0,
                               f"{a['id']}: could not evaluate — {e}"))
            continue
        if ok:
            continue
        fmt = dict(ns)
        for k, expr in (a.get("vars") or {}).items():
            try:
                v = eval(expr, safe, ns)
                fmt[k] = round(v, 2) if isinstance(v, float) else v
            except Exception:
                fmt[k] = "?"
        for k, v in list(fmt.items()):
            if isinstance(v, float) and v.is_integer():
                fmt[k] = int(v)
        try:
            msg = " ".join(str(a["message"]).format(**fmt).split())
        except Exception:
            msg = " ".join(str(a["message"]).split())
        # severity: WARN for an assertion known to fail while a dispute is open
        out.append(Finding(str(a.get("severity", "ERROR")).upper(), "assertion", "registry.yaml", 0,
                           f"{a['id']}: {msg}"))
    return out


# ---------------------------------------------------------------- --set
def set_value(reg_path, mid, new_value, asof, note):
    """Update one metric's value/as_of in place and append a history.csv row.

    Returns (old_value, stamped_asof) so callers doing several of these in a
    row (the weekly batch) can print one summary instead of one block each.
    """
    text = reg_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    start = None
    for i, l in enumerate(lines):
        if re.match(rf"^\s*-\s+id:\s*{re.escape(mid)}\s*$", l):
            start = i
            break
    if start is None:
        sys.exit(f"no metric with id '{mid}' in the registry")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^\s*-\s+id:\s", lines[j]) or re.match(r"^assertions:", lines[j]):
            end = j
            break
    old = None
    for j in range(start, end):
        vm = re.match(r"^(\s*value:\s*)(.+?)(\s*)$", lines[j])
        if vm:
            old = vm.group(2).strip()
            lines[j] = f"{vm.group(1)}{new_value}\n"
            break
    if old is None:
        sys.exit(f"'{mid}' has no value: line")
    stamped = asof or dt.date.today().isoformat()
    for j in range(start, end):
        am = re.match(r"^(\s*as_of:\s*)(.+?)(\s*)$", lines[j])
        if am:
            lines[j] = f"{am.group(1)}{stamped}\n"
            break
    reg_path.write_text("".join(lines), encoding="utf-8")

    hist = reg_path.parent / "history.csv"
    new_file = not hist.exists()
    with hist.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new_file:
            w.writerow(["changed_at", "id", "old_value", "new_value", "as_of", "note"])
        w.writerow([dt.datetime.now().isoformat(timespec="seconds"), mid,
                    old, new_value, stamped, note or ""])
    return old, stamped


def valid_set_expr(expr):
    """ID=VALUE where VALUE parses; anything else would make every marker drift."""
    return "=" in expr and parse_value(expr.split("=", 1)[1]) is not None


def selftest(reg_path):
    """Run set_value on a temp copy of the registry and check what it wrote."""
    import shutil, tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "registry.yaml"
        shutil.copy(reg_path, tmp)
        mid = yaml.safe_load(tmp.read_text(encoding="utf-8"))["metrics"][0]["id"]
        old, stamped = set_value(tmp, mid, "12,345", "2001-02-03", "selftest")
        m = {x["id"]: x for x in yaml.safe_load(tmp.read_text(encoding="utf-8"))["metrics"]}[mid]
        assert parse_value(m["value"]) == 12345.0, m["value"]
        assert str(m["as_of"]) == "2001-02-03", m["as_of"]
        rows = list(csv.reader((Path(d) / "history.csv").open(encoding="utf-8")))
        assert rows[0][0] == "changed_at" and rows[-1][1:] == [mid, old, "12,345", "2001-02-03", "selftest"], rows
    assert parse_value("NZ$1.5M") == 1.5e6
    day = dt.date(2026, 11, 21)
    stale = lambda period, age, fallback=75: [f.code for f in check_staleness(
        [dict(id="x", period=period, as_of=(day - dt.timedelta(days=age)).isoformat())], fallback, day)]
    assert stale("weekly", 15) == ["stale"] and stale("weekly", 10) == []
    assert stale("monthly", 41) == ["stale"] and stale("annual", 99) == []
    assert stale("fortnightly", 20, fallback=19) == ["stale"]
    assert valid_set_expr("a.b=18.4") and not valid_set_expr("a.b=abc") and not valid_set_expr("a.b")
    print("selftest ok")
    return 0


# ---------------------------------------------------------------- report
def report(findings, args, n_files, n_metrics):
    errs = [f for f in findings if f.sev == "ERROR"]
    warns = [f for f in findings if f.sev == "WARN"]
    if args.json:
        print(json.dumps(dict(errors=len(errs), warnings=len(warns),
                              files_scanned=n_files, metrics=n_metrics,
                              findings=[f.as_dict() for f in findings]), indent=2))
        return 1 if errs else 0

    by_file = {}
    for f in findings:
        by_file.setdefault(f.path, []).append(f)
    for path in sorted(by_file):
        print(f"\n{BOLD}{path}{OFF}")
        for f in sorted(by_file[path], key=lambda x: (x.line, x.code)):
            tag = f"{RED}ERROR{OFF}" if f.sev == "ERROR" else f"{YEL}warn {OFF}"
            loc = f"{f.line}" if f.line else "-"
            print(f"  {loc:>5}  {tag}  {DIM}[{f.code}]{OFF} {f.msg}")
            if f.hint and not args.quiet:
                print(f"         {DIM}↳ {f.hint}{OFF}")

    print(f"\n{BOLD}{'—'*66}{OFF}")
    print(f"  {n_metrics} metrics · {n_files} files scanned · "
          f"{RED}{len(errs)} errors{OFF} · {YEL}{len(warns)} warnings{OFF}")
    if not findings:
        print(f"  {BOLD}clean{OFF} — every marked copy matches the registry.")
    return 1 if errs else 0


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Verify vault metrics against the registry.")
    ap.add_argument("--root", default=None, help="vault root (default: registry config, else cwd)")
    ap.add_argument("--registry", default=None, help="path to registry.yaml")
    ap.add_argument("--set", dest="setexprs", metavar="ID=VALUE", action="append",
                     help="update one metric value; repeat --set for a weekly batch "
                          "(one command for every metric that moved, instead of one per metric)")
    ap.add_argument("--asof", help="as_of date applied to every --set in this run (default: today)")
    ap.add_argument("--note", help="history note applied to every --set in this run")
    ap.add_argument("--no-check", action="store_true",
                     help="with --set, skip the automatic full check afterwards")
    ap.add_argument("--list", action="store_true", help="list metrics and exit")
    ap.add_argument("--status", help="filter --list by status")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="suppress hint lines")
    ap.add_argument("--no-colour", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="test --set on a temp copy of the registry and exit")
    args = ap.parse_args()
    colour(not args.no_colour and sys.stdout.isatty() and not args.json)

    reg_path = Path(args.registry) if args.registry else Path(__file__).with_name("registry.yaml")
    if not reg_path.exists():
        sys.exit(f"registry not found: {reg_path}")
    if args.selftest:
        return selftest(reg_path)

    if args.setexprs:
        # validate the whole batch before writing anything, so a typo cannot half-apply it
        for expr in args.setexprs:
            if not valid_set_expr(expr):
                print(f"--set expects ID=VALUE with a numeric value (got {expr!r}); registry not changed",
                      file=sys.stderr)
                return 2
        for expr in args.setexprs:
            mid, val = expr.split("=", 1)
            old, stamped = set_value(reg_path, mid.strip(), val.strip(), args.asof, args.note)
            print(f"{BOLD}{mid.strip()}{OFF}  {old} → {val.strip()}   as_of {stamped}")
        print(f"{DIM}logged to {reg_path.parent / 'history.csv'}{OFF}")
        try:  # dashboard is a view only; never let it block a --set
            sys.path.insert(0, str(Path(__file__).parent))
            from build_dashboard import build
            build(reg_path, reg_path.with_name("METRICS_DASHBOARD.md"))
            print(f"{DIM}refreshed METRICS_DASHBOARD.md{OFF}")
        except Exception as e:
            print(f"{YEL}dashboard not refreshed: {e}{OFF}", file=sys.stderr)
        if args.no_check:
            print("\nSkipped the automatic check (--no-check). Run without it to see what needs fixing.")
            return 0
        print(f"\n{DIM}Running the full check to find every copy that now disagrees...{OFF}")
        # fall through to the check below, against the registry we just wrote.

    reg = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
    cfg = reg.get("config", {}) or {}
    metrics = reg.get("metrics", []) or []
    by_id = {m["id"]: m for m in metrics if "id" in m}

    if args.list:
        for m in metrics:
            if args.status and m.get("status") != args.status:
                continue
            print(f"{m['id']:<46} {str(m['value']):>12} {m['unit']:<26} "
                  f"{m['period']:<8} {m['status']:<11} {m['as_of']}")
        return 0

    root = Path(args.root or cfg.get("vault_root") or ".").expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"vault root not a directory: {root}")
    files = gather_files(root, cfg)

    findings = []
    findings += check_schema(metrics)
    findings += check_staleness(metrics, int(cfg.get("stale_after_days", 90)))
    ignore_sections = cfg.get("ignore_sections") or []
    findings += check_markers(files, by_id, root, cfg.get("period_words"), ignore_sections)
    findings += check_untagged_and_forbidden(files, metrics, root, ignore_sections)
    findings += check_assertions(reg.get("assertions"), by_id)

    return report(findings, args, len(files), len(metrics))


if __name__ == "__main__":
    sys.exit(main())

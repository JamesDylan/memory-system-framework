#!/usr/bin/env node
// lint.mjs — the DETERMINISTIC half of the `lint` skill.
//
// Runs the mechanical checks that don't need an LLM: dead pointers, staleness,
// missing stamps, orphan skills, inbox age, index/changelog drift, deployed-skill
// drift, run integrity (did the thing actually run), STATE field budgets, typed facts, the
// rejection loop (repeated reason chips, PLAN S2.3) and what a new vault has not filled in yet. Costs zero
// agent tokens. The judgment half (semantic single-source-of-truth conflicts,
// "is this stale in meaning", what-to-think-about-next) stays with the agent —
// see 3_RESOURCES/AI Skills/lint/SKILL.md.
//
// Usage:
//   node .scripts/lint.mjs                 # human-readable markdown report to stdout
//   node .scripts/lint.mjs --strict        # exit 1 if any 🔴 finding (for cron alerting)
//   node .scripts/lint.mjs --json          # machine-readable JSON instead of markdown
//   node .scripts/lint.mjs --shared        # shared-vault checks only (CI: no _private mount, no Mac)
//
// Zero dependencies. Node 22+ (uses fs/promises, import assertions avoided).

import { readFile, readdir, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { SESSIONS, parseSessions, chipRule } from "./scorecard.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const args = new Set(process.argv.slice(2));
const AS_JSON = args.has("--json");
const STRICT = args.has("--strict");
// Move 11h: CI has the repo only. Skip what needs the private vault or this Mac, keep everything else.
const SHARED = args.has("--shared");
const PRIV = (cfg) => cfg.privateBoundary?.mount || "_private";

const cfg = JSON.parse(await readFile(join(ROOT, ".scripts/lint.config.json"), "utf8"));

// Extensions that count as a vault artefact reference. Configurable so adding a
// new artefact type (html walkthroughs, csv exports) needs no code change — the
// 2026-07-31 pilot-initiative .html pointer went unchecked purely because .html wasn't here.
const POINTER_EXTS = cfg.pointerExtensions?.length
  ? cfg.pointerExtensions
  : ["md", "json", "sh", "mjs", "base", "canvas", "ps1"];
const EXT_RE = new RegExp(`\\.(${POINTER_EXTS.join("|")})$`, "i");

// Glob → RegExp. Only `*` (within a path segment) and `**` (across segments).
function globToRe(pattern) {
  const esc = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&");
  const body = esc.replace(/\*\*/g, "\u0000").replace(/\*/g, "[^/]*").replace(/\u0000/g, ".*");
  return new RegExp(`^${body}$`);
}

// todo = "not filled in yet" (Check 13): its own section and JSON key, so red/amber consumers (CI, health) ignore it.
const findings = { red: [], amber: [], green: [], todo: [] };
const add = (sev, check, msg, fix) => findings[sev].push({ check, msg, fix });

const today = new Date();
const DATE_RE = /(\d{4})-(\d{2})-(\d{2})/g;
const daysBetween = (a, b) => Math.round((a - b) / 86_400_000);
const parseDate = (s) => { const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; };

async function readSafe(p) { try { return await readFile(p, "utf8"); } catch { return null; } }

// "Last touched" and "Last verified accurate" mean DIFFERENT things and must not
// be collapsed. Touched = someone edited it. Verified = someone confirmed the
// content is still true. A file can be touched daily and unverified for months;
// collapsing them (as this script did until 2026-08-10) reports that as fresh.
//
// Parse per-LABEL, not per-line. Both stamps routinely share one line
// ("**Last touched:** X | **Last verified accurate:** Y"); a per-line scan
// assigns every date on the line to both stamps and reports the stale one as
// fresh. Anchor each date to the label immediately preceding it.
function stampsOf(text) {
  const pick = (re) => {
    let latest = null;
    for (const m of text.matchAll(re)) {
      const d = parseDate(m[1]);
      if (d && (!latest || d > latest)) latest = d;
    }
    return latest;
  };
  const verified = pick(/last\s+verified\s+accurate\D{0,12}(\d{4}-\d{2}-\d{2})/gi);
  const touched = pick(/last\s+(?:updated|touched)\D{0,12}(\d{4}-\d{2}-\d{2})/gi);
  return { touched, verified };
}

// registry.yaml: newest `as_of:` stands in for both stamps.
function registryStamps(text) {
  let latest = null;
  for (const m of text.matchAll(/^\s*as_of:\s*(\d{4}-\d{2}-\d{2})\s*$/gm)) {
    const d = parseDate(m[1]);
    if (d && (!latest || d > latest)) latest = d;
  }
  return { touched: latest, verified: latest };
}
// The edition a file reflects: the FIRST date on its "Source as of" line (stamp schema puts the source's date first).
// Accepts 2026-10-27, "20 May 2026" and "June 2026" (read as the 1st). Null if the line or a date is missing.
const MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
function sourceAsOf(text) {
  const line = /source\s+as\s+of:?\**:?\s*(.*)/i.exec(text)?.[1];
  const m = line && /(\d{4})-(\d{2})-(\d{2})|(?:(\d{1,2})\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{4})/i.exec(line);
  if (!m) return null;
  return m[1] ? new Date(+m[1], +m[2] - 1, +m[3]) : new Date(+m[6], MONTHS.indexOf(m[5].toLowerCase()), +(m[4] || 1));
}
// A paused initiative (frontmatter health: paused / on_hold) is not expected to change, so it is not "stale" (Move 11d).
function isPaused(text) {
  const fm = /^---\n([\s\S]*?)\n---/.exec(text);
  return !!fm && /^health:\s*(paused|on_hold)\s*$/m.test(fm[1]);
}
// Typed facts (PLAN S2.4): top-level `key: value` frontmatter as strings, quotes stripped. Null if none.
function frontmatter(text) {
  const fm = /^---\n([\s\S]*?)\n---/.exec(text);
  if (!fm) return null;
  const out = {};
  for (const m of fm[1].matchAll(/^([A-Za-z_]+):[ \t]*(.*)$/gm)) out[m[1]] = m[2].trim().replace(/^"(.*)"$/, "$1");
  return out;
}
// errors = schema problems (must fix); stale = why a live fact is past its freshness limit, else null;
// unsourced = `verified` is a date but `source` names no person check and no pointable original (fc.verifiedPointer).
function factIssues(text, fc = cfg.facts, now = today) {
  const f = frontmatter(text);
  if (!f) return { errors: ["no frontmatter"], stale: null };
  const errors = fc.required.filter((k) => !f[k]).map((k) => `missing \`${k}\``);
  const statuses = fc.types[f.type];
  if (f.type && !statuses) errors.push(`type \`${f.type}\` is not one of ${Object.keys(fc.types).join(", ")}`);
  else if (statuses && f.status && !statuses.includes(f.status)) errors.push(`status \`${f.status}\` is not valid for ${f.type} (${statuses.join(", ")})`);
  if (f.as_of && !parseDate(f.as_of)) errors.push("`as_of` is not YYYY-MM-DD");
  const v = f.verified ? parseDate(f.verified) : null;
  if (f.verified && !v && f.verified !== "not yet") errors.push('`verified` is not YYYY-MM-DD or "not yet"');
  let stale = null;
  const limit = fc.freshnessDays[f.type];
  if (!errors.length && fc.live.includes(f.status) && limit != null) {
    if (!v) stale = "is `verified: not yet`";
    else if (daysBetween(now, v) > limit) stale = `was last verified ${daysBetween(now, v)}d ago (>${limit}d for ${f.type})`;
  }
  const unsourced = !errors.length && v && fc.verifiedPointer && !new RegExp(fc.verifiedPointer).test(f.source || "");
  return { errors, stale, unsourced: !!unsourced };
}
// Check 13 helpers (F1.3). The marker is a whole line (or ends a `#` comment), so a doc quoting it inline is not a stub.
const nf = cfg.notFilled || {};
const MARKER_RE = nf.marker ? new RegExp(`^(?:>|#.*)\\s*${nf.marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*$`, "m") : null;
const isStub = (text) => !!MARKER_RE?.test(text);
// The first template text (cfg.notFilled.patterns) left in a file, else null.
function templateText(text, patterns = nf.patterns || []) {
  for (const p of patterns) { const m = text.match(new RegExp(p)); if (m) return m[0]; }
  return null;
}
// Keys in a `| Key | Value |` table whose value is blank, "-", or still holds "(set X)" or "{{X}}".
function profileGaps(text) {
  const out = [];
  let inTable = false;
  for (const line of text.split("\n")) {
    if (/^\|\s*Key\s*\|\s*Value\s*\|/.test(line)) { inTable = true; continue; }
    if (!inTable) continue;
    if (!line.startsWith("|")) { inTable = false; continue; }
    const [, key, val = ""] = line.split("|").map((c) => c.trim());
    if (!key || /^:?-+:?$/.test(key)) continue;
    const v = val.replace(/`/g, "").trim();
    if (!v || v === "-" || /\(set [A-Z_]+\)|\{\{[A-Z_]+\}\}/.test(v)) out.push(key);
  }
  return out;
}
// Stamp lines aside, a cycle file names its cycle with a date or a "cycle ... <number>" line.
const cycleMissing = (text) => !/\d{4}-\d{2}-\d{2}|\bcycle\b[^\n]*\d/i.test(text.split("\n").filter((l) => !/last\s+(updated|touched|verified)|source\s+as\s+of/i.test(l)).join("\n"));
if (process.argv.includes("--selftest")) {
  const t = (txt) => stampsOf(txt), d = (x) => x && `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`;
  const ok = (c, m) => { if (!c) { console.error("selftest FAIL: " + m); process.exitCode = 1; } };
  ok(d(t("**Last Updated:** 2026-11-20\n**Last verified accurate:** not yet").touched) === "2026-11-20", "touched date");
  ok(t("**Last verified accurate:** not yet").verified === null, "not yet has no date");
  ok(d(registryStamps("  as_of: 2026-09-13\n  as_of: 2026-10-27\n").touched) === "2026-10-27", "registry newest as_of");
  ok(registryStamps("note: as_of: 2026-12-01 in prose").touched === null, "as_of in prose ignored");
  ok(isPaused("---\nproject: X\nhealth: paused\n---\n") && isPaused("---\nhealth: on_hold\n---\n"), "paused health detected");
  ok(!isPaused("---\nhealth: on_track\n---\nhealth: paused in prose"), "paused only read from frontmatter");
  ok(d(sourceAsOf("**Source as of:** pre-read, 2026-10-27 (deck, 2026-10-14)")) === "2026-10-27", "source: first ISO date");
  ok(d(sourceAsOf("**Source as of:** FY26 results, 20 May 2026 (16 Nov 2026 not read)")) === "2026-05-20", "source: day month year");
  ok(d(sourceAsOf("**Source as of:** Survey, June 2026, n=407")) === "2026-06-01", "source: month year");
  ok(sourceAsOf("**Source as of:** Vision document (undated)") === null && sourceAsOf("no stamp") === null, "source: no date");
  const lf = { maxKB: 50, dirs: ["1_PROJECTS"], allow: ["**/LOG.md"] };
  ok(isTooLarge("1_PROJECTS/X/PLAN.md", 60_000, lf), "large: big md flagged");
  ok(!isTooLarge("1_PROJECTS/X/LOG.md", 60_000, lf) && !isTooLarge("1_PROJECTS/X/a.md", 40_000, lf) && !isTooLarge("3_RESOURCES/a.md", 60_000, lf), "large: allow-list, size, dir");
  const fc = { required: ["type", "claim", "source", "as_of", "verified", "status"], types: { decision: ["active", "superseded"], "open-question": ["open", "answered"] }, live: ["active", "open"], freshnessDays: { decision: 180, "open-question": 30 }, verifiedPointer: cfg.facts.verifiedPointer };
  const fact = (o) => "---\n" + Object.entries({ type: "decision", claim: "\"X: y\"", source: "\"LOG\"", as_of: "2026-10-01", verified: "2026-11-01", status: "active", ...o }).filter(([, v]) => v !== null).map(([k, v]) => `${k}: ${v}`).join("\n") + "\n---\n";
  const fi = (o, now = new Date(2026, 10, 22)) => factIssues(fact(o), fc, now);
  ok(!fi({}).errors.length && fi({}).stale === null, "fact: valid decision is clean");
  ok(fi({ source: null }).errors.join() === "missing `source`", "fact: missing field");
  ok(/not one of/.test(fi({ type: "risk" }).errors.join()), "fact: unknown type");
  ok(/not valid for decision/.test(fi({ status: "open" }).errors.join()), "fact: status must fit type");
  ok(fi({ as_of: "Oct 2026", verified: "soon" }).errors.length === 2, "fact: bad dates");
  ok(/verified: not yet/.test(fi({ verified: "not yet" }).stale), "fact: not yet is stale when live");
  ok(fi({}).unsourced && !fi({ verified: "not yet" }).unsourced, "fact: dated verified with no pointable source is flagged");
  ok(!fi({ source: "\"Slack https://{{SLACK_WORKSPACE}}.slack.com/archives/C1/p1\"" }).unsourced && !fi({ source: "\"PB-123\"" }).unsourced && !fi({ source: "\"metric:acq.x\"" }).unsourced && !fi({ source: "\"Checked by PM A\"" }).unsourced, "fact: link, item ID, metric ID or person check counts");
  ok(/>30d/.test(fi({ type: "open-question", status: "open", verified: "2026-10-01" }).stale), "fact: open question past 30d");
  ok(fi({ type: "open-question", status: "answered", verified: "2026-01-01" }).stale === null, "fact: closed facts do not age");
  ok(factIssues("no frontmatter", fc).errors[0] === "no frontmatter", "fact: no frontmatter");
  const ses = (...chips) => "## Sessions\n\n| Date | Initiative | Versions (dp / ingest) | Reasons |\n|---|---|---|---|\n" + chips.map((c, i) => `| 2026-11-${String(10 + i).padStart(2, "0")} | Pilot | ${c[1] ?? "v1 / v1"} | ${c[0]} |\n`).join("");
  const hit = chipRule(parseSessions(ses(["wrong fact"], ["wording"], ["wrong fact ×2"], ["—"])));
  ok(hit.length === 1 && hit[0].chip === "wrong fact" && hit[0].count === 3 && hit[0].sessions.length === 2, "rejection loop: 3 of one chip fires, names chip and sessions");
  ok(!chipRule(parseSessions(ses(["wrong fact ×2"], ["wording"], ["none ×5"]))).length, "rejection loop: 2 of a chip, or `none`, does not fire");
  ok(!chipRule(parseSessions(ses(["duplicate"], ["duplicate", "v2 / v1"], ["duplicate", "v3 / v1"]))).length, "rejection loop: counts per version only");
  ok(!chipRule(parseSessions(ses(["duplicate ×3"], ...Array(10).fill(["—"])))).length, "rejection loop: only the last 10 sessions count");
  ok(isStub("# X\n\nWhat goes here.\n\n> Not filled in yet.\n") && isStub("# Open actions. > Not filled in yet.\nfilters:\n"), "not-filled: marker line in md and in a .base comment");
  ok(!isStub("Stubs end with `> Not filled in yet.` until filled."), "not-filled: marker quoted inline is not a stub");
  ok(templateText("**Owner:** [name] | **Health:** [critical|at_risk]") === "[name]" && templateText("- [date]: [event]") === "[date]", "not-filled: bracketed slots");
  ok(templateText("Owner: TBD") === "TBD" && templateText("Empty. Fills as material is ingested.") && templateText("Ask <your name>") === "<your name>", "not-filled: TBD, empty note, angle slot");
  ok(templateText("See [the doc](x.md), [[wiki note]], - [x] done, line<br>break, [PB-12]") === null, "not-filled: links, wikilinks, checkboxes, html and IDs are not slots");
  const me = "| Key | Value |\n|---|---|\n| Name | Sam Example |\n| Role | |\n| Slack user ID | `(set OWNER_SLACK_ID)` |\n| Product | Widgets ({{PRODUCT_LONG}}) |\n| Level | 1 |\n\n| Who | Why |\n|---|---|\n| | |\n";
  ok(profileGaps(me).join() === "Role,Slack user ID,Product", "not-filled: unfilled ME/ORG fields listed by name");
  ok(cycleMissing("# Active Cycle\n\n**Last Updated:** 2026-11-22 | **Last verified accurate:** not yet\n**Cycle:** (name), (start) to (end)\n"), "not-filled: cycle file with stamps only has no cycle");
  ok(!cycleMissing("**Cycle:** C5, 2026-10-06 to 2026-11-14") && !cycleMissing("# Active Cycle — Cycle 5"), "not-filled: named or dated cycle is filled");
  if (!process.exitCode) console.log("selftest ok"); process.exit();
}

// Recursively collect files, honouring excludeDirs.
async function walk(dir, out = []) {
  let entries;
  try { entries = await readdir(dir, { withFileTypes: true }); } catch { return out; }
  for (const e of entries) {
    if (e.name.startsWith(".") && e.name !== ".scripts" && e.isDirectory()) continue;
    if (cfg.excludeDirs.includes(e.name)) continue;
    const full = join(dir, e.name);
    if (e.isDirectory()) await walk(full, out);
    else out.push(full);
  }
  return out;
}

// Full inventory of the vault, built once: relative paths + basename lookup.
let VAULT_PATHS = new Set();     // e.g. "2_AREAS/{{ORG}}/context/strategic_context.md"
let VAULT_BASENAMES = new Set(); // e.g. "strategic_context.md"
let VAULT_DIRS = new Set();      // relative dir paths, e.g. "0_INBOX"
async function buildInventory() {
  for (const f of await walk(ROOT)) {
    const rel = f.slice(ROOT.length + 1);
    VAULT_PATHS.add(rel);
    VAULT_BASENAMES.add(rel.split("/").pop());
    let d = rel;
    while (d.includes("/")) { d = d.slice(0, d.lastIndexOf("/")); VAULT_DIRS.add(d); }
  }
  // Private vault (two-vault layout, 2026-11-13): walk() does not follow the
  // symlinked mount, so inventory it separately under its mount prefix. Without
  // this, bare-filename and suffix shorthand for private files reads as dead.
  const mount = cfg.privateBoundary?.mount;
  if (mount && existsSync(join(ROOT, mount))) {
    const base = join(ROOT, mount);
    for (const f of await walk(base)) {
      const rel = mount + "/" + f.slice(base.length + 1);
      VAULT_PATHS.add(rel);
      VAULT_BASENAMES.add(rel.split("/").pop());
      let d = rel;
      while (d.includes("/")) { d = d.slice(0, d.lastIndexOf("/")); VAULT_DIRS.add(d); }
    }
  }
}

// Resolve a vault-relative reference. Returns true if it points at something real.
// - relative to the citing file's own directory ("../STATE.md", bare "Artefacts/"
//   used as "my own subfolder") is checked FIRST. Before 2026-08-10 this wasn't
//   checked at all, so every project doc's `../BRIEF.md`/`../LOG.md`/`Artefacts/`
//   sibling-reference — a normal, correct way to write a relative link — was
//   flagged dead even though the file was sitting right next to it. That's why
//   turning on the `1_PROJECTS`/`2_AREAS` scan (same day) produced 165 findings
//   instead of the real number: the resolver had never been taught relative paths.
// - bare filename  → true if a file with that basename exists anywhere in the vault
// - multi-segment  → true if it resolves under a base, OR is a suffix of a known path
// - trailing slash → treated as a directory reference
function pathResolves(tokenRaw, srcRelPath) {
  if (srcRelPath) {
    const srcDir = dirname(join(ROOT, srcRelPath));
    const candidate = resolve(srcDir, tokenRaw.replace(/\/+$/, "") || ".");
    if (candidate.startsWith(ROOT) && existsSync(candidate)) return true;
  }
  const token = tokenRaw.replace(/\/+$/, "");
  const isDir = tokenRaw.endsWith("/");
  if (isDir) {
    return VAULT_DIRS.has(token) || cfg.pathResolveBases.some((b) => existsSync(join(ROOT, b, token)));
  }
  if (!token.includes("/")) return VAULT_BASENAMES.has(token); // bare filename shorthand
  if (cfg.pathResolveBases.some((b) => existsSync(join(ROOT, b, token)))) return true;
  // Partial path (e.g. "_H2 Roadmap/CANDIDATES.md") — accept if it's a suffix of a real path.
  for (const p of VAULT_PATHS) if (p === token || p.endsWith("/" + token)) return true;
  return false;
}

// A token is a *vault* path we should check (not an external/system/URL path).
function isVaultPathToken(tok) {
  if (/^(node|bash|sh|zsh|npx|python3?|git|cd|curl)\s/.test(tok)) return false;            // shell command, not a path
  if (tok.startsWith("http") || tok.startsWith("~") || tok.startsWith("/")) return false; // external
  if (tok.includes("/Users/") || /\s\//.test(tok)) return false;                           // embedded absolute path / shell command
  if (tok.includes("[") || tok.includes("*")) return false;                                // template/glob
  if (tok.includes(" ") && !EXT_RE.test(tok)) return false;                                 // prose in backticks
  return EXT_RE.test(tok) || tok.endsWith("/");
}

// A filename *template* (e.g. `0_INBOX/YYYY-MM-DD_slack-review.md` describing a
// naming convention) can never resolve to a real vault path — it isn't a
// reference, it's a pattern. Flagging it as dead-pointer noise every run
// (2026-08-10 report) trains the reader to skim past real 🔴 findings. Anything
// containing the literal placeholder tokens YYYY/MM/DD is a pattern, not a path.
function isTemplatePattern(tok) {
  return /\bYYYY\b|_MM_|_DD[_.]|MM-DD/.test(tok);
}

// A backticked path cited as a historical precedent ("Precedent: `path` — ...",
// documenting a past incident that was diagnosed and cleaned up) is *expected*
// to no longer resolve once the incident is resolved. It's a citation, not a
// live reference the vault promises still exists. Detected by the label
// immediately preceding the token on the same line — deliberately narrow so it
// doesn't swallow genuine dead pointers that happen to share a line with prose.
function isPrecedentCitation(text, matchIndex) {
  const lineStart = text.lastIndexOf("\n", matchIndex) + 1;
  const linePrefix = text.slice(lineStart, matchIndex);
  return /\bprecedent\s*:/i.test(linePrefix);
}

// ── Check 1: dead pointers ────────────────────────────────────────────────
// Sources = the explicit list + every SKILL.md + every .md under deadPointerDirs.
// Before 2026-08-10 only memory_index.md and the skills were scanned, so a
// dangling pointer inside a project STATE.md — the file the loading model calls
// a single source of truth — was structurally unreachable by this check.
async function checkDeadPointers() {
  const sources = new Set(cfg.deadPointerSources);
  const skillsRoot = join(ROOT, cfg.skillsDir);
  for (const f of await walk(skillsRoot)) {
    if (f.endsWith("SKILL.md")) sources.add(f.slice(ROOT.length + 1));
  }
  for (const dir of cfg.deadPointerDirs || []) {
    for (const f of await walk(join(ROOT, dir))) {
      if (f.endsWith(".md")) sources.add(f.slice(ROOT.length + 1));
    }
  }
  // Some content is reference/research material that *quotes* an external
  // system's file layout (a repo audit, a separate prototype's own doc set) as
  // prose — those backtick tokens were never vault links and can't be told
  // apart from real ones by shape alone. Excluding the whole source file is
  // more honest than teaching the regex increasingly specific exceptions for
  // content that isn't about this vault at all.
  const excludeRe = (cfg.deadPointerExcludeSources || []).map(globToRe);
  for (const src of [...sources]) {
    if (excludeRe.some((re) => re.test(src))) sources.delete(src);
  }
  const seen = new Set();
  let checked = 0, dead = 0;
  for (const src of sources) {
    const text = await readSafe(join(ROOT, src));
    if (!text) continue;
    for (const m of text.matchAll(/`([^`\n]+)`/g)) {
      const tok = m[1].trim();
      if (!isVaultPathToken(tok)) continue;
      if (isTemplatePattern(tok)) continue;
      if (isPrecedentCitation(text, m.index)) continue;
      // shortcut: --shared skips bare filenames too (cannot tell a private one from a shared one); the local run still checks them.
      if (SHARED && (tok.startsWith(PRIV(cfg)) || !tok.replace(/\/+$/, "").includes("/"))) continue;
      const key = `${src}::${tok}`;
      if (seen.has(key)) continue;
      seen.add(key);
      checked++;
      if (!pathResolves(tok, src)) { dead++; add("red", "dead-pointer", `\`${tok}\` referenced in \`${src}\` resolves to nothing in the vault`, "Fix the path or remove the reference"); }
    }
  }
  if (dead === 0) add("green", "dead-pointer", `${checked} vault path references across index, skills and ${(cfg.deadPointerDirs || []).length} content dir(s) all resolve`);
}

// ── Check 2: staleness + missing stamps ─────────────────────────────────────
// Explicit files plus anything matching an operationalGlob (project STATE files etc).
function operationalTargets() {
  const targets = new Map();
  for (const { path, rhythm } of cfg.operationalFiles) targets.set(path, rhythm);
  for (const { pattern, rhythm } of cfg.operationalGlobs || []) {
    const re = globToRe(pattern);
    for (const p of VAULT_PATHS) if (re.test(p) && !targets.has(p)) targets.set(p, rhythm);
  }
  return targets;
}
async function checkStaleness() {
  const targets = operationalTargets();

  const contracts = new Map((cfg.refreshContracts || []).map((c) => [c.path, c]));
  for (const p of contracts.keys()) if (!targets.has(p)) add("red", "contract", `Refresh contract names \`${p}\`, which is not an operational file`, "Add it to operationalFiles with a rhythm, or fix the path");
  const fmt = (x) => `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`;

  let clean = 0, paused = 0;
  for (const [path, rhythm] of targets) {
    if (SHARED && path.startsWith(PRIV(cfg) + "/")) continue;
    const text = await readSafe(join(ROOT, path));
    if (text === null) { add("red", "dead-pointer", `Operational file \`${path}\` (staleness policy) is missing`, "Fix path in lint.config.json or restore file"); continue; }
    if (isStub(text)) continue; // a stub has nothing to be stale; Check 13 lists it under not filled in yet
    if (isPaused(text)) { paused++; continue; }
    const threshold = cfg.stalenessThresholdsDays[rhythm];
    // The registry has no prose stamps: its newest per-metric as_of is both its edit and its confirmation date.
    const { touched, verified } = path.endsWith(".yaml") ? registryStamps(text) : stampsOf(text);
    const mustVerify = (cfg.requireVerified || []).some((g) => globToRe(g).test(path));

    if (!touched && !verified) { add("amber", "missing-stamp", `\`${path}\` has no staleness stamp — can't judge freshness at a glance`, "Add **Last Updated:** YYYY-MM-DD near the top"); continue; }

    // Refresh contract (Move 11f): judge the file against its source's cadence and its confirmer, not its edit date.
    const c = contracts.get(path);
    if (c) {
      const src = path.endsWith(".yaml") ? touched : sourceAsOf(text);
      const vThreshold = cfg.verificationThresholdsDays?.[rhythm] ?? threshold;
      let ok = true;
      if (!src) { ok = false; add("amber", "contract", `\`${path}\` has a refresh contract but no readable date on its Source as of line`, "Put the source's date first on that line (YYYY-MM-DD)"); }
      else if (daysBetween(today, src) > c.sourceEveryDays + (cfg.sourceGraceDays ?? 0)) {
        ok = false;
        add("amber", "source-newer", `\`${path}\` reflects ${c.source} as of ${fmt(src)} (${daysBetween(today, src)}d ago). That source publishes every ${c.sourceEveryDays}d, so a newer edition should exist`, `Read the newer edition, update the file and its Source as of, then ask ${c.confirms} to confirm`);
      }
      if (!verified || daysBetween(today, verified) > vThreshold) {
        ok = false;
        add("amber", "contract-overdue", `\`${path}\` ${verified ? `was last confirmed ${daysBetween(today, verified)}d ago (>${vThreshold}d ${rhythm})` : "was never confirmed against its source"}. Confirmer: ${c.confirms}`, `Ask ${c.confirms} to check it against ${c.source}, then stamp Last verified accurate`);
      }
      if (ok) clean++;
      continue;
    }

    const age = daysBetween(today, touched || verified);
    if (age > threshold) {
      add("amber", "stale", `\`${path}\` last updated ${age}d ago (>${threshold}d ${rhythm} threshold)`, "Review and restamp, or confirm still accurate");
      continue;
    }

    // Fresh by edit, but is it fresh by *confirmation*? This is the check that was
    // missing entirely — an actively-edited file can carry long-unverified content.
    const vThreshold = cfg.verificationThresholdsDays?.[rhythm] ?? threshold;
    if (verified) {
      const vAge = daysBetween(today, verified);
      if (vAge > vThreshold) {
        add("amber", "unverified", `\`${path}\` was touched ${age}d ago but last verified accurate ${vAge}d ago (>${vThreshold}d) — edited without re-confirming the rest still holds`, "Re-read and move the Last verified accurate stamp, or state plainly what wasn't checked");
        continue;
      }
    } else if (/last\s+verified\s+accurate\W{0,6}not\s+yet/i.test(text)) {
      add("amber", "unverified", `\`${path}\` says "Last verified accurate: not yet" — edited, never checked against its source`, "Check it against its Source as of, then stamp the date");
      continue;
    } else if (/last\s+verified\s+accurate/i.test(text)) {
      add("amber", "missing-stamp", `\`${path}\` has a "Last verified accurate" label with no parseable date`, "Add a YYYY-MM-DD date to it");
      continue;
    } else if (mustVerify && !path.endsWith(".yaml")) {
      add("amber", "missing-stamp", `\`${path}\` is shared context but has no "Last verified accurate" stamp — lint can't tell edited from checked`, "Add the stamp block (see lint SKILL.md, stamp schema)");
      continue;
    }
    clean++;
  }
  if (clean) add("green", "staleness", `${clean} operational file(s) within their freshness and verification windows`);
  if (paused) add("green", "staleness", `${paused} paused initiative STATE file(s) skipped (frontmatter health: paused)`);
}

// ── Check 3: orphan skills (on disk but not in the index) ────────────────────
async function checkOrphanSkills() {
  const index = await readSafe(join(ROOT, "memory_index.md"));
  if (!index) { add("red", "dead-pointer", "memory_index.md is missing", "Restore it — it's the master router"); return; }
  const skillsRoot = join(ROOT, cfg.skillsDir);
  let entries;
  try { entries = await readdir(skillsRoot, { withFileTypes: true }); } catch { return; }
  let registered = 0;
  for (const e of entries) {
    if (!e.isDirectory() || e.name.startsWith(".")) continue;
    if ((cfg.skillsExemptFromRegistration || []).includes(e.name)) continue;
    if (!existsSync(join(skillsRoot, e.name, "SKILL.md"))) continue;
    if (index.includes(`${e.name}/SKILL.md`) || index.includes(`\`${e.name}\``)) registered++;
    else add("amber", "orphan-skill", `Skill \`${e.name}\` has a SKILL.md but isn't registered in memory_index.md`, "Add it to the 3_RESOURCES file map + query patterns");
  }
  if (registered) add("green", "orphan-skill", `${registered} skill(s) registered in the index`);
}

// ── Check 4: inbox age ──────────────────────────────────────────────────────
async function checkInbox() {
  const dir = join(ROOT, cfg.inbox.dir);
  let entries;
  try { entries = await readdir(dir); } catch { return; }
  let old = 0, total = 0;
  for (const name of entries) {
    if (name.startsWith(".") || cfg.inbox.exempt.includes(name)) continue;
    total++;
    // Prefer a date in the filename; fall back to mtime.
    const fnDate = (name.match(/(\d{4})[-_](\d{2})[-_](\d{2})/) || null);
    let d = fnDate ? new Date(+fnDate[1], +fnDate[2] - 1, +fnDate[3]) : (await stat(join(dir, name))).mtime;
    const age = daysBetween(today, d);
    if (age > cfg.inbox.maxAgeDays) { old++; add("amber", "inbox-age", `\`${cfg.inbox.dir}/${name}\` is ${age}d old (>${cfg.inbox.maxAgeDays}d) — process or consciously delete`, "Run the ingest skill or drop it"); }
  }
  if (total === 0) add("green", "inbox-age", "Inbox is empty (trending as it should)");
  else if (old === 0) add("green", "inbox-age", `${total} inbox item(s), all within ${cfg.inbox.maxAgeDays}d`);
}

// ── Check 5: index ↔ changelog drift ────────────────────────────────────────
async function checkVersionDrift() {
  const index = await readSafe(join(ROOT, "memory_index.md"));
  const changelog = await readSafe(join(ROOT, "CHANGELOG.md"));
  if (!index || !changelog) return;
  const idxDateM = index.match(/last\s+updated:\**\s*(\d{4}-\d{2}-\d{2})/i);
  const clDates = [...changelog.matchAll(/^##\s+(\d{4}-\d{2}-\d{2})/gm)].map((m) => m[1]);
  const latestCl = clDates.map(parseDate).filter(Boolean).sort((a, b) => b - a)[0];
  const idxDate = idxDateM ? parseDate(idxDateM[1]) : null;
  if (idxDate && latestCl && latestCl > idxDate) {
    const gap = daysBetween(latestCl, idxDate);
    add("amber", "index-drift", `memory_index.md "Last Updated" (${idxDateM[1]}) is ${gap}d behind the latest CHANGELOG entry (${clDates[0]}) — index may not reflect recent structural changes`, "Review the index against recent changelog entries");
  } else if (idxDate && latestCl) {
    add("green", "index-drift", `Index date (${idxDateM[1]}) is current vs latest changelog entry (${clDates[0]})`);
  }
}

// ── Check 6: deployed-skill drift ──────────────────────────────────────
// The vault lints itself, but nothing checked the copies that actually execute.
// If a mirror path is configured, diff it against the vault source. If none is
// configured, say so — an unconfigured integrity check should report its own
// absence rather than pass silently, which is how this gap survived three
// separate incidents (see Actions/deployed-skill-copies-diverged-from-vault.md).
async function checkDeployedSkills() {
  if (SHARED) return; // deployed copies live on the user's machine
  const mirrors = cfg.deployedSkillMirrors || [];
  if (!mirrors.length) {
    add("amber", "deployed-skill", "No `deployedSkillMirrors` configured — nothing verifies that deployed skill copies match their vault source", "Add mirror paths to lint.config.json, or record the decision that the vault is documentation only");
    return;
  }
  let matched = 0;
  for (const { name, vault, deployed, mode = "copy" } of mirrors) {
    const a = await readSafe(join(ROOT, vault));
    const dep = deployed.replace(/^~(?=\/)/, homedir());
    const b = await readSafe(dep.startsWith("/") ? dep : join(ROOT, dep));
    if (a === null) { add("red", "deployed-skill", `Vault source for \`${name}\` missing at \`${vault}\``, "Fix the path in lint.config.json"); continue; }
    if (b === null) { add("amber", "deployed-skill", `Deployed copy of \`${name}\` not readable at \`${deployed}\` — cannot verify it matches the vault`, "Check the mirror path, or drop the entry if the copy is unreachable by design"); continue; }

    if (mode === "pointer") {
      // A loader must NOT carry the skill body — if it does, it can drift, which
      // is the whole failure this mode exists to make impossible. Two conditions:
      // it names the vault path, and it is short enough that it plainly contains
      // no procedure of its own.
      const namesVault = b.includes(vault) || b.includes(vault.replace(/^3_RESOURCES\//, ""));
      const LOADER_MAX_BYTES = 4000;
      if (!namesVault) add("red", "deployed-skill", `Loader for \`${name}\` does not name its vault source \`${vault}\` — it cannot delegate to a path it never states`, "Rewrite the loader to point at the vault file");
      else if (b.length > LOADER_MAX_BYTES) add("red", "deployed-skill", `Loader for \`${name}\` is ${b.length} bytes (>${LOADER_MAX_BYTES}) — it has grown a body of its own and can now drift from the vault`, "Strip it back to a delegation stub; the procedure lives in the vault only");
      else matched++;
      continue;
    }

    if (a.trim() !== b.trim()) add("red", "deployed-skill", `Deployed \`${name}\` has diverged from its vault source — the executing copy is not what the vault says it is`, "Re-sync from the vault, or reverse the direction and update the vault");
    else matched++;
  }
  if (matched) add("green", "deployed-skill", `${matched} deployed skill copy/copies match their vault source`);
}

// ── Check 7: run integrity (did the pipeline actually run?) ────────────────
// Checks 1–6 all assume an artefact exists to inspect. A skill that never fired
// — or a drifted deployed copy that answered in chat and wrote nothing — leaves
// no artefact, so every other check passes and the failure is invisible. That is
// precisely how the 10–12 Aug daily-slack-review divergence survived. Absence is
// the signal here, and version mismatch is the second signal: output produced by
// an older copy of the skill carries an older version string, or none at all.
function weekdaysBetween(from, to) {
  let n = 0;
  const d = new Date(from);
  d.setHours(0, 0, 0, 0);
  const end = new Date(to);
  end.setHours(0, 0, 0, 0);
  while (d < end) {
    d.setDate(d.getDate() + 1);
    const wd = d.getDay();
    if (wd !== 0 && wd !== 6) n++;
  }
  return n;
}

async function checkRunIntegrity() {
  for (const job of cfg.runIntegrity || []) {
    if (SHARED && (job.searchDirs || []).every((d) => d.startsWith(PRIV(cfg)))) continue;
    const src = await readSafe(join(ROOT, job.sourceSkill));
    if (src === null) { add("red", "run-integrity", `Source skill for \`${job.name}\` missing at \`${job.sourceSkill}\``, "Fix the path in lint.config.json"); continue; }
    const vm = src.match(/^version:\s*(\S+)\s*$/m);
    if (!vm) { add("amber", "run-integrity", `\`${job.sourceSkill}\` has no \`version:\` in frontmatter — run output cannot be tied to a skill version`, "Add a version field and have the skill echo it in its provenance footer"); continue; }
    const expected = vm[1];

    // Newest artefact across all search dirs (inbox pre-processing, archive after).
    let newest = null;
    for (const dir of job.searchDirs || []) {
      for (const f of await walk(join(ROOT, dir))) {
        const base = f.split("/").pop();
        if (!base.endsWith(job.artifactPattern)) continue;
        const m = base.match(/(\d{4})-(\d{2})-(\d{2})/);
        if (!m) continue;
        const d = new Date(+m[1], +m[2] - 1, +m[3]);
        if (!newest || d > newest.date) newest = { date: d, path: f, base };
      }
    }

    if (!newest) {
      // Never run is should-fix: a new vault has no output yet. Late or stale output (below) stays must-fix.
      add("amber", "run-integrity", `\`${job.name}\` has never run: no output in ${(job.searchDirs || []).join(", ")}. Either it has not been run yet, or it writes somewhere unexpected`, "Run the skill once and confirm where it writes");
      continue;
    }

    const gap = job.weekdaysOnly ? weekdaysBetween(newest.date, today) : daysBetween(today, newest.date);
    const grace = job.graceWeekdays ?? 1;
    if (gap > grace) {
      add("red", "run-integrity", `Latest \`${job.name}\` output is \`${newest.base}\` — ${gap} weekday(s) ago (>${grace}). Either it hasn't run, or a drifted copy ran and wrote no file`, "Run it, and check the deployed-skill findings above before assuming it's a scheduling problem");
      continue;
    }

    const text = await readSafe(newest.path);
    const fm = job.footerRe ? (text || "").match(new RegExp(job.footerRe)) : null;
    if (!fm) {
      add("red", "run-integrity", `\`${newest.base}\` has no parseable provenance footer — cannot tell which copy of \`${job.name}\` produced it`, "A missing footer means a pre-2026-08-12 copy executed; re-sync the deployed copies");
    } else if (fm[1] !== expected) {
      add("red", "run-integrity", `\`${newest.base}\` was produced by \`${job.name}\` v${fm[1]}, but the vault source is v${expected} — a stale copy is executing`, "Re-sync the deployed copy from the vault");
    } else {
      add("green", "run-integrity", `\`${job.name}\` ran within ${grace} weekday(s) (\`${newest.base}\`) and reports the current version (v${expected})`);
    }
  }
}

// ── Check 8: STATE field budgets (snapshot, not history) ───────────────────
// Added 2026-10-29. The pilot initiative's STATE grew to 12,055 words under diff-propose because the
// only size rule (a 200-word cap) lived in skill prose and nothing measured it.
// Budgets are the ones in diff-propose/SKILL.md ("STATE is a snapshot, not a
// history"). strictFiles (diff-propose pilots, whose contract these budgets are)
// report 🔴; other matches report 🟡, since they predate the budgets.
const bulletWords = (line) => line.replace(/^\s*-\s+/, "").split(/\s+/).filter(Boolean).length;

async function checkStateBudgets() {
  const sb = cfg.stateBudgets;
  if (!sb) return;
  const strict = new Set(sb.strictFiles || []);
  const targets = new Set(strict);
  for (const pattern of sb.globs || []) {
    const re = globToRe(pattern);
    for (const p of VAULT_PATHS) if (re.test(p)) targets.add(p);
  }

  let clean = 0;
  for (const path of [...targets].sort()) {
    const text = await readSafe(join(ROOT, path));
    if (text === null) { if (strict.has(path)) add("red", "state-budget", `Budgeted STATE \`${path}\` is missing`, "Fix path in lint.config.json or restore file"); continue; }

    // Collect bullets per "## " section; indented bullets are counted separately.
    const sections = new Map();
    let cur = null;
    for (const line of text.split("\n")) {
      const h = line.match(/^##\s+(.+?)\s*$/);
      if (h) { cur = h[1]; sections.set(cur, { top: [], nested: 0 }); continue; }
      if (!cur) continue;
      if (/^-\s+/.test(line)) sections.get(cur).top.push(line);
      else if (/^\s+-\s+/.test(line)) sections.get(cur).nested++;
    }

    const issues = [];
    for (const [field, rule] of Object.entries(sb.fields)) {
      const sec = sections.get(field);
      if (!sec) continue;
      const n = sec.top.length;
      if (rule.maxBullets != null && n > rule.maxBullets) issues.push(`${field}: ${n} bullets (max ${rule.maxBullets})`);
      if (rule.exactBullets != null && n !== rule.exactBullets) issues.push(`${field}: ${n} bullets (exactly ${rule.exactBullets})`);
      if (rule.maxWords != null) {
        const long = sec.top.map(bulletWords).filter((w) => w > rule.maxWords);
        if (long.length) issues.push(`${field}: ${long.length} bullet(s) over ${rule.maxWords} words (longest ${Math.max(...long)})`);
      }
      if (sec.nested) issues.push(`${field}: ${sec.nested} nested bullet(s) — fields are one level, history goes to LOG`);
    }

    // "Last touched" is one date plus a short clause; more dates means it's being appended to.
    const lt = text.match(/Last touched:?\**:?\s*([^|\n]*)/i);
    if (lt) {
      const dates = lt[1].match(DATE_RE) || [];
      if (dates.length > 1) issues.push(`Last touched: ${dates.length} dates — replace it, don't append`);
    }

    if (!issues.length) { clean++; continue; }
    add(strict.has(path) ? "red" : "amber", "state-budget", `\`${path}\` over field budget — ${issues.join("; ")}`, "Retire the least-live items to LOG.md, or trim; budgets are in diff-propose/SKILL.md");
  }
  if (clean) add("green", "state-budget", `${clean} STATE file(s) within field budgets`);
}

// ── Check 9: private boundary (two vaults) ──────────────────────────────────
// Added 2026-11-13. The private vault lives outside this repo and is mounted as a
// gitignored symlink (cfg.privateBoundary.mount). Two things must stay true:
// git never tracks the mount, and shared content never names a specific private
// file. walk() does not follow symlinks, so shared files are all it sees here.
async function checkPrivateBoundary() {
  const pb = cfg.privateBoundary;
  if (!pb?.mount) return;
  if (!SHARED && !existsSync(join(ROOT, pb.mount))) {
    add("amber", "private-boundary", `Private vault mount \`${pb.mount}\` is missing — private paths will not resolve`, "Create the symlink to your private vault");
    return;
  }
  const ignore = (await readSafe(join(ROOT, ".gitignore"))) || "";
  if (!ignore.split("\n").some((l) => l.trim() === `/${pb.mount}` || l.trim() === pb.mount)) {
    add("red", "private-boundary", `\`${pb.mount}\` is not in .gitignore — private files could be committed`, `Add /${pb.mount} to .gitignore`);
  }
  const fileRef = new RegExp(`${pb.mount}/[^\`"<>|)\\]\\n]*\\.(${POINTER_EXTS.join("|")})`, "i");
  let leaks = 0;
  for (const dir of pb.contentDirs || []) {
    for (const f of await walk(join(ROOT, dir))) {
      if (!f.endsWith(".md")) continue;
      const rel = f.slice(ROOT.length + 1);
      if (cfg.deadPointerExcludeSources?.some((g) => globToRe(g).test(rel))) continue;
      const text = await readSafe(f);
      const m = text && text.match(fileRef);
      if (m) { leaks++; add(pb.leakSeverity === "red" ? "red" : "amber", "private-boundary", `\`${rel}\` names a private file (\`${m[0]}\`)`, "Fine in your own vault. Remove the reference or move the fact before this file is shared with others"); }
    }
  }
  if (!leaks) add("green", "private-boundary", `No shared content file names a private file; \`${pb.mount}\` is gitignored`);
}

// ── Check 10: large files (audit item 12) ───────────────────────────────────
// One search hit on a 300 KB file can fill an agent's context. Kept sources go in cfg.largeFiles.allow.
function isTooLarge(rel, bytes, lf = cfg.largeFiles) {
  return !!lf && rel.endsWith(".md") && bytes > lf.maxKB * 1024
    && lf.dirs.some((d) => rel.startsWith(d + "/")) && !lf.allow.some((g) => globToRe(g).test(rel));
}
async function checkLargeFiles() {
  const lf = cfg.largeFiles;
  if (!lf) return;
  for (const dir of lf.dirs) {
    for (const f of await walk(join(ROOT, dir))) {
      const rel = f.slice(ROOT.length + 1), bytes = (await stat(f)).size;
      if (isTooLarge(rel, bytes)) add("amber", "large-file", `\`${rel}\` is ${Math.round(bytes / 1024)} KB (>${lf.maxKB} KB) — an agent that reads it whole loses most of its context`, "Split it, move history to LOG/archive, or add it to `largeFiles.allow` if it is a kept source");
    }
  }
}
// ── Check 11: typed facts (PLAN S2.4) ───────────────────────────────────────
// One file per fact in <Initiative>/facts/. Rules and limits are in cfg.facts.
async function checkFacts() {
  const fc = cfg.facts;
  if (!fc) return;
  const re = globToRe(fc.glob);
  let clean = 0;
  for (const p of [...VAULT_PATHS].filter((x) => re.test(x)).sort()) {
    const { errors, stale, unsourced } = factIssues((await readSafe(join(ROOT, p))) || "");
    if (errors.length) add("red", "fact", `\`${p}\`: ${errors.join("; ")}`, "Fix the frontmatter (see 3_RESOURCES/framework/templates/FACT.template.md)");
    else if (stale) add("amber", "fact-stale", `\`${p}\` ${stale}`, "Ask a person to check it, or find the original (Slack permalink, Doc link with section, metric ID, Jira/Productboard item) that states it and put the link in `source`; then set `verified` to today. Or close it (change `status`)");
    else if (unsourced) add("amber", "fact-unsourced", `\`${p}\` has a \`verified\` date but its \`source\` names no person check and no link to an original`, "Add the link or ID of the original, or \"Checked by <Name>\", to `source`. Otherwise set `verified` to \"not yet\"");
    else clean++;
  }
  if (clean) add("green", "fact", `${clean} typed fact(s) valid and inside their freshness limit`);
}
// ── Check 12: rejection loop (VISION §4.4 step 5; v2 PLAN Move 9 R2; PLAN S2.3) ──
// The same reason chip 3+ times in the last 10 sessions of one skill version → propose one rule change.
async function checkRejectionLoop() {
  const text = await readSafe(join(ROOT, SESSIONS));
  if (text === null) return;
  const hits = chipRule(parseSessions(text));
  for (const h of hits) add("amber", "rejection-loop", `Reason chip \`${h.chip}\` occurs ${h.count} times in the last ${h.window} sessions of skill version ${h.version}: ${h.sessions.join("; ")}`, "Propose one change to the diff-propose or ingest rules that stops this chip. The owner (`_private/ME.md`) approves it like any diff; never edit the skill in the same pass");
  if (!hits.length) add("green", "rejection-loop", "No reason chip occurs 3+ times in the last 10 sessions of any skill version");
}
// ── Check 13: not filled in yet (F1.3) ─────────────────────────────────────
// A new vault's to-do list: profile fields, the cycle file, stubs, and template text left in operational files.
async function checkNotFilled() {
  const todo = new Map();
  const note = (p, why) => todo.set(p, [...(todo.get(p) || []), why]);
  const priv = (p) => SHARED && p.startsWith(PRIV(cfg) + "/");
  for (const p of nf.profiles || []) {
    const text = priv(p) ? null : await readSafe(join(ROOT, p));
    const gaps = text === null ? [] : profileGaps(text);
    if (gaps.length) note(p, `fill in ${gaps.join(", ")}`);
  }
  const cycle = nf.cycleFile && await readSafe(join(ROOT, nf.cycleFile));
  if (cycle && cycleMissing(cycle)) note(nf.cycleFile, "no cycle name or dates");
  const skip = (nf.skip || []).map(globToRe);
  const ops = operationalTargets();
  for (const p of [...VAULT_PATHS].sort()) {
    if (!/\.(md|base)$/.test(p) || priv(p) || skip.some((re) => re.test(p))) continue;
    const text = await readSafe(join(ROOT, p));
    if (!text) continue;
    if (isStub(text)) note(p, "still the starter text");
    else if (ops.has(p)) { const t = templateText(text); if (t) note(p, `template text left: \`${t}\``); }
  }
  for (const [p, why] of todo) {
    add("todo", "not-filled", `\`${p}\`: ${why.join("; ")}`, (nf.profiles || []).includes(p) ? "Fill in the Value column" : `Fill it in, then delete the \`> ${nf.marker}\` line if it has one`);
  }
}
await buildInventory();
await checkNotFilled();
await checkDeadPointers();
await checkStaleness();
await checkOrphanSkills();
await checkInbox();
await checkVersionDrift();
await checkDeployedSkills();
await checkRunIntegrity();
await checkStateBudgets();
await checkPrivateBoundary();
await checkLargeFiles();
await checkFacts();
await checkRejectionLoop();

// ── Output ──────────────────────────────────────────────────────────────────
const stamp = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

if (AS_JSON) {
  // Audit item 8: tag findings on a STATE file with its owner (Slack ID from owner_slack, else the owner name).
  for (const f of [...findings.red, ...findings.amber]) {
    const p = f.msg.match(/`([^`]*\/STATE\.md)`/)?.[1];
    const fm = p && /^---\n([\s\S]*?)\n---/.exec((await readSafe(join(ROOT, p))) || "")?.[1];
    const field = (k) => fm?.match(new RegExp(`^${k}:[ \\t]*"?([^"\\n]*?)"?[ \\t]*$`, "m"))?.[1];
    if (fm) f.owner = field("owner_slack") || field("owner") || null;
  }
  console.log(JSON.stringify({ date: stamp, findings }, null, 2));
} else {
  const section = (title, arr) => arr.length
    ? `\n## ${title}\n` + arr.map((f) => `- **[${f.check}]** ${f.msg}${f.fix ? `\n  → _${f.fix}_` : ""}`).join("\n") + "\n"
    : "";
  let out = `# Lint Report (mechanical${SHARED ? ", shared checks only" : ""}) — ${stamp}\n`;
  out += `\n_Deterministic checks only. Run the \`lint\` skill's judgment pass for single-source-of-truth conflicts, semantic staleness, and what-to-investigate-next._\n`;
  out += section("📝 Not filled in yet — do these first", findings.todo);
  out += section("🔴 Must fix", findings.red);
  out += section("🟡 Should fix", findings.amber);
  out += section("🟢 Healthy", findings.green);
  out += `\n---\n_Summary: ${findings.red.length} must-fix · ${findings.amber.length} should-fix · ${findings.green.length} healthy · ${findings.todo.length} not filled in yet._\n`;
  out += `\n**Judgment pass (needs the agent — not checked here):** single-source-of-truth conflicts (same fact, two files, different values) · semantic staleness (dates fresh but content wrong) · orphan/missing structure · 2–3 questions worth investigating next.\n`;
  console.log(out);
}

if (STRICT && findings.red.length) process.exit(1);

#!/usr/bin/env node
// scorecard.mjs — the E2 scorecard (PLAN S2.3; v2 PLAN "Evals" E2).
//
// Prints one page per skill version (diff-propose / ingest) from what is
// already logged: diff-sessions.md (outcomes, tiers, reason chips, minutes per
// day), git (words added to STATE, STATE changes outside diff-propose) and
// lint Check 8 (STATE budgets, latest version only). Read the clean rate with
// the counter-metric, never alone.
//
// Usage:
//   node .scripts/scorecard.mjs             # markdown, one page per version
//   node .scripts/scorecard.mjs --selftest  # assert-based check on a fixture
//
// lint.mjs imports parseSessions and chipRule (Check 12, rejection loop).
// Zero dependencies. Node 22+.

import { readFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { join, dirname, resolve, basename } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const SESSIONS = "3_RESOURCES/AI Skills/diff-propose/diff-sessions.md";
const MIN_SESSIONS = 10; // R2 window and the "enough to judge" bar
const MIN_DECIDED = 30; // diff-sessions.md: tier comparison needs ~30 tier-logged diffs

const cells = (line) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((s) => s.trim());
// Rows of the first table under `heading`, keyed by lower-case header. Columns are found by name, so new columns do not break it.
function table(text, heading) {
  const sec = text.split(heading)[1];
  if (!sec) return [];
  const lines = sec.split("\n").map((l) => l.trim());
  const start = lines.findIndex((l) => l.startsWith("|"));
  if (start < 0) return [];
  const head = cells(lines[start]).map((h) => h.toLowerCase());
  const out = [];
  for (const l of lines.slice(start + 2)) {
    if (!l.startsWith("|")) break;
    const c = cells(l);
    if (c.length === head.length) out.push(Object.fromEntries(head.map((h, i) => [h, c[i]])));
  }
  return out;
}
const col = (row, prefix) => row[Object.keys(row).find((k) => k.startsWith(prefix))];
const num = (s) => (/^\d+$/.test(s ?? "") ? +s : 0);
const blank = (s) => !s || s === "—" || s === "-";
const tier = (s) => (/^\d+\/\d+\/\d+$/.test(s ?? "") ? s.split("/").map(Number) : null);

// "wrong fact ×2, wording" → { "wrong fact": 2, wording: 1 }. Unknown chips are kept as they are.
export function parseReasons(s) {
  const out = {};
  if (blank(s)) return out;
  for (const part of s.split(",").map((p) => p.trim()).filter(Boolean)) {
    const m = part.match(/^(.*?)\s*[×x]\s*(\d+)$/);
    const [chip, n] = m ? [m[1], +m[2]] : [part, 1];
    out[chip] = (out[chip] || 0) + n;
  }
  return out;
}

export function parseSessions(text) {
  return table(text, /^## Sessions\s*$/m).map((r) => ({
    date: col(r, "date"), initiative: col(r, "initiative"),
    trigger: (col(r, "trigger") || "").match(/^(daily-slack-review|meeting-ingest|ingest)/)?.[1] ?? "other",
    proposed: num(col(r, "proposed")), approved: num(col(r, "approved")), edited: num(col(r, "edited")),
    rejected: num(col(r, "rejected")), pending: num(col(r, "pending")),
    direct: tier(col(r, "direct")), inferred: tier(col(r, "inferred")),
    version: blank(col(r, "versions")) ? null : col(r, "versions"),
    reasons: parseReasons(col(r, "reasons")),
  }));
}

// R2 / VISION §4.4 step 5: a chip (not `none`) seen 3+ times in the last 10 sessions of one version.
export function chipRule(rows, window = MIN_SESSIONS, limit = 3) {
  const hits = [];
  const versions = [...new Set(rows.filter((r) => r.version).map((r) => r.version))];
  for (const v of versions) {
    const last = rows.filter((r) => r.version === v).sort((a, b) => a.date.localeCompare(b.date)).slice(-window);
    const count = {};
    for (const r of last) for (const [c, n] of Object.entries(r.reasons)) if (c !== "none") count[c] = (count[c] || 0) + n;
    for (const [chip, n] of Object.entries(count)) if (n >= limit) {
      hits.push({ version: v, chip, count: n, window: last.length, sessions: last.filter((r) => r.reasons[chip]).map((r) => `${r.date} ${r.initiative}`) });
    }
  }
  return hits;
}

const pct = (a, b) => (b ? `${Math.round((100 * a) / b)}%` : "n/a");
const sum = (rows, k) => rows.reduce((s, r) => s + r[k], 0);

// The parts of a page that need only the session rows (selftest covers these).
export function outcomes(rows) {
  const decided = sum(rows, "approved") + sum(rows, "edited") + sum(rows, "rejected");
  const byTrigger = {};
  for (const r of rows) {
    const t = (byTrigger[r.trigger] ??= { a: 0, d: 0 });
    t.a += r.approved; t.d += r.approved + r.edited + r.rejected;
  }
  const tiers = {};
  for (const k of ["direct", "inferred"]) {
    const t = rows.filter((r) => r[k]).reduce((s, r) => s.map((x, i) => x + r[k][i]), [0, 0, 0]);
    tiers[k] = { a: t[0], d: t[0] + t[1] + t[2] };
  }
  const chips = {};
  for (const r of rows) for (const [c, n] of Object.entries(r.reasons)) chips[c] = (chips[c] || 0) + n;
  // Rows with an edit or reject but no chip at all: E1 is not being filled in.
  const noChip = rows.filter((r) => r.edited + r.rejected > 0 && !Object.keys(r.reasons).length).length;
  return { decided, byTrigger, tiers, chips, noChip };
}

function git(...a) {
  try { return execFileSync("git", a, { cwd: ROOT, encoding: "utf8", maxBuffer: 64 << 20, stdio: ["ignore", "pipe", "ignore"] }); } catch { return null; }
}
const STATE_GLOB = ":(glob)1_PROJECTS/**/STATE.md";
const nextDay = (d) => new Date(Date.parse(d) + 86_400_000).toISOString().slice(0, 10);

function page(key, rows, until, extra) {
  const dates = rows.map((r) => r.date).sort();
  const [from, to] = [dates[0], dates.at(-1)];
  const o = outcomes(rows);
  const P = sum(rows, "proposed"), A = sum(rows, "approved"), E = sum(rows, "edited"), R = sum(rows, "rejected"), N = sum(rows, "pending");
  const inits = [...new Set(rows.map((r) => r.initiative))];
  let s = `# Scorecard — ${key ? `diff-propose / ingest ${key}` : "unversioned rows (before E1)"}\n\n`;
  s += `Sessions: ${rows.length} (${from} to ${to}). Initiatives: ${inits.join(", ")}.\n`;
  const warn = [];
  if (rows.length < MIN_SESSIONS) warn.push(`fewer than ${MIN_SESSIONS} sessions`);
  if (o.decided < MIN_DECIDED) warn.push(`fewer than ${MIN_DECIDED} decided diffs`);
  if (!key) warn.push("no tier or chip data before E1");
  if (warn.length) s += `**Small sample:** ${warn.join("; ")}. Read these numbers as a direction, not a result.\n`;

  s += `\n## Outcomes\n\n| Measure | Count | Rate |\n|---|---|---|\n`;
  s += `| Proposed | ${P} | |\n| Decided (A+E+R) | ${o.decided} | |\n`;
  s += `| Approved (clean rate) | ${A} | ${pct(A, o.decided)} of decided |\n| Edited | ${E} | ${pct(E, o.decided)} of decided |\n`;
  s += `| Rejected | ${R} | ${pct(R, o.decided)} of decided |\n| Pending (ignored) | ${N} | ${pct(N, P)} of proposed |\n`;

  s += `\n## Clean rate by trigger\n\n| Trigger | Decided | Clean rate |\n|---|---|---|\n`;
  for (const [t, x] of Object.entries(o.byTrigger)) s += `| ${t} | ${x.d} | ${pct(x.a, x.d)} |\n`;
  s += `\n## Clean rate by tier (direct vs inferred)\n\n| Tier | Decided | Clean rate |\n|---|---|---|\n`;
  for (const [t, x] of Object.entries(o.tiers)) s += `| ${t} | ${x.d} | ${pct(x.a, x.d)} |\n`;

  s += `\n## Reason chips (edits and rejects)\n\n`;
  const chips = Object.entries(o.chips).sort((a, b) => b[1] - a[1]);
  s += chips.length ? chips.map(([c, n]) => `- ${c}: ${n}`).join("\n") + "\n" : "- none logged\n";
  if (o.noChip) s += `- Sessions with an edit or reject but no chip logged: ${o.noChip}\n`;

  // git: STATE files changed from the first session of this version until the next version starts.
  s += `\n## STATE growth (git, ${from} to ${until})\n\n`;
  const log = git("log", `--since=${from}`, `--until=${nextDay(until)}`, "--diff-filter=M", "--format=", "--name-only", "--", STATE_GLOB);
  const wd = git("log", `--since=${from}`, `--until=${nextDay(until)}`, "-p", "--diff-filter=M", "--word-diff=porcelain", "--format=", "--", ...extra.statePaths.filter((p) => inits.includes(basename(dirname(p)))), "no-such-path"); // never an empty pathspec (= whole repo)
  if (log === null || wd === null) s += "- git not available\n";
  else {
    if (extra.firstCommit > from) s += `- Git history starts ${extra.firstCommit}; changes before that are not counted.\n`;
    const added = wd.split("\n").filter((l) => l.startsWith("+") && !l.startsWith("+++")).reduce((n, l) => n + l.slice(1).split(/\s+/).filter(Boolean).length, 0);
    s += `- Words added to these initiatives' STATE.md: ${added}; per approved or edited diff: ${A + E ? Math.round(added / (A + E)) : "n/a"}\n`;
    const changed = [...new Set(log.split("\n").filter(Boolean))];
    // Counter-metric part 1. Lower bound: diff-propose writes are not tagged, so a STATE change for an initiative with a session is not counted.
    const manual = changed.filter((p) => !inits.includes(basename(dirname(p))));
    s += `\n## Counter-metric (what the clean rate can hide)\n\n`;
    s += `- Manual edits (lower bound): ${manual.length} STATE.md file(s) changed with no diff-propose session for that initiative${manual.length ? `: ${manual.map((p) => basename(dirname(p))).join(", ")}` : ""}\n`;
  }
  s += `- Monthly sampled audit (5 STATE items, "still true?"): no results logged yet\n`;

  const mins = extra.minutes.filter((m) => m.week >= new Date(Date.parse(from) - 6 * 86_400_000).toISOString().slice(0, 10) && m.week <= until);
  s += `\n## Minutes per day (go/no-go, target under 10)\n\n`;
  s += mins.length ? mins.map((m) => `- Week of ${m.week}: ${m.minutes}`).join("\n") + "\n" : "- none logged in this window\n";

  if (extra.latest) {
    s += `\n## STATE now (latest version only)\n\n| Initiative | Words | Budget findings (lint Check 8) |\n|---|---|---|\n`;
    for (const i of inits) {
      const p = extra.statePaths.find((x) => basename(dirname(x)) === i);
      s += `| ${i} | ${p ? extra.words[p] ?? "n/a" : "no STATE.md"} | ${p ? extra.budget.filter((f) => f.msg.includes(p)).length : "n/a"} |\n`;
    }
  }
  return s;
}

async function main() {
  const text = await readFile(join(ROOT, SESSIONS), "utf8");
  const rows = parseSessions(text);
  const minutes = table(text, /^## Minutes per day.*$/m).map((r) => ({ week: col(r, "week"), minutes: col(r, "minutes") }));
  const statePaths = (git("ls-files", STATE_GLOB) || "").split("\n").filter(Boolean);
  const words = {};
  for (const p of statePaths) words[p] = (await readFile(join(ROOT, p), "utf8")).split(/\s+/).filter(Boolean).length;
  let budget = [];
  try {
    const out = execFileSync(process.execPath, [join(ROOT, ".scripts/lint.mjs"), "--shared", "--json"], { cwd: ROOT, encoding: "utf8", maxBuffer: 64 << 20 });
    budget = JSON.parse(out).findings.red.concat(JSON.parse(out).findings.amber).filter((f) => f.check === "state-budget");
  } catch { /* lint failed: budget column shows 0; the lint run itself reports why */ }
  const firstCommit = (git("log", "--max-parents=0", "--format=%ad", "--date=short") || "").trim().split("\n").sort()[0] || "";

  const keys = [...new Set(rows.map((r) => r.version))].sort((a, b) => (a === null ? -1 : b === null ? 1 : a.localeCompare(b)));
  const today = new Date().toISOString().slice(0, 10);
  const pages = keys.map((k, i) => {
    const rs = rows.filter((r) => r.version === k);
    const next = keys[i + 1] !== undefined ? rows.filter((r) => r.version === keys[i + 1]).map((r) => r.date).sort()[0] : null;
    const until = next ? new Date(Date.parse(next) - 86_400_000).toISOString().slice(0, 10) : today;
    return page(k, rs, until, { minutes, statePaths, words, budget, firstCommit, latest: i === keys.length - 1 });
  });
  const versioned = keys.filter(Boolean).length;
  let head = `_Source: \`${SESSIONS}\`. ${rows.length} sessions, ${rows.filter((r) => r.version).length} versioned, ${versioned} skill version(s)._\n`;
  if (versioned < 2) head += `_Only ${versioned} versioned skill version: no version-to-version comparison is possible yet._\n`;
  console.log(head + "\n" + pages.join("\n---\n\n"));
}

const isMain = !!process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url); // lint.mjs imports this file
if (isMain && process.argv.includes("--selftest")) {
  const ok = (c, m) => { if (!c) { console.error("selftest FAIL: " + m); process.exitCode = 1; } };
  const H = "| Date | Initiative | Trigger | Proposed | Approved | Edited | Rejected | Pending | Note | Direct A/E/R | Inferred A/E/R | Versions (dp / ingest) | Reasons | Source flags |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n";
  const row = (d, init, trig, p, a, e, r, n, dir, inf, v, rs) => `| ${d} | ${init} | ${trig} | ${p} | ${a} | ${e} | ${r} | ${n} | note | ${dir} | ${inf} | ${v} | ${rs} | disagree |\n`;
  const fx = "## Sessions\n\n" + H
    + row("2026-08-14", "{{PILOT}}", "ingest (ad hoc)", 2, 0, 0, 2, 0, "—", "—", "—", "—")
    + row("2026-11-02", "{{PILOT}}", "daily-slack-review (x)", 4, 2, 1, 1, 0, "1/0/1", "1/1/0", "v1 / v1", "wording, wrong fact ×1")
    + row("2026-11-03", "SCW", "meeting-ingest (y)", 2, 1, 1, 0, 1, "0/0/0", "1/1/0", "v1 / v1", "disagree ×2")
    + "\n## Running totals\n| a | b |\n|---|---|\n| 1 | 2 |\n";
  const rows = parseSessions(fx);
  ok(rows.length === 3, "parse: 3 rows, running totals table ignored");
  ok(rows[0].version === null && rows[1].version === "v1 / v1", "parse: versions");
  ok(rows[1].trigger === "daily-slack-review" && rows[2].trigger === "meeting-ingest" && rows[0].trigger === "ingest", "parse: trigger kind");
  ok(rows[1].reasons.wording === 1 && rows[1].reasons["wrong fact"] === 1 && rows[2].reasons.disagree === 2, "parse: chips, unknown chip kept");
  const o = outcomes(rows.filter((r) => r.version));
  ok(o.decided === 6 && o.byTrigger["daily-slack-review"].a === 2 && o.byTrigger["daily-slack-review"].d === 4, "outcomes: decided and by trigger");
  ok(o.tiers.direct.d === 2 && o.tiers.direct.a === 1 && o.tiers.inferred.d === 4 && o.tiers.inferred.a === 2, "outcomes: tiers");
  ok(o.chips.disagree === 2 && o.noChip === 0, "outcomes: chip mix");
  ok(outcomes(rows.slice(0, 1)).noChip === 1, "outcomes: reject with no chip counted");
  ok(pct(1, 3) === "33%" && pct(1, 0) === "n/a", "pct");
  if (!process.exitCode) console.log("scorecard selftest ok");
} else if (isMain) {
  await main();
}

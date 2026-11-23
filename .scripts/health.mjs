#!/usr/bin/env node
// health.mjs — PLAN S2.2: turn one lint run into one row of health numbers (VISION §4.4 item 4).
//
// Usage:
//   node .scripts/lint.mjs --shared --json > lint.json
//   node .scripts/health.mjs lint.json            # print the Slack lead line only
//   node .scripts/health.mjs lint.json --append   # also append the row to 2_AREAS/{{ORG}}/_metrics/health.csv
//   node .scripts/health.mjs --selftest
//
// Measures (all from lint's own output, so the numbers match the findings list):
//   states_*   STATE files in lint's field-budget check; in budget = no state-budget finding.
//   sources_*  operational files in lint's staleness check; fresh = no stale/unverified/contract/stamp finding.
//   asks_*     red + amber findings that lint tags with a STATE owner (the asks the quality loop sends a person).
//              asks_max is the largest count for one owner (VISION target: 3 or less a week).
//   minutes_per_week  the newest "minutes per week" row in BASELINES.md, until a newer number exists.
//   truth_rate, test_score  empty until PLAN S3.5.
// Zero dependencies.

import { readFileSync, appendFileSync, existsSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CSV = join(ROOT, "2_AREAS/{{ORG}}/_metrics/health.csv");
const BASELINES = join(ROOT, "1_PROJECTS/memory-system-upgrade/BASELINES.md");
const COLS = ["date", "states_in_budget", "states_total", "sources_fresh", "sources_total", "asks_max", "asks_by_owner", "minutes_per_week", "truth_rate", "test_score"];
// Findings from lint's staleness check (Check 2). "contract" is only a file finding when amber; the red one names a config error.
const STALE_CHECKS = new Set(["stale", "unverified", "missing-stamp", "source-newer", "contract-overdue"]);

const greenCount = (green, check, re) => Number(green.find((f) => f.check === check && re.test(f.msg))?.msg.match(/^(\d+)/)?.[1] ?? 0);
const pathOf = (msg) => msg.match(/`([^`]+)`/)?.[1];

export function row({ date, findings: f }, minutes) {
  const bad = [...f.red, ...f.amber];

  const statesOver = bad.filter((x) => x.check === "state-budget").length;
  const statesIn = greenCount(f.green, "state-budget", /STATE file\(s\) within field budgets/);

  const stale = new Set(bad.filter((x) =>
    STALE_CHECKS.has(x.check) || (x.check === "contract" && f.amber.includes(x)) || (x.check === "dead-pointer" && /^Operational file /.test(x.msg))
  ).map((x) => pathOf(x.msg)));
  const fresh = greenCount(f.green, "staleness", /operational file\(s\) within/);

  // Same grouping as the Slack digest: a finding with an owner key counts; a null owner is "no owner".
  const by = {};
  for (const x of bad) if (x.owner !== undefined) by[x.owner || "no owner"] = (by[x.owner || "no owner"] || 0) + 1;
  const owners = Object.entries(by).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

  // A new vault whose operational files are all stubs (lint lists them under todo) has no sources yet: report it, don't throw.
  const noSourcesYet = fresh + stale.size === 0 && f.todo?.some((x) => x.check === "not-filled");
  if (statesIn + statesOver === 0 || (fresh + stale.size === 0 && !noSourcesYet)) throw new Error("lint output has no STATE or staleness results; did its format change?");
  return {
    date, states_in_budget: statesIn, states_total: statesIn + statesOver,
    sources_fresh: fresh, sources_total: fresh + stale.size,
    asks_max: owners[0]?.[1] ?? 0, asks_by_owner: owners.map(([o, n]) => `${o}=${n}`).join(" "),
    minutes_per_week: minutes, truth_rate: "", test_score: "",
  };
}

// The newest BASELINES row whose Measure says "minutes per week"; bold and en dash removed.
export function minutesFrom(md) {
  const rows = md.split("\n").filter((l) => /^\|[^|]*minutes per week/i.test(l));
  return rows.length ? rows.at(-1).split("|")[2].replace(/\*/g, "").replace(/–/g, "-").trim() : "";
}

const cell = (v) => (/[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
export const csvLine = (r) => COLS.map((c) => cell(r[c])).join(",");

export function slackLine(r) {
  const n = (v) => (v === "" ? "—" : v);
  return `*Vault health ${r.date}:* STATEs in budget ${r.states_in_budget}/${r.states_total} · ${r.sources_total ? `sources fresh ${r.sources_fresh}/${r.sources_total}` : "no sources yet"}`
    + ` · most asks for one owner ${r.asks_max} (target 3 or less) · upkeep ${n(r.minutes_per_week)} min/week`
    + ` · truth rate ${n(r.truth_rate)} · test score ${n(r.test_score)}`;
}

if (process.argv.includes("--selftest")) {
  const assert = (await import("node:assert/strict")).default;
  const lint = { date: "2026-11-23", findings: {
    red: [
      { check: "state-budget", msg: "`A/STATE.md` over field budget", owner: "U1" },
      { check: "dead-pointer", msg: "Operational file `x.md` (staleness policy) is missing" },
      { check: "contract", msg: "Refresh contract names `y.md`, which is not an operational file" },
    ],
    amber: [
      { check: "stale", msg: "`A/STATE.md` last updated 20d ago", owner: "U1" },
      { check: "unverified", msg: "`c.md` says not yet" },
      { check: "source-newer", msg: "`d.md` reflects PowerBI" },
      { check: "contract-overdue", msg: "`d.md` was never confirmed" }, // same file twice counts once
      { check: "contract", msg: "`e.md` has a refresh contract but no readable date" },
      { check: "state-budget", msg: "`B/STATE.md` over field budget", owner: null },
      { check: "large-file", msg: "`big.md` is 50 KB" },
    ],
    green: [
      { check: "staleness", msg: "4 operational file(s) within their freshness and verification windows" },
      { check: "staleness", msg: "2 paused initiative STATE file(s) skipped" },
      { check: "state-budget", msg: "3 STATE file(s) within field budgets" },
    ],
  } };
  const r = row(lint, "60-120");
  assert.equal(r.states_in_budget, 3); assert.equal(r.states_total, 5);
  assert.equal(r.sources_fresh, 4); assert.equal(r.sources_total, 9); // x, A, c, d, e + 4 fresh
  assert.equal(r.asks_max, 2); assert.equal(r.asks_by_owner, "U1=2 no owner=1");
  assert.equal(csvLine(r), "2026-11-23,3,5,4,9,2,U1=2 no owner=1,60-120,,");
  assert.match(slackLine(r), /STATEs in budget 3\/5 · sources fresh 4\/9 .* truth rate — · test score —$/);
  assert.equal(minutesFrom("| Measure | Value |\n| Owner's minutes per week on upkeep | **60–120** | 2026-11-22 |\n| Minutes per week (correction) | **45** | x |"), "45");
  assert.equal(minutesFrom("no table"), "");
  assert.throws(() => row({ date: "d", findings: { red: [], amber: [], green: [] } }, ""), /format change/);
  const stubs = { date: "d", findings: { red: [], amber: [], green: lint.findings.green.slice(2), todo: [{ check: "not-filled", msg: "`s.md`: still the starter text" }] } };
  assert.match(slackLine(row(stubs, "")), /STATEs in budget 3\/3 · no sources yet · /);
  console.log("selftest ok");
  process.exit();
}

const file = process.argv.slice(2).find((a) => !a.startsWith("--"));
if (!file) { console.error("usage: node .scripts/health.mjs <lint.json> [--append] | --selftest"); process.exit(2); }
const r = row(JSON.parse(readFileSync(file, "utf8")), existsSync(BASELINES) ? minutesFrom(readFileSync(BASELINES, "utf8")) : "");
if (process.argv.includes("--append")) {
  if (!existsSync(CSV)) appendFileSync(CSV, COLS.join(",") + "\n");
  appendFileSync(CSV, csvLine(r) + "\n");
}
console.log(slackLine(r));

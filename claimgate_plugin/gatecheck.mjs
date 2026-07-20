#!/usr/bin/env node
/**
 * GateCheck v0.1 — who guards the guards: acceptance testing for gates themselves.
 *
 *   gatecheck <manifest.json> [--heldout <dir>]
 *       exit 0 = gate implementation ACCEPTED, 1 = rejected, 2 = error
 *
 * The bootstrap problem: agents cheat while IMPLEMENTING control systems
 * (a builder under pressure to go green writes gates that structurally cannot
 * fail). You cannot trust the builder's word that the gate works — but you can
 * trust that the gate REJECTS a sealed library of known-bad cases and PASSES
 * known-good ones. The fixture library is the trust anchor:
 *
 *   - curated by the human (small, readable), sealed BEFORE the gate is built
 *   - the builder agent sees the visible cases; a --heldout dir contains cases
 *     the builder never saw (blindness — same shape, unknown content)
 *   - every discovered bypass becomes a new fixture: gates only ratchet tighter
 *
 * Manifest:
 * {
 *   "gate_name": "claimgate lint-receipt",
 *   "cases": [
 *     {"id": "inflated-verdict", "cmd": "node", "args": ["claimgate.mjs", "lint-receipt", "fixtures/receipt_inflated.json"], "expect_exit": 1},
 *     {"id": "honest-receipt",   "cmd": "node", "args": ["claimgate.mjs", "lint-receipt", "fixtures/receipt_honest.json"],   "expect_exit": 0}
 *   ]
 * }
 *
 * Held-out dir: each subdirectory is a case containing case.json
 * ({cmd, args, expect_exit}) with paths relative to that subdirectory.
 *
 * A gate is ACCEPTED only when EVERY case (visible + held-out) produces its
 * expected exit code. Any surprise in either direction — a bad case admitted
 * OR a good case rejected — is a rejection of the gate implementation.
 *
 * No dependencies. Node >= 18. Small on purpose: this file is part of the
 * trusted base a human actually reads.
 */

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

function die(msg, code = 2) {
  process.stderr.write(`gatecheck: ${msg}\n`);
  process.exit(code);
}

function runCase(c, cwd) {
  const r = spawnSync(c.cmd, c.args, { cwd, timeout: c.timeout_ms ?? 60000, encoding: "utf8" });
  if (r.error) return { got: null, err: String(r.error.message) };
  return { got: r.status, err: null };
}

function main() {
  const args = process.argv.slice(2);
  const manifestPath = args.find((a) => !a.startsWith("--"));
  const hi = args.indexOf("--heldout");
  const heldoutDir = hi >= 0 ? args[hi + 1] : null;
  if (!manifestPath) die("usage: gatecheck <manifest.json> [--heldout <dir>]");

  let manifest;
  try { manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8")); } catch (e) { die(`bad manifest: ${e.message}`); }
  const cases = manifest.cases || [];
  if (cases.length < 2) die("manifest needs at least one expected-reject and one expected-pass case — a gate tested only one way is not tested");
  const exits = new Set(cases.map((c) => c.expect_exit));
  if (!exits.has(0) || ![...exits].some((e) => e !== 0)) {
    die("manifest must contain BOTH expect_exit 0 (known-good admitted) and nonzero (known-bad rejected) cases — one-sided fixtures let a gate that always passes (or always fails) through");
  }

  const results = [];
  const baseDir = path.dirname(path.resolve(manifestPath));

  for (const c of cases) {
    if (!c.id || !c.cmd || !Array.isArray(c.args) || !Number.isInteger(c.expect_exit)) {
      die(`malformed case: ${JSON.stringify(c).slice(0, 100)} (need id, cmd, args[], expect_exit)`);
    }
    const { got, err } = runCase(c, baseDir);
    results.push({ id: c.id, heldout: false, expect: c.expect_exit, got, ok: got === c.expect_exit, err });
  }

  if (heldoutDir) {
    let subdirs = [];
    try { subdirs = fs.readdirSync(heldoutDir, { withFileTypes: true }).filter((e) => e.isDirectory()); } catch (e) { die(`cannot read heldout dir: ${e.message}`); }
    if (!subdirs.length) die("--heldout given but contains no case directories");
    for (const d of subdirs) {
      const caseDir = path.join(heldoutDir, d.name);
      let c;
      try { c = JSON.parse(fs.readFileSync(path.join(caseDir, "case.json"), "utf8")); } catch (e) { die(`heldout case ${d.name}: ${e.message}`); }
      const { got, err } = runCase(c, path.resolve(caseDir));
      results.push({ id: `heldout/${d.name}`, heldout: true, expect: c.expect_exit, got, ok: got === c.expect_exit, err });
    }
  }

  const failures = results.filter((r) => !r.ok);
  const report = {
    tool: "gatecheck",
    gate: manifest.gate_name || manifestPath,
    cases_run: results.length,
    heldout_run: results.filter((r) => r.heldout).length,
    verdict: failures.length ? "GATE_REJECTED" : "GATE_ACCEPTED",
    failures,
    results,
  };
  process.stdout.write(JSON.stringify(report, null, 1) + "\n");
  process.exit(failures.length ? 1 : 0);
}

main();

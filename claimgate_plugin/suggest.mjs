#!/usr/bin/env node
/**
 * suggest.mjs -- the generative rebalance: turns a gate's NO into a HOW.
 *
 * Read-only over every gate's output. It never edits gate_registry.json,
 * gates_manifest.json, claim_verify.py, claimgate.mjs, claimgate/claimgate.py,
 * ratchet_floor.py, fixtures/, or any AUDIT_VERDICT.md -- those are contended
 * or owned by other sessions (see FIX_PATTERNS.md). It re-runs them exactly as
 * the harness does, reads their JSON, and appends a paste-ready fix per
 * finding. It cannot weaken a verdict: it changes no exit code but its own.
 *
 *   node suggest.mjs <receipt.json> [--reason <gate_output.json>]
 *                                    [--store <ratchet_floor_store.json>]
 *                                    [--json]
 *
 *   exit 0 = ran to completion (findings, if any, are printed -- this tool
 *            never fails a receipt, it only explains a failure)
 *   exit 2 = usage / IO error (bad path, unreadable receipt JSON)
 *
 * Interface is stdout: a human block, then a "=== SUGGEST (json) ===" marker,
 * then one JSON object {findings: [...]}. --json prints only the JSON object.
 *
 * Dependency-free Node (fs/path/child_process/url only, no npm packages).
 */
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

function die(msg, code = 2) {
  process.stderr.write(`suggest: ${msg}\n`);
  process.exit(code);
}

function findRepoRoot(start) {
  let d = path.resolve(start);
  for (;;) {
    if (fs.existsSync(path.join(d, ".git")) && fs.existsSync(path.join(d, "claimgate_plugin"))) return d;
    const parent = path.dirname(d);
    if (parent === d) return process.cwd();
    d = parent;
  }
}

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = findRepoRoot(HERE);
const PLUGIN_DIR = path.join(ROOT, "claimgate_plugin");

function run(cmd, args, cwd = ROOT) {
  const r = spawnSync(cmd, args, { cwd, encoding: "utf8", timeout: 120000, maxBuffer: 16 * 1024 * 1024 });
  return { status: r.status, stdout: r.stdout || "", stderr: r.stderr || "", error: r.error };
}

function parseJsonSafe(s) {
  try { return JSON.parse(s); } catch { return null; }
}

function readTextSafe(p) {
  try { return fs.readFileSync(p, "utf8"); } catch { return null; }
}

// ---------------------------------------------------------------- live data
// Everything below is READ, never guessed -- so a fix stays true even if the
// source rules/registries change under it.

function extractArrayLiteral(src, key) {
  if (!src) return null;
  const m = src.match(new RegExp(`${key}\\s*:\\s*(\\[[^\\]]*\\])`, "s"));
  if (!m) return null;
  const parsed = parseJsonSafe(m[1]);
  return Array.isArray(parsed) ? parsed : null;
}

function loadLiveData() {
  const mjsSrc = readTextSafe(path.join(PLUGIN_DIR, "claimgate.mjs"));
  const rulesRatchet = parseJsonSafe(readTextSafe(path.join(PLUGIN_DIR, "rules_ratchet.json"))) || {};
  const registry = parseJsonSafe(readTextSafe(path.join(PLUGIN_DIR, "gate_registry.json"))) || {};
  const pySrc = readTextSafe(path.join(ROOT, "claimgate", "claimgate.py"));

  // mirror claimgate.mjs's `{ ...DEFAULT_RULES, ...readJson(rulesPath) }` merge,
  // reconstructing DEFAULT_RULES fields live from the committed source text.
  const defaultFromMjs = {
    provenance_fields: extractArrayLiteral(mjsSrc, "provenance_fields") || [],
    baseline_fields: extractArrayLiteral(mjsSrc, "baseline_fields") || [],
    divergence_explanation_fields: extractArrayLiteral(mjsSrc, "divergence_explanation_fields") || [],
    claim_field_patterns: extractArrayLiteral(mjsSrc, "claim_field_patterns") || [],
    chance_fields: extractArrayLiteral(mjsSrc, "chance_fields") || [],
    recompute_ops: extractArrayLiteral(mjsSrc, "recompute_ops") || [],
  };
  const rules = { ...defaultFromMjs, ...rulesRatchet };

  let allowedClassifications = [];
  if (pySrc) {
    const m = pySrc.match(/ALLOWED_CLASSIFICATIONS\s*=\s*\{([^}]*)\}/s);
    if (m) allowedClassifications = [...m[1].matchAll(/"([^"]+)"/g)].map((x) => x[1]).sort();
  }

  return {
    rules,
    allowedClassifications,
    verdictPassMap: rulesRatchet.verdict_pass_map || {},
    claimKinds: registry.claim_kinds || {},
    gates: registry.gates || {},
    calibrationGates: (registry.audit_policy || {}).calibration_gates || {},
    registry,
  };
}

// ---------------------------------------------------------------- ingestion
// Each ingest_* function runs a real gate and turns its JSON into
// {source, code, detail, trail?} findings. No detection logic is
// re-implemented here beyond what the gates themselves already computed.

function ingestClaimgateMjs(receiptPath, findings) {
  const mjs = path.join(PLUGIN_DIR, "claimgate.mjs");
  const rules = path.join(PLUGIN_DIR, "rules_ratchet.json");
  if (!fs.existsSync(mjs)) return;
  const r = run("node", [mjs, "lint-receipt", receiptPath, "--rules", rules]);
  const parsed = parseJsonSafe(r.stdout);
  if (parsed && Array.isArray(parsed.violations)) {
    for (const v of parsed.violations) {
      findings.push({ source: "claimgate.mjs (tier0 -- the linter hooks/post_receipt_gate.sh actually invokes)", code: v.rule, detail: v.detail, trail: v.trail });
    }
  }
}

function ingestClaimgatePy(receiptPath, findings) {
  const py = path.join(ROOT, "claimgate", "claimgate.py");
  if (!fs.existsSync(py)) return;
  const r = run("python3", [py, receiptPath]);
  if (r.status === 0) return;
  const parsed = parseJsonSafe(r.stdout);
  if (parsed && Array.isArray(parsed.reasons)) {
    for (const rr of parsed.reasons) {
      findings.push({ source: "claimgate/claimgate.py (tier0 -- the linter claim_verify.py prefers)", code: rr.code, detail: rr.detail });
    }
  }
}

function ingestClaimVerify(receiptPath, findings, live) {
  const cv = path.join(PLUGIN_DIR, "claim_verify.py");
  if (!fs.existsSync(cv)) return null;
  const r = run("python3", [cv, receiptPath]);
  const parsed = parseJsonSafe(r.stdout);
  if (!parsed) return null;

  const claimKind = parsed.claim_kind;
  const known = claimKind != null && Object.prototype.hasOwnProperty.call(live.claimKinds, claimKind);
  // only surface depth-resolution findings when INSUFFICIENT_DEPTH is genuinely
  // the reason (verdict==INSUFFICIENT_DEPTH) -- when a tier FAILED outright the
  // verdict is REJECTED and req_unmet is a side effect of that failure, not the
  // real story; the FAIL findings above/below already cover it.
  if (parsed.verdict === "INSUFFICIENT_DEPTH") {
    if (!known) {
      findings.push({ source: "claim_verify.py (tier dispatcher)", code: "unclassified_claim_kind", detail: `claim_kind=${JSON.stringify(claimKind)} names no entry in gate_registry.json claim_kinds -- required depth cannot be resolved, verdict is capped at INSUFFICIENT_DEPTH` });
    } else if (Array.isArray(parsed.required_unmet) && parsed.required_unmet.length) {
      findings.push({ source: "claim_verify.py (tier dispatcher)", code: "required_tier_unmet", detail: `claim_kind=${claimKind} requires tiers ${JSON.stringify(parsed.required_tiers)}; unmet: ${JSON.stringify(parsed.required_unmet)}`, claimKind, requiredUnmet: parsed.required_unmet });
    }
  }

  for (const t of parsed.tier_results || []) {
    if (t.tier !== "tier4") continue;
    const d = String(t.detail || "");
    if (t.status === "SKIP" && d.includes("no sibling audit")) {
      findings.push({ source: "claim_verify.py tier4", code: "tier4_no_audit", detail: d });
    } else if (t.status === "FAIL" && d.includes("no exact 'verdict:")) {
      findings.push({ source: "claim_verify.py tier4", code: "tier4_prose_verdict", detail: d, auditPath: t.evidence_ref });
    } else if (t.status === "FAIL" && d.includes("self-audit forbidden")) {
      findings.push({ source: "claim_verify.py tier4", code: "tier4_self_audit", detail: d, auditPath: t.evidence_ref });
    } else if (t.status === "FAIL" && d.includes("names no 'auditor:'")) {
      findings.push({ source: "claim_verify.py tier4", code: "tier4_no_auditor_identity", detail: d, auditPath: t.evidence_ref });
    } else if (t.status === "FAIL" && d.includes("not freshly calibrated")) {
      findings.push({ source: "claim_verify.py tier4", code: "tier4_not_calibrated", detail: d, auditPath: t.evidence_ref });
    } else if (t.status === "FAIL" && d.startsWith("audit verdict")) {
      findings.push({ source: "claim_verify.py tier4", code: "tier4_tainted_fatal", detail: d, auditPath: t.evidence_ref });
    }
  }
  return parsed;
}

function ingestFloor(receiptPath, storeArg, findings) {
  const rf = path.join(PLUGIN_DIR, "ratchet_floor.py");
  if (!fs.existsSync(rf)) return;
  // NEVER touch the real store: copy it to a scratch file and point --store
  // there, so a receipt that would genuinely ADMIT does not silently advance
  // the real floor as a side effect of asking for advice.
  const tmp = path.join(os.tmpdir(), `suggest_floor_${process.pid}_${Date.now()}.json`);
  try {
    if (fs.existsSync(storeArg)) fs.copyFileSync(storeArg, tmp);
    const r = run("python3", [rf, "admit", receiptPath, "--store", tmp]);
    const parsed = parseJsonSafe(r.stdout);
    if (!parsed) return;
    for (const p of parsed.parked || []) {
      findings.push({ source: "ratchet_floor.py (floor stage)", code: "floor_park_unknown_key", detail: p.reason, key: p.key, nearestExistingKey: p.nearest_existing_key, similarity: p.similarity, storeArg });
    }
    for (const v of parsed.violations || []) {
      const code = /REGRESSION/.test(v.reason) ? "floor_regression" : /direction tamper/.test(v.reason) ? "floor_direction_tamper" : "floor_malformed_claim";
      findings.push({ source: "ratchet_floor.py (floor stage)", code, detail: v.reason, key: v.key, floor: v.floor, claimed: v.claimed });
    }
  } finally {
    try { fs.unlinkSync(tmp); } catch {}
  }
}

function ingestBcScan(receiptPath, findings) {
  const bc = path.join(PLUGIN_DIR, "bc_scan.py");
  if (!fs.existsSync(bc)) return;
  const r = run("python3", [bc, receiptPath]);
  const parsed = parseJsonSafe(r.stdout);
  const row = parsed && Array.isArray(parsed.per_receipt) ? parsed.per_receipt[0] : null;
  if (!row || !row.flagged) return;
  for (const [cls, names] of Object.entries(row.flagged)) {
    findings.push({ source: "bc_scan.py (by-construction triage)", code: `bc_scan_${cls}`, detail: `${names.length} check(s) name-flagged as suspect ${cls}: ${names.join(", ")}`, checkClass: cls, names });
  }
}

function ingestSmtRoleHeuristic(receipt, findings) {
  const tid = receipt.TOOL_INTEGRATION_DEPTH;
  if (!tid || typeof tid !== "object") return;
  const loadBearingSmt = Object.entries(tid).filter(([tool, depth]) => /^(z3|cvc5)$/i.test(tool) && depth === "load_bearing");
  if (!loadBearingSmt.length) return;
  const hasSmtRole = jsonHasKey(receipt, "smt_role");
  const hasLoadBearingEvidence = jsonHasKey(receipt, "load_bearing_evidence");
  if (hasSmtRole && hasLoadBearingEvidence) return; // already carries the honest-packaging fields
  for (const [tool] of loadBearingSmt) {
    findings.push({
      source: "suggest.mjs static heuristic (systemic finding, git b12c0e8c7 / 4fcd539d6)",
      code: "smt_maybe_decorative",
      detail: `TOOL_INTEGRATION_DEPTH.${tool}="load_bearing" but the receipt has no 'smt_role' / 'load_bearing_evidence' field -- the audited systemic pattern is a generic single-valued-function tautology (recover(k)==A AND ==B -> UNSAT for ANY A!=B) mislabeled load_bearing when it never encodes the real mechanism.`,
      tool,
    });
  }
}

function jsonHasKey(node, key) {
  if (node && typeof node === "object") {
    if (!Array.isArray(node) && Object.prototype.hasOwnProperty.call(node, key)) return true;
    for (const v of Array.isArray(node) ? node : Object.values(node)) {
      if (jsonHasKey(v, key)) return true;
    }
  }
  return false;
}

function ingestExternalReason(reasonPath, findings) {
  const parsed = parseJsonSafe(readTextSafe(reasonPath));
  if (!parsed) return;
  const arrays = [
    ["reasons", "code"],
    ["violations", "rule"],
    ["problems", "gate"],
    ["near_duplicates", "gate"],
  ];
  for (const [field, codeKey] of arrays) {
    if (Array.isArray(parsed[field])) {
      for (const item of parsed[field]) {
        findings.push({ source: `--reason ${reasonPath}`, code: item[codeKey] || item.code || item.rule || "external_unknown", detail: item.detail || JSON.stringify(item), trail: item.trail });
      }
    }
  }
}

// ---------------------------------------------------------------- checkNames
// exactly what claimgate.mjs R4 already computes internally and never emits
// (Tier C1 in the ledger) -- recomputed here from the receipt so the fix is
// a paste-ready block, not just "add preregistration".

function getCheckNames(receipt) {
  const checks = receipt.checks;
  if (!checks || typeof checks !== "object") return null;
  return Array.isArray(checks) ? checks.map(String) : Object.keys(checks);
}

// ---------------------------------------------------------------- fix map

function buildFix(f, receipt, live) {
  const A = (arr, n = 12) => (arr && arr.length ? arr.slice(0, n).join(", ") + (arr.length > n ? ", ..." : "") : "(none found)");

  switch (f.code) {
    // ---- claimgate/claimgate.py (tier0, claim_verify-preferred) ----
    case "classification_missing":
      return {
        fix: `Add: "classification": "tool_lego_fit_probe", "promotion_allowed": false  (or another value from allowed_classifications below, matched to what was actually earned)`,
        allowed_classifications: live.allowedClassifications,
      };
    case "classification_not_allowed": {
      const got = (f.detail.match(/classification=(\S+)/) || [])[1] || "";
      const nearest = live.allowedClassifications
        .map((c) => [c, jaccardTokens(got, c)])
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([c]) => c);
      return {
        fix: `Replace the classification with one of allowed_classifications below. Closest by name: ${nearest.join(", ") || "(no close match)"}.`,
        allowed_classifications: live.allowedClassifications,
      };
    }
    case "promotion_without_canonical_evidence":
      return {
        fix: `Either set "promotion_allowed": false (honest downgrade, no canonical evidence exists yet), or -- only if it is genuinely earned -- set "accepted_status_label": "canonical by process" and cite the passing SIM_TEMPLATE + tool manifest + reasons + classification that justify it. Do not set the label to unblock promotion; that is exactly the inflation this rule catches.`,
      };
    case "verdict_inflation":
      // claimgate.py's check_verdict_inflation fires on ANY INTEGRATED/GREEN
      // string beside a false pass and does NOT accept a divergence note as an
      // escape (verified by round-trip). Only the .mjs R1 check accepts that,
      // handled under "R1-verdict-inflation". Do NOT offer the divergence-field
      // option here or the suggestion would be wrong for the gate that raised it.
      return {
        fix: `At the flagged object: either flip 'pass' to true if the check genuinely passed, or change the verdict string away from INTEGRATED/GREEN to one that means fail (e.g. FAILED_AS_EXPECTED, BLOCKED). NOTE: the strict tier0 (claimgate.py) does not accept a divergence/caveat note as an escape here -- the string+false-pass pairing itself is the finding.`,
      };
    case "controls_missing":
      return {
        fix: `Add a top-level "controls": { "<control_name>": {...independently computed...} } block. It must be a genuine alternative run (different input/channel), not a restatement of the main numbers -- see controls_copy_of_main_run below for what NOT to do.`,
      };
    case "controls_copy_of_main_run":
      return {
        fix: `This is the frozen-control defect. Recompute the control from a genuinely different input so its numeric leaves differ from the main run. Template: the feed-both-and-differ pattern in ratchet_contract/ratchetings/vn_to_shannon.py (dephasing vs unitary control, 'control_discriminates = bool(dephasing_is_one_way and not control_is_one_way)') and ratchet_contract/ratchetings/finite_to_continuum_rung.py (lossy vs lossless). Both replaced a "any unitary invertible -> control never flips" dead-code control with one that genuinely differs by mechanism.`,
        template_path: "ratchet_contract/ratchetings/vn_to_shannon.py",
        template_path_2: "ratchet_contract/ratchetings/finite_to_continuum_rung.py",
      };
    case "negative_mutual_information":
      return {
        fix: `This is a correctness bug in the computation, not a documentation gap -- mutual information cannot be negative. Check the entropy sign convention and any clipping/regularization near 0 in the code that produced this number; do not just rename or hide the field.`,
      };
    case "preregistration_missing": {
      const names = getCheckNames(receipt);
      return {
        fix: names
          ? `Add: "preregistered": ${JSON.stringify(names)}  (the exact check names already present in this receipt's 'checks' block)`
          : `Add a "preregistered" block listing every check name evaluated in this receipt's 'checks' section, written BEFORE the run.`,
      };
    }

    // ---- claimgate.mjs (tier0, hook-invoked) ----
    case "R1-unknown-verdict":
      return {
        fix: `Use a verdict already in the agreed vocabulary, or add it to rules_ratchet.json's verdict_pass_map (owned by the dual-tier0 session, not this tool). Vocabulary: ${A(Object.keys(live.verdictPassMap))}`,
      };
    case "R1-verdict-inflation":
      return {
        fix: `Add one of divergence_explanation_fields (>30 chars) to the SAME object explaining the mismatch, or make the pass field agree with the verdict. Fields: ${A(live.rules.divergence_explanation_fields)}`,
      };
    case "R2-claim-without-evidence":
      return {
        fix: `Add a non-empty sibling field next to '${f.trail || "the claim"}' whose NAME CONTAINS one of provenance_fields: ${A(live.rules.provenance_fields)}`,
      };
    case "R3-baseline-honesty":
      return {
        fix: `Add a sibling field whose name CONTAINS one of baseline_fields: ${A(live.rules.baseline_fields)}`,
      };
    case "R4-no-preregistration": {
      const names = getCheckNames(receipt);
      return {
        fix: names
          ? `Add: "preregistered": ${JSON.stringify(names)}`
          : `Add a "preregistered" array/object listing the check names before 'checks' is evaluated.`,
      };
    }
    case "R4-posthoc-gate": {
      const checkName = (f.trail || "").split(".").pop();
      return { fix: `Add '${checkName}' to the "preregistered" block (it was evaluated in 'checks' but never declared in advance).` };
    }
    case "R5-recompute-missing-raw":
      return { fix: `Add the raw array at the path this recompute contract names (${f.trail || "see detail"}) so the claim is re-derivable, not just asserted.` };
    case "R5-recompute-bad-op":
      return { fix: `Use one of recompute_ops: ${A(live.rules.recompute_ops)}` };
    case "R5-recompute-mismatch":
      return { fix: `Recompute mismatch is a real discrepancy between the claimed number and its own declared raw data -- fix the claimed value or the raw array so they agree (see detail for both numbers), do not widen the tolerance.` };
    case "R5-tolerance-gaming":
      return { fix: `Lower 'tol' to at most 5% of |claim| (or 1e-6, whichever is larger) -- see detail for the computed ceiling.` };

    // ---- claim_verify.py tier dispatcher ----
    case "unclassified_claim_kind":
      return {
        fix: `Add: "claim_kind": "<one of the values below>". Available claim_kinds (from gate_registry.json): ${A(Object.keys(live.claimKinds))}`,
        available_claim_kinds: Object.keys(live.claimKinds),
      };
    case "required_tier_unmet": {
      const kind = live.claimKinds[f.claimKind] || {};
      const gateNames = (f.requiredUnmet || []).map((t) => kind[`${t}_gate`]).filter(Boolean);
      const cmds = gateNames.map((g) => (live.gates[g] || {}).cmd).filter(Boolean);
      return {
        fix: gateNames.length
          ? `Run the registered gate(s) that satisfy the unmet tier(s): ${gateNames.join(", ")}. Command(s): ${cmds.map((c) => c.join(" ")).join("  |  ")}. If this receipt is honestly a probe not meant to reach that depth, that is the correct ceiling -- keep exit 3 (INSUFFICIENT_DEPTH), do not fabricate a passing tier.`
          : `The unmet tier(s) (${A(f.requiredUnmet)}) have no gate registered for claim_kind=${f.claimKind} in gate_registry.json -- this is a registry gap, route to the dual-tier0/registry owner, not fixable from the receipt alone.`,
      };
    }
    case "tier4_no_audit":
      return {
        fix: `Informational, not a failure (SKIP, not FAIL) -- claim_verify does not require tier4 unless the claim_kind's required_tiers include it. To lift it anyway, add a sibling AUDIT_VERDICT.md next to this receipt with: a line 'verdict: CLEAN' (or TAINTED/FATAL), a line 'auditor: <name>', where <name> is one of the registered auditors: ${A(Object.keys(live.calibrationGates))}, and where <name> differs from this receipt's produced_by/builder/author.`,
      };
    case "tier4_prose_verdict":
      return {
        fix: `In ${f.auditPath || "the sibling AUDIT_VERDICT.md"}, add the exact machine-readable line 'verdict: CLEAN' (grammar: CLEAN|TAINTED|FATAL only -- a prose headline like "Audit: CLEAN" as a heading is not matched, it must be its own line starting with 'verdict:').`,
      };
    case "tier4_no_auditor_identity":
      return { fix: `In ${f.auditPath || "the sibling AUDIT_VERDICT.md"}, add a line 'auditor: <name>' distinct from this receipt's produced_by/builder/author.` };
    case "tier4_self_audit":
      return { fix: `The auditor named in ${f.auditPath || "AUDIT_VERDICT.md"} matches this receipt's producer -- route the audit to a different, independent auditor identity.` };
    case "tier4_not_calibrated":
      return {
        fix: `The named auditor has no fresh evalcheck calibration. Registered auditors with a calibration gate: ${A(Object.keys(live.calibrationGates))}. Either use one of those identities and let evalcheck re-run against its sealed deck, or register a new calibration_gates entry in gate_registry.json (owned by the audit-token/dual-tier0 sessions, not this tool).`,
      };
    case "tier4_tainted_fatal":
      return { fix: `The audit itself found a real defect (${f.detail}) -- fix the underlying issue it names in ${f.auditPath || "AUDIT_VERDICT.md"}; no suggestion layer can paper over a TAINTED/FATAL verdict.` };

    // ---- ratchet_floor.py ----
    case "floor_park_unknown_key": {
      // FINDING C guard: do NOT casually advise --allow-new-keys when the key is
      // similar to an existing floor key -- that is the rename-evasion path (a
      // regressed metric renamed to dodge the locked floor). High similarity =>
      // steer to the locked key; only permit --allow-new-keys with an explicit
      // different-metric justification.
      const sim = typeof f.similarity === "number" ? f.similarity : 0;
      if (f.nearestExistingKey && sim >= 0.5) {
        return {
          fix: `LIKELY RENAME of the locked floor key '${f.nearestExistingKey}' (similarity ${f.similarity}). If it is the same metric, use that exact locked key so the floor actually compares -- do NOT pass --allow-new-keys, which would register a fresh (possibly regressed) floor and defeat the ratchet. Only if this is a GENUINELY different metric, register it under a clearly distinct name with --allow-new-keys AND state why it is not '${f.nearestExistingKey}'.`,
          warning: `--allow-new-keys on a key this similar is the rename-evasion path; not advised here.`,
        };
      }
      return {
        fix: f.nearestExistingKey
          ? `Closest existing floor key is '${f.nearestExistingKey}' (similarity ${f.similarity}, low). If it is the same metric, rename to it; otherwise register the new metric: python3 claimgate_plugin/ratchet_floor.py admit <receipt> --store ${f.storeArg} --allow-new-keys`
          : `Run: python3 claimgate_plugin/ratchet_floor.py admit <receipt> --store ${f.storeArg} --allow-new-keys  (no similar existing key found -- this looks like a genuinely new floor metric).`,
      };
    }
    case "floor_regression":
      return {
        fix: `Design gap, not a self-serve fix (Tier D in the ledger): '${f.key}' claims ${f.claimed} which weakens the recorded floor ${f.floor}. There is no admissible reset path in ratchet_floor.py today -- either recompute a genuinely better value, or route to the owner for a logged --allow-regression <reason> / human-only floor reset (not yet implemented; do not hand-edit the floor store).`,
      };
    case "floor_direction_tamper":
      return {
        fix: `'${f.key}' changed its locked higher_is_better/lower_is_better direction -- this is treated as tamper by design. If the direction genuinely needs to change, that is an owner decision (route it), not a receipt-level fix.`,
      };
    case "floor_malformed_claim":
      return { fix: `Fix the floor_claims entry so it has {key: string, value: finite number, direction: "higher_is_better"|"lower_is_better"}.` };

    // ---- bc_scan.py / decorative-SMT / frozen-control triage ----
    case "bc_scan_symmetry_forced":
    case "bc_scan_decorative_finite":
      return {
        fix: `These checks are name-flagged as a possible frozen/symmetry-forced control (the same class the systemic finding closed on vn_to_shannon and finite_to_continuum). Confirm with canfail_probe.py: if a mutation TARGETS one of ${A(f.names)} and it never flips, rewrite it as feed-both-and-differ (a genuinely different mechanism must produce a different answer) using the pattern in the templates below.`,
        template_path: "ratchet_contract/ratchetings/vn_to_shannon.py",
        template_path_2: "ratchet_contract/ratchetings/finite_to_continuum_rung.py",
      };
    case "bc_scan_entropy_theorem":
    case "bc_scan_algebraic_identity":
    case "bc_scan_counting_tautology":
      return {
        fix: `These checks are name-flagged as possibly by-construction (a theorem/identity/count that cannot fail). This is a SUSPECT, not a proof (bc_scan's own honest ceiling) -- confirm with canfail_probe.py by targeting ${A(f.names)} with a mutation that severs the claimed mechanism. If it is confirmed by-construction, the honest fix is NOT to force a failure: relabel the receipt (classification="tool_lego_fit_probe", promotion_allowed=false) so it is never presented as evidence beyond what it is.`,
      };

    // ---- SMT role heuristic ----
    case "smt_maybe_decorative":
      return {
        fix: `Check whether ${f.tool}'s constraint is tied to the actual object (a mechanism-specific encoding) or is the generic single-valued-function tautology (recover(k)==A AND ==B -> UNSAT for ANY A!=B, decoupled from the mechanism). If generic: downgrade "TOOL_INTEGRATION_DEPTH.${f.tool}" to "supportive" and add "smt_role": "supportive_nonvacuity_only" plus a "load_bearing_evidence" field naming the real witness (the numpy/sympy/direct recompute that actually carries the arrow). If genuinely mechanism-tied: follow the template below, which pins the real object as z3 Function constraints (not a placeholder) and proves it by perturbation-flip (change the object, UNSAT should flip to SAT) plus an unsat-core check.`,
        template_path: "ratchet_contract/ratchetings/magma_smt_genuine.py",
      };

    default:
      return {
        fix: `No template on file for code '${f.code}' yet. Raw detail: ${f.detail || "(none)"}. If this recurs, add a case to claimgate_plugin/suggest.mjs's buildFix() and a row to claimgate_plugin/FIX_PATTERNS.md.`,
      };
  }
}

function jaccardTokens(a, b) {
  const toks = (s) => new Set(String(s).toLowerCase().split(/[^a-z0-9]+/).filter(Boolean));
  const A = toks(a), B = toks(b);
  if (!A.size || !B.size) return 0;
  let inter = 0;
  for (const t of A) if (B.has(t)) inter++;
  return inter / (A.size + B.size - inter);
}

// ---------------------------------------------------------------- main

function main() {
  const args = process.argv.slice(2);
  const jsonOnly = args.includes("--json");
  const flag = (name, dflt) => {
    const i = args.indexOf(`--${name}`);
    return i >= 0 ? args[i + 1] : dflt;
  };
  const positional = args.filter((a, i) => !a.startsWith("--") && args[i - 1] !== "--reason" && args[i - 1] !== "--store");
  const receiptArg = positional[0];
  if (!receiptArg) die("usage: node suggest.mjs <receipt.json> [--reason <gate_output.json>] [--store <ratchet_floor_store.json>] [--json]");
  if (!fs.existsSync(receiptArg)) die(`receipt not found: ${receiptArg}`);
  // subprocesses run with cwd=ROOT (mirrors claim_verify.py) -- resolve to
  // absolute so a relative path typed from claimgate_plugin/ still works.
  const receiptPath = path.resolve(receiptArg);

  let receipt;
  try {
    receipt = JSON.parse(fs.readFileSync(receiptPath, "utf8"));
  } catch (e) {
    die(`cannot parse receipt JSON: ${e.message}`);
  }

  const live = loadLiveData();
  const findings = [];

  const reasonArg = flag("reason", null);
  if (reasonArg) ingestExternalReason(path.resolve(reasonArg), findings);

  ingestClaimgateMjs(receiptPath, findings);
  ingestClaimgatePy(receiptPath, findings);
  ingestClaimVerify(receiptPath, findings, live);

  if (Array.isArray(receipt.floor_claims) && receipt.floor_claims.length) {
    const storeArg = path.resolve(flag("store", path.join(PLUGIN_DIR, "ratchet_floor.json")));
    ingestFloor(receiptPath, storeArg, findings);
  }

  if (receipt.checks && typeof receipt.checks === "object") {
    ingestBcScan(receiptPath, findings);
  }
  ingestSmtRoleHeuristic(receipt, findings);

  const withFixes = findings.map((f) => ({ ...f, ...buildFix(f, receipt, live) }));

  const machine = { tool: "suggest.mjs", receipt: receiptArg, n_findings: withFixes.length, findings: withFixes };

  if (!jsonOnly) {
    if (!withFixes.length) {
      process.stdout.write(`suggest: no findings from any gate against ${receiptArg} -- nothing to fix (this is advisory-only; it does not itself admit the receipt).\n`);
    } else {
      process.stdout.write(`suggest: ${withFixes.length} finding(s) for ${receiptArg}\n\n`);
      withFixes.forEach((f, i) => {
        process.stdout.write(`[${i + 1}] ${f.code}\n`);
        process.stdout.write(`    source: ${f.source}\n`);
        if (f.trail) process.stdout.write(`    at:     ${f.trail}\n`);
        process.stdout.write(`    detail: ${f.detail}\n`);
        process.stdout.write(`    fix:    ${f.fix}\n`);
        if (f.template_path) process.stdout.write(`    template: ${f.template_path}\n`);
        if (f.template_path_2) process.stdout.write(`    template: ${f.template_path_2}\n`);
        process.stdout.write("\n");
      });
    }
    process.stdout.write("=== SUGGEST (json) ===\n");
  }
  process.stdout.write(JSON.stringify(machine, null, 1) + "\n");
  process.exit(0);
}

main();

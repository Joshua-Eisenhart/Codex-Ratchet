#!/usr/bin/env node
/**
 * ClaimGate v0.1 — done-ness is computed, never asserted.
 *
 * Two commands, exit codes are the interface (gates are code, not prose):
 *
 *   claimgate lint-receipt <receipt.json> [--rules <rules.json>]
 *       Validates an agent "done" claim receipt mechanically.
 *       exit 0 = claim admissible, 1 = violations, 2 = malformed/error
 *
 *   claimgate admit-module <declaration.json> --estate <dir> [--registry <admissions.jsonl>]
 *       Admission gate for CREATING new modules (kills split-brain implementations).
 *       exit 0 = admit, 3 = park for human review (near-duplicate), 1 = reject, 2 = error
 *
 * Design sources (Codex-Ratchet campaign receipts, 2026-07-19/20):
 *   - verdict==pass enforcement        (caught: INTEGRATED with pass:false, heldout 0.0)
 *   - claims need raw-data provenance  (caught: 4 by-construction gates in unified v1)
 *   - preregistration                  (post-hoc gates are void)
 *   - baseline honesty                 (caught: "beats chance 0.5" hiding majority 0.867)
 *   - near-duplicate admission         (Lev ratchet-admission.flow.yaml gate 4, applied to code)
 *   - inventory-before-generation      (6 generate-instead-of-retrieve incidents, one campaign)
 *
 * No dependencies. Node >= 18.
 */

import fs from "node:fs";
import path from "node:path";

// ---------------------------------------------------------------- helpers

function die(msg, code = 2) {
  process.stderr.write(`claimgate: ${msg}\n`);
  process.exit(code);
}

function readJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, "utf8"));
  } catch (e) {
    die(`cannot read/parse JSON at ${p}: ${e.message}`);
  }
}

function* walkObjects(node, trail = "$") {
  if (node && typeof node === "object" && !Array.isArray(node)) {
    yield [trail, node];
    for (const [k, v] of Object.entries(node)) yield* walkObjects(v, `${trail}.${k}`);
  } else if (Array.isArray(node)) {
    for (let i = 0; i < node.length; i++) yield* walkObjects(node[i], `${trail}[${i}]`);
  }
}

function getPath(obj, dotted) {
  // supports $.a.b[2].c
  const parts = dotted.replace(/^\$\.?/, "").split(/\.|\[|\]/).filter(Boolean);
  let cur = obj;
  for (const p of parts) {
    if (cur == null) return undefined;
    cur = cur[/^\d+$/.test(p) ? Number(p) : p];
  }
  return cur;
}

const num = (x) => typeof x === "number" && Number.isFinite(x);

// ---------------------------------------------------------------- lint-receipt

const DEFAULT_RULES = {
  // verdict vocabularies and what pass-state each verdict REQUIRES.
  // null = pass must be absent/false-y (a blocked tool has no pass).
  verdict_fields: ["verdict", "status", "outcome"],
  pass_fields: ["pass", "all_pass", "passed", "ok"],
  verdict_pass_map: {
    INTEGRATED: true,
    PASS: true,
    CLEAN: true,
    GREEN: true,
    CONFIRMED: true,
    FAILED_AS_EXPECTED: false,
    BLOCKED: false,
    PRUNED: false,
    FAIL: false,
    RED: false,
    TAINTED: false,
    // verdicts that carry no pass obligation:
    INCONCLUSIVE: null,
    OPEN: null,
    SURVIVED_UNEXPECTEDLY: null,
    NUMEROLOGY_NOT_REJECTED_AS_SUCH: null,
  },
  // exceptions: paths where verdict/pass divergence is allowed IF an
  // explanation field is present (honest gate-miss pattern).
  divergence_explanation_fields: ["gate_miss_note", "divergence_note", "caveat"],
  // fields that constitute a CLAIM and therefore need provenance:
  claim_field_patterns: [
    "accuracy", "corr", "correlation", "efficiency", "fidelity",
    "mutual_information", "p_value", "pvalue", "margin",
  ],
  // provenance = any of these present in the same object or an ancestor object:
  provenance_fields: [
    "raw", "data", "arrays", "samples", "trace", "per_tick", "per_item",
    "bootstrap", "ci95", "draws", "source_path", "sha256", "result",
    "computed_number", "detail", "evidence",
  ],
  // if a comparison-to-chance claim exists, an honest baseline must accompany it.
  chance_fields: ["chance", "chance_accuracy", "computed_chance_accuracy"],
  baseline_fields: [
    "majority_baseline", "majority_class_baseline", "null_mean", "null_p95",
    "permutation_null_mean_bits", "shuffled", "twin", "baseline",
  ],
  // preregistration: if a `preregistered` block exists, every check key
  // evaluated in `checks` must appear in it.
  preregistration_block: "preregistered",
  checks_block: "checks",
  // recompute contract: receipt may declare its own re-derivations.
  // recompute: [{claim: "$.x.mean_acc", op: "mean", from: "$.x.raw_accs", tol: 1e-9}]
  recompute_ops: ["mean", "min", "max", "count", "sum", "fraction_true"],
};

function lintReceipt(receiptPath, rulesPath) {
  const receipt = readJson(receiptPath);
  const rules = rulesPath
    ? { ...DEFAULT_RULES, ...readJson(rulesPath) }
    : DEFAULT_RULES;
  const violations = [];
  const notes = [];

  // ---- R1: verdict == pass-state, everywhere, or an explanation is present
  for (const [trail, obj] of walkObjects(receipt)) {
    const vKey = rules.verdict_fields.find((f) => typeof obj[f] === "string");
    if (!vKey) continue;
    const verdict = obj[vKey].toUpperCase();
    if (!(verdict in rules.verdict_pass_map)) {
      notes.push({ rule: "R1-vocab", trail, note: `unknown verdict '${obj[vKey]}' — not in vocabulary, not checkable` });
      continue;
    }
    const required = rules.verdict_pass_map[verdict];
    if (required === null) continue;
    const pKey = rules.pass_fields.find((f) => f in obj);
    if (pKey === undefined) continue; // no pass field beside this verdict — R2 may still catch missing evidence
    const actual = obj[pKey];
    const agrees = required === true ? actual === true : actual !== true;
    if (!agrees) {
      const explained = rules.divergence_explanation_fields.some(
        (f) => typeof obj[f] === "string" && obj[f].length > 10
      ) || rules.divergence_explanation_fields.some(
        (f) => obj.detail && typeof obj.detail[f] === "string" && obj.detail[f].length > 10
      );
      if (explained) {
        notes.push({ rule: "R1-explained", trail, note: `verdict ${verdict} vs ${pKey}=${JSON.stringify(actual)} diverge WITH explanation — allowed, surfaced` });
      } else {
        violations.push({ rule: "R1-verdict-inflation", trail, detail: `verdict '${verdict}' requires ${pKey}=${required} but found ${JSON.stringify(actual)}, no explanation field` });
      }
    }
  }

  // ---- R2: claim fields need provenance in the same object
  for (const [trail, obj] of walkObjects(receipt)) {
    for (const key of Object.keys(obj)) {
      const isClaim =
        num(obj[key]) &&
        rules.claim_field_patterns.some((p) => key.toLowerCase().includes(p));
      if (!isClaim) continue;
      const hasProv = rules.provenance_fields.some((f) => f in obj && obj[f] != null);
      if (!hasProv) {
        violations.push({ rule: "R2-claim-without-evidence", trail: `${trail}.${key}`, detail: `numeric claim '${key}'=${obj[key]} has no provenance field beside it (need one of: ${rules.provenance_fields.slice(0, 6).join(", ")}, ...)` });
      }
    }
  }

  // ---- R3: chance-comparison needs an honest baseline somewhere in the same object
  for (const [trail, obj] of walkObjects(receipt)) {
    const hasChance = rules.chance_fields.some((f) => num(obj[f]));
    if (!hasChance) continue;
    const hasBaseline = rules.baseline_fields.some((f) => f in obj);
    if (!hasBaseline) {
      violations.push({ rule: "R3-baseline-honesty", trail, detail: `claims a chance comparison but carries no majority/null/twin baseline field — 'beats chance' can hide a majority-class artifact` });
    }
  }

  // ---- R4: preregistration coverage
  const prereg = receipt[rules.preregistration_block];
  const checks = receipt[rules.checks_block];
  if (checks && typeof checks === "object") {
    if (!prereg) {
      violations.push({ rule: "R4-no-preregistration", trail: `$.${rules.checks_block}`, detail: `receipt evaluates ${Object.keys(checks).length} checks but has no '${rules.preregistration_block}' block — gates must exist before the run` });
    } else {
      const declared = new Set(Array.isArray(prereg) ? prereg : Object.keys(prereg));
      for (const k of Object.keys(checks)) {
        if (!declared.has(k)) {
          violations.push({ rule: "R4-posthoc-gate", trail: `$.${rules.checks_block}.${k}`, detail: `check '${k}' evaluated but not preregistered` });
        }
      }
    }
  }

  // ---- R5: declared recomputations must reproduce
  const rec = receipt.recompute;
  if (Array.isArray(rec)) {
    for (const r of rec) {
      const claimed = getPath(receipt, r.claim);
      const from = getPath(receipt, r.from);
      const tol = num(r.tol) ? r.tol : 1e-9;
      if (!Array.isArray(from)) {
        violations.push({ rule: "R5-recompute-missing-raw", trail: r.from, detail: `raw array for recompute not found` });
        continue;
      }
      let got;
      switch (r.op) {
        case "mean": got = from.reduce((a, b) => a + b, 0) / from.length; break;
        case "sum": got = from.reduce((a, b) => a + b, 0); break;
        case "min": got = Math.min(...from); break;
        case "max": got = Math.max(...from); break;
        case "count": got = from.length; break;
        case "fraction_true": got = from.filter(Boolean).length / from.length; break;
        default:
          violations.push({ rule: "R5-recompute-bad-op", trail: r.claim, detail: `unknown op '${r.op}'` });
          continue;
      }
      if (!num(claimed) || Math.abs(got - claimed) > tol) {
        violations.push({ rule: "R5-recompute-mismatch", trail: r.claim, detail: `claimed ${claimed}, recomputed ${got} from ${r.from} (op=${r.op}, tol=${tol})` });
      } else {
        notes.push({ rule: "R5-ok", trail: r.claim, note: `recomputed ${r.op} matches (${got})` });
      }
    }
  } else {
    notes.push({ rule: "R5-absent", note: "receipt declares no recompute contract — numbers are asserted, not re-derivable by this linter" });
  }

  const verdict = violations.length === 0 ? "ADMISSIBLE" : "REJECTED";
  const report = { tool: "claimgate.lint-receipt", receipt: receiptPath, verdict, violations, notes };
  process.stdout.write(JSON.stringify(report, null, 1) + "\n");
  process.exit(violations.length === 0 ? 0 : 1);
}

// ---------------------------------------------------------------- admit-module

const CODE_EXT = new Set([".ts", ".js", ".mjs", ".cjs", ".py", ".jl", ".go", ".rs"]);
const STOP = new Set(["the", "a", "an", "of", "for", "and", "or", "to", "in", "on", "with", "impl", "index", "main", "src", "core", "lib", "utils", "helper", "helpers", "new", "get", "set"]);

function tokens(s) {
  return new Set(
    String(s)
      .replace(/([a-z0-9])([A-Z])/g, "$1 $2") // camelCase split
      .toLowerCase()
      .split(/[^a-z0-9]+/)
      .filter((t) => t.length > 2 && !STOP.has(t))
  );
}

function tokMatch(t, u) {
  // exact, singular/plural, or prefix relation >=4 chars (config~configuration, load~loads)
  if (t === u) return true;
  const [s, l] = t.length <= u.length ? [t, u] : [u, t];
  if (s.length >= 3 && (l === s + "s" || l === s + "es")) return true;
  return s.length >= 4 && l.startsWith(s);
}

function jaccard(a, b) {
  if (a.size === 0 || b.size === 0) return 0;
  let inter = 0;
  for (const t of a) if ([...b].some((u) => tokMatch(t, u))) inter++;
  return inter / (a.size + b.size - inter);
}

function harvestEstate(dir, maxFiles = 4000) {
  const out = [];
  const skip = new Set(["node_modules", ".git", "__pycache__", "dist", "build", ".venv", "results"]);
  const stack = [dir];
  while (stack.length && out.length < maxFiles) {
    const d = stack.pop();
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (e.isDirectory()) {
        if (!skip.has(e.name) && !e.name.startsWith(".")) stack.push(path.join(d, e.name));
      } else if (CODE_EXT.has(path.extname(e.name))) {
        const p = path.join(d, e.name);
        let head = "";
        try { head = fs.readFileSync(p, "utf8").slice(0, 2000); } catch {}
        // exported/def-ed identifiers, cheap and language-agnostic enough
        const ids = [...head.matchAll(/(?:export\s+(?:async\s+)?(?:function|const|class)\s+|def\s+|function\s+|struct\s+|class\s+)([A-Za-z_][A-Za-z0-9_]*)/g)].map((m) => m[1]);
        out.push({ path: p, nameTokens: tokens(e.name), headTokens: tokens(head.split("\n").slice(0, 15).join(" ")), ids: new Set(ids) });
      }
    }
  }
  return out;
}

function admitModule(declPath, estateDir, registryPath, threshold) {
  const decl = readJson(declPath);
  const problems = [];
  const parks = [];

  // ---- G1: declaration completeness (schema gate)
  for (const f of ["name", "purpose", "paths_to_create"]) {
    if (!decl[f] || (Array.isArray(decl[f]) && decl[f].length === 0)) {
      problems.push({ gate: "G1-schema", detail: `declaration missing '${f}'` });
    }
  }

  // ---- G2: inventory-before-generation — a real search receipt is mandatory
  const searched = decl.searched;
  if (!Array.isArray(searched) || searched.length === 0) {
    problems.push({ gate: "G2-inventory", detail: `no 'searched' receipt — agent must search the estate for existing implementations BEFORE proposing a new module (queries + hit counts)` });
  } else {
    for (const s of searched) {
      if (typeof s.query !== "string" || !("hits" in s)) {
        problems.push({ gate: "G2-inventory", detail: `search entry malformed (need {query, tool, hits}): ${JSON.stringify(s).slice(0, 80)}` });
      }
    }
  }

  // ---- G3: immutability — refuse creation over existing paths
  for (const p of decl.paths_to_create || []) {
    if (fs.existsSync(p)) {
      problems.push({ gate: "G3-immutability", detail: `path already exists: ${p} — a new version is a NEW admission at a new path, never an overwrite` });
    }
  }

  // ---- G4: near-duplicate against the estate (the split-brain killer)
  const estate = harvestEstate(estateDir);
  const declName = tokens(decl.name);
  const declPurpose = tokens(decl.purpose || "");
  const declIface = new Set((decl.interface || decl.exports || []).map(String));
  for (const mod of estate) {
    const nameSim = jaccard(declName, mod.nameTokens);
    const purposeSim = jaccard(declPurpose, mod.headTokens);
    let ifaceOverlap = 0;
    if (declIface.size && mod.ids.size) {
      for (const id of declIface) if (mod.ids.has(id)) ifaceOverlap++;
    }
    const overlapFrac = declIface.size ? ifaceOverlap / declIface.size : 0;
    const score = Math.max(nameSim, purposeSim * 0.9) + 0.5 * overlapFrac;
    if (score >= threshold) {
      parks.push({ gate: "G4-near-duplicate", existing: mod.path, name_similarity: +nameSim.toFixed(3), purpose_similarity: +purposeSim.toFixed(3), interface_overlap: ifaceOverlap, detail: `candidate duplicate — human must decide: extend the existing module or justify the split` });
    }
  }

  // ---- G5: term fence (optional registry of defined terms)
  if (decl.term_registry && fs.existsSync(decl.term_registry)) {
    const reg = new Set(readJson(decl.term_registry).terms || []);
    for (const t of decl.terms_used || []) {
      if (!reg.has(t)) problems.push({ gate: "G5-term-fence", detail: `undefined term '${t}' — define it in the registry before use` });
    }
  }

  const verdict = problems.length ? "REJECT" : parks.length ? "PARK_FOR_REVIEW" : "ADMIT";
  const record = {
    tool: "claimgate.admit-module",
    at: new Date().toISOString(),
    declaration: declPath,
    name: decl.name,
    verdict,
    problems,
    near_duplicates: parks,
  };
  if (registryPath) fs.appendFileSync(registryPath, JSON.stringify(record) + "\n"); // append-only log
  process.stdout.write(JSON.stringify(record, null, 1) + "\n");
  process.exit(verdict === "ADMIT" ? 0 : verdict === "PARK_FOR_REVIEW" ? 3 : 1);
}

// ---------------------------------------------------------------- cli

const [, , cmd, ...args] = process.argv;
const flag = (name, dflt) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : dflt;
};

if (cmd === "lint-receipt") {
  const target = args.find((a) => !a.startsWith("--"));
  if (!target) die("usage: claimgate lint-receipt <receipt.json> [--rules rules.json]");
  lintReceipt(target, flag("rules"));
} else if (cmd === "admit-module") {
  const target = args.find((a) => !a.startsWith("--"));
  const estate = flag("estate");
  if (!target || !estate) die("usage: claimgate admit-module <declaration.json> --estate <dir> [--registry admissions.jsonl] [--threshold 0.6]");
  admitModule(target, estate, flag("registry"), Number(flag("threshold", "0.6")));
} else {
  die(`unknown command '${cmd ?? ""}' — commands: lint-receipt, admit-module`, 2);
}

#!/usr/bin/env node --experimental-sqlite
// CR-SIDE ENVELOPE CHECK for the serialized transport canary — NON-FINAL.
//
// Scope (webui audit 2026-07-22): this validates the CR evidence ENVELOPE —
// chain of custody, re-derived digests, bound proof receipts, mock quarantine.
// A complete hash chain proves provenance and byte identity ONLY; it never
// proves the mathematics. Truth evaluation belongs to Lev core/eval, and
// settlement to the later policy layer. This check is one composable link:
//   CR stage execution -> CR envelope check (THIS) -> Lev effect persistence
//   -> non-final claim intake -> core/eval -> policy -> settlement.
// It must never become a self-certifying gate, and "admitted" here means
// "envelope sound, eligible for claim intake" — not canon.
//
// Zero-trust means RE-DERIVE, not read: every artifact is re-hashed from disk
// and compared to the ledger's recorded digest.
//
// Status axes are handled distinctly (never collapsed):
//   execution_status  COMPLETED | INFRA_ERROR — non-COMPLETED z3 parks;
//   proof_status      SAT -> REJECTED here as a PRESERVED counterexample
//                     receipt (completed negative science — it reached this
//                     check as evidence, exactly as required); UNKNOWN parks;
//                     UNSAT continues. SAT is never an infrastructure crash.
//
// Exit codes: 0 envelope-sound, 3 PARKED, 1 REJECTED.
// Usage: node --experimental-sqlite claim_admission.mjs <run_id> <state_db>
import { DatabaseSync } from "node:sqlite";
import { createHash } from "node:crypto";
import { readFileSync, existsSync } from "node:fs";

const STAGES = ["julia", "jax", "pysindy", "z3"];
const [runId, stateDb] = process.argv.slice(2);
if (!runId || !stateDb) {
  console.error("usage: claim_admission.mjs <run_id> <state_db>");
  process.exit(2);
}

const db = new DatabaseSync(stateDb, { readOnly: true });
const get = (key) => {
  const row = db.prepare("SELECT value FROM kv WHERE key = ?").get(key);
  return row ? JSON.parse(row.value) : null;
};
const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");

console.log(`[ClaimGate] auditing run: ${runId}`);
let prevDigest = null;

for (const stage of STAGES) {
  const receipt = get(`runs/${runId}/stages/${stage}`);

  if (!receipt) {
    console.log(`[ClaimGate] PARKED — no receipt for stage '${stage}'; pipeline incomplete.`);
    process.exit(3);
  }

  // Re-derive the artifact digest from disk — never trust the recorded value.
  if (!existsSync(receipt.artifact_path)) {
    console.log(`[ClaimGate] REJECTED — ${stage} artifact missing from disk: ${receipt.artifact_path}`);
    process.exit(1);
  }
  const onDisk = sha256(receipt.artifact_path);
  if (onDisk !== receipt.output_digest) {
    console.log(`[ClaimGate] REJECTED — tamper evident at '${stage}': ledger says ` +
      `${receipt.output_digest.slice(0, 8)}, disk re-derives ${onDisk.slice(0, 8)}.`);
    process.exit(1);
  }

  // Chain link: this stage's input must be the prior stage's output.
  if (prevDigest !== null && receipt.input_digest !== prevDigest) {
    console.log(`[ClaimGate] REJECTED — chain broken at '${stage}': input_digest ` +
      `${String(receipt.input_digest).slice(0, 8)} != prior output ${prevDigest.slice(0, 8)}.`);
    process.exit(1);
  }
  prevDigest = receipt.output_digest;
  console.log(`[ClaimGate]   ${stage}: digest ${onDisk.slice(0, 8)} re-derived OK, link OK`);
}

// Proof axis (z3 stage): SAT / UNSAT / UNKNOWN are three different facts.
const z3 = get(`runs/${runId}/stages/z3`);
if (z3.execution_status && z3.execution_status !== "COMPLETED") {
  console.log(`[ClaimGate] PARKED — z3 execution_status '${z3.execution_status}' (infra, not science).`);
  process.exit(3);
}
if (z3.proof_status === "SAT") {
  console.log("[ClaimGate] REJECTED — proof is SAT: a counterexample EXISTS and its receipt is " +
    "preserved as completed negative science. Admission refused; evidence retained for evaluation.");
  process.exit(1);
}
if (z3.proof_status === "UNKNOWN") {
  console.log("[ClaimGate] PARKED — solver returned UNKNOWN (neither proof nor counterexample).");
  process.exit(3);
}
if (z3.proof_status !== "UNSAT") {
  console.log(`[ClaimGate] PARKED — proof status '${z3.proof_status}' (not UNSAT); review.`);
  process.exit(3);
}

// Gate M1: a REAL julia stage must carry its bound bipartiteness proof —
// sat on the torus AND the unsat polarity flip (referee finding: a proof
// living only in stdout pins nothing; it must sit in the ledger).
const julia = get(`runs/${runId}/stages/julia`);
if (julia.payload === "real") {
  if (julia.m1_status !== "sat" || julia.m1_polarity !== "unsat" || !julia.m1_receipt_digest) {
    console.log(`[ClaimGate] REJECTED — real julia stage lacks a bound Gate M1 proof pair ` +
      `(m1_status=${julia.m1_status}, m1_polarity=${julia.m1_polarity}).`);
    process.exit(1);
  }
  console.log(`[ClaimGate]   Gate M1 bound: sat/unsat pair, receipt ${julia.m1_receipt_digest.slice(0, 8)}`);
}

// MOCK QUARANTINE (referee finding: an unlabeled mock chain reached ADMITTED).
// Mock stages prove the spine, never the physics — any mock parks the run.
const mock = STAGES.filter((s) => get(`runs/${runId}/stages/${s}`).payload !== "real");
if (mock.length > 0) {
  console.log(`[ClaimGate] PARKED — mock stages present [${mock.join(", ")}]; ` +
    `spine verified, nothing admitted to canon until every stage is real.`);
  process.exit(3);
}

console.log("[ClaimGate] ENVELOPE SOUND — chain unbroken, digests re-derived, proofs bound, all stages real. " +
  "Non-final: eligible for Lev claim intake -> core/eval -> settlement. Not canon.");
process.exit(0);

#!/usr/bin/env node --experimental-sqlite
// ClaimGate admission auditor — the zero-trust inspector for the serialized
// physics spine. Runnable TODAY under node v22 (node:sqlite built in).
// The same logic, expressed as a native Lev FlowMind capability, is the
// proposed patch in claimgate_plugin/lev_patch/claim-admission.ts.
//
// Zero-trust means RE-DERIVE, not read: every artifact is re-hashed from disk
// and compared to the ledger's recorded digest. A ledger that says "fine"
// about a tampered file is itself the tamper evidence.
//
// Verdicts (exit codes match ClaimGate convention):
//   0 = ADMITTED  — full chain julia->jax->pysindy->z3, every digest
//                   re-derives, every link matches, z3 proof_status UNSAT.
//   3 = PARKED    — incomplete pipeline (missing receipt) or proof unknown.
//   1 = REJECTED  — digest mismatch (tamper), broken link, or z3 SAT.
//
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

// Gate M5: the z3 receipt must carry an UNSAT proof.
const z3 = get(`runs/${runId}/stages/z3`);
if (z3.proof_status === "SAT") {
  console.log("[ClaimGate] REJECTED — Gate M5 proof is SAT: finitude violated, counterexample exists.");
  process.exit(1);
}
if (z3.proof_status !== "UNSAT") {
  console.log(`[ClaimGate] PARKED — Gate M5 proof status '${z3.proof_status}' (not UNSAT); Oracle review.`);
  process.exit(3);
}

console.log("[ClaimGate] ADMITTED — chain unbroken, every digest re-derived, Gate M5 UNSAT.");
process.exit(0);

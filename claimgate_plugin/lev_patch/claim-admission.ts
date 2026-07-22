// WITHDRAWN 2026-07-22 (webui audit) — do not implement as written.
//
// This proposed a FINALIZING physics.claim-admission capability: one function
// that interprets the proof, decides truth, and writes canon. The audit
// rejects that collapse: Lev claim admission is deliberately NON-FINAL; truth
// evaluation belongs to core/eval (which EXISTS in lev-main, with CR eval
// tests already present); settlement is a separate later policy layer. The
// invented registerCapability / @lev-os/flowmind-types surface also does not
// exist — the real native seam is `lev.call` (currently a design-doc span
// name, not yet wired).
//
// What replaces this: claimgate_plugin/claim_admission.mjs relabeled as the
// CR-side ENVELOPE check (non-final, one composable link), feeding Lev's real
// chain: effect persistence -> non-final claim intake -> core/eval -> policy
// -> settlement. Kept on disk as an honest negative, per repo doctrine.

import { createHash } from "node:crypto";
import { readFileSync, existsSync } from "node:fs";
// Proposed imports — these packages are the patch's dependency ask:
// import { AgentFS } from "@lev-os/agentfs-sdk";
// import { Capability, CapabilityContext, BranchResult } from "@lev-os/flowmind-types";
type BranchResult = { branch: "admitted" | "parked" | "rejected"; output: Record<string, unknown> };
type CapabilityContext = { logger: { info(m: string): void; warn(m: string): void; error(m: string): void } };

interface ClaimInputs { run_id: string; state_db: string; }

const STAGES = ["julia", "jax", "pysindy", "z3"] as const;

const sha256 = (path: string) =>
  createHash("sha256").update(readFileSync(path)).digest("hex");

export const claimAdmissionCapability = {
  name: "physics.claim-admission",
  description:
    "Cryptographic chain-of-custody audit (re-derived digests) + Gate M5 UNSAT verification.",

  async execute(inputs: ClaimInputs, context: CapabilityContext, agentFs: any): Promise<BranchResult> {
    const { run_id } = inputs;
    context.logger.info(`[ClaimGate] auditing run: ${run_id}`);

    let prevDigest: string | null = null;
    for (const stage of STAGES) {
      const receipt = await agentFs.kv.get(`runs/${run_id}/stages/${stage}`);
      if (!receipt) {
        context.logger.warn(`[ClaimGate] missing receipt for '${stage}' — parking.`);
        return { branch: "parked", output: { reason: `missing_${stage}` } };
      }
      // RE-DERIVE: recompute the artifact digest from disk.
      if (!existsSync(receipt.artifact_path)) {
        return { branch: "rejected", output: { reason: "artifact_missing", stage } };
      }
      const onDisk = sha256(receipt.artifact_path);
      if (onDisk !== receipt.output_digest) {
        context.logger.error(`[ClaimGate] tamper evident at '${stage}'.`);
        return { branch: "rejected", output: { reason: "digest_mismatch", stage } };
      }
      if (prevDigest !== null && receipt.input_digest !== prevDigest) {
        context.logger.error(`[ClaimGate] chain broken at '${stage}'.`);
        return { branch: "rejected", output: { reason: "chain_broken", stage } };
      }
      prevDigest = receipt.output_digest;
    }

    const z3 = await agentFs.kv.get(`runs/${run_id}/stages/z3`);
    if (z3.proof_status === "SAT") {
      return { branch: "rejected", output: { reason: "proof_failed" } };
    }
    if (z3.proof_status !== "UNSAT") {
      return { branch: "parked", output: { reason: "proof_unknown" } };
    }

    // Gate M1: a real julia stage must carry its bound proof pair (sat + unsat polarity).
    const julia = await agentFs.kv.get(`runs/${run_id}/stages/julia`);
    if (julia.payload === "real" &&
        (julia.m1_status !== "sat" || julia.m1_polarity !== "unsat" || !julia.m1_receipt_digest)) {
      return { branch: "rejected", output: { reason: "gate_m1_unbound" } };
    }

    // Mock quarantine: mock stages prove the spine, never the physics.
    const mock: string[] = [];
    for (const stage of STAGES) {
      const r = await agentFs.kv.get(`runs/${run_id}/stages/${stage}`);
      if (r.payload !== "real") mock.push(stage);
    }
    if (mock.length > 0) {
      return { branch: "parked", output: { reason: "mock_stages", stages: mock } };
    }

    context.logger.info("[ClaimGate] admitted — chain unbroken, digests re-derived, M1 bound, M5 UNSAT, all real.");
    return { branch: "admitted", output: { status: "canonical", final_digest: prevDigest } };
  },
};

// PROPOSED LEV PATCH — physics.claim-admission native capability.
//
// STATUS (honest): the current Lev repo has NO registerCapability / Capability /
// @lev-os/flowmind-types plugin surface (verified by grep 2026-07-22), and
// @lev-os/agentfs-sdk is not an installed package. This file is the zip-pack
// PROPOSAL for the Lev dev: the admission auditor expressed as a native
// FlowMind op with the 3-way branch (admitted/parked/rejected) that
// lev.validate's binary pass/fail cannot express.
//
// The RUNNABLE equivalent (same logic, node:sqlite, exit 0/3/1) is
// claimgate_plugin/claim_admission.mjs — that is what the flow executes today.
//
// Zero-trust rule carried over from ClaimGate's three_engine_seal: RE-DERIVE,
// don't read. Every artifact digest is recomputed from disk; the ledger's
// recorded value is a claim to be checked, never evidence.

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

    context.logger.info("[ClaimGate] admitted — chain unbroken, digests re-derived, M5 UNSAT.");
    return { branch: "admitted", output: { status: "canonical", final_digest: prevDigest } };
  },
};

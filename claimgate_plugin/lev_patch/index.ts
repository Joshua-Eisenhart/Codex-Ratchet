// PROPOSED LEV PATCH — plugin registration for physics.claim-admission.
// See claim-admission.ts header: the registry API below is the ASK, not a
// currently-existing Lev surface. Ships in the ClaimGate zip-pack.
import { claimAdmissionCapability } from "./claim-admission";

export function registerPhysicsPlugin(registry: { registerCapability(c: unknown): void }) {
  registry.registerCapability(claimAdmissionCapability);
  console.log("[+] registered native op: physics.claim-admission");
}

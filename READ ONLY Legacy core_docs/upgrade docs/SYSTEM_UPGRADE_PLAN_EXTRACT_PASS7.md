# SYSTEM UPGRADE PLAN — EXTRACTION PASS 7

FOCUS: SIM PIPELINE, APPROVAL MECHANICS, DETERMINISTIC BOUNDARIES

This document is an extraction of material already present in the conversation.
No synthesis, redesign, or resolution is performed.
Contradictions and ambiguities are preserved.

---

## SIM ROLE (DETERMINISTIC)

- SIM is NOT a chat agent.
- SIM runs in a terminal or external executor.
- SIM executes only approved instructions.
- SIM never invents.
- SIM never interprets.
- SIM never proposes.

SIM exists to:
- execute deterministic workloads
- produce results
- emit evidence artifacts

---

## SIM APPROVAL FLOW (AS DISCUSSED)

Repeatedly stated structure:

1. A0 prepares SIM_PROPOSAL
2. SIM_PROPOSAL is sent to B
3. B validates proposal against canon
4. If accepted, approval token is generated
5. A0 packages SIM_RUN material
6. SIM TERMINAL executes
7. SIM produces results
8. Results go back to A0
9. A0 compiles SIM_EVIDENCE
10. SIM_EVIDENCE goes to B
11. B ratchets or rejects

Explicitly stated constraints:
- SIM must not run without B approval
- SIM must not invent new structures
- SIM output must be auditable

---

## HASH / BINDING REQUIREMENTS (PARTIAL, NOT FINAL)

The following bindings were repeatedly referenced but not fully formalized:

- baseline state hash
- proposal hash
- input hash
- output hash

Unresolved:
- exact hash formula
- where hashes are computed
- how invalidation propagates if B changes

STATUS:
UNSPECIFIED — DO NOT INFER

---

## DETERMINISM BOUNDARY

Strong repeated statements:

- A0 is deterministic
- B is deterministic
- SIM is deterministic
- Deterministic threads must not:
  - narrate
  - smooth
  - infer
  - help
  - reinterpret intent

Any of the above is considered drift.

---

## FAILURE MODES IDENTIFIED

Observed failure risks:

- SIM executed before approval
- SIM proposal modified after approval
- SIM results interpreted instead of passed through
- A0 or SIM acting “helpful”
- Approval token reused after B state changed

These are failure cases, not resolved designs.

---

## OPEN AMBIGUITIES

- Whether SIM artifacts are always ZIPs
- Whether SIM results are single or multi-artifact
- How many SIMs can run concurrently
- How SIM failures are classified vs graveyard

STATUS:
UNSPECIFIED — DO NOT INFER

---

## NOTES ON EXTRACTION PROCESS

- This pass extracted only SIM-related material.
- Other threads (A1, Rosetta, ZIP tooling) intentionally excluded.
- No attempt made to resolve contradictions.

END OF PASS 7

# [Controller-safe] Boot Lane Dispatch Surface

**Date:** 2026-03-27
**Purpose:** Wire up the existing boot packets as mandatory preload blocks for subagent dispatch.
The real boot content already exists (`BOOTPACK_THREAD_B_v3.9.13.md`, `BOOTPACK_THREAD_A_v2.60.md`).
The problem was not missing boots — it was boot-skipping at dispatch time.

> **Hard rule:** No subagent task is valid unless the relevant boot content is the FIRST text in its Task prompt. Boot is not context. Boot is the governing kernel. If a subagent hasn't confirmed boot acknowledgment, its outputs are not admissible.

---

## Lane Definitions

### LANE-B: Thread B Enforcement Kernel
**Boot source:** `core_docs/upgrade docs/BOOTPACK_THREAD_B_v3.9.13.md`
**Role:** Admissibility gate. Judges what evidence classes are allowed. Never runs sims.
**Never does:** Generate candidates, run probes, smooth narratives, produce sims.
**Does:** ACCEPT/PARK/KILL items from EXPORT_BLOCKs. Maintain SURVIVOR_LEDGER and TERM_REGISTRY.
**Dispatch rule:** The Task prompt MUST begin with the full text of the boot, followed by the ARTIFACT_MESSAGE or COMMAND_MESSAGE.

### LANE-SIM: Simulation / Evidence Producer
**Boot source:** `system_v4/docs/ENGINE_GRAMMAR_DISCRETE.md` + sim harness constraints
**Role:** Lower-loop evidence producer. Runs probes on the constraint manifold.
**Constraint-first preflight (required before any sim runs):**
1. State the primary constrained manifold (must be S³/spinor, not density)
2. State what projection loss this sim incurs (if any)
3. State what claim class is allowed from this sim
4. Declare which of the 10 ENGINE_GRAMMAR_DISCRETE invariants are being tested
**Never does:** Claim axis recovery from density-only probes. Promote single proxy to canon.

### LANE-A0: Controller / Graveyard / Router
**Boot source:** `BOOTPACK_THREAD_A_v2.60.md` (controller/routing section)
**Role:** Dispatch, monitor, collect, route. Primary graveyard operator.
**Graveyard is primary:** Dead candidates, failed probes, wrong conflations are the primary memory surface — not cleanup. Route from graveyard, not after it.
**Never does:** Synthesize results across lanes before B has gated them.

### LANE-A1: Wiggle / Branch Explorer
**Boot source:** Wiggle boot (multiple variants)
**Role:** Broad branch generation. Many candidates. No closure.
**Required by design:** Wide exploration before B gates. Must NOT be force-sequenced first.
**Outputs go to:** Graveyard first (to preserve dead branches), then to B-lane for admissibility.
**Anti-smoothing:** For every main candidate → 2 side ledges + 1 anti-hypothesis. Dead candidates must be preserved.

---

## Dispatch Protocol (How to Force Boot Loading)

Since subagents cannot load files themselves, the boot content must be **embedded in the Task prompt at dispatch time**.

### Step 1: Generate the booted task prompt

For LANE-B dispatch, the task prompt format is:
```
[FULL TEXT OF BOOTPACK_THREAD_B_v3.9.13.md]

---
BEGIN TASK

ARTIFACT_MESSAGE:
[content to gate]
```

For LANE-SIM dispatch, the task prompt format is:
```
CONSTRAINT MANIFOLD PREFLIGHT:
Primary manifold: [state explicitly]
Projection loss: [state explicitly]
Allowed claim class: [state explicitly]
ENGINE_GRAMMAR_DISCRETE invariants tested: [list which of the 10]

---
[Full text of ENGINE_GRAMMAR_DISCRETE.md invariants section]

---
BEGIN SIM TASK

[specific sim instructions]
```

### Step 2: Enforce acknowledgment before work begins

For LANE-B: The subagent must respond with `BOOT_ID: BOOTPACK_THREAD_B_v3.9.13.md / RESULT: PASS` before any other output.
For LANE-SIM: The subagent must output `PREFLIGHT: PASS` and restate the 3 preflight items before running.

If acknowledgment is missing from the output → result is not admissible.

### Step 3: Route outputs through graveyard

All outputs (PASS and FAIL alike) go to:
- `system_v4/a2_state/graveyard/` — preserved, not deleted
- Dead candidates are FIRST CLASS in graveyard, not afterthoughts

### Step 4: B-lane gates graveyard outputs

B-lane consumes SIM_EVIDENCE blocks from the LANE-SIM graveyard outputs.
Only SURVIVOR_LEDGER items from B are admissible for any synthesis.

---

## Boot Content References (Absolute Paths)

| Lane | Boot file |
|------|-----------|
| LANE-B | `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/upgrade docs/BOOTPACK_THREAD_B_v3.9.13.md` |
| LANE-A | `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/upgrade docs/BOOTPACK_THREAD_A_v2.60.md` |
| LANE-SIM preflight | `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/ENGINE_GRAMMAR_DISCRETE.md` |
| Grammar invariants | `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/ENGINE_GRAMMAR_DISCRETE.md` (Minimal Stable Grammar section) |
| Authority map | `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/DOC_AUTHORITY_MAP.md` |
| Bridge firewall | `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/RUNTIME_TO_STRUCTURE_BRIDGE.md` |

---

## Why the Boots Were Not Being Used

1. **Boot-skipping at dispatch:** Subagents were dispatched with task descriptions, not boot content. The boot was a file the agent was expected to read — but reading was not forced.
2. **Voluntarism:** The system assumed the agent would "want to" follow the boot. The boot was treated as context, not as a mandatory kernel.
3. **Recency bias:** Local artifacts (recent sims, recent docs) dominated over the boot surfaces because they were in working context.

**The correction:** Embed boot content directly in the Task prompt. Make boot acknowledgment a precondition of any output being treated as valid. This is mechanical enforcement, not behavioral guidance.

---

## Known Limitation

Subagents cannot spawn sub-subagents. So LANE-A1 wiggle depth is limited to one hop. Multiple A1 variants must be dispatched in parallel from the controller (A0 lane / this conversation), not recursively.

The workaround: dispatch many A1 variants in parallel with different wiggle seeds/constraints, route all outputs to the same graveyard, let B gate in batch.

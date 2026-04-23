# [Controller-safe] Kernel Stabilization Checklist

**Date:** 2026-03-27  
**Purpose:** Concrete queue for stabilizing the engine kernel before any broader systems upgrade.

> **Rule:** Do not open a larger architecture lane until the runtime/boot pair is less collapse-prone.

---

## Priority Order

1. Stabilize the kernel surface.
2. Stop reinfection from contaminated docs and task artifacts.
3. Rebuild the runtime around the kernel.
4. Enforce boot discipline mechanically.
5. Improve `A1 -> graveyard -> B -> SIM` coupling.
6. Only then reopen broad upgrade lanes.

---

## Work Queue

### 1. Kernel Surface

- [ ] Tighten `system_v4/docs/ENGINE_KERNEL_MINIMAL.md`
- [ ] Keep only:
  - carrier/manifold
  - dual-loop engine grammar
  - type/flow/precedence separation
  - runtime truth vs structural scaffold
  - quarantine list
- [ ] Link outward only to stronger guardrail/runtime surfaces

Primary refs:
- `system_v4/docs/ENGINE_KERNEL_MINIMAL.md`
- `system_v4/docs/DOC_AUTHORITY_MAP.md`
- `system_v4/docs/ENGINE_GRAMMAR_DISCRETE.md`

### 2. Contamination Quarantine

- [ ] Finish body-level scrub of contaminated antigravity files, not just header quarantine
- [ ] Keep quarantine list explicit:
  - “all 64 states are visited”
  - “Holodeck/FEP/autopoiesis are unified runtime truth”
  - “Ax3/Ax4/Ax5 are recovered and closed”
  - “type = flow = chirality”
- [ ] Route future agents away from hot history surfaces

### 3. Runtime / Engine Ownership

- [ ] Rework `system_v4/probes/engine_core.py`
- [ ] Move toward:
  - spinor-primary state
  - explicit outer/inner loops
  - explicit heating/cooling role placement
  - explicit inversion across the two engine families
  - explicit `32 / 32 / 64` ownership boundaries
- [ ] Stop treating flattened terrain/operator arrays as sufficient engine grammar

Primary refs:
- `system_v4/docs/DUAL_LOOP_SPINOR_GRAMMAR.md`
- `system_v4/docs/TYPE_FLOW_PRECEDENCE_SEPARATION.md`
- `system_v4/docs/ENGINE_OWNERSHIP_GRAMMAR_32_32_64.md`

### 4. Boot Discipline

- [ ] Create tiny required boot packet per lane
- [ ] Make boot acknowledgment mandatory before work is admissible
- [ ] Reject blended “helpful context” as a substitute for boot ingestion
- [ ] Keep lanes separate:
  - `A0`
  - `A1`
  - `SIM`
  - `B`

Primary refs:
- `system_v4/docs/BOOT_LANE_DISPATCH_SETUP.md`
- `system_v4/docs/boot_lane_registry.json`

### 5. Coupling

- [ ] Ensure grammar constrains engine design
- [ ] Ensure engine state constrains sim admissibility
- [ ] Ensure sims feed graveyard and bridge docs
- [ ] Ensure ratchet upgrades only what survives grammar plus runtime pressure

### 6. Axis Recovery Reopen

- [ ] Treat `Ax3`, `Ax4`, `Ax5` as open on-manifold recovery problems
- [ ] Use metaphor spaces only as mining/search spaces:
  - IGT
  - Jungian
  - I Ching
  - Szilard
  - Carnot
  - dual-stacked engines
- [ ] Do not promote them into direct ontology

---

## Done Means

- [ ] Future agents can start from the kernel without blob collapse
- [ ] `engine_core.py` no longer encodes a flattened fake grammar
- [ ] Boot skipping is mechanically invalid
- [ ] Pre-runs produce pressure instead of narrative smoothing
- [ ] Axis work remains explicitly provisional where still provisional

---

## Immediate Next Move

Start with the runtime/boot pair:

1. Patch runtime ownership grammar
2. Build fail-closed boot packets
3. Run pre-runs on the better-coupled runtime
4. Then reopen `A1 -> graveyard -> B`

# New Search Probes — Contract Packet

Status: active
Date: 2026-04-03
Issued by: Claude Code (Terminal D)
Issuing handoff: claude__probe_contract_packet_for_new_searches

---

## Purpose

This packet defines the contractual status of four new probe/search files
added around operator basis, entanglement object search, and entropy structure
search. Each probe is evaluated as a pre-Axis lego candidate against the
LEGO_SIM_CONTRACT requirements. Claims are bounded strictly to what the code
supports.

---

## Probe 1 — sim_c1_entanglement_object_search.py

**Likely tier:** Band C1 (entanglement object admission layer)

**Sim class:** `carrier_probe` / entanglement search

**Purpose / scientific question:**
Can joint 4×4 operators (Ti, Fe, Te, Fi) produce mutual information that
LOCC-only operators cannot? Identifies first nonclassical binding objects
surviving on the admitted Hopf/Weyl + Pauli substrate.

**Required tools actually used:**
- `numpy` (density matrix math, VN entropy, Frobenius norms)
- `engine_core` (GeometricEngine, EngineState, StageControls, TERRAINS)
- `geometric_operators` (apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
  partial_trace_A/B, _ensure_valid_density, negentropy, SIGMA_X/Y/Z)
- `stage_matrix_neg_lib` (all_stage_rows, init_stage, baseline_controls, axes_delta)

**Validation surface present or missing:**
- PRESENT: LOCC ablation — local-only product state evolution; verifies
  mi_locc < 1e-10 via `locc_theorem_verified` flag
- PRESENT: `is_witnessed` gate (mi_joint > 1e-5 AND mi_locc < 1e-10)
- PRESENT: JSON output with per-stage results and admission verdict
- MISSING: Fake coupling control (listed in docstring, not implemented in code)
- MISSING: Mispair control (cross-torus mispair listed in docstring, not
  implemented in code — only the LOCC ablation runs)
- MISSING: Proof surface (no z3 / formal constraint check)
- MISSING: Graph surface (no topology or graph artifact emitted)

**Promotion blockers:**
1. Fake coupling control not implemented — docstring claims it but code has no
   classical-correlation-only path that attempts to spoof Axis 0 signal
2. Mispair control not implemented — cross-torus mispair branch absent
3. No proof surface — admission is numerical only; no formal guard against
   classical smuggling
4. No graph / topology artifact emitted — cannot compose upward to graph layer

**Status:** `keep_but_open`

Rationale: core positive witness (LOCC vs. joint MI gap) is real and
scientifically honest. LOCC ablation is structurally sound. But two of three
declared negatives are unimplemented, and there is no graph or proof surface.
Not yet a full lego; retains value as a partial carrier-probe scaffolding.

---

## Probe 2 — sim_c2_entropy_structure_search.py

**Likely tier:** Band C2 (entropy structure admission layer)

**Sim class:** `constraint_probe` / entropy structure search

**Purpose / scientific question:**
Does Von Neumann entropy on the 4×4 joint state reveal nonclassical coherent
information (Ic > 0) that a classical Shannon entropy shortcut cannot reproduce?

**Required tools actually used:**
- `numpy` (density matrix math, eigenvalue decomposition)
- `engine_core` (GeometricEngine, EngineState, StageControls, TERRAINS)
- `geometric_operators` (apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
  partial_trace_A/B, _ensure_valid_density)
- `stage_matrix_neg_lib` (all_stage_rows, init_stage, baseline_controls)

**Validation surface present or missing:**
- PRESENT: Shannon shortcut ablation — diagonal-population-only entropy computed
  and compared against full VN coherent info; `is_shortcut_killed` gate
- PRESENT: JSON output with per-stage `vn_Ic`, `shannon_Ic`, `shortcut_gap`
- PRESENT: Admission verdict tied to shortcut_kill_count
- PRESENT: Purity-only proxy control — `get_purity_proxy(rho_AB)` computes
  `Tr(rho²)` on joint and marginals; `purity_Ic = purity_B - purity_AB`;
  killed on all 8 VN-positive stages (purity_proxy_verdict: KILLED — VN is necessary)
- PRESENT: Graph artifact — `c2_entropy_polarity_contrast_graph` emitted to
  `c2_entropy_polarity_graph.json`; 16 nodes (one per stage result), 16 directed
  edges connecting vn_Ic-positive nodes to vn_Ic-negative nodes within each
  terrain label; discrimination audit trail (shortcut_killed, purity_killed) on
  every node and edge
- MISSING: Proof surface (no formal constraint verification)

**Promotion blockers:**
1. ~~Purity-only proxy control not implemented~~ — CLOSED (killed 8/8 VN-positive stages)
2. ~~No graph or topology artifact emitted~~ — CLOSED (entropy polarity contrast graph, 16 nodes / 16 edges)
3. No proof surface — open

**Status:** `keep_but_open`

Rationale: Shannon shortcut ablation is legitimate and structurally honest.
Coherent information gap (VN vs. Shannon) is a valid discriminator. Purity proxy
is killed on all VN-positive stages — VN coherent information is doing unique work
the proxy cannot replicate. Graph artifact captures the Fe/Fi (positive) vs Ti/Te
(negative) entropy polarity contrast structure across all 16 stage results.
Remaining blocker: no formal proof surface. Not a full lego yet, but significantly
closer.

---

## Probe 3 — sim_operator_basis_search.py

**Likely tier:** Band B3 (operator/basis layer, lower-tier substrate)

**Sim class:** `geometry_probe` / operator basis search

**Purpose / scientific question:**
Is the {Ti, Te, Fi, Fe} operator assignment on the admitted Hopf/Weyl carrier
a real substrate constraint, or could it be remapped/collapsed without changing
lower-tier law behavior? Tests basis remap, coordinate-change control,
noncommutation ablation, and per-operator load-bearing status.

**Required tools actually used:**
- `numpy` only (self-contained; no engine_core, no stage_matrix_neg_lib)
- Spinor geometry built inline (S³ Hopf fiber/base sampling)

**Validation surface present or missing:**
- PRESENT: B3.1 basis remap — x-family ↔ z-family swap, fiber_base_gap measured
- PRESENT: B3.2 coordinate-change control — global Hadamard conjugation of
  both states AND operators; distinguishes real substrate change from relabeling
- PRESENT: B3.3 noncommutation ablation — all-z-family collapse, gap degradation
  measured with explicit noncomm_ratio
- PRESENT: B3.4 per-operator ablation — each of {Te, Fi, Ti, Fe} removed
  individually; load_bearing flag (gap drop > 20%)
- PRESENT: JSON output with all four sub-results and per-operator status map
- PRESENT: Explicit thresholds (10% / 5% / 20%) with stated rationale
- MISSING: Formal proof surface — thresholds are numerically defined, no z3 or
  symbolic constraint backing
- MISSING: Graph/topology artifact — no graph surface emitted
- MISSING: Cross-check against engine_core stage geometry — uses inline spinor
  sampling, not the main engine's stage rows

**Promotion blockers:**
1. No formal proof surface — all four gates are numerical threshold gates only
2. No graph artifact emitted
3. Inline spinor geometry not cross-checked against engine_core TERRAINS or
   stage_matrix; may diverge from canonical carrier definition used by C1/C2

**Status:** `keep_but_open`

Rationale: this is the most structurally complete of the three search probes.
Four explicit gates with stated discriminating thresholds, coordinate-change
control to distinguish relabeling from real substrate change, per-operator
demotion analysis. The validation logic is honest. Promotion blocker is the
absence of formal proof backing and graph surface — not a fatal flaw at this
tier, but required before lego promotion.

---

## Probe 4 — validate_operator_basis_packet.py

**Likely tier:** Band B3 companion (meta-validation / admission gate)

**Sim class:** `placement_probe` (post-hoc gate, not a simulation)

**Purpose / scientific question:**
Gate the B3 operator basis admission. Reads
`operator_basis_search_results.json` and applies four explicit pass/fail gates
to determine whether {Ti, Te, Fi, Fe} is admitted as lower-tier substrate.

**Required tools actually used:**
- `json`, `os`, `datetime` (stdlib only — pure file reader and gate evaluator)
- No numpy, no engine imports

**Validation surface present or missing:**
- PRESENT: Four named gates with explicit thresholds and verdict strings
- PRESENT: Per-operator `admitted_substrate` / `demotion_candidate` status map
- PRESENT: JSON output with gates, score, and operator_basis_verdict
- PRESENT: Console report
- MISSING: Independent proof path — entirely dependent on
  `sim_operator_basis_search.py` output; cannot run standalone or verify
  independently
- MISSING: No fallback if sim results are stale or from an incompatible run

**Promotion blockers:**
1. Hard dependency on upstream sim output file — if sim_operator_basis_search
   is re-run with different geometry parameters, validator may read stale data
2. No independent verification path
3. No graph artifact

**Status:** `admitted` (as a validation gate, conditionally)

Rationale: the gate logic is sound and explicit. Its role is defined and
bounded — it reads, gates, and reports. It does exactly what a placement_probe
should. Conditional admission: it is admitted as a gate for the B3 layer
specifically, contingent on the upstream sim being run first. It does not claim
to be a standalone sim.

---

## Summary Table

| Probe | Tier | Sim Class | Status | Primary Blocker |
|---|---|---|---|---|
| sim_c1_entanglement_object_search.py | C1 | carrier_probe | keep_but_open | MI witness not quantum-specific (fake coupling + mispair not killed) |
| sim_c2_entropy_structure_search.py | C2 | constraint_probe | keep_but_open | no proof surface (purity proxy closed; graph artifact present) |
| sim_operator_basis_search.py | B3 | geometry_probe | keep_but_open | no formal proof surface; no cross-check with engine_core |
| validate_operator_basis_packet.py | B3 companion | placement_probe | admitted (conditional) | upstream dependency; no independent path |

---

## Shared Deficits Across C1, C2, B3

Current shared deficit:
- No proof surface (z3 or formal constraint guard not present) — all three probes

Partially resolved:
- Graph artifact: C2 now has `c2_entropy_polarity_graph.json` (16 nodes / 16 edges). C1 and B3 still lack graph artifacts.
- Declared negatives: C2 purity proxy closed. C1 fake coupling + mispair implemented but not killed — deeper MI discriminator issue exposed.

These are not treated as `broken` because the implemented paths are honest and
scientifically sound. They are `keep_but_open` pending the missing negatives
and surfaces.

---

## Probes Requiring Future Implementation Handoff

**sim_c1_entanglement_object_search.py** needs a follow-up handoff for:
- Implement fake coupling control (classical correlation path attempting Axis 0 signal)
- Implement mispair control (cross-torus entanglement pairing test)

**sim_c2_entropy_structure_search.py** needs a follow-up handoff for:
- Implement purity-only proxy control (Tr(rho²) branch)

**sim_operator_basis_search.py** needs a follow-up handoff for:
- Cross-check spinor geometry against engine_core TERRAINS/stage rows
- Add graph artifact output (even a minimal edge list)

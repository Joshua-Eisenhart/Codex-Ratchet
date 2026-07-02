# Probe/Effect -> Spinor/Quaternion Bottom-Up Manifold Suite Audit

Date: 2026-05-24

Status: current executable audit, not final manifold admission.

## Purpose

This run rebuilt the manifold in the corrected order, with one important process rule:

> Model each constraint-manifold layer locally with its full tool matrix first. Do not treat a single all-at-once manifold run as evidence that every layer works.

The intended build order is:

1. finite probe/effect identity
2. admitted density/history effects
3. spinor/quaternion/Hopf/Weyl geometry
4. operator loop and tensor carriers
5. source-aligned engine runtime
6. Xi/Phi0 bridge control receipts
7. support Axis0 candidate gate
8. flux layer candidate gate
9. flux-bound downstream Axis0 gradient readout

The correction is explicit: Bloch, Pauli, vectors, and Cartesian pictures are not root substrate. They can appear only as admitted adapters, local charts, diagnostics, or controls after finite probes/effects and noncommuting operator relations are in place.

The second correction is procedural: each layer must have its own bounded model, tool receipts, controls, and carry-forward boundary before the next layer is trusted. The stack can be run bottom-up, but a downstream pass does not erase upstream obligations.

## Main Suite Result

Command:

```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/run_probe_effect_spinor_bottom_up_manifold_suite_20260524.py
```

Result file:

```text
system_v5/ops/formal_scouts/results/probe_effect_spinor_bottom_up_manifold_suite_20260524_results.json
```

Summary:

- all_pass: true
- scripts: 54
- strict validation: pass
- source lint: pass
- unexpected failures: none
- elapsed seconds: 996.98

Important: `all_pass` here means the suite executed, validated strict rows, and classified expected nonpromotion receipts. It does not mean Axis0, flux, PEPS3D, gravity, Standard Model, Yang-Mills, Riemann, or final physics claims are admitted.

## Foundation Alignment Gate

After the recovery pass, a stricter standalone gate was added:

```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/sim_constraint_manifold_foundation_alignment_gate_probe.py
```

Result file:

```text
system_v5/ops/formal_scouts/results/constraint_manifold_foundation_alignment_gate_probe_results.json
```

Summary:

- all_pass: true
- foundation_closed: false
- flux_layer_allowed: false
- downstream_axis0_allowed: false
- policy: `freeze_axis0_and_block_flux_layer_until_lower_manifold_layers_are_correct`

This is the current correction to the work order. The suite can show useful local receipts while the foundation is still not closed. The gate classifies the lower layers as:

| Layer | Gate status | Meaning |
|---|---|---|
| L0 finite effect/probe substrate | partial supported, not final | finite effect/probe and Weyl-Heisenberg receipts exist, but they do not admit final manifold ontology |
| L1 spinor/quaternion networks | partial supported, adapter-bound | spinor/quaternion rows exist, but density-carrier adapters remain in the live evidence surface |
| L2 MPS/PEPS/PEPS3D carriers | blocked local/sampled PEPS3D | PEPS3D rows are local/sampled/scaling receipts, not full PEPS3D environment closure |
| L3 engine runtime | blocked until PEPS3D spinor-native | source-aligned runtime exists, but not as a full spinor/quaternion PEPS3D runtime |

Therefore flux-layer rows are blocker/control instrumentation until the lower constraint-manifold layers close. Axis0 remains a downstream readout and should not be the active science target until the foundation gate and flux layer change status.

Live-runner status:

- The full-suite receipt is now fresh relative to the current runner.
- `run_probe_effect_spinor_bottom_up_manifold_suite_20260524.py` stages 54 scripts, with L7 expanded to 13 rows.
- The fresh receipt is `54/54` green as a formal-scout suite receipt, not as scientific closure.
- A later standalone integrated shell/boundary/flux/Axis0 control scout has its own receipt and is not yet registered into the 54-row suite.

Contract-lint repair note:

- A tooling hole was found after this receipt: `scripts/lint_sim_contract.py` only treated exact `nonclassical` as nonclassical, so prefixed rows such as `nonclassical_peps3d_flux_axis0_runtime_bound_loop4` could bypass C7/C8.
- The linter now treats `nonclassical_*` as nonclassical and bridge-like values ending in or containing `_bridge` as bridge.
- Local formal-scout load-bearing dependencies now require a fresh source/result pin by source hash when present, otherwise by result mtime newer than source mtime.
- Focused regression coverage now proves prefixed nonclassical C7/C8 firing, bridge suffix/infix C7 firing, and stale local formal-scout receipt rejection.
- Targeted lint over the newest PEPS3D L7 rows passes with zero violations under the repaired gate; this repairs gate coverage only, not scientific admission.

## Layer-Local Tool Matrix Audit

Command:

```bash
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/run_constraint_manifold_layer_tool_matrix_audit_20260524.py
```

Result file:

```text
system_v5/ops/formal_scouts/results/constraint_manifold_layer_tool_matrix_audit_20260524_results.json
```

Summary:

- all_pass: true
- layers audited: 8
- failed layers: none
- suite scripts covered: 54
- not-all-at-once contract: pass
- strict validation: pass

This layer-tool audit covers the latest 54-row full-suite receipt estate. It does not cover the later standalone integrated shell/boundary/flux/Axis0 control scout unless that scout is explicitly registered into the suite and the suite is rerun.
- source lint: pass

The layer audit checks the actual staged receipts against required tool groups:

| Layer | Required local tool groups | Status |
|---|---|---|
| L0 finite probe/effect substrate | finite effect/probe, torch-native evidence | pass |
| L1 spinor/quaternion networks | spinor/quaternion, torch-native evidence, engine runtime | pass |
| L2 MPS/PEPS/PEPS3D carriers | tensor carrier, torch-native evidence | pass |
| L3 engine runtime | engine runtime, torch-native evidence | pass |
| L4 Xi/Phi0 bridge controls | bridge/Axis0, torch-native evidence | pass |
| L5 Axis0 candidates | bridge/Axis0, spinor/quaternion, torch-native evidence | pass |
| L6 flux layer candidates | flux, spinor/quaternion, torch-native evidence | pass |
| L7 flux-bound Axis0 gradient | flux, bridge/Axis0, spinor/quaternion, tensor carrier, torch-native evidence | pass |

This does not mean every layer is complete. It means the current suite now has a receipt-bound local model for each layer, instead of relying on one blended full-manifold run.

Two read-only sidecar audits checked the split:

- L0-L2 are layer-local under the current matrix, with no missing required groups. L2 remains bounded carrier evidence, not PEPS/PEPS3D closure.
- L3-L7 are layer-local under the current matrix, with no missing required groups. L4 contains expected negative/nonpromotion bridge rows. L6 is derived flux candidate coverage, and L7 tests Axis0 only after derived PEPS3D flux.

Caveats surfaced by sidecar audit:

- The current suite/audit files are worktree artifacts unless and until they are explicitly checkpointed. Do not treat Git-index state as proof that these have been promoted.
- `engine_runtime` in L1 is evidenced by source/category and `canonical_qit_engine_specs` support, not by every L1 row making engine runtime the only load-bearing tool.
- The L2 matrix now includes a local PEPS/PEPS3D environment-contraction gate, but it is still local-star/local-edge contraction, not CTMRG or full PEPS3D closure.
- External Axis0 audit killed the earlier "carrier-discriminates-by-polarity-sign" framing under smooth coupling. Current formal work should track magnitudes, named cuts, and finite branch-history weights separately; do not collapse them into one Axis0 sign claim.

The required debugging order is now:

```text
fix local layer receipt
-> run local layer controls
-> stack with the immediately lower layer
-> run pairwise handoff controls
-> only then include it in the full bottom-up suite
```

## What Actually Worked

### L0: finite probe/effect substrate

Passed:

- finite effect algebra laws
- finite SIC/Weyl-Heisenberg substrate admission
- SIC vs MUB probe comparison
- finite contextuality/sheaf event gate
- process POVM / quantum-comb history gate
- representation alignment audit

Interpretation:

The root direction is now executable. The state primitive can be treated as finite probe response/effect algebra first. SIC/POVM and Weyl-Heisenberg relations are better root-aligned than primitive Bloch/Pauli pictures.

### L1: spinor/quaternion networks

Passed:

- IJK quaternion flux shell-fuzz engine probe
- eight-node spinor network flux-current gate
- explicit 8-qubit spinor entanglement engine manifold
- full IGT 64-substage spinor engine cycle

Key receipts:

- 64 substages are represented.
- 8 distinct terrain variants are represented.
- IJK flux is represented as three-component quaternionic readout, not a scalar.
- The eight-node spinor network runs at dimension 256.

Interpretation:

The spinor/quaternion correction is now present in runnable scouts. This is the right level for `i,j,k`: literal quaternion components, not jargon or scalar flux.

### L2: MPS / PEPS / PEPS3D carriers

Passed as strict or classified bounded receipts:

- spinor IGT schedule portability across MPS/PEPS/PEPS3D
- MPS scaling at 8, 16, 32, 64 sites
- explicit PEPS3D 64-site geometry flux
- PEPS/PEPS3D local environment-contraction gate
- PEPS small-grid dynamics as bounded first rung
- PEPS3D tiny-grid dynamics as bounded first rung
- PEPS/PEPS3D stage-loop depth inventory

Interpretation:

MPS scaling to 64 is working. PEPS3D 64-site geometry flux is working as a geometry/carrier scout. A stricter PEPS/PEPS3D local environment-contraction gate now also passes. The older dynamic PEPS and PEPS3D rows are not final closures; they are tiny/small-grid bounded receipts and remain blockers for full PEPS/PEPS3D dynamics.

New PEPS/PEPS3D environment-contraction receipt:

- script: `sim_peps_peps3d_local_environment_contraction_gate_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json`
- carriers: PEPS 4x4 and PEPS3D 4x4x4
- environment kind: local star and local edge
- full network contraction: false
- dense full state/environment constructed: false
- PEPS site count: 16
- PEPS3D site count: 64
- PEPS identity-environment gap: 0.6047254369971227
- PEPS shuffled-topology gap: 0.6858880810878262
- PEPS3D identity-environment gap: 0.010763832329353025
- PEPS3D shuffled-topology gap: 0.06494953254479104
- PEPS3D sampled site: `(0, 0, 0)`
- PEPS3D sampled edge: `(0, 0, 0) -> (1, 0, 0)`

Interpretation of the environment row:

- It upgrades L2 from local tensor signatures to actual local contraction receipts.
- It verifies trace, PSD, normalization, identity-environment controls, shuffled-topology controls, and dense-ban fields.
- It still does not prove full PEPS/PEPS3D dynamics. It is a bounded contraction gate that future dynamic rows must consume.

### L3: engine runtime

Passed:

- source-aligned QIT engine runtime
- source-aligned QIT attractor basin probe
- two-root QIT engine manifold runtime build

Interpretation:

The engines are running in the bounded source-aligned sense. The suite confirms engine schedules, runtime convergence/basin evidence, and the current manifold runtime build. This still does not prove final scale-level attractor basin admission.

### L4/L5: bridge and Axis0

Axis0 audit now passes as a routing/audit gate, not as closure. The suite now also includes an 8-qubit spinor/quaternion Axis0 shell-response scout derived from the Axis0 v0.1-v0.3 and physics-bridge draft packet.

Current bridge statuses:

- MPS Phi0 bridge: open nonzero, not control-separated
- slow-mode/terrain bridge: open nonzero, not control-separated
- coupled-E16 stress: open nonrobust internal controls
- response-gradient repair: open nonrobust response controls
- MPS Stinespring/process-history handoff: live local handoff, not final Xi

The Layered Axis0 audit reframes this correctly:

- L2 unlocks chart A0 sign / torus-seat entropy.
- L4 unlocks signed bipartite cut entropy, coherent information, conditional entropy.
- Schedule-history Xi and shell-weighted Phi0 remain next bridge targets.
- L7 is now the flux-bound Axis0 gradient scout: derived PEPS3D flux first, signed QIT/FEP readout second.

New Axis0 shell-response receipt:

- script: `sim_axis0_ijk_shell_correlation_response_probe.py`
- result: `system_v5/ops/formal_scouts/results/axis0_ijk_shell_correlation_response_probe_results.json`
- qubits: 8
- Hilbert dimension: 256
- engine rows: 64
- terrain variants: 8
- `jk_shell_time_magnitude`: 1.147431144329474
- `negative_conditional_entropy_fraction`: 1.0
- Axis0 response norm under shell perturbation: 0.1382546337695323
- global-phase-only control response norm: 0.0
- static `j/k` control response norm: 0.0
- topology-blind control gap: 0.03196270641329968
- swapped-arrow control gap: 0.14666945143090404

Candidate derivatives emitted by that receipt:

```text
dD_MI                     = 0.13025897972861541
dVar_MI                  = 0.0000014395317814279578
dT_total_correlation      = 0.01772418820179998
di_shell_coherent_sum     = 0.02015852606214124
dCMI_shell_mean           = 0.0042730853748989064
dH_history                = -0.037525586973468826
```

Interpretation of the new row:

- It gives the Axis0 draft packet an executable bottom-up carrier: admitted spinors -> quaternion shell gates -> finite shell/cut reductions -> QIT entropies.
- It treats `i` as a shell/cut scalar order-parameter candidate, not primitive time.
- It treats `j/k` as finite shell-history/refinement fuzz, not a narrative future.
- It confirms negative conditional entropy across all tested shell cuts in this bounded engine state.
- It does not admit final Axis0. It only shows that this specific shell-response harness is live and control-separated at 8 qubits.

New MPS Axis0/Kraus handoff receipt:

- script: `sim_axis0_mps_shell_kraus_handoff_probe.py`
- result: `system_v5/ops/formal_scouts/results/axis0_mps_shell_kraus_handoff_probe_results.json`
- site counts: 8, 16, 32, 64
- engine rows per scale: 64
- finite branch count: 16
- MPS max bond seen: 8
- `min_response_norm`: 0.06421383271564596
- `max_response_norm`: 0.18873702943576853
- `min_history_entropy`: 2.7710939292425167
- `max_history_entropy`: 2.771429871912556
- noncommuting witness gap: 0.5022063652615356
- commuting control gap: 0.00000038515446745677166
- global-phase-only response norms: all 0.0
- static `j/k` response norms: all 0.0
- cut-erased gaps: 0.36679088213880134, 0.3449526228877771, 0.08564751271053914, 0.001227112648458187
- schedule-scrambled gaps: 0.44744773823873896, 0.07235487044034733, 0.3477474881818047, 0.21449802225139886

Interpretation of the MPS handoff row:

- It ports the Axis0 shell/cut harness onto compressed explicit-spinor MPS carriers at 8/16/32/64 sites.
- It replaces the earlier shell-history proxy with finite Kraus/effect branch weights, while still stopping short of a full Stinespring/process-tensor closure.
- It uses smooth quaternion-shell coupling, not argmax axis selection. This follows the external audit finding that argmax coupling created false chirality/polarity artifacts.
- It reports magnitudes and named cuts, not a final Axis0 polarity sign.
- It does not consume raw Axis0 router vectors.
- The 64-site cut-erasure gap is positive but weak, so PEPS/PEPS3D and later scale rows need stronger cut/environment witnesses.

New MPS Stinespring/process-history Xi handoff receipt:

- script: `sim_axis0_mps_stinespring_process_xi_handoff_probe.py`
- result: `system_v5/ops/formal_scouts/results/axis0_mps_stinespring_process_xi_handoff_probe_results.json`
- system site counts: 8, 16, 32, 64
- total site counts with history ancillas: 16, 24, 40, 72
- history ancillas: 8
- max history entropy: 2.0823199171040123
- min history entropy: 2.0823145820691216
- max system-history MI: 0.02911656862354687
- min system-history MI: 0.027030696629383583
- nearby variants: 11/11

Interpretation of the Stinespring row:

- It adds explicit finite history ancilla sites to the MPS carrier.
- It replaces the pure branch-weight row with Stinespring-style system/history coupling.
- It is a process-history Xi handoff, not a final Xi/Phi0 kernel.

Flat Axis0 gradient control:

- script: `sim_axis0_qit_fep_signed_gradient_probe.py`
- status: not wired into the suite
- result: failed one gate: pair-level chirality did not change signed pressure magnitude

Interpretation:

This is a useful negative control. It shows that a flat pair-level signed FEP gradient is too shallow for the current target. The suite therefore does not promote that row. The aligned target is PEPS3D spinor-network flux first, then Axis0 as the signed QIT/FEP gradient on that derived flux.

Interpretation:

Axis0 is not closed. The raw L4 cut-state candidates are nonrobust under controls. The new MPS/Kraus handoff improves the carrier layer, but it does not rescue a final Axis0 sign claim. The next serious Axis0 work is Stinespring/process-history Xi and L8 shell-weighted coherent-information style Phi0.

### L6: derived flux candidates

Passed as bounded/open candidates:

- dynamic spinor-shell chiral flux topology mutation
- layer-dependency flux ablation
- spinor-twistor flux basin binding
- flux coherent recovery Phi0 candidate
- flux coherent recovery stress

Interpretation:

Flux is still derived, not primitive. The current evidence supports treating it as a bounded multi-component current/coexistence family over already-admitted geometry/history layers. The new dynamic shell receipt sharpens this: flux should currently be modeled as a chiral spinor-shell boundary current that can mutate the four topology signatures, not as a scalar and not as a free local degree of freedom.

New flux shell receipt:

- script: `sim_dynamic_spinor_shell_chiral_flux_topology_probe.py`
- result: `system_v5/ops/formal_scouts/results/dynamic_spinor_shell_chiral_flux_topology_probe_results.json`
- row count: 64
- shell count: 8
- IJK component count: 3
- flux magnitude: 0.6910214323838306
- `jk_temporal_shell_magnitude`: 1.2795987604953156
- engine chiral gap: 0.6414133720777885
- topology off-diagonal mutation mass: 4.117972900511347
- minimum finite shell entropy compression delta: 0.23221370327517876
- zero-flux graveyard: no topology mutation
- static-shell graveyard: no dynamic shell-time
- swapped-arrow and topology-blind controls change the signature

Interpretation of the new flux row:

- It uses literal quaternion algebra: `i^2 = j^2 = k^2 = -1`, `ij = k`, `jk = i`, `ki = j`, with anti-commuting reversals.
- It assigns `i` to the rotation/order tick, `j` to past-outward shell flow, and `k` to future-inward shell flow as a scout-level temporal shell grammar.
- It tests flux as engine-bound and chiral by comparing type-one and type-two schedules.
- It shows flux changes all four topology signatures in the bounded scout.
- It keeps flux below admission: no final flux, no final Axis0, no physics claim.

### L7: flux-bound Axis0 gradient

Passed:

- PEPS3D spinor-network flux -> signed Axis0/QIT-FEP gradient

New PEPS3D flux-bound Axis0 receipt:

- script: `sim_peps3d_spinor_network_flux_axis0_gradient_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_spinor_network_flux_axis0_gradient_probe_results.json`
- PEPS3D carrier: 2x2x2, 8 sites
- contraction: local-star PEPS3D boundary contraction on all 8 shell sites
- full network contraction: false
- engine rows: 32 per engine type
- nominal flux norm: 0.07484629056762065
- sheet-erased flux ratio: 7.416687027542895e-16
- shell-time reversal `j/k` gap: 0.06269651957546982
- topology-freeze gap: 0.030978355847462308
- engine-swap flux gap: 0.004123406366561486
- homeostatic Axis0 gradient: -0.10957077169626434
- allostatic Axis0 gradient: 0.635611299969109
- neutral/no-structure Axis0 gradient: 0.0
- branch-count-only gradient: 0.0

Interpretation of the new L7 row:

- It implements the corrected doctrine: flux is the engine-bound quaternionic L/R spinor-shell boundary current; Axis0 is the signed QIT/FEP entropy-gradient readout on that current.
- It starts at 8 PEPS3D shell sites, as requested, rather than using a 1D MPS result as the final target.
- It derives flux from left/right chiral PEPS3D boundary responses after engine transport; flux is not inserted as a variable.
- It tests the required controls: sheet erase, shell-time reversal, topology freeze, engine swap, branch-count-only, homeostatic compression, allostatic reconfiguration, and neutral/no-structure.
- It passes as a first PEPS3D shell scout. It does not close PEPS3D, flux, Axis0, Xi, or physics.

New PEPS3D flux-bound Axis0 scaling receipt:

- script: `sim_peps3d_spinor_network_flux_axis0_scaling_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_spinor_network_flux_axis0_scaling_probe_results.json`
- PEPS3D site counts: 8, 27, 64
- sampled boundary site counts: 8, 18, 19
- calibration: homeostatic target `lambda=0.34`; allostatic transition-cost scale `5.0`
- 8-site flux norm: 0.09505846441555725
- 27-site flux norm: 0.09481309191593701
- 64-site flux norm: 0.06621758786151175
- sheet-erased flux ratio: 0.0 at all three scales
- shell-time reversal `j/k` gaps: 0.050637475324232836, 0.012355028714070668, 0.044630423654420076
- topology-freeze gaps: 0.05979588618759758, 0.014146874250998365, 0.0872864355450573
- engine-swap flux gaps: 0.01516365064831357, 0.06982086999903933, 0.02590091987488577
- homeostatic Axis0 gradients: -0.9675008829291842, -0.19232577060350337, -0.5324652746701408
- allostatic Axis0 gradients: 0.4694222928294328, 2.586596686443972, 5.789334059138125
- neutral/no-structure gradients: 0.0 at all three scales

Interpretation of the scaling row:

- The flux witness itself survived scaling before calibration: flux present, sheet erasure collapse, shell-time reversal, topology freeze, and engine binding all held at 8/27/64.
- The first inherited FEP sign fixture failed at scale: allostatic sign failed at 8 and homeostatic sign failed at 64.
- A target-sensitivity sweep found a fixed scale-stable FEP fixture: homeostatic target `lambda=0.34` and allostatic transition-cost scale `5.0`.
- This is a successful scaling scout with an explicit calibration caveat, not a final Axis0 theorem.

New PEPS3D flux-bound Axis0 calibration-ablation receipt:

- script: `sim_peps3d_flux_axis0_calibration_ablation_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_calibration_ablation_probe_results.json`
- admitted calibration passes at 8/27/64:
  - homeostatic gradients: -0.9675008829291842, -0.19232577060350337, -0.5324652746701408
  - allostatic gradients: 0.4694222928294328, 2.586596686443972, 5.789334059138125
- inherited unscaled calibration fails at scale:
  - 8-site allostatic gradient: -1.0003638748451782
  - 64-site homeostatic gradient: 0.7057698746561882
- over-costed homeostasis fails at all three scales:
  - 0.9946942694513683, 1.7723912921986231, 1.3669953978787397
- nominal flux remains present independently of calibration:
  - 0.09505846441555725, 0.09481309191593701, 0.06621758786151175

Interpretation of the calibration-ablation row:

- The FEP calibration is load-bearing and now explicitly tested.
- The old inherited fixture is preserved as a graveyard control, not silently forgotten.
- The flux witness remains present even when FEP calibration fails, separating "flux exists" from "Axis0 sign is correctly calibrated."
- This still does not admit final Axis0; it narrows the next target to calibration-independent or better-derived F_QIT terms.

New PEPS3D flux-bound Axis0 calibration-envelope stress receipt:

- script: `sim_peps3d_flux_axis0_calibration_envelope_stress_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_calibration_envelope_stress_probe_results.json`
- current constants survive only inside a narrow finite target/cost envelope.
- inherited fixtures and broad-grid controls fail.

New PEPS3D flux-bound Axis0 held-out-shape stress receipt:

- script: `sim_peps3d_flux_axis0_heldout_shape_stress_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_heldout_shape_stress_probe_results.json`
- held-out shapes: `(2,3,4)`, `(2,4,4)`, `(3,3,4)`
- allostatic signs survive all three held-out shapes.
- homeostatic sign fails on `(3,3,4)`.
- interpretation: shape-agnostic calibration under the current constants is killed.

New PEPS3D flux-bound Axis0 boundary-sampler stress receipt:

- script: `sim_peps3d_flux_axis0_boundary_sampler_stress_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_boundary_sampler_stress_probe_results.json`
- tested samplers: canonical, all-boundary, reverse-stride, parity, deterministic-hash.
- alternate samplers expose sign sensitivity, including `8:parity:homeostatic`, `64:reverse_stride:homeostatic`, and `64:parity:allostatic`.
- interpretation: sampled-boundary stability is not full PEPS3D closure.

New PEPS3D flux-bound Axis0 target-scramble control receipt:

- script: `sim_peps3d_flux_axis0_target_scramble_control_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_target_scramble_control_probe_results.json`
- wrong targets break 5 cells but survive 25 cells.
- interpretation: target choice is load-bearing, but not uniquely derived.

New PEPS3D flux-bound Axis0 runtime-record binding gate receipt:

- script: `sim_peps3d_flux_axis0_runtime_record_binding_gate_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_runtime_record_binding_gate_probe_results.json`
- builds 384 enriched runtime records.
- exposes that raw PEPS3D rows were too shallow for runtime claims.
- interpretation: runtime record binding is better instrumentation, not Axis0 closure.

New PEPS3D flux-bound Axis0 boundary-functional invariance receipt:

- script: `sim_peps3d_flux_axis0_boundary_functional_invariance_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_boundary_functional_invariance_probe_results.json`
- all-boundary is a better scaffold than the earlier sampled boundary.
- held-out `(3,3,4)` still fails homeostatic sign.
- interpretation: this records a blocker; it is not sampler-invariant or shape-invariant closure.

New PEPS3D flux-bound Axis0 calibration-rule derivation blocker receipt:

- script: `sim_peps3d_flux_axis0_calibration_rule_derivation_blocker_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_calibration_rule_derivation_blocker_probe_results.json`
- simple monotone beta shape-asymmetry rules do not fix all held-out shapes.
- interpretation: the simple rule family is killed; calibration is still not derived.

New PEPS3D flux-bound Axis0 runtime-bound loop4 receipt:

- script: `sim_peps3d_flux_axis0_runtime_bound_loop4_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_runtime_bound_loop4_probe_results.json`
- runtime binding changes the flux readout.
- runtime-bound variants kill source allostatic sign in loops 2-4.
- the runtime-weighted surface fails held-out homeostasis.
- interpretation: runtime binding is progress because it exposes the correct failures; it does not solve Axis0 sign calibration.

New PEPS3D flux-bound Axis0 coordinate-face boundary-functional receipt:

- script: `sim_peps3d_flux_axis0_axis_face_orbit_boundary_functional_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_axis_face_orbit_boundary_functional_probe_results.json`
- tests runtime-bound x/y/z PEPS3D carrier face-pair means and an equal six-face boundary mean.
- the x/y/z faces are coordinate-carrier adapter/control instruments, not root geometry.
- no group orbit, gauge orbit, manifold orbit, or sampler invariant is defined or proven by this row.
- source axis-pair spread is nonzero on `3x3x3`, so axis dependence is measured rather than hidden.
- six-face mean allostatic signs survive heldouts, but homeostatic signs fail on the held-out shapes tested.
- root-substrate classifier bucket: `boundary_functional_control`, not clean `aligned_candidate`.
- interpretation: six-face averaging is useful carrier-boundary instrumentation, not sampler-invariant closure or Axis0 calibration repair.

New PEPS3D flux-bound Axis0 runtime-cardinality calibration gate receipt:

- script: `sim_peps3d_flux_axis0_runtime_cardinality_calibration_gate_probe.py`
- result: `system_v5/ops/formal_scouts/results/peps3d_flux_axis0_runtime_cardinality_calibration_gate_probe_results.json`
- freezes `lambda_home = 0.18 + 0.04 * 4 = 0.34` from enriched runtime-record cardinality.
- records that `LAM0=0.18` and `DELTA=0.04` are inherited fixture constants, not derived by this row.
- source homeostatic signs pass on `2x2x2` and `3x3x3`.
- held-out homeostatic signs pass on `2x3x4` and `2x4x4`, but fail on `3x3x4`.
- root-substrate classifier bucket: `calibration_rule_control`, not clean `aligned_candidate`.
- interpretation: the one-feature runtime-cardinality rule is a useful source gate, but the complete calibration-closure claim is killed by the held-out failure and the constants still need derivation.

Interpretation of the new stress rows:

- These rows pass because they successfully expose fragility and preserve nonpromotion boundaries.
- They do not strengthen final Axis0. They narrow the live blocker to derived calibration, sampler invariance, and source-conformant runtime coupling.
- The honest wording is now: runtime-bound PEPS3D flux/Axis0 is better instrumented, but final Axis0 remains blocked. Flux witness and coordinate-face boundary instrumentation survive these sampled PEPS3D rows more robustly than the Axis0 homeostatic sign calibration does.

## Expected Blockers

These rows are intentionally classified as expected nonpromotion receipts:

- `sim_two_root_constraint_peps_small_grid_dynamics_probe.py`
- `sim_two_root_constraint_peps3d_tiny_grid_dynamics_probe.py`
- `sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe.py`
- `sim_two_root_constraint_full_manifold_runtime_trace_refresh_probe.py`
- `sim_two_root_constraint_coupled_e16_phi0_stress_controls_probe.py`
- `sim_two_root_constraint_full_manifold_trace_after_phi0_stress_probe.py`
- `sim_two_root_constraint_phi0_bridge_response_gradient_after_stress_probe.py`
- `sim_two_root_constraint_axis0_layered_entropy_ratchet_audit_probe.py`
- `sim_axis0_qit_fep_signed_gradient_probe.py`

This is not hiding failures. These are the current scientific blockers:

- PEPS/PEPS3D dynamics are not yet full closures.
- Coupled-E16 Phi0 is weak and control-sensitive.
- Stress controls beat the current L4 Phi0 bridge family.
- Axis0 audit passes only by keeping final closure blocked.
- A flat pair-level signed FEP gradient is too shallow; it fails the chirality-magnitude gate without PEPS3D spinor-network flux.
- PEPS3D flux-bound Axis0 calibration is shape-sensitive, sampler-sensitive, and target-sensitive under the new stress rows.

## Current Scientific Bottom Line

The corrected bottom-up stack is now runnable as a staged suite:

```text
finite effects / probe-relative identity
-> SIC/MUB/contextual/process histories
-> spinor/quaternion/Hopf/Weyl geometry
-> MPS/PEPS/PEPS3D carriers
-> source-aligned 64-substage engine schedule
-> bridge/control receipts
-> derived dynamic shell flux candidates
-> Axis0 as signed QIT/FEP gradient on derived PEPS3D flux
```

That is not the same as saying the whole manifold has been solved in one full-depth model. The current status is better described as: every listed layer has a local receipt, the staged suite passes, and the hard integrations now have to be debugged by layer handoff rather than by a monolithic run.

The engines are running. Spinor networks are running. Quaternion/IJK flux is represented. MPS to 64 sites is running. PEPS3D 64-site geometry flux is running. PEPS/PEPS3D local environment contraction is running. Axis0 now has support rows plus flux-bound PEPS3D signed-gradient rows. The flux-bound Axis0 scout has been scaled to 8/27/64 PEPS3D sites with sampled boundary contractions, and the FEP calibration has an explicit ablation receipt. The newest held-out-shape, boundary-sampler, and target-scramble stress rows make the blocker sharper: flux remains detectable, but Axis0 sign calibration is not shape-agnostic, sampler-invariant, or uniquely target-derived. Final Axis0 remains blocked because this is still local/sampled PEPS3D contraction with an explicit FEP calibration fixture, not full PEPS3D manifold closure.

What is not admitted:

- final Axis0
- final Xi
- final flux
- full PEPS/PEPS3D dynamics or full environment contraction closure
- scale-level basin theorem
- gravity / Standard Model / Yang-Mills / Riemann physics claims

## Next Work

1. Keep enforcing the layer-local contract:

```text
one layer
one full local tool matrix
one control family
one handoff boundary
then stack upward
```

Do not debug Axis0, flux, PEPS3D, and physics in one merged run until the layer that failed has been isolated.

2. Harden the scaled L7 PEPS3D flux-bound Axis0 row:

```text
8/27/64 sampled shells
-> held-out asymmetric shapes
-> alternate boundary samplers
-> wrong-target scrambles
-> derive the next calibration and sampler rules
```

Current status:

- calibration ablation: done; calibration is load-bearing.
- held-out shape stress: done; shape-agnostic current calibration is killed.
- boundary-sampler stress: done; sampled-boundary sign invariance is killed.
- target-scramble controls: done; target choice is load-bearing but not uniquely derived.
- runtime-record binding gate: done; enriched runtime records exist, but raw PEPS3D rows remain too shallow for runtime claims.
- boundary-functional invariance: done; all-boundary helps but does not close sampler or shape invariance.
- calibration-rule derivation blocker: done; the simple beta rule family is killed.
- runtime-bound loop4: done; runtime binding changes flux but exposes new Axis0 sign failures.
- coordinate-face boundary functional: done; axis-pair dependence is measured and six-face held-out homeostasis still fails.
- runtime-cardinality calibration gate: done; source homeostasis passes but held-out `3x3x4` kills complete calibration closure; constants are not derived.

Next L7 work should be one of:

- derive a calibration update rule from runtime-record cardinalities or boundary-functional structure, then test it on held-out shapes without refitting;
- bind the next PEPS3D flux-bound Axis0 row to the enriched runtime records while preserving the source-sign failures as graveyard evidence.

3. Build Xi-history:

```text
engine schedule history -> finite process POVM / quantum comb -> rho_AB -> Phi0
```

Required controls:

- history-erased
- suffix-erased
- order-scrambled
- terrain-erased
- type-swap
- tensor-carrier

4. Build shell-weighted Phi0:

```text
Phi_shell = sum_r w_r I_c(A_r -> B_r)
```

Required controls:

- shell-shuffled
- weight-shuffled
- terrain-erased
- carrier-swapped
- product-state
- type-swap

5. Continue MPS Stinespring/process-history toward process tensor closure:

```text
8/16/32/64 MPS shell response
-> explicit finite Kraus/effect branch weights
-> Stinespring ancilla sites
-> process tensor / quantum comb history
-> rho_AB cut-state bridge
```

This is the current bridge from the Axis0 draft docs into scalable carriers. The MPS Kraus/effect branch row and Stinespring/history-ancilla row are now present; process-tensor closure is not.

6. Upgrade PEPS/PEPS3D dynamics:

Bottom-up, not top-down:

```text
finite effect laws
-> local spinor sites
-> local terrain update
-> nearest-neighbor noncommuting gate
-> finite boundary/cut readout
-> PEPS/PEPS3D contraction receipt
```

Do not call PEPS3D complete until it has dynamics, controls, and bounded contraction receipts beyond tiny-grid first rungs. The stricter next gate should require real environment contraction receipts, not local tensor signatures: contractor/path metadata, width/cost, sampled site/edge reductions, trace/PSD/normalization checks, dense-ban fields, and control rows.

7. Keep physics model exploratory until the above pass:

The entropy-knot / matter-bubble / left-right engine asymmetry ideas should be translated into finite spinor/quaternion/process-history math before any Standard Model or gravity claim is treated as more than a scout.

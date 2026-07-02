# INFORMAL → FORMAL chained handoff — iter_312 through iter_321

Date: 2026-05-25
Author: Claude (informal sidequest thread)
Lane: `system_v5/grok_sim/` only. Not formal-lane evidence.

All ten iters carry: `claim_ceiling = side_quest_only`, `promotion_allowed = false`, `evidence_allowed = false`, `evidence_allowed_for_formal = false`. No writes outside `system_v5/grok_sim/`. The earlier `INFORMAL_TO_FORMAL_HANDOFF_iter_312_318_chain.md` covers iter_312–318; this doc supersedes it for the ten-iter chain.

---

## 1. What ran

Ten chained torch-native iters under `system_v5/grok_sim/iters/`. Each writes its own result JSON in `system_v5/grok_sim/results/`. Total wall time across all ten: under 4 seconds on the codex-ratchet env.

| Iter | Subject | strict_scientific_pass | Wall time |
|---|---|:---:|---:|
| iter_312 | end-to-end manifold-ratchet prototype | True | ~0.05 s |
| iter_313 | seed-sweep robustness (288 runs) | False | ~1.1 s |
| iter_314 | bond-link cross-cell channel + 3 controls | True | ~0.04 s |
| iter_315 | quaternion shell map + invariant + 3 controls | False | ~0.03 s |
| iter_316 | control-stress / Popper closure | True | ~0.03 s |
| iter_317 | 400-seed L/R region heatmap | True | ~0.07 s |
| iter_318 | 8-site PEPS3D exact dense full lattice | True | ~0.11 s |
| iter_319 | corruption-coverage sweep (5 controls × 8 corruptions) | False | ~0.06 s |
| iter_320 | 64-cell × bond-link integrated schedule | True | ~1.13 s |
| iter_321 | η-stratified q-change probe (200 seeds) | False | ~0.06 s |

Six pass strictly; four register an honest fail. None of the "False" outcomes is a crash or a smuggled threshold — each records a real finding the formal lane should know.

---

## 2. What worked

The chain holds together as a real exploratory artifact across three new follow-up dimensions.

**iter_319 corruption-coverage sweep.** Mean true-positive rate 0.935 across the five iter_314/315 controls. q-erased, scalar-only, and fixed-axis controls each catch 100% of the multi-shell axis-varying corruption families tested. ZZ-bonds catches 88% (one corruption family — substituting ZX for ZZ at v,w — happens to commute by structure). Per-site-only catches 80% (a YY-bond corruption on (0,1) happens to commute with the SY single-site on site 1 because the shared site's Y commutes with itself). Three controls are TNR-perfect: every baseline case I marked "should pass" did pass. Two controls had baseline-labeling errors I made (cases I called "shouldn't fail" that actually fail correctly because my labeling missed group structure). Those false-positive baselines are NOT control failures; they are my own mislabelings.

**iter_320 integrated 64-cell × bond-link schedule.** 64 single-site operator channels and 64 XY bond unitaries woven alternately on the 2×2×2 lattice. All 6 gates pass: final min site purity 0.534 (strong entanglement growth from initial product state), neighbor correlation 0.374 vs diagonal 0.082 (4.6× ratio, lattice geometry persistent), forward-vs-reverse schedule N01 = 1.41 (schedule order matters substantially), schedule vs bond-only fingerprint difference 1.41 (cells contribute distinct structure beyond bonds), global trace and purity preserved to 1e-9 (unitary closure intact).

**iter_321 η-stratified q-change probe — falsified my prediction.** I predicted, from iter_317's L/R structural-ratio heatmap, that pole bands (η near 0 or π/2) would show larger q-change under Ni-L terrain than mid-eta bands (η near π/4). The opposite is true: mean q-change is 0.0075 in band 1 (η in [π/8, π/4]) but only 0.0038–0.0045 in the two pole bands. The pole/mid ratio is 0.59. This is a real research finding: **L/R structural ratio dominance and single-channel q-rotation measure different things**. The L/R structural ratio is about how differently the two sheets' channels act on ρ; the q-change is about how much the Bloch direction rotates under one channel action. At the polarization extremes (Bloch z = ±1), σ₋ dissipates ρ substantially but the Bloch direction is degenerate so q (which encodes direction) barely changes.

**iter_312 through iter_318** still stand as in the previous chained handoff: end-to-end manifold-ratchet chain at smoke scale with seed-robustness sweep, bond-link channels with controls, quaternion shell map with controls, control-stress test, L/R seed-region heatmap, and 8-site exact dense lattice. See `INFORMAL_TO_FORMAL_HANDOFF_iter_312_318_chain.md` for those details.

---

## 3. What failed (honestly)

**iter_313 — L/R constant-ratio falsified.** Range 1.06–2.12 across 24 seeds; structural advantage is region-dependent.

**iter_315 — q-change threshold borderline.** Min 8e-4 at one of 16 seeds; threshold was 1e-3.

**iter_319 — coverage-sweep TNR imperfect for two controls.** Per-site-only and fixed-axis controls have one baseline case each that I labeled "should pass" but the control caught (because the case actually does break structure that I missed). This is mislabeling on my side, not a control deficiency. TPR remains 80% and 100% respectively.

**iter_321 — pole-vs-mid prediction falsified.** Mid-eta bands have higher q-change than pole bands. Identifies that the iter_317 L/R-ratio heatmap and the iter_315 q-change probe measure different things. The smallest q-change globally (3e-4 at η=0.162) is well below the iter_315 1e-3 threshold, confirming the threshold cuts through real seed-dependent variation rather than recording a hardware noise floor.

None of these failures is a crash or a smuggled threshold.

---

## 4. What is likely fake / scaffold

Aggregated across all ten iters:

- **PEPS3D environment is exact dense at 2×2×2 only.** iter_318 and iter_320 do full multi-bond lattice evolution at 256-dim state. No boundary-MPS at finite χ is performed anywhere.
- **Pauli appears as adapter chart throughout.** SX/SY/SZ/σ₋/σ₊ are effect-builders and operator-generator chart. ρ derives from ψ (the spinor formula); no iter uses Bloch as the root.
- **Quaternion construction reconstructed from Bloch.** iter_315 and iter_321 build q from ρ's Bloch decomposition. The Bloch step is adapter; the quaternion lives in Im(H) under Hamilton products. Formal lane needs an intrinsic ψ → H map.
- **iter_320 skips true Lindblad-on-lattice lift.** The iter applies only the operator_channel (single-site unitary) part of each cell; the terrain Lindblad step is NOT lifted to the full lattice state because that would require its Kraus representation. Labeled S4 in the iter's shortcuts.
- **Cell-to-site and bond-to-edge mappings are modulo-based** in iter_320. The engine schedule generator that derives `cell → site → bond` is not built; mod-by-8 / mod-by-12 is a stand-in.
- **iter_319 expected-fail labels were wrong on two cases.** One YY-bond case and one 180°-axis-flip case. These are mislabelings of my own design, not control issues. The controls themselves correctly catch the structure those cases break.
- **iter_321 reveals my iter_317 → iter_321 transfer was wrong.** I assumed the L/R structural-ratio heatmap structure would predict the q-change distribution. It does not. Two different probes, two different structures.

---

## 5. Best formal reproduction targets (consolidated for ten-iter chain)

Each row is a *reproduction prompt* for the formal lane. Seven fields per row.

### Target T1 — finite probe quotient as CPTP-invariant equivalence
(unchanged from iter_312_318 chain)

### Target T2 — Hopf horizontality on density-visibility metric
(unchanged)

### Target T3 — L/R structural-ratio MAP with geometric structure
(unchanged; iter_317 still the primary source)

### Target T4 — bond-link N01 witness on PEPS3D
(unchanged; iter_318 and iter_314 sources)

### Target T5 — quaternion shell map specification
(unchanged; iter_315 / iter_316 sources)

### Target T6 — first-order Trotter N01 scaling
(unchanged)

### Target T7 — BCH θ² scaling for bond-link N01
(unchanged)

### Target T8 — lattice distance correlation structure on PEPS3D
(unchanged; iter_318 source)

### Target T9 — Popper-real controls, multi-corruption coverage
(updated with iter_319 coverage data)

| Field | Value |
|---|---|
| candidate map | "for each control, the fraction of structurally-distinct corruption families it catches" |
| domain | (control, corruption-family) pairs |
| codomain | binary catch / no-catch per pair, aggregated to TPR per control |
| control needed | corruption families designed to break SHARED structure (not single-site / single-shell), plus baseline cases that should NOT trigger |
| why interesting | iter_319 measures mean TPR 0.935 across 5 controls. q-erased, scalar-only, fixed-axis at 100%; ZZ-bonds at 88%; per-site-only at 80%. Two non-perfect cases trace to specific group-structure coincidences (YY corruption commuting with SY single-site; ZX corruption commuting with ZZ on shared Z-component) |
| why not evidence yet | 8-9 corruption families per control; not exhaustive. Formal lane needs a corruption-family taxonomy plus per-family coverage map |

### Target T10 — integrated 64-cell × bond-link schedule (NEW from iter_320)

| Field | Value |
|---|---|
| candidate map | `(cell_sequence, bond_sequence) → final ρ_full_lattice` |
| domain | 64-cell sequence + 64-bond sequence on 8-site lattice |
| codomain | 256-dim density (full lattice state) plus per-site reduced densities |
| control needed | per-site-only baseline (no bonds; entanglement = 0); bond-only baseline (no cells; bonds alone produce baseline correlation); schedule-reverse (forward vs reverse final state) |
| why interesting | iter_320 measures final min site purity 0.534, neighbor/diagonal correlation ratio 4.6, forward-vs-reverse N01 1.41, schedule-vs-bond-only fingerprint diff 1.41. Lattice geometry persists through 128 unitary steps; schedule order matters substantially; cells contribute distinct structure |
| why not evidence yet | dense 256-dim only; cell→site and bond→edge mappings are modulo-based, not from an engine schedule generator; terrain Lindblad lift is skipped (operator_channel only). Formal lane should derive the routing from the engine schedule per ENGINE_64_SCHEDULE_ATLAS and lift terrain Lindblad to full state via Kraus representation |

### Target T11 — η-stratified single-channel q-rotation (NEW from iter_321)

| Field | Value |
|---|---|
| candidate map | `(η-band, channel) → distribution of q-change per seed` |
| domain | 4 η-bands × Ni-L channel × 50 seeds per band |
| codomain | per-band mean / min / max / std of q-change, count of below-threshold seeds |
| control needed | the bands themselves are stratification; cross-reference with rho-change to separate Bloch-direction effects from purity effects |
| why interesting | **iter_321 falsifies the simple prediction that iter_317's L/R-region structure predicts iter_315's q-change structure.** Pole bands have smaller mean q-change than mid-eta bands. The L/R structural ratio measures sheet asymmetry; the q-change measures single-channel Bloch-direction rotation. At the poles, ρ changes substantially under σ₋ but the Bloch direction is degenerate so q (which encodes direction) barely changes |
| why not evidence yet | 50 seeds per band; not statistically robust to within-band heterogeneity. Formal lane should map both the L/R sheet asymmetry AND the per-sheet Bloch-rotation magnitudes as separate (η, χ) maps, NOT assume one predicts the other |

---

## 6. Formal blockers that remain

After ten iters, the substrate gate flags are unchanged:

```
foundation_closed = false
peps3d_from_start_required = true
substage_cell_embedding_proven = false
quaternion_layer_closed = false
flux_queue_allowed = false
axis0_queue_allowed = false
shell_boundary_geometry_present = false

peps3d_full_environment_closed = (true at 2x2x2 only)
peps3d_boundary_mps_at_finite_chi = false
```

What remains for the formal lane:

- **Boundary-MPS at finite χ.** All exact dense work here is at 2×2×2. Lift bond-link N01 and lattice correlations and the 64-cell schedule to a larger lattice with boundary-MPS at χ ≥ 4.
- **Terrain Lindblad lift to full lattice.** iter_320 skipped this; needs Kraus representation of `X_terrain(τ, s)` lifted to single-site channel on the 8-qubit state.
- **Quaternion intrinsic-to-ψ map.** Build q_shell(v, k, ψ_v) without going through Bloch components.
- **Shell-index lattice geometry.** Replace linear k ∈ {0, 1, 2} with a finite shell-index lattice anchored to PEPS sites.
- **Engine schedule routing generator.** Derive `cell → site → bond` from the engine schedule per ENGINE_64_SCHEDULE_ATLAS, not modulo.
- **L/R seed-region analytic theory.** Derive WHY structural advantage lives at polarization extremes (probably σ₋/σ₊ asymmetry on |0⟩ vs |1⟩).
- **Two-probe map separation.** iter_321 establishes that L/R structural-ratio and q-change-under-channel are distinct probes; formal lane should map both and document the relationship rather than conflating them.

---

## 7. Exact files written this session

```text
system_v5/grok_sim/iters/iter_312_claude_informal_manifold_ratchet.py
system_v5/grok_sim/iters/iter_313_claude_seed_sweep_robustness.py
system_v5/grok_sim/iters/iter_314_claude_bond_link_cross_cell_channel.py
system_v5/grok_sim/iters/iter_315_claude_quaternion_shell_map_invariant.py
system_v5/grok_sim/iters/iter_316_claude_control_stress_popper_closure.py
system_v5/grok_sim/iters/iter_317_claude_seed_region_LR_map.py
system_v5/grok_sim/iters/iter_318_claude_8site_peps3d_exact_dense.py
system_v5/grok_sim/iters/iter_319_claude_corruption_coverage_sweep.py
system_v5/grok_sim/iters/iter_320_claude_64cell_bondlink_schedule.py
system_v5/grok_sim/iters/iter_321_claude_eta_stratified_q_change.py

system_v5/grok_sim/results/iter_312_claude_informal_manifold_ratchet_results.json
system_v5/grok_sim/results/iter_313_claude_seed_sweep_robustness_results.json
system_v5/grok_sim/results/iter_314_claude_bond_link_cross_cell_channel_results.json
system_v5/grok_sim/results/iter_315_claude_quaternion_shell_map_invariant_results.json
system_v5/grok_sim/results/iter_316_claude_control_stress_popper_closure_results.json
system_v5/grok_sim/results/iter_317_claude_seed_region_LR_map_results.json
system_v5/grok_sim/results/iter_318_claude_8site_peps3d_exact_dense_results.json
system_v5/grok_sim/results/iter_319_claude_corruption_coverage_sweep_results.json
system_v5/grok_sim/results/iter_320_claude_64cell_bondlink_schedule_results.json
system_v5/grok_sim/results/iter_321_claude_eta_stratified_q_change_results.json

system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312.md
system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312_315_chain.md
system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312_318_chain.md
system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312_321_chain.md   (this file)
```

No writes to `system_v5/ops/formal_scouts/`, `system_v5/docs/`, `system_v5/evidence/`, or any formal classifier / index. All ten result JSONs use sidequest-local vocabulary; no formal-scout stamps anywhere; banned-vocabulary check came back clean.

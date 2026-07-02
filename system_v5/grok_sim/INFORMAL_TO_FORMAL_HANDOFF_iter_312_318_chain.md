# INFORMAL → FORMAL chained handoff — iter_312 through iter_318

Date: 2026-05-25
Author: Claude (informal sidequest thread)
Lane: `system_v5/grok_sim/` only. Not formal-lane evidence.

All seven iters carry: `claim_ceiling = side_quest_only`, `promotion_allowed = false`, `evidence_allowed = false`, `evidence_allowed_for_formal = false`. No writes outside `system_v5/grok_sim/`. The earlier `INFORMAL_TO_FORMAL_HANDOFF_iter_312_315_chain.md` covers iter_312–315; this doc supersedes it for the seven-iter chain.

---

## 1. What ran

Seven chained torch-native iters under `system_v5/grok_sim/iters/`. Each writes its own result JSON in `system_v5/grok_sim/results/`. Total wall time across all seven: under 2.5 seconds on the codex-ratchet env.

| Iter | Subject | strict_scientific_pass | Wall time |
|---|---|:---:|---:|
| iter_312 | end-to-end manifold-ratchet prototype | True | ~0.05 s |
| iter_313 | seed-sweep robustness (24 × 4 × 3 = 288 runs) | False | ~1.1 s |
| iter_314 | bond-link cross-cell channel + controls | True | ~0.04 s |
| iter_315 | quaternion shell map + invariant + controls | False | ~0.03 s |
| iter_316 | control-stress / Popper closure for iter_314+315 | True | ~0.03 s |
| iter_317 | 400-seed L/R structural-ratio region heatmap | True | ~0.07 s |
| iter_318 | 8-site PEPS3D exact dense full-lattice contraction | True | ~0.11 s |

Two of seven are False, by honest reporting. iter_313 falsifies the iter_312 single-seed constant-ratio claim. iter_315 records one borderline gate value at the chosen threshold. iter_316 then closes the open Popper falsifier from the iter_312–315 chain.

---

## 2. What worked

The chain stands together as a real exploratory artifact. The pieces that hold up under wide variation, controls, and Popper-style corruption tests:

**Spinor / Hopf carrier (iter_312, iter_313).** The spinor formula `ψ_s(φ, χ; η)` and its derived `ρ = ψψ†` give clean Hopf horizontality at machine ε for the inner loop and ~0.85 traversal for the outer loop, robust across all 24 seeds of the seed sweep. `A_Hopf(Y_out) = 0` by computed horizontality. F01 finite-probe quotient distinguishes 100% of seed configurations under the full 6-effect family and collapses to numerical zero under the z-axis truncation.

**Bond-link channel and controls (iter_314, iter_316).** XY bond unitary on (u,v) and (v,w) sharing site v produces a real reduced-density N01 witness at v. ZZ-bonds-commute control = 0 to machine ε; disjoint-single-site-unitary control = 0 to machine ε; both controls survive Popper-style corruption (iter_316: corrupted ZZ→XZ produces real witness, corrupted disjoint→2-site V_u sharing v produces real witness). BCH θ² scaling slope = 1.94, within 50% of theoretical 2.0.

**Quaternion shell map (iter_315, iter_316).** Hamilton-product baseline `|ij − ji| = 2` exact. Unit quaternion norm preserved at every (seed, shell) within 1e-9. Axis-varying shell-order witness has mean 1.22, min 0.58 across 16 seeds. Three structural controls collapse: q-erased = 0 exact, scalar-only ≈ 1e-16, fixed-axis ≈ 3e-16. Crucially, iter_316 confirmed all three controls survive corruption: q-erased corrupted with axis-varying inserts at multiple shells produces real witness; scalar-only corrupted with non-scalar components at two shells produces real witness; fixed-axis corrupted to axis-varying matches iter_315's axis-varying probe. The map specifies what it CHANGES (q before/after Ni-L terrain, mean change 6.4e-3), what it PRESERVES (unit norm), and what it FORBIDS (fixed-axis and scalar-only and erased q families cannot witness shell-order noncommutativity).

**L/R structural-ratio seed-region map (iter_317).** 400 Halton seeds binned into an 8×8 (η, 2χ) heatmap reveal a clean geometric structure: structural-channel dominance (mean ratio > 1.8) concentrates in 17 bins at η near 0 or π/2 (the spinor-polarization extremes), while two bins at mid-η (near π/4) show collapse to ~1.2. Global mean 1.75, std 2.48; global min 0.90, global max 48 (single-bin extreme where sign-flip diff is near zero). The iter_313 falsification is reproduced at higher density and now has a geometric explanation: the σ_-/σ_+ structural advantage maximizes when ρ is concentrated near a polarization extreme, not in a balanced state.

**8-site PEPS3D exact dense (iter_318).** 2×2×2 = 8-site lattice as a 256-dim state vector. Twelve XY bond unitaries applied across all lattice edges. Global purity preserved at 1.0 within 1e-9 (unitary closure). All 8 sites become mixed after the bond layer (per-site purity 0.945–0.965). Nearest-neighbor reduced pair correlation = 0.080; diagonal-corner reduced pair = 0.065 — neighbors are more correlated than diagonals, so lattice geometry IS present in the receipt. Bond-link N01 witness at site 0 between two overlapping bonds = 0.019; non-overlapping-bond control = 3e-17 (machine ε). At this scale, exact dense IS the full PEPS3D environment — honestly labeled.

---

## 3. What failed (honestly)

**iter_313 — L/R structural ratio is not a constant.** The iter_312 single-seed "structural difference is ~2× sign-flip" reading is falsified. Across 24 Halton seeds the ratio ranges 1.06–2.12. iter_317 reproduces this at 400 seeds and identifies the geometric structure: structural advantage lives near η = 0 and η = π/2, collapses near η = π/4.

**iter_315 — q-change-under-Ni-L-terrain threshold.** Min observed change = 8e-4 across 16 seeds; my threshold was 1e-3. The structural claims of the iter (axis variation required, controls collapse, unit norm preserved) are unaffected and pass strictly. Left as is per the no-author-also-writes-threshold discipline.

**Nothing else fails.** Even the seven-iter chain produces a strict_scientific_pass = True on five of seven iters with controls and corruption tests holding throughout.

---

## 4. What is likely fake / scaffold

Each iter lists its own `shortcuts_labeled`. The aggregate:

- **PEPS3D environment contraction is exact dense at 2×2×2 only.** iter_318 is the only iter that does full multi-bond lattice evolution, and it uses dense 256-dim state. No boundary-MPS at finite χ is performed in any iter. The `peps3d_boundary_mps_at_finite_chi` gate stays false.
- **Pauli appears as adapter chart throughout.** SX/SY/SZ/σ₋/σ₊ are effect-builders and operator-generator chart. ρ derives from ψ (spinor formula); no iter uses Bloch components as the root state. iter_315's quaternion is reconstructed from Bloch — adapter — not from an intrinsic ψ → H map.
- **64-cell × bond-link integration not exercised.** iter_312's 64 single-site cells and iter_314/318's bond-link channels live in separate iters. No iter runs the 64-cell schedule WITH bond-link Φ_(u,v) channels woven in.
- **Initial states are product / factorizable.** iter_312, iter_314, iter_318 all start from product spinor states. The full chain has not been tested on a pre-entangled initial state.
- **iter_316 v1 corruption diagnostics surface a real group-theory point.** Two of the five v1 corruption attempts in iter_316 still passed the "control" because of group structure (single-axis insertions still commute; single-shell scalar insertions still commute). The required v2 corruptions break SHARED structure across multiple shells. This is an epistemic finding about WHAT the controls actually test — the controls are NOT just trivially-passing-by-math, but they require multi-shell axis variation to be broken.
- **No engine schedule yet.** iter_312 enumerates 64 cells; no iter executes a temporally-ordered engine schedule over those cells with terrain/loop/operator transitions across the lattice.

---

## 5. Best formal reproduction targets (updated for seven-iter chain)

Each row is a *prompt* for the formal lane to rebuild from source docs, not an established result. Seven fields per row.

### Target T1 — finite probe quotient as CPTP-invariant equivalence

| Field | Value |
|---|---|
| candidate map | `Q_P : S → S/~_P` with `s ~_P t iff p(s) = p(t)` for all `p ∈ P` |
| domain | finite admissible state set on torch-native d=2 site carrier |
| codomain | quotient set of finite cardinality |
| control needed | truncated probe family (iter_312/313 use z-axis pair); CPTP-equivalent state stress; gauge-relabel |
| why interesting | iter_313 confirmed the quotient holds at 100% of 288 (seed, dt, n_steps) combinations |
| why not evidence yet | single-qubit only; no finite-state ensemble; no CPTP-stability test |

### Target T2 — Hopf horizontality on density-visibility metric

| Field | Value |
|---|---|
| candidate map | `(ψ_s, Y_field) → max_u ‖ρ(u) − ρ(0)‖` along Y_in or Y_out |
| domain | spinor `ψ_s(φ,χ;η)` at fixed (φ₀,χ₀,η₀) |
| codomain | non-negative real |
| control needed | shell-erase, Hopf-flat connection, a third Y-field that is neither vertical nor horizontal |
| why interesting | inner stays at float64 noise floor at 100% of seeds; outer ≈ 0.85; `A_Hopf(Y_out) = 0` by construction |
| why not evidence yet | no PEPS3D anchor; the formal lane must show this on a finite PEPS3D-carried section, not a free C² |

### Target T3 — L/R sheet structural-ratio MAP (with geometric structure)

| Field | Value |
|---|---|
| candidate map | `(η, χ) → ratio = ‖X_Ni_L(ρ) − X_Ni_R(ρ)‖ / ‖X_Ni_signflip_L(ρ) − X_Ni_signflip_R(ρ)‖` |
| domain | (η, χ) on a finite grid in [0, π/2] × [0, π] (using 2χ mod π) |
| codomain | non-negative real ratio |
| control needed | sign-flip-only baseline (iter_312/317); seed-region binning (iter_317); per-region purity check |
| why interesting | **iter_313 and iter_317 falsify the constant-ratio reading.** iter_317 identifies a clean geometric structure: structural advantage peaks at η near 0 and π/2 (polarization extremes), collapses near η = π/4. 17 dominant bins, 2 collapsed bins in the 8×8 grid |
| why not evidence yet | sidequest with 400 seeds; the formal lane should derive the structure analytically (probably from the σ_-/σ_+ action on |0⟩ vs |1⟩ being asymmetric) and verify against CPTP equivalent of the map |

### Target T4 — bond-link N01 witness on PEPS3D, exact-vs-MPS

| Field | Value |
|---|---|
| candidate map | `(c_A, c_B) → ‖r_P(Φ_{c_A} ∘ Φ_{c_B}(ρ)) − r_P(Φ_{c_B} ∘ Φ_{c_A}(ρ))‖` for bonds sharing or not sharing a site |
| domain | pairs of bond channels on adjacent edges, anywhere in the PEPS3D lattice |
| codomain | non-negative real |
| control needed | iter_314 has three (ZZ-commute, disjoint-commute, BCH θ²); iter_316 corrupts them; iter_318 has lattice-overlap-vs-not on 2×2×2 |
| why interesting | iter_314 establishes the witness at 3-site dense. iter_318 lifts it to 8-site full-lattice with all 12 edges. Bond-link N01 at shared site 0 = 0.019; non-overlap control = 3e-17 (machine ε). All three controls survive iter_316 corruption stress. **Now needs lifting to boundary-MPS at χ ≥ 4** so it scales beyond 2×2×2 |
| why not evidence yet | 2×2×2 only; no boundary-MPS at finite χ; uniform θ across edges; no integration with engine schedule |

### Target T5 — quaternion shell map: changes / preserves / forbids

| Field | Value |
|---|---|
| candidate map | `q_shell(v, k, ψ_v) ∈ H_1` with Hamilton-product shell-order witness ‖Q_forward − Q_reverse‖ |
| domain | per-site spinor data + finite shell index k |
| codomain | unit quaternion + non-negative noncommutation witness |
| control needed | q-erased, scalar-only, fixed-axis families (iter_315 implements all three; iter_316 corrupts all three) |
| why interesting | iter_315 specifies exactly what the map does (changes q post-terrain, preserves unit norm, forbids fixed-axis / scalar-only / erased q families). iter_316 confirms via corruption that controls are real epistemic tests |
| why not evidence yet | q reconstructed from Bloch (adapter); no PEPS anchor for k; no terrain-coupled q dynamics; the formal lane must build q_shell as an intrinsic ψ → H map and evolve it under terrain channels, not reconstruct it from ρ |

### Target T6 — first-order Trotter N01 scaling

| Field | Value |
|---|---|
| candidate map | `dt → N01_witness(seed, terrain_pair, dt, n_steps)` |
| domain | non-commuting terrain pair (Se, Ne) on sheet L |
| codomain | non-negative real |
| control needed | commuting-pair, higher-order integrator comparison |
| why interesting | iter_313 log-log slope = 0.895 (within 50% of 1.0); first-order Euler scaling shape matches expectation |
| why not evidence yet | single seed at 4 dt values; needs population averaging and higher-order integrator |

### Target T7 — BCH θ² scaling for bond-link N01

| Field | Value |
|---|---|
| candidate map | `θ → N01_full_state(U_(u,v)(θ), U_(v,w)(θ))` |
| domain | bond coupling strength θ |
| codomain | non-negative real |
| control needed | commuting-bond, large-θ regime |
| why interesting | iter_314 log-log slope = 1.94 (within 50% of theoretical 2.0) |
| why not evidence yet | sidequest with 4 θ values, single bond pair |

### Target T8 — lattice distance correlation structure on PEPS3D

| Field | Value |
|---|---|
| candidate map | `(site_pair) → ‖ρ_pair − ρ_marg1 ⊗ ρ_marg2‖` |
| domain | pairs of sites at varying lattice distance |
| codomain | non-negative real (deviation from product) |
| control needed | iter_318 shows neighbor (0.080) vs diagonal (0.065); needs intermediate-distance pairs and bond-strength variation |
| why interesting | iter_318 verifies lattice geometry is present in the receipt: neighbors are more correlated than diagonal corners after a uniform bond layer. This is a real lattice-distance signature, not a labelled one |
| why not evidence yet | 2×2×2 only; uniform θ; one bond pattern; the formal lane should map distance-vs-correlation at larger lattice with boundary-MPS |

### Target T9 — Popper-real controls (epistemic test discipline)

| Field | Value |
|---|---|
| candidate map | "control X claims to fail when structure Y is broken" |
| domain | each named control in iter_314 and iter_315 |
| codomain | binary: corrupted-control fails the gate or not |
| control needed | the corruption itself, designed to break SHARED structure (not just single-site/single-shell) |
| why interesting | iter_316 confirms all 5 controls real. v1 corruptions surfaced a real subtlety: single-axis or single-shell insertions still commute by group structure, so the corruption must break multi-shell shared structure to actually fail the gate |
| why not evidence yet | only the iter_314/315 controls; the formal lane should adopt this discipline for every control it introduces |

---

## 6. Formal blockers that remain

After seven iters, the substrate gate flags stand as:

```
foundation_closed = false
peps3d_from_start_required = true
substage_cell_embedding_proven = false
quaternion_layer_closed = false
flux_queue_allowed = false
axis0_queue_allowed = false
shell_boundary_geometry_present = false

peps3d_full_environment_closed = (true at 2x2x2 only; false at finite chi)
peps3d_boundary_mps_at_finite_chi = false
```

What the formal lane still has to build before flux can be queued:

- **Boundary-MPS at finite χ.** iter_318 has full 2×2×2 dense; the next step is lifting bond-link N01 and lattice correlations to a larger lattice (e.g., 2×2×4 or 4×4×4) with boundary-MPS contraction at χ ≥ 4.
- **64-cell × bond-link integrated schedule.** iter_312's 64 single-site cells, iter_314's bond-link channels, and iter_318's lattice all live in separate iters. The formal-lane target is a single sim that traverses 64 cells WITH bond-link Φ_(u,v) actions woven in.
- **Quaternion-as-intrinsic-spinor-property map.** iter_315 reconstructs q from Bloch (adapter). The formal lane needs a map directly from ψ ∈ S³ to a quaternion attached to a PEPS site without going through Bloch components, plus a quaternion dynamic under terrain channels.
- **Shell-index lattice geometry.** iter_315 uses k ∈ {0,1,2} as a linear index. Nested-Hopf-tori shells require a finite shell-index lattice anchored to PEPS sites, with nesting/projection maps.
- **Seed-region analytic theory.** iter_317 identifies WHERE the L/R structural advantage lives; the formal lane should derive WHY (probably σ_-/σ_+ asymmetry on |0⟩ vs |1⟩) and verify the geometric structure holds under CPTP equivalence.
- **Terrain channel integration with bond-link.** iter_312 has terrain channels; iter_314/318 have bond-link unitaries. A single iter combining `(terrain Lindblad step) ∘ (bond-link channel)` would test whether terrain dynamics and bond-link entanglement growth interact constructively or destructively.

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

system_v5/grok_sim/results/iter_312_claude_informal_manifold_ratchet_results.json
system_v5/grok_sim/results/iter_313_claude_seed_sweep_robustness_results.json
system_v5/grok_sim/results/iter_314_claude_bond_link_cross_cell_channel_results.json
system_v5/grok_sim/results/iter_315_claude_quaternion_shell_map_invariant_results.json
system_v5/grok_sim/results/iter_316_claude_control_stress_popper_closure_results.json
system_v5/grok_sim/results/iter_317_claude_seed_region_LR_map_results.json
system_v5/grok_sim/results/iter_318_claude_8site_peps3d_exact_dense_results.json

system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312.md
system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312_315_chain.md
system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312_318_chain.md   (this file)
```

No writes to `system_v5/ops/formal_scouts/`, `system_v5/docs/`, `system_v5/evidence/`, or any formal classifier / index. All seven result JSONs use sidequest-local vocabulary. No formal-scout stamps anywhere.

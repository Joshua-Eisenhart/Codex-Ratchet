# INFORMAL → FORMAL chained handoff — iter_312 through iter_315

Date: 2026-05-25
Author: Claude (informal sidequest thread)
Lane: `system_v5/grok_sim/` only. Not formal-lane evidence.

All four iters carry: `claim_ceiling = side_quest_only`, `promotion_allowed = false`, `evidence_allowed = false`, `evidence_allowed_for_formal = false`. No writes outside `system_v5/grok_sim/`. The earlier `INFORMAL_TO_FORMAL_HANDOFF_iter_312.md` covers iter_312 alone; this doc supersedes it for the four-iter chain.

---

## 1. What ran

Four chained torch-native iters under `system_v5/grok_sim/iters/`. Each writes its own result JSON in `system_v5/grok_sim/results/`. Total wall time across all four: well under 2 seconds on the codex-ratchet env.

| Iter | Subject | strict_scientific_pass | Wall time |
|---|---|:---:|---:|
| iter_312 | end-to-end manifold-ratchet prototype | True | ~0.05 s |
| iter_313 | seed sweep robustness (24 × 4 × 3 = 288 runs) | False | ~1.1 s |
| iter_314 | bond-link cross-cell channel + controls | True | ~0.04 s |
| iter_315 | quaternion shell map + invariant + controls | False | ~0.03 s |

The two False results are honest. iter_313 falsifies a single-seed claim from iter_312. iter_315 reports a borderline gate value rather than smoothing it; the structural claims of iter_315 hold.

---

## 2. What worked

**iter_312 end-to-end chain.** Real spinor formula ψ_s(φ,χ;η), real density ρ = ψψ†, Hopf horizontality `A_Hopf(Y_out) = 0` computed analytically and to machine ε in the density-visibility test, 8 terrain generators with σ₋/σ₊ structural difference on Ni, 16 placements with non-zero local action, 64 cells with per-cell local channel and a cross-cell N01 witness of 0.16. POVM completeness exact (cube-vertex frame).

**iter_313 seed-sweep.** 24 Halton-sequence seeds across (φ, χ, η), 4 dt values {0.01, 0.025, 0.05, 0.10}, 3 n_steps values {3, 6, 12} = 288 runs. F01 quotient passes 100% of seeds, Hopf inner/outer pass 100% of seeds, N01 dt-scaling log-log slope = 0.895 (close to the 1.0 first-order-Trotter expectation, within 50%). The sweep itself ran in ~1.1 s.

**iter_314 bond-link channel.** Real torch-native bond unitary `U_(u,v) = exp(-iθ H_uv)` with `H_uv = σ_x⊗σ_x + σ_y⊗σ_y`, applied to a 3-site product state, partial-traced to per-site reduced density. The bond-link N01 witness at the shared site v is real and large. The two controls collapse strictly: (i) ZZ bonds analytically commute on the shared site (full-state N01 = 0 to machine ε), (ii) disjoint single-site unitaries commute trivially (full-state N01 = 0 to machine ε). BCH θ² scaling slope = 1.94, within 50% of the expected 2.0.

**iter_315 quaternion shell map.** Hamilton-product baseline `|ij − ji| = 2` exact. q_shell unit norm preserved at every (seed, shell) within 1e-9. Axis-varying shell-order witness has mean 1.22, min 0.58, across 16 seeds — robust noncommutation. Three controls collapse to machine ε or exact zero: q-erased (identity quaternion), scalar-only quaternions, and a separate fixed-axis diagnostic (which intentionally COMMUTES to identify what the map forbids).

---

## 3. What failed (honestly)

**iter_313 — L/R structural ratio is not stable across seeds.** This is the most informative finding. The iter_312 single-seed claim was that the L/R structural difference (Ni terrain σ₋ on L vs σ₊ on R) is ~2× the bare-sign-flip baseline. Across the 24 Halton seeds, the structural ratio has min 1.058, max 2.123, mean 1.365, std 0.237. At many seeds the structural channel barely beats sign-flip alone. The single-seed 2× figure was lucky positioning.

This **falsifies the strong reading of the L/R structural claim**. The weaker reading still holds: there exists a seed regime where structural ratio ≈ 2 (e.g., near the seed iter_312 originally used). The strong claim of "structural difference always exceeds sign-flip" survives only after restricting (η, φ, χ) — which the iter does not currently do.

**iter_315 — q-shell change under terrain is borderline at one seed.** The probe gate required min q-shell change above 1e-3 across all 16 seeds. Observed min = 8e-4. The mean change is 6.4e-3 and the maximum is well above 1e-3. The structural map claims (axis-varying produces witness, fixed-axis forbids it, controls collapse) all hold robustly; the borderline value is on a small-dt single-step integration, not on the structural claim itself. Receipt stays at strict_scientific_pass = False to record the borderline honestly.

---

## 4. What is likely fake / scaffold

Each iter lists its own `shortcuts_labeled` array. Aggregated:

- **PEPS3D never fully contracted.** iter_312 uses product-fixture per-site readout from 6-leg `T_v` tensors. iter_314 uses dense 3-site state (exact small contraction). iter_315 uses per-site Bloch readback. None of the four iters performs a finite-bond boundary-MPS environment contraction at χ ≥ 4.
- **No engine schedule integrated with bonds.** iter_312 runs 64 per-site cells in isolation; iter_314 runs bond-links in isolation. The 64-cell × bond-link composition is not exercised.
- **Pauli appears as adapter chart, not root.** SX/SY/SZ/σ₋/σ₊ are used as operator generators and effect-builders. ρ is read off ψ where ψ comes from the spinor formula. No iter uses Bloch components as the root state.
- **Quaternion construction is Bloch-derived.** iter_315 builds q_shell from rho's Bloch decomposition. The Bloch step is adapter; the quaternion lives in Im(H) under Hamilton products. But the spinor never directly produces a quaternion via an intrinsic map — a real formal-lane build would have the quaternion as a primary object, not Bloch-derived.
- **N01 dt-scaling expectation was wrong in iter_312 header text.** iter_313 measured slope ≈ 1.0, not 2.0. Reason: with two sequences of n Euler steps each, the leading-order witness is O(dt · n) for fixed n, linear in dt, not O(dt²). iter_313's audit uses the correct linear expectation.
- **Threshold smuggling avoided.** iter_315's failed gate (q-change min 8e-4 vs 1e-3 threshold) is left as-is rather than retro-fitting the threshold to the data, per the prior session's discipline on not authoring both the sim and its case criteria.

---

## 5. Best formal reproduction targets (updated for the four-iter chain)

Each row is a *prompt* for the formal lane to rebuild from source docs, not an established result. Seven fields per row.

### Target T1 — finite probe quotient as CPTP-invariant equivalence

| Field | Value |
|---|---|
| candidate map | `Q_P : S → S/~_P` with `s ~_P t iff p(s) = p(t)` for all `p ∈ P` |
| domain | finite admissible state set on a torch-native d=2 site carrier |
| codomain | quotient set of finite cardinality |
| control needed | truncated probe family (iter_312/313 used z-axis pair); CPTP-equivalent state stress; gauge-relabel control |
| why interesting | iter_313 confirmed the quotient holds at 100% of 288 (seed, dt, n_steps) combinations; |P| dependence is computed at 288 seeds, not stipulated |
| why not evidence yet | single-qubit only; no finite-state ensemble; no CPTP-stability test |

### Target T2 — Hopf horizontality on density-visibility metric

| Field | Value |
|---|---|
| candidate map | `(ψ_s, Y_field) → max_u ‖ρ(u) − ρ(0)‖` along Y_in or Y_out |
| domain | spinor `ψ_s(φ,χ;η)` at fixed (φ₀,χ₀,η₀) |
| codomain | non-negative real |
| control needed | shell-erase, Hopf-flat connection control, a third Y-field neither vertical nor horizontal |
| why interesting | inner stays at float64 noise floor (1.4e-16 in iter_312, 100% of seeds in iter_313); outer ≈ 0.85 at all 24 seeds; `A_Hopf(Y_out) = 0` by construction confirmed |
| why not evidence yet | smoke; no PEPS3D anchor; the formal lane must show this on a finite PEPS3D-carried spinor section |

### Target T3 — L/R sheet structural-ratio map, NOT a constant

| Field | Value |
|---|---|
| candidate map | `(τ ∈ {Ni}, s ∈ {L,R}, ρ_seed) → ratio = ‖X_Ni_L(ρ) − X_Ni_R(ρ)‖ / ‖X_Ni_sign_flip_L(ρ) − X_Ni_sign_flip_R(ρ)‖` |
| domain | sheet pairs with σ₋/σ₊ structural choice plus H_L/H_R sign flip |
| codomain | non-negative real ratio |
| control needed | sign-flip-only baseline (iter_312 has this); η/φ/χ seed sweep (iter_313 has this); seed regime classification |
| why interesting | **iter_313 falsifies the constant-ratio claim.** The structural ratio is seed-dependent: min 1.058, max 2.123, mean 1.365. Formal lane should study where in (η,φ,χ) the structural channel dominates vs. where it nearly collapses to sign-flip |
| why not evidence yet | iter_313 is sidequest with 24 seeds; the formal lane needs a denser map of (η, φ, χ) regions and a CPTP-invariant version of the ratio |

### Target T4 — bond-link N01 witness on PEPS3D environment

| Field | Value |
|---|---|
| candidate map | `(c_A, c_B) → ‖r_P(Φ_{c_A} ∘ Φ_{c_B}(ρ)) − r_P(Φ_{c_B} ∘ Φ_{c_A}(ρ))‖` for bonds touching a shared site |
| domain | pairs of bond channels on adjacent edges of the PEPS3D lattice |
| codomain | non-negative real |
| control needed | iter_314 has three: ZZ-bonds-commute analytically, disjoint single-site unitaries commute trivially, and BCH θ²-scaling fit |
| why interesting | iter_314 establishes the bond-link witness at exact small scale (3-site dense). All three controls collapse strictly. The formal lane should lift this to the 2×2×2 PEPS3D lattice with boundary-MPS contraction at χ ≥ 4 |
| why not evidence yet | dense 3-site only; no PEPS environment contraction; single dt and θ point only for the order witness |

### Target T5 — quaternion shell map with axis variation as the closure witness

| Field | Value |
|---|---|
| candidate map | `q_shell(v, k, ψ_v) ∈ H_1`, Hamilton product over shell sequence, witness = ‖Q_forward − Q_reverse‖ |
| domain | per-site spinor data + finite shell index k |
| codomain | unit quaternion plus a non-negative noncommutation witness |
| control needed | q-erased identity (witness = 0 exact); scalar-only quaternions (witness = 0 to ε); fixed-axis q-shell family (witness = 0 to ε); axis-varying family (witness > 1e-3 at every seed) |
| why interesting | iter_315 identifies the structural requirement: **axis variation across shells is what makes the quaternion layer non-trivial**. Fixed-axis quaternions, scalar-only, and erased all collapse the witness. This is exactly the "what the map changes, preserves, or forbids" specification CONSTRAINT_MANIFOLD_MATH_LEDGER sec 4 demands |
| why not evidence yet | iter_315 ran at 16 seeds, 3 shell indices, per-site only. No PEPS anchor for the shell index; no terrain coupling to q_shell evolution; q-change borderline at one seed (8e-4 vs 1e-3). The formal lane must build q_shell as an intrinsic property of the spinor carrier on a PEPS site rather than reconstructed from Bloch |

### Target T6 — N01 witness dt-scaling for terrain generators

| Field | Value |
|---|---|
| candidate map | `dt → N01_witness(seed, terrain_pair, dt, n_steps)` |
| domain | non-commuting terrain pair (Se, Ne) on sheet L |
| codomain | non-negative real, plot vs dt |
| control needed | commuting-pair (Se with itself) → witness = 0 exact; integration order test |
| why interesting | iter_313 measures log-log slope = 0.895 (close to 1.0); first-order Euler integration is correct; scaling law is computed, not assumed |
| why not evidence yet | sidequest with 4 dt values at single seed; the formal lane needs the slope across seed populations and across higher-order integrators |

### Target T7 — BCH θ² scaling for bond-link N01

| Field | Value |
|---|---|
| candidate map | `θ → N01_full_state(U_(u,v)(θ), U_(v,w)(θ))` |
| domain | bond coupling strength θ |
| codomain | non-negative real |
| control needed | commuting-bond control (ZZ); larger-θ regime (where BCH breaks down) |
| why interesting | iter_314 measures log-log slope = 1.94; matches BCH leading-order expectation of 2.0 within 50% |
| why not evidence yet | sidequest with 4 θ values, single bond pair; formal lane should run higher-order BCH validation and the breakdown threshold |

---

## 6. Formal blockers that remain

The four iters collectively flip **none** of the substrate gate flags. All carry:

```
foundation_closed = false
peps3d_from_start_required = true
substage_cell_embedding_proven = false
quaternion_layer_closed = false
flux_queue_allowed = false
axis0_queue_allowed = false
shell_boundary_geometry_present = false
peps3d_full_environment_closed = false
```

What the formal lane still has to build before flux can be queued:

- **PEPS3D environment contraction at finite bond-dim.** Boundary-MPS at χ ≥ 4, exact small-case checks, product-boundary negative control. iter_314 has dense 3-site smoke; not a real PEPS contraction.
- **64-cell × bond-link composition.** iter_312 runs 64 per-site cells, iter_314 runs bond-links, but the composition (a 64-cell schedule whose cells include bond-link Φ_(u,v) actions) is not exercised.
- **Quaternion-as-intrinsic-spinor-property map.** iter_315 reconstructs q from Bloch, which is adapter. The formal lane needs a map directly from ψ ∈ S³ to a quaternion attached to the PEPS site without going through Bloch.
- **Terrain coupling to q_shell evolution.** iter_315 measures q before and after a Lindblad terrain step but doesn't EVOLVE q_shell via a quaternionic dynamic equation. That dynamic is required before quaternion_layer_closed can be set true.
- **Shell-index lattice geometry.** iter_315 uses k ∈ {0, 1, 2} as a linear index. Real nested-Hopf-tori shells require a finite shell-index lattice anchored to PEPS sites (k_v(v) ∈ E_eta), not a free integer.
- **Seed-region map for the L/R structural ratio.** iter_313 shows the ratio ranges 1.06–2.12 across seeds; the formal lane should produce a (η, φ, χ) map of where structural and sign-flip channels diverge most.

---

## 7. Exact files written this session

```text
system_v5/grok_sim/iters/iter_312_claude_informal_manifold_ratchet.py
system_v5/grok_sim/iters/iter_313_claude_seed_sweep_robustness.py
system_v5/grok_sim/iters/iter_314_claude_bond_link_cross_cell_channel.py
system_v5/grok_sim/iters/iter_315_claude_quaternion_shell_map_invariant.py
system_v5/grok_sim/results/iter_312_claude_informal_manifold_ratchet_results.json
system_v5/grok_sim/results/iter_313_claude_seed_sweep_robustness_results.json
system_v5/grok_sim/results/iter_314_claude_bond_link_cross_cell_channel_results.json
system_v5/grok_sim/results/iter_315_claude_quaternion_shell_map_invariant_results.json
system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312.md   (single-iter version, kept for trail)
system_v5/grok_sim/INFORMAL_TO_FORMAL_HANDOFF_iter_312_315_chain.md   (this file)
```

No writes to `system_v5/ops/formal_scouts/`, `system_v5/docs/`, `system_v5/evidence/`, or any formal classifier / index. All four result JSONs carry sidequest-local vocabulary. No formal-scout stamp in any of them.

---
title: Axis0 Current Doctrine State Card
created: 2026-04-10
updated: 2026-04-16
type: summary
tags: [reference, system, status, constraints, research]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/AXIS0_CURRENT_DOCTRINE_STATE_CARD.md
framing: current
---

# Axis0 Current Doctrine State Card

## Overview
Compact wiki mirror of the live `Axis 0` doctrine card. It preserves the repo’s earned/open/killed split without pretending the open bridge and cut problems are already solved.

## Earned
- `Axis 0` is geometry-seated, but geometry is still not the final doctrine object.
- Coherent-information / negative-conditional-entropy remains the strongest simple signed candidate family.
- `Xi_hist` is a live bridge candidate, but current sampled bakeoffs still favor the shell / Phase 4 baseline family.
- The history-window cut remains a live executable candidate cut family rather than a closed winner.
- The shell / interior-boundary cut is the strongest doctrine-facing cut family.

### Newly cited earned items in the current packet snapshot
- **I_c = −S(A|B) formally confirmed**: `sim_shell_entropy_signed_cut` (14/14 pass) proves S(A|B) < 0 for entangled states, z3 UNSAT for separable+negative — the signed entropy is structurally real, not a convention.
- **Arrow-of-time asymmetry formally proven**: `sim_arrow_of_time_l1_l3_asymmetry` (15/15 pass) — L1→L3 (coherent→dephased) is NOT reversible. z3 UNSAT: off-diagonal=0 AND fiber entropy > 0 is impossible. Dephasing is one-directional.
- **Berry phase → Axis 0 gradient connected**: `sim_symplectic_berry_flux_axis0` (15/15 pass) — γ = Ω/2, Stokes theorem on S², ∂I_c/∂θ nonzero at θ=π/4. Symplectic 2-form on S² links Berry curvature and the sampled Axis 0 gradient behavior.
- **Layer coupling matrix canonical** (13/13 pass): L3 operator formally incompatible with L1 fiber entropy — z3 UNSAT proven. Two entropy types on the same state are structurally incompatible.
- **Tensor network substrate established**: `shell_indexed_tensor_network` canonical, all_pass. Shell order is load-bearing for contraction values. I_c present in results.
- **Spinor torus TN**: `sim_tensor_network_spinor_torus` 14/14 pass — MPS fidelity=1.0, entropy varies with torus parameter η. The sampled `η = π/4` point reaches near-max bipartition entropy in this finite ring.
- **I_c gradient on TN bonds**: `sim_tensor_network_ic_gradient` 17/17 pass (classical_baseline). I_c = log(χ) for pure Schmidt states; monotone in bond dimension χ∈{1,2,4}. χ=1 → product state → I_c ≤ 0.
- **MERA shell geometry**: `sim_mera_shell_axis0` 19/19 pass (classical_baseline). I_c decreases monotonically under coarse-graining; causal cone O(log N) confirmed. Each MERA layer = one G-tower rung.
- **SU3 gauge invariance of Axis 0**: `sim_su3_gauge_invariant_tensor_contraction` 12/12 pass (classical_baseline). Tr(g†Ag)=Tr(A) proven via sympy cyclic trace; ∂I_c/∂g=0 at g=identity via pytorch autograd (su(3) projected); z3 UNSAT: gauge-invariant AND gauge-dependent simultaneously is impossible.
- **Phi0 seam**: closed (2026-04-08). `bridge_phi0_proof_integration` canonical, 17/17 pass, pytorch+z3+cvc5+sympy+geomstats+rustworkx.
- **Hopf connection operators**: `sim_hopf_connection_curvature_operators` 10/10 pass (2026-04-15). A(vertical)=1, ∫F=4π (c₁=1), horizontal lift A=0. z3 UNSAT: c₁=0 on Hopf bundle. Equatorial holonomy Hol(2π loop)=-1 confirmed.
- **Cl(3) bivector entropy**: `sim_cl3_bivector_entropy` 14/14 pass (2026-04-15). Pure bivector entropy=0; max entropy=log(3) for uniform mix; SU(2) double-cover entropy gap = **log(2)** confirmed (SO(3) quotient increases entropy by exactly 1 bit).
- **Rosetta R4 — SU(2)→SO(3) log(2) gap confirmed from 3 independent methods** (2026-04-15):
  - `sim_gtower_entropy_reduction_chain`: entropy increases log(2) when viewed from SO(3) (±ψ indistinguishable)
  - `sim_cl3_bivector_entropy`: rotor path S=0 in SU(2), S=log(2) in SO(3) quotient
  - `sim_spectral_triple_entropy_coupling`: Connes distance SU(2) > SO(3) for same pair; z3 UNSAT on reversed ordering
  Three distinct tools (scipy/clifford/sympy), zero shared code, same invariant. This is earned Rosetta evidence.
- **TN×G-tower bond dimension**: `sim_tn_gtower_bond_dimension` all_pass (2026-04-15). I_c=log(χ): GL3/O3/SO3/U3/SU3 all have χ=3; Sp6 has χ=6. Entropy gap at SU3→Sp6 = log(6)−log(3) = log(2) ≈ 0.693. z3 UNSAT on bond dimension decrease. **Sp6 is the symplectic expansion step** — information capacity increases by exactly 1 bit.
- **TN MPO operator families**: `sim_tn_mpo_operator_family` all_pass (2026-04-15). Identity/SWAP/dephasing MPO verified; data-processing inequality confirmed (z3 UNSAT on entropy decrease under dephasing).
- **MERA×G-tower layer assignment**: `sim_tn_mera_gtower_layers` all_pass (2026-04-15). GL3(layer 0)→SO3(layer 1)→SU3(layer 2): monotone I_c decrease across MERA layers; SU3 has 8 DOF vs GL3's 9 (det=1 removes 1 parameter).
- **Step 5 emergence confirmed**: `sim_hopf_weyl_emergence_quantities` 7/7 pass (2026-04-15). Q₁ = P_L(Hol·ψ) − Hol·P_L(ψ) is a genuine emergent observable: non-zero only in joint Hopf+Weyl shell, exactly zero for either shell alone. Joint entropy sub-additive: S(joint)=0.289 < S(Hopf)+S(Weyl)=1.076. Q₁ antisymmetric under CW/CCW loop reversal. Topology-sensitive: zero on flat torus.

## Live but open
- Final canon `Xi` is still open.
- Final doctrine-level cut `A|B` is still open.
- Exact `Xi_hist` family construction and exact shell bridge construction are still open.
- Shell/history unification is still open even though typed sync surfaces exist.
- The broader `j/k`-fuzz and `i`-scalar genealogy is real in the Axis-0 document family, but its exact bridge into the current doctrine card remains open rather than closed. See [[jk-fuzz-field]] and [[i-scalar-and-axis-0-genealogy]].

## Killed or demoted
- Raw local `L|R` is killed as sufficient bridge doctrine.
- Uncoupled pure-product `L|R` is demoted to control only.
- Old shell-strata pointwise bridge/cut shortcuts are killed.
- Runtime `GA0` is demoted to proxy only.

## Anti-smoothing rule
The repo card is explicit that strongest executable family != final doctrine closure. Do not collapse exploratory bridge wins, typed contract existence, or geometry seating into a solved Axis 0 theorem.

## Related pages
- [[constraint-geometry-axis0-separation]]
- [[current-authoritative-stack-index]]
- [[qit-engine-geometry-entropy-bridge]]
- [[constraint-surface-and-process]]

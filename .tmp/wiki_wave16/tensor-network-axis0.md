---
title: Tensor Network Substrate for Axis 0
created: 2026-04-15
updated: 2026-04-15
type: concept
tags: [axis0, tensor-network, geometry, simulation, quantum, entropy, mera]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/shell_indexed_tensor_network.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_tensor_network_spinor_torus.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_tensor_network_ic_gradient.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_mera_shell_axis0.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_su3_gauge_invariant_tensor_contraction.py
framing: current
---

# Tensor Network Substrate for Axis 0

## Core claim

Axis 0 (I_c = −S(A|B)) can be viewed as operating on an entangled tensor network. This is a strong candidate view and a useful refinement lane, not yet a canon-closing result.

The justification:
- Shell order is load-bearing for contraction values in the shell-indexed TN (all_pass canonical)
- I_c is present in contraction results — cutting across a bond in the TN gives an I_c value
- Bond dimension χ = local entanglement capacity. χ=1 gives product state → I_c ≤ 0 (z3 UNSAT χ=1 AND I_c>0 proven)
- Some nonzero `η` values in the tested spinor-torus family give bipartition entropies near 1.0; entanglement varies substantially with `η`

The current probes suggest the TN is a useful geometric model for the Axis 0 bridge candidate. They do not yet establish it as the engine's substrate.

## Layer structure

| TN component | Physical role |
|---|---|
| Bond dimension χ | Local entanglement capacity = Axis 0 gradient resolution |
| Bond cut A\|B | The cut-state family; I_c(A→B) = Axis 0 value at that cut |
| Shell index r | Ordered constraint level; contraction values depend on order |
| Tensor at vertex v | Local operator/state at shell boundary |
| Edge e | Entanglement link between shells; χ_e is bond dimension |

## I_c gradient across TN bonds

I_c as a function of bond dimension χ:
- χ=1 (product): I_c ≤ 0 always (no coherence across cut)
- χ=2 (Bell-capable): I_c can be positive for entangled states
- χ=4 (higher): I_c magnitude grows with entanglement depth

The gradient ∂I_c/∂χ across bond cuts is the Axis 0 gradient in the TN picture.

Sim in progress: `sim_tensor_network_ic_gradient.py` — I_c vs χ∈{1,2,4} with z3 UNSAT for χ=1 AND I_c>0.

## MERA as holographic shell geometry

MERA (Multi-scale Entanglement Renormalization Ansatz) maps directly onto the G-tower and shell architecture:

| MERA layer | G-tower rung | Physical meaning |
|---|---|---|
| Layer 0 (finest) | Sp6/F4 | Short-range entanglement, Berry phase active |
| Layer 1 | SU3 | Gauge-locked phase |
| Layer 2 | U3 | Complex phase only |
| Layer 3 (coarsest) | SO3/O3 | Classical orientation |

MERA properties:
- Disentanglers remove short-range entanglement at each layer
- Isometries coarse-grain the state
- Causal cone = O(log N) — holographic property
- I_c **decreases** as you coarse-grain (information lost to environment = past shell)

The holographic direction in MERA = the shell direction in the constraint manifold. Coarse-graining toward the center = going toward the past.

Sim in progress: `sim_mera_shell_axis0.py` — 3-layer MERA on 8 sites; ∂I_c/∂disentangler parameters via autograd.

## SU3 gauge invariance

Claim: in the tested bond-insertion probe, the Axis 0 surrogate is gauge-stable under paired SU3 transformations on TN bonds.

Concretely: in the tested setup, inserting `g⊗g†` on adjacent bonds (`g∈SU3`) leaves `I_c` unchanged. This is consistent with the reduced-state picture where the paired insertion cancels at the measured bond cut.

One-sided insertion does change `I_c` in the probe, which is the diagnostic contrast.

Sim in progress: `sim_su3_gauge_invariant_tensor_contraction.py` — ∂I_c/∂g=0 at g=identity; single-bond insertion breaks invariance.

## Established evidence (as of 2026-04-15)

The table below should be read conservatively. It mixes stronger classical-baseline evidence with worker-reported or not-yet-upgraded nonclassical implications. In particular, these entries do **not** by themselves imply canon by process for an Axis 0 bridge lane, because proper non-classical sims are still missing.

| Claim | Sim | Status |
|---|---|---|
| Shell order load-bearing for TN contraction | `shell_indexed_tensor_network` | canonical, all_pass |
| I_c present in TN bond-cut results | `shell_indexed_tensor_network` | canonical, all_pass |
| MPS fidelity=1.0, entropy varies with η | `sim_tensor_network_spinor_torus` | 14/14 pass |
| Bipartition entropies ~1.0 for entangled torus | `sim_tensor_network_spinor_torus` | 14/14 pass |
| I_c = −S(A|B) formally (signed, structural) | `sim_shell_entropy_signed_cut` | 14/14 pass |
| I_c = log(χ) for pure Schmidt states; monotone in χ | `sim_tensor_network_ic_gradient` | 17/17 pass (classical_baseline) |
| χ=1 → I_c ≤ 0 (confirmed; z3 UNSAT would require canonical upgrade) | `sim_tensor_network_ic_gradient` | 17/17 pass |
| MERA: I_c decreases under coarse-grain; causal cone O(log N) | `sim_mera_shell_axis0` | 19/19 pass (classical_baseline) |
| SU3 cyclic trace: Tr(g†Ag)=Tr(A) — sympy load-bearing proof | `sim_su3_gauge_invariant_tensor_contraction` | 12/12 pass (classical_baseline) |
| In the tested paired `g⊗g†` insertion, `I_c` stays unchanged at the measured cut | `sim_su3_gauge_invariant_tensor_contraction` | 12/12 pass |
| One-sided insertion changes the measured `I_c` response | `sim_su3_gauge_invariant_tensor_contraction` | 12/12 pass |

**All three new sims are `classical_baseline`.** Canonical gate requires: genuine quantum circuit execution or optimized TN, plus structural impossibility z3 UNSAT beyond the trivial χ=1 case.

## What remains open

- Canonical Ξ bridge sim (exact map from shell geometry into ρ_AB via TN)
- A|B cut specification — which cut on which bond is the doctrine cut
- Shell/history unification — TN shell index r vs Xi_hist history window

The TN lane does not close Axis 0. It provides a stronger geometric-model candidate on which the bridge problem is better posed.

## Related pages

- [[axis0-current-doctrine-state-card]] — earned/open/killed split for Axis 0
- [[axis-and-entropy-reference]] — three-layer entropy architecture; I_c family
- [[qit-engine-geometry-entropy-bridge]] — bridge problem; Ξ candidates
- [[shell-local-to-coupled-program]] — coupling-program map and candidate synthesis surface
- [[gerbe-g-tower-and-motives-packets]] — G-tower ordering packet and adjacent motives-family summary
- [[berry-phase-and-holonomy]] — Berry connection and Sp6 rung
- [[quantum-shannon-theory-reference]] — coherent information, conditional entropy

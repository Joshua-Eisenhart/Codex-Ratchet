---
title: Cl(3) / Cl(6) Result Family
created: 2026-04-15
updated: 2026-04-16
type: concept
tags: [clifford, geometry, simulation, spinors, results, rosetta]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl3_e3nn_rotor_vs_wignerD_vector.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl3_rotor_associativity.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl6_even_subalgebra_closure.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_clifford_deep_cl3_rotor_double_cover.py
framing: current
---

# Cl(3) / Cl(6) Result Family

## Summary

Four cited Clifford algebra scripts define a bounded result family around Cl(3) rotor structure and Cl(6) even-subalgebra structure.

**Current artifact caveat**: in this workspace audit I did not rely on a matching checked-in set of `sim_cl3_*` / `sim_cl6_*` result JSONs to assign a fresh family-wide truth label. The cited scripts themselves are written to emit `classification: canonical` plus `overall_pass`, so this page should be read as a script-grounded family digest rather than a fresh artifact-status card.

## Sim inventory

| Sim | Script-level result shape | Key claims |
|---|---|---|
| `sim_cl3_e3nn_rotor_vs_wignerD_vector` | script writes `classification: canonical`, `overall_pass` | Clifford rotor rotation = e3nn WignerD on vectors; double-cover identity action error = 0.0 |
| `sim_cl3_rotor_associativity` | script writes `classification: canonical`, `overall_pass` | Rotor product is associative; R_π * R_π = -1 (double cover); identity boundary error = 0.0 |
| `sim_cl6_even_subalgebra_closure` | script writes `classification: canonical`, `overall_pass` | Even subalgebra closed under product; 100 random pairs, 0 odd-grade leaks; max_odd_grade_leak = 0.0 |
| `sim_clifford_deep_cl3_rotor_double_cover` | script writes `classification: canonical`, `overall_pass` | Deep double-cover probe; SU(2)->SO(3) double-cover identities and 4π periodicity |

## Key structural facts confirmed

**Double cover**: Cl(3) rotors R and −R give the same SO(3) action on vectors but different scalar parts. This cannot be detected by numpy matrix multiply alone — it requires Clifford algebra semantics.

**Even subalgebra closure (Cl(6))**: Product of two even-grade elements in Cl(6) stays in the even subalgebra. Zero odd-grade leak in 100 random pairs confirms algebraic closure.

**Rotor–WignerD agreement (Rosetta)**: Clifford rotor sandwich action on a 3-vector agrees with e3nn WignerD matrix applied to the same vector. This is Rosetta R2 from the G-Tower/Hopf/Weyl integration spec — tool-family agreement on the same underlying SO(3) invariant.

## Ablation findings

`sim_cl3_e3nn_rotor_vs_wignerD_vector` ablation:
- R and −R (as rotors) give identical vector action but distinct scalar parts
- Confirms numpy SO(3) matrix multiply is insufficient — it cannot distinguish R from −R
- `ablation_shows_numpy_insufficient: True` in all cases

`sim_cl3_rotor_associativity` ablation:
- Numpy rotation matrix R_π² = identity (wrong)
- Clifford rotor R_π² = −1 (correct spinor behavior)
- This is the structural gap that makes Clifford load-bearing, not decorative

## Connection to G-Tower

The Cl(3) / Cl(6) algebra sits at the O(3)→SO(3) and SO(3)→U(3) levels of the G-tower:
- Cl(3): real Clifford algebra, encodes SO(3) double cover — G-tower rung O→SO
- Cl(6): encodes higher-dimensional spinor structure — bridges toward U→SU rung
- Even subalgebra of Cl(6) ≅ Cl(5) as algebras — connection to SU(2) actions

Weyl spinors (half-spinors) are elements of the minimal left ideal in Cl(1,3) — the chirality split is grade-decomposition in Clifford.

## Related pages

- [[cl3-cl6-micro-sims]] — public router for standalone micro-sims; existence-level summary
- [[clifford-algebra-qit]] — Clifford algebras, rotors, Spin(3), qubit/Bloch bridge
- [[g-tower-hopf-weyl-integration]] — G-tower ordering; Rosetta R1/R2/R3 predictions
- [[gerbe-g-tower-and-motives-packets]] — G-tower canonical ordering (8/8 sims)

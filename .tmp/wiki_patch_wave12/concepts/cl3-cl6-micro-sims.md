---
title: Cl3 and Cl6 Micro-Sims
created: 2026-04-14
updated: 2026-04-14
type: concept
framing: current
tags: [clifford, geometry, chirality, simulation, algebra]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl3_basis.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl3_basis.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl3_rotor_product.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl3_rotor_product.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl3_bivector_exp.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl3_bivector_exp.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl3_reflection.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl3_reflection.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl3_composition.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl3_composition.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl3_invariants.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl3_invariants.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl6_basis.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl6_basis.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl6_rotor_product.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl6_rotor_product.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl6_spin_group_embedding.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl6_spin_group_embedding.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_cl6_chirality.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/results/sim_cl6_chirality.json
---

# Cl3 and Cl6 Micro-Sims

## Purpose
This page gives the first public routing surface for the new standalone Clifford micro-sims that were landed as tiny basis/product/chirality-style probes.

## Role in the live wiki cluster
- Strongest use: route readers from the general Clifford reference into the newly separated Cl(3) and Cl(6) micro-probe layer.
- Weak use: claiming the whole Clifford lane or chirality lane is complete.
- Authority boundary: in this maintenance pass the artifacts are summarized at `exists` unless a fresh rerun is cited.

## Packet snapshot
There are explicit standalone micro-sims for Cl(3) and Cl(6) in this maintenance pass, rather than only larger mixed packets.

Cl(3) micro-surfaces are present for:
- basis
- rotor product
- bivector exponential
- reflection
- composition
- invariants

Cl(6) micro-surfaces are present for:
- basis
- rotor product
- spin-group embedding
- chirality

## Why this matters
The Clifford lane is more legible when these tiny algebraic objects are separated:
- basis and rotor product are not the same probe as chirality
- Cl(3) local rotor/reflection algebra is not identical to Cl(6) spin/chirality structure
- the chirality claim can now be named as its own bounded object instead of only being inferred from broader packets

Representative artifact behavior:
- `sim_cl6_chirality.py` treats the pseudoscalar as the chirality operator and tests its commutation/anticommutation behavior with even and odd grades
- clifford is load-bearing there, not decorative

Safe public label in this pass for these artifacts:
- `exists`

## What is already present
| Family | Evidence path(s) | Artifact-side field seen in this pass | Safe public label |
|---|---|---|---|
| Cl(3) micro-sims | `system_v4/probes/results/sim_cl3_*.json` | sampled artifacts record `classification: classical_baseline`, `pass: true` | `exists` |
| Cl(6) micro-sims | `system_v4/probes/results/sim_cl6_*.json` | sampled artifacts record `classification: classical_baseline`, `pass: true` | `exists` |

## What is still open
1. No fresh rerun was performed in this maintenance pass.
2. The public geometry/ledger pages have not yet normalized these Cl(3)/Cl(6) micro-sims into explicit rows.
3. The standalone micro-sims help separate the local algebra layer, but they do not by themselves close the wider spinor/chirality/geometry lane.

## Related pages
- [[cl3-cl6-result-family]]
- [[clifford-geometric-algebra-reference]]
- [[clifford-algebra-qit]]
- [[pauli-on-weyl-loop-interaction]]
- [[sim-tranche-2026-04-14-axioms-tools-gerbes-motives]]
- [[tooling-status]]
- [[current-research-overlays]]
- [[geometry-ingredient-map]]

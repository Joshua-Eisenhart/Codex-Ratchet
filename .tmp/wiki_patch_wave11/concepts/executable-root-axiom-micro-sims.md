---
title: Executable Root-Axiom Micro-Sims
created: 2026-04-14
updated: 2026-04-14
type: concept
framing: current
tags: [formal-methods, constraints, distinguishability, simulation, axioms]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_f01_finite_state_set.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_f01_finite_state_set_results.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_f01_finite_measurement_set.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_f01_finite_measurement_set_results.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_f01_finite_hilbert_dim.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_f01_finite_hilbert_dim_results.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_f01_quotient_well_defined.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_f01_quotient_well_defined_results.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_n01_noncommutation_generic.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_n01_noncommutation_generic_results.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_n01_composition_order_distinguishes.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_n01_composition_order_distinguishes_results.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_n01_identity_via_indistinguishability.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_n01_identity_via_indistinguishability_results.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_n01_indiscernibility_implies_identity.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_n01_indiscernibility_implies_identity_results.json
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axiom_n01_pauli_algebra_closure.py
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/sim_axiom_n01_pauli_algebra_closure_results.json
---

# Executable Root-Axiom Micro-Sims

## Purpose
This page turns the root axioms into a public executable cluster instead of leaving them only as doctrine sentences or scattered probe files.

## Role in the live wiki cluster
- Strongest use: route readers from the root-constraint doctrine into the new bounded probes that directly test F01 and N01.
- Weak use: declaring the whole root-axiom lane complete.
- Authority boundary: in this maintenance pass the artifacts below are summarized at `exists` unless a fresh rerun is cited.

## Packet snapshot
An explicit micro-sim packet for the two root constraints is present in the artifact layer in this maintenance pass.

Safe public label in this maintenance pass:
- every artifact listed here = `exists`

Why the label stays there:
- I read the probe files and their result artifacts directly
- the artifacts record internal `classification: "canonical"` and sampled `pass: true`
- I did not freshly rerun the probes in this pass

## F01 packet
F01 is represented here by direct bounded probes for:
- finite state set
- finite measurement set
- finite Hilbert dimension
- quotient well-definedness

Representative artifact behavior:
- `sim_axiom_f01_finite_measurement_set.py` uses z3 load-bearing to force distinct measurement indices in a finite set and return UNSAT for the pigeonhole violation case
- the same file uses SymPy supportively to exhibit the canonical finite Pauli measurement triad

## N01 packet
N01 is represented here by direct bounded probes for:
- generic noncommutation
- composition-order distinction
- identity via indistinguishability
- indiscernibility implies identity
- Pauli algebra closure as a joint F01+N01 carrier instance

Representative artifact behavior:
- `sim_axiom_n01_pauli_algebra_closure.py` uses SymPy load-bearing for symbolic Pauli closure on `C^2`
- torch is used supportively there as a numeric witness layer
- the negative tests explicitly reject a fake commutative-Pauli hypothesis

## Why this matters
This packet changes the public shape of the formal-methods lane in one important way:
- the root constraints are no longer only described as background principles
- they appear here as bounded executable objects with positive, negative, and boundary sections

That makes the lower-most admissibility layer more legible for later ledger normalization.

## What is already present
| Packet | Evidence path | Artifact-side internal field seen in this pass | Safe public label |
|---|---|---|---|
| F01 finite-state/measurement/Hilbert/quotient packet | `system_v4/probes/a2_state/sim_results/sim_axiom_f01_*_results.json` | sampled artifacts record `classification: canonical`, `pass: true` | `exists` |
| N01 noncommutation/order/identity/Pauli-closure packet | `system_v4/probes/a2_state/sim_results/sim_axiom_n01_*_results.json` | sampled artifacts record `classification: canonical`, `pass: true` | `exists` |

## What is still open
1. No fresh rerun was performed in this maintenance pass, so the packet stays at `exists` here.
2. The grouped and exhaustive lego ledgers still describe these root constraints mostly as registry pressure rather than as a normalized explicit family.
3. The next useful normalization step is to connect these probes more directly to the root/admission rows in the public registry language.

## Related pages
- [[constraint-on-distinguishability]]
- [[constraint-on-distinguishability-full-math]]
- [[current-formal-methods-core]]
- [[sim-tranche-2026-04-14-axioms-tools-gerbes-motives]]
- [[llm-controller-contract]]
- [[nominalist-translation-rules]]
- [[actual-lego-registry]]
- [[lego-build-catalog]]

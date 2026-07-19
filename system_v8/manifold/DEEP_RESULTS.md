# Deep-layer manifold results

## What ran

`RUN_DEEP.sh` ran connection, history, persistence, chirality, whole-manifold-v2,
semantic verification, and double in-process deterministic replay with the required
sim-stack Python interpreter. All seven stages passed. Verification rejected 25/25
digest-preserving adversarial mutations; replay passed 28/28 checks.

## Deep frontier

The tournament evaluated 4,752 declared candidates. The plural frontier contains
12 candidates: the cross-product of bases `{classical_distribution, finite_automaton,
finite_relation}`, nestings `{complete_pairwise, ternary_relation}`, geometry
`shannon_fisher`, connection `parity_sign_transport`, and histories
`{branching_tree_histories, sequence_histories}`. Beaten candidates remain in
Purgatory with concrete comparison witnesses and a re-offer rule.

## Noncommutation

Earned for the finite tested transports. On input state `[0,1,0]`, with
`T1=parity_sign_transport` and `T2=qca_permutation_transport`, `T2(T1(x))=[0,0,1]`
while `T1(T2(x))=[0,0,0]`. The branching tree's terminal leaves and every
root-to-node restriction path recompute their mapped history tables.

## Chirality

Expressible: `true`; forced: `false`; installable: `true`.
Status: `EXPRESSIBLE_INSTALLABLE_NOT_FORCED`.

## Open caveats

Results are packet-relative finite evidence only. They do not promote or formally
admit a candidate, force an orientation, establish a canonical or terminal
manifold, exhaust the proposal grammar, or assert the late entropy/geometry
readout as physics. Any changed source packet, restriction table, requirement,
witness, or grammar extension triggers re-offer.

## Fresh `RUN_DEEP.sh` output

```text
{"all_pass": true, "candidate_count": 3, "default": "parity_sign_transport", "frontier": ["parity_sign_transport"]}
{"all_pass": true, "candidate_count": 3, "frontier": ["branching_tree_histories", "sequence_histories"], "noncommutation_earned": true, "witness": {"T1": "parity_sign_transport", "T1_after_T2": [0, 0, 0], "T2": "qca_permutation_transport", "T2_after_T1": [0, 0, 1], "distinguishes_order": true, "input_state": [0, 1, 0]}}
{"all_pass": true, "candidate_manifold_count": 9, "current_frontier": ["parity_sign_transport__branching_tree_histories", "parity_sign_transport__sequence_histories"], "shared_surviving_distinctions": 11}
{"all_pass": true, "expressible": true, "forced": false, "installable": true, "status": "EXPRESSIBLE_INSTALLABLE_NOT_FORCED"}
{"all_pass": true, "candidate_count": 4752, "default": "classical_distribution__complete_pairwise__shannon_fisher__parity_sign_transport__branching_tree_histories", "final_frontier": ["classical_distribution__complete_pairwise__shannon_fisher__parity_sign_transport__branching_tree_histories", "classical_distribution__complete_pairwise__shannon_fisher__parity_sign_transport__sequence_histories", "classical_distribution__ternary_relation__shannon_fisher__parity_sign_transport__branching_tree_histories", "classical_distribution__ternary_relation__shannon_fisher__parity_sign_transport__sequence_histories", "finite_automaton__complete_pairwise__shannon_fisher__parity_sign_transport__branching_tree_histories", "finite_automaton__complete_pairwise__shannon_fisher__parity_sign_transport__sequence_histories", "finite_automaton__ternary_relation__shannon_fisher__parity_sign_transport__branching_tree_histories", "finite_automaton__ternary_relation__shannon_fisher__parity_sign_transport__sequence_histories", "finite_relation__complete_pairwise__shannon_fisher__parity_sign_transport__branching_tree_histories", "finite_relation__complete_pairwise__shannon_fisher__parity_sign_transport__sequence_histories", "finite_relation__ternary_relation__shannon_fisher__parity_sign_transport__branching_tree_histories", "finite_relation__ternary_relation__shannon_fisher__parity_sign_transport__sequence_histories"], "frontier_count": 12}
{"all_pass": true, "checks": 56, "failed_checks": [], "mutation_count": 25, "mutations_rejected": 25}
{"all_pass": true, "checks": 28, "failed_checks": [], "replayed_stages": ["connection", "history", "persistence", "chirality", "whole_manifold_v2", "verification"]}
```

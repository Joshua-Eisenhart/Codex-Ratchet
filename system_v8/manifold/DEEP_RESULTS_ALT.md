# DEEP_RESULTS_ALT

What ran: `bash system_v8/manifold/RUN_DEEP_ALT.sh` rebuilt the redundant alt deep lane into `system_v8/manifold/results/deep_alt/` and exited 0.

Receipts: connection, history, persistence, chirality, whole manifold v2, verification, deterministic replay.

Connection frontier: `qca_permutation_transport`, `spinor_parity_sign_transport`; default `qca_permutation_transport`. `identity_transport` is excluded with a concrete transported-state witness.

Deep frontier: 6 plural candidates from 4,752 complete `(base x nesting x geometry x connection x history)` candidates:

- `classical_distribution__complete_pairwise__shannon_fisher__spinor_parity_sign_transport__sequence_histories`
- `classical_distribution__ternary_relation__shannon_fisher__spinor_parity_sign_transport__sequence_histories`
- `finite_automaton__complete_pairwise__shannon_fisher__spinor_parity_sign_transport__sequence_histories`
- `finite_automaton__ternary_relation__shannon_fisher__spinor_parity_sign_transport__sequence_histories`
- `finite_relation__complete_pairwise__shannon_fisher__spinor_parity_sign_transport__sequence_histories`
- `finite_relation__ternary_relation__shannon_fisher__spinor_parity_sign_transport__sequence_histories`

Noncommutation status: earned for `sequence_histories` and `branching_tree_histories`; explicit negative for `unordered_set_baseline`. Witness packet: `nested_completion_baseline`.

Chirality status: expressible true, forced false, installable true; classification `merely_installable`. Octonion witness trial 0 has bracketing gap squared 888 and chirality gap squared 560.

Verification: 51 semantic checks passed; 15 adversarial mutations rejected. Deterministic replay: 14 checks passed.

Open caveats: `promotion_allowed: false`, `formal_admission_allowed: false`; this is a packet-relative redundant alt frontier, not a final manifold, official rung, canonical admission, or physics claim.

Fresh `RUN_DEEP_ALT.sh` stdout:
{"all_pass": true, "candidate_count": 3, "default": "qca_permutation_transport", "failed_transports": ["identity_transport"], "frontier": ["qca_permutation_transport", "spinor_parity_sign_transport"]}
{"all_pass": true, "candidate_count": 3, "frontier": ["sequence_histories"], "noncommutation_status": {"branching_tree_histories": "earned", "sequence_histories": "earned", "unordered_set_baseline": "explicit_negative"}}
{"all_pass": true, "candidate_count": 1, "frontier": ["sequence_histories"], "surviving_counts": {"sequence_histories": 10}}
{"all_pass": true, "chirality_status": {"classification": "merely_installable", "expressible": true, "forced": false, "installable": true}, "witness_trial": 0}
{"all_pass": true, "candidate_count": 4752, "default": "classical_distribution__complete_pairwise__shannon_fisher__spinor_parity_sign_transport__sequence_histories", "final_frontier": ["classical_distribution__complete_pairwise__shannon_fisher__spinor_parity_sign_transport__sequence_histories", "classical_distribution__ternary_relation__shannon_fisher__spinor_parity_sign_transport__sequence_histories", "finite_automaton__complete_pairwise__shannon_fisher__spinor_parity_sign_transport__sequence_histories", "finite_automaton__ternary_relation__shannon_fisher__spinor_parity_sign_transport__sequence_histories", "finite_relation__complete_pairwise__shannon_fisher__spinor_parity_sign_transport__sequence_histories", "finite_relation__ternary_relation__shannon_fisher__spinor_parity_sign_transport__sequence_histories"]}
{"all_pass": true, "checks": 51, "failed_checks": [], "mutation_count": 15, "mutations_rejected": 15}
{"all_pass": true, "checks": 14, "failed_checks": []}


# CONSTRAINT_TIGHTENING_PROPOSAL v1

This specification defines the advisory object A2 may provide to A1 suggesting constraint tightening actions.
This is **non-kernel** and MUST NOT mutate canon directly.

## 1. Form
Carried inside `A2_PROPOSAL.json` as an array under key `constraint_tightening_proposals`.

## 2. Proposal schema

Required fields:
- `schema`: MUST equal `"CONSTRAINT_TIGHTENING_PROPOSAL_v1"`
- `proposal_id`: string
- `target_constraint_id`: string (bootpack-defined identifier; must be treated as opaque by A2)
- `tightening_action`: string (bootpack-defined action label; A2 must not invent new kernel primitives)
- `evidence_basis`: object (see below)
- `regression_guard`: object (see below)
- `notes`: string (optional; non-authoritative)

### evidence_basis
Required:
- `supporting_sim_ids`: array of strings (sorted)
- `supporting_hashes`: array of lowercase hex64 (sorted)
- `supporting_counts`: object with integer counts (e.g., kill signals, negative sims)

### regression_guard
Required:
- `must_not_increase_kill_signal_count`: boolean
- `must_not_reduce_pass_rate_below`: integer (counts-based; not probability)
- `required_stress_families`: array of strings (sorted)

## 3. Deterministic admissibility
A2 proposals are advisory. A1 must convert them into admissible A1_STRATEGY proposals.
A0/B decide acceptance; A2 never mutates canon.

## 4. Prohibitions
No probabilities, scores, or optimization fields.
No new kernel primitives.

# gcm_nested_geometry_delta_3q_v0 Build Card

Layer declaration: `nested-geometry-delta | integrated | 3Q`.

This packet computes the first flip-controlled geometry delta on the <=3Q tower. The observable is the normalized shell-occupation distribution of the A-marginal Bloch vector, keyed by probe-family signature and radius shell. The free layer is the C1-valid 3Q candidate carrier; the nested layer is the C1+C2+C3 carved 3Q survivor carrier.

Flip controls are load-bearing:

- alternate registry pin: `alternate_C1_C2_pin_without_C3`
- alternate probe family: `M_prime_xy`
- scrambled-pin control: `scrambled_same_cardinality_pin`
- negative control: `killed_candidate_count_delta`

Ceiling: `scratch_diagnostic_first_flip_controlled_geometry_delta_carrier_and_pins_relative`. The packet is not a manifold admission, intrinsic geometry claim, bridge claim, or axis-level claim.

Source inputs:

- `system_v6/sims/gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json`
- `system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_results.json`
- `system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_registry.json`
- `system_v6/sims/gcm_nesting_tower_le3q_v0/results/gcm_nesting_tower_le3q_v0_results.json`
- `scripts/gcm_nested_schema_check.py`
- `scripts/gcm_substrate_check.py`

# Current Audit Verdict - gcm_nested_geometry_delta_3q_v0

Bottom line: GENUINE_WITH_CAVEATS. Supersedes audit_verdict.md and audit_verdict_strengthened.md, both of which predate the applied fixes. The NEEDS_FIX items from audit_verdict_strengthened.md are resolved: the same-input null control is present and z3/cvc5 are demoted to supportive. Two structural caveats remain: the generic three-engine validator is RED (this is by design — the packet is declared 2-genuine-engine, not generic-three-engine-green); the packet-local validator is GREEN.

## CURRENT STATE

### Null control
PRESENT. The same-input null control is in place: `build_packet` runs a second `delta_run` with identical free pin, nested pin, and probe family as `main`, and the vector L1 distance between the two runs is `0.0` with matching SHA. This falsifier passes.

### z3/cvc5 depth
SUPPORTIVE (crossover load_bearing = false). z3 and cvc5 are demoted from `load_bearing` to `supportive`. The proof structure — asserting `x=v AND x!=v` UNSAT — does not flip when a measured input is corrupted; that is decorative, not load_bearing. The demotion is applied in source and result. Neither z3 nor cvc5 appears in `claim_path_tools` as a claim-bearing tool. `crossover_proofs.*.load_bearing=false`.

### Engine status
Two genuine engines: Python packet (geometry-delta, null/flip controls) and Julia (independent carve parse, probe-family bin, delta/L1 computation, Graphs incidence observables). JAX is a scaled-value guard (supportive). PyTorch is a packet-vector L1 recomputation (supportive). No all-three-engine independence claim is made or admitted.

### Validator state
- Packet-local validator (`validate_gcm_nested_geometry_delta_3q_v0.py`): GREEN / `ok=true`
- Generic three-engine validator (`scripts/validate_three_engine_sim_result.py`): RED / `ok=false` — error: `jax.aligned_packages_load_bearing must be non-empty`. This RED is consistent with the honest relabeling: the packet presents 2 genuine engines + 2 supportive guards, not a generic three-engine load-bearing result. The generic validator failure is not a defect to repair; it is the correct outcome for a packet that does not claim generic-three-engine-green.

### Claim ceiling
`scratch_diagnostic_first_flip_controlled_geometry_delta_carrier_and_pins_relative`

This admits only: a carrier/pin/probe-relative scratch diagnostic showing the A-marginal probe-shell occupation delta moves under alternate registry pin and alternate probe family inputs, with a same-input null control that returns 0.

This does NOT admit: intrinsic nested geometry, manifold or terrain claims, engine-independence claims, Axis0, bridge, formal admission, canonical-by-process, or any promotion.

### Classification
`scratch_diagnostic`. `promotion_allowed=false`. `formal_admission_allowed=false`.

## Summary of resolved NEEDS_FIX items

| Item from audit_verdict_strengthened.md | Resolution |
|---|---|
| No same-input null control | RESOLVED: null control present, vector L1 = 0.0, SHA stable |
| z3/cvc5 labeled load_bearing | RESOLVED: demoted to supportive; load_bearing=false in crossover_proofs and TOOL_INTEGRATION_DEPTH |

## Surviving caveats (by design, not defects)

| Caveat | Status |
|---|---|
| Generic three-engine validator RED | BY DESIGN: packet is 2-genuine-engine; generic validator mismatch is expected and correct |
| JAX/PyTorch not independent geometry engines | ACKNOWLEDGED: supportive guards only; no independence language in ceiling |
| Claim ceiling is scratch_diagnostic only | ACKNOWLEDGED: no manifold/terrain/Axis0/bridge admission |

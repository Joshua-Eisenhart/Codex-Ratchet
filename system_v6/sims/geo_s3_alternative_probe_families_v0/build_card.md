# geo_s3_alternative_probe_families_v0 Build Card

Status: builder-only scratch diagnostic.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

This packet tests the S3 untested-gap row from `system_v6/receipts/stack_uniqueness_map_20260611.md`: alternative probe families. It compares the committed Pauli/IC/z-probe structure against:

- exact d=2 SIC tetrahedron;
- d=2 three-MUB family;
- deliberately coarse single-axis Z family;
- deterministic rank-deficient random-frame null.

Battery:

- state separation over the six committed half-axis Bloch states;
- induced quotient/identity classes;
- exact frame rank against `d^2=4`;
- probe-relative identity rows;
- z3/cvc5 erased-flip proof on raw computed rank/separation values;
- Julia `QuantumOptics`/`Z3` sidecar mirror.

Expected structural answer:

SIC and MUB co-survive on informational completeness and six-state separation. The single-axis Z family reproduces the committed z-probe quotient classes but fails separation. The null is rank deficient. The committed composite pattern is therefore shared on IC rank/separation and unique, in this battery, on the combined z-coarsening plus committed projective N01/order behavior.

Blocked consumers:

- formal admission;
- global S3 uniqueness;
- global stack uniqueness;
- bridge/axis claims;
- canonical-by-process status.

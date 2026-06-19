# Builder Self-Assessment - `gcm_flux_strips_v0`

Bottom line: PASS at `scratch_diagnostic` ceiling.

- Complete strip table: all 10 increasing occupied-shell pairs are computed.
- Stokes check: every row verifies `h(eta_j)-h(eta_i) + int_F = 0` at tolerance.
- Leakage adjudication: the old leakage wording is narrowed to geometric Stokes closure; no runtime/QIT/transport leakage is claimed.
- G2 metadata: corrected to cite landed attach audit `748fca97c`; no `in_flight` status is inherited.
- Substrate: positive frozen-lineage check passes; lineage-free negative fails as required.
- Fences: `layers 10-12 | integrated | 1Q`; carrier-and-pins-relative; no formal admission.


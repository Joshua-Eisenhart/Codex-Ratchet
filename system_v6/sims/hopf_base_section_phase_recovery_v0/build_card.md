# BUILD CARD: hopf_base_section_phase_recovery_v0

Old-estate item 11 translation. One object, one claim: on the committed finite Hopf carrier, a closed base loop through a declared section recovers the expected U(1) phase from the Hopf connection/enclosed-area holonomy, with the section-change gauge term computed rather than asserted.

Authority:
- `system_v6/receipts/old_estate_mine_20260611.md` item 11.
- Legacy source `system_v4/probes/sim_hopf_base_section_phase_recovery.py`.
- S1 source anchor `geo_s1_spinor_hopf_free_v0`: committed Hopf map `S3 -> S2`.
- S2/S9 connection anchor: committed connection `A=dphi+cos(2eta)dchi` and holonomy spectrum class from `9de3f3633`.
- File-boundary pattern from `f1907c814`: builder packet emits `no_builder_audit_verdict=true`; the builder does not create `audit_verdict.md`.

Scope:
- Stage/mode: S1/S2 chart-relative geometry, scratch diagnostic.
- Carrier: finite named Hopf rows at `eta in {0, pi/12, pi/6, pi/4, pi/3, pi/2}` plus one contractible loop and one boundary row.
- Declared north section: `s_N(theta,beta)=(cos(theta/2), exp(i beta) sin(theta/2))`.
- Primary one-loop phase: recovered phase `gamma_N=-Omega/2=-pi*(1-cos(theta))`.
- Anchor lifted-cycle phase: repo convention `h(eta)=-2*pi*cos(2eta)` with the S2 convention pin.
- Gauge row: section change `s' = exp(i beta) s_N` shifts the lifted phase by `-2*pi`, with unchanged U(1) endpoint.

Controls:
- Contractible loop computes recovered phase `0`.
- Gauge-shift control computes the expected section-change term and flips under wrong sign.
- Area-degenerate pole row computes U(1)-identity phase even when the lifted-real representative is `+-2*pi`.
- SMT flips: z3 and cvc5 prove computed-vs-predicted equality is UNSAT to violate, and wrong-sign/erased controls are SAT.

Fences:
- No bridge, axis, physics, or global uniqueness claims.
- No claim that a chart-relative section is canonical.
- No promotion beyond `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.
- PyTorch excluded because no graph/network/autograd claim path is scoped.

Expected files:
- `hopf_base_section_phase_recovery_v0.py`
- `hopf_base_section_phase_recovery_v0_julia.jl`
- `validate_hopf_base_section_phase_recovery_v0.py`
- `results/hopf_base_section_phase_recovery_v0_julia_results.json`
- `results/hopf_base_section_phase_recovery_v0_envelope_results.json`
- `results/hopf_base_section_phase_recovery_v0_validator_results.json`

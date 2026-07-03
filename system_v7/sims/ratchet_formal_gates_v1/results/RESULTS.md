# ratchet_formal_gates_v1 RESULTS

classification: `scratch_diagnostic`
claim_ceiling: `formal_gate_diagnostic_only`
promotion_allowed: `false`
formal_admission_allowed: `false`

## Carrier

- Hilbert carrier: `C^8`.
- Executable finite carrier states: `40`.
- Probe family: `63` non-identity 3-qubit Pauli strings.
- Enumeration: full deterministic carrier/probe enumeration; no sampling.
- Roster formula: `8 terrains x (1 fixed + 2 native operators x 2 order states)` -> expected `40`, actual `40`.

## Gate Verdicts

| gate | verdict | basis |
|---|---|---|
| `token_identity_R5` | `PASS` | z3+cvc5 tuple-field token model: same_entity/fresh/replay derived from content_id/probe_signature/lineage/branch/replay fields; identity grounded in probe_signature |
| `progress_measure_R6` | `PASS` | z3+cvc5 concrete X/H/Q pre/post registers, derived non-step predicate, strict progress for effective steps, and anti-stall fuel flip |
| `observable_quotient_R4` | `PASS` | full C^8 carrier enumeration, roster formula 8*(1+2*2)=40, full/coarse probe epoching with lineage reprojection, numpy/JAX/Torch parity at 1e-10 and Julia parity at 1e-9 |
| `xi_ref_quotient_lift` | `FAIL` | representative-independence checked nontrivially on the coarse single-Z probe epoch; failure demotes Xi_ref to raw-carrier discriminator |

## Numeric Parity

- numpy/JAX/Torch parity at 1e-10 and Julia pair parity at 1e-9: `True`.
- max Pauli-vector abs diff: `2.0650425813784068e-12`.
- max trace abs diff: `4.440892098500626e-16`.
- Xi_ref descriptor spread diff: `1.000088900582341e-12`.
- pair parity: `{'numpy_julia': True, 'numpy_jax': True, 'numpy_torch': True, 'julia_jax': True, 'julia_torch': True, 'jax_torch': True}`.
- parity failures: `[]`.

## Quotient And Xi_ref

- quotient classes: `40`.
- class sizes: `[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]`.
- collapsed pairs: `0`.
- surviving differences: `780`.
- coarse probe epoch: `M_coarse_single_qubit_Z` with probes `['ZII']`, rounding digits `0`.
- coarse quotient classes: `3`.
- coarse multi-representative classes: `3`.
- full-resolution Xi_ref caveat: `constructed_untested_nontrivially_at_full_resolution`.
- Xi_ref status: `demoted_to_raw_carrier_discriminator`.
- Xi_ref probe epoch: `M_coarse_single_qubit_Z`.
- Xi_ref checked class pairs: `9`.
- Xi_ref multi-representative classes: `3`.
- Xi_ref failures: `9`.

## Gate 1.1 Repair Round

- R5 was UNSOUND because booleans were hand-set. It now models token tuples in SMT and derives identity/fresh/replay from fields.
- R5 identity is now grounded in `probe_signature`, not `content_id`; content perturbation with unchanged probe signature remains the same entity.
- R6 was UNSOUND because changed/non-step flags were hand-set. It now derives change predicates from finite pre/post `X`, `H`, and `Q` registers.
- R6 now treats more than K consecutive non-steps as process failure via a fuel/stutter SMT flip.
- R4 now materializes the 40-state roster formula and tags quotient classes by probe epoch.
- Xi_ref was vacuous at full Pauli resolution because all classes were singleton. The full-resolution verdict is demoted to constructed-but-untested-nontrivially.
- Xi_ref was rerun on the coarse single-Z epoch; it failed representative-independence and is demoted to `raw-carrier discriminator`.

## Runtime Caveat

doctor was not green in this session: quimb and clifford import-cache checks failed; active installer scan was blocked by sandbox ps permission

Generated: 2026-07-03T22:54:30Z

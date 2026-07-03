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

## Gate Verdicts

| gate | verdict | basis |
|---|---|---|
| `token_identity_R5` | `PASS` | z3+cvc5 both polarities: bad same-identity reentry UNSAT; erased bad reentry SAT; logged replay SAT-as-new-branch |
| `progress_measure_R6` | `PASS` | z3+cvc5 effective-step strict lexicographic decrease plus objective non-step predicate |
| `observable_quotient_R4` | `PASS` | full C^8 carrier enumeration with all 63 non-identity Pauli probes; numpy/Julia parity at 1e-9 |
| `xi_ref_quotient_lift` | `PASS` | representative-independence checked over every quotient-class pair in numpy and Julia |

## Numeric Parity

- numpy/Julia parity at 1e-9: `True`.
- max Pauli-vector abs diff: `8.770761894538737e-15`.
- max trace abs diff: `3.3306690738754696e-16`.
- Xi_ref descriptor spread diff: `0.0`.
- parity failures: `[]`.

## Quotient And Xi_ref

- quotient classes: `40`.
- class sizes: `[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]`.
- collapsed pairs: `0`.
- surviving differences: `780`.
- Xi_ref status: `quotient_lift_constructed`.
- Xi_ref checked class pairs: `1600`.
- Xi_ref multi-representative classes: `0`.
- Xi_ref failures: `0`.

## Runtime Caveat

doctor was not green in this session: quimb and clifford import-cache checks failed; active installer scan was blocked by sandbox ps permission

Generated: 2026-07-03T21:06:47Z

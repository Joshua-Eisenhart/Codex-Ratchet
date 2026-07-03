# FORMAL_SPEC: ratchet_formal_gates_v1

Status: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

This file is generated from the executable gate artifacts in `results/`. It closes the referee-specified formalization gaps as a Gate-1 diagnostic layer only; it does not advance the Axis-0 bridge, `Phi_0`, or the unified emergence pipeline.

## Source Anchors

- `system_v7/sims/DUAL_RATCHET_FORMALIZATION_XI_EXTRACTION_20260703.md`: R1-R6 extraction, theorem obligations, Xi candidate status, and open gaps.
- `/Users/joshuaeisenhart/wiki/concepts/axes-full-layout-relations-anti-conflation-2026-07-03.md` section 7: referee obligations for R5, R6, observable quotient, and Xi_ref quotient-lift.
- `system_v7/constraint_core/reference_docs_from_josh/physics_program/ratchet_definition_and_emergence_spec_DRAFT_20260614.md`: canonical ratchet definition draft and scratch-only ceiling.
- `system_v7/constraint_core/engines/oracle_targets_3q.py`: real C^8 carrier and full 63-Pauli probe convention used by the executable numeric gates.

## 1. Token Identity (R5)

Formal definition: a token identity tuple is `(content, lineage_id, branch_id, replay_receipt_id)`. Two token occurrences are the same entity iff content is identical, probe observations are indistinguishable, lineage is connected, and there is no logged replay receipt separating the occurrences. A replay receipt opens a fresh branch identity even when content and probes match.

Executable SMT gate:
- bad re-entry without fresh identity tuple: z3 `unsat`, cvc5 `unsat`.
- erased-control bad re-entry: z3 `sat`, cvc5 `sat`.
- logged replay as new branch: z3 `sat`, cvc5 `sat`.
- Gate verdict: `PASS`.

## 2. Progress Measure mu (R6)

Formal definition: `mu : State -> N^3` with strict lexicographic order. The source spec demands a progress measure but does not fix codomain/order; this is the one explicit OPEN-CHOICE. Alternatives retained in `spec.json` are a single finite-state rank in `N`, an `N^2` survivor/receipt rank, or an ordinal notation below `omega^k`.

Objective non-step predicate: a step is a non-step iff it changes none of `X_k`, `H_k`, or the observable quotient projection. This predicate is observer-independent because it is computed from equality of three finite registers, not from a narrative judgment.

Executable SMT gate:
- effective step with non-decreasing mu: z3 `unsat`, cvc5 `unsat`.
- erased-control effective step: z3 `sat`, cvc5 `sat`.
- objective non-step definition violation: z3 `unsat`, cvc5 `unsat`.
- Termination argument: Strict descent in N^3 lexicographic order is well-founded; the survivor stream terminates because the finite carrier gives a finite initial rank and every effective survivor step must strictly decrease it.
- Gate verdict: `PASS`.

## 3. Observable Quotient (R4)

Formal definition: the carrier is the finite executable set of real 3-qubit engine states generated from `oracle_targets_3q.py`. The probe family `M` is all 63 non-identity 3-qubit Pauli strings. `rho_a ~ rho_b` iff every probe expectation in `M` agrees. The projection map sends each carrier state to its equivalence-class id. A difference survives the observable quotient iff the two states project to distinct classes.

Non-circularity: the quotient is defined before R4 consumes it and depends only on carrier states plus probes; it does not depend on update maps, admissibility predicates, or Xi candidates.

Executable numeric gate:
- carrier states: `40`.
- probes: `63`.
- quotient classes: `40`.
- class sizes: `[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]`.
- numpy/Julia parity at 1e-9: `True` with max pvec diff `8.770761894538737e-15`.
- Gate verdict: `PASS`.

## 4. Xi_ref Quotient-Lift

Formal definition: `x_ref` is selected as a quotient class `c_ref`, not as a raw representative. `Xi_ref(c_ref, c)` is well-defined only if the raw point-reference descriptor `Xi_ref(x_ref, x)` is independent of the representative choices `x_ref in c_ref` and `x in c`.

Executable descriptor: the reference representative selects a cut qubit by maximal local Pauli strength; the target descriptor records coherent information `S(B)-S(AB)` for that cut plus local XYZ expectations. This is a discriminator/lift test, not a final Axis-0 bridge doctrine.

Executable lift gate:
- status: `quotient_lift_constructed`.
- checked quotient-class pairs: `1600`.
- multi-representative classes: `0`.
- max descriptor spread: `0.0`.
- failure count: `0`.
- Gate verdict: `PASS`.

## Overall Gate Result

- all gates pass: `True`.
- accepted ceiling: `passes local rerun` if the Python, Julia, validator, and lint commands in the closeout all exit 0; never above `scratch_diagnostic` / `formal_gate_diagnostic_only` without later admission gates.
- blocked consumers: Axis-0 bridge closure, `Phi_0` evaluation, unified emergence admission, and further pipeline advancement.

Generated: 2026-07-03T21:06:47Z

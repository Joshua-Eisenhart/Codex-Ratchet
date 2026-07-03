# FORMAL_SPEC: ratchet_formal_gates_v1

Status: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

This file is generated from the executable gate artifacts in `results/`. It repairs and re-audits the referee-specified formalization gaps as a Gate 1.1 diagnostic layer only; it does not advance the Axis-0 bridge, `Phi_0`, or the unified emergence pipeline.

## Source Anchors

- `system_v7/sims/DUAL_RATCHET_FORMALIZATION_XI_EXTRACTION_20260703.md`: R1-R6 extraction, theorem obligations, Xi candidate status, and open gaps.
- `/Users/joshuaeisenhart/wiki/concepts/axes-full-layout-relations-anti-conflation-2026-07-03.md` section 7: referee obligations for R5, R6, observable quotient, and Xi_ref quotient-lift.
- `system_v7/constraint_core/reference_docs_from_josh/physics_program/ratchet_definition_and_emergence_spec_DRAFT_20260614.md`: canonical ratchet definition draft and scratch-only ceiling.
- `system_v7/constraint_core/engines/oracle_targets_3q.py`: real C^8 carrier and full 63-Pauli probe convention used by the executable numeric gates.

## 1. Token Identity (R5)

Formal definition: a token identity tuple is `(content_id, probe_signature, lineage_id, branch_id, replay_receipt_id)`. `same_entity`, `fresh`, and `replay` are derived from field equalities over small finite SMT domains. `same_entity` is grounded in `probe_signature`, lineage, branch, and absence of replay receipt, not in `content_id`; `content_id` is provenance metadata only.

Root-axiom alignment: this implements `a=a iff a~b` by using the R4 quotient-facing `probe_signature` as the entity discriminator. A content perturbation with identical probe signature is the same entity, so laundering is caught. Different probe signature is genuinely different even if `content_id` matches.

Executable SMT gate:
- content perturbation / same probe violation: z3 `unsat`, cvc5 `unsat`.
- content perturbation erased predicates: z3 `sat`, cvc5 `sat`.
- different probe signature violation: z3 `unsat`, cvc5 `unsat`.
- replay receipt violation: z3 `unsat`, cvc5 `unsat`.
- Gate verdict: `PASS`.

## 2. Progress Measure mu (R6)

Formal definition: `mu : State -> N^3` with strict lexicographic order. The source spec demands a progress measure but does not fix codomain/order; this is the one explicit OPEN-CHOICE. Alternatives retained in `spec.json` are a single finite-state rank in `N`, an `N^2` survivor/receipt rank, or an ordinal notation below `omega^k`.

Objective non-step predicate: a step is a non-step iff finite pre/post registers satisfy `X_pre=X_post`, `H_pre=H_post`, and `Q_pre=Q_post`. This predicate is observer-independent because `changed_x`, `changed_h`, and `changed_q` are derived from equality of three finite registers, not asserted as scenario booleans.

Anti-stall rule: more than K consecutive non-steps is process failure, not a rest state. At full Pauli resolution on density matrices no nontrivial hidden activity exists because 63 expectations determine rho, but coarse probe families reintroduce the risk; the fuel rule is load-bearing for coarse epochs.

Executable SMT gate:
- effective step with non-decreasing mu: z3 `unsat`, cvc5 `unsat`.
- erased-control effective step: z3 `sat`, cvc5 `sat`.
- objective non-step definition violation: z3 `unsat`, cvc5 `unsat`.
- anti-stall K: `2`.
- anti-stall violation with fuel axiom: z3 `unsat`, cvc5 `unsat`.
- anti-stall erased fuel control: z3 `sat`, cvc5 `sat`.
- Termination argument: Strict descent in N^3 lexicographic order is well-founded for effective steps. Derived non-steps are allowed only up to the fuel bound; >K consecutive non-steps is process failure. At full Pauli resolution on density matrices no nontrivial hidden activity exists because 63 expectations determine rho, but coarse probe families reintroduce hidden-activity risk, so the fuel rule is load-bearing for coarse epochs.
- Gate verdict: `PASS`.

## 3. Observable Quotient (R4)

Formal definition: the carrier is the finite executable set of real 3-qubit engine states generated from `oracle_targets_3q.py`. The probe family `M` is all 63 non-identity 3-qubit Pauli strings. `rho_a ~ rho_b` iff every probe expectation in `M` agrees. The projection map sends each carrier state to its equivalence-class id. A difference survives the observable quotient iff the two states project to distinct classes.

Non-circularity: the quotient is defined before R4 consumes it and depends only on carrier states plus probes; it does not depend on update maps, admissibility predicates, or Xi candidates.

Executable numeric gate:
- carrier states: `40`.
- probes: `63`.
- roster formula: `8 terrains x (1 fixed + 2 native operators x 2 order states)`.
- roster expected/actual: `40` / `40`.
- quotient classes: `40`.
- class sizes: `[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]`.
- probe epoching: full epoch `M_full_pauli_63` and coarse epoch `M_coarse_single_qubit_Z`; equivalence is valid only within an epoch and cross-epoch identity requires re-projection.
- coarse epoch multi-representative classes: `3`.
- numpy/Julia/JAX parity at 1e-10: `True` with max pvec diff `2.063155202236544e-12`.
- Gate verdict: `PASS`.

## 4. Xi_ref Quotient-Lift

Formal definition: `x_ref` is selected as a quotient class `c_ref`, not as a raw representative. `Xi_ref(c_ref, c)` is well-defined only if the raw point-reference descriptor `Xi_ref(x_ref, x)` is independent of the representative choices `x_ref in c_ref` and `x in c`. Full Pauli resolution has singleton classes here, so the previous full-resolution verdict is only `constructed_untested_nontrivially_at_full_resolution`.

Executable descriptor: the reference representative selects a cut qubit by maximal local Pauli strength; the target descriptor records coherent information `S(B)-S(AB)` for that cut plus local XYZ expectations. This is a discriminator/lift test, not a final Axis-0 bridge doctrine.

Executable lift gate:
- full-resolution caveat: `constructed_untested_nontrivially_at_full_resolution`.
- coarse probe epoch: `M_coarse_single_qubit_Z`.
- status: `demoted_to_raw_carrier_discriminator`.
- checked quotient-class pairs: `9`.
- multi-representative classes: `3`.
- max descriptor spread: `3.7706132209499996`.
- failure count: `9`.
- Gate verdict: `FAIL`.
- Honest outcome: `Xi_ref is demoted to raw-carrier discriminator for this coarse epoch`.

## Gate 1.1 Repair Round

- Repaired UNSOUND R5: eliminated hand-set scenario booleans and modeled field tuples in z3/cvc5.
- Repaired UNSOUND R6: eliminated hand-set changed/non-step booleans and modeled concrete pre/post registers plus anti-stall fuel.
- Repaired R4 caveat: made the 40-state roster formula and probe-epoch tagging first-class artifacts.
- Repaired Xi_ref vacuity: demoted the singleton full-Pauli verdict and reran a nontrivial coarse-probe representative-independence test.

## Overall Gate Result

- all gates pass: `False`.
- accepted ceiling: `passes local rerun` if the Python, Julia, validator, and lint commands in the closeout all exit 0; never above `scratch_diagnostic` / `formal_gate_diagnostic_only` without later admission gates.
- blocked consumers: Axis-0 bridge closure, `Phi_0` evaluation, unified emergence admission, and further pipeline advancement.

Generated: 2026-07-03T22:37:17Z

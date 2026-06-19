# Independent Audit Verdict - gcm_constraint_carve_5q_v0

audit_mode: fresh read-only audit; live repo write scope limited to this file
auditor: Codex controller-local audit
audit_date: 2026-06-13
binding_inputs: standards codex including G.2a; 3Q-v0 first-failed-label FAIL lesson; 4Q PASS pattern at `77a37f018`; tribunal ban list at `f65a81010`; hardened helper

Bottom line: VERDICT = PASS_WITH_CAVEAT / GENUINE-WITH-CEILING for the 5Q ladder rung.

The packet earns the narrow 5Q count-fixture claim: `556` content-addressed
`rho_ABCDE` candidates -> `547` survivors in `9` first-qubit x/z quotient
classes. The full C1/C2/C3 matrix is present and recomputes cleanly on the
requested stratified sample; all candidate states are stored; GHZ5/W5/cluster
rows are full-matrix rows; the 4Q regression is `546/9`; the 3Q regression is
`545/9`; and read-only strict envelope/helper checks are green.

Caveat: the 15 bipartitions store names plus representative entropy/MI rows, but
not per-cut reduced matrices for every 5Q candidate. This is the same unresolved
reduced-cut-state caveat carried from 4Q, not a resolved cut-state artifact.

Accepted claim ceiling:
`scratch_diagnostic_state_artifacted_5q_count_fixture`.
`promotion_allowed=false`; `formal_admission_allowed=false`.

Citation rule: cite this only as a carrier-and-pins-relative, state-artifacted
5Q scratch-diagnostic count fixture with full C1/C2/C3 matrix rows. Do not cite
it as geometry, terrain, formal admission, THE manifold, bridge/axis/physics
evidence, SLOCC or five-party entanglement-classification evidence, residual
5-tangle evidence, a 5Q registry freeze, or stored per-cut reduced-state evidence.
Because this 5Q packet is currently untracked in the working tree, cite the result
artifact path and `result_sha256`, not a commit, until it is checkpointed.

## Route Truth

Wizard/subagent route truth is PARTIAL. Native Codex subagents were not spawned:
the available subagent tool is only authorized when the user explicitly asks for
delegation. This verdict rests on direct source/result reads, read-only local
tools, independent recomputation from stored matrices, and no-write packet
inspection.

No git add, commit, generated result rewrite, validator rewrite, or normal packet
test run was performed. The normal pytest/validator paths would rewrite result
files, which is outside this audit's write boundary.

## 1. Matrix

PASS.

Independent recomputation from stored `rho_ABCDE` matrices checked a stratified
sample of `60` candidates: all `9` killed rows, GHZ5, W5, cluster_linear_5, and
`51` survivors. Every sampled C1/C2/C3 cell matched the stored matrix.

```text
candidate_count = 556
survivor_count = 547
killed_count = 9
quotient_class_count = 9
sample_size = 60
matrix_mismatch_count = 0
kill_counts_by_constraint = {"C1": 1, "C2": 5, "C3": 7}
```

Named full-matrix rows:

```text
GHZ5             C1=true  C2=false C3=false failed=C2,C3
W5               C1=true  C2=true  C3=false failed=C3
cluster_linear_5 C1=true  C2=false C3=false failed=C2,C3
```

The first-failed field is display-only. The packet stores `all_failed_constraints`
and every C1/C2/C3 cell, so the 3Q-v0 first-failed-label disease is absent in the
sampled audit path.

## 2. State Storage

PASS.

Six stored `rho_ABCDE` artifacts were loaded and checked directly:
`4q_lift_0`, `4q_lift_544`, `4q_lift_545`, `GHZ5`, `W5`, and
`locally_rotated_generalized_GHZ5_anchor`.

For all six:

```text
trace_real = 1.0
trace_imag = 0.0
hermitian_error = 0.0
min_eigenvalue = 0.0
content_id_rule matched = true
single-cell mutation changed content id = true
```

This passes the storage and mutation-sensitivity check.

## 3. 5-Party Monogamy Narrowing

PASS.

The packet names the narrowed form as the Osborne-Verstraete N-qubit CKW
focus-qubit inequality and states the check as
`C(qi|rest)^2 >= sum_j C(qi,qj)^2` for stored pure survivor states. It explicitly
sets `residual_5_tangle_claimed=false` and
`higher_party_residual_allocation_claimed=false`.

Stored result:

```text
computed_from_stored_rho_ABCDE = true
pure_survivor_count_checked = 3
all_focus_qubits_satisfy_ckw = true
```

This is honest narrowing. It is not a five-party residual-tangle claim and not a
five-party entanglement-classification result.

## 4. Bipartitions

PASS_WITH_CAVEAT.

The packet stores all `15` 5Q bipartition names:

```text
q0|q1234
q1|q0234
q2|q0134
q3|q0124
q4|q0123
q01|q234
q02|q134
q03|q124
q04|q123
q12|q034
q13|q024
q14|q023
q23|q014
q24|q013
q34|q012
```

There are `6` representative cut rows and each has all `15` cuts with entropy/MI
values. But `per_cut_reduced_matrices_stored=false`, with the explicit caveat:
per-cut reduced matrices are not stored for all 5Q candidates in this tractable
count fixture.

## 5. Cross-Rung, Controls, Feedstock, G.2a

PASS.

Cross-rung:

```text
4Q input survivors = 546
5Q product lifts surviving = 546
Tr_E reproduces 4Q state count = 546
max_abs_delta_TrE_vs_4q_rho = 0.0
```

Regressions:

```text
4Q = 546 survivors / 9 classes at 77a37f018
3Q = 545 survivors / 9 classes
1Q/2Q/3Q object and registry hashes match expected lineage
```

Controls:

```text
empty-C survivor_count = 556
cliff_overconstrained survivor_count = 0
erasure-bite = true for C1, C2, C3 drops
probe-scramble quotient moved: 9 -> 6 classes
source-recompute injection-red = true; caught terrain, atlas, Se
```

Feedstock and floor:

```text
consume_existing_feedstock_never_rebuild = true
geo_s1_five_qubit_safety_margin_exact_v0 pin = 5c307e272a57500790253697e7d9ca2682e9ae3fd57e35098c5ab57b62213f47
stage_lifted_spinor_shell_n5_v0 pin = c577080b23533b15807d4e7f87ab6fdd82897f3cbc1e7b600d499e9152d95ffc
Cl(10) rows consumed, not rebuilt
```

G.2a:

```text
builder_audit_boundary source exists = true
builder_audit_boundary git_last_commit = aed311e85
no_builder_audit_verdict = true
no_builder_audit_verdict_envelope_gate = true
boundary_helper_fully_used = true
```

The packet is file-disjoint from this audit verdict and the audit verdict header
declares an independent fresh audit.

## 6. Strict Checks And Ban List

PASS.

Read-only commands run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/helper_process_audit.py --strict
```

Result: `all_pass=true`, `helper_process_count=0`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/gcm_constraint_carve_5q_v0/results/gcm_constraint_carve_5q_v0_envelope_results.json
```

Result: `ok=true`.

The envelope reports all three lanes ran: Julia with `Graphs`, JAX with
`networkx/sympy/z3/cvc5`, and PyTorch with `torch.func/sympy`. The source-backed
three-engine validator accepts the envelope.

Ban-list result: no positive geometry, terrain, admission, manifold, bridge, axis,
physics, canonical, SLOCC, or entanglement-classification claim is accepted by the
packet. Literal hits are confined to negative/fence fields, blocked consumers,
claim-ceiling text, and the terrain-injection red-control guard. The operative
claim language stays count-fixture.

## 7. Final Classification

Keep:
`gcm_constraint_carve_5q_v0` as a state-artifacted 5Q scratch-diagnostic count
fixture: `556 -> 547 / 9`, with full C1/C2/C3 matrix, stored `rho_ABCDE`, 4Q/3Q
regressions, 15 cut names, narrowed CKW focus-qubit checks, and strict green
envelope/helper checks.

Audit further:
per-cut reduced matrices for all 15 bipartitions if any future consumer wants
stored reduced-cut-state evidence.

Demote:
any citation that calls this geometry, terrain, formal admission, THE manifold,
bridge/axis/physics evidence, SLOCC separation, five-party residual-tangle
evidence, five-party entanglement classification, or stored per-cut reduced-state
evidence.

Broken/blocked:
none for the narrow count-fixture claim. The only open caveat is the reduced-cut
state storage gap.

Next build:
emit per-cut reduced matrices for all 5Q candidates or keep downstream citations
strictly at the current count-fixture ceiling.

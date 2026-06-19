# Independent Audit Verdict - gcm_constraint_carve_4q_v0

audit_mode: fresh read-only audit; live repo write scope limited to this file
freshness_tier: TIER-2 results-available; 3Q v0 FAIL lesson and 3Q v1 PASS pattern were exposed by the prompt
auditor: Codex controller-local audit
audit_date: 2026-06-13
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_inputs: standards codex including G.2a; 3Q v0 demotion lesson; 3Q v1 state-artifacted PASS pattern; hardened helper; current packet source/results

Bottom line: VERDICT = PASS_WITH_CAVEAT / GENUINE-WITH-CEILING for the 4Q count fixture, not strict-green for every builder subclaim.

The packet earns the requested 4Q ladder rung at the narrow ceiling:
`555` content-addressed `rho_ABCD` candidates -> `546` survivors in `9`
first-qubit x/z quotient classes. It stores every candidate state, emits the full
C1/C2/C3 matrix for every candidate, reproduces the 3Q product-lift regression
`545/9`, passes the read-only-safe strict checks, and handles the 4-party CKW row
as a narrowed focus-qubit inequality rather than a residual 4-tangle claim.

Caveat: the packet does not store reduced density matrices for each 4Q bipartition.
It stores the 7 cut names and representative entropy/mutual-information summaries.
Do not cite it as a stored reduced-cut-state artifact until those reduced states are
actually emitted.

Accepted claim ceiling:
`scratch_diagnostic_state_artifacted_4q_count_fixture`.
`promotion_allowed=false`; `formal_admission_allowed=false`.

This may be cited as a carrier-and-pins-relative, state-artifacted 4Q scratch
diagnostic count fixture. It must not be cited as formal QIT-floor admission, THE
manifold, bridge/axis/physics evidence, a SLOCC GHZ/W/cluster separator, a residual
4-tangle result, or a reduced-cut-state artifact.

## Route Truth

Wizard/subagent route truth is PARTIAL. I did not spawn native Codex subagents in
this turn; the verdict rests on direct source reads, local tools, existing result
artifacts, in-memory no-write rebuild/validation, and independent recomputation from
stored matrices.

The local `work` skill's handoff-write requirement was blocked by the user's
read-only boundary. No handoff, git add, commit, or generated result rewrite was
performed.

## 1. Full C1/C2/C3 Matrix

PASS.

Independent recomputation from stored `rho_ABCD` matrices checked all `555 x 3`
C1/C2/C3 cells:

```text
candidate_count = 555
states_by_content_id = 555
candidate_state_index = 555
survivor_states = 546
survivor_count = 546
killed_count = 9
quotient_class_count = 9
full_matrix_mismatch_count = 0
content_id_mismatch_count = 0
```

The requested stratified sample was `90` candidates, including GHZ4, W4,
cluster_linear_4, all `9` killed rows, at least `30` survivors, and all quotient
classes. The full matrix was also recomputed, so the sample is not carrying the
verdict by itself.

Killed rows:

```text
545 GHZ4                                  failed C2,C3
546 W4                                    failed C3
547 cluster_linear_4                      failed C2,C3
548 product_0000                          failed C3
549 lifted_ladder_n4_feedstock_product_anchor failed C3
551 invalid_trace_anchor                  failed C1
552 GHZ4_minus                            failed C2,C3
553 biseparable_Bell_AB_tensor_00CD       failed C2,C3
554 order_only_no_probe_anchor            failed C2
```

`first_failed_constraint_display_only` is present on every row, so literal absence
is not true. The 3Q v1 discipline is nevertheless satisfied: every row also stores
all three constraint cells and `all_failed_constraints`, and the first-failed field
is display-only, not the mechanism or evidence surface.

## 2. GHZ4 / W4 / Cluster Mechanisms

PASS.

Matrix rows from independent recomputation:

```text
GHZ4             = C1 true, C2 false, C3 false
W4               = C1 true, C2 true,  C3 false
cluster_linear_4 = C1 true, C2 false, C3 false
```

Mechanism:

```text
GHZ4 first-qubit Bloch = [0.0, 0.0, 0.0], x/z signature = [0, 0], order_gap = 0.0
W4   first-qubit Bloch = [0.0, 0.0, 0.5], x/z signature = [0, 1], order_gap = 0.0
cluster first-qubit Bloch = [0.0, 0.0, 0.0], x/z signature = [0, 0], order_gap = 0.0
```

The honest statement is local-fixture only: W4 is more admissible than GHZ4 because
it passes C2 first-qubit x/z distinguishability; both fail C3 persistence/order-gap.
The cluster representative is killed by the same C2+C3 pattern as GHZ4. The surviving
4-party boundary anchor is `locally_rotated_generalized_GHZ4_anchor`, not the cluster
state.

## 3. State Storage

PASS.

All `555` candidates have stored content-addressed `rho_ABCD` matrices under the
packet rule `rhoabcd_<sha256(canonical rho_ABCD JSON)[:24]>`. The mutation-sensitive
check changed one matrix entry and changed the derived id from
`rhoabcd_0030690041fe264cfa3df2fc` to `rhoabcd_42a4615259e831cbdd16ae27`.

Eight loaded states passed the requested storage checks:

```text
3q_lift_0                                herm=0 trace=1.0 min_eig=0 id_ok=true
3q_lift_17                               herm=0 trace=1.0 min_eig=0 id_ok=true
3q_lift_544                              herm=0 trace=1.0 min_eig=0 id_ok=true
GHZ4                                     herm=0 trace=1.0 min_eig=0 id_ok=true
W4                                       herm=0 trace=1.0 min_eig=0 id_ok=true
cluster_linear_4                         herm=0 trace=1.0 min_eig=0 id_ok=true
locally_rotated_generalized_GHZ4_anchor  herm=0 trace=1.0 min_eig=0 id_ok=true
invalid_trace_anchor                     herm=0 trace=1.2 min_eig=0 id_ok=true
```

The invalid trace row is correctly killed by C1.

## 4. 4-Party CKW Narrowing

PASS.

The packet names the narrowed form as the Osborne-Verstraete N-qubit CKW focus-qubit
inequality and explicitly sets `residual_4_tangle_claimed=false`. It does not claim a
residual 4-tangle, SLOCC classification, or general monogamy theorem.

Independent recomputation from stored `rho_ABCD` matched the packet rows:

```text
3q_lift_544:
  q0 margin 0.1875; q1 margin 0.1875; q2 margin 0.1875; q3 margin 0.0

locally_rotated_generalized_GHZ4_anchor:
  q0 margin 0.1875; q1 margin 0.1875; q2 margin 0.1875; q3 margin 0.1875
```

This is an honest narrowed focus-qubit check for stored pure survivor states only.

## 5. 7 Bipartitions

PASS for cut-lattice enumeration. FAIL for the stronger reduced-state-storage
subclaim.

The packet stores the expected 7 4Q bipartitions:

```text
q0|q123
q1|q023
q2|q013
q3|q012
q01|q23
q02|q13
q03|q12
```

It stores representative cut rows for `3q_lift_544` and
`locally_rotated_generalized_GHZ4_anchor`, but those rows contain `S_left`,
`S_right`, `S_full`, and `mutual_I`, not reduced density matrices. I found no
`rho_left`, `rho_right`, `reduced_rho`, or equivalent stored reduced-state fields in
source or result JSON.

## 6. Cross-Rung, Controls, G.2a, Coordinates

PASS.

Cross-rung embedding:

```text
3Q input survivors = 545
4Q product lifts = 545
all_3q_survivors_have_one_4q_lift = true
Tr_D_reproduces_3q_state_count = 545
max_abs_delta_TrD_vs_3q_rho = 0.0
3Q regression survivor/class count = 545/9
```

Quotient classes:

```text
Q0-Q7: eight inherited 3Q product-lift classes, 68 rows each
Q8: signature [2,1], 2 rows = 3q_lift_544 + locally_rotated_generalized_GHZ4_anchor
```

Controls:

```text
empty_C survivor_count = 555
cliff_overconstrained survivor_count = 0
erasure_bite = true for C1, C2, C3
probe_scramble = 9 -> 6 classes, quotient_moved=true
source_recompute_injection_red = true, caught terrain/atlas/Se
terrain_blindness_guard.clean = true
1Q/2Q/3Q lineage-free negatives = red with error codes
```

G.2a:

```text
builder_gates.file_disjoint_packet = true
builder_gates.boundary_helper_fully_used = true
builder_gates.G_2a_idempotency_from_birth = true
no_builder_audit_verdict = true
no_builder_audit_verdict_envelope_gate = true
```

Coordinates:

```text
layers = 1-2 (+17 tensor)
operation = carve
qubit_depth = 4Q
```

## Checks Run

Read-only-safe checks:

```text
make helper-process-audit-strict
  all_pass=true; helper_process_count=0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
  fresh build_packet(write=False, include_helper_preflight=True)
  validate_payload(..., require_helper_preflight=True)
  fresh_all_pass=true; errors=[]; survivor_count=546; class_count=9
  normalized_existing_equals_fresh=true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
  validate_three_engine_sim_result envelope with require_pytorch=true,
  strict_source_backed=true, require_tool_intent=true
  errors=[]

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
  independent all-555 C1/C2/C3 recomputation from stored rho_ABCD
  full_matrix_mismatch_count=0; content_id_mismatch_count=0
```

Existing lane artifacts read:

```text
julia all_pass=true survivor_count=546 quotient_class_count=9
jax all_pass=true survivor_count=546 quotient_class_count=9
pytorch all_pass=true survivor_count=546 quotient_class_count=9
validator ok=true errors=[]
```

I did not run packet scripts, validator scripts, or pytest directly because this audit
was read-only except for `audit_verdict.md`, and those paths rewrite generated result
JSON or cache artifacts.

## Citation Rule

Allowed citation:

> `gcm_constraint_carve_4q_v0` is a state-artifacted 4Q scratch diagnostic count
> fixture. It stores `555` content-addressed `rho_ABCD` candidates, emits a full
> C1/C2/C3 matrix for every candidate, computes `555 -> 546` survivors in `9`
> first-qubit x/z quotient classes, records GHZ4 as `(C1 T, C2 F, C3 F)`, W4 as
> `(C1 T, C2 T, C3 F)`, cluster_linear_4 as `(C1 T, C2 F, C3 F)`, reproduces the
> 3Q product-lift/Tr_D regression `545/9`, and checks a narrowed Osborne-Verstraete
> focus-qubit CKW inequality for stored pure survivors.

Required caveats:

- Claim ceiling is `scratch_diagnostic_state_artifacted_4q_count_fixture`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- Carrier and pins are local to this C1/C2/C3 first-qubit x/z fixture.
- GHZ4/W4/cluster wording is local admissibility only.
- Cluster is killed here; it is not the new admitted 4Q object.
- The cut lattice has 7 named bipartitions and representative entropy summaries, but
  not stored reduced density matrices per cut.
- The packet directory is currently untracked in this checkout.

Forbidden citation:

- Do not cite as formal QIT-floor admission.
- Do not cite as THE manifold, canonical geometry, bridge/axis/stage/physics evidence.
- Do not cite as a SLOCC GHZ/W/cluster separator.
- Do not cite as a residual 4-tangle or general monogamy theorem.
- Do not cite as stored reduced-cut-state evidence.

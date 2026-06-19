# Independent Audit Verdict - gcm_constraint_carve_3q_v1

audit_mode: fresh read-only audit; live repo write scope limited to this file
freshness_tier: TIER-2 results-available; prior v0 FAIL verdict and builder repair claims were exposed by the prompt
auditor: Codex controller-local audit
audit_date: 2026-06-13
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_inputs: standards codex including G.2a; gcm_constraint_carve_3q_v0 FAIL verdict; hardened helper; current packet source/results

Bottom line: VERDICT = PASS / GENUINE-WITH-CEILING for the requested floor repair.

The v1 packet satisfies the v0 five-point repair contract at the declared ceiling:
actual `rho_ABC` states are stored under content IDs, the full 552-row C1/C2/C3
matrix recomputes independently, GHZ/W is now stated from the matrix rather than
first-failed bookkeeping, CKW is recomputed from the stored surviving anchor
`rho_ABC`, and the strict fixes are green in this checkout.

Accepted claim ceiling:
`scratch_diagnostic_state_artifacted_3q_count_fixture`.
`promotion_allowed=false`; `formal_admission_allowed=false`.

This may now be cited as a repaired, state-artifacted 3Q scratch diagnostic QIT-floor
fixture: `552` content-addressed `rho_ABC` candidates -> `545` survivors in `9`
first-qubit x/z probe classes; GHZ matrix row `(C1 T, C2 F, C3 F)`; W matrix row
`(C1 T, C2 T, C3 F)`; one locally rotated generalized-GHZ survivor with CKW margin
`0.1875` on all three cuts recomputed from stored `rho_ABC`.

It must not be cited as formal QIT-floor admission, THE manifold, a SLOCC GHZ/W
separator, an axis/bridge/physics result, or canonical manifold evidence.

## Route Truth

Wizard/subagent route truth is PARTIAL. I did not spawn native Codex subagents because
the callable `spawn_agent` tool in this session is restricted to explicit user
authorization for delegation. The verdict rests on direct source reads, local tools,
fresh no-write/in-memory recomputation, and strict validators.

The local `work` skill's handoff-write step was blocked by the user's write boundary.
No handoff, git add, commit, or generated result rewrite was performed.

## 1. Full C1/C2/C3 Matrix

PASS.

Independent recomputation over all stored states checked every matrix cell:

```text
candidate_state_index_len = 552
unique_state_count = 552
constraint_matrix_len = 552
survivor_count = 545
survivor_states_len = 545
quotient_class_count = 9
cell_mismatch_count_all_552x3 = 0
all_failed_constraints_mismatch_count = 0
content_id_mismatch_count = 0
```

The matrix is not a first-failed ledger. Every row stores all three pass/fail cells.
`first_failed_constraint_display_only` is consistent with the full failed list and is
not the evidence surface.

The requested "20 killed" sample clause is arithmetically impossible for this packet:
there are only `7` killed candidates because `552 - 545 = 7`. I audited all `7` killed
rows and a deterministic `100`-candidate sample that included GHZ, W, the surviving
entangled anchor, all killed rows, and survivors. The full `552 x 3` matrix was also
audited, so the sample requirement is exceeded except for the impossible killed-row
count.

Killed rows:

```text
544 GHZ                              failed C2,C3
545 W                                failed C3
546 biseparable_Bell_AB_tensor_0C    failed C2,C3
547 product_000                      failed C3
549 invalid_trace_anchor             failed C1
550 GHZ_minus                        failed C2,C3
551 order_only_no_probe_anchor       failed C2
```

The quotient classes are eight inherited 2Q/product-lift classes of `68` rows each plus
one singleton class for the locally rotated generalized-GHZ anchor.

## 2. GHZ/W Mechanisms

PASS.

The honest matrix is:

```text
GHZ = C1 true, C2 false, C3 false
W   = C1 true, C2 true,  C3 false
```

Mechanism check:

```text
GHZ rho_A Bloch = [0.0, 0.0, 0.0]
GHZ x/z signature = [0, 0]
GHZ order_gap = 0.0

W rho_A Bloch = [0.0, 0.0, 0.333333333333]
W x/z signature = [0, 1]
W order_gap = 0.0
```

C2 fails GHZ because the first marginal is maximally mixed in the x/z probe pair. C2
passes W because W's first marginal is x/z-distinguishable under the local adapter pin.
C3 fails both: the persistence/order-gap computation gives `0.0` for GHZ and `0.0`
for W.

Accepted wording:

> W is strictly more admissible than GHZ under this local C1-C3 fixture. The separating
> constraint is first-qubit x/z distinguishability (C2). The common killer is
> persistence/order-gap (C3).

Forbidden widening: this is not a SLOCC GHZ/W separator and not formal QIT-floor
admission.

## 3. CKW From Stored States

PASS.

The surviving tripartite-entangled row is:

```text
candidate_id = 548
survivor_id = 544
state_id = locally_rotated_generalized_GHZ_anchor
rho_ABC_content_id = rhoabc_8325d0b8f1ead2ed0044791a
first_bloch = [0.75, 0.3, 0.4]
probe_signature = [2, 1]
order_gap = 1.0
```

Independent CKW recomputation from the stored `rho_ABC` gives:

```text
A|BC: one_tangle=0.1875, pairwise_sum=0.0, margin=0.1875
B|AC: one_tangle=0.1875, pairwise_sum=0.0, margin=0.1875
C|AB: one_tangle=0.1875, pairwise_sum=0.0, margin=0.1875
```

The 2Q audit's `OPEN_REQUIRES_3Q_FOR_CKW` is closed for this packet's one stored
surviving tripartite anchor. The earned language is narrow: CKW inequality closure from
a stored 3Q density matrix for the surviving generalized-GHZ anchor. It is not a general
monogamy theorem, formal admission, or broader QIT-floor proof.

## 4. State Storage

PASS.

All `552` candidate state IDs are content-derived by the packet rule
`rhoabc_<sha256(canonical rho_ABC JSON)[:24]>`. No content-ID mismatches were found.
There are `545` survivor-state rows with stored `rho_ABC` matrices.

Ten loaded state records were checked for content ID, Hermiticity, trace, and spectrum:
`2q_lift_0` through `2q_lift_4`, GHZ, W, the locally rotated generalized-GHZ anchor,
`invalid_trace_anchor`, and `2q_lift_543`.

The valid rows have Hermiticity error `0.0`, trace approximately `1.0`, and nonnegative
spectrum up to numerical roundoff. The deliberate `invalid_trace_anchor` has trace
`1.2` and is correctly killed by C1.

## 5. Strict Fixes, Regressions, G.2a, Coordinates

PASS.

Fresh checks:

```text
scripts/helper_process_audit.py --strict
  all_pass=true, helper_process_count=0

pytest -q -p no:cacheprovider system_v6/sims/gcm_constraint_carve_3q_v1/tests/test_gcm_constraint_carve_3q_v1.py
  5 passed

fresh in-memory build_packet(include_helper_preflight=True)
  all_pass=true
  validate_payload errors=[]

validate_three_engine_sim_result envelope, require_pytorch=true,
strict_source_backed=true, require_tool_intent=true
  error_count=0

Julia no-write Graphs check
  graphs_imported=true, vertices=9, edges=8, component_count=1, all_pass=true

gcm_constraint_carve_3q_v1_boundary.boundary_payload()
  builder_audit_boundary_ok=true, errors=[]
```

The existing result estate is nonvolatile-equal to a fresh packet rebuild after ignoring
`generated_at`, `result_sha256`, and the live helper-preflight timestamp. Existing lane
results report `julia=true`, `jax=true`, `pytorch=true`; existing validator result has
`ok=true` and `errors=[]`.

Lineage and ledger:

```text
1Q substrate check ok=true
2Q registry substrate check ok=true
lineage-free negative red=true
ledger_lock_refreshed.refreshed_from_disk=true
ledger sha256 = cf863089bc0c5fc8483fcb0ff31f00eb577a711f52e0c84b67981de4d425b2c4
ledger git_last_commit = 1778ad021
```

Terrain-blindness and injection-red:

```text
terrain_blindness_guard.clean=true
controls.injection_red.red=true
in-memory injected C2 predicate "terrain atlas Se"
  validate_payload -> terrain blindness guard failed
```

Regressions and cross-rung embeddings:

```text
candidate_count = 552
survivor_count = 545
quotient_class_count = 9
product_embedding_from_2q_count = 544
all_lifted_survive = true
Tr_C image equals 2Q survivor local pin set = true
pair_entanglement_not_claimed = true
```

Coordinates:

```text
layers = 1-2 (+17)
operation = carve
qubit_depth = 3Q
```

G.2a passes for this packet shape. The builder boundary helper is used from birth, the
packet declares `no_builder_audit_verdict=true`, and this file's header declares
independent fresh/read-only audit status.

## Citation Rule

Allowed citation:

> `gcm_constraint_carve_3q_v1` is a repaired, state-artifacted 3Q scratch diagnostic
> count fixture. It stores `552` content-addressed `rho_ABC` candidates, emits the full
> C1/C2/C3 matrix for every candidate, recomputes `552 -> 545` survivors in `9`
> first-qubit x/z probe classes, records GHZ as `(C1 T, C2 F, C3 F)` and W as
> `(C1 T, C2 T, C3 F)`, and recomputes CKW margin `0.1875` on all three cuts from the
> stored surviving locally rotated generalized-GHZ `rho_ABC`.

Required caveats:

- Claim ceiling is `scratch_diagnostic_state_artifacted_3q_count_fixture`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- GHZ/W wording is local-fixture admissibility: W is more admissible than GHZ because it
  passes C2; both fail C3.
- CKW closure is earned for the one stored surviving tripartite anchor only.
- The packet directory is currently untracked in this checkout.

Forbidden citation:

- Do not cite as formal QIT-floor admission.
- Do not cite as THE manifold, canonical geometry, bridge/axis/stage/physics evidence.
- Do not cite as a SLOCC GHZ/W class separator.
- Do not cite as a general CKW/monogamy theorem.

## Checks Run

Commands were run with `PYTHONDONTWRITEBYTECODE=1` where Python imports were involved;
pytest used `-p no:cacheprovider` to avoid writing `.pytest_cache`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/helper_process_audit.py --strict
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/gcm_constraint_carve_3q_v1/tests/test_gcm_constraint_carve_3q_v1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'  # fresh packet + strict envelope validation, no live result write
julia --project=system_v5/julia_carrier -e 'using JSON3, Graphs; ...'  # no-write Graphs check
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'  # in-memory terrain injection-red check
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'  # independent 552x3 matrix, storage, GHZ/W, CKW recomputation
```


# Independent Audit Verdict - gcm_constraint_carve_3q_v0

audit_mode: independent fresh read-only audit; live repo read-only except this file
freshness_tier: TIER-2 results-available; builder claims exposed in prompt; no prior target audit
auditor: Codex controller-local audit
audit_date: 2026-06-12
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_inputs: standards codex incl G.2a; 1Q/2Q carve audits; Panel 11 Q3; 2Q freeze/cut audit; hardened helper check

Bottom line: VERDICT = FAIL_AS_HEADLINE / DEMOTE_TO_SCRATCH_COUNT_FIXTURE.

The executable count fixture recomputes: `552` candidates, `545` survivors, `9`
probe classes, `544` product lifts, and one surviving tripartite-entangled
anchor. That narrow count result is real inside the packet's own pinned
candidate family.

The claimed QIT-floor rung does not pass audit. The differential GHZ/W kill
fails the required cross-check: GHZ is killed by C2, but GHZ also fails C3
under the packet's own order-gap computation. The packet's
`constraints_distinguish_GHZ_and_W=true` is therefore only a first-failed-label
fact, not the two-mechanism separation claimed. CKW closure is also not earned:
the lone entangled survivor has hardcoded CKW fields and no stored/recomputed
3Q state or density matrix. Strict source-backed validation fails, and strict
helper preflight is red.

Accepted ceiling: `scratch_diagnostic_count_fixture_only`.
`promotion_allowed=false`; `formal_admission_allowed=false`; not a QIT-floor
admission; not a SLOCC-class separator; not CKW closure; not final Cl(6)
survivor structure; not terrain/atlas/manifold/axis/bridge/physics evidence.

## Citation Rule

Cite this packet only as:

`gcm_constraint_carve_3q_v0` is a scratch fixture over `544` 2Q product-lift
candidates plus `8` hand-pinned 3Q anchors. Under the packet's C1-C3 predicates
it recomputes `552 -> 545` survivors in `9` first-qubit x/z probe classes, with
all `544` product lifts surviving and one hand-pinned locally rotated
generalized-GHZ anchor surviving.

Every citation must also carry:

- claim ceiling: `scratch_diagnostic_count_fixture_only`;
- `promotion_allowed=false`, `formal_admission_allowed=false`;
- GHZ/W caveat: standard GHZ fails both C2 and C3; W passes C2 and fails C3;
  the advertised distinction is first-failed-label-only;
- CKW caveat: the `0.1875` margin is not recomputed from an artifacted 3Q
  density/state;
- strict gate caveat: `--strict-source-backed` fails on the Julia `Graphs`
  declaration, and helper strict preflight is red.

Do not cite this as a QIT floor rung, a SLOCC GHZ/W class separation, CKW
monogamy closure, a final 3Q manifold/terrain object, a source-backed strict
three-engine result, or a clean substrate/helper admission.

## Authority And Route Truth

Read authority:

- `AGENTS.md`
- `CODEX.md`
- `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
- `system_v5/docs/LEGO_SIM_CONTRACT.md`
- `system_v6/receipts/audit_standards_codex_v1.md`
- `system_v6/receipts/panel11_blind_wave_targets_20260612.md`
- `system_v6/sims/gcm_constraint_carve_floor_v0/audit_verdict.md`
- `system_v6/sims/gcm_constraint_carve_2q_v0/audit_verdict.md`
- `system_v6/sims/gcm_2q_freeze_and_cut_v0/audit_verdict.md`
- `system_v6/sims/gcm_constraint_carve_3q_v0/*`

Wizard v4.2 route truth: PARTIAL. The controller loaded the v4.2 packet and
sim-audit spine, but native subagent spawning was not used because this runtime
allows `spawn_agent` only when the user explicitly asks for delegation. No
worker report is accepted as evidence. The verdict rests on direct source reads,
no-write recomputation, result inspection, and validator calls.

I did not run pytest or validator `main()` because the test suite and validator
entrypoint can write generated result JSONs. I used no-write validator imports
and read-only shared validators instead.

## Differential Kill

FAIL for the headline.

Independent state check for standard representatives:

```text
GHZ rho_A = [[0.5, 0.0], [0.0, 0.5]]
GHZ first Bloch = [0.0, 0.0, 0.0]
GHZ x/z probe pair = [0.0, 0.0]

W rho_A = [[0.666666666667, 0.0], [0.0, 0.333333333333]]
W first Bloch = [0.0, 0.0, 0.333333333333]
W x/z probe pair = [0.0, 0.333333333333]
```

The C2 lineage is real: GHZ has maximally mixed first marginal, so the local
x/z probe family cannot distinguish it. This is the same local-marginal
mechanism accepted in the 2Q Bell-diagonal kill row.

The C3 cross-check fails:

```text
GHZ: C1=true, C2=false, C3=false, order_gap=0.0
W:   C1=true, C2=true,  C3=false, order_gap=0.0
```

The kill ledger confirms the problem:

```text
GHZ all_failed_constraints = [C2, C3], killed_by = C2
W   all_failed_constraints = [C3],     killed_by = C3
```

So GHZ does not pass C3. The claimed differential structure collapses to:

- GHZ: first failed at C2, but also fails C3.
- W: passes C2 and fails C3.

That is not a two-mechanism GHZ/W class separation. It is a first-failed-label
artifact. The SLOCC ceiling is lower still: the standard GHZ and the locally
rotated generalized-GHZ anchor are in the same GHZ family, but one is killed and
the other survives because the predicates are probe-frame/local-marginal
dependent. This realization does not separate SLOCC classes.

## Candidate Space

PASS for explicit construction; FAIL for broad/unbiased 3Q carve claims.

The candidate space is exactly:

```text
544 2q_survivor_product_lift rows
8 entangled_boundary_anchor rows
552 total candidates
```

The eight anchors are hand-pinned rows: `GHZ`, `W`,
`biseparable_Bell_AB_tensor_0C`, `product_000`,
`locally_rotated_generalized_GHZ_anchor`, `invalid_trace_anchor`, `GHZ_minus`,
and `order_only_no_probe_anchor`.

This is much smaller than the 2Q `15783` candidate space because it is not a 3Q
density-space enumeration. It is a 2Q-survivor lift plus an eight-row anchor
fixture. That is acceptable only at scratch-fixture ceiling. It is fitting-prone
for the claimed GHZ/W story because the lone tripartite survivor is a hand-pinned
locally rotated generalized-GHZ anchor with active first-qubit probes.

The terrain-blind guard is only a predicate-token guard. It catches forbidden
terrain/atlas tokens and the injection-red control fires, but it does not blind
against hand-picking anchor Bloch vectors or hardcoding CKW fields.

## Full Recompute

PASS for the internal count fixture.

Manual no-write recomputation over all `552` candidates, including all
tripartite anchors and inherited 2Q-entangled product lifts, matched the stored
result:

```text
manual_candidate_count = 552
manual_sample_count = 552
manual_survivor_count = 545
manual_class_count = 9
manual_kill_counts =
  C1_finite_3q_density_carrier: 1
  C2_probe_distinguishability_xz_local_adapter_pin: 4
  C3_persistence_n01_order_gap: 2
manual_vs_stored_kill_mismatch_count = 0
```

The nine classes are the eight inherited 2Q/1Q x/z signatures with `68` members
each, plus one singleton `(2, 1)` class for the locally rotated
generalized-GHZ anchor.

The single tripartite survivor is:

```text
anchor_id = locally_rotated_generalized_GHZ_anchor
stored first_bloch = [0.75, 0.3, 0.4]
stored probe_signature = [2, 1]
stored order_gap = 1.0
stored CKW = tau_A_BC 0.1875, tau_AB_plus_tau_AC 0.0, margin 0.1875
```

Why it survives C2/C3 inside this packet:

- C2 passes because the first-qubit x/z signature is `(2, 1)`, not `(0, 0)`.
- C3 passes because the packet's rounded first-qubit order-gap proxy moves the
  x/z signature from `(1, 1)` to `(1, 0)`, giving gap `1.0`.

What is missing: an artifacted state vector or `rho_ABC`. The row is stored as a
Bloch/CKW anchor, not as a recomputable quantum state.

## CKW Row

FAIL as CKW closure; PASS only as a hardcoded consistency readout.

The stored value is internally consistent with the first-Bloch radius:

```text
first_bloch = [0.75, 0.3, 0.4]
radius_squared = 0.8125
1 - radius_squared = 0.1875 = 3/16
```

For a pure A|BC state this would equal the one-tangle `4 det(rho_A)`. But the
packet does not store the corresponding 3Q state, does not compute pairwise
reductions `rho_AB`/`rho_AC`, and does not recompute `tau_AB` or `tau_AC` from
matrices. The `ckw` dictionary is part of the anchor data.

Therefore the 2Q audit's monogamy OPEN row is not closed by this packet. The
honest row is: `one hand-pinned GHZ-class-like anchor carries a CKW-compatible
stored margin 0.1875; CKW closure remains unearned`.

## Cl(6) Floor Rows

PASS for consumed feedstock; FAIL for survivor-specific recomputation.

The 3Q floor feedstock hash matches the expected envelope:

```text
three_q_floor hash_matches_expected = true
sha256 = b305e6e456ea04d8e7ef14b6db87a3b57ba104a05fa6c84f4f34af7d0ebd2eb4
```

Independent gamma computation over the declared gamma convention gives:

```text
Cl(6) generated Pauli-word basis dimension = 64
gamma7 eigenspace split = {-1: 4, 1: 4}
```

But `floor_rows()` copies the floor packet's `Y4/Y6` carrier rows and attaches
`candidate_survivor_count = 545`. It does not compute a gamma7 statistic on
survivor density matrices. The accepted claim is only: the survivors live on the
same consumed `C^8` carrier with the preexisting Cl(6) floor available.

## Cross-Rung Rows

PASS_WITH_SCOPE.

The metadata/lift rows pass:

```text
product_embedding_vs_2q.input_2q_survivor_count = 544
product_embedding_vs_2q.lifted_survivor_count = 544
all_lifted_survive = true
partial_trace_vs_2q.image_equals_2q_survivor_set = true
partial_trace fiber count values = {1}
```

This is an ID/fiber fact over the product-lift construction `rho_AB tensor
|0><0|_C`, not a recomputation over stored 3Q density matrices. It supports the
narrow product-lift fixture, not a full 3Q candidate-space claim.

The 2Q registry conditionality must be stated carefully. The 2Q freeze/cut audit
confirms the math unlock at scratch scope and confirms the 2Q registry/stored
state carrier, but rejects strict helper enforcement. This 3Q packet still marks
the 2Q registry as `conditional_audit_in_flight=true`; that is stale relative to
the existing 2Q audit, but the strict-helper caveat remains live.

## Gates And Controls

Mixed.

Passing or scoped-green checks:

- common payload validation and packet boundary checks: `[]`;
- shared three-engine shape validator without strict source backing: `ok=true`;
- `scripts/lint_sim_contract.py ..._common.py`: `violation_total=0`;
- G.2a fields are present from birth and use `scripts/builder_audit_boundary.py`;
- terrain token guard is clean and injection-red fires;
- all C1-C3 erasure controls bite;
- empty-C and overconstrained-C controls behave as expected.

Failing checks:

```text
validate_gcm_constraint_carve_3q_v0.validate_payload(envelope)
  -> FAIL
  packet drift against source rebuild
  exact drift:
    source_locks.climb_ledger_correction.git_last_commit
      stored: 1cf29c03d
      live:   1778ad021
    source_locks.climb_ledger_correction.sha256
      stored: 1cc557ebb1a41b572ae43a4ee72dc67601eeeb53c214fabca608dd9e673c5c7c
      live:   cf863089bc0c5fc8483fcb0ff31f00eb577a711f52e0c84b67981de4d425b2c4
```

That drift is an upstream source-lock freshness failure in the checked-in result
packet, not an audit-header/G.2a failure.

```text
validate_three_engine_sim_result.py --require-pytorch --strict-source-backed
  -> FAIL
  julia: source-backed audit failed
  declared load-bearing packages not imported in source: Graphs
```

```text
validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent
  -> FAIL
  julia.Graphs tool_intent declared but source-token-thin/not-backed
```

```text
scripts/helper_process_audit.py --strict
  -> FAIL
  helper_process_count = 15
```

The Julia lane is explicitly a JSON3/SHA/count mirror over the common packet. It
is not an independent semantic arbiter and does not import `Graphs` despite
declaring it load-bearing/aligned.

## Final Decision

Accepted only:

- a scratch count fixture over the declared `552` candidate rows;
- the internal C1-C3 predicate recomputation and kill ledger;
- product-lift metadata from 2Q survivors to 3Q candidates;
- consumed Cl(6)/C^8 floor feedstock by hash and independent carrier gamma7
  sanity check.

Rejected:

- `strict green`;
- `constraints_distinguish_GHZ_and_W=true` as a mechanism claim;
- SLOCC GHZ/W class separation;
- CKW closure of the 2Q monogamy OPEN row;
- survivor-specific Cl(6)/gamma7 computation;
- strict source-backed three-engine admission;
- fresh source-lock validator status;
- strict helper/substrate admission.

Block K:

- Gates cited: standards codex G.2a; 1Q/2Q carve discipline; Panel 11 Q3;
  full 552-row C1-C3 recompute; GHZ/W marginal and C2/C3 cross-check; CKW
  provenance check; Cl(6) feedstock hash and gamma7 sanity check; cross-rung
  metadata rows; no-write validator import; strict source-backed validator;
  source-lock drift diff; helper strict preflight.
- Admission decisions: count fixture admitted at scratch ceiling only; headline
  QIT-floor/differential/CKW claims rejected.
- Narrative substitutions intercepted: first-failed label is not a differential
  mechanism; stored CKW fields are not CKW recomputation; carrier-global Cl(6)
  feedstock is not survivor-specific gamma7 structure.
- Worker claims verified: none accepted from workers.
- Worker claims not verified: builder `strict green` rejected against fresh
  checks.
- Status label changes to registry: none.
- Blocked actions: no git add/commit; no generated result rewrite; no pytest or
  validator main run because the live write boundary allowed only this file.

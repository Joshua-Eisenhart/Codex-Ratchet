# Independent Audit Verdict - gcm_constraint_carve_2q_v0

audit_mode: independent fresh read-only audit; live repo read-only except this file
freshness_tier: TIER-2 results-available with independent source recomputation
auditor: Codex cross-backend auditor
audit_date: 2026-06-12
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_inputs: 1Q carve PASS verdict; terrain-blind validator pattern; Panel 11 commit 59a55f539; gcm layer-stack supplement 1

Bottom line: VERDICT = PASS_WITH_CAVEATS, not STRICT GREEN.

The second rung is sustained as a bounded 2Q boundary/control carve: the active
C1-C3 forms are literal 2Q instantiations of the repaired 1Q pins, the carve
recomputes to 15783 candidates / 1167 density rows / 544 survivors / 8 quotient
classes, the 528 product + 16 entangled-purification split is reproduced, both
cross-rung rows pass, the validator has the repaired source-recompute plus
injection-red tooth, and G.2a is wired from birth.

The strict-green wording is rejected because Panel 11's monogamy-type question
is not checked and is not explicitly named open inside the packet. This audit
marks monogamy-type constraint evidence OPEN. The entanglement mechanism that
is actually computed is local-first-marginal/probe dependent, not a monogamy
certificate and not a direct entanglement predicate.

Accepted ceiling: `scratch_diagnostic_carrier_and_pins_relative_2q_boundary_control_rung`.
`promotion_allowed=false`; `formal_admission_allowed=false`; not THE manifold;
not terrain/atlas admission; not axis/engine/physics admission; not monogamy
evidence.

## Citation Rule

Cite this packet only as:

`gcm_constraint_carve_2q_v0` gives a carrier-and-pins-relative 2Q boundary
carve with C1-C3 terrain-blind local-adapter predicates, 544 survivors in 8
first-qubit x/z quotient classes, all 16 pinned 1Q survivors embedded by
product, and exact partial-trace image equality back to the 1Q survivor set.

Every citation must also carry:

- claim ceiling: `scratch_diagnostic`;
- `promotion_allowed=false`, `formal_admission_allowed=false`;
- identity leak caveat: identity-inclusive leakage is detected; after excluding
  row identity/fingerprints, best non-identity predictor accuracy is
  `0.965532535006 < 1.0`;
- monogamy-type constraint row: OPEN / not checked by this packet;
- strict-green wording: rejected by this audit.

Do not cite this as final `M(C)`, terrain/atlas residency, a QIT-engine runtime
object, a monogamy result, bridge/physics evidence, or canonical process
admission.

## Authority And Route Truth

Read authority:

- `AGENTS.md`
- `CODEX.md`
- `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
- `system_v5/docs/LEGO_SIM_CONTRACT.md`
- `system_v6/receipts/audit_standards_codex_v1.md`
- `system_v6/receipts/gcm_layer_stack_reference_20260612.md`
- `system_v6/receipts/panel11_blind_wave_targets_20260612.md`
- `system_v6/sims/gcm_constraint_carve_v1/audit_verdict.md`
- `system_v6/sims/gcm_constraint_carve_2q_v0/*`

Wizard v4.2 route truth: PARTIAL. The controller loaded the v4.2 runtime packet
and spawned three Codex explorer lanes, but no subagent receipt returned before
this verdict was written. No worker report is accepted as evidence in this file.
The verdict rests on direct source reads, in-process no-write validator calls,
fresh no-write backend recomputation, and result inspection.

I did not run the packet validator `main()` or pytest live because both can
write `results/gcm_constraint_carve_2q_v0_validator_results.json`. Instead I
called validator functions in-process without invoking their writer entry point.

## Constraint Instantiation

PASS_WITH_SCOPE.

The 1Q repaired carve pins active C as C1-C3 only:

- `C1_finite_density_carrier`: finite Bloch-grid density row.
- `C2_probe_distinguishability_xz_local_adapter_pin`: active x/z probe pair
  not `(0,0)`.
- `C3_persistence_n01_order_gap`: `D_z after R_x` and `R_x after D_z` active
  x/z probe signatures differ.

The 2Q packet keeps the same forms over the pinned first-qubit local adapter:

- C1: finite 2Q candidate with trace one and nonnegative spectrum under the
  family eigenvalue rule.
- C2: `(2*Tr((sigma_x tensor I)rho), 2*Tr((sigma_z tensor I)rho)) != (0,0)`.
- C3: first-qubit `D_z after R_x` and `R_x after D_z` active x/z signatures
  differ.

No new admissibility C4 is smuggled into active C. The only added named hook is
`C5_t1_positive_active_coordinate_pin`, and the packet marks it as downstream
`M(C,t)`, not part of C1-C3 survival.

Evidence paths:

- 1Q pins: `system_v6/sims/gcm_constraint_carve_v1/build_card.md`
- 2Q pins: `system_v6/sims/gcm_constraint_carve_2q_v0/build_card.md`
- executable predicates: `system_v6/sims/gcm_constraint_carve_2q_v0/gcm_constraint_carve_2q_v0_common.py`

## Terrain-Blind Validator Tooth

PASS.

The 2Q validator recomputes terrain-blindness from current source predicate
text and compares it to the emitted guard. I ran an in-memory source-only
injection by appending `terrain atlas label must pass before survival` to C2
without regenerating result JSONs. The recomputed guard went red:

```text
C2_probe_distinguishability_xz_local_adapter_pin: forbidden predicate token 'terrain'
C2_probe_distinguishability_xz_local_adapter_pin: forbidden predicate token 'atlas'
```

The clean guard stayed green and matched the emitted predicate-text hash.
The packet's own injected bad variant is also caught.

Evidence paths:

- `system_v6/sims/gcm_constraint_carve_2q_v0/validate_gcm_constraint_carve_2q_v0.py`
- `system_v6/sims/gcm_constraint_carve_2q_v0/gcm_constraint_carve_2q_v0_common.py`

## Counts And Controls

PASS.

Fresh source recomputation reproduced:

```text
candidate_count = 15783
density_subcarrier_count = 1167
survivor_count = 544
quotient_class_count = 8
survivor_family_counts = {product_grid: 528, purification_boundary: 16}
kill_counts_by_constraint =
  C1_finite_2q_density_carrier: 14616
  C2_probe_distinguishability_xz_local_adapter_pin: 215
  C3_persistence_n01_order_gap: 408
M(C,t) = 272 survivors / 4 quotient classes
```

Stratified sample check: 650 candidates were rechecked, including all 46 valid
entangled candidates and all 20 Bell-diagonal entangled C2 kills. Manual
predicate re-evaluation over C1-C3 had `manual_mismatch_count=0`.

Controls passed:

- empty-C: 15783 survivors, degenerate no-manifold control fires;
- over-constrained-C: 0 survivors;
- C1 erasure: 12016 survivors, bite true;
- C2 erasure: 680 survivors, bite true;
- C3 erasure: 952 survivors, bite true;
- probe scramble: quotient moves from 8 classes to 6 classes;
- source injection-red: caught;
- 1Q regression/hash lock: all expected 1Q hashes match.

Existence probes passed:

```text
stable = true
independent = true
chart_recoverable = true
negative_controlled = true
identity_leak_detected = true
identity_leak_excluded_best_accuracy = 0.965532535006
```

## Cross-Backend Checks

PASS.

I ran fresh no-write backend checks:

- JAX lane `build_result()` with `common.write_json` monkeypatched to no-op:
  `all_pass=true`, 544 survivors, 8 classes, 204 components, 16 entangled
  survivors, 16 embedded 1Q rows; NetworkX component match true; SymPy guard
  true.
- PyTorch lane `build_result()` with `common.write_json` monkeypatched to no-op:
  `all_pass=true`, 544 survivors, 8 classes, 204 components, 16 entangled
  survivors, 16 embedded 1Q rows; `torch.func` receipt has active probes/order
  gaps true, M(C,t) positive count 272; SymPy guard true.
- Julia lane via `julia -e 'include(...); ...'` without calling `main()`:
  15783 candidates, 1167 density rows, 544 survivors, 8 classes, 204
  components, 16 entangled survivors, 272 M(C,t) survivors, 16 embedded 1Q
  rows, and the same kill counts.

The checked-in envelope also reports all three engine lanes green and agreement
on survivor count, quotient class count, component count, entangled survivor
count, and embedded 1Q count.

## Entanglement Mechanism

PASS_WITH_CAVEAT.

The computed mechanism is clear:

- Bell-diagonal candidates have first marginal `I/2`, so their local first-qubit
  x/z probe signature is always `(0,0)`.
- C2 is exactly the nonzero local first-qubit x/z probe test.
- Therefore all 20 valid Bell-diagonal entangled candidates are killed by C2.
- Purification-boundary candidates are entangled when the pinned first marginal
  has radius strictly between 0 and 1; they survive only when that first
  marginal is already a 1Q survivor under C1-C3.

Fresh mechanism counts:

```text
valid_entangled_candidate_count = 46
bell_diagonal_valid_entangled_count = 20
bell_diagonal_entangled_killed_by = {C2_probe_distinguishability_xz_local_adapter_pin: 20}
bell_local_probe_signatures = {(0,0): 20}
purification_entangled_survivor_count = 16
purification_order_gap_counts = {1.0: 16}
purification survivor probe signatures =
  (-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)
  with 2 rows each
```

This is a real rung product, but it is not a monogamy result. Entanglement is a
post-carve boundary readout. The predicates only see density validity, local
first-qubit x/z distinguishability, and local order gap.

## Cross-Rung Rows

PASS.

Panel 11 required both directions because they answer different questions. Both
pass:

```text
product_control_embedding_count = 16
product_control_embedding_all_survive = true
partial_trace_A_image_count = 16
partial_trace_A_image_equals_1q_survivor_set = true
partial_trace_A_fiber_count_values = {34}
one_q_hashes_match_expected = true for common/result/envelope/freeze registry
```

Interpretation: every pinned 1Q survivor embeds into 2Q by product with the
pinned control qubit, and the entire 2Q survivor set projects by first marginal
to exactly the 1Q survivor set. Each 1Q survivor has a 34-row 2Q fiber: 33
product-grid rows plus 1 purification-boundary row.

## Monogamy-Type Row

FAIL_AS_CHECKED / OPEN_AS_QUESTION.

Panel 11 names monogamy-type constraints as a genuinely 2Q phenomenon to
expect. The 2Q packet does not contain `monogamy`, does not compute a monogamy
quantity, and does not explicitly mark the monogamy-type question open.

This does not kill the recomputed C1-C3 carve, but it does kill the builder's
`strict green` wording. The honest citation is:

`cross-rung product and partial-trace rows pass; local-marginal entanglement
boundary mechanism is computed; monogamy-type constraint evidence remains open.`

## Eight-Class Coincidence

STRUCTURAL, not coincidental.

The 2Q quotient is intentionally bucketed by the same first-qubit x/z probe
family as the 1Q carve. The partial-trace image equals the 1Q survivor set
exactly, and no Bell-diagonal entangled row survives to add a new zero-local
class. Therefore the class count is capped by the 1Q probe resolution.

Fresh class structure:

```text
one_q_class_count = 8
two_q_class_count = 8
two_q_probe_signatures =
  (-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)
two_q_member_counts = 68 in each class
two_q_entangled_member_counts = 2 in each class
```

This is not evidence that 1Q and 2Q have the same manifold. It says the pinned
2Q candidate family is a 34-row fiber over each pinned 1Q survivor under the
same first-marginal probe quotient.

## G.2a

PASS.

The build card declares G.2a from birth, the common packet and envelope carry
`no_builder_audit_verdict=true` and `no_builder_audit_verdict_envelope_gate=true`,
and the local boundary delegates to `scripts/builder_audit_boundary.py`. Pre-write
boundary checks returned no packet or envelope errors. Post-write no-write
validation also returned:

```text
validate_payload_no_write_errors = []
packet_boundary_errors = []
envelope_boundary_errors = []
builder_audit_boundary_ok = true
```

## Three Coordinates

PASS.

The packet answers the layer-stack supplement 1 coordinates:

```text
layer = layers 1-2: constraint set plus carved object M(C)+S/~_M
nesting = carve (order B), with 1Q -> 2Q product and partial-trace cross-rung row
qubit_depth = 2Q boundary rung
```

Seven audit questions are present in the result packet. The answer to surface
is deliberately narrow: finite 2Q Pauli-coordinate candidate surface,
product-grid + Bell-diagonal + purification-boundary; no CA/network runtime
surface claimed.

## Final Decision

Admitted at scratch ceiling:

- C1-C3 terrain-blind 2Q carve as a carrier-and-pins-relative boundary/control
  rung.
- Counts: 15783 / 1167 / 544 / 8.
- Split: 528 product survivors + 16 entangled purification-boundary survivors.
- Boundary mechanism: Bell-diagonal entangled rows killed by C2 because the
  first marginal is locally x/z indistinguishable; purification entangled rows
  survive only by inherited 1Q first-marginal admissibility.
- Cross-rung rows: product embedding 16/16 and exact partial-trace image
  equality.
- G.2a and repaired terrain-blind validator pattern.

Blocked or open:

- strict-green wording;
- monogamy-type constraint evidence;
- final manifold, terrain, axis, engine, bridge, physics, or formal admission
  claims;
- any use of the 8-class match as more than probe-resolution structure.

Block K:

- Gates cited: C1-C3 source instantiation; terrain-blind source recompute plus
  injection-red; full source count recompute; >=500 stratified predicate sample;
  JAX/PyTorch/Julia no-write backend recomputation; controls; cross-rung
  product and partial-trace rows; G.2a boundary helper; layer-stack supplement
  coordinates.
- Admission decisions: admitted only at `scratch_diagnostic` ceiling; strict
  green rejected; monogamy open.
- Narrative substitutions intercepted: "entanglement-dependent admissibility"
  is narrowed to local-first-marginal/probe-dependent boundary behavior; "8
  classes at both rungs" is structural probe-resolution/fiber evidence, not
  manifold identity.
- Worker claims verified: none accepted; sidecar subagents had not returned
  receipt evidence before this verdict.
- Worker claims not verified: all sidecar worker routes are unaccepted for this
  file.
- Status label changes to registry: none.
- Blocked actions: no git add/commit; no generated result rewrite; no validator
  main/pytest run because the live write boundary allowed only this audit file.

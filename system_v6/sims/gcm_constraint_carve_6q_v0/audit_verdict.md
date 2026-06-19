# Independent Audit Verdict - gcm_constraint_carve_6q_v0

audit_mode: read-only audit
auditor: independent Codex audit, not builder
freshness_tier: TIER-2 results-available, with source/result recomputation in this turn
write_scope: only this audit_verdict.md
git_scope: no git add, no commit

Bottom line: VERDICT = PASS_WITH_CAVEATS at the exact ceiling `scratch_diagnostic_state_artifacted_6q_count_fixture`.

The 6Q packet sustains a bounded, state-artifacted count fixture: 557 pinned candidates, 548 survivors, and 9 quotient classes. It supports the local C1/C2/C3 matrix rows, content-addressed stored 6Q density matrices, the 547/547 5Q-to-6Q product lifts plus Tr_F retraction, 31 named bipartitions with entropy/MI rows, narrowed CKW focus-qubit checks for stored pure survivor rows, controls, lineage checks, strict helper green, and consumed-not-rebuilt Cl(12) feedstock.

It does not support formal admission, THE manifold, canonical manifold, geometry, axis, bridge, physics, SLOCC, six-party entanglement classification, 6Q registry freeze, or reduced-cut-state artifact claims. The few risky labels such as `m_c_6q`, `M(C)@6Q`, `ghz6_w6_cluster_admissibility_matrix`, and `rank_K_13_admissible` are accepted only under the surrounding count-fixture fences, not as admission or geometry language.

## 1. Matrix Recompute

PASS.

I recomputed C1/C2/C3 from stored `rho_ABCDEF` for a 58-row stratified sample: GHZ6, W6, cluster_linear_6, all 9 killed rows, 25 early survivors, 25 evenly spaced survivors, and all anchor rows. Fresh booleans matched stored booleans exactly. `sample_errors=[]`.

Full-matrix disease absent at the checked levels:

- every row in the 557-row matrix has C1, C2, and C3;
- every row has `all_failed_constraints`;
- `first_failed_constraint_display_only` is consistent with `all_failed_constraints` across all 557 rows, and is display-only rather than the source of the verdict.

Named rows verified:

- GHZ6: C1 true, C2 false, C3 false.
- W6: C1 true, C2 true, C3 false.
- cluster_linear_6: C1 true, C2 false, C3 false.

Result counts verified from the artifact:

- candidate_count: 557.
- survivor_count: 548.
- quotient_class_count: 9.
- killed_count: 9.
- kill_counts_by_constraint: C1=1, C2=5, C3=7.

## 2. State Storage

PASS.

The main result file is a genuine large state artifact: `303318038` bytes. The packet stores:

- `states_by_content_id`: 557 entries.
- `candidate_state_index`: 557 entries.
- `survivor_states`: 548 entries.

I loaded five `rho_ABCDEF` matrices directly from the JSON: GHZ6, W6, cluster_linear_6, 5q_lift_0, and locally_rotated_generalized_GHZ6_anchor. Each loaded as a real 64x64 complex matrix with 64 JSON rows and 64 cells in row 0, not a truncated summary. Each content id recomputed from canonical rho JSON matched the stored id, and a one-cell mutation changed the content id.

Fresh matrix checks on those five rows:

- Hermiticity error: 0.0 for all five.
- Trace: 1.0 within rounding tolerance for all five.
- Minimum eigenvalue: nonnegative within numerical tolerance.
- State vectors are present where expected for the pure anchor rows.

Scale honesty passes. The ambient 6Q density-matrix carrier is large, but the packet does not silently enumerate the full density-matrix state space. Its candidate space is pinned to `547 5Q survivor product lifts plus 10 6Q boundary/feedstock/control anchors`, with an explicit note that no exhaustive C^64 state grid is run.

## 3. Monogamy And Cuts

PASS_WITH_CAVEAT.

The cut lattice is honest for this fixture:

- 31 bipartition names are present.
- Each of the 6 representative cut rows has all 31 cuts.
- Each representative cut entry carries `S_left`, `S_right`, `S_full`, and `mutual_I`.
- `per_cut_reduced_matrices_stored=false`.
- Caveat carried: per-cut reduced matrices are not stored for all 6Q candidates; only entropy/MI rows are emitted.

The 6-party monogamy wording is narrow enough:

- Generalization named: Osborne-Verstraete N-qubit CKW focus-qubit inequality.
- Computed from stored `rho_ABCDEF`: true.
- Pure survivor rows checked: 4.
- Focus qubits per checked row: 6.
- All focus inequalities satisfy CKW in the stored rows.
- `residual_6_tangle_claimed=false`.
- `higher_party_residual_allocation_claimed=false`.
- The result explicitly says six-party residual allocation and entanglement-class separation are not claimed.

The caveat is scope, not failure: this is a narrowed monogamy check, not a general six-party entanglement theorem.

## 4. Cross-Rung, Controls, Cl(12), G.2a

PASS_WITH_CAVEATS.

Cross-rung rows pass:

- 5Q product embedding input survivor count: 547.
- Lifted 6Q survivor count: 547.
- All 5Q survivors have one 6Q lift: true.
- `Tr_F` reproduces 5Q state count: 547.
- Max absolute delta for `Tr_F(rho_ABCDEF)` vs 5Q rho: 0.0.

Regressions and lineage:

- Direct 6Q regression rows cover 1Q, 2Q, 3Q, and 5Q.
- 5Q regression is 547 survivors / 9 classes.
- 3Q regression is 545 survivors / 9 classes.
- 1Q and 2Q object/hash checks are green.
- 4Q is not a direct 6Q regression row. It is inherited through the 5Q parent, which carries the 4Q 546/9 source. Do not cite this packet as an independent direct 4Q rerun.
- Coordinates are present: layers `1-2 (+17 tensor)`, operation `carve`, qubit_depth `6Q`.
- `gcm_lineage` carries 1Q/2Q/3Q IDs and hashes; 5Q is linked through consumed feedstock rather than folded into one direct 1Q-6Q lineage object.

Controls fire:

- empty-C control: 557 survivors.
- cliff-overconstrained control: 0 survivors.
- erasure-bite controls all bite: dropping C1 gives 549, dropping C2 gives 549, dropping C3 gives 551.
- probe-scramble moves quotient: 9 classes to 6 classes.
- terrain-blindness guard is clean.
- source recompute injection-red catches `terrain`, `atlas`, and `Se`.
- substrate lineage-free and stale-lineage negatives are red with error codes for 1Q, 2Q, 3Q, and 5Q.

Cl(12):

- `floor_rows_extended.consumed_not_rebuilt=true`.
- The packet consumes `geo_s1_scaling_stress_678q_exact_v0` and `stage_lifted_spinor_shell_n6_v0`.
- The Cl(12) row must be cited with the stored symplectic-rank certificate wording, not as a newly materialized exhaustive 4095-vertex clique search by this packet.

G.2a:

- Builder/audit boundary is wired from birth through `scripts/builder_audit_boundary.py`.
- `builder_gates.G_2a_idempotency_from_birth=true`.
- `boundary_helper_fully_used=true`.
- `no_builder_audit_verdict=true`.
- This file declares independent/read-only audit status in its header, so post-audit idempotency should remain valid.

## 5. Ban-List And Claim Ceiling

PASS_WITH_WORDING_CAVEAT.

The packet's operative claim ceiling is correct:

- `classification=scratch_diagnostic`.
- `promotion_allowed=false`.
- `formal_admission_allowed=false`.
- `claim_ceiling=scratch_diagnostic_state_artifacted_6q_count_fixture`.
- `not_THE_manifold=true`.
- blocked consumers include formal admission, canonical manifold, axis/bridge, physics, SLOCC/six-party classification, 6Q registry freeze, and reduced-cut-state artifact claims.

Ban-list scan result:

- No operative `geometry`, `geometric`, `smooth`, `stratified`, `canonical G2`, `real embedding`, `InducedGeometry`, or `g2-irreducible` claim was found in the checked claim-bearing summary surfaces.
- Hits for `admission`, `bridge`, `axis`, `physics`, and `SLOCC` occur in blocked-consumer or explicit non-claim wording.
- Wording-risk labels remain: `m_c_6q`, `M(C)@6Q`, `ghz6_w6_cluster_admissibility_matrix`, and `rank_K_13_admissible`. These are tolerated only because the surrounding fields fence them to count-fixture, local-matrix, or feedstock-certificate meaning.

Citation rule: cite this packet as `state-artifacted 6Q count fixture` or `scratch_diagnostic_state_artifacted_6q_count_fixture`; do not cite it as geometry, admission, manifold, SLOCC, axis, bridge, physics, registry freeze, or reduced-cut-state evidence.

## 6. Fresh Checks Run

Commands/checks run in this audit:

```bash
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba make helper-process-audit-strict
```

Result: `all_pass=true`, helper process count 0.

```bash
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_envelope_results.json
```

Result: `ok=true`.

```bash
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v6/sims/gcm_constraint_carve_6q_v0/gcm_constraint_carve_6q_v0_common.py
```

Result: `violation_total=0`.

```bash
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# in-memory structured checks against the existing result:
# - validate_payload(..., require_helper_preflight=True)
# - 58-row C1/C2/C3 recompute from stored rho_ABCDEF
# - 5 stored 64x64 rho matrices, hermiticity/trace/positivity/content-id mutation
# - cross-rung/cut/CKW/control summaries
PY
```

Results: `validate_payload_in_memory_ok=true`, `sample_errors=[]`, all five content ids mutation-sensitive.

Not run live:

- `validate_gcm_constraint_carve_6q_v0.py`, because it writes `results/gcm_constraint_carve_6q_v0_validator_results.json` and this audit was authorized to write only `audit_verdict.md`.
- Full packet rebuild/lane reruns, because the user requested a read-only audit except this verdict file.

Existing result surfaces read:

- `system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_results.json`
- `system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_envelope_results.json`
- `system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_validator_results.json`
- `system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_jax_results.json`
- `system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_pytorch_results.json`
- `system_v6/sims/gcm_constraint_carve_6q_v0/results/gcm_constraint_carve_6q_v0_julia_results.json`

## 7. Block K

Gates cited: standards codex G.2a; 3Q-v0 first-failed failure lesson; 4Q/5Q state-artifacted count-fixture pattern; tribunal ban list; hardened helper; strict three-engine envelope; sim contract lint; in-memory packet validator; terrain-blind injection-red control.

Admission decisions: state-artifacted 6Q count fixture admitted only at scratch_diagnostic count-fixture ceiling; formal admission blocked; geometry/manifold/axis/bridge/physics/SLOCC/reduced-cut-state consumers blocked.

Narrative substitutions intercepted: count fixture is not geometry; `M(C)@6Q` wording is not manifold admission; Cl(12) feedstock consumption is not a rebuild; 4Q regression is inherited via 5Q, not directly rerun here.

Worker claims verified: two read-only Codex explorer sidecars checked cross-rung/control/lineage and monogamy/cut/ban-list surfaces; controller independently verified decisive rows with structured parsing and recomputation.

Worker claims not verified: no external Claude/Gemini child receipts were used or counted; no full Wizard v4.2 matrix was claimed.

Status label changes to registry: none.

Blocked actions: no git add/commit; no validator/rebuild commands that would write result files; no promotion beyond `scratch_diagnostic_state_artifacted_6q_count_fixture`.

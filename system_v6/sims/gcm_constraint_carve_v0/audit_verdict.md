# Independent Audit Verdict: gcm_constraint_carve_v0

Bottom line: FAIL for the claimed FULL first computed `M(C)` frontier packet. The arithmetic carve is real and reproducible, but the packet does not pass the lethal source/constraint-honesty teeth: the carve is not terrain-blind, C2/C4 citations do not fully say what the executable predicates do, and the "independent" existence probe is only constraint-erasure bite, not the standards-codex no-identity-leak test.

Accepted residue: a useful `scratch_diagnostic` arithmetic carve under the builder's pinned carrier and predicates. It may be cited only as "125 finite grid candidates -> 8 survivors -> 4 probe classes under this packet's C, with controls firing under those predicates." It must not be cited as `THE manifold`, an admitted first `M(C)`, terrain-atlas evidence, axis/engine/physics evidence, or a fully source-honest constraint carve.

Audit mode: read-only audit, independent auditor verdict. Freshness tier: `TIER-2 results-available` under `system_v6/receipts/audit_standards_codex_v1.md:120-126`; no prior audit verdict existed, but source and result artifacts were read. Allowed write scope for this audit: this file only. No `git add`, commit, push, or live result JSON rewrite was performed.

## Verdict Table

| Tooth | Verdict | Reason |
|---|---:|---|
| Constraint honesty | FAIL | C1 and C3 are adequately executable/source-supported; C2 is executable and biting but the cited architecture line supports the general quotient contract, not the exact x/z probe and zero-active-class predicate; C4 is executable and biting but its exact `not (x != 0 and z != 0)` residency predicate is terrain-framed and not directly justified by the cited lines. |
| Terrain-blindness / fitting risk | FAIL | The carve path contains terrain/atlas/macro terms inside the common carve source, including C4, `residency_signature`, `terrain_question`, and validator/test locks. A terrain row can be reported honestly as partial, but it cannot be sold as read off a terrain-blind carve. |
| Recomputed carve | PASS | Independent no-write recomputation reproduced 125 candidates, 33 density-grid candidates, 8 survivors, and kill ledger C1=92, C2=5, C3=12, C4=8. |
| Quotient and components | PASS | Recomputed `S/~_M` gives 4 classes with components `[Q0,Q3]`, `[Q1]`, `[Q2]`. |
| Existence probes | FAIL | Stability, chart recovery, and negative controls are computed. Independence is not computed per no-identity-leak doctrine; required `identity_leak_detected`, `identity_leak_excluded_best_accuracy`, and `identity_leak_exclusion_rule` fields are absent. |
| Terrain row | FAIL as evidence, PASS as caveated wording | The packet says `partial_macro_match_not_full_atlas` and denies full atlas admission, but the macro split is entangled with the C4 terrain/residency predicate. |
| Controls | PASS under chosen predicates | Empty-C, overconstrained-C, per-constraint erasure, and probe scramble all fire. |
| `M(C,t)` hook | PASS as recomputed scratch hook | The C->C' update recomputes to 4 survivors and 2 classes; source is tracked at `dd9ec4999`. |
| Scale honesty / G.2a | PASS | The packet stays `scratch_diagnostic`, `carrier-and-pins-relative`, `not THE manifold`, and the builder did not create this audit verdict. |
| Git/process admissibility | FAIL for committed-packet claims | The whole target subtree was untracked during audit: `git status --short -- system_v6/sims/gcm_constraint_carve_v0` returned `?? system_v6/sims/gcm_constraint_carve_v0/`. Binding commits 393c5147a and 75a8d0627 bind doctrine/route, not this packet's tracked source. |

## Evidence

### Constraint Source Honesty

The executable constraints are in `system_v6/sims/gcm_constraint_carve_v0/gcm_constraint_carve_v0_common.py:251-294`.

- `C1_finite_density_carrier`: PASS with caveat. Code uses the 5-point grid and Bloch-ball radius cut at `gcm_constraint_carve_v0_common.py:192-210` and dispatches at `277-278`. The cited sources support finitude and the finite `M(C)` construction contract: `system_v6/foundations/root_axioms_v0_1_DRAFT.md:53-65` and `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:23-38`. The exact 5-point carrier remains a local carrier choice, not owner-source-derived by those lines.

- `C2_probe_distinguishability_xz`: FAIL for line-honest citation. Code pins `PROBE_FAMILY = ("sigma_x", "sigma_z")` at `gcm_constraint_carve_v0_common.py:35`, maps x/z at `213-219`, and rejects the zero active-probe class at `279-280`. `root_axioms_v0_1_DRAFT.md:45-51` supports probe-relative quotient and noncommutation generally. `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md:82-88` is a build-order/blocked-claims region, not a source for the exact x/z probe pin or the zero-active-class predicate.

- `C3_persistence_n01_order_gap`: PASS. Code compares `D_z after R_x` with `R_x after D_z` probe signatures at `gcm_constraint_carve_v0_common.py:222-232` and dispatches at `281-282`. The cited root/source math supports noncommuting order pressure: `root_axioms_v0_1_DRAFT.md:49-53` and `system_v6/foundations/working_math_scaffold_20260609.md:105-107`.

- `C4_G7_operator_residency_pin`: FAIL for the FULL claim, INCONCLUSIVE as a bounded scaffold pin. Code labels terrain-style residency at `gcm_constraint_carve_v0_common.py:235-248` and rejects simultaneous nonzero x and z at `283-284`. `audit_standards_codex_v1.md:43-59` supports predeclared finite pinning; `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md:75-87` and `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/qit-axes-terrain-operator-fold-2026-06-09.md:253-324` support terrain-family distinctions and count discipline. They do not literally justify `x != 0 and z != 0` as the source-derived illegality predicate. This is exactly the fitting-prone adapter row.

### Terrain-Blindness

The prompt's lethal check says the carve must not know about terrains. This packet does know about them inside the carve path:

- terrain source locks: `gcm_constraint_carve_v0_common.py:56-57`;
- terrain-related tool intent: `gcm_constraint_carve_v0_common.py:103`;
- terrain/residency labels before the terrain answer: `gcm_constraint_carve_v0_common.py:235-248`;
- C4 source/test terrain wording: `gcm_constraint_carve_v0_common.py:268-270`;
- terrain answer construction: `gcm_constraint_carve_v0_common.py:526-539`;
- validator locks the terrain answer: `validate_gcm_constraint_carve_v0.py:77`;
- pytest locks the terrain answer: `tests/test_gcm_constraint_carve_v0.py:67`.

This does not prove bad faith or fake arithmetic. It does kill the stronger claim that the terrain macro split was read from a terrain-blind `M(C)`. The terrain row should be treated as a scaffold-aligned readout under a terrain-aware C4 pin, not as discovered terrain structure.

### Recomputed Arithmetic

No live result files were rewritten. The normal packet runners write result JSONs (`gcm_constraint_carve_v0_common.py:736-739`, `gcm_constraint_carve_v0_jax.py:144`, `gcm_constraint_carve_v0_pytorch.py:122`, `gcm_constraint_carve_v0_julia.jl:211-214`, `validate_gcm_constraint_carve_v0.py:134-143`), so the audit used no-write in-memory probes and `/tmp` scratch for Julia.

Fresh commands:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# independent grid/probe recomputation in the shell, no repo writes
...
PY
```

Observed output:

```text
candidate_count=125
density_count=33
survivor_count=8
survivor_candidate_ids=[32,42,56,58,66,68,82,92]
kill_counts={C1_finite_density_carrier:92,C2_probe_distinguishability_xz:5,C3_persistence_n01_order_gap:12,C4_G7_operator_residency_pin:8}
quotient_class_count=4
classes=Q0:[32,42], Q1:[56,66], Q2:[58,68], Q3:[82,92]
quotient_components=[[Q0,Q3],[Q1],[Q2]]
empty_C=125
overconstrained=0
erasures all bite
mct_survivor_count=4
mct_candidate_ids=[58,68,82,92]
```

No-write imports with result paths patched to `/tmp` reproduced:

```text
common all_pass=true; survivor_count=8; quotient_components=[[Q0,Q3],[Q1],[Q2]]
jax all_pass=true; survivor_count=8; quotient_class_count=4; component_count=3; wrote /tmp/gcm_constraint_carve_v0_jax_results_audit.json
pytorch all_pass=true; survivor_count=8; quotient_class_count=4; wrote /tmp/gcm_constraint_carve_v0_pytorch_results_audit.json
```

Julia was run from a `/tmp` scratch copy, not the live repo path:

```text
all_pass=true
candidate_count=125
density_count=33
survivor_count=8
quotient_class_count=4
component_count=3
```

The in-memory packet validator call also returned `ok=true`, `error_count=0` without rewriting `gcm_constraint_carve_v0_validator_results.json`.

### Quotient And Controls

The quotient implementation groups survivors by probe signature at `gcm_constraint_carve_v0_common.py:335-352`. The graph and component implementation is at `396-464`. The result artifact records the expected classes and components in `system_v6/sims/gcm_constraint_carve_v0/results/gcm_constraint_carve_v0_results.json`:

- quotient classes and member ids: result `quotient`;
- quotient components `[Q0,Q3]`, `[Q1]`, `[Q2]`: result `adjacency_connectivity.quotient_components`;
- controls: result `controls`;
- persisted validator result: `results/gcm_constraint_carve_v0_validator_results.json` has `ok: true`, `errors: []`.

The controls do real work under the chosen predicates:

- empty C: 125 survivors;
- overconstrained C: 0 survivors;
- C1 erasure: survivor count 32, delta 24;
- C2 erasure: survivor count 12, delta 4;
- C3 erasure: survivor count 16, delta 8;
- C4 erasure: survivor count 16, delta 8;
- probe scramble moves the quotient from 4 signatures to 6 signatures.

These controls prove the predicates are load-bearing. They do not prove the predicates are source-honest or terrain-blind.

### Existence Probes

`gcm_constraint_carve_v0_common.py:542-573` computes:

- `stable`: from the class-stability certificate;
- `independent`: `all(row["bite"] for row in erasures)`;
- `chart_recoverable`: region recovered from probe signature;
- `negative_controlled`: empty-C, overconstrained-C, and probe-scramble checks.

The stable/chart/negative rows are acceptable as packet-local checks. The independence row fails the doctrine requested in the prompt. `system_v6/receipts/audit_standards_codex_v1.md:63-85` defines no-identity-leak, and `audit_standards_codex_v1.md:228-236` requires the identity-leak fields in future packets. The target result has none:

```text
identity_leak_detected: absent
identity_leak_excluded_best_accuracy: absent
identity_leak_exclusion_rule: absent
```

Therefore the builder claim "ALL FOUR existence probes true" is rejected as worded. The honest statement is: three packet-local probes pass, and the packet-local erasure-bite independence check passes, but the standards-codex independence probe was not run.

### Terrain Row

The language is honest but the evidence is not terrain-blind.

Passes:

- source/result answer is `partial_macro_match_not_full_atlas`;
- result sets `terrain_atlas_not_claimed: true`;
- result says the object has 4 quotient classes and does not realize the full 4-family/8-realization terrain atlas;
- no full atlas, axis, engine, or physics claim is admitted.

Fails:

- the same file that computes survival also computes terrain-style residency signatures;
- C4 kills candidates by a terrain/residency predicate before the terrain row is read;
- the terrain row is locked by validator/test expectations rather than held as a post-carve exploratory readout.

Citation rule: do not cite this as "the carved M(C) discovered dissipative vs circulation terrain regions." At most cite: "under a terrain-aware C4 residency pin, the surviving quotient separates two macro labels while explicitly failing full atlas realization."

### `M(C,t)` Hook

`gcm_constraint_carve_v0_common.py:508-523` recomputes `C -> C_prime = C plus C5_t1_orientation_pin` and rebuilds the quotient. The cited source `system_v6/foundations/two_engine_readout_automaton_20260609.md:21-25` is tracked at commit `dd9ec4999` and supports a constrained fibered transition/readout object, not a free relabel. The recomputed hook returns:

```text
survivor_count=4
quotient_class_count=2
survivor_candidate_ids=[58,68,82,92]
```

Ceiling: scratch hook only. It is not dynamic manifold admission.

### Scale, Boundary, And Git Truth

Scale honesty passes. The packet repeatedly states:

- `classification = scratch_diagnostic`;
- `promotion_allowed = false`;
- `formal_admission_allowed = false`;
- claim ceiling `first_computed_carve_candidate_only_carrier_and_pins_relative`;
- `not THE manifold`;
- disallowed claims include terrain atlas, axis, engine, physics, and canonical-by-process claims.

G.2a boundary passes. Before this audit, `audit_verdict.md` did not exist. The builder boundary helper allows a later independent audit verdict only if the header declares independent/fresh/read-only audit status: `scripts/builder_audit_boundary.py:21-38`. This file does so in its header.

Git truth blocks stronger process claims. The target directory was untracked during audit:

```text
?? system_v6/sims/gcm_constraint_carve_v0/
```

The binding commits:

- `393c5147a`: GCM re-anchor and the tooth "where is the constraint set and what did it carve?";
- `75a8d0627`: owner stop order, manifold first, carve lane continuing.

Those commits bind the audit standard and route. They do not make this untracked packet a committed canonical artifact.

## Claim Ceiling

Accepted status label: `exists` plus local `passes no-write recomputation` for arithmetic. Public repo truth must not exceed `exists` until the packet itself is tracked and the appropriate runner/validator commands can be rerun under an allowed write plan.

Allowed citation:

```text
gcm_constraint_carve_v0 is an untracked scratch_diagnostic packet whose arithmetic recomputes, under its chosen C, to 8 survivors and 4 probe classes, with controls firing and a 4-survivor/2-class C->C' hook.
```

Forbidden citation:

```text
the first computed M(C) is admitted;
all four existence probes pass under doctrine;
the terrain macro split was read off a terrain-blind constraint carve;
the packet proves the terrain atlas, axes, engine, physics, or THE manifold;
the result is canonical by process.
```

Next admissible repair:

1. Split C4 out of the admissibility carve or rewrite it as a terrain-blind, source-pinned constraint with a literal cited predicate.
2. Add a real no-identity-leak independence probe and required `identity_leak_*` fields.
3. Repair C2 citation so the exact x/z probe and zero-active-class exclusion are sourced or explicitly demoted as a local adapter pin.
4. Keep terrain readout as a downstream post-carve analysis that cannot affect survival.
5. Track the packet, then rerun normal live validators under an explicit write plan.


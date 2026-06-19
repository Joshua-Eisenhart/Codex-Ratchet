# Fresh Audit: ring_checkerboard_support_graph_probe

Audit date: 2026-06-10

VERDICT: GENUINE-WITH-CAVEATS.

This packet is not decorative under the mine receipt kill conditions. The support graph, coloring, partition, phi0 field, orientation table, ladder rows, controls, presentation row-location receipts, and SMT flip all trace to emitted source/result tables. The strongest caveats are: z3/cvc5 bind a computed same-parity edge count rather than each edge/color variable directly; JAX and PyTorch share a pure-Python scalar construction path for the core vertex formulas; and the presentation disagreement controls are schematic/hardcoded even though the row-location receipts themselves are real.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as Axis-0 closure, manifold admission, canonical ring-checkerboard support, settled Xi, physics/cosmology/consciousness/world-engine proof, or a collapse of the live readings preserved in the pre-AI provenance page.

## Evidence Boundary

Sources/results read:

- `system_v6/receipts/ring_checkerboard_support_mine_20260610.md`
- `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md`
- `system_v6/sims/ring_checkerboard_support_graph_probe/build_card.md`
- `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_jax.py`
- `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_pytorch.py`
- `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_julia.jl`
- `system_v6/sims/ring_checkerboard_support_graph_probe/ring_checkerboard_support_graph_probe_envelope.py`
- `system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_jax_results.json`
- `system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_julia_results.json`
- `system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_pytorch_results.json`
- `system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_envelope_results.json`

Fresh checks run:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_envelope_results.json`
- Inline read-only recomputation from the emitted JAX result table for one orientation edge, one phi0 formula value, one directed phi0 gradient, parity rate from all emitted edges, and z3/cvc5 SMT flip.

Validator result:

```text
{"ok": true, "result_json": "system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_envelope_results.json"}
```

## Hand Recomputation

For edge `e0000`, emitted source/destination are `r00:s01 -> r00:s00`.

Source rule:

```python
key_a = (va["orientation_score"], va["phi0"], va["density_phase"])
key_b = (vb["orientation_score"], vb["phi0"], vb["density_phase"])
if key_a <= key_b:
    src, dst = a, b
else:
    src, dst = b, a
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:229-245`.

Recomputed values:

```json
{
  "edge_id": "e0000",
  "src": "r00:s01",
  "dst": "r00:s00",
  "recalc_src_key": [0.523168285992, 0.818645304115, 0.171010071663],
  "emitted_src_key": [0.523168285992, 0.818645304115, 0.171010071663],
  "recalc_dst_key": [0.602813748065, 0.823050008323, 0.0],
  "emitted_dst_key": [0.602813748065, 0.823050008323, 0.0],
  "src_key_le_dst_key": true,
  "recalc_gradient": 0.004404704208,
  "emitted_gradient": 0.004404704208,
  "recalc_src_phi0_from_formula": 0.818645304115,
  "emitted_src_phi0": 0.818645304115
}
```

Parity rate recomputed from all emitted edges:

```json
{
  "parity_same_from_edges": 0,
  "parity_diff_from_edges": 120,
  "parity_transition_rate_from_edges": 1.0
}
```

SMT flip rerun:

```json
{
  "z3_original": "unsat",
  "z3_flipped_same_1": "sat",
  "cvc5_original": "unsat",
  "cvc5_flipped_same_1": "sat"
}
```

## K1 Orientation Rule

Decision: PASSES. The per-edge orientation is computed from order-sensitive quantities, not label order. The orientation key is `(orientation_score, phi0, density_phase)`, and `orientation_score` includes `order_gap`, `density_phase`, `density_real`, and `b0_eta`.

Quoted source:

```python
order_gap = fro_norm2(sub2(terrain_py(dephase_z_py(rho), theta), dephase_z_py(terrain_py(rho, theta))))
offdiag = rho[0][1]
b0_eta = math.cos(2.0 * eta)
density_phase = offdiag.imag
density_real = offdiag.real
phi0 = math.tanh(b0_eta + 0.37 * order_gap + 0.19 * density_phase + 0.07 * density_real)
orientation_score = order_gap + 0.113 * density_phase + 0.041 * density_real + 0.017 * b0_eta
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:188-199`.

The mean orientation score delta `0.119427896323` traces to edge-level `orientation_score_delta` and is summarized from those deltas:

```python
score_delta = dv["orientation_score"] - sv["orientation_score"]
...
"orientation_score_delta": r12(score_delta)
...
score_deltas = jnp.asarray([edge["orientation_score_delta"] for edge in edges], dtype=jnp.float64)
...
"mean_orientation_score_delta": r12(cfloat(jnp.mean(score_deltas)))
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:244-258`, `ring_checkerboard_support_graph_probe_jax.py:286-298`.

## K2 phi0 Definition

Decision: PASSES WITH CAVEAT. `phi0` is not a vertex-label-only transform. It uses `b0_eta`, a noncommuting `order_gap`, and density off-diagonal phase/real terms. The caveat is that this is still a pinned bounded scalar candidate, not Axis-0 closure.

Quoted source:

```python
phi0 = math.tanh(b0_eta + 0.37 * order_gap + 0.19 * density_phase + 0.07 * density_real)
```

Cite: `ring_checkerboard_support_graph_probe_jax.py:198`.

Variance `0.293978847053` traces to computed `phi0` values:

```python
phi_values = jnp.asarray([v["phi0"] for v in vertices], dtype=jnp.float64)
phi_var = cfloat(jnp.var(phi_values))
...
"phi0_variance": r12(phi_var)
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:284-297`.

The live kill check compares against a label-only baseline and does not fire:

```python
label_only_values = [r12(math.tanh((vertex["ring"] + 1) / (PRIMARY_N + 1))) for vertex in primary["vertices"]]
label_only_matches = all(abs(a - b) <= 1.0e-6 for a, b in zip(phi_values, label_only_values))
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:554-563`.

## K3 Controls / H4 Pattern

Decision: PASSES FOR GRAPH READOUTS, WITH PRESENTATION-CONTROL CAVEAT.

The graph controls are not the R3 `x-x` pattern. Shuffled adjacency rebuilds a graph and compares readouts; reversed orientation flips gradients; erased coloring and erased nesting gate on original row availability and remove the corresponding rows.

Quoted source:

```python
shuffled = build_graph(PRIMARY_N, shuffled_pairs(PRIMARY_N, primary["summary"]["edge_count"]))
...
"shuffled_adjacency": {
    "fired": abs(shuffled_summary["mean_abs_gradient"] - original["mean_abs_gradient"]) > TOL
    or shuffled_summary["parity_transition_counts"] != original["parity_transition_counts"],
...
"erased_coloring": {
    "fired": original["parity_transition_counts"]["different"] > 0,
    "parity_rows_available_after_erasure": False,
...
"erased_nesting": {
    "fired": original["cross_partition_edge_count"] > 0,
    "partition_rows_available_after_erasure": False,
...
"reversed_orientation": {
    "fired": all(abs(a + b) <= TOL for a, b in zip(original_gradients, reversed_gradients)),
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:492-531`.

Observed control movement:

```json
{
  "shuffled_adjacency": {
    "original_mean_abs_gradient": 0.131316967405,
    "shuffled_mean_abs_gradient": 0.608904558612,
    "original_parity_transition_counts": {"different": 120, "same": 0},
    "shuffled_parity_transition_counts": {"different": 71, "same": 49}
  },
  "reversed_orientation": {
    "original_mean_signed_gradient": 0.069967258783,
    "reversed_mean_signed_gradient": -0.069967258783
  }
}
```

Caveat: `label_shuffle` is intentionally a no-structural-change control and is set as such. Presentation `disagreement_controls` are schematic/hardcoded `fired: true`; they are not used as evidence for graph readout sensitivity.

## K4 Ladder

Decision: PASSES. The ladder changes normalized readouts, not only row count.

Ladder excerpts:

```text
n=2:  mean_abs_gradient=0.293940353264, cross_partition_rate=0.333333333333, phi0_variance=0.194402095374, mean_orientation_score_delta=0.005666666667
n=8:  mean_abs_gradient=0.131316967405, cross_partition_rate=0.066666666667, phi0_variance=0.293978847053, mean_orientation_score_delta=0.119427896323
n=64: mean_abs_gradient=0.017936646386, cross_partition_rate=0.007874015748, phi0_variance=0.319163189797, mean_orientation_score_delta=0.021789303609
```

The kill-condition code checks normalized keys directly:

```python
normalized_keys = ["mean_abs_gradient", "cross_partition_rate", "phi0_variance", "mean_orientation_score_delta"]
changed = {
    key: len({row["summary"][key] for row in ladder_rows}) > 1
    for key in normalized_keys
}
...
"ring_step_ladder_only_changes_row_counts": not any(changed.values())
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:549-564`.

## K5 Presentation Receipts

Decision: PASSES FOR ROW-LOCATION RECEIPTS. Each of the three presentation keys carries per-row `support_id`, `row_index`, `row_location`, and coordinates. The n=8 result has 64 receipts for each presentation.

Quoted source:

```python
row_receipts["flat"].append(
    {
        "support_id": vertex["vertex_id"],
        "row_index": row_index,
        "row_location": f"flat.row={ring}.col={step}",
...
row_receipts["spherical-shell"].append(
...
        "row_location": f"spherical-shell.shell={ring}.phase_step={step}",
...
row_receipts["nested-ring"].append(
...
        "row_location": f"nested-ring.parent_ring={ring}.attached_step={step}",
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:438-469`.

Receipt counts:

```json
{
  "flat": 64,
  "spherical-shell": 64,
  "nested-ring": 64
}
```

## K6 SMT / H5 Pattern

Decision: PASSES WITH CAVEAT. The z3/cvc5 checks are real and flipable, but they bind a computed summary count derived from the emitted edge/color table rather than a quantified per-edge adjacency/color relation.

Quoted source:

```python
parity_same = sum(1 for edge in edges if edge["src_kappa"] == edge["dst_kappa"])
...
"parity_transition_counts": {"same": parity_same, "different": edge_count - parity_same}
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:282-291`.

SMT source:

```python
solver.add(same_parity_edges == int(edge_summary["parity_transition_counts"]["same"]))
solver.add(edge_count == int(edge_summary["edge_count"]))
solver.add(edge_count > 0)
solver.add(same_parity_edges > 0)
```

Cites: z3 `ring_checkerboard_support_graph_probe_jax.py:368-391`; cvc5 `ring_checkerboard_support_graph_probe_jax.py:404-435`.

Rerun flip:

```text
same=0, edge_count=120 -> z3 unsat, cvc5 unsat
same=1, edge_count=121 -> z3 sat, cvc5 sat
```

So this is not a summary boolean echo. It is a table-derived count proof with a SAT control, but weaker than a per-edge SMT encoding.

## K7 Shared Graph Object / H1 Pattern

Decision: PASSES. The primary graph is built once and then shared by the graph readouts, controls, presentations, kill conditions, and proofs. This is not the R3 disjoint-fixture pattern.

Quoted source:

```python
primary = build_graph(PRIMARY_N)
ladder_rows = ladder_sweep()
presentations = presentation_receipts(primary)
control_rows = controls(primary)
same_parity_control = build_graph(PRIMARY_N, same_parity_control_pairs(primary))
z3_proof = z3_coloring_proof(primary, same_parity_control)
cvc5_proof = cvc5_coloring_proof(primary, same_parity_control)
kill_rows = kill_conditions(primary, control_rows, ladder_rows, presentations)
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:615-623`.

The summary itself is computed from the same vertex and edge arrays:

```python
gradients = jnp.asarray([edge["directed_gradient_phi0"] for edge in edges], dtype=jnp.float64)
parity_same = sum(1 for edge in edges if edge["src_kappa"] == edge["dst_kappa"])
cross_partition = sum(1 for edge in edges if edge["src_partition"] != edge["dst_partition"])
phi_values = jnp.asarray([v["phi0"] for v in vertices], dtype=jnp.float64)
```

Cites: `ring_checkerboard_support_graph_probe_jax.py:277-298`.

## K8 Cross-Engine Divergence

Decision: NOT RESULT-ECHO, BUT EXACT ZERO IS A SHARED-PIN/ROUNDING RESULT.

The envelope records distinct source paths and `reads_peer_result=false` per leg:

```python
"source_path": payload["source_path"],
"source_sha256": payload["source_sha256"],
...
"reads_peer_result": payload["reads_peer_result"],
```

Cites: `ring_checkerboard_support_graph_probe_envelope.py:62-80`.

Envelope source does read leg result JSONs, but only in the controller comparison:

```python
legs = {engine: load_leg(engine) for engine in ("julia", "jax", "pytorch")}
```

Cite: `ring_checkerboard_support_graph_probe_envelope.py:110-111`.

The leg files do not read each other's result JSONs on their claim path. A grep found result writes and envelope reads, but no leg-side peer-result load. The result flags are:

```json
{
  "jax": {"reads_peer_result": false},
  "julia": {"reads_peer_result": false},
  "pytorch": {"reads_peer_result": false}
}
```

The zero divergence is exact after the common PIN and 12-digit rounding:

```json
{
  "mean_abs_gradient": {"jax": 0.131316967405, "julia": 0.131316967405, "pytorch": 0.131316967405},
  "phi0_variance": {"jax": 0.293978847053, "julia": 0.293978847053, "pytorch": 0.293978847053},
  "mean_orientation_score_delta": {"jax": 0.119427896323, "julia": 0.119427896323, "pytorch": 0.119427896323},
  "max_divergence": 0.0
}
```

Caveat: JAX and PyTorch use shared pure-Python scalar construction helpers for the core vertex formulas before engine-specific summaries/proofs. Julia mirrors the same formulas independently. This is enough to reject result-echo, but not enough to treat exact float equality as strong independent numerical corroboration.

## K9 Fences

Decision: PASSES. The must-not-claim list is exact and the envelope enforces it across legs.

Envelope fence:

```python
MUST_NOT_CLAIM_FENCES = [
    "Axis-0 closure",
    "manifold admission",
    "canonical ring-checkerboard support",
    "settled Xi",
    "physics/cosmology/consciousness/world-engine",
    "collapse of the live readings preserved in the pre-AI provenance page",
]
```

Cites: `ring_checkerboard_support_graph_probe_envelope.py:43-50`, `ring_checkerboard_support_graph_probe_envelope.py:116-123`, `ring_checkerboard_support_graph_probe_envelope.py:190-205`.

Result fence values:

```text
Axis-0 closure
manifold admission
canonical ring-checkerboard support
settled Xi
physics/cosmology/consciousness/world-engine
collapse of the live readings preserved in the pre-AI provenance page
```

## Named Gaps

1. SMT is count-bound, not per-edge-bound. The solvers receive `same_parity_edges` and `edge_count` computed from the table. This is materially better than a pass boolean and the flip works, but a hardened version should bind each edge endpoint's emitted kappa directly.
2. JAX/PyTorch independence is limited. The core support construction uses mirrored pure-Python scalar helper code in both Python legs; engine-specific packages are more load-bearing in summaries/proofs than in the core finite-object semantics.
3. Presentation disagreement controls are schematic. Row-location receipts are real and complete, but `disagreement_controls` are hardcoded as fired rather than recomputing a mutated presentation comparison.
4. `phi0` is a bounded candidate scalar. It passes the mine's nondegeneracy and label-only kill tests, but it remains candidate support-graph evidence, not Axis-0 closure.

## Final Verdict

VERDICT: GENUINE-WITH-CAVEATS.

Accepted claim: executable three-engine scratch diagnostic for the declared finite ring/checkerboard support graph at n=8, with computed ladder rows over n in `{2,4,8,16,32,64}`, table-derived coloring/partition/gradient/readout controls, row-location presentation receipts, and flipable z3/cvc5 coloring pressure.

Rejected upgrades: no Axis-0 closure; no manifold admission; no canonical support; no settled Xi; no physics/cosmology/consciousness/world-engine claim; no collapse of the two live readings.

## Post-Hardening Re-Audit Addendum

Audit date: 2026-06-10

Scope: focused re-audit of the four named-gap closures above after hardening. Original audit text is retained as historical context; this addendum records the current state after direct source reads and fresh reruns.

### Gap 1: per-edge SMT

Decision: CLOSED.

The active z3 and cvc5 encodings now bind each emitted edge endpoint kappa directly and assert existence of a monochromatic edge. In JAX, each edge creates `src_kappa` and `dst_kappa` variables, constrains them to `edge["src_kappa"]` and `edge["dst_kappa"]`, and adds `src_kappa == dst_kappa` to the disjunction; the result records `per_edge_endpoint_kappa_bound`, `per_edge_constraints_bound`, endpoint bindings, sample edge bindings, and the retained prior count-bound proof. Cites: `ring_checkerboard_support_graph_probe_jax.py:395-435`, `ring_checkerboard_support_graph_probe_jax.py:481-526`.

PyTorch mirrors the per-edge z3/cvc5 structure and retains the old count-bound proof under the honest `retained_prior_count_bound_proof` name. Cites: `ring_checkerboard_support_graph_probe_pytorch.py:353-393`, `ring_checkerboard_support_graph_probe_pytorch.py:433-472`.

Julia's Z3.jl leg also binds per-edge endpoint kappa variables and retains the count-bound proof. Cites: `ring_checkerboard_support_graph_probe_julia.jl:289-333`.

Fresh SMT rerun from the JAX source path:

```json
{
  "z3_original": "unsat",
  "z3_scrambled": "sat",
  "cvc5_original": "unsat",
  "cvc5_scrambled": "sat",
  "per_edge_constraints_bound": 120,
  "endpoint_bindings_bound": 240,
  "retained_prior_count_bound_verdict": "unsat",
  "retained_prior_count_bound_control": "sat"
}
```

### Gap 2: core_semantics_path and engine_native_roles

Decision: CLOSED WITH HONEST CAVEAT.

The fields are present on all three legs through the envelope record. Cites: `ring_checkerboard_support_graph_probe_envelope.py:62-80`, `ring_checkerboard_support_graph_probe_envelope.py:132-138`.

The labels match the sources: JAX declares `core_semantics_path="mirrored_pure_python_helpers"` and roles for x64 lane discipline, JAX reductions over emitted tables, and z3/cvc5 per-edge kappa pressure. Cite: `ring_checkerboard_support_graph_probe_jax.py:805-824`.

PyTorch declares `core_semantics_path="mirrored_pure_python_helpers"` and roles for torch tensor reductions, torch_geometric out-degree, and z3/cvc5 per-edge kappa pressure. Cite: `ring_checkerboard_support_graph_probe_pytorch.py:644-663`.

Julia declares `core_semantics_path="julia_independent_formula_implementation"` and roles for canon finite graph construction, Graphs.jl out-degree, Z3.jl per-edge pressure, and LinearAlgebra density/order-gap arithmetic. Cite: `ring_checkerboard_support_graph_probe_julia.jl:498-508`.

Caveat retained: JAX and PyTorch still honestly say the core semantics are mirrored pure-Python helpers, so this closes the missing/ambiguous-label gap, not the broader independence caveat.

### Gap 3: disagreement controls recompute

Decision: CLOSED.

The presentation disagreement controls now mutate rows, recompute row hashes, count changed rows, and compare original versus mutated values. Mutations are explicit: `drop_ring_coordinate`, `flatten_shell`, and `erase_nesting`. The old hardcoded controls are preserved only under `superseded_hardcoded_disagreement_controls`. Cites: `ring_checkerboard_support_graph_probe_jax.py:531-621`, `ring_checkerboard_support_graph_probe_pytorch.py:477-531`, `ring_checkerboard_support_graph_probe_julia.jl:336-395`.

Fresh recomputation emitted changed values:

```json
{
  "flat": {"mutation": "drop_ring_coordinate", "fired": true, "changed_row_count": 64, "agreement_after_mutation": false},
  "spherical-shell": {"mutation": "flatten_shell", "fired": true, "changed_row_count": 64, "agreement_after_mutation": false},
  "nested-ring": {"mutation": "erase_nesting", "fired": true, "changed_row_count": 64, "agreement_after_mutation": false}
}
```

Graph controls also still recompute changed values: shuffled adjacency changes mean absolute gradient to `0.608904558612`, erased coloring and erased nesting fire, reversed orientation flips signed gradients, and the SMT scramble creates a same-parity edge. Cites: `ring_checkerboard_support_graph_probe_jax.py:625-676`, `ring_checkerboard_support_graph_probe_pytorch.py:535-557`, `ring_checkerboard_support_graph_probe_julia.jl:399-414`.

### Gap 4: phi0_status on every leg

Decision: CLOSED.

All legs emit `phi0_status="candidate_support_graph_scalar_not_axis0"`, and the envelope requires that value for every leg. Cites: `ring_checkerboard_support_graph_probe_jax.py:805`, `ring_checkerboard_support_graph_probe_pytorch.py:644`, `ring_checkerboard_support_graph_probe_julia.jl:498`, `ring_checkerboard_support_graph_probe_envelope.py:138`.

Fresh result read:

```json
{
  "jax": "candidate_support_graph_scalar_not_axis0",
  "julia": "candidate_support_graph_scalar_not_axis0",
  "pytorch": "candidate_support_graph_scalar_not_axis0"
}
```

### Byte Stability

Decision: PASS.

Fresh in-memory recomputation from the JAX source path and envelope read matched the requested stable values exactly:

```json
{
  "vertices": 64,
  "edges": 120,
  "parity": 1.0,
  "cross_partition": 0.066666666667,
  "phi0_variance": 0.293978847053,
  "mean_abs_gradient": 0.131316967405,
  "orientation_delta": 0.119427896323,
  "out_degree": 1.875,
  "z3_coloring_unsat": 1.0,
  "cvc5_coloring_unsat": 1.0
}
```

### Validator

Decision: PASS.

Fresh command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_envelope_results.json
```

Fresh output:

```json
{
  "ok": true,
  "result_json": "system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_envelope_results.json"
}
```

### Stale Surface Check

Decision: PASS WITH HISTORICAL-CONTEXT NOTE.

The original `## Named Gaps` section above remains intentionally unchanged as the pre-hardening audit record. Outside that historical section, a stale-surface search for `count-bound`, `not per-edge`, `schematic`, `hardcoded as fired`, `open gap`, and `hardcoded` found only the explicitly named `superseded_hardcoded_disagreement_controls` fields and the build-card prohibition `No hardcoded literals`; no active surface now implies the four gaps remain open.

### Final Re-Audit Verdict

GENUINE-WITH-CAVEATS sustained.

Ceiling restated: `classification=scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. No Axis-0 closure, no manifold admission, no canonical support, no settled Xi, no physics/cosmology/consciousness/world-engine claim, and no collapse of the live readings preserved in the provenance material.

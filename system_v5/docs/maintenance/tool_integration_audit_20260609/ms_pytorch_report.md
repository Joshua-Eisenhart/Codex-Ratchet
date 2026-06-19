# PyTorch Leg TOOL-INTEGRATION Audit

Target source:
`/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_pytorch.py`

Target result:
`/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json`

Bottom line: the PyTorch leg is not a pure decorative stub. It really calls PyTorch-native graph, ODE, geometry, equivariance, autograd, optimization, and SMT APIs. But the result overstates several tools as `load_bearing`. The safest classification is mixed:

- genuinely load-bearing for this receipt: `torch`, `torchdiffeq`, `torch.func`, `xitorch`, `z3`, `cvc5`
- partially load-bearing / overstated: `torch_geometric`
- witness/control but not load-bearing on `all_pass`: `geomstats`, `clifford`, `torch_ga`, `e3nn`
- not used in this leg: `torchode`

The PyG answer to the direct question: `MessagePassing` is actually executing an octonion edge update through `message()` and `propagate()`. It is not a dummy stub. However, the reported `noncommutative_message_gap` is computed outside PyG from per-edge manual products, not from the routed aggregate `out`, so the receipt should not claim that PyG itself proves that gap unless the network readout is patched to derive a graph-routed noncommutative invariant from `out`.

## Checks Performed

- Read source and result JSON directly.
- Confirmed source hash in JSON matches live source: `1b733a4a373d0fb5348811b08ff1299bca6ccf3f83eec69fecdb57fa9d28fe04`.
- Ran canonical runtime doctor:
  - interpreter: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`
  - result: `ok=True install_state=stable_observed`
- Imported package versions in the canonical runtime:
  - `torch 2.11.0`
  - `torch_geometric 2.7.0`
  - `torchdiffeq 0.2.5`
  - `geomstats 2.8.0`
  - `clifford 1.5.1`
  - `torch_ga 0.0.6`
  - `e3nn 0.6.0`
  - `xitorch 0.3.0`
  - `cvc5 1.3.3`
- Confirmed `geomstats` backend is `geomstats.pytorch` and `Hypersphere.metric.dist` returns a torch tensor.
- Probed PyG routing with the same table/node/edge construction:
  - PyG output shape: `(4, 8)`
  - PyG aggregate equals manual destination aggregation: `True`
  - routed norm: `4.0`
  - permuting `edge_attr` changes routed output: `True`
  - per-edge forward/reverse noncommutative gap: `5.656854249492381`

## Per-Tool Verdicts

### `torch_geometric` / `MessagePassing`

Verdict: partially load-bearing, not decorative, but overstated.

Evidence:

- Source defines `OctonionEdgeMessagePassing(MessagePassing)` and calls `super().__init__(aggr="add")`.
- `forward()` calls `self.propagate(edge_index=edge_index, x=x, edge_attr=edge_attr)`.
- `message()` returns `table_multiply(self.table, edge_attr[i], x_j[i])` for each edge, so the update order is edge coefficient times source node state.
- A focused probe confirmed PyG output equals manual destination aggregation and changes when `edge_attr` is permuted.

Why it is not a stub:

- The graph engine routes source node states through `edge_index`.
- `edge_attr` is used inside the PyG `message()` path.
- The aggregate output `out` is used for `message_norm`.

Why the current claim is overstated:

- `network["noncommutative_message_gap"]` is computed outside PyG as `norm(forward - reverse)`.
- `forward` and `reverse` are per-edge manual stacks, not the `MessagePassing` aggregate output.
- `quotient_readout()` uses only `network["cycle_rank"] > 0`, not the PyG `message_norm` or a graph-routed noncommutative invariant.
- `all_pass` uses `quotient["drop_probe_strictly_coarsens"]`, but that predicate only requires `cycle_rank > 0` from the network field. The actual PyG output could be broken and `all_pass` would not necessarily fail unless the call itself errored.

API footguns:

- The `message()` signature uses annotations with `from __future__ import annotations`. PyG's inspector can fail if the module is dynamically loaded without registering it in `sys.modules`; I reproduced `KeyError: 'ptleg_audit'` under a naive `importlib.util.spec_from_file_location` harness. Normal script execution should be fine, but validators that import this file need to register the module before `exec_module`.
- `message()` uses a Python loop over edges and indexes by `edge_attr.shape[0]`; this is correct for the tiny probe but brittle for batched graphs and slower than a vectorized `einsum`.
- The class stores `self.table` as a plain tensor, not a registered buffer. That is okay for a script-only finite probe, but it will not move with `.to(device)` if the module is reused as a real `torch.nn.Module`.
- Because `message_norm` is only a norm, cancellation or rerouting errors could hide semantic defects. The receipt needs an output equality or route-specific invariant, not just a nonzero aggregate.

Patch direction:

- Keep PyG as real, but demote the current `torch_geometric` verdict to `partial_load_bearing` unless `all_pass` is made to depend on a PyG-routed noncommutative invariant.
- Add a `pyg_routed_forward_reverse_gap` computed through two `MessagePassing` instances or one `message_order` flag, then require that it flips against an associative/commuting control.
- Add a check that the PyG aggregate equals an explicit destination aggregation for this finite graph.

### `torchdiffeq` / `torchode`

Verdict: `torchdiffeq` is load-bearing for the current `all_pass`; `torchode` is not used.

Evidence:

- Source imports `odeint` from `torchdiffeq`.
- `dynamics_readout()` calls `odeint(rhs, rho0.reshape(-1), ts, rtol=1.0e-8, atol=1.0e-10)`.
- `all_pass` requires `abs(final_trace - 1.0) <= TOL`.
- Result records `final_excited_population = 0.7877603703752858` and `final_trace = 1.0000000000000004`.

Why `torchdiffeq` is genuinely load-bearing:

- If the ODE solve fails or trace is not conserved, `all_pass` fails.
- This is a real package API call, not just a recorded scalar.

Limits:

- The ODE is a local two-level Lindblad toy path, not coupled to the PyG node states or octonion edge update.
- The acceptance only gates trace conservation, not positivity, CP-ness across steps, or relation to the network state.
- `torchode` appears in the user's audit list and current runtime target set, but this script omits it. The JSON `omitted_tools` lists `torchode`, so the result is honest on omission.

API footguns:

- `torchdiffeq` is a candidate/witness generator in the current `pytorch-sim` skill, not a proof backbone.
- Complex ODE support works here, but future solvers/options may differ; pin the exact solver/method if the path becomes regression-tested.

Patch direction:

- Skill should require reporting `torchdiffeq` and `torchode` separately: `torchdiffeq_used`, `torchode_used`, `ode_solver_role`.
- Do not let a `torchdiffeq` trace check imply `torchode` coverage.
- Require positivity/eigenvalue and trace checks if an ODE path is marked load-bearing.

### `geomstats`

Verdict: real torch-backed geometry call, but witness/control rather than load-bearing on the current acceptance path.

Evidence:

- Source sets `GEOMSTATS_BACKEND=pytorch` before importing `Hypersphere`.
- `geometry_readout()` calls `Hypersphere(dim=3).metric.dist(spinor, erased)`.
- Focused probe confirmed backend module `geomstats.pytorch`, return type `torch.Tensor`, and value `2.0943951023931957`.
- `quotient_readout()` and `all_pass` depend on geometry fields through `chirality_split_norm > 0`, and the result also records the S3 distance.

Why it is not load-bearing:

- The quotient predicate does not require `s3_distance_to_erased_reference` specifically; it requires chirality split from plain torch tensor arithmetic.
- The geomstats distance is a real torch-backed geometry witness, but it is not the exact scalar currently gating `drop_probe_strictly_coarsens`.

API footguns:

- Backend must be set before importing `geomstats`. The source does this correctly with `os.environ.setdefault`.
- A stronger receipt should record the backend module and tensor type in JSON, not rely on environment convention.

Patch direction:

- Require `geomstats_backend == "geomstats.pytorch"` and `is_torch_tensor == true` in PyTorch receipts that mark `geomstats` load-bearing.
- Keep current `geomstats` status as `witness` unless at least one `all_pass`/control predicate depends on a geomstats-returned tensor, not only adjacent torch geometry.

### `clifford` / `torch_ga`

Verdict: real calls, useful carrier witnesses, not load-bearing on current `all_pass`.

Evidence:

- `carrier_tool_readouts()` calls `clifford.Cl(3)`.
- It computes `clifford_order_gap_sum_abs` from `blades["e1"] * blades["e2"] - blades["e2"] * blades["e1"]`.
- It constructs `torch_ga.GeometricAlgebra(metric=[1.0, 1.0, 1.0])` and computes `ga.geom_prod(e1, e2) - ga.geom_prod(e2, e1)`.
- Result records `clifford_order_gap_sum_abs = 2.0`, `torch_ga_order_gap = 2.0`, `torch_ga_blade_count = 8`.

Why this is not decorative:

- Both package APIs are actually invoked and return nontrivial carrier sanity checks.

Why it is not load-bearing:

- `carrier` output is included in JSON and `tool_calls`, but no `controls` predicate or `all_pass` condition depends on it.
- The decisive algebra controls use the local Cayley-Dickson table in `algebra_readouts()`, not `clifford` or `torch_ga`.
- The packages check Cl(3), not the octonion/sedenion table driving the main finite carrier.

API footguns:

- `clifford` uses its own multivector representation, not torch tensors; it is not differentiable torch machinery.
- `torch_ga` is torch-native here, but the receipt does not test autograd through `geom_prod`.
- `ga.blade_mvs[1]` and `[2]` depend on package blade ordering; okay for a micro receipt, but record blade labels if promoted.

Patch direction:

- Skill should distinguish `carrier_witness` from `load_bearing`.
- Require `torch_ga` load-bearing claims to include either autograd through `geom_prod` or direct dependence of a pass/fail predicate on `torch_ga` output.
- Do not count `clifford` as PyTorch-native load-bearing unless it certifies a torch-derived finite value or is explicitly a non-torch control.

### `e3nn`

Verdict: real API call and useful equivariance witness, but not load-bearing on current `all_pass`.

Evidence:

- `equivariance_readout()` calls `o3.matrix_z()` and `o3.Irreps("1x1o").D_from_matrix(rotation)`.
- Result records `so3_equivariance_residual = 5.3360049004682235e-15`.

Why it is not decorative:

- The code uses a real e3nn irreps representation matrix and compares it to a rotation action.

Why it is not load-bearing:

- `all_pass` does not require `equivariance["so3_equivariance_residual"] <= TOL`.
- `quotient_readout()` does not use equivariance at all.
- The check is a vector-image sanity witness, not directly connected to the Hopf output or network state in the acceptance path.

API footguns:

- `Irreps("1x1o")` is a vector irrep in this context, but the parity label may be irrelevant for a pure SO(3) matrix check.
- A residual of the representation matrix against `rotation @ vector` is expected to be tiny; a stronger test should include a deliberately wrong transform control.

Patch direction:

- Skill should require equivariance residual thresholds and a wrong-transform control before `e3nn` can be load-bearing.
- If `e3nn` is listed in `aligned_packages_load_bearing`, require `all_pass` to gate on its residual.

### `xitorch`

Verdict: load-bearing for current `all_pass`, but only as a candidate/witness generator.

Evidence:

- `xitorch_readout()` calls `xitorch.optimize.rootfinder`.
- `all_pass` requires `bool(xiroot["stable_positive"])`.
- Result records `positive_basin_fixed_point = 0.9575039380655463`, `stable_positive = true`.

Why it is load-bearing:

- If the root solve fails or returns non-positive, `all_pass` fails.

Limits:

- The scalar equation `y - tanh(a*y)` is an isolated basin-stability witness, not the finite basin update itself.
- This should not be treated as proof without exact/SMT/interval certification.

API footguns:

- Rootfinding can converge to different roots depending on initialization. Here the initial value is hardcoded positive.
- No negative-initialization or erased-control root solve is actually run, despite the tool call text saying negative control is erased basin update zero.

Patch direction:

- Skill should require rootfinder receipts to record initialization, residual norm, convergence status if available, and at least one alternate initial condition/control.
- Keep `xitorch` as `candidate_load_bearing` unless an exact or interval check certifies the solved property.

### `torch.func`

Verdict: load-bearing and genuinely PyTorch-native.

Evidence:

- `torch_func_sensitivity()` calls `jacrev(coherent_information_at)(strength0)`.
- `all_pass` requires `bool(sensitivity["nonzero"])`.
- Result records `coherent_information_strength_jacrev = 0.061400849112272005`, `nonzero = true`.

Why it is load-bearing:

- The pass/fail path depends directly on a `torch.func.jacrev` output.

Limits:

- The sensitivity spinor is local to the function and not the same exact `TARGET` used in the main QIT readout.
- It proves nonzero sensitivity of a related coherent-information expression, not full network sensitivity.

API footguns:

- `torch.tensor(-0.8, dtype=DTYPE)` constants inside the differentiated function are fixed, which is okay, but only `strength` is differentiated.
- A stronger check should also compare against finite differences or a zero-strength/control case for regression diagnostics.

Patch direction:

- Skill should require `torch.func` receipts to include the transformed function name, input shape/dtype, output scalar/tensor shape, and control/fallback comparison.
- Keep this as one of the best examples of a real PyTorch-native load-bearing role.

### `z3`

Verdict: load-bearing, but as a crossover proof check over torch-derived finite table entries.

Evidence:

- `z3_product_exprs()` expands each product into solver terms from `table_int(table, k, i, j)`.
- `z3_assoc_zero()` asserts associator equality and checks satisfiability.
- `z3_basin_escape()` encodes finite seed constraints and escape condition.
- `all_pass` requires the combined `z3_cvc5_derive_flip`.
- Result records octonion assoc-zero `unsat`, quaternion control `sat`, real escape `unsat`, erased escape `sat`.

Why it is load-bearing:

- If the Z3/cvc5 flip fails, `all_pass` fails.
- The solver derives formulas from table entries rather than only checking a precomputed scalar.

Limits:

- The table entries come from a locally generated torch Cayley-Dickson table, not an external canonical artifact with proof tags.
- `table_int()` silently assumes exact integer-valued float64 entries. It should assert all entries are within tolerance of integers before solver conversion.

API footguns:

- Python `sum` in `z3_basin_escape()` starts with integer `0`; Z3 overloads make it work, but explicit `z3.IntVal(0)` is cleaner and less fragile.
- Unsat/sat strings are compared as strings; acceptable for a receipt, but structured solver status would be safer.

Patch direction:

- Skill should require solver checks to record whether coefficients were integer-certified before conversion.
- Require exact source for table entries: local generated, Julia Canon artifact, or other, with proof tag if canonical claims are made.

### `cvc5`

Verdict: load-bearing, independent-ish crossover check, but with same table-source limits as Z3.

Evidence:

- `cvc5_product_exprs()` expands products with `Kind.MULT` and `Kind.ADD`.
- `cvc5_assoc_zero()` uses `QF_LIA`.
- `cvc5_basin_escape()` independently encodes the finite basin escape condition.
- `all_pass` requires cvc5 agreement in the combined flip.
- Result agrees with Z3 on all reported statuses.

Why it is load-bearing:

- If cvc5 disagrees, `all_pass` fails.

Limits:

- It is not a fully independent algebra source; it receives integerized coefficients from the same generated torch table.
- The solver path checks finite formulas, not the validity of the Cayley-Dickson table construction itself.

API footguns:

- `cvc5_and()` and `cvc5_or()` do not handle empty lists; current callers pass non-empty lists, but helper hardening would be cheap.
- cvc5 Python API changes around `Kind` and solver result strings can break receipts; record package version in result JSON.

Patch direction:

- Skill should require cvc5 and z3 result agreement to be represented as a named control, not hidden under a generic tool-call list.
- Require package versions for solver-backed receipts.

## Result JSON Issues

1. `TOOL_INTEGRATION_DEPTH` marks too many tools as `load_bearing`.
   - `geomstats`, `clifford`, `torch_ga`, and `e3nn` are real witness/control calls but do not gate `all_pass`.
   - `torch_geometric` is real but only partially gates the network role; `all_pass` does not depend on the graph-routed update itself.

2. `aligned_packages_load_bearing` includes packages that are not actually acceptance-bearing.
   - It lists `geomstats`, `clifford`, `torch_ga`, and `e3nn`, but those values do not feed `controls`, `quotient`, or `all_pass`.
   - It omits `torchdiffeq` and `xitorch`, both of which actually affect `all_pass`.

3. `tool_calls[0].output_object` for PyG points to `network["noncommutative_message_gap"]`, but that scalar is not the PyG aggregate output.
   - The PyG aggregate output is only represented by `message_norm`.
   - The named noncommutative gap is manually computed from per-edge products.

4. `quotient_readout()` accepts network evidence from `cycle_rank > 0`.
   - This is graph topology, not graph message-passing evidence.
   - A broken PyG update could leave `cycle_rank > 0` intact.

5. Tool versions and backend proof are not recorded in the result JSON.
   - Runtime-specific package truth matters in this repo.

## Concrete `pytorch-sim` Skill Patch Recommendations

Patch 1: update package status and runtime map date.

Replace the stale runtime-map reference with the current file name:

```md
Before package-dependent work or any install proposal, read
`system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md`
```

should become:

```md
Before package-dependent work or any install proposal, read the current
`system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_*.md` file, preferring the newest
dated map present in the repo, then run the doctor below.
```

Patch 2: add a `load_bearing` definition that depends on acceptance-path usage.

Add under `## Step 3: Make A Tool Load Bearing`:

```md
A package is `load_bearing` only when its output is consumed by a named control,
quotient predicate, verifier predicate, or `all_pass`/exit-status decision.
Actual import plus API call is `used`; a nontrivial diagnostic value that does
not affect acceptance is `witness`; text in `tool_calls` alone is never enough.
`aligned_packages_load_bearing` must be a subset of packages whose outputs gate
the result.
```

Patch 3: add a PyG-specific graph-engine gate.

Add under the tool list after `torch_geometric`:

```md
For `torch_geometric`, `MessagePassing.propagate` is load-bearing only if the
receipt records a graph-routed output invariant and `all_pass` depends on it.
Minimum receipt fields:

- `pyg_message_shape`
- `pyg_manual_destination_aggregate_equal`
- `pyg_edge_attr_changes_output`
- `pyg_routed_noncommutative_gap` or a named routed invariant
- a negative/control graph where the invariant flips

If the noncommutative scalar is computed outside `propagate`, classify PyG as
`partial_load_bearing` or `witness` unless a routed aggregate derived from PyG
also gates acceptance.
```

Patch 4: separate ODE packages.

Add:

```md
Record `torchdiffeq` and `torchode` separately. A `torchdiffeq.odeint` call does
not imply `torchode` coverage. ODE tools are candidate/witness generators unless
their output gates a finite check such as trace, positivity/eigenvalue bounds,
or a certified control. Record solver package, method/options, final trace,
minimum eigenvalue or positivity check when applicable, and whether the ODE
state is coupled to the claimed network/carrier state.
```

Patch 5: split witness packages from load-bearing packages in the emitted receipt.

Change the sample result fragment to include:

```json
"packages_used": ["torch", "torch_geometric", "torchdiffeq", "geomstats"],
"packages_witness": ["clifford", "torch_ga", "e3nn"],
"aligned_packages_load_bearing": ["torch_geometric", "torch.func", "z3", "cvc5"],
"acceptance_dependencies": {
  "torch_geometric": ["pyg_routed_noncommutative_gap"],
  "torch.func": ["coherent_information_strength_jacrev_nonzero"],
  "z3": ["octonion_assoc_zero_unsat", "real_basin_escape_unsat"],
  "cvc5": ["octonion_assoc_zero_unsat", "real_basin_escape_unsat"]
}
```

Patch 6: require backend/version receipts for fragile APIs.

Add:

```md
For `geomstats`, record backend module and whether the returned distance is a
torch tensor. For `cvc5`, `z3`, `torch_geometric`, `torchdiffeq`, `torchode`,
`torch_ga`, and `e3nn`, record package versions in result JSON. Version/import
success is not claim integration, but missing version/backend evidence demotes
the package to `used_unverified` for audit purposes.
```

Patch 7: harden solver table conversion.

Add:

```md
Before sending torch-generated finite algebra tables to `z3` or `cvc5`, assert
that every coefficient is within tolerance of an integer and record the max
rounding residual. Solver load-bearing status requires the formula to be built
from those certified coefficients, not from precomputed scalar summaries.
```

Patch 8: add import-harness warning for PyG annotations.

Add:

```md
When dynamically importing a PyG `MessagePassing` script for audit, register the
module in `sys.modules` before `exec_module`. PyG inspects annotated `message()`
signatures and can fail under unregistered `importlib` harnesses even when the
script itself runs normally.
```

## Recommended Local Source Fixes For This Specific Leg

These are recommendations only; no repo files were changed in this audit.

1. Change `OctonionEdgeMessagePassing` to register `table` as a buffer:

```python
self.register_buffer("table", table)
```

2. Add a second message-passing path or flag for reversed multiplication order, then compute:

```python
pyg_forward = mp_forward(data.x, data.edge_index, data.edge_attr)
pyg_reverse = mp_reverse(data.x, data.edge_index, data.edge_attr)
pyg_routed_noncommutative_gap = torch.linalg.norm(pyg_forward - pyg_reverse)
```

3. Make `quotient_readout()` require `pyg_routed_noncommutative_gap > TOL`, not only `cycle_rank > 0`.

4. Add `controls["pyg_routed_noncommutative_control"]` and require it in `all_pass`.

5. Move `clifford`, `torch_ga`, and `e3nn` from `load_bearing` to `witness` unless their outputs become acceptance dependencies.

6. Move `torchdiffeq` and `xitorch` into `aligned_packages_load_bearing` if keeping the current `all_pass` logic, because both currently gate acceptance.

7. Record:

```json
"package_versions": {...},
"geomstats_backend": "geomstats.pytorch",
"pyg_manual_destination_aggregate_equal": true,
"pyg_edge_attr_changes_output": true
```

## Final Classification

This PyTorch leg is a real `scratch_diagnostic` integration scout with several genuine package calls. It should not be promoted as a clean full-stack PyTorch tool integration until the receipt separates `used`, `witness`, `partial_load_bearing`, and `load_bearing`, and until the PyG network-engine role gates acceptance through a graph-routed noncommutative invariant.

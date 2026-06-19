# Fresh read-only audit: `foundation_spinor_network_full_stack_layer`

Bottom line: **partly-decorative**.

The packet is not inflated wholesale: the core algebra, QIT coherent-information, ODE trace/population, finite-basin controls, and Z3/cvc5 derive-in-solver checks are real and value-coupled. But several advertised rich-tool calls are side receipts: they are imported/called and recorded, but their outputs do not gate the engine `all_pass`, the envelope `all_pass`, or the envelope `max_divergence`.

## Files inspected

- `system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_envelope.py`
- `system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_jax.py`
- `system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_pytorch.py`
- `system_v5/julia_carrier/foundation_spinor_network_full_stack_layer_julia.jl`
- `system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_jax_results.json`
- `system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json`
- `system_v5/julia_carrier/results/foundation_spinor_network_full_stack_layer_julia_results.json`

## Direct checks

- Source hashes in the result receipts match the current source files:
  - Julia: `cb02c47fa2f300491e0f4a426d101ecc5448047f4f7f174bd9bfbc23abe5c805`
  - JAX: `de453221f701b7838d12ac8a7d565487a8db1bdba7060962b848e51608596cc8`
  - PyTorch: `1b733a4a373d0fb5348811b08ff1299bca6ccf3f83eec69fecdb57fa9d28fe04`
  - Envelope: `5cc482172a479a65a2da85641f6a56a8fcf1e907ea76a0c83153338710883e69`
- `scripts/validate_three_engine_sim_result.py --require-pytorch system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json` returned `{"ok": true, ...}`.
- Engine result counts are `julia=11`, `jax=7`, `pytorch=9`, for 27 total `tool_calls`.
- Engine legs set `reads_peer_result=false`. Grep found no `read_text`, peer-result JSON load, `numpy`, `np.asarray`, or `.numpy()` claim path in the three engine legs. Only the envelope reads the three engine JSON receipts, as expected for aggregation.
- Envelope `max_divergence` is `2.3040302998822426e-10`, computed from shared scalar values loaded from the three independent engine result JSONs.

## Key source facts

- JAX `dynamiqs`: `res.states.to_jax()[-1]` is actually used to compute `dynamiqs_final_entropy`.
- JAX `diffrax`: `diffeqsolve` is called in `diffrax_basin_flow`, and separately in `dynamics_readout` for final trace/population.
- Julia `Attractors`: `CoupledODEs`, `AttractorsViaProximity`, and `basins_of_attraction` are actually called and return two attractor labels.
- PyTorch `torch_geometric`: `MessagePassing.propagate` routes through `message`, where octonion table multiplication is applied to `edge_attr` and `x_j`.
- PyTorch `torchdiffeq`: `odeint` is actually called for the Lindblad-style node ODE. The prompt mentions `torchode`, but this file omits `torchode` and uses `torchdiffeq`.
- Z3 and cvc5 product expressions expand table entries inside solver terms; they are not merely checking a precomputed scalar.
- Octonion associator and quaternion zero control are value-coupled across engines: octonion associator norm is `2.0`, quaternion associator control is `0.0`.
- Sedenion zero-divisor control is value-coupled to zero product plus nonzero factor norms, but the stated "octonion division control" is not a separately computed negative-control value.

## Per-tool-call verdicts

Criterion used here: **load-bearing** means the tool output gates engine `all_pass`, envelope `all_pass`, envelope `max_divergence`, or a named negative-control/proof value used by those gates. **Decorative** means the call is real but only recorded as a side readout/tool receipt.

### Julia, 11 calls

| # | Tool | Verdict | Evidence |
|---|---|---|---|
| J1 | `Octonions` | LOAD-BEARING | Computes nonzero octonion associator; feeds `associative_control`, quotient coarsening, scalar divergence. |
| J2 | `Quaternions` | LOAD-BEARING | Computes quaternion order gap and associative-zero control; feeds `commuting_control` and `associative_control`. |
| J3 | `Cayley-Dickson` | LOAD-BEARING | Computes sedenion zero product plus nonzero factors; gates `sedenion_zero_divisor_kill`. Negative "octonion division control" is text only. |
| J4 | `QuantumOptics` | LOAD-BEARING | Computes coherent information and erased control; gates `carrier_erasure` and quotient coarsening. |
| J5 | `DifferentialEquations` | LOAD-BEARING | `ODEProblem/solve` output gates trace check and contributes final population to divergence. |
| J6 | `Attractors+DynamicalSystems` | DECORATIVE for final pass | Real `basins_of_attraction` call, but engine/envelope `basin_control` uses `finite_basins`, not `attractors_package_basin`. |
| J7 | `Manifolds` | DECORATIVE for final pass | Computes S3 distance, but `all_pass` uses chirality split/no-chirality from plain matrix norms, not the distance. |
| J8 | `Graphs` | LOAD-BEARING | Cycle rank feeds quotient coarsening and cross-engine scalar divergence. |
| J9 | `ITensors` | DECORATIVE for final pass | Tensor contraction norm is recorded but does not gate controls, quotient, or divergence. |
| J10 | `Yao` | DECORATIVE for final pass | X/H commutator norm is recorded in dynamics/tool call but not used by `all_pass` or divergence. |
| J11 | `Z3` | LOAD-BEARING | Solver expands table products and basin update terms; gates `z3_derive_flip` and envelope proof matrix. |

### JAX, 7 calls

| # | Tool | Verdict | Evidence |
|---|---|---|---|
| X1 | `dynamiqs` | DECORATIVE for final pass | `QArray.to_jax()` is genuinely used for `dynamiqs_final_entropy`, but that entropy does not gate controls, quotient, or divergence. |
| X2 | `diffrax+jax.vmap` | DECORATIVE for final pass | Real `diffeqsolve` over finite seeds, but the pass-gating basin control uses `finite_basins`, not this `diffrax_basin_flow`. Separately, `diffrax` is load-bearing via the unlisted dynamics trace/population path. |
| X3 | `quimb+cotengra` | DECORATIVE for final pass | MPS contraction is real, but contraction norm is not used by `all_pass`, quotient, or divergence. |
| X4 | `e3nn_jax` | DECORATIVE for final pass | SO(3) residual is computed, but not used by `all_pass`, quotient, or divergence. |
| X5 | `jax` | DECORATIVE for final pass | `vmap/einsum` computes noncommutative message gap, but quotient/pass use `cycle_rank`, not the message gap. |
| X6 | `z3` | LOAD-BEARING | Derive-in-solver associator and basin checks gate `z3_cvc5_derive_flip` and envelope proof matrix. |
| X7 | `cvc5` | LOAD-BEARING | Same derive-in-solver checks as Z3; gates `z3_cvc5_derive_flip` and envelope proof matrix. |

### PyTorch, 9 calls

| # | Tool | Verdict | Evidence |
|---|---|---|---|
| P1 | `torch_geometric` | DECORATIVE for final pass | `MessagePassing.propagate` really performs octonion edge multiplication, but final gates use `cycle_rank`, not `noncommutative_message_gap`. |
| P2 | `torchdiffeq` | LOAD-BEARING | `odeint` output gates trace check and contributes final population to divergence. |
| P3 | `geomstats` | DECORATIVE for final pass | S3 distance is recorded but not used by `all_pass`, quotient, or divergence. Also source does not set `GEOMSTATS_BACKEND=pytorch`, so torch-backed status is not proven from the file alone. |
| P4 | `clifford/torch_ga` | DECORATIVE for final pass | Carrier order gaps are computed, but not used by controls, `all_pass`, quotient, or divergence. |
| P5 | `e3nn` | DECORATIVE for final pass | SO(3) residual is computed, but not used by `all_pass`, quotient, or divergence. |
| P6 | `xitorch` | LOAD-BEARING | `rootfinder` result gates PyTorch engine `all_pass` via `stable_positive`. |
| P7 | `torch.func` | LOAD-BEARING | `jacrev` sensitivity gates PyTorch engine `all_pass` via nonzero sensitivity. |
| P8 | `z3` | LOAD-BEARING | Derive-in-solver associator and basin checks gate `z3_cvc5_derive_flip` and envelope proof matrix. |
| P9 | `cvc5` | LOAD-BEARING | Same derive-in-solver checks as Z3; gates `z3_cvc5_derive_flip` and envelope proof matrix. |

## Controls

- `commuting_control`: genuine value-coupled flip in all engines: structured `2.0`, control `0.0`.
- `associative_control`: genuine value-coupled flip in all engines: octonion `2.0`, quaternion `0.0`.
- `sedenion_zero_divisor_kill`: product/factor check is genuine; separate octonion division-control value is not computed.
- `carrier_erasure`: genuine value-coupled flip in all engines: structured coherent information about `0.693147180559945`, erased `-0.6931471805599453`.
- `no_chirality`: genuine value-coupled flip in all engines: chirality split about `0.632455532033676`, no-chirality control `0.0`.
- `basin_control`: genuine finite-state value flip in all engines, but it is not the Julia `Attractors` basin result or the JAX `diffrax_basin_flow`; it comes from local finite update functions.
- `z3/cvc5_derive_flip`: genuine derive-in-solver flip for JAX/PyTorch Z3+cvc5 and Julia Z3. Julia has no cvc5 leg.

## TMR / cross-substrate divergence

The `2.3040302998822426e-10` max divergence is a genuine cross-engine comparison over locally produced scalar result JSONs, not a numpy claim path and not an engine peer-read. Limits:

- It compares stored scalar receipts, not live tensor exchange.
- It omits rich per-tool objects such as tensor contraction, equivariance residual, Attractors basin receipt, PyG message gap, and torch carrier-tool gap.
- It therefore supports `scratch_diagnostic` cross-substrate agreement over selected scalar observables, not a full-stack claim that every listed package is necessary.

## Final classification

**partly-decorative**.

Load-bearing core: Julia `Octonions`, `Quaternions`, `Cayley-Dickson`, `QuantumOptics`, `DifferentialEquations`, `Graphs`, `Z3`; JAX `z3`, `cvc5` plus `diffrax` only through the dynamics path; PyTorch `torchdiffeq`, `xitorch`, `torch.func`, `z3`, `cvc5`; envelope scalar divergence and controls.

Decorative or side-receipt tools in the 27 explicit `tool_calls`: Julia `Attractors+DynamicalSystems`, `Manifolds`, `ITensors`, `Yao`; JAX `dynamiqs`, `diffrax+jax.vmap`, `quimb+cotengra`, `e3nn_jax`, `jax` message-gap call; PyTorch `torch_geometric`, `geomstats`, `clifford/torch_ga`, `e3nn`.

Not inflated enough to reject the artifact as fake: the core gates are real, and the source/result hashes line up. But it should not be called `genuine-full-stack-integration` because multiple rich tool calls are not actually necessary for the final pass or cross-engine divergence.

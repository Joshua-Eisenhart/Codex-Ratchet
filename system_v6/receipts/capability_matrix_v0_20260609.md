# CAPABILITY-PROBE MATRIX v0

Scope: `/Users/joshuaeisenhart/Codex-Ratchet`, read-only inventory lane. Written artifact only: `/tmp/found/capability_matrix_v0.md`.

Status rule: `PROVEN` means a passing capability probe result exists under `system_v4/probes/a2_state/sim_results/` with `summary.all_pass`, `all_pass`, `overall_pass`, or `passed == true`. `USED-UNPROVEN` means the package appears in current sims, envelope usage, or result receipts, but no qualifying capability probe exists for that package/math cell. `EMPTY` means I found no current serving package evidence for that engine/cell. Julia has installed and used carrier packages, but no qualifying v4 Julia capability probe surface, so Julia cells below are not marked `PROVEN`.

## Matrix

| # | Math class | julia | jax/python | pytorch/python |
|---:|---|---|---|---|
| 1 | division algebras: quaternion/octonion/sedenion structure constants | `USED-UNPROVEN`: `Quaternions`, `Octonions`, `Grassmann`, `CliffordAlgebras`; used in carrier/canon/division results, no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/Project.toml`, `system_v5/codex_skills/three-engine-sim/references/tested_package_patterns.md`, `system_v5/julia_carrier/division_algebra_ratchet_ladder_julia_results.json`, `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json`. | `USED-UNPROVEN`: `jax`, `jax.numpy`; used by `system_v5/julia_carrier/jax_division_algebra_ratchet_ladder.py` and results, but no passing `jax` capability probe. Evidence: `system_v5/julia_carrier/division_algebra_ratchet_ladder_jax_results.json`. | `EMPTY`: no current PyTorch division-algebra capability or current sim evidence found. |
| 2 | nonassociativity: associator, Jordan | `USED-UNPROVEN`: `Octonions`, `Grassmann`, `CliffordAlgebras`; used in nonassoc/foundation results, no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/nonassociativity_as_probe_bracketing_julia_results.json`, `system_v5/julia_carrier/results/foundation_foundation_r3_j3o_jordan_julia_results.json`, `system_v5/julia_carrier/results/foundation_r3_associator_xhigh_julia_results.json`. | `USED-UNPROVEN`: `jax`, `jax.numpy`; used in `system_v5/julia_carrier/jax_nonassociativity_as_probe_bracketing.py`, no passing `jax` capability probe. Evidence: `system_v5/julia_carrier/nonassociativity_as_probe_bracketing_jax_results.json`. | `EMPTY`: no current PyTorch nonassociativity package/probe evidence found. |
| 3 | Clifford/geometric algebra | `USED-UNPROVEN`: `CliffordAlgebras`, `QuantumClifford`, `Z3`; installed and source-backed in current envelopes, but no v4 Julia probe. Evidence: `system_v5/evidence/sim_tool_library_coverage_20260608.json`, `system_v5/julia_carrier/clifford_algebra_ladder_julia_results.json`, `system_v5/julia_carrier/clifford_spinor_carrier_rung_julia_results.json`. | `USED-UNPROVEN`: `jax`, `jax.numpy`, `z3-solver`, `cvc5`; JAX Clifford/spinor SMT result exists, but the proven probes are solver capability, not JAX Clifford capability. Solver probe paths: `system_v4/probes/a2_state/sim_results/z3_capability_results.json`, `system_v4/probes/a2_state/sim_results/cvc5_capability_results.json`. Use evidence: `system_v5/julia_carrier/jax_clifford_spinor_carrier_smt_results.json`. | `USED-UNPROVEN`: `torch_ga`, `torch.func`, `torch`; `torch` itself is proven, but `torch_ga` has no passing capability result. Torch probe paths: `system_v4/probes/a2_state/sim_results/pytorch_capability_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_torch_results.json`. Missing `torch_ga` result: `system_v4/probes/tool_capability_torch_ga.py` has no matching passing result. Current use: `system_v5/evidence/sim_tool_library_coverage_20260608.json`. |
| 4 | spinor geometry: Hopf, Weyl chirality | `USED-UNPROVEN`: `CliffordAlgebras`, `QuantumClifford`, `Manifolds`, `QuantumOptics`; used in Julia carrier spinor/Hopf/Weyl results, no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/density_matrix_spinor_lift_julia_results.json`, `system_v5/julia_carrier/hopf_three_ways_julia_results.json`, `system_v5/julia_carrier/results/foundation_foundation_r5_hopf_fibration_julia_results.json`, `system_v5/julia_carrier/results/foundation_foundation_r5_weyl_chirality_pair_julia_results.json`. | `PROVEN` for supporting Python geometry packages `geomstats`, `clifford`, `sympy`, `z3-solver`, `cvc5`; not a native JAX spinor proof. Probe paths: `system_v4/probes/a2_state/sim_results/geomstats_capability_results.json`, `system_v4/probes/a2_state/sim_results/clifford_capability_results.json`, `system_v4/probes/a2_state/sim_results/sympy_capability_results.json`, `system_v4/probes/a2_state/sim_results/z3_capability_results.json`, `system_v4/probes/a2_state/sim_results/cvc5_capability_results.json`. JAX use evidence: `system_v5/julia_carrier/hopf_three_ways_jax_results.json`, `system_v5/julia_carrier/density_matrix_spinor_lift_jax_results.json`. | `USED-UNPROVEN`: `torch`, `torch.func`, `torch_ga`, `e3nn`; `torch`/`e3nn` have passing capability probes, but the spinor/GA dependency `torch_ga` is unproven. Probe paths: `system_v4/probes/a2_state/sim_results/tool_capability_torch_results.json`, `system_v4/probes/a2_state/sim_results/e3nn_capability_results.json`. Current `torch_ga` use: `system_v5/evidence/sim_tool_library_coverage_20260608.json`. |
| 5 | quantum info: density/Lindblad/entropies/stabilizers | `USED-UNPROVEN`: `QuantumOptics`, `QuantumToolbox`, `QuantumClifford`, `Yao`, `ITensors`; installed/current-envelope use, no v4 Julia capability probe. Evidence: `system_v5/evidence/sim_tool_library_coverage_20260608.json`, `system_v5/julia_carrier/qit_density_entropy_3qubit_cl6_julia_results.json`, `system_v5/julia_carrier/carnot_szilard_qit_engine_julia_results.json`. | `PROVEN` for `qutip` QIT primitives and solver sidecars; `dynamiqs`, `netket`, `qutip-jax` are installed/targeted but not proven by v4 capability probes. Probe paths: `system_v4/probes/a2_state/sim_results/qutip_capability_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_qutip_results.json`, `system_v4/probes/a2_state/sim_results/z3_capability_results.json`, `system_v4/probes/a2_state/sim_results/cvc5_capability_results.json`. Current use: `system_v5/evidence/sim_tool_library_coverage_20260608.json`. | `PROVEN` for `torch` density/entropy autograd primitives; `torch_ga` remains unproven where GA enters. Probe paths: `system_v4/probes/a2_state/sim_results/pytorch_capability_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_torch_results.json`. Use evidence: `system_v4/probes/a2_state/sim_results/sim_pytorch_density_entropy_gradient_micro_results.json`, `system_v5/ops/wizard_admissions/coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3.json`. |
| 6 | dynamics + attractors: ODE/master eq/basins | `USED-UNPROVEN`: `DifferentialEquations`, `DynamicalSystems`, `Attractors`, `ChaosTools`, `QuantumOptics`; installed and used/named, no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/Project.toml`, `system_v5/julia_carrier/explore_julia_results.json`, `system_v5/evidence/sim_tool_library_coverage_20260608.json`. | `USED-UNPROVEN`: `diffrax`, `dynamiqs`, `jax`; installed and target-mapped, but no passing capability probe for these packages. Evidence: `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`, `system_v5/evidence/sim_tool_library_coverage_20260608.json`. `qutip` master-equation support has passing Python probe/use: `system_v4/probes/a2_state/sim_results/qutip_capability_results.json`, `system_v4/probes/a2_state/sim_results/sim_qutip_mesolve_scipy_liouvillian_amplitude_damping_reference_micro_results.json`. | `PROVEN` only for `torch` differentiable dynamics/autograd primitives, not for a dedicated attractor/master-equation package. Probe path: `system_v4/probes/a2_state/sim_results/pytorch_capability_results.json`. |
| 7 | topology/TDA/hypergraphs | `USED-UNPROVEN`: `Graphs`; Julia graph package installed but no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/Project.toml`. | `PROVEN`: `gudhi`, `TopoNetX`, `XGI`, `rustworkx`, `networkx`. Probe paths: `system_v4/probes/a2_state/sim_results/gudhi_capability_results.json`, `system_v4/probes/a2_state/sim_results/toponetx_capability_results.json`, `system_v4/probes/a2_state/sim_results/xgi_capability_results.json`, `system_v4/probes/a2_state/sim_results/rustworkx_capability_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_networkx_results.json`. | `PROVEN` for graph-message substrate via `torch_geometric`; TDA itself is Python-side, not torch-native. Probe paths: `system_v4/probes/a2_state/sim_results/sim_capability_pyg_isolated_results.json`, `system_v4/probes/a2_state/sim_results/sim_pyg_hopf_graph_deep_capability_results.json`. |
| 8 | tensor networks: MPS/contraction | `USED-UNPROVEN`: `ITensors`, `ITensorMPS`; installed and used, no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/Project.toml`, `system_v5/julia_carrier/hopf_linking_itensors_clifford_result.json`. | `USED-UNPROVEN`: `quimb`, `cotengra`, `opt_einsum`; installed/targeted and named in current evidence index, but no passing capability probe found. Evidence: `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`, `system_v5/evidence/sim_tool_library_coverage_20260608.json`, `system_v5/evidence/sim_estate_integration_index.json`. | `USED-UNPROVEN`: `torch`, `opt_einsum`, `torch_geometric` in MPS/graph leakage sims; `torch` is proven, tensor-network contraction package is not. Probe path for torch only: `system_v4/probes/a2_state/sim_results/tool_capability_torch_results.json`. Use evidence: `system_v5/evidence/sim_estate_integration_index.json` entries such as `eight_qubit_mps_channel_order_graph_leakage_pyg_pytorch_opt_einsum_z3_probe`. |
| 9 | equivariance: SU(2)/SO(3) | `USED-UNPROVEN`: `CliffordAlgebras`, `Manifolds`, `QuantumClifford`; no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/hurwitz_minimality_prelim_julia_results.json`, `system_v5/julia_carrier/gs_sp2_quaternionic_results.json`, `system_v5/julia_carrier/gs_su3_calabiyau_julia_results.json`. | `USED-UNPROVEN`: `e3nn-jax`, `jax`; installed/targeted, no v4 `e3nn_jax` capability probe. Evidence: `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`. | `PROVEN`: `e3nn` + `torch` for SO(3) equivariance. Probe paths: `system_v4/probes/a2_state/sim_results/e3nn_capability_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_torch_results.json`. |
| 10 | manifolds + symbolic exact | `USED-UNPROVEN`: `Manifolds`, `Symbolics`; installed, no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/Project.toml`. | `PROVEN`: `geomstats`, `sympy`, plus `z3-solver`/`cvc5` exact checks. Probe paths: `system_v4/probes/a2_state/sim_results/geomstats_capability_results.json`, `system_v4/probes/a2_state/sim_results/sympy_capability_results.json`, `system_v4/probes/a2_state/sim_results/z3_capability_results.json`, `system_v4/probes/a2_state/sim_results/cvc5_capability_results.json`. | `PROVEN` for Python packages usable from torch-side workflows: `geomstats`, `sympy`, `torch`. Probe paths: `system_v4/probes/a2_state/sim_results/geomstats_capability_results.json`, `system_v4/probes/a2_state/sim_results/sympy_capability_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_torch_results.json`. |
| 11 | proof: SMT derive-in-solver | `USED-UNPROVEN`: Julia `Z3` installed and used in carrier results, but no v4 Julia capability probe. Evidence: `system_v5/julia_carrier/Project.toml`, `system_v5/evidence/sim_tool_library_coverage_20260608.json`, `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json`. | `PROVEN`: `z3-solver`, `cvc5`, `sympy` sidecars. Probe paths: `system_v4/probes/a2_state/sim_results/z3_capability_results.json`, `system_v4/probes/a2_state/sim_results/cvc5_capability_results.json`, `system_v4/probes/a2_state/sim_results/sympy_capability_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_z3_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_cvc5_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_sympy_results.json`. | `PROVEN` for Python solver sidecars and torch autograd witness generation, not a torch-native theorem prover. Probe paths: `system_v4/probes/a2_state/sim_results/z3_capability_results.json`, `system_v4/probes/a2_state/sim_results/cvc5_capability_results.json`, `system_v4/probes/a2_state/sim_results/pytorch_capability_results.json`. |
| 12 | GNN/message-passing | `EMPTY`: no installed/current Julia GNN package in strict carrier project; coverage explicitly lists Julia NN/graph packages as missing/unchecked. Evidence: `system_v5/evidence/sim_tool_library_coverage_20260608.json`. | `USED-UNPROVEN`: `jraph`, `jax`, possibly `e3nn-jax`; installed/targeted, no passing v4 capability probe. Evidence: `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`. | `PROVEN`: `torch_geometric`, `torch`, `e3nn` for graph/equivariant message passing. Probe paths: `system_v4/probes/a2_state/sim_results/sim_capability_pyg_isolated_results.json`, `system_v4/probes/a2_state/sim_results/sim_pyg_hopf_graph_deep_capability_results.json`, `system_v4/probes/a2_state/sim_results/e3nn_capability_results.json`, `system_v4/probes/a2_state/sim_results/tool_capability_torch_results.json`. |

## 1. Redundancy Gaps

Classes with fewer than two engines `PROVEN` under the strict v4 capability-probe rule:

1. Division algebras: 0 engines proven. Julia and JAX are active/used; both need explicit capability probes.
2. Nonassociativity/Jordan: 0 engines proven. Julia and JAX have results, but no qualifying capability probe.
3. Clifford/geometric algebra: 0 strict engine cells proven for the three-engine target. Python `clifford` is proven, but that is not Julia `CliffordAlgebras`, JAX-native Clifford, or PyTorch `torch_ga`.
4. Spinor geometry: 1 engine-ish cell proven through Python support packages; PyTorch remains blocked by `torch_ga` unproven, Julia unproven.
5. Quantum info: 2 engines have proven Python/PyTorch support (`qutip`, `torch`), Julia is used-unproven.
6. Dynamics/attractors: at most 1 engine proven, and only through generic `torch`/`qutip` support; Julia/JAX dedicated dynamics packages need probes.
7. Topology/TDA/hypergraphs: 2 engines proven (`jax/python` Python topology stack and PyTorch graph substrate); Julia graph/topology is unproven.
8. Tensor networks: 0 engines proven. `ITensors`, `quimb`, `cotengra`, and torch-side contraction use all need explicit capability probes.
9. Equivariance: 1 engine proven (`pytorch/e3nn`); JAX `e3nn-jax` and Julia SU(2)/SO(3) carrier probes are missing.
10. Manifolds + symbolic exact: 2 engines proven via Python packages (`geomstats`, `sympy`, solver sidecars) plus torch support; Julia is unproven.
11. Proof/SMT derive-in-solver: 2 engines proven on Python side (`z3`, `cvc5`, `sympy` used from JAX/PyTorch workflows); Julia `Z3` is used-unproven.
12. GNN/message-passing: 1 engine proven (`torch_geometric`); JAX `jraph` and Julia graph-NN packages are not proven/current.

Highest-risk redundancy gaps for the owner’s goal: classes 1, 2, 3, 8, and 9.

## 2. Package Health

Versions checked from `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pip show ...` and `system_v5/julia_carrier/Manifest.toml`. Health is local operational health, not scientific admission. `FRAGILE` includes the user-provided external-scan warning for `clifford` and `torch_ga`.

| Package | Engine | Installed version | Health | Reason |
|---|---|---:|---|---|
| `Quaternions` | Julia | `0.7.7` | AGING | Specialized package; used for carrier constants, but no capability probe. |
| `Octonions` | Julia | `0.2.3` | AGING | Specialized 0.x package; used in carrier constants, no capability probe. |
| `Grassmann` | Julia | `0.8.44` | AGING | Source-backed use is narrow; no capability probe. |
| `CliffordAlgebras` | Julia | `0.1.4` | AGING | Strict-carrier load works, but early 0.x API and no Julia capability probe. |
| `QuantumClifford` | Julia | `0.11.4` | HEALTHY | Active strict-carrier dependency; no class-specific probe yet. |
| `QuantumOptics` | Julia | `1.2.6` | HEALTHY | Source-backed current envelope use; needs v4 capability probe for proof. |
| `QuantumToolbox` | Julia | `0.47.0` | AGING | Installed in strict carrier; 0.x and not source-backed in current envelope counts. |
| `Yao` | Julia | `0.9.3` | AGING | Installed; no current source-backed envelope usage in coverage. |
| `DifferentialEquations` | Julia | `8.0.0` | HEALTHY | Current major SciML package; no local capability probe. |
| `DynamicalSystems` | Julia | `3.6.8` | HEALTHY | Installed dynamics stack; no local capability probe. |
| `Attractors` | Julia | `1.37.0` | HEALTHY | Installed attractor package; over-claim risk until probed. |
| `ChaosTools` | Julia | `3.5.4` | HEALTHY | Installed support package; no class probe. |
| `Graphs` | Julia | `1.14.0` | HEALTHY | Standard Julia graph package; no strict-carrier capability probe. |
| `ITensors` | Julia | `0.9.30` | HEALTHY | Current tensor package installed; no tensor capability probe. |
| `ITensorMPS` | Julia | `0.4.1` | AGING | MPS package is 0.x; no capability probe. |
| `Manifolds` | Julia | `0.11.27` | HEALTHY | Installed geometry package; no capability probe. |
| `Symbolics` | Julia | `7.26.0` | HEALTHY | Current symbolic package; no strict-carrier proof probe. |
| `Z3` | Julia | `1.0.4` | HEALTHY | Installed/used; no Julia-side derive-in-solver probe under v4. |
| `jax` / `jaxlib` | JAX/Python | `0.10.1` / `0.10.1` | HEALTHY | Canonical env current target; surprisingly no v4 `jax` capability probe. |
| `diffrax` | JAX/Python | `0.7.2` | HEALTHY | Dedicated JAX dynamics package; missing capability probe. |
| `dynamiqs` | JAX/Python | `0.3.4` | AGING | Useful JAX QIT/dynamics package, but 0.x and unproven locally. |
| `netket` | JAX/Python | `3.21.0` | HEALTHY | Installed many-body/QIT package; no current capability probe. |
| `qutip` | JAX/Python | `5.2.3` | HEALTHY | Passing QIT capability probes exist. |
| `qutip-jax` | JAX/Python | `0.1.1` | FRAGILE | Early bridge package; installed but no v4 capability probe. |
| `quimb` | JAX/Python | `1.14.0` | HEALTHY | Tensor/QIT package installed; no capability probe found. |
| `cotengra` | JAX/Python | `0.8.0` | HEALTHY | Contraction optimizer installed; no capability probe found. |
| `e3nn-jax` | JAX/Python | `0.21.0` | AGING | Installed, but no local `e3nn_jax` probe; PyTorch `e3nn` is the proven side. |
| `jraph` | JAX/Python | `0.0.6.dev0` | FRAGILE | Dev-version GNN package; no capability probe. |
| `ott-jax` | JAX/Python | `0.6.0` | AGING | Installed optional geometry/OT package; no current matrix use/probe. |
| `z3-solver` | Python sidecar | `4.16.0.0` | HEALTHY | Passing capability probes exist. |
| `cvc5` | Python sidecar | `1.3.3` | HEALTHY | Passing capability probes exist. |
| `sympy` | Python sidecar | `1.14.0` | HEALTHY | Passing capability probes exist. |
| `gudhi` | Python | `3.12.0` | HEALTHY | Passing TDA capability probes exist. |
| `TopoNetX` | Python | `0.4.0` | AGING | Passing probe exists, but 0.x research API. |
| `xgi` | Python | `0.10.1` | AGING | Passing probe exists, but 0.x research API. |
| `rustworkx` | Python | `0.17.1` | HEALTHY | Passing graph capability probe exists. |
| `networkx` | Python | `3.6.1` | HEALTHY | Passing tool capability probe exists. |
| `scipy` | Python | `1.17.1` | HEALTHY | Passing isolated capability probe exists. |
| `numpy` | Python | `2.3.4` | HEALTHY | Passing capability probe exists; support package, not a rich engine by itself. |
| `opt_einsum` | Python | `3.4.0` | HEALTHY | Installed support package; no tensor-network capability probe. |
| `torch` | PyTorch/Python | `2.11.0` | HEALTHY | Passing PyTorch capability probes exist. |
| `torch-geometric` | PyTorch/Python | `2.7.0` | HEALTHY | Passing PyG isolated/deep graph probes exist. |
| `torch_ga` | PyTorch/Python | `0.0.6` | FRAGILE | User-provided external scan flags hobby-tier/design-frozen; no passing capability result found. |
| `clifford` | Python | `1.5.1` | FRAGILE | User-provided external scan flags design-frozen/fragile; passing v4 probe exists, but do not rely on it as future-proof. |
| `geomstats` | Python | `2.8.0` | HEALTHY | Passing manifold capability probe exists. |
| `e3nn` | PyTorch/Python | `0.6.0` | HEALTHY | Passing SO(3) equivariance capability probe exists. |

## 3. Dead Weight

Candidates to prune or demote from skills because they are installed/named/probed but serve no current matrix cell in current three-engine sims found in this inventory:

- Optimization/search/metaheuristic packages from v4 probe stubs with no result and no current matrix cell: `cma`, `deap`, `evotorch`, `optuna`, `pymoo`, `ribs`.
- Data/mining/test helper packages from v4 probe stubs with no current matrix cell: `datasketch`, `hdbscan`, `hypothesis`, `pynndescent`, `sklearn`, `umap`, `igraph`.
- Quantum frameworks outside the three-engine Julia/JAX/PyTorch target: `qiskit`, `pennylane`, `cirq`. `qiskit` has passing old v4 receipts, but it is not part of the owner’s current three-engine engine split.
- JAX optional modeling packages named in `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md` with no current matrix cell/probe evidence in this pass: `blackjax`, `jaxopt`, `lineax`, `optimistix`, `optax`, `flax`, `orbax`, `chex`, `jaxtyping`, `haiku`, `numpyro`, `flowMC`, `jax_dataclasses`, `jaxlie`.
- Julia packages named as missing/unchecked in coverage should stay out of active skills until there is a concrete cell and probe: `PythonCall`, `DLPack`, `CUDA`, `Reactant`, `Enzyme`, `Flux`, `Lux`, `GraphNeuralNetworks`, `GraphNeuralNets`, `Basins`, `CVC5`.

This is not a deletion instruction. It is a skill-surface prune list: either attach each package to a matrix cell with a probe, or move it out of default skill promises.

## 4. Top 5 Missing Probes To Build Next

1. Julia strict-carrier algebra capability probe: `Quaternions` + `Octonions` + `CliffordAlgebras` + Julia `Z3`, deriving structure constants and associator controls in one small v4-style result. Buys redundancy for rows 1, 2, 3, 4, and 11.
2. JAX-native algebra/spinor capability probe: `jax`/`jax.numpy` x64 Cayley-Dickson, Clifford gamma anticommutation, Hopf/Weyl readout, with `z3`/`cvc5` controls. Buys rows 1, 2, 3, 4, and 11 on the JAX side.
3. PyTorch `torch_ga` capability probe: import/version, basis blades, products, rotor sandwich, differentiability through GA operation, and negative/boundary controls. Buys rows 3 and 4, and removes the biggest PyTorch fragility.
4. Tensor-network capability pair: Julia `ITensors`/`ITensorMPS` and Python `quimb`/`cotengra` on the same tiny MPS/contraction fixture with explicit contraction-order controls. Buys row 8 for two engines.
5. Dynamics/QIT capability pair: Julia `DifferentialEquations`/`Attractors`/`QuantumOptics` and JAX `diffrax`/`dynamiqs`/`qutip-jax` on the same tiny ODE/master-equation/basin fixture. Buys rows 5 and 6 and clarifies whether JAX has real redundancy beyond `qutip`.

## Checks Performed

- Enumerated v4 capability probe sources matching `sim_<tool>_capability.py`, `sim_capability_<tool>_isolated.py`, and `tool_capability_<tool>.py`.
- Parsed v4 result JSON pass fields under `system_v4/probes/a2_state/sim_results/`.
- Read current coverage/evidence docs: `system_v5/evidence/sim_tool_library_coverage_20260608.json`, `system_v5/evidence/tool_function_receipt_matrix.json`, `system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md`, and `system_v5/codex_skills/three-engine-sim/references/tested_package_patterns.md`.
- Checked Python package versions with `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pip show ...`.
- Checked Julia strict-carrier packages from `system_v5/julia_carrier/Project.toml` and `system_v5/julia_carrier/Manifest.toml`.


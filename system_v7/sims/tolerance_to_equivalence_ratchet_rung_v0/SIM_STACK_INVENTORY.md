# V8 Sim Engine, Library, Tool, Repo, and Code State

Generated in an isolated worktree based on commit `fe6487de5136d18e7471952a2aa70595cc0f5cf7`. The new packet is bound by per-source hashes and is not yet commit-bound. This is an inventory and scratch-tooth report, not launch authority.

## Outcome

- Finite roster: **139** rows across **10** buckets.
- Historical estate: **95** operational passes and **29** integration edges, but bound to `576229471147` / tree `c249f58d144f` and stale to V8.
- Fresh first tooth: **COMMIT_ONE_BOUNDED_SCRATCH_TOOTH**, with all G0-G10 code gates green.
- Official launch: **BLOCKED**. `proof_backed_execution=false`, the Lev evaluator advisory red is preserved, and no ProofBundle was written.

## Bucket Counts

| Bucket | Count |
|---|---:|
| `admitted_quarantined_surface` | 1 |
| `blocked_or_avoid` | 9 |
| `candidate_available_unisolated` | 7 |
| `candidate_missing` | 25 |
| `current_core` | 71 |
| `current_isolated` | 3 |
| `current_optional_available` | 8 |
| `current_support` | 3 |
| `legacy_unclassified` | 9 |
| `quarantined` | 3 |

## Complete 139-Row Roster

### `admitted_quarantined_surface` (1)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `py_pykoopman` | `pykoopman` | `system_identification` | `python_canonical` | `quarantined` | historical receipt; stale to V8 tree | none |

### `blocked_or_avoid` (9)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `py_bayeux` | `bayeux` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |
| `py_oryx` | `oryx` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |
| `py_jax_verify` | `jax-verify` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |
| `py_dgl` | `dgl` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |
| `py_torch_scatter` | `torch-scatter` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |
| `py_torch_sparse` | `torch-sparse` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |
| `py_pyg_lib` | `pyg-lib` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |
| `py_torch_cluster` | `torch-cluster` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |
| `py_torch_spline_conv` | `torch-spline-conv` | `blocked_compatibility` | `python_canonical` | `installed_only` | blocked_or_avoid | none |

### `candidate_available_unisolated` (7)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `candidate_jl_combinatorialspaces` | `CombinatorialSpaces` | `candidate_extension` | `julia_default_project` | `installed_only` | historical receipt; stale to V8 tree | none |
| `candidate_jl_enzyme` | `Enzyme` | `candidate_extension` | `julia_default_project` | `installed_only` | historical receipt; stale to V8 tree | none |
| `candidate_jl_flux` | `Flux` | `candidate_extension` | `julia_default_project` | `installed_only` | historical receipt; stale to V8 tree | none |
| `candidate_jl_itensornetworks` | `ITensorNetworks` | `candidate_extension` | `julia_default_project` | `installed_only` | historical receipt; stale to V8 tree | none |
| `candidate_jl_lux` | `Lux` | `candidate_extension` | `julia_default_project` | `installed_only` | historical receipt; stale to V8 tree | none |
| `candidate_jl_tensoroperations` | `TensorOperations` | `candidate_extension` | `julia_default_project` | `installed_only` | historical receipt; stale to V8 tree | none |
| `candidate_jl_zygote` | `Zygote` | `candidate_extension` | `julia_default_project` | `installed_only` | historical receipt; stale to V8 tree | none |

### `candidate_missing` (25)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `candidate_py_hypernetx` | `hypernetx` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_hypergraphx` | `hypergraphx` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_ripser` | `ripser` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_persim` | `persim` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_pyflagser` | `pyflagser` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_pygsp` | `pygsp` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_egglog` | `egglog` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_matchpy` | `matchpy` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_distrax` | `distrax` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_pycauset` | `pycauset` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_dowhy` | `dowhy` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_causal_learn` | `causal_learn` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_pgmpy` | `pgmpy` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_pomegranate` | `pomegranate` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_graph_tool` | `graph_tool` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_py_causalai` | `causalai` | `candidate_extension` | `python_canonical` | `installed_only` | candidate_missing | none |
| `candidate_jl_graphneuralnetworks` | `GraphNeuralNetworks` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |
| `candidate_jl_geometricflux` | `GeometricFlux` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |
| `candidate_jl_cvc5` | `CVC5` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |
| `candidate_jl_catlab` | `Catlab` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |
| `candidate_jl_algebraicrewriting` | `AlgebraicRewriting` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |
| `candidate_jl_jump` | `JuMP` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |
| `candidate_jl_sumofsquares` | `SumOfSquares` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |
| `candidate_jl_reachabilityanalysis` | `ReachabilityAnalysis` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |
| `candidate_jl_taylormodels` | `TaylorModels` | `candidate_extension` | `julia_isolated_required` | `installed_only` | candidate_missing | none |

### `current_core` (71)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `py_jax` | `jax` | `jax_core` | `python_canonical` | `function_level_receipt` | fresh_bounded_claim_load_bearing | batched census and fixed-point closure |
| `py_jaxlib` | `jaxlib` | `jax_core` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_equinox` | `equinox` | `jax_ml` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_diffrax` | `diffrax` | `jax_dynamics` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_lineax` | `lineax` | `jax_dynamics` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_optimistix` | `optimistix` | `jax_dynamics` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_blackjax` | `blackjax` | `jax_probabilistic` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_jaxopt` | `jaxopt` | `jax_dynamics` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_optax` | `optax` | `jax_ml` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_flax` | `flax` | `jax_ml` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_orbax` | `orbax` | `jax_ml` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_chex` | `chex` | `jax_ml` | `python_canonical` | `supportive` | historical receipt; stale to V8 tree | none |
| `py_jaxtyping` | `jaxtyping` | `jax_ml` | `python_canonical` | `supportive` | historical receipt; stale to V8 tree | none |
| `py_dynamiqs` | `dynamiqs` | `qit_tensor` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_netket` | `netket` | `qit_tensor` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_quimb` | `quimb` | `qit_tensor` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_cotengra` | `cotengra` | `qit_tensor` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_e3nn_jax` | `e3nn_jax` | `geometry_graph` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_jraph` | `jraph` | `geometry_graph` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_haiku` | `dm-haiku` | `jax_ml` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_numpyro` | `numpyro` | `jax_probabilistic` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_ott` | `ott-jax` | `optimization_transport` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_qutip` | `qutip` | `qit_tensor` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_qutip_jax` | `qutip-jax` | `qit_tensor` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_z3` | `z3-solver` | `proof_symbolic` | `python_canonical` | `proof_discharge` | fresh_bounded_proof_discharge | free-variable equivalence SAT/UNSAT encoding |
| `py_cvc5` | `cvc5` | `proof_symbolic` | `python_canonical` | `proof_discharge` | fresh_bounded_proof_discharge | independent free-variable equivalence SAT/UNSAT encoding |
| `py_sympy` | `sympy` | `proof_symbolic` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_torch` | `torch` | `pytorch_core` | `python_canonical` | `function_level_receipt` | fresh_bounded_claim_load_bearing | tensor census and graph closure support |
| `py_torch_geometric` | `torch-geometric` | `geometry_graph` | `python_canonical` | `function_level_receipt` | fresh_bounded_claim_load_bearing | MessagePassing reachability closure |
| `py_torchdiffeq` | `torchdiffeq` | `pytorch_core` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_torchode` | `torchode` | `pytorch_core` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_xitorch` | `xitorch` | `pytorch_core` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_cvxpylayers` | `cvxpylayers` | `optimization_transport` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_geomstats` | `geomstats` | `geometry_graph` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_e3nn` | `e3nn` | `geometry_graph` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_torch_ga` | `torch-ga` | `algebra_geometry` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_clifford` | `clifford` | `algebra_geometry` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_pysindy` | `pysindy` | `system_identification` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_networkx` | `networkx` | `graph_topology` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_igraph` | `igraph` | `graph_topology` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_rustworkx` | `rustworkx` | `graph_topology` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_xgi` | `xgi` | `graph_topology` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_toponetx` | `toponetx` | `graph_topology` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_gudhi` | `gudhi` | `graph_topology` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_kanren` | `kanren` | `graph_topology` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_kahypar` | `kahypar` | `graph_topology` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_opt_einsum` | `opt_einsum` | `qit_tensor` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_numpy` | `numpy` | `control_support` | `python_canonical` | `control_only` | historical receipt; stale to V8 tree | none |
| `py_scipy` | `scipy` | `control_support` | `python_canonical` | `control_only` | historical receipt; stale to V8 tree | none |
| `py_pandas` | `pandas` | `control_support` | `python_canonical` | `supportive` | historical receipt; stale to V8 tree | none |
| `jl_attractors` | `Attractors` | `julia_dynamics` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_chaostools` | `ChaosTools` | `julia_dynamics` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_cliffordalgebras` | `CliffordAlgebras` | `julia_algebra` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_differentialequations` | `DifferentialEquations` | `julia_dynamics` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_dynamicalsystems` | `DynamicalSystems` | `julia_dynamics` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_graphs` | `Graphs` | `julia_qit` | `julia_strict_carrier` | `function_level_receipt` | fresh_bounded_claim_load_bearing | connected-component equivalence closure |
| `jl_grassmann` | `Grassmann` | `julia_algebra` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_itensormps` | `ITensorMPS` | `julia_tensor` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_itensors` | `ITensors` | `julia_tensor` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_json` | `JSON` | `provenance_support` | `julia_strict_carrier` | `supportive` | historical receipt; stale to V8 tree | none |
| `jl_json3` | `JSON3` | `provenance_support` | `julia_strict_carrier` | `supportive` | fresh_support | structured engine receipt serialization |
| `jl_manifolds` | `Manifolds` | `julia_dynamics` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_octonions` | `Octonions` | `julia_algebra` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_quantumclifford` | `QuantumClifford` | `julia_qit` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_quantumoptics` | `QuantumOptics` | `julia_qit` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_quantumtoolbox` | `QuantumToolbox` | `julia_qit` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_quaternions` | `Quaternions` | `julia_algebra` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_staticarrays` | `StaticArrays` | `julia_dynamics` | `julia_strict_carrier` | `supportive` | historical receipt; stale to V8 tree | none |
| `jl_symbolics` | `Symbolics` | `julia_algebra` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_yao` | `Yao` | `julia_qit` | `julia_strict_carrier` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_z3` | `Z3` | `julia_algebra` | `julia_strict_carrier` | `proof_discharge` | historical receipt; stale to V8 tree | none |

### `current_isolated` (3)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `jl_tensorkit` | `TensorKit` | `julia_tensor` | `julia_tensorkit` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_pepskit` | `PEPSKit` | `julia_tensor` | `julia_peps` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `jl_intervalarithmetic` | `IntervalArithmetic` | `certified_bounds` | `julia_attractors` | `function_level_receipt` | historical receipt; stale to V8 tree | none |

### `current_optional_available` (8)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `py_dynamax` | `dynamax` | `jax_dynamics` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_flowmc` | `flowMC` | `optimization_transport` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_jax_dataclasses` | `jax-dataclasses` | `jax_ml` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_jaxlie` | `jaxlie` | `geometry_graph` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_jaxga` | `jaxga` | `algebra_geometry` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_autoray` | `autoray` | `qit_tensor` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_pymc` | `pymc` | `jax_probabilistic` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_sklearn` | `scikit-learn` | `system_identification` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |

### `current_support` (3)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `jl_dates` | `Dates` | `provenance_support` | `julia_strict_carrier` | `supportive` | fresh_support | receipt timestamp |
| `jl_sha` | `SHA` | `provenance_support` | `julia_strict_carrier` | `supportive` | fresh_support | source hash binding |
| `jl_linearalgebra` | `LinearAlgebra` | `julia_tensor` | `julia_strict_carrier` | `control_only` | historical receipt; stale to V8 tree | none |

### `legacy_unclassified` (9)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `py_ribs` | `ribs` | `optimization_search` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_deap` | `deap` | `optimization_search` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_evotorch` | `evotorch` | `optimization_search` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_datasketch` | `datasketch` | `data_index` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_pymoo` | `pymoo` | `optimization_search` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_hypothesis` | `hypothesis` | `property_testing` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_optuna` | `optuna` | `optimization_search` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_hdbscan` | `hdbscan` | `clustering` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |
| `py_umap` | `umap-learn` | `clustering` | `python_canonical` | `function_level_receipt` | historical receipt; stale to V8 tree | none |

### `quarantined` (3)

| ID | Package | Family | Runtime | Expected role | Current honest state | First-tooth role |
|---|---|---|---|---|---|---|
| `jl_pythoncall` | `PythonCall` | `julia_bridge` | `julia_strict_carrier` | `quarantined` | quarantined | none |
| `jl_dlpack` | `DLPack` | `julia_bridge` | `julia_strict_carrier` | `quarantined` | quarantined | none |
| `jl_condapkg` | `CondaPkg` | `julia_bridge` | `julia_strict_carrier` | `quarantined` | quarantined | none |

## The 29 Registered Connections

- Compatibility/co-health witnesses (25): all non-cross IDs plus legacy reconciliation.
- Independent recomputations (3): `cross_tensor`, `cross_dynamics`, `cross_proof`.
- Direct value handoff (1): `cross_jax_torch` through DLPack.

Exact IDs: `py_jax_backend`, `py_jax_module_train`, `py_flax_orbax`, `py_probabilistic`, `py_jax_dynamics`, `py_jax_quantum`, `py_tensor_network`, `py_equivariant_graph`, `py_transport`, `py_haiku_flax`, `py_torch_core`, `py_torch_graph_geometry`, `py_torch_convex`, `py_geometric_algebra`, `py_proof_symbolic`, `py_system_id`, `py_graph_algorithms`, `py_higher_order_topology`, `jl_algebra`, `jl_tensor`, `jl_dynamics`, `jl_qit`, `jl_receipt`, `jl_isolated_tensor`, `py_legacy_reconciliation`, `cross_tensor`, `cross_dynamics`, `cross_proof`, `cross_jax_torch`.

## Connected Repositories

| Path | Role | Live state | Connection / boundary |
|---|---|---|---|
| `/Users/joshuaeisenhart/Codex-Ratchet` | active dirty owner checkout | `session/r0-three-engine-probes` `4f3fb20ac839`; dirty 48 tracked + 87 untracked | source repo and parallel R0 work; not the V8 execution tree (live_repo_dirty) |
| `/Users/joshuaeisenhart/.config/superpowers/worktrees/Codex-Ratchet/v8-first-rungs-20260715` | V8 isolated worktree | `codex/v8-first-rungs-20260715` `fe6487de5136`; dirty 0 tracked + 1 untracked | current inventory and first-tooth execution (v8_execution_tree) |
| `/Users/joshuaeisenhart/lev-main` | active Lev development checkout | `fable/cr-sim-eval-pack` `5f844cb9580e`; dirty 1 tracked + 1 untracked | current process archaeology only; dirty and not the pinned gate runner (live_repo_dirty) |
| `/Users/joshuaeisenhart/lev-main/.worktrees/eval-projection-contract` | pinned Lev gate executor | `codex/eval-projection-contract` `856acb1a5de4`; clean | deterministic no-model FlowMind G10 replay (pinned_clean_runtime) |
| `/Users/joshuaeisenhart/wiki` | research and Wizard context | `main` `db038242238a`; dirty 6 tracked + 0 untracked | context/provenance only; not executable canon (research_context) |
| `/Users/joshuaeisenhart/GitHub/auto_LiRPA` | neural bound oracle | `master` `ca767f1d8c0a`; clean | bounded CROWN/IBP gap-J fixture (external_bounded_oracle) |
| `/Users/joshuaeisenhart/GitHub/qics` | convex/QIT numerical oracle | `DETACHED` `be18e5ef0725`; clean | isolated QuantRelEntr/Model/Solver receipt (external_supportive_oracle) |
| `/Users/joshuaeisenhart/GitHub/physlib` | Lean proof repo | `master` `a19625088528`; clean | finite-dimensional associative DPI proof build (external_bounded_proof) |
| `/Users/joshuaeisenhart/GitHub/pysindy` | system-identification upstream | `DETACHED` `1edf31260fc0`; clean | SINDy/PolynomialLibrary/STLSQ function receipt (external_runtime_support) |
| `/Users/joshuaeisenhart/GitHub/pykoopman` | Koopman upstream | `DETACHED` `61d24f765cd4`; clean | narrow Identity plus EDMD surface only (external_quarantined_support) |
| `/Users/joshuaeisenhart/GitHub/deeptime` | VAMP runtime | `DETACHED` `79837fdc7f91`; clean | bounded stage-interior discriminator receipt (external_bounded_oracle) |
| `/Users/joshuaeisenhart/GitHub/alco` | GAP/ALCO exact oracle | `DETACHED` `e10ec05acbdf`; dirty 0 tracked + 1 untracked | five frozen J3(O) cases (external_bounded_oracle) |
| `/Users/joshuaeisenhart/GitHub/le-wm` | world-model source | `main` `bf04d3e8c375`; dirty 0 tracked + 2 untracked | source import and inlining; current result artifacts absent (source_only) |
| `/Users/joshuaeisenhart/GitHub/lpwm` | world-model source | `main` `4cf53c403433`; dirty 0 tracked + 1 untracked | source-only/deferred (source_only) |
| `/Users/joshuaeisenhart/GitHub/flowm` | world-model source | `main` `b6fa31beba9b`; dirty 0 tracked + 1 untracked | source-only/deferred (source_only) |
| `/Users/joshuaeisenhart/GitHub/AnyFlow` | flow-model source | `main` `549236a9d9b1`; clean | source-only/deferred (source_only) |
| `/Users/joshuaeisenhart/GitHub/Sana` | diffusion source | `main` `6554c8d90d46`; clean | API/model-load smoke targets installed package, not checkout (checkout_not_consumed) |
| `/Users/joshuaeisenhart/GitHub/stylegan3` | generative-model source | `main` `c233a919a6fa`; dirty 0 tracked + 4 untracked | deferred/rejected for current lane (deferred) |
| `/Users/joshuaeisenhart/GitHub/LevRatchet` | flat reference folder | non-Git | non-Git quarantine/reference only (quarantined_reference) |

## Code Surfaces

| Surface | State | Evidence | Boundary |
|---|---|---|---|
| V8 tolerance-to-equivalence Julia | fresh bounded claim-load-bearing | `run_julia.jl plus results/julia_results.json` | Graphs connected-component closure and n=1..5 census; scratch only |
| V8 tolerance-to-equivalence JAX | fresh bounded claim-load-bearing | `run_jax.py plus results/jax_results.json` | x64 vmap census and lax fixed-point closure; scratch only |
| V8 tolerance-to-equivalence PyTorch/PyG | fresh bounded claim-load-bearing | `run_pytorch.py plus results/pytorch_results.json` | MessagePassing reachability and torch census; scratch only |
| V8 z3/cvc5 proof pair | fresh bounded proof discharge | `run_proofs.py plus results/proof_results.json` | free Boolean relation variables for four frozen SAT/UNSAT queries only |
| V8 Lev deterministic gate | fresh orchestration receipt | `results/lev_replay_receipt.json` | four blocking GateProofs pass; ProofBundle absent, evaluator advisory red retained |
| deep-stack 139-tool estate | historical function-level estate stale to V8 tree | `system_v5/ops/tooling/deep_stack_stress_20260714/results/deep_stack_estate_lev.json` | 95 operational, 44 policy, 29 edges historically green; projection-only and source-bound to an older commit/tree |
| Julia R0 distinguishability | stored unbound function receipt | `system_v5/julia_carrier/foundation_r0_distinguishability_julia.jl` | green scratch result lacks source hash |
| JAX R0 SMT scout | imported in source | `system_v5/ops/formal_scouts/foundation_r0_distinguishability_jax_smt.py` | result absent in inspected V8 tree |
| PyTorch R0 gradient scout | imported in source | `system_v5/ops/formal_scouts/foundation_r0_distinguishability_pytorch_grad.py` | result absent in inspected V8 tree |
| Julia R2 admissibility | matching bounded function receipt | `system_v5/julia_carrier/foundation_foundation_r2_admissibility_mc_julia_leg.jl` | source/result match and all_pass, but scratch and non-promotable |
| PySINDy | historical function receipt | `native SINDy, PolynomialLibrary, and STLSQ probe` | not generally claim-bearing |
| PyKoopman | narrow historical function receipt | `Identity plus EDMD` | full distribution quarantined |
| coherent-information gradient z3 | decorative and must be demoted | `solver asserts free g>0 or g==0 rather than binding computed gradient` | API smoke, not proof discharge |
| ratchet_climb_engine_v1_drive | not launch evidence | `existing climb source` | climb steps/target rungs are hardcoded rather than forced |
| ratchet_formal_gates_v1 | informative red | `existing formal gate results` | Xi representative-independence failure must remain red |

## Tools Outside the Frozen 139

| Tool | State | Evidence | Blocker |
|---|---|---|---|
| Lean4/mathlib | bounded proof discharge | external physlib lake build; 8617 jobs and no sorry/admit for finite-dimensional associative DPI only | not connected to the 139-row Lev estate by a repo-local producer |
| Maude Python | later bounded tool surface | outside the frozen 139-row registry | requires explicit V8 roster admission |
| auto_LiRPA | bounded claim-load-bearing | fixed 2-4-1 ReLU CROWN/IBP region oracle | not a general Ratchet proof |
| QICS | function receipt/supportive | native QuantRelEntr, Model, and Solver | currently duplicates a spectral oracle and lacks a unique bypass-demotion gate |
| ALCO/GAP | bounded claim-load-bearing | five frozen J3(O) exact cases | no general algebraic claim |
| physlib | bounded proof discharge | Lean finite-dimensional associative DPI theorem | external proof is not a Ratchet launch receipt |
| deeptime | bounded claim-load-bearing | VAMP stage-interior discriminator | local fixture only |
| PyDMD | bounded claim-load-bearing | BOPDMD/HankelDMD stage-interior discriminator | local fixture only |
| kingdon | later algebra surface | outside the frozen 139-row registry | requires explicit V8 roster admission |

## Launch Boundary

The code has earned exactly one bounded scratch tooth. It has not earned official launch, canonical status, a QIT derivation, terrain/operator promotion, or any cross-domain scientific claim. The next infrastructure blocker is a real runtime caller for `assembleProofBundle()` plus independent bundle validation; the next scientific rung is a broader tolerance/context tournament, not a prose promotion of this fixture.

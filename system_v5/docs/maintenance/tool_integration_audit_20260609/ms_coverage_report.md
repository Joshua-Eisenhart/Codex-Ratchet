# Tool-Stack Coverage Audit

Scope: read-only scan of `system_v5/ops/formal_scouts` sim sources/results. I also scanned `system_v5/julia_carrier` for Julia carrier sims/results because the requested Julia installed set is declared and exercised there.

Criterion: install/import is not enough. `USED - function/claim receipt` means a result ties the tool to claim/depth evidence and has an explicit `tool_calls` receipt. `USED - schema-thin` means source plus result evidence shows a bounded load-bearing sim, but the result lacks an explicit `tool_calls` key. `UNDER-EXERCISED` means only import/manifest evidence was found.

## Observed

- Runtime doctor: `ok=True install_state=stable_observed` for `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py`.
- Source files scanned: 905.
- Result JSONs scanned: 394.
- Result JSONs with tool fields: 336. Result JSONs with `tool_calls`: 13. JSON parse errors: 0.
- Classification counts: USED - function/claim receipt: 34, UNUSED-but-installed: 6, UNDER-EXERCISED - import/manifest only: 1, USED - schema-thin receipt (no tool_calls key): 6

## USED Tools

| Tool | Stack | Status | Sources | Claim/load-bearing receipts | Tool-call receipts | Evidence examples |
|---|---|---|---:|---:|---:|---|
| `QuantumOptics` | Julia | USED - function/claim receipt | 28 | 33 | 4 | system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json |
| `Yao` | Julia | USED - function/claim receipt | 1 | 1 | 1 | system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `CliffordAlgebras` | Julia | USED - function/claim receipt | 42 | 34 | 3 | system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json |
| `Grassmann` | Julia | USED - function/claim receipt | 5 | 4 | 1 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json |
| `QuantumClifford` | Julia | USED - function/claim receipt | 1 | 1 | 1 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json |
| `Octonions` | Julia | USED - function/claim receipt | 3 | 3 | 2 | system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `Quaternions` | Julia | USED - function/claim receipt | 3 | 3 | 2 | system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `Manifolds` | Julia | USED - function/claim receipt | 2 | 2 | 2 | system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `Attractors` | Julia | USED - function/claim receipt | 2 | 2 | 1 | system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json |
| `DynamicalSystems` | Julia | USED - function/claim receipt | 2 | 2 | 1 | system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `DifferentialEquations` | Julia | USED - function/claim receipt | 4 | 3 | 2 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `ITensors` | Julia | USED - function/claim receipt | 11 | 3 | 1 | system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `ITensorMPS` | Julia | USED - function/claim receipt | 8 | 1 | 1 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json |
| `Graphs` | Julia | USED - function/claim receipt | 6 | 3 | 2 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `Symbolics` | Julia | USED - function/claim receipt | 4 | 4 | 1 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json |
| `Z3` | Julia | USED - function/claim receipt | 33 | 37 | 4 | system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json |
| `jax` | Python JAX/QIT/TN | USED - function/claim receipt | 162 | 197 | 5 | system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_jax_leg_results.json; system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json |
| `diffrax` | Python JAX/QIT/TN | USED - function/claim receipt | 3 | 6 | 6 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json |
| `dynamiqs` | Python JAX/QIT/TN | USED - function/claim receipt | 3 | 6 | 6 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json |
| `quimb` | Python JAX/QIT/TN | USED - function/claim receipt | 31 | 4 | 2 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json |
| `cotengra` | Python JAX/QIT/TN | USED - function/claim receipt | 24 | 4 | 4 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `qutip` | Python JAX/QIT/TN | USED - schema-thin receipt (no tool_calls key) | 6 | 10 | 0 | system_v5/ops/formal_scouts/results/three_engine_qit_cptp_dephasing_pinned_rho_envelope_results.json; system_v5/ops/formal_scouts/results/three_engine_qit_density_entropy_pinned_rho_envelope_results.json |
| `e3nn_jax` | Python JAX/QIT/TN | USED - function/claim receipt | 1 | 2 | 2 | system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_jax_results.json |
| `ott` | Python JAX/QIT/TN | USED - function/claim receipt | 1 | 2 | 2 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json |
| `torch` | Python PyTorch/Geometry | USED - function/claim receipt | 389 | 104 | 9 | system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_pytorch_leg_results.json; system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json |
| `torch_geometric` | Python PyTorch/Geometry | USED - function/claim receipt | 72 | 6 | 4 | system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_pytorch_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json |
| `torchdiffeq` | Python PyTorch/Geometry | USED - function/claim receipt | 1 | 2 | 2 | system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json |
| `xitorch` | Python PyTorch/Geometry | USED - function/claim receipt | 1 | 2 | 2 | system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json |
| `geomstats` | Python PyTorch/Geometry | USED - function/claim receipt | 33 | 7 | 7 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_pytorch_results.json |
| `clifford` | Python PyTorch/Geometry | USED - schema-thin receipt (no tool_calls key) | 46 | 2 | 0 | system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json |
| `torch_ga` | Python PyTorch/Geometry | USED - function/claim receipt | 5 | 9 | 6 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_pytorch_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json |
| `e3nn` | Python PyTorch/Geometry | USED - function/claim receipt | 23 | 4 | 2 | system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json |
| `z3` | Python SMT/Symbolic | USED - function/claim receipt | 371 | 97 | 12 | system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_jax_leg_results.json; system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_pytorch_leg_results.json |
| `cvc5` | Python SMT/Symbolic | USED - function/claim receipt | 124 | 95 | 12 | system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_jax_leg_results.json; system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_pytorch_leg_results.json |
| `sympy` | Python SMT/Symbolic | USED - function/claim receipt | 146 | 12 | 4 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json; system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json |
| `gudhi` | Python Graph/Topology | USED - schema-thin receipt (no tool_calls key) | 94 | 2 | 0 | system_v5/ops/formal_scouts/results/constraint_survivor_probe_quotient_order_dependence_probe_results.json; system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json |
| `toponetx` | Python Graph/Topology | USED - schema-thin receipt (no tool_calls key) | 38 | 1 | 0 | system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json |
| `xgi` | Python Graph/Topology | USED - schema-thin receipt (no tool_calls key) | 38 | 1 | 0 | system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json |
| `rustworkx` | Python Graph/Topology | USED - schema-thin receipt (no tool_calls key) | 134 | 4 | 0 | system_v5/ops/formal_scouts/results/constraint_survivor_probe_quotient_order_dependence_probe_results.json; system_v5/ops/formal_scouts/results/two_root_constraint_group_action_dynamics_connectivity_probe_results.json; system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json |
| `networkx` | Python Graph/Topology | USED - function/claim receipt | 97 | 4 | 2 | system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json; system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json |

## UNUSED / Under-Exercised Installed Tools

| Tool | Stack | Status | Sources | Claim/load-bearing receipts | Tool-call receipts | Evidence examples |
|---|---|---|---:|---:|---:|---|
| `QuantumToolbox` | Julia | UNUSED-but-installed | 0 | 0 | 0 | - |
| `ChaosTools` | Julia | UNUSED-but-installed | 0 | 0 | 0 | - |
| `StaticArrays` | Julia | UNDER-EXERCISED - import/manifest only | 2 | 0 | 0 | system_v5/julia_carrier/branch_prune_spinor_field_object.jl; system_v5/julia_carrier/foundation_spinor_network_full_stack_layer_julia.jl |
| `netket` | Python JAX/QIT/TN | UNUSED-but-installed | 0 | 0 | 0 | - |
| `blackjax` | Python JAX/QIT/TN | UNUSED-but-installed | 0 | 0 | 0 | - |
| `optimistix` | Python JAX/QIT/TN | UNUSED-but-installed | 0 | 0 | 0 | - |
| `torchode` | Python PyTorch/Geometry | UNUSED-but-installed | 0 | 0 | 0 | - |

## Coverage Gaps

- UNUSED-but-installed in requested set: `QuantumToolbox`, `ChaosTools`, `netket`, `blackjax`, `optimistix`, `torchode`
- Under-exercised/import-only: `StaticArrays`
- Used but schema-thin, missing explicit `tool_calls`: `qutip`, `clifford`, `gudhi`, `toponetx`, `xgi`, `rustworkx`
- Julia `QuantumToolbox`, `ChaosTools`, and `StaticArrays` are installed/imported but did not show a bounded load-bearing formal-scout receipt in this scan.
- Python `netket`, `blackjax`, `optimistix`, and `torchode` appear only in omitted/installed-target lists in this scan, not as exercised imports or result receipts; they need one-function micro-probes before claim use.
- `qutip`, `gudhi`, `toponetx`, `xgi`, and `rustworkx` have real load-bearing source/result evidence, but their strongest receipts are schema-thin. Add explicit per-tool `tool_calls` objects to remove ambiguity.

## Over-Tooling / Forced Tool Risk

- Blanket or loop-generated load-bearing depth appears in these representative sources:
  - `system_v5/ops/formal_scouts/sim_boundary_conditional_expectation_area_law_entropy_scaling_probe.py`
  - `system_v5/ops/formal_scouts/sim_boundary_projected_gamma5_chirality_channel_choi_rank_probe.py`
  - `system_v5/ops/formal_scouts/sim_boundary_projected_gamma5_chirality_channel_coherent_information_probe.py`
  - `system_v5/ops/formal_scouts/sim_boundary_projected_gamma5_chirality_channel_trace_distance_probe.py`
  - `system_v5/ops/formal_scouts/sim_chirality_asymmetric_channel_coherent_information_novelty_killer_probe.py`
  - `system_v5/ops/formal_scouts/sim_constraint_manifold_delta_neural_readout_probe.py`
  - `system_v5/ops/formal_scouts/sim_constraint_manifold_discrete_degrees_of_freedom_enumeration_probe.py`
  - `system_v5/ops/formal_scouts/sim_constraint_manifold_layer_causal_responsibility_matrix_probe.py`
  - `system_v5/ops/formal_scouts/sim_constraint_manifold_multitool_entropy_geometry_carrier_integration_probe.py`
  - `system_v5/ops/formal_scouts/sim_constraint_manifold_qit_work_execution_probe.py`
  - `system_v5/ops/formal_scouts/sim_constraint_survivor_probe_quotient_order_dependence_probe.py`
  - `system_v5/ops/formal_scouts/sim_density_metric_geometry_survivor_quotient_persistence_probe.py`
  - `system_v5/ops/formal_scouts/sim_density_spinor_hopf_shell_graph_coherent_information_coupling_probe.py`
  - `system_v5/ops/formal_scouts/sim_discrete_dof_topological_obstruction_interpolation_probe.py`
  - `system_v5/ops/formal_scouts/sim_dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe.py`
  - `system_v5/ops/formal_scouts/sim_dynamic_shell_rate_sequence_parameter_compression_probe.py`
  - `system_v5/ops/formal_scouts/sim_eight_qubit_boundary_projected_gamma5_channel_coherent_information_probe.py`
  - `system_v5/ops/formal_scouts/sim_eight_qubit_boundary_projected_gamma5_mutual_information_persistence_probe.py`
  - `system_v5/ops/formal_scouts/sim_eight_qubit_dynamic_shell_chirality_asymmetric_cptp_entropy_coupling_probe.py`
  - `system_v5/ops/formal_scouts/sim_eight_qubit_dynamic_shell_gamma5_chirality_survivor_quotient_probe.py`
- `foundation_qit_operator_composition_mcp_jax` is a legitimate rich-tool example, but it also shows the risk boundary: `numpy` is explicitly control-only host conversion, not claim-bearing.
- Broad torch/z3/rustworkx probe families often declare many tools load-bearing; promote only when the result has per-tool API surface, input/output, positive case, negative/erased control, boundary case, and demotion condition.
- Envelopes are useful for coverage only when the child leg receipt carries the tool evidence. Engine agreement without child function receipts is not enough.

## Smallest Next Coverage Moves

1. Add explicit `tool_calls` to the schema-thin graph/topology/QIT receipts, starting with `wave_a_cs_ai_no_install_micro_probes_results.json` and the qutip pinned-rho leg receipts.
2. Write one bounded capability sim each for `QuantumToolbox`, `ChaosTools`, `StaticArrays`, `netket`, `blackjax`, `optimistix`, and `torchode` if those tools are still intended to be claim-bearing.
3. Demote any blanket load-bearing manifest where the tool only supplies fixture assembly, host conversion, or optimizer search without a decisive bounded observable.

## Parse Notes

- Static scan only: I did not rerun all sims.
- Julia `Z3` and Python `z3` are both shown because the requested sets list both; some envelope evidence necessarily overlaps.
- No repo files were modified; this report was written only to `/tmp/found/ms_coverage_report.md`.

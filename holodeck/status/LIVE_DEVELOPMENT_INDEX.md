# Holodeck live development status

Generated: `2026-08-06T20:35:40.086493+00:00`

Installed tooling, legacy source discovery, and Holodeck integration are separate facts.

| Tool | Visible | Version | Declared level | Role |
|---|---|---:|---|---|
| `python.numpy` | True | `2.3.4` | imported_in_source | finite_state_and_reference_arrays |
| `python.scipy` | True | `1.17.1` | imported_in_source | reference_dynamics_and_matrix_functions |
| `python.torch` | True | `2.11.0` | function_level_receipt | trainable_predictive_and_memory_models |
| `python.torch-geometric` | True | `2.7.0` | function_level_receipt | graph_world_models_and_hopfield_support |
| `python.lightning` | True | `2.6.5` | installed_only | optional_training_orchestration |
| `python.gymnasium` | True | `1.2.3` | installed_only | controlled_environment_interface |
| `python.scikit-learn` | True | `1.8.0` | installed_only | classical_predictive_controls |
| `python.e3nn` | True | `0.6.0` | function_level_receipt | equivariant_geometric_models |

## Candidate sources

| Source | Exists | Status | Capability |
|---|---|---|---|
| `system_v4/probes/world_model_sim.py` | True | legacy_candidate_source | state_and_surface_learning_loops |
| `system_v4/probes/sim_qit_predictive_world_model.py` | True | legacy_candidate_source | qit_predictive_update |
| `system_v4/probes/sim_holodeck_entropy_compression_operator.py` | True | legacy_candidate_source | entropy_compression_probe |
| `system_v4/probes/sim_holodeck_observer_projection_operator.py` | True | legacy_candidate_source | observer_projection_probe |
| `system_v4/skills/sim_holodeck_engine.py` | True | legacy_candidate_source | legacy_runner_wrapper |
| `system_v5/ops/formal_scouts/sim_holodeck_core_prediction_memory_seed_probe.py` | True | legacy_candidate_source | prediction_memory_seed |
| `system_v5/ops/formal_scouts/sim_holodeck_basin_grade_probe.py` | True | legacy_candidate_source | basin_grade_model |
| `system_v5/ops/formal_scouts/sim_world_model_repo_admission_gap_adapter_probe.py` | True | legacy_candidate_source | repo_admission_gap_adapter |

QIT bridge: `blocked_pending_independent_qit_engine_reality_gate`

No candidate source is promoted to an integrated Holodeck engine by this snapshot.

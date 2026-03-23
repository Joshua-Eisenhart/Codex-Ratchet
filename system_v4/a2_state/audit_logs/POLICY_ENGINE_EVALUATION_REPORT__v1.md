# POLICY ENGINE EVALUATION REPORT - v1

## Executive Summary

| Graph | Rule 1 | Rule 2 | Rule 3 | Rule 4 | Rule 5 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| identity_registry_overlap_suggestions_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| system_graph_v3_full_system_ingest_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ❌ FAIL (228) | ✅ PASS |
| a2_mid_refinement_graph_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ❌ FAIL (1) |
| nested_graph_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| enriched_a2_low_control_graph_v1.json | ❌ FAIL (418) | ✅ PASS | ✅ PASS | ✅ PASS | ❌ FAIL (4) |
| a2_high_intake_graph_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ❌ FAIL (164) |
| system_graph_v3_ingest_pass1.json | ✅ PASS | ✅ PASS | ✅ PASS | ❌ FAIL (157) | ✅ PASS |
| a2_low_control_graph_v1.json | ❌ FAIL (418) | ✅ PASS | ✅ PASS | ✅ PASS | ❌ FAIL (4) |
| system_graph_a2_refinery.json | ❌ FAIL (811) | ✅ PASS | ✅ PASS | ❌ FAIL (123) | ❌ FAIL (259) |
| a1_jargoned_graph_v1.json | ❌ FAIL (385) | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| identity_registry_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| promoted_subgraph.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ❌ FAIL (1) |
| a1_cartridge_graph_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| a1_stripped_graph_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| skill_registry_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| A1_GRAPH_PROJECTION.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| a1_jargoned_graph_v1.json | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |

## Policy Details

1. **Kernel nodes** must have `admissibility_state = ADMITTED`.
2. **No edge** may reference a non-existent node.
3. **Promoted nodes** must appear in at least 2 layer graphs.
4. **Skill nodes** must have `operation_type` defined.
5. **Graveyard nodes** must not have `LIVE` status edges.

## Detailed Violations

### system_graph_v3_full_system_ingest_v1.json
- **rule4_skill_operation_type**: 228 violations found.
  - `V3_OPERATIONS::export_a2_controller_launch_gate_result_graph.py`
  - `V3_OPERATIONS::build_graveyard_failure_topology.py`
  - `V3_OPERATIONS::a2_controller_launch_handoff_models.py`
  - `V3_OPERATIONS::a1_brain_append_event.py`
  - `V3_OPERATIONS::run_long_run_write_guard_gate.py`
  - ... and 223 more.

### a2_mid_refinement_graph_v1.json
- **rule5_graveyard_live_edges**: 1 violations found.
  - `XLINK::NAME::A2_2::REFINED::graveyard_branch_work::f94edca8dd36d295--A2_3::SOURCE_MAP_PASS::graveyard_branch_work::f94edca8dd36d295`

### enriched_a2_low_control_graph_v1.json
- **rule1_kernel_admissibility**: 418 violations found.
  - `A2_2::REFINED::DETERMINISTIC_KERNEL_PIPELINE::030ebc838121b473`
  - `A2_2::REFINED::a0_budget_and_truncation::4745e5fd4d283ec6`
  - `A2_2::REFINED::a0_export_block_compilation::0689ed62233c4265`
  - `A2_2::REFINED::a1_anti_classical_leakage::702a223de5c2c206`
  - `A2_2::REFINED::a1_strategy_v1_schema::d471f02fe871cb95`
  - ... and 413 more.
- **rule5_graveyard_live_edges**: 4 violations found.
  - `XLINK::TERM::A2_3::SOURCE_MAP_PASS::zip_dropins_03_task__classical_residue_graveyar::acbfa66d9975d56d--A2_3::SOURCE_MAP_PASS::03_task__classical_residue_graveyard_registry_and_::480c6a62bad752c2`
  - `XLINK::NAME::A2_3::SOURCE_MAP_PASS::zip_dropins_03_task__classical_residue_graveyar::acbfa66d9975d56d--A2_3::SOURCE_MAP_PASS::zip_dropins_global_classical_residue_graveyard_::8fb24cfdb4241fcd`
  - `XLINK::NAME::A2_3::SOURCE_MAP_PASS::03_task__classical_residue_graveyard_registry_and_::480c6a62bad752c2--A2_3::SOURCE_MAP_PASS::zip_dropins_03_task__classical_residue_graveyar::acbfa66d9975d56d`
  - `XLINK::NAME::A2_3::SOURCE_MAP_PASS::03_task__classical_residue_graveyard_registry_and_::480c6a62bad752c2--A2_3::SOURCE_MAP_PASS::zip_dropins_global_classical_residue_graveyard_::8fb24cfdb4241fcd`

### a2_high_intake_graph_v1.json
- **rule5_graveyard_live_edges**: 164 violations found.
  - `EDGE::A2_3::SOURCE::A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__v1.md::b06e74875e31bc70--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::a1_state_a1_graveyard_first_validity_profile__v1::713912a7d63af423`
  - `EDGE::A2_3::SOURCE::A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__v1.md::b06e74875e31bc70--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::a1_state_a1_rescue_and_graveyard_operators__v1::1743a98bdba4c06b`
  - `EDGE::A2_3::SOURCE::DOC_INDEX_STATUS_CAUTION__v1.md::019f4a1ebb8672d9--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::a2_state_v3_entropy_graveyard_failure_topology__v1::9218e3b3d97655b3`
  - `EDGE::A2_3::SOURCE::PARALLEL_CODEX_WORKER_RESULT_SINK__v1.md::c4f0815b90e8b220--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::a2_state_v3_run_graveyard_validity_entropy_bridge_cl::f16ae6c80f75c76b`
  - `EDGE::A2_3::SOURCE::00_READ_FIRST.md::4126808f7af159bc--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::sysrepair_v2_graveyard_cluster_protocol_v1::b3c5d1c5e0b0b4bd`
  - ... and 159 more.

### system_graph_v3_ingest_pass1.json
- **rule4_skill_operation_type**: 157 violations found.
  - `V3_TOOL::build_graveyard_failure_topology.py`
  - `V3_TOOL::a1_brain_append_event.py`
  - `V3_TOOL::run_long_run_write_guard_gate.py`
  - `V3_TOOL::build_fuel_digest.py`
  - `V3_TOOL::create_a1_worker_launch_packet.py`
  - ... and 152 more.

### a2_low_control_graph_v1.json
- **rule1_kernel_admissibility**: 418 violations found.
  - `A2_2::REFINED::DETERMINISTIC_KERNEL_PIPELINE::030ebc838121b473`
  - `A2_2::REFINED::a0_budget_and_truncation::4745e5fd4d283ec6`
  - `A2_2::REFINED::a0_export_block_compilation::0689ed62233c4265`
  - `A2_2::REFINED::a1_anti_classical_leakage::702a223de5c2c206`
  - `A2_2::REFINED::a1_strategy_v1_schema::d471f02fe871cb95`
  - ... and 413 more.
- **rule5_graveyard_live_edges**: 4 violations found.
  - `XLINK::TERM::A2_3::SOURCE_MAP_PASS::zip_dropins_03_task__classical_residue_graveyar::acbfa66d9975d56d--A2_3::SOURCE_MAP_PASS::03_task__classical_residue_graveyard_registry_and_::480c6a62bad752c2`
  - `XLINK::NAME::A2_3::SOURCE_MAP_PASS::zip_dropins_03_task__classical_residue_graveyar::acbfa66d9975d56d--A2_3::SOURCE_MAP_PASS::zip_dropins_global_classical_residue_graveyard_::8fb24cfdb4241fcd`
  - `XLINK::NAME::A2_3::SOURCE_MAP_PASS::03_task__classical_residue_graveyard_registry_and_::480c6a62bad752c2--A2_3::SOURCE_MAP_PASS::zip_dropins_03_task__classical_residue_graveyar::acbfa66d9975d56d`
  - `XLINK::NAME::A2_3::SOURCE_MAP_PASS::03_task__classical_residue_graveyard_registry_and_::480c6a62bad752c2--A2_3::SOURCE_MAP_PASS::zip_dropins_global_classical_residue_graveyard_::8fb24cfdb4241fcd`

### system_graph_a2_refinery.json
- **rule1_kernel_admissibility**: 811 violations found.
  - `A2_3::TERM_CONFLICT_PASS::entropic_monism::8406fb95900f12ef`
  - `A2_3::SOURCE_MAP_PASS::holographic_entropy_bound::dae2251ea1c2a197`
  - `A2_3::SOURCE_MAP_PASS::retrocausal_multiverse_genesis::1659d7f485a7030c`
  - `A2_3::SOURCE_MAP_PASS::finite_universe_compressibility::71ef60b58bfaa3d3`
  - `A2_3::SOURCE_MAP_PASS::converging_possibilities_gravity::8eb939aece17635f`
  - ... and 806 more.
- **rule4_skill_operation_type**: 123 violations found.
  - `SKILL::a0-compiler`
  - `SKILL::a1-brain`
  - `SKILL::a1-cartridge-assembler`
  - `SKILL::a1-distiller`
  - `SKILL::a1-from-a2-distillation`
  - ... and 118 more.
- **rule5_graveyard_live_edges**: 259 violations found.
  - `EDGE::A2_3::SOURCE::THREAD_CONTEXT_EXTRACT__MAX__2026_03_17__v1.md::0bf12086c506c620--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::graveyard_branch_work::f94edca8dd36d295`
  - `EDGE::A2_3::SOURCE::03_B_KERNEL_SPEC.md::9e1ec3b00e4fc649--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::graveyard_write_contract::fd4e4b578cd838db`
  - `EDGE::A2_3::SOURCE::16_ZIP_SAVE_AND_TAPES_SPEC.md::cf4a073347439a78--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::graveyard_rescue_share::94e791e7b745b5f4`
  - `EDGE::A2_3::SOURCE::A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__v1.md::b06e74875e31bc70--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::a1_state_a1_graveyard_first_validity_profile__v1::713912a7d63af423`
  - `EDGE::A2_3::SOURCE::A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__v1.md::b06e74875e31bc70--SOURCE_MAP_PASS-->A2_3::SOURCE_MAP_PASS::a1_state_a1_rescue_and_graveyard_operators__v1::1743a98bdba4c06b`
  - ... and 254 more.

### a1_jargoned_graph_v1.json
- **rule1_kernel_admissibility**: 385 violations found.
  - `A2_3::TERM_CONFLICT_PASS::entropic_monism::8406fb95900f12ef`
  - `A2_3::SOURCE_MAP_PASS::holographic_entropy_bound::dae2251ea1c2a197`
  - `A2_3::SOURCE_MAP_PASS::retrocausal_multiverse_genesis::1659d7f485a7030c`
  - `A2_3::SOURCE_MAP_PASS::finite_universe_compressibility::71ef60b58bfaa3d3`
  - `A2_3::SOURCE_MAP_PASS::converging_possibilities_gravity::8eb939aece17635f`
  - ... and 380 more.

### promoted_subgraph.json
- **rule5_graveyard_live_edges**: 1 violations found.
  - `XLINK::NAME::A2_2::REFINED::graveyard_branch_work::f94edca8dd36d295--A2_3::SOURCE_MAP_PASS::graveyard_branch_work::f94edca8dd36d295`


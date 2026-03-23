---
id: "A1_STRIPPED::ZIP_PROTOCOL_V2"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# ZIP_PROTOCOL_V2
**Node ID:** `A1_STRIPPED::ZIP_PROTOCOL_V2`

## Description
Massive 280-line protocol defining ZIP transmission. Requires ZIP_HEADER.json, MANIFEST.json, HASHES.sha256. Defines 8 zip_types (e.g. A1_TO_A0_STRATEGY_ZIP, B_TO_A0_STATE_UPDATE_ZIP). Enforces determ

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["zip_header"]

## Outward Relations
- **STRIPPED_FROM** → [[zip_protocol_v2]]

## Inward Relations
- [[zip_protocol_v2]] → **ROSETTA_MAP**
- [[ZIP_PROTOCOL_V2_CARTRIDGE]] → **PACKAGED_FROM**
- [[a2_low_entropy_boot_order]] → **DEPENDS_ON**
- [[zip_subagent_template_matrix]] → **DEPENDS_ON**
- [[control_plane_a1_strategy_v1]] → **DEPENDS_ON**
- [[control_plane_a2_execution_policy_v1]] → **DEPENDS_ON**
- [[control_plane_anti_helpfulness_policy_v1]] → **DEPENDS_ON**
- [[control_plane_layer_isolation_invariant_v1]] → **DEPENDS_ON**
- [[control_plane_reject_tag_taxonomy_v1]] → **DEPENDS_ON**
- [[control_plane_sim_evidence_v1]] → **DEPENDS_ON**
- [[control_plane_zip_protocol_v2]] → **DEPENDS_ON**
- [[control_plane_zip_subagent_template_matrix__v1]] → **DEPENDS_ON**
- [[control_plane_a0_determinism_test]] → **DEPENDS_ON**
- [[control_plane_full_cycle_simulation_v2_3]] → **DEPENDS_ON**
- [[control_plane_zip_validation_matrix]] → **DEPENDS_ON**
- [[v3_spec_zip_protocol_v2]] → **DEPENDS_ON**
- [[sysrepair_v2_a2_execution_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v2_anti_helpfulness_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v2_reject_tag_taxonomy_v1]] → **DEPENDS_ON**
- [[sysrepair_v2_sim_evidence_v1]] → **DEPENDS_ON**
- [[sysrepair_v2_zip_protocol_v2]] → **DEPENDS_ON**
- [[sysrepair_v2_zip_validation_matrix]] → **DEPENDS_ON**
- [[sysrepair_v3_a2_execution_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v3_anti_helpfulness_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v3_reject_tag_taxonomy_v1]] → **DEPENDS_ON**
- [[sysrepair_v3_sim_evidence_v1]] → **DEPENDS_ON**
- [[sysrepair_v3_zip_protocol_v2]] → **DEPENDS_ON**
- [[sysrepair_v3_zip_validation_matrix]] → **DEPENDS_ON**
- [[sysrepair_v4_a2_execution_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v4_anti_helpfulness_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v4_reject_tag_taxonomy_v1]] → **DEPENDS_ON**
- [[sysrepair_v4_sim_evidence_v1]] → **DEPENDS_ON**
- [[sysrepair_v4_zip_protocol_v2]] → **DEPENDS_ON**
- [[sysrepair_v4_zip_validation_matrix]] → **DEPENDS_ON**
- [[v3_runtime_test_zip_protocol_v2_validator]] → **DEPENDS_ON**
- [[v3_runtime_zip_protocol_v2_validator]] → **DEPENDS_ON**
- [[v3_runtime_zip_protocol_v2_writer]] → **DEPENDS_ON**
- [[reject_tag_taxonomy_v1]] → **DEPENDS_ON**
- [[events_jsonl]] → **DEPENDS_ON**
- [[zip_protocol_v2_validator_py]] → **DEPENDS_ON**
- [[zip_protocol_v2_writer_py]] → **DEPENDS_ON**
- [[test_zip_protocol_v2_validator_py]] → **DEPENDS_ON**

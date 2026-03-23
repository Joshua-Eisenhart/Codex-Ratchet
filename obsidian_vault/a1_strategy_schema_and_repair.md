---
id: "A2_3::SOURCE_MAP_PASS::a1_strategy_schema_and_repair::c8259e5f0ba9fe0f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "DRAFT"
---

# a1_strategy_schema_and_repair
**Node ID:** `A2_3::SOURCE_MAP_PASS::a1_strategy_schema_and_repair::c8259e5f0ba9fe0f`

## Description
A1_STRATEGY_v1 JSON schema: required fields (schema, run_id, sequence, strategy_id, inputs, budget, diversity_budget, targets, alternatives, self_audit). Budget: max_targets/alternatives/total_items/sim_requests. Diversity budget: axes with min_distinct_values. Proposals: proposal_id, proposal_class (TARGET/ALTERNATIVE), spec_kind, requires, fields, asserts, operator_id. Self-audit: strategy_sha256 (recursion-safe), structural_digest. Anti-fake: forbidden keys confidence/probability/embedding. Real wiggle gate: at least 1 alternative structurally distinct. A1_REPAIR_OPERATOR_MAPPING: maps operators to repair actions. A1_CONSOLIDATION_PREPACK_JOB: batch driver for pre-A0 strategy surface.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[a1_consolidation_prepack_job]]
- **DEPENDS_ON** → [[a1_repair_operator_mapping]]
- **DEPENDS_ON** → [[structural_digest]]
- **DEPENDS_ON** → [[a1_strategy_v1]]
- **DEPENDS_ON** → [[input]]
- **DEPENDS_ON** → [[value]]
- **DEPENDS_ON** → [[request]]
- **DEPENDS_ON** → [[a1_strategy_v1_json]]
- **STRUCTURALLY_RELATED** → [[canon_geometry_seven_axes]]
- **STRUCTURALLY_RELATED** → [[cl_topology_contract_v1]]
- **STRUCTURALLY_RELATED** → [[a2_state_v3_doc_92656a174243]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_topology_contract_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_doc_92656a174243]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_topology_contract_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_doc_92656a174243]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_topology_contract_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_doc_92656a174243]]
- **STRUCTURALLY_RELATED** → [[Constraint_Ladder_IS_The_Language]]
- **STRUCTURALLY_RELATED** → [[CMD_Nonflattenability]]

## Inward Relations
- [[A1_STRATEGY_v1.md]] → **SOURCE_MAP_PASS**
- [[a2_low_entropy_boot_order]] → **STRUCTURALLY_RELATED**
- [[stage_3_template_flow]] → **STRUCTURALLY_RELATED**
- [[B_SURVIVOR_F205_LABEL_DEF]] → **ACCEPTED_FROM**
- [[B_PARKED_F207]] → **PARKED_FROM**
- [[B_PARKED_F208]] → **PARKED_FROM**

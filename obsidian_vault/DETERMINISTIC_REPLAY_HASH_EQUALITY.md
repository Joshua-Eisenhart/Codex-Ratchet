---
id: "A2_3::ENGINE_PATTERN_PASS::DETERMINISTIC_REPLAY_HASH_EQUALITY::bdb42d5287cc4361"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# DETERMINISTIC_REPLAY_HASH_EQUALITY
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::DETERMINISTIC_REPLAY_HASH_EQUALITY::bdb42d5287cc4361`

## Description
Two runs with identical strategy + replay source produce byte-identical output hashes, proving full pipeline determinism. Test asserts hash_a == hash_b and export_block_a == export_block_b.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[deterministic_dual_replay]]
- **STRUCTURALLY_RELATED** → [[control_plane_deterministic_replay_runner_outline_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_deterministic_replay_runner_ou]]
- **STRUCTURALLY_RELATED** → [[sim_deterministic_replay]]
- **STRUCTURALLY_RELATED** → [[deterministic_replay_runner]]
- **STRUCTURALLY_RELATED** → [[deterministic_replay_runner_outline_v1]]

## Inward Relations
- [[test_a1_a0_b_sim_integration.py]] → **ENGINE_PATTERN_PASS**
- [[CANONICAL_SERIALIZATION_EVERYWHERE]] → **RELATED_TO**
- [[deterministic_dual_replay]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_DUAL_REPLAY]] → **STRUCTURALLY_RELATED**

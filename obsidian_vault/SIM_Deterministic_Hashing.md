---
id: "A2_3::ENGINE_PATTERN_PASS::SIM_Deterministic_Hashing::ddf98d59d0bc3548"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# SIM_Deterministic_Hashing
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::SIM_Deterministic_Hashing::ddf98d59d0bc3548`

## Description
Every sim manifest includes: sim_id, tier, family, input_hash, code_hash, output_hash, manifest_hash, evidence_tokens. Replay with same code+input must reproduce hashes.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[sim_deterministic_replay]]
- **RELATED_TO** → [[zip_protocol_v2_contract]]

## Inward Relations
- [[06_SIM_EVIDENCE_AND_TIERS_SPEC.md]] → **ENGINE_PATTERN_PASS**
- [[CANONICAL_SERIALIZATION_EVERYWHERE]] → **RELATED_TO**

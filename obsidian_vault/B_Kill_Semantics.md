---
id: "A2_3::ENGINE_PATTERN_PASS::B_Kill_Semantics::41b315c926bd5aef"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# B_Kill_Semantics
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::B_Kill_Semantics::41b315c926bd5aef`

## Description
KILL_IF is declarative. Item killed iff: declares KILL_IF with COND_TOKEN, AND SIM_EVIDENCE contains matching KILL_SIGNAL, AND kill binding passes. Default: SIM_ID must equal target ID. Remote kill requires explicit KILL_BIND DEF_FIELD.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[kill_if_semantics]]

## Inward Relations
- [[BOOTPACK_THREAD_B_v3.9.13.md]] → **ENGINE_PATTERN_PASS**
- [[kill_if_semantics]] → **STRUCTURALLY_RELATED**
- [[KILL_IF_SEMANTICS]] → **STRUCTURALLY_RELATED**

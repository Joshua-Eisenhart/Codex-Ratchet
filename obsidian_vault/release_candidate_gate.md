---
id: "A2_3::SOURCE_MAP_PASS::release_candidate_gate::b4cc25671eda1d8f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# release_candidate_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::release_candidate_gate::b4cc25671eda1d8f`

## Description
Final release approval checks two end-to-end replay passes establishing identical state/log hashes, packaged in RELEASE_CHECKLIST_v1.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **EXCLUDES** → [[v3_tools_run_release_candidate_gate]]
- **EXCLUDES** → [[run_release_candidate_gate_py]]

## Inward Relations
- [[21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md]] → **SOURCE_MAP_PASS**
- [[dual_replay_release_gate]] → **RELATED_TO**

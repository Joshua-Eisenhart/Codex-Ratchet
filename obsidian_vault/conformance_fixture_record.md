---
id: "A2_3::SOURCE_MAP_PASS::conformance_fixture_record::c46bed4f6b48d13d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# conformance_fixture_record
**Node ID:** `A2_3::SOURCE_MAP_PASS::conformance_fixture_record::c46bed4f6b48d13d`

## Description
Immutable fixture entry containing fixture_id, expected_status (PASS|PARK|REJECT), expected_tags, and rule_families. Carries minimal reproducible payload to validate B behavior and block drift.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[v3_spec_23_bootpack_conformance_fixture_mat]]
- **STRUCTURALLY_RELATED** → [[v3_tools_run_conformance_fixture_matrix]]
- **STRUCTURALLY_RELATED** → [[run_conformance_fixture_matrix_py]]

## Inward Relations
- [[23_BOOTPACK_CONFORMANCE_FIXTURE_MATRIX_CONTRACT.md]] → **SOURCE_MAP_PASS**
- [[conformance_fixture_matrix_contract]] → **STRUCTURALLY_RELATED**
- [[23_bootpack_conformance_fixture_matrix_contract]] → **STRUCTURALLY_RELATED**
- [[conformance_fixture_matrix_contract]] → **STRUCTURALLY_RELATED**
- [[CONFORMANCE_FIXTURE_MATRIX_CONTRACT]] → **STRUCTURALLY_RELATED**

---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_expected_outcomes::1cfd0bb196f89a21"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_expected_outcomes
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_expected_outcomes::1cfd0bb196f89a21`

## Description
expected_outcomes.json (4684B): [   {     "fixture_name": "axiom_root_pass.txt",     "expected_status": "PASS",     "expected_tags": []   },   {     "fixture_name": "axiom_root_reject.txt",     "expected_status": "REJECT",     "expected_tags": [       "SCHEMA_FAIL"     ]   },   {  

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[axiom_root_reject]]
- **DEPENDS_ON** → [[axiom_root_pass]]

## Inward Relations
- [[sim_term_generic_negative.py]] → **SOURCE_MAP_PASS**
- [[expected_outcomes_json]] → **EXCLUDES**

---
id: "A2_3::ENGINE_PATTERN_PASS::B_KERNEL_LINE_FENCE_VALIDATION::ff4c2bb2244302e7"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# B_KERNEL_LINE_FENCE_VALIDATION
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::B_KERNEL_LINE_FENCE_VALIDATION::ff4c2bb2244302e7`

## Description
Every line in an export block must match a recognized regex pattern (SPEC_HYP, DEF_FIELD, REQUIRES, etc.). Unrecognized lines cause immediate REJECT. This is a fail-closed content gate.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[stage_2_schema_stubs]]
- **RELATED_TO** → [[deterministic_promotion]]
- **RELATED_TO** → [[stage_2_validation_behavior]]
- **RELATED_TO** → [[COMMENT_BAN_ENFORCEMENT]]
- **RELATED_TO** → [[L0_LEXEME_SET_18_STRUCTURAL_TOKENS]]
- **STRUCTURALLY_RELATED** → [[b_kernel_rejection_fence]]
- **STRUCTURALLY_RELATED** → [[b_kernel_rejection_tag_fence]]
- **STRUCTURALLY_RELATED** → [[V3_BKernel_Line_Fence_System]]
- **STRUCTURALLY_RELATED** → [[THREAD_B_FENCE_PRE_VALIDATION]]

## Inward Relations
- [[kernel.py]] → **ENGINE_PATTERN_PASS**
- [[B_Deterministic_10_Stage_Order]] → **RELATED_TO**

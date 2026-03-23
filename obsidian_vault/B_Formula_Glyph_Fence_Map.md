---
id: "A2_3::ENGINE_PATTERN_PASS::B_Formula_Glyph_Fence_Map::460002fac05ac5ce"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# B_Formula_Glyph_Fence_Map
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::B_Formula_Glyph_Fence_Map::460002fac05ac5ce`

## Description
21 glyphs mapped to required TERM_REGISTRY entries. Each glyph (+ - * / ^ ~ ! [ ] { } ( ) < > | & , : .) requires its corresponding term (plus_sign, minus_sign, etc.) to be CANONICAL_ALLOWED before use in FORMULA strings. Unknown glyphs → REJECT.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **EXCLUDES** → [[conformance_fix_formula_001_glyph_reject]]
- **EXCLUDES** → [[sysrepair_v2_fix_formula_001_glyph_reject]]
- **EXCLUDES** → [[sysrepair_v3_fix_formula_001_glyph_reject]]
- **EXCLUDES** → [[sysrepair_v4_fix_formula_001_glyph_reject]]
- **EXCLUDES** → [[fix_formula_001_glyph_reject]]

## Inward Relations
- [[BOOTPACK_THREAD_B_v3.9.13.md]] → **ENGINE_PATTERN_PASS**

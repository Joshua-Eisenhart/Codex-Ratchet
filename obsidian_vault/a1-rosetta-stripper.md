---
id: "SKILL::a1-rosetta-stripper"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-rosetta-stripper
**Node ID:** `SKILL::a1-rosetta-stripper`

## Description
Strip jargon overlays from concepts

## Properties
- **skill_type**: refinement
- **source_type**: operator_module
- **source_path**: system_v4/skills/a1_rosetta_stripper.py
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "A1_STRIPPED", "PHASE_A1_STRIPPER"]
- **applicable_trust_zones**: ["A1_JARGONED", "A1_STRIPPED", "PHASE_A1_STRIPPER"]
- **applicable_graphs**: ["rosetta"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/a1_rosetta_stripper.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[a1_rosetta_function]]

## Inward Relations
- [[a1-jargoned-graph-builder]] → **RELATED_TO**
- [[a1-jargoned-scope-aligner]] → **RELATED_TO**
- [[a1-stripped-graph-builder]] → **RELATED_TO**

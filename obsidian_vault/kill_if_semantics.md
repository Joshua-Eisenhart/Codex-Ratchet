---
id: "A1_STRIPPED::KILL_IF_SEMANTICS"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# KILL_IF_SEMANTICS
**Node ID:** `A1_STRIPPED::KILL_IF_SEMANTICS`

## Description
KILL_IF is declarative and idempotent. An item is KILLED iff: (1) item declares KILL_IF <ID> CORR <COND_TOKEN>, (2) SIM_EVIDENCE contains matching KILL_SIGNAL, and (3) kill binding passes (default loc

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["explicit"]

## Outward Relations
- **STRIPPED_FROM** → [[kill_if_semantics]]
- **STRUCTURALLY_RELATED** → [[kill_if_semantics]]
- **STRUCTURALLY_RELATED** → [[B_Kill_Semantics]]

## Inward Relations
- [[kill_if_semantics]] → **ROSETTA_MAP**
- [[KILL_IF_SEMANTICS_CARTRIDGE]] → **PACKAGED_FROM**

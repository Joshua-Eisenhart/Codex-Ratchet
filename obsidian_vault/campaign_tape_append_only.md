---
id: "A1_STRIPPED::CAMPAIGN_TAPE_APPEND_ONLY"
type: "REFINED_CONCEPT"
layer: "A1_STRIPPED"
authority: "CROSS_VALIDATED"
---

# CAMPAIGN_TAPE_APPEND_ONLY
**Node ID:** `A1_STRIPPED::CAMPAIGN_TAPE_APPEND_ONLY`

## Description
CAMPAIGN_TAPE v1 is mandatory and append-only. Records (EXPORT_BLOCK + THREAD_B_REPORT) pairs in canonical order via deterministic JSONL. EXPORT_TAPE v1 is the pre-run ordered list that promotes into

## Properties
- **dropped_jargon**: []
- **required_anchors**: ["UNVERIFIED"]

## Outward Relations
- **STRIPPED_FROM** → [[campaign_tape_append_only]]
- **STRUCTURALLY_RELATED** → [[campaign_tape_append_only]]
- **STRUCTURALLY_RELATED** → [[campaign_tape_000_jsonl]]
- **STRUCTURALLY_RELATED** → [[campaign_tape_v1_format]]
- **STRUCTURALLY_RELATED** → [[Campaign_Tape_Mandatory]]

## Inward Relations
- [[campaign_tape_append_only]] → **ROSETTA_MAP**
- [[CAMPAIGN_TAPE_APPEND_ONLY_CARTRIDGE]] → **PACKAGED_FROM**

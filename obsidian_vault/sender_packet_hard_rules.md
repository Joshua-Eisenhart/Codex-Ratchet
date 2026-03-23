---
id: "A2_3::SOURCE_MAP_PASS::sender_packet_hard_rules::fe161f1f6e25b1e1"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# sender_packet_hard_rules
**Node ID:** `A2_3::SOURCE_MAP_PASS::sender_packet_hard_rules::fe161f1f6e25b1e1`

## Description
Message must be exactly "go on". Cannot target Pro or Controller threads. Count lock engages if continuation count >= 1, requiring fresh manual review.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[verification_lock]]
- **EXCLUDES** → [[v3_runtime_test_bootpack_hard_rules]]
- **EXCLUDES** → [[test_bootpack_hard_rules_py]]

## Inward Relations
- [[44_AUTO_GO_ON_SENDER_PACKET__v1.md]] → **SOURCE_MAP_PASS**
- [[no_free_chaining_constraint]] → **RELATED_TO**
- [[browser_helper_refusals]] → **RELATED_TO**
- [[real_send_hard_refusals]] → **RELATED_TO**
- [[a2_thread_boot_nine_hard_rules]] → **EXCLUDES**
- [[a1_thread_boot_eight_hard_rules]] → **EXCLUDES**
- [[a2_seven_hard_rules]] → **STRUCTURALLY_RELATED**
- [[a2_thread_boot_nine_hard_rules]] → **STRUCTURALLY_RELATED**
- [[a1_thread_boot_eight_hard_rules]] → **STRUCTURALLY_RELATED**
- [[a2_seven_hard_rules]] → **STRUCTURALLY_RELATED**
- [[a2_hard_rules]] → **STRUCTURALLY_RELATED**
- [[A2_THREAD_BOOT_NINE_HARD_RULES]] → **STRUCTURALLY_RELATED**
- [[A1_THREAD_BOOT_EIGHT_HARD_RULES]] → **STRUCTURALLY_RELATED**
- [[A2_SEVEN_HARD_RULES]] → **STRUCTURALLY_RELATED**

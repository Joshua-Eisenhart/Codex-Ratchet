---
id: "A2_3::SOURCE_MAP_PASS::a1_ranking_comparator::abb864d48d064d4a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# a1_ranking_comparator
**Node ID:** `A2_3::SOURCE_MAP_PASS::a1_ranking_comparator::abb864d48d064d4a`

## Description
Deterministic branch ranking: (1) viability_score descending, (2) novelty_score descending, (3) unresolved dependency count ascending, (4) branch_id lexical ascending. Tie behavior is deterministic and stable. No randomization.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[a2_deterministic_tick_sequence]]
- **RELATED_TO** → [[b_kernel_10_stage_pipeline]]
- **RELATED_TO** → [[b_kernel_deterministic_stage_order]]
- **RELATED_TO** → [[dual_replay_release_gate]]

## Inward Relations
- [[18_A1_WIGGLE_EXECUTION_CONTRACT.md]] → **SOURCE_MAP_PASS**
- [[a0_deterministic_compilation_contract]] → **RELATED_TO**
- [[a0_deterministic_truncation_contract]] → **RELATED_TO**

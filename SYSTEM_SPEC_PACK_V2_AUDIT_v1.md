# SYSTEM_SPEC_PACK_V2_AUDIT_v1

Timestamp (UTC): 2026-02-21T04:46:33Z

## What this zip is
A **Codex-friendly, high-level system spec pack** describing A2/A1/A0/B/SIM roles, the “translator boundary”, and an A1 wiggle/repair loop.

This is closer to your described architecture than the FlowMind pack.

## Contents (non-MacOS files)
- system_spec_pack_v2
- system_spec_pack_v2/00_MANIFEST.md
- system_spec_pack_v2/01_OVERVIEW.md
- system_spec_pack_v2/02_THREADS_AND_BOOT.md
- system_spec_pack_v2/03_B_ARTIFACTS_AND_FENCES.md
- system_spec_pack_v2/04_CANON_STATE_SCHEMA.md
- system_spec_pack_v2/05_EVIDENCE_SIMS_NEGATIVE.md
- system_spec_pack_v2/06_GRAVEYARD_AND_ALTERNATIVES.md
- system_spec_pack_v2/07_DOC_SYSTEM_AND_SHARDING.md
- system_spec_pack_v2/08_MODEL_SWITCH_PROTOCOL.md
- system_spec_pack_v2/09_A1_STRATEGY_DECLARATION.md
- system_spec_pack_v2/10_TRANSLATOR_BOUNDARY_AND_POLICY.md
- system_spec_pack_v2/11_PROVENANCE_CHAIN_AND_REPLAY.md
- system_spec_pack_v2/12_TERM_COMPOSITION_AND_RATCHET_COMPLETENESS.md
- system_spec_pack_v2/13_A2_YAML_USAGE_AND_COMPACTION.md
- system_spec_pack_v2/14_DO_NOT_DO_AND_FORBIDDEN_MOVES.md
- system_spec_pack_v2/15_AUDIT_GATES_AND_SUCCESS_CRITERIA.md
- system_spec_pack_v2/16_A2_PERSISTENT_BRAIN_SCHEMA.md
- system_spec_pack_v2/17_A1_REPAIR_LOOP_AND_WIGGLE_PROTOCOL.md
- system_spec_pack_v2/18_A1_A2_CONFORMANCE_CHECKLIST.md
- system_spec_pack_v2/19_SIM_TIER_ARCHITECTURE.md
- system_spec_pack_v2/20_SIM_PROMOTION_AND_MASTER_SIM.md
- system_spec_pack_v2/21_SYSTEM_REQUIREMENTS_LEDGER.md
- system_spec_pack_v2/22_SPEC_COVERAGE_MATRIX.md

## Strengths (for onboarding a coding assistant)
- Provides a *reading spine* and a coherent authority order: A2 (high entropy) → A1 (wiggle/rosetta) → A0 (deterministic compiler/orchestrator) → B (deterministic kernel) with SIM as deterministic executor.
- Includes a model-switch protocol and a “wiggle protocol” framing that matches your stated A1 role.

## Risks / watch-outs
- This pack is **not your bootpacks**; treat it as **vNext / A2-level guidance** unless explicitly ratcheted into B.
- Some parts use placeholder naming (e.g., model labels) that may not match your actual Codex UI; use as intent, not literal.

## Recommendation
Use this zip as the **primary “Codex orientation binder”** (A2-level) to prevent drift while implementing the real bootpacks.

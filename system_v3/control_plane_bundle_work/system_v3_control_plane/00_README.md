
# system_v3_control_plane

This bundle is a **control-plane spec suite** for the Ratchet runtime.

It is intended to be sent between Codex threads (and/or used locally) as the **single source-of-truth** for:
- ZIP transport law (typed, directional, deterministic)
- Strategy/evidence schemas
- Repair discipline
- Promotion binding (semantic ratchet activation)
- A2 perception/analysis interfaces
- FlowMind integration boundary (governance vs transport vs truth)

## What this bundle is
- A **frozen spec surface** intended to reduce drift across A2/A1/A0/B/SIM.
- A set of **interlocking contracts**. If two documents disagree, treat it as a bug.

## What this bundle is not
- Not implementation code.
- Not a redesign proposal.
- Not a place for policy/ABAC/confidence/TTL/classifier semantics inside transport law.

## Start here
1) `01_ARCHITECTURE_OVERVIEW.md`
2) `02_LAYER_BOUNDARIES.md`
3) `03_MUTATION_PATH_RULES.md`
4) `SYSTEM_CONTEXT_UPDATE_v2.6_PREP.md`
5) `specs/ZIP_PROTOCOL_v2.md`
6) `specs/ZIP_SUBAGENT_TEMPLATE_MATRIX__v1.md`
7) `specs/A1_CONSOLIDATION_PREPACK_JOB__v1.md`
8) `flowmind_integration/LEV_MMM_DECENTRALIZATION_AUDIT_v2_1.md`
9) `specs/ENUM_REGISTRY_v1.md`
10) `specs/STRUCTURAL_DIGEST_v1.md`
11) `specs/A0_SAVE_SUMMARY_v1.md`
12) `validator_contract/FULL_CYCLE_SIMULATION_v2_3.md`
13) `validator_contract/SEMANTIC_RATCHET_STRESS_TEST_PLAN_v1.md`
14) `validator_contract/AUTOMATED_STRESS_HARNESS_BLUEPRINT_v1.md`
15) `validator_contract/DETERMINISTIC_REPLAY_RUNNER_OUTLINE_v1.md`
16) `flowmind_integration/CODEX_ONLY_CAPSULE_EXECUTION_TOPOLOGY_v1.md`
17) `specs/ANTI_HELPFULNESS_POLICY_v1.md`
18) `specs/LAYER_ISOLATION_INVARIANT_v1.md`
19) `specs/INTERACTION_DENSITY_v1.md`
20) `specs/A2_MODES_v1.md`
21) `specs/A2_EXECUTION_POLICY_v1.md`
22) `specs/A2_ENTROPY_POLICY_v1.md`
23) `specs/RUNTIME_IMAGE_POLICY_v1.md`
24) `specs/CROSS_BASIN_REQUIREMENT_v1.md`
25) `specs/FALSIFIABILITY_CLAUSE_v1.md`

## Execution posture
- Fail-closed.
- Deterministic validation.
- No bypass paths.
- Mutation only via the declared mutation path.
- No implicit defaults.

## Version coupling rule
If `ZIP_PROTOCOL` version changes:
- `REJECT_TAG_TAXONOMY` version MUST be reviewed.
- `A1_STRATEGY` version MUST be reviewed.
- `STRUCTURAL_DIGEST` version MUST be reviewed.
- `STATE_TRANSITION_DIGEST` version MUST be reviewed.

## Template note
The `templates/` directory contains **non-authoritative scaffolds** for building valid ZIPs.
Do not include extra files when producing a ZIP; ZIP validation is allowlist-only.

## Active adapter note
The `A1_CONSOLIDATION_PREPACK_JOB` family has an active tooling adapter:
- `system_v3/tools/run_a1_consolidation_prepack_job.py`
- `system_v3/tools/a1_external_memo_batch_driver.py` now invokes it on exchange responses and records `exchange_prepack_rows`

That adapter stays above the lower loop and emits one strict pre-A0 strategy surface.

# ZIP_SUBAGENT_TEMPLATE_MATRIX__v1

Status: DRAFT / NONCANON
Date: 2026-03-06
Role: master template matrix for transport ZIPs and portable ZIP subagent bundles

## 1) Purpose

This document is the single matrix for the ZIP-subagent engineering layer.

It does **not** replace:
- `ZIP_PROTOCOL_v2` for cross-layer transport
- individual template folders for concrete scaffolds

It does:
- define the whole template family set in one place
- separate active transport ZIPs from work/prototype ZIP_JOB bundles
- make each concrete template an instance of a small number of primitive families

## 2) Two ZIP Regimes

### 2.1 Transport ZIPs (active lower mutation path)
These are cross-layer, allowlist-typed, deterministic carriers.

Authority surfaces:
- `specs/ZIP_PROTOCOL_v2.md`
- `templates/`

Properties:
- exact filenames
- exact layer directions
- exact payload allowlists
- deterministic validation
- no policy logic inside transport

### 2.2 ZIP_JOB / ZIP subagent bundles (upper-layer work orders)
These are portable, task-doc driven bundles used inside A2/A1 sandboxes or external worker surfaces.

Primary owner/reference surfaces:
- `work/zip_subagents/ZIP_JOB__SUBAGENT_BUNDLE_PROTOCOL_v1.md`
- `work/zip_subagents/ZIP_JOB__VARIANT__A2_DOC_TOPIC_REFINERY_v1.md`
- `work/zip_subagents/ZIP_SUBAGENT_SYSTEM_v2_1__CONTROL_PLANE_ALIGNED__LONG_EXPLICIT_NAMING.md`

Derived / delivery surfaces:
- `work/zip_dropins/`
- `work/curated_zips/`
- `work/coordination_sandbox__codex_minimax__noncanonical_delete_safe/`

Properties:
- multi-file task bundles
- can carry templates, inputs, outputs, and logs
- not direct B-facing mutation containers
- portable across Codex / browser / other worker surfaces

## 3) Master Primitive Families

All concrete templates should be understood as instances of these primitive families.

### F1) TRANSPORT_FORWARD
Purpose:
- move structured proposals downward toward mutation

Current concrete members:
- `A2_TO_A1_PROPOSAL_ZIP`
- `A1_TO_A0_STRATEGY_ZIP`
- `A0_TO_B_EXPORT_BATCH_ZIP`

### F2) TRANSPORT_BACKWARD
Purpose:
- move deterministic feedback / save state upward

Current concrete members:
- `B_TO_A0_STATE_UPDATE_ZIP`
- `SIM_TO_A0_SIM_RESULT_ZIP`
- `A0_TO_A1_SAVE_ZIP`
- `A1_TO_A2_SAVE_ZIP`
- `A2_META_SAVE_ZIP`

### F3) A2_EXTRACTION_JOB
Purpose:
- document/topic extraction
- topic clustering
- contradiction-preserving distillation

Current prototype members:
- `A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION`
- `A2_DOC_TOPIC_REFINERY`
- `A2_TOPIC_PACKET`
- `A2_TOPIC_CLUSTER`
- `A2_TOPIC_DEDUP_AND_COMPRESSION_REFINEMENT`

### F4) A2_TO_A1_DISTILLATION_JOB
Purpose:
- convert A2 understanding into structured A1-ready outputs

Current prototype members:
- `A2_A1_RATCHET_FUEL_MINT`
- `A2_LAYER_1_5__MULTI_RUN_CONSOLIDATION_AND_A1_WIGGLE_PREP`

### F5) A1_GENERATION_JOB
Purpose:
- large A1 family generation above the lower loop

Current prototype members:
- `A1_WIGGLE_MASS_TERM_MINT_1000`
- `A1_LLM_LANE_REQUEST`

### F6) A1_CONSOLIDATION_PREPACK_JOB
Purpose:
- merge many A1 worker outputs into one strict pre-A0 package

Current status:
- now defined as a clean top-level template family under `job_templates/A1_CONSOLIDATION_PREPACK_JOB_TEMPLATE/`
- still upper-layer only and non-transport

### F7) AUDIT_VALIDATION_JOB
Purpose:
- validate bundles, expected outputs, and deterministic behavior

Current prototype members:
- golden checks under `work/golden_tests`
- bundle validation and schema-gate work

### F8) EXTERNAL_WORKER_JOB
Purpose:
- browser/claw or other external worker execution at the A2 border

Current prototype members:
- ChatUI dropins under `work/zip_dropins`
- claw-related curated zips under `work/curated_zips`
- `EXTERNAL_RESEARCH_RETOOL_REFINERY`

## 4) Concrete Template Matrix

| Primitive family | Concrete template / type | Layer role | Current location | State |
|---|---|---|---|---|
| `TRANSPORT_FORWARD` | `A2_TO_A1_PROPOSAL_ZIP` | A2 → A1 | `templates/A2_TO_A1_PROPOSAL_ZIP_TEMPLATE` | active |
| `TRANSPORT_FORWARD` | `A1_TO_A0_STRATEGY_ZIP` | A1 → A0 | `templates/A1_TO_A0_STRATEGY_ZIP_TEMPLATE` | active |
| `TRANSPORT_FORWARD` | `A0_TO_B_EXPORT_BATCH_ZIP` | A0 → B | `templates/A0_TO_B_EXPORT_BATCH_ZIP_TEMPLATE` | active |
| `TRANSPORT_BACKWARD` | `B_TO_A0_STATE_UPDATE_ZIP` | B → A0 | `templates/B_TO_A0_STATE_UPDATE_ZIP_TEMPLATE` | active |
| `TRANSPORT_BACKWARD` | `SIM_TO_A0_SIM_RESULT_ZIP` | SIM → A0 | `templates/SIM_TO_A0_SIM_RESULT_ZIP_TEMPLATE` | active |
| `TRANSPORT_BACKWARD` | `A0_TO_A1_SAVE_ZIP` | A0 → A1 | `templates/A0_TO_A1_SAVE_ZIP_TEMPLATE` | active |
| `TRANSPORT_BACKWARD` | `A1_TO_A2_SAVE_ZIP` | A1 → A2 | `templates/A1_TO_A2_SAVE_ZIP_TEMPLATE` | active |
| `TRANSPORT_BACKWARD` | `A2_META_SAVE_ZIP` | A2 → A2 | `templates/A2_META_SAVE_ZIP_TEMPLATE` | active |
| `A2_EXTRACTION_JOB` | `A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION` | A2 sandbox | `work/zip_job_templates/A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__BUNDLE_TEMPLATE_v*` | prototype |
| `A2_EXTRACTION_JOB` | `A2_TOPIC_*` families | A2 sandbox | `work/zip_job_templates/A2_TOPIC_*` | prototype |
| `A2_TO_A1_DISTILLATION_JOB` | `A2_A1_RATCHET_FUEL_MINT` | A2 → A1 prep | `work/zip_job_templates/A2_A1_RATCHET_FUEL_MINT__BUNDLE_TEMPLATE_v1` | prototype |
| `A2_TO_A1_DISTILLATION_JOB` | `A2_LAYER_1_5__MULTI_RUN_CONSOLIDATION_AND_A1_WIGGLE_PREP` | A2 → A1 prep | `work/zip_dropins/ZIP_JOB__A2_LAYER_1_5__MULTI_RUN_CONSOLIDATION_AND_A1_WIGGLE_PREP__*` | prototype |
| `A1_GENERATION_JOB` | `A1_WIGGLE_MASS_TERM_MINT_1000` | A1 sandbox | `work/zip_job_templates/A1_WIGGLE_MASS_TERM_MINT_1000__BUNDLE_TEMPLATE_v1` | prototype |
| `A1_GENERATION_JOB` | `A1_LLM_LANE_REQUEST` | A1 sandbox | `work/a1_llm_lane_requests` | prototype |
| `A1_CONSOLIDATION_PREPACK_JOB` | `A1_CONSOLIDATION_PREPACK_JOB_TEMPLATE` | A1 sandbox | `job_templates/A1_CONSOLIDATION_PREPACK_JOB_TEMPLATE` | defined-draft |
| `AUDIT_VALIDATION_JOB` | golden checks / ZIP VM checks | validation | `work/golden_tests` | prototype |
| `EXTERNAL_WORKER_JOB` | ChatUI/Claw dropins | A2-border | `work/zip_dropins`, `work/curated_zips` | prototype |
| `EXTERNAL_WORKER_JOB` | `EXTERNAL_RESEARCH_RETOOL_REFINERY` | A2-border | `work/zip_job_templates/EXTERNAL_RESEARCH_RETOOL_REFINERY__BUNDLE_TEMPLATE_v1` | prototype |

## 5) Template Composition Rules

### Transport ZIP templates
Each transport ZIP template is defined by:
- exact `zip_type`
- exact direction
- exact source/target layer
- exact payload filename allowlist
- exact forbidden container set

These are governed only by:
- `ZIP_PROTOCOL_v2`
- `ENUM_REGISTRY_v1`
- validator contracts

### ZIP_JOB / subagent templates
Each ZIP_JOB template should be composed from the same parts:
- `meta/`
  - manifest
  - hashes
  - optional shard map
- `input/`
- `tasks/`
- `templates/`
- `output/`
- optional `log/`

The job family determines:
- task order
- expected outputs
- failure policy
- whether it is A2-only, A1-only, or A2-border

### Parallel worker rule
ZIP_JOB families are allowed to support many isolated workers in parallel.

Required discipline:
- each worker lane receives a bounded bundle
- each worker lane emits bounded outputs/logs only
- worker lanes do not trust or directly mutate each other
- any cross-lane merge must happen in an explicit consolidation job family

Sequential consolidation rule:
- parallel generation/extraction may happen before consolidation
- consolidation into one downstream handoff package must be deterministic and replayable
- only the consolidated result may be adapted into transport ZIPs for the lower mutation path

This preserves:
- parallel upper-layer search and throughput
- strict lower-layer authority and ordering
- ZIP-mediated fresh-thread portability without hidden context dependence

## 6) Promotion Rule

Only `TRANSPORT_FORWARD` and `TRANSPORT_BACKWARD` families participate directly in the active lower mutation path.

All ZIP_JOB families are:
- upper-layer work artifacts
- noncanon
- promotable only by explicit conversion/adaptation into transport ZIPs

## 7) Engineering Rule

Do not create new template names first.

First ask:
1. which primitive family does this belong to?
2. is there already a concrete template in that family?
3. can this be expressed as a parameterization of an existing template?

Only create a new concrete template if the answer is no.

## 8) Immediate Gap

The clearest current remaining gap after defining this family is:
- binding the new family cleanly to active tooling without overgrowing the lower loop

## 9) Bottom Line

The system should not have many unrelated ZIP template systems.

It should have:
- one transport ZIP regime
- one ZIP_JOB / subagent regime
- one master matrix

Every concrete template should be legible as a part of that whole.

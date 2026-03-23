# A2_UPDATE_NOTE__A1_FAMILY_SLICE_SCHEMA_DRAFT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the first draft schema for `A2_TO_A1_FAMILY_SLICE_v1` without promoting it into owner doctrine

## Scope

This note records the first schema draft for the proposed bounded A2-derived A1 family-slice object.

It is not an owner-surface spec.
It is a work-surface draft intended to support planner-reset design and reload continuity.

## Draft artifacts

Schema draft:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`

Sample payload:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Companion contract notes:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_CONTRACT__2026_03_15__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_SAMPLE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.md`

## Intent

The draft schema exists to make the planner reset concrete enough to test against a real bounded object.

It is meant to replace profile-driven doctrinal substitution with explicit family-slice input carrying:
- routing and scope
- source anchors and contradictions
- family identity
- lane obligations
- branch/negative/rescue obligations
- admissibility placement
- SIM/evidence hooks
- planner guardrails

## Admission guard result

Surface class:
- `DERIVED_A2`

Why admitted:
- additive note only
- explicit noncanon status
- explicit provenance to doctrine and reset notes
- stored as a pointer to work-surface drafts, not as a replacement owner spec

Guardrail:
- do not treat this draft schema as active owner law until it is cross-audited against the existing schema spine and the planner rewrite path actually consumes it

## Next use

Best next use is narrow:
1. validate the sample payload against the draft schema
2. prototype planner input loading from this object
3. only then decide whether a promoted owner-surface schema is warranted

## Validation checkpoint

Completed on 2026-03-15:
- JSON parse check passed for the schema draft and sample payload
- `jsonschema.validate(...)` passed for:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

First correction made during validation:
- relaxed `slice_id` / `dispatch_id` pattern from uppercase-only to repo-real alphanumeric-with-underscore naming so lowercase `v1` suffixes remain valid

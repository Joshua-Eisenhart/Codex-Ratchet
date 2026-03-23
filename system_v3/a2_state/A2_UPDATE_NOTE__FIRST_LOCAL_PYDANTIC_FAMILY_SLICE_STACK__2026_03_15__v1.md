# A2_UPDATE_NOTE__FIRST_LOCAL_PYDANTIC_FAMILY_SLICE_STACK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first real local spec-object stack for `A2_TO_A1_FAMILY_SLICE_v1`, so the family-slice contract now exists as an executable Pydantic model plus GraphML projection instead of only as hand-written JSON schema and prose

## Scope

Local stack env:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph`

New tools:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_a2_to_a1_family_slice_pydantic.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a2_to_a1_family_slice_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a2_to_a1_family_slice_pydantic_schema.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`

Generated artifacts:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

Validated active input:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

## What changed

The repo already had:
- one hand-written draft JSON schema for `A2_TO_A1_FAMILY_SLICE_v1`
- one concrete sample payload
- several runtime/control consumers that still treated the family slice mostly as raw JSON

It did not yet have:
- one actual executable typed model for that object
- one local graph projection path from the same object
- one way to emit a model-derived schema from the same source of truth

This patch adds the first local spec-object layer:
- `Pydantic + JSON first`
- `NetworkX` graph projection
- `GraphML` export

The new model:
- validates the full current family-slice shape
- enforces required lanes
- enforces required SIM-family coverage
- enforces probe override / SIM-tier consistency
- enforces head-term blocking rules from the admissibility hints

The same model can now:
- audit one active family slice
- emit one GraphML graph for that slice
- emit one Pydantic-derived JSON schema for that slice contract

## Verification

Local stack install:
- `.venv_spec_graph/bin/python -m pip install pydantic networkx lxml jsonschema`

Focused compile + tests:
- `.venv_spec_graph/bin/python -m py_compile system_v3/tools/a2_to_a1_family_slice_models.py system_v3/tools/audit_a2_to_a1_family_slice_pydantic.py system_v3/tools/export_a2_to_a1_family_slice_graph.py system_v3/tools/emit_a2_to_a1_family_slice_pydantic_schema.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- `.venv_spec_graph/bin/python -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`

Result:
- `Ran 3 tests ... OK`

Active family-slice audit:
- `.venv_spec_graph/bin/python system_v3/tools/audit_a2_to_a1_family_slice_pydantic.py --family-slice-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Observed result:
- `valid = true`
- `family_id = substrate_base_family`
- graph summary:
  - `node_count = 39`
  - `edge_count = 38`
  - `primary_target_count = 5`
  - `required_lane_count = 5`
  - `required_negative_class_count = 5`
  - `required_sim_family_count = 5`

Schema emit:
- `.venv_spec_graph/bin/python system_v3/tools/emit_a2_to_a1_family_slice_pydantic_schema.py --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

Manual-vs-Pydantic schema comparison:
- top-level property count:
  - manual draft = `41`
  - Pydantic-emitted = `41`
- difference:
  - `manual_only = []`
  - `pydantic_only = []`

## Important boundary

This is intentionally a local stack seam, not a live runtime dependency flip.

Why:
- the repo's default `python3` interpreter is still the Homebrew system interpreter
- `pydantic` was not safe to assume there without isolating it
- the new stack therefore lives under `.venv_spec_graph` for now

So this patch creates a real spec-object compiler substrate without silently breaking the current runtime path.

## Next seam

The next useful move is not “make the live runtime depend on Pydantic everywhere” yet.

The next useful move is:
- choose one bounded family-slice consumer
- let it optionally consume the local Pydantic loader/model
- and keep the default runtime path fail-closed and compatibility-safe until the interpreter boundary is decided

# A2_UPDATE_NOTE__A1_RUNTIME_RESET_AND_SPEC_OBJECT_DIRECTION__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the 2026-03-15 controller-thread reset on A1 runtime alignment, audit priorities, and spec-object direction without rewriting owner surfaces

## Scope

This note captures the bounded controller-thread conclusions reached after:
- re-reading the A1 doctrine and control-plane surfaces
- auditing the recent A1/runtime/control changes against those surfaces
- clarifying the intended A2 -> A1 -> A0/B/SIM shape with the user
- clarifying that the planning/context substrate problem is about structured ingest and compiled slices, not raw markdown reload

This note is a `DERIVED_A2` memory-preservation surface.
It does not itself promote canon or rewrite active owner summaries.

## Runtime provenance

- 2026-03-15 controller-thread audit and correction session in Codex desktop
- explicit user corrections during that session about:
  - A1 being non-conservative and branch-rich
  - graveyard-first validity pressure
  - B as the conservative fence
  - the need for A2 refinery over the whole system
  - the need for structured spec/object compilation instead of raw-doc reload

## Source anchors

Primary doctrine / owner surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/26_BOOTPACK_A1_WIGGLE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/33_A2_VS_A1_ROLE_SPLIT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_BRAIN_SLICE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_RESCUE_AND_GRAVEYARD_OPERATORS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_CONSOLIDATION_PREPACK_JOB__v1.md`

High-signal live runtime/control surfaces audited:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_request_to_codex_prompt.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_llm_lane_driver.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_sandbox_only_runner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

## A2_UPDATE_DELTA

### 1) The recent A1-specific runtime/control direction is not trustworthy as-is

The controller-thread audit concluded that earlier A1-specific work was built before the A1 doctrine was sufficiently read and internalized.

Consequence:
- A1-specific runtime/spec decisions made in that phase should be treated as suspect until re-audited against the real doctrine.
- Passing tests in those areas are not strong evidence of alignment if the tests only protect the scripted path.

### 2) The current executable A1 path still drifts from the documented family/cartridge model

Grounded A1 doctrine now read:
- A1 is family/cartridge-first, not flat-candidate-first
- family units include primary, alternatives, negatives, rescue, lineage, and SIM hooks
- graveyard is active workspace, not a sink
- graveyard-first validity is a real operating mode
- A1 starts from bounded A2 handoff, not raw repo mass or thread-memory vibes

Observed live drift:
- the active planner/runtime remains ladder-scripted
- fixed goal ladders and hardcoded probe terms still dominate the executable path
- controller wrappers and tests institutionalize that scripted shape

### 3) The main recent technical risk is phantom verification plus policy-imposing harness behavior

High-risk audit conclusions from the recent runtime/control set:
- `run_real_loop.py` can reconstruct missing outputs into PASS-looking compile/preflight/evidence/tape artifacts and then validate those reconstructions through the gate pipeline
- `run_real_loop.py`, `autoratchet.py`, and adjacent controller wrappers impose fixed profile/campaign shapes rather than acting as neutral controllers over bounded A2/A1 intent
- `run_a1_wiggle_control_cycle.py` advertises guardrail knobs it does not actually forward
- `build_a1_autoratchet_controller_result.py` can stop on generic semantic PASS without checking doctrinal family obligations
- `run_a1_autoratchet_cycle_audit.py` is too thin to prove family completeness or branch diversity

### 4) The user-corrected A1 operating model is materially broader than the currently scripted runtime

Controller-thread clarification preserved here:
- A1 is not supposed to be timid or overly conservative
- the A-side can branch aggressively, generate many candidate paths, and fill graveyard early
- B is the conservative fence
- nothing is valid merely by upper-loop wording; survival still depends on lower-loop/B/SIM pressure
- B begins from lexemes, terms, labels, math defs, and admissibility gates
- terms such as `density_matrix` should not be blindly preinstalled as preferred executable heads unless they are doctrinally staged or naturally reached by the branch process

This note preserves that correction as controller-facing understanding, not as earned lower-loop truth.

### 5) The A2 refinery idea remains correct, but the substrate must change

The controller-thread conclusion was not:
- abandon whole-system A2 refinery

It was:
- stop trying to make A2/A1/controller lanes reconstruct the system by rereading raw markdown mass every time

Direction preserved:
- markdown remains source
- the runtime-readable substrate should become structured spec/object data
- A2 should refine over that object/graph substrate
- A1 should receive bounded compiled slices from it

## A1_IMPACT_DELTA

- Do not treat prompt-thread wrappers as the definition of A1 runtime.
- Do not treat broad raw-doc loading as a valid substitute for bounded A2 -> A1 handoff.
- Do not treat scripted goal ladders as adequate proxies for family/cartridge campaigns.
- Preserve the distinction between:
  - scaffold/probe runs
  - graveyard-first validity runs
  - consolidation into one strict pre-A0 surface

## CONTROLLER_ARCHITECTURE_DIRECTION

The strongest controller-side direction preserved from the thread is:

1. Keep markdown as the authoring/source corpus.
2. Add a structured spec/object schema first.
3. Compile markdown into validated objects with explicit fields and provenance.
4. Build graph views and compiled slices from those objects.
5. Feed A2, A1, and controller lanes from compiled slices instead of raw-file reload.
6. Keep B/SIM as the conservative lower-loop truth fence.

Practical local-first stack direction preserved from the thread:
- `Pydantic`-style schema validation first
- canonical JSON object form first
- graph compilation/querying locally
- `NetworkX`-style graph work as the likely early substrate
- optional `GraphML` as export/interchange, not truth
- heavier graph/database tooling only if the lean local compiler outgrows file-based operation

Vector-search-only posture is explicitly not enough for this purpose.

## REWRITE_OR_REAUDIT_FIRST

Highest-priority reset/re-audit targets:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_request_to_codex_prompt.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_llm_lane_driver.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_sandbox_only_runner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Likely salvageable later, but not the first reset target:
- selector/admissibility bridge work
- warning/provenance cleanup
- SIM/save/report helper work
- some control-plane packaging/validation helpers

## UNRESOLVED_TENSIONS

- Some substrate-first ladders do appear in the doctrine, so not every occurrence of early QIT structure is drift. The real issue is hardcoded executable preference displacing bounded family generation and A2 handoff.
- The repo contains multiple overlapping A1/control stories:
  - doctrine/state surfaces
  - executable planner/runtime surfaces
  - prompt/worker/control-plane helper surfaces
  Clarifying authority and reload order remains necessary.
- A graph/spec-object compiler direction looks promising, but it is still a controller/intake direction, not yet an implemented owner-surface law.

## HOLD_OR_REVISIT

- Do not rewrite active owner surfaces from this note alone.
- Do not promote the graph/spec-object direction into standing system doctrine without a bounded implementation pass.
- Do not resume aggressive A1 runtime mutation until the reset targets above are re-audited against doctrine.

## Reload use

On future reload, this note should be read as:
- a preserved controller-thread reset packet
- a warning against trusting the recent scripted A1 runtime path at face value
- a reminder that the right next architectural seam is structured spec/object compilation feeding bounded A2/A1 slices

It should not be read as:
- earned lower-loop truth
- a replacement for the primary owner surfaces
- permission to skip the full doctrine/runtime comparison work

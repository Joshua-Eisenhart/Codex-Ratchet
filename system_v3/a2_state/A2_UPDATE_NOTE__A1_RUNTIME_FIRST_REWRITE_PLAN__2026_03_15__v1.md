# A2_UPDATE_NOTE__A1_RUNTIME_FIRST_REWRITE_PLAN__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the doctrine-grounded first rewrite plan for the highest-risk A1/runtime seams

## Scope

This note captures the first rewrite plan after the 2026-03-15 reset audit.

It is intentionally limited to the first three reset targets:
- `run_real_loop.py`
- `a1_adaptive_ratchet_planner.py`
- `autoratchet.py`

It does not mutate code.

## Source basis

Reset/audit notes:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_RUNTIME_RESET_AND_SPEC_OBJECT_DIRECTION__2026_03_15__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_RUNTIME_RESET_CLASSIFICATION__2026_03_15__v1.md`

Doctrine anchors:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_CONSOLIDATION_PREPACK_JOB__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`

Live targets:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`

## REWRITE_PLAN

### 1) `run_real_loop.py`

#### Current failure

`run_real_loop.py` currently mixes three incompatible roles:
- real runtime launcher
- artifact repair/synthesis tool
- final validation/gating wrapper

That leads to the main risk:
- missing runtime artifacts can be reconstructed into PASS-looking reports/evidence/tapes and then validated as if they were runtime-native outputs

#### Rewrite direction

Split the roles.

Keep:
- run-surface bootstrap
- explicit invocation of a runtime entrypoint
- final gate/sprawl invocation

Remove from the default success path:
- synthetic compile/preflight PASS reports
- synthetic events derived from ZIP headers
- synthetic SIM evidence packs
- fallback tape materialization

Replace with:
- strict missing-artifact detection
- explicit `MISSING_REQUIRED_RUNTIME_ARTIFACTS` style failure reporting
- optional separate repair/recovery tool if salvage of broken runs is still needed

#### Required new rule

Default `run_real_loop.py` behavior must be:
- if canonical runtime artifacts are missing, fail closed
- do not generate substitute artifacts and then pass them to the validator as if equivalent

#### Policy cleanup

Also remove the hardwired campaign policy from the wrapper:
- no forced `refined_fuel`
- no forced `interleaved`
- no forced `graveyard_first_then_recovery`
- no forced minimum `96`-step sweep

Controller/runtime intent should be passed in, not silently imposed here.

### 2) `a1_adaptive_ratchet_planner.py`

#### Current failure

The planner currently defines the active A1 path through hardcoded goal tuples and profile ladders.

That is too strong a replacement for:
- bounded A2 handoff
- family/cartridge campaign structure
- scaffold versus validity-mode distinction
- family-local admissibility judgment

#### Rewrite direction

Demote goal tuples from “the A1 runtime doctrine” to “seed libraries / optional scaffold profiles”.

The active planner input should become:
- one bounded A2-derived family slice or campaign slice
- with explicit target family, alternatives, negatives, rescue linkage, SIM hooks, and admissibility hints when available

The planner should then:
- materialize one bounded proposal campaign from that slice
- preserve branch diversity obligations
- emit explicit family lineage and admissibility structure
- stay proposal-only

#### Keep versus move

Likely keep:
- deterministic item assembly logic
- component/bootstrap helper handling
- SIM/probe token construction machinery
- some term-availability / component-gating helpers

Move out of the core path:
- fixed `CORE_GOALS`
- fixed `REFINED_FUEL_GOALS`
- fixed profile ladders as the main runtime chooser

Those can survive only as:
- explicit scaffold seed profiles
- or source-bound campaign presets

#### Required new rule

Planner success should be measured against:
- family completeness
- branch diversity
- rescue/negative presence
- admissibility placement

not just:
- whether the next ladder term was emitted cleanly

### 3) `autoratchet.py`

#### Current failure

`autoratchet.py` is acting as the main runtime orchestrator while still choosing campaign meaning through:
- goal profile
- required probe terms by profile
- debate strategy presets

That makes it a policy-defining engine instead of a neutral orchestrator over bounded campaign inputs.

#### Rewrite direction

Shrink `autoratchet.py` into a thinner orchestration wrapper.

Its job should be closer to:
- accept one explicit campaign/campaign-slice input
- run the deterministic lower path for a bounded number of steps
- preserve run-local reports
- stop with explicit reason

It should not be the place where the system decides:
- which concept family is the runtime truth
- which probe terms are required for a profile
- what the doctrinal family shape is

#### Keep versus move

Likely keep:
- run/root/bootstrap handling
- resume handling
- child-process orchestration
- run-summary reporting

Move out:
- `_required_probe_terms_for_profile(...)`
- profile-to-goal-family doctrine
- hardwired executable prioritization

#### Required new rule

If scaffold profiles are retained, they must be explicit scaffold modes.
Validity-mode campaigns should instead be driven by:
- explicit graveyard-first family inputs
- concept-local or source-bound campaign presets
- bounded consolidation/prepack outputs when relevant

## Suggested sequence

1. rewrite `run_real_loop.py` first to restore fail-closed runtime validation
2. rewrite `a1_adaptive_ratchet_planner.py` second so the active A1 planner stops defining doctrine through ladders
3. rewrite `autoratchet.py` third as a thinner orchestrator over explicit campaign inputs

## Guardrail

Do not try to fix these three simultaneously by adding more wrapper notes or more controller glue around the current path.

The rewrite should reduce doctrinal substitution, not hide it behind additional layers.

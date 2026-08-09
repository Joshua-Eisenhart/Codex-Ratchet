# CB PROJECT STATE

Generated from disk by `cb_project_state.py` at 2026-08-07T21:49:17Z.

**Generation-order caveat:** counts are as-of-generation. If a script or doc is written AFTER this file is generated, it is missing from these counts. `cb_build_handoff.py` regenerates this file as its first step so the package it builds is counted, but any file created after that step will be short by one. Regenerate to refresh.
Every number here is read off the filesystem at generation time. The previous handoff was typed from memory and four counts were wrong.

## What CB is (owner canon, verbatim)

> CB is a deterministic gating LLM constraint harness for mass looping
> swarms, of diverse llms, where the llms dont control their own gating.

> Constraint box is a constraint box. not a gate for truth. it gates the
> domain the right answers will be in and ones that are auditable.

Full rulings: `constraint_box/docs/OWNER_RULINGS_VERBATIM_20260806.md` — that file wins over any model summary, including this one.

## Repo facts

- branch `claimgate/bypass-regression` @ `6e362506a`, 224 dirty files, 10 worktrees
- `constraint_box/scripts/`: 30 .py (20 named cb_*)
- `constraint_box/docs/`: 51 .md
- `constraint_box/config/`: 8 .json
- `constraint_box/receipts/`: 171 .json
- **69 paths under constraint_box/ are UNTRACKED** — the estate exists on disk, not in git history

## Registries

- `council_member_registry_v1.json`: 72 entries
- `council_member_registry_skills_v1.json`: 59 entries
- `member_role_wave_v1.json`: 43 entries

**131 = the union of the two member registries, not one file.**

## Execution truth

From `member_role_wave_v1.json`, 43 member x role x wave units:

- EXEMPLIFIED: 21
- RUN_NOT_EXEMPLIFIED: 6
- NEVER_RUN: 16

`never_run=0` in the integrated-run receipts is a TEXT-PRESENCE measure, not execution. Real execution coverage is 21/43.

## Verified defects (each grep-able, none from memory)


## Self-tests, rerun at generation time

- `cb_light_integrations.py`: 19/19 rc=0
- `cb_light_tier2.py`: 21/21 rc=0
- `cb_control_laws.py`: 5/5 rc=0
- `cb_strategy_memory.py`: 6/6 rc=0

## Do NOT run

- `cb_loop.py --cycles 20` — bills 20 rounds of provider calls, and its third leg (autoresearch) has never executed.

## Scripts on disk

- `build_contained_core_bundle.py`
- `build_handoff_manifest.py`
- `cb_all_tools_council.py`
- `cb_autoresearch_loop.py`
- `cb_build_handoff.py`
- `cb_control_laws.py`
- `cb_integrated_run.py`
- `cb_lateral_heavy.py`
- `cb_lateral_wave.py`
- `cb_light_integrations.py`
- `cb_light_tier2.py`
- `cb_loop.py`
- `cb_multi_provider.py`
- `cb_project_state.py`
- `cb_run.py`
- `cb_run2.py`
- `cb_skill_premortem.py`
- `cb_strategy_memory.py`
- `cb_tiered_dispatch.py`
- `cb_wave_falsifier.py`
- `cb_wave_falsifier_v2.py`
- `cb_wave_falsifier_v3.py`
- `finalize_sim_registry.py`
- `index_external_validation_receipt.py`
- `run_contained_local_sim_product.py`
- `run_external_validation.py`
- `run_failure_rehearsal.py`
- `verify_attractor_basin_envelope.py`
- `verify_contained_core_bundle.py`
- `verify_wheel.py`

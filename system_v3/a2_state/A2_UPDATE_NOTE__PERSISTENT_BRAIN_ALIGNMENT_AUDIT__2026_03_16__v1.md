# A2_UPDATE_NOTE__PERSISTENT_BRAIN_ALIGNMENT_AUDIT__2026_03_16__v1
Status: ACTIVE CONTROL NOTE / NONCANON
Date: 2026-03-16
Role: bounded source-bound audit of whether current controller reload and active A2 memory discipline still align with the intended persistent-brain model

## Scope

This pass checked:
- active A2 owner/control surfaces
- current controller launch/reload surfaces
- canonical A2 persistence artifacts
- recent worker closeout sink usage
- current surface-count / sprawl pressure in `a2_state`, intake, and runs

This pass did not:
- rewrite the controller state record
- redesign the persistence contract
- mutate lower-loop runtime truth

## What was read

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/memory.jsonl`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/doc_index.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/fuel_queue.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_derived_indices_noncanonical/thread_seals.000.jsonl`

## Findings

1. The intended persistent-brain model remains the right model, but the live controller reload path is only partially using it.
2. The current weighted controller state remains centered on a March 13 worldview and still points `NEXT_ADMISSIBLE_W1` at the older Stage-1 worker launch path, so fresh controller reload does not recover the most current operational picture cleanly.
3. The live controller send-text companion reload path reads only a partial subset of the active A2 owner surfaces and also pulls in `work/CURRENT.md`, which means active controller context is still partly carried by helper/support surfaces instead of a freshly compressed layered owner-brain set.
4. The canonical persistence surfaces exist, but they are not acting as the main live semantic/control carrier:
   - `memory.jsonl` currently records autosave ticks rather than the recent semantic controller deltas
   - `doc_index.json` remains on a March 6 generation
   - `fuel_queue.json` is still in an older shape (`version`, `entries`) rather than the stronger current summary schema described in `07_A2_OPERATIONS_SPEC.md`
   - `thread_seals.000.jsonl` is effectively inactive for the current controller/worker loop
5. Surface sprawl remains materially real even after cleanup progress:
   - `system_v3/a2_state` now contains hundreds of files, including large note-stack and worker-support families
   - `system_v3/a2_high_entropy_intake_surface` remains much larger than the standing controller kernel, which is acceptable only if layer boundaries remain explicit and reload stays fail-closed
   - `system_v3/runs` remains bulky on disk
   - worker return / closeout staging remains materially populated
6. The closeout sink is useful and real, but recent worker deltas are being accumulated faster than they are being compressed back into the lean active A2-1 / controller kernel.

## Off-process flags

- `CONTROLLER_RELOAD_PARTIAL_BRAIN`
  - current controller reload depends on a stale weighted state plus partial overlays instead of a freshly compressed owner-brain set
- `CANONICAL_PERSISTENCE_NOT_PRIMARY_CONTEXT`
  - canonical A2 persistence artifacts exist, but they are not the primary carrier of current semantic/controller state
- `NOTE_STACK_AND_CLOSEOUT_ACCUMULATION_PRESSURE`
  - helper notes, update notes, and closeout packets are still accumulating faster than owner-surface consolidation
- `LAYERED_BRAIN_VS_SMALL_BRAIN_WORDING_RISK`
  - the real target is a layered A2 brain with a lean A2-1 kernel, not a globally tiny A2 memory surface

## A2 -> A1 impact

- Do not widen `A1` from current controller momentum alone.
- Keep `A1_QUEUE_STATUS: NO_WORK` as the default read unless one bounded controller-brain consolidation pass first refreshes the active owner/kernel surfaces.
- Prefer one controller-brain consolidation pass before any broader new A1 family opening.

## Safest next bounded correction

Run one controller-brain consolidation pass that:
- refreshes `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
- refreshes the current controller launch/send-text companion surfaces from the true owner-brain set
- explicitly records what is active owner-law versus helper/runtime/archive support across `A2-3`, `A2-2`, and `A2-1`
- compresses the recent closeout/update deltas into the lean current control kernel without pretending the whole A2 brain should collapse to that size

Do not respond to this finding with more broad worker spawning until that compression step is done.

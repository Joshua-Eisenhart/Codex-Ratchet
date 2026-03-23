# 27_MASTER_CONTROLLER_THREAD_PROCESS__v1
Status: ACTIVE / NONCANONICAL / CONTROLLER PROCESS SURFACE
Date: 2026-03-08
Purpose: define the master-controller role for fresh-thread worker dispatch, boot verification, artifact collection, and weak-lane correction.

## 1) Scope
This surface governs the controller thread that watches shared artifacts and decides when to spawn or correct fresh-thread worker lanes.

It does not:
- replace active A2-1 control memory
- replace deterministic A0 / B / SIM runtime logic
- force a fully fixed final architecture

This surface is provisional and should evolve from actual run pressure.

## 2) Core Framing
The controller is an entropy-routing and problem-routing role.

It should spawn or correct worker lanes when:
- entropy accumulates in shared surfaces
- a ratchet path plateaus
- one lane keeps failing or staying shallow
- a new large source drop appears
- a reduction/promotion queue is piling up

The controller should not spawn threads simply because parallelism is available.

## 3) Thread Model
Fresh threads are disposable worker lanes.
Shared repo artifacts are the persistent coordination and memory surface.

The controller thread:
- reads repo-held boot surfaces
- reads worker outputs
- decides the next dispatches
- keeps role separation explicit
- assumes workers are restartable and disposable

## 4) Stable Role Labels
Every fresh-thread worker prompt should begin with:
- `ROLE_LABEL`
- `ROLE_TYPE`
- `ROLE_SCOPE`

Preferred stable role labels:
- `Controller Master`
- `A2H Upgrade Docs`
- `A2H Archived State`
- `A2H Sims`
- `A2H Refined Fuel Non-Sims`
- `A2M Promotion Review`
- `A2M Contradiction Reprocess`
- `A1 Rosetta Bridge`
- `A1 Cartridge Judge`
- `A1 Strategy Audit`

Labels should describe role and scope, not temporary backlog state.

Dispatch surface rule:
- the controller may keep a worker dispatch packet `.md` as the repo-held controller record
- the controller must launch the worker from the matching raw prompt `.txt` surface, not by copy-pasting the wrapper packet body
- if both surfaces are not explicitly identifiable, dispatch is not yet ready

## 5) Controller Boot Inputs
The controller should be able to reboot from a small file set.

Minimum boot set:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`

When the bounded task is controller-backed `A1` launch preparation, the controller may additionally use the fixed subset-graph helper path:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/controller_helper_surfaces/FIRST_CONTROLLER_GRAPH_USE_CONTROLLER_CHECKLIST__2026_03_16__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/compile_first_controller_a1_launch_subset_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/refresh_first_controller_a1_launch_subset_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_first_controller_a1_launch_subset_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`

Timing/use rule for this helper path:
- use `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/controller_helper_surfaces/FIRST_CONTROLLER_GRAPH_USE_CONTROLLER_CHECKLIST__2026_03_16__v1.md` as the compact controller-facing checklist for this helper path so a fresh controller can reload the timing, entrypoint, audit-shape, and consult boundaries without hunting across tools
- use `refresh_first_controller_a1_launch_subset_graph.py` as the normal controller reload/pre-dispatch entrypoint, immediately before a decision that depends on the bounded first controller-mediated `A1` launch path
- after every `refresh`, run `audit_first_controller_a1_launch_subset_graph.py` before trusting the subset; if audit fails, treat the helper path as not ready and do not dispatch from it
- use `compile_first_controller_a1_launch_subset_graph.py` directly only for a cold build from explicit absolute source GraphML paths or when the wrapper defaults are intentionally not being used
- consult the compiled subset only for bounded dispatch/reload questions about whether the controller packet/handoff/spine and the `A1` packet/send-text/handoff/spine still cohere in one auditable slice
- require the bounded audit shape from the checklist before dispatch trust:
  - subset root `first_controller_a1_launch_subset`
  - `graph_count=9`
  - `compiled_from_count=9`
  - `artifact_bridge_count=43`
  - `queue_status_bridge_count=5`
- verify the dispatch-facing readiness fields remain visible before using the subset to support a dispatch decision:
  - controller node: `thread_class=A2_CONTROLLER`, `mode=CONTROLLER_ONLY`
  - controller spine: `launch_gate_status=LAUNCH_READY`
  - A1 launch spine: `launch_gate_status=LAUNCH_READY`
  - A1 launch packet: `queue_status=READY_FROM_NEW_A2_HANDOFF`, `target_a1_role=A1_PROPOSAL`, `go_on_budget=1`
  - A1 send-text companion: `read_path_count=7`
- preserve the live tension instead of smoothing it:
  - controller-side queue state may normalize to `NO_WORK`
  - A1 worker launch packet may normalize to `READY_FROM_NEW_A2_HANDOFF`
  - treat that as bounded decision support, not proof that dispatch already happened
- do not use this helper path as background maintenance, whole-repo indexing, general ontology, or graph-architecture work

## 6) Controller Boot Check
Before dispatching new work, the controller should confirm:
- active A2 control surfaces are readable
- intake ledger is readable
- current worker roles are identifiable from artifact locations or role labels
- no critical unresolved process break is blocking dispatch

If the dispatch decision depends on a ready `A1` queue artifact, the controller should also confirm:
- the first controller/A1 launch subset helper path is internally consistent for the current bounded graph slice
- ready `A1` queue status and launch packet artifacts expose family-slice validation requested mode, resolved mode, source, requested provenance, and resolved provenance when those fields are present

Minimal boot-check outputs:
- `boot_ok`
- `known_active_lanes`
- `strongest_recent_outputs`
- `weakest_lane`
- `spawn_recommendation`

## 7) Worker Classes
### A2-high workers
Role:
- doc-by-doc high-entropy intake
- bounded batch creation
- no active A2 mutation

Output:
- bounded intake batches under `a2_high_entropy_intake_surface`

### A2-mid workers
Role:
- refine existing intake batches
- selective promotion notes
- contradiction reprocess
- no direct A2-1 mutation unless explicitly requested

Output:
- refined batches or selective-promotion notes under `a2_high_entropy_intake_surface`

### A1 workers
Role:
- rosetta reformulation
- cartridge review
- strategy audit

Output:
- bounded A1 artifacts under `a1_state`

## 8) Spawn Triggers
The controller may spawn a fresh-thread worker when one of these is true:

### Entropy overload
- a new large doc or corpus drop appears
- intake batches accumulate faster than they are reduced
- contradiction clusters expand
- sims source material is present but underprocessed

### Ratchet plateau / problem state
- the same family keeps partial-passing without richer landing
- residue dominates movement
- route diversity keeps failing
- evidence boundaries remain muddy
- selector output stays too shallow or inconsistent

### Promotion pressure
- multiple strong A2-mid batches exist but no reduction note has been made
- strong A1 review outputs exist but no workflow uptake follows

## 9) Weak-Lane Correction Rule
The controller should not immediately spawn more threads when one lane is weak.

Correction order:
1. verify the lane is actually weak, not just early-stage
2. identify whether the failure is:
- shallow extraction
- packaging drift
- contradiction collapse
- selector-local judgment
- stalled source-map behavior
3. prefer one bounded correction prompt over creating another redundant lane

Example:
- if `A2H Sims` remains stuck at top-level source-map mode, the next move is a correction pass toward executable-family extraction, not a second sims thread

## 10) Artifact Collection Rule
The controller should evaluate outputs by:
- packaging completeness
- compression quality
- contradiction preservation
- downstream reuse value
- actual fit for promotion versus quarantine

The controller should prefer:
- strongest reusable artifacts
- weakest-lane diagnosis
- next bounded correction or promotion

over:
- broad narrative recaps
- parallelism for its own sake

## 11) Promotion Queue Rule
The controller should maintain a mental or repo-held queue of:
- strong reusable outputs
- quarantined warm outputs
- weak lanes needing correction
- candidates for selective promotion

This queue should be small and explicit.

## 11A) Regeneration Witness Rule
When a workflow is auditable only because transient memo state is still present, the controller should prefer:
- a compact regeneration witness
- or a run-anchor summary that records the latest memo -> cold-core -> strategy chain

The controller should not preserve large transient memo directories locally just to keep old runs replayable.

Preferred policy:
- `ACTIVE` runs may keep transient memo state while still live
- `ANCHOR` runs or anchor families should keep only a compact regeneration witness
- `ARCHIVED` runs should not require local transient memo workspaces

## 12) Bidirectional / Provisional Rule
Every layer is bidirectional.
Each layer may perform both induction and deduction on entropy.

This process surface is provisional.
Exact loop structure should be revised from actual run pressure and observed needs.

The controller should not freeze the architecture too early.

## 13) Preferred Output From Controller Turns
When operating as master controller, the thread should usually answer:
- strongest recent outputs
- weakest lane
- whether to spawn a new worker
- whether to correct an existing worker
- what bounded next step to take

## 14) Current Priority Bias
Current bias:
- prefer auditing existing lane outputs before spawning more threads
- prefer bounded correction of weak lanes over thread proliferation
- prefer artifact-held process over thread-memory process

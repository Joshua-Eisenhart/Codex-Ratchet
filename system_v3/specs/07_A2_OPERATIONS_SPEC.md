# A2 Operations Specification
Status: DRAFT / NONCANON
Date: 2026-03-07
Owner: `RQ-070..RQ-078`, `RQ-145..RQ-147`

## Role
A2 is system debug/upgrade/mining/orchestration memory layer.
This thread is operating in A2 function.

Schema-depth companion:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`

## Mining Function
A2 is the miner for:
- high-entropy docs
- prior thread transcripts
- failed-run artifacts

Mining outputs are structured fuel and explicit contradiction/risk records.

## Persistent Brain (`RQ-070`)
Canonical A2 persistent state lives under `system_v3/a2_state/`.

Required artifacts (fixed interface):
- append-only:
  - `system_v3/a2_state/memory.jsonl`
- registries (rewrite allowed; deterministic ordering required):
  - `system_v3/a2_state/doc_index.json`
  - `system_v3/a2_state/fuel_queue.json`
  - `system_v3/a2_state/rosetta.json` (noncanon overlay map; never overrides canon)
  - `system_v3/a2_state/constraint_surface.json` (derived snapshot; regenerable)
- active control/brain surfaces (human-readable; non-authoritative, but required for
  current A2-first operation and default active-path reload):
  - `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
  - `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
  - `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
  - `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
  - `system_v3/a2_state/INTENT_SUMMARY.md`
  - `system_v3/a2_state/MODEL_CONTEXT.md`
  - `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
  - `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
  - `system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md` (controller relaunch weighting surface)

Interpretation rule:
- `INTENT_SUMMARY.md` and `MODEL_CONTEXT.md` are not sufficient by themselves as the
  standing A2 brain.
- Active A2 persistence/load paths should preserve the full control/brain surface set
  above, not only the thin summary pair.
- `MODEL_CONTEXT.md` remains interpretive overlay and must not outrank source-bound
  A2 control surfaces.

Optional (non-required) A2 helper indices may live under `system_v3/a2_derived_indices_noncanonical/` as derived views
over the canonical A2 state (regenerable; bounded; never treated as canon inputs).

Optional derived index set (bounded; regenerable; noncanon):
- `system_v3/a2_derived_indices_noncanonical/brain_manifest.yaml` (pointers + hashes + shard map)
- `system_v3/a2_derived_indices_noncanonical/decisions.yaml` (extracted from `memory.jsonl` entries of type `decision`)
- `system_v3/a2_derived_indices_noncanonical/contradictions.yaml` (extracted from `memory.jsonl` + doc audits)
- `system_v3/a2_derived_indices_noncanonical/pending_actions.yaml` (extracted from `memory.jsonl` + open TODOs)
- `system_v3/a2_derived_indices_noncanonical/thread_seals.000.jsonl` (append-only seal cadence log; shardable)
- `system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl` (append-only worker closeout capture sink; shardable)

YAML usage:
- YAML is permitted above the kernel boundary for authoring/drafts (A2/A1).
- Canonical A2 state remains JSON/JSONL for deterministic hashing and stable tooling.

## Canonical Schemas (Summary)
`memory.jsonl` (append-only):
- one JSON object per line
- required keys: `ts` (ISO-8601 UTC), `type`, `content`
- optional keys: `source_paths[]`, `tags[]`, `run_id`, `state_hash`

`doc_index.json` (rewrite allowed; deterministic sort):
- required: `generated_utc`, `documents[]`
- document fields: `path`, `sha256`, `size_bytes`, `layer`
- deterministic ordering: sort `documents` by `path`

`fuel_queue.json` (rewrite allowed; deterministic ordering):
- required: `schema`, `generated_utc`, `entries[]`
- entry fields: `id`, `label`, `body`, `source_doc`, `concepts_needed[]`, `priority`

`rosetta.json` (rewrite allowed; overlay only):
- required: `schema`, `mappings{overlay_term: mapping}`
- mapping fields: `b_spec_id` (optional), `binds` (optional), `state` (optional)

`constraint_surface.json` (derived; regenerable):
- derived snapshot of failure patterns + graveyard summaries for A1/A2 use
- must not be treated as canon authority

## Contradiction Handling (`RQ-071`)
A2 must:
- preserve conflict pairs with source pointers
- mark unresolved items explicitly
- avoid forced narrative harmonization

## Upgrade and Debug Function (`RQ-072`)
A2 responsibilities:
- diagnose A1/A0/B/SIM failure patterns
- draft upgrade specs and deltas
- maintain boundary discipline across layers

## Lean Doc Interface (`RQ-073`)
Controls:
- fixed primary file interfaces
- append+shard logs
- bounded generated output areas
- archive separation for large artifacts

## Reversible Upgrade Discipline (`RQ-074`)
Upgrades must be:
- additive in versioned paths
- manifested
- rollback-capable by path switch

## Seal Cadence (`RQ-075`)
A2 must maintain:
- periodic thread seals
- seal triggers: scope completion, context risk, or batch milestone
- explicit pending-action queue update at seal time

## Delta Manifest Requirement (`RQ-076`)
Each upgrade set includes:
- changed files list
- requirement ids impacted
- unresolved gaps
- migration notes

## Model Declaration (`RQ-077`)
Each major task must record:
- active model
- reason for model choice
- boundary of expected outputs (spec/code/audit/run)

## Legacy Protection (`RQ-078`)
- legacy docs are read-only
- promotions occur only via new versioned spec sets
- no in-place rewrites of historical canon sources

## Controller Launch Packet (`RQ-145`)
Fresh `A2_CONTROLLER` relaunches must use one explicit launch packet that declares:
- model
- thread class
- mode
- primary corpus
- controller state record
- go-on count
- go-on budget
- stop rule
- dispatch rule
- initial bounded scope

Current launch packet surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`

## Controller Weighted State (`RQ-146`)
Fresh `A2_CONTROLLER` relaunches must recover weighted current truth from one small controller state record rather than inferring present priority from mixed execution history alone.

Minimum weighted state must include:
- primary corpus
- current primary lane
- current secondary lanes
- last valid `A2 -> A1` path
- current `A1` queue status
- next admissible worker dispatch
- disallowed next moves

Current weighted state surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`

Current machine-readable A1 queue companions may also be used as controller support surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`

When the current bounded dispatch path is the first controller-mediated `A1` launch, controller support may also include the fixed subset-graph helper path:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/compile_first_controller_a1_launch_subset_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_first_controller_a1_launch_subset_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_first_controller_a1_launch_subset_graph.py`

Operational timing rule for this helper path:
- use it only at controller reload or immediately before controller-backed `A1` dispatch when readiness depends on the bounded first-launch subset artifacts
- `refresh_first_controller_a1_launch_subset_graph.py` is the normal controller entrypoint and should be run immediately before the decision so the controller reads a regenerated bounded view instead of stale prior output
- `audit_first_controller_a1_launch_subset_graph.py` must run after every `refresh` and before the controller trusts the subset for dispatch/reload decisions; audit failure is fail-closed and means the helper path is not ready for use
- `compile_first_controller_a1_launch_subset_graph.py` is the low-level cold-build path for the fixed nine-GraphML subset and should be used directly only when the controller must build from explicit absolute source GraphML paths instead of the wrapper defaults
- the controller should consult the compiled subset only for bounded dispatch/reload questions about coherence of the controller-side and `A1`-side launch artifacts; it is not a general repo graph or graph-DB path

Readiness/provenance rule for this path:
- machine-readable `A1` queue status and launch packet companions must preserve family-slice validation as explicit fields, not implied success
- requested mode, resolved mode, validation source, requested provenance, and resolved provenance must remain inspectable on the ready artifacts when present
- current validators for this gate are:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`

## Dispatch-First Controller Rule (`RQ-147`)
`A2_CONTROLLER` is a routing/dispatch role first.

If substantive processing is needed and a bounded worker packet can express it, the controller must dispatch the worker instead of absorbing worker/refinery behavior itself.

For worker launch execution:
- the dispatch packet `.md` is the controller record and audit surface
- the raw prompt/send-text `.txt` is the operator launch surface
- controller/operator flow must not treat the wrapper packet markdown as the worker prompt body

Direct controller-side substantive work is limited to:
- weighted state refresh
- queue/readiness evaluation
- one bounded controller audit/evaluation pass
- launch/dispatch/closeout routing

## Active A2 Update Loop (working operational rule)
A2 must act as a recurring control-memory maintenance loop, not only as a mining store.

Primary triggers:
- new user correction or architectural clarification
- active `system_v3` doc change affecting meaning or process
- active tool/runner/contract change
- important run evidence
- discovery of process drift or contract drift
- before major new A1 work
- before broader runtime experimentation

Read order per loop:
1. current user correction / task signal
2. changed active system surfaces
3. changed tools/contracts
4. new run evidence
5. current active A2 control surfaces
6. A2->A1 handoff surface

Minimum outputs per loop:
- `A2_UPDATE_NOTE`
- append-safe A2 surface updates
- `A2_TO_A1_IMPACT_NOTE`
- `OFF_PROCESS_FLAGS` when applicable

Hard rules:
- no recency bias over authority
- no contradiction smoothing
- no direct jump from new input to A1/A0 without A2 distillation
- if A2 is stale relative to active system changes, broader work must pause

## Active Audit Loop (working operational rule)
The A2-side audit loop exists to test whether the system is obeying the A2-first process in real active paths.

Audit checks:
- A2 freshness versus active repo/runtime reality
- A2-first task initiation
- A1 traceability to refreshed A2
- ZIP/packet producer-validator agreement
- fail-closed boundary behavior
- proposal vs earned-state hygiene
- scaffold-vs-foundation drift
- repo-shape classification before mutation pressure

Repo-shape classification rule:
- every touched surface in an audit or cleanup/demotion task must first be classified as one of:
  - active system surface
  - active low-touch/reference surface
  - alias/migration scaffolding surface
  - `work/` legacy/test/prototype spillover surface
  - external archive/retention surface
- audits must not treat all of these as one generic cleanup class
- mutation permission depends on class:
  - active system surfaces: highest restraint; change only for bounded process/runtime/spec reasons
  - active low-touch/reference surfaces: preserve as law/reference unless a bounded alignment patch is needed
  - alias/migration scaffolding: classify first; do not infer missing active content from emptiness alone
  - `work/`: treat as prototype/test spillover, not as authoritative runtime/control memory by default
  - external archive: treat as retention/heat-dump, not as active runtime input by default

Audit implication:
- `AUDIT_SCOPE` should name which surface classes were touched
- `DRIFT_FLAGS` should include any case where a task treats archive, `work/`, alias scaffolding, and active surfaces as interchangeable

Required audit outputs:
- `AUDIT_SCOPE`
- `FINDINGS` or `NO_FINDINGS`
- `DRIFT_FLAGS`
- `REQUIRED_FIXES`
- `SAFE_TO_CONTINUE`

Severity model:
- `P1` = active-path boundary/process failure
- `P2` = contract drift or stale control surface likely to cause process failure
- `P3` = wording/coverage/audit-gap issue without active-path breakage

## Gating Rule (working operational rule)
Work must pause when any of the following are true:
- relevant A2 surfaces are stale
- a user correction has not been ingested into A2
- the active path has unresolved `P1`
- the active path has unresolved in-scope `P2`
- A1 work is not traceable to refreshed A2
- active packet/ZIP contract drift exists

Broader runtime work may proceed only when:
- relevant A2 surfaces are current
- the latest audit marks the path safe enough for the intended task
- the intended path remains within declared layer/process boundaries

## Fresh-Thread Controller / Worker Pattern (working operational rule)
The system may use many fresh bounded threads as disposable worker lanes when shared
repo artifacts, not conversational memory, carry the durable state.

Controller process companion:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- If this companion surface is present but untracked in the current workspace, treat it as a local overlay for controller operations rather than a guaranteed tracked baseline dependency.

Operational rule:
- fresh-thread workers are allowed for:
  - `A2-high` intake
  - `A2-mid` refinement
  - bounded `A1` rosetta / cartridge-review lanes
- deterministic `A0` / `B` / `SIM` remain primarily runtime/tool surfaces rather than
  chat-thread worker surfaces

Controller responsibilities:
- boot from repo-held control surfaces
- audit artifact outputs from active lanes
- decide when to spawn, correct, or stop worker lanes
- route entropy/problem states into bounded worker roles

Worker rule:
- each worker should be bootable from repo files alone
- each worker should write bounded artifacts to a shared surface
- each worker should be disposable after artifact emission

Current design stance:
- this controller/worker pattern is active and useful
- but still provisional, because exact bidirectional loop structure should continue to
  be revised from actual runs and observed needs

## Append-First Safety Guardrail (working operational rule)
Default posture for A2/doc/archive work:
- classify before mutating
- append before rewriting
- demote before deleting

Required implications:
- do not broadly rewrite active control docs to produce a cleaner story
- do not replace older user corrections or preserved contradictions with smoother restatements
- do not delete or demote system surfaces as part of ordinary cleanup pressure
- treat archive movement as reversible heat-dumping, not proof that a surface is dispensable

Allowed mutation order:
1. read and classify the relevant surfaces
2. append-save the new understanding, correction, or unresolved tension
3. audit whether the active path still depends on the candidate surface
4. only then consider bounded demotion or tighter consolidation
5. only after a successful without-it test may real deletion be considered

Goodhart guard:
- leaner appearance is not itself evidence of improvement
- stable operation without the demoted surface is partial evidence only
- in the absence of stable-system proof, prefer retained archive/demotion over deletion

## Low-Entropy A2 Kernel Boot Order (working operational rule)
Initial A2 kernel formation should begin from the lowest-entropy active system-law
surfaces, then expand outward.

Ordered read set:
1. `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
2. `system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ZIP_PROTOCOL_v2.md`
3. `system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
4. `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
5. `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
6. `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
7. `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
8. `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
9. `system_v3/a2_state/INTENT_SUMMARY.md`
10. `system_v3/a2_state/MODEL_CONTEXT.md`
11. `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`

Boot rule:
- do not begin from high-entropy thread material first
- do not begin from interpretive overlay first
- establish process law, boundary law, admission law, and active A2 control law before
  reading broader model overlay or thread-save material

Purpose:
- keep A2 from becoming thread-memory dependent
- make fresh-thread continuation possible from repo-held surfaces
- ensure the initial A2 kernel is constraint-led before it becomes expansive

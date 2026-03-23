# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_work_surface_residual_handoff_and_zipjob_refinery__v1`
Extraction mode: `RESIDUAL_HANDOFF_AND_ZIPJOB_REFINERY_PASS`

## C1) `CONTEXT_PACK_FAT_TO_LIGHT_TO_AUTO`
- source membership:
  - manual full context pack `00_READ_FIRST.md`
  - manual full `CONTEXT_PACK_INVENTORY.json`
  - manual run launcher
  - light pack `00_READ_FIRST.md`
  - light `CONTEXT_PACK_INVENTORY.json`
  - `STATE_INPUTS_NOTE.md`
  - auto-built lean `00_READ_FIRST.md`
  - auto-built lean `CONTEXT_PACK_INVENTORY.json`
- compressed read:
  - one context-pack family moves from a 89-file full packet to a 48-file light packet, then to an auto-built lean packet with the same inventory membership as the light variant
- reusable value:
  - useful pattern for deterministic Pro handoff slimming:
    - keep run order stable
    - slim the packet
    - preserve an inventory manifest

## C2) `SMALL_DELTA_WITH_PROCESS_FILTERING`
- source membership:
  - `PRO_THREAD_UPDATE_PACK__v5_SMALL/00_READ_FIRST.md`
  - `A2_BRAIN_v1__type_counts.json`
  - `A2_BRAIN_v1__filtered__no_SYSTEM_PROCESS.json`
- compressed read:
  - “small delta” packaging is being achieved partly by heavy type-based pruning of A2 state, especially by excluding `SYSTEM_PROCESS`
- reusable value:
  - useful pattern for distinguishing portable operator residue from process-heavy state exhaust

## C3) `ZIPJOB_TEMPLATE_TO_STRICT_DROPIN_LADDER`
- source membership:
  - Layer-1.5 v4 readme and manifest
  - layered extraction template v3 readme and manifest
  - layered extraction template realized manifest
  - strict drop-in v7_2_4 readme, runbook, and manifest
- compressed read:
  - the template family moves from scaffold contracts and generic topic placeholders toward stricter exact-path, exact-key, self-audit, and single-attachment drop-ins
- reusable value:
  - useful pattern for how a work-order template becomes a runnable ChatUI drop-in without giving up deterministic task order

## C4) `SANDBOX_BOUNDARY_AND_EXTERNAL_CLAW_DOCTRINE`
- source membership:
  - sandbox manifest
  - read-only violation report
  - handoff note 25
  - outbox alignment reply
  - refinery spec confirmation
- compressed read:
  - the sandbox lane establishes hard boundaries first, then converts zip-subagent ideas into an external-claw process with quarantine and validation
- reusable value:
  - useful pattern for safe prototype automation:
    - sandbox-only drafting
    - explicit violation capture
    - external hostile lane
    - internal validation before promotion

## C5) `NAMING_AND_INTERCHANGE_RECONCILIATION`
- source membership:
  - `ZIP_SUBAGENT_SYSTEM_v2_1__CONTROL_PLANE_ALIGNED__LONG_EXPLICIT_NAMING.md`
  - `MESSAGE_TO_CODEX__ZIP_SUBAGENT_ALIGNMENT.md`
  - `EXTRACT_TOPIC_v1/INSTRUCTIONS.md`
  - outbox alignment reply
- compressed read:
  - the older zip-subagent lane still mixes folder-per-topic outputs and shorter leaf names, while the later alignment lane demands long explicit names and flat-file ChatUI interchange
- reusable value:
  - useful pattern for tracking naming-contract convergence without erasing the earlier template logic

## Cross-Cluster Read
- `C1` and `C2` show how the residual lane tries to shrink external handoffs without losing too much operator context
- `C3` shows the corresponding hardening on the ZIP_JOB side:
  - more exact tasks
  - more exact outputs
  - more exact path and schema rules
- `C4` and `C5` show why the residue still matters:
  - the sandbox exchange records the doctrine that explains the later manifests
  - the naming/interchange surface is still visibly mid-migration rather than fully settled

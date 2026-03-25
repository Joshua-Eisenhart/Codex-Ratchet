# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / CLUSTERED INTAKE MAP
Batch: `BATCH_refinedfuel_thread_s_full_save_family__v1`
Extraction mode: `SAVE_KIT_PASS`

## Cluster C1: replay shell and integrity envelope
- members:
  - source 1
  - source 2
  - source 3
  - source 4
- cluster role:
  - defines what the kit is, how it should be read, what policy flags were live, and how file integrity is recorded
- strongest reusable read:
  - the family treats replayability as an artifact package with explicit sidecars, not as chat continuity

## Cluster C2: compact state census
- members:
  - source 5
- cluster role:
  - provides the short-form inventory of active axioms, math defs, term defs, and final counters
- strongest reusable read:
  - this is the quickest surface for reading the save-state scale:
    - `2` active axioms
    - `2` active math defs
    - `264` active term defs
    - `19` accepted batches

## Cluster C3: canonical replay container
- members:
  - source 8
- cluster role:
  - stores the portable single-container state image that Thread S is supposed to archive/replay
- strongest reusable read:
  - the snapshot is intentionally self-contained:
    - survivor ledger
    - park set
    - term registry
    - evidence pending
    - provenance

## Cluster C4: full-body expansion layer
- members:
  - source 7
  - source 6
- cluster role:
  - expands the compact snapshot into body-level declarations and a full term enumeration
- strongest reusable read:
  - the kit separates portable replay from verbose inspection:
    - snapshot for containment
    - dumps for audit/detail

## Cluster C5: quiet checkpoint markers
- members:
  - source 1
  - source 3
  - source 5
  - source 7
  - source 8
- cluster role:
  - marks this save as a low-noise checkpoint rather than an active unresolved campaign state
- strongest reusable read:
  - the family is especially clean because:
    - `PARK_SET` is empty
    - `EVIDENCE_PENDING` is empty
    - `STATE_CHANGE` is `NONE`
    - the unchanged-ledger streak is still `0`

## Cluster C6: archived authority boundary
- members:
  - source 1
  - source 3
  - source 4
  - source 8
- comparison anchors:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md:126-157`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md:56-85`
- cluster role:
  - preserves the gap between this older replay-kit packaging and the tighter current ZIP/tape transport model
- strongest reusable read:
  - the save kit is still valuable as lineage, but current transport doctrine and run-surface layout outrank it

# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archive_surface_deep_archive_root_milestone_split__v1`
Extraction mode: `ARCHIVE_DEEP_MILESTONE_ROOT_SPLIT_PASS`

## T1) Low-entropy milestone label vs high artifact volume
- source markers:
  - family counts
  - migrated subtree counts
- tension:
  - the family is labeled low-entropy and milestone-only
  - it still contains `7805` files across `183` directories, overwhelmingly in a migrated run-root tree
- preserved read:
  - milestone retention here is about selection class, not small size

## T2) Top-level snapshot zips vs migrated run-root dominance
- source markers:
  - top-level inventory
  - subtree counts
- tension:
  - three `system_v3` zips are visually prominent at the family root
  - almost all files live under `LEGACY__MIGRATED__FROM_RUN_ROOT`
- preserved read:
  - root appearance understates where the real archival mass sits

## T3) Milestone retention vs packaging noise
- source markers:
  - zip member listings
- tension:
  - these are deep-archive milestone snapshots
  - all three zips still retain `__MACOSX/*` and `.DS_Store` noise
- preserved read:
  - milestone status did not imply perfect archival hygiene

## T4) Snapshot-ladder breadth vs common structural skeleton
- source markers:
  - zip member counts and listings
- tension:
  - `system_v3.zip`, `system_v3 3.zip`, and `system_v3 2.zip` differ dramatically in member count
  - they still expose a shared top-level `system_v3/` skeleton
- preserved read:
  - preserve this as milestone-size drift over a recognizably continuous system frame

## T5) Run-history preservation vs current-state residue preservation
- source markers:
  - immediate subtree counts
- tension:
  - one branch preserves thousands of historical run files
  - another preserves only `27` current-state residue files
- preserved read:
  - the deep archive keeps both process history and quasi-live residue rather than choosing one retention mode

## T6) Compact registry summary vs huge unread run corpus
- source markers:
  - `_RUNS_REGISTRY.jsonl`
  - run subtree counts
- tension:
  - a `27`-line registry gives a compact run summary
  - the actual run subtree remains massive and unread at this stage
- preserved read:
  - the registry is useful as an index, but not a substitute for deeper run-family reads

# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_work_surface_shadow_systemv3_and_curated_wrappers__v1`
Extraction mode: `SHADOW_SYSTEMV3_DUPLICATE_AND_CURATED_WRAPPER_PASS`

## C1) `EXACT_ALIAS_SURFACES`
- source membership:
  - derived-index pair
  - public-facing-doc pair
  - conformance fixture pair
  - control-plane bundle pair
- compressed read:
  - multiple `work/system_v3` surfaces are duplicated byte-for-byte under different names
- reusable value:
  - strong duplicate-surface pattern:
    - different surface labels
    - same bytes
    - migration debt carried as directory aliasing rather than content change

## C2) `NEAR_LIVE_A2_STATE_MIRROR`
- source membership:
  - `a2_state`
  - `a2_persistent_context_and_memory_surface`
- compressed read:
  - the two trees are nearly the same, with drift confined to append-like files and incidental metadata
- reusable value:
  - useful pattern for identifying state mirrors that differ only by continued persistence activity

## C3) `FROZEN_RUNTIME_AND_TOOLING_SUBSETS`
- source membership:
  - `AUTOWIGGLE_README.md`
  - sandbox-only packet contract
  - extra `a1_wiggle_autopilot.py`
  - frozen runtime blocked-files inventory
  - runtime/tools equivalence counts
- compressed read:
  - the tooling surface is almost an exact duplicate of `tools/`, while the deterministic runtime surface is a reduced frozen subset of `runtime/` with one substantive autowiggle code divergence
- reusable value:
  - useful pattern for separating shadow “full alias” from shadow “frozen subset”

## C4) `CURATED_THREAD_WRAPPERS`
- source membership:
  - curated refinery/claw zip
  - curated mechanism-plus-upgrades zip
  - patched booted-run surface zip
- compressed read:
  - wrapper zips repackage the shadow tree into progressively broader Pro-thread understanding-transfer bundles
- reusable value:
  - useful packaging lineage:
    - narrow curated concept pack
    - broader mechanism-plus-upgrades pack
    - largest booted-run surface pack

## C5) `QUARANTINED_PROPOSED_DOCS`
- source membership:
  - quarantine `WORKSPACE_LAYOUT_v1.md`
  - quarantine `doc_index.json`
  - quarantine `index_v1.json`
- compressed read:
  - the quarantine snapshot is related to the later shadow tree but not byte-identical to it
- reusable value:
  - useful pre-shadow snapshot pattern for preserving alternate proposed surfaces without mutating the later tree

## Cross-Cluster Read
- `C1` and `C2` show two kinds of duplication:
  - exact aliasing
  - near-live mirror drift
- `C3` adds a third kind:
  - frozen subset duplication with selective divergence
- `C4` and `C5` show how those shadows travel:
  - out through curated wrappers
  - back to earlier or alternative proposals in quarantine

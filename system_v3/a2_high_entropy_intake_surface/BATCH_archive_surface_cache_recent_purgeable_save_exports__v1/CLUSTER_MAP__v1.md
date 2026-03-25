# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`
Extraction mode: `ARCHIVE_CACHE_SAVE_EXPORT_PASS`

## Cluster 1: Safe-Delete Policy Surface
- members:
  - `SAFE_TO_DELETE_NOW__20260224_071639Z.txt`
- cluster read:
  - this family is explicitly classified as removable cache, which is itself an important retention signal
- current usefulness:
  - strong archive witness of demotion depth and purgeability policy

## Cluster 2: Bootstrap Save Export Surface
- members:
  - `SYSTEM_SAVE__bootstrap__20260224_065046Z.zip`
  - `SYSTEM_SAVE__bootstrap__smoke.zip`
  - both detached `.sha256` sidecars
- cluster read:
  - bootstrap exports are a two-step near-duplicate pair with no run ids and only light packaging drift
- current usefulness:
  - useful historical witness of baseline save-profile export behavior

## Cluster 3: Debug Autoratchet Save Export Surface
- members:
  - `SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_065121Z.zip`
  - `SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_070148Z.zip`
  - `SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__smoke.zip`
  - three detached `.sha256` sidecars
- cluster read:
  - debug exports form a short revision ladder around one autoratchet debug run identity, with small `_CURRENT_*` state drift and a leaner smoke variant
- current usefulness:
  - high-value archive witness of near-live debug save export accretion

## Cluster 4: Detached Integrity Surface
- members:
  - all five `.sha256` sidecars
- cluster read:
  - integrity is preserved externally by one-line detached hashes rather than richer embedded provenance surfaces
- current usefulness:
  - useful archive signal of lightweight integrity practice in the purgeable cache tier

## Cluster 5: Broad Save-Profile Content Surface
- members:
  - internal zip member listings across all five exports
- cluster read:
  - even purgeable cache exports captured a broad `core_docs/` plus `system_v3/` save profile, including Thread-S full save contents and sim code
- current usefulness:
  - strong comparison point against later archive-derived extraction packages that retained only top-layer outputs

## Cluster 6: Revision-Drift Surface
- members:
  - cross-zip member-set and common-file comparisons
- cluster read:
  - most drift is confined to manifests, workspace layout, current-run markers, and current-state files rather than broad corpus change
- current usefulness:
  - useful lineage packet for save-export delta discipline and smoke-profile trimming

## Cluster 7: Deferred Next Family
- members:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`
- cluster read:
  - the next unread archive-root family moves from purgeable recent cache into low-entropy milestone retention
- current usefulness:
  - clear folder-order re-entry point for the next bounded archive intake

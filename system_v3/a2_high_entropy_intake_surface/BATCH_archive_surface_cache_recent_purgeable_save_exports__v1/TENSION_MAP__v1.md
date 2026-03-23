# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`
Extraction mode: `ARCHIVE_CACHE_SAVE_EXPORT_PASS`

## T1) Explicit deleteability vs rich retained contents
- source markers:
  - safe-delete marker
  - internal zip member listings
- tension:
  - the family is explicitly marked safe to delete now
  - the exports still retain broad `core_docs/`, Thread-S full save bodies, sims, and `system_v3/tools/*`
- preserved read:
  - cache-tier purgeability reflects retention policy, not triviality of content

## T2) Detached hash integrity vs thin provenance
- source markers:
  - `.sha256` sidecars
  - internal `SYSTEM_SAVE_PROFILE_MANIFEST_v1.json`
- tension:
  - every export has a detached checksum
  - integrity context stays external and minimal compared with richer internal provenance or ledger surfaces
- preserved read:
  - detached integrity exists here, but it is thinner than milestone-grade archival proof

## T3) Bootstrap timestamped vs smoke near-duplication
- source markers:
  - bootstrap pair member-set and common-file comparison
- tension:
  - bootstrap timestamped and smoke variants preserve the same member set and manifest file count
  - they still differ in the profile manifest and workspace layout
- preserved read:
  - smoke naming does not imply byte identity; it marks a light revision seam

## T4) Debug timestamp ladder vs narrow live-state drift
- source markers:
  - debug timestamped pair comparison
- tension:
  - the two timestamped debug exports preserve the same member set and profile scope
  - they still drift on manifest metadata plus `_CURRENT_RUN` and `_CURRENT_STATE` files
- preserved read:
  - debug save exports track near-live state rather than purely static corpus packaging

## T5) Debug smoke simplification vs lingering numbered state artifacts
- source markers:
  - debug late timestamp vs smoke comparison
- tension:
  - smoke implies a leaner simplified export
  - the preceding debug export still carried numbered `_CURRENT_STATE` files, and smoke drops exactly three of them
- preserved read:
  - the save profile was being cleaned up, but duplicate/current-state residue had not fully stabilized

## T6) Cache-tier recency vs archival retention
- source markers:
  - family path naming
  - safe-delete marker
- tension:
  - this family is labeled recent/high-entropy/purgeable
  - it is still retained inside the external archive tree
- preserved read:
  - the archive preserves not only milestones but also recent removable staging families as lineage evidence

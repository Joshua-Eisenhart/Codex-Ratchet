# Return Queue Status Card

**Date:** 2026-03-29  
**Purpose:** Compact controller card for what still remains live in `system_v4/thread_returns` after archive-only returns were moved out of the active queue.

---

## 1. Accepted Live Support

These returns remain live because they are already accepted in `EXTERNAL_SWARM_BATCH_01_INGEST.md` as direct controller support or `accepted_with_fence`.

- `RETURN__GEMINI_HIGH__AX0_OWNER_STACK_AUDIT__2026_03_29__v1.md`
- `RETURN__SONNET__AUTHORITY_INDEX_CROSSCHECK__2026_03_29__v1.md`
- `RETURN__GEMINI_LOW__THREAD_B_REGISTRY_CHECK__2026_03_29__v1.md`
- `RETURN__SONNET__THREAD_B_OVERREACH_HUNT__2026_03_29__v1.md`
- `RETURN__OPUS__AX1_AX4_CHAIN_ATTACK__2026_03_29__v1.md`
- `RETURN__GEMINI_FLASH__DOC_INVENTORY_CLUSTER__2026_03_29__v1.md`
- `RETURN__GEMINI_FLASH__CITATION_MAP_INVENTORY__2026_03_29__v1.md`

---

## 2. Live Partial Support

These returns remain live only as bounded pressure, inventory, or dissent surfaces. They should not be treated as controller-final guidance.
The partial queue intentionally retained here reflects controller-open cleanup and doctrine-pressure questions that have not yet been fully absorbed into current owner surfaces.

- `RETURN__GEMINI_LOW__DUPLICATE_FAMILY_AUDIT__2026_03_29__v1.md`
- `RETURN__SONNET__DUPLICATE_FAMILY_COLLAPSE_PLAN__2026_03_29__v1.md`
- `RETURN__GEMINI_FLASH__NAMING_DRIFT_CLUSTER_AUDIT__2026_03_29__v1.md`
- `RETURN__GEMINI_FLASH__THREAD_B_NAMING_DRIFT__2026_03_29__v1.md`
- `RETURN__GEMINI_HIGH__RIVAL_STACK_AUDIT__2026_03_29__v1.md`
- `RETURN__GEMINI_HIGH__OWNER_PACKET_GAP_HUNT__2026_03_29__v1.md`
- `RETURN__GEMINI_LOW__DOC_CLEANUP_AUDIT__2026_03_29__v1.md`
- `RETURN__OPUS__SIM_TO_DOCTRINE_MISMATCH_AUDIT__2026_03_29__v1.md`

---

## 3. Queue Rule

- `accepted` / `accepted_with_fence` rows stay live until their signal is fully absorbed into current owner or controller surfaces.
- `partial` rows stay live only while they provide bounded pressure not yet fully absorbed into current controller surfaces.
- `archive_only` rows belong in `system_v4/thread_archive/raw_returns`, not in `system_v4/thread_returns`.

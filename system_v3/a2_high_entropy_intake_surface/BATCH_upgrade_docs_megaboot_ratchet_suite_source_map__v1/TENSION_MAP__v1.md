# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_upgrade_docs_megaboot_ratchet_suite_source_map__v1`
Extraction mode: `SOURCE_MAP_PASS`

## T1) No separate `THREAD_S` / `THREAD_SIM` vs repeated `THREAD_S` / `THREAD_SIM` workflows
- source markers:
  - source 1: `20-21`
  - source 1: `67-89`
  - source 1: `301`
  - source 1: `388`
  - source 1: `475-476`
  - source 1: `634-642`
  - source 1: `706-707`
  - source 1: `846-851`
- tension:
  - top-level definitions remove separate `THREAD_S` and `THREAD_SIM`
  - later reboot/save/batching/bootpack sections repeatedly depend on them
- preserved read:
  - do not collapse this into one stable topology

## T2) Single-document canon vs embedded noncanon and human-guidance layers
- source markers:
  - source 1: `3`
  - source 1: `100-213`
  - source 1: `216-489`
  - source 1: `717`
- tension:
  - the document declares itself canonical
  - it embeds:
    - non-enforceable human roadmap/guidance
    - noncanon A1 bootpack
    - overlay/mining artifact doctrine
- preserved read:
  - the wrapper is canon-labeled, but its contents are authority-mixed

## T3) `THREAD_A0` topology vs `BOOTPACK_THREAD_A` naming and older `THREAD_A`/`THREAD_S` project steps
- source markers:
  - source 1: `15`
  - source 1: `474-476`
  - source 1: `497-504`
  - source 1: `775`
- tension:
  - the doc uses:
    - `THREAD_A0`
    - `THREAD_A`
    - `BOOTPACK_THREAD_A v2.62`
  - these are not presented as one clean naming family
- preserved read:
  - preserve the naming drift as source-local topology residue

## T4) B does not need megaboot knowledge vs megaboot as single authoritative document
- source markers:
  - source 1: `3`
  - source 1: `16`
  - source 1: `561-575`
- tension:
  - the megadoc claims single-document authority
  - it also explicitly states B does not load or interpret the megaboot and only loads `BOOTPACK_THREAD_B`
- preserved read:
  - megaboot-level authority and kernel-local authority are not the same thing here

## T5) Massive non-conservative exploration vs safe size guidance and single-container constraints
- source markers:
  - source 1: `25-31`
  - source 1: `332-373`
  - source 1: `379-410`
  - source 1: `533`
- tension:
  - the doc pushes large exploratory batching and anti-conservative behavior
  - it also imposes:
    - one-container messaging
    - size limits
    - linting
    - forensic replay discipline
- preserved read:
  - scale pressure and feed safety are both core values here

## T6) Direct legacy restore into B vs A0-mediated restore path
- source markers:
  - source 1: `66-98`
  - source 1: `567-575`
  - source 1: `656-662`
- tension:
  - early reboot kit allows direct snapshot paste into B
  - later restore doctrine prefers A0-mediated FULL+ restore
  - old-save upgrade keeps legacy direct paste as a conditional compatibility path
- preserved read:
  - the restore path is plural, not fully flattened into one method

## T7) Embedded Thread B duplicated with a real correction
- source markers:
  - source 1: `1092-2066`
  - source 1: `2068-3050`
- tension:
  - the embedded Thread B surface appears twice
  - second copy adds `"=" -> "equals_sign"` and closes correctly as Thread B
  - first copy closes with `END BOOTPACK_THREAD_S v1.64`
- preserved read:
  - this is not harmless duplication; it preserves a material correction and packaging residue

## T8) Sacred-heart axiom id vs Thread B namespace rule
- source markers:
  - source 1: `8-10`
  - source 1: `1143-1147`
  - source 1: `2123-2127`
- tension:
  - top-level sacred-heart definition includes `AXIOM_HYP N01_NONCOMMUTATION`
  - embedded Thread B namespace rules restrict AXIOM ids to `F*`, `W*`, `K*`, `M*`
- preserved read:
  - keep this as a real identifier-class tension inside the doc family

## T9) Graveyard/campaign tape owned by A0 vs owned by Thread S
- source markers:
  - source 1: `20`
  - source 1: `301`
  - source 1: `359`
  - source 1: `536-544`
- tension:
  - top-level topology collapses save/graveyard/packaging into A0
  - migration and tape sections still assign strong ownership to Thread S
- preserved read:
  - storage/orchestration ownership remains mixed

# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_root_spec_control_spine_drift_refresh__v1`
Extraction mode: `ACTIVE_CONTROL_SPINE_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## T1) `SOURCE_BOUND_FIRST_PASS_EXACTNESS_VS_LIVE_ACTIVE_SPEC_DRIFT`
- tension:
  - the earlier root/control-spine batch was source-bound and valid when created
  - six live members of that family now differ materially from the recorded snapshot
- preserve:
  - the older batch remains a historical snapshot
  - current reuse claims must follow live-source exactness, not merely batch existence

## T2) `TRACKED_BASELINE_STABILITY_VS_LOCAL_OVERLAY_AWARENESS`
- tension:
  - `specs/00_MANIFEST.md` still tries to enforce deterministic read order
  - the live file now explicitly admits tracked-baseline versus local-overlay variance for items `24..29` and supplements
- preserve:
  - deterministic read order remains the goal
  - overlay and supplement drift must stay explicit rather than being silently flattened

## T3) `THINNER_A1_MACRO_READ_VS_LIVE_PACKET_PROFILE_CONCRETION`
- tension:
  - the earlier first-pass packet saw A1 mainly as macro scheduler plus repair layer
  - the live `specs/05` surface now adds packet-profile, helper-summary, and admissibility detail
- preserve:
  - the A1 macro picture is still useful
  - live packet-shape doctrine is now denser and should not be omitted from current active reads

## T4) `OLDER_A2_OWNER_READ_VS_LIVE_A2_FRESHNESS_AND_AUDIT_LOOP`
- tension:
  - the earlier snapshot captured A2 as upstream control memory
  - the live `specs/07` surface now makes update-loop, audit-loop, repo-shape classification, and pause-when-stale rules explicit
- preserve:
  - the older read was not false
  - the live file now carries stronger operational consequences than the first-pass packet recorded

## T5) `THICKER_RUN_SURFACE_LAYOUT_VS_LEANER_PREVIOUS_FLOW_PACKET`
- tension:
  - the earlier `specs/08` read was a thinner loop-and-state-flow packet
  - the live file now contains concrete run paths, split state surfaces, and no-sprawl rules
- preserve:
  - the loop picture remains valid
  - the concrete filesystem contract is now part of the active read and not optional commentary

## T6) `STRICT_ZIP_MINIMALISM_VS_BROADER_SAVE_WITNESS_AND_ARCHIVE_OPERATIONS`
- tension:
  - the earlier control-spine packet already preserved a split between strict ZIP transport and broader save/tape doctrine
  - the live `specs/16` surface expands the broader operational side with witness retention, compaction, and archive demotion
- preserve:
  - the split remains real
  - the broader operational side is now thicker and more explicit than the earlier packet recorded

## T7) `NARROWER_OLD_A2_CANONICAL_INTERFACE_VS_LIVE_COMPATIBILITY_AND_SEAL_CONCRETION`
- tension:
  - the earlier packet preserved `specs/19` mainly as the narrow canonical schema/seal contract
  - the live file now includes current compatibility profile, registry detail, and deterministic refresh sequencing
- preserve:
  - narrower canonical interface language still matters
  - live compatibility and refresh-sequence detail now materially affect how operators read the file

## T8) `LATER_ACTIVE_LINEAGE_AUDITS_VS_OLDER_PARENT_SNAPSHOT_DEPENDENCE`
- tension:
  - later active-lineage audit and manifest-bridge packets remain useful
  - they still reference the older root/control-spine snapshot rather than this live refresh
- preserve:
  - those later packets are not invalidated automatically
  - they should not be mistaken for evidence that the old first-pass batch still source-matches the live repo

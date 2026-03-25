# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_refinedfuel_thread_s_full_save_family__v1`
Extraction mode: `SAVE_KIT_PASS`
Batch scope: next bounded non-sims refined-fuel subfolder in folder order; a bundled archive/replay kit extract from the `THREAD_S_FULL_SAVE` family
Date: 2026-03-08

## 1) Assigned Root Inventory
- root:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel`
- nontrivial top-level entry count:
  - `11`
- ignored filesystem noise:
  - `.DS_Store`
- folder order:
  - `AXES_MASTER_SPEC_v0.2.md`
  - `AXIS0_PHYSICS_BRIDGE_v0.1.md`
  - `AXIS0_SPEC_OPTIONS_v0.1.md`
  - `AXIS0_SPEC_OPTIONS_v0.2.md`
  - `AXIS0_SPEC_OPTIONS_v0.3.md`
  - `AXIS_FOUNDATION_COMPANION_v1.4.md`
  - `CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md`
  - `PHYSICS_FUEL_DIGEST_v1.0.md`
  - `THREAD_S_FULL_SAVE/`
  - `constraint ladder/`
  - `sims/`

## 2) Batch Selection
- selected bounded batch:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/README.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/PROVENANCE.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/REPORT_POLICY_STATE.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/SHA256SUMS.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/DUMP_INDEX.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/DUMP_TERMS.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/DUMP_LEDGER_BODIES.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/THREAD_S_SAVE_SNAPSHOT_v2.txt`
- reason for selection:
  - this is the first unprocessed non-`sims` bounded unit in folder order after the top-level refined-fuel docs
  - the folder is explicitly packaged as a single `Thread S Full Save Kit` rather than a loose note collection
  - all members share one `BOOT_ID` and timestamp:
    - `BOOTPACK_THREAD_B_v3.9.13`
    - `2026-02-04T09:54:24Z`
  - the family naturally bundles:
    - a canonical snapshot container
    - full survivor-ledger bodies
    - full term-registry dump
    - index/count surface
    - policy flags
    - provenance counters
    - integrity hashes
  - `SAVE_KIT_PASS` is the best fit because the main value is archive/replay packaging and portable state externalization, not term conflict or broad theory mapping
- deferred next doc in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/constraint ladder/AXIS_FUNCTION_ADMISSIBILITY_v1.md`

## 3) Source Membership
- source 1:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/README.md`
  - role in batch: family readme and explicit archive/replay intent statement
  - sha256: `4729f5845b5d281a84e1386897ad4e10bd120ce830c70103809f48e2be3fc9ca`
  - size bytes: `829`
  - line count: `21`
  - source class:
    - refined-fuel save-kit readme
- source 2:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/PROVENANCE.txt`
  - role in batch: compact counters/provenance sidecar
  - sha256: `05284c2f4c4e548b1b5032d90a104750fcfd1d3e61402b80a7e31b864f104618`
  - size bytes: `133`
  - line count: `7`
  - source class:
    - refined-fuel save-kit provenance sidecar
- source 3:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/REPORT_POLICY_STATE.txt`
  - role in batch: policy-flag sidecar for the save state
  - sha256: `c3c34a0ab63c2d2f933bf01511a6ccb5e2a3b464d50cb42b4a9c89c4b6dc84de`
  - size bytes: `351`
  - line count: `14`
  - source class:
    - refined-fuel save-kit policy surface
- source 4:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/SHA256SUMS.txt`
  - role in batch: per-file integrity hash list
  - sha256: `9c6b502df0f8a42dca6fed8a6fa9db0c8b29fd1ce9f226b02fef98917793f9a8`
  - size bytes: `594`
  - line count: `8`
  - source class:
    - refined-fuel save-kit integrity sidecar
- source 5:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/DUMP_INDEX.txt`
  - role in batch: compact census/index of axioms, specs, counts, and checkpoint totals
  - sha256: `76766947b22310fd360f67ab28d56d143a333bd2af2a208f7bb6d2cfa1d6ecb4`
  - size bytes: `12863`
  - line count: `283`
  - source class:
    - refined-fuel save-kit index surface
- source 6:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/DUMP_TERMS.txt`
  - role in batch: full term-registry enumeration
  - sha256: `2904b5054c3e24c78fb9cd9fc324630b2820b5b4ac46f5eb4420153b24d0fd41`
  - size bytes: `23416`
  - line count: `273`
  - source class:
    - refined-fuel save-kit term dump
- source 7:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/DUMP_LEDGER_BODIES.txt`
  - role in batch: full survivor-ledger-body dump with park-set body section
  - sha256: `a39182592658f96dbf2c90c2d71d693b06668cbab38066300749a2926367dd96`
  - size bytes: `85049`
  - line count: `1881`
  - source class:
    - refined-fuel save-kit ledger-body dump
- source 8:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/THREAD_S_SAVE_SNAPSHOT_v2.txt`
  - role in batch: canonical snapshot container for Thread-S-side replay of Thread-B state
  - sha256: `ac4bb0255175120ad3eadbcb227ee150984466fe3e3ad22306ca84540e898c8b`
  - size bytes: `108452`
  - line count: `2161`
  - source class:
    - refined-fuel save-kit canonical snapshot

## 4) Structural Map Of The Family
Source numbering below follows manifest order.

### Segment A: kit identity, member listing, and archive intent
- source anchors:
  - source 1: `1-20`
  - source 2: `1-6`
  - source 4: `1-7`
- source role:
  - declares the family as a single ZIP-style replay kit and identifies the sidecars needed to carry it
- strong markers:
  - `Thread S Full Save Kit`
  - `everything Thread S needs to archive/replay the current Thread B state`
  - canonical snapshot container
  - provenance counters
  - integrity hashes

### Segment B: compact census and checkpoint summary
- source anchors:
  - source 5: `1-14`
  - source 5: `279-282`
- source role:
  - gives the small summary view over active axioms, active math defs, active term defs, and checkpoint counters
- strong markers:
  - `AXIOM_HYP ACTIVE_COUNT 2`
  - `SPEC_HYP MATH_DEF ACTIVE_COUNT 2`
  - `SPEC_HYP TERM_DEF ACTIVE_COUNT 264`
  - `PARK_SET EMPTY`
  - `ACCEPTED_BATCH_COUNT 19`

### Segment C: canonical snapshot container
- source anchors:
  - source 8: `1-30`
  - source 8: `1877-1889`
  - source 8: `2151-2160`
- source role:
  - stores the replay-oriented portable snapshot with survivor ledger, park set, term registry, evidence pending, and provenance all in one container
- strong markers:
  - `BEGIN THREAD_S_SAVE_SNAPSHOT v2`
  - `SURVIVOR_LEDGER`
  - `PARK_SET`
  - `TERM_REGISTRY`
  - `EVIDENCE_PENDING`
  - `PROVENANCE`

### Segment D: full survivor-ledger body expansion
- source anchors:
  - source 7: `1-60`
  - source 7: `1877-1880`
- source role:
  - expands the admitted axioms and term-def bodies into their full structural declarations instead of the compact snapshot form
- strong markers:
  - `SURVIVOR_LEDGER_BODIES`
  - `S_PROBE_FND`
  - `S_AUTO_MD_ANCHOR`
  - `PARK_SET_BODIES`
  - `EMPTY`

### Segment E: term-registry enumeration
- source anchors:
  - source 6: `1-16`
  - source 6: `202-270`
- source role:
  - enumerates the full permitted term menu, including the large `auto_*` cluster bound to `S_AUTO_MD_ANCHOR`
- strong markers:
  - `TERM_REGISTRY`
  - `TERM syntax`
  - `TERM auto_simarchive`
  - `TERM auto_state`
  - `TERM auto_workerpool`

### Segment F: policy flags and quiet-state markers
- source anchors:
  - source 3: `1-13`
  - source 1: `18-20`
- source role:
  - states the save-time policy flag posture and the fact that park/evidence queues are empty in this checkpoint
- strong markers:
  - `ACTIVE_RULESET_SHA256_EMPTY TRUE`
  - `ACTIVE_MEGABOOT_SHA256_EMPTY TRUE`
  - `EQUALS_SIGN_CANONICAL_ALLOWED FALSE`
  - `DIGIT_SIGN_CANONICAL_ALLOWED FALSE`
  - `TERM_PERMITTED only`

## 5) Source-Class Read
- best classification:
  - refined-fuel archived save-kit / replay bundle family
  - artifact-based state externalization companion to the Thread-B family
- useful as:
  - lineage for portable snapshot design backed by sidecar dumps and integrity hashes
  - evidence that this snapshot captured a zero-park / zero-evidence-pending checkpoint
  - distinction between:
    - compact replay container
    - full ledger-body dump
    - full term dump
  - compact view of the large `auto_*` operational term menu without treating it as active law
- not best classified as:
  - active run-surface doctrine
  - lower-loop mutation authority
  - proof that the archived Thread-S replay kit still describes the current transport boundary
- possible downstream consequence:
  - later A2-mid reduction can reuse this family as lineage for artifact-chained continuity and sealed replay packaging, but active ZIP/tape transport law and archive-only boundaries must outrank any direct replay-authority reading from this old save kit

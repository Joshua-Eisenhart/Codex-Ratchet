# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_root_milestone_split__v1`
Extraction mode: `ARCHIVE_DEEP_MILESTONE_ROOT_SPLIT_PASS`
Batch scope: root split of `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY` without descending into the full migrated run-root corpus
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/system_v3.zip`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/system_v3 2.zip`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/system_v3 3.zip`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/_RUNS_REGISTRY.jsonl`
  - root inventory and immediate subtree counts for `LEGACY__MIGRATED__FROM_RUN_ROOT`
- reason for bounded family batch:
  - this is the next unread archive-root family in folder order after the purgeable cache tier
  - the family is too large to flatten into one pass, so this batch fixes the root topology first: three top-level milestone zips versus one migrated run-root subtree
  - keeping the batch at family-root scope preserves retention class, snapshot split, and migrated-run-root scale without pretending to have processed all `7805` files
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/system_v3.zip`
- sha256: `801961984392f4b98abed6bac24ab4dd6515772e4ca3ba06eb8b1871fba77b9a`
- size bytes: `5353245`
- container member count: `9424`
- source class: top-level milestone `system_v3` snapshot zip

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/system_v3 2.zip`
- sha256: `b48678f74fc8ca47eeaf337814846de570566c8e058fc3362eabb3d3340710f3`
- size bytes: `1712537`
- container member count: `1798`
- source class: smaller top-level milestone `system_v3` snapshot zip

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/system_v3 3.zip`
- sha256: `82c88f58853a61f5de3f6344c61d8c4cfd08e6849a6cb315303e66c49a151e47`
- size bytes: `2314382`
- container member count: `2652`
- source class: intermediate top-level milestone `system_v3` snapshot zip

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/_RUNS_REGISTRY.jsonl`
- sha256: `7cab6aa9ac70f04d09c2d9a2e24955cf018fc59c73e2c9da1099d994449bc96a`
- size bytes: `7771`
- line count: `27`
- source class: migrated run-root registry ledger

### Source 5
- path class: `family_root_inventory`
- observed top-level members:
  - `system_v3.zip`
  - `system_v3 2.zip`
  - `system_v3 3.zip`
  - `LEGACY__MIGRATED__FROM_RUN_ROOT`
  - `.DS_Store`
- source class: root split and packaging-noise inventory

## 3) Structural Map Of The Sources
### Segment A: deep-archive root split
- source anchors:
  - family-root inventory
- source role:
  - defines the root of the low-entropy milestone family as a split between three `system_v3` snapshot zips and one migrated run-root subtree
- strong markers:
  - total family scale: `7805` files / `183` directories
  - `LEGACY__MIGRATED__FROM_RUN_ROOT` holds `7801` files / `182` directories
  - the three top-level zips are milestone snapshots, not sidecars to the migrated subtree

### Segment B: milestone `system_v3` zip ladder
- source anchors:
  - sources 1-3 member listings
- source role:
  - preserves a three-step top-level snapshot ladder with sharply different size scales
- strong markers:
  - `system_v3.zip`: `9424` members / `5353245` bytes
  - `system_v3 3.zip`: `2652` members / `2314382` bytes
  - `system_v3 2.zip`: `1798` members / `1712537` bytes
  - all three expose the same high-level `system_v3/` skeleton: `tools`, `specs`, `runtime`, `a2_state`, `public_facing_docs`, `runs`, and related folders
  - all three also preserve packaging noise such as `__MACOSX/*` and `.DS_Store`

### Segment C: migrated run-root topology
- source anchors:
  - immediate subtree counts under `LEGACY__MIGRATED__FROM_RUN_ROOT`
- source role:
  - records how most of the deep archive is actually concentrated
- strong markers:
  - `bootpack_b_kernel_v1__runs__`: `7772` files / `178` directories
  - `bootpack_b_kernel_v1__current_state__`: `27` files / `0` directories
  - `bootpack_b_kernel_v1__runs___RESIDUAL__TEST_A1_PACKET_ZIP`: `1` file / `1` directory
  - this family is run-root heavy rather than snapshot-zip heavy

### Segment D: migrated run registry surface
- source anchors:
  - source 4: `_RUNS_REGISTRY.jsonl`
- source role:
  - preserves a compact summary of run outcomes without reading the full run directories yet
- strong markers:
  - `27` registry lines
  - visible runs include `TEST_DET_A`, `TEST_DET_B`, `TEST_A1_PACKET_ZIP`, `TEST_A1_PACKET_EMPTY`, and `TEST_STATE_TRANSITION_MUTATION`
  - early entries show stop reasons like `A2_OPERATOR_SET_EXHAUSTED`, `MAX_STEPS`, and `A1_NEEDS_EXTERNAL_STRATEGY`
  - run registry therefore acts as a milestone-index surface into the larger subtree

### Segment E: legacy run corpus content-class layer
- source anchors:
  - immediate subdir names under `bootpack_b_kernel_v1__runs__`
- source role:
  - shows the migrated run-root carries many named campaign/test families rather than one monolithic run
- strong markers:
  - named families include `RUN_FOUNDATION_BATCH_0001`, `RUN_QIT_AUTORATCHET_0001..0005`, `RUN_SIGNAL_0003..0005`, `RUN_SEMANTIC_SIM_0001`, `RUN_DENSITY_MATRIX_0001..0003`, `PHASEA_RESUME_001`, `GPT_ZIP_OPENAI_001`, and multiple `TEST_*` runs
  - zip-packet traffic is preserved inside the run tree
  - current-state residue is preserved alongside run history

## 4) Source-Class Read
- best classification:
  - deep-archive root topology batch for low-entropy milestone retention, showing snapshot-zips versus migrated run-root concentration
- useful as:
  - root map for how milestone retention was organized after migration
  - lineage evidence that most deep-archive mass lives in migrated run-root state, not in the top-level `system_v3` zips
  - bounded entry point for later milestone-run intake passes
- not best classified as:
  - current active runtime state
  - a single coherent doctrine bundle
  - full processing of the deep-archive family
- possible downstream consequence:
  - later archive passes should descend next into `LEGACY__MIGRATED__FROM_RUN_ROOT` as its own bounded family rather than treating the whole deep archive as one undifferentiated corpus

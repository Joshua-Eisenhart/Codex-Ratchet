# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_20260225T070252Z_root_split__v1`
Extraction mode: `ARCHIVE_HEAT_DUMPS_20260225T070252Z_ROOT_SPLIT_PASS`
Batch scope: archive-only intake of `HEAT_DUMPS/20260225T070252Z`, bounded to its immediate child families and nested archive-index signature only
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z`
  - immediate child families:
    - `RUN_ENGINE_ENTROPY_0001`
    - `repo_archive__moved_out_of_git`
  - nested archive signature:
    - `repo_archive__moved_out_of_git/ARCHIVE_INDEX_v1.json`
- reason for bounded family batch:
  - this pass classifies the timestamped heat dump as a root split and does not descend into either child family beyond inventory signatures
  - the archive value is structural: one sandbox-like engine-entropy residue family sits beside one much larger moved-out-of-git archive mirror
  - this object is useful for lineage because it preserves a second-order archive fork where prompt/memo heat and nested archive relocation coexist inside one timestamped dump
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/RUN_ENGINE_ENTROPY_0001`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z`
- source class: timestamped heat-dump root
- retained top-level entries:
  - `RUN_ENGINE_ENTROPY_0001`
  - `repo_archive__moved_out_of_git`
  - `.DS_Store`
- archive meaning:
  - this timestamped dump is itself a two-branch archive split, not a single coherent run root

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/RUN_ENGINE_ENTROPY_0001`
- source class: sandbox-like engine entropy residue family
- family markers:
  - file count: `2558`
  - directory count: `3`
  - retained child families:
    - `a1_sandbox__incoming_consumed`
    - `a1_sandbox__lawyer_memos`
    - `a1_sandbox__prompt_queue`
  - subtree counts:
    - `a1_sandbox__incoming_consumed`: `810` files
    - `a1_sandbox__lawyer_memos`: `810` files
    - `a1_sandbox__prompt_queue`: `938` files
  - naming signatures:
    - consumed/lawyer memo roles repeat:
      - `LENS_VN`
      - `LENS_MUTUAL_INFO`
      - `LENS_CONDITIONAL`
      - `LENS_THERMO_ANALOGY`
      - `DEVIL_CLASSICAL_SMUGGLER`
      - `RESCUER`
    - prompt queue adds:
      - `ROLE_7_PACK_SELECTOR`
- archive meaning:
  - this branch looks like high-volume A1 sandbox prompt/memo residue rather than a normal system run root

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git`
- source class: nested moved-out-of-git archive mirror
- family markers:
  - file count: `25056`
  - directory count: `1166`
  - retained top-level members:
    - `ARCHIVE_INDEX_v1.json`
    - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`
    - `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`
    - `HEAT_DUMPS`
    - `OPS_LOGS`
  - subtree counts:
    - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`: `25017` files / `1154` dirs
    - `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`: `30` files / `8` dirs
    - `HEAT_DUMPS`: `0` files / `0` dirs
    - `OPS_LOGS`: `7` files / `0` dirs
- archive meaning:
  - this branch is a nested archive mirror that already compresses a cache/deep-archive/ops-log taxonomy inside the larger heat dump

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/ARCHIVE_INDEX_v1.json`
- source class: nested archive checkpoint/index signature
- retained markers:
  - `schema ARCHIVE_INDEX_v1`
  - latest checkpoint:
    - `archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/CHECKPOINTS/SYSTEM_V3_A1_TUNING_20260225T011355Z`
  - recent heat dumps list length:
    - `10`
  - recent heat-dump entries are all archive-local relative paths under:
    - `archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/...`
- archive meaning:
  - the nested archive mirror carries its own checkpoint and recent-heat ledger, reinforcing that this timestamped dump embeds an already-organized external archive state

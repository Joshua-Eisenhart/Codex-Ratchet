# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_root_family_split__v1`
Extraction mode: `ARCHIVE_HEAT_DUMPS_ROOT_FAMILY_SPLIT_PASS`
Batch scope: archive-only intake of the top-level `HEAT_DUMPS` family, bounded to root inventory, representative demotion manifests, and top-level family signatures only
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS`
  - top-level family entries:
    - `20260225T070252Z`
    - `SYSTEM_V3__CURRENT_STATE_ROTATIONS__20260224T223517Z`
    - `SYSTEM_V3__CURRENT_STATE_ROTATIONS__20260224T223534Z`
    - `SYSTEM_V3__RUNS_OVER_2MB__20260224T224703Z`
    - `SYSTEM_V3__RUN_SAVE_EXPORTS__20260224T224330Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_01__20260308T205105Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_02A__20260308T205343Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_02B__20260308T205508Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_03__20260309T050608Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_04__20260308T235900Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_05__20260308T222429Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_06__20260309T054702Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_07__20260309T060500Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_09__20260309T070408Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_10__20260309T070854Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_11__20260309T071410Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_12__20260309T071701Z`
    - `SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z`
  - representative family docs:
    - all top-level `RUN_DEMOTION_MANIFEST__v1.md` files under `SYSTEM_V3__RUN_DEMOTION_BATCH_*`
- reason for bounded family batch:
  - this pass classifies `HEAT_DUMPS` as a root archive family and does not descend into any one subfamily beyond representative manifests and root signatures
  - the archive value is structural: recursive heat-dump nesting, current-state rotation residue, oversized-run retention, save-export duplication, and a 13-wave demotion ledger that explicitly moved raw runs out of the active tree after witness/anchor rewrites
  - this object is useful for lineage because it shows how older raw run surfaces were demoted from active runtime authority into external heat storage without being deleted
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS`
- source class: archive heat-dump root
- retained top-level entries:
  - `20260225T070252Z`
  - `SYSTEM_V3__CURRENT_STATE_ROTATIONS__20260224T223517Z`
  - `SYSTEM_V3__CURRENT_STATE_ROTATIONS__20260224T223534Z`
  - `SYSTEM_V3__RUNS_OVER_2MB__20260224T224703Z`
  - `SYSTEM_V3__RUN_SAVE_EXPORTS__20260224T224330Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_01__20260308T205105Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_02A__20260308T205343Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_02B__20260308T205508Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_03__20260309T050608Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_04__20260308T235900Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_05__20260308T222429Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_06__20260309T054702Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_07__20260309T060500Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_09__20260309T070408Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_10__20260309T070854Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_11__20260309T071410Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_12__20260309T071701Z`
  - `SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z`
- archive meaning:
  - `HEAT_DUMPS` is a multi-family retention surface, not one homogeneous run corpus

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z`
- source class: timestamped mega-dump family
- family markers:
  - file count: `27615`
  - directory count: `1171`
  - immediate children:
    - `RUN_ENGINE_ENTROPY_0001`
    - `repo_archive__moved_out_of_git`
  - `RUN_ENGINE_ENTROPY_0001` keeps sandbox-like subtrees:
    - `a1_sandbox__incoming_consumed`
    - `a1_sandbox__lawyer_memos`
    - `a1_sandbox__prompt_queue`
  - `repo_archive__moved_out_of_git` recursively contains:
    - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/...`
- archive meaning:
  - this is a recursive archive-of-archives heat dump with very high file density and nested moved-out-of-git residue

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__CURRENT_STATE_ROTATIONS__20260224T223517Z`
- source class: empty current-state rotation placeholder
- family markers:
  - file count: `0`
  - directory count: `0`
- archive meaning:
  - one rotation surface was created but retained no payload

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__CURRENT_STATE_ROTATIONS__20260224T223534Z`
- source class: loose-file current-state rotation snapshot
- family markers:
  - file count: `47`
  - directory count: `0`
  - visible file families:
    - `state 2.json` through `state 25.json`
    - `sequence_state 2.json` through `sequence_state 24.json`
- archive meaning:
  - this family preserves numbered loose-file state and sequence snapshots without enclosing manifest or run-root context

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUNS_OVER_2MB__20260224T224703Z`
- source class: oversized-run bucket
- family markers:
  - file count: `2912`
  - directory count: `42`
  - retained run families:
    - `RUN_QIT_EXTENDED_PROBEGATE_0001`
    - `RUN_QIT_EXTENDED_PROBEGATE_0002`
    - `RUN_QIT_FRONTIER_0001`
    - `RUN_QIT_FRONTIER_0002`
    - `RUN_QIT_REALSIM_0001`
    - `RUN_QIT_REALSIM_0002`
    - `RUN_QIT_TOOLKIT_LAWYERS_0002`
- archive meaning:
  - one heat-dump branch is explicitly size-based rather than doctrine-based

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_SAVE_EXPORTS__20260224T224330Z`
- source class: save-export micro-family
- family markers:
  - file count: `4`
  - directory count: `1`
  - retained under `_save_exports/`:
    - `SYSTEM_SAVE__bootstrap__smoke.zip`
    - `SYSTEM_SAVE__bootstrap__smoke.zip.sha256`
    - `SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__smoke.zip`
    - `SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__smoke.zip.sha256`
- archive meaning:
  - this branch mirrors a tiny save-export retention kit inside `HEAT_DUMPS`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_01__20260308T205105Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: first demotion-wave manifest
- manifest markers:
  - action: archive demotion by move only
  - deletion: none
  - moved runs:
    - `RUN_WIGGLE_REFINED_SMOKE_01`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0018`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0007`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0001`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0002`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0003`
  - explicit active keep set remains:
    - `_CURRENT_STATE`
    - `RUN_SUBSTRATE_FAMILY_EXCHANGE_SMOKE_0001`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_STRUCTURE_LOCAL_0004`
    - `RUN_DUAL_THREAD_NO_PRO_SMOKE_0004`
- archive meaning:
  - the first wave frames heat-dump storage as reversible demotion, not deletion, with an explicit keep-set split

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_02A__20260308T205343Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: second-wave safe-half manifest
- manifest markers:
  - action: archive demotion by move only
  - moved run families:
    - `RUN_DUAL_THREAD_NO_PRO_SMOKE_*`
    - `RUN_SUBSTRATE_FAMILY_EXCHANGE_SMOKE_*`
  - notes say this is the safer half of the second demotion wave
- archive meaning:
  - the demotion program split riskier and safer waves rather than moving all history at once

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_02B__20260308T205508Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: second-wave bridge-continuation manifest
- manifest markers:
  - moved runs are older bridge continuation/history runs
  - explicit retained local bridge runs remain:
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_PINNED_0001`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0036`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0010`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0031`
- archive meaning:
  - pinned and anchor-like continuation runs were explicitly spared while adjacent history runs were demoted

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_03__20260309T050608Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: doctrine-rewrite-gated manifest
- manifest markers:
  - purpose: stage the third run-demotion batch before moving manifest into external archive heat-dump folder
  - moved runs:
    - bridge executable cluster witnesses
    - entropy diversity broad and alias runs
  - explicit rewrite requirement:
    - multiple `system_v3/run_anchor_surface/` files must be rewritten to archive paths in the same bounded step
- archive meaning:
  - by batch 03, demotion is tightly coupled to archive-path rewrites of active anchor/witness surfaces

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_04__20260308T235900Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: normalized-anchor continuation manifest
- manifest markers:
  - purpose: demote rescue/continuation cluster after family-level doctrine was rewritten to normalized anchor and regeneration-witness surfaces
  - moved runs include:
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0008`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_PINNED_0001`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0010`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0031`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0036`
- archive meaning:
  - even previously pinned or continuation-heavy runs became archive-safe once normalized anchor/witness surfaces took over

### Source 12
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_05__20260308T222429Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: single-run move-with-witness-rewrite manifest
- manifest markers:
  - policy: move-with-witness-rewrite
  - moved run:
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0012`
- archive meaning:
  - the demotion mechanism also handles small single-run corrective waves

### Source 13
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_06__20260309T054702Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: single-run local-structure demotion manifest
- manifest markers:
  - type: archive demotion, not deletion
  - moved run:
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_STRUCTURE_LOCAL_0004`
  - move mode:
    - move-with-witness-rewrite
- archive meaning:
  - by batch 06, even a formerly local keep-set run becomes demotion-safe after witness rewrite

### Source 14
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_07__20260309T060500Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: residue-broad family demotion manifest
- manifest markers:
  - moved runs:
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RESIDUE_BROAD_0001`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RESIDUE_BROAD_0003`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RESIDUE_BROAD_0004`
  - note:
    - active doctrine was rewritten to residue-broad anchor/witness surfaces before this move
- archive meaning:
  - demotion lineage keeps broad-family residue while shifting active doctrine to normalized family surfaces

### Source 15
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_08__20260309T062522Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: local/broad pair demotion manifest
- manifest markers:
  - batch class: `HEAT_DUMP`
  - action: `move-with-witness-rewrite`
  - moved pair:
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_LOCAL_0001`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_BROAD_0001`
  - witness rewrite rule targets:
    - `RUN_ANCHOR__ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__v1.md`
    - `RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_LOCAL_BROAD_PAIR__v1.md`
- archive meaning:
  - paired local/broad families were explicitly collapsed into shared anchor/witness surfaces before demotion

### Source 16
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_09__20260309T070408Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: rate-family demotion manifest
- manifest markers:
  - batch class: `HEAT_DUMP`
  - moved runs include:
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001`
    - `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RATE_LIFT_BROAD_0001`
- archive meaning:
  - later demotion waves extend the same archive-path rewrite policy into entropy-rate families

### Source 17
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_10__20260309T070854Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: substrate-family demotion manifest
- manifest markers:
  - moved runs are substrate family exchange smoke runs
  - witness rewrite targets:
    - `RUN_ANCHOR__SUBSTRATE_FAMILY__v1.md`
    - `RUN_REGENERATION_WITNESS__SUBSTRATE_FAMILY__v1.md`
  - doctrine rewrite precondition references multiple active `a1_state` and `a2_state` surfaces
- archive meaning:
  - demotion later becomes coupled not just to run-anchor rewrites but also to doctrine-surface rewrites in active A1/A2 state

### Source 18
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_11__20260309T071410Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: substrate-enrichment demotion manifest
- manifest markers:
  - moved runs cover packet smoke, local, bridge, and continuation members of substrate-enrichment families
  - witness rewrite targets:
    - `RUN_ANCHOR__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`
    - `RUN_REGENERATION_WITNESS__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`
  - doctrine rewrite precondition references several active `a1_state` and `a2_state` surfaces
- archive meaning:
  - by batch 11, demotion is governed by family-anchor doctrine plus regeneration-witness continuity across multiple active surfaces

### Source 19
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_12__20260309T071701Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: entropy-structure family demotion manifest
- manifest markers:
  - moved runs cover local, patch, and seeded entropy-structure families
  - witness rewrite targets:
    - `RUN_ANCHOR__ENTROPY_STRUCTURE_FAMILY__v1.md`
    - `RUN_REGENERATION_WITNESS__ENTROPY_STRUCTURE_FAMILY__v1.md`
  - additional control-surface rewrite references active `A2_TO_A1_DISTILLATION_INPUTS`, `SIM_FAMILY_PROMOTION_AUDIT__ACTIVE_LANES`, and entropy graveyard topology surfaces
- archive meaning:
  - this wave explicitly ties archive demotion to archive-path rewrites inside active control surfaces, not just witness docs

### Source 20
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_DEMOTION_MANIFEST__v1.md`
- source class: packet-smoke and bookkeeping-bridge demotion manifest
- manifest markers:
  - moved runs cover:
    - `RUN_ENTROPY_BRIDGE_PACKET_SMOKE_*`
    - `RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_*`
  - witness rewrite targets:
    - `RUN_ANCHOR__ENTROPY_BRIDGE_PACKET_SMOKE_FAMILY__v1.md`
    - `RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_PACKET_SMOKE_FAMILY__v1.md`
    - `RUN_ANCHOR__ENTROPY_BOOKKEEPING_PACKET_SMOKE_FAMILY__v1.md`
    - `RUN_REGENERATION_WITNESS__ENTROPY_BOOKKEEPING_PACKET_SMOKE_FAMILY__v1.md`
  - note:
    - no extra A1/A2 raw-path rewrites were required because active doctrine already cited normalized family surfaces
- archive meaning:
  - the final visible wave shows the end state of demotion discipline: raw run paths can move once anchor/witness normalization is complete

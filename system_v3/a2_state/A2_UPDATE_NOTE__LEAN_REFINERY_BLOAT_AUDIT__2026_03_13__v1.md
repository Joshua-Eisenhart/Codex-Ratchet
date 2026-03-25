# A2_UPDATE_NOTE__LEAN_REFINERY_BLOAT_AUDIT__2026_03_13__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND A2 UPDATE
Date: 2026-03-13
Role: bounded A2 brain refresh for active-memory bloat and lean-refinery discipline

## AUDIT_SCOPE
- active `system_v3/a2_state` mass versus the refined fuel it is steering
- active owner-surface growth versus helper/update-note growth
- current A2 -> A1 handoff size pressure
- distinction between valid standing memory and refinery spillover

## SOURCE_ANCHORS
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/INTENT_SUMMARY.md`

## OBSERVED_SIZE_PRESSURE
- `system_v3/a2_state` is currently about `2.5M`
- `system_v3/a1_state` is currently about `500K`
- `core_docs/a1_refined_Ratchet Fuel` is currently about `1.8M`
- `core_docs/a2_feed_high entropy doc` is currently about `6.5M`
- top-level active A2 file count is currently `218`
- note pressure inside active A2 currently includes:
  - `45` `A2_UPDATE_NOTE__*`
  - `43` `A2_TO_A1_IMPACT_NOTE__*`
  - `22` `EXTERNAL_BOOT_COMPARATIVE_REFRESH__*`

## FINDINGS
1. The user correction is materially right: active A2 memory is now larger than the refined A1 fuel it is steering.
2. The main pressure is not the core standing registries alone. `memory.jsonl`, `fuel_queue.json`, and `doc_index.json` are legitimate standing state even when large.
3. The stronger bloat signal is active-mind reload pressure coming from:
   - repeated note/impact-note accumulation
   - large mixed execution ledgers
   - comparative refresh cascades remaining too close to the active brain
   - helper ingest surfaces remaining visible enough to compete with owner docs
   - owner surfaces carrying repeated refresh residue instead of only the smallest current rule set
4. This is not a call for broad deletion or broad demotion. It is a control-memory discipline issue first.

## LEAN_REFINERY_RULE
Separate these two functions explicitly:

- source extraction / refinery
  - may over-capture
  - may preserve wide comparison sets
  - may keep helper packets and intermediate notes

- active control memory
  - should be smaller than the refinery it steers
  - should preserve only current owner truth, unresolved tensions, and explicit deltas
  - should not mirror every intermediate comparison or same-level note pair

Operational consequence:
- a refinery pass may be broad
- the active A2 brain must remain narrow
- if the active A2 brain grows mainly by same-level note stacking, treat that as refinery spillover rather than healthy memory growth

## ACTIVE_MEMORY_CLASSIFICATION_READ
Keep as standing active memory:
- owner surfaces
- registries
- append-only memory sinks
- current weighted controller record

Treat as consolidation or archive-pressure candidates rather than default reload core:
- long same-day note chains
- repeated impact-note chains
- comparative refresh ladders once their consequence subset is already absorbed
- mixed execution ledgers used only as historical witness
- helper ingest surfaces that no longer add unique active control law

## CURRENT_CORRECTION
- future A2 updates should prefer owner-surface patching plus a small delta note over generating many adjacent same-scope notes
- A2 should remember current support-program context without reloading all support-program intermediate design surfaces
- A2 -> A1 should hand down owner surfaces plus named deltas, not diffuse note mass by default
- no broad archive/demotion mutation was performed in this pass

## SAFE_TO_CONTINUE
- yes for bounded owner-surface tightening
- yes for later consolidation planning
- no for broad deletion or broad active-surface demotion from this note alone

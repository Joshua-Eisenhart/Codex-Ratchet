# RUN_REGENERATION_WITNESS__SUBSTRATE_ENRICHMENT_FAMILY__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest memo -> cold-core -> selector witness for the substrate-enrichment family without preserving the full transient memo workspace

## Anchor Family

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_ENRICHMENT_FAMILY__v1.md`

## Why This Family

- the pass-2 substrate ladder is still cited across multiple active A1/A2 surfaces
- packet-side proof is important, but the family also has a clean memo -> cold-core -> selector chain
- the concept-local enrichment seed is the smallest retained run that still carries the family's exact four-term saturation read

## First Normalized Witness Instance

- instance id:
  - `SUBSTRATE_ENRICHMENT_FAMILY__INSTANCE_0003`
- source run:
  - `RUN_GRAVEYARD_VALIDITY_SUBSTRATE_ENRICH_LOCAL_0003`

### Normalized Retained Triple

- memo witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_11__20260309T071410Z/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_ENRICH_LOCAL_0003/reports/a1_external_memo_batch_driver_report.json`
  - witness meaning:
    - compact retained record that the concept-local enrichment seed ran through the memo/exchange path

- cold-core witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_11__20260309T071410Z/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_ENRICH_LOCAL_0003/a1_sandbox/cold_core/000004_A1_COLD_CORE_PROPOSALS_v1.json`
  - witness meaning:
    - retained proposal surface for the exact four-term enrichment family after family-local graveyard pressure

- strategy witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_11__20260309T071410Z/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_ENRICH_LOCAL_0003/a1_sandbox/outgoing/000004_A1_STRATEGY_v1__PACK_SELECTOR.json`
  - witness meaning:
    - retained selector output showing the same four-term family at the seed-saturation boundary

## Family-Level Retained Meaning

- packet-side proof already established:
  - `unitary_operator`
  - `commutator_operator`
- concept-local seed saturation preserves the exact enrichment-family quartet:
  - `unitary_operator`
  - `commutator_operator`
  - `hamiltonian_operator`
  - `lindblad_generator`
- later dynamics-local and cluster-clamped runs refine the family read, but are not needed to preserve the minimal regeneration chain

## Provenance Rule

- this witness is not full replay history
- it is the smallest retained chain needed to say:
  - memo-side pressure existed
  - cold-core proposals were formed
  - selector emitted a family-shaped strategy

## Local Retention Rule

- do not preserve broad transient memo churn locally for this family just to keep old proofs auditable
- preserve or distill only:
  - one memo witness
  - one cold-core witness
  - one strategy witness
  - this provenance note

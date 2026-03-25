# RUN_REGENERATION_WITNESS__ENTROPY_BOOKKEEPING_PACKET_SMOKE_FAMILY__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest packet-side witness chain for the entropy-bookkeeping packet-smoke family without preserving every packet artifact

## Anchor Family

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BOOKKEEPING_PACKET_SMOKE_FAMILY__v1.md`

## Why This Family

- active A1/A2 docs repeatedly cite the same narrow bookkeeping packet runs to make one family-level point
- this is a packet-first family, so the preferred memo -> cold-core -> selector witness shape from policy does not exist here
- the normalized retained witness is therefore one packet triple per live blocker class:
  - summary witness
  - lower-loop failure witness
  - state witness

## Normalized Retained Packet Instances

### ENTROPY_BOOKKEEPING_PACKET_SMOKE_FAMILY__INSTANCE_0002

- source run:
  - `RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0002`
- campaign summary witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0002/reports/autoratchet_campaign_summary.json`
  - witness meaning:
    - retains the narrow bookkeeping packet summary where `density_entropy` survives and helper leakage remains bounded
- lower-loop failure witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0002/b_reports/b_report_0002.txt`
  - witness meaning:
    - preserves the explicit `UNDEFINED_LEXEME:neumann` failure for `von_neumann_entropy`
- state witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0002/state.json`
  - witness meaning:
    - retains the end-state survivor set and counts for the first repaired bookkeeping packet pass

### ENTROPY_BOOKKEEPING_PACKET_SMOKE_FAMILY__INSTANCE_0003

- source run:
  - `RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0003`
- campaign summary witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0003/reports/autoratchet_campaign_summary.json`
  - witness meaning:
    - retains the narrow bookkeeping packet summary for the rate-side target
- lower-loop failure witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0003/b_reports/b_report_0002.txt`
  - witness meaning:
    - preserves the explicit `UNDEFINED_LEXEME:rate` failure for `entropy_production_rate`
- state witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0003/state.json`
  - witness meaning:
    - retains the end-state survivor set and counts for the rate-side bookkeeping probe

### ENTROPY_BOOKKEEPING_PACKET_SMOKE_FAMILY__INSTANCE_0004

- source run:
  - `RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0004`
- campaign summary witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0004/reports/autoratchet_campaign_summary.json`
  - witness meaning:
    - retains the colder bound-side packet summary with `density_entropy` still surviving
- lower-loop failure witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0004/b_reports/b_report_0002.txt`
  - witness meaning:
    - preserves the explicit `UNDEFINED_LEXEME:work` and related extraction debt for `information_work_extraction_bound`
- state witness:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BOOKKEEPING_BRIDGE_PACKET_SMOKE_0004/state.json`
  - witness meaning:
    - retains the end-state survivor set and counts for the colder bound-side bookkeeping probe

## Normalized Family Read

- across all retained instances, `density_entropy` is the only narrow bookkeeping seed that survives
- each attempted direct bookkeeping witness collapses on a different unresolved lexeme surface:
  - `neumann`
  - `rate`
  - `work`
- helper fragments survive, but they do not convert into honest narrow bookkeeping landing

## Provenance Rule

- this witness is not full replay history
- it is the smallest retained packet-side chain needed to say:
  - packet summary evidence existed
  - lower-loop failure evidence is preserved for each live blocker class
  - end-state survivors and counts are preserved

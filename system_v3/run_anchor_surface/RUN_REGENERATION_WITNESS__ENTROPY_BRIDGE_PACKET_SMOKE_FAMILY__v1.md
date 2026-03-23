# RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_PACKET_SMOKE_FAMILY__v1

## Status

- surface class: noncanonical anchor witness surface
- purpose: retain the smallest packet-side witness chain for the entropy-bridge packet-smoke family without preserving every packet artifact

## Anchor Family

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_PACKET_SMOKE_FAMILY__v1.md`

## Why This Family

- active A1/A2 docs repeatedly cite the same four local packet-smoke runs
- this is a packet-first family, so the preferred memo -> cold-core -> selector witness shape from policy does not exist here
- the normalized retained witness is therefore:
  - one compact campaign summary witness
  - one compact lower-loop failure witness
  - one state witness
  - one provenance note

## First Normalized Witness Instance

- instance id:
  - `ENTROPY_BRIDGE_PACKET_SMOKE_FAMILY__INSTANCE_0002`
- source run:
  - `RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0002`

### Normalized Retained Packet Triple

- campaign summary witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0002/reports/autoratchet_campaign_summary.json`
  - witness meaning:
    - strongest positive packet-side summary for the family, preserving the route where `correlation_polarity` still survives while bookkeeping pressure starts to spill

- lower-loop failure witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0002/b_reports/b_report_0003.txt`
  - witness meaning:
    - compact retained failure record that the bookkeeping side still collapses on `rate` with missing math/term/canon support

- state witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0002/state.json`
  - witness meaning:
    - retained end-state registry showing the surviving packet-side helper/bridge terms and the run-end counts

## Secondary Negative Closure Instance

- instance id:
  - `ENTROPY_BRIDGE_PACKET_SMOKE_FAMILY__INSTANCE_0004`
- source run:
  - `RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0004`

### Normalized Retained Packet Triple

- campaign summary witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0004/reports/autoratchet_campaign_summary.json`
  - witness meaning:
    - retained one-step summary showing the restored packet route still exists

- lower-loop failure witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0004/b_reports/b_report_0001.txt`
  - witness meaning:
    - compact retained failure record that `correlation_polarity` still collapses on `polarity`

- state witness:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0004/state.json`
  - witness meaning:
    - retained end-state registry showing only helper `correlation` survives and graveyard pressure does not grow

## Contradiction Note

- `RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0003` remains family-level negative evidence
- active doctrine currently describes that run as `correlation_polarity` failing on:
  - `UNDEFINED_LEXEME:polarity`
- the retained B-report at:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_13__20260309T072246Z/RUN_ENTROPY_BRIDGE_PACKET_SMOKE_0003/b_reports/b_report_0001.txt`
  currently records:
  - `UNDEFINED_LEXEME:correlation`
- preserve the contradiction; do not normalize it away until a later audit resolves which surface is the intended family read

## Normalized Family Read

- packet-side proof is real, but only on the correlation/helper side
- the strongest positive retained instance still keeps bookkeeping closed on `rate`
- the strongest late negative retained instance closes the route back down to helper `correlation`
- the family therefore supports narrow helper/bootstrap evidence, not narrow executable closure for `correlation_polarity` or the bookkeeping/bound terms

## Provenance Rule

- this witness is not full replay history
- it is the smallest retained packet-side chain needed to say:
  - packet summary evidence existed
  - lower-loop failure evidence is preserved
  - end-state survivors and counts are preserved

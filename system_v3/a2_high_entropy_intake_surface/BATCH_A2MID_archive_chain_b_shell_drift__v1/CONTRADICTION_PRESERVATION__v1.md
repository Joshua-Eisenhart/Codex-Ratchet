# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_chain_b_shell_drift__v1`
Date: 2026-03-09

## Preserved Contradictions
- contradiction 1:
  - summary, soak, and sequence counters count `3`
  - event ledger and canonical state preserve only `2` executed transitions
- contradiction 2:
  - the run is attributed to replay
  - summary also keeps `needs_real_llm true`
- contradiction 3:
  - the last visible executed event ends on `232c1595...`
  - summary/state bind final closure to `3ce0407f...`
- contradiction 4:
  - the queued third strategy packet is not executed
  - it uses the summary/state final hash as its input state
- contradiction 5:
  - step 2 advances both lanes to `S0002`
  - final survivor lineage advances only the alternative lane while the target remains at `S0001`
- contradiction 6:
  - the root carries mixed-suffix duplicate files and an empty `zip_packets 2/` directory shell
  - those artifacts do not become a distinct new execution surface or packet lane
- contradiction 7:
  - archived event rows still point to live-runtime paths
  - the retained packet bodies now live under the archive mirror

## Preservation Rule
- this batch keeps all contradictions above intact
- none of them are resolved into a clean three-step success story, a clean replay story, or a clean packaging story


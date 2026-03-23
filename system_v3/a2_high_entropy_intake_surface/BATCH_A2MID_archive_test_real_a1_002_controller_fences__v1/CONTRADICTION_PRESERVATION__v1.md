# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_real_a1_002_controller_fences__v1`
Date: 2026-03-09

## Preserved Contradictions
- contradiction 1:
  - the run is named `TEST_REAL_A1_002`
  - summary attributes the strategy source to replay and the inbox is empty
- contradiction 2:
  - the run retains a full two-step eight-packet lattice
  - `sequence_state.json` is absent
- contradiction 3:
  - step 1 ends on `7a249c9e...`
  - step 2 begins from `cc9ebfe4...`
- contradiction 4:
  - the last event ends on `7716a637...`
  - summary/state sidecar bind final closure to `b87bc843...`
- contradiction 5:
  - step 2 records `SCHEMA_FAIL`
  - the paired export leaves the target `NEGATIVE_CLASS` blank while the alternative still keeps `NEG_BOUNDARY`
- contradiction 6:
  - the second-step proposal advances both lanes to `S0002`
  - final survivor lineage advances only the alternative lane while the target remains at `S0001`
- contradiction 7:
  - summary and soak report zero parked packets and final state keeps `kill_log` empty
  - both SIM packets emit `NEG_NEG_BOUNDARY` and state still keeps `PARKED` promotion residue

## Preservation Rule
- this batch keeps all contradictions above intact
- none of them are resolved into one clean run story, causal story, or promotion story


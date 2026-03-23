# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
Date: 2026-03-09

## Cluster 1: Two-Step Clean Packet Lattice Without Queued Continuation
- archive meaning:
  - this run preserves a compact two-step execution with a balanced packet lattice and no queued third-step continuation
- bound evidence:
  - two `step_result` rows in `events.jsonl`
  - two packets each for `A0_TO_B`, `A1_TO_A0`, `B_TO_A0`, and `SIM_TO_A0`
  - summary and soak both report `accepted 7`, `rejected 1`, and `MAX_STEPS`
  - `a1_inbox/` is empty
- retained interpretation:
  - useful historical example of a small two-step run whose transport surfaces are mostly intact even though closure is not complete

## Cluster 2: Real-A1-Named Run With Replay Attribution
- archive meaning:
  - the run name suggests real-A1 lineage while the retained summary attributes the strategy source to replay
- bound evidence:
  - run id is `TEST_REAL_A1_002`
  - summary says `a1_source replay`
  - `needs_real_llm false`
  - inbox is empty
- retained interpretation:
  - useful naming-versus-lineage contradiction for archive history

## Cluster 3: Same Strategy Id Across Descending Step Families
- archive meaning:
  - both retained strategy packets share one `strategy_id`, but the proposed spec family descends from `PERTURBATION/T1_COMPOUND` to `BASELINE/T0_ATOM`
- bound evidence:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip` and `000002_A1_TO_A0_STRATEGY_ZIP.zip` both use `STRAT_000202`
  - step 1 proposes `S_SIM_TARGET_SIGMA_S0001` and `S_SIM_ALT_OMEGA_ALT_S0001` as `PERTURBATION` / `T1_COMPOUND`
  - step 2 proposes `S_SIM_TARGET_SIGMA_S0002` and `S_SIM_ALT_OMEGA_ALT_S0002` as `BASELINE` / `T0_ATOM`
- retained interpretation:
  - useful historical example of one retained strategy identity spanning multiple inner step regimes

## Cluster 4: Schema-Fail Second Step With Blank Target Negative Class
- archive meaning:
  - the second step records the only retained reject, and the paired export surface also preserves a blank target `NEGATIVE_CLASS`
- bound evidence:
  - step 2 in `events.jsonl` reports `rejected 1` with `reject_tags SCHEMA_FAIL`
  - `state.json` reject log keeps `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK`
  - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip` leaves `S_SIM_TARGET_SIGMA_S0002` target `NEGATIVE_CLASS` blank while the alternative still keeps `NEG_BOUNDARY`
- retained interpretation:
  - useful correlation surface for archive history, but not proof that the blank export field alone caused the reject

## Cluster 5: Hidden Hash Bridges Without Sequence Ledger
- archive meaning:
  - retained state lineage includes more transitions than the visible event ledger explains
- bound evidence:
  - step-1 event ends on `7a249c9e...`
  - step-2 strategy input and canonical previous hash are `cc9ebfe4...`
  - step-2 event ends on `7716a637...`
  - summary and sidecar bind the final state to `b87bc843...`
  - `sequence_state.json` is not retained
- retained interpretation:
  - useful archive evidence of hidden normalization or closure bridges between event rows and final state

## Cluster 6: Mixed `S0001` and `S0002` Survivor Lineage
- archive meaning:
  - the second-step proposal advances both target and alternative ids to `S0002`, but the retained final survivor set advances only the alternative lane
- bound evidence:
  - second strategy and second export both propose `S_SIM_TARGET_SIGMA_S0002` and `S_SIM_ALT_OMEGA_ALT_S0002`
  - second Thread-S snapshot and final state keep `S_SIM_ALT_OMEGA_ALT_S0002` but retain `S_SIM_TARGET_SIGMA_S0001` instead of `S_SIM_TARGET_SIGMA_S0002`
  - `000002_SIM_TO_A0_SIM_RESULT_ZIP.zip` also still reports `S_SIM_TARGET_SIGMA_S0001`
- retained interpretation:
  - useful archive seam where target lineage stalls while alternative lineage advances

## Cluster 7: Clean Packet Counters With Open Promotion and Kill Residue
- archive meaning:
  - packet-level park counts stay clean while semantic promotion and kill residue remain open
- bound evidence:
  - summary and soak report `parked_total 0`
  - state keeps `3` `PARKED` sim promotion states and `3` unresolved blockers
  - both retained SIM evidence packets emit `NEG_NEG_BOUNDARY`
  - final state keeps `kill_log` empty
- retained interpretation:
  - useful historical example of transport cleanliness diverging from semantic closure and final kill bookkeeping

# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_packet_zip_identity_residue__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `ARCHIVE_ONLY_MINIMAL_FOUR_LANE_PACKET_LOOP`
- candidate read:
  - `TEST_A1_PACKET_ZIP` should stay classified as an archive-only minimal packet-loop object:
    - one retained `A1_TO_A0`
    - one retained `A0_TO_B`
    - one retained `B_TO_A0`
    - one retained `SIM_TO_A0`
  rather than as active runtime proof or a clean success case
- why candidate:
  - this is the parent's clearest archive-role boundary
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary A`
  - `A2_3_DISTILLATES__v1.md:Distillate 1`
  - `CLUSTER_MAP__v1.md:Cluster 1`

## Candidate RC2: `SUMMARY_COLLAPSE_DOES_NOT_ERASE_ACCEPTED_STATE_AND_EVENT_RESIDUE`
- candidate read:
  - zeroed top-line counters:
    - `accepted_total 0`
    - zero unique digests
  should be preserved together with the deeper retained residue:
    - `accepted_batch_count 2`
    - two canonical ledger entries
    - three duplicated success rows
    - one schema-fail reject
    - three parked sim promotion states
- why candidate:
  - this is the parent's strongest bookkeeping-collapse contradiction
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary B`
  - `A2_3_DISTILLATES__v1.md:Distillate 2`
  - `CLUSTER_MAP__v1.md:Cluster 2`
  - `TENSION_MAP__v1.md:Tension 1`
  - `TENSION_MAP__v1.md:Tension 2`

## Candidate RC3: `ZEROED_SEQUENCE_LEDGER_DOES_NOT_NEGATE_VISIBLE_PACKET_LATTICE`
- candidate read:
  - the fully zeroed `sequence_state.json` should stay classified as flattened bookkeeping residue, not as proof that the visible A1, A0, B, and SIM packet lattice was absent
- why candidate:
  - this is the parent's cleanest packet-presence versus sequence-bookkeeping split
- parent dependencies:
  - `A2_3_DISTILLATES__v1.md:Distillate 4`
  - `CLUSTER_MAP__v1.md:Cluster 3`
  - `TENSION_MAP__v1.md:Tension 3`

## Candidate RC4: `SAME_NAME_STRATEGY_PACKET_SPLITS_BY_LOCATION_AND_VALIDITY`
- candidate read:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip` should stay modeled as a location-dependent packet family:
    - inbox and consumed copies are byte-identical to each other and schema-invalid
    - the transport-lane copy is larger, structurally richer, and tied to a different prior state hash
  so filename identity must not outrank retained byte and payload divergence
- why candidate:
  - this is the parent's sharpest packet-identity contradiction
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:Candidate Summary C`
  - `A2_3_DISTILLATES__v1.md:Distillate 3`
  - `CLUSTER_MAP__v1.md:Cluster 5`
  - `TENSION_MAP__v1.md:Tension 4`
  - `TENSION_MAP__v1.md:Tension 7`

## Candidate RC5: `DUPLICATED_EVENT_LEDGER_IS_INFLATED_NOT_LINEAR_EXECUTION`
- candidate read:
  - the event ledger should be preserved as inflated archive residue:
    - three identical success rows at step `1`
    - twenty-nine repeated schema-fail rows with one shared error string
  rather than retold as a clean linear step trace or a trustworthy accepted-count surface
- why candidate:
  - this is the parent's strongest single-step ledger-inflation rule
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 4`
  - `TENSION_MAP__v1.md:Tension 1`
  - `TENSION_MAP__v1.md:Tension 6`
  - `TENSION_MAP__v1.md:Tension 7`

## Candidate RC6: `ACCEPTED_PACKET_SPINE_AND_SCHEMA_FAIL_REGEN_OVERLAY_COEXIST`
- candidate read:
  - the retained export packet, Thread-S snapshot, and SIM result should stay visible as one accepted baseline spine, while the repeated schema-fail regeneration layer and reject log remain preserved as a later contradictory overlay at the same step
- why candidate:
  - this is the parent's narrowest usable execution-versus-fail overlay seam
- parent dependencies:
  - `A2_3_DISTILLATES__v1.md:Distillate 2`
  - `CLUSTER_MAP__v1.md:Cluster 6`
  - `CLUSTER_MAP__v1.md:Cluster 7`
  - `TENSION_MAP__v1.md:Tension 5`

## Quarantined Q1: `THREE_DUPLICATED_SUCCESS_ROWS_AS_PROOF_OF_SIX_REAL_ACCEPTED_ITEMS`
- quarantine read:
  - do not treat the three repeated success rows or their accepted total of `6` as proof that six distinct accepted items actually occurred
- why quarantined:
  - the parent explicitly preserves the ledger as duplicated step-1 inflation rather than a clean accepted-count authority surface
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 4`
  - `TENSION_MAP__v1.md:Tension 1`

## Quarantined Q2: `SAME_FILENAME_AS_CANONICAL_SAME_PACKET_IDENTITY`
- quarantine read:
  - do not collapse inbox, consumed, and transport copies into one canonical packet just because they share the same filename and sequence
- why quarantined:
  - the parent explicitly preserves different hashes, sizes, validity states, and payload structures across locations
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 5`
  - `TENSION_MAP__v1.md:Tension 4`

## Quarantined Q3: `ZEROED_COUNTERS_AS_PROOF_THAT_NO_PACKET_LOOP_OR_ACCEPTED_WORK_EXISTED`
- quarantine read:
  - do not let zeroed sequence counters or zeroed summary accepted counters erase the visibly retained packet loop, state residue, or accepted packet spine
- why quarantined:
  - the parent explicitly preserves nonzero deeper packet and state structure beneath those collapsed counters
- parent dependencies:
  - `CLUSTER_MAP__v1.md:Cluster 2`
  - `CLUSTER_MAP__v1.md:Cluster 3`
  - `TENSION_MAP__v1.md:Tension 1`
  - `TENSION_MAP__v1.md:Tension 3`


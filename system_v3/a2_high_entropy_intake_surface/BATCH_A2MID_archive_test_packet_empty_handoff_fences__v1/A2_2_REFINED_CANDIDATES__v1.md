# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `ARCHIVE_ONLY_MINIMAL_A0_TO_A1_BOUNDARY_STUB`
- candidate read:
  - `TEST_A1_PACKET_EMPTY` should stay classified as an archive-only minimal A0-to-A1 boundary stub rather than as a substantive execution run or active runtime reference
- why candidate:
  - this is the parent packet's clearest archive-role rule
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate Summary A`
  - `A2_3_DISTILLATES__v1:Distillate 1`
  - `CLUSTER_MAP__v1:Cluster 1`

## Candidate RC2: `ONE_HASH_ALIGNMENT_IS_REAL_BUT_LOW_INFORMATION`
- candidate read:
  - the aligned final hash across summary, state, sidecar, and the only event row should be kept as real integrity evidence
  while also being kept low-information because nothing progressed beyond the initial request boundary
- why candidate:
  - this is the parent packet's strongest integrity-without-closure rule
- parent dependencies:
  - `A2_3_DISTILLATES__v1:Distillate 2`
  - `CLUSTER_MAP__v1:Cluster 2`
  - `TENSION_MAP__v1:Tension 4`

## Candidate RC3: `REQUEST_ONLY_HANDOFF_WITH_EMPTY_DOWNSTREAM_RECEIPT`
- candidate read:
  - the run preserves a request-only handoff state:
    - one `a1_strategy_request_emitted` event
    - `A1` sequence still `0`
    - empty `a1_inbox/`
    - stop reason `A1_NEEDS_EXTERNAL_STRATEGY`
  and this should stay distinct from any partially completed strategy cycle
- why candidate:
  - this is the parent packet's main boundary-failure signature
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate Summary B`
  - `A2_3_DISTILLATES__v1:Distillate 3`
  - `CLUSTER_MAP__v1:Cluster 3`
  - `TENSION_MAP__v1:Tension 1`
  - `TENSION_MAP__v1:Tension 2`

## Candidate RC4: `SAVED_STRATEGY_SKELETON_IS_INTENT_NOT_EXECUTED_WORK`
- candidate read:
  - the lone `A0_TO_A1_SAVE_ZIP` should be preserved as intended downstream structure:
    - one baseline target
    - one negative alternative
    - explicit operator ids
  but not retold as evidence that downstream A1, B, or SIM work actually occurred
- why candidate:
  - this keeps the strongest nonempty structure from the parent without collapsing the boundary failure
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster 4`
  - `TENSION_MAP__v1:Tension 3`
  - `TENSION_MAP__v1:Tension 7`

## Candidate RC5: `SEED_VOCABULARY_AND_SURVIVORS_ARE_PRELOADED_NOT_EARNED_RUNTIME`
- candidate read:
  - the preserved `47` derived-only terms, `19` L0 lexemes, and survivor pair:
    - `F01_FINITUDE`
    - `N01_NONCOMMUTATION`
  should stay classified as conceptual seed residue rather than earned runtime structure because all live execution registries remain empty
- why candidate:
  - this is the parent packet's clearest seed-versus-runtime split
- parent dependencies:
  - `A2_2_CANDIDATE_SUMMARIES__v1:Candidate Summary C`
  - `A2_3_DISTILLATES__v1:Distillate 4`
  - `CLUSTER_MAP__v1:Cluster 5`
  - `TENSION_MAP__v1:Tension 5`

## Candidate RC6: `DUPLICATE_EMPTY_PACKET_DIRECTORY_IS_PACKAGING_NOISE_ONLY`
- candidate read:
  - the real transport account stays anchored to `zip_packets/`, while `zip_packets 2/` remains packaging residue only and should not be upgraded into a second packet lane
- why candidate:
  - this preserves the parent packet's clearest packaging-noise fence
- parent dependencies:
  - `A2_3_DISTILLATES__v1:Distillate 5`
  - `CLUSTER_MAP__v1:Cluster 6`
  - `CLUSTER_MAP__v1:Cluster 7`
  - `TENSION_MAP__v1:Tension 6`

## Quarantined Q1: `A1_SOURCE_PACKET_AS_PROOF_OF_RECEIVED_A1_PACKET`
- quarantine read:
  - do not treat summary field `a1_source packet` as proof that an A1 packet was actually received or consumed
- why quarantined:
  - the parent packet explicitly preserves empty inbox, zero A1 sequence, and request-only stopping
- parent dependencies:
  - `TENSION_MAP__v1:Tension 1`
  - `TENSION_MAP__v1:Tension 2`

## Quarantined Q2: `PLACEHOLDER_HASHED_SAVE_PACKET_AS_TRUSTED_PROVENANCE`
- quarantine read:
  - do not treat the lone save packet's repeated placeholder hashes as trusted runtime provenance
- why quarantined:
  - the parent packet explicitly marks the packet as structurally concrete but provenance-weak
- parent dependencies:
  - `TENSION_MAP__v1:Tension 7`
  - `CLUSTER_MAP__v1:Cluster 4`

## Quarantined Q3: `CLEAN_HASH_ALIGNMENT_AS_SUBSTANTIVE_COMPLETION`
- quarantine read:
  - do not read the clean final-hash alignment as proof of substantive run completeness
- why quarantined:
  - the parent packet explicitly says the alignment is real because almost nothing happened
- parent dependencies:
  - `TENSION_MAP__v1:Tension 4`
  - `CLUSTER_MAP__v1:Cluster 2`

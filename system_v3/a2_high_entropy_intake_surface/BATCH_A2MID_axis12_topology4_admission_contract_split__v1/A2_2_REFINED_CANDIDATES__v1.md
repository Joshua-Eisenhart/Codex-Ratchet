# A2-2 REFINED CANDIDATES

## Candidate 1: AXIS12_TOPOLOGY4_SEAM_SHELL

- status: `A2_2_CANDIDATE`
- type: `residual paired-family shell`
- claim:
  - the bounded family is the seam between a current local topology4 channelfamily runner surface and a directly admitted repo-top terrain8 surface selected under the same runner hash
- source lineage:
  - parent batch: `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1`
  - parent basis: cluster A, distillates D1 and D5, candidates C1-C3
- retained boundary:
  - do not absorb the next `channelgrid` pair into this shell

## Candidate 2: DIRECT_TERRAIN8_ADMISSION_WITHOUT_LOCAL_SIMID_ADMISSION

- status: `A2_2_CANDIDATE`
- type: `admission seam packet`
- claim:
  - repo-top evidence directly admits `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1` under the current runner hash while the current local channelfamily SIM_ID remains omitted from top-level admission
- source lineage:
  - parent basis: cluster D, tension T1, distillate D4, candidate C4
- retained contradiction marker:
  - exact admission survives
  - present local SIM_ID admission does not

## Candidate 3: CHANNELFAMILY_VS_TERRAIN8_OUTPUT_CONTRACT_SPLIT

- status: `A2_2_CANDIDATE`
- type: `schema and contract split`
- claim:
  - the current local result stores topology4 family metrics such as `deltaH_absmean`, `lin_err_mean`, and `dS_mean`, while the admitted surface stores terrain/sign/direction cells with `entropy_mean` and `purity_mean`; same-runner provenance therefore does not collapse the two into one current contract
- source lineage:
  - parent basis: clusters B and C, tensions T2 and T3, distillates D2 and D3, candidates C3-C5
- retained contradiction marker:
  - provenance continuity is preserved
  - output-contract continuity is not granted

## Candidate 4: TERRAIN8_SIGN_PATTERN_STRUCTURE_PACKET

- status: `A2_2_CANDIDATE`
- type: `admitted surface structure packet`
- claim:
  - the admitted terrain8 surface carries real terrain-specific sign structure, with `Si` strongest overall on stored entropy/purity and with sign effects differing across `Se`, `Ne`, and `Si`, so the admitted surface should remain usable as its own structured endpoint packet
- source lineage:
  - parent basis: cluster C, tension T4, distillate D3
- retained boundary:
  - do not infer this sign structure from the current local topology4-family result, which lacks terrain-by-sign axes

## Candidate 5: HASH_MATCH_WITH_TOKENIZATION_DRIFT

- status: `A2_2_CANDIDATE`
- type: `evidence naming drift packet`
- claim:
  - exact admitted output-hash continuity can coexist with naming/tokenization drift between evidence-pack metric keys and admitted JSON keys, so evidence transport normalization must stay separate from schema-identity claims
- source lineage:
  - parent basis: tension T5
- retained contradiction marker:
  - hash match persists
  - tokenization identity does not

## Candidate 6: NEXT_CHANNELGRID_DEFERRAL_BOUNDARY

- status: `A2_2_CANDIDATE`
- type: `family boundary packet`
- claim:
  - the next residual pair beginning at `run_axis12_topology4_channelgrid_v1.py` remains outside this reduction, even though the current seam already spans two topology4 surface types
- source lineage:
  - parent basis: cluster E, tension T6, distillate D5, candidate C6
- retained boundary:
  - this packet prevents cross-family flattening during later residual cleanup

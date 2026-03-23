# A2-2 REFINED CANDIDATES

## Candidate 1: CLOSURE_CORRECTION_SINGLE_SURFACE_SHELL

- status: `A2_2_CANDIDATE`
- type: `closure-correction shell`
- claim:
  - `results_axis12_topology4_channelfamily_suite_v2.json` should remain a one-file closure-correction shell rather than being retold as a newly discovered large family or folded back into generic closure prose
- source lineage:
  - parent batch: `BATCH_sims_axis12_topology4_channelfamily_suite_v2_orphan_surface__v1`
  - parent basis: cluster A, distillates D1 and D5, candidates C1-C3
- retained boundary:
  - one local result surface only

## Candidate 2: INTENTIONAL_COMPARISON_ONLY_THEN_SOURCE_ADMISSION

- status: `A2_2_CANDIDATE`
- type: `correction-history packet`
- claim:
  - the strongest reusable history rule is that the local channelfamily result was intentionally kept comparison-only during the earlier seam pass, and only later source-admitted when the aggregate coverage scan proved that the omission left one uncovered sims file
- source lineage:
  - parent basis: cluster C, cluster D, tension T1, distillates D1 and D3, candidates C1 and C4
- retained contradiction marker:
  - the original seam decision was deliberate
  - the later correction was still necessary

## Candidate 3: TERRAIN8_SEAM_REMAINS_VALID_AFTER_CORRECTION

- status: `A2_2_CANDIDATE`
- type: `nonreplacement seam packet`
- claim:
  - local source admission of the channelfamily result does not replace the earlier terrain8 admission seam, because the earlier batch still preserves the mismatch between local channelfamily output and repo-top admitted terrain8 output under the same runner hash
- source lineage:
  - parent basis: cluster C, tension T2, distillates D3 and D5, candidate C4
  - comparison anchor:
    - `BATCH_A2MID_axis12_topology4_admission_contract_split__v1`
- retained contradiction marker:
  - source admission now exists
  - seam mismatch still remains

## Candidate 4: COMPACT_TOPOLOGY4_STRUCTURE_PACKET

- status: `A2_2_CANDIDATE`
- type: `local-result structure packet`
- claim:
  - the orphan surface should stay reusable as a compact topology4 packet because it still preserves real adaptive-vs-fixed and EC-vs-EO structure, with `EC_AD` carrying the largest `lin_err_mean` and `EO_FX` the largest `deltaH_absmean`
- source lineage:
  - parent basis: cluster B, tension T4, distillate D2, candidate C3
- retained boundary:
  - compact size does not erase structured content

## Candidate 5: FULL_DIRECT_SOURCE_COVERAGE_ARRIVES_ONLY_HERE

- status: `A2_2_CANDIDATE`
- type: `closure-timing packet`
- claim:
  - the earlier hygiene pass can remain a real closure step while full direct-source coverage must still be timed only to this correction batch, because the aggregate remained one file short until this exact admission
- source lineage:
  - parent basis: cluster D, tensions T5 and T6, distillates D4 and D6, candidates C5-C6
  - comparison anchors:
    - `BATCH_A2MID_hygiene_artifact_closure_split__v1`
    - `BATCH_A2MID_sims_residual_coverage_split__v1`
- retained contradiction marker:
  - hygiene closure survives
  - full direct-source coverage arrives later

## Candidate 6: NO_FURTHER_SIMS_INTAKE_AFTER_CORRECTION

- status: `A2_2_CANDIDATE`
- type: `terminal handoff packet`
- claim:
  - after this correction batch, no further sims-side intake batches are needed because residual-class completion and direct-source coverage completion finally coincide at the same point
- source lineage:
  - parent basis: tension T6, distillates D4 and D6, candidate C6
- retained boundary:
  - terminal handoff applies only after this correction, not before

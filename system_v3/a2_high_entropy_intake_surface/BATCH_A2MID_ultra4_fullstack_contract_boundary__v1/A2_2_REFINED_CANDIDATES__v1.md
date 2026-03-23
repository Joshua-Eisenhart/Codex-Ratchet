# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_ultra4_fullstack_contract_boundary__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `ULTRA4_FULL_STACK_SHELL_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_ultra4_full_stack.py` and `results_ultra4_full_stack.json` should stay compressed as:
  - one standalone full-stack macro family
  - one runner plus one paired result
  - one shell combining:
    - geometry
    - `stage16`
    - `axis0_ab`
    - `axis12`
    - `seqs`
  - not one narrow single-branch sim

Why this survives reduction:
- it is the parent batch's clearest family-identity claim
- later ultra-lane work needs the full-stack shell kept visible before the inner seams are isolated further

Source lineage:
- parent cluster `A`
- parent distillates:
  - `D1`
  - `D2`
- parent candidate `C2`

Preserved limits:
- this batch does not treat the shell as repo-top admitted
- it preserves full-stack identity only

## Candidate RC2) `LOCAL_ULTRA4_SIM_ID_WITHOUT_REPOTOP_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest provenance packet in the parent batch is:
  - the current runner writes `S_SIM_ULTRA4_FULL_STACK`
  - the catalog lists the family
  - the repo-held top-level evidence pack contains no matching block
- local writer existence and catalog visibility must stay weaker than repo-top evidence admission

Why this survives reduction:
- it is the cleanest compression of the parent batch's main evidence contradiction
- later ultra-lane lineage work needs the local-only admission split kept explicit

Source lineage:
- parent cluster `A`
- parent distillate `D4`
- parent candidate `C3`
- parent tension `T1`
- comparison anchors:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`
  - `BATCH_A2MID_stage16_absolute_delta_boundary__v1:RC2`

Preserved limits:
- this batch does not deny the local writer contract or catalog visibility
- it preserves only that neither upgrades the family into repo-top evidence status

## Candidate RC3) `AXIS0_AB_BASELINE_DELTA_MIXED_RECORD_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the `axis0_ab` branch should preserve one mixed-contract packet:
  - `SEQ01` records store absolute baselines
  - `SEQ02` through `SEQ04` store only delta records
  - one shared map therefore does not imply one uniform record contract

Why this survives reduction:
- it is the parent batch's sharpest contract seam
- later Axis0 reads need a compact rule for not mixing baseline and delta records into one schema

Source lineage:
- parent cluster `D`
- parent distillate `D3`
- parent candidate `C4`
- parent tension `T2`

Preserved limits:
- this batch does not deny those records share one branch container
- it preserves only that container identity is weaker than record-contract identity

## Candidate RC4) `BERRY_FLUX_SIGN_SYMMETRY_WITH_NONEXACT_MAGNITUDE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the geometry layer should keep one compact packet:
  - `berry_flux_plus` and `berry_flux_minus` are exact sign mirrors at stored precision
  - the stored magnitude is near but not equal to the comment-level `±2π` expectation
- symmetry and nonexact magnitude must stay together

Why this survives reduction:
- it is the parent batch's clearest geometry-facing contradiction packet
- later geometry summaries need a compact rule for not overstating exact quantization from this surface alone

Source lineage:
- parent cluster `B`
- parent distillates:
  - `D2`
  - `D5`
- parent candidate `C5`
- parent tension `T3`

Preserved limits:
- this batch does not deny the strong sign symmetry
- it preserves only that symmetry is stronger than exact-magnitude claims here

## Candidate RC5) `BRANCH_SPECIFIC_SCALE_SPLIT_WITH_SE_CENTERED_STAGE16_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the full-stack result should keep two local truths at once:
  - the largest Axis0 AB deltas are much larger than the Stage16 deltas
  - the Stage16 branch remains Se-centered rather than broadly even across the lattice
- full-stack coexistence does not erase branch-specific scale or concentration

Why this survives reduction:
- it is the parent batch's clearest anti-flattening packet across the internal branches
- later interpretation should not average the full stack into one effect scale or one evenly spread Stage16 map

Source lineage:
- parent clusters:
  - `C`
  - `D`
- parent distillate `D5`
- parent tensions:
  - `T4`
  - `T5`

Preserved limits:
- this batch does not deny that all branches share one full-stack shell
- it preserves only that shared shell is weaker than branch-specific scale and concentration

## Candidate RC6) `ULTRA_SWEEP_NEXT_FAMILY_NONMERGE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_ultra_axis0_ab_axis6_sweep.py` should stay comparison-only here because:
  - it begins the next bounded family
  - it keeps Stage16 and Axis0 sweep structure
  - it drops Berry flux and Axis12
  - it foregrounds sweep metadata instead

Why this survives reduction:
- it is the parent batch's clearest next-family boundary packet
- keeping the ultra sweep separate preserves bounded-batch discipline and a clean next step

Source lineage:
- parent cluster `E`
- parent distillates:
  - `D4`
  - `D6`
- parent candidates:
  - `C5`
  - `C6`
- parent tension `T6`
- comparison anchor:
  - `BATCH_A2MID_ultra2_macro_hidden_scope__v1:RC6`

Preserved limits:
- this batch does not deny continuity across the broader ultra strip
- it preserves only that the sweep family is not the same bounded family as ultra4

## Quarantined Residue Q1) `CATALOG_PLUS_LOCAL_WRITER_AS_REPOTOP_EVIDENCE_STATUS`
Status:
- `QUARANTINED`

Preserved residue:
- local ultra4 writer contract
- catalog visibility
- all treated as if those two facts together promoted ultra4 into repo-top evidence status

Why it stays quarantined:
- the parent batch explicitly preserves zero repo-top evidence-pack matches for the ultra4 SIM_ID
- local writer existence and catalog visibility are both weaker than repo-top admission

Source lineage:
- parent distillate `D4`
- parent candidate `C3`
- parent tension `T1`

## Quarantined Residue Q2) `AXIS0_AB_AS_ONE_UNIFORM_RECORD_CONTRACT`
Status:
- `QUARANTINED`

Preserved residue:
- one `axis0_ab` map
- all records treated as if they shared one contract instead of mixed absolute and delta records

Why it stays quarantined:
- the parent batch explicitly preserves `SEQ01` absolute baselines and `SEQ02` through `SEQ04` delta records
- one branch container is weaker than one record contract

Source lineage:
- parent distillate `D3`
- parent candidate `C4`
- parent tension `T2`

## Quarantined Residue Q3) `BERRY_FLUX_AS_EXACTLY_QUANTIZED_FROM_THIS_SURFACE_ALONE`
Status:
- `QUARANTINED`

Preserved residue:
- strong Berry-flux sign symmetry
- all treated as if the stored magnitude already proved exact quantization from this surface alone

Why it stays quarantined:
- the parent batch explicitly preserves near-`2π` magnitude rather than exact equality
- symmetry is stronger than exact quantization here

Source lineage:
- parent distillates:
  - `D2`
  - `D5`
- parent candidate `C5`
- parent tension `T3`

## Quarantined Residue Q4) `ONE_UNIFORM_ULTRA4_EFFECT_SCALE`
Status:
- `QUARANTINED`

Preserved residue:
- Stage16 branch
- Axis0 AB branch
- all treated as if ultra4 lived on one uniform effect scale

Why it stays quarantined:
- the parent batch explicitly preserves much larger Axis0 AB deltas alongside smaller Stage16 deltas
- one full-stack file is weaker than one shared numeric scale

Source lineage:
- parent distillate `D5`
- parent tensions:
  - `T4`
  - `T5`

## Quarantined Residue Q5) `ULTRA_SWEEP_AS_SAME_BOUNDED_FAMILY`
Status:
- `QUARANTINED`

Preserved residue:
- raw-order adjacency to the ultra sweep family
- shared ultra strip direction
- all treated as if the ultra sweep belonged inside the same bounded family as ultra4

Why it stays quarantined:
- the parent batch explicitly preserves dropped geometry and Axis12 plus added sweep metadata as boundary markers
- adjacency and macro similarity are weaker than bounded-family identity

Source lineage:
- parent distillates:
  - `D4`
  - `D6`
- parent candidate `C5`
- parent tension `T6`

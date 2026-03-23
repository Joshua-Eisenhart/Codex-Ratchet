# A2-2 REFINED CANDIDATES

## Candidate 1: AXIS12_CHANNELGRID_FINAL_PAIRED_SHELL

- status: `A2_2_CANDIDATE`
- type: `residual paired-family shell`
- claim:
  - `run_axis12_topology4_channelgrid_v1.py` and `results_axis12_topology4_channelgrid_v1.json` form the final clean local paired family in the residual paired-family campaign
- source lineage:
  - parent batch: `BATCH_sims_axis12_topology4_channelgrid_family__v1`
  - parent basis: cluster A, distillate D1, candidates C1-C3
- retained boundary:
  - this shell stays at one runner and one paired result only

## Candidate 2: CLEAN_LOCAL_PAIR_WITHOUT_REPO_TOP_ADMISSION

- status: `A2_2_CANDIDATE`
- type: `visibility and admission packet`
- claim:
  - the current channelgrid runner/result pair is internally clean and source-matched even though the repo-top evidence pack omits `S_SIM_AXIS12_TOPOLOGY4_CHANNELGRID_V1` and still admits the neighboring terrain8 topology4 surface instead
- source lineage:
  - parent basis: cluster E, tension T1, distillate D4, candidate C4
- retained contradiction marker:
  - clean local pairing survives
  - repo-top admission still does not

## Candidate 3: TEST_CONTROL_SIGN_CONTRACT

- status: `A2_2_CANDIDATE`
- type: `axis3 control packet`
- claim:
  - the channelgrid family keeps a real test-vs-control sign contract: `n_ctrl` suppresses sign gaps to numerical noise while `n_test` leaves small but nonzero sign gaps, especially in `EO_FX` and `EO_AD`
- source lineage:
  - parent basis: cluster C, tension T2, distillate D2, candidate C3
- retained contradiction marker:
  - control success survives
  - complete disappearance of test-axis sign sensitivity is not claimed

## Candidate 4: ADAPTIVE_FIXED_NONLINEARITY_SPLIT

- status: `A2_2_CANDIDATE`
- type: `axis2 nonlinearity packet`
- claim:
  - `AD` families carry the stored nonlinearity signal while `FX` families remain effectively linear at stored precision, making `lin_err_mean` the sharpest clean discriminator in this pair
- source lineage:
  - parent basis: cluster D, tension T3, distillate D3
- retained boundary:
  - this packet preserves axis2 separation without implying that all other topology4 behavior reduces to the same split

## Candidate 5: TOPOLOGY4_QUADRANT_PEAK_SPLIT

- status: `A2_2_CANDIDATE`
- type: `quadrant asymmetry packet`
- claim:
  - topology4 behavior does not collapse into one scalar strength ranking: energy-open families dominate `deltaH_absmean`, while energy-closed families dominate stored entropy increase
- source lineage:
  - parent basis: cluster B, tension T4, distillate D6
- retained contradiction marker:
  - `EO` strongest on energy-shift magnitude
  - `EC` strongest on entropy increase

## Candidate 6: PAIRED_FAMILY_COMPLETION_CLASS_SHIFT

- status: `A2_2_CANDIDATE`
- type: `campaign boundary packet`
- claim:
  - this batch closes the residual paired-family campaign, but that closure only shifts residual work into runner-only, result-only, diagnostic, and hygiene classes; it does not close the full sims residual inventory
- source lineage:
  - parent basis: cluster E, tension T6, distillate D5, candidate C6
- retained boundary:
  - do not merge this clean pair back into the neighboring terrain8 seam or forward into the harden residual classes

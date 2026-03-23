# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / ARCHIVE-ONLY DISTILLATES
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_FOUNDATION_BATCH_PASS`

## D1) This is a real long-run campaign, not a thin test packet
- `RUN_FOUNDATION_BATCH_0001` preserves `60` cycles, `265` event rows, `2365` packet files, and a `4 MB` terminal state body
- it should be read as a retained historical campaign surface, not as a tiny smoke artifact

## D2) State integrity survived better than runtime context
- `state.json.sha256`, `state.json`, and `summary.final_state_hash` agree exactly on the terminal hash
- the same state keeps empty megaboot and ruleset identifiers, so context binding is weaker than integrity binding

## D3) Transport grammar is the main preserved structure
- retained packet counts are:
  - `SIM_TO_A0`: `1571`
  - `A1_TO_A0`: `265`
  - `A0_TO_B`: `264`
  - `B_TO_A0`: `263`
  - `A0_TO_A1_SAVE`: `2`
- this run is best understood through its exchange grammar, not through any single prose file

## D4) Promotion failure remains central
- despite `840` accepted outcomes and `263` canonical ledger entries, the run ends at `MAX_STEPS` with `master_sim_status NOT_READY`
- retained blockers remain high at `519`

## D5) Archived evidence is incomplete in a specific way
- the archive keeps event and soak-report references to many `sim/sim_evidence_*` files
- the run directory itself no longer contains a `sim/` subtree
- archival retention favored packet/result traces over evidence-body preservation

## D6) A1 strategy history is doubled but not perfectly aligned
- `zip_packets/` retains `265` strategy packets
- `a1_inbox/consumed/` retains `267` consumed strategy zips in irregular numbered blocks
- inbox residue should be treated as historical spill, not as a cleaner authority surface than the packet lattice

## D7) Best next descent
- the next bounded target should be `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE`
- it is the closest derived export of this run and should clarify what the archive chose to compress or omit from the parent campaign

# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / ARCHIVE-ONLY DISTILLATES
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_PROGRESS_BUNDLE_PASS`

## D1) This is a replay/export kit, not a mini-parent-run
- the bundle contains only `63` files and `5` directories
- its embedded child run is narrow: `summary`, `state`, `soak_report`, `events`, `zip_packets`, and consumed strategy residue only

## D2) README and embedded run preserve different truths
- `README_PROGRESS.txt` keeps the staged replay script and cumulative totals across the packet-injection sequence
- the embedded run snapshot keeps only the final one-step state and its hash

## D3) The bundle preserves three strategy surfaces
- `packets/` carries seven A1 strategy zips
- `a1_inbox/consumed/` duplicates the same seven zips byte-for-byte
- `zip_packets/` embeds those seven strategies inside a larger mixed packet subset

## D4) Embedded state is small but not failure-free
- `summary.json` says `accepted_total 15`, `parked_total 0`, `rejected_total 0`
- `state.json` still preserves `5` kills, `7` parked survivors, and `11` reject-log entries

## D5) The event ledger is selective
- only six lines are retained
- only five of the seven carried strategies are referenced in that ledger
- the bundle therefore preserves replay material more broadly than it preserves replay history

## D6) Sim evidence bodies were dropped again
- event and soak surfaces still point at `sim/sim_evidence_*` runtime paths
- no `sim/` subtree survives inside the embedded run

## D7) Best next descent
- the next bounded target should be `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2`
- that sibling revision is the cleanest way to measure how this export family changed after the first progress bundle

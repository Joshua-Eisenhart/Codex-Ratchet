# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_FOUNDATION_BATCH_PASS`

## T1) Zeroed top-line rejection counts vs retained rejection/park history
- source markers:
  - `summary.json`
  - `HARDMODE_METRICS.json`
  - `state.json`
  - early `events.jsonl` rows
- tension:
  - the summary ends with `rejected_total 0` and `parked_total 0`
  - metrics and state still preserve `killed_count 519`, `promotion_status_counts.PARKED 519`, `reject_log_len 153`, and `park_set_len 12`, while early event rows show explicit rejected and parked movement
- preserved read:
  - the archive’s top-line outcome view suppresses failure texture that the deeper control surfaces still retain

## T2) Strong state integrity vs empty governing identifiers
- source markers:
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
- tension:
  - the end-state is strongly hash-bound and the detached hash matches exactly
  - `active_megaboot_id`, `active_megaboot_sha256`, and `active_ruleset_sha256` are all empty strings
- preserved read:
  - the archive retained terminal state integrity more clearly than the identifiers of the governing boot/ruleset context

## T3) Dense sim-result traffic vs absent retained sim evidence bodies
- source markers:
  - `events.jsonl`
  - `soak_report.md`
  - top-level directory inventory
- tension:
  - the run retains `1571` SIM result packets and many explicit `sim/sim_evidence_*` path references
  - the archived run directory does not retain a `sim/` subtree at all
- preserved read:
  - transport and digest traces survived archival more fully than the underlying evidence files they reference

## T4) Packet-lattice counts vs inbox-residue counts
- source markers:
  - `zip_packets/`
  - `a1_inbox/consumed/`
  - `sequence_state.json`
- tension:
  - `zip_packets/` retains `265` strategy packets and `sequence_state.json` records `A1 265`
  - `a1_inbox/consumed/` retains `267` consumed strategy zips across irregular numbering blocks
- preserved read:
  - the archive holds two nonidentical views of A1 strategy traffic rather than one perfectly normalized history

## T5) Cumulative failure tags vs soak-report tail summary
- source markers:
  - `HARDMODE_METRICS.json`
  - `soak_report.md`
- tension:
  - metrics cumulative reject tags are `SCHEMA_FAIL 85`, `SHADOW_ATTEMPT 56`, `NEAR_REDUNDANT 5`, `UNDEFINED_TERM_USE 7`
  - the soak report headlines only `SCHEMA_FAIL 35` and `SHADOW_ATTEMPT 28`
- preserved read:
  - the human-readable run report is a windowed or compressed view, not the full cumulative failure ledger

## T6) High throughput vs unresolved readiness
- source markers:
  - `summary.json`
  - `HARDMODE_METRICS.json`
  - final `events.jsonl` rows
- tension:
  - the campaign completes `60` cycles, `840` accepted outcomes, `263` canonical ledger entries, and `2365` packet artifacts
  - it still ends on `MAX_STEPS`, `master_sim_status NOT_READY`, and `unresolved_promotion_blocker_count 519`
- preserved read:
  - long-run throughput and structural richness did not convert into promotion readiness

## T7) Large campaign label vs minimal save points
- source markers:
  - `zip_packets/` inventory
  - `sequence_state.json`
- tension:
  - the run is a dense `60`-cycle foundation campaign
  - only `2` `A0_TO_A1_SAVE_ZIP` artifacts were retained across `265` A1 sequences and `1571` SIM results
- preserved read:
  - save/export checkpoints were sparse relative to the internal traffic volume

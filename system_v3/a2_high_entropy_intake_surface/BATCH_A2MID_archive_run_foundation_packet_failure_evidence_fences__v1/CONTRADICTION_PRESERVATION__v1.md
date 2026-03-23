# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION PRESERVATION
Batch: `BATCH_A2MID_archive_run_foundation_packet_failure_evidence_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction CP1) Summary cleanliness vs retained failure texture
- preserved contradiction:
  - summary totals end at zero rejected and parked
  - deeper metrics, state, and early event rows preserve kills, rejects, parked entries, and failure tags
- anti-smoothing rule:
  - do not let top-line run summaries erase deeper failure texture

## Preserved contradiction CP2) Strong state integrity vs weak governing context
- preserved contradiction:
  - `state.json`, `state.json.sha256`, and `summary.final_state_hash` agree exactly
  - active megaboot and ruleset identifiers are empty
- anti-smoothing rule:
  - do not convert hash agreement into full provenance certainty

## Preserved contradiction CP3) Dense sim trace retention vs missing evidence bodies
- preserved contradiction:
  - many sim traces and runtime-path references are retained
  - the run body contains no retained `sim/` subtree
- anti-smoothing rule:
  - do not assume referenced evidence bodies still survive because their trace layer does

## Preserved contradiction CP4) One normalized packet lattice vs mismatched inbox residue
- preserved contradiction:
  - `zip_packets/` retains a normalized strategy-packet count of `265`
  - `a1_inbox/consumed/` retains `267` consumed strategy zips in irregular blocks
- anti-smoothing rule:
  - do not collapse residue spill into cleaner authority than the normalized packet lattice

## Preserved contradiction CP5) High throughput vs unresolved readiness
- preserved contradiction:
  - the campaign is long, dense, and packet-rich
  - it still ends `MAX_STEPS`, `master_sim_status NOT_READY`, and blocker-heavy
- anti-smoothing rule:
  - do not read throughput as success or promotion readiness

## Preserved contradiction CP6) Parent campaign reduction complete vs derivative bundle still unread
- preserved contradiction:
  - this batch now narrows the parent campaign itself
  - the nearest derived export surface still belongs to the next progress-bundle step
- anti-smoothing rule:
  - do not treat this child as if it already semantically read the derivative bundle

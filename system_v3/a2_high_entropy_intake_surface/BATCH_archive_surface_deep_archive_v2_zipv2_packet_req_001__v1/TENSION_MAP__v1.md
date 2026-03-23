# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1`
Date: 2026-03-09

## Tension 1: `a1_source packet` Versus No Retained Inbound Strategy Or Digests
- source anchors:
  - `summary.json`
  - `a1_inbox/`
  - `zip_packets/`
- bounded contradiction:
  - summary says `a1_source packet`, but the run keeps `unique_strategy_digest_count 0`, an empty inbox, and only one outbound `A0_TO_A1_SAVE_ZIP`
- intake handling:
  - preserve packet-mode labeling and zero-execution residue together rather than smoothing them into a completed packet loop

## Tension 2: `steps_requested 3` Versus Single-Step Immediate Handoff
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - the run requests `3` steps, but only one step is retained and it is a request-emission row with zero accepted work
- intake handling:
  - preserve planned-step count and actual retained execution separately as historical planning-versus-runtime residue

## Tension 3: Real Outer State Hash Versus Embedded Base-Strategy Zero Hash
- source anchors:
  - `state.json`
  - `state.json.sha256`
  - `000001_A0_TO_A1_SAVE_ZIP.zip`
- bounded contradiction:
  - state and outer save summary bind to `de0e5fe9...`, while the embedded sample strategy uses an all-zero `inputs.state_hash`
- intake handling:
  - preserve the split between actual request state and sample payload scaffold rather than reconciling them

## Tension 4: Archive-Local Save Packet Versus Runtime-Local Event Path
- source anchors:
  - `events.jsonl`
  - archive-local `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
- bounded contradiction:
  - the archive keeps a local save packet copy, but the event row still points to `system_v3/runtime/...`
- intake handling:
  - preserve path leakage as a relocation artifact instead of rewriting it into archive-local form

## Tension 5: Inert Final State Versus Live Request Emission
- source anchors:
  - `state.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - final state shows no earned work, no survivors, and no registry growth, yet the run still emits a live A0-to-A1 request packet
- intake handling:
  - preserve outbound orchestration as distinct from earned lower-loop state change

# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1`
Date: 2026-03-09

## Cluster 1: Request-Only ZIPv2 Bootstrap
- archive meaning:
  - this run preserves only an outbound A0-to-A1 request and no executed lower-loop packet cycle
- bound evidence:
  - `summary.json` keeps `accepted_total 0`, `parked_total 0`, `rejected_total 0`
  - `events.jsonl` contains one `a1_strategy_request_emitted` row
  - `zip_packets/` contains only `000001_A0_TO_A1_SAVE_ZIP.zip`
- retained interpretation:
  - useful historical example of packet-mode request bootstrap rather than packet execution

## Cluster 2: Inert Final State With Retained Lexical Shells
- archive meaning:
  - the final state is materially unchanged, but lexical/bootstrap registries remain populated
- bound evidence:
  - `accepted_batch_count 0`
  - `canonical_ledger_len 0`
  - `survivor_ledger_len 0`
  - `derived_only_terms`, `formula_glyph_requirements`, and `l0_lexeme_set` remain populated
  - summary/state bind to `de0e5fe9...`
- retained interpretation:
  - useful archive seam between inert earned state and preloaded lexical scaffolding

## Cluster 3: Packet Source Label Without Retained Inbound Strategy
- archive meaning:
  - the run is labeled `packet`, but no inbound A1 packet or strategy digest survives locally
- bound evidence:
  - `summary.json` keeps `a1_source packet`
  - `unique_strategy_digest_count 0`
  - `a1_inbox/` is empty
  - the only retained packet is an outbound `A0_TO_A1_SAVE_ZIP`
- retained interpretation:
  - useful historical sign that packet-mode labeling did not imply a completed packet loop

## Cluster 4: Outer Save State Hash Versus Embedded Base-Strategy Zero Hash
- archive meaning:
  - the save packet binds to the real run state while its embedded base strategy still uses a sample all-zero state scaffold
- bound evidence:
  - outer `A0_SAVE_SUMMARY.state_hash` is `de0e5fe9...`
  - embedded `base_strategy.inputs.state_hash` is all zeroes
  - embedded self-audit digests remain placeholder values
- retained interpretation:
  - useful archive seam between actual request state and generic sample strategy payload

## Cluster 5: Runtime-Local Event Path Leakage And Missing Sequence Ledger
- archive meaning:
  - the archived run still points to the old runtime tree and does not retain local sequence counters
- bound evidence:
  - `events.jsonl` points to `system_v3/runtime/.../000001_A0_TO_A1_SAVE_ZIP.zip`
  - archive-local copy exists under `zip_packets/`
  - top-level `sequence_state.json` is absent
- retained interpretation:
  - useful relocation-era archive signature for request-only objects

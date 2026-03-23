# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archive_surface_deep_archive_migrated_run_root_registry_and_family_signatures__v1`
Extraction mode: `ARCHIVE_DEEP_MIGRATED_RUN_ROOT_REGISTRY_SIGNATURE_PASS`

## C1) Current-state residue surface
- members:
  - `bootpack_b_kernel_v1__current_state__/state.json`
  - `bootpack_b_kernel_v1__current_state__/state 2..13.json`
  - `bootpack_b_kernel_v1__current_state__/sequence_state.json`
  - `bootpack_b_kernel_v1__current_state__/sequence_state 2..14.json`
- retained read:
  - the migrated archive preserved a quasi-live numbered state ladder rather than only frozen milestone summaries

## C2) Registry repetition surface
- members:
  - `_RUNS_REGISTRY.jsonl`
  - repeated entries for `TEST_DET_A`, `TEST_DET_B`, `TEST_A1_PACKET_ZIP`, `TEST_A1_PACKET_EMPTY`, `TEST_STATE_TRANSITION_MUTATION`, `TEST_STATE_TRANSITION_CHAIN_A`, `TEST_STATE_TRANSITION_CHAIN_B`, `RUN_REGISTRY_SMOKE_0001`, and `RUN_A2_SNAPSHOT_DEMO_0001`
- retained read:
  - the registry is a compact re-entry tool, but it behaves more like repeated checkpoint reporting than a normalized final-run ledger

## C3) Namespace taxonomy surface
- members:
  - `RUN_*`, `TEST_*`, `V2_*`, `BOOT_*`, `GPT_*`, `PHASEA_*`, `CODEX_*`
- retained read:
  - the subtree preserved multiple experimentation and transport eras in one migrated run-root family

## C4) Long-run campaign surface
- members:
  - `RUN_FOUNDATION_BATCH_0001`
  - `RUN_HARDMODE_CLEAN_0001`
  - `RUN_SIGNAL_0004`
  - `RUN_SIGNAL_0005`
  - `RUN_BLOAT_CHECK_0001`
- retained read:
  - the largest historical mass sits in long-run campaign directories, not in the compact registry or current-state residue

## C5) Packet-exchange skeleton surface
- members:
  - `zip_packets/00000n_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/00000n_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `zip_packets/00000n_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `zip_packets/00000n_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - occasional `A0_TO_A1_SAVE_ZIP.zip`
- retained read:
  - distinct campaign families still share one repeated ZIP-traffic grammar

## C6) Overlay audit surface
- members:
  - `RUN_FOUNDATION_BATCH_0001/HARDMODE_METRICS.json`
  - `RUN_SIGNAL_0005/SIGNAL_AUDIT.json`
  - `RUN_SIGNAL_0005/REPLAY_AUDIT.json`
  - `soak_report.md`
  - `events.jsonl`
- retained read:
  - family-specific overlays were layered on top of the same run skeleton, preserving different analysis modes rather than one standard report shape

## C7) Deterministic and external-strategy test surface
- members:
  - `TEST_DET_A`
  - `TEST_DET_B`
  - `TEST_A1_PACKET_EMPTY`
  - `TEST_A1_PACKET_ZIP`
  - `TEST_STATE_TRANSITION_*`
- retained read:
  - test lineage preserved both deterministic exhaustion runs and explicit external-strategy failure modes

## C8) Bundle and residual spill surface
- members:
  - `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE`
  - `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2`
  - `RUN_FOUNDATION_BATCH_0001_bundle`
  - `RUN_SIGNAL_0005_bundle.zip`
  - `bootpack_b_kernel_v1__runs___RESIDUAL__TEST_A1_PACKET_ZIP/a1_inbox/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- retained read:
  - export/bundle derivatives and one detached packet spill were preserved alongside the core run tree instead of being normalized away

## C9) Deferred next family
- next bounded target:
  - `bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001`
- reason:
  - it is a dense parent campaign with direct derivatives (`PROGRESS_BUNDLE`, `PROGRESS_BUNDLE_v2`, `bundle`) and the largest inspected file count in this pass

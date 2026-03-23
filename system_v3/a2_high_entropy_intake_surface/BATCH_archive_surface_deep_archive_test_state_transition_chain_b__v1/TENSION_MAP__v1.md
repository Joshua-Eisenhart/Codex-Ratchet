# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1`
Date: 2026-03-09

## Tension 1: Replay Attribution Versus `needs_real_llm true`
- source anchors:
  - `summary.json`
- bounded contradiction:
  - summary attributes the run to `replay`, yet also marks `needs_real_llm true`
- intake handling:
  - preserve the lineage mismatch without forcing the run into either a fully replay-only or fully live-LLM category

## Tension 2: Three Counted A1 Steps Versus Two Executed Transitions
- source anchors:
  - `summary.json`
  - `soak_report.md`
  - `sequence_state.json`
  - `state.json`
  - `events.jsonl`
- bounded contradiction:
  - summary, soak, and sequence counters preserve `3` A1 steps, while canonical ledger and executed event rows preserve only `2`
- intake handling:
  - preserve the distinction between queued continuation generation and executed state transition count

## Tension 3: Final Summary Hash Versus Last Executed Event Endpoint
- source anchors:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - summary and sidecar bind to `3ce0407f...`, while the last executed event ends on `232c1595...`
- intake handling:
  - preserve summary/state sidecar as the stronger final snapshot while keeping the event-lattice endpoint visibly distinct

## Tension 4: Queued Third Strategy Versus Missing Third-Step Downstream Packets
- source anchors:
  - `sequence_state.json`
  - `zip_packets/`
  - `events.jsonl`
- bounded contradiction:
  - `A1` sequence advances to `3` and `000003_A1_TO_A0_STRATEGY_ZIP.zip` survives, but there is no `000003_A0_TO_B`, `000003_B_TO_A0`, or `000003_SIM_TO_A0` packet and no third event row
- intake handling:
  - preserve the third strategy as queued continuation residue, not as executed work

## Tension 5: Step-2 `S0002` Proposal Versus Mixed Final Survivor Lineage
- source anchors:
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`
- bounded contradiction:
  - the second-step proposal advances both lanes to `S0002`, but the retained final survivor set advances only `S_BIND_ALPHA_ALT_ALT_S0002`; the target lane remains `S_BIND_ALPHA_S0001`
- intake handling:
  - preserve the mixed lineage rather than normalizing the target lane upward to `S0002`

## Tension 6: Second-Step `SCHEMA_FAIL` Versus Blank Target `NEGATIVE_CLASS`
- source anchors:
  - step-2 row in `events.jsonl`
  - `state.json`
  - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- bounded contradiction:
  - the second step records `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK`, and the paired second export leaves the target `NEGATIVE_CLASS` blank while the alternative retains `NEG_BOUNDARY`
- intake handling:
  - preserve the correlation without asserting a stronger causal mechanism than the archive proves

## Tension 7: Mixed-Suffix Duplicate File Family Versus Single Runtime Branch
- source anchors:
  - all primary run-core files
  - all suffixed duplicate files
- bounded contradiction:
  - the root keeps two top-level file families, but the suffixed family is byte-identical to the primary one even though the suffix numbers mix `2` and `3`
- intake handling:
  - preserve the duplicate family as packaging residue rather than as evidence of a second branch

## Tension 8: Event Schema, Path Drift, And Empty `zip_packets 2/`
- source anchors:
  - `events.jsonl`
  - archive-local `zip_packets/`
  - `zip_packets 2/`
- bounded contradiction:
  - executed rows omit explicit `event` keys, use variant counter field names, leave `sim_outputs[].path` empty, still point packet paths at `system_v3/runtime/...`, and the root keeps an empty duplicate packet-shell directory
- intake handling:
  - preserve the runtime-emitted event shape, path leakage, and empty packet-shell residue rather than rewriting them into a normalized archive-local form

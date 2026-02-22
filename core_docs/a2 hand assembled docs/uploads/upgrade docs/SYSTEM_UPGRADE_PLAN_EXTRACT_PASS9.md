
# SYSTEM_UPGRADE_PLAN_EXTRACT_PASS9

## Scope
- Transport of plans, intents, conflicts, and unresolved upgrades discussed.
- No resolution. No redesign. No prioritization.

## Core System Upgrades (Extracted)
- Megaboot is a single authoritative document containing all boots.
- ZIPs are an upgrade for inter-thread communication and execution, not a replacement for megaboot authority.
- Threads consolidation intent:
  - A0 absorbs Thread S and SIM coordination.
  - A1 absorbs Rosetta and Mining.
  - B remains deterministic canon kernel.
  - SIM TERMINAL remains external and deterministic.

## Determinism Boundaries (Extracted)
- A0, B, SIM TERMINAL must be fully deterministic.
- A1 is internally non-deterministic but emits deterministic artifacts only.
- A1 must operate with explicit modes to constrain LLM failure vectors:
  hallucination, drift, smoothing, narrative, helpfulness.

## ZIP-as-Subagent (Extracted)
- ZIPs are atomic, deterministic, chatless subagents.
- ZIPs never split; documents inside may shard with size limits.
- ZIP ingestion is a single-line deterministic action.
- ZIP templates required for multiple artifact types.

## SIM Pipeline (Extracted)
- SIM requires two artifacts:
  - SIM_PROPOSAL_ZIP (approval path to B via A0).
  - SIM_RUN_ZIP (execution path to terminal).
- SIM returns results; A0 packages evidence; B ingests.
- Hash binding discussed repeatedly (baseline + proposal + input).

## Graveyard Philosophy (Extracted)
- Graveyard is mandatory and never dead.
- At least 50% of batches interact with graveyard when non-empty.
- Graveyard is exploration fuel, not failure.
- Graveyard size should be “big enough to be useful,” not maximal.

## Rosetta / Mining (Extracted)
- Rosetta is experimental overlay and mining mechanism.
- Acts as alternative dictionary / weighted labeling.
- Proposes ratchetable terms only.
- Must never directly affect canon.
- Validation only through ratchet + sims.

## Boot / Load Sequence (Extracted)
- A1 loads full++ (or equivalent) context and confirms.
- A0 loads B with required material only and confirms.
- A0 orchestrates remaining initialization.
- Legacy Thread S assumptions rejected.

## Scaling Concerns (Extracted)
- Ratchet size expected to become very large.
- ZIP sharding required due to LLM context limits.
- Multi-LLM compatibility desired (Claude, Kimi, etc.).
- Human-usable now; automatable later.

## Meta Issues / Conflicts (Preserved)
- Confusion between template ZIPs and extracted ZIPs.
- Drift between “megaboot upgrade” vs “communication ZIP upgrade”.
- Repeated loss of intent during long audit loops.
- Mode control for A1 identified as critical but not fully solved.
- Extraction tools vs system upgrade conflated in multiple passes.

## Unresolved / Ambiguous
UNSPECIFIED — DO NOT INFER

## Process Notes
- Multiple extraction loops requested.
- Each loop expected to extract different facets.
- Larger files preferred to avoid loss via summarization.

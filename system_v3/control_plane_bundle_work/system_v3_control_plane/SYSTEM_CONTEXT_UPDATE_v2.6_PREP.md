# SYSTEM_CONTEXT_UPDATE_v2.6_PREP

This document records a system context directive for the control-plane bundle.

## ARCHITECTURAL INVARIANTS
- A2 → A1 → A0 → B
- Feedback via SIM and SAVE ladder.
- Single mutation path:
  - `A1_TO_A0_STRATEGY_ZIP` → A0 → `A0_TO_B_EXPORT_BATCH_ZIP` → B
- ZIP transport immutable.
- Container primitives fixed.
- ENUM_REGISTRY fixed.
- ROOT_AXIOMS enforced in B:
  - `F01_FINITUDE`
  - `N01_NONCOMMUTATION`
- Do NOT modify B kernel.
- Do NOT redefine root axioms.
- Do NOT restate their semantics.
- No new mutation paths allowed.

## ENTROPY LAYERS

ZERO ENTROPY:
- A0
- B
- SIM
- Structural digest
- State transition digest
- Replay enforcement

MEDIUM ENTROPY:
- A1 structured proposal
- Operator mapping
- Structural distinctness
- Repair loop

HIGH ENTROPY:
- A2 mining
- A2 debugging
- A2 tightening
- A2 fuel generation

A2 is manual-triggered only.
A2 may emit suggestion notices.
A2 may request HIGH model tier.
A2 must use existing ZIP types only.
No new artifact types.
No new container primitives.

## ANTI-HACKING DOCTRINE
- All entropy layers are adversarial.
- A0/B/SIM treat all LLM artifacts as hostile input.
- No auto-correction.
- No schema forgiveness.
- No implicit defaults.
- No free-text interpretation.
- Do NOT modify ZIP_PROTOCOL_v2.

## INTERACTION DENSITY RULE
- Every new term must participate in non-trivial SIM interactions.
- Graveyard entries must be SIM-falsified, not narrative-rejected.
- Promotion requires interaction density.
- Do NOT modify SIM_EVIDENCE_v1 structure.
- Do NOT introduce new SIM primitives.

## CROSS-BASIN FAIRNESS
- A1 must generate structurally distinct alternatives.
- Enforcement layers must remain neutral.
- No probabilistic selection.
- Do NOT modify A1_STRATEGY_v1 schema.

## RUNTIME MEMORY MODEL
runtime/
- canonical_ledger/
- snapshots/
- current_state/
- cache/

- Cache is derived-only.
- Cache is deletable.
- Deleting cache must not change state_hash.
- Zipping runtime/ is full system image.
- Do NOT introduce new persistent directories.
- Do NOT introduce new serialization formats.

## MODEL CAPABILITY
- MODEL_CAPABILITY_LEVEL enum: `LOW`, `MEDIUM`, `HIGH`
- A2 automatic tightening requires `HIGH`.
- Escalation is advisory only.
- No auto-escalation.
- No wall-clock triggers.
- Do NOT modify ZIP header schema.

## SYSTEM PROPERTY
This is a brutal proof engine.
It must be capable of disproving the injected model.
Enforcement layers must remain neutral.
Do NOT embed theoretical model into kernel.
Do NOT alter enforcement layers.

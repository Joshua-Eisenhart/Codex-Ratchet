# COUPLED_RATCHET_AND_SIM_LADDERS__v1
Status: PROPOSED / NONCANONICAL / A2 WORKING UNDERSTANDING
Date: 2026-03-06
Role: Source-bound clarification of the core machine as one ratchet with two coupled ladders

## 1) Purpose
This document clarifies that the active system is not:
- a theorem prover alone
- a simulation pipeline alone
- a generic agent workflow

It is one ratchet with two coupled ladders:
- structural admissibility
- executable evidence

## 2) Structural Ladder
Current structural ladder:
- `A2 -> A1 -> A0 -> B`

Roles:
- `A2` extracts, classifies, distills, and preserves contradiction
- `A1` emits proposal families
- `A0` packages and orders admissible artifacts
- `B` ratchets structure under the active kernel rules

Question answered here:
- `B` answers: is this structure admissible under the current lower-loop constraints?

## 3) Evidence Ladder
Current evidence ladder:
- `SIM T0 -> T1 -> T2 -> ... -> integrated sim`

Roles:
- lower tiers test local/operator sanity
- middle tiers test composition and subsystem behavior
- higher tiers test integrated behavior

Question answered here:
- `SIM` answers: does this admitted structure behave coherently under executable pressure?

## 4) Coupling Rule
These ladders are coupled, not independent.

Rules:
- `B` does not independently produce ontology from simulation
- `SIM` does not independently elevate ontology without `B`-admitted structure
- meaningful progress requires both:
  - structure surviving the lower constraint path
  - executable evidence surviving the tiered SIM path

Short form:
- ratchet structure
- ratchet behavior

## 5) Why the Ratchet Must Have SIM
Without the structural ladder:
- simulation becomes detached from admissible substrate

Without the evidence ladder:
- the system can only accumulate elegant but weakly tested structures

The active machine exists to avoid both failure modes.

## 6) Negative SIM Rule
Negative sims are first-class.

Positive sims answer:
- can this structure survive?

Negative sims answer:
- does the wrong nearby structure fail?

Meaningful survivors require both positive and negative pressure, plus graveyard-linked alternatives.

## 7) Tiering Rule
Higher sims must be reducible to lower evidence surfaces.

Required discipline:
- no opaque mega-sim as first evidence
- no tier skip
- higher-tier claims must trace back to lower-tier tested components

This is why the evidence ladder remains auditable.

## 8) Graveyard Link
The graveyard is part of both ladders.

It stores:
- structural failures
- executable failures
- failed compositions
- negative witnesses
- rescue attempts

So the graveyard is a sim-backed failure basin, not a reject dump.

## 9) World-Model Direction
The world-model system should emerge from:
- ratcheted structure
- tiered SIM composition
- graveyard evidence
- accumulated executable survivors

It should not appear as a separate magical top layer.

## 10) Current Active Status
The general tiered SIM contract already exists at:
- `system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`

The active family-specific promotion contracts now exist at:
- `system_v3/a2_state/SIM_FAMILY_PROMOTION_CONTRACTS__ACTIVE_LANES__v1.md`

What is still needed:
- continued execution and closure against those lane-specific contracts
- especially where current active lanes still stall on:
  - helper residue
  - path-build saturation
  - rescue efficacy / frontier movement under sustained rescue

## 11) Source Anchors
- `system_v3/specs/01_REQUIREMENTS_LEDGER.md`
- `system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
- `system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
- `system_v3/a1_state/A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1.md`
- `system_v3/a1_state/A1_RESCUE_AND_GRAVEYARD_OPERATORS__v1.md`

# BOOTPACK_A1_WIGGLE__v1
Status: DRAFT / NONCANON
Date: 2026-03-03
Owner: A1 wiggle execution lane

## Purpose
Define the A1 multi-narrative execution contract for generating structured proposal packets from A2 outputs.
This bootpack enforces explicit adversarial exploration and graveyard-as-workspace updates.

## Inputs
Required context inputs:
1. `system_v3/a1_state/A1_BRAIN_SLICE__v1.md`
2. `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
3. A2 topic extraction outputs and brain-delta packets.
4. Stage-0 naming rules:
   `system_v3/specs/24_NAMING_AND_ARTIFACT_RULES__STAGE_0_FREEZE.md`

## Non-Negotiable Rules
1. Do not collapse to one narrative lane.
2. Emit explicit negative lanes and rescue lanes.
3. Do not suppress contradictions to improve readability.
4. Do not admit canon claims.
5. Keep failures actionable (reason + rescue transform).

## Required Lanes Per Cycle
1. `STEELMAN`
2. `ALT_FORMALISM`
3. `BOUNDARY_REPAIR`
4. `ADVERSARIAL_NEG`
5. `RESCUER`

A cycle missing any lane is incomplete.

## Required Candidate Shapes
Per cycle, produce candidates in structured form:
1. `TERM_DEF` candidates
2. `MATH_DEF` candidates
3. `SIM_SPEC` positive candidates
4. `SIM_SPEC` negative candidates with explicit `NEGATIVE_CLASS`

Each candidate must include:
- source anchor(s),
- target class,
- lane id,
- explicit fail condition or success condition.

## Graveyard Update Contract
Each failed or parked candidate must append:
1. failure class,
2. likely classical residue,
3. minimal rescue edit,
4. retry priority.

## Output Validation Stub
Stage-2 schema stubs:
- `system_v3/specs/schemas/RATCHET_FUEL_CANDIDATE_PACKET_STAGE2_v1.schema.json`
- `system_v3/specs/schemas/A1_BRAIN_ROSETTA_UPDATE_PACKET_STAGE2_v1.schema.json`

## Naming
All outputs from this bootpack must follow Stage-0 naming freeze.


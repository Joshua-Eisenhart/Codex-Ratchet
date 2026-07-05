# Capstone audit — ratchet_climb_engine_v2_blind

Status: `DRAFT_UNAUDITED`

This directory is the repair target pre-registered by the `ratchet_climb_engine_v1_drive` capstone audit.

Required repair properties:

1. Fact-only drive events: no `target_rung`, no rung labels, and no rung-naming demand types in drive facts.
2. Blinded selector: enumerate candidate lifts, test fact-measured quotient loss, select weakest repairing lift under MSS discipline.
3. Independent legs: NumPy, JAX, and Julia each implement the drive and selector natively.
4. Controls: commuting drive, static fact list, memoryless drive, and label/fact shuffle.

Claim ceiling: `scratch_diagnostic`; `promotion_allowed=false`.

# SIM Tier Architecture (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: define an explicit tiered SIM structure where lower-tier sims compose into higher-tier sims, with an eventual single whole-system sim target.

==================================================
1) Tier Model (normative)
==================================================

SIM tiers are discrete:
- `T0_ATOM`: validates one atomic term or one atomic relation.
- `T1_COMPOUND`: validates a composed term/relation built from multiple T0 units.
- `T2_OPERATOR`: validates operator-level behaviors over T1 structures.
- `T3_STRUCTURE`: validates multi-operator structures.
- `T4_SYSTEM_SEGMENT`: validates subsystem behavior from multiple T3 structures.
- `T5_ENGINE`: validates full engine behavior from multiple T4 segments.
- `T6_WHOLE_SYSTEM`: validates the full integrated model in one sim.

Every sim must declare exactly one tier.

==================================================
2) Composition Contract
==================================================

Higher-tier sims must reference lower-tier dependencies:
- each `Tn` sim (`n > 0`) must depend on at least one `Tn-1` sim
- dependencies must be explicit by sim id
- dependency graph must be acyclic at sim-spec level

No tier skipping for canonical promotion:
- A `Tn` sim cannot be promoted if required lower-tier dependencies are absent or unvalidated.

==================================================
3) Evidence Contract Per Tier
==================================================

Each sim must emit deterministic evidence:
- `sim_id`
- `tier`
- `input_hash`
- `code_hash`
- `output_hash`
- `manifest_hash`
- `evidence_token`

Each tier must include:
- positive sims (`SIM_SPEC`)
- negative sims (`NEG_SIM_SPEC` or equivalent negative designation)
- linked plausible alternatives in graveyard for key targets

Negative sim classes per tier:
- `NEG_EXPECT_FAIL_TARGET` (adversarial invalid input/condition should fail)
- `NEG_EXPECT_REJECT_ALTERNATIVE` (nearby alternative construction should fail)

At least one negative sim class must be present per target class; both are preferred for closure.

==================================================
4) Tier Coverage Requirement
==================================================

A tier is considered structurally covered when:
- all required targets for that tier have a positive sim result
- at least one negative sim exists per target class
- alternatives exist in graveyard for each target class

Coverage is required before planning major expansion in the next tier.

==================================================
4A) Exploration + Stress Requirement
==================================================

SIM work must include rich exploration around targets, not only one pass/fail check.

Required sim families per target class:
- `BASELINE`: intended behavior under nominal conditions.
- `BOUNDARY_SWEEP`: parameter/range edge behavior.
- `PERTURBATION`: small local variations around admitted structure.
- `ADVERSARIAL_NEG`: targeted falsification attempts (negative sims).
- `COMPOSITION_STRESS`: behavior under composed higher-tier dependency stacks.

Stress suites are tier-aware:
- lower tiers focus on strict local validity and perturbation response
- higher tiers add composition load, dependency interaction, and long-horizon stability checks

==================================================
5) Whole-System Sim Target
==================================================

`T6_WHOLE_SYSTEM` is mandatory long-term target:
- one integrated sim that composes validated lower tiers
- no special bypass rights
- must satisfy same evidence and determinism rules as all other tiers

The whole-system sim is a convergence artifact, not a replacement for lower-tier sims.

==================================================
6) Forbidden Shortcuts
==================================================

- Do not mark a tier as covered without negative sims.
- Do not mark a tier as covered without graveyard alternatives.
- Do not admit a whole-system sim without dependency coverage.
- Do not treat unversioned or unhashed sim output as evidence.

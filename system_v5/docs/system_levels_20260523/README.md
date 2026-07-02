# Codex Ratchet System Levels Documentation Pack

Date: 2026-05-23

Status: working documentation pack. Not canon by itself. This pack organizes
the current model by audience and execution level so humans, CS implementers,
LLM controllers, and system/runtime code do not collapse different claims into
one word like "axiom."

2026-05-23 quarantine note: the conceptual and naming material in this pack can
be reviewed as non-evidence documentation. Any "current receipt", "fresh-rerun",
or "completed vertical slice" anchor in this pack is quarantined until clean
independent reruns rebuild the cited formal-scout scripts and result JSONs.

## Purpose

The project needs several explanations of the same system:

1. A human explanation that preserves the owner's philosophy and goals.
2. A CS/engineering explanation that turns the philosophy into data structures,
   tests, and bounded work.
3. An LLM-facing explanation that prevents prompt drift and semantic smuggling.
4. A system/runtime explanation that describes what files, sims, receipts, and
   gates actually enforce.
5. A research agenda that names the physics model, QIT-FEP, Axis0, flux, and
   mathematical proof targets without pretending they are already solved.

This directory is that packet.

## Documents

| File | Audience | Job |
| --- | --- | --- |
| `00_LEVEL_MAP_AND_AUTHORITY.md` | everyone | separates thesis, root constraint, derived constraint, process law, sim, and receipt |
| `01_HUMAN_FACING_MODEL.md` | humans | explains the philosophy, goals, and why bounded work follows from the model |
| `02_CS_ENGINEERING_MODEL.md` | engineers | turns the system into types, state machines, sims, controls, and receipts |
| `03_LLM_CONTROLLER_MODEL.md` | LLM agents | tells agents how to talk, reason, refuse overclaims, and route work |
| `04_SYSTEM_RUNTIME_MODEL.md` | repo/runtime | names the enforceable surfaces, current sim layers, and build process |
| `05_PHYSICS_QIT_FEP_AXIS0_FLUX_MODEL.md` | research builders | lays out the physics model, QIT-FEP, Holodeck, Axis0, flux, and next sims |
| `06_MATH_PROOF_AGENDA.md` | proof/research lanes | sorts Riemann, P vs NP, Navier-Stokes, Yang-Mills, and other targets by plausible fit |
| `07_FULL_RICH_SYSTEM_MANUAL.md` | everyone | full long-form explanation from owner thesis to constraints, QIT, Holodeck, Axis0, flux, proof agenda, and open questions |
| `08_DETAILED_SIM_AND_PROOF_PROGRAM.md` | builders/researchers | detailed sim template, controls, current vertical slices, next sim lanes, and proof program |
| `09_EXTENDED_CONSTRAINT_CANDIDATE_LEDGER.md` | constraint/system workers | root constraints, derived constraints, candidate fences, enforcement gates, and promotion requirements |
| `10_NAMING_NOTATION_AND_CLAIM_GRAMMAR.md` | humans/agents/tools | clean vocabulary, notation, status grammar, claim grammar, and LLM enforcement rules |
| `11_LEGACY_SOURCE_VETTING_AND_QIT_TRANSLATION.md` | source processors | vetted intake of the old Gemini/Grok legacy docs and their QIT/CS translation rules |
| `12_PRE_MANIFOLD_TO_RATCHET_DERIVATION.md` | systems/research builders | step-by-step derivation from pre-manifold pressure to constraint manifold, ratchet, engines, Holodeck, Axis0, flux, and sims |
| `13_AXES_0_6_QIT_ENGINE_ATLAS.md` | axis/engine builders | rich Axes 0-6 atlas with QIT math, IGT charts as engine strategy grammar, terrain laws, operator channels, token grammar, engine charts, Axis0 candidates, flux status, and open proof obligations |
| `machine_readable/system_level_registry_20260523.json` | tools/agents | machine-readable version of the level stack, docs, receipt anchors, and next gates |
| `machine_readable/constraint_registry_20260523.json` | tools/agents | machine-readable constraint/fence ledger with enforcement fields and claim requirements |
| `machine_readable/axes_qit_engine_registry_20260523.json` | tools/agents | machine-readable axis, token, engine-row, Axis0, flux, and sim-row schema registry |

The first seven Markdown docs are entry routes. The long-form center of gravity
is now docs `07` through `12`.

Doc `13` is the rich axis/engine atlas. It exists because the shorter docs do
not carry enough operational math for agents to rebuild the engine safely.

## Authority Boundary

The pack is a map, not a promotion.

It can say:

```text
This is the current best organization of the work.
This is the next sim or proof target.
This is how to make a claim enforceable.
```

It cannot say:

```text
Axis0 is solved.
Flux is a root.
The physics model proves a Millennium problem.
The Holodeck is a complete FEP runtime.
Old high-entropy docs are canon because they contain a good phrase.
```

## Quarantined Receipt Anchors

The following were written as receipt anchors during the contaminated expansion
window and must not be treated as current evidence:

```text
system_v5/ops/formal_scouts/sim_holodeck_qit_fep_predictive_world_model_probe.py
system_v5/ops/formal_scouts/sim_flux_qit_engine_holodeck_runtime_probe.py
system_v5/ops/formal_scouts/sim_axes_qit_engine_math_consistency_probe.py
```

Their prior pass/fresh-rerun wording is stale. Use them only as proposed rerun
targets until clean independent receipts exist. They do not admit final Axis0,
final Xi, final flux, full E=16 density runtime, or production Holodeck.

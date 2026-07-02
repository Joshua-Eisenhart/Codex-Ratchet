# System Levels 20260525 Spinor-Enforced Rebuild

Status: replacement working pack, not canon, not a promotion receipt.

This pack replaces the current working story for manifold, engine, terrain,
operator, Axis0, flux, QIT-FEP, IGT, physics, and Holodeck docs. It does not
delete or rewrite `system_v5/docs/system_levels_20260523/`. The older pack is
now historical/reference for these topics because it can be read as if density
matrices, Bloch images, Hopf charts, PEPS3D, flux, and Axis0 were one smooth
earned stack. The current repo contract requires a stricter build.

The controlling correction is:

```text
F01 finite carrier/probe/operator/path set
N01 noncommuting or order-sensitive operation/control
-> finite probe/effect quotient
-> finite PEPS3D-carried spinor-network carrier from the first carrier step
-> spinor, Hopf, Weyl, terrain, operator-substage maps on that carrier
-> only then flux, Xi, Phi0, Axis0, Holodeck/FEP, and physics readouts
```

The user-side correction that motivated this pack is also preserved:

```text
Axis0 must not collapse to a single i scalar.
Spinor space must not be bypassed by Bloch/density/chart shortcuts.
The i, j, k language is carrier/quaternion/genealogy material, not an Axis0
solution by itself.
```

## Pack Map

| File | Role |
|---|---|
| `00_AUTHORITY_AND_OPEN_GAPS.md` | Authority order, old-doc demotions, missing TUI caveat, and nonclaim boundaries. |
| `01_ROOT_TO_SPINOR_PEPS3D_MANIFOLD.md` | Math chain from F01/N01 through finite effects, PEPS3D, spinors, Hopf tori, Weyl sheets, terrain placements, and substages. |
| `02_TERRAIN_OPERATOR_ENGINE_IGT_ATLAS.md` | Separates terrain families, loop fields, operators, placements, IGT grammar, schedule rows, and substage cell obligations. |
| `03_AXIS0_FLUX_PHYSICS_HOLODECK_BOUNDARIES.md` | Keeps Axis0, flux, i/j/k, QIT-FEP, physics, and Holodeck distinct and blocked until their lower gates are earned. |
| `04_SIM_RATCHET_AND_DOC_REBUILD_PROGRAM.md` | Concrete formal/informal simulation ratchet for rebuilding the docs without canonizing sketches. |
| `05_FULL_NUANCED_MODEL_MANUAL.md` | Long-form manual laying out the object taxonomy, carrier geometry, terrain/operator/engine semantics, Axis0/flux/Holodeck boundaries, and receipt ceilings in one place. |
| `06_FULL_IGT_MAPPING_ATLAS.md` | Full IGT/Jung/I Ching mapping atlas: quadrant locks, token laws, signed operators, Type-1/Type-2 charts, 8x8 schedule grid, and runtime 64 expansion. |
| `07_IGT_QIT_FEP_STRATEGY_MATH.md` | Candidate math bridge for Axis6-swapped strategies, Axis5 first/second strategy, and IGT-aligned game theory translated into QIT-FEP terms. |
| `08_STRATEGY_LOOP_ENGINE_SEMISYMMETRY_MAP.md` | Full candidate comparison map for all 16 strategies across loops, engines, semisymmetry pairs, runtime slots, and QIT-FEP witnesses. |
| `09_CLASSICAL_GAME_QIT_FEP_CORRELATION_AXES_7_12.md` | Exploratory classical-game baseline, QIT-FEP population lift, game-world engine map, and non-canon axes 7-12 shadow-axis candidate space. |
| `10_BOUNDED_MAX_EXPLORATION_PROCESS_REPAIR.md` | Process repair doc for bounded-but-broad level exploration, formal-sim failure analysis, Wizard v4.2 enforcement, frontier matrices, and validator gaps. |
| `machine_readable/doc_status_20260525.json` | Small status ledger for controllers and later audits. |

Related executable guard:

```text
scripts/validate_bounded_max_exploration.py
```

This guard is intentionally red on the current Phase 1 candidate estate until
the frontier matrix exists and the candidate receipts are reissued, rerun,
killed, or blocked under the current contract. Once a frontier matrix reaches
its declared threshold, the same guard must stay red until the matrix also names
a non-stop post-threshold action: continue the active level, write a transition
artifact, or write a blocked-repair artifact. A green threshold is not a stop
condition.

Formal closeouts also have a geometry-answer gate: before file lists, command
lists, validator output, or `all_pass=true`, the worker must state what geometry
is working. For the current Phase 1 surface that means the finite probe/effect
response quotient `Q_P = S / ~_P` and any finite projective/incidence or
history-effect probe-family geometries that were actually receipted. It does
not mean PEPS3D, spinor/Hopf/Weyl, terrain, substage, flux, Axis0, Holodeck, or
physics geometry.

## Current Source Surfaces

This pack is grounded in the current repo authority/process docs and these
repair/audit surfaces:

```text
AGENTS.md
CODEX.md
system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
system_v5/docs/LLM_CONTROLLER_CONTRACT.md
system_v5/docs/LEGO_SIM_CONTRACT.md
system_v5/ops/TUI_MANIFOLD_LAYER_FAILURE_AUDIT_20260525.md
system_v5/ops/CONSTRAINT_MANIFOLD_MATH_LEDGER_20260525.md
system_v5/ops/FINITE_EFFECT_SIC_WEYL_SUBSTRATE_AUDIT_20260524.md
system_v5/ops/FLUX_SPINOR_SCALE_AUDIT_20260524.md
system_v5/ops/FULL_MANIFOLD_ENGINE_TERRAIN_CONSTRAINT_LAYOUT_20260525.md
system_v5/ops/QIT_FEP_AXIS0_SPINOR_PATH_INTEGRAL_WORKOUT_20260523.md
system_v5/ops/QIT_ENGINE_FULL_EXPLICIT_MATH_PACKET_20260522.md
system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md
```

Nearby wiki pages were used only as genealogy/support surfaces, not as current
repo promotion receipts:

```text
/Users/joshuaeisenhart/wiki/concepts/i-scalar-and-axis-0-genealogy.md
/Users/joshuaeisenhart/wiki/concepts/axis0-current-doctrine-state-card.md
/Users/joshuaeisenhart/wiki/concepts/quaternion-and-spinor-carrier-foundations.md
/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md
/Users/joshuaeisenhart/wiki/concepts/engine-64-schedule-atlas.md
/Users/joshuaeisenhart/wiki/concepts/holodeck-doctrine.md
/Users/joshuaeisenhart/wiki/concepts/projective-holodeck-memory-model.md
```

## Missing Context Notice

This pack does not claim to recover every statement from the previous TUI
thread. Anything that exists only in chat and not in repo, wiki, memory, or a
receipt remains missing until pasted or reconstructed explicitly.

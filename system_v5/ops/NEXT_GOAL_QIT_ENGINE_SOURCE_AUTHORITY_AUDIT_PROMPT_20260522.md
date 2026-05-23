# Next Goal Prompt: QIT Engine Source Authority Audit

**Created:** 2026-05-22
**Status:** active replacement prompt
**Supersedes:** `system_v5/ops/NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md`

## Paste-Ready Goal

Continue in `/Users/joshuaeisenhart/Desktop/Codex Ratchet`.

The previous full QIT engine / constraint-manifold build goal is stopped. Do not continue PEPS/PEPS3D, MPDO, Phi0, attractor-basin, final-manifold, wiki-batch, or sidequest simulation work.

Primary goal: audit and repair the source-to-runtime mapping for the QIT engine axes/operators/terrains before any further engine build. The old docs already define the math; the failure is that recent sims/runtime paths let the operator-axis layer drift away from the defined tables.

Read first:

- `AGENTS.md`
- `system_v5/ops/QIT_ENGINE_MANIFOLD_AUDIT_FREEZE_20260522.md`
- `system_v5/ops/QIT_ENGINE_SOURCE_AUTHORITY_AUDIT_20260522.md`
- `system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md`
- `system_v5/READ ONLY Reference Docs/outdated system math and geometry.md`
- `system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md`
- `system_v5/READ ONLY Reference Docs/operator math explicit.md`
- `system_v5/READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md`
- `system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md`
- `system_v5/docs/17_actual_lego_registry.md`
- `system_v5/grok_sim/SCREENSHOTS_INDEX.md`
- `system_v5/docs/CLAUDE_THREAD_HANDOFF_FLUX_TERRAIN_AXIS_OPERATOR_DISCIPLINE_20260515.md`
- `system_v5/ops/formal_scouts/canonical_qit_engine_specs.py`
- `system_v5/ops/formal_scouts/qit_engine_runtime.py`
- `system_v5/ops/formal_scouts/sim_two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe.py`
- `system_v5/ops/formal_scouts/results/two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe_results.json`

Current source truth:

- Jungian functions are labels and chart grammar, not replacement math.
- The exact operator math is the four base operators `Ti`, `Te`, `Fi`, `Fe`.
- `UP/DOWN` is not extra operator math by itself; it is precedence after a terrain map is chosen.
- Axis 5 is the operator-family split: dephasing `{Ti, Te}` versus rotation `{Fi, Fe}`.
- Axis 6 is left action versus right action: `L_A(rho)=A rho` versus `R_A(rho)=rho A`. In the current token tables this is represented as operator-first versus terrain-first precedence / signed token position. Runtime rows should carry both `axis6_action_side` and `precedence` until the alignment is enforced.
- Axis 4's source-backed math anchor is loop-order family: `U o E o U o E` versus `E o U o E o U`, implemented as `FeTi` versus `TeFi` loop families.
- Pair/symbolic overlays such as `TiFe`/`FeTi`, `FeFi`/`TiTe`, or `TeTi`/`FeFi` are not allowed to override the exact Ax4/Ax5/Ax6 anchors without row-by-row audit.
- Do not admit an `A4 x A5 intersection -> operator` grid as canon. Treat it as an exploratory reconstruction until checked against the atlas, token table, and engine charts.
- The 16 ordered tokens are first-class: `TiSe`, `SeTi`, `FiSe`, `SeFi`, `TiNe`, `NeTi`, `FiNe`, `NeFi`, `TeNi`, `NiTe`, `FeNi`, `NiFe`, `TeSi`, `SiTe`, `FeSi`, `SiFe`.
- `NiTe` and `SiTe` are explicit `Te`-down terrain-first tokens on the conjugated `Ni/Si` side. They must not disappear into generic `Ni`, generic `Si`, or a generic entropy-gradient readout.
- `Te` is not descent/ascent in isolation. It is the `sigma_x` dephasing/projection channel; it can be entropy-ascent, purity-descent, or target-distance descent depending on the functional. Any gradient label must name the functional, target/attractor, terrain context, Axis 6 precedence, and ordered token.
- `NiTe` and `SiTe` are the candidate terrain-first compression/descent rows to audit; `TeNi` and `TeSi` are the corresponding operator-first compression rows to compare. Do not generalize these four rows to all 16 placements.
- Exact operator channel, semantic role, terrain/topology label, loop placement, sheet/type, and token precedence must be separate runtime columns.
- The old formalized-math doc already gives the build order: constraints -> `M(C)` -> geometry on `M(C)` -> axes.

Required work:

1. Build a source-authority matrix.
   - Rows: each source doc/screenshot/table.
   - Columns: terrain/topology, judging operator, exact channel, Axis 5 family, Axis 6 action side, Axis 6 precedence/sign, ordered token, loop, sheet/type, semantic role, functional readout, target/attractor, terrain generator, path law, density law, readout observable, source refs.
   - Do not collapse semantic labels into exact operator math.

2. Build a canonical 16-token matrix.
   - Include all Type 1 and Type 2 outer/inner rows.
   - Include `NiTe` and `SiTe` explicitly.
   - Include exact `Ti/Te/Fi/Fe` channel, not just the terrain label.
   - Mark whether each row is dephasing or rotation, operator-first or terrain-first, fiber or base, left or right sheet.

3. Build runtime conformance matrix.
   - Compare `canonical_qit_engine_specs.py`, `qit_engine_runtime.py`, `engine_core.py`, D130 PEPS/PEPS3D inventory, MPS scouts, Axis0 scouts, and recent sidequest references.
   - Classify each as `source_conformant`, `partial`, `terrain_only`, `semantic_only`, `decorative_axis_labels`, `contradictory`, or `not_applicable`.

4. Quarantine dependent results.
   - Any result depending on terrain-only runtime may remain as tensor plumbing or simplified-channel evidence.
   - It cannot promote as full operator-axis placement, full engine, Phi0 bridge, attractor basin, or final manifold evidence.

5. Specify repaired runtime contract.
   - Define the required event-row schema.
   - Define fail-closed tests for missing ordered token, Ax5 family, Ax6 action side, Ax6 sign, precedence, exact channel, loop law, sheet/type, functional readout for gradient claims, target/attractor for descent/ascent claims, and class-correct readout.
   - Identify whether `canonical_qit_engine_specs.py` can become the recovery anchor or whether a new source-native runtime spec file is needed.

6. Only after audit, propose implementation.
   - Do not implement PEPS/PEPS3D dynamics in this goal.
   - Do not implement MPDO dynamics in this goal.
   - Do not run broad sim queues.
   - Do not resume Phi0 or basin work.

Forbidden:

- Do not treat Jungian labels as math authority by themselves.
- Do not treat `Se/Ne/Ni/Si` terrain-only rows as full stage rows.
- Do not treat D130 as proof that all 16 operator-axis placements ran.
- Do not apply one generic readout such as entropy gradient to all 16 placements unless the source-authority matrix proves it row-by-row.
- Do not use sidequest wiki batches as substitute for runtime conformance.
- Do not claim source conflict when the right answer is layer separation: exact operator map, semantic role, chart token, and terrain placement are separate columns.

Done condition:

- New or updated audit artifact contains the source-authority matrix.
- New or updated audit artifact contains the 16-token matrix.
- New or updated audit artifact contains runtime conformance classifications.
- New or updated audit artifact contains quarantine classifications for dependent evidence.
- New or updated audit artifact defines the repaired runtime event schema.
- `system_v5/ops/formal_scouts/README.md` and `.lev/pm/handoffs/20260520-formal-manifold-tooling-retool-session-1.md` are updated.
- No sim implementation, staging, or commit is done unless explicitly requested.

Recommended first concrete artifact:

`system_v5/ops/QIT_ENGINE_SOURCE_AUTHORITY_RUNTIME_CONFORMANCE_MATRIX_20260522.md`

That artifact should be the bridge from the source-authority audit to code repair. It should not contain new science claims.

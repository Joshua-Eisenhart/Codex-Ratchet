# QIT Engine / Constraint Manifold Audit Freeze

**Created:** 2026-05-22T05:00:34Z
**Status:** audit freeze, implementation halted
**Supersedes active execution of:** `QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md` and `NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md`

## Stop Condition

The full QIT engine / geometric constraint manifold build is halted.

Reason: the current sim path allowed the operator/axis layer to drift away from the already-defined axis/operator/terrain tables. This is not a small local bug. If a sim can lose or misclassify `NiTe`, `SiTe`, `TeNi`, `TeSi`, or the Axis 5 / Axis 6 operator placement law, then the axes are not constraining the runtime and the current evidence path is not trustworthy for promotion.

No further engine, tensor, Phi0, PEPS, PEPS3D, basin, or final-manifold implementation work is admissible until the audit below closes.

## Authority Clarification

The Jungian functions are labels, not math authority by themselves.

The source math lives in the axes/operator/terrain tables:

- `system_v5/READ ONLY Reference Docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md`
  - exact operator table: lines 208-211
  - token table: lines 253-256
  - signed operator variants: lines 271-278
- `system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md`
  - dephasing/rotation split: lines 429-464
  - signed variants and tokens: lines 588-595
  - engine type tables: lines 614-626
- `system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md`
  - terrain-family classes: lines 301-307
  - Rosetta operator labels: lines 323-341
  - screenshot-backed candidate terrain laws: lines 1379-1407
  - Type-1/Type-2 chart tables: lines 1461-1502
- Screenshots:
  - `system_v5/READ ONLY Reference Docs/Screenshots/Common Operators.png`
  - `system_v5/READ ONLY Reference Docs/Screenshots/Terrain.png`
  - `system_v5/READ ONLY Reference Docs/Screenshots/The actuel candidene math we've been ceeling la lunt thit, once, in one table.png`
- `system_v5/READ ONLY Reference Docs/operator math explicit.md`
  - four base operators only; `UP / DOWN` is not extra operator math by itself: lines 1-6
  - exact operator packet: `Ti`, `Te`, `Fi`, `Fe`
- `system_v5/READ ONLY Reference Docs/outdated system math and geometry.md`
  - old formalized stack: constraints, geometry/carrier, axes 0-6, exact operators, engine types, and next move to extend terrain generators / 16 placements / graph-topology objects / engine loop ownership

Any runtime that uses `Se/Ne/Ni/Si` terrain labels without the chart-locked operator token, Axis 5 family, Axis 6 sign, loop placement, sheet/type, and exact class-correct observable/readout is insufficient for this project.

## Immediate Audit Findings

### F1. The current runtime anchor drops ordered operator tokens.

`system_v5/ops/formal_scouts/qit_engine_runtime.py` uses terrain-only stage orders:

- `ENGINE_STAGE_ORDERS` at lines 50-58 contains only `Se`, `Ne`, `Ni`, `Si`.
- `terrain_stage_channels` at lines 143-172 returns only terrain-keyed channels.

This omits chart-locked tokens such as `NiTe`, `SiTe`, `TeNi`, `TeSi`, `FeSi`, `NiFe`, etc. It also omits Axis 6 sign and operator-first versus terrain-first precedence as first-class runtime data.

### F2. The richer operator-token map exists elsewhere but was not the enforced runtime anchor.

`system_v5/ops/formal_scouts/canonical_qit_engine_specs.py` does carry the missing structure:

- native operator sets: lines 122-127
- operator family table: lines 129-134
- `CHART_TOKEN_PRECEDENCE`: lines 136-153
- `get_chart_token_spec`: lines 478-493
- `get_operator_slot_spec`: lines 496-549

But later scouts used `qit_engine_runtime.py` as the shared runtime anchor, which means the richer chart-locked spec was not consistently load-bearing.

### F3. The PEPS/PEPS3D inventory is not an operator-axis inventory.

`system_v5/ops/formal_scouts/sim_two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe.py` claims a 16-placement inventory at lines 11-17 and imports `qit_engine_runtime.py` at line 38. Its placement rows are based on sheet, loop, stage index, and terrain only. It does not make `NiTe`, `SiTe`, Axis 5 family, Axis 6 sign, or precedence load-bearing.

Therefore D130 is useful only as a tiny terrain-only tensor substrate inventory. It must not be cited as evidence that the 16 operator-axis placements ran correctly.

### F4. The Te/Ni/Si issue exposes a layer-separation rule that was not enforced.

The reference docs keep separate:

- exact table language where `Te` is `x`-basis dephasing/projection (`JUNGIAN...` lines 208-211; Atlas lines 429-464; `operator math explicit.md` line 279 onward);
- semantic/Rosetta language where `Te` can carry gradient / Hamiltonian-drive meaning (`apple axes terrain operator math.md` lines 323-341);
- chart tables where `NiTe` and `SiTe` are terrain-first `Te-down` tokens on the conjugated `Ni/Si` side (`JUNGIAN...` line 276; Atlas line 593; screenshot `Terrain.png`).

These are not interchangeable columns. The exact operator map, semantic role, ordered token, terrain/topology, and loop/sheet placement must all survive into the runtime event row. A sim may not silently collapse them and then claim axis fidelity.

### F5. At least 26 recent formal scouts import or depend on `qit_engine_runtime.py`.

Every result depending on the simplified terrain-only runtime must be quarantined for operator-axis promotion until checked against the chart-locked spec. This does not mean every numeric result is false; it means the results cannot be used as evidence that the full axes/operator/terrain manifold is running.

## Quarantine Scope

Quarantine for operator-axis promotion:

- `qit_engine_runtime.py` as a full runtime authority.
- D90-D130 style results that cite `qit_engine_runtime.py` as the runtime anchor.
- D130 PEPS/PEPS3D stage-loop inventory as a full 16-placement claim.
- Any sidequest or formal result that applies one readout family across all 16 placements without proving it is class-correct per Axis 5 / Axis 6.
- Any result that treats Jungian labels as sufficient evidence without the axis/operator/terrain table.

Still usable with caveat:

- source documents and screenshots as authority surfaces;
- result JSONs as historical evidence of what was run;
- tensor substrate plumbing as implementation evidence only, not as operator-axis manifold evidence;
- `canonical_qit_engine_specs.py` as a possible recovery anchor, pending audit.

## Audit Required Before Any Further Build

1. Build a source authority matrix.
   - Rows: source doc/screenshot/table.
   - Columns: terrain, operator, Axis 5 family, Axis 6 sign, precedence, loop, sheet/type, exact channel, semantic class, readout observable.
   - Explicitly mark conflicts.

2. Build a runtime conformance matrix.
   - Compare `canonical_qit_engine_specs.py`, `qit_engine_runtime.py`, `engine_core.py`, current PEPS/PEPS3D scouts, MPS scouts, and Axis0 scouts.
   - Mark each as `source_conformant`, `partial`, `terrain_only`, `contradictory`, or `decorative_axis_labels`.

3. Quarantine claims.
   - For every result that depends on `qit_engine_runtime.py`, mark whether it is still usable as:
     - terrain-only numeric evidence;
     - tensor plumbing evidence;
     - spectral evidence for simplified channel;
     - operator-axis evidence;
     - invalid for promotion.

4. Repair the runtime only after audit.
   - Runtime event rows must include:
     - `perception/topology`
     - terrain name
     - ordered token
     - operator
     - Axis 5 family
     - Axis 6 sign
     - precedence
     - loop
     - sheet/type
     - exact channel family
     - class-correct observable/readout
   - A scout must fail if any of these are missing.

5. Only then restart MPDO/PEPS/PEPS3D work.
   - No PEPS/PEPS3D MPDO scout should run until the operator-axis runtime rows are source-conformant.

## Replacement Source Audit

The active replacement audit package is:

- `system_v5/ops/QIT_ENGINE_SOURCE_AUTHORITY_AUDIT_20260522.md`
- `system_v5/ops/NEXT_GOAL_QIT_ENGINE_SOURCE_AUTHORITY_AUDIT_PROMPT_20260522.md`

The old full-build prompt remains retired. The next admissible move is source-authority and runtime-conformance work, not another engine run.

## Current Admission Status

`final_manifold_admission_allowed=false`.

`full_qit_engine_goal_complete=false`.

Current reason: operator-axis/runtime drift, not merely Phi0 or tensor-network incompleteness.

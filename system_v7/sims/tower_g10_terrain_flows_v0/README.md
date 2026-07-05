# Tower G10 Terrain Flows v0

Rerunnable scratch packet for the eight terrain generators as flows on the G5
density-matrix floor. The terrains are geometry on the state manifold, not axes.

Source anchors read for this packet:

- `system_v7/sims/ASSEMBLY_INVENTORY_20260704.md`, G10 row and rerun notes.
- `system_v7/sims/TYPE1_ENGINE_EXTRACTION_20260703.md`, Type-1 quartet and Type-2 boundary.
- `system_v7/sims/AXIS_RELATION_ALGEBRA_EXTRACTION_20260703.md`, anti-collapse rules.
- `system_v7/constraint_core/reference_docs_from_josh/physics_program/working_math_scaffold_20260609.md`, sections 4.1, 4.2, 4.3, 19.
- `system_v7/constraint_core/reference_docs_from_josh/physics_program/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md`, terrain placement table.

Run:

```sh
$(make -pn | awk '/^SIM_PY /{print $3; exit}') tower_g10_terrain_flows_v0_jax.py
$(make -pn | awk '/^SIM_PY /{print $3; exit}') tower_g10_terrain_flows_v0_pytorch.py
julia tower_g10_terrain_flows_v0_julia.jl
$(make -pn | awk '/^SIM_PY /{print $3; exit}') check_agreement.py
```

Claim ceiling: `scratch_diagnostic`, `promotion_allowed=false`.

# QIT Graph Promotion Gates

> Defines when a QIT concept moves from bounded sidecar projection to owner-layer truth.
> No sidecar may claim semantic ownership without passing its promotion gate.

---

## General Gate Requirements

Every promotion must satisfy ALL of these before the concept moves inward:

1. **Negative proof exists.** A SIM must demonstrate that removing the sidecar's semantic contribution breaks something measurable. If you can remove it and nothing changes, it's not owner-worthy.
2. **Pydantic schema exists.** The promoted concept must have a typed contract in `qit_owner_schemas.py` before it enters the owner graph.
3. **Round-trip test passes.** The concept must survive serialization to JSON and deserialization back without loss. Owner truth must be JSON-representable.
4. **No sidecar dependency at read time.** Other components must be able to read the promoted concept from the owner graph WITHOUT having TopoNetX, clifford, PyG, or any sidecar installed.
5. **Human audit.** At least one human must verify the promotion makes physical sense before it lands.

---

## Gate 1: Torus Semantics Promotion

**What moves**: Torus surfaces from TopoNetX 2-cell projections to owner-layer truth.

| Requirement | Status | Evidence Needed |
|---|---|---|
| Negative proof | ✅ `sim_neg_no_torus_transport.py` and `sim_neg_torus_scrambled.py` already KILL | Both produce graveyard kills |
| Pydantic schema | ✅ `TorusState` exists in `qit_owner_schemas.py` | Validated |
| Round-trip test | ⬜ Not yet tested | Need to serialize TopoNetX 2-cell boundaries as JSON edge lists |
| No sidecar dependency | ⬜ Not yet verified | Owner graph must store torus boundary loops as explicit edge sets, not as TopoNetX objects |
| Human audit | ⬜ Pending | — |

**What changes on promotion**: Owner graph stores the torus 2-cell boundaries as explicit lists of boundary edges (the 1-cells forming each torus loop), instead of only the node identities. The TopoNetX CellComplex becomes regenerable from owner data rather than being the only place this information exists.

---

## Gate 2: Chirality Payload Promotion

**What moves**: Cl(3) pseudoscalar chirality semantics from clifford edge payloads to owner-layer edge attributes.

| Requirement | Status | Evidence Needed |
|---|---|---|
| Negative proof | ✅ `sim_neg_no_chirality.py` and `neg_type_flatten_stage_matrix_sim.py` KILL | Chirality removal destroys asymmetry |
| Pydantic schema | ✅ `CliffordEdgePayload` exists | With grade-3 pseudoscalar mapping |
| Round-trip test | ⬜ Not yet tested | Need to serialize Cl(3) coefficients as flat JSON arrays |
| No sidecar dependency | ⬜ Not yet verified | Owner graph must store the 8 coefficients as a plain `list[float]`, not require `clifford` library to interpret |
| Human audit | ⬜ Pending | — |

**What changes on promotion**: `CHIRALITY_COUPLING` edges in the owner graph gain an `algebraic_payload` attribute containing `[0,0,0,0,0,0,0,1.0]` as a plain list. The clifford library becomes optional for reading (still useful for computation).

---

## Gate 3: Stage/Subcycle Topology Promotion

**What moves**: Stage 1-cycles and stage-diamond 2-cells from TopoNetX projections to owner-layer truth.

| Requirement | Status | Evidence Needed |
|---|---|---|
| Negative proof | ✅ Multiple negative SIMs kill on stage order violation | `neg_missing_operator_stage_matrix_sim.py`, etc. |
| Pydantic schema | ✅ `MacroStage`, `SubcycleStep` exist | With `closes_cycle` edge attribute |
| Round-trip test | ⬜ Not yet tested | Need to verify cycle closure is recoverable from JSON edge list alone |
| No sidecar dependency | ✅ Already satisfied | `STAGE_SEQUENCE` edges with `closes_cycle: true` are sufficient to reconstruct the cycle without TopoNetX |
| Human audit | ⬜ Pending | — |

**What changes on promotion**: Owner graph explicitly marks which edge sets form closed cycles (already partially done via `closes_cycle` attribute). TopoNetX verification becomes a consistency check rather than the source of cycle truth.

---

## Gate 4: Axis 0 Runtime Integration

**What moves**: Axis 0 from a structural identity (it exists) to a runtime-governing variable (it controls entropy gradients during engine execution).

| Requirement | Status | Evidence Needed |
|---|---|---|
| Negative proof | ✅ `sim_neg_axis0_frozen.py` KILLS | Freezing Axis 0 destroys entropy flow |
| Pydantic schema | ✅ `AxisState` exists | With `proven: true` |
| Round-trip test | ⬜ Not yet tested | Need state-graph axis readings to serialize |
| No sidecar dependency | ⬜ Not yet verified | Runtime axis readings are pure NumPy — no sidecar needed, but need JSON format |
| Human audit | ⬜ Pending | — |

**What changes on promotion**: State graph gains `axis_0_level: float` on ENGINE nodes, updated each engine step. History graph records axis trajectories per run.

---

## Promotion Ceremony

When a gate is fully satisfied:

1. PR title: `promote: [concept] from [sidecar] sidecar to owner truth`
2. Add the new attributes to the owner JSON schema
3. Update `qit_engine_graph_builder.py` to emit the promoted attributes
4. Update `qit_owner_schemas.py` with any new fields
5. Run the full autoresearch harness to verify no regressions
6. Update `QIT_GRAPH_SIDECAR_POLICY.md` to reflect the changed permissions
7. Update this file to mark the gate as `✅ PROMOTED`

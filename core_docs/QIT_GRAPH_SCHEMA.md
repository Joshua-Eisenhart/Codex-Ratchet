# QIT Graph Schema — Canonical Node & Edge Inventory

> Source of truth for the current owner-layer QIT graph surface.
> Owner contracts: `system_v4/skills/qit_owner_schemas.py`
> Builder: `system_v4/skills/qit_engine_graph_builder.py`
> Live graph: `system_v4/a2_state/graphs/qit_engine_graph_v1.json`

---

## Live Owner Graph

- Schema: `QIT_ENGINE_GRAPH_v2`
- Nodes: `105`
- Edges: `272`
- Live node types: `7`
- Live relation types: `11`
- Schema-ready but not instantiated: `WEYL_BRANCH`

The current owner graph carries:

- repo-standard owner metadata (`owner_layer`, `materialized`, `build_status`, `derived_from`, `selection_contract`)
- stable `public_id` on every node
- stable `edge_id` on every edge
- `public_id_index` for explicit cross-layer admission
- `content_hash` for snapshot-level provenance

---

## Node Types

| Node Type | Count | Owner Schema | Description |
|---|---:|---|---|
| `ENGINE` | 2 | `EngineType` | Deductive (`type1_left_weyl`) and Inductive (`type2_right_weyl`) engine identities |
| `MACRO_STAGE` | 16 | `MacroStage` | One of the 8 canonical terrains within one engine type |
| `OPERATOR` | 4 | `SubcycleOperator` | Fixed operator family: `Ti`, `Fe`, `Te`, `Fi` |
| `TORUS` | 3 | `TorusState` | Nested Hopf torus identities: `inner`, `clifford`, `outer` |
| `AXIS` | 7 | `AxisState` | Load-bearing axes `axis_0` through `axis_6` |
| `NEG_WITNESS` | 9 | `NegativeWitness` | Kill witnesses proving specific structures are necessary |
| `SUBCYCLE_STEP` | 64 | `SubcycleStep` | One operator application within one macro-stage (`16 stages × 4 operators`) |

**Live total:** `105` nodes

### Schema-Ready But Not Instantiated

| Node Type | Owner Schema | Description |
|---|---|---|
| `WEYL_BRANCH` | `WeylBranch` | Left/right spinor branch schema exists, but the live owner graph does not emit these nodes yet |

---

## Owner Node Attributes

| Attribute | Applies To | Description |
|---|---|---|
| `public_id` | all nodes | Stable join handle, e.g. `qit::ENGINE::type1_left_weyl` |
| `label` | all nodes | Human-readable display label |
| `engine_type` | `MACRO_STAGE`, `SUBCYCLE_STEP` | Which engine family the stage/step belongs to |
| `terrain` | `MACRO_STAGE`, `SUBCYCLE_STEP` | Canonical terrain code such as `Se_f` |
| `loop` | `MACRO_STAGE` | `fiber` or `base` |
| `mode` | `MACRO_STAGE` | `expand` or `compress` |
| `boundary` | `MACRO_STAGE` | `open` or `closed` |
| `stage_index` | `MACRO_STAGE` | Position `0..7` in the engine-family stage loop |
| `action` | `OPERATOR` | Operator action summary |
| `nesting_rank` | `TORUS` | `0=inner`, `1=clifford`, `2=outer` |
| `proven` | `AXIS` | Whether the axis is currently treated as load-bearing in this owner graph |
| `negative_witness` | `AXIS` | Negative sim reference when present |
| `target_structure` | `NEG_WITNESS` | `TORUS`, `AXIS`, `OPERATOR`, or `CHIRALITY` |
| `specific_targets` | `NEG_WITNESS` | Explicit owner members named by the witness when the proof is narrower than a whole class |
| `owner_edge_emission` | `NEG_WITNESS` | Whether owner proof edges are emitted directly, swept per member, or suppressed pending a better owner concept |
| `proves_label` | `NEG_WITNESS` | Witness-specific proof claim carried onto any emitted `NEGATIVE_PROVES` edges |
| `operator` | `SUBCYCLE_STEP` | The operator used at this step |
| `position_in_subcycle` | `SUBCYCLE_STEP` | Fixed subcycle slot `0=Ti`, `1=Fe`, `2=Te`, `3=Fi` |

---

## Edge Relations

| Relation | Source → Target | Count | Sidecar Cl(3) Grade | Description |
|---|---|---:|---:|---|
| `ENGINE_OWNS_STAGE` | `ENGINE → MACRO_STAGE` | 16 | 1 | Engine-family ownership of its 8 stages |
| `STAGE_SEQUENCE` | `MACRO_STAGE → MACRO_STAGE` | 16 | 1 | Canonical 8-stage order within each engine family |
| `SUBCYCLE_ORDER` | `OPERATOR → OPERATOR` | 4 | 1 | Global operator cycle `Ti → Fe → Te → Fi → Ti` |
| `STEP_IN_STAGE` | `SUBCYCLE_STEP → MACRO_STAGE` | 64 | 1 | Each runtime step belongs to one macro-stage |
| `STEP_USES_OPERATOR` | `SUBCYCLE_STEP → OPERATOR` | 64 | 1 | Each runtime step uses one fixed operator |
| `STEP_SEQUENCE` | `SUBCYCLE_STEP → SUBCYCLE_STEP` | 48 | 1 | In-stage order `Ti → Fe → Te → Fi` |
| `STAGE_ON_TORUS` | `MACRO_STAGE → TORUS` | 32 | 2 | Primary/shared torus placement for each stage |
| `TORUS_NESTING` | `TORUS → TORUS` | 2 | 2 | `inner → clifford → outer` nesting chain |
| `CHIRALITY_COUPLING` | `ENGINE → ENGINE` | 1 | 3 | Complementary engine-family coupling |
| `AXIS_GOVERNS` | `AXIS → ENGINE` | 14 | 1 | Each axis governs both engine families |
| `NEGATIVE_PROVES` | `NEG_WITNESS → owner node` | 11 | 2 | Negative proof edges only where the witness names a faithful owner-level target |

**Live total:** `272` edges

> The `Sidecar Cl(3) Grade` column is a bounded sidecar mapping from `graph_tool_integration.py`, not an owner payload stored directly on the live graph edges.

---

## Owner Edge Attributes

| Attribute | Applies To | Description |
|---|---|---|
| `edge_id` | all edges | Stable edge handle derived from relation + endpoint public ids |
| `source_public_id` / `target_public_id` | all edges | Stable public endpoint refs carried alongside hashed node ids |
| `closes_cycle` | `STAGE_SEQUENCE`, `SUBCYCLE_ORDER` | Marks the edge that closes the loop |
| `position` | `SUBCYCLE_ORDER`, `STEP_SEQUENCE` | Sequence slot within the fixed cycle |
| `engine_type` | `STAGE_SEQUENCE` | Engine family for the stage loop |
| `loop` | `STAGE_ON_TORUS` | `fiber` or `base` torus assignment |
| `primary` | `STAGE_ON_TORUS` | Whether this is the primary torus for the stage |
| `shared` | `STAGE_ON_TORUS` | Shared Clifford torus marker |
| `axis` | `AXIS_GOVERNS` | The governing axis id |
| `operator` | `STEP_IN_STAGE` | Which operator this step represents |
| `proves` | `NEGATIVE_PROVES` | What the negative witness is taken to prove |
| `scope` | `NEGATIVE_PROVES` | Whether the proof edge comes from specific named targets or a per-member sweep |

---

## Current Boundaries

- `WEYL_BRANCH` is schema-ready but not live.
- Runtime state/history are still graph-adjacent packet surfaces, not promoted owner subgraphs.
- Cross-layer QIT integration requires explicit bridge admission outside the owner builder.
- Sidecar projections remain bounded read-only carriers, not semantic owners.

---

## Verification

```bash
python3 system_v4/skills/qit_owner_schemas.py
python3 system_v4/skills/qit_engine_graph_builder.py
python3 system_v4/skills/qit_graph_stack_runtime.py
python3 system_v4/skills/qit_graph_stack_runtime.py --write-report
```

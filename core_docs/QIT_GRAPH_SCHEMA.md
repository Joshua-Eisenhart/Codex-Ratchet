# QIT Graph Schema — Canonical Node & Edge Inventory

> Source of truth for every node type and edge type in the QIT Engine graph layer.
> Owner: `system_v4/skills/qit_owner_schemas.py` (Pydantic contracts)
> Graph: `system_v4/a2_state/graphs/qit_engine_graph_v1.json`
> Builder: `system_v4/skills/qit_engine_graph_builder.py`

---

## Node Types

| Node Type | Count | Owner Schema | Description |
|---|---|---|---|
| `ENGINE_TYPE` | 2 | `EngineType` | Deductive (Type 1) or Inductive (Type 2) engine |
| `MACRO_STAGE` | 16 | `MacroStage` | One terrain (Se_f, Si_f, Ne_f, Ni_f, Se_b, Si_b, Ne_b, Ni_b) within one engine type |
| `OPERATOR` | 4 | `SubcycleOperator` | Ti (constrain), Fe (release), Te (explore), Fi (filter) |
| `TORUS` | 3 | `TorusState` | Inner (rank 0), Clifford (rank 1), Outer (rank 2) |
| `WEYL_BRANCH` | — | `WeylBranch` | Left or right spinor branch. Not yet instantiated in the graph; schema-ready. |
| `AXIS` | 7 | `AxisState` | Load-bearing axes 0–6, each with a negative witness link |
| `NEG_WITNESS` | 9 | `NegativeWitness` | Graveyard kill proving a specific structure is necessary |

**Total**: 41 nodes (16 + 4 + 3 + 2 + 7 + 9)

### Node Attributes (Owner-Layer Only)

| Attribute | Applies To | Type | Description |
|---|---|---|---|
| `engine_type` | `MACRO_STAGE` | enum | Which engine owns this stage |
| `terrain` | `MACRO_STAGE` | str | Terrain code (e.g. `Se_f`) |
| `loop` | `MACRO_STAGE` | `fiber` \| `base` | Which Hopf torus loop |
| `mode` | `MACRO_STAGE` | `expand` \| `compress` | Stage mode |
| `boundary` | `MACRO_STAGE` | `open` \| `closed` | Boundary condition |
| `stage_index` | `MACRO_STAGE` | int 0–7 | Position in the 8-stage cycle |
| `action` | `OPERATOR` | str | What the operator does |
| `nesting_rank` | `TORUS` | int 0–2 | 0=inner, 1=Clifford, 2=outer |
| `proven` | `AXIS` | bool | Whether negatively proven |
| `target_structure` | `NEG_WITNESS` | enum | TORUS, AXIS, OPERATOR, or CHIRALITY |

---

## Edge Types

| Edge Type | Source → Target | Count | Cl(3) Grade | Description |
|---|---|---|---|---|
| `ENGINE_OWNS_STAGE` | ENGINE → MACRO_STAGE | 16 | 1 (e₃) | Engine type owns its 8 stages |
| `STAGE_SEQUENCE` | MACRO_STAGE → MACRO_STAGE | 16 | 1 (e₁+e₂) | n→n+1 within each engine type; closes into cycle |
| `SUBCYCLE_ORDER` | OPERATOR → OPERATOR | 4 | 1 (e₁) | Ti→Fe→Te→Fi→Ti; the fixed internal operator cycle |
| `OPERATOR_ACTS_ON` | OPERATOR → MACRO_STAGE | 64 | 1 (e₁+e₃) | Each operator acts on every stage |
| `STAGE_ON_TORUS` | MACRO_STAGE → TORUS | 48 | 2 (e₂∧e₃) | Which torus surface a stage lives on |
| `TORUS_NESTING` | TORUS → TORUS | 2 | 2 (e₁∧e₃) | inner→Clifford→outer |
| `CHIRALITY_COUPLING` | ENGINE → ENGINE | 1 | 3 (e₁₂₃) | Pseudoscalar parity coupling |
| `AXIS_GOVERNS` | AXIS → ENGINE | 14 | 1 (iso) | Each axis governs both engine types |
| `NEGATIVE_PROVES` | NEG_WITNESS → various | 20+ | 2 (−e₁∧e₂) | Each kill proves a structure is necessary |

**Total**: 185 edges

### Edge Attributes (Owner-Layer Only)

| Attribute | Applies To | Type | Description |
|---|---|---|---|
| `closes_cycle` | `STAGE_SEQUENCE`, `SUBCYCLE_ORDER` | bool | True on the edge that completes the loop |
| `engine_type` | `OPERATOR_ACTS_ON`, `STAGE_SEQUENCE` | enum | Which engine this edge belongs to |
| `loop` | `STAGE_ON_TORUS` | `fiber` \| `base` | Which loop family |
| `shared` | `STAGE_ON_TORUS` | bool | True if stage touches the Clifford torus |
| `proves` | `NEGATIVE_PROVES` | str | What the kill demonstrates |
| `position` | `SUBCYCLE_ORDER` | int 0–3 | Position in the operator cycle |

---

## Schema Validation

```bash
python3 system_v4/skills/qit_owner_schemas.py
```

Expected output: `All schemas valid. ✓`

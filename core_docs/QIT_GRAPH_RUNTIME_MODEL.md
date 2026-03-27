# QIT Graph Runtime Model

> How engine execution relates to structure, packetized state overlays, and packetized history/evidence.
> Separates three concerns: **structure**, **state overlays**, and **history/evidence packets**.

---

## The Three Graphs

### 1. Structure Graph (Static)

**What it holds**: The engine's topology. This does not change during a run.

| Content | Example |
|---|---|
| Engine type nodes | `qit::ENGINE::type1_deductive` |
| Macro-stage nodes | `qit::MACRO_STAGE::type1_deductive_Se_f` |
| Operator nodes | `qit::OPERATOR::Ti` |
| Torus nodes | `qit::TORUS::inner` |
| Axis nodes | `qit::AXIS::axis_0` |
| Negative witness nodes | `qit::NEG_WITNESS::neg_no_chirality` |
| All structural edges | `STAGE_SEQUENCE`, `SUBCYCLE_ORDER`, `TORUS_NESTING`, etc. |

**Location**: `system_v4/a2_state/graphs/qit_engine_graph_v1.json`
**Builder**: `system_v4/skills/qit_engine_graph_builder.py`
**Mutability**: Rebuilt only when the engine architecture itself changes (new stages, new axes, etc.). Not touched during runtime.

### 2. State Overlay Surface (Dynamic, Packet-Only Today)

**What it holds**: The engine's current position during execution. Changes every step, but today this is surfaced as a graph-adjacent packet rather than a promoted graph.

| State Variable | Type | Description |
|---|---|---|
| `current_stage` | int 0–7 | Which macro-stage is active |
| `current_operator` | int 0–3 | Future finer-grain state field. Not yet surfaced by the current packet-only bridge. |
| `current_engine_type` | enum | Deductive or Inductive |
| `rho_L` | 2×2 complex | Left Weyl spinor density matrix |
| `rho_R` | 2×2 complex | Right Weyl spinor density matrix |
| `eta` | float | Current torus latitude |
| `theta_1` | float | Angle on first circle |
| `theta_2` | float | Angle on second circle |
| `axis_0_level` | float | Current entropy / identity axis value. The current packet bridge exposes this as `ga0_level`. |

**Location**: Not yet instantiated as a graph. Currently lives in `engine_core.py` as the `EngineState` dataclass and can be exported as a graph-adjacent packet or persisted as a read-only audit artifact.

**Smallest real next slice now available**:
- `system_v4/skills/qit_runtime_state_history_adapter.py` emits a graph-adjacent `RuntimeStateOverlay`
- the overlay references stable QIT `public_id`s only and does NOT mutate the owner graph
- the current overlay is stage-granular; it reports active macro-stage and last completed subcycle step, not a live in-flight operator cursor
- `system_v4/skills/qit_runtime_evidence_bridge.py` can persist that runtime slice into a read-only audit-log packet/report without claiming a live state graph

**Future graph form if promoted later**: State would be stored as attribute annotations on structure-graph nodes:
- `MACRO_STAGE` nodes get `active: bool`, `last_activated_utc: str`
- `TORUS` nodes get `current_eta: float`, `current_theta_1: float`
- `ENGINE` nodes get `rho_L: list[list[complex]]`, `rho_R: list[list[complex]]`

**Design rule**: State attributes are mutable overlays on immutable structure nodes. They NEVER change the structure graph's node/edge set.

### 3. History/Evidence Packet Surface (Append-Only Today)

**What it holds**: Every probe outcome, run trajectory, and evidence token ever generated. Today this is packet/file-based, not a promoted graph.

| Content | Example |
|---|---|
| SIM run records | `RUN::sim_L6_master_engine::20260326T090300Z` |
| Evidence tokens | `EVIDENCE::PASS::L6_MASTER_ENGINE` |
| Kill records | `KILL::neg_no_chirality::20260326T085300Z` |
| Trajectory snapshots | `TRAJECTORY::type1_deductive::cycle_42` |
| Harness reports | `REPORT::autoresearch_evaluation_report::20260326T090300Z` |

**Location**: Currently `system_v4/probes/a2_state/sim_results/*.json` (flat files). Not yet a graph.

**Smallest real next slice now available**:
- `system_v4/skills/qit_runtime_state_history_adapter.py` emits an append-only `HistoryRunPacket`
- each step record points at stable `SUBCYCLE_STEP` and `MACRO_STAGE` `public_id`s from the structure graph
- this is still a packet surface, not a promoted history graph
- `system_v4/skills/qit_runtime_evidence_bridge.py` can persist selected run packets plus mapped SIM evidence under `a2_state/audit_logs/` as a read-only bridge surface

**Future graph form if promoted later**: Each run becomes a node with:
- `RUN_EVIDENCES` edges to the `MACRO_STAGE` nodes it exercised
- `RUN_PROVES` edges to the `NEG_WITNESS` nodes it confirmed
- `RUN_TRAJECTORY` edges forming the temporal chain of state snapshots

**Design rule**: Append-only. No deletions. No mutations. Every entry is timestamped.

---

## How a Single Engine Step Touches Each Graph

```
engine.step(state, stage_idx=3)
```

| Graph | What Happens |
|---|---|
| **Structure** | Nothing. Read-only. The step reads the structure to know which operators to apply, which torus to use, which axis governs. |
| **State** | Updated in memory. `current_stage` moves to 3, and the live bridge can export a stage-granular `RuntimeStateOverlay` packet without mutating the owner graph. |
| **History** | Accumulated in memory. The current bridge can export a `HistoryRunPacket` for audit/retrieval use, but there is still no persisted history graph. |

---

## Minimal Runtime Slice

The current honest bridge is:

1. Keep the structure graph immutable and owner-held.
2. Map `EngineState` to a `RuntimeStateOverlay` keyed by stable QIT `public_id`s.
3. Map `state.history` to a `HistoryRunPacket` keyed by stable `SUBCYCLE_STEP` / `MACRO_STAGE` `public_id`s.
4. Keep the adapter packet ephemeral by default; when a concrete audit/retrieval consumer exists, persist it only as read-only audit-log sidecars through `qit_runtime_evidence_bridge.py` and downstream retrieval artifacts.

This keeps runtime and history graph work executable now without overclaiming that a live state graph already exists.

---

## Sidecar Interaction During Runtime

| Sidecar | When It Runs | What It Sees |
|---|---|---|
| **TopoNetX** | Post-run analysis only | Reads the structure graph and computes cell complex views. Does not observe state transitions. |
| **clifford** | Post-run analysis only | Reads edge payloads from the structure graph. Does not modify state. |
| **PyG** | Post-run analysis or future training | Reads structure + optionally state snapshots. Could train on trajectory data from history graph. |
| **QIT retrieval seam (current)** | Post-run or on-demand | Reads QIT docs plus read-only runtime/evidence bridge packets with lexical fallback. Context only, not proof. |
| **LightRAG (target)** | Post-run or on-demand | Embedding-backed retrieval over the same bounded corpus once embedding config is available. Never touches structure or state. |

**No sidecar runs during a live engine step.** Sidecars are offline analysis tools.

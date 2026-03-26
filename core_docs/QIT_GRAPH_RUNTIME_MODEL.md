# QIT Graph Runtime Model

> How engine execution updates graph state over time.
> Separates three graph concerns: **structure**, **state**, and **history**.

---

## The Three Graphs

### 1. Structure Graph (Static)

**What it holds**: The engine's topology. This does not change during a run.

| Content | Example |
|---|---|
| Engine type nodes | `ENGINE::type1_deductive` |
| Macro-stage nodes | `MACRO_STAGE::type1_deductive_Se_f` |
| Operator nodes | `OPERATOR::Ti` |
| Torus nodes | `TORUS::inner` |
| Axis nodes | `AXIS::axis_0` |
| Negative witness nodes | `NEG_WITNESS::neg_no_chirality` |
| All structural edges | `STAGE_SEQUENCE`, `SUBCYCLE_ORDER`, `TORUS_NESTING`, etc. |

**Location**: `system_v4/a2_state/graphs/qit_engine_graph_v1.json`
**Builder**: `system_v4/skills/qit_engine_graph_builder.py`
**Mutability**: Rebuilt only when the engine architecture itself changes (new stages, new axes, etc.). Not touched during runtime.

### 2. State Graph (Dynamic)

**What it holds**: The engine's current position during execution. Changes every step.

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
| `axis_0_level` | float | Current entropy / identity axis value |

**Location**: Not yet instantiated as a graph. Currently lives in `engine_core.py` as the `EngineState` dataclass.

**Smallest real next slice now available**:
- `system_v4/skills/qit_runtime_state_history_adapter.py` emits a graph-adjacent `RuntimeStateOverlay`
- the overlay references stable QIT `public_id`s only and does NOT mutate the owner graph
- the current overlay is stage-granular; it reports active macro-stage and last completed subcycle step, not a live in-flight operator cursor

**Future graph form**: State would be stored as attribute annotations on structure-graph nodes:
- `MACRO_STAGE` nodes get `active: bool`, `last_activated_utc: str`
- `TORUS` nodes get `current_eta: float`, `current_theta_1: float`
- `ENGINE` nodes get `rho_L: list[list[complex]]`, `rho_R: list[list[complex]]`

**Design rule**: State attributes are mutable overlays on immutable structure nodes. They NEVER change the structure graph's node/edge set.

### 3. History/Evidence Graph (Append-Only)

**What it holds**: Every probe outcome, run trajectory, and evidence token ever generated.

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

**Future graph form**: Each run becomes a node with:
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
| **State** | Updated. `current_stage` moves to 3. `rho_L`, `rho_R`, `eta`, `theta_1`, `theta_2` all updated by the 4 operator applications. |
| **History** | Appended. If this is a probe run, the step's outcome (PASS/KILL, entropy delta, axis readings) is logged as a new evidence record. |

---

## Minimal Runtime Slice

The current honest bridge is:

1. Keep the structure graph immutable and owner-held.
2. Map `EngineState` to a `RuntimeStateOverlay` keyed by stable QIT `public_id`s.
3. Map `state.history` to a `HistoryRunPacket` keyed by stable `SUBCYCLE_STEP` / `MACRO_STAGE` `public_id`s.
4. Keep those packets ephemeral by default; only persist them beside a run when a concrete audit/retrieval consumer exists and the output is clearly sidecar-only.

This keeps runtime and history graph work executable now without overclaiming that a live state graph already exists.

---

## Sidecar Interaction During Runtime

| Sidecar | When It Runs | What It Sees |
|---|---|---|
| **TopoNetX** | Post-run analysis only | Reads the structure graph and computes cell complex views. Does not observe state transitions. |
| **clifford** | Post-run analysis only | Reads edge payloads from the structure graph. Does not modify state. |
| **PyG** | Post-run analysis or future training | Reads structure + optionally state snapshots. Could train on trajectory data from history graph. |
| **LightRAG** | Post-run or on-demand | Indexes history/evidence records for retrieval. Never touches structure or state. |

**No sidecar runs during a live engine step.** Sidecars are offline analysis tools.

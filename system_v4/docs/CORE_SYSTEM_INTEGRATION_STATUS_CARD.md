# Core System Integration Status Card

**Date:** 2026-03-30  
**Status:** Working controller support surface.  
**Purpose:** Capture the current real integration state of the QIT engine, `Axis 0` bridge status, graph coupling, daemon and `ctx`/`yaml` control-plane layer, and the two live heartbeat surfaces without smoothing open gaps.

---

## 1. Fully Running

- The constrained geometry stack is live and still validates through the lower layers:
  - `L0` Hopf / `S^3` manifold validation passes.
  - `L1` two-loop-family validation passes.
  - `L2` eight-topological-stage validation passes.
- The composed engine stack is back to passing:
  - `L3` operator validation passes.
  - `L4` engine-family validation passes.
  - `L5` axis orthogonality validation passes.
  - [sim_L6_master_engine.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L6_master_engine.py) currently returns `PASS`.
- The owner QIT graph is real and mechanically aligned to the live engine topology and sequencing:
  - [qit_graph_engine_alignment_probe.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/qit_graph_engine_alignment_probe.py) currently returns `PASS`.
  - The owner graph still matches stage presence, stage order, and subcycle operator order.
- The smallest honest engine-native `Axis 0` control bridge is now live:
  - [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) now exposes `pair_cut_state(state)`, `evaluate_axis0_kernel(rho_ab)`, and `axis0_bridge_snapshot(state)`.
  - The direct-control bridge family is explicitly fenced as `Xi_LR_direct_control`.
- The strict `Axis 0` bakeoff now consumes the engine-native direct-control bridge path:
  - [axis0_xi_strict_bakeoff_sim.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/axis0_xi_strict_bakeoff_sim.py) currently returns `PASS`.
- The deterministic source-registration daemon is real:
  - [run_refinery_daemon.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/runners/run_refinery_daemon.py) watches files, dedups by content hash, queues them FIFO, and ingests them through the A2 graph refinery in deterministic `SOURCE_MAP` mode.
- The `ctx` layer is real as a control-plane spec:
  - [graph.yaml](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/ctx/graph.yaml) is the system DNA.
  - [operating_protocol.yaml](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/ctx/operating_protocol.yaml) is the graph-tick operating procedure.
- The two external surfaces are network-live (not engine-truth surfaces; see Section 3 and Section 5):
  - `https://civic-epoch-vf96.here.now/` returned `HTTP 200` and the page title `Constraint-Driven UI Evolution: CPU Scheduling Applied to Agentic Loops`. **Network-live only — not yet wired to engine state or sim evidence.**
  - `https://rising-island-bswn.here.now/` returned `HTTP 200` and the page title `Leviathan Heartbeat`. **Network-live only — not yet wired to engine state or sim evidence.**

---

## 2. Partially Running

- The QIT engine runtime is partially running, not fully closed:
  - [engine_core.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/engine_core.py) has live two-engine, eight-stage, four-operator runtime machinery.
  - `GA0..GA5` runtime readouts are live.
  - torus-entropy and hemisphere `Axis 0` diagnostics are live.
- The graph coupling is partially real:
  - structure graph is owner-held and aligned
  - runtime coupling exists as packet-based overlays and history packets keyed to stable `public_id`s
  - runtime/evidence bridge exists as read-only audit artifacts
  - the runtime adapter and runtime evidence bridge now both carry a read-only `axis0_bridge_snapshot` packet
  - the runtime adapter and runtime evidence bridge now also carry a read-only `axis0_history_window_snapshot` packet
- The daemon and `ctx`/`yaml` layer are partially integrated:
  - they are integrated with the A2 graph/control-plane path
  - they are not yet deeply integrated with QIT-engine-specific semantics or sim truth-state promotion
- `Axis 0` is partially connected:
  - geometry seat is strong
  - an engine-native direct-control bridge object now exists
  - a read-only history-window Axis 0 control consumer now also exists on the runtime path:
    - `axis0_history_window_snapshot`
    - `Xi_hist_window_control`
  - signed kernel metrics `I(A:B)`, `S(A|B)`, and `I_c` are now available on that direct-control cut-state
  - the direct-control bridge remains MI-trivial on the live engine, so it is a control surface, not final closure
  - `Xi_hist` remains the strongest live nontrivial executable bridge family
  - the strongest constructive bridge family is now cross-temporal chiral (Weyl/chirality-weighted) rather than same-time or direct-only (note: the retro-temporal weighting is noise per Phase 5C; the Weyl/chirality axis is the surviving earned lever)
  - current fixed-marginal evidence is still near-zero in the certified preserving lane
  - current scramble-neutral read holds at the Phase 5C `2σ` threshold
  - shell/interior-boundary remains the strongest doctrine-facing cut family
  - but final process-level closure is still missing

---

## 3. Not Yet Connected

- No final history-shaped or shell-shaped `Xi` family is wired into the runtime loop.
- No engine-native `Axis 0` bridge result currently feeds back into stage execution or control updates.
- No engine-native `Axis 0` bridge packet or history-window control packet is yet consumed by the heartbeat surfaces or by direct `ctx`/`yaml` engine-state logic.
- Read-only control-plane uptake now exists through the persisted `axis0_control_plane_summary` contract:
  - runtime evidence bridge
  - daemon status
  - graph-stack status
  - retrieval sidecar
  - Hopf-Weyl projection sidecar
  - Hopf-Weyl evidence audit
- Runtime `ga0_level` remains a control proxy, not final `Axis 0` doctrine math.
- There is no promoted live runtime-state graph yet.
- There is no promoted live history graph yet.
- The daemon does not yet perform engine-aware refinement of sim outputs into QIT-specific graph truth.
- The external heartbeat/UI pages are not yet shown to be wired into engine state, sim evidence, or `Axis 0` bridge objects.

---

## 4. Graph Daemon And Ctx Layer

### 4.1 Graph layer

- Real now:
  - immutable owner structure graph
  - graph-engine alignment probe
  - packet-based runtime overlay
  - packet-based history run packet
  - read-only runtime/evidence bridge
- Still sidecar only:
  - live state graph
  - promoted history graph
  - advanced sidecars as owner truth

### 4.2 Advanced graph tools

- Ready as bounded read-only projections:
  - `TopoNetX`
  - `clifford`
- Ready only as bounded projection when local dependencies are present:
  - `PyG`
- Not yet ready as active core coupling:
  - `LightRAG` indexing/query, pending embedding configuration

### 4.3 Daemon and ctx/yaml layer

- [run_refinery_daemon.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/runners/run_refinery_daemon.py) is a deterministic source-registration daemon.
- [graph.yaml](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/ctx/graph.yaml) defines the graph-first operating DNA.
- [operating_protocol.yaml](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/ctx/operating_protocol.yaml) defines the ingest-observe-propose-gate-apply-update-emit tick.
- Current limit:
  - the graph/control-plane layer is structurally active
  - engine-aware graph gating and sim/evidence-token admission are not yet tightly wired

---

## 5. External Heartbeat Surfaces

| Surface | Current observed status | Current role read |
|---|---|---|
| `https://civic-epoch-vf96.here.now/` | `HTTP 200`; title `Constraint-Driven UI Evolution: CPU Scheduling Applied to Agentic Loops` | live adjacent UI/control-plane surface |
| `https://rising-island-bswn.here.now/` | `HTTP 200`; title `Leviathan Heartbeat` | live heartbeat/status surface |

Current honest read:

- both surfaces are live
- both look adjacent to orchestration / control-plane visibility
- neither is yet shown to be a direct engine-truth surface

---

## 6. Fundamental Open Issues

- The lower composed QIT engine is honestly running again.
  - Fresh rerun of [sim_L6_master_engine.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_L6_master_engine.py) returns `PASS`.
  - The main remaining gap is not lower-engine breakage; it is incomplete `Axis 0` process closure and higher-layer coupling.
- `Axis 0` is still not fully connected to the engine process.
  - The direct-control `L|R` bridge now exists, but remains too weak to close `Axis 0`.
  - The history-window control consumer now exists on the live runtime path, but it remains read-only and below final `Xi_hist`.
  - The cross-temporal chiral (Weyl/chirality-weighted) constructive bridge family now leads the raw MI search lane, but it remains a constructed cut-state and not an earned fixed-marginal closure. (Retro-temporal weighting is noise per Phase 5C; the Weyl/chirality axis is the surviving lever.)
  - The fixed-marginal lane is now certified near-zero rather than merely unresolved because of solver ambiguity.
  - The scramble-neutral read now holds at the current `2σ` threshold, so temporal order is not yet the main earned lever.
  - The final canon `Xi` is still open.
  - The final doctrine-level cut `A|B` is still open.
  - `Axis 0` remains history-late and cut-late even though it is no longer completely absent from the engine path.
- The graph stack is aligned to engine structure, but not yet promoted to live engine-state truth.
- The daemon and `ctx`/`yaml` surfaces are active, but still closer to graph/control-plane infrastructure than to engine closure.
  - the daemon now has a read-only status uptake of the direct-control and history-window `Axis 0` packets from the persisted runtime evidence bridge
  - the wider local reporting stack now also consumes the same top-level `axis0_control_plane_summary` contract in read-only form
  - the heartbeat/UI side and direct `ctx`/`yaml` engine-state side are still not consuming those packets
- The system still has a process risk:
  - it is easy to drift into symbolic or sidecar work while the core engine/bridge/operator issues remain unresolved

---

## 7. Next Tightening Work

1. Tighten the engine-side `Axis 0` connection past the direct-control bridge:
   - keep `ga0_level` fenced as proxy
   - keep `Xi_LR_direct_control` fenced as control-only
   - keep the current history-window consumer fenced as control-only and compare it against stronger bridge candidates without pretending `Axis 0` is process-closed
   - keep the cross-temporal constructive winner fenced away from fixed-marginal closure
   - keep the fixed-marginal near-zero and scramble-neutral reads visible in the controller surfaces
2. Keep graph work bounded to what helps the engine now:
   - structure alignment
   - runtime/history packet bridges
   - engine-aware evidence ingestion
   - not premature promoted state-graph complexity
3. Use the daemon and heartbeat surfaces as control-plane infrastructure, then connect them to real engine/evidence status only when the engine and `Axis 0` slices are tighter.
4. Keep the clean status docs synchronized with the repaired runtime state so controller-facing surfaces do not lag the real engine path.
5. Use [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md) as the compact navigation entrypoint for the active `Axis 0` controller/owner/support packet stack.

Current best next autoresearch target:

- `earned-vs-constructed Axis 0 seam tightening on the strongest cross-temporal bridge family`

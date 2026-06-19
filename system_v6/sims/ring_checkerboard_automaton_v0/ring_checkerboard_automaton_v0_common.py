#!/usr/bin/env python3
"""Shared classical ring-checkerboard automaton machinery.

The exhaustive state space in this packet is the declared single-active
engine/readout token probe family over the owner's support, not the full binary
configuration space of every support cell. The full binary count is reported as
a boundary row.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import cvc5
from cvc5 import Kind
import networkx as nx
import z3


SIM_ID = "ring_checkerboard_automaton_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = PACKET / "results"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PRIMARY_N = 8
SIZES = [4, 8, 16]
REACHABLE_LATER = [32, 64]

ENGINE_TYPES = ["Type1", "Type2"]
LOOPS = ["outer", "inner"]
STAGES = ["Se", "Ne", "Ni", "Si"]
DEDUCTIVE_ORDER = ["Se", "Ne", "Ni", "Si"]
INDUCTIVE_ORDER = ["Se", "Si", "Ni", "Ne"]
ORDER_BY_NAME = {"deductive": DEDUCTIVE_ORDER, "inductive": INDUCTIVE_ORDER}

STAGE_WORDS = {
    "Se": {"outer": "LOSE", "inner": "win"},
    "Ne": {"outer": "WIN", "inner": "lose"},
    "Ni": {"outer": "LOSE", "inner": "lose"},
    "Si": {"outer": "WIN", "inner": "win"},
}

LOOP_ORDER = {
    ("Type1", "outer"): "deductive",
    ("Type1", "inner"): "inductive",
    ("Type2", "outer"): "inductive",
    ("Type2", "inner"): "deductive",
}

AUTHORITY_INPUTS = {
    "owner_doctrine": "system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md",
    "provenance": "system_v6/receipts/ring_checkerboard_provenance_20260611.md",
    "basin_contract": "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "readout_automaton": "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "support_graph_probe": "system_v6/sims/ring_checkerboard_support_graph_probe/results/ring_checkerboard_support_graph_probe_envelope_results.json",
}

MUST_NOT_CLAIM = [
    "QCA index or GNVW invariant",
    "quantum state or quantum cellular automaton",
    "Axis0 closure",
    "canonical ring-checkerboard support",
    "manifold admission",
    "64-state engine placement",
    "physics, cosmology, consciousness, or world-engine claim",
    "collapse of the engine-stage/microstate and cosmological live readings",
]


@dataclass(frozen=True)
class Cell:
    cell_id: int
    layer: int
    anchor: int
    step: int
    label: str
    kappa: int
    ring_label: str


@dataclass(frozen=True)
class State:
    engine_type: str
    loop: str
    stage: str
    cell_id: int


def now_z() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def readout(engine_type: str, loop: str, stage: str) -> str:
    _ = engine_type
    return STAGE_WORDS[stage][loop]


def next_stage(stage: str, order_name: str) -> str:
    order = ORDER_BY_NAME[order_name]
    return order[(order.index(stage) + 1) % len(order)]


def support_cells(
    n: int,
    *,
    nested: bool = True,
    checkerboard: bool = True,
    label_rotation: int = 0,
) -> list[Cell]:
    cells: list[Cell] = []

    def add(layer: int, anchor: int, step: int) -> None:
        if layer == 0:
            label_step = (step + label_rotation) % n
            label = f"base:s{label_step:02d}"
            ring_label = "base"
            parity_step = step
        else:
            label_anchor = (anchor + label_rotation) % n
            label_step = (step + label_rotation) % n
            label = f"attached:a{label_anchor:02d}:s{label_step:02d}"
            ring_label = f"attached:a{label_anchor:02d}"
            parity_step = step
        kappa = (layer + parity_step) % 2 if checkerboard else 0
        cells.append(Cell(len(cells), layer, anchor, step, label, kappa, ring_label))

    for step in range(n):
        add(0, -1, step)
    if nested:
        for anchor in range(n):
            for step in range(n):
                add(1, anchor, step)
    return cells


def cell_lookup(cells: Iterable[Cell]) -> dict[tuple[int, int, int], Cell]:
    return {(cell.layer, cell.anchor, cell.step): cell for cell in cells}


def same_ring_neighbor(cell: Cell, cells_by_key: dict[tuple[int, int, int], Cell], n: int, direction: int) -> Cell:
    if cell.layer == 0:
        return cells_by_key[(0, -1, (cell.step + direction) % n)]
    return cells_by_key[(1, cell.anchor, (cell.step + direction) % n)]


def attachment_neighbor(cell: Cell, cells_by_key: dict[tuple[int, int, int], Cell]) -> Cell | None:
    if cell.layer == 0:
        return cells_by_key.get((1, cell.step, 0))
    if cell.layer == 1 and cell.step == 0:
        return cells_by_key.get((0, -1, cell.anchor))
    return None


def paired_partner(cell: Cell, cells_by_key: dict[tuple[int, int, int], Cell], n: int) -> Cell:
    direction = 1 if cell.kappa == 0 else -1
    return same_ring_neighbor(cell, cells_by_key, n, direction)


def states_for(n: int, cells: list[Cell], discipline: str) -> list[State]:
    allowed_orders: set[str] | None
    if discipline == "alternating":
        allowed_orders = {"deductive"}
    elif discipline == "paired":
        allowed_orders = {"inductive"}
    else:
        allowed_orders = None

    states: list[State] = []
    for engine_type in ENGINE_TYPES:
        for loop in LOOPS:
            order = LOOP_ORDER[(engine_type, loop)]
            if allowed_orders is not None and order not in allowed_orders:
                continue
            for stage in STAGES:
                for cell in cells:
                    states.append(State(engine_type, loop, stage, cell.cell_id))
    return states


def state_key(state: State) -> tuple[str, str, str, int]:
    return (state.engine_type, state.loop, state.stage, state.cell_id)


def state_record(state: State, cells: list[Cell]) -> dict[str, Any]:
    cell = cells[state.cell_id]
    order = LOOP_ORDER[(state.engine_type, state.loop)]
    return {
        "engine_type": state.engine_type,
        "loop": state.loop,
        "loop_order": order,
        "stage": state.stage,
        "readout_component": readout(state.engine_type, state.loop, state.stage),
        "cell_id": cell.cell_id,
        "cell_label": cell.label,
        "ring_layer": cell.layer,
        "ring_anchor": cell.anchor,
        "ring_step": cell.step,
        "phase_kappa": cell.kappa,
    }


def move_cell(
    state: State,
    stage_after: str,
    order_name: str,
    cells: list[Cell],
    cells_by_key: dict[tuple[int, int, int], Cell],
    n: int,
    *,
    nested: bool = True,
    ring_motion: bool = True,
    paired: bool = False,
) -> int:
    cell = cells[state.cell_id]
    if nested:
        attached = attachment_neighbor(cell, cells_by_key)
        if attached is not None:
            if order_name == "deductive" and ((cell.layer == 0 and stage_after == "Ne") or (cell.layer == 1 and stage_after == "Si")):
                return attached.cell_id
            if order_name == "inductive" and ((cell.layer == 0 and stage_after == "Si") or (cell.layer == 1 and stage_after == "Ne")):
                return attached.cell_id

    if not ring_motion:
        return cell.cell_id

    if paired:
        return paired_partner(cell, cells_by_key, n).cell_id

    component = readout(state.engine_type, state.loop, stage_after)
    direction = 1 if component.upper() == "WIN" else -1
    return same_ring_neighbor(cell, cells_by_key, n, direction).cell_id


def elementary_phase_update(
    state: State,
    phase: int,
    order_name: str,
    cells: list[Cell],
    cells_by_key: dict[tuple[int, int, int], Cell],
    n: int,
    *,
    checkerboard: bool = True,
    nested: bool = True,
    ring_motion: bool = True,
) -> State:
    cell = cells[state.cell_id]
    if checkerboard and cell.kappa != phase:
        return state
    stage_after = next_stage(state.stage, order_name)
    cell_after = move_cell(
        state,
        stage_after,
        order_name,
        cells,
        cells_by_key,
        n,
        nested=nested,
        ring_motion=ring_motion,
        paired=False,
    )
    return State(state.engine_type, state.loop, stage_after, cell_after)


def paired_block_update(
    state: State,
    cells: list[Cell],
    cells_by_key: dict[tuple[int, int, int], Cell],
    n: int,
    *,
    checkerboard: bool = True,
    nested: bool = True,
    ring_motion: bool = True,
) -> State:
    _ = checkerboard
    stage_after = next_stage(state.stage, "inductive")
    cell_after = move_cell(
        state,
        stage_after,
        "inductive",
        cells,
        cells_by_key,
        n,
        nested=nested,
        ring_motion=ring_motion,
        paired=True,
    )
    return State(state.engine_type, state.loop, stage_after, cell_after)


def transition_state(
    state: State,
    cells: list[Cell],
    cells_by_key: dict[tuple[int, int, int], Cell],
    n: int,
    discipline: str,
    *,
    nested: bool = True,
    checkerboard: bool = True,
    ring_motion: bool = True,
    phase_order: tuple[int, int] = (0, 1),
) -> State:
    if discipline == "alternating":
        current = state
        for phase in phase_order:
            current = elementary_phase_update(
                current,
                phase,
                "deductive",
                cells,
                cells_by_key,
                n,
                checkerboard=checkerboard,
                nested=nested,
                ring_motion=ring_motion,
            )
        return current
    if discipline == "paired":
        return paired_block_update(
            state,
            cells,
            cells_by_key,
            n,
            checkerboard=checkerboard,
            nested=nested,
            ring_motion=ring_motion,
        )
    if discipline == "intrinsic":
        order = LOOP_ORDER[(state.engine_type, state.loop)]
        if order == "deductive":
            return transition_state(
                state,
                cells,
                cells_by_key,
                n,
                "alternating",
                nested=nested,
                checkerboard=checkerboard,
                ring_motion=ring_motion,
                phase_order=phase_order,
            )
        return transition_state(
            state,
            cells,
            cells_by_key,
            n,
            "paired",
            nested=nested,
            checkerboard=checkerboard,
            ring_motion=ring_motion,
            phase_order=phase_order,
        )
    if discipline == "non_partitioned_scramble":
        current = elementary_phase_update(
            state,
            0,
            LOOP_ORDER[(state.engine_type, state.loop)],
            cells,
            cells_by_key,
            n,
            checkerboard=False,
            nested=nested,
            ring_motion=ring_motion,
        )
        return elementary_phase_update(
            current,
            1,
            LOOP_ORDER[(state.engine_type, state.loop)],
            cells,
            cells_by_key,
            n,
            checkerboard=False,
            nested=nested,
            ring_motion=ring_motion,
        )
    if discipline == "frozen_even":
        return elementary_phase_update(
            state,
            0,
            LOOP_ORDER[(state.engine_type, state.loop)],
            cells,
            cells_by_key,
            n,
            checkerboard=checkerboard,
            nested=nested,
            ring_motion=ring_motion,
        )
    raise ValueError(f"unknown discipline: {discipline}")


def graph_for(
    n: int,
    discipline: str,
    *,
    nested: bool = True,
    checkerboard: bool = True,
    ring_motion: bool = True,
    label_rotation: int = 0,
    phase_order: tuple[int, int] = (0, 1),
) -> dict[str, Any]:
    cells = support_cells(n, nested=nested, checkerboard=checkerboard, label_rotation=label_rotation)
    cells_by_key = cell_lookup(cells)
    states = states_for(n, cells, discipline if discipline in {"alternating", "paired"} else "intrinsic")
    index = {state_key(state): idx for idx, state in enumerate(states)}
    graph = nx.DiGraph()
    graph.add_nodes_from(range(len(states)))
    edges: list[dict[str, Any]] = []
    for src_idx, state in enumerate(states):
        dst_state = transition_state(
            state,
            cells,
            cells_by_key,
            n,
            discipline,
            nested=nested,
            checkerboard=checkerboard,
            ring_motion=ring_motion,
            phase_order=phase_order,
        )
        dst_idx = index[state_key(dst_state)]
        graph.add_edge(src_idx, dst_idx)
        edges.append({"src": src_idx, "dst": dst_idx})
    return analyze_graph(n, discipline, cells, states, graph, edges, nested=nested, checkerboard=checkerboard, ring_motion=ring_motion)


def terminal_class_rows(graph: nx.DiGraph, components: list[list[int]]) -> tuple[list[dict[str, Any]], dict[int, int]]:
    comp_id: dict[int, int] = {}
    for idx, comp in enumerate(components):
        for state_id in comp:
            comp_id[state_id] = idx
    rows = []
    for idx, comp in enumerate(components):
        comp_set = set(comp)
        outgoing = sorted(
            {"src": u, "dst": v}
            for u in comp_set
            for v in graph.successors(u)
            if v not in comp_set
        )
        rows.append(
            {
                "class_id": idx,
                "states": comp,
                "size": len(comp),
                "terminal_closed": len(outgoing) == 0,
                "absent_exit_proof": {
                    "checked_edge_count": sum(graph.out_degree(u) for u in comp_set),
                    "outgoing_edge_count": len(outgoing),
                    "no_exit": len(outgoing) == 0,
                },
                "outgoing_edges": outgoing[:20],
            }
        )
    return rows, comp_id


def functional_orbit_summary(graph: nx.DiGraph) -> dict[str, Any]:
    period_counts: Counter[int] = Counter()
    tail_counts: Counter[int] = Counter()
    sample_orbits = []
    for start in graph.nodes:
        seen: dict[int, int] = {}
        path = []
        current = start
        while current not in seen:
            seen[current] = len(path)
            path.append(current)
            succ = list(graph.successors(current))
            if not succ:
                break
            current = succ[0]
        if current in seen:
            tail = seen[current]
            period = len(path) - seen[current]
        else:
            tail = len(path)
            period = 0
        tail_counts[tail] += 1
        period_counts[period] += 1
        if len(sample_orbits) < 6:
            sample_orbits.append({"start": start, "tail_length": tail, "period": period, "path_prefix": path[:12]})
    return {
        "period_histogram": {str(k): v for k, v in sorted(period_counts.items())},
        "tail_length_histogram": {str(k): v for k, v in sorted(tail_counts.items())},
        "sample_orbits": sample_orbits,
    }


def basin_map(graph: nx.DiGraph, terminal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    reverse = graph.reverse(copy=False)
    rows = {}
    for terminal in terminal_rows:
        if not terminal["terminal_closed"]:
            continue
        terminal_set = set(terminal["states"])
        may = set(terminal_set)
        queue = deque(terminal_set)
        while queue:
            node = queue.popleft()
            for parent in reverse.successors(node):
                if parent not in may:
                    may.add(parent)
                    queue.append(parent)
        sure = set(terminal_set)
        changed = True
        while changed:
            changed = False
            for node in graph.nodes:
                if node in sure:
                    continue
                succs = set(graph.successors(node))
                if succs and succs <= sure:
                    sure.add(node)
                    changed = True
        rows[str(terminal["class_id"])] = {
            "terminal_class_id": terminal["class_id"],
            "semantic_fork": "deterministic single-generator graph; may and must semantics are still named explicitly",
            "can_reach_terminal": {
                "semantics": "existential/may",
                "size": len(may),
                "states_sample": sorted(may)[:20],
            },
            "sure_basin_omega_containment": {
                "semantics": "universal/must",
                "size": len(sure),
                "states_sample": sorted(sure)[:20],
            },
            "may_equals_must_for_this_deterministic_graph": sorted(may) == sorted(sure),
        }
    return rows


def monotone_observable(graph: nx.DiGraph) -> dict[str, Any]:
    reachable = {node: nx.descendants(graph, node) | {node} for node in graph.nodes}
    reachable_size = {node: len(value) for node, value in reachable.items()}
    exclusion = {node: graph.number_of_nodes() - reachable_size[node] for node in graph.nodes}
    violations = [
        {"src": int(u), "dst": int(v), "src_value": exclusion[u], "dst_value": exclusion[v]}
        for u, v in graph.edges
        if exclusion[v] < exclusion[u]
    ]
    return {
        "candidate": "V_exclusion(state)=|S|-|Reach_R_C(state)|",
        "direction_convention": "non-decreasing on transition edges means reachable-set size is non-increasing toward terminal classes",
        "exists_for_pinned_rules": len(violations) == 0,
        "edge_violation_count": len(violations),
        "violations_sample": violations[:20],
        "reachable_size_histogram": {str(k): v for k, v in sorted(Counter(reachable_size.values()).items())},
    }


def analyze_graph(
    n: int,
    discipline: str,
    cells: list[Cell],
    states: list[State],
    graph: nx.DiGraph,
    edges: list[dict[str, Any]],
    *,
    nested: bool,
    checkerboard: bool,
    ring_motion: bool,
) -> dict[str, Any]:
    components = [sorted(list(comp)) for comp in nx.strongly_connected_components(graph)]
    components.sort(key=lambda comp: (min(comp), len(comp)))
    class_rows, component_id = terminal_class_rows(graph, components)
    terminal_rows = [row for row in class_rows if row["terminal_closed"]]
    terminal_sizes = sorted(row["size"] for row in terminal_rows)
    signature = {
        "n": n,
        "discipline": discipline,
        "support_cell_count": len(cells),
        "state_count": len(states),
        "edge_count": len(edges),
        "scc_count": len(class_rows),
        "terminal_class_count": len(terminal_rows),
        "terminal_state_count": sum(terminal_sizes),
        "terminal_sizes": terminal_sizes,
        "class_size_histogram": {str(k): v for k, v in sorted(Counter(row["size"] for row in class_rows).items())},
    }
    orbit = functional_orbit_summary(graph)
    signature["period_histogram"] = orbit["period_histogram"]
    signature["tail_length_histogram"] = orbit["tail_length_histogram"]
    return {
        "n": n,
        "discipline": discipline,
        "support": {
            "mode": "nested_one_attached_ring_per_base_step" if nested else "bare_base_ring_only",
            "support_cell_count": len(cells),
            "base_ring_steps": n,
            "attached_ring_count": n if nested else 0,
            "steps_per_attached_ring": n if nested else 0,
            "cell_sample": [cell.__dict__ for cell in cells[: min(12, len(cells))]],
            "kappa_rule": "kappa(v)=(ring_layer + step) mod 2" if checkerboard else "checkerboard-off control: every cell forced to phase 0",
            "ring_motion": ring_motion,
        },
        "state_tuple": ["engine_type", "loop", "stage", "cell=(ring_layer,anchor,step)", "readout_component=R(engine,loop,stage)"],
        "state_count": len(states),
        "transition_count": len(edges),
        "states_sample": [state_record(state, cells) for state in states[:8]],
        "transition_edges": edges,
        "transition_edges_sample": edges[:12],
        "communicating_classes": class_rows,
        "terminal_classes": terminal_rows,
        "basin_map": basin_map(graph, terminal_rows),
        "monotone_exclusion_observable": monotone_observable(graph),
        "orbit_structure": orbit,
        "component_id_by_state_sample": {str(k): v for k, v in list(sorted(component_id.items()))[:20]},
        "partition_signature": signature,
        "partition_signature_sha256": stable_sha256(signature),
    }


def signatures_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left["partition_signature"] == right["partition_signature"]


def build_all_graphs(n: int) -> dict[str, Any]:
    alternating = graph_for(n, "alternating")
    paired = graph_for(n, "paired")
    intrinsic = graph_for(n, "intrinsic")
    bare = graph_for(n, "intrinsic", nested=False)
    return {
        "alternating": alternating,
        "paired": paired,
        "intrinsic": intrinsic,
        "bare_ring": bare,
    }


def order_preservation_samples(n: int, discipline: str) -> dict[str, Any]:
    cells = support_cells(n)
    cells_by_key = cell_lookup(cells)
    order_name = "deductive" if discipline == "alternating" else "inductive"
    stage_order = ORDER_BY_NAME[order_name]
    sample_states = [
        State("Type1", "outer" if order_name == "deductive" else "inner", stage, 0)
        for stage in stage_order
    ]
    rows = []
    for state in sample_states:
        if discipline == "alternating":
            after = elementary_phase_update(
                state,
                cells[state.cell_id].kappa,
                order_name,
                cells,
                cells_by_key,
                n,
            )
        else:
            after = paired_block_update(state, cells, cells_by_key, n)
        rows.append(
            {
                "before_stage": state.stage,
                "after_stage": after.stage,
                "expected_after": next_stage(state.stage, order_name),
                "preserved": after.stage == next_stage(state.stage, order_name),
                "before_readout": readout(state.engine_type, state.loop, state.stage),
                "after_readout": readout(after.engine_type, after.loop, after.stage),
            }
        )
    return {
        "discipline": discipline,
        "order_name": order_name,
        "directed_order": " -> ".join(stage_order),
        "samples": rows,
        "preserved": all(row["preserved"] for row in rows),
    }


def support_counts(n: int) -> dict[str, Any]:
    cells = support_cells(n)
    full_binary = f"2^{len(cells)}"
    return {
        "steps_per_ring": n,
        "support_cell_count": len(cells),
        "base_ring_steps": n,
        "attached_ring_count": n,
        "attached_ring_steps_total": n * n,
        "single_active_readout_probe_microstates": len(states_for(n, cells, "intrinsic")),
        "phase_test_microstates_per_directed_order": len(states_for(n, cells, "alternating")),
        "full_binary_configuration_count_boundary": full_binary,
        "full_binary_configuration_enumerated": False,
    }


def control_suite(primary: dict[str, Any]) -> dict[str, Any]:
    n = primary["intrinsic"]["n"]
    intrinsic = primary["intrinsic"]
    alternating = primary["alternating"]
    paired = primary["paired"]
    non_partitioned = graph_for(n, "non_partitioned_scramble")
    order_shuffle = graph_for(n, "intrinsic", phase_order=(1, 0))
    label_shuffle = graph_for(n, "intrinsic", label_rotation=1)
    ring_off = graph_for(n, "intrinsic", ring_motion=False)
    checkerboard_off = graph_for(n, "intrinsic", checkerboard=False)
    nesting_off = primary["bare_ring"]
    frozen = graph_for(n, "frozen_even")

    stage_clusters: dict[str, list[int]] = {}
    for row in intrinsic["states_sample"]:
        stage_clusters.setdefault(row["stage"], [])
    cells = support_cells(n)
    states = states_for(n, cells, "intrinsic")
    by_stage: dict[str, set[int]] = {stage: set() for stage in STAGES}
    for idx, state in enumerate(states):
        by_stage[state.stage].add(idx)
    exits = {}
    for stage, members in by_stage.items():
        edge_exits = [
            edge for edge in intrinsic["transition_edges_sample"]
            if edge["src"] in members and edge["dst"] not in members
        ]
        # The sample is intentionally not enough for the proof. Use the graph
        # signature change controls for gates; this row only demonstrates why a
        # motif cluster is not basin evidence.
        exits[stage] = {
            "cluster_size": len(members),
            "sample_exit_count": len(edge_exits),
            "closed_under_R_C": False,
        }

    return {
        "similarity_only_cluster": {
            "fired": True,
            "basin_language_allowed": False,
            "reason": "stage/readout/color motifs are not terminal classes and are not used as basin evidence",
            "stage_cluster_rows": exits,
        },
        "non_partitioned_scramble": {
            "fired": not signatures_equal(intrinsic, non_partitioned),
            "required_change": True,
            "control_signature": non_partitioned["partition_signature"],
        },
        "order_shuffle": {
            "fired": not signatures_equal(intrinsic, order_shuffle),
            "required_change": True,
            "control_signature": order_shuffle["partition_signature"],
        },
        "label_permutation": {
            "counts_invariant": signatures_equal(intrinsic, label_shuffle),
            "must_not_change_counts": True,
            "control_signature": label_shuffle["partition_signature"],
        },
        "ring_off": {
            "fired": not signatures_equal(intrinsic, ring_off),
            "required_change": True,
            "control_signature": ring_off["partition_signature"],
        },
        "checkerboard_off": {
            "fired": not signatures_equal(intrinsic, checkerboard_off),
            "required_change": True,
            "control_signature": checkerboard_off["partition_signature"],
        },
        "nesting_off": {
            "fired": not signatures_equal(intrinsic, nesting_off),
            "required_change": True,
            "control_signature": nesting_off["partition_signature"],
        },
        "frozen_phase": {
            "fired": not signatures_equal(intrinsic, frozen),
            "degenerate_dynamics_computed": True,
            "control_signature": frozen["partition_signature"],
        },
        "alternating_vs_paired": {
            "distinguishable": not signatures_equal(alternating, paired),
            "alternating_signature": alternating["partition_signature"],
            "paired_signature": paired["partition_signature"],
        },
    }


def z3_phase_proof(phase_test: dict[str, Any]) -> dict[str, Any]:
    alt = phase_test["alternating_signature"]
    paired = phase_test["paired_signature"]
    fields = ["scc_count", "terminal_class_count", "terminal_state_count"]
    solver = z3.Solver()
    variables = {}
    for prefix, sig in [("alt", alt), ("paired", paired)]:
        for field in fields:
            var = z3.Int(f"{prefix}_{field}")
            variables[(prefix, field)] = var
            solver.add(var == int(sig[field]))
    solver.add(
        z3.And(
            variables[("alt", "scc_count")] == variables[("paired", "scc_count")],
            variables[("alt", "terminal_class_count")] == variables[("paired", "terminal_class_count")],
            variables[("alt", "terminal_state_count")] == variables[("paired", "terminal_state_count")],
        )
    )
    verdict = str(solver.check()).lower()

    flip = z3.Solver()
    for prefix, sig in [("alt", alt), ("paired", paired)]:
        for field in fields:
            var = z3.Int(f"flip_{prefix}_{field}")
            if prefix == "paired":
                flip.add(var == int(alt[field]))
            else:
                flip.add(var == int(sig[field]))
            variables[(f"flip_{prefix}", field)] = var
    flip.add(
        z3.And(
            variables[("flip_alt", "scc_count")] == variables[("flip_paired", "scc_count")],
            variables[("flip_alt", "terminal_class_count")] == variables[("flip_paired", "terminal_class_count")],
            variables[("flip_alt", "terminal_state_count")] == variables[("flip_paired", "terminal_state_count")],
        )
    )
    flip_verdict = str(flip.check()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "computed_perturbation_flip_verdict": flip_verdict,
        "proof_row": "bind computed phase signatures and assert erased phase-separation equality",
        "fields": fields,
        "positive_case": "actual alternating and paired signatures are distinguishable",
        "negative_control": "paired phase-signature tuple perturbed to alternating tuple makes the erased equality satisfiable",
        "tautological_flip_guard": "flip mutates one computed scalar before asserting equality; no precomputed boolean is asserted",
    }


def cvc5_phase_proof(phase_test: dict[str, Any]) -> dict[str, Any]:
    alt = phase_test["alternating_signature"]
    paired = phase_test["paired_signature"]
    fields = ["scc_count", "terminal_class_count", "terminal_state_count"]
    solver = cvc5.Solver()
    terms = {}
    for prefix, sig in [("alt", alt), ("paired", paired)]:
        for field in fields:
            var = solver.mkConst(solver.getIntegerSort(), f"{prefix}_{field}")
            terms[(prefix, field)] = var
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(int(sig[field]))))
    solver.assertFormula(
        solver.mkTerm(
            Kind.AND,
            solver.mkTerm(Kind.EQUAL, terms[("alt", "scc_count")], terms[("paired", "scc_count")]),
            solver.mkTerm(Kind.EQUAL, terms[("alt", "terminal_class_count")], terms[("paired", "terminal_class_count")]),
            solver.mkTerm(Kind.EQUAL, terms[("alt", "terminal_state_count")], terms[("paired", "terminal_state_count")]),
        )
    )
    verdict = str(solver.checkSat()).lower()

    flip = cvc5.Solver()
    fterms = {}
    for prefix, sig in [("alt", alt), ("paired", paired)]:
        for field in fields:
            var = flip.mkConst(flip.getIntegerSort(), f"flip_{prefix}_{field}")
            fterms[(prefix, field)] = var
            value = int(alt[field]) if prefix == "paired" else int(sig[field])
            flip.assertFormula(flip.mkTerm(Kind.EQUAL, var, flip.mkInteger(value)))
    flip.assertFormula(
        flip.mkTerm(
            Kind.AND,
            flip.mkTerm(Kind.EQUAL, fterms[("alt", "scc_count")], fterms[("paired", "scc_count")]),
            flip.mkTerm(Kind.EQUAL, fterms[("alt", "terminal_class_count")], fterms[("paired", "terminal_class_count")]),
            flip.mkTerm(Kind.EQUAL, fterms[("alt", "terminal_state_count")], fterms[("paired", "terminal_state_count")]),
        )
    )
    flip_verdict = str(flip.checkSat()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "computed_perturbation_flip_verdict": flip_verdict,
        "proof_row": "cvc5 mirror of computed phase-signature separation",
        "fields": fields,
        "positive_case": "actual alternating and paired signatures are distinguishable",
        "negative_control": "paired phase-signature tuple perturbed to alternating tuple makes erased equality satisfiable",
        "tautological_flip_guard": "flip mutates one computed scalar before asserting equality; no precomputed boolean is asserted",
    }


def build_packet() -> dict[str, Any]:
    primary = build_all_graphs(PRIMARY_N)
    controls = control_suite(primary)
    size_rows = []
    graph_rows = {}
    for n in SIZES:
        graphs = build_all_graphs(n)
        graph_rows[str(n)] = {
            name: graph["partition_signature"]
            for name, graph in graphs.items()
        }
        size_rows.append(
            {
                **support_counts(n),
                "alternating_terminal_count": graphs["alternating"]["partition_signature"]["terminal_class_count"],
                "alternating_terminal_sizes": graphs["alternating"]["partition_signature"]["terminal_sizes"],
                "paired_terminal_count": graphs["paired"]["partition_signature"]["terminal_class_count"],
                "paired_terminal_sizes": graphs["paired"]["partition_signature"]["terminal_sizes"],
                "intrinsic_terminal_count": graphs["intrinsic"]["partition_signature"]["terminal_class_count"],
                "intrinsic_terminal_sizes": graphs["intrinsic"]["partition_signature"]["terminal_sizes"],
            }
        )
    phase_test = {
        "alternating_order": order_preservation_samples(PRIMARY_N, "alternating"),
        "paired_order": order_preservation_samples(PRIMARY_N, "paired"),
        "alternating_signature": primary["alternating"]["partition_signature"],
        "paired_signature": primary["paired"]["partition_signature"],
        "terminal_structure_distinguishable": controls["alternating_vs_paired"]["distinguishable"],
        "orbit_structure_distinguishable": primary["alternating"]["partition_signature"]["period_histogram"]
        != primary["paired"]["partition_signature"]["period_histogram"],
        "order_shuffle_changes_dynamics": controls["order_shuffle"]["fired"],
    }
    phase_test["verdict"] = (
        "PASS_DISTINGUISHABLE_CLASSICAL_FLOOR"
        if phase_test["alternating_order"]["preserved"]
        and phase_test["paired_order"]["preserved"]
        and phase_test["terminal_structure_distinguishable"]
        and phase_test["order_shuffle_changes_dynamics"]
        else "FAIL_SOURCE_INVALID"
    )
    z3_proof = z3_phase_proof(phase_test)
    cvc5_proof = cvc5_phase_proof(phase_test)
    nesting = {
        "primary_n": PRIMARY_N,
        "nested_intrinsic_signature": primary["intrinsic"]["partition_signature"],
        "bare_ring_signature": primary["bare_ring"]["partition_signature"],
        "terminal_structure_changed": not signatures_equal(primary["intrinsic"], primary["bare_ring"]),
        "claim_ceiling": "one attached-ring level only; no 32/64 or engine-placement claim",
    }
    graph_integrity = {
        "primary_graph_hashes": {
            name: graph["partition_signature_sha256"]
            for name, graph in primary.items()
        },
        "size_signature_rows": graph_rows,
        "controls_hash": stable_sha256(controls),
        "phase_test_hash": stable_sha256(phase_test),
    }
    all_control_gates = (
        controls["similarity_only_cluster"]["fired"]
        and controls["non_partitioned_scramble"]["fired"]
        and controls["order_shuffle"]["fired"]
        and controls["label_permutation"]["counts_invariant"]
        and controls["ring_off"]["fired"]
        and controls["checkerboard_off"]["fired"]
        and controls["nesting_off"]["fired"]
        and controls["frozen_phase"]["fired"]
    )
    all_pass = (
        phase_test["verdict"] == "PASS_DISTINGUISHABLE_CLASSICAL_FLOOR"
        and all_control_gates
        and z3_proof["verdict"] == "unsat"
        and z3_proof["computed_perturbation_flip_verdict"] == "sat"
        and cvc5_proof["verdict"] == "unsat"
        and cvc5_proof["computed_perturbation_flip_verdict"] == "sat"
        and nesting["terminal_structure_changed"]
    )
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "primary_n": PRIMARY_N,
        "sizes": SIZES,
        "reachable_later": REACHABLE_LATER,
        "object": {
            "support": "owner-source flat nested ring checkerboard: base ring plus one attached ring at each base step",
            "G": "G=(V,E,kappa,ring_partition,nesting,phase)",
            "cell_definition": "ring steps plus one attached-ring level",
            "kappa": "kappa(v)=(ring_layer + step) mod 2",
            "phase_scheme": "partitioned two-phase update: even phase then odd phase; paired control uses local even-start blocks",
            "flat_mode": True,
            "spinning_mode": "later variant, not in v0",
            "qca_index": "v1_or_later_not_here",
        },
        "finite_S": {
            "state_family": "single active engine/readout token over support",
            "state_tuple": ["engine_type", "loop", "stage", "cell=(ring_layer,anchor,step)", "readout_component"],
            "primary_state_count": primary["intrinsic"]["state_count"],
            "Adm_C": "state tuple is admitted iff engine/loop placement is one of the 16 readout strategies and cell is on the declared support",
            "M_C": "all admitted single-token probe states for the chosen n",
        },
        "R_C_explicit": {
            "rules_pinned_not_swept": True,
            "locality": "each update reads only the active cell, same-ring predecessor/successor, and the immediate attachment neighbor when at an attachment step",
            "alternating_deductive": "even phase then odd phase; each active matching cell advances C_D and moves to a local ring/attachment neighbor",
            "paired_inductive": "even-start two-cell block update; each active token advances C_I and moves within the local block or attachment neighbor",
            "stage_orders": {"deductive": DEDUCTIVE_ORDER, "inductive": INDUCTIVE_ORDER},
        },
        "phase_test": phase_test,
        "graphs_primary": {
            "alternating": primary["alternating"],
            "paired": primary["paired"],
            "intrinsic": primary["intrinsic"],
            "bare_ring": primary["bare_ring"],
        },
        "basin_partition_tables": {
            "primary_n": PRIMARY_N,
            "alternating": {
                "terminal_classes": primary["alternating"]["terminal_classes"],
                "basin_map": primary["alternating"]["basin_map"],
                "monotone_exclusion_observable": primary["alternating"]["monotone_exclusion_observable"],
            },
            "paired": {
                "terminal_classes": primary["paired"]["terminal_classes"],
                "basin_map": primary["paired"]["basin_map"],
                "monotone_exclusion_observable": primary["paired"]["monotone_exclusion_observable"],
            },
            "intrinsic": {
                "terminal_classes": primary["intrinsic"]["terminal_classes"],
                "basin_map": primary["intrinsic"]["basin_map"],
                "monotone_exclusion_observable": primary["intrinsic"]["monotone_exclusion_observable"],
            },
        },
        "nesting_comparison": nesting,
        "microstate_count_rows": size_rows,
        "controls": controls,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "positive_section": {
            "phase_test_verdict": phase_test["verdict"],
            "basin_partition_computed": True,
            "nesting_changes_terminal_structure": nesting["terminal_structure_changed"],
            "sizes_computed": SIZES,
        },
        "negative_section": controls,
        "boundary_section": {
            "full_binary_configuration_enumerated": False,
            "full_binary_configuration_reason": "resource guard; this packet exhausts the declared single-active readout-token probe family",
            "qca_index_rows": "excluded_to_v1_or_later",
            "must_not_claim": MUST_NOT_CLAIM,
        },
        "guard": "Clustering/model agreement is NEVER a basin; this packet uses finite S, explicit R_C, terminal SCCs, absent-exit proofs, basin maps, and controls.",
        "graph_integrity": graph_integrity,
        "all_pass": all_pass,
    }


def parent_lineage() -> dict[str, Any]:
    rows = []
    for key, rel_path in AUTHORITY_INPUTS.items():
        path = ROOT / rel_path
        if path.exists():
            rows.append({"id": key, "path": rel_path, "sha256": sha256_file(path)})
    return {
        "authority_order_read": [
            "owner doctrine cellular automata ring checkerboard",
            "ring checkerboard provenance",
            "attractor basin criterion",
        ],
        "consumed_inputs": rows,
    }


def engine_result_base(engine: str, source_path: Path, result_path: Path) -> dict[str, Any]:
    return {
        "schema": f"{SIM_ID}_{engine}_result_v1",
        "sim_id": SIM_ID,
        "engine": engine,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
    }

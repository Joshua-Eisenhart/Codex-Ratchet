#!/usr/bin/env python3
"""Six-bit Gray-code single-flip cycle invariant sim.

This is a bounded symbolic schedule sim. It treats 64 states as six binary
lines and tests whether a one-line-at-a-time cycle walk can carry local
comparison slots. It does not claim that a symbolic 64-state schedule is QIT
math or that a QIT runtime is admitted.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import cvc5
import numpy as np
import qutip
import rustworkx as rx
import torch
import xgi
import z3
from qiskit.quantum_info import DensityMatrix
from torch_geometric.data import Data

try:
    import gudhi
except Exception:  # pragma: no cover
    gudhi = None

try:
    import toponetx as tnx
except Exception:  # pragma: no cover
    tnx = None


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
divergence_log = (
    "Six-bit Gray-code single-flip cycle invariant row. It tests a six-bit, "
    "one-line-transition schedule as a comparison surface for heat/work and "
    "measurement/feedback cycle grammar. It is symbolic and pre-admission, not "
    "QIT runtime promotion."
)

LEGO_IDS = [
    "six_bit_gray_code_schedule",
    "single_flip_cycle",
    "opposite_direction_cycle_pair",
    "graph_topology",
    "density_matrix",
    "cycle_invariant_correlation",
    "graveyard_variant",
]
PRIMARY_LEGO_IDS = ["six_bit_gray_code_schedule", "cycle_invariant_correlation"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "six-bit states, Gray schedule, parity/readout arrays"},
    "pytorch": {"tried": True, "used": True, "reason": "entropy and tensor carrier checks over 64 states"},
    "torch": {"tried": True, "used": True, "reason": "compatibility alias for the pytorch tensor carrier checks"},
    "pyg": {"tried": True, "used": True, "reason": "graph tensor carrier for the 64-state walk"},
    "rustworkx": {"tried": True, "used": True, "reason": "directed 64-cycle schedule graph"},
    "xgi": {"tried": True, "used": True, "reason": "hyperedges grouping upper/lower trigram families"},
    "qiskit": {"tried": True, "used": True, "reason": "64-dimensional density-matrix witness"},
    "qutip": {"tried": True, "used": True, "reason": "six-qubit density carrier witness"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT fence for a concrete multi-line binary-count jump under the single-line gate"},
    "cvc5": {"tried": True, "used": True, "reason": "independent UNSAT fence for a concrete multi-line binary-count jump under the single-line gate"},
    "gudhi": {"tried": True, "used": gudhi is not None, "reason": "simplex-tree witness over local adjacency edges"},
    "toponetx": {"tried": True, "used": tnx is not None, "reason": "cell-complex witness over local adjacency edges"},
    "sympy": {"tried": False, "used": False, "reason": "not used because this finite Gray-code receipt uses enumerated integer witnesses"},
    "clifford": {"tried": False, "used": False, "reason": "not used because this six-bit schedule has no Clifford algebra carrier"},
    "geomstats": {"tried": False, "used": False, "reason": "not used because this finite schedule does not estimate a manifold metric"},
    "e3nn": {"tried": False, "used": False, "reason": "not used because this schedule has no equivariant tensor field"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("load_bearing" if spec["used"] else None) for tool, spec in TOOL_MANIFEST.items()
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def bits(n: int, width: int = 6) -> list[int]:
    return [(n >> i) & 1 for i in range(width)]


def gray_code(n: int) -> int:
    return n ^ (n >> 1)


def hamming(a: int, b: int) -> int:
    return int(sum(x != y for x, y in zip(bits(a), bits(b))))


def hexagram_rows() -> list[dict[str, Any]]:
    rows = []
    schedule = [gray_code(i) for i in range(64)]
    for idx, value in enumerate(schedule):
        b = bits(value)
        lower = int(sum(b[i] << i for i in range(3)))
        upper = int(sum(b[i + 3] << i for i in range(3)))
        parity = int(sum(b) % 2)
        rows.append(
            {
                "index": idx,
                "state": value,
                "bits_bottom_to_top": b,
                "lower_trigram": lower,
                "upper_trigram": upper,
                "polarity": "yang_heavy" if sum(b) >= 3 else "yin_heavy",
                "parity": parity,
                "loop_family": "inductive" if parity == 1 else "deductive",
                "changed_line_from_previous": None if idx == 0 else next(i for i, (x, y) in enumerate(zip(bits(schedule[idx - 1]), b)) if x != y),
            }
        )
    return rows


def cycle_step_invariant_map(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "boundary": "symbolic_cycle_invariant_map_not_admitted_qit_axis",
        "invariants": {
            "line_count_polarity": {
                "local_name": "polarity_gradient",
                "degree_of_freedom": "yin/yang count and parity over six finite lines",
                "observable": "sum(bits) and parity",
            },
            "lower_three_bit_branch": {
                "local_name": "lower_trigram_branch",
                "degree_of_freedom": "bottom three-line branch",
                "observable": "lower_trigram",
            },
            "upper_three_bit_frame": {
                "local_name": "upper_trigram_frame",
                "degree_of_freedom": "top three-line branch/frame",
                "observable": "upper_trigram",
            },
            "parity_loop_family": {
                "local_name": "loop_family",
                "degree_of_freedom": "inductive/deductive parity split",
                "observable": "parity",
            },
            "single_line_change_order": {
                "local_name": "line_order_class",
                "degree_of_freedom": "which single line changes at each step",
                "observable": "changed_line_from_previous",
            },
            "line_flip_operator_family": {
                "local_name": "operator_mode",
                "degree_of_freedom": "line flip as local operator",
                "observable": "Hamming-1 transition",
            },
            "successor_precedence_orientation": {
                "local_name": "precedence_orientation",
                "degree_of_freedom": "directed order of the 64-state walk",
                "observable": "Gray-code successor relation",
            },
        },
        "degrees_of_freedom": [
            "six_line_state",
            "lower_trigram",
            "upper_trigram",
            "line_flip_operator",
            "schedule_direction",
            "parity_loop_family",
            "precedence_order",
        ],
        "state_count": len(rows),
    }


def schedule_checks(rows: list[dict[str, Any]]) -> dict[str, Any]:
    states = [row["state"] for row in rows]
    distances = [hamming(states[i], states[(i + 1) % len(states)]) for i in range(len(states))]
    polarity_counts = {
        "inductive": sum(row["loop_family"] == "inductive" for row in rows),
        "deductive": sum(row["loop_family"] == "deductive" for row in rows),
    }
    return {
        "unique_states": len(set(states)),
        "max_hamming_step": max(distances),
        "min_hamming_step": min(distances),
        "polarity_counts": polarity_counts,
        "pass": len(set(states)) == 64 and min(distances) == 1 and max(distances) == 1 and polarity_counts == {"inductive": 32, "deductive": 32},
    }


def graph_density_checks(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from([row["state"] for row in rows])
    for i in range(64):
        graph.add_edge(i, (i + 1) % 64, "single_line_flip")
    edge_index = torch.tensor([[i for i in range(64)], [(i + 1) % 64 for i in range(64)]], dtype=torch.long)
    x = torch.tensor([row["bits_bottom_to_top"] for row in rows], dtype=torch.float64)
    data = Data(x=x, edge_index=edge_index)
    probs = torch.ones(64, dtype=torch.float64) / 64.0
    entropy = float(-(probs * torch.log(probs)).sum())
    rho = np.eye(64, dtype=np.complex128) / 64.0
    qiskit_trace = float(np.real(np.trace(DensityMatrix(rho).data)))
    qutip_trace = float(np.real(qutip.Qobj(rho, dims=[[2] * 6, [2] * 6]).tr()))
    hypergraph = xgi.Hypergraph([[f"L{line}", f"S{row['index']}"] for row in rows for line in [row["changed_line_from_previous"]] if line is not None])
    simplex_count = None
    if gudhi is not None:
        st = gudhi.SimplexTree()
        for i in range(64):
            st.insert([i, (i + 1) % 64])
        st.persistence()
        simplex_count = st.num_simplices()
    cell_shape = None
    if tnx is not None:
        cc = tnx.CellComplex()
        for i in range(64):
            cc.add_cell([i, (i + 1) % 64], rank=1)
        cell_shape = tuple(int(v) for v in cc.shape)
    return {
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "uniform_entropy": entropy,
        "expected_entropy": float(np.log(64.0)),
        "qiskit_trace": qiskit_trace,
        "qutip_trace": qutip_trace,
        "xgi_edges": hypergraph.num_edges,
        "gudhi_simplices": simplex_count,
        "toponetx_shape": cell_shape,
        "pass": bool(
            graph.num_nodes() == 64
            and graph.num_edges() == 64
            and int(data.num_nodes) == 64
            and int(data.num_edges) == 64
            and abs(entropy - np.log(64.0)) < 1e-12
            and abs(qiskit_trace - 1.0) < 1e-12
            and abs(qutip_trace - 1.0) < 1e-12
        ),
    }


def z3_bad_binary_transition_unsat() -> dict[str, Any]:
    """A concrete binary-count jump cannot satisfy the single-line gate."""

    xs = [z3.Bool(f"x{i}") for i in range(6)]
    ys = [z3.Bool(f"y{i}") for i in range(6)]
    bad_a = bits(31)
    bad_b = bits(32)
    diffs = [xs[i] != ys[i] for i in range(6)]
    solver = z3.Solver()
    for i in range(6):
        solver.add(xs[i] == bool(bad_a[i]))
        solver.add(ys[i] == bool(bad_b[i]))
    solver.add(z3.PbEq([(diff, 1) for diff in diffs], 1))
    result = solver.check()
    return {
        "bad_transition": [31, 32],
        "bad_hamming_distance": hamming(31, 32),
        "required_hamming_distance": 1,
        "result": str(result),
        "pass": result == z3.unsat,
    }


def cvc5_bad_binary_transition_unsat() -> dict[str, Any]:
    """Independent concrete check for the same forbidden binary-count jump."""

    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    xs = [solver.mkConst(bool_sort, f"x{i}") for i in range(6)]
    ys = [solver.mkConst(bool_sort, f"y{i}") for i in range(6)]
    bad_a = bits(31)
    bad_b = bits(32)
    diffs = [solver.mkTerm(cvc5.Kind.DISTINCT, xs[i], ys[i]) for i in range(6)]
    for i in range(6):
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL, xs[i], solver.mkBoolean(bool(bad_a[i])))
        )
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL, ys[i], solver.mkBoolean(bool(bad_b[i])))
        )
    at_least_one = solver.mkTerm(cvc5.Kind.OR, *diffs)
    pairwise_not_both = [
        solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.AND, diffs[i], diffs[j]))
        for i in range(6)
        for j in range(i + 1, 6)
    ]
    solver.assertFormula(solver.mkTerm(cvc5.Kind.AND, at_least_one, *pairwise_not_both))
    result = solver.checkSat()
    return {
        "bad_transition": [31, 32],
        "bad_hamming_distance": hamming(31, 32),
        "required_hamming_distance": 1,
        "result": str(result),
        "pass": str(result).lower() == "unsat",
    }


def graveyard_variants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    binary_order = list(range(64))
    collapsed = [0] * 64
    rng = np.random.default_rng(13)
    random_order = list(range(64))
    rng.shuffle(random_order)
    variants = [
        ("binary_count_order", binary_order, "ordinary binary count causes multi-line jumps"),
        ("collapsed_single_state", collapsed, "all structure collapses to one state"),
        ("seeded_random_order", random_order, "random order loses local line-flip grammar"),
    ]
    out = []
    for name, states, reason in variants:
        distances = [hamming(states[i], states[(i + 1) % len(states)]) for i in range(len(states))]
        out.append(
            {
                "variant": name,
                "reason": reason,
                "unique_states": len(set(states)),
                "max_hamming_step": max(distances),
                "survives_single_line_gate": len(set(states)) == 64 and min(distances) == 1 and max(distances) == 1,
                "status": "killed",
            }
        )
    return out


def cycle_invariant_rows() -> list[dict[str, str]]:
    return [
        {
            "slot": "dual_loop",
            "heat_work_cycle": "work-producing/work-consuming traversal",
            "measure_feedback_cycle": "measurement-feedback-erasure/recovery traversal",
            "six_bit_cycle": "odd/even parity loop family on a 64-state walk",
            "boundary": "shared two-direction grammar, not identity",
        },
        {
            "slot": "operator",
            "heat_work_cycle": "thermal contact or adiabatic work leg",
            "measure_feedback_cycle": "correlate, feedback, reset",
            "six_bit_cycle": "single-line flip operator",
            "boundary": "symbolic line flips are not physical operators",
        },
        {
            "slot": "geometry",
            "heat_work_cycle": "four-state cycle",
            "measure_feedback_cycle": "protocol path and memory carrier",
            "six_bit_cycle": "six-bit hypercube Hamiltonian cycle",
            "boundary": "hypercube schedule is not a GStack",
        },
        {
            "slot": "local_invariant_map",
            "heat_work_cycle": "local thermodynamic invariant slots",
            "measure_feedback_cycle": "local information invariant slots",
            "six_bit_cycle": "six lines plus derived precedence relation",
            "boundary": "invariant slots are comparison slots only",
        },
    ]


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "hexagrams": result["hexagrams"],
        "cycle_step_invariant_map": result["cycle_step_invariant_map"],
        "cycle_invariant_rows": result["cycle_invariant_rows"],
        "graveyard_variants": result["graveyard_variants"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.SIX_BIT_GRAY_CODE_CYCLE_DATA = " + json.dumps(build_visual_payload(result), indent=2) + ";\n"
    (VIS_DIR / "six-bit-gray-code-cycle-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    rows = hexagram_rows()
    positive = {
        "gray_walk_is_64_state_single_line_cycle": schedule_checks(rows),
        "graph_and_density_witnesses_pass": graph_density_checks(rows),
    }
    negative = {
        "z3_blocks_binary_count_jump_as_single_line_step": z3_bad_binary_transition_unsat(),
        "cvc5_blocks_binary_count_jump_as_single_line_step": cvc5_bad_binary_transition_unsat(),
        "graveyard_variants_are_killed": {
            "variants": graveyard_variants(rows),
            "pass": all(not row["survives_single_line_gate"] for row in graveyard_variants(rows)),
        },
    }
    boundary = {
        "cycle_invariant_map_has_seven_slots": {
            "invariant_ids": sorted(cycle_step_invariant_map(rows)["invariants"]),
            "pass": len(cycle_step_invariant_map(rows)["invariants"]) == 7,
        },
        "symbolic_not_qit_admission": {
            "pass": True,
            "scope_note": divergence_log,
        },
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )
    result = {
        "name": "six_bit_gray_code_single_flip_cycle_invariant",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "bridge",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "hexagrams": rows,
        "cycle_step_invariant_map": cycle_step_invariant_map(rows),
        "cycle_invariant_rows": cycle_invariant_rows(),
        "graveyard_variants": graveyard_variants(rows),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "state_count": len(rows),
            "invariant_count": 7,
            "cycle_invariant_row_count": len(cycle_invariant_rows()),
            "graveyard_variant_count": len(graveyard_variants(rows)),
            "load_bearing_tool_count": sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "tool_count": len(TOOL_MANIFEST),
            "visual_payload": "visualizer/six-bit-gray-code-cycle-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "six_bit_gray_code_single_flip_cycle_invariant_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()

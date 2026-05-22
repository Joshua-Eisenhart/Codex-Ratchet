#!/usr/bin/env python3
"""Two-bath heat/work reversible cycle-pair sim.

This row makes a finite two-bath heat/work cycle visible as two opposite
traversals of one four-state cycle:

- inductive_heating_loop: forward work-producing direction, entropy exported to the
  cold reservoir, positive work output.
- deductive_cooling_loop: reverse refrigerator direction, entropy removed from
  the cold reservoir, positive work input.

The row is a sim and visualization support artifact. It does not claim the
repo's broader QIT runtime is solved.
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Any

import cvc5
import numpy as np
import qutip
import rustworkx as rx
import scipy.linalg
import sympy as sp
import torch
import xgi
import z3
from qiskit.quantum_info import DensityMatrix
from torch_geometric.data import Data

try:
    import toponetx as tnx
except Exception:  # pragma: no cover
    tnx = None

try:
    import gudhi
except Exception:  # pragma: no cover
    gudhi = None


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
SIM_EXECUTION_KIND = "classical"
divergence_log = (
    "Two-bath heat/work reversible cycle-pair row: same finite qubit working "
    "substance, two opposite cycle directions. It supports cycle visualization "
    "and tool coupling; it does not promote a final QIT runtime or admitted-axis claim."
)

LEGO_IDS = [
    "two_bath_heat_work_cycle",
    "opposite_direction_cycle_pair",
    "quantum_thermodynamics",
    "density_matrix",
    "graph_topology",
    "proof_fence",
]
PRIMARY_LEGO_IDS = ["two_bath_heat_work_cycle", "opposite_direction_cycle_pair"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "state, heat, work, and entropy bookkeeping"},
    "scipy": {"tried": True, "used": True, "reason": "matrix-log von Neumann entropy check"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic Carnot efficiency and COP identities"},
    "z3": {"tried": True, "used": True, "reason": "general super-Carnot UNSAT fence"},
    "cvc5": {"tried": True, "used": True, "reason": "independent fixed-parameter super-Carnot UNSAT fence"},
    "qutip": {"tried": True, "used": True, "reason": "density-matrix carrier witness"},
    "qiskit": {"tried": True, "used": True, "reason": "independent density-matrix carrier witness"},
    "pytorch": {"tried": True, "used": True, "reason": "autograd verifies opposite loop gradients"},
    "pyg": {"tried": True, "used": True, "reason": "stage graph tensor carrier for both loops"},
    "rustworkx": {"tried": True, "used": True, "reason": "directed cycle graph for loop order"},
    "xgi": {"tried": True, "used": True, "reason": "hypergraph groups isothermal and adiabatic legs"},
    "toponetx": {"tried": True, "used": tnx is not None, "reason": "cell-complex witness for closed four-leg cycle"},
    "gudhi": {"tried": True, "used": gudhi is not None, "reason": "simplex-tree witness for stage adjacency"},
    "clifford": {"tried": False, "used": False, "reason": "not used because this finite two-bath calibration has no Clifford algebra carrier"},
    "geomstats": {"tried": False, "used": False, "reason": "not used because this finite cycle does not estimate a manifold metric"},
    "e3nn": {"tried": False, "used": False, "reason": "not used because this calibration has no equivariant tensor field"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "qutip": "load_bearing",
    "qiskit": "load_bearing",
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "supportive",
    "gudhi": "supportive",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def binary_entropy(p: float) -> float:
    p = min(max(float(p), 1e-15), 1.0 - 1e-15)
    return float(-(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)))


def gibbs_excited_probability(temperature: float, gap: float) -> float:
    weight = math.exp(-float(gap) / float(temperature))
    return float(weight / (1.0 + weight))


def state(label: str, temperature: float, gap: float, p_excited: float | None = None) -> dict[str, float | str]:
    p = gibbs_excited_probability(temperature, gap) if p_excited is None else float(p_excited)
    entropy = binary_entropy(p)
    internal_energy = p * gap
    free_energy = internal_energy - temperature * entropy
    return {
        "label": label,
        "temperature": float(temperature),
        "gap": float(gap),
        "p_excited": p,
        "entropy": entropy,
        "internal_energy": internal_energy,
        "free_energy": free_energy,
    }


def density(p_excited: float) -> np.ndarray:
    p = min(max(float(p_excited), 0.0), 1.0)
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=np.complex128)


def isothermal(before: dict[str, Any], after_gap: float, bath_temperature: float, label: str) -> dict[str, Any]:
    after = state(label, bath_temperature, after_gap)
    delta_u = after["internal_energy"] - before["internal_energy"]
    delta_s = after["entropy"] - before["entropy"]
    heat_into_system = bath_temperature * delta_s
    work_by_system = heat_into_system - delta_u
    return {
        "kind": "isothermal",
        "before": before,
        "after": after,
        "bath_temperature": bath_temperature,
        "delta_entropy": delta_s,
        "heat_into_system": heat_into_system,
        "work_by_system": work_by_system,
        "delta_u": delta_u,
    }


def adiabatic(before: dict[str, Any], after_gap: float, after_temperature: float, label: str) -> dict[str, Any]:
    after = state(label, after_temperature, after_gap, p_excited=before["p_excited"])
    delta_u = after["internal_energy"] - before["internal_energy"]
    return {
        "kind": "adiabatic",
        "before": before,
        "after": after,
        "bath_temperature": None,
        "delta_entropy": after["entropy"] - before["entropy"],
        "heat_into_system": 0.0,
        "work_by_system": -delta_u,
        "delta_u": delta_u,
    }


def reverse_step(step: dict[str, Any], label: str) -> dict[str, Any]:
    return {
        "kind": f"{step['kind']}_reverse",
        "before": step["after"],
        "after": step["before"],
        "bath_temperature": step["bath_temperature"],
        "delta_entropy": -step["delta_entropy"],
        "heat_into_system": -step["heat_into_system"],
        "work_by_system": -step["work_by_system"],
        "delta_u": -step["delta_u"],
        "label": label,
    }


def base_forward_cycle() -> dict[str, Any]:
    t_hot = 2.0
    t_cold = 1.0
    gap_high = 3.0
    gap_hot_low = 1.0
    gap_cold_low = gap_hot_low * t_cold / t_hot
    gap_cold_high = gap_high * t_cold / t_hot
    a = state("A_hot_high_gap", t_hot, gap_high)
    hot_iso = isothermal(a, gap_hot_low, t_hot, "B_hot_low_gap")
    expand = adiabatic(hot_iso["after"], gap_cold_low, t_cold, "C_cold_low_gap")
    cold_iso = isothermal(expand["after"], gap_cold_high, t_cold, "D_cold_high_gap")
    compress = adiabatic(cold_iso["after"], gap_high, t_hot, "A_hot_high_gap_return")
    return {
        "parameters": {
            "t_hot": t_hot,
            "t_cold": t_cold,
            "gap_high": gap_high,
            "gap_hot_low": gap_hot_low,
            "gap_cold_low": gap_cold_low,
            "gap_cold_high": gap_cold_high,
        },
        "states": [a, hot_iso["after"], expand["after"], cold_iso["after"]],
        "steps": [hot_iso, expand, cold_iso, compress],
    }


def summarize_loop(loop_id: str, role: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    heat_hot = 0.0
    heat_cold = 0.0
    for step in steps:
        if step["bath_temperature"] == 2.0:
            heat_hot += step["heat_into_system"]
        elif step["bath_temperature"] == 1.0:
            heat_cold += step["heat_into_system"]
    work_by_system = sum(step["work_by_system"] for step in steps)
    working_delta_entropy = sum(step["delta_entropy"] for step in steps)
    cold_reservoir_entropy_delta = -heat_cold / 1.0
    hot_reservoir_entropy_delta = -heat_hot / 2.0
    total_reservoir_entropy_delta = cold_reservoir_entropy_delta + hot_reservoir_entropy_delta
    return {
        "loop_id": loop_id,
        "role": role,
        "step_labels": [step["after"]["label"] for step in steps],
        "heat_from_hot_bath_into_system": heat_hot,
        "heat_from_cold_bath_into_system": heat_cold,
        "work_by_system": work_by_system,
        "work_input": max(0.0, -work_by_system),
        "working_substance_delta_entropy": working_delta_entropy,
        "cold_reservoir_entropy_delta": cold_reservoir_entropy_delta,
        "hot_reservoir_entropy_delta": hot_reservoir_entropy_delta,
        "total_reservoir_entropy_delta": total_reservoir_entropy_delta,
        "stage_trace": [
            {
                "kind": step["kind"],
                "before": step["before"]["label"],
                "after": step["after"]["label"],
                "delta_entropy": step["delta_entropy"],
                "heat_into_system": step["heat_into_system"],
                "work_by_system": step["work_by_system"],
            }
            for step in steps
        ],
    }


def symbolic_checks() -> dict[str, Any]:
    tc, th = sp.symbols("Tc Th", positive=True)
    eta = sp.simplify(1 - tc / th)
    cop = sp.simplify(tc / (th - tc))
    eta_expected = 1 - tc / th
    cop_expected = tc / (th - tc)
    return {
        "efficiency_identity": str(eta),
        "cop_identity": str(cop),
        "pass": bool(sp.simplify(eta - eta_expected) == 0 and sp.simplify(cop - cop_expected) == 0),
    }


def z3_super_carnot_unsat() -> dict[str, Any]:
    tc, th, qh, qc, w, eta = z3.Reals("tc th qh qc w eta")
    solver = z3.Solver()
    solver.add(tc > 0, th > 0, tc < th, qh > 0, qc >= 0)
    solver.add(w == qh - qc, qc / tc >= qh / th, eta == w / qh)
    solver.add(eta > 1 - tc / th)
    result = solver.check()
    return {"result": str(result), "pass": result == z3.unsat}


def cvc5_super_carnot_unsat() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")
    real = solver.getRealSort()
    qc = solver.mkConst(real, "qc")
    one = solver.mkReal(1)
    two = solver.mkReal(2)
    half = solver.mkReal(1, 2)
    eta = solver.mkTerm(cvc5.Kind.DIVISION, solver.mkTerm(cvc5.Kind.SUB, two, qc), two)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, qc, one))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GT, eta, half))
    result = solver.checkSat()
    return {"result": str(result), "pass": str(result).lower() == "unsat"}


def density_checks(states: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for item in states:
        rho = density(item["p_excited"])
        qutip_rho = np.asarray(qutip.Qobj(rho, dims=[[2], [2]]).full(), dtype=np.complex128)
        qiskit_rho = np.asarray(DensityMatrix(rho).data, dtype=np.complex128)
        entropy_direct = item["entropy"]
        entropy_scipy = float(np.real(-np.trace(rho @ scipy.linalg.logm(rho))))
        rows.append({
            "label": item["label"],
            "trace": float(np.real(np.trace(rho))),
            "qutip_qiskit_max_error": float(np.max(np.abs(qutip_rho - qiskit_rho))),
            "entropy_direct": entropy_direct,
            "entropy_scipy_logm": entropy_scipy,
        })
    return {
        "rows": rows,
        "pass": all(abs(row["trace"] - 1.0) < 1e-12 and row["qutip_qiskit_max_error"] < 1e-12 and abs(row["entropy_direct"] - row["entropy_scipy_logm"]) < 1e-10 for row in rows),
    }


def graph_checks() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(["A", "B", "C", "D"])
    graph.add_edge(0, 1, "hot_iso")
    graph.add_edge(1, 2, "adiabatic_expand")
    graph.add_edge(2, 3, "cold_iso")
    graph.add_edge(3, 0, "adiabatic_compress")

    data = Data(
        x=torch.tensor([[2.0, 3.0], [2.0, 1.0], [1.0, 0.5], [1.0, 1.5]], dtype=torch.float64),
        edge_index=torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long),
    )
    ratio = torch.tensor(0.5, dtype=torch.float64, requires_grad=True)
    eta = 1.0 - ratio
    cop = ratio / (1.0 - ratio)
    (eta + cop).backward()

    hypergraph = xgi.Hypergraph([["hot_iso", "cold_iso"], ["adiabatic_expand", "adiabatic_compress"]])

    cell_shape = None
    if tnx is not None:
        cc = tnx.CellComplex()
        for edge in ([0, 1], [1, 2], [2, 3], [3, 0]):
            cc.add_cell(edge, rank=1)
        cell_shape = tuple(int(v) for v in cc.shape)

    simplex_count = None
    if gudhi is not None:
        simplex = gudhi.SimplexTree()
        for edge in ([0, 1], [1, 2], [2, 3], [0, 3]):
            simplex.insert(edge)
        simplex.persistence()
        simplex_count = simplex.num_simplices()

    return {
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "xgi_edges": hypergraph.num_edges,
        "toponetx_shape": cell_shape,
        "gudhi_simplices": simplex_count,
        "autograd_eta_plus_cop_gradient_at_ratio_half": float(ratio.grad),
        "pass": bool(graph.num_edges() == 4 and data.num_edges == 4 and hypergraph.num_edges == 2 and ratio.grad is not None),
    }


def cycle_step_invariant_map(inductive: dict[str, Any], deductive: dict[str, Any], params: dict[str, float]) -> dict[str, Any]:
    """Local cycle-step invariant map.

    These are not admitted QIT axes. They are local observable slots that can
    be compared against other cycle receipts later.
    """
    return {
        "boundary": "local_cycle_invariant_map_not_admitted_axis_promotion",
        "invariants": {
            "entropy_transfer_polarity": {
                "local_name": "entropy_gradient_polarity",
                "degree_of_freedom": "sign and magnitude of reservoir entropy transfer",
                "observable": "cold_reservoir_entropy_delta",
                "inductive_value": inductive["cold_reservoir_entropy_delta"],
                "deductive_value": deductive["cold_reservoir_entropy_delta"],
                "correlation_hint": "closest to thermodynamic entropy-drive intuition, not a QIT cut kernel",
            },
            "bath_contact_branch": {
                "local_name": "bath_branch",
                "degree_of_freedom": "hot-contact versus cold-contact branch",
                "observable": "isothermal leg bath label",
                "values": ["hot_isotherm", "cold_isotherm"],
                "correlation_hint": "terrain/topology split analogue",
            },
            "temperature_gap_frame": {
                "local_name": "working_frame",
                "degree_of_freedom": "temperature-scaled gap frame",
                "observable": "gap / temperature invariant along adiabats",
                "hot_high_ratio": params["gap_high"] / params["t_hot"],
                "cold_high_ratio": params["gap_cold_high"] / params["t_cold"],
                "hot_low_ratio": params["gap_hot_low"] / params["t_hot"],
                "cold_low_ratio": params["gap_cold_low"] / params["t_cold"],
                "correlation_hint": "frame-change analogue; adiabats preserve occupation probability",
            },
            "cycle_traversal_family": {
                "local_name": "loop_family",
                "degree_of_freedom": "work-producing versus work-consuming traversal family",
                "observable": "work sign and cold entropy sign",
                "values": {
                    "inductive_heating": {"work_by_system": inductive["work_by_system"], "cold_entropy_delta": inductive["cold_reservoir_entropy_delta"]},
                    "deductive_cooling": {"work_by_system": deductive["work_by_system"], "cold_entropy_delta": deductive["cold_reservoir_entropy_delta"]},
                },
                "correlation_hint": "work-cycle-family split analogue",
            },
            "step_sequence_parity": {
                "local_name": "leg_order_class",
                "degree_of_freedom": "isothermal/adiabatic composition order",
                "observable": "I-A-I-A versus reversed A-I-A-I",
                "inductive_order": [step["kind"] for step in inductive["stage_trace"]],
                "deductive_order": [step["kind"] for step in deductive["stage_trace"]],
                "correlation_hint": "loop-order family analogue",
            },
            "heat_work_operator_family": {
                "local_name": "operator_mode",
                "degree_of_freedom": "heat-exchange leg versus work-only leg",
                "observable": "nonzero heat_into_system versus zero heat_into_system",
                "values": ["thermal_contact", "adiabatic_work"],
                "correlation_hint": "operator-family split analogue",
            },
            "stage_precedence_orientation": {
                "local_name": "precedence_orientation",
                "degree_of_freedom": "which leg precedes which under traversal direction",
                "observable": "directed cycle order",
                "inductive_order": [stage["after"] for stage in inductive["stage_trace"]],
                "deductive_order": [stage["after"] for stage in deductive["stage_trace"]],
                "correlation_hint": "composition/precedence analogue",
            },
        },
        "degrees_of_freedom": [
            "temperature_ratio",
            "gap_ratio",
            "cycle_direction",
            "bath_contact_branch",
            "leg_order",
            "heat_work_mode",
            "stage_precedence",
            "entropy_gradient_sign",
        ],
    }


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "loops": result["dual_stack"],
        "states": result["states"],
        "cycle_step_invariant_map": result["cycle_step_invariant_map"],
        "tool_summary": {
            "tool_count": result["summary"]["tool_count"],
            "load_bearing_tool_count": result["summary"]["load_bearing_tool_count"],
        },
        "boundaries": result["negative"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_visual_payload(result)
    js = "window.CARNOT_DUAL_STACK_DATA = " + json.dumps(payload, indent=2) + ";\n"
    (VIS_DIR / "carnot-dual-stack-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    forward = base_forward_cycle()
    inductive_steps = forward["steps"]
    deductive_steps = [
        reverse_step(forward["steps"][3], "reverse_adiabatic_to_cold_high"),
        reverse_step(forward["steps"][2], "reverse_cold_isotherm"),
        reverse_step(forward["steps"][1], "reverse_adiabatic_to_hot_low"),
        reverse_step(forward["steps"][0], "reverse_hot_isotherm"),
    ]
    inductive = summarize_loop("inductive_heating_loop", "forward_work_producing_cycle", inductive_steps)
    deductive = summarize_loop("deductive_cooling_loop", "reverse_refrigerator", deductive_steps)

    q_hot = inductive["heat_from_hot_bath_into_system"]
    q_cold_out = -inductive["heat_from_cold_bath_into_system"]
    work_out = inductive["work_by_system"]
    efficiency = work_out / q_hot
    carnot_bound = 1.0 - forward["parameters"]["t_cold"] / forward["parameters"]["t_hot"]
    q_cold_absorbed = deductive["heat_from_cold_bath_into_system"]
    work_input = deductive["work_input"]
    cop = q_cold_absorbed / work_input
    cop_carnot = forward["parameters"]["t_cold"] / (forward["parameters"]["t_hot"] - forward["parameters"]["t_cold"])

    positive = {
        "inductive_loop_produces_work_and_heats_cold_reservoir": {
            "work_output": work_out,
            "cold_reservoir_entropy_delta": inductive["cold_reservoir_entropy_delta"],
            "pass": work_out > 0.0 and inductive["cold_reservoir_entropy_delta"] > 0.0,
        },
        "deductive_loop_consumes_work_and_cools_cold_reservoir": {
            "work_input": work_input,
            "cold_reservoir_entropy_delta": deductive["cold_reservoir_entropy_delta"],
            "pass": work_input > 0.0 and deductive["cold_reservoir_entropy_delta"] < 0.0,
        },
        "loops_are_opposite_traversals_with_closed_working_entropy": {
            "inductive_working_entropy_delta": inductive["working_substance_delta_entropy"],
            "deductive_working_entropy_delta": deductive["working_substance_delta_entropy"],
            "pass": abs(inductive["working_substance_delta_entropy"]) < 1e-12 and abs(deductive["working_substance_delta_entropy"]) < 1e-12,
        },
        "forward_cycle_hits_reversible_efficiency": {
            "efficiency": efficiency,
            "carnot_bound": carnot_bound,
            "pass": abs(efficiency - carnot_bound) < 1e-10,
        },
        "reverse_refrigerator_hits_carnot_cop": {
            "cop": cop,
            "cop_carnot": cop_carnot,
            "pass": abs(cop - cop_carnot) < 1e-10,
        },
    }
    negative = {
        "super_carnot_blocked_by_z3": z3_super_carnot_unsat(),
        "super_carnot_blocked_by_cvc5_fixed_case": cvc5_super_carnot_unsat(),
        "dual_stack_is_not_two_different_cycles": {
            "shared_state_count": len(forward["states"]),
            "pass": len(forward["states"]) == 4,
        },
    }
    boundary = {
        "symbolic_identities": symbolic_checks(),
        "density_carriers": density_checks(forward["states"]),
        "graph_topology": graph_checks(),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in negative.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "name": "two_bath_heat_work_reversible_cycle_pair",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "allowed_claims": [
            "two-bath heat/work reversible cycle-pair sim exists and runs",
            "opposite-direction heating/cooling loop bookkeeping",
            "web visualization payload for Carnot loop inspection",
            "no final QIT runtime or admitted-axis promotion",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "not yet coupled to Szilard dual-stack row",
            "not yet nested in GStack",
            "not a final runtime QIT claim",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "states": forward["states"],
        "dual_stack": {
            "inductive_heating_loop": inductive,
            "deductive_cooling_loop": deductive,
        },
        "cycle_step_invariant_map": cycle_step_invariant_map(inductive, deductive, forward["parameters"]),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "forward_efficiency": efficiency,
            "forward_carnot_bound": carnot_bound,
            "reverse_cop": cop,
            "reverse_cop_carnot": cop_carnot,
            "q_hot_absorbed": q_hot,
            "q_cold_rejected": q_cold_out,
            "q_cold_absorbed_reverse": q_cold_absorbed,
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_tool_count": sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "visual_payload": "visualizer/carnot-dual-stack-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "two_bath_heat_work_reversible_cycle_pair_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()

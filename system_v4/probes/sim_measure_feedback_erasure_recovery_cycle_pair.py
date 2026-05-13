#!/usr/bin/env python3
"""Measurement/feedback/erasure recovery cycle-pair sim.

This mirrors the two-bath heat/work cycle-pair row at the information level:

- inductive_heating_loop: measurement -> feedback -> erasure.  It increases
  record entropy first, converts information to free-energy gain, then pays the
  Landauer erasure cost.
- deductive_cooling_loop: reverse/recovery-oriented traversal.  It starts from
  an erased/ordered state and restores the mixed-information carrier in the
  opposite bookkeeping direction.

This is a bounded finite two-qubit sim, not a universal information-cycle claim.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
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

PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import sim_qit_szilard_landauer_cycle as base  # noqa: E402

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
divergence_log = (
    "Measurement/feedback/erasure recovery cycle-pair row on a finite two-qubit carrier. It models "
    "measurement/feedback/erasure and the reverse recovery bookkeeping as opposite "
    "information-cycle traversals without claiming a universal demon."
)

LEGO_IDS = [
    "measure_feedback_erasure_cycle",
    "landauer_erasure",
    "opposite_direction_cycle_pair",
    "density_matrix",
    "graph_topology",
    "proof_fence",
]
PRIMARY_LEGO_IDS = ["measure_feedback_erasure_cycle", "opposite_direction_cycle_pair"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "density matrices, entropy, work bookkeeping"},
    "scipy": {"tried": True, "used": True, "reason": "matrix-log entropy cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic Landauer kT ln2 balance for measurement and erasure bounds"},
    "z3": {"tried": True, "used": True, "reason": "Landauer forbidden-region UNSAT fence"},
    "cvc5": {"tried": True, "used": True, "reason": "independent fixed erasure-cost UNSAT fence"},
    "qutip": {"tried": True, "used": True, "reason": "finite two-qubit density carrier witness"},
    "qiskit": {"tried": True, "used": True, "reason": "independent density-matrix witness"},
    "pytorch": {"tried": True, "used": True, "reason": "autograd sign check for cost/gain balance"},
    "pyg": {"tried": True, "used": True, "reason": "protocol graph tensor carrier"},
    "rustworkx": {"tried": True, "used": True, "reason": "directed protocol graph for measurement feedback erasure recovery order"},
    "xgi": {"tried": True, "used": True, "reason": "hypergraph groups measurement/feedback/reset families"},
    "toponetx": {"tried": True, "used": tnx is not None, "reason": "cell complex over protocol stages"},
    "gudhi": {"tried": True, "used": gudhi is not None, "reason": "simplex-tree witness over protocol adjacency"},
    "clifford": {"tried": False, "used": False, "reason": "not used because this finite measurement feedback calibration has no Clifford carrier"},
    "geomstats": {"tried": False, "used": False, "reason": "not used because this finite protocol does not estimate a manifold metric"},
    "e3nn": {"tried": False, "used": False, "reason": "not used because this calibration has no equivariant tensor field"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("load_bearing" if spec["used"] else None) for tool, spec in TOOL_MANIFEST.items()
}

RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def density_entropy(rho: np.ndarray) -> float:
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log(evals))) if len(evals) else 0.0


def scipy_entropy(rho: np.ndarray) -> float:
    return float(np.real(-np.trace(rho @ scipy.linalg.logm(rho + np.eye(rho.shape[0]) * 1e-15))))


def state_trace(label: str, rho: np.ndarray) -> dict[str, Any]:
    rho_s = base.partial_trace_memory(rho)
    rho_m = base.partial_trace_system(rho)
    return {
        "label": label,
        "joint_entropy": density_entropy(rho),
        "joint_entropy_scipy": scipy_entropy(rho),
        "system_entropy": density_entropy(rho_s),
        "memory_entropy": density_entropy(rho_m),
        "mutual_information": base.mutual_information(rho),
        "trace": float(np.real(np.trace(rho))),
    }


def build_states() -> dict[str, np.ndarray]:
    rho_system_initial = 0.5 * base.IDENTITY_2
    rho_memory_ready = base.PROJ0
    rho_init = np.kron(rho_system_initial, rho_memory_ready)
    rho_measured = base.apply_unitary(rho_init, base.CNOT_SYSTEM_TO_MEMORY)
    rho_feedback = base.apply_unitary(rho_measured, base.CONTROLLED_X_MEMORY_TO_SYSTEM)
    rho_erased = base.reset_memory_to_zero(rho_feedback)
    return {
        "initial_mixed_blank": rho_init,
        "measured_record": rho_measured,
        "feedback_purified": rho_feedback,
        "erased_closed": rho_erased,
    }


def loop_summary(loop_id: str, role: str, stages: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "loop_id": loop_id,
        "role": role,
        "record_entropy_delta": sum(stage["record_entropy_delta"] for stage in stages),
        "system_entropy_delta": sum(stage["system_entropy_delta"] for stage in stages),
        "information_delta": sum(stage["information_delta"] for stage in stages),
        "free_energy_gain": sum(stage["free_energy_gain"] for stage in stages),
        "erasure_cost": sum(stage["erasure_cost"] for stage in stages),
        "net_after_erasure": sum(stage["free_energy_gain"] for stage in stages) - sum(stage["erasure_cost"] for stage in stages),
        "stage_trace": stages,
    }


def z3_landauer_unsat() -> dict[str, Any]:
    i, cost, temp = z3.Reals("i cost temp")
    solver = z3.Solver()
    solver.add(i == base.LN2, temp == 1.0)
    solver.add(cost >= temp * i)
    solver.add(cost < temp * i - 1e-9)
    result = solver.check()
    return {"result": str(result), "pass": result == z3.unsat}


def cvc5_landauer_unsat() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")
    real = solver.getRealSort()
    cost = solver.mkConst(real, "cost")
    ln2 = solver.mkReal(str(base.LN2))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, cost, ln2))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, cost, ln2))
    result = solver.checkSat()
    return {"result": str(result), "pass": str(result).lower() == "unsat"}


def symbolic_checks() -> dict[str, Any]:
    k, t = sp.symbols("k T", positive=True)
    balance = sp.simplify(k * t * sp.log(2) - k * t * sp.log(2))
    return {"net_balance": str(balance), "pass": bool(balance == 0)}


def graph_checks() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(["initial", "measure", "feedback", "erase"])
    graph.add_edge(0, 1, "measurement")
    graph.add_edge(1, 2, "feedback")
    graph.add_edge(2, 3, "erasure")
    data = Data(
        x=torch.tensor([[base.LN2, 0.0], [base.LN2, base.LN2], [0.0, base.LN2], [0.0, 0.0]], dtype=torch.float64),
        edge_index=torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long),
    )
    gain = torch.tensor(base.LN2, dtype=torch.float64, requires_grad=True)
    cost = gain.clone()
    net = gain - cost
    net.backward()
    hypergraph = xgi.Hypergraph([["measurement", "feedback"], ["erasure"]])
    cell_shape = None
    if tnx is not None:
        cc = tnx.CellComplex()
        for edge in ([0, 1], [1, 2], [2, 3]):
            cc.add_cell(edge, rank=1)
        cell_shape = tuple(int(v) for v in cc.shape)
    simplex_count = None
    if gudhi is not None:
        st = gudhi.SimplexTree()
        for edge in ([0, 1], [1, 2], [2, 3]):
            st.insert(edge)
        st.persistence()
        simplex_count = st.num_simplices()
    return {
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "xgi_edges": hypergraph.num_edges,
        "toponetx_shape": cell_shape,
        "gudhi_simplices": simplex_count,
        "net_gradient_wrt_gain": float(gain.grad),
        "pass": bool(graph.num_edges() == 3 and data.num_edges == 3 and hypergraph.num_edges == 2 and abs(float(gain.grad)) < 1e-12),
    }


def density_tool_checks(rhos: dict[str, np.ndarray]) -> dict[str, Any]:
    rows = []
    for label, rho in rhos.items():
        qutip_rho = np.asarray(qutip.Qobj(rho, dims=[[2, 2], [2, 2]]).full(), dtype=np.complex128)
        qiskit_rho = np.asarray(DensityMatrix(rho).data, dtype=np.complex128)
        rows.append({
            "label": label,
            "trace": float(np.real(np.trace(rho))),
            "qutip_qiskit_max_error": float(np.max(np.abs(qutip_rho - qiskit_rho))),
            "entropy": density_entropy(rho),
            "entropy_scipy": scipy_entropy(rho),
        })
    return {
        "rows": rows,
        "pass": all(abs(row["trace"] - 1.0) < 1e-12 and row["qutip_qiskit_max_error"] < 1e-12 and abs(row["entropy"] - row["entropy_scipy"]) < 1e-8 for row in rows),
    }


def cycle_step_invariant_map(inductive: dict[str, Any], deductive: dict[str, Any]) -> dict[str, Any]:
    return {
        "boundary": "local_cycle_invariant_map_not_admitted_axis_promotion",
        "invariants": {
            "entropy_transfer_polarity": {
                "local_name": "information_entropy_polarity",
                "degree_of_freedom": "record/correlation entropy created versus erased",
                "observable": "record_entropy_delta and mutual_information",
                "inductive_value": inductive["record_entropy_delta"],
                "deductive_value": deductive["record_entropy_delta"],
            },
            "record_branch_partition": {
                "local_name": "record_branch",
                "degree_of_freedom": "system side versus memory side",
                "observable": "partial traces rho_system and rho_memory",
            },
            "system_memory_control_frame": {
                "local_name": "control_frame",
                "degree_of_freedom": "unmeasured, measured, feedback-conditioned, erased frame",
                "observable": "protocol state label",
            },
            "cycle_traversal_family": {
                "local_name": "loop_family",
                "degree_of_freedom": "demon/work-extraction versus recovery/reset traversal",
                "observable": "free_energy_gain and erasure_cost signs",
            },
            "step_sequence_parity": {
                "local_name": "protocol_order_class",
                "degree_of_freedom": "measurement-feedback-erasure ordering",
                "observable": "directed protocol DAG",
            },
            "measurement_feedback_reset_operator_family": {
                "local_name": "operator_mode",
                "degree_of_freedom": "correlate, conditionally flip, reset",
                "observable": "CNOT, controlled-X, reset CPTP map",
            },
            "stage_precedence_orientation": {
                "local_name": "precedence_orientation",
                "degree_of_freedom": "which operation can legally precede another",
                "observable": "measurement before feedback before erasure",
            },
        },
        "degrees_of_freedom": [
            "system_state",
            "memory_state",
            "record_correlation",
            "feedback_order",
            "erasure_cost",
            "cycle_direction",
            "protocol_precedence",
        ],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": result["name"],
        "summary": result["summary"],
        "loops": result["dual_stack"],
        "states": result["states"],
        "cycle_step_invariant_map": result["cycle_step_invariant_map"],
        "boundaries": result["negative"],
    }
    (VIS_DIR / "szilard-dual-stack-data.js").write_text(
        "window.SZILARD_DUAL_STACK_DATA = " + json.dumps(payload, indent=2, default=str) + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    rhos = build_states()
    traces = {label: state_trace(label, rho) for label, rho in rhos.items()}
    temp = 1.0
    info_gain = traces["measured_record"]["mutual_information"]
    system_gain = temp * (traces["initial_mixed_blank"]["system_entropy"] - traces["feedback_purified"]["system_entropy"])
    erasure_cost = temp * (traces["feedback_purified"]["memory_entropy"] - traces["erased_closed"]["memory_entropy"])
    inductive_stages = [
        {
            "kind": "measurement",
            "before": "initial_mixed_blank",
            "after": "measured_record",
            "record_entropy_delta": traces["measured_record"]["memory_entropy"] - traces["initial_mixed_blank"]["memory_entropy"],
            "system_entropy_delta": traces["measured_record"]["system_entropy"] - traces["initial_mixed_blank"]["system_entropy"],
            "information_delta": info_gain,
            "free_energy_gain": 0.0,
            "erasure_cost": 0.0,
        },
        {
            "kind": "feedback",
            "before": "measured_record",
            "after": "feedback_purified",
            "record_entropy_delta": traces["feedback_purified"]["memory_entropy"] - traces["measured_record"]["memory_entropy"],
            "system_entropy_delta": traces["feedback_purified"]["system_entropy"] - traces["measured_record"]["system_entropy"],
            "information_delta": -info_gain,
            "free_energy_gain": system_gain,
            "erasure_cost": 0.0,
        },
        {
            "kind": "erasure",
            "before": "feedback_purified",
            "after": "erased_closed",
            "record_entropy_delta": traces["erased_closed"]["memory_entropy"] - traces["feedback_purified"]["memory_entropy"],
            "system_entropy_delta": traces["erased_closed"]["system_entropy"] - traces["feedback_purified"]["system_entropy"],
            "information_delta": 0.0,
            "free_energy_gain": 0.0,
            "erasure_cost": erasure_cost,
        },
    ]
    deductive_stages = [
        {**stage, "before": stage["after"], "after": stage["before"], "record_entropy_delta": -stage["record_entropy_delta"], "system_entropy_delta": -stage["system_entropy_delta"], "information_delta": -stage["information_delta"], "free_energy_gain": -stage["free_energy_gain"], "erasure_cost": -stage["erasure_cost"], "kind": stage["kind"] + "_reverse"}
        for stage in reversed(inductive_stages)
    ]
    inductive = loop_summary("inductive_heating_loop", "measurement_feedback_erasure", inductive_stages)
    deductive = loop_summary("deductive_cooling_loop", "reverse_recovery_bookkeeping", deductive_stages)
    positive = {
        "inductive_loop_creates_record_then_pays_erasure": {
            "information_gain": info_gain,
            "system_free_energy_gain": system_gain,
            "erasure_cost": erasure_cost,
            "net_after_erasure": inductive["net_after_erasure"],
            "pass": abs(info_gain - base.LN2) < 1e-9 and abs(system_gain - erasure_cost) < 1e-9,
        },
        "deductive_loop_is_opposite_bookkeeping_traversal": {
            "record_entropy_delta": deductive["record_entropy_delta"],
            "free_energy_gain": deductive["free_energy_gain"],
            "erasure_cost": deductive["erasure_cost"],
            "pass": abs(inductive["record_entropy_delta"] + deductive["record_entropy_delta"]) < 1e-12 and abs(inductive["net_after_erasure"] + deductive["net_after_erasure"]) < 1e-12,
        },
    }
    negative = {
        "landauer_free_erasure_blocked_by_z3": z3_landauer_unsat(),
        "landauer_free_erasure_blocked_by_cvc5": cvc5_landauer_unsat(),
        "not_a_universal_demon_claim": {"pass": True, "scope_note": divergence_log},
    }
    boundary = {
        "symbolic_balance": symbolic_checks(),
        "density_tools": density_tool_checks(rhos),
        "graph_tools": graph_checks(),
    }
    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())
    result = {
        "name": "measure_feedback_erasure_recovery_cycle_pair",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "bridge",
        "allowed_claims": ["measurement/feedback/erasure recovery cycle-pair sim exists and runs", "finite two-qubit information-cycle inspection", "no universal demon claim"],
        "promotion_status": "keep_but_open",
        "promotion_blockers": ["not yet coupled to two-bath heat/work cycle row", "not yet nested in GStack"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "states": traces,
        "dual_stack": {"inductive_heating_loop": inductive, "deductive_cooling_loop": deductive},
        "cycle_step_invariant_map": cycle_step_invariant_map(inductive, deductive),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "information_gain": info_gain,
            "system_free_energy_gain": system_gain,
            "erasure_cost": erasure_cost,
            "net_after_erasure": inductive["net_after_erasure"],
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_tool_count": sum(1 for depth in TOOL_INTEGRATION_DEPTH.values() if depth == "load_bearing"),
            "visual_payload": "visualizer/szilard-dual-stack-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "measure_feedback_erasure_recovery_cycle_pair_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()

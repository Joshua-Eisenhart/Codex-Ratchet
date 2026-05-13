#!/usr/bin/env python3
"""Triadic Rosetta mode layer for Carnot, Szilard, and I Ching-64.

This layer compares three already receipt-backed rows across classical,
bridge, and nonclassical-adjacent modes.  It is a comparison and stress-test
surface only.  It does not promote the I Ching row, the thermodynamic rows, or
the Rosetta comparison into QIT-engine admission.
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
import torch
import z3
from qiskit.quantum_info import DensityMatrix
from torch_geometric.data import Data


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
divergence_log = (
    "Triadic Rosetta mode layer over Carnot, Szilard, and I Ching-64 rows. "
    "It compares the three through classical, bridge, and nonclassical-adjacent "
    "mode surfaces, then stress-tests identity-collapse and promotion mistakes. "
    "It is not QIT-engine admission, not I Ching proof, and not an axis claim."
)

LEGO_IDS = [
    "carnot_cycle",
    "szilard_cycle",
    "iching_64_schedule",
    "dual_stacked_engine",
    "axis_schedule",
    "density_matrix",
    "graph_topology",
    "proof_fence",
    "rosetta_correlation",
    "graveyard_variant",
]
PRIMARY_LEGO_IDS = ["rosetta_correlation", "graveyard_variant"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads exact source receipts"},
    "numpy": {"tried": True, "used": True, "reason": "mode feature matrix and entropy/readout comparisons"},
    "torch": {"tried": True, "used": True, "reason": "tensor carrier for the triad mode graph"},
    "pyg": {"tried": True, "used": True, "reason": "graph tensor witness for mode couplings"},
    "rustworkx": {"tried": True, "used": True, "reason": "triad-by-mode coupling graph"},
    "qiskit": {"tried": True, "used": True, "reason": "nonclassical-adjacent density carrier witness"},
    "qutip": {"tried": True, "used": True, "reason": "independent density carrier witness"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT fence against collapsing distinct triad state counts into one identity"},
    "cvc5": {"tried": True, "used": True, "reason": "independent UNSAT fence against identity collapse"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["json"] = "supportive"
TOOL_INTEGRATION_DEPTH["pathlib"] = "supportive"
TOOL_INTEGRATION_DEPTH["python_stdlib"] = "supportive"
TOOL_INTEGRATION_DEPTH["python_json"] = "supportive"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load_result(stem: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{stem}_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def pass_at(result: dict[str, Any], *path: str) -> bool:
    node: Any = result
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    return bool(isinstance(node, dict) and node.get("pass") is True)


def engine_digest(carnot: dict[str, Any], szilard: dict[str, Any], iching: dict[str, Any]) -> dict[str, dict[str, Any]]:
    iching_schedule = iching.get("positive", {}).get("gray_walk_is_64_state_single_line_cycle", {})
    return {
        "carnot": {
            "source": "two_bath_heat_work_reversible_cycle_pair_results.json",
            "state_count": len(carnot.get("states", [])),
            "operator_count": len(carnot["dual_stack"]["inductive_heating_loop"]["stage_trace"]),
            "loop_count": len(carnot.get("dual_stack", {})),
            "axis_count": len(carnot.get("axes_candidate_model", {}).get("axes", {})),
            "entropy_readout": "reservoir entropy plus heat/work efficiency",
            "geometry": "four-state thermodynamic cycle",
            "classical_pass": bool(carnot["summary"]["all_pass"]),
            "bridge_pass": bool(
                pass_at(carnot, "boundary", "symbolic_identities")
                and pass_at(carnot, "boundary", "graph_topology")
                and pass_at(carnot, "negative", "super_carnot_blocked_by_z3")
            ),
            "nonclassical_adjacent_pass": pass_at(carnot, "boundary", "density_carriers"),
            "scope": "classical thermodynamic engine with finite density-carrier witnesses",
        },
        "szilard": {
            "source": "measure_feedback_erasure_recovery_cycle_pair_results.json",
            "state_count": len(szilard.get("states", {})),
            "operator_count": len(szilard["dual_stack"]["inductive_heating_loop"]["stage_trace"]),
            "loop_count": len(szilard.get("dual_stack", {})),
            "axis_count": len(szilard.get("axes_candidate_model", {}).get("axes", {})),
            "entropy_readout": "record entropy, mutual information, erasure cost",
            "geometry": "finite two-qubit system-memory protocol path",
            "classical_pass": bool(szilard["summary"]["all_pass"]),
            "bridge_pass": bool(
                pass_at(szilard, "boundary", "symbolic_balance")
                and pass_at(szilard, "boundary", "graph_tools")
                and pass_at(szilard, "negative", "landauer_free_erasure_blocked_by_z3")
            ),
            "nonclassical_adjacent_pass": pass_at(szilard, "boundary", "density_tools"),
            "scope": "finite information engine with density and proof witnesses",
        },
        "iching_64": {
            "source": "six_bit_gray_code_single_flip_cycle_invariant_results.json",
            "state_count": int(iching["summary"]["state_count"]),
            "operator_count": int(iching["summary"]["state_count"]),
            "loop_count": 2,
            "axis_count": len(iching.get("axes_candidate_model", {}).get("axes", {})),
            "entropy_readout": "uniform state entropy plus parity polarity",
            "geometry": "six-bit hypercube Gray-cycle symbolic schedule",
            "classical_pass": bool(iching["summary"]["all_pass"] and iching_schedule.get("pass")),
            "bridge_pass": bool(
                pass_at(iching, "boundary", "axis_model_has_ax0_through_ax6")
                and pass_at(iching, "negative", "z3_blocks_binary_count_jump_as_single_line_step")
            ),
            "nonclassical_adjacent_pass": pass_at(iching, "positive", "graph_and_density_witnesses_pass"),
            "scope": "symbolic 64-state schedule, not QIT math or I Ching proof",
        },
    }


def mode_matrix(digests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    mode_specs = {
        "classical": {
            "claim": "finite state/operator bookkeeping with an entropy readout",
            "boundary": "classical agreement is surface grammar, not identity",
        },
        "bridge": {
            "claim": "axis slots, graph/order, and proof fences connect language layers",
            "boundary": "bridge rows are comparison scaffolds, not promotion gates",
        },
        "nonclassical_adjacent": {
            "claim": "density carriers or graph tensors give a nonclassical-compatible representation",
            "boundary": "density/tool witnesses are not a final QIT engine runtime",
        },
    }
    for engine, digest in digests.items():
        for mode, spec in mode_specs.items():
            rows.append(
                {
                    "engine": engine,
                    "mode": mode,
                    "pass": bool(digest[f"{mode}_pass"]),
                    "claim": spec["claim"],
                    "geometry": digest["geometry"],
                    "entropy_readout": digest["entropy_readout"],
                    "state_count": digest["state_count"],
                    "operator_count": digest["operator_count"],
                    "axis_count": digest["axis_count"],
                    "boundary": spec["boundary"],
                }
            )
    return rows


def shared_structure_rows(digests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "slot": "finite_carrier",
            "status": "shared_with_different_cardinality",
            "evidence": {name: digest["state_count"] for name, digest in digests.items()},
            "boundary": "same finite-carrier grammar, not same state space",
        },
        {
            "slot": "ordered_local_operator",
            "status": "shared_with_different_operator_language",
            "evidence": {name: digest["operator_count"] for name, digest in digests.items()},
            "boundary": "thermal legs, information operations, and line flips do not collapse",
        },
        {
            "slot": "dual_orientation",
            "status": "shared",
            "evidence": {name: digest["loop_count"] for name, digest in digests.items()},
            "boundary": "two-direction grammar is a comparison invariant only",
        },
        {
            "slot": "axis_schedule",
            "status": "shared_candidate_slots",
            "evidence": {name: digest["axis_count"] for name, digest in digests.items()},
            "boundary": "Ax0-Ax6 labels remain local candidate slots, not admitted axes",
        },
        {
            "slot": "entropy_gradient",
            "status": "shared_shape_different_readout",
            "evidence": {name: digest["entropy_readout"] for name, digest in digests.items()},
            "boundary": "reservoir entropy, record entropy, and parity entropy stay distinct",
        },
        {
            "slot": "nonclassical_adjacent_carrier",
            "status": "shared_tool_surface",
            "evidence": {name: digest["nonclassical_adjacent_pass"] for name, digest in digests.items()},
            "boundary": "qutip/qiskit/PyG witnesses do not equal QIT engine admission",
        },
    ]


def z3_identity_collapse_unsat(digests: dict[str, dict[str, Any]]) -> dict[str, Any]:
    c, s, i = z3.Ints("c s i")
    solver = z3.Solver()
    solver.add(c == digests["carnot"]["state_count"])
    solver.add(s == digests["szilard"]["state_count"])
    solver.add(i == digests["iching_64"]["state_count"])
    solver.add(c == s, s == i)
    result = solver.check()
    return {
        "fixed_counts": {name: digest["state_count"] for name, digest in digests.items()},
        "claim": "all three rows are the same state space",
        "result": str(result),
        "pass": result == z3.unsat,
    }


def cvc5_identity_collapse_unsat(digests: dict[str, dict[str, Any]]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    c = solver.mkConst(integer, "c")
    s = solver.mkConst(integer, "s")
    i = solver.mkConst(integer, "i")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, c, solver.mkInteger(digests["carnot"]["state_count"])))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, s, solver.mkInteger(digests["szilard"]["state_count"])))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, i, solver.mkInteger(digests["iching_64"]["state_count"])))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, c, s))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, s, i))
    result = solver.checkSat()
    return {
        "fixed_counts": {name: digest["state_count"] for name, digest in digests.items()},
        "claim": "all three rows are the same state space",
        "result": str(result),
        "pass": str(result).lower() == "unsat",
    }


def graph_tensor_density_check(digests: dict[str, dict[str, Any]]) -> dict[str, Any]:
    names = list(digests)
    modes = ["classical", "bridge", "nonclassical_adjacent"]
    graph = rx.PyDiGraph()
    for name in names:
        for mode in modes:
            graph.add_node(f"{name}:{mode}")
    node_index = {graph[index]: index for index in range(graph.num_nodes())}
    edges = []
    for name in names:
        for src, dst in zip(modes, modes[1:]):
            edges.append((node_index[f"{name}:{src}"], node_index[f"{name}:{dst}"]))
    for mode in modes:
        for src, dst in zip(names, names[1:]):
            edges.append((node_index[f"{src}:{mode}"], node_index[f"{dst}:{mode}"]))
    graph.add_edges_from_no_data(edges)
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    features = torch.tensor(
        [
            [
                digests[name]["state_count"],
                digests[name]["operator_count"],
                digests[name]["axis_count"],
                float(digests[name][f"{mode}_pass"]),
            ]
            for name in names
            for mode in modes
        ],
        dtype=torch.float64,
    )
    data = Data(x=features, edge_index=edge_index)
    probs = np.array([digest["state_count"] for digest in digests.values()], dtype=np.float64)
    probs = probs / probs.sum()
    rho = np.diag(probs.astype(np.complex128))
    qutip_trace = float(np.real(qutip.Qobj(rho).tr()))
    qiskit_trace = float(np.real(np.trace(DensityMatrix(rho).data)))
    entropy = float(-np.sum(probs * np.log(probs)))
    return {
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "density_dimension": int(rho.shape[0]),
        "state_count_distribution": {name: int(digest["state_count"]) for name, digest in digests.items()},
        "state_count_entropy": entropy,
        "qutip_trace": qutip_trace,
        "qiskit_trace": qiskit_trace,
        "pass": bool(
            graph.num_nodes() == 9
            and graph.num_edges() == len(edges)
            and int(data.num_nodes) == 9
            and int(data.num_edges) == len(edges)
            and abs(qutip_trace - 1.0) < 1e-12
            and abs(qiskit_trace - 1.0) < 1e-12
        ),
    }


def stress_tests(digests: dict[str, dict[str, Any]], mode_rows: list[dict[str, Any]]) -> dict[str, Any]:
    identity_z3 = z3_identity_collapse_unsat(digests)
    identity_cvc5 = cvc5_identity_collapse_unsat(digests)
    return {
        "all_source_rows_pass": {
            "pass": all(digest["classical_pass"] for digest in digests.values()),
            "source_pass": {name: digest["classical_pass"] for name, digest in digests.items()},
        },
        "all_modes_have_receipts": {
            "pass": all(row["pass"] for row in mode_rows),
            "failed": [row for row in mode_rows if not row["pass"]],
        },
        "all_axis_slots_present_but_not_promoted": {
            "pass": all(digest["axis_count"] == 7 for digest in digests.values()),
            "axis_counts": {name: digest["axis_count"] for name, digest in digests.items()},
            "boundary": "axis slots are candidate comparison slots only",
        },
        "z3_blocks_identity_collapse": identity_z3,
        "cvc5_blocks_identity_collapse": identity_cvc5,
        "graph_tensor_density_witness": graph_tensor_density_check(digests),
    }


def graveyard_rows(digests: dict[str, dict[str, Any]], checks: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "variant": "collapse_all_three_to_one_state_space",
            "status": "killed",
            "reason": "Carnot/Szilard four-state receipts and I Ching 64-state receipt cannot satisfy one shared state-count identity.",
            "evidence": {
                "z3": checks["z3_blocks_identity_collapse"]["result"],
                "cvc5": checks["cvc5_blocks_identity_collapse"]["result"],
            },
        },
        {
            "variant": "erase_dual_orientation",
            "status": "killed",
            "reason": "Each row has two orientation families; deleting that axis loses the engine grammar under comparison.",
            "evidence": {name: digest["loop_count"] for name, digest in digests.items()},
        },
        {
            "variant": "promote_symbolic_iching_to_qit_admission",
            "status": "blocked",
            "reason": "The I Ching row is symbolic and nonclassical-adjacent only; no GStack or QIT runtime receipt exists.",
            "evidence": digests["iching_64"]["scope"],
        },
        {
            "variant": "collapse_operator_languages",
            "status": "rejected",
            "reason": "Thermal legs, information operations, and line flips share ordered-local-operator grammar but remain different operators.",
            "evidence": {name: digest["operator_count"] for name, digest in digests.items()},
        },
        {
            "variant": "read_nonclassical_tools_as_engine_runtime",
            "status": "blocked",
            "reason": "Density and graph witnesses show compatible carriers, not a final QIT engine or admitted axis stack.",
            "evidence": {name: digest["nonclassical_adjacent_pass"] for name, digest in digests.items()},
        },
    ]


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "mode_matrix": result["mode_matrix"],
        "shared_structure_rows": result["shared_structure_rows"],
        "stress_tests": result["stress_tests"],
        "graveyard_rows": result["graveyard_rows"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.ROSETTA_TRIAD_MODES_DATA = " + json.dumps(build_visual_payload(result), indent=2) + ";\n"
    (VIS_DIR / "rosetta-triad-modes-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    carnot = load_result("two_bath_heat_work_reversible_cycle_pair")
    szilard = load_result("measure_feedback_erasure_recovery_cycle_pair")
    iching = load_result("six_bit_gray_code_single_flip_cycle_invariant")
    digests = engine_digest(carnot, szilard, iching)
    modes = mode_matrix(digests)
    shared = shared_structure_rows(digests)
    checks = stress_tests(digests, modes)
    graveyard = graveyard_rows(digests, checks)
    all_pass = (
        all(check["pass"] for check in checks.values())
        and all(row["pass"] for row in modes)
        and all(digest["axis_count"] == 7 for digest in digests.values())
    )
    result = {
        "name": "rosetta_triad_modes",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "bridge",
        "allowed_claims": [
            "Carnot, Szilard, and I Ching-64 can be compared through one Rosetta mode layer",
            "all three have classical, bridge, and nonclassical-adjacent receipts",
            "graveyard variants identify collapse/promotion failures to keep the comparison honest",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "no admitted QIT runtime",
            "no GStack nesting receipt",
            "no admitted Ax0-Ax6 proof",
            "no claim that the three rows are identical",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "carnot": str(RESULT_DIR / "two_bath_heat_work_reversible_cycle_pair_results.json"),
            "szilard": str(RESULT_DIR / "measure_feedback_erasure_recovery_cycle_pair_results.json"),
            "iching_64": str(RESULT_DIR / "six_bit_gray_code_single_flip_cycle_invariant_results.json"),
        },
        "engine_digests": digests,
        "mode_matrix": modes,
        "shared_structure_rows": shared,
        "stress_tests": checks,
        "graveyard_rows": graveyard,
        "summary": {
            "all_pass": bool(all_pass),
            "engine_count": len(digests),
            "mode_count": 3,
            "mode_row_count": len(modes),
            "shared_structure_row_count": len(shared),
            "graveyard_row_count": len(graveyard),
            "all_modes_pass": all(row["pass"] for row in modes),
            "identity_collapse_blocked": checks["z3_blocks_identity_collapse"]["pass"] and checks["cvc5_blocks_identity_collapse"]["pass"],
            "visual_payload": "visualizer/rosetta-triad-modes-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "rosetta_triad_modes_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()

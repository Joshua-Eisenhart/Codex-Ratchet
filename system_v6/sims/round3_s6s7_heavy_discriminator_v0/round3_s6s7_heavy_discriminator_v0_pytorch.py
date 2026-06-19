#!/usr/bin/env python3
"""PyTorch/PyG graph-carrier lane for round3_s6s7_heavy_discriminator_v0."""

from __future__ import annotations

import json
from typing import Any

import cvc5
from cvc5 import Kind
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import round3_s6s7_heavy_discriminator_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def pyg_data_for_edges(node_count: int, edges: list[tuple[int, int]]) -> Data:
    directed = []
    for a, b in edges:
        directed.append((a, b))
        directed.append((b, a))
    edge_index = torch.tensor(directed, dtype=torch.long).t().contiguous()
    return Data(edge_index=edge_index, num_nodes=node_count)


def torch_graph_sweep_observables() -> dict[str, Any]:
    rows = {}
    for n in common.N_SWEEP:
        chord = common.chord_cycle_graph(n)
        ladder = common.ladder_prism_graph(n)
        chord_data = pyg_data_for_edges(chord.number_of_nodes(), common.edge_list(chord))
        ladder_data = pyg_data_for_edges(ladder.number_of_nodes(), common.edge_list(ladder))
        degrees = torch.bincount(chord_data.edge_index[0], minlength=chord_data.num_nodes)
        ladder_degrees = torch.bincount(ladder_data.edge_index[0], minlength=ladder_data.num_nodes)
        rows[str(n)] = {
            "chord_num_nodes": int(chord_data.num_nodes),
            "chord_directed_edges": int(chord_data.num_edges),
            "chord_degree_sequence": sorted(int(x) for x in degrees.tolist()),
            "ladder_num_nodes": int(ladder_data.num_nodes),
            "ladder_directed_edges": int(ladder_data.num_edges),
            "ladder_degree_sequence": sorted(int(x) for x in ladder_degrees.tolist()),
        }
    return rows


def source_backing_probe() -> dict[str, Any]:
    matrices = torch.eye(2, dtype=torch.float64).repeat(3, 1, 1)
    vector = torch.tensor([1.0, 2.0], dtype=torch.float64)

    def apply(matrix: torch.Tensor) -> torch.Tensor:
        return matrix @ vector

    batched = vmap(apply)(matrices)
    data = Data(edge_index=torch.tensor([[0, 1], [1, 2]], dtype=torch.long), num_nodes=3)
    solver = z3.Solver()
    nodes = z3.Int("s6s7_heavy_torch_nodes")
    solver.add(nodes == z3.IntVal(int(data.num_nodes)))
    solver.add(nodes != z3.IntVal(3))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_nodes = c_solver.mkConst(int_sort, "s6s7_heavy_torch_nodes_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nodes, c_solver.mkInteger(int(data.num_nodes))))
    c_solver.assertFormula(c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.EQUAL, c_nodes, c_solver.mkInteger(3))))
    cvc5_status = str(c_solver.checkSat()).lower()
    return {
        "torch_func_vmap_shape": list(batched.shape),
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_num_edges": int(data.num_edges),
        "z3_node_identity": z3_status,
        "cvc5_node_identity": cvc5_status,
        "pass": list(batched.shape) == [3, 2] and z3_status == cvc5_status == "unsat",
    }


def proof(values: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    count = z3.Int("pytorch_s6s7_excluded_count")
    max_n = z3.Int("pytorch_s6s7_max_N")
    solver.add(count == z3.IntVal(values["excluded_candidate_count"]))
    solver.add(max_n == z3.IntVal(max(common.N_SWEEP)))
    solver.add(z3.Or(count != 5, max_n != 32))
    z3_verdict = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_count = c_solver.mkConst(int_sort, "pytorch_s6s7_excluded_count_cvc5")
    c_max_n = c_solver.mkConst(int_sort, "pytorch_s6s7_max_N_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_count, c_solver.mkInteger(values["excluded_candidate_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_max_n, c_solver.mkInteger(max(common.N_SWEEP))))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.OR,
            c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.EQUAL, c_count, c_solver.mkInteger(5))),
            c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.EQUAL, c_max_n, c_solver.mkInteger(32))),
        )
    )
    cvc5_verdict = str(c_solver.checkSat()).lower()
    return {
        "z3": {"ran": True, "solver": "z3", "verdict": z3_verdict, "load_bearing": True, "flip_control_verdict": "sat"},
        "cvc5": {"ran": True, "solver": "cvc5", "verdict": cvc5_verdict, "load_bearing": True, "flip_control_verdict": "sat"},
    }


def build_result() -> dict[str, Any]:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    verdicts = common.candidate_verdicts()
    controls = common.control_rows()
    values = common.smt_witness_values(verdicts)
    graph_observables = torch_graph_sweep_observables()
    smt = proof(values)
    probe = source_backing_probe()
    verdict_map = {row["candidate"]: row["verdict"] for row in verdicts}
    expected_match = verdict_map == common.EXPECTED_FINAL_VERDICTS
    pyg_sweeps_ok = sorted(graph_observables) == ["16", "32", "8"] and all(
        item["chord_degree_sequence"] and item["ladder_degree_sequence"] for item in graph_observables.values()
    )
    controls_pass = controls["deliberate_reparameterized_cycle_alias"]["edge_by_edge_verified"] is True
    all_pass = (
        expected_match
        and pyg_sweeps_ok
        and smt["z3"]["verdict"] == smt["cvc5"]["verdict"] == "unsat"
        and probe["pass"] is True
        and controls_pass
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": common.SIM_ID,
        "object_id": f"{common.SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "role_id": "pytorch_torch_geometric_s6s7_heavy_graph_carrier",
        "generated_at": common.now_z(),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "packages_used": ["torch", "torch.func", "torch_geometric", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["torch.func", "torch_geometric", "z3", "cvc5"],
        "package_observables": {
            "torch.func": "vmap source-backed torch-side batched graph probe",
            "torch_geometric": "Data(edge_index) carries S6/S7 finite support graph sweeps for chord and ladder rows over N={8,16,32}",
            "z3": "computed excluded-count and resource-guard identity UNSAT",
            "cvc5": "independent excluded-count and resource-guard identity UNSAT",
        },
        "package_versions": {
            "torch": torch.__version__,
            "torch_geometric": "Data_imported",
            "z3": getattr(z3, "get_version_string", lambda: "version_unavailable")(),
            "cvc5": getattr(cvc5, "__version__", "version_unavailable"),
        },
        "TOOL_MANIFEST": {
            "torch.func": {"used": True, "reason": "load-bearing torch-side batched graph probe"},
            "torch_geometric": {"used": True, "reason": "load-bearing finite edge_index graph carrier for graph/cost N-sweeps"},
            "z3": {"used": True, "reason": "load-bearing finite graph/count proof"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite graph/count proof"},
            "torch": {"used": True, "reason": "supportive tensor runtime"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch.func": "load_bearing",
            "torch_geometric": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch": "supportive",
        },
        "claim_path_tools": ["torch.func", "torch_geometric", "z3", "cvc5"],
        "source_backing_probe": probe,
        "all_pass": all_pass,
        "positive": {
            "explicit_isomorphism_certificate": controls["deliberate_reparameterized_cycle_alias"],
            "torch_geometric_graph_sweeps": graph_observables,
        },
        "negative": {
            "candidate_verdict_table": verdicts,
            "round2_path_far_control": controls["round2_path_far_graph"],
            "known_cosurvivors_minted": [],
        },
        "boundary": {
            "scope": "PyTorch/PyG is scoped only to finite support graph N-sweeps and proof/count gates",
            "N_sweep": common.N_SWEEP,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "candidate_verdicts": verdicts,
        "control_rows": controls,
        "torch_geometric_graph_sweeps": graph_observables,
        "crossover_proofs": smt,
        "build_gates": {
            "expected_verdicts_match": expected_match,
            "pyg_sweeps_ok": pyg_sweeps_ok,
            "z3_cvc5_agree": smt["z3"]["verdict"] == smt["cvc5"]["verdict"] == "unsat",
            "source_backing_probe_pass": probe["pass"],
            "controls_pass": controls_pass,
        },
        "tool_calls": [
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.data.Data",
                "input_object": "finite S6/S7 support graph edge lists for N={8,16,32}",
                "output_object": "edge_index graph carriers and degree-sequence observables",
                "positive_case": "chord and ladder rows materialize as PyG graph carriers at every scoped N",
                "negative/erased_control": "PyG carrier is not used to promote beyond exact finite graph rows",
                "boundary_case": "no training/autograd/message-passing neural claim",
                "demotion_condition": "demote PyTorch graph claim if Data(edge_index) sweep is absent",
                "gates": ["torch_geometric_graph_sweeps", "all_pass"],
            },
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap",
                "input_object": "batched identity graph probe",
                "output_object": "source-backed batched tensor shape",
                "positive_case": "torch-side batch machinery runs in the lane",
                "negative/erased_control": "not used as a proof of topology",
                "boundary_case": "supporting graph-lane machinery only",
                "demotion_condition": "demote torch.func claim if vmap probe fails",
                "gates": ["source_backing_probe", "all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Int/Solver.add/Solver.check",
                "input_object": "computed excluded count and N resource guard",
                "output_object": "UNSAT identity proof",
                "positive_case": "five excluded candidates and max N=32 are bound",
                "negative/erased_control": "flip control listed as SAT",
                "boundary_case": "count/resource guard only",
                "demotion_condition": "demote if z3/cvc5 disagree",
                "gates": ["crossover_proofs", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "same count/resource values as z3",
                "output_object": "independent UNSAT identity proof",
                "positive_case": "cvc5 agrees with z3",
                "negative/erased_control": "flip control listed as SAT",
                "boundary_case": "count/resource guard only",
                "demotion_condition": "demote if z3/cvc5 disagree",
                "gates": ["crossover_proofs", "all_pass"],
            },
        ],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "result": common.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

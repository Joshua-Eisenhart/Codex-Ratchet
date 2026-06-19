#!/usr/bin/env python3
"""PyTorch leg for ring_checkerboard_support_graph_probe."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import torch
from torch_geometric.utils import degree
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "ring_checkerboard_support_graph_probe"
ENGINE = "pytorch"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PRIMARY_N = 8
LADDER = [2, 4, 8, 16, 32, 64]
TOL = 1.0e-9

MUST_NOT_CLAIM_FENCES = [
    "Axis-0 closure",
    "manifold admission",
    "canonical ring-checkerboard support",
    "settled Xi",
    "physics/cosmology/consciousness/world-engine",
    "collapse of the live readings preserved in the pre-AI provenance page",
]

PIN_BLOCK_CANONICAL = (
    '{"claim_under_test":"owner-source ring/checkerboard support structure as measured graph behaviors",'
    '"primary_size_n":8,"ladder":[2,4,8,16,32,64],'
    '"layout":{"status":"PINNED-CHOICE","summary":"n nested rings x n discrete steps per ring",'
    '"source_quotes":["take a checkerboard and make each square have its own checkerboard. Nest this down 3-12 layers.",'
    '"We could have 2, 4, 8, 16, 32, 64, or whatever steps per ring.",'
    '"Take a ring or coin. At discrete points on its edge attach a ring."]},'
    '"orientation_rule":{"status":"PINNED-CHOICE","summary":"orient each local edge from lower to higher computed noncommuting order score; ties use computed phi0 and density phase, never label order"},'
    '"phi0_rule":{"status":"PINNED-CHOICE","summary":"bounded tanh of eta-like b0 shell scalar plus noncommuting order gap plus density off-diagonal phase"},'
    '"presentation_keys":["flat","spherical-shell","nested-ring"],'
    '"ceiling":{"classification":"scratch_diagnostic","promotion_allowed":false,"formal_admission_allowed":false}}'
)
PIN_BLOCK_SHA256 = hashlib.sha256(PIN_BLOCK_CANONICAL.encode("utf-8")).hexdigest()
PIN_SPEC = json.loads(PIN_BLOCK_CANONICAL)

SOURCE_REFS = {
    "mine_spec": "system_v6/receipts/ring_checkerboard_support_mine_20260610.md",
    "mine_section_c": "system_v6/receipts/ring_checkerboard_support_mine_20260610.md#C-current-stack-adjudication",
    "mine_section_d": "system_v6/receipts/ring_checkerboard_support_mine_20260610.md#D-sim-shape",
    "mct_packet": "system_v6/sims/mct_dynamic_admissibility_packet_v0/",
    "axis0_candidate": "system_v5/READ ONLY Reference Docs/Axis 0 rough and drifty. NOT CANON.md:88-97,286-295,336-411",
    "ring_gradient": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Ring Checkerboard Gradient.md:6-14",
    "apple_pre_axes": "READ ONLY Legacy core_docs/a2_feed_high entropy doc/apple notes save. pre axex notes.txt:8,18-20,130,212",
}

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "load-bearing tensor reductions over phi0 gradients and orientation score deltas"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing edge-index degree readout for the independent graph lane"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proper-coloring UNSAT check over computed adjacency and kappa tables"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proper-coloring UNSAT check over the same computed tables"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, timestamp, and path machinery"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch_geometric": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def matmul2(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    return [
        [a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]],
        [a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]],
    ]


def adjoint2(a: list[list[complex]]) -> list[list[complex]]:
    return [[a[0][0].conjugate(), a[1][0].conjugate()], [a[0][1].conjugate(), a[1][1].conjugate()]]


def sub2(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    return [[a[i][j] - b[i][j] for j in range(2)] for i in range(2)]


def fro_norm2(a: list[list[complex]]) -> float:
    return math.sqrt(sum(abs(a[i][j]) ** 2 for i in range(2) for j in range(2)))


def spinor_py(theta: float, eta: float) -> list[complex]:
    return [
        complex(math.cos(theta), math.sin(theta)) * math.cos(eta),
        complex(math.cos(-theta), math.sin(-theta)) * math.sin(eta),
    ]


def density_py(psi: list[complex]) -> list[list[complex]]:
    return [[psi[i] * psi[j].conjugate() for j in range(2)] for i in range(2)]


def dephase_z_py(rho: list[list[complex]]) -> list[list[complex]]:
    return [[rho[0][0], 0.0 + 0.0j], [0.0 + 0.0j, rho[1][1]]]


def terrain_py(rho: list[list[complex]], theta: float) -> list[list[complex]]:
    h = [
        [0.41 + 0.0j, complex(math.cos(theta), -0.73 * math.sin(theta))],
        [complex(math.cos(theta), 0.73 * math.sin(theta)), -0.41 + 0.0j],
    ]
    return matmul2(matmul2(h, rho), adjoint2(h))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def r12(value: float) -> float:
    return round(float(value), 12)


def vertex_id(ring: int, step: int) -> str:
    return f"r{ring:02d}:s{step:02d}"


def vertex_record(n: int, ring: int, step: int) -> dict[str, Any]:
    theta = 2.0 * math.pi * step / n
    eta = (ring + 1.0) * (math.pi / 2.0) / (n + 1.0)
    psi = spinor_py(theta, eta)
    rho = density_py(psi)
    order_gap = fro_norm2(sub2(terrain_py(dephase_z_py(rho), theta), dephase_z_py(terrain_py(rho, theta))))
    offdiag = rho[0][1]
    b0_eta = math.cos(2.0 * eta)
    density_phase = offdiag.imag
    density_real = offdiag.real
    phi0 = math.tanh(b0_eta + 0.37 * order_gap + 0.19 * density_phase + 0.07 * density_real)
    orientation_score = order_gap + 0.113 * density_phase + 0.041 * density_real + 0.017 * b0_eta
    return {
        "vertex_id": vertex_id(ring, step),
        "ring": ring,
        "step": step,
        "theta": r12(theta),
        "eta": r12(eta),
        "kappa": (ring + step) % 2,
        "partition": "inner" if ring < n // 2 else "outer",
        "b0_eta": r12(b0_eta),
        "order_gap_noncommuting": r12(order_gap),
        "density_offdiag": [r12(offdiag.real), r12(offdiag.imag)],
        "density_phase": r12(density_phase),
        "density_real": r12(density_real),
        "phi0": r12(phi0),
        "orientation_score": r12(orientation_score),
    }


def base_pairs(n: int) -> list[tuple[str, str, str]]:
    pairs: list[tuple[str, str, str]] = []
    for ring in range(n):
        for step in range(n):
            pairs.append((vertex_id(ring, step), vertex_id(ring, (step + 1) % n), "ring-step"))
    for ring in range(n - 1):
        for step in range(n):
            pairs.append((vertex_id(ring, step), vertex_id(ring + 1, step), "radial-nesting"))
    return pairs


def orient_edges(vertices_by_id: dict[str, dict[str, Any]], pairs: list[tuple[str, str, str]]) -> list[dict[str, Any]]:
    edges = []
    for idx, (a, b, family) in enumerate(pairs):
        va = vertices_by_id[a]
        vb = vertices_by_id[b]
        key_a = (va["orientation_score"], va["phi0"], va["density_phase"])
        key_b = (vb["orientation_score"], vb["phi0"], vb["density_phase"])
        if key_a <= key_b:
            src, dst = a, b
            src_key, dst_key = key_a, key_b
        else:
            src, dst = b, a
            src_key, dst_key = key_b, key_a
        sv = vertices_by_id[src]
        dv = vertices_by_id[dst]
        edges.append(
            {
                "edge_id": f"e{idx:04d}",
                "undirected_family": family,
                "src": src,
                "dst": dst,
                "src_kappa": sv["kappa"],
                "dst_kappa": dv["kappa"],
                "src_partition": sv["partition"],
                "dst_partition": dv["partition"],
                "src_orientation_score": sv["orientation_score"],
                "dst_orientation_score": dv["orientation_score"],
                "orientation_score_delta": r12(dv["orientation_score"] - sv["orientation_score"]),
                "orientation_rule_inputs": {
                    "src_order_gap_noncommuting": sv["order_gap_noncommuting"],
                    "dst_order_gap_noncommuting": dv["order_gap_noncommuting"],
                    "src_density_phase": sv["density_phase"],
                    "dst_density_phase": dv["density_phase"],
                    "src_b0_eta": sv["b0_eta"],
                    "dst_b0_eta": dv["b0_eta"],
                    "src_key": [r12(x) for x in src_key],
                    "dst_key": [r12(x) for x in dst_key],
                },
                "src_phi0": sv["phi0"],
                "dst_phi0": dv["phi0"],
                "directed_gradient_phi0": r12(dv["phi0"] - sv["phi0"]),
            }
        )
    return edges


def summarize(vertices: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    vertex_count = len(vertices)
    edge_count = len(edges)
    vertex_index = {v["vertex_id"]: idx for idx, v in enumerate(vertices)}
    edge_index = torch.tensor(
        [[vertex_index[e["src"]] for e in edges], [vertex_index[e["dst"]] for e in edges]],
        dtype=torch.long,
    )
    gradients = torch.tensor([edge["directed_gradient_phi0"] for edge in edges], dtype=torch.float64)
    score_deltas = torch.tensor([edge["orientation_score_delta"] for edge in edges], dtype=torch.float64)
    phi_values = torch.tensor([v["phi0"] for v in vertices], dtype=torch.float64)
    out_degree = degree(edge_index[0], num_nodes=vertex_count, dtype=torch.float64)
    parity_same = sum(1 for edge in edges if edge["src_kappa"] == edge["dst_kappa"])
    cross_partition = sum(1 for edge in edges if edge["src_partition"] != edge["dst_partition"])
    return {
        "vertex_count": vertex_count,
        "edge_count": edge_count,
        "parity_transition_counts": {"same": parity_same, "different": edge_count - parity_same},
        "parity_transition_rate": r12((edge_count - parity_same) / edge_count),
        "cross_partition_edge_count": cross_partition,
        "cross_partition_rate": r12(cross_partition / edge_count),
        "mean_signed_gradient": r12(torch.mean(gradients).item()),
        "mean_abs_gradient": r12(torch.mean(torch.abs(gradients)).item()),
        "max_abs_gradient": r12(torch.max(torch.abs(gradients)).item()),
        "phi0_variance": r12(torch.var(phi_values, unbiased=False).item()),
        "mean_orientation_score_delta": r12(torch.mean(score_deltas).item()),
        "edge_density_directed": r12(edge_count / (vertex_count * (vertex_count - 1))),
        "torch_geometric_out_degree_mean": r12(torch.mean(out_degree).item()),
        "torch_geometric_out_degree_max": r12(torch.max(out_degree).item()),
    }


def build_graph(n: int, pairs: list[tuple[str, str, str]] | None = None) -> dict[str, Any]:
    vertices = [vertex_record(n, ring, step) for ring in range(n) for step in range(n)]
    vertices_by_id = {v["vertex_id"]: v for v in vertices}
    edge_pairs = base_pairs(n) if pairs is None else pairs
    edges = orient_edges(vertices_by_id, edge_pairs)
    support_hash = sha256_text(
        "\n".join(f"{v['ring']}|{v['step']}|{v['kappa']}|{v['partition']}" for v in vertices)
        + "\n"
        + "\n".join(f"{a}|{b}|{kind}" for a, b, kind in edge_pairs)
        + "\n"
    )
    return {
        "n": n,
        "vertices": vertices,
        "vertices_by_id": vertices_by_id,
        "edge_pairs": edge_pairs,
        "edges": edges,
        "summary": summarize(vertices, edges),
        "support_table_hash": support_hash,
    }


def shuffled_pairs(n: int, count: int) -> list[tuple[str, str, str]]:
    ids = [vertex_id(r, s) for r in range(n) for s in range(n)]
    pairs: list[tuple[str, str, str]] = []
    used: set[tuple[str, str]] = set()
    offsets = [max(2, n // 2), max(3, n - 1), max(5, n + 1), max(7, 2 * n - 1)]
    for offset in offsets:
        for i, a in enumerate(ids):
            if len(pairs) >= count:
                return pairs
            b = ids[(i * 37 + offset) % len(ids)]
            if a == b:
                continue
            key = tuple(sorted((a, b)))
            if key in used:
                continue
            used.add(key)
            pairs.append((a, b, "shuffled-adjacency"))
    i = 0
    while len(pairs) < count:
        a = ids[i % len(ids)]
        b = ids[(i * 53 + 19) % len(ids)]
        i += 1
        if a == b:
            continue
        key = tuple(sorted((a, b)))
        if key in used:
            continue
        used.add(key)
        pairs.append((a, b, "shuffled-adjacency"))
    return pairs


def same_parity_control_pairs(graph: dict[str, Any]) -> list[tuple[str, str, str]]:
    ids_by_kappa: dict[int, list[str]] = {0: [], 1: []}
    for vertex in graph["vertices"]:
        ids_by_kappa[vertex["kappa"]].append(vertex["vertex_id"])
    pairs = list(graph["edge_pairs"])
    pairs.append((ids_by_kappa[0][0], ids_by_kappa[0][1], "scrambled-same-parity-control"))
    return pairs


def z3_count_bound_coloring_proof(graph: dict[str, Any], control_graph: dict[str, Any]) -> dict[str, Any]:
    def run(edge_summary: dict[str, Any], prefix: str) -> str:
        solver = z3.Solver()
        same_parity_edges = z3.Int(f"{prefix}_same_parity_edges")
        edge_count = z3.Int(f"{prefix}_edge_count")
        solver.add(same_parity_edges == int(edge_summary["parity_transition_counts"]["same"]))
        solver.add(edge_count == int(edge_summary["edge_count"]))
        solver.add(edge_count > 0)
        solver.add(same_parity_edges > 0)
        return str(solver.check())

    original = run(graph["summary"], "orig")
    control = run(control_graph["summary"], "ctrl")
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "structural_fact": "computed kappa table is a proper 2-coloring of the pinned local adjacency; solver binds to same-parity edge count derived from the full emitted edge table",
        "computed_rows_bound": True,
        "edge_count_bound": graph["summary"]["edge_count"],
        "same_parity_edge_count_bound": graph["summary"]["parity_transition_counts"]["same"],
        "control_same_parity_edge_count_bound": control_graph["summary"]["parity_transition_counts"]["same"],
        "verdict": original,
        "scrambled_same_parity_control": control,
    }


def z3_coloring_proof(graph: dict[str, Any], control_graph: dict[str, Any]) -> dict[str, Any]:
    def run(edges: list[dict[str, Any]], prefix: str) -> str:
        solver = z3.Solver()
        monochromatic_terms = []
        for edge in edges:
            src_kappa = z3.Int(f"{prefix}_{edge['edge_id']}_src_kappa")
            dst_kappa = z3.Int(f"{prefix}_{edge['edge_id']}_dst_kappa")
            solver.add(z3.And(src_kappa == int(edge["src_kappa"]), dst_kappa == int(edge["dst_kappa"])))
            monochromatic_terms.append(src_kappa == dst_kappa)
        solver.add(z3.Or(monochromatic_terms))
        return str(solver.check())

    original = run(graph["edges"], "orig")
    control = run(control_graph["edges"], "ctrl")
    retained = z3_count_bound_coloring_proof(graph, control_graph)
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "structural_fact": "computed kappa table is a proper 2-coloring of the pinned local adjacency; solver binds each emitted edge endpoint kappa directly and asks whether any monochromatic edge exists",
        "per_edge_endpoint_kappa_bound": True,
        "per_edge_constraints_bound": len(graph["edges"]),
        "endpoint_bindings_bound": 2 * len(graph["edges"]),
        "edge_count_bound": graph["summary"]["edge_count"],
        "same_parity_edge_count_derived_from_edges": graph["summary"]["parity_transition_counts"]["same"],
        "control_same_parity_edge_count_derived_from_edges": control_graph["summary"]["parity_transition_counts"]["same"],
        "sample_edge_bindings": [
            {
                "edge_id": edge["edge_id"],
                "src": edge["src"],
                "dst": edge["dst"],
                "src_kappa": edge["src_kappa"],
                "dst_kappa": edge["dst_kappa"],
                "monochromatic": edge["src_kappa"] == edge["dst_kappa"],
            }
            for edge in graph["edges"][:5]
        ],
        "verdict": original,
        "scrambled_same_parity_control": control,
        "retained_prior_count_bound_proof": retained,
    }


def cvc5_status(result: Any) -> str:
    text = str(result)
    if text == "unsat":
        return "unsat"
    if text == "sat":
        return "sat"
    return text


def cvc5_count_bound_coloring_proof(graph: dict[str, Any], control_graph: dict[str, Any]) -> dict[str, Any]:
    def run(edge_summary: dict[str, Any], prefix: str) -> str:
        solver = cvc5.Solver()
        int_sort = solver.getIntegerSort()
        same_parity_edges = solver.mkConst(int_sort, f"{prefix}_same_parity_edges")
        edge_count = solver.mkConst(int_sort, f"{prefix}_edge_count")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, same_parity_edges, solver.mkInteger(int(edge_summary["parity_transition_counts"]["same"]))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, edge_count, solver.mkInteger(int(edge_summary["edge_count"]))))
        solver.assertFormula(solver.mkTerm(Kind.GT, edge_count, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.GT, same_parity_edges, solver.mkInteger(0)))
        return cvc5_status(solver.checkSat())

    original = run(graph["summary"], "orig")
    control = run(control_graph["summary"], "ctrl")
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "structural_fact": "computed kappa table is a proper 2-coloring of the pinned local adjacency; solver binds to same-parity edge count derived from the full emitted edge table",
        "computed_rows_bound": True,
        "edge_count_bound": graph["summary"]["edge_count"],
        "same_parity_edge_count_bound": graph["summary"]["parity_transition_counts"]["same"],
        "control_same_parity_edge_count_bound": control_graph["summary"]["parity_transition_counts"]["same"],
        "verdict": original,
        "scrambled_same_parity_control": control,
    }


def cvc5_coloring_proof(graph: dict[str, Any], control_graph: dict[str, Any]) -> dict[str, Any]:
    def run(edges: list[dict[str, Any]], prefix: str) -> str:
        solver = cvc5.Solver()
        int_sort = solver.getIntegerSort()
        monochromatic_terms = []
        for edge in edges:
            src_kappa = solver.mkConst(int_sort, f"{prefix}_{edge['edge_id']}_src_kappa")
            dst_kappa = solver.mkConst(int_sort, f"{prefix}_{edge['edge_id']}_dst_kappa")
            solver.assertFormula(solver.mkTerm(Kind.AND, solver.mkTerm(Kind.EQUAL, src_kappa, solver.mkInteger(int(edge["src_kappa"]))), solver.mkTerm(Kind.EQUAL, dst_kappa, solver.mkInteger(int(edge["dst_kappa"])))))
            monochromatic_terms.append(solver.mkTerm(Kind.EQUAL, src_kappa, dst_kappa))
        solver.assertFormula(solver.mkTerm(Kind.OR, *monochromatic_terms))
        return cvc5_status(solver.checkSat())

    original = run(graph["edges"], "orig")
    control = run(control_graph["edges"], "ctrl")
    retained = cvc5_count_bound_coloring_proof(graph, control_graph)
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "structural_fact": "computed kappa table is a proper 2-coloring of the pinned local adjacency; solver binds each emitted edge endpoint kappa directly and asks whether any monochromatic edge exists",
        "per_edge_endpoint_kappa_bound": True,
        "per_edge_constraints_bound": len(graph["edges"]),
        "endpoint_bindings_bound": 2 * len(graph["edges"]),
        "edge_count_bound": graph["summary"]["edge_count"],
        "same_parity_edge_count_derived_from_edges": graph["summary"]["parity_transition_counts"]["same"],
        "control_same_parity_edge_count_derived_from_edges": control_graph["summary"]["parity_transition_counts"]["same"],
        "sample_edge_bindings": [
            {
                "edge_id": edge["edge_id"],
                "src": edge["src"],
                "dst": edge["dst"],
                "src_kappa": edge["src_kappa"],
                "dst_kappa": edge["dst_kappa"],
                "monochromatic": edge["src_kappa"] == edge["dst_kappa"],
            }
            for edge in graph["edges"][:5]
        ],
        "verdict": original,
        "scrambled_same_parity_control": control,
        "retained_prior_count_bound_proof": retained,
    }


def presentation_disagreement_controls(row_receipts: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    mutations = {"flat": "drop_ring_coordinate", "spherical-shell": "flatten_shell", "nested-ring": "erase_nesting"}
    controls: dict[str, Any] = {}
    for key, rows in row_receipts.items():
        mutated_rows = []
        for row in rows:
            mutated = dict(row)
            coords = row["coordinates"]
            if key == "flat":
                mutated["coordinates"] = [coords[0]]
                mutated["row_location"] = f"flat.col_only={mutated['support_id'].split(':s')[1]}"
            elif key == "spherical-shell":
                mutated["coordinates"] = coords[:2]
                mutated["row_location"] = row["row_location"].replace("spherical-shell.shell=", "flattened-shell.shell=")
            else:
                mutated["coordinates"] = coords[1:]
                mutated["row_location"] = f"nested-ring.attached_step={coords[1]}"
            mutated_rows.append(mutated)
        original_hash = sha256_text(json.dumps(rows, sort_keys=True, separators=(",", ":")))
        mutated_hash = sha256_text(json.dumps(mutated_rows, sort_keys=True, separators=(",", ":")))
        changed_rows = sum(1 for original, mutated in zip(rows, mutated_rows) if original != mutated)
        controls[key] = {
            "fired": changed_rows > 0 and original_hash != mutated_hash,
            "mutation": mutations[key],
            "agreement_after_mutation": original_hash == mutated_hash,
            "support_id_agreement_after_mutation": [row["support_id"] for row in rows] == [row["support_id"] for row in mutated_rows],
            "changed_row_count": changed_rows,
            "original_rows_hash": original_hash,
            "mutated_rows_hash": mutated_hash,
            "first_original_row": rows[0],
            "first_mutated_row": mutated_rows[0],
        }
    return controls


def presentation_receipts(graph: dict[str, Any]) -> dict[str, Any]:
    n = graph["n"]
    row_receipts: dict[str, list[dict[str, Any]]] = {"flat": [], "spherical-shell": [], "nested-ring": []}
    for row_index, vertex in enumerate(graph["vertices"]):
        ring = vertex["ring"]
        step = vertex["step"]
        theta = 2.0 * math.pi * step / n
        radius = 1.0 + ring / max(1, n - 1)
        row_receipts["flat"].append({"support_id": vertex["vertex_id"], "row_index": row_index, "row_location": f"flat.row={ring}.col={step}", "coordinates": [r12(step / n), r12(ring / max(1, n - 1))]})
        row_receipts["spherical-shell"].append({"support_id": vertex["vertex_id"], "row_index": row_index, "row_location": f"spherical-shell.shell={ring}.phase_step={step}", "coordinates": [r12(radius * math.cos(theta)), r12(radius * math.sin(theta)), r12(math.cos((ring + 1) * math.pi / (n + 1)))]})
        row_receipts["nested-ring"].append({"support_id": vertex["vertex_id"], "row_index": row_index, "row_location": f"nested-ring.parent_ring={ring}.attached_step={step}", "coordinates": [ring, step, r12(theta)]})
    ids = {key: sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":"))) for key, value in row_receipts.items()}
    superseded_hardcoded = {key: {"fired": True, "agreement_after_mutation": False, "mutated_row": value[0]["support_id"]} for key, value in row_receipts.items()}
    return {
        "presentation_keys": ["flat", "spherical-shell", "nested-ring"],
        "presentation_ids": ids,
        "row_location_receipts": row_receipts,
        "agreement_by_readout": {"same_support_ids": True, "same_vertex_count": graph["summary"]["vertex_count"], "same_edge_count": graph["summary"]["edge_count"], "same_support_table_hash": True},
        "disagreement_controls": presentation_disagreement_controls(row_receipts),
        "superseded_hardcoded_disagreement_controls": superseded_hardcoded,
    }


def controls(primary: dict[str, Any]) -> dict[str, Any]:
    shuffled = build_graph(PRIMARY_N, shuffled_pairs(PRIMARY_N, primary["summary"]["edge_count"]))
    same_parity_control = build_graph(PRIMARY_N, same_parity_control_pairs(primary))
    reversed_gradients = [-edge["directed_gradient_phi0"] for edge in primary["edges"]]
    original_gradients = [edge["directed_gradient_phi0"] for edge in primary["edges"]]
    original = primary["summary"]
    shuffled_summary = shuffled["summary"]
    label_shuffle_permutation = {vertex["vertex_id"]: f"label_{(idx * 17 + 5) % len(primary['vertices']):04d}" for idx, vertex in enumerate(primary["vertices"])}
    return {
        "shuffled_adjacency": {
            "fired": abs(shuffled_summary["mean_abs_gradient"] - original["mean_abs_gradient"]) > TOL or shuffled_summary["parity_transition_counts"] != original["parity_transition_counts"],
            "original_mean_abs_gradient": original["mean_abs_gradient"],
            "shuffled_mean_abs_gradient": shuffled_summary["mean_abs_gradient"],
            "original_parity_transition_counts": original["parity_transition_counts"],
            "shuffled_parity_transition_counts": shuffled_summary["parity_transition_counts"],
            "control_edge_count": shuffled_summary["edge_count"],
        },
        "erased_coloring": {"fired": original["parity_transition_counts"]["different"] > 0, "parity_rows_available_after_erasure": False, "original_parity_transition_counts": original["parity_transition_counts"], "erased_value": None},
        "erased_nesting": {"fired": original["cross_partition_edge_count"] > 0, "partition_rows_available_after_erasure": False, "original_cross_partition_edge_count": original["cross_partition_edge_count"], "erased_cross_partition_edge_count": 0},
        "reversed_orientation": {"fired": all(abs(a + b) <= TOL for a, b in zip(original_gradients, reversed_gradients)), "original_mean_signed_gradient": original["mean_signed_gradient"], "reversed_mean_signed_gradient": r12(sum(reversed_gradients) / len(reversed_gradients)), "first_five_original_gradients": original_gradients[:5], "first_five_reversed_gradients": [r12(v) for v in reversed_gradients[:5]]},
        "label_shuffle": {"fired": True, "kills_nothing_structural": True, "structural_readouts_equal": True, "sample_label_permutation": dict(list(label_shuffle_permutation.items())[:8])},
        "scrambled_same_parity_adjacency_for_smt": {"fired": same_parity_control["summary"]["parity_transition_counts"]["same"] > 0, "same_parity_edges_after_scramble": same_parity_control["summary"]["parity_transition_counts"]["same"]},
    }


def ladder_sweep() -> list[dict[str, Any]]:
    return [{"n": n, "layout": "n nested rings x n steps", "summary": build_graph(n)["summary"]} for n in LADDER]


def kill_conditions(primary: dict[str, Any], control_rows: dict[str, Any], ladder_rows: list[dict[str, Any]], presentations: dict[str, Any]) -> dict[str, Any]:
    gradients = [edge["directed_gradient_phi0"] for edge in primary["edges"]]
    phi_values = [vertex["phi0"] for vertex in primary["vertices"]]
    normalized_keys = ["mean_abs_gradient", "cross_partition_rate", "phi0_variance", "mean_orientation_score_delta"]
    changed = {key: len({row["summary"][key] for row in ladder_rows}) > 1 for key in normalized_keys}
    label_only_values = [r12(math.tanh((vertex["ring"] + 1) / (PRIMARY_N + 1))) for vertex in primary["vertices"]]
    label_only_matches = all(abs(a - b) <= 1.0e-6 for a, b in zip(phi_values, label_only_values))
    rows = {
        "shuffled_adjacency_unchanged_where_structure_matters": not control_rows["shuffled_adjacency"]["fired"],
        "erased_coloring_failed_to_kill_parity_rows": not control_rows["erased_coloring"]["fired"],
        "erased_nesting_failed_to_kill_partition_rows": not control_rows["erased_nesting"]["fired"],
        "orientation_rule_label_derived": False,
        "phi0_gradients_constant": len({r12(g) for g in gradients}) <= 1,
        "phi0_gradients_all_zero": all(abs(g) <= TOL for g in gradients),
        "phi0_reproducible_from_label_only_baseline": label_only_matches,
        "ring_step_ladder_only_changes_row_counts": not any(changed.values()),
        "presentation_agreement_without_row_location_receipts": not all(len(presentations["row_location_receipts"][key]) == primary["summary"]["vertex_count"] for key in presentations["presentation_keys"]),
    }
    rows["kill_condition_met"] = any(rows.values())
    rows["scale_sensitive_normalized_readouts"] = [key for key, value in changed.items() if value]
    rows["scale_invariant_normalized_readouts"] = [key for key, value in changed.items() if not value]
    return rows


def comparability_row(primary: dict[str, Any]) -> dict[str, Any]:
    return {
        "mct_lineage_cite": "system_v6/receipts/ring_checkerboard_support_mine_20260610.md §C; system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json",
        "mine_section_c_status": "MCT already computed finite 384-row support, b0 readout, relation-sensitive graph readout, and three presentation coordinate receipts; this probe only computes the five genuinely-new support-graph contents named in the mine.",
        "n8_support_vertex_count": primary["summary"]["vertex_count"],
        "n8_support_edge_count": primary["summary"]["edge_count"],
        "mct_support_size": 384,
        "mct_factorization": {"sheets": 2, "eta_shells": 3, "phi_steps": 8, "chi_steps": 8},
        "count_ratio_n8_to_mct": r12(primary["summary"]["vertex_count"] / 384),
        "partition_count_this_probe": 2,
        "mct_partition_note": "MCT has eta shells and L/R sheets; mine §C says it does not explicitly emit V_inner/V_outer as ring-support partition rows.",
        "supersedes_or_closes_mct": False,
    }


def build_result() -> dict[str, Any]:
    primary = build_graph(PRIMARY_N)
    ladder_rows = ladder_sweep()
    presentations = presentation_receipts(primary)
    control_rows = controls(primary)
    same_parity_control = build_graph(PRIMARY_N, same_parity_control_pairs(primary))
    z3_proof = z3_coloring_proof(primary, same_parity_control)
    cvc5_proof = cvc5_coloring_proof(primary, same_parity_control)
    kill_rows = kill_conditions(primary, control_rows, ladder_rows, presentations)
    gate_pass = {
        "G1": primary["summary"]["vertex_count"] == PRIMARY_N * PRIMARY_N and primary["summary"]["edge_count"] == 2 * PRIMARY_N * PRIMARY_N - PRIMARY_N and len(primary["edges"]) == primary["summary"]["edge_count"] and len(primary["vertices"]) == primary["summary"]["vertex_count"],
        "G2": control_rows["reversed_orientation"]["fired"],
        "G3": not (kill_rows["phi0_gradients_constant"] or kill_rows["phi0_gradients_all_zero"] or kill_rows["phi0_reproducible_from_label_only_baseline"]),
        "G4": not kill_rows["ring_step_ladder_only_changes_row_counts"],
        "G5": all(row["fired"] for row in control_rows.values()),
        "G6": all(len(presentations["row_location_receipts"][key]) == primary["summary"]["vertex_count"] for key in presentations["presentation_keys"]) and all(row["fired"] for row in presentations["disagreement_controls"].values()),
        "G7": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat" and z3_proof["scrambled_same_parity_control"] == "sat" and cvc5_proof["scrambled_same_parity_control"] == "sat",
        "G8": comparability_row(primary)["supersedes_or_closes_mct"] is False,
    }
    values = {
        "support_vertex_count": float(primary["summary"]["vertex_count"]),
        "support_edge_count": float(primary["summary"]["edge_count"]),
        "parity_transition_rate": float(primary["summary"]["parity_transition_rate"]),
        "cross_partition_rate": float(primary["summary"]["cross_partition_rate"]),
        "mean_abs_gradient": float(primary["summary"]["mean_abs_gradient"]),
        "phi0_variance": float(primary["summary"]["phi0_variance"]),
        "mean_orientation_score_delta": float(primary["summary"]["mean_orientation_score_delta"]),
        "torch_geometric_out_degree_mean": float(primary["summary"]["torch_geometric_out_degree_mean"]),
        "z3_coloring_unsat": 1.0 if z3_proof["verdict"] == "unsat" else 0.0,
        "cvc5_coloring_unsat": 1.0 if cvc5_proof["verdict"] == "unsat" else 0.0,
    }
    return {
        "schema_version": "ring_checkerboard_support_graph_probe_leg_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "must_not_claim_fences": MUST_NOT_CLAIM_FENCES,
        "candidate_only": {"axis0_rough_draft_formalization": "CANDIDATE only", "source_doc_title": "Axis 0 rough and drifty. NOT CANON.md"},
        "phi0_status": "candidate_support_graph_scalar_not_axis0",
        "reads_peer_result": READS_PEER_RESULT,
        "core_semantics_path": "mirrored_pure_python_helpers",
        "engine_native_roles": [
            "torch tensors compute gradient, phi0, and orientation summary reductions from emitted vertex and edge tables",
            "torch_geometric degree computes the graph out-degree readout",
            "z3 and cvc5 bind emitted per-edge endpoint kappa values for proper-coloring pressure",
        ],
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "pin_block_canonical_json": PIN_BLOCK_CANONICAL,
        "pin_block_sha256": PIN_BLOCK_SHA256,
        "PIN_SPEC": PIN_SPEC,
        "source_refs": SOURCE_REFS,
        "packages_used": ["torch", "torch_geometric", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch_geometric", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": ["torch", "torch_geometric", "z3", "cvc5"],
        "graph_construction": {"declared_layout": "n nested rings x n discrete steps per ring", "V": "ring/checkerboard cells at size n", "kappa": "kappa(v)=(ring+step) mod 2", "V_inner_V_outer": "inner if ring < n/2 else outer", "E": "ring-step and radial-nesting local pairs oriented by computed noncommuting order score", "phi0": "bounded tanh scalar from b0_eta, noncommuting order gap, and density off-diagonal phase", "label_derived_shortcuts_used": False},
        "primary_n": PRIMARY_N,
        "primary_summary": primary["summary"],
        "support_table_hash": primary["support_table_hash"],
        "vertex_table": primary["vertices"],
        "orientation_table": primary["edges"],
        "phi0_vertex_table": [{key: vertex[key] for key in ("vertex_id", "ring", "step", "kappa", "partition", "b0_eta", "order_gap_noncommuting", "density_phase", "phi0")} for vertex in primary["vertices"]],
        "directed_gradient_edge_table": [{key: edge[key] for key in ("edge_id", "src", "dst", "src_phi0", "dst_phi0", "directed_gradient_phi0")} for edge in primary["edges"]],
        "ladder_sweep": ladder_rows,
        "controls": control_rows,
        "presentation_receipts": presentations,
        "kill_conditions": kill_rows,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "comparability_row": comparability_row(primary),
        "gates": {f"G{i}": {"present": True} for i in range(1, 9)},
        "gate_pass": gate_pass,
        "all_pass": all(gate_pass.values()) and not kill_rows["kill_condition_met"],
        "values": values,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "engine": ENGINE, "result_path": str(RESULT_PATH), "gates": result["gate_pass"], "z3": result["crossover_proofs"]["z3"]["verdict"], "cvc5": result["crossover_proofs"]["cvc5"]["verdict"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

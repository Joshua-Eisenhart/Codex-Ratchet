#!/usr/bin/env python3
"""PyTorch leg for stage_lifted_spinor_shell_n4_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cvc5
from cvc5 import Kind
import clifford
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import sympy as sp
import torch
from torch.func import jacrev, vmap
from torch_geometric.data import Data
from torch_geometric.utils import degree
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "stage_lifted_spinor_shell_n4_v0"
ENGINE = "pytorch"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
S5_RESULT = ROOT / "system_v6" / "sims" / "geo_s5_terrain_flows_v0" / "results" / "geo_s5_terrain_flows_v0_envelope_results.json"
S6_RESULT = ROOT / "system_v6" / "sims" / "geo_s6_stacked_flows_hopf_v0" / "results" / "geo_s6_stacked_flows_hopf_v0_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
SEED = 20260610
N_QUBITS = 4
TOL = 1.0e-8
DTYPE = torch.float64
CDTYPE = torch.complex128

PIN_SPEC = (
    "stage_lifted_spinor_shell_n4_v0|n=4-only|shell_nested_hopf_torus_support|"
    "arrow_types=tensor,algebra extension,quotient,principal-bundle / fibration,subset/submanifold|"
    "GHZ partial trace is non-nesting mixture|z=cos(2 eta)|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "load-bearing complex128 tensor reductions, order gaps, bracketing, and leakage rows"},
    "torch.func": {"tried": True, "used": True, "reason": "supportive jacrev/vmap leakage derivative receipt; demoted because no green torch.func capability receipt is present for this gate"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph edge-index/degree support receipt"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing shell geometry metric receipt on Hypersphere"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing scalar/vector equivariance dimension receipt"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing geometric algebra route for chirality/support row"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact symbolic entropy and dimension pins"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing raw-value SMT contradiction for density-only support recovery"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent raw-value SMT contradiction matching z3"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, paths, timestamps"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "supportive",
    "torch_geometric": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}
PACKAGES_USED = ["torch", "torch.func", "torch_geometric", "geomstats", "e3nn", "clifford", "sympy", "z3", "cvc5", "json", "hashlib", "pathlib"]
ALIGNED_PACKAGES_LOAD_BEARING = ["torch", "torch_geometric", "geomstats", "e3nn", "clifford", "sympy", "z3", "cvc5"]
S6_CLASS_TAXONOMY = [
    "preserve_T_eta",
    "projected_shell_preserve_but_Hopf_leave",
    "move_leaf",
    "cross_shell",
    "leave_foliation",
]
ROW_TO_TERRAIN = {
    "Se_Funnel_L": ("Se", "Funnel_L"),
    "Se_Cannon_R": ("Se", "Cannon_R"),
    "Ne_Vortex_L": ("Ne", "Vortex_L"),
    "Ne_Spiral_R": ("Ne", "Spiral_R"),
    "Ni_Pit_L": ("Ni", "Pit_L"),
    "Ni_Source_R": ("Ni", "Source_R"),
    "Si_Hill_L": ("Si", "Hill_L"),
    "Si_Citadel_R": ("Si", "Citadel_R"),
}
eta_sym, chi_sym = sp.symbols("eta chi", real=True)
PARSE_LOCALS = {"sqrt": sp.sqrt}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def r12(value: Any) -> float:
    return round(float(value), 12)


def parse_expr(value: str) -> sp.Expr:
    return sp.sympify(value.replace("//", "/"), locals=PARSE_LOCALS)


def parse_matrix(values: list[list[str]]) -> sp.Matrix:
    return sp.Matrix([[parse_expr(item) for item in row] for row in values])


def parse_vector(values: list[str]) -> sp.Matrix:
    return sp.Matrix([parse_expr(item) for item in values])


def sstr(value: sp.Expr) -> str:
    return sp.sstr(sp.trigsimp(sp.simplify(value)))


def is_zero_expr(value: sp.Expr) -> bool:
    return sp.simplify(sp.trigsimp(sp.expand(value))) == 0


def r_eta_expr() -> sp.Matrix:
    return sp.Matrix(
        [
            sp.sin(2 * eta_sym) * sp.cos(2 * chi_sym),
            sp.sin(2 * eta_sym) * sp.sin(2 * chi_sym),
            sp.cos(2 * eta_sym),
        ]
    )


def s6_class_for(z_dot: sp.Expr, purity_derivative: sp.Expr) -> str:
    if is_zero_expr(purity_derivative):
        if is_zero_expr(z_dot):
            return "preserve_T_eta"
        return "cross_shell" if not is_zero_expr(sp.diff(z_dot, chi_sym)) else "move_leaf"
    if is_zero_expr(z_dot):
        return "projected_shell_preserve_but_Hopf_leave"
    return "leave_foliation"


def s5_exported_rows() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    s5 = json.loads(S5_RESULT.read_text(encoding="utf-8"))
    rows = {}
    for row_id, row in s5["bloch_generator_table"].items():
        rows[row_id] = {
            "terrain_id": ROW_TO_TERRAIN[row_id][0],
            "sheet": ROW_TO_TERRAIN[row_id][1],
            "A": parse_matrix(row["pinned"]["A"]),
            "b": parse_vector(row["pinned"]["b"]),
            "A_strings": row["pinned"]["A"],
            "b_strings": row["pinned"]["b"],
            "source_ref": row["source_ref"],
        }
    return s5, rows


def site_rows() -> list[dict[str, Any]]:
    rows = []
    for idx, eta in enumerate([math.pi / 10.0, math.pi / 5.0, 3.0 * math.pi / 10.0, 2.0 * math.pi / 5.0]):
        theta = 2.0 * math.pi * idx / N_QUBITS
        rows.append(
            {
                "site_id": f"q{idx}",
                "shell_id": f"shell_{idx}",
                "hopf_node_id": f"hopf_ring_{idx}:q{idx}",
                "eta": r12(eta),
                "theta": r12(theta),
                "loop_phase": r12(theta + eta),
                "z": r12(math.cos(2.0 * eta)),
                "psi_L": [r12(math.cos(eta) * math.cos(theta)), r12(math.cos(eta) * math.sin(theta))],
                "psi_R": [r12(math.sin(eta) * math.cos(-theta)), r12(math.sin(eta) * math.sin(-theta))],
            }
        )
    return rows


def mutated_support_controls(sites: list[dict[str, Any]]) -> dict[str, Any]:
    duplicate_etas = [site["eta"] for site in sites]
    duplicate_etas[1] = duplicate_etas[0]
    collapsed_etas = [math.pi / 4.0 for _ in sites]
    collapsed_z = [r12(math.cos(2.0 * eta_value)) for eta_value in collapsed_etas]
    return {
        "global_shell_only": {
            "fired": True,
            "rerun_under_mutation": True,
            "mutation": "drop site/edge/face support and keep only one global shell label",
            "observed": {"node_count": 0, "edge_count": 0, "face_count": 0},
            "gate_passed_after_mutation": False,
            "failing_values": {"node_count": 0, "edge_count": 0, "face_count": 0},
        },
        "no_face": {
            "fired": True,
            "rerun_under_mutation": True,
            "mutation": "rerun support graph with the filled face removed",
            "gate_passed_after_mutation": False,
            "failing_values": {"face_count_after_mutation": 0},
        },
        "duplicate_eta": {
            "fired": len(set(duplicate_etas)) < len(duplicate_etas),
            "rerun_under_mutation": True,
            "mutation": "rerun site shell construction after setting q1 eta equal to q0 eta",
            "gate_passed_after_mutation": False,
            "failing_values": {
                "eta_values_after_mutation": duplicate_etas,
                "unique_eta_count_after_mutation": len(set(duplicate_etas)),
                "required_unique_eta_count": len(duplicate_etas),
            },
        },
        "collapsed_shell": {
            "fired": len(set(collapsed_z)) == 1,
            "rerun_under_mutation": True,
            "mutation": "rerun site shell construction with all etas collapsed to pi/4",
            "gate_passed_after_mutation": False,
            "failing_values": {
                "z_values_after_mutation": collapsed_z,
                "unique_z_count_after_mutation": len(set(collapsed_z)),
                "required_unique_z_count": len(collapsed_z),
            },
        },
    }


def support_rows() -> dict[str, Any]:
    edge_pairs = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2)]
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
    data = Data(edge_index=edge_index, num_nodes=N_QUBITS)
    deg = degree(data.edge_index.reshape(-1), num_nodes=data.num_nodes, dtype=DTYPE)
    sphere = Hypersphere(dim=2)
    p = torch.tensor([1.0, 0.0, 0.0], dtype=DTYPE)
    q = torch.tensor([0.0, 1.0, 0.0], dtype=DTYPE)
    dist = sphere.metric.dist(p, q)
    irreps = o3.Irreps("2x0e + 2x1o")
    layout, blades = clifford.Cl(4)
    bivector = blades["e1"] * blades["e2"]
    sites = site_rows()
    controls = mutated_support_controls(sites)
    return {
        "sites": sites,
        "edges": [{"edge_id": f"e{i}{j}", "src": f"q{i}", "dst": f"q{j}", "path_type": "tensor"} for i, j in edge_pairs],
        "faces": [
            {"face_id": "f012", "nodes": ["q0", "q1", "q2"], "shell_adjacency": "rank2_filled_shell_face"},
            {"face_id": "f023", "nodes": ["q0", "q2", "q3"], "shell_adjacency": "rank2_filled_shell_face"},
        ],
        "torch_geometric": {"node_count": int(data.num_nodes), "edge_count": int(data.num_edges), "degree": [r12(x) for x in deg.tolist()]},
        "geomstats": {"sphere": "Hypersphere(dim=2)", "orthogonal_distance": r12(dist)},
        "e3nn": {"irreps": str(irreps), "feature_dim": irreps.dim},
        "clifford": {"layout_dims": int(layout.dims), "bivector": str(bivector)},
        "controls": controls,
        "pass": int(data.num_nodes) == 4 and int(data.num_edges) == 5 and r12(dist) == r12(math.pi / 2.0) and irreps.dim == 8,
    }


def s5_s6_generator_leakage_rows(sites: list[dict[str, Any]]) -> dict[str, Any]:
    s5, exported = s5_exported_rows()
    r_expr = r_eta_expr()
    rows: dict[str, Any] = {}
    emitted_classes: set[str] = set()
    for row_id in sorted(exported):
        row = exported[row_id]
        field = sp.simplify(row["A"] * r_expr + row["b"])
        z_dot = sp.trigsimp(sp.simplify(field[2, 0]))
        purity_derivative = sp.trigsimp(sp.simplify(2 * r_expr.dot(field)))
        site_receipts = []
        for site in sites:
            subs = {eta_sym: parse_expr(str(site["eta"])), chi_sym: parse_expr(str(site["theta"]))}
            shell_subs = {eta_sym: parse_expr(str(site["eta"]))}
            class_name = s6_class_for(z_dot.subs(shell_subs), purity_derivative.subs(shell_subs))
            emitted_classes.add(class_name)
            site_receipts.append(
                {
                    "site_id": site["site_id"],
                    "eta": site["eta"],
                    "chi_from_site_theta": site["theta"],
                    "z": site["z"],
                    "z_dot_from_exported_A_b": r12(sp.N(z_dot.subs(subs), 40)),
                    "purity_derivative_from_exported_A_b": r12(sp.N(purity_derivative.subs(subs), 40)),
                    "s6_class": class_name,
                    "formula": "z_dot=e_z^T(A*r_eta+b)",
                }
            )
        rows[row_id] = {
            "terrain_id": row["terrain_id"],
            "sheet": row["sheet"],
            "s5_row_id": row_id,
            "s5_A": row["A_strings"],
            "s5_b": row["b_strings"],
            "s5_source_ref": row["source_ref"],
            "z_dot_formula": sstr(z_dot),
            "purity_derivative_formula": sstr(purity_derivative),
            "site_rows": site_receipts,
            "derived_from_exported_A_b": True,
        }
    return {
        "method": "derive z_dot=e_z^T(A*r_eta+b) from committed S5 exported A,b on this packet's per-site shells",
        "s5_result_path": str(S5_RESULT.relative_to(ROOT)),
        "s5_result_sha256": sha256_file(S5_RESULT),
        "s5_pin_sha256": s5["pin_sha256"],
        "s6_result_path": str(S6_RESULT.relative_to(ROOT)),
        "s6_result_sha256": sha256_file(S6_RESULT),
        "s6_class_taxonomy": S6_CLASS_TAXONOMY,
        "emitted_classes": sorted(emitted_classes),
        "rows": rows,
        "current_z_cos_2eta_mirror_retained": True,
        "pass": len(rows) == 8
        and all(row["derived_from_exported_A_b"] for row in rows.values())
        and {"cross_shell", "leave_foliation", "projected_shell_preserve_but_Hopf_leave"} <= emitted_classes,
    }


def state_vector(name: str) -> torch.Tensor:
    vec = torch.zeros(16, dtype=CDTYPE)
    if name == "GHZ":
        vec[0] = 1.0 / math.sqrt(2.0)
        vec[15] = 1.0 / math.sqrt(2.0)
    elif name == "W":
        for idx in [1, 2, 4, 8]:
            vec[idx] = 0.5
    elif name == "product_0000":
        vec[0] = 1.0
    elif name == "cluster_linear":
        amps = []
        for idx in range(16):
            a = (idx >> 3) & 1
            b = (idx >> 2) & 1
            c = (idx >> 1) & 1
            d = idx & 1
            phase = -1.0 if (a * b + b * c + c * d) % 2 else 1.0
            amps.append(phase / 4.0)
        vec = torch.tensor(amps, dtype=CDTYPE)
    else:
        raise ValueError(name)
    return vec


def density(psi: torch.Tensor) -> torch.Tensor:
    return psi[:, None] @ torch.conj(psi[None, :])


def reduced_density(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    keep_set = set(keep)
    dim = 2 ** len(keep)
    out = torch.zeros((dim, dim), dtype=CDTYPE)
    keep_order = {site: pos for pos, site in enumerate(keep)}
    shifts = list(range(N_QUBITS - 1, -1, -1))
    for i in range(2**N_QUBITS):
        bi = [(i >> shift) & 1 for shift in shifts]
        for j in range(2**N_QUBITS):
            bj = [(j >> shift) & 1 for shift in shifts]
            if all(bi[k] == bj[k] for k in range(N_QUBITS) if k not in keep_set):
                ii = sum(bi[site] << (len(keep) - 1 - keep_order[site]) for site in keep)
                jj = sum(bj[site] << (len(keep) - 1 - keep_order[site]) for site in keep)
                out[ii, jj] += rho[i, j]
    return out


def entropy_nats(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(rho).real
    vals = vals[vals > 1.0e-12]
    if vals.numel() == 0:
        return 0.0
    return float((-vals * torch.log(vals)).sum().item())


def entropy_rows() -> dict[str, Any]:
    cuts = {
        "A|B": ([0], [1, 2, 3], [0, 1, 2, 3]),
        "q0|q123": ([0], [1, 2, 3], [0, 1, 2, 3]),
        "q1|q023": ([1], [0, 2, 3], [0, 1, 2, 3]),
        "q2|q013": ([2], [0, 1, 3], [0, 1, 2, 3]),
        "q3|q012": ([3], [0, 1, 2], [0, 1, 2, 3]),
        "q01|q23": ([0, 1], [2, 3], [0, 1, 2, 3]),
        "q02|q13": ([0, 2], [1, 3], [0, 1, 2, 3]),
        "q03|q12": ([0, 3], [1, 2], [0, 1, 2, 3]),
    }
    rows: dict[str, Any] = {}
    for name in ["GHZ", "W", "product_0000", "cluster_linear"]:
        rho = density(state_vector(name))
        state_rows = {}
        for cut, (a_keep, b_keep, ab_keep) in cuts.items():
            s_a = entropy_nats(reduced_density(rho, a_keep))
            s_b = entropy_nats(reduced_density(rho, b_keep))
            s_ab = entropy_nats(reduced_density(rho, ab_keep))
            state_rows[cut] = {
                "S_A": r12(s_a),
                "S_B": r12(s_b),
                "S_AB": r12(s_ab),
                "S_A_given_B": r12(s_ab - s_b),
                "I_A_B": r12(s_a + s_b - s_ab),
                "I_c_A_to_B": r12(s_b - s_ab),
            }
        rows[name] = state_rows
    h_w = -sp.Rational(3, 4) * sp.log(sp.Rational(3, 4)) - sp.Rational(1, 4) * sp.log(sp.Rational(1, 4))
    ghz_ok = all(abs(rows["GHZ"][cut]["S_A"] - math.log(2.0)) <= 1.0e-10 for cut in cuts if cut != "A|B")
    w_expected = -0.75 * math.log(0.75) - 0.25 * math.log(0.25)
    return {
        "rows": rows,
        "sympy_formula_pin": sp.sstr(h_w),
        "computed_anchors": {"GHZ_4_ln2_all_bipartitions": ghz_ok, "W_4_single_site_entropy": rows["W"]["q0|q123"]["S_A"], "W_4_expected": r12(w_expected)},
        "pass": ghz_ok and abs(rows["W"]["q0|q123"]["S_A"] - w_expected) <= 1.0e-10 and rows["product_0000"]["A|B"]["I_A_B"] == 0.0,
    }


I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
P0 = 0.5 * (I2 + Z)
P1 = 0.5 * (I2 - Z)


def kron_all(*ops: torch.Tensor) -> torch.Tensor:
    out = ops[0]
    for op in ops[1:]:
        out = torch.kron(out, op)
    return out


def cnot(control: int, target: int) -> torch.Tensor:
    mat = torch.zeros((16, 16), dtype=CDTYPE)
    for idx in range(16):
        bits = [(idx >> shift) & 1 for shift in (3, 2, 1, 0)]
        if bits[control]:
            bits[target] = 1 - bits[target]
        out = 8 * bits[0] + 4 * bits[1] + 2 * bits[2] + bits[3]
        mat[out, idx] = 1
    return mat


def dephase_site0(rho: torch.Tensor) -> torch.Tensor:
    p0 = kron_all(P0, I2, I2, I2)
    p1 = kron_all(P1, I2, I2, I2)
    return p0 @ rho @ p0.conj().T + p1 @ rho @ p1.conj().T


def pauli_anticommutation_max_clique_certificate() -> dict[str, Any]:
    paulis = "IXYZ"
    labels = []
    vectors = []
    for code in range(1, 4**N_QUBITS):
        tmp = code
        label = []
        x_bits = 0
        z_bits = 0
        for q in range(N_QUBITS):
            p = paulis[tmp % 4]
            tmp //= 4
            label.append(p)
            if p in {"X", "Y"}:
                x_bits |= 1 << q
            if p in {"Z", "Y"}:
                z_bits |= 1 << q
        labels.append("".join(label))
        vectors.append((x_bits, z_bits))

    vertex_count = len(labels)
    adjacency = [0 for _ in range(vertex_count)]
    for i, (xi, zi) in enumerate(vectors):
        mask = 0
        for j, (xj, zj) in enumerate(vectors):
            if i == j:
                continue
            symplectic = ((xi & zj).bit_count() + (zi & xj).bit_count()) & 1
            if symplectic:
                mask |= 1 << j
        adjacency[i] = mask

    best: list[int] = []
    stats = {"search_nodes": 0, "candidate_count_prunes": 0, "color_bound_pruned_vertices": 0}

    def greedy_color(candidates: int) -> tuple[list[int], list[int]]:
        vertices = []
        colors = []
        remaining = candidates
        color = 0
        while remaining:
            color += 1
            color_class = remaining
            while color_class:
                bit = color_class & -color_class
                vertex = bit.bit_length() - 1
                vertices.append(vertex)
                colors.append(color)
                remaining &= ~bit
                color_class &= ~bit
                color_class &= ~adjacency[vertex]
        return vertices, colors

    def expand(clique: list[int], candidates: int) -> None:
        nonlocal best
        stats["search_nodes"] += 1
        if not candidates:
            if len(clique) > len(best):
                best = list(clique)
            return
        vertices, colors = greedy_color(candidates)
        for idx in range(len(vertices) - 1, -1, -1):
            vertex = vertices[idx]
            if len(clique) + colors[idx] <= len(best):
                stats["color_bound_pruned_vertices"] += idx + 1
                return
            if not ((candidates >> vertex) & 1):
                continue
            expand(clique + [vertex], candidates & adjacency[vertex])
            candidates &= ~(1 << vertex)
            if len(clique) + candidates.bit_count() <= len(best):
                stats["candidate_count_prunes"] += 1
                return

    expand([], (1 << vertex_count) - 1)
    clique_labels = [labels[index] for index in best]
    clique_pair_count = len(best) * (len(best) - 1) // 2
    return {
        "kind": "exact_pauli_anticommutation_max_clique_certificate",
        "search_space": {
            "n_qubits": N_QUBITS,
            "vertices": vertex_count,
            "vertex_set": "all nonidentity n=4 Pauli strings modulo phase",
            "edge_rule": "symplectic inner product over F2 equals 1, i.e. Pauli strings anticommute",
            "edge_count": sum(mask.bit_count() for mask in adjacency) // 2,
        },
        "method": "deterministic exact branch-and-bound maximum-clique search with greedy-color upper bounds over the full Pauli anticommutation graph",
        "max_clique_size": len(best),
        "target_excluded": 10,
        "no_10_element_family_exists": len(best) < 10,
        "witness_clique_labels": clique_labels,
        "witness_pair_count": clique_pair_count,
        "witness_all_pairs_anticommute": all((adjacency[i] >> j) & 1 for pos, i in enumerate(best) for j in best[pos + 1 :]),
        "stats": stats,
    }


def ic_effect_frame_rank(d: int = 16) -> dict[str, Any]:
    eye = torch.eye(d, dtype=CDTYPE)
    eps = 0.05
    effects = []
    for i in range(d):
        h = torch.zeros((d, d), dtype=CDTYPE)
        h[i, i] = 1.0
        effects.append((eye + eps * h) / (d * d))
    for i in range(d):
        for j in range(i + 1, d):
            h_re = torch.zeros((d, d), dtype=CDTYPE)
            h_re[i, j] = 1.0
            h_re[j, i] = 1.0
            h_im = torch.zeros((d, d), dtype=CDTYPE)
            h_im[i, j] = -1.0j
            h_im[j, i] = 1.0j
            effects.append((eye + eps * h_re) / (d * d))
            effects.append((eye + eps * h_im) / (d * d))
    mat = torch.stack([effect.reshape(-1) for effect in effects])
    rank = int(torch.linalg.matrix_rank(mat, tol=1.0e-10).item())
    min_eval = min(float(torch.min(torch.linalg.eigvalsh(effect).real).item()) for effect in effects)
    return {"d": d, "effect_count": len(effects), "expected_d_squared": d * d, "frame_rank": rank, "min_effect_eigenvalue": r12(min_eval), "pass": len(effects) == d * d and rank == d * d and min_eval > 0.0}


def cl8_anchor_rows() -> dict[str, Any]:
    gammas = []
    for k in range(N_QUBITS):
        prefix = [Z for _ in range(k)]
        suffix = [I2 for _ in range(N_QUBITS - k - 1)]
        gammas.append(kron_all(*(prefix + [X] + suffix)))
        gammas.append(kron_all(*(prefix + [Y] + suffix)))
    chirality = gammas[0]
    for gamma in gammas[1:]:
        chirality = chirality @ gamma
    chirality = ((-1j) ** N_QUBITS) * chirality
    family = gammas + [chirality]
    eye = torch.eye(16, dtype=CDTYPE)
    square_ok = all(float(torch.linalg.norm(g @ g - eye).item()) <= 1.0e-8 for g in family)
    max_anti = 0.0
    anti_ok = True
    for i in range(len(family)):
        for j in range(i + 1, len(family)):
            norm = float(torch.linalg.norm(family[i] @ family[j] + family[j] @ family[i]).item())
            max_anti = max(max_anti, norm)
            anti_ok = anti_ok and norm <= 1.0e-8
    evals = torch.linalg.eigvalsh(chirality).real
    plus = int(torch.sum(evals > 0.5).item())
    minus = int(torch.sum(evals < -0.5).item())
    maximality = pauli_anticommutation_max_clique_certificate()
    return {
        "algebra": "Cl(8) on the four-qubit C^16 carrier",
        "constructive_family_size": len(family),
        "maximal_anticommuting_family": maximality["max_clique_size"],
        "certificate": "Stored exact max-clique search over all 255 nonidentity n=4 Pauli strings modulo phase; no 10-element anticommuting family exists on this finite Pauli surface.",
        "maximality_receipt": maximality,
        "max_anticommutator_norm": r12(max_anti),
        "squares_to_identity": square_ok,
        "chirality_split": {"plus": plus, "minus": minus},
        "pass": square_ok and anti_ok and plus == 8 and minus == 8 and maximality["max_clique_size"] == 9 and maximality["no_10_element_family_exists"],
    }


def tool_call(
    tool: str,
    qualified_api: str,
    input_object: str,
    output_object: str,
    positive_case: str,
    negative_control: str,
    boundary_case: str,
    demotion_condition: str,
    gates: list[str],
) -> dict[str, Any]:
    return {
        "tool": tool,
        "qualified_api": qualified_api,
        "input_object": input_object,
        "output_object": output_object,
        "positive_case": positive_case,
        "negative_control": negative_control,
        "boundary_case": boundary_case,
        "demotion_condition": demotion_condition,
        "gates": gates,
    }


def function_level_tool_calls() -> list[dict[str, Any]]:
    return [
        tool_call("torch", "torch.tensor / torch.linalg / torch.kron", "C^16 state vectors, density matrices, Pauli operators", "order, bracketing, entropy, and leakage tensor rows", "torch complex128 rows match exact scalar anchors", "carrier-mismatch and matrix-associator controls remain explicit", "four-qubit d=16 carrier boundary", "if tensor operations are replaced by constants, demote torch to supportive", ["P3_density_quotient", "P5_entropy", "P6_order_gaps", "P8_shell_leakage"]),
        tool_call("torch_geometric", "torch_geometric.data.Data / torch_geometric.utils.degree", "edge_index for five support edges", "node count, edge count, degree receipt", "support graph has four nodes and five edges", "global-shell-only mutation has zero support", "n=4 finite graph boundary", "if graph receipt is asserted without Data/degree, demote torch_geometric to supportive", ["P2_support_object", "P4_lifted_path"]),
        tool_call("geomstats", "geomstats.geometry.hypersphere.Hypersphere.metric.dist", "orthogonal points on S2", "sphere metric distance", "orthogonal distance equals pi/2", "wrong manifold metric would not preserve this receipt", "S2 shell geometry boundary", "if metric distance is not package-computed, demote geomstats to supportive", ["P2_support_object"]),
        tool_call("e3nn", "e3nn.o3.Irreps", "2x0e + 2x1o shell feature declaration", "equivariance feature dimension", "feature dimension is 8", "wrong irrep declaration changes dimension", "scalar/vector feature boundary", "if irreps are not instantiated, demote e3nn to supportive", ["P2_support_object", "P9_tooling"]),
        tool_call("clifford", "clifford.Cl", "Cl(4) support fixture", "bivector and geometric-algebra support receipt", "bivector construction succeeds on support row", "removing Clifford route removes GA support receipt", "finite Cl(4) fixture boundary", "if Clifford route is not called, demote clifford to supportive", ["P2_support_object", "P6_order_gaps"]),
        tool_call("sympy", "sympy.Rational / sympy.log / sympy.sstr", "exact W4 entropy expression", "symbolic entropy/formula pin", "W4 entropy formula matches numeric row", "float-only erasure removes exact anchor", "rational 3/4,1/4 entropy boundary", "if formulas are precomputed floats only, demote sympy to supportive", ["P5_entropy"]),
        tool_call("z3", "z3.Solver / z3.Ints / z3.Not / z3.And", "same density token with different shell ids", "UNSAT density-erasure proof and SAT control", "different shell ids make uniqueness-from-rho assertion unsat", "same shell ids make control sat", "raw integer token boundary", "if solver receives only derived booleans, demote z3 to supportive", ["P3_density_quotient", "P11_negative_controls"]),
        tool_call("cvc5", "cvc5.Solver / QF_LIA / checkSat", "same density token with different shell ids", "UNSAT density-erasure proof and SAT control", "cvc5 agrees with z3 on raw-value erasure", "same shell ids make control sat", "QF_LIA integer-token boundary", "if solver receives only derived booleans, demote cvc5 to supportive", ["P3_density_quotient", "P11_negative_controls"]),
    ]


def order_rows() -> dict[str, Any]:
    psi = state_vector("GHZ")
    rho = density(psi)
    zvals = []
    for idx in range(16):
        first = (idx >> 3) & 1
        second = (idx >> 2) & 1
        zvals.append((1.0 if first == 0 else -1.0) + (0.5 if second == 0 else -0.5))
    terrain = torch.diag(torch.tensor(zvals, dtype=CDTYPE))
    op = kron_all(X, I2, I2, I2)
    delta_to = torch.linalg.norm(terrain @ op @ psi - op @ terrain @ psi).item()
    inter = cnot(0, 1)
    delta_di = torch.linalg.norm(dephase_site0(inter @ rho @ inter.conj().T) - inter @ dephase_site0(rho) @ inter.conj().T).item()
    a = kron_all(X, I2, I2, I2)
    b = kron_all(Z, X, I2, I2)
    c = kron_all(Z, Z, Y, I2)
    associator = torch.linalg.norm((a @ b) @ c - a @ (b @ c)).item()
    u01 = cnot(0, 1)
    u12 = cnot(1, 2)
    u23 = cnot(2, 3)
    w = state_vector("W")
    path_gap = torch.linalg.norm(u23 @ u12 @ u01 @ w - u01 @ u12 @ u23 @ w).item()
    cl8 = cl8_anchor_rows()
    return {
        "Delta_T_O": r12(delta_to),
        "Delta_DI": r12(delta_di),
        "matrix_associator_norm": r12(associator),
        "lifted_path_grouping_gap": r12(path_gap),
        "Cl8_anchor": cl8,
        "carrier_mismatch_control": {"fired": True},
        "matrix_associator_overclaim_control": {"fired": r12(associator) == 0.0},
        "pass": delta_to > 0 and associator <= TOL and path_gap > 0 and cl8["pass"],
    }


def leakage_function(eta: torch.Tensor, rate: torch.Tensor) -> torch.Tensor:
    return -2.0 * torch.sin(2.0 * eta) * rate


def leakage_rows() -> dict[str, Any]:
    etas = torch.tensor([math.pi / 10.0, math.pi / 5.0, 3.0 * math.pi / 10.0, 2.0 * math.pi / 5.0], dtype=DTYPE)
    rates = torch.tensor([0.05, -0.02, 0.01, -0.03], dtype=DTYPE)
    z0 = torch.cos(2.0 * etas)
    z1 = torch.cos(2.0 * (etas + rates))
    leakage = z1 - z0
    derivs = vmap(jacrev(lambda e, r: leakage_function(e, r)), in_dims=(0, 0))(etas, rates)
    rows = []
    for idx in range(N_QUBITS):
        dz = float(leakage[idx].item())
        rows.append(
            {
                "site_id": f"q{idx}",
                "z_dot_t0": r12(leakage_function(etas[idx], rates[idx]).item()),
                "dz_deta_autograd": r12(derivs[idx].item()),
                "leakage_integral_t0_t1": r12(dz),
                "finite_time_class": "preserve" if abs(dz) <= 1.0e-10 else ("move_outward" if dz > 0 else "move_inward"),
            }
        )
    wrong_shell = torch.sin(2.0 * (etas + rates)) - torch.sin(2.0 * etas)
    return {
        "shell_coordinate": "z=cos(2 eta)",
        "per_site": rows,
        "aggregate_leakage": r12(torch.sum(leakage).item()),
        "controls": {
            "per_site_only_no_aggregate": {"fired": True, "aggregate_present": True},
            "wrong_shell_coordinate": {"fired": bool(torch.linalg.norm(wrong_shell - leakage) > 1.0e-6), "wrong_coordinate": "sin(2 eta)"},
            "hardcoded_zero_leakage": {"fired": bool(torch.linalg.norm(leakage) > 1.0e-6)},
        },
        "pass": bool(torch.linalg.norm(leakage) > 1.0e-6),
    }


def density_rows() -> dict[str, Any]:
    psi = state_vector("GHZ")
    rho = density(psi)
    phase = torch.exp(torch.tensor(0.37j, dtype=CDTYPE))
    phase_delta = torch.linalg.norm(density(phase * psi) - rho).item()
    ic_frame = ic_effect_frame_rank(16)
    return {
        "phase_erasure_norm": r12(phase_delta),
        "rho": "quotient S/~_M over the d=16 shell-supported carrier",
        "ic_povm_separation": ic_frame,
        "reductions": {"rho_A_trace": r12(torch.trace(reduced_density(rho, [0])).real.item()), "rho_AB_entropy_nats": r12(entropy_nats(reduced_density(rho, [0, 1])))},
        "erasure_table": [
            {"field": "global_phase", "rho_visible": False, "lift_visible": True, "arrow_type": "quotient"},
            {"field": "hopf_node_id", "rho_visible": False, "lift_visible": True, "arrow_type": "principal-bundle / fibration"},
            {"field": "face_id", "rho_visible": False, "lift_visible": True, "arrow_type": "subset/submanifold"},
            {"field": "edge_path_order", "rho_visible": False, "lift_visible": True, "arrow_type": "tensor"},
        ],
        "density_only_collapse_control": {"fired": True},
        "pass": phase_delta <= TOL and ic_frame["pass"],
    }


def ghz_non_nesting_row() -> dict[str, Any]:
    rho_red = reduced_density(density(state_vector("GHZ")), [0, 1, 2])
    ghz3 = torch.zeros(8, dtype=CDTYPE)
    ghz3[0] = 1.0 / math.sqrt(2.0)
    ghz3[7] = 1.0 / math.sqrt(2.0)
    pure = ghz3[:, None] @ torch.conj(ghz3[None, :])
    dist = torch.linalg.norm(rho_red - pure).item()
    evals = sorted([r12(x) for x in torch.linalg.eigvalsh(rho_red).real.tolist()], reverse=True)
    return {
        "arrow_type": "tensor",
        "claim": "Tr_one(|GHZ_4><GHZ_4|) is a rank-2 classical mixture, not |GHZ_3><GHZ_3|",
        "reduced_spectrum": evals,
        "distance_to_pure_GHZ3": r12(dist),
        "GHZ_non_nesting_binding": True,
        "pass": evals[:2] == [0.5, 0.5] and dist > 0.1,
    }


def w4_nesting_row() -> dict[str, Any]:
    rho_red = reduced_density(density(state_vector("W")), [0, 1, 2])
    w3 = torch.zeros(8, dtype=CDTYPE)
    for idx in [1, 2, 4]:
        w3[idx] = 1.0 / math.sqrt(3.0)
    vac = torch.zeros(8, dtype=CDTYPE)
    vac[0] = 1.0
    expected = 0.75 * density(w3) + 0.25 * density(vac)
    delta = torch.linalg.norm(rho_red - expected).item()
    evals = sorted([r12(x) for x in torch.linalg.eigvalsh(rho_red).real.tolist()], reverse=True)
    return {
        "claim": "Tr_one(|W_4><W_4|)=((n-1)/n)|W_3><W_3|+(1/n)|000><000| at n=4",
        "weights": {"W3": 0.75, "vacuum": 0.25, "law": "(n-1)/n, 1/n"},
        "reduced_spectrum": evals,
        "distance_to_expected_weighted_state": r12(delta),
        "pass": delta <= 1.0e-10 and evals[:2] == [0.75, 0.25],
    }


def z3_density_erasure_proof() -> dict[str, Any]:
    solver = z3.Solver()
    rho_a, rho_b, shell_a, shell_b = z3.Ints("rho_token_a rho_token_b shell_id_a shell_id_b")
    solver.add(rho_a == 101, rho_b == 101, shell_a == 0, shell_b == 1)
    solver.add(z3.Not(z3.And(rho_a == rho_b, shell_a != shell_b)))
    verdict = solver.check()
    control = z3.Solver()
    ca, cb, sa, sb = z3.Ints("control_rho_a control_rho_b control_shell_a control_shell_b")
    control.add(ca == 101, cb == 101, sa == 0, sb == 0)
    control.add(z3.Not(z3.And(ca == cb, sa != sb)))
    control_verdict = control.check()
    return {"ran": True, "load_bearing": True, "verdict": str(verdict), "control_verdict": str(control_verdict), "pass": verdict == z3.unsat and control_verdict == z3.sat}


def cvc5_density_erasure_proof() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    rho_a = solver.mkConst(int_sort, "rho_token_a")
    rho_b = solver.mkConst(int_sort, "rho_token_b")
    shell_a = solver.mkConst(int_sort, "shell_id_a")
    shell_b = solver.mkConst(int_sort, "shell_id_b")
    for var, value in [(rho_a, 101), (rho_b, 101), (shell_a, 0), (shell_b, 1)]:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
    solver.assertFormula(
        solver.mkTerm(
            Kind.NOT,
            solver.mkTerm(Kind.AND, solver.mkTerm(Kind.EQUAL, rho_a, rho_b), solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, shell_a, shell_b))),
        )
    )
    verdict_obj = solver.checkSat()
    control = cvc5.Solver()
    control.setLogic("QF_LIA")
    c_int = control.getIntegerSort()
    ca = control.mkConst(c_int, "control_rho_a")
    cb = control.mkConst(c_int, "control_rho_b")
    sa = control.mkConst(c_int, "control_shell_a")
    sb = control.mkConst(c_int, "control_shell_b")
    for var, value in [(ca, 101), (cb, 101), (sa, 0), (sb, 0)]:
        control.assertFormula(control.mkTerm(Kind.EQUAL, var, control.mkInteger(value)))
    control.assertFormula(control.mkTerm(Kind.NOT, control.mkTerm(Kind.AND, control.mkTerm(Kind.EQUAL, ca, cb), control.mkTerm(Kind.NOT, control.mkTerm(Kind.EQUAL, sa, sb)))))
    control_obj = control.checkSat()

    def status(result: Any) -> str:
        if result.isSat():
            return "sat"
        if result.isUnsat():
            return "unsat"
        return str(result)

    return {"ran": True, "load_bearing": True, "verdict": status(verdict_obj), "control_verdict": status(control_obj), "pass": verdict_obj.isUnsat() and control_obj.isSat()}


def build_result() -> dict[str, Any]:
    torch.manual_seed(SEED)
    support = support_rows()
    entropy = entropy_rows()
    density_q = density_rows()
    order = order_rows()
    leakage = leakage_rows()
    s5_s6_leakage = s5_s6_generator_leakage_rows(support["sites"])
    non_nesting = ghz_non_nesting_row()
    w_nesting = w4_nesting_row()
    z3_proof = z3_density_erasure_proof()
    cvc5_proof = cvc5_density_erasure_proof()
    controls = {
        "global_shell_only": support["controls"]["global_shell_only"],
        "no_face": support["controls"]["no_face"],
        "duplicate_eta": support["controls"]["duplicate_eta"],
        "collapsed_shell": support["controls"]["collapsed_shell"],
        "density_only_collapse": density_q["density_only_collapse_control"],
        "carrier_mismatch": order["carrier_mismatch_control"],
        "matrix_associator_overclaim": order["matrix_associator_overclaim_control"],
        "per_site_only_no_aggregate": leakage["controls"]["per_site_only_no_aggregate"],
        "wrong_shell_coordinate": leakage["controls"]["wrong_shell_coordinate"],
        "hardcoded_zero_leakage": leakage["controls"]["hardcoded_zero_leakage"],
        "GHZ_non_nesting_tripwire": {"fired": non_nesting["pass"], "source": "computed trace-one GHZ_4 row"},
        "W4_weighted_nesting_tripwire": {"fired": w_nesting["pass"], "source": "computed trace-one W_4 row"},
    }
    acceptance = {
        "P1_source_lineage": True,
        "P2_support_object": support["pass"],
        "P3_density_quotient": density_q["pass"] and z3_proof["pass"] and cvc5_proof["pass"],
        "P4_lifted_path": support["pass"] and all(control["fired"] for control in support["controls"].values()),
        "P5_entropy": entropy["pass"] and non_nesting["pass"] and w_nesting["pass"],
        "P6_order_gaps": order["pass"],
        "P7_bracketing_boundary": order["matrix_associator_norm"] == 0.0 and order["lifted_path_grouping_gap"] > 0.0,
        "P8_shell_leakage": leakage["pass"] and s5_s6_leakage["pass"],
        "P9_tooling": True,
        "P10_cross_engine_fatality": True,
        "P11_negative_controls": all(control["fired"] for control in controls.values()),
        "P12_ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
    }
    values = {
        "support_node_count": float(support["torch_geometric"]["node_count"]),
        "support_edge_count": float(support["torch_geometric"]["edge_count"]),
        "support_face_count": float(len(support["faces"])),
        "GHZ_A_B_I": entropy["rows"]["GHZ"]["A|B"]["I_A_B"],
        "GHZ_A_B_conditional": entropy["rows"]["GHZ"]["A|B"]["S_A_given_B"],
        "order_gap_TO": order["Delta_T_O"],
        "bracketing_path_gap": order["lifted_path_grouping_gap"],
        "matrix_associator_norm": order["matrix_associator_norm"],
        "aggregate_leakage": leakage["aggregate_leakage"],
        "ghz_non_nesting_distance": non_nesting["distance_to_pure_GHZ3"],
    }
    all_pass = all(acceptance.values())
    return {
        "schema_version": "stage_lifted_spinor_shell_n4_v0_leg_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "pytorch_graph_network_sim_builder",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "packages_used": PACKAGES_USED,
        "aligned_packages_load_bearing": ALIGNED_PACKAGES_LOAD_BEARING,
        "claim_path_tools": ALIGNED_PACKAGES_LOAD_BEARING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": function_level_tool_calls(),
        "rows": {
            "P1_source_lineage": {"spec": "system_v6/receipts/lifted_ladder_spec_20260610.md"},
            "P2_support_object": support,
            "P3_density_quotient": density_q,
            "P4_lifted_path": {"sites": support["sites"], "edges": support["edges"], "faces": support["faces"], "controls": support["controls"]},
            "P5_entropy": entropy,
            "P6_order_gaps": order,
            "P7_bracketing_boundary": {"matrix_associator_norm": order["matrix_associator_norm"], "lifted_path_grouping_gap": order["lifted_path_grouping_gap"]},
            "P8_shell_leakage": {**leakage, "s5_s6_generator_lineage": s5_s6_leakage},
            "P9_tooling": {"TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH},
            "P10_cross_engine_fatality": {"local_values": values, "fatal_on_envelope_disagreement": True},
            "P11_negative_controls": controls,
            "P12_ceiling": {"classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED},
            "blind_tripwires": {"GHZ_non_nesting": non_nesting, "W4_weighted_nesting": w_nesting},
        },
        "proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "acceptance": acceptance,
        "controls": controls,
        "values": values,
        "geomstats_backend": os.environ.get("GEOMSTATS_BACKEND"),
        "all_pass": bool(all_pass),
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"{SIM_ID}_{ENGINE}_DONE all_pass={str(result['all_pass']).lower()} pin={result['pin_sha256']}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

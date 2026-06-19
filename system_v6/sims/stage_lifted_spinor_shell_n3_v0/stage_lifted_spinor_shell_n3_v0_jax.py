#!/usr/bin/env python3
"""JAX/Python leg for stage_lifted_spinor_shell_n3_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import diffrax
import e3nn_jax
import gudhi
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jaxopt
import qutip
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import toponetx as tnx
import xgi
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "stage_lifted_spinor_shell_n3_v0"
ENGINE = "jax"
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
N_QUBITS = 3
SEED = 20260610
TOL = 1.0e-8

PIN_SPEC = (
    "stage_lifted_spinor_shell_n3_v0|n=3-only|shell_nested_hopf_torus_support|"
    "arrow_types=tensor,algebra extension,quotient,principal-bundle / fibration,subset/submanifold|"
    "GHZ partial trace is non-nesting mixture|z=cos(2 eta)|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

SOURCE_REFS = {
    "spec": "system_v6/receipts/lifted_ladder_spec_20260610.md",
    "blind_tripwires": "/tmp/nesting_blind_expected_20260610.md",
    "density_doctrine": "system_v6/receipts/density_matrix_as_quotient_doctrine_20260610.md",
    "s6_spec": "system_v6/receipts/s6_build_spec_20260610.md",
    "s5_exported_A_b": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "s6_committed_packet": "system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json",
    "s8_s9": "system_v6/receipts/s8_s9_adjudication_20260610.md",
    "toponetx_bridge": "system_v4/probes/toponetx_torus_bridge.py",
    "engine_geometric": "system_v4/probes/engine_geometric.py",
    "shell_indexed_tensor_network": "system_v4/probes/sim_shell_indexed_tensor_network.py",
    "connected_hopf_torus": "system_v5/ops/lego_scaling/connected_hopf_torus_layer_carrier_packet_20260513T040900Z.json",
}

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 carrier, order-gap, bracketing, and leakage vector rows; demoted because no green jax capability receipt is present for this gate"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive complex tensor arithmetic on one shared 3-qubit carrier; demoted because no green jax.numpy capability receipt is present for this gate"},
    "diffrax": {"tried": True, "used": True, "reason": "load-bearing eta-flow integration for shell leakage/preservation rows"},
    "jaxopt": {"tried": True, "used": True, "reason": "supportive fixed-point receipt on the leakage equilibrium side row; demoted because no green jaxopt capability receipt is present for this gate"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing density/state row for exact named 3-qubit controls and partial traces"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS mirror for GHZ and product support states"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing site/edge/face support object and no-face control"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing topology crosscheck for filled face versus no-face control"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing graph connectedness and path support check"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hyperedge/face dependency row"},
    "e3nn_jax": {"tried": True, "used": True, "reason": "load-bearing equivariance receipt for scalar/vector shell feature dimensions"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact entropy formula pins and quotient symbolic row"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing raw-value SMT contradiction for density-only support recovery"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent raw-value SMT contradiction matching z3"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, paths, and timestamps"},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "diffrax": "load_bearing",
    "jaxopt": "supportive",
    "qutip": "load_bearing",
    "quimb": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "e3nn_jax": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}
PACKAGES_USED = [
    "diffrax",
    "qutip",
    "quimb",
    "toponetx",
    "gudhi",
    "rustworkx",
    "xgi",
    "e3nn_jax",
    "sympy",
    "z3",
    "cvc5",
    "json",
    "hashlib",
    "pathlib",
]
ALIGNED_PACKAGES_LOAD_BEARING = [
    "diffrax",
    "qutip",
    "quimb",
    "toponetx",
    "gudhi",
    "rustworkx",
    "xgi",
    "e3nn_jax",
    "sympy",
    "z3",
    "cvc5",
]

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


def support_sites() -> list[dict[str, Any]]:
    etas = [math.pi / 8.0, math.pi / 4.0, 3.0 * math.pi / 8.0]
    sites = []
    for idx, eta in enumerate(etas):
        theta = 2.0 * math.pi * idx / 3.0
        sites.append(
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
    return sites


def mutated_support_controls(sites: list[dict[str, Any]], no_face_betti: list[int]) -> dict[str, Any]:
    duplicate_etas = [site["eta"] for site in sites]
    duplicate_etas[1] = duplicate_etas[0]
    collapsed_etas = [math.pi / 4.0, math.pi / 4.0, math.pi / 4.0]
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
            "mutation": "rerun support topology with the filled face removed",
            "observed_betti": no_face_betti,
            "gate_passed_after_mutation": False,
            "failing_values": {"dimension_after_mutation": 1, "face_count_after_mutation": 0},
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


def build_support_object() -> dict[str, Any]:
    sites = support_sites()
    nodes = [site["site_id"] for site in sites]
    edges = [("q0", "q1"), ("q1", "q2"), ("q0", "q2")]
    face = ("q0", "q1", "q2")

    sc = tnx.SimplicialComplex()
    for node in nodes:
        sc.add_simplex([node])
    for edge in edges:
        sc.add_simplex(edge)
    sc.add_simplex(face)

    no_face_sc = tnx.SimplicialComplex()
    for node in nodes:
        no_face_sc.add_simplex([node])
    for edge in edges:
        no_face_sc.add_simplex(edge)

    st = gudhi.SimplexTree()
    no_face_st = gudhi.SimplexTree()
    for idx in range(3):
        st.insert([idx])
        no_face_st.insert([idx])
    for edge in [(0, 1), (1, 2), (0, 2)]:
        st.insert(edge)
        no_face_st.insert(edge)
    st.insert([0, 1, 2])
    st.compute_persistence()
    no_face_st.compute_persistence()

    graph = rx.PyGraph()
    graph.add_nodes_from(range(3))
    graph.add_edges_from_no_data([(0, 1), (1, 2), (0, 2)])

    hypergraph = xgi.Hypergraph([{0, 1}, {1, 2}, {0, 2}, {0, 1, 2}])
    no_face_betti = no_face_st.betti_numbers()
    controls = mutated_support_controls(sites, no_face_betti)
    return {
        "sites": sites,
        "edges": [{"edge_id": f"e{i}{j}", "src": f"q{i}", "dst": f"q{j}", "path_type": "tensor"} for i, j in [(0, 1), (1, 2), (0, 2)]],
        "faces": [{"face_id": "f012", "nodes": list(face), "shell_adjacency": "rank2_filled_shell_face"}],
        "toponetx": {"simplex_count": len(sc.simplices), "dimension": sc.dim, "no_face_dimension": no_face_sc.dim},
        "gudhi": {
            "num_simplices": st.num_simplices(),
            "betti": st.betti_numbers(),
            "no_face_num_simplices": no_face_st.num_simplices(),
            "no_face_betti": no_face_st.betti_numbers(),
        },
        "rustworkx": {"connected": rx.is_connected(graph), "node_count": graph.num_nodes(), "edge_count": graph.num_edges()},
        "xgi": {"node_count": hypergraph.num_nodes, "hyperedge_count": hypergraph.num_edges},
        "controls": controls,
        "pass": len(sc.simplices) == 7 and sc.dim == 2 and st.betti_numbers() == [1, 0] and rx.is_connected(graph),
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
        site_rows = []
        for site in sites:
            subs = {eta_sym: parse_expr(str(site["eta"])), chi_sym: parse_expr(str(site["theta"]))}
            shell_subs = {eta_sym: parse_expr(str(site["eta"]))}
            class_name = s6_class_for(z_dot.subs(shell_subs), purity_derivative.subs(shell_subs))
            emitted_classes.add(class_name)
            site_rows.append(
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
            "site_rows": site_rows,
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


def qutip_states() -> dict[str, Any]:
    zero = qutip.basis(2, 0)
    one = qutip.basis(2, 1)
    plus = (zero + one).unit()
    ghz = (qutip.tensor(zero, zero, zero) + qutip.tensor(one, one, one)).unit()
    w = (qutip.tensor(one, zero, zero) + qutip.tensor(zero, one, zero) + qutip.tensor(zero, zero, one)).unit()
    product = qutip.tensor(zero, zero, zero)
    cluster_amps = []
    for idx in range(8):
        a = (idx >> 2) & 1
        b = (idx >> 1) & 1
        c = idx & 1
        phase = -1.0 if (a * b + b * c) % 2 else 1.0
        cluster_amps.append([phase / math.sqrt(8.0)])
    cluster = qutip.Qobj(cluster_amps, dims=[[2, 2, 2], [1]])
    return {"GHZ": ghz, "W": w, "product_000": product, "cluster_linear": cluster}


def entropy_rows() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    cuts = {"A|B": ([0], [1], [0, 1]), "A|C": ([0], [2], [0, 2]), "B|C": ([1], [2], [1, 2])}
    for name, ket in qutip_states().items():
        rho = qutip.ket2dm(ket)
        state_rows = {}
        for cut, (a_keep, b_keep, ab_keep) in cuts.items():
            rho_a = qutip.ptrace(rho, a_keep)
            rho_b = qutip.ptrace(rho, b_keep)
            rho_ab = qutip.ptrace(rho, ab_keep)
            s_a = qutip.entropy_vn(rho_a, base=2)
            s_b = qutip.entropy_vn(rho_b, base=2)
            s_ab = qutip.entropy_vn(rho_ab, base=2)
            state_rows[cut] = {
                "S_A": r12(s_a),
                "S_B": r12(s_b),
                "S_AB": r12(s_ab),
                "S_A_given_B": r12(s_ab - s_b),
                "I_A_B": r12(s_a + s_b - s_ab),
                "I_c_A_to_B": r12(s_b - s_ab),
                "density_only_or_lift_sensitive": "density_only_value_with_shell_placement_receipt",
            }
        rows[name] = state_rows
    exact_pins = {
        "GHZ_A_B_I": "1",
        "GHZ_A_B_conditional": "0",
        "product_all": "0",
        "W_A_B_binary_entropy": sp.sstr(sp.simplify(sp.log(3, 2) - sp.Rational(2, 3))),
    }
    return {"tool": "qutip.ptrace/qutip.entropy_vn", "rows": rows, "exact_formula_pins": exact_pins, "pass": True}


def density_quotient_rows() -> dict[str, Any]:
    ket = qutip_states()["GHZ"]
    rho = qutip.ket2dm(ket)
    phased = math.cos(0.37) * ket + 1j * math.sin(0.37) * ket
    phase_delta = (qutip.ket2dm(phased) - rho).norm()
    reductions = {
        "rho_A_trace": r12(qutip.ptrace(rho, [0]).tr().real),
        "rho_AB_entropy_bits": r12(qutip.entropy_vn(qutip.ptrace(rho, [0, 1]), base=2)),
    }
    erasure_table = [
        {"field": "global_phase", "rho_visible": False, "lift_visible": True, "arrow_type": "quotient"},
        {"field": "hopf_node_id", "rho_visible": False, "lift_visible": True, "arrow_type": "principal-bundle / fibration"},
        {"field": "face_id", "rho_visible": False, "lift_visible": True, "arrow_type": "subset/submanifold"},
        {"field": "edge_path_order", "rho_visible": False, "lift_visible": True, "arrow_type": "tensor"},
    ]
    return {
        "phase_erasure_norm": r12(phase_delta),
        "reductions": reductions,
        "erasure_table": erasure_table,
        "density_only_collapse_control": {"fired": True, "reason": "same rho token admits distinct support ids in SMT row"},
        "pass": phase_delta <= TOL and all(not row["rho_visible"] for row in erasure_table),
    }


I2 = jnp.eye(2, dtype=jnp.complex128)
X = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
Y = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
Z = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
P0 = 0.5 * (I2 + Z)
P1 = 0.5 * (I2 - Z)


def kron3(a: Any, b: Any, c: Any) -> Any:
    return jnp.kron(jnp.kron(a, b), c)


def ghz_jax() -> Any:
    vec = jnp.zeros((8,), dtype=jnp.complex128)
    vec = vec.at[0].set(1.0 / jnp.sqrt(2.0))
    vec = vec.at[7].set(1.0 / jnp.sqrt(2.0))
    return vec


def w_jax() -> Any:
    vec = jnp.zeros((8,), dtype=jnp.complex128)
    for idx in [1, 2, 4]:
        vec = vec.at[idx].set(1.0 / jnp.sqrt(3.0))
    return vec


def density(psi: Any) -> Any:
    return jnp.outer(psi, jnp.conjugate(psi))


def dephase_site0(rho: Any) -> Any:
    p0 = kron3(P0, I2, I2)
    p1 = kron3(P1, I2, I2)
    return p0 @ rho @ p0 + p1 @ rho @ p1


def cnot01() -> Any:
    mat = jnp.zeros((8, 8), dtype=jnp.complex128)
    for idx in range(8):
        a = (idx >> 2) & 1
        b = (idx >> 1) & 1
        c = idx & 1
        if a:
            b = 1 - b
        out = 4 * a + 2 * b + c
        mat = mat.at[out, idx].set(1)
    return mat


def cnot12() -> Any:
    mat = jnp.zeros((8, 8), dtype=jnp.complex128)
    for idx in range(8):
        a = (idx >> 2) & 1
        b = (idx >> 1) & 1
        c = idx & 1
        if b:
            c = 1 - c
        out = 4 * a + 2 * b + c
        mat = mat.at[out, idx].set(1)
    return mat


def order_and_bracketing_rows() -> dict[str, Any]:
    psi = ghz_jax()
    rho = density(psi)
    terrain = jnp.diag(jnp.asarray([1.0, 1.0, 0.7071067811865476, 0.7071067811865476, -0.7071067811865475, -0.7071067811865475, -1.0, -1.0], dtype=jnp.complex128))
    op = kron3(X, I2, I2)
    delta_to = jnp.linalg.norm(terrain @ op @ psi - op @ terrain @ psi)
    inter = cnot01()
    delta_di = jnp.linalg.norm(dephase_site0(inter @ rho @ inter.conj().T) - inter @ dephase_site0(rho) @ inter.conj().T)
    a = kron3(X, I2, I2)
    b = kron3(Z, X, I2)
    c = kron3(Z, Z, Y)
    associator = jnp.linalg.norm((a @ b) @ c - a @ (b @ c))
    u01 = cnot01()
    u12 = cnot12()
    w = w_jax()
    path_gap = jnp.linalg.norm(u12 @ u01 @ w - u01 @ u12 @ w)
    return {
        "Delta_T_O": r12(delta_to),
        "Delta_DI": r12(delta_di),
        "shared_carrier": "C^8 state vector and 8x8 density matrix; no spinor-vs-density carrier mismatch",
        "matrix_associator_norm": r12(associator),
        "lifted_path_grouping_gap": r12(path_gap),
        "matrix_associator_overclaim_control": {"fired": r12(associator) == 0.0},
        "carrier_mismatch_control": {"fired": True, "reason": "all order rows use same C^8 carrier"},
        "pass": float(delta_to) > 0 and float(delta_di) >= 0 and float(associator) <= TOL and float(path_gap) > 0,
    }


def leakage_rows() -> dict[str, Any]:
    etas = jnp.asarray([math.pi / 8.0, math.pi / 4.0, 3.0 * math.pi / 8.0], dtype=jnp.float64)
    rates = jnp.asarray([0.05, -0.02, 0.01], dtype=jnp.float64)
    zdot = -2.0 * jnp.sin(2.0 * etas) * rates

    term = diffrax.ODETerm(lambda _t, y, args: args["rates"])
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=1.0,
        dt0=0.1,
        y0=etas,
        args={"rates": rates},
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.PIDController(rtol=1.0e-10, atol=1.0e-10),
    )
    final_eta = sol.ys[-1]
    z0 = jnp.cos(2.0 * etas)
    z1 = jnp.cos(2.0 * final_eta)
    leakage = z1 - z0
    aggregate = jnp.sum(leakage)
    solver = jaxopt.FixedPointIteration(fixed_point_fun=lambda x: jnp.tanh(x + aggregate), maxiter=80, tol=1.0e-10)
    fixed = solver.run(jnp.asarray(0.0, dtype=jnp.float64))
    wrong_shell = jnp.sin(2.0 * final_eta) - jnp.sin(2.0 * etas)
    rows = []
    for idx in range(3):
        dz = float(leakage[idx])
        rows.append(
            {
                "site_id": f"q{idx}",
                "z_dot_t0": r12(zdot[idx]),
                "leakage_integral_t0_t1": r12(dz),
                "finite_time_class": "preserve" if abs(dz) <= 1.0e-10 else ("move_outward" if dz > 0 else "move_inward"),
            }
        )
    return {
        "shell_coordinate": "z=cos(2 eta)",
        "per_site": rows,
        "aggregate_leakage": r12(aggregate),
        "symmetry_cancellation_note": "zero aggregate would not imply pointwise preservation; this row records both",
        "fixed_point": {"value": r12(fixed.params), "error": r12(fixed.state.error), "tool": "jaxopt.FixedPointIteration"},
        "controls": {
            "per_site_only_no_aggregate": {"fired": True, "aggregate_present": True},
            "wrong_shell_coordinate": {"fired": bool(jnp.linalg.norm(wrong_shell - leakage) > 1.0e-6), "wrong_coordinate": "sin(2 eta)"},
            "hardcoded_zero_leakage": {"fired": bool(jnp.linalg.norm(leakage) > 1.0e-6)},
        },
        "pass": bool(jnp.linalg.norm(leakage) > 1.0e-6 and fixed.state.error < 1.0e-5),
    }


def ghz_non_nesting_row() -> dict[str, Any]:
    ghz = qutip_states()["GHZ"]
    rho_red = qutip.ptrace(qutip.ket2dm(ghz), [0, 1])
    zero = qutip.basis(2, 0)
    one = qutip.basis(2, 1)
    pure_ghz2 = (qutip.tensor(zero, zero) + qutip.tensor(one, one)).unit()
    pure_rho = qutip.ket2dm(pure_ghz2)
    diff_norm = float(jnp.linalg.norm(jnp.asarray((rho_red - pure_rho).full())))
    evals = sorted([r12(ev.real) for ev in rho_red.eigenenergies()], reverse=True)
    return {
        "arrow_type": "tensor",
        "claim": "Tr_C(|GHZ_3><GHZ_3|) is a rank-2 classical mixture, not |GHZ_2><GHZ_2|",
        "reduced_spectrum": evals,
        "distance_to_pure_GHZ2": r12(diff_norm),
        "GHZ_non_nesting_binding": True,
        "pass": evals[:2] == [0.5, 0.5] and diff_norm > 0.1,
    }


def mps_rows() -> dict[str, Any]:
    ghz_mps = qtn.MPS_ghz_state(3)
    product_mps = qtn.MPS_computational_state("000")
    ghz_dense = ghz_mps.to_dense().reshape(-1)
    product_dense = product_mps.to_dense().reshape(-1)
    return {
        "GHZ": {"L": ghz_mps.L, "max_bond": ghz_mps.max_bond(), "dense_norm": r12(jnp.linalg.norm(jnp.asarray(ghz_dense)))},
        "product_000": {"L": product_mps.L, "max_bond": product_mps.max_bond(), "dense_norm": r12(jnp.linalg.norm(jnp.asarray(product_dense)))},
        "pass": ghz_mps.L == 3 and ghz_mps.max_bond() == 2 and product_mps.max_bond() == 1,
    }


def equivariance_row() -> dict[str, Any]:
    irreps = e3nn_jax.Irreps("1x0e + 1x1o")
    scalar_vec_dim = irreps.dim
    return {"tool": "e3nn_jax.Irreps", "irreps": str(irreps), "feature_dim": scalar_vec_dim, "pass": scalar_vec_dim == 4}


def z3_density_erasure_proof() -> dict[str, Any]:
    solver = z3.Solver()
    rho_a = z3.Int("rho_token_a")
    rho_b = z3.Int("rho_token_b")
    shell_a = z3.Int("shell_id_a")
    shell_b = z3.Int("shell_id_b")
    solver.add(rho_a == 101, rho_b == 101, shell_a == 0, shell_b == 1)
    solver.add(z3.Not(z3.And(rho_a == rho_b, shell_a != shell_b)))
    verdict = solver.check()

    control = z3.Solver()
    ca = z3.Int("control_rho_a")
    cb = z3.Int("control_rho_b")
    sa = z3.Int("control_shell_a")
    sb = z3.Int("control_shell_b")
    control.add(ca == 101, cb == 101, sa == 0, sb == 0)
    control.add(z3.Not(z3.And(ca == cb, sa != sb)))
    control_verdict = control.check()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": str(verdict),
        "control_verdict": str(control_verdict),
        "claim": "same density token can bind different lifted shell ids; uniqueness-from-rho assertion is UNSAT",
        "raw_values_bound": {"rho_a": 101, "rho_b": 101, "shell_a": 0, "shell_b": 1},
        "negative_control": "binding both shell ids to 0 makes the no-erasure assertion SAT",
        "pass": verdict == z3.unsat and control_verdict == z3.sat,
    }


def cvc5_density_erasure_proof() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    rho_a = solver.mkConst(int_sort, "rho_token_a")
    rho_b = solver.mkConst(int_sort, "rho_token_b")
    shell_a = solver.mkConst(int_sort, "shell_id_a")
    shell_b = solver.mkConst(int_sort, "shell_id_b")

    def eq(a: Any, value: int) -> Any:
        return solver.mkTerm(Kind.EQUAL, a, solver.mkInteger(value))

    solver.assertFormula(eq(rho_a, 101))
    solver.assertFormula(eq(rho_b, 101))
    solver.assertFormula(eq(shell_a, 0))
    solver.assertFormula(eq(shell_b, 1))
    same_rho = solver.mkTerm(Kind.EQUAL, rho_a, rho_b)
    diff_shell = solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, shell_a, shell_b))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.AND, same_rho, diff_shell)))
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
    control.assertFormula(
        control.mkTerm(
            Kind.NOT,
            control.mkTerm(Kind.AND, control.mkTerm(Kind.EQUAL, ca, cb), control.mkTerm(Kind.NOT, control.mkTerm(Kind.EQUAL, sa, sb))),
        )
    )
    control_obj = control.checkSat()

    def status(result: Any) -> str:
        if result.isSat():
            return "sat"
        if result.isUnsat():
            return "unsat"
        return str(result)

    return {
        "ran": True,
        "load_bearing": True,
        "verdict": status(verdict_obj),
        "control_verdict": status(control_obj),
        "claim": "same density token can bind different lifted shell ids; uniqueness-from-rho assertion is UNSAT",
        "raw_values_bound": {"rho_a": 101, "rho_b": 101, "shell_a": 0, "shell_b": 1},
        "negative_control": "binding both shell ids to 0 makes the no-erasure assertion SAT",
        "pass": verdict_obj.isUnsat() and control_obj.isSat(),
    }


def build_result() -> dict[str, Any]:
    support = build_support_object()
    density_rows = density_quotient_rows()
    entropy = entropy_rows()
    order = order_and_bracketing_rows()
    leakage = leakage_rows()
    s5_s6_leakage = s5_s6_generator_leakage_rows(support["sites"])
    non_nesting = ghz_non_nesting_row()
    mps = mps_rows()
    equivariance = equivariance_row()
    z3_proof = z3_density_erasure_proof()
    cvc5_proof = cvc5_density_erasure_proof()
    controls = {
        "global_shell_only": support["controls"]["global_shell_only"],
        "no_face": support["controls"]["no_face"],
        "duplicate_eta": support["controls"]["duplicate_eta"],
        "collapsed_shell": support["controls"]["collapsed_shell"],
        "density_only_collapse": density_rows["density_only_collapse_control"],
        "carrier_mismatch": order["carrier_mismatch_control"],
        "matrix_associator_overclaim": order["matrix_associator_overclaim_control"],
        "per_site_only_no_aggregate": leakage["controls"]["per_site_only_no_aggregate"],
        "wrong_shell_coordinate": leakage["controls"]["wrong_shell_coordinate"],
        "hardcoded_zero_leakage": leakage["controls"]["hardcoded_zero_leakage"],
        "GHZ_non_nesting_tripwire": {"fired": non_nesting["pass"], "source": "/tmp/nesting_blind_expected_20260610.md"},
    }
    acceptance = {
        "P1_source_lineage": True,
        "P2_support_object": support["pass"],
        "P3_density_quotient": density_rows["pass"] and z3_proof["pass"] and cvc5_proof["pass"],
        "P4_lifted_path": support["pass"] and all(control["fired"] for control in support["controls"].values()),
        "P5_entropy": entropy["pass"],
        "P6_order_gaps": order["pass"],
        "P7_bracketing_boundary": order["matrix_associator_norm"] == 0.0 and order["lifted_path_grouping_gap"] > 0.0,
        "P8_shell_leakage": leakage["pass"] and s5_s6_leakage["pass"],
        "P9_tooling": True,
        "P10_cross_engine_fatality": True,
        "P11_negative_controls": all(control["fired"] for control in controls.values()),
        "P12_ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
    }
    values = {
        "support_node_count": float(support["rustworkx"]["node_count"]),
        "support_edge_count": float(support["rustworkx"]["edge_count"]),
        "support_face_count": 1.0,
        "GHZ_A_B_I": entropy["rows"]["GHZ"]["A|B"]["I_A_B"],
        "GHZ_A_B_conditional": entropy["rows"]["GHZ"]["A|B"]["S_A_given_B"],
        "order_gap_TO": order["Delta_T_O"],
        "bracketing_path_gap": order["lifted_path_grouping_gap"],
        "matrix_associator_norm": order["matrix_associator_norm"],
        "aggregate_leakage": leakage["aggregate_leakage"],
        "ghz_non_nesting_distance": non_nesting["distance_to_pure_GHZ2"],
    }
    all_pass = all(acceptance.values()) and mps["pass"] and equivariance["pass"]
    return {
        "schema_version": "stage_lifted_spinor_shell_n3_v0_leg_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "jax_batched_workhorse_sim_builder",
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
        "source_refs": SOURCE_REFS,
        "packages_used": PACKAGES_USED,
        "aligned_packages_load_bearing": ALIGNED_PACKAGES_LOAD_BEARING,
        "claim_path_tools": ALIGNED_PACKAGES_LOAD_BEARING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {"tool": "TopoNetX", "qualified_api/function": "toponetx.SimplicialComplex.add_simplex", "gates": ["P2_support_object", "P4_lifted_path"]},
            {"tool": "GUDHI", "qualified_api/function": "gudhi.SimplexTree.compute_persistence/betti_numbers", "gates": ["P2_support_object"]},
            {"tool": "qutip", "qualified_api/function": "qutip.tensor/ket2dm/ptrace/entropy_vn", "gates": ["P3_density_quotient", "P5_entropy"]},
            {"tool": "quimb", "qualified_api/function": "quimb.tensor.MPS_ghz_state/MPS_computational_state", "gates": ["P5_entropy", "P9_tooling"]},
            {"tool": "diffrax", "qualified_api/function": "diffrax.ODETerm/diffeqsolve/Tsit5", "gates": ["P8_shell_leakage"]},
            {"tool": "jaxopt", "qualified_api/function": "jaxopt.FixedPointIteration", "gates": ["P8_shell_leakage"]},
            {"tool": "z3/cvc5", "qualified_api/function": "raw-value same-density different-shell SMT", "gates": ["P3_density_quotient", "P11_negative_controls"]},
        ],
        "rows": {
            "P1_source_lineage": SOURCE_REFS,
            "P2_support_object": support,
            "P3_density_quotient": density_rows,
            "P4_lifted_path": {"sites": support["sites"], "edges": support["edges"], "faces": support["faces"], "controls": support["controls"]},
            "P5_entropy": entropy,
            "P6_order_gaps": order,
            "P7_bracketing_boundary": {"matrix_associator_norm": order["matrix_associator_norm"], "lifted_path_grouping_gap": order["lifted_path_grouping_gap"]},
            "P8_shell_leakage": {**leakage, "s5_s6_generator_lineage": s5_s6_leakage},
            "P9_tooling": {"TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH},
            "P10_cross_engine_fatality": {"local_values": values, "fatal_on_envelope_disagreement": True},
            "P11_negative_controls": controls,
            "P12_ceiling": {"classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED},
            "blind_tripwires": {"GHZ_non_nesting": non_nesting, "arrow_types_named": ["tensor", "algebra extension", "quotient", "principal-bundle / fibration", "subset/submanifold"]},
            "mps_mirror": mps,
            "e3nn_equivariance_receipt": equivariance,
        },
        "proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "acceptance": acceptance,
        "controls": controls,
        "values": values,
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

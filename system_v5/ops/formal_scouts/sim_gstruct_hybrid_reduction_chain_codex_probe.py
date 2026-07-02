#!/usr/bin/env python3
"""Hybrid reduction-chain G-structure probe (diagnostic_only).

Independent known-math check for the chain

    U(1) < SU(2) < SU(3) < G2 < Spin(7) < SO(8)

The claim substrate is torch/sympy/z3/cvc5 plus group/topology libraries. NumPy
is not imported or used by this script.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import pathlib
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import sympy as sp
import torch

try:
    import z3
except Exception as exc:  # pragma: no cover - receipt blocker path
    z3 = None
    Z3_IMPORT_ERROR = repr(exc)
else:
    Z3_IMPORT_ERROR = None

try:
    import cvc5
    from cvc5 import Kind
except Exception as exc:  # pragma: no cover - receipt blocker path
    cvc5 = None
    Kind = None
    CVC5_IMPORT_ERROR = repr(exc)
else:
    CVC5_IMPORT_ERROR = None

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover - receipt blocker path
    Cl = None
    CLIFFORD_IMPORT_ERROR = repr(exc)
else:
    CLIFFORD_IMPORT_ERROR = None

try:
    import geomstats.backend as gs
    from geomstats.geometry.special_orthogonal import SpecialOrthogonal
except Exception as exc:  # pragma: no cover - receipt blocker path
    gs = None
    SpecialOrthogonal = None
    GEOMSTATS_IMPORT_ERROR = repr(exc)
else:
    GEOMSTATS_IMPORT_ERROR = None

try:
    import gudhi
except Exception as exc:  # pragma: no cover - receipt blocker path
    gudhi = None
    GUDHI_IMPORT_ERROR = repr(exc)
else:
    GUDHI_IMPORT_ERROR = None

try:
    import toponetx as tnx
except Exception as exc:  # pragma: no cover - receipt blocker path
    tnx = None
    TOPONETX_IMPORT_ERROR = repr(exc)
else:
    TOPONETX_IMPORT_ERROR = None

try:
    import rustworkx as rx
except Exception as exc:  # pragma: no cover - receipt blocker path
    rx = None
    RUSTWORKX_IMPORT_ERROR = repr(exc)
else:
    RUSTWORKX_IMPORT_ERROR = None

try:
    from e3nn import o3
except Exception as exc:  # pragma: no cover - receipt blocker path
    o3 = None
    E3NN_IMPORT_ERROR = repr(exc)
else:
    E3NN_IMPORT_ERROR = None


CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_SO3 = 1.0e-6
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "gstruct_hybrid_reduction_chain_codex_probe"

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


def perm_sign(seq: tuple[int, ...]) -> int:
    inv = 0
    for i in range(len(seq)):
        for j in range(i + 1, len(seq)):
            if seq[i] > seq[j]:
                inv += 1
    return -1 if inv % 2 else 1


def form_value(form: dict[tuple[int, ...], int], inds: tuple[int, ...]) -> int:
    if len(set(inds)) != len(inds):
        return 0
    sorted_inds = tuple(sorted(inds))
    return perm_sign(inds) * form.get(sorted_inds, 0)


def hodge_star(form: dict[tuple[int, ...], int], n: int) -> dict[tuple[int, ...], int]:
    out: dict[tuple[int, ...], int] = {}
    full = tuple(range(n))
    for inds, coeff in form.items():
        comp = tuple(i for i in full if i not in inds)
        sign = perm_sign(inds + comp)
        out[comp] = out.get(comp, 0) + coeff * sign
    return {k: v for k, v in out.items() if v != 0}


def wedge_basis(
    form: dict[tuple[int, ...], int],
    basis_index: int,
) -> dict[tuple[int, ...], int]:
    out: dict[tuple[int, ...], int] = {}
    for inds, coeff in form.items():
        raw = inds + (basis_index,)
        if len(set(raw)) != len(raw):
            continue
        key = tuple(sorted(raw))
        out[key] = out.get(key, 0) + coeff * perm_sign(raw)
    return {k: v for k, v in out.items() if v != 0}


def standard_g2_phi() -> dict[tuple[int, int, int], int]:
    # e123 + e145 + e167 + e246 - e257 - e347 - e356, 0-indexed.
    return {
        (0, 1, 2): 1,
        (0, 3, 4): 1,
        (0, 5, 6): 1,
        (1, 3, 5): 1,
        (1, 4, 6): -1,
        (2, 3, 6): -1,
        (2, 4, 5): -1,
    }


def spin7_cayley_form() -> dict[tuple[int, int, int, int], int]:
    phi = standard_g2_phi()
    star_phi = hodge_star(phi, 7)
    phi_wedge_e8 = wedge_basis(phi, 7)
    omega: dict[tuple[int, int, int, int], int] = {}
    for source in (star_phi, phi_wedge_e8):
        for inds, coeff in source.items():
            omega[inds] = omega.get(inds, 0) + coeff
    return {k: v for k, v in omega.items() if v != 0}


def so_basis(n: int) -> list[list[list[int]]]:
    basis = []
    for i in range(n):
        for j in range(i + 1, n):
            mat = [[0 for _ in range(n)] for _ in range(n)]
            mat[i][j] = 1
            mat[j][i] = -1
            basis.append(mat)
    return basis


def form_action_vector(
    mat: list[list[int]],
    form: dict[tuple[int, ...], int],
    n: int,
    degree: int,
) -> list[int]:
    rows = []
    for target in itertools.combinations(range(n), degree):
        total = 0
        target_list = list(target)
        for slot, idx in enumerate(target):
            for p in range(n):
                coeff = mat[p][idx]
                if coeff == 0:
                    continue
                changed = target_list.copy()
                changed[slot] = p
                total += -coeff * form_value(form, tuple(changed))
        rows.append(total)
    return rows


def fixed_vector_rows(n: int, basis: list[list[list[int]]], vector_index: int) -> list[list[int]]:
    rows: list[list[int]] = []
    for component in range(n):
        rows.append([mat[component][vector_index] for mat in basis])
    return rows


def exact_rank(rows: list[list[int]]) -> int:
    if not rows:
        return 0
    return int(sp.Matrix(rows).rank())


def torch_rank(rows: list[list[int]], tol: float = 1.0e-8) -> int:
    if not rows:
        return 0
    m = torch.tensor(rows, dtype=RTYPE)
    if m.numel() == 0:
        return 0
    s = torch.linalg.svdvals(m)
    return int((s > tol).sum().item())


def stabilizer_report(
    name: str,
    n: int,
    form: dict[tuple[int, ...], int],
    fixed_vector: int | None = None,
) -> dict[str, Any]:
    degree = len(next(iter(form)))
    basis = so_basis(n)
    columns = [form_action_vector(mat, form, n, degree) for mat in basis]
    form_rows = [list(row) for row in zip(*columns)]
    rows = form_rows
    if fixed_vector is not None:
        rows = rows + fixed_vector_rows(n, basis, fixed_vector)
    rank_exact = exact_rank(rows)
    rank_torch = torch_rank(rows)
    return {
        "name": name,
        "ambient_so_dim": len(basis),
        "constraint_rows": len(rows),
        "rank_exact_sympy": rank_exact,
        "rank_torch_svd": rank_torch,
        "stabilizer_dim_exact": len(basis) - rank_exact,
        "stabilizer_dim_torch": len(basis) - rank_torch,
        "fixed_vector_index": fixed_vector,
        "form_terms": len(form),
    }


def cartan_rank_report() -> dict[str, Any]:
    cartan = {
        "SU(2)_A1": sp.Matrix([[2]]),
        "SU(3)_A2": sp.Matrix([[2, -1], [-1, 2]]),
        "G2": sp.Matrix([[2, -1], [-3, 2]]),
        "Spin(7)_B3": sp.Matrix([[2, -1, 0], [-1, 2, -2], [0, -1, 2]]),
    }
    return {name: int(mat.rank()) for name, mat in cartan.items()}


def normalize_axis(axis: tuple[float, float, float]) -> torch.Tensor:
    raw = torch.tensor(axis, dtype=RTYPE)
    return raw / torch.linalg.vector_norm(raw)


def u1_in_su2(theta: float) -> torch.Tensor:
    return torch.diag(torch.tensor([complex(math.cos(theta), math.sin(theta)),
                                    complex(math.cos(-theta), math.sin(-theta))],
                                   dtype=CDTYPE))


def su2_from_axis_angle(theta: float, axis: tuple[float, float, float]) -> torch.Tensor:
    n = normalize_axis(axis)
    h = n[0] * SX + n[1] * SY + n[2] * SZ
    return torch.linalg.matrix_exp(-0.5j * theta * h)


def embed_su2_in_su3(u: torch.Tensor) -> torch.Tensor:
    out = torch.eye(3, dtype=CDTYPE)
    out[:2, :2] = u
    return out


def unitary_defect(u: torch.Tensor) -> float:
    eye = torch.eye(u.shape[0], dtype=CDTYPE)
    return float(torch.linalg.matrix_norm(u.conj().T @ u - eye).item())


def det_one_defect(u: torch.Tensor) -> float:
    return float(torch.abs(torch.linalg.det(u) - torch.tensor(1.0, dtype=CDTYPE)).item())


def su2_induced_so3(u: torch.Tensor) -> torch.Tensor:
    r = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = u @ sj @ u.conj().T
        for i, si in enumerate(PAULI):
            r[i, j] = torch.trace(si @ conj).real / 2
    return r


def so3_defects(r: torch.Tensor) -> dict[str, float]:
    return {
        "det_defect": abs(float(torch.det(r).item()) - 1.0),
        "orthogonality_defect": float(torch.linalg.matrix_norm(r.T @ r - torch.eye(3, dtype=RTYPE)).item()),
    }


def torch_group_report() -> dict[str, Any]:
    theta_a = 0.37
    theta_b = -0.91
    ua = u1_in_su2(theta_a)
    ub = u1_in_su2(theta_b)
    u1_hom = float(torch.linalg.matrix_norm(ua @ ub - u1_in_su2(theta_a + theta_b)).item())

    su2_a = su2_from_axis_angle(0.73, (1.0, 2.0, 3.0))
    su2_b = su2_from_axis_angle(-1.11, (0.25, -0.4, 0.8))
    su3_a = embed_su2_in_su3(su2_a)
    su3_b = embed_su2_in_su3(su2_b)
    su2_su3_hom = float(torch.linalg.matrix_norm(su3_a @ su3_b - embed_su2_in_su3(su2_a @ su2_b)).item())

    u_2pi = su2_from_axis_angle(2.0 * math.pi, (0.0, 0.0, 1.0))
    u_4pi = su2_from_axis_angle(4.0 * math.pi, (0.0, 0.0, 1.0))
    r_2pi = su2_induced_so3(u_2pi)
    r_a = su2_induced_so3(su2_a)
    r_b = su2_induced_so3(su2_b)
    r_hom = float(torch.linalg.matrix_norm(su2_induced_so3(su2_a @ su2_b) - r_a @ r_b).item())

    return {
        "u1_in_su2": {
            "unitary_defect": unitary_defect(ua),
            "det_one_defect": det_one_defect(ua),
            "homomorphism_defect": u1_hom,
        },
        "su2_in_su3": {
            "su2_unitary_defect": unitary_defect(su2_a),
            "su2_det_one_defect": det_one_defect(su2_a),
            "embedded_su3_unitary_defect": unitary_defect(su3_a),
            "embedded_su3_det_one_defect": det_one_defect(su3_a),
            "embedding_homomorphism_defect": su2_su3_hom,
        },
        "spin3_to_so3": {
            "u_2pi_minus_negative_identity_norm": float(torch.linalg.matrix_norm(u_2pi + I2).item()),
            "u_4pi_minus_identity_norm": float(torch.linalg.matrix_norm(u_4pi - I2).item()),
            "r_2pi_minus_identity_norm": float(torch.linalg.matrix_norm(r_2pi - torch.eye(3, dtype=RTYPE)).item()),
            "so3_defects_sample": so3_defects(r_a),
            "homomorphism_defect": r_hom,
            "sample_so3_matrix": [[float(x) for x in row] for row in r_a],
        },
    }


def z3_dim_chain_certificate(dims: list[int]) -> dict[str, Any]:
    if z3 is None:
        return {"negation_status": "import_error", "pass": False, "error": Z3_IMPORT_ERROR}
    solver = z3.Solver()
    vars_ = [z3.Int(f"d{i}") for i in range(len(dims))]
    for var, val in zip(vars_, dims):
        solver.add(var == val)
    solver.add(z3.Or([vars_[i] >= vars_[i + 1] for i in range(len(vars_) - 1)]))
    status = str(solver.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_dim_chain_certificate(dims: list[int]) -> dict[str, Any]:
    if cvc5 is None or Kind is None:
        return {"negation_status": "import_error", "pass": False, "error": CVC5_IMPORT_ERROR}
    slv = cvc5.Solver()
    slv.setLogic("QF_LIA")
    int_sort = slv.getIntegerSort()
    vars_ = [slv.mkConst(int_sort, f"d{i}") for i in range(len(dims))]
    for var, val in zip(vars_, dims):
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, var, slv.mkInteger(val)))
    violations = [slv.mkTerm(Kind.GEQ, vars_[i], vars_[i + 1]) for i in range(len(vars_) - 1)]
    slv.assertFormula(slv.mkTerm(Kind.OR, *violations))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat()}


def clifford_double_cover_report() -> dict[str, Any]:
    if Cl is None:
        return {"pass": False, "error": CLIFFORD_IMPORT_ERROR}
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    bivector = e1 * e2
    theta = 2.0 * math.pi
    rotor = math.cos(theta / 2.0) - math.sin(theta / 2.0) * bivector
    scalar = float(rotor.value[0])
    non_scalar_norm = math.sqrt(sum(float(x) * float(x) for x in rotor.value[1:]))
    basis = [e1, e2, e3]
    r = torch.zeros((3, 3), dtype=RTYPE)
    for j, ej in enumerate(basis):
        rotated = rotor * ej * (~rotor)
        for i, ei in enumerate(basis):
            r[i, j] = float((rotated * ei).value[0])
    identity_defect = float(torch.linalg.matrix_norm(r - torch.eye(3, dtype=RTYPE)).item())
    return {
        "rotor_scalar_at_2pi": scalar,
        "rotor_non_scalar_norm_at_2pi": non_scalar_norm,
        "vector_rotation_identity_defect_at_2pi": identity_defect,
        "pass": abs(scalar + 1.0) < TOL and non_scalar_norm < TOL and identity_defect < TOL,
    }


def geomstats_so3_report(r: torch.Tensor) -> dict[str, Any]:
    if gs is None or SpecialOrthogonal is None:
        return {"pass": False, "error": GEOMSTATS_IMPORT_ERROR}
    try:
        try:
            group = SpecialOrthogonal(n=3, point_type="matrix")
        except TypeError:
            group = SpecialOrthogonal(n=3)
        belongs = group.belongs(gs.array([[float(x) for x in row] for row in r]), atol=TOL_SO3)
        if hasattr(belongs, "item"):
            belongs_bool = bool(belongs.item())
        else:
            belongs_bool = bool(belongs)
        return {"belongs_so3": belongs_bool, "pass": belongs_bool}
    except Exception as exc:  # pragma: no cover - receipt blocker path
        return {"pass": False, "error": repr(exc)}


def e3nn_so3_report(r: torch.Tensor) -> dict[str, Any]:
    if o3 is None:
        return {"pass": False, "error": E3NN_IMPORT_ERROR}
    try:
        rf = r.to(torch.float32)
        a, b, c = o3.matrix_to_angles(rf)
        recon = o3.angles_to_matrix(a, b, c)
        recon_err = float(torch.linalg.matrix_norm(recon - rf).item())
        defects = so3_defects(r)
        passed = recon_err < TOL_SO3 and defects["det_defect"] < TOL_SO3 and defects["orthogonality_defect"] < TOL_SO3
        return {
            "e3nn_reconstruction_error": recon_err,
            "det_defect": defects["det_defect"],
            "orthogonality_defect": defects["orthogonality_defect"],
            "pass": passed,
        }
    except Exception as exc:  # pragma: no cover - receipt blocker path
        return {"pass": False, "error": repr(exc)}


def gudhi_s7_report() -> dict[str, Any]:
    if gudhi is None:
        return {"pass": False, "error": GUDHI_IMPORT_ERROR}
    try:
        st = gudhi.SimplexTree()
        vertices = tuple(range(9))
        facets = [tuple(v for v in vertices if v != omitted) for omitted in vertices]
        for facet in facets:
            st.insert(facet, filtration=0.0)
        st.persistence(persistence_dim_max=True)
        betti = [int(x) for x in st.betti_numbers()]
        expected = [1, 0, 0, 0, 0, 0, 0, 1]
        return {
            "complex": "boundary_of_8_simplex",
            "num_vertices": 9,
            "num_facets": len(facets),
            "betti_numbers": betti,
            "expected_s7_betti": expected,
            "pass": betti == expected,
        }
    except Exception as exc:  # pragma: no cover - receipt blocker path
        return {"pass": False, "error": repr(exc)}


def toponetx_s7_report() -> dict[str, Any]:
    if tnx is None:
        return {"pass": False, "error": TOPONETX_IMPORT_ERROR}
    try:
        vertices = tuple(range(9))
        facets = [tuple(v for v in vertices if v != omitted) for omitted in vertices]
        sc = tnx.SimplicialComplex(facets)
        dim_attr = getattr(sc, "dim", None)
        dim = dim_attr() if callable(dim_attr) else dim_attr
        cells_7 = None
        if hasattr(sc, "skeleton"):
            cells_7 = len(list(sc.skeleton(7)))
        passed = int(dim) == 7 and len(facets) == 9
        return {
            "complex": "boundary_of_8_simplex",
            "dimension": int(dim),
            "input_facets": len(facets),
            "skeleton_7_size": cells_7,
            "pass": passed,
        }
    except Exception as exc:  # pragma: no cover - receipt blocker path
        return {"pass": False, "error": repr(exc)}


def rustworkx_chain_report(dims: dict[str, int]) -> dict[str, Any]:
    if rx is None:
        return {"pass": False, "error": RUSTWORKX_IMPORT_ERROR}
    try:
        chain = ["U(1)", "SU(2)", "SU(3)", "G2", "Spin(7)", "SO(8)"]
        graph = rx.PyDiGraph()
        node_ids = {name: graph.add_node(name) for name in chain}
        for left, right in zip(chain[:-1], chain[1:]):
            graph.add_edge(node_ids[left], node_ids[right], "reduction")
        edges = [(graph[u], graph[v]) for u, v in graph.edge_list()]
        monotone_edges = all(dims[left] < dims[right] for left, right in edges)
        topo = [graph[idx] for idx in rx.topological_sort(graph)]
        return {
            "nodes": chain,
            "edges": edges,
            "topological_order": topo,
            "num_nodes": graph.num_nodes(),
            "num_edges": graph.num_edges(),
            "strictly_increasing_along_edges": monotone_edges,
            "pass": topo == chain and monotone_edges and graph.num_edges() == 5,
        }
    except Exception as exc:  # pragma: no cover - receipt blocker path
        return {"pass": False, "error": repr(exc)}


def make_check(invariant: str, computed: Any, known: Any, match: bool) -> dict[str, Any]:
    return {
        "invariant": invariant,
        "computed": computed,
        "known": known,
        "match": bool(match),
    }


def build_receipt() -> dict[str, Any]:
    phi = standard_g2_phi()
    omega = spin7_cayley_form()
    g2 = stabilizer_report("G2_stabilizer_of_phi_in_so7", 7, phi)
    su3_in_g2 = stabilizer_report("SU3_as_G2_stabilizer_of_unit_vector", 7, phi, fixed_vector=6)
    spin7 = stabilizer_report("Spin7_stabilizer_of_Cayley_4form_in_so8", 8, omega)
    g2_in_spin7 = stabilizer_report("G2_as_Spin7_stabilizer_of_unit_vector", 8, omega, fixed_vector=7)

    dims = {
        "U(1)": 1,
        "SU(2)": 2 * 2 - 1,
        "SU(3)": 3 * 3 - 1,
        "G2": g2["stabilizer_dim_exact"],
        "Spin(7)": spin7["stabilizer_dim_exact"],
        "SO(8)": len(so_basis(8)),
    }
    dim_chain = [dims[name] for name in ["U(1)", "SU(2)", "SU(3)", "G2", "Spin(7)", "SO(8)"]]
    known_dims = {"U(1)": 1, "SU(2)": 3, "SU(3)": 8, "G2": 14, "Spin(7)": 21, "SO(8)": 28}
    rank_report = cartan_rank_report()
    known_ranks = {"SU(2)_A1": 1, "SU(3)_A2": 2, "G2": 2, "Spin(7)_B3": 3}

    torch_group = torch_group_report()
    sample_so3 = torch.tensor(torch_group["spin3_to_so3"]["sample_so3_matrix"], dtype=RTYPE)
    z3_cert = z3_dim_chain_certificate(dim_chain)
    cvc5_cert = cvc5_dim_chain_certificate(dim_chain)
    clifford = clifford_double_cover_report()
    geomstats = geomstats_so3_report(sample_so3)
    e3 = e3nn_so3_report(sample_so3)
    gudhi_s7 = gudhi_s7_report()
    toponetx_s7 = toponetx_s7_report()
    rust_chain = rustworkx_chain_report(dims)

    quotient_orbit_dim = spin7["stabilizer_dim_exact"] - g2_in_spin7["stabilizer_dim_exact"]
    dim_strict = all(dim_chain[i] < dim_chain[i + 1] for i in range(len(dim_chain) - 1))
    exact_torch_dims_agree = (
        g2["stabilizer_dim_exact"] == g2["stabilizer_dim_torch"]
        and su3_in_g2["stabilizer_dim_exact"] == su3_in_g2["stabilizer_dim_torch"]
        and spin7["stabilizer_dim_exact"] == spin7["stabilizer_dim_torch"]
        and g2_in_spin7["stabilizer_dim_exact"] == g2_in_spin7["stabilizer_dim_torch"]
    )

    known_value_checks = [
        make_check("dimension_chain_values", dims, known_dims, dims == known_dims),
        make_check("dimension_chain_strictly_increasing", dim_chain, "1 < 3 < 8 < 14 < 21 < 28", dim_strict),
        make_check("z3_unsat_to_violate_dimension_monotonicity", z3_cert["negation_status"], "unsat", z3_cert["pass"]),
        make_check("cvc5_unsat_to_violate_dimension_monotonicity", cvc5_cert["negation_status"], "unsat", cvc5_cert["pass"]),
        make_check("cartan_ranks_SU2_SU3_G2_Spin7", rank_report, known_ranks, rank_report == known_ranks),
        make_check(
            "U1_embeds_in_SU2_by_unitary_det1_and_homomorphism",
            torch_group["u1_in_su2"],
            "unitary defect=0, det defect=0, E(a)E(b)=E(a+b)",
            torch_group["u1_in_su2"]["unitary_defect"] < TOL
            and torch_group["u1_in_su2"]["det_one_defect"] < TOL
            and torch_group["u1_in_su2"]["homomorphism_defect"] < TOL,
        ),
        make_check(
            "SU2_embeds_in_SU3_by_block_unitary_det1_and_homomorphism",
            torch_group["su2_in_su3"],
            "unitary defect=0, det defect=0, E(A)E(B)=E(AB)",
            torch_group["su2_in_su3"]["su2_unitary_defect"] < TOL
            and torch_group["su2_in_su3"]["su2_det_one_defect"] < TOL
            and torch_group["su2_in_su3"]["embedded_su3_unitary_defect"] < TOL
            and torch_group["su2_in_su3"]["embedded_su3_det_one_defect"] < TOL
            and torch_group["su2_in_su3"]["embedding_homomorphism_defect"] < TOL,
        ),
        make_check("G2_stabilizer_dimension_of_standard_3form_phi", g2, "dim 14", g2["stabilizer_dim_exact"] == 14),
        make_check("SU3_subset_G2_as_unit_vector_stabilizer", su3_in_g2, "dim 8", su3_in_g2["stabilizer_dim_exact"] == 8),
        make_check("Spin7_stabilizer_dimension_of_Cayley_4form", spin7, "dim 21", spin7["stabilizer_dim_exact"] == 21),
        make_check("G2_subset_Spin7_as_unit_vector_stabilizer", g2_in_spin7, "dim 14", g2_in_spin7["stabilizer_dim_exact"] == 14),
        make_check("Spin7_over_G2_orbit_dimension", quotient_orbit_dim, "7", quotient_orbit_dim == 7),
        make_check("torch_svd_stabilizer_dimensions_match_sympy_exact_ranks", exact_torch_dims_agree, "True", exact_torch_dims_agree),
        make_check(
            "Spin3_SU2_to_SO3_double_cover_2pi",
            torch_group["spin3_to_so3"],
            "2pi spinor=-I and induced SO3 rotation=I",
            torch_group["spin3_to_so3"]["u_2pi_minus_negative_identity_norm"] < TOL_SO3
            and torch_group["spin3_to_so3"]["r_2pi_minus_identity_norm"] < TOL_SO3
            and torch_group["spin3_to_so3"]["u_4pi_minus_identity_norm"] < TOL_SO3,
        ),
        make_check(
            "SU2_to_SO3_homomorphism_R_UV_equals_RU_RV",
            torch_group["spin3_to_so3"]["homomorphism_defect"],
            "0",
            torch_group["spin3_to_so3"]["homomorphism_defect"] < TOL_SO3,
        ),
        make_check("clifford_Cl3_rotor_double_cover_at_2pi", clifford, "rotor=-1, vector action identity", clifford["pass"]),
        make_check("geomstats_certifies_induced_matrix_belongs_SO3", geomstats, "belongs SO(3)", geomstats["pass"]),
        make_check("e3nn_l1_roundtrip_certifies_induced_SO3", e3, "SO(3) l=1 reconstruction", e3["pass"]),
        make_check("GUDHI_boundary_of_8simplex_has_S7_homology", gudhi_s7, "Betti [1,0,0,0,0,0,0,1]", gudhi_s7["pass"]),
        make_check("TopoNetX_boundary_of_8simplex_dimension", toponetx_s7, "dimension 7 with 9 facets", toponetx_s7["pass"]),
        make_check("rustworkx_reduction_chain_graph_is_ordered_and_monotone", rust_chain, "single ordered chain with increasing dimensions", rust_chain["pass"]),
    ]

    import_errors = {
        "z3": Z3_IMPORT_ERROR,
        "cvc5": CVC5_IMPORT_ERROR,
        "clifford": CLIFFORD_IMPORT_ERROR,
        "geomstats": GEOMSTATS_IMPORT_ERROR,
        "gudhi": GUDHI_IMPORT_ERROR,
        "toponetx": TOPONETX_IMPORT_ERROR,
        "rustworkx": RUSTWORKX_IMPORT_ERROR,
        "e3nn": E3NN_IMPORT_ERROR,
    }
    import_blockers = [f"{name} import failed: {err}" for name, err in import_errors.items() if err]
    known_values_all_match = all(check["match"] for check in known_value_checks)
    blockers = import_blockers + [
        f"KNOWN-VALUE MISMATCH: {check['invariant']} computed={check['computed']} known={check['known']}"
        for check in known_value_checks
        if not check["match"]
    ]
    all_pass = known_values_all_match and not import_blockers

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "complex128 SU(2)/SU(3) embeddings, determinant/unitarity checks, SU(2)->SO(3) double cover, homomorphism defects, and numerical stabilizer rank cross-checks",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "exact integer-rank stabilizer dimensions for G2 and Spin(7), and exact Cartan-matrix ranks for SU(2), SU(3), G2, Spin(7)",
        },
        "z3": {
            "used": z3 is not None,
            "role": "load_bearing",
            "reason": "SMT certificate that the computed dimension chain cannot violate strict monotonicity; the violation query must be UNSAT",
        },
        "cvc5": {
            "used": cvc5 is not None,
            "role": "load_bearing",
            "reason": "independent SMT certificate for the same dimension-chain monotonicity violation query",
        },
        "clifford": {
            "used": Cl is not None,
            "role": "load_bearing",
            "reason": "Cl(3) rotor computes the Spin(3)->SO(3) double-cover witness at 2pi independently from the Pauli-matrix torch path",
        },
        "geomstats": {
            "used": gs is not None and SpecialOrthogonal is not None,
            "role": "load_bearing",
            "reason": "SpecialOrthogonal.belongs certifies the SU(2)-induced real matrix is on SO(3)",
        },
        "gudhi": {
            "used": gudhi is not None,
            "role": "load_bearing",
            "reason": "computes homology of the boundary of the 8-simplex as the S^7 topology witness for Spin(7)/G2",
        },
        "toponetx": {
            "used": tnx is not None,
            "role": "load_bearing",
            "reason": "builds the same boundary-of-8-simplex simplicial complex and checks its 7-dimensional cell structure",
        },
        "rustworkx": {
            "used": rx is not None,
            "role": "load_bearing",
            "reason": "represents the reduction chain as a directed graph and verifies ordered monotone edges",
        },
        "e3nn": {
            "used": o3 is not None,
            "role": "load_bearing",
            "reason": "round-trips the induced SO(3) matrix through the l=1 representation angle machinery",
        },
    }

    return {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "known_gstructure_lie_group_probe",
        "purpose": "Independent known-math reduction-chain probe for U(1)<SU(2)<SU(3)<G2<Spin(7)<SO(8), computed without copying any external model numbers.",
        "scientific_question": "Do finite matrix embeddings, exact stabilizer equations, SMT monotonicity certificates, and topology/group-library checks reproduce the known hybrid reduction chain invariants?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a known-value cross-model comparison probe. Does not admit a manifold layer, G-structure selection, Axis0, flux, or physics claim.",
        "finite_map": "candidate group/algebra data -> exact stabilizer constraint matrices, embedding homomorphism defects, quotient orbit dimension, and S^7 topology witness",
        "domain": "finite matrix representatives for U(1), SU(2), SU(3); integer exterior-form tensors phi in Lambda^3(R7*) and Omega in Lambda^4(R8*); directed reduction graph; boundary-of-8-simplex S^7 model",
        "codomain_or_output": "dimension/rank/containment/double-cover/topology known-value checks and JSON result receipt",
        "carrier_realization": "torch.complex128/float64 matrices and sympy exact integer forms; no NumPy claim substrate",
        "reduction_chain": ["U(1)", "SU(2)", "SU(3)", "G2", "Spin(7)", "SO(8)"],
        "known_dimensions_target": known_dims,
        "computed_dimensions": dims,
        "known_ranks_target": known_ranks,
        "computed_ranks": rank_report,
        "stabilizer_reports": {
            "G2": g2,
            "SU3_in_G2": su3_in_g2,
            "Spin7": spin7,
            "G2_in_Spin7": g2_in_spin7,
        },
        "embedding_and_double_cover_reports": torch_group,
        "smt_certificates": {"z3": z3_cert, "cvc5": cvc5_cert},
        "library_reports": {
            "clifford": clifford,
            "geomstats": geomstats,
            "gudhi": gudhi_s7,
            "toponetx": toponetx_s7,
            "rustworkx": rust_chain,
            "e3nn": e3,
        },
        "known_value_checks": known_value_checks,
        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "n_known_value_checks": len(known_value_checks),
            "blocker_count": len(blockers),
            "classification": "diagnostic_only",
        },
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: spec["role"] for name, spec in tool_manifest.items()},
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "group_surfaces_used": ["torch", "clifford", "geomstats", "e3nn"],
        "topology_surfaces_used": ["gudhi", "toponetx", "rustworkx"],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "geomstats", "gudhi", "toponetx", "rustworkx", "e3nn"],
        "actual_tools_used": [name for name, spec in tool_manifest.items() if spec["used"]],
        "required_artifacts": ["json_result_receipt"],
        "artifacts_emitted": ["json_result_receipt"],
        "negative_or_block_conditions": [
            "any known dimension or rank mismatch",
            "z3 or cvc5 monotonicity violation query not UNSAT",
            "det=1/unitary embedding defect above tolerance",
            "G2 or Spin(7) stabilizer dimension mismatch",
            "Spin(7)/G2 orbit dimension not 7",
            "S^7 topology witness does not have expected homology/dimension",
            "2pi SU(2) spinor not -I or induced SO(3) not identity",
        ],
        "pass_rule": "all known_value_checks have match=true and no required tool import blocker exists",
        "fail_rule": "any mismatch or missing required load-bearing tool records a blocker; no value is fudged",
        "all_pass": all_pass,
        "blockers": blockers,
        "eligible_consumers": ["cross_model_known_gstructure_comparison"],
        "blocked_consumers": ["manifold_admission", "official_G_structure_selection", "Axis0", "flux", "physics"],
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_receipt()
    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(out),
        "all_pass": result["all_pass"],
        "known_values_all_match": result["result_summary"]["known_values_all_match"],
        "n_known_value_checks": result["result_summary"]["n_known_value_checks"],
        "blockers": result["blockers"],
        "known_value_checks": [
            {
                "invariant": check["invariant"],
                "computed": check["computed"],
                "known": check["known"],
                "match": check["match"],
            }
            for check in result["known_value_checks"]
        ],
    }, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

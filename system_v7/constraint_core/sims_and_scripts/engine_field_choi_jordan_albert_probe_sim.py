#!/usr/bin/env python3
"""Engine-field Choi to Jordan/Albert packing probe.

Scratch diagnostic only.

Question under test:
Can the planned axes 7-12 many-engine mirror layer be given a bounded carrier
candidate where engine nodes have Choi-channel data and pairwise relations pack
into Hermitian octonionic matrices?

What this can earn:
- A finite packing pattern: n real node scalars plus 8*C(n,2) edge coordinates.
- H_2(O) and H_3(O) satisfy the Jordan identity; H_4(O) generically fails.
- Three engine nodes are the first nontrivial Albert-coordinate candidate.

What this cannot earn:
- axes 7-12 runtime truth;
- a natural/canonical Choi-to-octonion map;
- F4/E6/E7/E8 dynamics;
- "dim 52 = F4 state space" claims.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/engine_field_choi_jordan_albert_probe_sim.py"
RESULT_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/engine_field_choi_jordan_albert_probe_sim_results.json"

SIM_ID = "engine_field_choi_jordan_albert_probe"
SEED = 7
TOL_PASS = 1.0e-8
TOL_FAIL = 1.0e-5
GENERIC_SAMPLES = 48
FIELD_SAMPLES = 24

FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite algebra tables, Choi matrices, Jordan residuals, and sampled controls",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, timestamps, paths, and scalar math",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "python_stdlib": "supportive"}


def basis(dim: int, idx: int) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[idx] = 1.0
    return out


def conjugate(x: np.ndarray) -> np.ndarray:
    out = np.array(x, dtype=float, copy=True)
    out[1:] *= -1.0
    return out


def setprod(table: np.ndarray, a: int, b: int, c: int, s: float) -> None:
    table[c, a, b] = s


def add_identity(table: np.ndarray) -> None:
    for a in range(table.shape[0]):
        setprod(table, 0, a, a, 1.0)
        setprod(table, a, 0, a, 1.0)


def octonion_table() -> np.ndarray:
    table = np.zeros((8, 8, 8), dtype=float)
    add_identity(table)
    for a in range(1, 8):
        setprod(table, a, a, 0, -1.0)
    for i, j, k in FANO:
        for a, b, c, s in (
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ):
            setprod(table, a, b, c, s)
    return table


def real_table() -> np.ndarray:
    return np.ones((1, 1, 1), dtype=float)


def cd_double(parent: np.ndarray) -> np.ndarray:
    n = parent.shape[0]
    dim = 2 * n
    table = np.zeros((dim, dim, dim), dtype=float)
    eye = np.eye(dim)
    for i in range(dim):
        for j in range(dim):
            x, y = eye[i], eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, conjugate(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, conjugate(c))
            table[:, i, j] = np.concatenate([first, second])
    return table


def multiply(table: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.einsum("cab,a,b->c", table, x, y)


def algebra_table(name: str) -> np.ndarray:
    if name == "R":
        return real_table()
    if name == "C":
        return cd_double(real_table())
    if name == "H":
        return cd_double(cd_double(real_table()))
    if name == "O":
        return octonion_table()
    if name == "S":
        return cd_double(octonion_table())
    raise ValueError(name)


def vector_terms(v: np.ndarray) -> list[dict[str, Any]]:
    return [
        {"basis_index": int(i), "label": f"e{i}", "coefficient": float(x)}
        for i, x in enumerate(v)
        if abs(float(x)) > 1.0e-10
    ]


def associator(table: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def fano_unit_tests(table: np.ndarray) -> dict[str, Any]:
    square_max = 0.0
    anti_max = 0.0
    fano_failures = []
    for i in range(1, 8):
        square_max = max(square_max, float(np.linalg.norm(multiply(table, basis(8, i), basis(8, i)) + basis(8, 0))))
    for i in range(1, 8):
        for j in range(1, 8):
            if i != j:
                anti_max = max(
                    anti_max,
                    float(np.linalg.norm(multiply(table, basis(8, i), basis(8, j)) + multiply(table, basis(8, j), basis(8, i)))),
                )
    for i, j, k in FANO:
        if np.linalg.norm(multiply(table, basis(8, i), basis(8, j)) - basis(8, k)) > 1.0e-12:
            fano_failures.append([i, j, k])
    witness = associator(table, basis(8, 1), basis(8, 2), basis(8, 4))
    return {
        "e_i_square_minus_one_max_residual": square_max,
        "anticommutativity_max_residual": anti_max,
        "fano_line_failures": fano_failures,
        "nonassociative_witness_e1_e2_e4_norm": float(np.linalg.norm(witness)),
        "nonassociative_witness_terms": vector_terms(witness),
        "pass": square_max < 1.0e-12 and anti_max < 1.0e-12 and not fano_failures and np.linalg.norm(witness) > 1.0,
    }


def random_hermitian(n: int, dim: int, rng: np.random.Generator, scale: float = 0.22) -> np.ndarray:
    m = np.zeros((n, n, dim), dtype=float)
    for i in range(n):
        m[i, i, 0] = rng.normal(scale=scale)
    for i in range(n):
        for j in range(i + 1, n):
            v = rng.normal(scale=scale, size=dim)
            m[i, j, :] = v
            m[j, i, :] = conjugate(v)
    return m


def hn_matmul(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n, _, dim = a.shape
    out = np.zeros((n, n, dim), dtype=float)
    for i in range(n):
        for k in range(n):
            acc = np.zeros(dim, dtype=float)
            for j in range(n):
                acc += multiply(table, a[i, j, :], b[j, k, :])
            out[i, k, :] = acc
    return out


def jordan(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 0.5 * (hn_matmul(table, a, b) + hn_matmul(table, b, a))


def jordan_identity_residual(table: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
    xx = jordan(table, x, x)
    xy = jordan(table, x, y)
    left = jordan(table, xy, xx)
    right = jordan(table, x, jordan(table, y, xx))
    return float(np.linalg.norm(left - right))


def generic_jordan_sweep(table: np.ndarray, n: int, dim: int, rng: np.random.Generator, samples: int = GENERIC_SAMPLES) -> dict[str, Any]:
    residuals = []
    for _ in range(samples):
        x = random_hermitian(n, dim, rng)
        y = random_hermitian(n, dim, rng)
        residuals.append(jordan_identity_residual(table, x, y))
    residuals_np = np.asarray(residuals)
    return {
        "n": n,
        "dim_algebra": dim,
        "dim_Hn": n + dim * n * (n - 1) // 2,
        "samples": samples,
        "max_residual": float(np.max(residuals_np)),
        "median_residual": float(np.median(residuals_np)),
        "pass_fraction_under_tol": float(np.mean(residuals_np < TOL_PASS)),
    }


def wrong_fano_table(table: np.ndarray) -> np.ndarray:
    bad = table.copy()
    bad[:, 1, 2] *= -1.0
    return bad


def sedenion_zero_divisor(table: np.ndarray) -> dict[str, Any]:
    left = basis(16, 1) + basis(16, 10)
    right = basis(16, 5) + basis(16, 14)
    product = multiply(table, left, right)
    return {
        "left_terms": vector_terms(left),
        "right_terms": vector_terms(right),
        "product_norm": float(np.linalg.norm(product)),
        "left_norm": float(np.linalg.norm(left)),
        "right_norm": float(np.linalg.norm(right)),
        "zero_divisor_found": float(np.linalg.norm(product)) < 1.0e-12,
    }


def paulis() -> list[np.ndarray]:
    i = np.eye(2, dtype=complex)
    x = np.array([[0, 1], [1, 0]], dtype=complex)
    y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    z = np.array([[1, 0], [0, -1]], dtype=complex)
    return [i, x, y, z]


def choi_frame() -> list[np.ndarray]:
    i, x, y, z = paulis()
    raw = [
        np.kron(x, i),
        np.kron(y, i),
        np.kron(z, i),
        np.kron(i, x),
        np.kron(i, y),
        np.kron(i, z),
        np.kron(x, x),
        np.kron(z, z),
    ]
    return [b / math.sqrt(float(np.trace(b.conj().T @ b).real)) for b in raw]


def random_cptp_channel(rng: np.random.Generator, kraus_count: int = 3) -> list[np.ndarray]:
    raw = []
    for _ in range(kraus_count):
        a = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
        raw.append(a / math.sqrt(2.0 * kraus_count))
    gram = sum(a.conj().T @ a for a in raw)
    vals, vecs = np.linalg.eigh(gram)
    invsqrt = vecs @ np.diag(1.0 / np.sqrt(np.maximum(vals, 1.0e-12))) @ vecs.conj().T
    return [a @ invsqrt for a in raw]


def choi_from_kraus(kraus: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4, 4), dtype=complex)
    for k in kraus:
        v = k.reshape(4, order="C")
        out += np.outer(v, np.conjugate(v))
    return out


def partial_trace_output(choi: np.ndarray) -> np.ndarray:
    tensor = choi.reshape(2, 2, 2, 2)
    out = np.zeros((2, 2), dtype=complex)
    for output_idx in range(2):
        out += tensor[output_idx, :, output_idx, :]
    return out


def choi_checks(choi: np.ndarray) -> dict[str, float | bool]:
    eigs = np.linalg.eigvalsh((choi + choi.conj().T) / 2.0)
    pt = partial_trace_output(choi)
    return {
        "trace": float(np.trace(choi).real),
        "min_eigenvalue": float(np.min(eigs)),
        "partial_trace_identity_error": float(np.linalg.norm(pt - np.eye(2))),
        "is_cp_tp": bool(np.min(eigs) > -1.0e-9 and np.linalg.norm(pt - np.eye(2)) < 1.0e-9),
    }


def edge_features(choi_a: np.ndarray, choi_b: np.ndarray, frame: list[np.ndarray]) -> np.ndarray:
    delta = ((choi_a - choi_b) + (choi_a - choi_b).conj().T) / 2.0
    return np.array([float(np.trace(delta @ b).real) for b in frame], dtype=float)


def field_to_hno(chois: list[np.ndarray], table_dim: int = 8) -> np.ndarray:
    frame = choi_frame()
    n = len(chois)
    ident = choi_from_kraus([np.eye(2, dtype=complex)])
    m = np.zeros((n, n, table_dim), dtype=float)
    for i, c in enumerate(chois):
        m[i, i, 0] = float(np.linalg.norm(c - ident) / math.sqrt(max(np.linalg.norm(ident), 1.0e-12)))
    for i in range(n):
        for j in range(i + 1, n):
            v = edge_features(chois[i], chois[j], frame)
            if table_dim != 8:
                vv = np.zeros(table_dim)
                vv[: min(table_dim, 8)] = v[: min(table_dim, 8)]
                v = vv
            m[i, j, :] = 0.05 * v
            m[j, i, :] = conjugate(m[i, j, :])
    return m


def field_sweep(table: np.ndarray, n: int, rng: np.random.Generator) -> dict[str, Any]:
    residuals = []
    min_cp = float("inf")
    max_tp_error = 0.0
    edge_norms = []
    identical_edge_norm = None
    for sample in range(FIELD_SAMPLES):
        channels = [random_cptp_channel(rng) for _ in range(n)]
        chois = [choi_from_kraus(kraus) for kraus in channels]
        for c in chois:
            check = choi_checks(c)
            min_cp = min(min_cp, float(check["min_eigenvalue"]))
            max_tp_error = max(max_tp_error, float(check["partial_trace_identity_error"]))
        x = field_to_hno(chois)
        y = random_hermitian(n, table.shape[0], rng, scale=0.1)
        residuals.append(jordan_identity_residual(table, x, y))
        for i in range(n):
            for j in range(i + 1, n):
                edge_norms.append(float(np.linalg.norm(x[i, j, :])))
        if sample == 0:
            ident_field = field_to_hno([chois[0] for _ in range(n)])
            identical_edge_norm = float(
                max(np.linalg.norm(ident_field[i, j, :]) for i in range(n) for j in range(i + 1, n))
            )
    residuals_np = np.asarray(residuals)
    return {
        "n": n,
        "samples": FIELD_SAMPLES,
        "max_jordan_residual_against_random_probe": float(np.max(residuals_np)),
        "median_jordan_residual": float(np.median(residuals_np)),
        "pass_fraction_under_tol": float(np.mean(residuals_np < TOL_PASS)),
        "choi_min_eigenvalue": min_cp,
        "choi_max_partial_trace_identity_error": max_tp_error,
        "all_choi_cp_tp": bool(min_cp > -1.0e-9 and max_tp_error < 1.0e-9),
        "edge_norm_min": float(np.min(edge_norms)),
        "edge_norm_max": float(np.max(edge_norms)),
        "identical_channel_edge_norm_control": identical_edge_norm,
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    tables = {name: algebra_table(name) for name in ["R", "C", "H", "O", "S"]}
    o_table = tables["O"]
    fano = fano_unit_tests(o_table)

    generic = {
        "H2O": generic_jordan_sweep(o_table, 2, 8, rng),
        "H3O_albert": generic_jordan_sweep(o_table, 3, 8, rng),
        "H4O_count_control_dim52_not_jordan": generic_jordan_sweep(o_table, 4, 8, rng),
        "H4H_associative_control": generic_jordan_sweep(tables["H"], 4, 4, rng),
        "H4C_associative_control": generic_jordan_sweep(tables["C"], 4, 2, rng),
        "H4R_associative_control": generic_jordan_sweep(tables["R"], 4, 1, rng),
        "H3S_sedenion_control": generic_jordan_sweep(tables["S"], 3, 16, rng),
        "H3O_wrong_fano_control": generic_jordan_sweep(wrong_fano_table(o_table), 3, 8, rng),
    }

    field = {
        "two_engine_field_H2O": field_sweep(o_table, 2, rng),
        "three_engine_field_H3O": field_sweep(o_table, 3, rng),
        "four_engine_field_H4O_control": field_sweep(o_table, 4, rng),
    }

    pass_conditions = {
        "fano_unit_tests": fano["pass"],
        "generic_H2O_passes": generic["H2O"]["max_residual"] < TOL_PASS,
        "generic_H3O_passes": generic["H3O_albert"]["max_residual"] < TOL_PASS,
        "generic_H4O_fails": generic["H4O_count_control_dim52_not_jordan"]["max_residual"] > TOL_FAIL,
        "associative_H4H_passes": generic["H4H_associative_control"]["max_residual"] < TOL_PASS,
        "associative_H4C_passes": generic["H4C_associative_control"]["max_residual"] < TOL_PASS,
        "associative_H4R_passes": generic["H4R_associative_control"]["max_residual"] < TOL_PASS,
        "sedenion_H3_fails": generic["H3S_sedenion_control"]["max_residual"] > TOL_FAIL,
        "wrong_fano_H3_fails": generic["H3O_wrong_fano_control"]["max_residual"] > TOL_FAIL,
        "field_H2O_passes": field["two_engine_field_H2O"]["max_jordan_residual_against_random_probe"] < TOL_PASS,
        "field_H3O_passes": field["three_engine_field_H3O"]["max_jordan_residual_against_random_probe"] < TOL_PASS,
        "field_H4O_fails": field["four_engine_field_H4O_control"]["max_jordan_residual_against_random_probe"] > TOL_FAIL,
        "field_choi_checks": all(row["all_choi_cp_tp"] for row in field.values()),
        "identical_channels_collapse_edges": all(
            row["identical_channel_edge_norm_control"] is not None and row["identical_channel_edge_norm_control"] < 1.0e-12
            for row in field.values()
        ),
    }
    all_pass = all(pass_conditions.values())

    return {
        "schema": "codex_ratchet.engine_field_choi_jordan_albert_probe_result.v1",
        "sim_id": SIM_ID,
        "name": "engine field Choi Jordan Albert probe",
        "version": "1.0",
        "tier": "planned many-engine mirror layer / axes 7-12 candidate carrier scout",
        "created_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_execution_kind": "classical",
        "sim_class": "carrier_packing_probe",
        "purpose": "Test whether Choi-derived pairwise engine relations can populate H_n(O) carrier candidates while preserving the classical H2/H3 valid and H4 invalid Jordan pattern.",
        "scientific_question": "Does the many-engine mirror layer have a bounded Albert-coordinate carrier candidate, and do the right controls prevent count-only overclaim?",
        "root_constraints_in_force": [
            "F01 finite sampled channels, finite algebra tables, finite H_n(O) matrices",
            "N01 noncommutative/nonassociative octonion product with explicit order/grouping tests",
        ],
        "carrier_layer": "candidate n-engine complete graph: n node Choi scalars plus 8 real Choi-relation features per pair, packed as H_n(O)",
        "geometry_layer": "Choi-space deviations and normalized fixed Pauli-tensor projection frame; not a canonical geometry",
        "bridge_layer": "none; planned axes 7-12 mirror layer remains inactive",
        "cut_layer": "none",
        "law_or_candidate_tested": "H_n(O) Jordan identity and Choi-to-8-edge packing for n=2,3,4 with wrong-algebra controls",
        "branch_status_before_run": "axes 7-12 planned/provisional only",
        "allowed_claims": [
            "H2(O) and H3(O) pass the sampled Jordan identity while H4(O) fails.",
            "A frozen Choi-deviation projection can populate H2(O)/H3(O) candidate field objects without breaking channel validity.",
            "Dimension 52 from H4(O) is not a valid Jordan state-space claim; F4 remains Aut(H3(O)), not H4(O).",
        ],
        "promotion_blockers": [
            "Choi-to-8 map is frozen but not natural/canonical.",
            "No E-series action, equivariance, Freudenthal construction, or axes 7-12 runtime admission is tested.",
            "No formal proof beyond sampled finite residuals.",
        ],
        "required_tools": ["numpy"],
        "actual_tools_used": ["numpy", "python_stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": [
            "planned axes 7-12 Choi mirror layer source note",
            "Grok 4.5 external pressure receipt",
            "Fano octonion convention from local Jordan/octonion sims",
        ],
        "data_or_artifact_dependencies": [
            "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/grok45_engine_field_jordan_design_pressure_20260708.json"
        ],
        "required_negatives": [
            "H4(O) Jordan failure despite dimension 52",
            "wrong Fano H3 failure",
            "sedenion H3 failure",
            "associative R/C/H H4 pass controls",
            "identical Choi channels collapse pairwise edges",
        ],
        "negatives_run": pass_conditions,
        "kill_conditions": [
            "H3(O) generic or field residual fails tolerance",
            "H4(O) does not fail generically",
            "wrong Fano or sedenion controls reproduce the selective H2/H3 pass pattern",
            "Choi inputs are not CP/TP",
            "identical-channel edges do not collapse",
        ],
        "dimensions": {
            "formula": "dim H_n(A_dim=d) = n + d*n*(n-1)/2",
            "H2O": generic["H2O"]["dim_Hn"],
            "H3O": generic["H3O_albert"]["dim_Hn"],
            "H4O": generic["H4O_count_control_dim52_not_jordan"]["dim_Hn"],
            "F4_warning": "52 is the dimension of Aut(H3(O)), not a valid H4(O) Jordan state-space admission.",
        },
        "fano_unit_tests": fano,
        "generic_jordan_identity": generic,
        "choi_field_projection": {
            "map_status": "frozen_a_priori_lossy_projection_not_canonical",
            "frame": [
                "XxI", "YxI", "ZxI", "IxX", "IxY", "IxZ", "XxX", "ZxZ"
            ],
            "diagonal_scalar": "Frobenius distance from identity Choi",
            "edge_features": "real Hilbert-Schmidt projections of Choi_i - Choi_j onto fixed eight-frame",
            "field_sweeps": field,
        },
        "sedenion_zero_divisor_control": sedenion_zero_divisor(tables["S"]),
        "pass_conditions": pass_conditions,
        "pass_rule": "all pass_conditions true; otherwise diagnostic fails",
        "verdict": "bounded_albert_field_candidate_survives" if all_pass else "candidate_failed",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": [
            "axes 7-12 runtime admission",
            "IGT admission",
            "F4/E6/E7/E8 action or symmetry claim",
            "natural/canonical Choi-to-octonion map claim",
            "Axis0, bridge, manifold, or physics claims",
        ],
        "blocked_downstream_consumers": [
            "axes 7-12 runtime admission",
            "IGT admission",
            "F4/E6/E7/E8 action or symmetry claim",
            "natural/canonical Choi-to-octonion map claim",
            "Axis0, bridge, manifold, or physics claims",
        ],
        "divergence_log": [
            {
                "surface": "H4(O)",
                "observed": "Jordan identity fails generically",
                "reason": "Hermitian octonionic matrices stop at n=3 for the exceptional Jordan algebra; n=4 dimension 52 is count-only noise.",
            },
            {
                "surface": "wrong_fano",
                "observed": "H3 Jordan identity fails",
                "reason": "The Fano/octonion multiplication table is load-bearing, not decorative.",
            },
            {
                "surface": "associative H4 controls",
                "observed": "R/C/H H4 pass",
                "reason": "The H4 failure is specific to octonionic nonassociativity, not generic matrix size.",
            },
        ],
        "claim_ceiling": "Scratch diagnostic: a frozen Choi-to-edge packing can populate H2(O)/H3(O) candidate field objects and reproduces the H2/H3 pass vs H4 fail Jordan pattern. No axes 7-12 admission, IGT admission, E-series action, or natural-map claim.",
        "all_pass": all_pass,
    }


def print_summary(result: dict[str, Any]) -> None:
    print("ENGINE_FIELD_CHOI_JORDAN_ALBERT_PROBE")
    print(f"seed={SEED} classification={result['classification']} promotion_allowed={result['promotion_allowed']}")
    print(f"fano_unit_tests_pass={result['fano_unit_tests']['pass']}")
    for key, row in result["generic_jordan_identity"].items():
        print(
            f"generic {key}: dim={row['dim_Hn']} max_residual={row['max_residual']:.6e} "
            f"pass_fraction={row['pass_fraction_under_tol']:.2f}"
        )
    for key, row in result["choi_field_projection"]["field_sweeps"].items():
        print(
            f"field {key}: max_residual={row['max_jordan_residual_against_random_probe']:.6e} "
            f"choi_cp_tp={row['all_choi_cp_tp']} identical_edge={row['identical_channel_edge_norm_control']:.3e}"
        )
    print(f"sedenion_zero_divisor_found={result['sedenion_zero_divisor_control']['zero_divisor_found']}")
    print(f"verdict={result['verdict']} all_pass={result['all_pass']}")
    print(f"wrote: {RESULT_PATH}")


def json_default(value: Any) -> Any:
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

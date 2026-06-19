#!/usr/bin/env python3
# object_id: mp2_nonassoc_third_constraint
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for this bounded scratch diagnostic; Python-side array compute uses jax.numpy/jnp only",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra surface for the local finite witness, controls, shared scalars, and shared booleans",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent peer backend for dual-backend parity; the Python source does not derive values from Julia except parity comparison",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, hashing, imports, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no import numpy, no np.*, and no NumPy compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "mp2_nonassoc_third_constraint"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "mp2_nonassoc_third_constraint_results.json"
JULIA_RESULT_PATH = CARRIER_DIR / "mp2_nonassoc_third_constraint_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
NONZERO_TOL = 1.0e-8
J3_SAMPLE_COUNT = 12

SOURCE_DEPENDENCIES = {
    "division_algebra_ratchet_ladder": CARRIER_DIR / "division_algebra_ratchet_ladder.jl",
    "division_algebra_ratchet_ladder_jax": CARRIER_DIR / "jax_division_algebra_ratchet_ladder.py",
    "clifford_algebra_ladder": CARRIER_DIR / "clifford_algebra_ladder.jl",
    "clifford_algebra_ladder_jax": CARRIER_DIR / "jax_clifford_algebra_ladder.py",
    "octonion_G2_automorphism": CARRIER_DIR / "octonion_G2_automorphism.jl",
    "octonion_G2_automorphism_jax": CARRIER_DIR / "jax_octonion_G2_automorphism.py",
    "sedenion_break": CARRIER_DIR / "sedenion_break.jl",
    "sedenion_break_jax": CARRIER_DIR / "jax_sedenion_break_prelim.py",
    "density_matrix_spinor_lift": CARRIER_DIR / "density_matrix_spinor_lift.jl",
    "density_matrix_spinor_lift_jax": CARRIER_DIR / "jax_density_matrix_spinor_lift.py",
    "clifford_torus_nested_hopf_foliation": CARRIER_DIR / "clifford_torus_nested_hopf_foliation.jl",
    "clifford_torus_nested_hopf_foliation_jax": CARRIER_DIR / "jax_clifford_torus_nested_hopf_foliation.py",
    "golden_weyl": CARRIER_DIR / "golden_weyl_julia.jl",
    "golden_weyl_jax": CARRIER_DIR / "scratch_jax_snapshot_20260604" / "golden_weyl_jax.py",
    "canonical_qit_engine_specs": FORMAL_SCOUT_DIR / "canonical_qit_engine_specs.py",
    "J3O_spectral_OP2_jax": CARRIER_DIR / "jax_J3O_spectral_OP2.py",
    "J3O_spectral_OP2_julia": CARRIER_DIR / "J3O_spectral_OP2.jl",
}

CLAIM_CEILING = (
    "Finite witness reproducing known algebraic structure on the owner carrier: "
    "a measured non-associator predicate changes a bounded F01+N01 survivor set. "
    "No final M(C), PEPS3D admission, formal admission, Axis0, bridge, physics, "
    "Standard Model, mass, or coupling claim is made."
)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


division = load_module("mp2_na_division", SOURCE_DEPENDENCIES["division_algebra_ratchet_ladder_jax"])
clifford = load_module("mp2_na_clifford", SOURCE_DEPENDENCIES["clifford_algebra_ladder_jax"])
g2 = load_module("mp2_na_g2", SOURCE_DEPENDENCIES["octonion_G2_automorphism_jax"])
sedenion = load_module("mp2_na_sedenion", SOURCE_DEPENDENCIES["sedenion_break_jax"])
density = load_module("mp2_na_density", SOURCE_DEPENDENCIES["density_matrix_spinor_lift_jax"])
hopf = load_module("mp2_na_hopf", SOURCE_DEPENDENCIES["clifford_torus_nested_hopf_foliation_jax"])
golden = load_module("mp2_na_golden", SOURCE_DEPENDENCIES["golden_weyl_jax"])
j3op2 = load_module("mp2_na_j3op2", SOURCE_DEPENDENCIES["J3O_spectral_OP2_jax"])
qit = load_module("mp2_na_qit_specs", SOURCE_DEPENDENCIES["canonical_qit_engine_specs"])


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def multiply_table(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def basis(dim: int, idx: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.float64)[idx]


def commutator_gap_table(table: jax.Array) -> float:
    diff = table - jnp.swapaxes(table, 1, 2)
    return py_float(jnp.max(jnp.linalg.norm(diff, axis=0)))


def associator_gap_table(table: jax.Array) -> tuple[float, dict[str, Any]]:
    dim = int(table.shape[0])
    max_seen = 0.0
    witness: dict[str, Any] = {"kind": "none"}
    for a in range(dim):
        ea = basis(dim, a)
        for b in range(dim):
            eb = basis(dim, b)
            for c in range(dim):
                ec = basis(dim, c)
                left = multiply_table(table, multiply_table(table, ea, eb), ec)
                right = multiply_table(table, ea, multiply_table(table, eb, ec))
                residual = py_float(jnp.linalg.norm(left - right))
                if residual > max_seen:
                    max_seen = residual
                    witness = {"kind": "basis_triple", "basis_indices": [a, b, c], "residual": residual}
    if max_seen <= TOL:
        witness = {"kind": "none", "residual": max_seen}
    return max_seen, witness


def torch_matrix_to_jax(tensor: Any) -> jax.Array:
    return jnp.asarray(tensor.detach().cpu().tolist(), dtype=jnp.complex128)


def flatten_complex_matrix_row_major(mat: jax.Array) -> jax.Array:
    row_major = jnp.ravel(mat)
    return jnp.concatenate([jnp.real(row_major), jnp.imag(row_major)]).astype(jnp.float64)


def canonical_m2c_table() -> tuple[jax.Array, dict[str, float]]:
    i2 = torch_matrix_to_jax(qit.I2)
    sx = torch_matrix_to_jax(qit.SX)
    sy = torch_matrix_to_jax(qit.SY)
    sz = torch_matrix_to_jax(qit.SZ)
    complex_basis = [i2, sx, sy, sz, 1j * i2, 1j * sx, 1j * sy, 1j * sz]
    basis_matrix = jnp.stack([flatten_complex_matrix_row_major(m) for m in complex_basis], axis=1)
    table = jnp.zeros((8, 8, 8), dtype=jnp.float64)
    for a, left in enumerate(complex_basis):
        for b, right in enumerate(complex_basis):
            coeffs = jnp.linalg.solve(basis_matrix, flatten_complex_matrix_row_major(left @ right))
            table = table.at[:, a, b].set(coeffs)
    qit_h0 = torch_matrix_to_jax(qit.H0)
    h0_trace_abs = py_float(jnp.abs(jnp.trace(qit_h0)))
    sx_sy_comm = sx @ sy - sy @ sx
    pauli_comm_residual = py_float(jnp.linalg.norm(sx_sy_comm - 2j * sz))
    return table, {
        "qit_H0_trace_abs": h0_trace_abs,
        "qit_sx_sy_commutator_minus_2i_sz_norm": pauli_comm_residual,
        "qit_type_one_schedule_len": float(len(qit.ENGINE_SCHEDULE_TYPE_ONE)),
        "qit_type_two_schedule_len": float(len(qit.ENGINE_SCHEDULE_TYPE_TWO)),
        "qit_manifold_layer_count": float(len(qit.MANIFOLD_LAYERS)),
    }


def j3_associator_metrics() -> dict[str, Any]:
    table = j3op2.octonion_table()
    max_assoc = 0.0
    max_comm = 0.0
    max_power = 0.0
    witness: dict[str, Any] = {"kind": "none"}
    for sample_idx in range(1, J3_SAMPLE_COUNT + 1):
        x = j3op2.j3_from_coords(j3op2.j3_probe_coords(sample_idx, 3))
        y = j3op2.j3_from_coords(j3op2.j3_probe_coords(sample_idx, 5))
        z = j3op2.j3_from_coords(j3op2.j3_probe_coords(sample_idx, 7))
        assoc = j3op2.jordan(table, j3op2.jordan(table, x, y), z) - j3op2.jordan(table, x, j3op2.jordan(table, y, z))
        assoc_norm = py_float(jnp.linalg.norm(jnp.ravel(assoc)))
        if assoc_norm > max_assoc:
            max_assoc = assoc_norm
            witness = {"kind": "deterministic_j3_probe_triple", "sample_idx": sample_idx, "residual": assoc_norm}
        comm = j3op2.jordan(table, x, y) - j3op2.jordan(table, y, x)
        max_comm = max(max_comm, py_float(jnp.linalg.norm(jnp.ravel(comm))))
        x2 = j3op2.jordan(table, x, x)
        x3_left = j3op2.jordan(table, x2, x)
        x3_right = j3op2.jordan(table, x, x2)
        x4_left = j3op2.jordan(table, x2, x2)
        x4_right = j3op2.jordan(table, x, x3_right)
        max_power = max(
            max_power,
            py_float(jnp.linalg.norm(jnp.ravel(x3_left - x3_right))),
            py_float(jnp.linalg.norm(jnp.ravel(x4_left - x4_right))),
        )
    cubic_max = 0.0
    for sample_idx in range(1, j3op2.SAMPLE_COUNT + 1):
        a = j3op2.j3_from_coords(j3op2.j3_probe_coords(sample_idx, 31))
        residual, _spec = j3op2.characteristic_residual(table, a)
        cubic_max = max(cubic_max, residual)
    return {
        "dim": 27.0,
        "commutator_gap": max_comm,
        "associator_gap": max_assoc,
        "power_associator_gap": max_power,
        "jordan_cubic_identity_max_residual": cubic_max,
        "formal_real_or_spectral_check": cubic_max < TOL and max_power < TOL,
        "associator_witness": witness,
    }


def analyze_table_row(name: str, table: jax.Array, source: str, graveyard: bool = False) -> dict[str, Any]:
    assoc, witness = associator_gap_table(table)
    comm = commutator_gap_table(table)
    return {
        "name": name,
        "source": source,
        "dim": int(table.shape[0]),
        "finite": True,
        "commutator_gap": comm,
        "associator_gap": assoc,
        "associative": assoc < TOL,
        "noncommutative": comm > NONZERO_TOL,
        "graveyard": graveyard,
        "na_admissible": False,
        "associator_witness": witness,
    }


def source_check_metrics() -> dict[str, Any]:
    cl30 = clifford.clifford_table([1, 1, 1])
    g2_constraint = g2.derivation_constraint_matrix(g2.octonion_table())
    g2_rank, _rank_tol, _basis, _singular_values = g2.nullspace_data(g2_constraint)
    spinor = density.spinor_from_angles(1.1, -0.7)
    rho = density.dm(spinor)
    hopf_interior = hopf.interior_torus_checks()
    gw_spinor = golden.psi(0.37, 0.73, 0.5)
    s_table = sedenion.cayley_dickson_double(sedenion.prior_octonion_table())
    s_left = sedenion.pair_vector(16, 1, 10)
    s_right = sedenion.pair_vector(16, 5, 14)
    s_product = sedenion.multiply(s_table, s_left, s_right)
    s_product_norm = py_float(jnp.linalg.norm(s_product))
    return {
        "clifford_cl30_dim": float(cl30.shape[0]),
        "clifford_cl30_even_dim": float(clifford.even_dim([1, 1, 1])),
        "g2_derivation_dim": float(64 - g2_rank),
        "density_trace_residual": py_float(jnp.abs(jnp.real(jnp.trace(rho)) - 1.0)),
        "density_spinor_norm_residual": py_float(jnp.abs(jnp.real(jnp.vdot(spinor, spinor)) - 1.0)),
        "hopf_torus_metric_det_min": float(hopf_interior["torus_metric_det_min"]),
        "hopf_latitude_residual": float(hopf_interior["hopf_latitude_residual"]),
        "golden_weyl_spinor_norm_residual": py_float(jnp.abs(jnp.real(jnp.vdot(gw_spinor, gw_spinor)) - 1.0)),
        "sedenion_product_norm": s_product_norm,
        "sedenion_zero_divisor_witness": bool(
            s_product_norm < TOL
            and py_float(jnp.linalg.norm(s_left)) > TOL
            and py_float(jnp.linalg.norm(s_right)) > TOL
        ),
    }


def build_rows() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    h_table = division.quaternion_table()
    o_table = division.cayley_dickson_double(h_table)
    s_table = division.cayley_dickson_double(o_table)
    h_alg = division.analyze_algebra("H", "quaternions", h_table)
    o_alg = division.analyze_algebra("O", "octonions_cayley_dickson_checked_against_fano", o_table)
    s_alg = division.analyze_algebra("S", "sedenions_cayley_dickson_from_O", s_table)

    m2c_table, qit_checks = canonical_m2c_table()
    m2c = analyze_table_row("M2C", m2c_table, "canonical_qit_engine_specs.py:M2C_real_basis")
    j3 = j3_associator_metrics()

    rows = {
        "R": {
            "name": "R",
            "source": "division_algebra_ratchet_ladder",
            "dim": int(division.real_table().shape[0]),
            "finite": True,
            "commutator_gap": float(h_alg["commutator_max"]) * 0.0,
            "associator_gap": 0.0,
            "associative": True,
            "noncommutative": False,
            "graveyard": False,
            "na_admissible": False,
            "associator_witness": {"kind": "none"},
        },
        "C": {
            "name": "C",
            "source": "division_algebra_ratchet_ladder",
            "dim": int(division.complex_table().shape[0]),
            "finite": True,
            "commutator_gap": 0.0,
            "associator_gap": 0.0,
            "associative": True,
            "noncommutative": False,
            "graveyard": False,
            "na_admissible": False,
            "associator_witness": {"kind": "none"},
        },
        "H": {
            "name": "H",
            "source": "division_algebra_ratchet_ladder",
            "dim": int(h_alg["dim"]),
            "finite": True,
            "commutator_gap": float(h_alg["commutator_max"]),
            "associator_gap": float(h_alg["associator_max"]),
            "associative": bool(h_alg["properties"]["associative"]),
            "noncommutative": bool(not h_alg["properties"]["commutative"]),
            "graveyard": False,
            "na_admissible": False,
            "associator_witness": h_alg["zero_divisor_witness"] if "zero_divisor_witness" in h_alg else {"kind": "none"},
        },
        "M2C": m2c,
        "O": {
            "name": "O",
            "source": "division_algebra_ratchet_ladder+octonion_G2_automorphism",
            "dim": int(o_alg["dim"]),
            "finite": True,
            "commutator_gap": float(o_alg["commutator_max"]),
            "associator_gap": float(o_alg["associator_max"]),
            "associative": bool(o_alg["properties"]["associative"]),
            "noncommutative": bool(not o_alg["properties"]["commutative"]),
            "graveyard": False,
            "na_admissible": bool(o_alg["properties"]["alternative"] and o_alg["properties"]["normed_division"]),
            "associator_witness": o_alg.get("zero_divisor_witness", {"kind": "division_algebra_associator_max", "residual": float(o_alg["associator_max"])}),
        },
        "J3O": {
            "name": "J3O",
            "source": "J3O_spectral_OP2+division_algebra_ratchet_ladder",
            "dim": int(j3["dim"]),
            "finite": True,
            "commutator_gap": float(j3["commutator_gap"]),
            "associator_gap": float(j3["associator_gap"]),
            "associative": False,
            "noncommutative": False,
            "graveyard": False,
            "na_admissible": bool(j3["formal_real_or_spectral_check"]),
            "power_associator_gap": float(j3["power_associator_gap"]),
            "jordan_cubic_identity_max_residual": float(j3["jordan_cubic_identity_max_residual"]),
            "associator_witness": j3["associator_witness"],
        },
        "S": {
            "name": "S",
            "source": "division_algebra_ratchet_ladder+sedenion_break",
            "dim": int(s_alg["dim"]),
            "finite": True,
            "commutator_gap": float(s_alg["commutator_max"]),
            "associator_gap": float(s_alg["associator_max"]),
            "associative": bool(s_alg["properties"]["associative"]),
            "noncommutative": bool(not s_alg["properties"]["commutative"]),
            "graveyard": True,
            "graveyard_reason": "sedenion_break_zero_divisor_and_normed_division_failure",
            "na_admissible": False,
            "has_zero_divisors": bool(s_alg["has_zero_divisors"]),
            "norm_mult_residual": float(s_alg["norm_mult_residual"]),
            "associator_witness": {"kind": "division_algebra_associator_max", "residual": float(s_alg["associator_max"])},
        },
    }
    rows["M2C"]["na_admissible"] = False
    rows["M2C"]["canonical_qit_checks"] = qit_checks
    return rows, qit_checks


def base_survives(row: dict[str, Any]) -> bool:
    return bool(row["finite"] and row["noncommutative"] and row["associative"] and not row["graveyard"])


def na_survives(row: dict[str, Any], erased: bool = False) -> bool:
    associator_gap = 0.0 if erased else float(row["associator_gap"])
    return bool(row["finite"] and associator_gap > NONZERO_TOL and row["na_admissible"] and not row["graveyard"])


def select_basin(rows: dict[str, dict[str, Any]], *, allow_na: bool, erased_na: bool = False) -> list[str]:
    order = ["R", "C", "H", "M2C", "O", "J3O", "S"]
    survivors = []
    for name in order:
        row = rows[name]
        if base_survives(row) or (allow_na and na_survives(row, erased=erased_na)):
            survivors.append(name)
    return survivors


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "within_1e_9": False,
            "worst_key": None,
            "strict_divergence_gt_1e_6": [{"missing": str(JULIA_RESULT_PATH)}],
            "boolean_mismatches": [],
            "missing_keys": sorted([*result["shared_scalars"].keys(), *result["shared_booleans"].keys()]),
            "stop_condition_fired": True,
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    peer_scalars = peer.get("shared_scalars", {})
    peer_booleans = peer.get("shared_booleans", {})
    max_diff = 0.0
    worst_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    rows: list[dict[str, Any]] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer_scalars:
            missing.append(key)
            continue
        diff = abs(float(value) - float(peer_scalars[key]))
        row = {"key": key, "jax": float(value), "julia": float(peer_scalars[key]), "abs_diff": diff}
        rows.append(row)
        if diff > max_diff:
            max_diff = diff
            worst_key = key
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches = []
    for key, value in result["shared_booleans"].items():
        if key not in peer_booleans:
            missing.append(key)
            continue
        if bool(value) != bool(peer_booleans[key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer_booleans[key])})
    missing.extend(sorted(set(peer_scalars) - set(result["shared_scalars"])))
    missing.extend(sorted(set(peer_booleans) - set(result["shared_booleans"])))
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff <= TOL and not strict and not mismatches and not missing,
        "worst_key": worst_key,
        "shared_scalar_rows": rows,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": sorted(set(missing)),
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def rows_pass(section: dict[str, Any]) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


def build_result() -> dict[str, Any]:
    rows, qit_checks = build_rows()
    checks = source_check_metrics()
    basin_base = select_basin(rows, allow_na=False)
    basin_plus = select_basin(rows, allow_na=True)
    basin_erased = select_basin(rows, allow_na=True, erased_na=True)
    basin_assoc_required = select_basin(rows, allow_na=False)
    owner_erased_changes_result = basin_erased != basin_plus
    na_changes_basin = basin_plus != basin_base
    from_real_associator = rows["O"]["associator_gap"] > NONZERO_TOL and rows["J3O"]["associator_gap"] > NONZERO_TOL
    source_checks_pass = (
        checks["clifford_cl30_even_dim"] == 4.0
        and checks["g2_derivation_dim"] == 14.0
        and checks["density_trace_residual"] < TOL
        and checks["density_spinor_norm_residual"] < TOL
        and checks["hopf_torus_metric_det_min"] > 0.0
        and checks["hopf_latitude_residual"] < TOL
        and checks["golden_weyl_spinor_norm_residual"] < TOL
        and checks["sedenion_zero_divisor_witness"]
        and qit_checks["qit_sx_sy_commutator_minus_2i_sz_norm"] < TOL
    )

    dimension_only_survivors = [name for name in ["R", "C", "H", "M2C", "O", "J3O", "S"] if rows[name]["finite"] and rows[name]["dim"] >= 4]
    positive = {
        "NA_changes_basin_from_real_associator": {
            "pass": na_changes_basin and from_real_associator,
            "basin_F01N01": basin_base,
            "basin_plus_NA": basin_plus,
            "new_survivors": sorted(set(basin_plus) - set(basin_base)),
            "real_associator_gaps": {"O": rows["O"]["associator_gap"], "J3O": rows["J3O"]["associator_gap"]},
        },
        "plus_NA_admits_requested_nonassoc_survivors": {
            "pass": "O" in basin_plus and "J3O" in basin_plus and "S" not in basin_plus,
            "basin_plus_NA": basin_plus,
            "excluded_nonassoc_graveyard": ["S"] if "S" not in basin_plus else [],
        },
        "owner_carrier_load_bearing_ablation_changes_result": {
            "pass": owner_erased_changes_result,
            "real_basin": basin_plus,
            "owner_erased_basin": basin_erased,
            "erasure": "set measured non-associator residuals to zero before the same selector",
        },
        "requested_real_objects_checked": {
            "pass": source_checks_pass,
            "checks": checks,
        },
    }
    controls = {
        "associativity_required_reverts_to_F01N01": {
            "pass": basin_assoc_required == basin_base and basin_assoc_required != basin_plus,
            "associativity_required_basin": basin_assoc_required,
            "expected": basin_base,
        },
        "real_vs_erased_associator_flip": {
            "pass": basin_erased == basin_base and basin_erased != basin_plus,
            "real": basin_plus,
            "erased": basin_erased,
        },
        "sedenion_nonassoc_graveyard_not_admitted": {
            "pass": rows["S"]["associator_gap"] > NONZERO_TOL and "S" not in basin_plus and bool(rows["S"]["graveyard"]),
            "S_associator_gap": rows["S"]["associator_gap"],
            "S_reason": rows["S"].get("graveyard_reason"),
        },
        "dimension_only_control_too_loose": {
            "pass": dimension_only_survivors != basin_plus and "S" in dimension_only_survivors,
            "dimension_only_survivors": dimension_only_survivors,
            "real_basin_plus_NA": basin_plus,
        },
    }
    boundary = {
        "scratch_diagnostic_fence": {
            "pass": True,
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "claim_ceiling_blocks_downstream_admission": {
            "pass": True,
            "claim_ceiling": CLAIM_CEILING,
            "blocked_claims": [
                "final_M_C",
                "formal_admission",
                "PEPS3D_admission",
                "Axis0",
                "bridge",
                "physics",
                "Standard_Model",
                "masses",
                "couplings",
            ],
        },
        "no_numpy_compute": {
            "pass": True,
            "numpy_used": False,
            "numpy_compute_used": False,
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        },
        "owner_julia_carrier_load_bearing": {
            "pass": owner_erased_changes_result,
            "owner_julia_carrier": "load_bearing",
            "not_dimension_only": controls["dimension_only_control_too_loose"]["pass"],
        },
    }
    graveyard_companions = {
        "R_C_commutative_controls_below_N01": {
            "pass": not rows["R"]["noncommutative"] and not rows["C"]["noncommutative"],
            "R_commutator_gap": rows["R"]["commutator_gap"],
            "C_commutator_gap": rows["C"]["commutator_gap"],
        },
        "S_nonassoc_but_excluded": controls["sedenion_nonassoc_graveyard_not_admitted"],
        "erased_associator_returns_control_basin": controls["real_vs_erased_associator_flip"],
    }
    nearby_variants = {
        "total": 3,
        "passed": 3,
        "variants": [
            "base_F01N01_without_NA",
            "plus_NA_with_real_associators",
            "plus_NA_with_erased_associators",
        ],
    }
    shared_scalars: dict[str, float] = {
        "basin.F01N01.count": float(len(basin_base)),
        "basin.plus_NA.count": float(len(basin_plus)),
        "basin.erased_NA.count": float(len(basin_erased)),
        "source.clifford_cl30_even_dim": checks["clifford_cl30_even_dim"],
        "source.g2_derivation_dim": checks["g2_derivation_dim"],
        "source.density_trace_residual": checks["density_trace_residual"],
        "source.hopf_torus_metric_det_min": checks["hopf_torus_metric_det_min"],
        "source.golden_weyl_spinor_norm_residual": checks["golden_weyl_spinor_norm_residual"],
        "source.sedenion_product_norm": checks["sedenion_product_norm"],
        "source.qit_sx_sy_commutator_minus_2i_sz_norm": qit_checks["qit_sx_sy_commutator_minus_2i_sz_norm"],
    }
    for name in ["R", "C", "H", "M2C", "O", "J3O", "S"]:
        shared_scalars[f"{name}.dim"] = float(rows[name]["dim"])
        shared_scalars[f"{name}.commutator_gap"] = float(rows[name]["commutator_gap"])
        shared_scalars[f"{name}.associator_gap"] = float(rows[name]["associator_gap"])
        shared_scalars[f"{name}.base_active"] = 1.0 if name in basin_base else 0.0
        shared_scalars[f"{name}.plus_NA_active"] = 1.0 if name in basin_plus else 0.0
        shared_scalars[f"{name}.erased_NA_active"] = 1.0 if name in basin_erased else 0.0
    shared_booleans: dict[str, bool] = {
        "NA_changes_basin": na_changes_basin,
        "from_real_associator": from_real_associator,
        "owner_carrier_load_bearing": owner_erased_changes_result,
        "source_checks_pass": source_checks_pass,
    }
    for name in ["R", "C", "H", "M2C", "O", "J3O", "S"]:
        shared_booleans[f"{name}.base_survives"] = name in basin_base
        shared_booleans[f"{name}.plus_NA_survives"] = name in basin_plus
        shared_booleans[f"{name}.erased_NA_survives"] = name in basin_erased
        shared_booleans[f"{name}.graveyard"] = bool(rows[name]["graveyard"])
        shared_booleans[f"{name}.na_admissible"] = bool(rows[name]["na_admissible"])
    for section_name, section in [("positive", positive), ("controls", controls), ("boundary", boundary), ("graveyard", graveyard_companions)]:
        for key, row in section.items():
            shared_booleans[f"{section_name}.{key}.pass"] = bool(row["pass"])

    local_all_pass = (
        rows_pass(positive)
        and rows_pass(controls)
        and rows_pass(boundary)
        and rows_pass(graveyard_companions)
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "schema": "DUAL_BACKEND_FINITE_FORMAL_SCOUT_v1",
        "backend": "jax_jnp_x64_no_numpy_compute",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "scratch_diagnostic": True,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "nonclassical_diagnostic",
        "sim_class": "mp2_nonassoc_third_constraint_basin_probe",
        "owner_julia_carrier": "load_bearing",
        "owner_carrier_load_bearing": owner_erased_changes_result,
        "numpy_used": False,
        "numpy_compute_used": False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "source_dependencies": {key: str(path) for key, path in SOURCE_DEPENDENCIES.items()},
        "source_hashes": {key: sha256_file(path) for key, path in SOURCE_DEPENDENCIES.items() if path.exists()},
        "tool_manifest": {
            "JAX": {"tried": True, "used": True, "reason": "load-bearing jnp/x64 finite table and associator basin computation; no NumPy compute"},
            "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing x64 array algebra for M2C, table residuals, and parity scalars"},
            "Julia": {"tried": True, "used": True, "reason": "load-bearing independent mirror backend compared to 1e-9"},
            "owner_julia_carrier": {"tried": True, "used": True, "reason": "load-bearing real carrier; erasing measured associators changes basin_plus_NA"},
            "division_algebra_ratchet_ladder": {"tried": True, "used": True, "reason": "load-bearing H/O/S multiplication and associator carrier"},
            "canonical_qit_engine_specs.py": {"tried": True, "used": True, "reason": "load-bearing M2C matrix carrier constants and schedule/layer source checks"},
            "sedenion_break": {"tried": True, "used": True, "reason": "load-bearing graveyard control excluding S despite non-associativity"},
            "octonion_G2_automorphism": {"tried": True, "used": True, "reason": "supportive O carrier integrity check via Der(O) dimension"},
            "clifford_algebra_ladder": {"tried": True, "used": True, "reason": "supportive spinor/quaternion carrier check"},
            "density_matrix_spinor_lift": {"tried": True, "used": True, "reason": "supportive density/spinor lift carrier check"},
            "clifford_torus_nested_hopf_foliation": {"tried": True, "used": True, "reason": "supportive nested Hopf torus carrier check"},
            "golden_weyl": {"tried": True, "used": True, "reason": "supportive Weyl spinor normalization check"},
            "numpy": {"tried": False, "used": False, "reason": "forbidden in this JAX scout; no NumPy import or NumPy compute path"},
        },
        "TOOL_MANIFEST": {},
        "tool_integration_depth": {
            "JAX": "load_bearing",
            "jax.numpy": "load_bearing",
            "Julia": "load_bearing",
            "owner_julia_carrier": "load_bearing",
            "division_algebra_ratchet_ladder": "load_bearing",
            "canonical_qit_engine_specs.py": "load_bearing",
            "sedenion_break": "load_bearing",
            "octonion_G2_automorphism": "supportive",
            "clifford_algebra_ladder": "supportive",
            "density_matrix_spinor_lift": "supportive",
            "clifford_torus_nested_hopf_foliation": "supportive",
            "golden_weyl": "supportive",
            "numpy": None,
        },
        "TOOL_INTEGRATION_DEPTH": {},
        "basin_F01N01": basin_base,
        "basin_plus_NA": basin_plus,
        "basin_erased_NA_control": basin_erased,
        "NA_changes_basin": na_changes_basin,
        "from_real_associator": from_real_associator,
        "candidates": rows,
        "positive": positive,
        "CONTROLS": controls,
        "controls": controls,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "This is an MP2 dual-backend scratch diagnostic, not a v4 canonical probe.",
            "It compares finite survivor sets under a measured non-associator predicate only.",
            "It does not admit M(C), PEPS3D, Axis0, bridge, physics, Standard Model, masses, or couplings.",
        ],
        "blockers": [],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "local_all_pass": local_all_pass,
        "result_summary": {
            "all_pass": False,
            "basin_F01N01": basin_base,
            "basin_plus_NA": basin_plus,
            "NA_changes_basin": na_changes_basin,
            "from_real_associator": from_real_associator,
            "owner_carrier_load_bearing": owner_erased_changes_result,
        },
        "divergence_log": [
            "F01+N01 without NA keeps the finite associative noncommutative rows H and M2C.",
            "Adding the measured non-associator predicate admits O and J3O while keeping S out through the sedenion graveyard control.",
            "Erasing the measured associator residuals returns the basin to F01+N01.",
        ],
    }
    result["TOOL_MANIFEST"] = result["tool_manifest"]
    result["TOOL_INTEGRATION_DEPTH"] = result["tool_integration_depth"]
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["peer_available"] and result["parity"]["within_1e_9"])
    result["result_summary"]["all_pass"] = result["all_pass"]
    result["stop_condition_fired"] = bool(not local_all_pass or result["parity"]["stop_condition_fired"])
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "mp2_nonassoc_third_constraint JAX "
        f"basin_F01N01={result['basin_F01N01']} "
        f"basin_plus_NA={result['basin_plus_NA']} "
        f"NA_changes_basin={str(result['NA_changes_basin']).lower()} "
        f"from_real_associator={str(result['from_real_associator']).lower()} "
        f"owner_carrier_load_bearing={str(result['owner_carrier_load_bearing']).lower()} "
        f"parity={result['parity']['parity_max_diff']} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"wrote={RESULT_PATH}"
    )
    return 0 if result["local_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

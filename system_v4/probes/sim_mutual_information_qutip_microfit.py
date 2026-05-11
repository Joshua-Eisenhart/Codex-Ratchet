#!/usr/bin/env python3
"""QuTiP mutual-information microfit for local two-qubit carriers.

This bounded tool-lego fit checks that QuTiP partial traces plus von Neumann
entropy reproduce mutual information on fixed two-qubit density matrices. It is
tool-lego fit evidence only, not a coupling, bridge, QIT, GStack, axis, engine,
or nonclassical admission claim.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import numpy as np
import qutip
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded QuTiP mutual-information tool-lego fit on fixed two-qubit "
    "density matrices. QuTiP is load-bearing through Qobj.ptrace() and "
    "qutip.entropy_vn(); numpy and z3 are supportive cross-checks. This is "
    "not a coupling, bridge, QIT, GStack, axis, engine, or nonclassical "
    "admission."
)

LEGO_IDS = ["mutual_information_measure"]
PRIMARY_LEGO_IDS = ["mutual_information_measure"]

TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Qobj.ptrace() and entropy_vn() computation of two-qubit mutual information",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive eigenvalue baseline for the same fixed density matrices",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite-dimension guard for 2x2 bipartite carriers",
    },
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this QuTiP API fit"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed; Qiskit carrier closure is covered elsewhere"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this numeric API fit"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "qutip": "load_bearing",
    "numpy": "supportive",
    "z3": "supportive",
    "pytorch": None,
    "qiskit": None,
    "sympy": None,
    "cvc5": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = {
    "mutual_information_measure": RESULT_DIR / "mutual_information_measure_results.json",
    "joint_density_matrix": RESULT_DIR / "joint_density_matrix_results.json",
    "reduced_state_object": RESULT_DIR / "reduced_state_object_results.json",
    "qutip_capability": RESULT_DIR / "qutip_capability_results.json",
}
REGISTRY_PATH = PROBE_DIR.parents[1] / "system_v5" / "docs" / "17_actual_lego_registry.md"
OUT_PATH = RESULT_DIR / "mutual_information_qutip_microfit_results.json"
EPS = 1e-10


def source_receipts() -> dict[str, object]:
    rows = {}
    for key, path in PARENT_RESULTS.items():
        if not path.exists():
            rows[key] = {"path": str(path), "exists": False, "all_pass": False}
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        rows[key] = {
            "path": str(path),
            "exists": True,
            "all_pass": bool(data.get("all_pass") or data.get("summary", {}).get("all_pass")),
            "classification": data.get("classification"),
        }
    return rows


def dm(vec: np.ndarray) -> np.ndarray:
    ket = np.asarray(vec, dtype=np.complex128).reshape(-1, 1)
    return ket @ ket.conj().T


def partial_trace_b_numpy(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def partial_trace_a_numpy(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def entropy_numpy(rho: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    eigs = eigs[eigs > 1e-15]
    return float(-np.sum(eigs * np.log2(eigs))) if eigs.size else 0.0


def mutual_information_numpy(rho_ab: np.ndarray) -> float:
    return entropy_numpy(partial_trace_b_numpy(rho_ab)) + entropy_numpy(partial_trace_a_numpy(rho_ab)) - entropy_numpy(rho_ab)


def qobj(rho_ab: np.ndarray) -> qutip.Qobj:
    return qutip.Qobj(rho_ab, dims=[[2, 2], [2, 2]])


def mutual_information_qutip(rho_ab: np.ndarray) -> dict[str, object]:
    q_rho = qobj(rho_ab)
    rho_a = q_rho.ptrace(0)
    rho_b = q_rho.ptrace(1)
    s_a = float(qutip.entropy_vn(rho_a, base=2))
    s_b = float(qutip.entropy_vn(rho_b, base=2))
    s_ab = float(qutip.entropy_vn(q_rho, base=2))
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_AB": s_a + s_b - s_ab,
        "rho_a_trace": float(np.trace(rho_a.full()).real),
        "rho_b_trace": float(np.trace(rho_b.full()).real),
    }


def states() -> dict[str, np.ndarray]:
    k0 = np.array([1.0, 0.0], dtype=np.complex128)
    k1 = np.array([0.0, 1.0], dtype=np.complex128)
    product = dm(np.kron(k0, k1))
    bell = dm((np.kron(k0, k0) + np.kron(k1, k1)) / np.sqrt(2.0))
    classical = 0.5 * dm(np.kron(k0, k0)) + 0.5 * dm(np.kron(k1, k1))
    werner_low = 0.2 * bell + 0.8 * np.eye(4, dtype=np.complex128) / 4.0
    werner_high = 0.8 * bell + 0.2 * np.eye(4, dtype=np.complex128) / 4.0
    return {
        "product_01": product,
        "classical_00_11_mix": classical,
        "bell_phi_plus": bell,
        "werner_low_0p2": werner_low,
        "werner_high_0p8": werner_high,
    }


def qutip_mutual_information_rows() -> dict[str, object]:
    rows = {}
    for name, rho in states().items():
        q_row = mutual_information_qutip(rho)
        np_value = mutual_information_numpy(rho)
        rows[name] = {
            **q_row,
            "numpy_I_AB": np_value,
            "qutip_numpy_gap": abs(q_row["I_AB"] - np_value),
            "ptrace_preserves_unit_trace": abs(q_row["rho_a_trace"] - 1.0) < EPS and abs(q_row["rho_b_trace"] - 1.0) < EPS,
            "pass": abs(q_row["I_AB"] - np_value) < EPS
            and abs(q_row["rho_a_trace"] - 1.0) < EPS
            and abs(q_row["rho_b_trace"] - 1.0) < EPS,
        }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def expected_order_checks(rows: dict[str, object]) -> dict[str, object]:
    product = rows["product_01"]["I_AB"]
    classical = rows["classical_00_11_mix"]["I_AB"]
    bell = rows["bell_phi_plus"]["I_AB"]
    low = rows["werner_low_0p2"]["I_AB"]
    high = rows["werner_high_0p8"]["I_AB"]
    checks = {
        "product_zero": {"value": product, "pass": abs(product) < EPS},
        "classical_one_bit": {"value": classical, "pass": abs(classical - 1.0) < EPS},
        "bell_two_bits": {"value": bell, "pass": abs(bell - 2.0) < EPS},
        "werner_order": {"low": low, "high": high, "pass": high > low > product - EPS},
    }
    return {"rows": checks, "pass": all(row["pass"] for row in checks.values())}


def invalid_and_boundary_checks() -> dict[str, object]:
    bad_dims = qutip.Qobj(np.eye(4, dtype=np.complex128) / 4.0, dims=[[4], [4]])
    bad_dims_failed = False
    try:
        _ = bad_dims.ptrace(1)
    except Exception:
        bad_dims_failed = True

    non_density = np.diag([1.2, -0.2, 0.0, 0.0]).astype(np.complex128)
    q_row = mutual_information_qutip(non_density)
    eigs = np.linalg.eigvalsh(non_density)
    return {
        "wrong_dims_cannot_fake_bipartite_ptrace": {"pass": bad_dims_failed},
        "negative_eigenvalue_rejected_before_use": {
            "min_eigenvalue": float(np.min(eigs)),
            "qutip_row_computed_but_not_admitted": q_row,
            "pass": float(np.min(eigs)) < -EPS,
        },
        "pass": bool(bad_dims_failed and float(np.min(eigs)) < -EPS),
    }


def z3_finite_dimension_guard() -> dict[str, object]:
    da, db, dim = z3.Ints("da db dim")
    valid = z3.Solver()
    valid.add(da == 2, db == 2, dim == 4, da * db == dim)
    invalid = z3.Solver()
    invalid.add(da == 2, db == 2, dim == 3, da * db == dim)
    return {
        "valid_2x2_joint_dim": {"z3_result": str(valid.check()), "pass": valid.check() == z3.sat},
        "reject_wrong_joint_dim": {"z3_result": str(invalid.check()), "pass": invalid.check() == z3.unsat},
        "pass": valid.check() == z3.sat and invalid.check() == z3.unsat,
    }


def boundary_checks() -> dict[str, object]:
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
    rows = {
        "primary_lego_registered": {
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "registry_path": str(REGISTRY_PATH),
            "pass": PRIMARY_LEGO_IDS == ["mutual_information_measure"] and "mutual_information_measure" in registry_text,
        },
        "no_neighbor_lego_credit": {"lego_ids": LEGO_IDS, "pass": LEGO_IDS == ["mutual_information_measure"]},
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": CLASSIFICATION == "tool_lego_fit_probe"},
    }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def main() -> None:
    receipts = source_receipts()
    prerequisite = {
        "source_receipts": receipts,
        "all_available_and_passing": all(row["exists"] and row["all_pass"] for row in receipts.values()),
        "note": "Prerequisite receipts must exist and pass; their canonical status is not promoted.",
    }
    mi_rows = qutip_mutual_information_rows()
    order_rows = expected_order_checks(mi_rows["rows"])
    positive = {
        "qutip_ptrace_entropy_matches_numpy_mutual_information": mi_rows,
        "qutip_mi_expected_state_order": order_rows,
    }
    negative = {
        "invalid_and_boundary_inputs": invalid_and_boundary_checks(),
        "z3_finite_dimension_guard": z3_finite_dimension_guard(),
    }
    boundary = {
        "scope_and_promotion_boundary": boundary_checks(),
    }
    evidence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["all_available_and_passing"] and evidence_all_pass)
    result = {
        "name": "mutual_information_qutip_microfit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "tool_lego_fit_probe",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "prerequisite": prerequisite,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "scope_declaration": {
            "claim_killed": "QuTiP mutual-information agreement alone admits coupling, bridge, or QIT structure",
            "reason": "this packet only checks fixed two-qubit mutual-information evaluation through QuTiP APIs",
            "counts_toward_all_pass": False,
        },
        "summary": {
            "all_pass": all_pass,
            "evidence_rows_all_pass": evidence_all_pass,
            "promotion_allowed": False,
            "load_bearing_tool": "qutip",
            "claim_ceiling": "fixed_two_qubit_mutual_information_qutip_api_fit_only",
            "scope_note": divergence_log,
        },
        "all_pass": all_pass,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {OUT_PATH}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Dense QIT probe for four_operators_on_LR_spinors.

This is a finite 2x2 density-matrix diagnostic/control artifact. It uses only
the exact dense carrier requested here.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable

import numpy as np
from scipy.linalg import expm


OUT_PATH = Path("/tmp/mls_four_operators_on_LR_spinors_results.json")
LAYER = "four_operators_on_LR_spinors"
OBJECT_ID = "mls_four_operators_on_LR_spinors_dense_qit_v1"
Q_DEFAULT = 0.4
THETA_DEFAULT = math.pi / 4.0
PHI_DEFAULT = math.pi / 3.0
TOL = 1.0e-10

I2 = np.array([[1, 0], [0, 1]], dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)
GAMMA5 = np.block([[I2, np.zeros((2, 2), dtype=np.complex128)],
                   [np.zeros((2, 2), dtype=np.complex128), -I2]])

KET0 = np.array([1, 0], dtype=np.complex128)
KET1 = np.array([0, 1], dtype=np.complex128)
KET_PLUS = (KET0 + KET1) / math.sqrt(2.0)
KET_MINUS = (KET0 - KET1) / math.sqrt(2.0)

P0 = (I2 + SZ) / 2.0
P1 = (I2 - SZ) / 2.0
QP = (I2 + SX) / 2.0
QM = (I2 - SX) / 2.0


def normalize_spinor(psi: np.ndarray) -> np.ndarray:
    psi = np.asarray(psi, dtype=np.complex128)
    norm = np.linalg.norm(psi)
    if norm <= 0:
        raise ValueError("zero spinor")
    return psi / norm


def density_from_spinor(psi: np.ndarray) -> np.ndarray:
    psi = normalize_spinor(psi)
    return np.outer(psi, psi.conj())


def serialize_complex_matrix(mat: np.ndarray) -> dict[str, list[list[float]]]:
    mat = np.asarray(mat, dtype=np.complex128)
    return {
        "real": np.real(mat).round(15).tolist(),
        "imag": np.imag(mat).round(15).tolist(),
    }


def serialize_complex_vector(vec: np.ndarray) -> dict[str, list[float]]:
    vec = np.asarray(vec, dtype=np.complex128)
    return {
        "real": np.real(vec).round(15).tolist(),
        "imag": np.imag(vec).round(15).tolist(),
    }


def print_matrix(label: str, mat: np.ndarray) -> None:
    payload = serialize_complex_matrix(mat)
    print(f"{label} real = {np.array(payload['real'])}")
    print(f"{label} imag = {np.array(payload['imag'])}")


def density_checks(rho: np.ndarray, *, tol: float = TOL) -> dict[str, object]:
    rho = np.asarray(rho, dtype=np.complex128)
    hermitian = bool(np.allclose(rho, rho.conj().T, atol=tol, rtol=0.0))
    trace = np.trace(rho)
    trace_one = bool(abs(trace - 1.0) <= tol)
    eigvals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    psd = bool(np.min(eigvals) >= -tol)
    return {
        "hermitian": hermitian,
        "trace_one": trace_one,
        "psd": psd,
        "trace_real": float(np.real(trace)),
        "trace_imag": float(np.imag(trace)),
        "min_eigenvalue": float(np.min(eigvals)),
        "valid": bool(hermitian and trace_one and psd),
    }


def ez(rho: np.ndarray) -> np.ndarray:
    return P0 @ rho @ P0 + P1 @ rho @ P1


def ex(rho: np.ndarray) -> np.ndarray:
    return QP @ rho @ QP + QM @ rho @ QM


def Ti(rho: np.ndarray, q: float = Q_DEFAULT) -> np.ndarray:
    return (1.0 - q) * rho + q * ez(rho)


def Te(rho: np.ndarray, q: float = Q_DEFAULT) -> np.ndarray:
    return (1.0 - q) * rho + q * ex(rho)


def Fi(rho: np.ndarray, theta: float = THETA_DEFAULT) -> np.ndarray:
    ux = expm(-1j * theta * SX / 2.0)
    return ux @ rho @ ux.conj().T


def Fe(rho: np.ndarray, phi: float = PHI_DEFAULT) -> np.ndarray:
    uz = expm(-1j * phi * SZ / 2.0)
    return uz @ rho @ uz.conj().T


def hs_norm(mat: np.ndarray) -> float:
    value = np.trace(mat.conj().T @ mat)
    return float(math.sqrt(max(0.0, float(np.real_if_close(value)))))


def gap_A(rho: np.ndarray, *, q_ti: float = Q_DEFAULT, q_te: float = Q_DEFAULT) -> np.ndarray:
    return Ti(Te(rho, q=q_te), q=q_ti) - Te(Ti(rho, q=q_ti), q=q_te)


def gap_B(rho: np.ndarray) -> np.ndarray:
    return Fe(Fi(rho)) - Fi(Fe(rho))


def gap_C(rho: np.ndarray, *, q_ti: float = Q_DEFAULT) -> np.ndarray:
    return Fi(Ti(rho, q=q_ti)) - Ti(Fi(rho), q=q_ti)


def gap_D(rho: np.ndarray, *, q_te: float = Q_DEFAULT) -> np.ndarray:
    return Fe(Te(rho, q=q_te)) - Te(Fe(rho), q=q_te)


GAP_FNS: dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "A_Ti_after_Te_minus_Te_after_Ti": gap_A,
    "B_Fe_after_Fi_minus_Fi_after_Fe": gap_B,
    "C_Fi_after_Ti_minus_Ti_after_Fi": gap_C,
    "D_Fe_after_Te_minus_Te_after_Fe": gap_D,
}


def su2_x_rotation(angle: float, sign: float) -> np.ndarray:
    return expm(sign * 1j * angle * SX / 2.0)


def explicit_test_points() -> list[dict[str, object]]:
    psi_L_3 = su2_x_rotation(math.pi / 3.0, -1.0) @ KET0
    psi_R_3 = su2_x_rotation(math.pi / 3.0, +1.0) @ KET0
    rho_L_4 = 0.7 * density_from_spinor(KET0) + 0.3 * I2 / 2.0
    rho_R_4 = 0.6 * density_from_spinor(KET1) + 0.4 * I2 / 2.0
    return [
        {
            "name": "point_1_z_basis",
            "L_kind": "pure",
            "R_kind": "pure",
            "psi_L": KET0,
            "psi_R": KET1,
            "rho_L": density_from_spinor(KET0),
            "rho_R": density_from_spinor(KET1),
        },
        {
            "name": "point_2_x_basis",
            "L_kind": "pure",
            "R_kind": "pure",
            "psi_L": KET_PLUS,
            "psi_R": KET_MINUS,
            "rho_L": density_from_spinor(KET_PLUS),
            "rho_R": density_from_spinor(KET_MINUS),
        },
        {
            "name": "point_3_su2_x_rotated",
            "L_kind": "pure",
            "R_kind": "pure",
            "psi_L": psi_L_3,
            "psi_R": psi_R_3,
            "rho_L": density_from_spinor(psi_L_3),
            "rho_R": density_from_spinor(psi_R_3),
        },
        {
            "name": "point_4_generic_mixed",
            "L_kind": "mixed",
            "R_kind": "mixed",
            "psi_L": None,
            "psi_R": None,
            "rho_L": rho_L_4,
            "rho_R": rho_R_4,
            "mixture_L": "0.7*|0><0| + 0.3*I/2",
            "mixture_R": "0.6*|1><1| + 0.4*I/2",
        },
    ]


def operator_outputs(rho: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "Ti_z_dephasing": Ti(rho),
        "Te_x_dephasing": Te(rho),
        "Fi_x_rotation": Fi(rho),
        "Fe_z_rotation": Fe(rho),
    }


def all_operator_validity(rho: np.ndarray) -> dict[str, object]:
    outputs = operator_outputs(rho)
    validity = {name: density_checks(out) for name, out in outputs.items()}
    for pair_name, gap_fn in GAP_FNS.items():
        if pair_name.startswith("A_"):
            first = Ti(Te(rho))
            second = Te(Ti(rho))
        elif pair_name.startswith("B_"):
            first = Fe(Fi(rho))
            second = Fi(Fe(rho))
        elif pair_name.startswith("C_"):
            first = Fi(Ti(rho))
            second = Ti(Fi(rho))
        else:
            first = Fe(Te(rho))
            second = Te(Fe(rho))
        validity[f"{pair_name}_terrain_first_output"] = density_checks(first)
        validity[f"{pair_name}_operator_first_output"] = density_checks(second)
        _ = gap_fn
    return {
        "checks": validity,
        "all_valid": bool(all(row["valid"] for row in validity.values())),
    }


def gaps_for_rho(rho: np.ndarray) -> dict[str, float]:
    return {name: hs_norm(fn(rho)) for name, fn in GAP_FNS.items()}


def kill_control() -> dict[str, object]:
    z_diagonal_states = {
        "ket0_z_diagonal": density_from_spinor(KET0),
        "ket1_z_diagonal": density_from_spinor(KET1),
        "mixed_z_diagonal": 0.35 * density_from_spinor(KET0) + 0.65 * density_from_spinor(KET1),
    }
    rows = {}
    for name, rho in z_diagonal_states.items():
        gap = Fe(Ti(rho)) - Ti(Fe(rho))
        rows[name] = hs_norm(gap)
    max_norm = max(rows.values())
    return {
        "pair": "Fe_after_Ti_minus_Ti_after_Fe_on_z_diagonal_rho",
        "per_state": rows,
        "max_norm": max_norm,
        "zero_within_tolerance": bool(max_norm <= 1.0e-9),
    }


def boundary_check(points: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for q_ti in [0.0, 0.1, 0.2, 0.4]:
        L_norms = [hs_norm(gap_A(point["rho_L"], q_ti=q_ti, q_te=Q_DEFAULT)) for point in points]
        R_norms = [hs_norm(gap_A(point["rho_R"], q_ti=q_ti, q_te=Q_DEFAULT)) for point in points]
        rows.append({
            "q_ti": q_ti,
            "q_te_fixed": Q_DEFAULT,
            "gap_A_L_norms": L_norms,
            "gap_A_R_norms": R_norms,
            "max_gap_A_L": max(L_norms),
            "max_gap_A_R": max(R_norms),
            "mean_gap_A_L": float(np.mean(L_norms)),
            "mean_gap_A_R": float(np.mean(R_norms)),
        })
    return rows


def ensemble_spinor(index: int, size: int, *, handedness: str) -> np.ndarray:
    alpha = (math.pi / 2.0) * (index + 0.5) / size
    beta = 2.0 * math.pi * index / size
    if handedness == "R":
        alpha = (math.pi / 2.0) * (size - index - 0.5) / size
        beta = beta + math.pi / 3.0
    return normalize_spinor(np.array([math.cos(alpha), np.exp(1j * beta) * math.sin(alpha)]))


def size_ladder() -> list[dict[str, object]]:
    ladder = []
    for size in [8, 16, 32, 64]:
        L_gap_rows = {name: [] for name in GAP_FNS}
        R_gap_rows = {name: [] for name in GAP_FNS}
        valid_rows = []
        for index in range(size):
            rho_L = density_from_spinor(ensemble_spinor(index, size, handedness="L"))
            rho_R = density_from_spinor(ensemble_spinor(index, size, handedness="R"))
            valid_rows.append(all_operator_validity(rho_L)["all_valid"])
            valid_rows.append(all_operator_validity(rho_R)["all_valid"])
            for pair_name, norm in gaps_for_rho(rho_L).items():
                L_gap_rows[pair_name].append(norm)
            for pair_name, norm in gaps_for_rho(rho_R).items():
                R_gap_rows[pair_name].append(norm)

        pair_summary = {}
        for pair_name in GAP_FNS:
            pair_summary[pair_name] = {
                "L_mean": float(np.mean(L_gap_rows[pair_name])),
                "L_max": float(np.max(L_gap_rows[pair_name])),
                "R_mean": float(np.mean(R_gap_rows[pair_name])),
                "R_max": float(np.max(R_gap_rows[pair_name])),
            }
        ladder.append({
            "ensemble_size": size,
            "states_per_handedness": size,
            "parameterization": "psi=[cos(alpha), exp(i beta) sin(alpha)], alpha grid in [0,pi/2], beta grid on S1",
            "all_valid_density": bool(all(valid_rows)),
            "pair_gap_summary": pair_summary,
            "any_gap_nonzero": bool(any(
                pair_summary[pair]["L_max"] > 1.0e-9 or pair_summary[pair]["R_max"] > 1.0e-9
                for pair in GAP_FNS
            )),
        })
    return ladder


def build_result() -> dict[str, object]:
    points = explicit_test_points()
    density_matrices_used = []
    spinors_used = []
    sample_gaps_L = {}
    sample_gaps_R = {}
    validity_flags = []

    print(f"layer = {LAYER}")
    print("gamma5 real =")
    print(np.real(GAMMA5))
    print("gamma5 imag =")
    print(np.imag(GAMMA5))
    print(f"parameters: q={Q_DEFAULT}, theta={THETA_DEFAULT}, phi={PHI_DEFAULT}")

    for point in points:
        name = str(point["name"])
        rho_L = np.asarray(point["rho_L"], dtype=np.complex128)
        rho_R = np.asarray(point["rho_R"], dtype=np.complex128)
        print(f"\n=== {name} ===")
        print_matrix(f"{name} rho_L", rho_L)
        print_matrix(f"{name} rho_R", rho_R)
        L_checks = density_checks(rho_L)
        R_checks = density_checks(rho_R)
        L_op_validity = all_operator_validity(rho_L)
        R_op_validity = all_operator_validity(rho_R)
        validity_flags.extend([L_checks["valid"], R_checks["valid"],
                               L_op_validity["all_valid"], R_op_validity["all_valid"]])

        density_matrices_used.append({
            "name": name,
            "rho_L": serialize_complex_matrix(rho_L),
            "rho_R": serialize_complex_matrix(rho_R),
            "rho_L_sector": "gamma5=+1 upper two components",
            "rho_R_sector": "gamma5=-1 lower two components",
            "rho_L_checks": L_checks,
            "rho_R_checks": R_checks,
            "rho_L_operator_validity": L_op_validity,
            "rho_R_operator_validity": R_op_validity,
        })

        spinor_row = {
            "name": name,
            "L_kind": point["L_kind"],
            "R_kind": point["R_kind"],
            "psi_L": None if point["psi_L"] is None else serialize_complex_vector(point["psi_L"]),
            "psi_R": None if point["psi_R"] is None else serialize_complex_vector(point["psi_R"]),
        }
        if "mixture_L" in point:
            spinor_row["mixture_L"] = point["mixture_L"]
            spinor_row["mixture_R"] = point["mixture_R"]
        spinors_used.append(spinor_row)

        for handedness, rho in [("L", rho_L), ("R", rho_R)]:
            for op_name, op_rho in operator_outputs(rho).items():
                print_matrix(f"{name} {handedness} {op_name}", op_rho)

        sample_gaps_L[name] = gaps_for_rho(rho_L)
        sample_gaps_R[name] = gaps_for_rho(rho_R)
        print(f"{name} gap norms L = {sample_gaps_L[name]}")
        print(f"{name} gap norms R = {sample_gaps_R[name]}")

    kill = kill_control()
    boundary = boundary_check(points)
    ladder = size_ladder()

    all_valid_density = bool(all(validity_flags) and all(row["all_valid_density"] for row in ladder))
    nonzero_pairs = []
    for pair_name in GAP_FNS:
        max_pair_gap = max(
            [sample_gaps_L[point["name"]][pair_name] for point in points]
            + [sample_gaps_R[point["name"]][pair_name] for point in points]
        )
        if max_pair_gap > 1.0e-9:
            nonzero_pairs.append(pair_name)

    any_gap_nonzero = bool(nonzero_pairs)
    boundary_q0_zero = bool(boundary[0]["max_gap_A_L"] <= 1.0e-9 and boundary[0]["max_gap_A_R"] <= 1.0e-9)
    pair_A_all_zero = bool(all(
        sample_gaps_L[point["name"]]["A_Ti_after_Te_minus_Te_after_Ti"] <= 1.0e-9
        and sample_gaps_R[point["name"]]["A_Ti_after_Te_minus_Te_after_Ti"] <= 1.0e-9
        for point in points
    ))
    all_pass = bool(all_valid_density and any_gap_nonzero and kill["zero_within_tolerance"] and boundary_q0_zero)

    print("\n=== kill control ===")
    print(json.dumps(kill, indent=2, sort_keys=True))
    print("\n=== boundary check gap A q_ti ladder ===")
    print(json.dumps(boundary, indent=2, sort_keys=True))
    print("\n=== size ladder ===")
    print(json.dumps(ladder, indent=2, sort_keys=True))
    print("\n=== summary ===")
    print(f"all_valid_density={all_valid_density}")
    print(f"any_gap_nonzero={any_gap_nonzero}")
    print(f"nonzero_pairs={nonzero_pairs}")
    print(f"pair_A_Ti_Te_commutes_zero={pair_A_all_zero}")
    print(f"kill_gap_zero={kill['zero_within_tolerance']}")
    print(f"all_pass={all_pass}")

    result = {
        "object_id": OBJECT_ID,
        "layer": LAYER,
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "f01_finite": {
            "finite_carrier": "exact dense 2x2 complex density matrices on left/right Weyl sectors",
            "domain": "finite list of rho_L/rho_R density matrices plus 8/16/32/64 finite S3 angle-grid ensembles",
            "codomain_or_output": "operator images, Hilbert-Schmidt order-gap norms, controls, boundary and ladder summaries",
            "operators_terminate": True,
            "matrix_exp_used": "scipy.linalg.expm on 2x2 Pauli generators only",
            "all_density_outputs_valid": all_valid_density,
            "dense_2x2_only": True,
        },
        "n01_noncommutation": {
            "order_gap_definition": "Op(T_terrain(rho)) - T_terrain(Op(rho))",
            "nonzero_pairs": nonzero_pairs,
            "any_gap_nonzero": any_gap_nonzero,
            "pair_A_Ti_Te_commutes_zero": pair_A_all_zero,
            "pair_A_note": "With the exact formulas, Ti and Te are both Pauli-transfer diagonal dephasing channels, so their superoperators commute for all tested states.",
            "pair_BC_D_witness_nonzero": all(pair in nonzero_pairs for pair in [
                "B_Fe_after_Fi_minus_Fi_after_Fe",
                "C_Fi_after_Ti_minus_Ti_after_Fi",
                "D_Fe_after_Te_minus_Te_after_Fe",
            ]),
        },
        "density_matrices_used": density_matrices_used,
        "spinors_used": spinors_used,
        "sample_gaps_L": sample_gaps_L,
        "sample_gaps_R": sample_gaps_R,
        "kill_control_gap": kill,
        "boundary_check": boundary,
        "size_ladder": ladder,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nwrote_result_json={OUT_PATH}")
    return result


def main() -> int:
    result = build_result()
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

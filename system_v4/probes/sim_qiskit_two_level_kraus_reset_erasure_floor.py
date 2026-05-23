#!/usr/bin/env python3
"""Qiskit two-level Kraus reset erasure-floor calibration."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import numpy as np
from qiskit.quantum_info import DensityMatrix, Kraus, Operator
from receipt_boundary import apply_default_receipt_boundary


NAME = "qiskit_two_level_kraus_reset_erasure_floor"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qiskit": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DensityMatrix/Kraus reset channel and Operator energy readouts",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive entropy, density validity, and scalar erasure-floor checks",
    },
}
TOOL_INTEGRATION_DEPTH = {"qiskit": "load_bearing", "numpy": "supportive"}


def matrix_pairs(matrix: np.ndarray) -> list[list[list[float]]]:
    arr = np.asarray(matrix, dtype=np.complex128)
    return [[[float(value.real), float(value.imag)] for value in row] for row in arr]


def entropy_nats(rho: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh((rho + rho.conjugate().T) / 2.0)
    positive = np.clip(eigs.real, 0.0, 1.0)
    positive = positive[positive > 1e-12]
    return float(-np.sum(positive * np.log(positive))) if positive.size else 0.0


def density_ok(rho: np.ndarray, tol: float = 1e-9) -> bool:
    arr = np.asarray(rho, dtype=np.complex128)
    hermitian = np.allclose(arr, arr.conjugate().T, atol=tol)
    trace_one = abs(float(np.trace(arr).real) - 1.0) < tol
    eigs = np.linalg.eigvalsh((arr + arr.conjugate().T) / 2.0)
    return bool(hermitian and trace_one and np.all(eigs >= -tol))


def fixtures() -> dict[str, np.ndarray | Operator | DensityMatrix]:
    ket0 = np.array([[1.0], [0.0]], dtype=np.complex128)
    ket1 = np.array([[0.0], [1.0]], dtype=np.complex128)
    p0 = ket0 @ ket0.conjugate().T
    p1 = ket1 @ ket1.conjugate().T
    return {
        "rho_unbiased": DensityMatrix(0.5 * p0 + 0.5 * p1),
        "rho_ground": DensityMatrix(p0),
        "rho_excited": DensityMatrix(p1),
        "H": Operator(p1),
    }


def amplitude_damping_kraus(gamma: float) -> Kraus:
    return Kraus(
        [
            np.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dtype=np.complex128),
            np.array([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=np.complex128),
        ]
    )


def energy(hamiltonian: Operator, rho: DensityMatrix) -> float:
    return float(np.trace(np.asarray(hamiltonian.data, dtype=np.complex128) @ np.asarray(rho.data)).real)


def apply_reset(rho0: DensityMatrix, *, gamma: float, kbt: float) -> dict[str, object]:
    f = fixtures()
    final = rho0.evolve(amplitude_damping_kraus(gamma))
    rho0_arr = np.asarray(rho0.data, dtype=np.complex128)
    final_arr = np.asarray(final.data, dtype=np.complex128)
    initial_entropy = entropy_nats(rho0_arr)
    final_entropy = entropy_nats(final_arr)
    entropy_removed = initial_entropy - final_entropy
    initial_energy = energy(f["H"], rho0)
    final_energy = energy(f["H"], final)
    return {
        "gamma": gamma,
        "initial_energy": initial_energy,
        "final_energy": final_energy,
        "energy_released": float(initial_energy - final_energy),
        "initial_entropy_nats": initial_entropy,
        "final_entropy_nats": final_entropy,
        "entropy_removed_nats": entropy_removed,
        "landauer_erasure_heat_floor": float(kbt * entropy_removed),
        "final_excited_population": final_energy,
        "final_density": matrix_pairs(final_arr),
        "final_density_ok": density_ok(final_arr),
    }


def run_positive() -> dict[str, object]:
    f = fixtures()
    kbt = 2.0
    reset = apply_reset(f["rho_unbiased"], gamma=1.0, kbt=kbt)
    return {
        "reset": reset,
        "kbt": kbt,
        "starts_with_one_bit_entropy": bool(np.isclose(reset["initial_entropy_nats"], math.log(2.0))),
        "removes_one_bit_entropy": bool(np.isclose(reset["entropy_removed_nats"], math.log(2.0))),
        "maps_to_ground_state": bool(np.isclose(reset["final_excited_population"], 0.0)),
        "density_remains_valid": bool(reset["final_density_ok"]),
        "energy_release_below_landauer_floor": bool(
            reset["energy_released"] <= reset["landauer_erasure_heat_floor"] + 1e-12
        ),
    }


def run_graveyards() -> dict[str, object]:
    f = fixtures()
    kbt = 2.0
    zero_gamma = apply_reset(f["rho_unbiased"], gamma=0.0, kbt=kbt)
    half_gamma = apply_reset(f["rho_unbiased"], gamma=0.5, kbt=kbt)
    ground_input = apply_reset(f["rho_ground"], gamma=1.0, kbt=kbt)
    excited_input = apply_reset(f["rho_excited"], gamma=1.0, kbt=kbt)
    return {
        "zero_gamma_identity_does_not_reset": {
            "final_excited_population": zero_gamma["final_excited_population"],
            "entropy_removed_nats": zero_gamma["entropy_removed_nats"],
            "passed": bool(
                np.isclose(zero_gamma["final_excited_population"], 0.5)
                and np.isclose(zero_gamma["entropy_removed_nats"], 0.0)
            ),
        },
        "partial_gamma_reset_is_incomplete": {
            "final_excited_population": half_gamma["final_excited_population"],
            "passed": bool(np.isclose(half_gamma["final_excited_population"], 0.25)),
        },
        "ground_input_has_no_record_entropy_to_erase": {
            "initial_entropy_nats": ground_input["initial_entropy_nats"],
            "entropy_removed_nats": ground_input["entropy_removed_nats"],
            "energy_released": ground_input["energy_released"],
            "passed": bool(
                np.isclose(ground_input["initial_entropy_nats"], 0.0)
                and np.isclose(ground_input["entropy_removed_nats"], 0.0)
                and np.isclose(ground_input["energy_released"], 0.0)
            ),
        },
        "pure_excited_input_releases_energy_without_record_entropy": {
            "initial_entropy_nats": excited_input["initial_entropy_nats"],
            "energy_released": excited_input["energy_released"],
            "passed": bool(
                np.isclose(excited_input["initial_entropy_nats"], 0.0)
                and np.isclose(excited_input["energy_released"], 1.0)
            ),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["starts_with_one_bit_entropy"]
        and positive["removes_one_bit_entropy"]
        and positive["maps_to_ground_state"]
        and positive["density_remains_valid"]
        and positive["energy_release_below_landauer_floor"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Qiskit two-level Kraus amplitude-damping reset erasure-floor calibration only; no QIT, GStack, "
            "axis, bridge, nonclassical, runtime-engine, work-reservoir, feedback-cycle, or target-system admission"
        ),
        "next_lego_target": "thermal_reset_erasure_floor_calibration_fixture",
        "promotion_condition": (
            "May only support later feedback-cycle planning after finite-temperature reset and explicit work-reservoir "
            "fixtures reproduce compatible accounting with graveyards."
        ),
        "demotion_condition": (
            "Demote if Kraus reset does not map the unbiased state to ground at gamma=1, if density validity fails, "
            "if entropy-removal accounting fails, or if zero/partial/ground/excited controls fail."
        ),
        "blocked_until": "blocked from target feedback-cycle mechanics until finite-temperature reset and work-reservoir fixtures exist",
        "out_of_scope": [
            "No finite-temperature bath.",
            "No explicit work reservoir.",
            "No repeated memory register dynamics.",
            "No QIT, GStack, axis, bridge, nonclassical, runtime-engine, feedback-cycle, or target-system admission.",
        ],
        "divergence_log": (
            "This is a Qiskit Kraus reset cross-check for the QuTiP mesolve reset fixture. It tests the same "
            "zero-temperature reset endpoint algebraically, but still treats the Landauer floor as a comparison bound."
        ),
        "operation_sequence": [
            "construct a two-level unbiased mixed density carrier",
            "apply the gamma=1 amplitude-damping Kraus reset channel",
            "read initial and final excited-state energy under H=|1><1|",
            "read initial and final von Neumann entropy in nats",
            "compute entropy removed and kBT times entropy removed as the erasure heat floor",
            "run zero-gamma, partial-gamma, ground-input, and pure-excited graveyards",
        ],
        "carrier_topology": "finite two-level density matrix with amplitude-damping Kraus reset channel",
        "observable": "final excited population, energy released, entropy removed, Landauer floor, and density validity",
        "pass_fail_predicate": (
            "unbiased mixed state starts at ln2 entropy, gamma=1 Kraus reset maps to ground, removes ln2 entropy, "
            "keeps the density valid, and adjacent graveyards collapse or separate energy release from record entropy"
        ),
        "graveyards": [
            "zero-gamma identity channel does not reset",
            "partial-gamma reset is incomplete",
            "ground input has no record entropy to erase",
            "pure excited input releases energy without record entropy",
        ],
        "baselines": [
            "scalar Szilard measurement-feedback-erasure Landauer receipt",
            "QuTiP two-level thermal reset erasure-floor receipt",
            "QuTiP two-level measurement-feedback-erasure receipt",
            "Qiskit two-level measurement-feedback-erasure receipt",
        ],
        "alternative_formulations": [
            "finite-temperature generalized amplitude damping",
            "explicit work battery model",
            "continuous-time QuTiP mesolve reset",
        ],
        "exact_tool_function_needs": {
            "qiskit": ["DensityMatrix", "Kraus", "Operator"],
            "numpy": ["trace", "log", "sum", "isclose", "eigvalsh"],
        },
        "lego_or_coupling_target": "thermal_reset_erasure_floor_calibration_fixture",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

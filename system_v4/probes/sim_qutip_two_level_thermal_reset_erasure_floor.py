#!/usr/bin/env python3
"""QuTiP two-level thermal reset erasure-floor calibration."""

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
import qutip
from receipt_boundary import apply_default_receipt_boundary


NAME = "qutip_two_level_thermal_reset_erasure_floor"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing mesolve reset evolution, two-level Qobj density carriers, collapse operator, and entropy/energy readouts",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive scalar checks for entropy removal, density validity, and bound comparisons",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": "load_bearing", "numpy": "supportive"}


def qobj_pairs(obj: qutip.Qobj) -> list[list[list[float]]]:
    matrix = np.asarray(obj.full(), dtype=np.complex128)
    return [[[float(value.real), float(value.imag)] for value in row] for row in matrix]


def entropy_nats(rho: qutip.Qobj) -> float:
    return float(qutip.entropy_vn(rho, base=math.e))


def density_ok(rho: qutip.Qobj, tol: float = 1e-9) -> bool:
    matrix = np.asarray(rho.full(), dtype=np.complex128)
    hermitian = np.allclose(matrix, matrix.conjugate().T, atol=tol)
    trace_one = abs(float(rho.tr().real) - 1.0) < tol
    eigs = np.linalg.eigvalsh((matrix + matrix.conjugate().T) / 2.0)
    return bool(hermitian and trace_one and np.all(eigs >= -tol))


def fixtures() -> dict[str, qutip.Qobj]:
    ket0 = qutip.basis(2, 0)
    ket1 = qutip.basis(2, 1)
    return {
        "rho_unbiased": 0.5 * qutip.ket2dm(ket0) + 0.5 * qutip.ket2dm(ket1),
        "rho_excited": qutip.ket2dm(ket1),
        "rho_ground": qutip.ket2dm(ket0),
        "H": qutip.ket2dm(ket1),
        "lowering": qutip.destroy(2),
    }


def evolve_reset(rho0: qutip.Qobj, *, gamma: float, duration: float, steps: int = 301) -> dict[str, object]:
    f = fixtures()
    times = np.linspace(0.0, duration, steps)
    collapse = [] if gamma == 0.0 else [math.sqrt(gamma) * f["lowering"]]
    result = qutip.mesolve(H=0.0 * f["H"], rho0=rho0, tlist=times, c_ops=collapse, e_ops=[])
    states = result.states
    energies = [float(qutip.expect(f["H"], state)) for state in states]
    entropies = [entropy_nats(state) for state in states]
    final = states[-1]
    return {
        "gamma": gamma,
        "duration": duration,
        "steps": steps,
        "initial_energy": energies[0],
        "final_energy": energies[-1],
        "energy_released": float(energies[0] - energies[-1]),
        "initial_entropy_nats": entropies[0],
        "final_entropy_nats": entropies[-1],
        "entropy_removed_nats": float(entropies[0] - entropies[-1]),
        "final_excited_population": float(qutip.expect(f["H"], final)),
        "final_density": qobj_pairs(final),
        "final_density_ok": density_ok(final),
    }


def run_positive() -> dict[str, object]:
    f = fixtures()
    gamma = 1.0
    duration = 12.0
    kbt = 2.0
    reset = evolve_reset(f["rho_unbiased"], gamma=gamma, duration=duration)
    floor = kbt * reset["entropy_removed_nats"]
    return {
        "reset": reset,
        "kbt": kbt,
        "landauer_erasure_heat_floor": floor,
        "starts_with_one_bit_entropy": bool(np.isclose(reset["initial_entropy_nats"], math.log(2.0))),
        "removes_nearly_one_bit_entropy": bool(reset["entropy_removed_nats"] > math.log(2.0) - 1e-3),
        "approaches_ground_state": bool(reset["final_excited_population"] < 1e-5),
        "density_remains_valid": bool(reset["final_density_ok"]),
        "energy_release_below_landauer_floor": bool(reset["energy_released"] <= floor + 1e-12),
    }


def run_graveyards() -> dict[str, object]:
    f = fixtures()
    gamma = 1.0
    long_duration = 12.0
    zero_time = evolve_reset(f["rho_unbiased"], gamma=gamma, duration=0.0, steps=2)
    zero_gamma = evolve_reset(f["rho_unbiased"], gamma=0.0, duration=long_duration)
    ground_input = evolve_reset(f["rho_ground"], gamma=gamma, duration=long_duration)
    short_time = evolve_reset(f["rho_unbiased"], gamma=gamma, duration=0.05)
    excited_input = evolve_reset(f["rho_excited"], gamma=gamma, duration=long_duration)
    return {
        "zero_time_does_not_reset": {
            "final_excited_population": zero_time["final_excited_population"],
            "entropy_removed_nats": zero_time["entropy_removed_nats"],
            "passed": bool(
                np.isclose(zero_time["final_excited_population"], 0.5)
                and np.isclose(zero_time["entropy_removed_nats"], 0.0)
            ),
        },
        "zero_gamma_does_not_reset": {
            "final_excited_population": zero_gamma["final_excited_population"],
            "entropy_removed_nats": zero_gamma["entropy_removed_nats"],
            "passed": bool(
                np.isclose(zero_gamma["final_excited_population"], 0.5)
                and np.isclose(zero_gamma["entropy_removed_nats"], 0.0)
            ),
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
        "short_duration_reset_is_incomplete": {
            "final_excited_population": short_time["final_excited_population"],
            "passed": bool(short_time["final_excited_population"] > 0.45),
        },
        "pure_excited_input_releases_energy_without_record_entropy": {
            "initial_entropy_nats": excited_input["initial_entropy_nats"],
            "energy_released": excited_input["energy_released"],
            "passed": bool(
                np.isclose(excited_input["initial_entropy_nats"], 0.0)
                and excited_input["energy_released"] > 0.99
            ),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["starts_with_one_bit_entropy"]
        and positive["removes_nearly_one_bit_entropy"]
        and positive["approaches_ground_state"]
        and positive["density_remains_valid"]
        and positive["energy_release_below_landauer_floor"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "QuTiP two-level amplitude-damping thermal-reset erasure-floor calibration only; no QIT, GStack, "
            "axis, bridge, nonclassical, runtime-engine, work-reservoir, feedback-cycle, or target-system admission"
        ),
        "next_lego_target": "thermal_reset_erasure_floor_calibration_fixture",
        "promotion_condition": (
            "May only support later feedback-cycle planning after an independent work-reservoir fixture and "
            "branch-feedback receipts reproduce compatible accounting with graveyards."
        ),
        "demotion_condition": (
            "Demote if mesolve reset does not approach the ground state, if density validity fails, if entropy removal "
            "or Landauer floor accounting fails, or if zero-time/zero-gamma/ground-input/short-duration controls fail."
        ),
        "blocked_until": "blocked from target feedback-cycle mechanics until work-reservoir and repeated-memory fixtures exist",
        "out_of_scope": [
            "No explicit work reservoir.",
            "No repeated memory register dynamics.",
            "No proof that amplitude-damping energy release saturates the Landauer floor.",
            "No QIT, GStack, axis, bridge, nonclassical, runtime-engine, feedback-cycle, or target-system admission.",
        ],
        "divergence_log": (
            "This is a QuTiP mesolve reset fixture. It adds an explicit dissipative reset stroke to the scalar and "
            "branch-feedback calibration receipts, but still treats the Landauer floor as a comparison bound rather "
            "than deriving it from a full finite-temperature work reservoir."
        ),
        "operation_sequence": [
            "construct a two-level unbiased mixed density carrier",
            "evolve the carrier under zero-temperature amplitude damping with qutip.mesolve",
            "read initial and final excited-state energy under H=|1><1|",
            "read initial and final von Neumann entropy in nats",
            "compute entropy removed and kBT times entropy removed as the erasure heat floor",
            "run zero-time, zero-gamma, ground-input, short-duration, and pure-excited graveyards",
        ],
        "carrier_topology": "finite two-level density matrix with dissipative reset evolution under one collapse operator",
        "observable": "final excited population, energy released, entropy removed, Landauer floor, and density validity",
        "pass_fail_predicate": (
            "unbiased mixed state starts at ln2 entropy, amplitude damping approaches ground, removes nearly ln2 entropy, "
            "keeps the density valid, and adjacent graveyards fail, collapse, or separate energy release from record entropy"
        ),
        "graveyards": [
            "zero-time evolution does not reset",
            "zero-gamma evolution does not reset",
            "ground input has no record entropy to erase",
            "short-duration reset is incomplete",
            "pure excited input releases energy without record entropy",
        ],
        "baselines": [
            "scalar Szilard measurement-feedback-erasure Landauer receipt",
            "QuTiP two-level measurement-feedback-erasure receipt",
            "Qiskit two-level measurement-feedback-erasure receipt",
            "QuTiP mesolve amplitude-damping channel fit receipt",
        ],
        "alternative_formulations": [
            "finite-temperature generalized amplitude damping",
            "explicit work battery model",
            "Qiskit Kraus-map reset channel cross-check",
        ],
        "exact_tool_function_needs": {
            "qutip": ["basis", "ket2dm", "destroy", "mesolve", "expect", "entropy_vn", "Qobj.tr"],
            "numpy": ["linspace", "isclose", "eigvalsh"],
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

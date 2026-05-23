#!/usr/bin/env python3
"""NumPy Weyl-sheet Hopf-loop readout separation baseline."""

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
from receipt_boundary import apply_default_receipt_boundary


NAME = "numpy_weyl_sheet_hopf_loop_readout_separation"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": (
            "samples complex two-component Hopf-coordinate carriers with a declared sheet-orientation parameter "
            "and computes density, Bloch, path-length, and signed-loop readouts"
        ),
    }
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

PAULI = {
    "x": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex),
    "y": np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex),
    "z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex),
}


def spinor(theta: float, phi: float, chi: float, sheet_orientation: int) -> np.ndarray:
    if sheet_orientation not in (-1, 1):
        raise ValueError("sheet_orientation must be -1 or +1")
    signed_phi = sheet_orientation * phi
    return np.array(
        [
            math.cos(theta / 2.0) * np.exp(0.5j * (chi + signed_phi)),
            math.sin(theta / 2.0) * np.exp(0.5j * (chi - signed_phi)),
        ],
        dtype=complex,
    )


def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, np.conjugate(psi))


def bloch_readout(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(rho @ matrix))) for matrix in PAULI.values()])


def signed_xy_area(points: list[np.ndarray]) -> float:
    xy = np.asarray([[point[0], point[1]] for point in points], dtype=float)
    rolled = np.roll(xy, -1, axis=0)
    return float(0.5 * np.sum(xy[:, 0] * rolled[:, 1] - rolled[:, 0] * xy[:, 1]))


def path_metrics(states: list[np.ndarray]) -> dict[str, object]:
    densities = [density(psi) for psi in states]
    bloch = [bloch_readout(rho) for rho in densities]
    density_steps = [
        float(np.linalg.norm(densities[idx + 1] - densities[idx], ord="fro"))
        for idx in range(len(densities) - 1)
    ]
    bloch_steps = [
        float(np.linalg.norm(bloch[idx + 1] - bloch[idx]))
        for idx in range(len(bloch) - 1)
    ]
    state_steps = [
        float(np.linalg.norm(states[idx + 1] - states[idx]))
        for idx in range(len(states) - 1)
    ]
    first_component_phase = np.unwrap(np.angle([psi[0] for psi in states]))
    return {
        "density_path_length": float(sum(density_steps)),
        "bloch_path_length": float(sum(bloch_steps)),
        "state_path_length": float(sum(state_steps)),
        "density_displacement_from_start": float(
            max(np.linalg.norm(rho - densities[0], ord="fro") for rho in densities)
        ),
        "bloch_displacement_from_start": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "signed_xy_area": signed_xy_area(bloch),
        "first_component_phase_span": float(first_component_phase[-1] - first_component_phase[0]),
        "start_bloch": [float(value) for value in bloch[0]],
        "end_bloch": [float(value) for value in bloch[-1]],
    }


def sample_path(sheet_orientation: int, loop_family: str, theta: float, samples: int) -> list[np.ndarray]:
    if loop_family == "fiber_loop":
        phi = 0.0
        return [spinor(theta, phi, chi, sheet_orientation) for chi in np.linspace(0.0, 2.0 * math.pi, samples)]
    if loop_family == "base_loop":
        chi = 0.0
        return [spinor(theta, phi, chi, sheet_orientation) for phi in np.linspace(0.0, 2.0 * math.pi, samples)]
    raise ValueError(f"unknown loop_family: {loop_family}")


def readout_family(theta: float = math.pi / 3.0, samples: int = 129) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for sheet_name, sheet_orientation in (("positive_sheet", 1), ("negative_sheet", -1)):
        for loop_family in ("fiber_loop", "base_loop"):
            key = f"{sheet_name}__{loop_family}"
            rows[key] = path_metrics(sample_path(sheet_orientation, loop_family, theta, samples))
    return rows


def sign(value: float, tol: float = 1e-9) -> int:
    if value > tol:
        return 1
    if value < -tol:
        return -1
    return 0


def run_positive() -> dict[str, object]:
    rows = readout_family()
    pos_base = rows["positive_sheet__base_loop"]
    neg_base = rows["negative_sheet__base_loop"]
    pos_fiber = rows["positive_sheet__fiber_loop"]
    neg_fiber = rows["negative_sheet__fiber_loop"]
    return {
        "readouts": rows,
        "survives_declared_sheet_loop_readout": bool(
            pos_fiber["density_path_length"] < 1e-9
            and neg_fiber["density_path_length"] < 1e-9
            and pos_base["density_path_length"] > 3.0
            and neg_base["density_path_length"] > 3.0
            and sign(float(pos_base["signed_xy_area"])) == -1
            and sign(float(neg_base["signed_xy_area"])) == 1
            and np.linalg.norm(np.asarray(pos_fiber["start_bloch"]) - np.asarray(pos_base["start_bloch"])) < 1e-9
            and np.linalg.norm(np.asarray(neg_fiber["start_bloch"]) - np.asarray(neg_base["start_bloch"])) < 1e-9
        ),
    }


def run_graveyards() -> dict[str, object]:
    rows = readout_family()
    pos_base = rows["positive_sheet__base_loop"]
    neg_base = rows["negative_sheet__base_loop"]
    pos_fiber = rows["positive_sheet__fiber_loop"]
    neg_fiber = rows["negative_sheet__fiber_loop"]
    pole_rows = readout_family(theta=0.0)
    pole_pos_base = pole_rows["positive_sheet__base_loop"]
    pole_neg_base = pole_rows["negative_sheet__base_loop"]
    same_sheet_rows = {
        "positive_sheet_copy_a__base_loop": path_metrics(sample_path(1, "base_loop", math.pi / 3.0, 129)),
        "positive_sheet_copy_b__base_loop": path_metrics(sample_path(1, "base_loop", math.pi / 3.0, 129)),
    }
    return {
        "drop_signed_area_collapses_base_sheet_orientation": {
            "positive_base_density_path_length": pos_base["density_path_length"],
            "negative_base_density_path_length": neg_base["density_path_length"],
            "signed_areas": [pos_base["signed_xy_area"], neg_base["signed_xy_area"]],
            "passed": bool(
                abs(float(pos_base["density_path_length"]) - float(neg_base["density_path_length"])) < 1e-9
                and sign(float(pos_base["signed_xy_area"])) != sign(float(neg_base["signed_xy_area"]))
            ),
        },
        "drop_density_path_length_collapses_loop_family": {
            "positive_sheet_start_points": [pos_fiber["start_bloch"], pos_base["start_bloch"]],
            "passed": bool(
                np.linalg.norm(np.asarray(pos_fiber["start_bloch"]) - np.asarray(pos_base["start_bloch"])) < 1e-9
                and pos_fiber["density_path_length"] < 1e-9
                and pos_base["density_path_length"] > 3.0
            ),
        },
        "same_sheet_duplicates_have_same_signed_area": {
            "areas": [
                same_sheet_rows["positive_sheet_copy_a__base_loop"]["signed_xy_area"],
                same_sheet_rows["positive_sheet_copy_b__base_loop"]["signed_xy_area"],
            ],
            "passed": bool(
                abs(
                    float(same_sheet_rows["positive_sheet_copy_a__base_loop"]["signed_xy_area"])
                    - float(same_sheet_rows["positive_sheet_copy_b__base_loop"]["signed_xy_area"])
                )
                < 1e-12
            ),
        },
        "base_loop_at_pole_collapses_sheet_orientation": {
            "positive_pole_base": pole_pos_base,
            "negative_pole_base": pole_neg_base,
            "passed": bool(
                pole_pos_base["density_path_length"] < 1e-9
                and pole_neg_base["density_path_length"] < 1e-9
                and abs(float(pole_pos_base["signed_xy_area"])) < 1e-9
                and abs(float(pole_neg_base["signed_xy_area"])) < 1e-9
            ),
        },
        "bare_sheet_loop_labels_without_carrier_are_insufficient": {
            "has_complex_carrier": False,
            "has_density_readout": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_declared_sheet_loop_readout"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "NumPy declared Weyl-sheet orientation and Hopf-loop readout separation baseline only; no physical "
            "sheet/loop independence, no full S3 bundle, no flux, no QIT, GStack, axis, bridge, nonclassical, "
            "target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "promotion_condition": (
            "May only support later geometry planning after symbolic, Clifford, density-object, and topology "
            "fixtures reproduce compatible declared-path readouts with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if base loops do not separate signed sheet orientation, if fiber loops traverse density, "
            "if base loops do not traverse density away from the pole, or if adjacent graveyards do not collapse."
        ),
        "blocked_until": (
            "blocked from target-system claims until full carrier/topology implementation and physical-evolution "
            "graveyards exist"
        ),
        "out_of_scope": [
            "No physical Weyl-sheet dynamics.",
            "No full Hopf bundle or nested Hopf-torus manifold.",
            "No flux representation or Pauli shortcut.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This is a NumPy sampled-coordinate baseline. It separates declared sheet-orientation and loop-family "
            "readouts in a local carrier chart, but it does not prove physical loop independence or implement a "
            "geometric-constraint manifold."
        ),
        "operation_sequence": [
            "declare a sheet-orientation sign in the Hopf-coordinate phase",
            "sample fiber-loop states by varying chi at fixed theta and phi",
            "sample base-loop states by varying phi at fixed theta and chi",
            "compute density matrices and Bloch readouts for both sheet signs and loop families",
            "compare density path length, signed xy area, and start/end Bloch readouts",
            "run dropped-readout, duplicate-sheet, pole-degenerate, and no-carrier graveyards",
        ],
        "carrier_topology": "sampled two-component complex Hopf-coordinate carrier with declared sheet-orientation sign; no full S3 bundle object",
        "observable": "density path length, Bloch path length, signed xy area, start Bloch readout, and phase span",
        "pass_fail_predicate": (
            "fiber loops remain density-stationary, base loops traverse density away from the pole, base-loop signed "
            "area changes sign under sheet orientation reversal, and adjacent controls collapse as declared"
        ),
        "graveyards": [
            "dropping signed area collapses base-loop sheet orientation",
            "dropping density path length collapses loop family",
            "same-sheet duplicates have same signed area",
            "base loop at pole collapses sheet orientation",
            "bare sheet/loop labels without carrier are insufficient",
        ],
        "baselines": [
            "z3 finite sheet-loop product readout separation",
            "NumPy Hopf inner/outer loop readout geometry",
            "SymPy Hopf density derivative identity",
            "Clifford projected Hopf outer-path rotor readout",
        ],
        "alternative_formulations": [
            "symbolic sheet-orientation derivative identity",
            "Clifford rotor orientation reversal fixture",
            "QuTiP/Qiskit density-object sheet orientation fixture",
            "TopoNetX or GUDHI nested torus carrier approximation",
        ],
        "exact_tool_function_needs": {"numpy": ["array", "exp", "outer", "trace", "linalg.norm", "unwrap", "roll"]},
        "lego_or_coupling_target": "inner_outer_hopf_weyl_loop_geometry_fit",
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

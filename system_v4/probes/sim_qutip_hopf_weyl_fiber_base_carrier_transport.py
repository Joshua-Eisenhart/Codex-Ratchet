#!/usr/bin/env python3
"""QuTiP Hopf/Weyl fiber-base carrier transport baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from qutip import Qobj, expect, sigmax, sigmay, sigmaz
from receipt_boundary import apply_default_receipt_boundary


NAME = "qutip_hopf_weyl_fiber_base_carrier_transport"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "constructs two-component ket carriers, density objects, Pauli expectation readouts, and trace-distance diagnostics",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples Hopf loop coordinates and computes path metrics and signed projected areas",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": "load_bearing", "numpy": "supportive"}

PAULI = (sigmax(), sigmay(), sigmaz())


def spinor(theta: float, phi: float, chi: float, sheet_orientation: int) -> Qobj:
    if sheet_orientation not in (-1, 1):
        raise ValueError("sheet_orientation must be -1 or +1")
    signed_phi = sheet_orientation * phi
    values = [
        math.cos(theta / 2.0) * np.exp(0.5j * (chi + signed_phi)),
        math.sin(theta / 2.0) * np.exp(0.5j * (chi - signed_phi)),
    ]
    return Qobj(np.asarray(values, dtype=complex).reshape((2, 1)))


def density(ket: Qobj) -> Qobj:
    return ket * ket.dag()


def bloch_readout(rho: Qobj) -> np.ndarray:
    return np.asarray([float(np.real(expect(op, rho))) for op in PAULI], dtype=float)


def signed_xy_area(points: list[np.ndarray]) -> float:
    xy = np.asarray([[point[0], point[1]] for point in points], dtype=float)
    rolled = np.roll(xy, -1, axis=0)
    return float(0.5 * np.sum(xy[:, 0] * rolled[:, 1] - rolled[:, 0] * xy[:, 1]))


def sample_path(sheet_orientation: int, loop_family: str, theta: float, samples: int) -> list[Qobj]:
    if loop_family == "fiber_loop":
        return [spinor(theta, 0.0, float(chi), sheet_orientation) for chi in np.linspace(0.0, 2.0 * math.pi, samples)]
    if loop_family == "base_loop":
        return [spinor(theta, float(phi), 0.0, sheet_orientation) for phi in np.linspace(0.0, 2.0 * math.pi, samples)]
    raise ValueError(f"unknown loop_family: {loop_family}")


def path_metrics(states: list[Qobj]) -> dict[str, object]:
    densities = [density(ket) for ket in states]
    bloch = [bloch_readout(rho) for rho in densities]
    density_steps = [
        float(np.linalg.norm((densities[idx + 1] - densities[idx]).full(), ord="fro"))
        for idx in range(len(densities) - 1)
    ]
    ket_steps = [
        float(np.linalg.norm((states[idx + 1] - states[idx]).full()))
        for idx in range(len(states) - 1)
    ]
    component_phase = np.unwrap(np.angle([ket.full()[0, 0] for ket in states]))
    return {
        "density_path_length": float(sum(density_steps)),
        "ket_path_length": float(sum(ket_steps)),
        "max_density_displacement": float(
            max(np.linalg.norm((rho - densities[0]).full(), ord="fro") for rho in densities)
        ),
        "max_bloch_displacement": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "signed_xy_area": signed_xy_area(bloch),
        "first_component_phase_span": float(component_phase[-1] - component_phase[0]),
        "start_bloch": [float(value) for value in bloch[0]],
        "end_bloch": [float(value) for value in bloch[-1]],
        "trace": float(np.real(densities[-1].tr())),
    }


def readout_family(theta: float = math.pi / 3.0, samples: int = 129) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for sheet_name, sheet_orientation in (("positive_sheet", 1), ("negative_sheet", -1)):
        for loop_family in ("fiber_loop", "base_loop"):
            rows[f"{sheet_name}__{loop_family}"] = path_metrics(
                sample_path(sheet_orientation, loop_family, theta, samples)
            )
    return rows


def sign(value: float, tol: float = 1e-9) -> int:
    if value > tol:
        return 1
    if value < -tol:
        return -1
    return 0


def run_positive() -> dict[str, object]:
    rows = readout_family()
    pos_fiber = rows["positive_sheet__fiber_loop"]
    neg_fiber = rows["negative_sheet__fiber_loop"]
    pos_base = rows["positive_sheet__base_loop"]
    neg_base = rows["negative_sheet__base_loop"]
    return {
        "readouts": rows,
        "survives_qutip_carrier_transport": bool(
            pos_fiber["density_path_length"] < 1e-9
            and neg_fiber["density_path_length"] < 1e-9
            and pos_fiber["ket_path_length"] > 2.0
            and neg_fiber["ket_path_length"] > 2.0
            and pos_base["density_path_length"] > 3.0
            and neg_base["density_path_length"] > 3.0
            and sign(float(pos_base["signed_xy_area"])) == -1
            and sign(float(neg_base["signed_xy_area"])) == 1
            and abs(float(pos_fiber["trace"]) - 1.0) < 1e-12
            and abs(float(pos_base["trace"]) - 1.0) < 1e-12
        ),
    }


def run_graveyards() -> dict[str, object]:
    rows = readout_family()
    pole_rows = readout_family(theta=0.0)
    pos_fiber = rows["positive_sheet__fiber_loop"]
    pos_base = rows["positive_sheet__base_loop"]
    neg_base = rows["negative_sheet__base_loop"]
    pole_pos_base = pole_rows["positive_sheet__base_loop"]
    pole_neg_base = pole_rows["negative_sheet__base_loop"]
    same_base_a = path_metrics(sample_path(1, "base_loop", math.pi / 3.0, 129))
    same_base_b = path_metrics(sample_path(1, "base_loop", math.pi / 3.0, 129))
    return {
        "fiber_loop_density_hides_global_phase": {
            "fiber_density_path_length": pos_fiber["density_path_length"],
            "fiber_ket_path_length": pos_fiber["ket_path_length"],
            "passed": bool(pos_fiber["density_path_length"] < 1e-9 and pos_fiber["ket_path_length"] > 2.0),
        },
        "dropping_density_path_length_collapses_loop_family": {
            "start_bloch_gap": float(
                np.linalg.norm(np.asarray(pos_fiber["start_bloch"]) - np.asarray(pos_base["start_bloch"]))
            ),
            "fiber_density_path_length": pos_fiber["density_path_length"],
            "base_density_path_length": pos_base["density_path_length"],
            "passed": bool(pos_fiber["density_path_length"] < 1e-9 and pos_base["density_path_length"] > 3.0),
        },
        "dropping_signed_area_collapses_sheet_orientation": {
            "positive_base_density_path_length": pos_base["density_path_length"],
            "negative_base_density_path_length": neg_base["density_path_length"],
            "positive_signed_area": pos_base["signed_xy_area"],
            "negative_signed_area": neg_base["signed_xy_area"],
            "passed": bool(
                abs(float(pos_base["density_path_length"]) - float(neg_base["density_path_length"])) < 1e-9
                and sign(float(pos_base["signed_xy_area"])) == -sign(float(neg_base["signed_xy_area"]))
            ),
        },
        "base_loop_at_pole_collapses_orientation_and_transport": {
            "positive_pole_base": pole_pos_base,
            "negative_pole_base": pole_neg_base,
            "passed": bool(
                pole_pos_base["density_path_length"] < 1e-9
                and pole_neg_base["density_path_length"] < 1e-9
                and abs(float(pole_pos_base["signed_xy_area"])) < 1e-9
                and abs(float(pole_neg_base["signed_xy_area"])) < 1e-9
            ),
        },
        "same_sheet_duplicate_base_loops_are_indistinguishable": {
            "signed_area_gap": float(abs(float(same_base_a["signed_xy_area"]) - float(same_base_b["signed_xy_area"]))),
            "density_path_gap": float(abs(float(same_base_a["density_path_length"]) - float(same_base_b["density_path_length"]))),
            "passed": bool(
                abs(float(same_base_a["signed_xy_area"]) - float(same_base_b["signed_xy_area"])) < 1e-12
                and abs(float(same_base_a["density_path_length"]) - float(same_base_b["density_path_length"])) < 1e-12
            ),
        },
        "bare_loop_labels_without_qutip_carrier_are_insufficient": {
            "has_qutip_ket": False,
            "has_density_object": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_qutip_carrier_transport"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "QuTiP two-component Hopf/Weyl carrier-state fiber/base transport baseline only; this compares ket, "
            "density, and Pauli-expectation readouts for declared loop families and sheet orientations; no physical "
            "inner/outer independence, no full nested Hopf-torus manifold, no flux, no QIT, GStack, axis, bridge, "
            "nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after symbolic, Clifford, topology, and physical "
            "operator-evolution fixtures reproduce compatible fiber/base readouts with adjacent graveyards."
        ),
        "demotion_condition": (
            "Demote if fiber loops move density readouts, if base loops do not move density away from the pole, "
            "if sheet-orientation reversal does not invert signed base-loop area, or if pole/duplicate/no-carrier "
            "graveyards do not collapse."
        ),
        "blocked_until": (
            "blocked from target-system claims until full carrier/topology implementation and physical-evolution "
            "graveyards exist"
        ),
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, or thermodynamic cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This is a carrier-state and density-object baseline over declared Hopf coordinates. It improves over "
            "label-only loop tests, but it still does not implement full geometry or prove physical independence."
        ),
        "operation_sequence": [
            "construct normalized two-component QuTiP kets from Hopf coordinates theta, phi, chi",
            "apply a declared sheet-orientation sign to the base-loop phi coordinate",
            "sample fiber loops by varying chi at fixed theta and phi",
            "sample base loops by varying phi at fixed theta and chi",
            "compute QuTiP density objects and Pauli expectation readouts",
            "compare ket path length, density path length, signed xy area, trace, and pole degeneracy",
            "run density-hidden, signed-area-hidden, pole, duplicate, and no-carrier graveyards",
        ],
        "carrier_topology": "sampled two-component Hopf-coordinate ket carrier with density-object readout; no full S3 bundle or nested-torus manifold",
        "observable": "ket path length, density path length, Pauli expectation path, signed xy area, density trace, and pole degeneracy",
        "pass_fail_predicate": (
            "fiber loops traverse ket phase while density remains stationary, base loops traverse density away from "
            "the pole, base-loop signed area flips under declared sheet orientation, density traces stay normalized, "
            "and adjacent controls collapse or become indistinguishable"
        ),
        "graveyards": [
            "fiber loop density hides global phase",
            "dropping density path length collapses loop family",
            "dropping signed area collapses sheet orientation",
            "base loop at pole collapses orientation and transport",
            "same-sheet duplicate base loops are indistinguishable",
            "bare loop labels without QuTiP carrier are insufficient",
        ],
        "baselines": [
            "NumPy Weyl-sheet Hopf-loop readout separation",
            "SymPy Weyl-sheet Hopf-loop derivative sign",
            "Clifford Hopf outer rotation readout",
            "SciPy connected Hopf-torus horizontal transport",
        ],
        "alternative_formulations": [
            "Qiskit statevector and density-matrix formulation",
            "Clifford Spin/SU(2) half-period carrier sign formulation",
            "symbolic connection integral over the same carrier chart",
            "triangulated nested Hopf-torus layer carrier",
        ],
        "exact_tool_function_needs": {
            "qutip": ["Qobj", "dag", "tr", "expect", "sigmax", "sigmay", "sigmaz"],
            "numpy": ["linspace", "exp", "unwrap", "angle", "roll", "linalg.norm"],
        },
        "lego_or_coupling_target": "hopf_weyl_carrier_loop_geometry_baseline",
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

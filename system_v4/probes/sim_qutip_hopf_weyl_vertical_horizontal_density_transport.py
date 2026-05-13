#!/usr/bin/env python3
"""QuTiP Hopf/Weyl vertical fiber and horizontal base-lift density transport."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from qutip import Qobj, expect, sigmax, sigmay, sigmaz
from receipt_boundary import apply_default_receipt_boundary


NAME = "qutip_hopf_weyl_vertical_horizontal_density_transport"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "constructs two-component ket carriers, density objects, and Pauli expectation readouts along vertical fiber and horizontal base-lift paths",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples Hopf-coordinate paths and computes density, Bloch, and phase path metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": "load_bearing", "numpy": "supportive"}

PAULI = (sigmax(), sigmay(), sigmaz())


def spinor(theta: float, phi: float, chi: float, sheet_orientation: int) -> Qobj:
    if sheet_orientation not in (-1, 1):
        raise ValueError("sheet_orientation must be -1 or +1")
    signed_phi = float(sheet_orientation) * phi
    values = [
        math.cos(theta / 2.0) * np.exp(0.5j * (chi + signed_phi)),
        math.sin(theta / 2.0) * np.exp(0.5j * (chi - signed_phi)),
    ]
    return Qobj(np.asarray(values, dtype=complex).reshape((2, 1)))


def density(ket: Qobj) -> Qobj:
    return ket * ket.dag()


def bloch_readout(rho: Qobj) -> np.ndarray:
    return np.asarray([float(np.real(expect(op, rho))) for op in PAULI], dtype=float)


def path_states(theta: float, phi0: float, chi0: float, sheet_orientation: int, family: str, samples: int) -> list[Qobj]:
    rows: list[Qobj] = []
    for value in np.linspace(0.0, 2.0 * math.pi, samples):
        if family == "vertical_fiber":
            phi = phi0
            chi = chi0 + float(value)
        elif family == "raw_base":
            phi = phi0 + float(value)
            chi = chi0
        elif family == "horizontal_base":
            phi = phi0 + float(value)
            chi = chi0 - float(sheet_orientation) * math.cos(theta) * float(value)
        elif family == "wrong_sign_horizontal_base":
            phi = phi0 + float(value)
            chi = chi0 + float(sheet_orientation) * math.cos(theta) * float(value)
        else:
            raise ValueError(f"unknown path family: {family}")
        rows.append(spinor(theta, phi, chi, sheet_orientation))
    return rows


def signed_xy_area(points: list[np.ndarray]) -> float:
    xy = np.asarray([[point[0], point[1]] for point in points], dtype=float)
    rolled = np.roll(xy, -1, axis=0)
    return float(0.5 * np.sum(xy[:, 0] * rolled[:, 1] - rolled[:, 0] * xy[:, 1]))


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
        "start_end_density_distance": float(np.linalg.norm((densities[-1] - densities[0]).full(), ord="fro")),
        "start_end_ket_distance": float(np.linalg.norm((states[-1] - states[0]).full())),
        "start_bloch": [float(value) for value in bloch[0]],
        "end_bloch": [float(value) for value in bloch[-1]],
        "trace": float(np.real(densities[-1].tr())),
    }


def finite_difference_bloch_tangent_dot(theta: float, phi: float, chi: float, sheet_orientation: int, eps: float = 1e-6) -> dict[str, float]:
    def bloch(theta_: float, phi_: float, chi_: float) -> np.ndarray:
        return bloch_readout(density(spinor(theta_, phi_, chi_, sheet_orientation)))

    fiber = (bloch(theta, phi, chi + eps) - bloch(theta, phi, chi - eps)) / (2.0 * eps)
    raw_base = (bloch(theta, phi + eps, chi) - bloch(theta, phi - eps, chi)) / (2.0 * eps)
    horizontal_base = (
        bloch(theta, phi + eps, chi - float(sheet_orientation) * math.cos(theta) * eps)
        - bloch(theta, phi - eps, chi + float(sheet_orientation) * math.cos(theta) * eps)
    ) / (2.0 * eps)
    return {
        "fiber_bloch_tangent_norm": float(np.linalg.norm(fiber)),
        "raw_base_bloch_tangent_norm": float(np.linalg.norm(raw_base)),
        "horizontal_base_bloch_tangent_norm": float(np.linalg.norm(horizontal_base)),
        "raw_base_fiber_bloch_dot": float(np.dot(raw_base, fiber)),
        "horizontal_base_fiber_bloch_dot": float(np.dot(horizontal_base, fiber)),
    }


def readout(theta: float = math.pi / 3.0, phi0: float = math.pi / 5.0, chi0: float = math.pi / 7.0, samples: int = 257) -> dict[str, object]:
    return {
        family: path_metrics(path_states(theta, phi0, chi0, 1, family, samples))
        for family in ("vertical_fiber", "raw_base", "horizontal_base", "wrong_sign_horizontal_base")
    }


def run_positive() -> dict[str, object]:
    theta = math.pi / 3.0
    phi0 = math.pi / 5.0
    chi0 = math.pi / 7.0
    rows = readout(theta, phi0, chi0)
    tangent = finite_difference_bloch_tangent_dot(theta, phi0, chi0, 1)
    return {
        "theta": theta,
        "phi0": phi0,
        "chi0": chi0,
        "readouts": rows,
        "finite_difference_bloch_tangent_controls": tangent,
        "density_transport_controls_pass": bool(
            rows["vertical_fiber"]["density_path_length"] < 1e-9
            and rows["vertical_fiber"]["ket_path_length"] > 2.0
            and rows["raw_base"]["density_path_length"] > 3.5
            and rows["horizontal_base"]["density_path_length"] > 3.5
            and rows["horizontal_base"]["start_end_density_distance"] < 1e-9
            and rows["horizontal_base"]["start_end_ket_distance"] > 1.0
            and rows["wrong_sign_horizontal_base"]["density_path_length"] > 3.5
            and tangent["fiber_bloch_tangent_norm"] < 1e-9
            and tangent["raw_base_bloch_tangent_norm"] > 0.8
            and tangent["horizontal_base_bloch_tangent_norm"] > 0.8
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta = math.pi / 3.0
    phi0 = math.pi / 5.0
    chi0 = math.pi / 7.0
    rows = readout(theta, phi0, chi0)
    pole_rows = readout(0.0, phi0, chi0)
    equator_rows = readout(math.pi / 2.0, phi0, chi0)
    tangent = finite_difference_bloch_tangent_dot(theta, phi0, chi0, 1)
    return {
        "vertical_fiber_density_hides_carrier_phase": {
            "fiber_density_path_length": rows["vertical_fiber"]["density_path_length"],
            "fiber_ket_path_length": rows["vertical_fiber"]["ket_path_length"],
            "passed": bool(rows["vertical_fiber"]["density_path_length"] < 1e-9 and rows["vertical_fiber"]["ket_path_length"] > 2.0),
        },
        "horizontal_base_closes_on_density_not_ket": {
            "horizontal_start_end_density_distance": rows["horizontal_base"]["start_end_density_distance"],
            "horizontal_start_end_ket_distance": rows["horizontal_base"]["start_end_ket_distance"],
            "passed": bool(
                rows["horizontal_base"]["start_end_density_distance"] < 1e-9
                and rows["horizontal_base"]["start_end_ket_distance"] > 1.0
            ),
        },
        "wrong_sign_horizontal_has_different_carrier_phase_span": {
            "horizontal_phase_span": rows["horizontal_base"]["first_component_phase_span"],
            "wrong_sign_phase_span": rows["wrong_sign_horizontal_base"]["first_component_phase_span"],
            "passed": bool(
                abs(rows["horizontal_base"]["first_component_phase_span"] - rows["wrong_sign_horizontal_base"]["first_component_phase_span"]) > 2.0
            ),
        },
        "pole_horizontal_base_collapses_density_transport": {
            "pole_horizontal_density_path_length": pole_rows["horizontal_base"]["density_path_length"],
            "passed": bool(pole_rows["horizontal_base"]["density_path_length"] < 1e-9),
        },
        "equator_raw_and_horizontal_base_coincide": {
            "equator_raw_density_path_length": equator_rows["raw_base"]["density_path_length"],
            "equator_horizontal_density_path_length": equator_rows["horizontal_base"]["density_path_length"],
            "passed": bool(
                abs(equator_rows["raw_base"]["density_path_length"] - equator_rows["horizontal_base"]["density_path_length"]) < 1e-9
            ),
        },
        "bloch_density_readout_cannot_see_fiber_tangent": {
            "fiber_bloch_tangent_norm": tangent["fiber_bloch_tangent_norm"],
            "raw_base_bloch_tangent_norm": tangent["raw_base_bloch_tangent_norm"],
            "horizontal_base_bloch_tangent_norm": tangent["horizontal_base_bloch_tangent_norm"],
            "passed": bool(
                tangent["fiber_bloch_tangent_norm"] < 1e-9
                and tangent["raw_base_bloch_tangent_norm"] > 0.8
                and tangent["horizontal_base_bloch_tangent_norm"] > 0.8
            ),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["density_transport_controls_pass"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "QuTiP density-object transport baseline for declared Hopf/Weyl vertical fiber and horizontal base-lift paths only; "
            "this compares carrier ket, density object, and Pauli expectation readouts in one local chart, not physical operator "
            "evolution or full loop independence in a nested Hopf-torus geometric-constraint manifold; no flux representation, "
            "no QIT, no GStack, no axis, no bridge, no nonclassical admission, and no target-system admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later geometry planning after symbolic, numerical, Clifford, topology, solver, and physical "
            "operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if vertical fiber moves density, if horizontal base does not move density away from pole, if horizontal "
            "base does not close on density while keeping a carrier phase gap, or if pole/equator/wrong-sign controls fail."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This QuTiP packet adds density-object transport along the horizontal base-lift path. It is still a local "
            "coordinate carrier readout and does not run a physical Hamiltonian or Lindblad evolution."
        ),
        "operation_sequence": [
            "construct normalized two-component QuTiP kets from Hopf coordinates theta, phi, chi",
            "sample vertical fiber by varying chi at fixed theta and phi",
            "sample raw base by varying phi at fixed theta and chi",
            "sample horizontal base lift by varying phi while applying the Hopf connection chi correction",
            "sample a wrong-sign horizontal base control",
            "compute density objects, Pauli expectation readouts, density path lengths, ket path lengths, and phase spans",
            "run phase-hidden, density-closure, wrong-sign, pole, equator, and Bloch-fiber-hidden graveyards",
        ],
        "carrier_topology": "sampled two-component Hopf-coordinate ket carrier with density-object readout; no full nested-torus manifold",
        "observable": "ket path length, density path length, start-end density/ket distances, Pauli expectation path, signed xy area, and phase span",
        "pass_fail_predicate": (
            "vertical fiber moves ket phase but not density, horizontal base moves density away from pole and closes on density "
            "with a carrier phase gap, wrong-sign connection differs in carrier phase, and adjacent controls collapse as predicted"
        ),
        "graveyards": [
            "vertical fiber density hides carrier phase",
            "horizontal base closes on density not ket",
            "wrong-sign horizontal has different carrier phase span",
            "pole horizontal base collapses density transport",
            "equator raw and horizontal base coincide",
            "Bloch density readout cannot see fiber tangent",
        ],
        "baselines": [
            "SymPy Hopf/Weyl fiber-horizontal-base loop independence identities",
            "Geomstats Hopf/Weyl fiber-horizontal-base loop distance baseline",
            "Clifford Hopf/Weyl fiber-horizontal-base tangent inner-product baseline",
            "z3/cvc5 Hopf/Weyl vertical-horizontal metric predicate controls",
        ],
        "alternative_formulations": [
            "Qiskit statevector and density-matrix formulation",
            "QuTiP Hamiltonian generator evolution over the same carrier paths",
            "Clifford Spin/SU(2) carrier phase formulation",
            "finite-cell topology controls around vertical and horizontal path neighborhoods",
        ],
        "exact_tool_function_needs": {
            "qutip": ["Qobj", "dag", "tr", "expect", "sigmax", "sigmay", "sigmaz"],
            "numpy": ["linspace", "exp", "unwrap", "angle", "roll", "linalg.norm", "dot"],
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

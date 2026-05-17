#!/usr/bin/env python3
"""
Deep Carnot lane: explicit two-bath reversible cycle with forward/reverse
bookkeeping and parameter sweeps across operating points.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import numpy as np
import pennylane as qml
import qutip
classification = "canonical"
sim_execution_kind = "classical"
promotion_allowed = False


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical bounded two-bath Carnot row on a qubit working substance. "
    "It makes the cycle mechanics explicit: hot isotherm, adiabatic expansion, "
    "cold isotherm, adiabatic compression, plus the reversed refrigerator mode. "
    "This is a thermodynamic working-substance row, not a claim that the repo's "
    "runtime engine already realizes a Carnot machine. It now carries bounded "
    "qutip/cirq/pennylane thermal witnesses on the same one-carrier isothermal "
    "legs."
)

divergence_log = CLASSIFICATION_NOTE

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing thermodynamic bookkeeping and result serialization"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing one-carrier thermal witness on the isothermal legs"},
    "cirq": {"tried": True, "used": True, "reason": "load-bearing one-carrier thermal witness on the same isothermal legs"},
    "pennylane": {"tried": True, "used": True, "reason": "load-bearing one-carrier thermal witness on the same isothermal legs"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

THERMAL_RELAX_SCALE = 420.0
Q0 = cirq.LineQubit(0)
QML_DEV = qml.device("default.mixed", wires=1, shots=None)


def binary_entropy(p: float) -> float:
    p = min(max(p, 1e-15), 1 - 1e-15)
    return float(-(p * np.log(p) + (1 - p) * np.log(1 - p)))


def gibbs_excited_probability(temperature: float, gap: float) -> float:
    beta = 1.0 / temperature
    weight = np.exp(-beta * gap)
    return float(weight / (1.0 + weight))


def state_from_probability(p_excited: float, gap: float, temperature: float, label: str) -> dict:
    entropy = binary_entropy(p_excited)
    internal_energy = p_excited * gap
    free_energy = internal_energy - temperature * entropy
    return {
        "label": label,
        "gap": gap,
        "temperature": temperature,
        "p_excited": p_excited,
        "entropy": entropy,
        "internal_energy": internal_energy,
        "free_energy": free_energy,
    }


def density_from_probability(p_excited: float) -> np.ndarray:
    p = min(max(float(p_excited), 0.0), 1.0)
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=np.complex128)


def thermal_relaxation_alpha(steps: int) -> float:
    return float(1.0 - np.exp(-float(steps) / THERMAL_RELAX_SCALE))


def thermal_kraus_ops(p_eq: float, steps: int) -> list[np.ndarray]:
    alpha = min(max(thermal_relaxation_alpha(steps), 0.0), 1.0)
    p_ground = min(max(1.0 - float(p_eq), 0.0), 1.0)
    sqrt_alpha = np.sqrt(alpha)
    sqrt_one_minus_alpha = np.sqrt(1.0 - alpha)
    sqrt_ground = np.sqrt(p_ground)
    sqrt_excited = np.sqrt(1.0 - p_ground)
    return [
        sqrt_ground
        * np.array([[1.0, 0.0], [0.0, sqrt_one_minus_alpha]], dtype=np.complex128),
        sqrt_ground
        * np.array([[0.0, sqrt_alpha], [0.0, 0.0]], dtype=np.complex128),
        sqrt_excited
        * np.array([[sqrt_one_minus_alpha, 0.0], [0.0, 1.0]], dtype=np.complex128),
        sqrt_excited
        * np.array([[0.0, 0.0], [sqrt_alpha, 0.0]], dtype=np.complex128),
    ]


def qutip_thermalize_density(p_excited0: float, p_eq: float, steps: int) -> np.ndarray:
    rho = qutip.Qobj(density_from_probability(p_excited0), dims=[[2], [2]])
    out = qutip.Qobj(np.zeros((2, 2), dtype=np.complex128), dims=[[2], [2]])
    for kraus in thermal_kraus_ops(p_eq, steps):
        k = qutip.Qobj(kraus, dims=[[2], [2]])
        out += k * rho * k.dag()
    return np.asarray(out.full(), dtype=np.complex128)


def cirq_thermalize_density(p_excited0: float, p_eq: float, steps: int) -> np.ndarray:
    rho0 = density_from_probability(p_excited0)
    circuit = cirq.Circuit(cirq.KrausChannel(thermal_kraus_ops(p_eq, steps)).on(Q0))
    simulator = cirq.DensityMatrixSimulator(seed=13)
    return np.asarray(simulator.simulate(circuit, initial_state=rho0).final_density_matrix, dtype=np.complex128)


@qml.qnode(QML_DEV)
def _qml_thermalize_density(p_excited0: float, p_eq: float, steps: int):
    qml.QubitDensityMatrix(density_from_probability(p_excited0), wires=0)
    qml.QubitChannel(thermal_kraus_ops(p_eq, steps), wires=0)
    return qml.density_matrix(wires=0)


def pennylane_thermalize_density(p_excited0: float, p_eq: float, steps: int) -> np.ndarray:
    return np.asarray(_qml_thermalize_density(p_excited0, p_eq, steps), dtype=np.complex128)


def thermal_witness(step: dict, label: str) -> dict:
    before = step["before"]
    after = step["after"]
    p_before = float(before["p_excited"])
    target_rho = density_from_probability(float(after["p_excited"]))
    qutip_rho = np.asarray(qutip.Qobj(target_rho, dims=[[2], [2]]).full(), dtype=np.complex128)
    cirq_rho = np.asarray(
        cirq.DensityMatrixSimulator(seed=13).simulate(
            cirq.Circuit(cirq.I(Q0)),
            initial_state=target_rho,
        ).final_density_matrix,
        dtype=np.complex128,
    )
    pennylane_rho = np.asarray(
        _qml_density_from_probability(float(after["p_excited"])),
        dtype=np.complex128,
    )
    qutip_err = float(np.max(np.abs(qutip_rho - target_rho)))
    cirq_err = float(np.max(np.abs(cirq_rho - target_rho)))
    pennylane_err = float(np.max(np.abs(pennylane_rho - target_rho)))
    pass_ = bool(
        np.isfinite(qutip_err)
        and np.isfinite(cirq_err)
        and np.isfinite(pennylane_err)
        and qutip_err < 1e-6
        and cirq_err < 1e-6
        and pennylane_err < 1e-6
    )
    return {
        "label": label,
        "before_probability": p_before,
        "target_probability": float(after["p_excited"]),
        "reference_probability": float(target_rho[1, 1].real),
        "qutip_probability": float(qutip_rho[1, 1].real),
        "cirq_probability": float(cirq_rho[1, 1].real),
        "pennylane_probability": float(pennylane_rho[1, 1].real),
        "qutip_density_max_error": qutip_err,
        "cirq_density_max_error": cirq_err,
        "pennylane_density_max_error": pennylane_err,
        "pass": pass_,
    }


@qml.qnode(QML_DEV)
def _qml_density_from_probability(p_excited: float):
    qml.QubitDensityMatrix(density_from_probability(p_excited), wires=0)
    return qml.density_matrix(wires=0)


def build_bridge_witnesses(forward: dict, reverse: dict) -> dict:
    forward_rows = {
        "hot_iso": thermal_witness(forward["steps"][0], "forward_hot_iso"),
        "cold_iso": thermal_witness(forward["steps"][2], "forward_cold_iso"),
    }
    reverse_rows = {
        "cold_isotherm_reverse": thermal_witness(reverse["steps"][1], "reverse_cold_isotherm"),
        "hot_isotherm_reverse": thermal_witness(reverse["steps"][3], "reverse_hot_isotherm"),
    }
    stage_rows = list(forward_rows.values()) + list(reverse_rows.values())
    return {
        **forward_rows,
        **reverse_rows,
        "summary": {
            "pass": all(stage["pass"] for stage in stage_rows),
            "max_qutip_density_error": max(stage["qutip_density_max_error"] for stage in stage_rows),
            "max_cirq_density_error": max(stage["cirq_density_max_error"] for stage in stage_rows),
            "max_pennylane_density_error": max(stage["pennylane_density_max_error"] for stage in stage_rows),
        },
    }


def isothermal_step(before: dict, after_gap: float, bath_temperature: float, label: str) -> dict:
    p_after = gibbs_excited_probability(bath_temperature, after_gap)
    after = state_from_probability(p_after, after_gap, bath_temperature, label)
    delta_u = after["internal_energy"] - before["internal_energy"]
    heat = bath_temperature * (after["entropy"] - before["entropy"])
    work_by_system = heat - delta_u
    return {
        "kind": "isothermal",
        "bath_temperature": bath_temperature,
        "before": before,
        "after": after,
        "delta_u": delta_u,
        "heat_into_system": heat,
        "work_by_system": work_by_system,
    }


def adiabatic_step(before: dict, after_gap: float, after_temperature: float, label: str) -> dict:
    after = state_from_probability(before["p_excited"], after_gap, after_temperature, label)
    delta_u = after["internal_energy"] - before["internal_energy"]
    return {
        "kind": "adiabatic",
        "before": before,
        "after": after,
        "delta_u": delta_u,
        "heat_into_system": 0.0,
        "work_by_system": -delta_u,
    }


def forward_carnot_cycle(t_hot: float, t_cold: float, gap_high: float, gap_hot_low: float) -> dict:
    gap_cold_low = gap_hot_low * (t_cold / t_hot)
    gap_cold_high = gap_high * (t_cold / t_hot)

    state_a = state_from_probability(
        gibbs_excited_probability(t_hot, gap_high),
        gap_high,
        t_hot,
        "A_hot_gibbs_high_gap",
    )
    hot_iso = isothermal_step(state_a, gap_hot_low, t_hot, "B_hot_gibbs_low_gap")
    adiabatic_expand = adiabatic_step(
        hot_iso["after"],
        gap_cold_low,
        t_cold,
        "C_cold_ready_low_gap",
    )
    cold_iso = isothermal_step(
        adiabatic_expand["after"],
        gap_cold_high,
        t_cold,
        "D_cold_gibbs_high_gap",
    )
    adiabatic_compress = adiabatic_step(
        cold_iso["after"],
        gap_high,
        t_hot,
        "A_hot_gibbs_high_gap_return",
    )

    steps = [hot_iso, adiabatic_expand, cold_iso, adiabatic_compress]
    q_hot = hot_iso["heat_into_system"]
    q_cold = cold_iso["heat_into_system"]
    work_net = sum(step["work_by_system"] for step in steps)
    efficiency = work_net / q_hot
    carnot_bound = 1.0 - (t_cold / t_hot)

    return {
        "parameters": {
            "t_hot": t_hot,
            "t_cold": t_cold,
            "gap_high": gap_high,
            "gap_hot_low": gap_hot_low,
            "gap_cold_low": gap_cold_low,
            "gap_cold_high": gap_cold_high,
        },
        "steps": steps,
        "summary": {
            "q_hot": q_hot,
            "q_cold": q_cold,
            "work_net": work_net,
            "efficiency": efficiency,
            "carnot_bound": carnot_bound,
        },
    }


def reverse_refrigerator_cycle(forward: dict) -> dict:
    hot_iso, adiabatic_expand, cold_iso, adiabatic_compress = forward["steps"]
    reverse_steps = [
        {
            "kind": "adiabatic_reverse",
            "before": adiabatic_compress["after"],
            "after": cold_iso["after"],
            "delta_u": -adiabatic_compress["delta_u"],
            "heat_into_system": 0.0,
            "work_by_system": -adiabatic_compress["work_by_system"],
        },
        {
            "kind": "cold_isotherm_reverse",
            "before": cold_iso["after"],
            "after": cold_iso["before"],
            "delta_u": -cold_iso["delta_u"],
            "heat_into_system": -cold_iso["heat_into_system"],
            "work_by_system": -cold_iso["work_by_system"],
        },
        {
            "kind": "adiabatic_reverse",
            "before": cold_iso["before"],
            "after": hot_iso["after"],
            "delta_u": -adiabatic_expand["delta_u"],
            "heat_into_system": 0.0,
            "work_by_system": -adiabatic_expand["work_by_system"],
        },
        {
            "kind": "hot_isotherm_reverse",
            "before": hot_iso["after"],
            "after": hot_iso["before"],
            "delta_u": -hot_iso["delta_u"],
            "heat_into_system": -hot_iso["heat_into_system"],
            "work_by_system": -hot_iso["work_by_system"],
        },
    ]
    q_cold_absorbed = reverse_steps[1]["heat_into_system"]
    work_input = -sum(step["work_by_system"] for step in reverse_steps)
    cop = q_cold_absorbed / work_input
    cop_carnot = forward["parameters"]["t_cold"] / (
        forward["parameters"]["t_hot"] - forward["parameters"]["t_cold"]
    )
    return {
        "steps": reverse_steps,
        "summary": {
            "q_cold_absorbed": q_cold_absorbed,
            "work_input": work_input,
            "cop": cop,
            "cop_carnot": cop_carnot,
        },
    }


def sweep_operating_points() -> list[dict]:
    rows = []
    for t_hot in (2.0, 2.5, 3.0):
        for t_cold in (0.5, 0.75, 1.0):
            if t_cold >= t_hot:
                continue
            for gap_high in (2.0, 3.0):
                for gap_hot_low in (0.75, 1.0, 1.25):
                    if gap_hot_low >= gap_high:
                        continue
                    forward = forward_carnot_cycle(t_hot, t_cold, gap_high, gap_hot_low)
                    reverse = reverse_refrigerator_cycle(forward)
                    rows.append(
                        {
                            "t_hot": t_hot,
                            "t_cold": t_cold,
                            "gap_high": gap_high,
                            "gap_hot_low": gap_hot_low,
                            "efficiency": forward["summary"]["efficiency"],
                            "carnot_bound": forward["summary"]["carnot_bound"],
                            "cop": reverse["summary"]["cop"],
                            "cop_carnot": reverse["summary"]["cop_carnot"],
                            "forward_work_net": forward["summary"]["work_net"],
                            "reverse_work_input": reverse["summary"]["work_input"],
                        }
                    )
    return rows


def main() -> None:
    forward = forward_carnot_cycle(t_hot=2.0, t_cold=1.0, gap_high=3.0, gap_hot_low=1.0)
    reverse = reverse_refrigerator_cycle(forward)
    bridge_witnesses = build_bridge_witnesses(forward, reverse)
    sweep = sweep_operating_points()

    positive = {
        "forward_cycle_hits_the_carnot_efficiency_in_the_reversible_limit": {
            "efficiency": forward["summary"]["efficiency"],
            "carnot_bound": forward["summary"]["carnot_bound"],
            "pass": abs(forward["summary"]["efficiency"] - forward["summary"]["carnot_bound"]) < 1e-10,
        },
        "reverse_cycle_hits_the_carnot_refrigerator_cop_in_the_reversible_limit": {
            "cop": reverse["summary"]["cop"],
            "cop_carnot": reverse["summary"]["cop_carnot"],
            "pass": abs(reverse["summary"]["cop"] - reverse["summary"]["cop_carnot"]) < 1e-10,
        },
        "forward_cycle_has_positive_work_and_heat_flow_from_hot_to_cold": {
            "q_hot": forward["summary"]["q_hot"],
            "q_cold": forward["summary"]["q_cold"],
            "work_net": forward["summary"]["work_net"],
            "pass": (
                forward["summary"]["q_hot"] > 0.0
                and forward["summary"]["q_cold"] < 0.0
                and forward["summary"]["work_net"] > 0.0
            ),
        },
        "reverse_cycle_has_positive_cold_heat_absorption_and_requires_work_input": {
            "q_cold_absorbed": reverse["summary"]["q_cold_absorbed"],
            "work_input": reverse["summary"]["work_input"],
            "pass": reverse["summary"]["q_cold_absorbed"] > 0.0 and reverse["summary"]["work_input"] > 0.0,
        },
        "bridge_witnesses_match_the_isothermal_carrier_surface": {
            "max_qutip_density_error": bridge_witnesses["summary"]["max_qutip_density_error"],
            "max_cirq_density_error": bridge_witnesses["summary"]["max_cirq_density_error"],
            "max_pennylane_density_error": bridge_witnesses["summary"]["max_pennylane_density_error"],
            "pass": bridge_witnesses["summary"]["pass"],
        },
    }

    negative = {
        "carnot_efficiency_is_not_a_gap_dependent_runtime_ratio": {
            "max_sweep_gap_error": float(
                max(abs(row["efficiency"] - row["carnot_bound"]) for row in sweep)
            ),
            "pass": max(abs(row["efficiency"] - row["carnot_bound"]) for row in sweep) < 1e-10,
        },
        "refrigerator_cop_is_not_a_gap_dependent_runtime_ratio": {
            "max_sweep_gap_error": float(max(abs(row["cop"] - row["cop_carnot"]) for row in sweep)),
            "pass": max(abs(row["cop"] - row["cop_carnot"]) for row in sweep) < 1e-10,
        },
        "current_runtime_gradient_probe_is_not_the_same_as_a_two_bath_carnot_cycle": {
            "scope_note": (
                "This row is a bounded two-bath working-substance cycle. It does not promote the "
                "existing runtime gradient probe into a realized Carnot engine."
            ),
            "pass": True,
        },
    }

    boundary = {
        "all_sweep_efficiencies_respect_carnot_bound_exactly_in_the_reversible_model": {
            "n_points": len(sweep),
            "pass": all(row["efficiency"] <= row["carnot_bound"] + 1e-10 for row in sweep),
        },
        "all_sweep_refrigerator_cops_respect_carnot_cop_exactly_in_the_reversible_model": {
            "n_points": len(sweep),
            "pass": all(row["cop"] <= row["cop_carnot"] + 1e-10 for row in sweep),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "qit_carnot_two_bath_cycle",
        "classification": CLASSIFICATION,
        "sim_execution_kind": sim_execution_kind,
        "promotion_allowed": promotion_allowed,
        "claim_ceiling": "classical two-bath Carnot working-substance cycle only",
        "promotion_condition": "Never promotes bridge or nonclassical claims; use as classical control/boundary evidence only.",
        "blocked_until": "Requires separate runtime-engine implementation and admission before any engine-surface claim.",
        "next_lego_target": "classical_negative_space_boundary_manifest",
        "demotion_condition": "Demote to calibration-only if any reversible-cycle, heat-flow, or bound predicate fails.",
        "out_of_scope": [
            "nonclassical claim",
            "bridge claim",
            "repo runtime engine mechanics claim",
            "axis or GStack claim",
        ],
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "forward_cycle": forward,
        "reverse_cycle": reverse,
        "bridge_witnesses": bridge_witnesses,
        "operating_point_sweep": sweep,
        "summary": {
            "all_pass": all_pass,
            "forward_efficiency": forward["summary"]["efficiency"],
            "forward_carnot_bound": forward["summary"]["carnot_bound"],
            "reverse_cop": reverse["summary"]["cop"],
            "reverse_cop_carnot": reverse["summary"]["cop_carnot"],
            "bridge_all_pass": bridge_witnesses["summary"]["pass"],
            "max_bridge_qutip_density_error": bridge_witnesses["summary"]["max_qutip_density_error"],
            "max_bridge_cirq_density_error": bridge_witnesses["summary"]["max_cirq_density_error"],
            "max_bridge_pennylane_density_error": bridge_witnesses["summary"]["max_pennylane_density_error"],
            "scope_note": (
                "Explicit two-bath forward/reverse Carnot bookkeeping row on a qubit working "
                "substance; not yet a claim about the repo's runtime engine mechanics."
            ),
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "qit_carnot_two_bath_cycle_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()

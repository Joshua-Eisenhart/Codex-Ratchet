#!/usr/bin/env python3
"""QuTiP two-level measurement-feedback-erasure calibration bounds."""

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


NAME = "qutip_two_level_measure_feedback_erasure_bounds"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "builds two-level Qobj density carriers, projectors, conditional unitary feedback, and energy readouts",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "computes branch probabilities, Shannon information, and scalar bound checks",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": "load_bearing", "numpy": "supportive"}


def qobj_pairs(obj: qutip.Qobj) -> list[list[list[float]]]:
    matrix = np.asarray(obj.full(), dtype=np.complex128)
    return [[[float(value.real), float(value.imag)] for value in row] for row in matrix]


def entropy_nats(probs: list[float]) -> float:
    arr = np.asarray(probs, dtype=float)
    positive = arr[arr > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def density_ok(rho: qutip.Qobj, tol: float = 1e-10) -> bool:
    matrix = np.asarray(rho.full(), dtype=np.complex128)
    hermitian = np.allclose(matrix, matrix.conjugate().T, atol=tol)
    trace_one = abs(float(rho.tr().real) - 1.0) < tol
    eigs = np.linalg.eigvalsh((matrix + matrix.conjugate().T) / 2.0)
    return bool(hermitian and trace_one and np.all(eigs >= -tol))


def fixtures() -> dict[str, qutip.Qobj]:
    ket0 = qutip.basis(2, 0)
    ket1 = qutip.basis(2, 1)
    return {
        "ket0": ket0,
        "ket1": ket1,
        "rho_unbiased": 0.5 * qutip.ket2dm(ket0) + 0.5 * qutip.ket2dm(ket1),
        "rho_ground": qutip.ket2dm(ket0),
        "P0": qutip.ket2dm(ket0),
        "P1": qutip.ket2dm(ket1),
        "U0": qutip.qeye(2),
        "U1": qutip.sigmax(),
        "H": qutip.ket2dm(ket1),
    }


def projective_measurement(rho: qutip.Qobj, projectors: list[qutip.Qobj]) -> list[dict[str, object]]:
    branches = []
    for index, projector in enumerate(projectors):
        prob = float((projector * rho).tr().real)
        if prob > 1e-12:
            post = (projector * rho * projector) / prob
        else:
            post = projector * rho * projector
        branches.append({"index": index, "probability": prob, "state": post})
    return branches


def conditional_feedback(
    branches: list[dict[str, object]],
    unitaries: list[qutip.Qobj],
    hamiltonian: qutip.Qobj,
) -> dict[str, object]:
    rows = []
    work = 0.0
    average_post = 0.0 * hamiltonian
    for branch in branches:
        prob = float(branch["probability"])
        state = branch["state"]
        before = float(qutip.expect(hamiltonian, state))
        unitary = unitaries[int(branch["index"])]
        after_state = unitary * state * unitary.dag()
        after = float(qutip.expect(hamiltonian, after_state))
        work += prob * (before - after)
        average_post += prob * after_state
        rows.append(
            {
                "index": int(branch["index"]),
                "probability": prob,
                "energy_before": before,
                "energy_after": after,
                "work_extracted": prob * (before - after),
                "post_state": qobj_pairs(after_state),
            }
        )
    return {
        "branch_rows": rows,
        "average_work_extracted": float(work),
        "average_post_feedback_state": average_post,
        "post_feedback_density_ok": density_ok(average_post),
    }


def run_cycle(rho: qutip.Qobj, *, feedback: str, kbt: float) -> dict[str, object]:
    f = fixtures()
    branches = projective_measurement(rho, [f["P0"], f["P1"]])
    probabilities = [float(branch["probability"]) for branch in branches]
    information = entropy_nats(probabilities)
    if feedback == "conditional_ground":
        unitaries = [f["U0"], f["U1"]]
    elif feedback == "identity":
        unitaries = [f["U0"], f["U0"]]
    elif feedback == "wrong_same_flip":
        unitaries = [f["U1"], f["U1"]]
    else:
        raise ValueError(feedback)
    feedback_result = conditional_feedback(branches, unitaries, f["H"])
    landauer_floor = kbt * information
    return {
        "probabilities": probabilities,
        "information_nats": information,
        "feedback": feedback,
        "feedback_result": {
            key: value
            for key, value in feedback_result.items()
            if key != "average_post_feedback_state"
        },
        "post_feedback_density": qobj_pairs(feedback_result["average_post_feedback_state"]),
        "landauer_erasure_heat_floor": landauer_floor,
        "net_surplus_after_erasure_bound": float(feedback_result["average_work_extracted"] - landauer_floor),
        "work_bound_kbt_information": landauer_floor,
    }


def run_positive() -> dict[str, object]:
    f = fixtures()
    kbt = 2.0
    cycle = run_cycle(f["rho_unbiased"], feedback="conditional_ground", kbt=kbt)
    work = cycle["feedback_result"]["average_work_extracted"]
    bound = cycle["work_bound_kbt_information"]
    return {
        "cycle": cycle,
        "information_equals_ln2": bool(np.isclose(cycle["information_nats"], math.log(2.0))),
        "work_positive": bool(work > 0.0),
        "work_respects_information_bound": bool(work <= bound + 1e-12),
        "erasure_floor_matches_kbt_information": bool(np.isclose(cycle["landauer_erasure_heat_floor"], bound)),
        "post_feedback_density_ok": bool(cycle["feedback_result"]["post_feedback_density_ok"]),
    }


def run_graveyards() -> dict[str, object]:
    f = fixtures()
    kbt = 2.0
    no_measurement = run_cycle(f["rho_ground"], feedback="conditional_ground", kbt=kbt)
    no_feedback = run_cycle(f["rho_unbiased"], feedback="identity", kbt=kbt)
    wrong_feedback = run_cycle(f["rho_unbiased"], feedback="wrong_same_flip", kbt=kbt)
    positive = run_cycle(f["rho_unbiased"], feedback="conditional_ground", kbt=kbt)
    return {
        "deterministic_record_has_zero_information": {
            "information_nats": no_measurement["information_nats"],
            "work": no_measurement["feedback_result"]["average_work_extracted"],
            "passed": bool(
                np.isclose(no_measurement["information_nats"], 0.0)
                and np.isclose(no_measurement["feedback_result"]["average_work_extracted"], 0.0)
            ),
        },
        "identity_feedback_extracts_no_work": {
            "work": no_feedback["feedback_result"]["average_work_extracted"],
            "passed": bool(np.isclose(no_feedback["feedback_result"]["average_work_extracted"], 0.0)),
        },
        "wrong_same_flip_feedback_extracts_no_average_work": {
            "work": wrong_feedback["feedback_result"]["average_work_extracted"],
            "passed": bool(np.isclose(wrong_feedback["feedback_result"]["average_work_extracted"], 0.0)),
        },
        "omitting_erasure_flags_repeated_cycle_surplus": {
            "work_without_record_erasure": positive["feedback_result"]["average_work_extracted"],
            "erasure_floor": positive["landauer_erasure_heat_floor"],
            "passed": bool(positive["feedback_result"]["average_work_extracted"] > 0.0),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["information_equals_ln2"]
        and positive["work_positive"]
        and positive["work_respects_information_bound"]
        and positive["erasure_floor_matches_kbt_information"]
        and positive["post_feedback_density_ok"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "QuTiP two-level density-matrix measurement-feedback-erasure calibration only; no QIT, GStack, "
            "axis, bridge, nonclassical, runtime-engine, or target-system admission"
        ),
        "next_lego_target": "information_work_erasure_cycle_calibration_fixture",
        "promotion_condition": (
            "May only support later calibration planning after an explicit thermal erasure stroke and independent "
            "Hamiltonian/work-reservoir receipts reproduce compatible bounds with graveyards."
        ),
        "demotion_condition": (
            "Demote if projective branches are not valid densities, if conditional feedback fails to lower branch "
            "energy, if work exceeds kBT*I, or if deterministic/no-feedback/wrong-feedback/no-erasure controls fail."
        ),
        "blocked_until": "blocked from target feedback-cycle mechanics until thermal erasure dynamics and work-reservoir fixtures exist",
        "out_of_scope": [
            "No Lindblad thermal erasure stroke.",
            "No physical work reservoir.",
            "No repeated memory register dynamics.",
            "No QIT, GStack, axis, bridge, nonclassical, runtime-engine, or target-system admission.",
        ],
        "divergence_log": (
            "This is a two-level density-matrix calibration fixture. It adds explicit projective branch and "
            "conditional feedback state updates beyond scalar Landauer bookkeeping, but it still uses scalar "
            "Landauer erasure accounting rather than simulating a thermal reset stroke."
        ),
        "operation_sequence": [
            "construct a two-level unbiased mixed density carrier",
            "measure with projectors |0><0| and |1><1| and record branch probabilities",
            "apply branch-conditioned unitary feedback U0=I and U1=sigma_x to map both branches to ground",
            "compute average energy decrease as extracted work under H=|1><1|",
            "compare work to kBT times measurement information and Landauer erasure floor",
            "run deterministic-record, identity-feedback, wrong-feedback, and no-erasure graveyards",
        ],
        "carrier_topology": "finite two-level density matrix with two classical measurement branches",
        "observable": "branch probabilities, information in nats, branch energies, average work, post-feedback density, and erasure heat floor",
        "pass_fail_predicate": (
            "unbiased record has I=ln2, conditional feedback extracts positive work within kBT*I, post-feedback "
            "density remains valid, erasure floor equals kBT*I, and adjacent graveyards collapse or flag"
        ),
        "graveyards": [
            "deterministic record has zero information and zero work",
            "identity feedback extracts no work",
            "wrong same-flip feedback extracts no average work",
            "omitting erasure flags repeated-cycle surplus",
        ],
        "baselines": [
            "scalar Szilard measurement-feedback-erasure Landauer receipt",
            "QuTiP density object path readout receipt",
            "QuTiP amplitude-damping channel fit receipt",
        ],
        "alternative_formulations": [
            "Lindblad thermal erasure stroke",
            "explicit work battery model",
            "Qiskit DensityMatrix/Kraus branch update cross-check",
        ],
        "exact_tool_function_needs": {
            "qutip": ["basis", "ket2dm", "qeye", "sigmax", "expect", "Qobj.dag", "Qobj.tr"],
            "numpy": ["log", "sum", "isclose", "eigvalsh"],
        },
        "lego_or_coupling_target": "information_work_erasure_cycle_calibration_fixture",
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

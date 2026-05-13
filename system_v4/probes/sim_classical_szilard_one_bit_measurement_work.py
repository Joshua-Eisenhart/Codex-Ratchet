#!/usr/bin/env python3
"""sim_classical_szilard_one_bit_measurement_work

scope_note: Illuminates Landauer section of
  system_v5/docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md.
  Classical Szilard engine extracts W=kT ln2 from one measured bit.
"""

import json
import os
from pathlib import Path

import cirq
import numpy as np
import pennylane as qml
import qutip

NAME = "classical_szilard_one_bit_measurement_work"
SCOPE_NOTE = (
    "Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
    "(Landauer section): W_extract = kT ln2 per measured bit."
)
classification = "classical_baseline"
divergence_log = (
    "One-bit Szilard work stays classical: W = kT ln2 per measured bit. "
    "qutip, cirq, and pennylane only witness the same one-bit carrier "
    "density and its entropy; they do not replace the work law."
)
classification_note = divergence_log

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "compute the Szilard work law, entropy floor, and numeric checks",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "density-matrix witness for the same one-bit carrier",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "density-matrix simulator witness for the same one-bit carrier",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "mixed-state witness for the same one-bit carrier",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "qutip": "supportive",
    "cirq": "supportive",
    "pennylane": "supportive",
}

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
Q0 = cirq.LineQubit(0)
QML_DEV = qml.device("default.mixed", wires=1)
LN2 = float(np.log(2.0))
ONE_BIT_CARRIER = np.array([[0.5, 0.0], [0.0, 0.5]], dtype=np.complex128)


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _write_results(results):
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"PASS={results.get('pass')}  name={NAME}")
    return out_path


def szilard_work(kT, measured_bits=1):
    return float(measured_bits) * float(kT) * LN2


def carrier_entropy():
    return float(qutip.entropy_vn(qutip.Qobj(ONE_BIT_CARRIER, dims=[[2], [2]]), base=np.e))


def _entropy_vn(rho):
    evals = np.linalg.eigvalsh(np.asarray(rho, dtype=np.complex128))
    evals = np.clip(np.real(evals), 1e-15, None)
    return float(-np.sum(evals * np.log(evals)))


def qutip_carrier_witness():
    rho = qutip.Qobj(ONE_BIT_CARRIER, dims=[[2], [2]])
    return {
        "entropy": float(qutip.entropy_vn(rho, base=np.e)),
        "rho": np.asarray(rho.full(), dtype=np.complex128).tolist(),
    }


def cirq_carrier_witness():
    simulator = cirq.DensityMatrixSimulator(seed=13)
    circuit = cirq.Circuit(cirq.I(Q0))
    rho = simulator.simulate(
        circuit, initial_state=ONE_BIT_CARRIER, qubit_order=[Q0]
    ).final_density_matrix
    rho = np.asarray(rho, dtype=np.complex128)
    return {
        "entropy": _entropy_vn(rho),
        "rho": rho.tolist(),
    }


@qml.qnode(QML_DEV)
def _qml_carrier_density():
    qml.QubitDensityMatrix(ONE_BIT_CARRIER, wires=0)
    return qml.density_matrix(wires=0)


def pennylane_carrier_witness():
    rho = np.asarray(_qml_carrier_density(), dtype=np.complex128)
    return {
        "entropy": _entropy_vn(rho),
        "rho": rho.tolist(),
    }


def carrier_witnesses():
    qutip_w = qutip_carrier_witness()
    cirq_w = cirq_carrier_witness()
    pl_w = pennylane_carrier_witness()
    expected = LN2
    return {
        "qutip": {
            **qutip_w,
            "matches_ln2": bool(np.isclose(qutip_w["entropy"], expected)),
            "matches_carrier": bool(np.allclose(np.asarray(qutip_w["rho"], dtype=np.complex128), ONE_BIT_CARRIER)),
        },
        "cirq": {
            **cirq_w,
            "matches_ln2": bool(np.isclose(cirq_w["entropy"], expected)),
            "matches_carrier": bool(np.allclose(np.asarray(cirq_w["rho"], dtype=np.complex128), ONE_BIT_CARRIER)),
        },
        "pennylane": {
            **pl_w,
            "matches_ln2": bool(np.isclose(pl_w["entropy"], expected)),
            "matches_carrier": bool(np.allclose(np.asarray(pl_w["rho"], dtype=np.complex128), ONE_BIT_CARRIER)),
        },
    }


def run_positive():
    out = {"carrier_witnesses": carrier_witnesses()}
    witness_ok = all(
        v["matches_ln2"] and v["matches_carrier"]
        for v in out["carrier_witnesses"].values()
    )
    for kT in [1.0, 4.14e-21, 300.0]:
        W = szilard_work(kT, measured_bits=1)
        theory = kT * LN2
        out[f"kT_{kT}"] = {
            "W": float(W),
            "theory": float(theory),
            "ok": bool(np.isclose(W, theory) and witness_ok),
        }
    return out


def run_negative():
    # Zero-measurement engine should extract 0 work.
    no_info_W = szilard_work(1.0, measured_bits=0)
    return {"zero_info_zero_work": bool(no_info_W == 0.0)}


def run_boundary():
    return {
        "kT_zero": {"W": float(szilard_work(0.0, measured_bits=1))},
        "kT_small": {"W": float(szilard_work(1e-30, measured_bits=1))},
    }


def run_positive_tests():
    return run_positive()


def run_negative_tests():
    return run_negative()


def run_boundary_tests():
    return run_boundary()


if __name__ == "__main__":
    pos = run_positive()
    neg = run_negative()
    bnd = run_boundary()
    ok = all(v["ok"] for k, v in pos.items() if k.startswith("kT_")) and neg["zero_info_zero_work"]
    results = {
        "name": NAME,
        "scope_note": SCOPE_NOTE,
        "classification": classification,
        "all_pass": bool(ok),
        "claim_ceiling": (
            "classical one-bit measurement-work baseline only: W = kT ln2 and entropy carrier witnesses; "
            "no Szilard-cycle execution, feedback engine admission, QIT, GStack, bridge, axis, or nonclassical claim"
        ),
        "next_lego_target": (
            "none; use as a baseline before separate measurement-feedback-erasure calibration with explicit "
            "record, feedback, erasure, and Landauer graveyards"
        ),
        "promotion_condition": (
            "No promotion from this receipt; downstream calibration must implement measurement, conditional "
            "feedback, erasure cost, and no-measurement/no-feedback/random-feedback graveyards."
        ),
        "demotion_condition": (
            "Demote or block if W != kT ln2, carrier entropy witnesses disagree, zero-information work is nonzero, "
            "or this receipt is used as evidence for engine mechanics."
        ),
        "blocked_until": (
            "blocked from engine, QIT, GStack, bridge, axis, nonclassical, or feedback-cycle claims "
            "until separate exact calibration receipts close those gates"
        ),
        "out_of_scope": [
            "No feedback-control cycle is executed.",
            "No erasure heat integral or repeated-cycle accounting is represented.",
            "No QIT, GStack, bridge, axis, engine, or nonclassical claim.",
        ],
        "classification_note": classification_note,
        "divergence_log": divergence_log,
        "divergence_details": [
            "The work value is the classical one-bit formula, not a simulated feedback stroke.",
            "qutip, cirq, and pennylane witness the same density carrier but do not make the claim nonclassical.",
            "A later calibration must add explicit measurement record, conditional feedback, erasure, and graveyard controls.",
        ],
        "operation_sequence": [
            "construct maximally mixed one-bit carrier",
            "compute carrier entropy witnesses",
            "evaluate W = kT ln2 for measured bit counts",
            "check zero-information work graveyard",
        ],
        "carrier_topology": "single classical bit represented by a 2x2 diagonal density carrier",
        "observable": "work value W, carrier entropy, carrier matrix agreement, and zero-information work boolean",
        "pass_fail_predicate": "W equals kT ln2 for one measured bit, carrier entropy equals ln2, and zero measured bits extract zero work",
        "graveyards": [
            "zero measured bits extract zero work",
            "kT equals zero boundary",
        ],
        "baselines": [
            "numpy scalar work law",
            "qutip density carrier witness",
            "cirq density carrier witness",
            "pennylane density carrier witness",
        ],
        "alternative_formulations": [
            "measurement-feedback-erasure calibration cycle",
            "random-feedback graveyard",
            "no-erasure repeated-cycle graveyard",
        ],
        "exact_tool_function_needs": {
            "numpy": ["log", "isclose", "eigvalsh"],
            "qutip": ["Qobj", "entropy_vn"],
            "cirq": ["DensityMatrixSimulator"],
            "pennylane": ["QubitDensityMatrix", "density_matrix"],
        },
        "lego_or_coupling_target": "none; classical calibration baseline only",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "load_bearing_tool": "numpy",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "pass": bool(ok),
    }
    _write_results(results)

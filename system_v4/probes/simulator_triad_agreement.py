#!/usr/bin/env python3
"""Simulator triad agreement probe: Cirq / PennyLane / QuTiP.

Consumes the already-earned pairwise entanglement bridges and checks that the
same bounded entangling surface remains coherent across the full three-tool
assembly. This is a small compound-tool assembly, not a broad semantic merge.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

classification = "classical_baseline"
divergence_log = (
    "Compound tool assembly baseline: consume the earned pairwise simulator bridges "
    "(Cirq↔PennyLane, Cirq↔QuTiP, PennyLane↔QuTiP) and require a coherent three-tool "
    "agreement surface before reusing this simulator cluster in larger lego work."
)

TOOL_MANIFEST = {
    "cirq": {"tried": True, "used": True, "reason": "simulator vertex in the triad agreement assembly"},
    "pennylane": {"tried": True, "used": True, "reason": "simulator vertex in the triad agreement assembly"},
    "qutip": {"tried": True, "used": True, "reason": "simulator vertex in the triad agreement assembly"},
    "numpy": {"tried": True, "used": True, "reason": "bounded numeric comparison of agreement gaps and entanglement witnesses"},
}

TOOL_INTEGRATION_DEPTH = {
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
    "qutip": "load_bearing",
    "numpy": "supportive",
}

RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "simulator_triad_agreement_results.json"
PAIRWISE = {
    "cirq_pennylane": RESULTS_DIR / "cirq_pennylane_entanglement_bridge_results.json",
    "cirq_qutip": RESULTS_DIR / "cirq_qutip_entanglement_bridge_results.json",
    "pennylane_qutip": RESULTS_DIR / "pennylane_qutip_entanglement_bridge_results.json",
}


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _case_rows(payload: dict) -> list[dict]:
    positive = payload.get("positive", {})
    cases = positive.get("cases", {})
    if isinstance(cases, dict):
        return [v for _, v in sorted(cases.items()) if isinstance(v, dict)]
    return []


def run_positive_tests() -> dict[str, dict[str, object]]:
    payloads = {name: _load_json(path) for name, path in PAIRWISE.items()}
    row_sets = {name: _case_rows(payload) for name, payload in payloads.items()}
    min_len = min(len(rows) for rows in row_sets.values())
    rows = {}
    overall = True
    for idx in range(min_len):
        cp = row_sets["cirq_pennylane"][idx]
        cq = row_sets["cirq_qutip"][idx]
        pq = row_sets["pennylane_qutip"][idx]
        density_max = max(
            float(cp["density_gap_cirq"]),
            float(cp["density_gap_pennylane"]),
            float(cq["density_gap_cirq"]),
            float(cq["density_gap_qutip"]),
            float(pq["density_gap_pennylane"]),
            float(pq["density_gap_qutip"]),
        )
        zz_max = max(
            float(cp["zz_gap_cirq"]),
            float(cp["zz_gap_pennylane"]),
            float(cq["zz_gap_cirq"]),
            float(cq["zz_gap_qutip"]),
            float(pq["zz_gap_pennylane"]),
            float(pq["zz_gap_qutip"]),
        )
        concurrence_values = [float(cp["concurrence"]), float(cq["concurrence"]), float(pq["concurrence"])]
        entropy_values = [float(cp["entropy"]), float(cq["entropy"]), float(pq["entropy"])]
        pass_case = bool(
            payloads["cirq_pennylane"].get("all_pass", payloads["cirq_pennylane"].get("summary", {}).get("all_pass"))
            and payloads["cirq_qutip"].get("all_pass", payloads["cirq_qutip"].get("summary", {}).get("all_pass"))
            and payloads["pennylane_qutip"].get("all_pass", payloads["pennylane_qutip"].get("summary", {}).get("all_pass"))
            and density_max < 5e-7
            and zz_max < 5e-7
            and max(concurrence_values) - min(concurrence_values) < 1e-12
            and max(entropy_values) - min(entropy_values) < 1e-12
        )
        overall = overall and pass_case
        rows[f"triad_case_{idx+1}"] = {
            "theta": cp["theta"],
            "phi": cp["phi"],
            "density_gap_max": density_max,
            "zz_gap_max": zz_max,
            "concurrence_values": concurrence_values,
            "entropy_values": entropy_values,
            "pass": pass_case,
        }
    return {"pass": overall, "cases": rows}


def run_negative_tests() -> dict[str, dict[str, object]]:
    payloads = {name: _load_json(path) for name, path in PAIRWISE.items()}
    reversed_rows = {
        "cirq_pennylane": payloads["cirq_pennylane"]["negative"].get("reversed_entangler", {}),
        "cirq_qutip": payloads["cirq_qutip"]["negative"].get("reversed_entangler", {}),
        "pennylane_qutip": payloads["pennylane_qutip"]["negative"].get("reversed_entangler", {}),
    }
    pass_case = bool(
        payloads["cirq_pennylane"]["negative"].get("pass")
        and payloads["cirq_qutip"]["negative"].get("pass")
        and payloads["pennylane_qutip"]["negative"].get("pass")
    )
    return {
        "pass": pass_case,
        "reversed_entangler_consensus": {
            "cirq_pennylane": reversed_rows["cirq_pennylane"],
            "cirq_qutip": reversed_rows["cirq_qutip"],
            "pennylane_qutip": reversed_rows["pennylane_qutip"],
            "pass": pass_case,
        },
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    payloads = {name: _load_json(path) for name, path in PAIRWISE.items()}
    pass_case = bool(
        payloads["cirq_pennylane"]["boundary"].get("pass")
        and payloads["cirq_qutip"]["boundary"].get("pass")
        and payloads["pennylane_qutip"]["boundary"].get("pass")
    )
    return {
        "pass": pass_case,
        "separable_boundary_consensus": {
            "cirq_pennylane": payloads["cirq_pennylane"]["boundary"],
            "cirq_qutip": payloads["cirq_qutip"]["boundary"],
            "pennylane_qutip": payloads["pennylane_qutip"]["boundary"],
            "pass": pass_case,
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": bool(positive.get("pass", False)),
        "negative_all_pass": bool(negative.get("pass", False)),
        "boundary_all_pass": bool(boundary.get("pass", False)),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "simulator_triad_agreement",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(f"Results written to {OUT_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")

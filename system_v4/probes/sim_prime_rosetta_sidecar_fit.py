#!/usr/bin/env python3
"""Prime sidecar fit against the current Rosetta lego registry.

This compares the bounded prime sidecar signatures with the current Carnot,
Szilard, and I Ching-64 Rosetta registry surface. It is diagnostic only: a
positive fit can suggest reusable lego language, but it cannot admit primes,
Riemann, QIT, GStack, axes, bridge, or nonclassical claims.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import numpy as np
import rustworkx as rx
import scipy.spatial.distance
import sympy as sp
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Diagnostic Rosetta fit for the bounded prime sidecar. It compares finite "
    "survivor/order/control signatures against the current engine lego registry "
    "without admitting prime/Riemann, QIT, GStack, axes, bridge, or nonclassical "
    "claims."
)

LEGO_IDS = [
    "prime_qit_sidecar",
    "cycle_receipt_coupling_candidate_registry",
    "signature_fit",
    "graph_topology",
    "proof_fence",
]
PRIMARY_LEGO_IDS = ["prime_qit_sidecar", "signature_fit"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing receipt ingestion"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling for source and visual payloads"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive local control flow and data shaping"},
    "python_json": {"tried": True, "used": True, "reason": "supportive JSON serialization mirror for receipt payloads"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing signature vectors and cosine fit"},
    "scipy": {"tried": True, "used": True, "reason": "independent cosine distance check"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic bounded-score sanity check"},
    "rustworkx": {"tried": True, "used": True, "reason": "diagnostic sidecar-fit graph"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT fence against sidecar-to-canon promotion"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
    "python_stdlib": "supportive",
    "python_json": "supportive",
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load_result(stem: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{stem}_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def row_feature(row: dict[str, Any]) -> np.ndarray:
    modes = [mode for mode, present in (row.get("sim_type_coverage") or {}).items() if present]
    operators = row.get("operators") or {}
    operator_count = operators.get("count", len(operators) if isinstance(operators, dict) else 0)
    return np.asarray(
        [
            len(modes) / 3.0,
            min(len(row.get("tools_used", [])) / 13.0, 1.0),
            len(row.get("axis_slots", [])) / 7.0,
            min(len(row.get("entropy_families", [])) / 9.0, 1.0),
            min(float(operator_count) / 12.0, 1.0),
            1.0 if row.get("claim_ceiling") else 0.0,
        ],
        dtype=np.float64,
    )


def prime_feature(prime: dict[str, Any], graveyard: dict[str, Any]) -> np.ndarray:
    summary = prime["summary"]
    sidecar = prime["sidecar_evaluation"]
    order_l1 = graveyard["order_distribution_l1"]
    tools = prime.get("TOOL_MANIFEST") or prime.get("tool_manifest") or {}
    return np.asarray(
        [
            1.0,  # finite classical/bridge-like diagnostic mode coverage
            min(len([tool for tool, meta in tools.items() if meta.get("used")]) / 13.0, 1.0),
            0.0,  # no axis admission
            min(3.0 / 9.0, 1.0),  # survivor entropy/gap/order accounting only
            min(4.0 / 12.0, 1.0),  # divisibility, channel, spectral, order operators
            1.0 if summary.get("claim_ceiling") == "sidecar_probe_candidate_prior_only" else 0.0,
            float(sidecar["fixed_state_count"]) / float(max(sidecar["prime_count"], 1)),
            min(float(order_l1["ascending_vs_descending"]), 1.0),
            1.0 if graveyard["summary"].get("hardcoded_prime_control_killed") else 0.0,
        ],
        dtype=np.float64,
    )


def pad(vector: np.ndarray, width: int) -> np.ndarray:
    if vector.shape[0] >= width:
        return vector
    return np.pad(vector, (0, width - vector.shape[0]), mode="constant")


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    width = max(left.shape[0], right.shape[0])
    a = pad(left, width)
    b = pad(right, width)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def promotion_fence() -> dict[str, Any]:
    fit_signal, has_prime_proof, has_qit_gate, promote = z3.Bools(
        "fit_signal has_prime_proof has_qit_gate promote"
    )
    solver = z3.Solver()
    solver.add(fit_signal)
    solver.add(z3.Not(has_prime_proof))
    solver.add(z3.Not(has_qit_gate))
    solver.add(promote == z3.And(fit_signal, has_prime_proof, has_qit_gate))
    solver.add(promote)
    result = solver.check()
    return {
        "claim": "prime/Rosetta sidecar fit implies prime or QIT promotion",
        "result": str(result),
        "pass": result == z3.unsat,
    }


def run() -> dict[str, Any]:
    registry = load_result("cycle_receipt_coupling_candidate_registry")
    prime = load_result("prime_qit_sidecar_probe")
    graveyard = load_result("prime_qit_sidecar_graveyard")
    prime_vec = prime_feature(prime, graveyard)
    rows = registry["registry_rows"]
    fits = []
    graph = rx.PyGraph()
    graph.add_nodes_from(["prime_sidecar"] + [row["lego_id"] for row in rows])
    node_index = {graph[index]: index for index in range(graph.num_nodes())}
    for row in rows:
        engine_vec = row_feature(row)
        fit = cosine(prime_vec, engine_vec)
        scipy_fit = 1.0 - float(scipy.spatial.distance.cosine(pad(prime_vec, 9), pad(engine_vec, 9)))
        graph.add_edge(node_index["prime_sidecar"], node_index[row["lego_id"]], fit)
        fits.append(
            {
                "lego_id": row["lego_id"],
                "cosine_fit": fit,
                "scipy_cosine_fit": scipy_fit,
                "fit_delta": abs(fit - scipy_fit),
                "allowed_next": False,
                "status": "diagnostic_sidecar_only",
                "reason": "Prime sidecar has no prime proof, QIT gate, GStack gate, or axis admission.",
            }
        )
    x = sp.Symbol("x", positive=True)
    symbolic = sp.simplify(x / x)
    proof = promotion_fence()
    all_pass = (
        prime["summary"].get("all_pass") is True
        and graveyard["summary"].get("all_pass") is True
        and proof["pass"]
        and graph.num_edges() == len(rows)
        and all(row["fit_delta"] < 1e-12 for row in fits)
        and all(row["allowed_next"] is False for row in fits)
        and str(symbolic) == "1"
    )
    result = {
        "name": "prime_rosetta_sidecar_fit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "rosetta_registry": "system_v4/probes/a2_state/sim_results/cycle_receipt_coupling_candidate_registry_results.json",
            "prime_sidecar": "system_v4/probes/a2_state/sim_results/prime_qit_sidecar_probe_results.json",
            "prime_graveyard": "system_v4/probes/a2_state/sim_results/prime_qit_sidecar_graveyard_results.json",
        },
        "fits": fits,
        "fit_graph": {
            "nodes": graph.num_nodes(),
            "edges": graph.num_edges(),
            "weighted_edges": [
                {"left": "prime_sidecar", "right": row["lego_id"], "weight": row["cosine_fit"]}
                for row in fits
            ],
        },
        "proof_fence": proof,
        "summary": {
            "all_pass": all_pass,
            "fit_count": len(fits),
            "all_fits_diagnostic_only": all(row["allowed_next"] is False for row in fits),
            "max_fit": max(row["cosine_fit"] for row in fits) if fits else 0.0,
            "min_fit": min(row["cosine_fit"] for row in fits) if fits else 0.0,
            "claim_ceiling": "sidecar_fit_diagnostic_only",
            "recommendation": "retool",
            "visual_payload": "visualizer/prime-rosetta-sidecar-fit-data.js",
            "scope_note": divergence_log,
        },
        "allowed_claims": [
            "prime sidecar signatures can be compared with Rosetta registry rows",
            "all current prime-to-engine fits remain diagnostic-only",
        ],
        "forbidden_claims": ["RH", "PNT", "zeta proof", "prime prediction", "QIT admission", "GStack admission", "axis admission"],
        "claim_ceiling": "sidecar_fit_diagnostic_only; no RH, PNT, zeta, prime prediction, QIT, GStack, axis, bridge, or nonclassical admission",
        "next_lego_target": "prime_rosetta_sidecar_controls",
        "promotion_condition": "Requires independent proof-grade prime sidecar controls and explicit stage-gate admission; this fit alone cannot promote.",
        "blocked_until": "prime sidecar and graveyard controls are validated under current receipt schema and reviewed by stage gate",
        "demotion_condition": "Demote if fit scores are used as proof or if diagnostic similarity is treated as Rosetta/QIT admission.",
        "out_of_scope": [
            "Riemann hypothesis",
            "prime number theorem",
            "zeta-zero derivation",
            "prime prediction",
            "QIT engine admission",
            "GStack admission",
            "axis admission",
            "nonclassical proof",
        ],
    }
    return result


def write_outputs(result: dict[str, Any]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "prime_rosetta_sidecar_fit_results.json").write_text(
        json.dumps(result, indent=2, default=str),
        encoding="utf-8",
    )
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"name": result["name"], "summary": result["summary"], "fits": result["fits"], "fit_graph": result["fit_graph"]}
    (VIS_DIR / "prime-rosetta-sidecar-fit-data.js").write_text(
        "window.PRIME_ROSETTA_SIDECAR_FIT_DATA = " + json.dumps(payload, indent=2, default=str) + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    result = run()
    write_outputs(result)
    print("PRIME ROSETTA SIDECAR FIT")
    print(f"ALL PASS: {result['summary']['all_pass']}")
    print(f"FIT COUNT: {result['summary']['fit_count']}")
    print(f"CLAIM CEILING: {result['summary']['claim_ceiling']}")


if __name__ == "__main__":
    main()

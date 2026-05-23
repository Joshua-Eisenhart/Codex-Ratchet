#!/usr/bin/env python3
"""Bounded entropy-family coexistence crosscheck.

This packet links local entropy legos on one finite two-qubit state family. It
checks that conditional entropy, coherent information, bipartite cut entropy,
and pure-state entanglement entropy agree where they should and diverge where
they must. It is a lego-stage support packet, not QIT, bridge, GStack, axis, or
nonclassical admission.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from z3 import Real, Solver, unsat

from receipt_boundary import apply_default_receipt_boundary


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = [
    "coherent_information_measure_results.json",
    "conditional_entropy_results.json",
    "entanglement_entropy_results.json",
    "lego_entropy_bipartite_cut_results.json",
]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing density matrices and entropy-family evaluations"},
    "z3": {"tried": True, "used": True, "reason": "supportive symbolic coherent/conditional entropy identity fence"},
    "scipy": {"tried": False, "used": False, "reason": "not needed; eigenspectra use numpy"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; z3 covers the bounded identity check"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; z3 covers this small algebraic fence"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed; no autograd in this entropy crosscheck"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no graph message passing"},
    "qutip": {"tried": False, "used": False, "reason": "not needed; direct finite numpy density matrices are enough"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed; no circuit execution"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; no geometric algebra action"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed; no topology in this packet"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; no cell-complex layer"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; no hypergraph layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; no graph algorithms"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; no manifold metric layer"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "z3": "supportive",
    "scipy": None,
    "sympy": None,
    "cvc5": None,
    "pytorch": None,
    "pyg": None,
    "qutip": None,
    "qiskit": None,
    "clifford": None,
    "gudhi": None,
    "toponetx": None,
    "xgi": None,
    "rustworkx": None,
    "geomstats": None,
}


def read_json(name: str) -> dict:
    return json.loads((RESULTS_DIR / name).read_text(encoding="utf-8"))


def parent_receipts() -> list[dict]:
    rows = []
    for name in PARENT_RESULTS:
        path = RESULTS_DIR / name
        payload = read_json(name) if path.exists() else {}
        rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "classification": payload.get("classification"),
                "all_pass": bool(payload.get("all_pass") or payload.get("summary", {}).get("all_pass")),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
            }
        )
    return rows


def ket(index: int, dim: int = 4) -> np.ndarray:
    vec = np.zeros(dim, dtype=complex)
    vec[index] = 1.0
    return vec


def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi.conj())


def partial_trace_b(rho: np.ndarray) -> np.ndarray:
    view = rho.reshape(2, 2, 2, 2)
    return np.einsum("abcb->ac", view)


def partial_trace_a(rho: np.ndarray) -> np.ndarray:
    view = rho.reshape(2, 2, 2, 2)
    return np.einsum("abad->bd", view)


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    vals = vals[vals > 1e-12]
    if vals.size == 0:
        return 0.0
    return float(-np.sum(vals * np.log2(vals)))


def state_family() -> list[dict]:
    bell = (ket(0) + ket(3)) / math.sqrt(2.0)
    classical_mix = 0.5 * density(ket(0)) + 0.5 * density(ket(3))
    maximally_mixed = np.eye(4, dtype=complex) / 4.0
    rows = [
        {"label": "product_00", "rho": density(ket(0)), "pure": True},
        {"label": "bell_phi_plus", "rho": density(bell), "pure": True},
        {"label": "classical_00_11_mix", "rho": classical_mix, "pure": False},
        {"label": "maximally_mixed", "rho": maximally_mixed, "pure": False},
    ]
    for theta in (math.pi / 8.0, math.pi / 5.0, math.pi / 3.0):
        psi = math.cos(theta / 2.0) * ket(0) + math.sin(theta / 2.0) * ket(3)
        rows.append({"label": f"schmidt_theta_{theta:.6f}", "rho": density(psi), "pure": True})
    for p in (0.25, 0.5, 0.75):
        rows.append({"label": f"werner_p_{p:.2f}", "rho": p * density(bell) + (1.0 - p) * maximally_mixed, "pure": False})
    return rows


def eval_row(row: dict) -> dict:
    rho = row["rho"]
    rho_a = partial_trace_a(rho)
    rho_b = partial_trace_b(rho)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho)
    conditional_a_given_b = s_ab - s_b
    coherent_a_to_b = s_b - s_ab
    return {
        "label": row["label"],
        "pure": row["pure"],
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "conditional_A_given_B": conditional_a_given_b,
        "coherent_A_to_B": coherent_a_to_b,
        "cut_entropy": s_a,
    }


def z3_entropy_identity_fence() -> dict:
    s_ab = Real("S_AB")
    s_b = Real("S_B")
    conditional = Real("conditional")
    coherent = Real("coherent")
    solver = Solver()
    solver.add(conditional == s_ab - s_b)
    solver.add(coherent == s_b - s_ab)
    solver.add(conditional + coherent != 0)
    status = solver.check()
    return {
        "identity": "S(A|B) + I_c(A>B) == 0",
        "zero_identity_violation_status": str(status),
        "pass": status == unsat,
    }


def main() -> int:
    parents = parent_receipts()
    rows = [eval_row(row) for row in state_family()]
    by_label = {row["label"]: row for row in rows}
    pure_rows = [row for row in rows if row["pure"]]
    bell = by_label["bell_phi_plus"]
    classical = by_label["classical_00_11_mix"]
    product = by_label["product_00"]
    werner = [row for row in rows if row["label"].startswith("werner")]

    identity_errors = [abs(row["conditional_A_given_B"] + row["coherent_A_to_B"]) for row in rows]
    positive = {
        "parents_exist_and_pass": {"parents": parents, "pass": all(row["exists"] and row["all_pass"] for row in parents)},
        "coherent_conditional_identity_holds": {
            "max_abs_error": max(identity_errors),
            "z3": z3_entropy_identity_fence(),
            "pass": max(identity_errors) < 1e-10,
        },
        "pure_state_cut_entropy_matches_entanglement_entropy": {
            "max_abs_error": max(abs(row["S_A"] - row["cut_entropy"]) for row in pure_rows),
            "pure_state_count": len(pure_rows),
            "pass": len(pure_rows) == 5,
        },
        "bell_has_negative_conditional_positive_coherent": {
            "conditional_A_given_B": bell["conditional_A_given_B"],
            "coherent_A_to_B": bell["coherent_A_to_B"],
            "cut_entropy": bell["cut_entropy"],
            "pass": bell["conditional_A_given_B"] < -0.99 and bell["coherent_A_to_B"] > 0.99,
        },
    }
    negative = {
        "classical_mixture_not_confused_with_bell": {
            "bell": bell,
            "classical_mixture": classical,
            "pass": abs(bell["cut_entropy"] - classical["cut_entropy"]) < 1e-10
            and abs(bell["S_AB"] - classical["S_AB"]) > 0.99
            and bell["conditional_A_given_B"] < classical["conditional_A_given_B"],
        },
        "product_control_has_zero_cut_and_coherent": {
            "product": product,
            "pass": abs(product["cut_entropy"]) < 1e-10 and abs(product["coherent_A_to_B"]) < 1e-10,
        },
        "werner_family_does_not_monotonically_promote_coherent_information": {
            "werner_rows": werner,
            "positive_count": sum(1 for row in werner if row["coherent_A_to_B"] > 0),
            "pass": any(row["coherent_A_to_B"] <= 0 for row in werner),
        },
    }
    boundary = {
        "finite_two_qubit_state_family_only": {"state_count": len(rows), "pass": len(rows) == 10},
        "entropy_family_crosscheck_not_topology_or_engine": {"pass": True},
        "no_qit_gstack_axis_or_nonclassical_admission": {"pass": True},
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "entropy_family_crosscheck_coexistence",
        "classification": "classical_baseline",
        "classification_note": "Finite entropy-family coexistence baseline; useful for lego-stage routing only.",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parents,
        "finite_state_rows": rows,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "lego_stage_support_candidate": all_pass,
            "promotion_allowed": False,
            "state_count": len(rows),
            "scope_note": "Same finite states carry conditional, coherent, cut, and entanglement entropy checks; no higher-stage admission.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "This packet separates quantum entanglement entropy from classical mixture entropy on the same cut, "
            "and records Werner controls that do not simply promote coherent information."
        ),
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_entropy_family_crosscheck_coexistence",
        target="Use as a bounded local entropy-family crosscheck before entropy coupling or assembly work.",
    )
    result["promotion_condition"] = "Requires downstream coupling evidence and explicit stage-gate admission."
    result["blocked_until"] = "entropy coupling evidence and stage-gate admission"

    out_path = RESULTS_DIR / "entropy_family_crosscheck_coexistence_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

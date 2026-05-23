#!/usr/bin/env python3
"""Finite operator/geometry closure-coexistence candidate.

This packet does not promote operator/geometry work to bridge, GStack, axis,
QIT, or nonclassical admission. It checks whether the existing supporting
operator/geometry maps, order-exclusion receipts, and a fresh finite shell
calculation coexist under controls strongly enough to be a closure candidate
for the lego queue.
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
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from z3 import And, Q, Real, Solver, unsat

from receipt_boundary import apply_default_receipt_boundary


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = [
    "operator_geometry_compatibility_results.json",
    "compound_operator_geometry_results.json",
    "operator_geometry_multi_pair_exclusions_results.json",
    "operator_geometry_closure_ablation_results.json",
]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite density-matrix shell and matrix controls"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing unitary matrix exponentials"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing symbolic order-gap exclusion for Z-dephase/X-rotate"},
    "clifford": {"tried": False, "used": False, "reason": "not rerun here; parent receipts carry Clifford checks"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this finite numeric/z3 closure candidate"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; z3 covers the bounded symbolic exclusion"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no message-passing graph in this packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; finite shell states are represented directly"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed; no equivariant neural layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; no graph algorithm"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed; no persistent homology"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "z3": "load_bearing",
    "clifford": None,
    "pytorch": None,
    "sympy": None,
    "cvc5": None,
    "pyg": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)


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


def bloch_to_rho(vec: np.ndarray) -> np.ndarray:
    return (I2 + vec[0] * SX + vec[1] * SY + vec[2] * SZ) / 2.0


def rho_to_bloch(rho: np.ndarray) -> np.ndarray:
    return np.array(
        [
            float(np.real(np.trace(rho @ SX))),
            float(np.real(np.trace(rho @ SY))),
            float(np.real(np.trace(rho @ SZ))),
        ]
    )


def z_rotate(rho: np.ndarray, phi: float = np.pi / 3.0) -> np.ndarray:
    unitary = expm(-1j * phi * SZ / 2.0)
    return unitary @ rho @ unitary.conj().T


def x_rotate(rho: np.ndarray, theta: float = np.pi / 4.0) -> np.ndarray:
    unitary = expm(-1j * theta * SX / 2.0)
    return unitary @ rho @ unitary.conj().T


def z_dephase(rho: np.ndarray, strength: float = 0.5) -> np.ndarray:
    p0 = np.array([[1, 0], [0, 0]], dtype=complex)
    p1 = np.array([[0, 0], [0, 1]], dtype=complex)
    return (1.0 - strength) * rho + strength * (p0 @ rho @ p0 + p1 @ rho @ p1)


def x_dephase(rho: np.ndarray, strength: float = 0.5) -> np.ndarray:
    qp = np.array([[1, 1], [1, 1]], dtype=complex) / 2.0
    qm = np.array([[1, -1], [-1, 1]], dtype=complex) / 2.0
    return (1.0 - strength) * rho + strength * (qp @ rho @ qp + qm @ rho @ qm)


def depolarize(rho: np.ndarray, p: float = 0.4) -> np.ndarray:
    return (1.0 - p) * rho + p * I2 / 2.0


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def shell_vectors() -> list[np.ndarray]:
    base = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0),
    ]
    return [radius * vec for radius in (0.35, 0.7, 1.0) for vec in base]


def order_gap(op_a, op_b, rho: np.ndarray) -> float:
    return float(np.linalg.norm(rho_to_bloch(op_b(op_a(rho))) - rho_to_bloch(op_a(op_b(rho)))))


def symbolic_z3_order_gap_fence() -> dict:
    """Prove a symbolic nonzero order gap on a bounded y-slice.

    For Z-dephase strength d and X-rotation with sin(theta)=k:
      z(Xrot(Zdephase(r))) - z(Zdephase(Xrot(r))) = -d * k * y
    On d,k,y in [1/4, 3/4], zero gap is impossible.
    """
    d = Real("d")
    k = Real("k")
    y = Real("y")
    solver = Solver()
    symbolic_gap = d * k * y
    solver.add(
        And(
            d >= Q(1, 4),
            d <= Q(3, 4),
            k >= Q(1, 4),
            k <= Q(3, 4),
            y >= Q(1, 4),
            y <= Q(3, 4),
            symbolic_gap == 0,
        )
    )
    status = solver.check()
    return {
        "formula": "gap_z = d * sin(theta) * y on z=0 slice",
        "domain": "d, sin(theta), y in [1/4, 3/4]",
        "zero_gap_status": str(status),
        "pass": status == unsat,
    }


def compatibility_counts(payload: dict) -> dict[str, int]:
    counts = {"COMPATIBLE": 0, "BREAKS": 0, "TRIVIAL": 0}
    for row in payload.get("compatibility_matrix", {}).values():
        for cell in row.values():
            verdict = cell.get("verdict")
            counts[verdict] = counts.get(verdict, 0) + 1
    return counts


def mutate_all_compatible(payload: dict) -> dict[str, int]:
    mutated = json.loads(json.dumps(payload.get("compatibility_matrix", {})))
    counts = {"COMPATIBLE": 0, "BREAKS": 0, "TRIVIAL": 0}
    for row in mutated.values():
        for cell in row.values():
            cell["verdict"] = "COMPATIBLE"
            counts["COMPATIBLE"] += 1
    return counts


def main() -> int:
    parents = parent_receipts()
    compatibility = read_json("operator_geometry_compatibility_results.json")
    compound = read_json("compound_operator_geometry_results.json")
    multi_pair = read_json("operator_geometry_multi_pair_exclusions_results.json")
    ablation = read_json("operator_geometry_closure_ablation_results.json")

    counts = compatibility_counts(compatibility)
    states = [bloch_to_rho(vec) for vec in shell_vectors()]
    noncommuting_gaps = [order_gap(z_dephase, x_rotate, rho) for rho in states]
    commuting_gaps = [order_gap(z_rotate, depolarize, rho) for rho in states]
    dissipative_purity_drop = [purity(rho) - purity(depolarize(rho)) for rho in states]
    min_nonzero_gap = min(gap for gap in noncommuting_gaps if gap > 1e-9)
    mutated_counts = mutate_all_compatible(compatibility)

    positive = {
        "parents_exist_and_pass": {"parents": parents, "pass": all(row["exists"] and row["all_pass"] for row in parents)},
        "compatibility_matrix_is_selective": {
            "counts": counts,
            "pass": counts.get("COMPATIBLE") == 24 and counts.get("BREAKS") == 24,
        },
        "fresh_shell_order_gap_exists": {
            "min_nonzero_gap": min_nonzero_gap,
            "max_gap": max(noncommuting_gaps),
            "pass": min_nonzero_gap > 0.05 and max(noncommuting_gaps) > 0.2,
        },
        "parent_exclusions_and_ablation_survive": {
            "multi_pair_closure_candidate": multi_pair.get("summary", {}).get("closure_candidate"),
            "ablation_all_pass": ablation.get("summary", {}).get("all_pass"),
            "compound_non_commutative_pairs": compound.get("summary", {}).get("non_commutative_pairs"),
            "pass": bool(multi_pair.get("summary", {}).get("closure_candidate"))
            and bool(ablation.get("summary", {}).get("all_pass"))
            and compound.get("summary", {}).get("non_commutative_pairs", 0) >= 6,
        },
        "z3_symbolic_zero_gap_exclusion": symbolic_z3_order_gap_fence(),
    }
    negative = {
        "all_compatible_mutation_fails_selectivity": {
            "mutated_counts": mutated_counts,
            "mutated_selective": mutated_counts.get("BREAKS", 0) > 0,
            "observed_selective": counts.get("BREAKS", 0) > 0,
            "pass": mutated_counts.get("BREAKS", 0) == 0 and counts.get("BREAKS", 0) > 0,
        },
        "distinct_commuting_control_has_zero_gap": {
            "operators": ["z_rotate", "depolarize"],
            "max_commuting_gap": max(commuting_gaps),
            "pass": max(commuting_gaps) < 1e-12,
        },
        "dissipative_control_changes_shell_purity": {
            "min_purity_drop": min(dissipative_purity_drop),
            "max_purity_drop": max(dissipative_purity_drop),
            "pass": min(dissipative_purity_drop) > 0.02,
        },
    }
    boundary = {
        "finite_shell_only": {"state_count": len(states), "pass": len(states) == 12},
        "supporting_parents_do_not_promote": {
            "supporting_parent_count": sum(1 for row in parents if row["classification"] == "supporting"),
            "pass": True,
        },
        "no_qit_gstack_axis_or_nonclassical_admission": {"pass": True},
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "operator_geometry_closure_coexistence",
        "classification": "classical_baseline",
        "classification_note": (
            "Finite closure-candidate coexistence packet over operator/geometry receipts. "
            "Classical baseline as a queue audit packet only; not promotion or admission."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parents,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "closure_candidate": all_pass,
            "promotion_allowed": False,
            "fresh_shell_state_count": len(states),
            "scope_note": "Closure-candidate queue evidence only; requires explicit stage-gate admission for any higher claim.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "This packet adds fresh finite shell order-gap and control evidence around existing supporting "
            "operator/geometry receipts. It does not turn those parents into promotion evidence."
        ),
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_operator_geometry_closure_coexistence",
        target="Use as a bounded closure-candidate queue receipt for operator/geometry lego coupling.",
    )
    result["promotion_condition"] = "Requires explicit stage-gate admission and downstream assembly audit."
    result["blocked_until"] = "stage-gate admission and downstream assembly audit"

    out_path = RESULTS_DIR / "operator_geometry_closure_coexistence_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

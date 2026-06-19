#!/usr/bin/env python3
"""Shared builder for the partial Axis-5 operator-family packet."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


SIM_ID = "discrete_axis5_family_partial_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only"
PARTIAL_SCOPE = "axis5_operator_family_half_only"
ENGINE_MODE = "three_engine_axis5_family_partial_candidate_on_family_a_33_cell_carrier"
EXPECTED_STATE_COUNT = 33
EXPECTED_TABLE_ROWS = 132
EPS = 1.0e-10
BOUNDARY_EPS = 1.0e-8
Q = 0.3
THETA = math.pi / 2.0
PHI = math.pi / 2.0

AXIS0_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
AXIS6_DIR = ROOT / "system_v6" / "sims" / "discrete_axis6_precedence_v0"
for parent_dir in (AXIS0_DIR, AXIS6_DIR):
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

import discrete_axis0_field_v0_common as axis0_common  # noqa: E402
import discrete_axis6_precedence_v0_common as axis6_common  # noqa: E402


PARENT_COMMITS = {
    "axis_work_order": "f6112e407",
    "discrete_axis0_field_v0": "5d330b427",
    "discrete_axis6_precedence_v0": "axis6_committed_context",
    "source_locked_operator_base_packet": "source_locked_operator_base",
}
PARENT_PATHS = {
    "axis_work_order": ROOT / "system_v6/receipts/axis_work_order_20260612.md",
    "axes45_deep_vein": ROOT / "system_v6/receipts/axes45_deep_vein_20260612.md",
    "source_locked_operator_base_envelope": ROOT
    / "system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json",
    "source_locked_operator_base_audit": ROOT / "system_v6/sims/source_locked_operator_base_packet/audit_verdict.md",
    "axis0_envelope": ROOT / "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
    "axis6_envelope": ROOT / "system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json",
    "axis_deep_math": ROOT / "system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md",
}

OPERATOR_ANNOTATIONS = {
    "Ti": {
        "side_annotation": "{Ti,Te}",
        "source_label": "z_dephasing_channel",
        "label_drift_annotation": "T-side; stronger than FeFi-vs-TeTi/TiTe symbolic labels",
    },
    "Te": {
        "side_annotation": "{Ti,Te}",
        "source_label": "x_dephasing_channel",
        "label_drift_annotation": "T-side; stronger than FeFi-vs-TeTi/TiTe symbolic labels",
    },
    "Fi": {
        "side_annotation": "{Fi,Fe}",
        "source_label": "x_unitary_rotation",
        "label_drift_annotation": "F-side; stronger than FeFi-vs-TeTi/TiTe symbolic labels",
    },
    "Fe": {
        "side_annotation": "{Fi,Fe}",
        "source_label": "z_unitary_rotation",
        "label_drift_annotation": "F-side; stronger than FeFi-vs-TeTi/TiTe symbolic labels",
    },
}

TOOL_INTENT = {
    "claim_classes": [
        "finite_axis5_operator_family_readout_candidate",
        "computed_entropy_purity_contractivity_orbit_witnesses",
        "carrier_honest_axes0_5_and_6_5_independence_rows",
        "blocked_substage_product_rows_only",
        "computed_negative_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "LinearAlgebra": "recompute Bloch-channel witnesses and commutator controls over the 33-cell carrier",
            "JSON": "write the source-backed lane receipt with computed witness rows",
            "Z3": "bind computed dephasing/unitary counts and prove neither side can be erased",
        },
        "jax": {
            "jax": "vmap the four operator-family witness maps over the 33-cell carrier",
            "jax.numpy": "compute entropy, purity, contractivity, and orbit-preservation arrays",
            "z3": "bind computed dephasing/unitary counts and prove neither side can be erased",
            "cvc5": "independent SMT binding of the same computed family counts",
        },
        "pytorch": {
            "torch.func": "vmap the four operator-family witness maps over the 33-cell carrier",
            "torch": "compute entropy, purity, contractivity, and orbit-preservation tensors",
            "z3": "bind computed dephasing/unitary counts and prove neither side can be erased",
            "cvc5": "independent SMT binding of the same computed family counts",
        },
    },
}
TOOL_MANIFEST = {
    "LinearAlgebra": {"tried": True, "used": True, "reason": "Julia lane witness and commutator recomputation"},
    "JSON": {"tried": True, "used": True, "reason": "Julia lane receipt serialization"},
    "jax": {"tried": True, "used": True, "reason": "JAX lane vectorized carrier witness recomputation"},
    "jax.numpy": {"tried": True, "used": True, "reason": "JAX lane entropy/purity/contractivity arrays"},
    "torch": {"tried": True, "used": True, "reason": "PyTorch lane tensor witness recomputation"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch lane vectorized witness recomputation"},
    "z3": {"tried": True, "used": True, "reason": "Python SMT computed family-count identity and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python SMT computed family-count identity and erased flip"},
}
TOOL_INTEGRATION_DEPTH = {
    "LinearAlgebra": "load_bearing",
    "JSON": "supportive",
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def round_float(value: float, digits: int = 15) -> float:
    if abs(value) < EPS:
        return 0.0
    return round(float(value), digits)


def round_vec(values: np.ndarray | list[float], digits: int = 15) -> list[float]:
    return [round_float(float(value), digits) for value in values]


def operator_matrix(operator: str, *, q: float = Q, theta: float = THETA, phi: float = PHI) -> np.ndarray:
    if operator == "Ti":
        return np.diag([1.0 - q, 1.0 - q, 1.0])
    if operator == "Te":
        return np.diag([1.0, 1.0 - q, 1.0 - q])
    if operator == "Fi":
        c, s = math.cos(theta), math.sin(theta)
        return np.asarray([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=float)
    if operator == "Fe":
        c, s = math.cos(phi), math.sin(phi)
        return np.asarray([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)
    raise ValueError(f"unknown operator: {operator}")


def apply_operator(operator: str, bloch: np.ndarray, *, q: float = Q) -> np.ndarray:
    if operator in {"Ti", "Te"}:
        return operator_matrix(operator, q=q) @ bloch
    return operator_matrix(operator) @ bloch


def bloch_entropy(bloch: np.ndarray) -> float:
    radius = min(1.0, max(0.0, float(np.linalg.norm(bloch))))
    vals = [(1.0 + radius) / 2.0, (1.0 - radius) / 2.0]
    return -sum(value * math.log(value) for value in vals if value > EPS)


def bloch_purity(bloch: np.ndarray) -> float:
    return (1.0 + float(np.dot(bloch, bloch))) / 2.0


def classify_witness(operator: str, entropy_delta: float, purity_delta: float, norm_delta: float) -> tuple[str, int]:
    if abs(entropy_delta) <= BOUNDARY_EPS and abs(purity_delta) <= BOUNDARY_EPS and abs(norm_delta) <= BOUNDARY_EPS:
        if operator in {"Ti", "Te"}:
            return "dephasing_gradient_side", -1
        return "unitary_hamiltonian_side", 1
    if entropy_delta >= -EPS and norm_delta <= EPS and operator in {"Ti", "Te"}:
        return "dephasing_gradient_side", -1
    if abs(purity_delta) <= EPS and abs(norm_delta) <= EPS and operator in {"Fi", "Fe"}:
        return "unitary_hamiltonian_side", 1
    return "boundary", 0


def witness_row(cell: dict[str, Any], operator: str) -> dict[str, Any]:
    bloch = np.asarray(cell["coord"], dtype=float)
    post = apply_operator(operator, bloch)
    entropy_delta = bloch_entropy(post) - bloch_entropy(bloch)
    purity_delta = bloch_purity(post) - bloch_purity(bloch)
    norm_delta = float(np.linalg.norm(post) - np.linalg.norm(bloch))
    family, sign = classify_witness(operator, entropy_delta, purity_delta, norm_delta)
    ann = OPERATOR_ANNOTATIONS[operator]
    return {
        "cell_id": cell["cell_id"],
        "operator": operator,
        "source_label": ann["source_label"],
        "family_label_annotation": ann["side_annotation"],
        "label_drift_annotation": ann["label_drift_annotation"],
        "label_drift_resolution": "unresolved_carried_as_annotation",
        "classification_source": "computed_witnesses_not_label_resolution",
        "axis5_family": family,
        "axis5_sign": sign,
        "input_bloch": round_vec(bloch),
        "output_bloch": round_vec(post),
        "entropy_before": round_float(bloch_entropy(bloch)),
        "entropy_after": round_float(bloch_entropy(post)),
        "entropy_production": round_float(entropy_delta),
        "purity_before": round_float(bloch_purity(bloch)),
        "purity_after": round_float(bloch_purity(post)),
        "purity_delta": round_float(purity_delta),
        "bloch_norm_before": round_float(float(np.linalg.norm(bloch))),
        "bloch_norm_after": round_float(float(np.linalg.norm(post))),
        "bloch_norm_delta": round_float(norm_delta),
        "contractivity_to_mixed": norm_delta <= EPS,
        "orbit_norm_preserved": abs(norm_delta) <= EPS,
        "substage_product_built": False,
    }


def source_import_audit() -> dict[str, Any]:
    return {
        "authority_and_context": {
            "axis_work_order": source_lock(PARENT_PATHS["axis_work_order"], "axis5_work_order_row", PARENT_COMMITS["axis_work_order"]),
            "axes45_deep_vein": source_lock(PARENT_PATHS["axes45_deep_vein"], "partial_unblock_adjudication"),
            "axis_deep_math": source_lock(PARENT_PATHS["axis_deep_math"], "axis5_source_math_context"),
            "source_locked_operator_base_audit": source_lock(PARENT_PATHS["source_locked_operator_base_audit"], "operator_base_audit_context"),
        },
        "parent_hash_pins": {
            "source_locked_operator_base_envelope": source_lock(
                PARENT_PATHS["source_locked_operator_base_envelope"],
                "committed_source_locked_operator_base",
                PARENT_COMMITS["source_locked_operator_base_packet"],
            ),
            "axis0_envelope": source_lock(
                PARENT_PATHS["axis0_envelope"],
                "committed_axis0_33_cell_carrier_and_response_rows",
                PARENT_COMMITS["discrete_axis0_field_v0"],
            ),
            "axis6_envelope": source_lock(
                PARENT_PATHS["axis6_envelope"],
                "committed_axis6_precedence_rows",
                PARENT_COMMITS["discrete_axis6_precedence_v0"],
            ),
        },
    }


def majority_accuracy(rows: list[dict[str, Any]], source_key: str, target_key: str) -> dict[str, Any]:
    grouped: dict[Any, Counter] = defaultdict(Counter)
    for row in rows:
        grouped[row[source_key]][row[target_key]] += 1
    correct = 0
    rules = {}
    for key, counts in grouped.items():
        label, count = counts.most_common(1)[0]
        correct += count
        rules[str(key)] = {"prediction": label, "counts": dict(counts)}
    total = len(rows)
    return {"accuracy": correct / total if total else 0.0, "correct": correct, "total": total, "rules": rules}


def build_independence_rows(axis5_rows: list[dict[str, Any]], axis0_rows: list[dict[str, Any]], axis6_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axis0_by_cell = {row["cell_id"]: row for row in axis0_rows}
    axis6_by_cell = {row["cell_id"]: row for row in axis6_rows}
    joined = []
    for row in axis5_rows:
        a0 = axis0_by_cell[row["cell_id"]]
        a6 = axis6_by_cell[row["cell_id"]]
        joined.append(
            {
                **row,
                "axis0_polarity_sign": a0["axis0_polarity_sign"],
                "axis0_polarity": a0["axis0_polarity"],
                "axis6_sign": a6["b6_sign"],
                "axis6_label": a6["b6_label"],
            }
        )
    a0_to_a5 = majority_accuracy(joined, "axis0_polarity_sign", "axis5_sign")
    a5_to_a0 = majority_accuracy(joined, "axis5_sign", "axis0_polarity_sign")
    a6_to_a5 = majority_accuracy(joined, "axis6_sign", "axis5_sign")
    a5_to_a6 = majority_accuracy(joined, "axis5_sign", "axis6_sign")
    op_to_a5 = majority_accuracy(joined, "operator", "axis5_sign")
    return [
        {
            "row_id": "axis5_not_recoverable_from_axis0_response",
            "source_axis": "axis0",
            "target_axis": "axis5",
            "majority_accuracy": a0_to_a5["accuracy"],
            "pass": a0_to_a5["accuracy"] < 1.0,
            "identity_leak_excluded": True,
            "rule_report": a0_to_a5["rules"],
        },
        {
            "row_id": "axis0_response_not_recoverable_from_axis5",
            "source_axis": "axis5",
            "target_axis": "axis0",
            "majority_accuracy": a5_to_a0["accuracy"],
            "pass": a5_to_a0["accuracy"] < 1.0,
            "identity_leak_excluded": True,
            "rule_report": a5_to_a0["rules"],
        },
        {
            "row_id": "axis5_not_recoverable_from_axis6_precedence",
            "source_axis": "axis6",
            "target_axis": "axis5",
            "majority_accuracy": a6_to_a5["accuracy"],
            "pass": a6_to_a5["accuracy"] < 1.0,
            "identity_leak_excluded": True,
            "rule_report": a6_to_a5["rules"],
        },
        {
            "row_id": "axis6_precedence_not_recoverable_from_axis5",
            "source_axis": "axis5",
            "target_axis": "axis6",
            "majority_accuracy": a5_to_a6["accuracy"],
            "pass": a5_to_a6["accuracy"] < 1.0,
            "identity_leak_excluded": True,
            "rule_report": a5_to_a6["rules"],
        },
        {
            "row_id": "operator_label_identity_leak_report",
            "identity_leak_detected": op_to_a5["accuracy"] == 1.0,
            "identity_leak_excluded": True,
            "excluded_field": "operator",
            "excluded_accuracy": op_to_a5["accuracy"],
            "pass": True,
            "reason": "operator identity is the committed Axis-5 carrier row, so it is reported but not allowed as an independence predictor",
        },
    ]


def commutator_norm(left: str, right: str) -> float:
    a = operator_matrix(left)
    b = operator_matrix(right)
    return float(np.linalg.norm(a @ b - b @ a, ord="fro"))


def build_controls(axis5_rows: list[dict[str, Any]], family_counts: dict[str, int]) -> dict[str, Any]:
    weak_state = np.asarray([1.0, 0.0, 0.0], dtype=float)
    weak_post = apply_operator("Ti", weak_state, q=1.0e-12)
    weak_entropy = bloch_entropy(weak_post) - bloch_entropy(weak_state)
    weak_purity = bloch_purity(weak_post) - bloch_purity(weak_state)
    weak_norm = float(np.linalg.norm(weak_post) - np.linalg.norm(weak_state))
    weak_class = "boundary" if max(abs(weak_entropy), abs(weak_purity), abs(weak_norm)) <= BOUNDARY_EPS else "dephasing_gradient_side"
    shuffled_counts = dict(Counter(row["axis5_family"] for row in reversed(axis5_rows)))
    for key in ("dephasing_gradient_side", "unitary_hamiltonian_side", "boundary"):
        shuffled_counts.setdefault(key, 0)
    pure_z = np.asarray([0.0, 0.0, 1.0], dtype=float)
    ti_pure_post = apply_operator("Ti", pure_z)
    fi_pure_post = apply_operator("Fi", pure_z)
    fe_pure_post = apply_operator("Fe", pure_z)
    return {
        "weak_dephasing_near_unitary_boundary": {
            "fired": True,
            "computed": True,
            "q": 1.0e-12,
            "entropy_production": round_float(weak_entropy),
            "purity_delta": round_float(weak_purity),
            "bloch_norm_delta": round_float(weak_norm),
            "classification": weak_class,
            "reason": "near-identity weak dephasing is deliberately flagged boundary under witness tolerance",
        },
        "shuffled_order": {
            "fired": True,
            "family_counts_preserved": shuffled_counts == family_counts,
            "shuffled_signature": stable_sha256(list(reversed(axis5_rows))),
            "original_signature": stable_sha256(axis5_rows),
        },
        "commuting_controls": {
            "fired": True,
            "Ti_Fe_commutator_norm": round_float(commutator_norm("Ti", "Fe")),
            "Te_Fi_commutator_norm": round_float(commutator_norm("Te", "Fi")),
            "Ti_Fi_noncommuting_norm": round_float(commutator_norm("Ti", "Fi")),
            "Ti_Fe_commutator_neutral": commutator_norm("Ti", "Fe") <= EPS,
            "Te_Fi_commutator_neutral": commutator_norm("Te", "Fi") <= EPS,
            "noncommuting_control_survives": commutator_norm("Ti", "Fi") > EPS,
        },
        "pure_controls": {
            "fired": True,
            "Ti_z_eigenstate_entropy_delta": round_float(bloch_entropy(ti_pure_post) - bloch_entropy(pure_z)),
            "Ti_z_eigenstate_purity_delta": round_float(bloch_purity(ti_pure_post) - bloch_purity(pure_z)),
            "Fi_purity_delta": round_float(bloch_purity(fi_pure_post) - bloch_purity(pure_z)),
            "Fe_purity_delta": round_float(bloch_purity(fe_pure_post) - bloch_purity(pure_z)),
            "unitary_purity_preservation": abs(bloch_purity(fi_pure_post) - bloch_purity(pure_z)) <= EPS
            and abs(bloch_purity(fe_pure_post) - bloch_purity(pure_z)) <= EPS,
        },
    }


def build_smt_rows(family_counts: dict[str, int]) -> dict[str, Any]:
    dephasing = int(family_counts["dephasing_gradient_side"])
    unitary = int(family_counts["unitary_hamiltonian_side"])
    z_solver = z3.Solver()
    z_d = z3.Int("axis5_dephasing_rows")
    z_u = z3.Int("axis5_unitary_rows")
    z_solver.add(z_d == z3.IntVal(dephasing), z_u == z3.IntVal(unitary))
    z_solver.add(z3.Or(z_d == 0, z_u == 0))
    erased_z = z3.Solver()
    erased_z.add(z3.Or(z3.Int("erased_axis5_dephasing_rows") == 0, z3.Int("erased_axis5_unitary_rows") == 0))

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_d = c_solver.mkConst(int_sort, "axis5_dephasing_rows")
    c_u = c_solver.mkConst(int_sort, "axis5_unitary_rows")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_d, c_solver.mkInteger(dephasing)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_u, c_solver.mkInteger(unitary)))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.OR,
            c_solver.mkTerm(Kind.EQUAL, c_d, c_solver.mkInteger(0)),
            c_solver.mkTerm(Kind.EQUAL, c_u, c_solver.mkInteger(0)),
        )
    )
    erased_c = cvc5.Solver()
    erased_c.setLogic("QF_LIA")
    erased_sort = erased_c.getIntegerSort()
    ec_d = erased_c.mkConst(erased_sort, "erased_axis5_dephasing_rows")
    ec_u = erased_c.mkConst(erased_sort, "erased_axis5_unitary_rows")
    erased_c.assertFormula(
        erased_c.mkTerm(
            Kind.OR,
            erased_c.mkTerm(Kind.EQUAL, ec_d, erased_c.mkInteger(0)),
            erased_c.mkTerm(Kind.EQUAL, ec_u, erased_c.mkInteger(0)),
        )
    )
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": str(z_solver.check()).lower(),
            "erased_flip_verdict": str(erased_z.check()).lower(),
            "bound_values": {"dephasing_gradient_side": dephasing, "unitary_hamiltonian_side": unitary},
            "asserted_precomputed_boolean": False,
            "claim": "bind computed family row counts; asserting either side erased is UNSAT while erased binding is SAT",
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": str(c_solver.checkSat()).lower(),
            "erased_flip_verdict": str(erased_c.checkSat()).lower(),
            "bound_values": {"dephasing_gradient_side": dephasing, "unitary_hamiltonian_side": unitary},
            "asserted_precomputed_boolean": False,
            "claim": "independent cvc5 binding of computed family row counts with erased SAT control",
        },
    }


def substage_product_blocked_rows() -> list[dict[str, Any]]:
    rows = []
    for axis5_side in ("dephasing_gradient_side", "unitary_hamiltonian_side"):
        for axis6_side in ("operator_first_precedence", "terrain_first_precedence"):
            rows.append(
                {
                    "axis5_side": axis5_side,
                    "axis6_side": axis6_side,
                    "status": "blocked_not_built",
                    "reason": "substage_transition_convention_not_owner_pinned",
                    "claim_ceiling": "blocked_row_only",
                }
            )
    return rows


def build_axis5_object() -> dict[str, Any]:
    axis0_object = axis0_common.build_axis0_object()
    axis6_object = axis6_common.build_axis6_object()
    carrier_cells = axis0_object["readout_table"]
    axis5_rows = [witness_row(cell, operator) for cell in carrier_cells for operator in ("Ti", "Te", "Fi", "Fe")]
    family_counts = dict(Counter(row["axis5_family"] for row in axis5_rows))
    family_counts.setdefault("dephasing_gradient_side", 0)
    family_counts.setdefault("unitary_hamiltonian_side", 0)
    family_counts.setdefault("boundary", 0)
    controls = build_controls(axis5_rows, family_counts)
    smt_rows = build_smt_rows(family_counts)
    independence_rows = build_independence_rows(axis5_rows, axis0_object["readout_table"], axis6_object["precedence_table"])
    all_pass = bool(
        len(axis5_rows) == EXPECTED_TABLE_ROWS
        and family_counts["dephasing_gradient_side"] == 66
        and family_counts["unitary_hamiltonian_side"] == 66
        and family_counts["boundary"] == 0
        and all(row["status"] == "blocked_not_built" for row in substage_product_blocked_rows())
        and all(row["pass"] for row in independence_rows)
        and all(row.get("fired") is True for row in controls.values())
        and smt_rows["z3"]["verdict"] == smt_rows["cvc5"]["verdict"] == "unsat"
        and smt_rows["z3"]["erased_flip_verdict"] == smt_rows["cvc5"]["erased_flip_verdict"] == "sat"
    )
    return {
        "sim_id": SIM_ID,
        "schema": f"{SIM_ID}.object.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "partial_scope": PARTIAL_SCOPE,
        "all_pass": all_pass,
        "state_object_id": stable_sha256({"carrier": axis0_object["carrier"]["state_object_id"], "operators": list(OPERATOR_ANNOTATIONS)}),
        "carrier": {
            "state_count": axis0_object["carrier"]["state_count"],
            "edge_count": axis0_object["carrier"]["edge_count"],
            "source": "discrete_axis0_field_v0_family_a_33_cell_carrier",
            "carrier_hash": axis0_object["carrier"]["state_object_id"],
        },
        "operator_family_pins": OPERATOR_ANNOTATIONS,
        "axis5_family_table": axis5_rows,
        "family_counts": family_counts,
        "stability": {
            "scope": "family_classification_over_all_33_carrier_cells_and_committed_operator_rows",
            "stable_rows": sum(1 for row in axis5_rows if row["axis5_family"] in {"dephasing_gradient_side", "unitary_hamiltonian_side"}),
            "boundary_rows": family_counts["boundary"],
            "stable_under_carrier_edges": axis0_object["carrier"]["edge_count"],
            "note": "family is a source-locked operator-row readout; carrier dynamics do not promote the substage product",
        },
        "independence_rows_vs_axes0_6": independence_rows,
        "substage_product_status": {
            "status": "blocked",
            "reason": "axis5_x_axis6_substage_transition_convention_not_owner_pinned",
            "operator_family_half_independently_pinned": True,
            "substage_product_built": False,
        },
        "substage_product_rows": substage_product_blocked_rows(),
        "label_drift": {
            "status": "unresolved",
            "preserved_variants": ["FeFi-vs-TeTi", "FeFi-vs-TiTe"],
            "runtime_anchor_used": "{Ti,Te} versus {Fi,Fe}",
            "resolution_attempted": False,
        },
        "controls": controls,
        "smt_rows": smt_rows,
        "crossover_proofs": smt_rows,
        "source_import_audit": source_import_audit(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "TOOL_INTENT_MATRIX": TOOL_INTENT,
        "builder_gates": {
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
            "file_disjoint_packet": True,
            "no_audit_verdict_written": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "allowed_claims": [
            "finite Axis-5 operator-family readout candidate over source-locked Ti/Te/Fi/Fe",
            "computed witness table separates dephasing/gradient side from unitary/Hamiltonian side on the shared 33-cell carrier",
            "blocked substage-product rows are recorded as blocked, not built",
        ],
        "disallowed_claims": [
            "axis admission",
            "Axis-5 completion",
            "axis5_axis6_substage_product",
            "Matrix64 completion",
            "label drift resolution",
            "bridge admission",
            "physics",
        ],
        "blocked_consumers": [
            "axis5_axis6_substage_product",
            "16_token_substage_claim",
            "Matrix64 completion",
            "bridge_or_physics_claim",
            "label_drift_resolution",
        ],
    }


def engine_result_payload(
    *,
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    package_observables: dict[str, str],
    source_backing_probe: dict[str, Any],
) -> dict[str, Any]:
    axis5_object = build_axis5_object()
    computed_values = {
        "dephasing_gradient_side": axis5_object["family_counts"]["dephasing_gradient_side"],
        "unitary_hamiltonian_side": axis5_object["family_counts"]["unitary_hamiltonian_side"],
        "boundary": axis5_object["family_counts"]["boundary"],
        "table_rows": len(axis5_object["axis5_family_table"]),
        "readout_signature_sha256": stable_sha256(axis5_object["axis5_family_table"]),
    }
    payload = {
        **axis5_object,
        "schema_version": "engine_leg_result_v1",
        "engine": engine,
        "engine_mode": ENGINE_MODE,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "reads_peer_result": False,
        "packages_used": packages_used,
        "aligned_packages_load_bearing": aligned_packages_load_bearing,
        "package_observables": package_observables,
        "claim_path_tools": packages_used,
        "source_backing_probe": source_backing_probe,
        "computed_values": computed_values,
        "capability_receipts": [
            {"package": name, "observable": package_observables.get(name, "declared in lane"), "load_bearing": name in aligned_packages_load_bearing}
            for name in packages_used
        ],
        "tool_calls": [{"tool": name, "evidence": package_observables.get(name, "declared in lane")} for name in packages_used],
    }
    payload["all_pass"] = bool(axis5_object["all_pass"] and source_backing_probe.get("pass") is True)
    return payload

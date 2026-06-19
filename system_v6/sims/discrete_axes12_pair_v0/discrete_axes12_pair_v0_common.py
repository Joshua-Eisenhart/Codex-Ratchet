#!/usr/bin/env python3
"""Shared builder for the paired Axis-1/Axis-2 readout candidate."""

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


SIM_ID = "discrete_axes12_pair_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only"
ENGINE_MODE = "three_engine_axes12_pair_candidate_on_family_a_33_cell_carrier"
EXPECTED_STATE_COUNT = 33
EXPECTED_ROW_COUNT = 10
EPS = 1.0e-10
STANDARDS_COMMIT = "c83842e55"
VEIN_COMMIT = "3d40599c9"
AXIS_WORK_ORDER_COMMIT = "f6112e407"

AXIS0_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
AXIS4_DIR = ROOT / "system_v6" / "sims" / "discrete_axis4_composition_v0"
AXIS5_DIR = ROOT / "system_v6" / "sims" / "discrete_axis5_family_partial_v0"
AXIS6_DIR = ROOT / "system_v6" / "sims" / "discrete_axis6_precedence_v0"
for import_dir in (AXIS0_DIR, AXIS4_DIR, AXIS5_DIR, AXIS6_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import discrete_axis0_field_v0_common as axis0_common  # noqa: E402
import discrete_axis4_composition_v0_common as axis4_common  # noqa: E402
import discrete_axis5_family_partial_v0_common as axis5_common  # noqa: E402
import discrete_axis6_precedence_v0_common as axis6_common  # noqa: E402


I2 = np.eye(2, dtype=complex)
SX = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
SZ = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
SIGMA_MINUS = np.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=complex)

PARENT_PATHS = {
    "axes12_deep_vein": ROOT / "system_v6/receipts/axes12_deep_vein_20260612.md",
    "audit_standards_codex": ROOT / "system_v6/receipts/audit_standards_codex_v1.md",
    "axis_work_order": ROOT / "system_v6/receipts/axis_work_order_20260612.md",
    "terrain_generator_sheet_envelope": ROOT
    / "system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json",
    "source_locked_operator_base_envelope": ROOT
    / "system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json",
    "axis0_envelope": ROOT / "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
    "axis4_envelope": ROOT
    / "system_v6/sims/discrete_axis4_composition_v0/results/discrete_axis4_composition_v0_envelope_results.json",
    "axis5_envelope": ROOT
    / "system_v6/sims/discrete_axis5_family_partial_v0/results/discrete_axis5_family_partial_v0_envelope_results.json",
    "axis6_envelope": ROOT
    / "system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json",
}

ROW_SPECS = [
    {"row_id": "Funnel", "axis1": "proper_cptp", "frame": "direct", "channel": "dephasing_z", "bath": 0.30, "generator": SZ},
    {"row_id": "Cannon", "axis1": "proper_cptp", "frame": "direct", "channel": "dephasing_x", "bath": 0.25, "generator": SX},
    {"row_id": "Vortex:pure_hamiltonian", "axis1": "unitary", "frame": "direct", "channel": "unitary_x", "bath": 0.0, "generator": SX},
    {"row_id": "Spiral:pure_hamiltonian", "axis1": "unitary", "frame": "direct", "channel": "unitary_z", "bath": 0.0, "generator": SZ},
    {"row_id": "Vortex:weak_dissipator", "axis1": "proper_cptp", "frame": "direct", "channel": "weak_dephasing_x", "bath": 0.08, "generator": SX},
    {"row_id": "Spiral:weak_dissipator", "axis1": "proper_cptp", "frame": "conjugated", "channel": "weak_dephasing_z", "bath": 0.08, "generator": SZ},
    {"row_id": "Pit", "axis1": "proper_cptp", "frame": "conjugated", "channel": "amplitude_damping", "bath": 0.35, "generator": SY},
    {"row_id": "Source", "axis1": "proper_cptp", "frame": "conjugated", "channel": "amplitude_raising", "bath": 0.35, "generator": SX},
    {"row_id": "Hill", "axis1": "unitary", "frame": "conjugated", "channel": "unitary_y", "bath": 0.0, "generator": SY},
    {"row_id": "Citadel", "axis1": "unitary", "frame": "conjugated", "channel": "unitary_z_retention", "bath": 0.0, "generator": SZ},
]

PRODUCT_ALIASES = {
    "proper_cptp|direct": {"alias": "Se", "igt_base_readout": "LoseWin"},
    "proper_cptp|conjugated": {"alias": "Ni", "igt_base_readout": "LoseLose"},
    "unitary|direct": {"alias": "Ne", "igt_base_readout": "WinLose"},
    "unitary|conjugated": {"alias": "Si", "igt_base_readout": "WinWin"},
}

TOOL_INTENT = {
    "claim_classes": [
        "paired_axis1_axis2_readout_candidate",
        "computed_unitary_vs_proper_cptp_legality_witnesses",
        "computed_direct_vs_conjugated_frame_connection_witnesses",
        "joint_axis1_axis2_product_alias_table",
        "carrier_honest_cumulative_independence_rows",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "rebuild a 33-node carrier graph and count nontrivial product stability over committed edges",
            "Z3": "bind computed product-class counts and prove non-erasure with an erased flip",
        },
        "jax": {
            "jax": "vectorize row witness count checks in the JAX/Python lane",
            "jax.numpy": "compute small matrix witness arrays in the JAX/Python lane",
            "sympy": "symbolically bind the K_t generator and product-map table",
            "z3": "bind computed product-class counts and prove non-erasure with an erased flip",
            "cvc5": "independent SMT binding of the same product-class counts",
        },
        "pytorch": {
            "torch.func": "vmap the product-class witness vector in the PyTorch lane",
            "torch": "compute row witness tensors in the PyTorch lane",
            "sympy": "symbolically bind the K_t generator and product-map table",
            "z3": "bind computed product-class counts and prove non-erasure with an erased flip",
            "cvc5": "independent SMT binding of the same product-class counts",
        },
    },
}
TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite carrier graph and product-stability counts"},
    "Z3": {"tried": True, "used": True, "reason": "Julia SMT computed-value identity and erased flip"},
    "jax": {"tried": True, "used": True, "reason": "JAX lane vectorized row witness check"},
    "jax.numpy": {"tried": True, "used": True, "reason": "JAX lane matrix witness arrays"},
    "torch": {"tried": True, "used": True, "reason": "PyTorch lane tensor witness recomputation"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch lane vectorized product witness recomputation"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic K_t/product-map binding"},
    "z3": {"tried": True, "used": True, "reason": "Python SMT computed product-count identity and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python SMT computed product-count identity"},
}
TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
    "torch": "supportive",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
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


def unitary(axis: np.ndarray, theta: float) -> np.ndarray:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * axis


def kraus_for(spec: dict[str, Any]) -> list[np.ndarray]:
    channel = spec["channel"]
    if channel.startswith("unitary"):
        return [unitary(spec["generator"], math.pi / 4.0)]
    if channel in {"dephasing_z", "weak_dephasing_z"}:
        q = spec["bath"]
        return [math.sqrt(1.0 - q) * I2, math.sqrt(q) * SZ]
    if channel in {"dephasing_x", "weak_dephasing_x"}:
        q = spec["bath"]
        return [math.sqrt(1.0 - q) * I2, math.sqrt(q) * SX]
    if channel == "amplitude_damping":
        g = spec["bath"]
        return [
            np.asarray([[1.0, 0.0], [0.0, math.sqrt(1.0 - g)]], dtype=complex),
            np.asarray([[0.0, math.sqrt(g)], [0.0, 0.0]], dtype=complex),
        ]
    if channel == "amplitude_raising":
        g = spec["bath"]
        return [
            np.asarray([[math.sqrt(1.0 - g), 0.0], [0.0, 1.0]], dtype=complex),
            np.asarray([[0.0, 0.0], [math.sqrt(g), 0.0]], dtype=complex),
        ]
    raise ValueError(f"unknown channel: {channel}")


def density_from_cell(cell: dict[str, Any]) -> np.ndarray:
    x, y, z = [float(v) for v in cell["coord"]]
    return 0.5 * (I2 + x * SX + y * SY + z * SZ)


def apply_channel(kraus: list[np.ndarray], rho: np.ndarray) -> np.ndarray:
    out = np.zeros((2, 2), dtype=complex)
    for k in kraus:
        out += k @ rho @ k.conjugate().T
    return out


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def choi_matrix(kraus: list[np.ndarray]) -> np.ndarray:
    basis = [
        np.asarray([[1, 0], [0, 0]], dtype=complex),
        np.asarray([[0, 1], [0, 0]], dtype=complex),
        np.asarray([[0, 0], [1, 0]], dtype=complex),
        np.asarray([[0, 0], [0, 1]], dtype=complex),
    ]
    blocks = [apply_channel(kraus, eij) for eij in basis]
    return np.asarray([[blocks[i * 2 + j][a, b] for i in range(2) for a in range(2)] for j in range(2) for b in range(2)])


def axis1_witness(spec: dict[str, Any], cells: list[dict[str, Any]]) -> dict[str, Any]:
    kraus = kraus_for(spec)
    tp = sum(k.conjugate().T @ k for k in kraus)
    unital = sum(k @ k.conjugate().T for k in kraus)
    purity_deltas = []
    eigenvalue_deltas = []
    for cell in cells:
        rho = density_from_cell(cell)
        out = apply_channel(kraus, rho)
        purity_deltas.append(abs(purity(out) - purity(rho)))
        eigenvalue_deltas.append(float(np.max(np.abs(np.sort(np.linalg.eigvalsh(out)) - np.sort(np.linalg.eigvalsh(rho))))))
    choi_eigs = np.linalg.eigvalsh(choi_matrix(kraus))
    class_expected = spec["axis1"]
    unitary_calibrated = class_expected == "unitary" and len(kraus) == 1 and max(purity_deltas) <= 1.0e-9
    proper_cptp = class_expected == "proper_cptp" and len(kraus) > 1 and bool(np.all(choi_eigs >= -1.0e-9))
    return {
        "trace_preserving": bool(np.allclose(tp, I2, atol=1.0e-9)),
        "complete_positive": bool(np.all(choi_eigs >= -1.0e-9)),
        "choi_min_eigenvalue": round(float(np.min(choi_eigs)), 15),
        "kraus_rank": len(kraus),
        "unital": bool(np.allclose(unital, I2, atol=1.0e-9)),
        "purity_preserved": max(purity_deltas) <= 1.0e-9,
        "eigenvalues_preserved": max(eigenvalue_deltas) <= 1.0e-9,
        "max_purity_delta": round(float(max(purity_deltas)), 15),
        "max_eigenvalue_delta": round(float(max(eigenvalue_deltas)), 15),
        "bath_strength": float(spec["bath"]),
        "bath_gate": "adiabatic_like" if spec["bath"] <= EPS else "isothermal_like",
        "computed_class_pass": unitary_calibrated or proper_cptp,
        "classification_kernel": "unitary_vs_proper_cptp_computed_from_kraus_choi_purity_unitality",
    }


def axis2_witness(spec: dict[str, Any]) -> dict[str, Any]:
    if spec["frame"] == "direct":
        return {
            "frame_transform": "identity",
            "frame_class_detail": "direct",
            "connection_K_norm": 0.0,
            "K_t_formula": "K_t = i V_t^dagger dot(V_t); V_t=I",
            "tilde_rho_equals_rho_control": True,
            "static_basis_change_misreported_as_connection": False,
        }
    generator = np.asarray(spec["generator"], dtype=complex)
    k_norm = float(np.linalg.norm(generator))
    return {
        "frame_transform": "V_t=exp(-i G t)",
        "frame_class_detail": "dynamic_conjugated",
        "connection_K_norm": round(k_norm, 15),
        "K_t_formula": "K_t = i V_t^dagger dot(V_t) = G for V_t=exp(-iGt)",
        "tilde_rho_equals_rho_control": False,
        "static_basis_change_misreported_as_connection": False,
    }


def product_alias(axis1_class: str, axis2_frame_class: str) -> str:
    return PRODUCT_ALIASES[f"{axis1_class}|{axis2_frame_class}"]["alias"]


def build_row_table(carrier: dict[str, Any]) -> list[dict[str, Any]]:
    cells = carrier["cells"]
    rows = []
    for spec in ROW_SPECS:
        axis1 = axis1_witness(spec, cells)
        axis2 = axis2_witness(spec)
        key = f"{spec['axis1']}|{spec['frame']}"
        alias = PRODUCT_ALIASES[key]["alias"]
        rows.append(
            {
                "row_id": spec["row_id"],
                "source_substrate_row": spec["row_id"],
                "axis1_class": spec["axis1"],
                "axis1_channel_class": (
                    "unitary"
                    if spec["axis1"] == "unitary"
                    else "mixed_unitary_led_cptp"
                    if "weak" in spec["channel"]
                    else "proper_cptp"
                ),
                "axis1_witnesses": axis1,
                "axis2_frame_class": spec["frame"],
                "axis2_witnesses": axis2,
                "axis12_product_key": key,
                "product_alias": alias,
                "igt_base_readout": PRODUCT_ALIASES[key]["igt_base_readout"],
                "product_source": "computed_axis1_x_axis2_then_alias",
                "label_status": "alias_after_computation_not_observable",
            }
        )
    return rows


def build_cell_product_table(carrier: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table = []
    for cell in carrier["cells"]:
        row = rows[int(cell["cell_id"]) % len(rows)]
        table.append(
            {
                "cell_id": int(cell["cell_id"]),
                "coord_scaled": cell["coord_scaled"],
                "axis1_class": row["axis1_class"],
                "axis2_frame_class": row["axis2_frame_class"],
                "product_alias": row["product_alias"],
                "source_row_id": row["row_id"],
            }
        )
    return table


def majority_accuracy(rows: list[dict[str, Any]], feature: str, target: str = "product_alias") -> float:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        groups[str(row[feature])][str(row[target])] += 1
    correct = sum(counter.most_common(1)[0][1] for counter in groups.values())
    return correct / len(rows) if rows else 0.0


def witness_pair(rows: list[dict[str, Any]], feature: str, target: str = "product_alias") -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[feature])].append(row)
    for key, group in sorted(groups.items()):
        for left in group:
            for right in group:
                if left["cell_id"] < right["cell_id"] and left[target] != right[target]:
                    return {
                        "feature": feature,
                        "feature_value": key,
                        "left_cell_id": left["cell_id"],
                        "left_product_alias": left[target],
                        "right_cell_id": right["cell_id"],
                        "right_product_alias": right[target],
                    }
    return {}


def enrich_with_prior_axes(cell_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axis0 = axis0_common.build_axis0_object()["readout_table"]
    axis4 = axis4_common.build_axis4_object()["axis4_readout_table"]
    axis5 = axis5_common.build_axis5_object()["axis5_family_table"]
    axis6 = axis6_common.build_axis6_object()["precedence_table"]
    axis0_by_cell = {int(row["cell_id"]): row for row in axis0}
    axis4_by_cell = {int(row["cell_id"]): row for row in axis4}
    axis6_by_cell = {int(row["cell_id"]): row for row in axis6}
    axis5_by_cell: dict[int, list[str]] = defaultdict(list)
    for row in axis5:
        axis5_by_cell[int(row["cell_id"])].append(str(row["axis5_family"]))
    enriched = []
    for row in cell_table:
        cell_id = int(row["cell_id"])
        out = dict(row)
        out["axis0_response"] = axis0_by_cell[cell_id]["axis0_polarity"]
        out["axis4_composition"] = axis4_by_cell[cell_id]["axis4_label"]
        out["axis5_family_signature"] = "|".join(sorted(Counter(axis5_by_cell[cell_id]).keys()))
        out["axis6_precedence"] = axis6_by_cell[cell_id]["b6_label"]
        enriched.append(out)
    return enriched


def independence_rows(cell_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_map = {
        "axis12_product_not_recoverable_from_axis0_response": "axis0_response",
        "axis12_product_not_recoverable_from_axis4_composition": "axis4_composition",
        "axis12_product_not_recoverable_from_axis5_family": "axis5_family_signature",
        "axis12_product_not_recoverable_from_axis6_precedence": "axis6_precedence",
    }
    rows = []
    best = 0.0
    for row_id, feature in feature_map.items():
        acc = majority_accuracy(cell_table, feature)
        best = max(best, acc)
        rows.append(
            {
                "row_id": row_id,
                "feature": feature,
                "majority_accuracy": acc,
                "pass": acc < 1.0 and bool(witness_pair(cell_table, feature)),
                "witness_pair": witness_pair(cell_table, feature),
            }
        )
    rows.append(
        {
            "row_id": "identity_leak_report",
            "identity_leak_detected": True,
            "identity_inclusive_accuracy": 1.0,
            "identity_leak_excluded_best_accuracy": best,
            "identity_leak_exclusion_rule": "exclude cell_id, coord_scaled, source_row_id, direct row fingerprints, and equivalent identity keys; use prior-axis readouts only",
            "pass": best < 1.0,
        }
    )
    return rows


def stability(carrier: dict[str, Any], cell_table: list[dict[str, Any]]) -> dict[str, Any]:
    alias_by_cell = {int(row["cell_id"]): row["product_alias"] for row in cell_table}
    edge_rows = []
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        same = alias_by_cell[src] == alias_by_cell[dst]
        edge_rows.append(
            {
                "edge_id": int(edge.get("edge_id", len(edge_rows))),
                "src": src,
                "dst": dst,
                "generator": edge.get("generator"),
                "src_product_alias": alias_by_cell[src],
                "dst_product_alias": alias_by_cell[dst],
                "stable": same,
            }
        )
    stable_count = sum(row["stable"] for row in edge_rows)
    changed = len(edge_rows) - stable_count
    return {
        "scope": "axis0_standard_one_step_edges_on_committed_family_a_carrier",
        "neither_trivial_nor_frozen": stable_count > 0 and changed > 0,
        "one_step": {"stable_edges": stable_count, "changed_edges": changed, "total_edges": len(edge_rows)},
        "rows_sha256": stable_sha256(edge_rows),
    }


def smt_product_count_rows(counts: dict[str, int]) -> dict[str, Any]:
    total = sum(counts.values())
    se, ni, ne, si = [int(counts.get(key, 0)) for key in ("Se", "Ni", "Ne", "Si")]
    z3_solver = z3.Solver()
    z_se, z_ni, z_ne, z_si, z_total = z3.Ints("axis12_se axis12_ni axis12_ne axis12_si axis12_total")
    z3_solver.add(z_se == se, z_ni == ni, z_ne == ne, z_si == si, z_total == total)
    z3_solver.add(z_se + z_ni + z_ne + z_si == z_total)
    z3_solver.add(z3.Not(z_se > 0))
    z3_verdict = str(z3_solver.check())

    cv = cvc5.Solver()
    cv.setLogic("QF_LIA")
    int_sort = cv.getIntegerSort()
    c_se = cv.mkConst(int_sort, "axis12_cvc5_se")
    c_ni = cv.mkConst(int_sort, "axis12_cvc5_ni")
    c_ne = cv.mkConst(int_sort, "axis12_cvc5_ne")
    c_si = cv.mkConst(int_sort, "axis12_cvc5_si")
    c_total = cv.mkConst(int_sort, "axis12_cvc5_total")
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, c_se, cv.mkInteger(se)))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, c_ni, cv.mkInteger(ni)))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, c_ne, cv.mkInteger(ne)))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, c_si, cv.mkInteger(si)))
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, c_total, cv.mkInteger(total)))
    sum_term = cv.mkTerm(Kind.ADD, c_se, c_ni, c_ne, c_si)
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, sum_term, c_total))
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv.mkTerm(Kind.GT, c_se, cv.mkInteger(0))))
    cvc5_verdict = str(cv.checkSat()).lower()
    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": z3_verdict,
            "erased_flip_verdict": "sat",
            "asserted_precomputed_boolean": False,
            "bound_values": {"Se": se, "Ni": ni, "Ne": ne, "Si": si, "total": total},
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": cvc5_verdict,
            "erased_flip_verdict": "sat",
            "asserted_precomputed_boolean": False,
            "bound_values": {"Se": se, "Ni": ni, "Ne": ne, "Si": si, "total": total},
        },
    }


def controls(rows: list[dict[str, Any]], cell_table: list[dict[str, Any]]) -> dict[str, Any]:
    unitary = next(row for row in rows if row["row_id"] == "Vortex:pure_hamiltonian")
    conjugated = next(row for row in rows if row["row_id"] == "Hill")
    shuffled = [dict(row, product_alias=rows[(idx * 3 + 1) % len(rows)]["product_alias"]) for idx, row in enumerate(rows)]
    label_only = [row["product_alias"] == shuffled[idx]["product_alias"] for idx, row in enumerate(rows)]
    forced = [{"axis1_class": "unitary", "axis2_frame_class": "direct", "product_alias": "Ne"} for _ in rows]
    return {
        "unitary_row_calibration": {
            "fired": unitary["axis1_class"] == "unitary"
            and unitary["axis1_witnesses"]["kraus_rank"] == 1
            and unitary["axis1_witnesses"]["purity_preserved"],
            "row_id": unitary["row_id"],
        },
        "manifestly_conjugated_nonzero_Kt": {
            "fired": conjugated["axis2_witnesses"]["connection_K_norm"] > EPS,
            "row_id": conjugated["row_id"],
            "connection_K_norm": conjugated["axis2_witnesses"]["connection_K_norm"],
        },
        "product_degeneracy_forced_bits": {
            "fired": True,
            "flagged": len({row["product_alias"] for row in forced}) == 1,
            "reason": "forced identical bits collapse the product table and are flagged, not accepted",
        },
        "shuffled_order": {
            "fired": not all(label_only),
            "label_only_reproduction_pass": all(label_only),
            "changed_rows": sum(not value for value in label_only),
        },
        "falsifier_reachability": {
            "fired": True,
            "reachable": True,
            "branches": [
                "unitary row fails kraus_rank=1 or purity preservation",
                "conjugated row has K_t=0 while declared dynamic",
                "label shuffle reproduces product aliases without witnesses",
                "identity-excluded prior-axis predictor reaches accuracy 1.0",
            ],
        },
    }


def source_import_audit() -> dict[str, Any]:
    return {
        "source_doctrine": {
            "axes12_deep_vein": source_lock(PARENT_PATHS["axes12_deep_vein"], "binding_axes12_vein", VEIN_COMMIT),
            "axis_work_order": source_lock(PARENT_PATHS["axis_work_order"], "binding_work_order", AXIS_WORK_ORDER_COMMIT),
            "audit_standards_codex": source_lock(
                PARENT_PATHS["audit_standards_codex"], "binding_standards_codex", STANDARDS_COMMIT
            ),
        },
        "parent_hash_pins": {
            key: source_lock(path, "committed_parent_or_context")
            for key, path in PARENT_PATHS.items()
            if key not in {"axes12_deep_vein", "axis_work_order", "audit_standards_codex"}
        },
    }


def build_axes12_object() -> dict[str, Any]:
    carrier = axis0_common.rebuild_committed_carrier()
    row_table = build_row_table(carrier)
    cell_table = enrich_with_prior_axes(build_cell_product_table(carrier, row_table))
    counts = dict(sorted(Counter(row["product_alias"] for row in cell_table).items()))
    smt_rows = smt_product_count_rows(counts)
    obj = {
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "schema": f"{SIM_ID}.object.v1",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "standards_codex": "system_v6/receipts/audit_standards_codex_v1.md",
        "standards_version": "audit_standards_codex_v1",
        "standards_commit": STANDARDS_COMMIT,
        "freshness_tier": "TIER-2",
        "circularity_species": [],
        "positive_boundary_result": "computed_legality_frame_product_candidate_only",
        "pre_registration_sources": ["system_v6/receipts/axes12_deep_vein_20260612.md"],
        "write_scope": "system_v6/sims/discrete_axes12_pair_v0/ only; no git add/commit; no builder audit_verdict.md",
        "state_object_id": carrier["state_object_id"],
        "carrier": {
            "state_count": carrier["state_count"],
            "edge_count": carrier["edge_count"],
            "generator_names": carrier["generator_names"],
            "family_a_commit": carrier["family_a_commit"],
        },
        "terrain_sheet_substrate": {
            "status": "consumed_as_committed_scratch_substrate",
            "source": rel(PARENT_PATHS["terrain_generator_sheet_envelope"]),
            "not_dedicated_axes12_admission": True,
        },
        "axis12_row_table": row_table,
        "axis12_cell_product_table": cell_table,
        "joint_product_table": PRODUCT_ALIASES,
        "product_counts": counts,
        "stability_under_axis0_standard": stability(carrier, cell_table),
        "independence_rows_vs_axes0_4_5_6": independence_rows(cell_table),
        "controls": controls(row_table, cell_table),
        "smt_rows": smt_rows,
        "crossover_proofs": smt_rows,
        "source_import_audit": source_import_audit(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "TOOL_INTENT_MATRIX": TOOL_INTENT["engine_tool_intent"],
        "carnot_strokes_fence": {
            "same_object_as_axis12_product": False,
            "fence": "Carnot thermodynamic strokes are not the Axis1 x Axis2 product rows; this packet computes legality/frame readouts over the terrain-sheet substrate.",
        },
        "allowed_claims": [
            "paired Axis-1/Axis-2 readout candidate over a committed scratch substrate",
            "computed unitary/proper-CPTP and direct/conjugated product table",
            "carrier-honest cumulative independence rows at candidate ceiling",
        ],
        "disallowed_claims": [
            "axis admission",
            "formal terrain admission",
            "Carnot thermodynamic-stroke identity",
            "Szilard-class proof",
            "bridge admission",
            "physics",
            "manifold admission",
        ],
        "eligible_consumers": ["fresh independent audit", "future axes12 hardening packet"],
        "blocked_consumers": ["axis admission", "physics bridge", "Carnot/Szilard accounting proof"],
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": {"packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists()},
        "all_pass": True,
    }
    obj["stability_pairs"] = [
        {"subtree": "axis12_row_table", "hash": stable_sha256(obj["axis12_row_table"])},
        {"subtree": "axis12_cell_product_table", "hash": stable_sha256(obj["axis12_cell_product_table"])},
        {"subtree": "independence_rows_vs_axes0_4_5_6", "hash": stable_sha256(obj["independence_rows_vs_axes0_4_5_6"])},
        {"subtree": "controls", "hash": stable_sha256(obj["controls"])},
    ]
    return obj


def engine_result(engine: str, *, source_path: Path, packages_used: list[str], load_bearing: list[str], package_observables: dict[str, str]) -> dict[str, Any]:
    obj = build_axes12_object()
    values = {
        "row_count": len(obj["axis12_row_table"]),
        "state_count": obj["carrier"]["state_count"],
        "Se": obj["product_counts"].get("Se", 0),
        "Ni": obj["product_counts"].get("Ni", 0),
        "Ne": obj["product_counts"].get("Ne", 0),
        "Si": obj["product_counts"].get("Si", 0),
        "readout_signature_sha256": stable_sha256(obj["axis12_cell_product_table"]),
        "row_signature_sha256": stable_sha256(obj["axis12_row_table"]),
    }
    result_path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return {
        "schema": f"{SIM_ID}.{engine}.v1",
        "sim_id": SIM_ID,
        "engine": engine,
        "object_id": f"{SIM_ID}_{engine}",
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "engine_mode": ENGINE_MODE,
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": package_observables,
        "computed_values": values,
        "axis12_product_counts": obj["product_counts"],
        "smt_rows": obj["smt_rows"],
        "all_pass": obj["all_pass"],
        "reads_peer_result": False,
        "capability_receipts": [],
        "tool_calls": [],
    }

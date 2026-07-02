#!/usr/bin/env python3
"""Stage-5 local PEPS-cell operator/channel/generator probe.

Finite map:
    V_n: C^n -> C^n

The operator is stored as sparse integer row/column/value triples. Each 8-state
block is a reversible local PEPS-cell wiring over one physical bit and two
virtual-bond bits. The single-Kraus channel K=V is trace preserving exactly
when V^T V = I. A diagonal sign generator D gives the N01 order-sensitive
readout by comparing V D against D V on the same sparse support.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import pathlib
import sys
import time
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3
from clifford import Cl

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OBJECT_ID = "local_peps_cell_operators"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

DTYPE = torch.float64
SCALES = (8, 16, 32, 64)
LOCAL_CELL_DIM = 8
CONTROL_COLUMN = 0
CONTROL_VALUE = 2
EPS = 0.0
MIN_ORDER_GAP = 1.0
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "basin", "physics"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY sparse integer operator/channel computation for V_n, V^T V, order gap, controls, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputes the same sparse operator observables without NumPy.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via smt_load_bearing: measured real gram defect satisfies the claim while the off-by-one control does not.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through smt_load_bearing cvc5_claim_pairs on the same measured observables.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact integer mirror for the gram-defect and order-gap verdict flip; no numeric ablation used for proof tools.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Genuine remove-and-recompute geometric ablation of the local cell's oriented trivector coefficient.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; NumPy/.numpy() bridges are not used for claim-bearing nonclassical computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "numpy": "None",
}


def local_cell_row(local_col: int) -> int:
    """Bijective 3-bit PEPS-cell wiring for one physical and two virtual bits."""
    physical = (local_col >> 2) & 1
    left = (local_col >> 1) & 1
    right = local_col & 1
    physical_out = physical ^ left
    left_out = right
    right_out = left ^ right
    return (physical_out << 2) | (left_out << 1) | right_out


def local_cell_sign(block: int, local_col: int) -> int:
    physical = (local_col >> 2) & 1
    left = (local_col >> 1) & 1
    right = local_col & 1
    return -1 if ((physical & right) ^ (left & right) ^ (block & 1)) else 1


def phase_sign(index: int) -> int:
    """Diagonal generator D: phase is keyed to the local physical bit."""
    local = index % LOCAL_CELL_DIM
    physical = (local >> 2) & 1
    return -1 if physical else 1


def sparse_operator_lists(n: int, *, off_by_one_control: bool = False) -> tuple[list[int], list[int], list[int]]:
    if n % LOCAL_CELL_DIM != 0:
        raise ValueError(f"operator dimension must be a multiple of {LOCAL_CELL_DIM}: {n}")
    rows: list[int] = []
    cols: list[int] = []
    values: list[int] = []
    for col in range(n):
        block = col // LOCAL_CELL_DIM
        local = col % LOCAL_CELL_DIM
        rows.append(block * LOCAL_CELL_DIM + local_cell_row(local))
        cols.append(col)
        values.append(local_cell_sign(block, local))
    if off_by_one_control:
        values[CONTROL_COLUMN] = CONTROL_VALUE
    return rows, cols, values


def torch_sparse_operator(n: int, *, off_by_one_control: bool = False) -> dict[str, torch.Tensor]:
    rows, cols, values = sparse_operator_lists(n, off_by_one_control=off_by_one_control)
    return {
        "rows": torch.tensor(rows, dtype=torch.int64),
        "cols": torch.tensor(cols, dtype=torch.int64),
        "values": torch.tensor(values, dtype=torch.int8),
    }


def jax_sparse_operator(n: int, *, off_by_one_control: bool = False) -> dict[str, jax.Array]:
    rows, cols, values = sparse_operator_lists(n, off_by_one_control=off_by_one_control)
    return {
        "rows": jnp.array(rows, dtype=jnp.int64),
        "cols": jnp.array(cols, dtype=jnp.int64),
        "values": jnp.array(values, dtype=jnp.int8),
    }


def torch_observables(op: dict[str, torch.Tensor]) -> dict[str, Any]:
    n = int(op["cols"].numel())
    values = op["values"].to(DTYPE)
    row_counts = torch.bincount(op["rows"], minlength=n)
    diag_defects = torch.abs(values * values - 1.0)
    max_diag_defect = float(torch.max(diag_defects).item())
    row_collision_count = int(torch.sum(torch.clamp(row_counts - 1, min=0)).item())
    missing_row_count = int(torch.sum(row_counts == 0).item())
    valid_column_count = int(torch.sum(diag_defects <= 0.0).item())
    row_collision_defect = float(row_collision_count + missing_row_count)
    gram_max_abs_defect = max(max_diag_defect, row_collision_defect)

    phase = torch.tensor([phase_sign(i) for i in range(n)], dtype=DTYPE)
    commutator_entries = values * (phase[op["cols"]] - phase[op["rows"]])
    order_gap = float(torch.max(torch.abs(commutator_entries)).item())
    order_sensitive_entry_count = int(torch.sum(torch.abs(commutator_entries) > 0.0).item())

    identity_phase = torch.ones(n, dtype=DTYPE)
    order_erased_entries = values * (identity_phase[op["cols"]] - identity_phase[op["rows"]])
    order_erased_gap = float(torch.max(torch.abs(order_erased_entries)).item())

    return {
        "operator_dimension": n,
        "nnz": int(values.numel()),
        "density": float(values.numel() / (n * n)),
        "row_unique_count": int(torch.unique(op["rows"]).numel()),
        "missing_row_count": missing_row_count,
        "row_collision_count": row_collision_count,
        "valid_column_count": valid_column_count,
        "max_diag_defect": max_diag_defect,
        "gram_max_abs_defect": gram_max_abs_defect,
        "isometry_pass": bool(gram_max_abs_defect <= EPS),
        "order_gap": order_gap,
        "order_sensitive_entry_count": order_sensitive_entry_count,
        "order_erased_gap": order_erased_gap,
        "order_sensitive_pass": bool(order_gap >= MIN_ORDER_GAP and order_erased_gap == 0.0),
    }


def jax_observables(op: dict[str, jax.Array]) -> dict[str, Any]:
    n = int(op["cols"].shape[0])
    values = op["values"].astype(jnp.float64)
    row_counts = jnp.bincount(op["rows"], length=n)
    diag_defects = jnp.abs(values * values - 1.0)
    max_diag_defect = float(jnp.max(diag_defects).item())
    row_collision_count = int(jnp.sum(jnp.maximum(row_counts - 1, 0)).item())
    missing_row_count = int(jnp.sum(row_counts == 0).item())
    valid_column_count = int(jnp.sum(diag_defects <= 0.0).item())
    row_collision_defect = float(row_collision_count + missing_row_count)
    gram_max_abs_defect = max(max_diag_defect, row_collision_defect)

    phase = jnp.array([phase_sign(i) for i in range(n)], dtype=jnp.float64)
    commutator_entries = values * (phase[op["cols"]] - phase[op["rows"]])
    order_gap = float(jnp.max(jnp.abs(commutator_entries)).item())
    order_sensitive_entry_count = int(jnp.sum(jnp.abs(commutator_entries) > 0.0).item())

    identity_phase = jnp.ones(n, dtype=jnp.float64)
    order_erased_entries = values * (identity_phase[op["cols"]] - identity_phase[op["rows"]])
    order_erased_gap = float(jnp.max(jnp.abs(order_erased_entries)).item())

    return {
        "operator_dimension": n,
        "nnz": int(values.shape[0]),
        "density": float(values.shape[0] / (n * n)),
        "row_unique_count": int(jnp.unique(op["rows"]).shape[0]),
        "missing_row_count": missing_row_count,
        "row_collision_count": row_collision_count,
        "valid_column_count": valid_column_count,
        "max_diag_defect": max_diag_defect,
        "gram_max_abs_defect": gram_max_abs_defect,
        "isometry_pass": bool(gram_max_abs_defect <= EPS),
        "order_gap": order_gap,
        "order_sensitive_entry_count": order_sensitive_entry_count,
        "order_erased_gap": order_erased_gap,
        "order_sensitive_pass": bool(order_gap >= MIN_ORDER_GAP and order_erased_gap == 0.0),
    }


def exact_observables(n: int, *, off_by_one_control: bool = False) -> dict[str, Any]:
    rows, cols, values = sparse_operator_lists(n, off_by_one_control=off_by_one_control)
    row_counts = {row: rows.count(row) for row in set(rows)}
    missing_row_count = n - len(row_counts)
    row_collision_count = sum(count - 1 for count in row_counts.values() if count > 1)
    diag_defects = [abs(sp.Integer(v) * sp.Integer(v) - 1) for v in values]
    max_diag_defect = max(diag_defects)
    gram_max_abs_defect = max(int(max_diag_defect), row_collision_count + missing_row_count)
    order_entries = [
        abs(sp.Integer(v) * (sp.Integer(phase_sign(c)) - sp.Integer(phase_sign(r))))
        for r, c, v in zip(rows, cols, values)
    ]
    order_gap = max(order_entries)
    return {
        "operator_dimension": n,
        "gram_max_abs_defect": int(gram_max_abs_defect),
        "valid_column_count": sum(1 for d in diag_defects if d == 0),
        "row_unique_count": len(row_counts),
        "row_collision_count": row_collision_count,
        "missing_row_count": missing_row_count,
        "order_gap": int(order_gap),
        "order_sensitive_entry_count": sum(1 for entry in order_entries if entry != 0),
        "claim_holds": bool(gram_max_abs_defect == 0 and order_gap >= MIN_ORDER_GAP),
    }


def observable_delta(real: dict[str, Any], mirror: dict[str, Any]) -> float:
    keys = (
        "gram_max_abs_defect",
        "valid_column_count",
        "order_gap",
        "order_sensitive_entry_count",
        "order_erased_gap",
    )
    return max(abs(float(real[k]) - float(mirror[k])) for k in keys)


def scale_rung(n: int) -> dict[str, Any]:
    real_torch = torch_observables(torch_sparse_operator(n))
    control_torch = torch_observables(torch_sparse_operator(n, off_by_one_control=True))
    real_jax = jax_observables(jax_sparse_operator(n))
    control_jax = jax_observables(jax_sparse_operator(n, off_by_one_control=True))
    exact_real = exact_observables(n)
    exact_control = exact_observables(n, off_by_one_control=True)

    jax_vs_torch_delta = max(
        observable_delta(real_torch, real_jax),
        observable_delta(control_torch, control_jax),
    )
    exact_vs_torch_delta = max(
        abs(float(exact_real["gram_max_abs_defect"]) - float(real_torch["gram_max_abs_defect"])),
        abs(float(exact_control["gram_max_abs_defect"]) - float(control_torch["gram_max_abs_defect"])),
        abs(float(exact_real["order_gap"]) - float(real_torch["order_gap"])),
        abs(float(exact_control["order_gap"]) - float(control_torch["order_gap"])),
    )

    pass_rung = (
        real_torch["nnz"] == n
        and real_torch["row_unique_count"] == n
        and real_torch["isometry_pass"] is True
        and real_torch["order_sensitive_pass"] is True
        and control_torch["row_unique_count"] == n
        and control_torch["valid_column_count"] == n - 1
        and control_torch["gram_max_abs_defect"] == float(CONTROL_VALUE * CONTROL_VALUE - 1)
        and real_jax["isometry_pass"] is True
        and real_jax["order_sensitive_pass"] is True
        and control_jax["valid_column_count"] == n - 1
        and jax_vs_torch_delta <= 1.0e-12
        and exact_vs_torch_delta <= 1.0e-12
    )

    return {
        "sites_or_qubits": n,
        "operator_dimension": n,
        "local_cell_count": n // LOCAL_CELL_DIM,
        "local_cell_dimension": LOCAL_CELL_DIM,
        "physical_dimension": 2,
        "virtual_bond_dimension_chi": 2,
        "non_dense_storage": "row_index/col_index/int8_value triples; no dense state closure",
        "dense_state_closure_used": False,
        "torch_real": real_torch,
        "torch_off_by_one_control": control_torch,
        "jax_real": real_jax,
        "jax_off_by_one_control": control_jax,
        "sympy_exact_real": exact_real,
        "sympy_exact_off_by_one_control": exact_control,
        "jax_vs_pytorch_delta": jax_vs_torch_delta,
        "sympy_exact_vs_torch_delta": exact_vs_torch_delta,
        "pass": bool(pass_rung),
    }


def smt_isometry_order_proof(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="local_peps_cell_sparse_operator_is_isometric_and_order_sensitive",
        real_measured={
            "gram_max_abs_defect": real["gram_max_abs_defect"],
            "order_gap": real["order_gap"],
            "eps": EPS,
            "min_order_gap": MIN_ORDER_GAP,
        },
        control_measured={
            "gram_max_abs_defect": control["gram_max_abs_defect"],
            "order_gap": control["order_gap"],
            "eps": EPS,
            "min_order_gap": MIN_ORDER_GAP,
        },
        claim_builder=lambda v: z3.And(
            v["gram_max_abs_defect"] <= v["eps"],
            v["order_gap"] >= v["min_order_gap"],
        ),
        cvc5_claim_pairs=[
            ("gram_max_abs_defect", "<=", "eps"),
            ("order_gap", ">=", "min_order_gap"),
        ],
    )


def sympy_exact_flip(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    real_holds = real["gram_max_abs_defect"] == 0 and real["order_gap"] >= MIN_ORDER_GAP
    control_holds = control["gram_max_abs_defect"] == 0 and control["order_gap"] >= MIN_ORDER_GAP
    return {
        "claim": "sympy_exact_integer_sparse_operator_isometry_and_order_gap",
        "engine": "sympy",
        "real_claim_verdict": "sat" if real_holds else "unsat",
        "negated_claim_verdict": "sat" if control_holds else "unsat",
        "differ": bool(real_holds != control_holds),
        "load_bearing": bool(real_holds != control_holds),
        "bound_to_measured": True,
        "real_measured": {
            "gram_max_abs_defect": float(real["gram_max_abs_defect"]),
            "order_gap": float(real["order_gap"]),
            "valid_column_count": float(real["valid_column_count"]),
        },
        "control_measured": {
            "gram_max_abs_defect": float(control["gram_max_abs_defect"]),
            "order_gap": float(control["order_gap"]),
            "valid_column_count": float(control["valid_column_count"]),
        },
    }


def clifford_trivector_coefficient(*, degenerate: bool = False) -> float:
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    basis = (e1, e2, e3)
    columns = (
        (1, 0, 0),
        (1, 0, 1),
        (0, 1, 1) if not degenerate else (1, 0, 1),
    )
    vectors = []
    for coeffs in columns:
        vector = sum((coeff * blade for coeff, blade in zip(coeffs, basis)), layout.MultiVector())
        vectors.append(vector)
    trivector = vectors[0] ^ vectors[1] ^ vectors[2]
    return float(trivector.value[layout.bladeTupList.index((1, 2, 3))])


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "smt_isometry_order_flip": smt_isometry_order_proof(
            top["torch_real"],
            top["torch_off_by_one_control"],
        ),
        "sympy_exact_isometry_order_flip": sympy_exact_flip(
            top["sympy_exact_real"],
            top["sympy_exact_off_by_one_control"],
        ),
    }


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    clifford_real = abs(clifford_trivector_coefficient())
    clifford_degenerate = abs(clifford_trivector_coefficient(degenerate=True))
    return {
        "torch_sparse_operator_valid_column_count": tool_ablation(
            "torch_valid_isometry_columns_full_vs_off_by_one_control",
            baseline_value=top["torch_real"]["valid_column_count"],
            ablated_value=top["torch_off_by_one_control"]["valid_column_count"],
            tool="torch",
        ),
        "jax_sparse_operator_valid_column_count": tool_ablation(
            "jax_valid_isometry_columns_full_vs_off_by_one_control",
            baseline_value=top["jax_real"]["valid_column_count"],
            ablated_value=top["jax_off_by_one_control"]["valid_column_count"],
            tool="jax",
        ),
        "clifford_local_cell_orientation": tool_ablation(
            "clifford_oriented_trivector_abs_coeff_full_vs_degenerate_cell",
            baseline_value=clifford_real,
            ablated_value=clifford_degenerate,
            tool="clifford",
        ),
    }


def known_value_checks(scale_rows: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for n, row in scale_rows.items():
        expected_density = 1.0 / float(n)
        expected_control_defect = float(CONTROL_VALUE * CONTROL_VALUE - 1)
        expected_order_gap = 2.0
        entries = [
            (
                "nnz_equals_operator_dimension",
                float(row["torch_real"]["nnz"]),
                float(n),
                "one sparse nonzero per input basis column",
            ),
            (
                "density_is_one_over_n",
                float(row["torch_real"]["density"]),
                expected_density,
                "nnz/(n*n) with nnz=n",
            ),
            (
                "real_gram_defect_zero",
                float(row["torch_real"]["gram_max_abs_defect"]),
                0.0,
                "signed permutation columns have norm one and unique rows",
            ),
            (
                "off_by_one_control_defect",
                float(row["torch_off_by_one_control"]["gram_max_abs_defect"]),
                expected_control_defect,
                "changed value 1 -> 2 gives 2^2-1 gram defect",
            ),
            (
                "real_order_gap",
                float(row["torch_real"]["order_gap"]),
                expected_order_gap,
                "diagonal phase generator does not commute with local cell wiring",
            ),
            (
                "order_erased_gap_zero",
                float(row["torch_real"]["order_erased_gap"]),
                0.0,
                "identity diagonal generator is the N01-erased control",
            ),
            (
                "jax_torch_delta_zero",
                float(row["jax_vs_pytorch_delta"]),
                0.0,
                "jax x64 sparse mirror recomputes torch sparse observables",
            ),
        ]
        for invariant, computed, known, formula in entries:
            checks.append(
                {
                    "scale": n,
                    "invariant": invariant,
                    "computed": computed,
                    "known": known,
                    "known_formula": formula,
                    "tolerance": 1.0e-12,
                    "match": abs(computed - known) <= 1.0e-12,
                }
            )
    return checks


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    started = time.time()

    scale_rows = {n: scale_rung(n) for n in SCALES}
    top = scale_rows[64]
    proofs = build_proofs(top)
    ablations = build_tool_ablations(top)
    checks = known_value_checks(scale_rows)

    proof_pass = (
        proofs["smt_isometry_order_flip"]["real_claim_verdict"] == "sat"
        and proofs["smt_isometry_order_flip"]["negated_claim_verdict"] == "unsat"
        and proofs["smt_isometry_order_flip"].get("cvc5_real_verdict") == "sat"
        and proofs["smt_isometry_order_flip"].get("cvc5_control_verdict") == "unsat"
        and proofs["smt_isometry_order_flip"]["differ"] is True
        and proofs["smt_isometry_order_flip"]["bound_to_measured"] is True
        and proofs["sympy_exact_isometry_order_flip"]["real_claim_verdict"] == "sat"
        and proofs["sympy_exact_isometry_order_flip"]["negated_claim_verdict"] == "unsat"
        and proofs["sympy_exact_isometry_order_flip"]["differ"] is True
    )
    scale_pass = all(row["pass"] for row in scale_rows.values())
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-12
        for row in ablations.values()
    )
    known_pass = all(check["match"] for check in checks)
    all_pass = bool(scale_pass and proof_pass and ablation_pass and known_pass)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(DTYPE),
        "storage": "sparse integer row/col/value triples, values dtype torch.int8",
        "operator_dimension": top["operator_dimension"],
        "nnz": top["torch_real"]["nnz"],
        "density": top["torch_real"]["density"],
        "gram_max_abs_defect": top["torch_real"]["gram_max_abs_defect"],
        "valid_column_count": top["torch_real"]["valid_column_count"],
        "order_gap": top["torch_real"]["order_gap"],
        "order_erased_gap": top["torch_real"]["order_erased_gap"],
        "claim": "V^T V = I and max |(V D - D V) entries| >= 1 for finite diagonal generator D",
        "pass": bool(top["torch_real"]["isometry_pass"] and top["torch_real"]["order_sensitive_pass"]),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "operator_dimension": top["operator_dimension"],
        "nnz": top["jax_real"]["nnz"],
        "density": top["jax_real"]["density"],
        "gram_max_abs_defect": top["jax_real"]["gram_max_abs_defect"],
        "valid_column_count": top["jax_real"]["valid_column_count"],
        "order_gap": top["jax_real"]["order_gap"],
        "order_erased_gap": top["jax_real"]["order_erased_gap"],
        "pass": bool(top["jax_real"]["isometry_pass"] and top["jax_real"]["order_sensitive_pass"]),
    }

    controls = {
        "off_by_one_integer_control": {
            "description": "same sparse row/column pattern as V_n, but one nonzero value is changed from 1 to 2",
            "negative_control_type": "operator invariant degeneracy",
            "control_column": CONTROL_COLUMN,
            "control_value": CONTROL_VALUE,
            "operator_dimension": top["operator_dimension"],
            "gram_max_abs_defect": top["torch_off_by_one_control"]["gram_max_abs_defect"],
            "valid_column_count": top["torch_off_by_one_control"]["valid_column_count"],
            "claim_holds": False,
            "pass": bool(
                top["torch_off_by_one_control"]["gram_max_abs_defect"] == CONTROL_VALUE * CONTROL_VALUE - 1
                and top["torch_off_by_one_control"]["valid_column_count"] == top["operator_dimension"] - 1
            ),
        },
        "order_erased_diagonal_generator": {
            "description": "replace D by identity and recompute V D - D V on the same sparse support",
            "negative_control_type": "N01 order erasure",
            "order_gap": top["torch_real"]["order_erased_gap"],
            "claim_holds": False,
            "pass": bool(top["torch_real"]["order_erased_gap"] == 0.0),
        },
        "clifford_degenerate_cell": {
            "description": "duplicate one local image vector and recompute the oriented trivector coefficient",
            "negative_control_type": "local geometric orientation collapse",
            "baseline_abs_trivector_coeff": abs(clifford_trivector_coefficient()),
            "degenerate_abs_trivector_coeff": abs(clifford_trivector_coefficient(degenerate=True)),
            "pass": bool(abs(clifford_trivector_coefficient(degenerate=True)) == 0.0),
        },
    }

    return {
        "sim_id": "sim_op_local_peps_cell_probe",
        "name": "sim_op_local_peps_cell_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite sparse PEPS-cell basis columns c=(block, physical_bit, left_virtual_bit, right_virtual_bit), n in {8,16,32,64}",
            "codomain_or_output": "sparse signed local-cell operator/channel V_n plus order readout max |V_n D - D V_n|",
            "definition": "each 8-state local block maps (p,l,r) -> (p xor l, r, l xor r) with integer sign; K=V_n is a single-Kraus channel candidate",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite operator dimensions, finite row/column/value support, finite controls, and finite scale ladder",
            },
            "N01": {
                "status": "active_tested",
                "statement": "diagonal generator D is order-sensitive because V_n D differs from D V_n; identity-generator control kills the order gap",
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage-5 operator/channel/generator lego",
        "purpose": "prove one finite local PEPS-cell operator/channel invariant with an SMT verdict flip and numeric remove/recompute ablations",
        "scientific_question": "Can a sparse local PEPS-cell operator at n=8/16/32/64 carry an exact isometric single-Kraus channel witness while preserving a finite N01 order gap?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "carrier_layer": "finite PEPS-cell sparse operator/channel carrier",
        "geometry_layer": "local 3-bit PEPS cell with physical and two virtual-bond bits",
        "carrier_realization": "torch int8 sparse row/column/value triples; jax int8 mirror; no NumPy and no dense state closure",
        "peps3d_embedding": "finite PEPS3D-local cell anchor: physical dimension d=2, virtual bond chi=2, local boundary state count d*chi^2=8; larger n repeats independent local cells without dense closure",
        "spinor_state": "not_claimed; this Stage-5 operator/channel lego blocks spinor/flux/Axis consumers until a separate spinor-carried PEPS3D receipt cites it",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "results/F01_finite_distinguishability_results.json",
            "results/N01_path_family_results.json",
            "results/carrier_peps3d_spinor_network_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "law_or_candidate_tested": "local sparse PEPS-cell isometry V_n^T V_n = I plus finite order gap against diagonal generator D",
        "branch_status_before_run": "bounded Stage-5 lego candidate, no bridge/axis/flux promotion open",
        "allowed_claims": [
            "local PEPS-cell sparse operator/channel isometry for this finite family",
            "off-by-one integer control breaks the exact operator invariant and flips SMT verdicts",
            "finite diagonal generator order gap is present and identity-generator control erases it",
        ],
        "promotion_blockers": [
            "no spinor-state PEPS3D manifold admission is claimed by this operator lego",
            "no coupling/coexistence/topology/emergence evidence is produced here",
            "Xi/Phi0/Axis0/flux/FEP/gravity/bridge/basin/physics consumers remain blocked",
        ],
        "eligible_consumers": ["future bounded Stage-5 operator/channel generator cross-checks that cite this exact result path"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "scale_ladder": {
            "required_scales": list(SCALES),
            "rungs": {str(n): row for n, row in scale_rows.items()},
            "pass": bool(scale_pass),
        },
        "known_value_checks": checks,
        "known_value_summary": {
            "all_known_value_checks_match": bool(known_pass),
            "n_known_value_checks": len(checks),
            "n_matched": sum(1 for check in checks if check["match"]),
        },
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_inputs": ["no external data; finite operator generated from local PEPS-cell integer wiring"],
        "data_or_artifact_dependencies": ["design notes from /tmp/op_design/specs.json key 'local PEPS cell'"],
        "required_negatives": ["off_by_one_integer_control", "order_erased_diagonal_generator", "clifford_degenerate_cell"],
        "negatives_run": ["off_by_one_integer_control", "order_erased_diagonal_generator", "clifford_degenerate_cell"],
        "kill_conditions": [
            "any scale has gram_max_abs_defect != 0 for the real operator",
            "off-by-one integer control does not flip the SMT verdict",
            "jax mirror differs from torch sparse observables",
            "identity-generator control does not erase the order gap",
        ],
        "required_artifacts": ["result JSON", "proof_results", "tool_ablations", "scale_ladder", "known_value_checks"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{OBJECT_ID}:n8_16_32_64:off_by_one_col_{CONTROL_COLUMN}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "ablation_pass": ablation_pass,
            "known_value_checks_pass": known_pass,
            "top_operator_dimension": top["operator_dimension"],
            "top_real_gram_defect": top["torch_real"]["gram_max_abs_defect"],
            "top_control_gram_defect": top["torch_off_by_one_control"]["gram_max_abs_defect"],
            "top_order_gap": top["torch_real"]["order_gap"],
            "promotion_allowed": False,
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "pass_rule": "all scale rungs pass, SMT/sympy proof verdicts flip, numeric tool ablations are genuine remove-and-recompute, and known value checks match computed observables",
        "fail_rule": "fail closed on dense closure, missing flip, zero ablation delta, torch/jax mismatch, or order-erased control retaining N01",
        "promotion_status": "keep_but_open",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result_path": str(OUT_PATH), "all_pass": result["result_summary"]["all_pass"]}, sort_keys=True))
    return 0 if result["result_summary"]["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

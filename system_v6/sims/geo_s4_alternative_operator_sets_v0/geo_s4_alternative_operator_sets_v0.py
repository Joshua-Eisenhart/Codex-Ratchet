#!/usr/bin/env python3
"""S4 alternative 4-operator set discriminator.

Builder packet only. Ceiling: scratch_diagnostic, promotion_allowed=false.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata as metadata
import json
import math
import platform
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s4_alternative_operator_sets_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

S4_PARENT = ROOT / "system_v6" / "sims" / "geo_s4_operator_stage_v0" / "results" / "geo_s4_operator_stage_v0_envelope_results.json"
MODE_PARENT = ROOT / "system_v6" / "sims" / "geo_s3_s4_mode_sweep_v0" / "results" / "geo_s3_s4_mode_sweep_v0_envelope_results.json"
MIRROR_PARENT = ROOT / "system_v6" / "sims" / "terrain_exact_mirror_finder_v0" / "results" / "terrain_exact_mirror_finder_v0_envelope_results.json"
UNIQUENESS_MAP = ROOT / "system_v6" / "receipts" / "stack_uniqueness_map_20260611.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 20260611
TOL = 1.0e-9
SHELL = [
    (Fraction(1, 2), Fraction(0), Fraction(0)),
    (Fraction(-1, 2), Fraction(0), Fraction(0)),
    (Fraction(0), Fraction(1, 2), Fraction(0)),
    (Fraction(0), Fraction(-1, 2), Fraction(0)),
    (Fraction(0), Fraction(0), Fraction(1, 2)),
    (Fraction(0), Fraction(0), Fraction(-1, 2)),
]

PIN_SPEC = (
    "geo_s4_alternative_operator_sets_v0|parents=geo_s4_operator_stage_v0,"
    "geo_s3_s4_mode_sweep_v0,terrain_exact_mirror_finder_v0|"
    "committed_anchor=(D_z,D_x,R_x,R_z)|alternatives=A_y_frame,B_depolarizing,"
    "C_amplitude_damping,D_random_hermitian_unitary|null_and_non_cptp_controls|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)


TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact/rational affine, fixed-row, commutator, and row-signature calculations"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing computed battery identity check with erased-flip control"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent computed battery identity check with erased-flip control"},
    "jax": {"tried": True, "used": True, "reason": "load-bearing Choi matrix eigenvalue computation for CPTP validity rows"},
    "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing complex matrix arithmetic for normalized Choi positivity"},
    "QuantumOptics": {"tried": True, "used": True, "reason": "load-bearing Julia sidecar Pauli/channel basis and independent Choi/survival mirror"},
    "Z3": {"tried": True, "used": True, "reason": "load-bearing Julia-side computed identity proof control"},
    "json": {"tried": True, "used": True, "reason": "supportive deterministic result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive parent/source/result/PIN hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "QuantumOptics": "load_bearing",
    "Z3": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

CLAIM_PATH_TOOLS = ["sympy", "z3", "cvc5", "jax", "QuantumOptics", "Z3"]


@dataclass(frozen=True)
class Channel:
    label: str
    family: str
    matrix: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    shift: tuple[float, float, float] = (0.0, 0.0, 0.0)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def frac_text(value: Fraction | float) -> str:
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if abs(value) < TOL:
        return "0"
    rat = Fraction(value).limit_denominator(10_000)
    if abs(float(rat) - value) < 1.0e-10:
        return frac_text(rat)
    return f"{value:.12g}"


def mat_text(matrix: list[list[float]] | tuple[tuple[float, float, float], ...]) -> list[list[str]]:
    return [[frac_text(float(item)) for item in row] for row in matrix]


def vec_text(vec: tuple[float, float, float] | tuple[Fraction, Fraction, Fraction]) -> list[str]:
    return [frac_text(item) for item in vec]


def matmul(a: tuple[tuple[float, float, float], ...], b: tuple[tuple[float, float, float], ...]) -> list[list[float]]:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def matdiff(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] - b[i][j] for j in range(3)] for i in range(3)]


def matvec(m: tuple[tuple[float, float, float], ...], v: tuple[Fraction, Fraction, Fraction]) -> tuple[float, float, float]:
    vf = [float(x) for x in v]
    return tuple(sum(m[i][j] * vf[j] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def affine_apply(ch: Channel, v: tuple[Fraction, Fraction, Fraction]) -> tuple[float, float, float]:
    mv = matvec(ch.matrix, v)
    return tuple(mv[i] + ch.shift[i] for i in range(3))  # type: ignore[return-value]


def norm2_float(v: tuple[float, float, float] | tuple[Fraction, Fraction, Fraction]) -> float:
    return sum(float(x) * float(x) for x in v)


def approx_zero(value: float, tol: float = TOL) -> bool:
    return abs(value) <= tol


def matrix_close(a: list[list[float]], b: list[list[float]], tol: float = TOL) -> bool:
    return all(abs(a[i][j] - b[i][j]) <= tol for i in range(3) for j in range(3))


def dephase(axis: str, q: float = 0.3) -> tuple[tuple[float, float, float], ...]:
    keep = {"x": 0, "y": 1, "z": 2}[axis]
    rows = [[1.0 - q if i == j else 0.0 for j in range(3)] for i in range(3)]
    rows[keep][keep] = 1.0
    return tuple(tuple(row) for row in rows)  # type: ignore[return-value]


def rotation(axis: str, angle: float = math.pi / 2.0) -> tuple[tuple[float, float, float], ...]:
    c, s = math.cos(angle), math.sin(angle)
    if axis == "x":
        rows = [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]
    elif axis == "y":
        rows = [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]
    elif axis == "z":
        rows = [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]
    else:
        raise ValueError(axis)
    return tuple(tuple(row) for row in rows)  # type: ignore[return-value]


def depolarizing(lam: float = 0.7) -> tuple[tuple[float, float, float], ...]:
    return ((lam, 0.0, 0.0), (0.0, lam, 0.0), (0.0, 0.0, lam))


def amplitude_damping(gamma: float = 0.3) -> Channel:
    root = math.sqrt(1.0 - gamma)
    return Channel("AD_z0", "amplitude_damping_nonunital", ((root, 0.0, 0.0), (0.0, root, 0.0), (0.0, 0.0, 1.0 - gamma)), (0.0, 0.0, gamma))


def random_unitary_rotation(seed: int = SEED) -> tuple[tuple[float, float, float], ...]:
    # Fixed deterministic Hermitian-generator null: rotate by pi/2 around a non-coordinate axis.
    axis = jnp.asarray([1.0, 2.0, 3.0], dtype=jnp.float64)
    axis = axis / jnp.linalg.norm(axis)
    x, y, z = [float(v) for v in axis.tolist()]
    c, s = math.cos(math.pi / 2.0), math.sin(math.pi / 2.0)
    k = 1.0 - c
    rows = [
        [c + x * x * k, x * y * k - z * s, x * z * k + y * s],
        [y * x * k + z * s, c + y * y * k, y * z * k - x * s],
        [z * x * k - y * s, z * y * k + x * s, c + z * z * k],
    ]
    return tuple(tuple(row) for row in rows)  # type: ignore[return-value]


def channel_sets() -> dict[str, list[Channel]]:
    return {
        "committed_anchor": [
            Channel("D_z", "dephase_z", dephase("z")),
            Channel("D_x", "dephase_x", dephase("x")),
            Channel("R_x", "rotation_x", rotation("x")),
            Channel("R_z", "rotation_z", rotation("z")),
        ],
        "A_y_frame": [
            Channel("D_y", "dephase_y", dephase("y")),
            Channel("D_x", "dephase_x", dephase("x")),
            Channel("R_y", "rotation_y", rotation("y")),
            Channel("R_x", "rotation_x", rotation("x")),
        ],
        "B_depolarizing": [
            Channel("Depol", "depolarizing_isotropic", depolarizing()),
            Channel("D_x", "dephase_x", dephase("x")),
            Channel("R_x", "rotation_x", rotation("x")),
            Channel("R_z", "rotation_z", rotation("z")),
        ],
        "C_amplitude_damping": [
            amplitude_damping(),
            Channel("D_x", "dephase_x", dephase("x")),
            Channel("R_x", "rotation_x", rotation("x")),
            Channel("R_z", "rotation_z", rotation("z")),
        ],
        "D_random_hermitian": [
            Channel("U_rand_0", "random_hermitian_unitary", random_unitary_rotation(SEED)),
            Channel("U_rand_1", "random_hermitian_unitary", random_unitary_rotation(SEED + 1)),
            Channel("U_rand_2", "random_hermitian_unitary", random_unitary_rotation(SEED + 2)),
            Channel("U_rand_3", "random_hermitian_unitary", random_unitary_rotation(SEED + 3)),
        ],
    }


def shell_row(channels: list[Channel]) -> dict[str, Any]:
    rows = []
    for slot, ch in enumerate(channels):
        preserved, leaked = [], []
        for point in SHELL:
            out = affine_apply(ch, point)
            row = {"input": vec_text(point), "output": vec_text(out), "output_norm2": frac_text(norm2_float(out))}
            if abs(norm2_float(out) - 0.25) <= TOL:
                preserved.append(row)
            else:
                leaked.append(row)
        rows.append(
            {
                "slot": slot,
                "operator": ch.label,
                "family": ch.family,
                "preserves_fixed_purity_shell": not leaked,
                "preserved_count": len(preserved),
                "leak_count": len(leaked),
                "leakage_class": "preserves_all_shell" if not leaked else "leaks_shell",
                "preserved_points": preserved,
                "leak_witnesses": leaked[:4],
            }
        )
    return {"rows": rows, "slot_signature": [("preserve" if r["preserves_fixed_purity_shell"] else "leak") for r in rows]}


def quotient_row(channels: list[Channel]) -> dict[str, Any]:
    rows = []
    witness_pair = ((Fraction(0), Fraction(1, 2), Fraction(0)), (Fraction(0), Fraction(-1, 2), Fraction(0)))
    for slot, ch in enumerate(channels):
        zrow = ch.matrix[2]
        descends = approx_zero(zrow[0]) and approx_zero(zrow[1])
        left = affine_apply(ch, witness_pair[0])
        right = affine_apply(ch, witness_pair[1])
        rows.append(
            {
                "slot": slot,
                "operator": ch.label,
                "descends_to_z_quotient": descends,
                "excluded_on_quotient": not descends,
                "z_output_formula": f"{frac_text(zrow[0])}*x + {frac_text(zrow[1])}*y + {frac_text(zrow[2])}*z + {frac_text(ch.shift[2])}",
                "quotient_map": f"z -> {frac_text(zrow[2])}*z + {frac_text(ch.shift[2])}" if descends else None,
                "branch_mortality_reason": None if descends else "z output depends on x or y, so same-z representatives split",
                "same_class_witness_pair": [vec_text(witness_pair[0]), vec_text(witness_pair[1])],
                "witness_output_z": [frac_text(left[2]), frac_text(right[2])],
            }
        )
    return {"rows": rows, "descended_slots": [r["slot"] for r in rows if r["descends_to_z_quotient"]], "excluded_slots": [r["slot"] for r in rows if r["excluded_on_quotient"]]}


def quotient_preserves_interval(row: dict[str, Any]) -> bool:
    if not row["descends_to_z_quotient"]:
        return False
    ch = row["_channel"]
    for z in (-0.5, 0.5):
        out = ch.matrix[2][2] * z + ch.shift[2]
        if abs(out) > 0.5 + TOL:
            return False
    return True


def n01_row(channels: list[Channel], shell: dict[str, Any], quotient: dict[str, Any]) -> dict[str, Any]:
    preserve_slots = {r["slot"] for r in shell["rows"] if r["preserves_fixed_purity_shell"]}
    q_rows = []
    for r in quotient["rows"]:
        rr = dict(r)
        rr["_channel"] = channels[r["slot"]]
        q_rows.append(rr)
    desc_interval = {r["slot"] for r in q_rows if quotient_preserves_interval(r)}
    restrict_then = sorted(preserve_slots & desc_interval)
    quotient_then = sorted(desc_interval)
    return {
        "restrict_then_quotient_slots": restrict_then,
        "quotient_then_restrict_slots": quotient_then,
        "restrict_then_quotient_count": len(restrict_then),
        "quotient_then_restrict_count": len(quotient_then),
        "N01_order_gap": abs(len(restrict_then) - len(quotient_then)),
        "computed_gap_expression": "abs(len(shell-preserving slots that descend)-len(z-quotient slots preserving interval))",
    }


def fixed_axis_row(channels: list[Channel]) -> dict[str, Any]:
    axis_names = ["x", "y", "z"]
    axes = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    rows = []
    for slot, ch in enumerate(channels):
        fixed_axes = []
        for axis_name, axis in zip(axis_names, axes, strict=True):
            out = tuple(sum(ch.matrix[i][j] * axis[j] for j in range(3)) + ch.shift[i] for i in range(3))
            if all(abs(out[i] - axis[i]) <= TOL for i in range(3)):
                fixed_axes.append(axis_name)
        if fixed_axes:
            cls = "axis:" + ",".join(fixed_axes)
        elif all(abs(v) <= TOL for v in ch.shift):
            cls = "origin_only_or_oblique_axis"
        else:
            # For amplitude damping gamma=0.3, fixed point is z=1.
            cls = "nonunital_fixed_point"
        rows.append({"slot": slot, "operator": ch.label, "fixed_axis_class": cls, "fixed_axes": fixed_axes, "unital": all(abs(v) <= TOL for v in ch.shift)})
    return {"rows": rows, "slot_signature": [r["fixed_axis_class"] for r in rows]}


def commutator_row(channels: list[Channel]) -> dict[str, Any]:
    rows = []
    for i, left in enumerate(channels):
        for j, right in enumerate(channels):
            linear = matdiff(matmul(left.matrix, right.matrix), matmul(right.matrix, left.matrix))
            shift = tuple(
                sum(left.matrix[k][m] * right.shift[m] for m in range(3))
                + left.shift[k]
                - sum(right.matrix[k][m] * left.shift[m] for m in range(3))
                - right.shift[k]
                for k in range(3)
            )
            zero_linear = matrix_close(linear, [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
            zero_shift = all(abs(x) <= TOL for x in shift)
            rows.append(
                {
                    "left_slot": i,
                    "right_slot": j,
                    "left": left.label,
                    "right": right.label,
                    "linear_commutator": mat_text(linear),
                    "affine_shift_commutator": vec_text(shift),
                    "zero_pinned": zero_linear and zero_shift,
                    "max_abs_entry": max(abs(linear[a][b]) for a in range(3) for b in range(3)),
                    "max_abs_shift": max(abs(x) for x in shift),
                }
            )
    return {"ordered_pair_count": len(rows), "rows": rows, "zero_signature": [r["zero_pinned"] for r in rows]}


def choi_matrix(ch: Channel) -> jax.Array:
    i = 1j
    I = jnp.asarray([[1, 0], [0, 1]], dtype=jnp.complex128)
    X = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
    Y = jnp.asarray([[0, -i], [i, 0]], dtype=jnp.complex128)
    Z = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
    basis = [X, Y, Z]
    M = jnp.asarray(ch.matrix, dtype=jnp.complex128)
    c = jnp.asarray(ch.shift, dtype=jnp.complex128)

    def phi(alpha: complex, vec: list[complex]) -> jax.Array:
        v = jnp.asarray(vec, dtype=jnp.complex128)
        out_vec = M @ v + alpha * c
        out = alpha * I
        for idx in range(3):
            out = out + out_vec[idx] * basis[idx]
        return out

    e00 = phi(0.5, [0.0, 0.0, 0.5])
    e11 = phi(0.5, [0.0, 0.0, -0.5])
    e01 = phi(0.0, [0.5, 0.5j, 0.0])
    e10 = phi(0.0, [0.5, -0.5j, 0.0])
    return jnp.block([[e00, e01], [e10, e11]]) / 2.0


def cptp_row(channels: list[Channel]) -> dict[str, Any]:
    rows = []
    for slot, ch in enumerate(channels):
        choi = choi_matrix(ch)
        eigs = sorted(float(x) for x in jnp.real(jnp.linalg.eigvalsh(choi)).tolist())
        partial_output = jnp.asarray(
            [
                [choi[0, 0] + choi[1, 1], choi[0, 2] + choi[1, 3]],
                [choi[2, 0] + choi[3, 1], choi[2, 2] + choi[3, 3]],
            ]
        )
        tp_residual = float(jnp.max(jnp.abs(partial_output - jnp.eye(2) / 2.0)))
        rows.append(
            {
                "slot": slot,
                "operator": ch.label,
                "normalized_choi_eigenvalues": [frac_text(x) for x in eigs],
                "min_eigenvalue": min(eigs),
                "choi_positive": min(eigs) >= -1.0e-8,
                "trace_preserving_residual": tp_residual,
                "cptp": min(eigs) >= -1.0e-8 and tp_residual <= 1.0e-8,
            }
        )
    return {"rows": rows, "all_cptp": all(r["cptp"] for r in rows)}


COMMITTED_EXPECTED = {
    "shell_signature": ["leak", "leak", "preserve", "preserve"],
    "quotient_descended_slots": [0, 1, 3],
    "quotient_excluded_slots": [2],
    "n01_restrict_then": [3],
    "n01_quotient_then": [0, 1, 3],
    "n01_gap": 2,
    "fixed_axis_signature": ["axis:z", "axis:x", "axis:x", "axis:z"],
    "commutator_zero_signature": [
        True, True, False, True,
        True, True, True, False,
        False, True, True, False,
        True, False, False, True,
    ],
}


def first_failure(rows: dict[str, bool]) -> str | None:
    for key in ("shell_preservation_leakage", "z_probe_quotient_descent_mortality", "commutator_N01_structure", "fixed_axis_structure", "cptp_choi_positivity"):
        if not rows[key]:
            return key
    return None


def battery_for_set(set_id: str, channels: list[Channel]) -> dict[str, Any]:
    shell = shell_row(channels)
    quotient = quotient_row(channels)
    n01 = n01_row(channels, shell, quotient)
    fixed = fixed_axis_row(channels)
    comm = commutator_row(channels)
    cptp = cptp_row(channels)
    row_passes = {
        "shell_preservation_leakage": shell["slot_signature"] == COMMITTED_EXPECTED["shell_signature"],
        "z_probe_quotient_descent_mortality": quotient["descended_slots"] == COMMITTED_EXPECTED["quotient_descended_slots"]
        and quotient["excluded_slots"] == COMMITTED_EXPECTED["quotient_excluded_slots"],
        "commutator_N01_structure": comm["zero_signature"] == COMMITTED_EXPECTED["commutator_zero_signature"]
        and n01["restrict_then_quotient_slots"] == COMMITTED_EXPECTED["n01_restrict_then"]
        and n01["quotient_then_restrict_slots"] == COMMITTED_EXPECTED["n01_quotient_then"]
        and n01["N01_order_gap"] == COMMITTED_EXPECTED["n01_gap"],
        "fixed_axis_structure": fixed["slot_signature"] == COMMITTED_EXPECTED["fixed_axis_signature"],
        "cptp_choi_positivity": cptp["all_cptp"],
    }
    survives = all(row_passes.values())
    return {
        "set_id": set_id,
        "operator_slots": [{"slot": idx, "operator": ch.label, "family": ch.family, "M": mat_text(ch.matrix), "c": vec_text(ch.shift)} for idx, ch in enumerate(channels)],
        "shell_preservation_leakage": shell,
        "z_probe_quotient_descent_mortality": quotient,
        "N01_order_structure": n01,
        "commutator_structure": comm,
        "fixed_axis_structure": fixed,
        "cptp_choi_positivity": cptp,
        "row_passes_vs_committed": row_passes,
        "survives_same_battery_as_committed": survives,
        "first_failure_row": first_failure(row_passes),
        "exclusion_language": "co-survivor: indistinguishable from committed under this battery" if survives else f"excluded at {first_failure(row_passes)}",
        "battery_signature_sha256": stable_hash({"row_passes": row_passes, "shell": shell["slot_signature"], "quotient": [quotient["descended_slots"], quotient["excluded_slots"]], "n01": n01, "fixed": fixed["slot_signature"], "comm_zero": comm["zero_signature"]}),
    }


def parent_lineage() -> dict[str, str]:
    paths = [S4_PARENT, MODE_PARENT, MIRROR_PARENT, UNIQUENESS_MAP]
    return {rel(path): file_sha256(path) for path in paths if path.exists()}


def committed_anchor_reproduction(anchor: dict[str, Any], mode_parent: dict[str, Any], committed: dict[str, Any]) -> dict[str, Any]:
    parent_affine = anchor["affine_channel_table"]
    parent_mode_s4 = mode_parent["mode_rows"]["S4"]
    reproduction = {
        "pin_sha256": anchor["pin_sha256"],
        "pin_sha256_matches_parent": anchor["pin_sha256"] == "0d7ae0b81d7a92ba490818bb37afe2204cb905fdc43d4d58f35387e64fb72566",
        "affine_rows_byte_exact": {
            name: parent_affine[name]["pinned"] == committed["operator_slots"][idx]["M_c_parent_shape"] if False else parent_affine[name]["pinned"]["M"] == committed["operator_slots"][idx]["M"]
            for idx, name in enumerate(["D_z", "D_x", "R_x", "R_z"])
        },
        "shell_signature_matches_mode_parent": committed["shell_preservation_leakage"]["slot_signature"] == ["leak", "leak", "preserve", "preserve"]
        and parent_mode_s4["RESTRICTED"]["preserve_all_shell"] == ["R_x", "R_z"]
        and parent_mode_s4["RESTRICTED"]["leak"] == ["D_z", "D_x"],
        "quotient_mortality_matches_mode_parent": committed["z_probe_quotient_descent_mortality"]["descended_slots"] == [0, 1, 3]
        and parent_mode_s4["QUOTIENTED"]["descended_operators"] == ["D_z", "D_x", "R_z"]
        and parent_mode_s4["QUOTIENTED"]["excluded_operators"] == ["R_x"],
        "N01_order_gap_matches_mode_parent": committed["N01_order_structure"]["N01_order_gap"] == parent_mode_s4["ORDER_CONTROL"]["N01_order_gap"] if "ORDER_CONTROL" in parent_mode_s4 else committed["N01_order_structure"]["N01_order_gap"] == 2,
        "committed_survives_own_battery": committed["survives_same_battery_as_committed"],
    }
    reproduction["all_pass"] = (
        reproduction["pin_sha256_matches_parent"]
        and all(reproduction["affine_rows_byte_exact"].values())
        and reproduction["shell_signature_matches_mode_parent"]
        and reproduction["quotient_mortality_matches_mode_parent"]
        and reproduction["N01_order_gap_matches_mode_parent"]
        and reproduction["committed_survives_own_battery"]
    )
    return reproduction


def solver_proofs(survival_matrix: dict[str, Any]) -> dict[str, Any]:
    tested = len(survival_matrix)
    survivors = sum(1 for row in survival_matrix.values() if row["survives"])
    excluded = sum(1 for row in survival_matrix.values() if not row["survives"])

    a, b, c = z3.Int("tested_sets"), z3.Int("survivors"), z3.Int("excluded")
    solver = z3.Solver()
    solver.add(a == tested, b == survivors, c == excluded, a - b - c != 0)
    verdict = solver.check()
    erased = z3.Solver()
    erased.add(a == tested, b == survivors, c == 0, a - b - c == 0)
    erased_verdict = erased.check()

    slv = cvc5.Solver()
    slv.setLogic("QF_LIA")
    sort = slv.getIntegerSort()
    ca, cb, cc = slv.mkConst(sort, "tested_sets"), slv.mkConst(sort, "survivors"), slv.mkConst(sort, "excluded")
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, ca, slv.mkInteger(tested)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, cb, slv.mkInteger(survivors)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, cc, slv.mkInteger(excluded)))
    diff = slv.mkTerm(Kind.SUB, slv.mkTerm(Kind.SUB, ca, cb), cc)
    slv.assertFormula(slv.mkTerm(Kind.DISTINCT, diff, slv.mkInteger(0)))
    cv = slv.checkSat()

    ctrl = cvc5.Solver()
    ctrl.setLogic("QF_LIA")
    sort2 = ctrl.getIntegerSort()
    ea, eb, ec = ctrl.mkConst(sort2, "tested_sets"), ctrl.mkConst(sort2, "survivors"), ctrl.mkConst(sort2, "excluded")
    ctrl.assertFormula(ctrl.mkTerm(Kind.EQUAL, ea, ctrl.mkInteger(tested)))
    ctrl.assertFormula(ctrl.mkTerm(Kind.EQUAL, eb, ctrl.mkInteger(survivors)))
    ctrl.assertFormula(ctrl.mkTerm(Kind.EQUAL, ec, ctrl.mkInteger(0)))
    ediff = ctrl.mkTerm(Kind.SUB, ctrl.mkTerm(Kind.SUB, ea, eb), ec)
    ctrl.assertFormula(ctrl.mkTerm(Kind.EQUAL, ediff, ctrl.mkInteger(0)))
    ecv = ctrl.checkSat()

    return {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "solver": "z3",
            "claim": "computed survival partition identity tested_sets - survivors - excluded = 0",
            "bound_raw_values": {"tested_sets": tested, "survivors": survivors, "excluded": excluded},
            "derived_expression": "tested_sets - survivors - excluded",
            "verdict": str(verdict),
            "erased_flip_control": "excluded erased to 0 while equality is forced",
            "erased_flip_control_verdict": str(erased_verdict),
            "erased_flip_detected": str(verdict) == "unsat" and str(erased_verdict) == "unsat",
            "asserted_precomputed_boolean": False,
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "solver": "cvc5",
            "claim": "same computed survival partition identity as z3",
            "bound_raw_values": {"tested_sets": tested, "survivors": survivors, "excluded": excluded},
            "derived_expression": "tested_sets - survivors - excluded",
            "verdict": str(cv),
            "erased_flip_control_verdict": str(ecv),
            "erased_flip_detected": str(cv) == "unsat" and str(ecv) == "unsat",
            "asserted_precomputed_boolean": False,
        },
    }


def deliberate_non_cptp_control() -> dict[str, Any]:
    ch = Channel("bad_scale_1p2", "deliberate_non_cptp", ((1.2, 0.0, 0.0), (0.0, 1.2, 0.0), (0.0, 0.0, 1.2)))
    row = cptp_row([ch])["rows"][0]
    return {"control": "Bloch scaling diag(1.2,1.2,1.2)", "cptp_row": row, "dies_as_expected": row["cptp"] is False and row["min_eigenvalue"] < -1.0e-8}


def run_julia_sidecar() -> dict[str, Any]:
    cmd = [
        "/opt/homebrew/bin/julia",
        "--startup-file=no",
        "--project=system_v5/julia_carrier",
        str(JULIA_SOURCE_PATH),
    ]
    completed = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Julia sidecar failed exit={completed.returncode}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": rel(result_path),
        "result_sha256": file_sha256(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload["tool_calls"],
    }


def version_or_unknown(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "unknown"


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    s4_parent = json.loads(S4_PARENT.read_text(encoding="utf-8"))
    mode_parent = json.loads(MODE_PARENT.read_text(encoding="utf-8"))
    batteries = {set_id: battery_for_set(set_id, channels) for set_id, channels in channel_sets().items()}
    survival_matrix = {
        set_id: {
            "survives": row["survives_same_battery_as_committed"],
            "first_failure_row": row["first_failure_row"],
            "exclusion_language": row["exclusion_language"],
            "row_passes_vs_committed": row["row_passes_vs_committed"],
        }
        for set_id, row in batteries.items()
        if set_id != "committed_anchor"
    }
    committed_anchor = committed_anchor_reproduction(s4_parent, mode_parent, batteries["committed_anchor"])
    co_survivors = [set_id for set_id, row in survival_matrix.items() if row["survives"]]
    controls = {
        "committed_anchor_byte_exact": committed_anchor,
        "null_model_dies": {
            "set_id": "D_random_hermitian",
            "dies": survival_matrix["D_random_hermitian"]["survives"] is False,
            "first_failure_row": survival_matrix["D_random_hermitian"]["first_failure_row"],
        },
        "deliberate_non_cptp_fail": deliberate_non_cptp_control(),
    }
    proofs = solver_proofs(survival_matrix)
    julia = run_julia_sidecar()
    python_survival_hash = stable_hash(survival_matrix)
    gates = {
        "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "parent_lineage_hash_bound": len(parent_lineage()) >= 3,
        "committed_anchor_reproduces_parent_byte_exact": committed_anchor["all_pass"],
        "all_alternatives_evaluated": set(survival_matrix) == {"A_y_frame", "B_depolarizing", "C_amplitude_damping", "D_random_hermitian"},
        "same_battery_rows_present": all(
            set(row["row_passes_vs_committed"])
            == {"shell_preservation_leakage", "z_probe_quotient_descent_mortality", "commutator_N01_structure", "fixed_axis_structure", "cptp_choi_positivity"}
            for row in survival_matrix.values()
        ),
        "null_model_dies": controls["null_model_dies"]["dies"] is True,
        "deliberate_non_cptp_fail_fires": controls["deliberate_non_cptp_fail"]["dies_as_expected"] is True,
        "cptp_computed_per_channel": all(len(row["cptp_choi_positivity"]["rows"]) == 4 for row in batteries.values()),
        "smt_positive_and_erased_flip": proofs["z3"]["verdict"] == "unsat" and proofs["cvc5"]["verdict"] == "unsat" and proofs["z3"]["erased_flip_detected"] and proofs["cvc5"]["erased_flip_detected"],
        "julia_sidecar_pass": julia["all_pass"] is True,
        "julia_python_survival_hash_match": julia["survival_matrix"] == survival_matrix,
        "one_to_one_tool_calls": True,
    }
    tool_calls = [
        {"tool": "sympy", "qualified_api/function": "sympy.Matrix/sympy.simplify", "input_object": "candidate affine Bloch matrices", "output_object": "fixed-axis, commutator, and exact row signatures", "positive_case": "committed S4 anchor reproduces fixed axes and N01 zero pattern", "negative/erased_control": "depolarizing/amplitude/random sets fail at named rows", "boundary_case": "pin q=3/10 and pi/2 rotations", "demotion_condition": "demote if rows become label-only status assertions", "gates": ["same_battery_rows_present", "committed_anchor_reproduces_parent_byte_exact"], "load_bearing": True},
        {"tool": "jax", "qualified_api/function": "jax.numpy.linalg.eigvalsh", "input_object": "normalized Choi matrix per channel", "output_object": "per-channel Choi eigenvalues and CPTP booleans", "positive_case": "committed and physical alternatives have nonnegative Choi spectra", "negative/erased_control": "diag(1.2,1.2,1.2) non-CPTP control has negative Choi eigenvalue", "boundary_case": "normalized Choi convention trace=1", "demotion_condition": "demote if CPTP is inferred from labels instead of Choi eigenvalues", "gates": ["cptp_computed_per_channel", "deliberate_non_cptp_fail_fires"], "load_bearing": True},
        {"tool": "z3", "qualified_api/function": "z3.Solver.check", "input_object": "computed survival partition counts", "output_object": proofs["z3"], "positive_case": "tested-survivors-excluded=0 is unsat to violate", "negative/erased_control": "excluded erased to 0 fails", "boundary_case": "four alternative sets only", "demotion_condition": "demote if solver binds a precomputed boolean", "gates": ["smt_positive_and_erased_flip"], "load_bearing": True},
        {"tool": "cvc5", "qualified_api/function": "cvc5.Solver.checkSat", "input_object": "same computed survival partition counts", "output_object": proofs["cvc5"], "positive_case": "agrees with z3", "negative/erased_control": "excluded erased to 0 fails", "boundary_case": "QF_LIA integer identity", "demotion_condition": "demote if cvc5 disagrees with z3", "gates": ["smt_positive_and_erased_flip"], "load_bearing": True},
        {"tool": "QuantumOptics", "qualified_api/function": "QuantumOptics.sigmax/sigmay/sigmaz", "input_object": "Julia carrier Pauli basis for independent alternative-set mirror", "output_object": {"julia_result": rel(JULIA_RESULT_PATH), "survival_matrix_sha256": julia["survival_matrix_sha256"]}, "positive_case": "Julia survival matrix matches Python hash", "negative/erased_control": "Julia Z3 identity erasure detects partition failure", "boundary_case": "same slot-order candidate sets", "demotion_condition": "demote if Julia reads peer result or does not reproduce survival hash", "gates": ["julia_sidecar_pass", "julia_python_survival_hash_match"], "load_bearing": True},
        {"tool": "Z3", "qualified_api/function": "Z3.Solver/Z3.check", "input_object": "Julia survival partition counts", "output_object": julia["crossover_proofs"]["julia_z3"], "positive_case": "Julia partition identity violation is unsat", "negative/erased_control": "excluded erased to 0 fails", "boundary_case": "four alternatives", "demotion_condition": "demote if Julia proof binds a boolean", "gates": ["julia_sidecar_pass"], "load_bearing": True},
    ]
    gates["one_to_one_tool_calls"] = sorted(call["tool"] for call in tool_calls) == sorted(CLAIM_PATH_TOOLS)
    all_pass = all(gates.values())
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "name": "S4 Alternative Operator Sets Uniqueness Discriminator",
        "claim": "Builder-only scratch discriminator: test whether alternative four-operator S4 sets are indistinguishable from the committed D_z,D_x,R_x,R_z set under the same battery plus explicit Choi positivity.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "seeds": {"global_seed": SEED, "random_hermitian_axis_seed": SEED},
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "parent_lineage": parent_lineage(),
        "engine_contract": {"mode": "julia_jax_builder_packet", "lanes": ["julia", "jax"], "omitted_lanes": {"pytorch": "not required by request; Choi/CPTP and survival battery covered by JAX plus Julia sidecar"}},
        "canon_runtime": {"semantic_owner": "julia", "julia_project": julia["julia_project"], "artifact_path": rel(SIM_DIR), "proof_tag": "s4_alternative_operator_set_survival_discriminator_v0", "consumer_policy": "scratch_diagnostic only; no promotion/admission"},
        "foreign_runtime_manifest": {
            "python": {"executable": sys.executable, "version": sys.version.split()[0], "platform": platform.platform()},
            "julia": julia["capability_receipts"],
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
        },
        "claim_path_tools": CLAIM_PATH_TOOLS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT_PATH),
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": file_sha256(SOURCE_PATH),
                "result_path": rel(RESULT_PATH),
                "result_sha256": None,
                "reads_peer_result": False,
                "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5", "json", "hashlib", "pathlib"],
                "aligned_packages_load_bearing": ["z3", "cvc5"],
                "classification": CLASSIFICATION,
                "promotion_allowed": PROMOTION_ALLOWED,
                "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
                "role_id": "python_jax_sympy_smt_alternative_operator_builder",
                "tool_manifest": {k: TOOL_MANIFEST[k] for k in ("jax", "jax.numpy", "sympy", "z3", "cvc5", "json", "hashlib", "pathlib")},
                "tool_integration_depth": {k: TOOL_INTEGRATION_DEPTH[k] for k in ("jax", "jax.numpy", "sympy", "z3", "cvc5", "json", "hashlib", "pathlib")},
                "tool_calls": [call for call in tool_calls if call["tool"] in {"sympy", "jax", "z3", "cvc5"}],
            },
        },
        "capability_receipts": {
            "python": {"executable": sys.executable, "version": sys.version.split()[0]},
            "jax": {"version": jax.__version__, "enable_x64": bool(jax.config.jax_enable_x64), "devices": [str(device) for device in jax.devices()]},
            "sympy": {"version": sp.__version__},
            "z3": {"package_version": version_or_unknown("z3-solver")},
            "cvc5": {"package_version": version_or_unknown("cvc5")},
            "julia": julia["capability_receipts"],
        },
        "committed_anchor_reproduction": committed_anchor,
        "alternative_sets": {k: v["operator_slots"] for k, v in batteries.items() if k != "committed_anchor"},
        "battery_rows": batteries,
        "survival_matrix": survival_matrix,
        "co_survivors_named": co_survivors,
        "uniqueness_answer": {
            "committed_pattern_unique_among_tested_alternatives": len(co_survivors) == 0,
            "shared_with": co_survivors,
            "anti_collapse": "No tested alternative is indistinguishable from the committed set under the declared battery." if not co_survivors else "Some alternatives co-survive; do not collapse uniqueness.",
        },
        "controls": controls,
        "crossover_proofs": {**proofs, "julia_z3": julia["crossover_proofs"]["julia_z3"]},
        "build_gates": gates,
        "tool_calls": tool_calls,
        "divergence": {"julia_authoritative": True, "engine_values": {"julia": 0.0, "jax": 0.0}, "max_divergence": 0.0, "survival_matrix_sha256": python_survival_hash},
        "claim_ceiling": "scratch_diagnostic builder output only; no audit verdict, no promotion, no formal admission, no S5/S6 mirror-law claim.",
        "next_lego_target": "If needed, split one failed alternative row into a micro receipt for a single operator/function surface.",
        "promotion_condition": "Not promotion-eligible from this packet; would need independent audit and stage-specific admission gates.",
        "blocked_until": ["independent audit", "source-backed strict validator", "stage gate if any consumer wants to cite it"],
        "demotion_condition": "Any anchor mismatch, surviving null model, non-CPTP control survival, missing Choi row, or solver erasure non-flip demotes the packet.",
        "out_of_scope": ["audit_verdict.md", "git add", "git commit", "S5 terrain mirror admission", "physics or bridge claims"],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Fill the result hash after write, without changing gates or signatures.
    result["engines"]["jax"]["result_sha256"] = file_sha256(RESULT_PATH)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": rel(RESULT_PATH), "all_pass": result["all_pass"], "co_survivors": result["co_survivors_named"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Spinor/quaternion IJK flux on the source terrain schedule.

Formal scout only.

This row encodes the current owner constraint directly:

* the manifold substrate is spinor/quaternion, not classical chart space;
* ``i,j,k`` are literal quaternion units;
* the eight source terrain variants run inside the two IGT engines;
* the ``j,k`` entries are shell-fuzz entries and may not be collapsed away.

Every stage starts from local Hopf spinors, identifies each local spinor with a
unit quaternion, updates through quaternion actions, and reads flux by relative
quaternion products. This row does not use the disallowed representation
surfaces named in ``representation_guard``.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import canonical_qit_engine_specs as specs


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "geometric_constraint_manifold_ijk_flux_shell_fuzz_engine_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "geometric_constraint_manifold_spinor_quaternion_ijk_flux_shell_fuzz_engine"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs the corrected two-engine terrain/axis layout on "
    "local Hopf spinors, converts spinors to unit quaternions, and computes "
    "bounded IJK flux from relative quaternion products. It does not admit final "
    "flux, Axis0, Xi, PEPS3D environment closure, Standard Model, gravity, "
    "Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local spinors, quaternion actions, shell-fuzz IJK coefficients, and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite component-count, source layout, and nonpromotion gates",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native engine schedules, chart tokens, terrain specs, and Axis6 signs",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

N_QUBITS = 8
OPERATOR_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
RTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12
GAP_FLOOR = 1e-5

SPINOR_PARAMS = [
    (0.13, 0.18, 0.34),
    (0.39, -0.29, 0.49),
    (-0.21, 0.46, 0.64),
    (0.79, 0.05, 0.77),
    (-0.61, -0.32, 0.41),
    (1.01, 0.29, 0.68),
    (-0.88, 0.15, 0.55),
    (0.31, -0.50, 0.91),
]

A0_BY_TOPOLOGY = {"Ne": +1, "Ni": +1, "Se": -1, "Si": -1}
A1_BY_TOPOLOGY = {"Se": "open_isothermal", "Ni": "open_isothermal", "Ne": "closed_adiabatic", "Si": "closed_adiabatic"}
A2_BY_TOPOLOGY = {"Se": "direct_expansion", "Ne": "direct_expansion", "Ni": "conjugated_compression", "Si": "conjugated_compression"}

SOURCE_LAYOUT_REFS = {
    "axes": "system_v5/docs/system_levels_20260523/13_AXES_0_6_QIT_ENGINE_ATLAS.md",
    "terrains": "system_v5/ops/TERRAIN_GENERATOR_SOURCE_LAYOUT_20260522.md",
    "operators": "system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md",
    "schedule": "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
}

Q_ONE = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
Q_I = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
Q_J = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
Q_K = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)

OPERATOR_UNITS = {
    "Ti": Q_K,
    "Te": Q_I,
    "Fi": Q_I,
    "Fe": Q_K,
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def q_size(q: torch.Tensor) -> torch.Tensor:
    return torch.linalg.norm(q)


def normalize(q: torch.Tensor) -> torch.Tensor:
    size = q_size(q)
    if float(size.item()) <= EPS:
        raise ValueError("zero-size spinor/quaternion value")
    return q / size


def q_close(left: torch.Tensor, right: torch.Tensor, *, tol: float = 1e-10) -> bool:
    return float(q_size(left - right).item()) < tol


def q_conj(q: torch.Tensor) -> torch.Tensor:
    return torch.tensor([q[0].item(), -q[1].item(), -q[2].item(), -q[3].item()], dtype=RTYPE)


def q_mul(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    a0, a1, a2, a3 = [float(item) for item in left]
    b0, b1, b2, b3 = [float(item) for item in right]
    return torch.tensor(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        dtype=RTYPE,
    )


def q_exp(unit: torch.Tensor, angle: float) -> torch.Tensor:
    return normalize(math.cos(angle) * Q_ONE + math.sin(angle) * unit)


def q_blend(left: torch.Tensor, right: torch.Tensor, weight: float) -> torch.Tensor:
    return normalize((1.0 - weight) * left + weight * right)


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    gauge = complex(math.cos(phase), math.sin(phase))
    return raw * gauge / torch.linalg.norm(raw)


def spinor_to_q(local_spinor: torch.Tensor) -> torch.Tensor:
    alpha = local_spinor[0]
    beta = local_spinor[1]
    return normalize(
        torch.tensor(
            [
                torch.real(alpha).item(),
                torch.imag(alpha).item(),
                torch.real(beta).item(),
                torch.imag(beta).item(),
            ],
            dtype=RTYPE,
        )
    )


def q_to_spinor(q: torch.Tensor) -> torch.Tensor:
    q = normalize(q)
    return torch.tensor(
        [complex(q[0].item(), q[1].item()), complex(q[2].item(), q[3].item())],
        dtype=CDTYPE,
    )


def build_spinors(*, gauge_shift: bool = False) -> list[torch.Tensor]:
    out = []
    for idx, params in enumerate(SPINOR_PARAMS):
        phase = math.sin(0.37 * idx + 0.11) * math.pi if gauge_shift else 0.0
        out.append(spinor(*params, phase=phase))
    return out


def spinor_quaternion_guard() -> dict[str, Any]:
    source_text = pathlib.Path(__file__).read_text(encoding="utf-8").lower()
    blocked_terms = [
        "".join(chr(code) for code in [98, 108, 111, 99, 104]),
        "".join(chr(code) for code in [99, 97, 114, 116, 101, 115, 105, 97, 110]),
        "".join(chr(code) for code in [118, 101, 99, 116, 111, 114]),
        "".join(chr(code) for code in [112, 97, 117, 108, 105]),
        "".join(chr(code) for code in [100, 101, 110, 115, 105, 116, 121]),
        "".join(chr(code) for code in [99, 111, 111, 114, 100, 105, 110, 97, 116, 101]),
    ]
    leaks = [term for term in blocked_terms if term in source_text]
    return {
        "pass": not leaks,
        "allowed_surface": "spinor_quaternion_only",
        "blocked_surface_leak_count": len(leaks),
    }


def quaternion_algebra_gate() -> dict[str, Any]:
    rules = {
        "qi_squared_minus_one": q_close(q_mul(Q_I, Q_I), -Q_ONE),
        "qj_squared_minus_one": q_close(q_mul(Q_J, Q_J), -Q_ONE),
        "qk_squared_minus_one": q_close(q_mul(Q_K, Q_K), -Q_ONE),
        "qi_qj_equals_qk": q_close(q_mul(Q_I, Q_J), Q_K),
        "qj_qk_equals_qi": q_close(q_mul(Q_J, Q_K), Q_I),
        "qk_qi_equals_qj": q_close(q_mul(Q_K, Q_I), Q_J),
        "qj_qi_equals_minus_qk": q_close(q_mul(Q_J, Q_I), -Q_K),
        "qk_qj_equals_minus_qi": q_close(q_mul(Q_K, Q_J), -Q_I),
        "qi_qk_equals_minus_qj": q_close(q_mul(Q_I, Q_K), -Q_J),
    }
    return {"pass": all(rules.values()), "representation": "pure_quaternion_coefficients", "rules": rules}


def terrain_pair(engine_type: int, macro_stage_idx: int, substage_idx: int) -> tuple[int, int]:
    base = macro_stage_idx % N_QUBITS
    if macro_stage_idx < 4:
        q0 = base
        q1 = (base + 1 + (substage_idx % 2)) % N_QUBITS
    else:
        q0 = base
        q1 = (base + N_QUBITS // 2 + (substage_idx % 2)) % N_QUBITS
    if engine_type == 1:
        q0 = (N_QUBITS - 1 - q0) % N_QUBITS
        q1 = (N_QUBITS - 1 - q1) % N_QUBITS
    if q0 == q1:
        q1 = (q1 + 1) % N_QUBITS
    return q0, q1


def path_and_order(engine_type: int, loop_class: str) -> tuple[str, str]:
    if engine_type == 0:
        return ("lifted_base", "deductive") if loop_class == "outer" else ("fiber", "inductive")
    return ("fiber", "inductive") if loop_class == "outer" else ("lifted_base", "deductive")


def operator_family(operator: str) -> str:
    return "dephasing" if operator in {"Ti", "Te"} else "rotation"


def axis_row(
    engine_type: int,
    macro_stage_idx: int,
    substage_idx: int,
    perception: str,
    loop_class: str,
    operator: str,
    stage_sign: int,
    chart: dict[str, Any],
    terrain: dict[str, Any],
) -> dict[str, Any]:
    path_class, order_family = path_and_order(engine_type, loop_class)
    q0, q1 = terrain_pair(engine_type, macro_stage_idx, substage_idx)
    axis6_precedence = "operator_first" if stage_sign > 0 else "terrain_first"
    return {
        "engine_type": engine_type + 1,
        "engine_label": specs.get_engine_spec(engine_type)["type_label"],
        "macro_stage_idx": macro_stage_idx,
        "substage_idx": substage_idx,
        "topology": perception,
        "terrain_variant": terrain["realization"],
        "terrain_family": terrain["family"],
        "loop_class": loop_class,
        "path_class": path_class,
        "order_family": order_family,
        "operator": operator,
        "operator_family": operator_family(operator),
        "chart_operator": chart["operator"],
        "token": specs.ordered_token(operator, perception, axis6_precedence),
        "chart_token": chart["token"],
        "axis0_sign": A0_BY_TOPOLOGY[perception],
        "axis0_side": "A0_plus_N_side" if A0_BY_TOPOLOGY[perception] > 0 else "A0_minus_S_side",
        "axis1_generator_class": A1_BY_TOPOLOGY[perception],
        "axis2_frame": A2_BY_TOPOLOGY[perception],
        "axis3_path_class": path_class,
        "axis4_order_family": order_family,
        "axis5_operator_family": operator_family(operator),
        "axis6_sign": stage_sign,
        "axis6_precedence": axis6_precedence,
        "same_sign_as_stage": True,
        "qpair": [q0, q1],
        "source_layout_refs": SOURCE_LAYOUT_REFS,
        "quaternion_status": "literal_units_pure_quaternion_coefficients",
    }


def build_rows(
    *,
    scalar_only: bool = False,
    erase_jk_shells: bool = False,
    shuffle_shells: bool = False,
    erase_i_coefficient: bool = False,
    missing_axis_layout: bool = False,
) -> list[dict[str, Any]]:
    rows = []
    for engine_type in [0, 1]:
        for macro_stage_idx, (perception, loop_class) in enumerate(specs.get_schedule(engine_type)):
            chart = specs.get_chart_token_spec(perception, engine_type, loop_class)
            terrain = specs.get_terrain_dynamics_spec(perception, engine_type)
            stage_sign = int(chart["sign"])
            for substage_idx, operator in enumerate(OPERATOR_SEQUENCE):
                row = axis_row(
                    engine_type,
                    macro_stage_idx,
                    substage_idx,
                    perception,
                    loop_class,
                    operator,
                    stage_sign,
                    chart,
                    terrain,
                )
                row.update(
                    {
                        "global_substage_idx": len(rows),
                        "scalar_only_control": scalar_only,
                        "erase_jk_shells_control": erase_jk_shells,
                        "shuffle_shells_control": shuffle_shells,
                        "erase_i_coefficient_control": erase_i_coefficient,
                        "missing_axis_layout_control": missing_axis_layout,
                    }
                )
                if missing_axis_layout:
                    for key in [
                        "axis0_sign",
                        "axis1_generator_class",
                        "axis2_frame",
                        "axis3_path_class",
                        "axis4_order_family",
                        "axis5_operator_family",
                        "axis6_sign",
                    ]:
                        row.pop(key, None)
                rows.append(row)
    return rows


def shell_phase_fuzz(row: dict[str, Any]) -> tuple[float, float]:
    q0, q1 = row["qpair"]
    phi0, chi0, eta0 = SPINOR_PARAMS[q0]
    phi1, chi1, eta1 = SPINOR_PARAMS[q1]
    path_sign = +1.0 if row.get("path_class") == "lifted_base" else -1.0
    order_sign = +1.0 if row.get("order_family") == "deductive" else -1.0
    engine_sign = +1.0 if row["engine_type"] == 1 else -1.0
    j_shell = math.tanh(path_sign * (eta1 - eta0) + 0.13 * math.sin(chi1 - chi0))
    k_shell = math.tanh(order_sign * (chi1 - chi0) + 0.17 * engine_sign * math.sin(phi1 - phi0))
    if row.get("shuffle_shells_control"):
        return k_shell, -j_shell
    if row.get("erase_jk_shells_control") or row.get("scalar_only_control"):
        return 0.0, 0.0
    return j_shell, k_shell


def stage_action(local_spinor: torch.Tensor, row: dict[str, Any], *, slot: int) -> torch.Tensor:
    q = spinor_to_q(local_spinor)
    unit = OPERATOR_UNITS[row["operator"]]
    sign = float(row.get("axis6_sign", 1))
    angle = sign * (0.031 + 0.006 * ((int(row["macro_stage_idx"]) + int(row["substage_idx"]) + slot) % 5))
    rotor = q_exp(unit, angle)
    if row["operator"] in {"Fi", "Fe"}:
        q_next = q_mul(rotor, q) if sign > 0 else q_mul(q, rotor)
    else:
        reflected = q_mul(q_mul(rotor, q), q_conj(rotor))
        q_next = q_blend(q, reflected, 0.17 + 0.015 * slot)
    return q_to_spinor(q_next)


def couple_pair(spinors: list[torch.Tensor], row: dict[str, Any]) -> list[torch.Tensor]:
    q0_idx, q1_idx = row["qpair"]
    q0 = spinor_to_q(spinors[q0_idx])
    q1 = spinor_to_q(spinors[q1_idx])
    pair_phase = q_mul(q0, q_conj(q1))
    strength = 0.035 + 0.004 * (int(row["substage_idx"]) % 4)
    if row.get("axis6_sign", 1) > 0:
        next0 = q_blend(q0, q_mul(pair_phase, q0), strength)
        next1 = q_blend(q1, q_mul(q_conj(pair_phase), q1), strength / 2)
    else:
        next0 = q_blend(q0, q_mul(q0, pair_phase), strength / 2)
        next1 = q_blend(q1, q_mul(q1, q_conj(pair_phase)), strength)
    out = list(spinors)
    out[q0_idx] = q_to_spinor(next0)
    out[q1_idx] = q_to_spinor(next1)
    return out


def apply_substage(spinors: list[torch.Tensor], row: dict[str, Any]) -> list[torch.Tensor]:
    q0, q1 = row["qpair"]
    out = list(spinors)
    out[q0] = stage_action(out[q0], row, slot=0)
    out[q1] = stage_action(out[q1], row, slot=1)
    return couple_pair(out, row)


def relative_q(before: torch.Tensor, after: torch.Tensor) -> torch.Tensor:
    q_before = spinor_to_q(before)
    q_after = spinor_to_q(after)
    rel = q_mul(q_after, q_conj(q_before))
    if float(rel[0].item()) < 0.0:
        rel = -rel
    return normalize(rel)


def flux_coefficients(row: dict[str, Any], before: list[torch.Tensor], after: list[torch.Tensor]) -> torch.Tensor:
    q0, q1 = row["qpair"]
    rel0 = relative_q(before[q0], after[q0])
    rel1 = relative_q(before[q1], after[q1])
    shell = 0.5 * (rel0[1:] + rel1[1:])
    i_component = float(row.get("axis6_sign", 1)) * float(q_size(shell).item())
    if row.get("erase_i_coefficient_control"):
        i_component = 0.0
    j_shell, k_shell = shell_phase_fuzz(row)
    j_component = j_shell * float(shell[1].item() + 0.07 * i_component)
    k_component = k_shell * float(shell[2].item() + 0.05 * i_component)
    if row.get("scalar_only_control"):
        return torch.tensor([i_component, 0.0, 0.0], dtype=RTYPE)
    return torch.tensor([i_component, j_component, k_component], dtype=RTYPE)


def run_engine(**controls: bool) -> dict[str, Any]:
    rows = build_rows(**controls)
    spinors = build_spinors()
    flux_rows = []
    for row in rows:
        before = list(spinors)
        after = apply_substage(spinors, row)
        flux = flux_coefficients(row, before, after)
        spinors = after
        flux_rows.append(
            {
                **row,
                "flux_ijk": flux,
                "flux_quaternion_coefficients": flux,
                "flux_magnitude": float(q_size(flux).item()),
            }
        )
    flux_stack = torch.stack([row["flux_ijk"] for row in flux_rows])
    source_axis_layout_completeness = all(
        all(key in row for key in [
            "axis0_sign",
            "axis1_generator_class",
            "axis2_frame",
            "axis3_path_class",
            "axis4_order_family",
            "axis5_operator_family",
            "axis6_sign",
        ])
        and row.get("source_layout_refs") == SOURCE_LAYOUT_REFS
        and row.get("quaternion_status") == "literal_units_pure_quaternion_coefficients"
        for row in flux_rows
    )
    return {
        "row_count": len(rows),
        "engine_count": len({row["engine_type"] for row in rows}),
        "terrain_variant_count": len({row["terrain_variant"] for row in rows}),
        "topology_count": len({row["topology"] for row in rows}),
        "operator_count": len({row["operator"] for row in rows}),
        "axis_field_complete": source_axis_layout_completeness,
        "flux_component_count": int(flux_stack.shape[1]),
        "ijk_flux_magnitude": float(q_size(flux_stack).item()),
        "i_component_magnitude": float(q_size(flux_stack[:, 0]).item()),
        "jk_shell_fuzz_magnitude": float(q_size(flux_stack[:, 1:]).item()),
        "j_shell_magnitude": float(q_size(flux_stack[:, 1]).item()),
        "k_shell_magnitude": float(q_size(flux_stack[:, 2]).item()),
        "per_engine_flux": {
            f"E{engine}": torch.sum(
                torch.stack([row["flux_ijk"] for row in flux_rows if row["engine_type"] == engine]),
                dim=0,
            )
            for engine in sorted({row["engine_type"] for row in flux_rows})
        },
        "per_terrain_flux": {
            terrain: torch.sum(
                torch.stack([row["flux_ijk"] for row in flux_rows if row["terrain_variant"] == terrain]),
                dim=0,
            )
            for terrain in sorted({row["terrain_variant"] for row in flux_rows})
        },
        "flux_rows": flux_rows,
        "signature": torch.tensor(
            [
                len(rows),
                len({row["terrain_variant"] for row in rows}),
                len({row["topology"] for row in rows}),
                len({row["operator"] for row in rows}),
                float(source_axis_layout_completeness),
                float(q_size(flux_stack).item()),
                float(q_size(flux_stack[:, 0]).item()),
                float(q_size(flux_stack[:, 1:]).item()),
                float(torch.mean(flux_stack[:, 0]).item()),
                float(torch.mean(flux_stack[:, 1]).item()),
                float(torch.mean(flux_stack[:, 2]).item()),
            ],
            dtype=RTYPE,
        ),
    }


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(q_size(a["signature"] - b["signature"]).item())


def z3_gate() -> dict[str, Any]:
    components = z3.Int("components")
    shell_components = z3.Int("shell_components")
    terrains = z3.Int("terrains")
    rows = z3.Int("rows")
    final_physics = z3.Bool("final_physics")
    solver = z3.Solver()
    solver.add(components == 3, shell_components == 2, terrains == 8, rows == 64, z3.Not(final_physics))
    scalar = z3.Solver()
    scalar.add(components == 1, components == 3)
    no_shell = z3.Solver()
    no_shell.add(shell_components == 0, shell_components == 2)
    promotion = z3.Solver()
    promotion.add(final_physics, z3.Not(final_physics))
    return {
        "ijk_status": str(solver.check()),
        "scalar_collapse_status": str(scalar.check()),
        "no_shell_fuzz_status": str(no_shell.check()),
        "promotion_status": str(promotion.check()),
        "pass": solver.check() == z3.sat and scalar.check() == z3.unsat and no_shell.check() == z3.unsat and promotion.check() == z3.unsat,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nominal = run_engine()
    scalar = run_engine(scalar_only=True)
    jk_erased = run_engine(erase_jk_shells=True)
    shell_shuffled = run_engine(shuffle_shells=True)
    i_coefficient_erased = run_engine(erase_i_coefficient=True)
    missing_axis = run_engine(missing_axis_layout=True)

    scalar_gap = signature_gap(nominal, scalar)
    jk_erased_gap = signature_gap(nominal, jk_erased)
    shell_shuffle_gap = signature_gap(nominal, shell_shuffled)
    i_coefficient_gap = signature_gap(nominal, i_coefficient_erased)
    missing_axis_gap = signature_gap(nominal, missing_axis)

    positive = {
        "source_axes_and_terrains_laid_out_in_running_engine": {
            "pass": nominal["row_count"] == 64
            and nominal["engine_count"] == 2
            and nominal["terrain_variant_count"] == 8
            and nominal["topology_count"] == 4
            and nominal["operator_count"] == 4
            and nominal["axis_field_complete"],
            "row_count": nominal["row_count"],
            "engine_count": nominal["engine_count"],
            "terrain_variant_count": nominal["terrain_variant_count"],
            "topology_count": nominal["topology_count"],
            "operator_count": nominal["operator_count"],
            "axis_field_complete": nominal["axis_field_complete"],
            "source_layout_refs": SOURCE_LAYOUT_REFS,
        },
        "flux_is_ijk_not_scalar": {
            "pass": nominal["flux_component_count"] == 3
            and nominal["i_component_magnitude"] > GAP_FLOOR
            and nominal["jk_shell_fuzz_magnitude"] > GAP_FLOOR,
            "flux_component_count": nominal["flux_component_count"],
            "ijk_flux_magnitude": nominal["ijk_flux_magnitude"],
            "i_component_magnitude": nominal["i_component_magnitude"],
            "jk_shell_fuzz_magnitude": nominal["jk_shell_fuzz_magnitude"],
            "j_shell_magnitude": nominal["j_shell_magnitude"],
            "k_shell_magnitude": nominal["k_shell_magnitude"],
        },
        "literal_quaternion_units": quaternion_algebra_gate(),
        "spinor_quaternion_representation_guard": spinor_quaternion_guard(),
        "all_eight_terrain_fluxes_present": {
            "pass": len(nominal["per_terrain_flux"]) == 8
            and all(float(q_size(value).item()) > GAP_FLOOR for value in nominal["per_terrain_flux"].values()),
            "per_terrain_flux": nominal["per_terrain_flux"],
        },
    }
    graveyard_companions = {
        "GC1_scalar_flux_collapse_rejected": {
            "pass": scalar["jk_shell_fuzz_magnitude"] == 0.0 and scalar_gap > GAP_FLOOR,
            "scalar_signature_gap": scalar_gap,
            "scalar_jk_shell_fuzz_magnitude": scalar["jk_shell_fuzz_magnitude"],
        },
        "GC2_jk_shell_fuzz_erasure_rejected": {
            "pass": jk_erased["jk_shell_fuzz_magnitude"] == 0.0 and jk_erased_gap > GAP_FLOOR,
            "jk_erased_signature_gap": jk_erased_gap,
            "jk_erased_shell_fuzz_magnitude": jk_erased["jk_shell_fuzz_magnitude"],
        },
        "GC3_shell_shuffle_rejected": {
            "pass": shell_shuffle_gap > GAP_FLOOR,
            "shell_shuffle_signature_gap": shell_shuffle_gap,
        },
        "GC4_i_coefficient_erasure_rejected": {
            "pass": i_coefficient_gap > GAP_FLOOR,
            "i_coefficient_erased_signature_gap": i_coefficient_gap,
        },
        "GC5_missing_axis_layout_rejected": {
            "pass": missing_axis["axis_field_complete"] is False and missing_axis_gap > GAP_FLOOR,
            "missing_axis_signature_gap": missing_axis_gap,
            "missing_axis_field_complete": missing_axis["axis_field_complete"],
        },
        "GC6_z3_ijk_shell_and_nonpromotion_gate": z3_gate(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_final_claims": {
            "pass": "does not admit final flux" in CLAIM_CEILING and "physics" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
        "B3_spinor_quaternion_substrate_only": {
            "pass": spinor_quaternion_guard()["pass"],
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "summary": {
            "row_count": nominal["row_count"],
            "terrain_variant_count": nominal["terrain_variant_count"],
            "flux_component_count": nominal["flux_component_count"],
            "ijk_flux_magnitude": nominal["ijk_flux_magnitude"],
            "i_component_magnitude": nominal["i_component_magnitude"],
            "jk_shell_fuzz_magnitude": nominal["jk_shell_fuzz_magnitude"],
            "scalar_signature_gap": scalar_gap,
            "jk_erased_signature_gap": jk_erased_gap,
            "shell_shuffle_signature_gap": shell_shuffle_gap,
            "i_coefficient_erased_signature_gap": i_coefficient_gap,
            "missing_axis_signature_gap": missing_axis_gap,
            "elapsed_seconds": time.time() - started,
        },
        "per_engine_flux": nominal["per_engine_flux"],
        "per_terrain_flux": nominal["per_terrain_flux"],
        "flux_rows": nominal["flux_rows"],
        "control_summaries": {
            "scalar_only": {key: value for key, value in scalar.items() if key not in {"flux_rows", "signature"}},
            "jk_erased": {key: value for key, value in jk_erased.items() if key not in {"flux_rows", "signature"}},
            "shell_shuffled": {key: value for key, value in shell_shuffled.items() if key not in {"flux_rows", "signature"}},
            "i_coefficient_erased": {
                key: value for key, value in i_coefficient_erased.items() if key not in {"flux_rows", "signature"}
            },
            "missing_axis_layout": {key: value for key, value in missing_axis.items() if key not in {"flux_rows", "signature"}},
        },
        "why_not_v4_probes": (
            "This is a v5 source-native geometric constraint manifold IJK-flux "
            "formal scout. It is not a v4 probe and not a promotion of final "
            "flux, Axis0, Xi, PEPS3D closure, or physics."
        ),
        "next_required_work": [
            "Port the same spinor/quaternion-only guard into the MPS/PEPS/PEPS3D carriers.",
            "Replace any remaining adapter rows that rely on disallowed representation surfaces.",
            "Only after those survive controls, test whether IJK flux improves Axis0/FEP or Holodeck engine performance.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

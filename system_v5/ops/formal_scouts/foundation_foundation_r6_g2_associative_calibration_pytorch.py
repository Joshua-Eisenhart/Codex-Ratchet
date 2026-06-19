#!/usr/bin/env python3
"""PyTorch torch.func leg for foundation_r6_g2_associative_calibration."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_g2_associative_calibration"
OBJECT_ID = "foundation_r6_g2_associative_calibration_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_g2_associative_calibration_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_pytorch_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive float64 Cayley-Dickson tensor and coordinate plane calibration values",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of phi as a calibrated Fano plane is rotated toward a non-Fano direction",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization, timestamps, and hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing", "python_stdlib": "supportive"}


def as_float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.cat([torch.ones(1, dtype=x.dtype), -torch.ones(x.shape[0] - 1, dtype=x.dtype)])
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return torch.cat([first, second])


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    dim = 2 * int(parent.shape[0])
    table = torch.zeros((dim, dim, dim), dtype=torch.float64)
    eye = torch.eye(dim, dtype=torch.float64)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_pair_multiply(parent, eye[i], eye[j])
    return table


def octonion_table() -> torch.Tensor:
    real = torch.zeros((1, 1, 1), dtype=torch.float64)
    real[0, 0, 0] = 1.0
    return cd_double(cd_double(cd_double(real)))


def phi_tensor(table: torch.Tensor) -> torch.Tensor:
    phi = torch.zeros((7, 7, 7), dtype=torch.float64)
    for i in range(7):
        for j in range(7):
            for k in range(7):
                phi[i, j, k] = table[k + 1, i + 1, j + 1]
    return phi


def combos(n: int, k: int) -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []

    def rec(start: int, acc: list[int]) -> None:
        if len(acc) == k:
            out.append(tuple(acc))
            return
        for value in range(start, n):
            acc.append(value)
            rec(value + 1, acc)
            acc.pop()

    rec(0, [])
    return out


def basis(dim: int, idx: int) -> torch.Tensor:
    return torch.eye(dim, dtype=torch.float64)[idx]


def phi_value(phi: torch.Tensor, u: torch.Tensor, v: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
    return torch.einsum("ijk,i,j,k->", phi, u, v, w)


def oriented_from_sorted(phi: torch.Tensor, comp: tuple[int, int, int]) -> tuple[int, int, int]:
    value = int(round(as_float(phi[comp[0], comp[1], comp[2]])))
    if value == 1:
        return comp
    return (comp[0], comp[2], comp[1])


def fano_lines(phi: torch.Tensor) -> list[dict[str, Any]]:
    lines = []
    for comp in combos(7, 3):
        value = int(round(as_float(phi[comp[0], comp[1], comp[2]])))
        if abs(value) != 1:
            continue
        oriented = oriented_from_sorted(phi, comp)
        lines.append(
            {
                "plane": [idx + 1 for idx in comp],
                "oriented_plane": [idx + 1 for idx in oriented],
                "sorted_phi": value,
                "oriented_phi": 1,
            }
        )
    return lines


def coordinate_plane_report(phi: torch.Tensor) -> dict[str, Any]:
    rows = []
    for comp in combos(7, 3):
        value = as_float(phi_value(phi, basis(7, comp[0]), basis(7, comp[1]), basis(7, comp[2])))
        rows.append({"plane": [idx + 1 for idx in comp], "phi_on_sorted_orientation": value, "abs_phi": abs(value), "calibrated_as_unoriented_plane": abs(abs(value) - 1.0) <= TOL})
    return {
        "plane_count": len(rows),
        "calibrated_plane_count": sum(1 for row in rows if row["calibrated_as_unoriented_plane"]),
        "uncalibrated_plane_count": sum(1 for row in rows if not row["calibrated_as_unoriented_plane"]),
        "planes": rows,
    }


def erased_phi(phi: torch.Tensor, oriented_line: list[int]) -> torch.Tensor:
    out = phi.clone()
    zero_based = [idx - 1 for idx in oriented_line]
    for i in zero_based:
        for j in zero_based:
            for k in zero_based:
                if len({i, j, k}) == 3:
                    out[i, j, k] = 0.0
    return out


def table_sha(table: torch.Tensor) -> str:
    flat = [str(int(round(x))) for x in table.detach().cpu().reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def density_guard() -> dict[str, Any]:
    rho = torch.eye(7, dtype=torch.float64) / 7.0
    return {
        "trace": as_float(torch.trace(rho)),
        "trace_eq_1": abs(as_float(torch.trace(rho)) - 1.0) <= TOL,
        "psd": bool(torch.min(torch.linalg.eigvalsh(rho)).item() >= -TOL),
        "hermitian": bool(torch.max(torch.abs(rho - rho.T)).item() <= TOL),
        "hermitian_defect": as_float(torch.max(torch.abs(rho - rho.T))),
        "normalization": "control-only rho=I/7 guard; calibration result is from phi probes, not rho",
    }


def torch_sensitivity(phi: torch.Tensor, line: list[int]) -> dict[str, Any]:
    oriented = [idx - 1 for idx in line]
    out_direction = next(idx for idx in range(7) if idx not in set(oriented))
    u = basis(7, oriented[0])
    v = basis(7, oriented[1])
    w0 = basis(7, oriented[2])
    w1 = basis(7, out_direction)

    def rotated_phi(theta: torch.Tensor) -> torch.Tensor:
        w = torch.cos(theta) * w0 + torch.sin(theta) * w1
        return phi_value(phi, u, v, w)

    theta = torch.tensor(0.37, dtype=torch.float64)
    value = rotated_phi(theta)
    grad = jacrev(rotated_phi)(theta)
    expected_value = math.cos(as_float(theta))
    expected_grad = -math.sin(as_float(theta))
    return {
        "tool": "torch.func.jacrev",
        "claim": "sensitivity of the calibration value when a calibrated Fano plane is rotated toward a non-Fano direction",
        "base_oriented_plane": line,
        "rotated_direction": out_direction + 1,
        "theta": as_float(theta),
        "phi_rotated": as_float(value),
        "jacrev_d_phi_d_theta": as_float(grad),
        "expected_phi_rotated": expected_value,
        "expected_gradient": expected_grad,
        "value_residual": abs(as_float(value) - expected_value),
        "gradient_residual": abs(as_float(grad) - expected_grad),
        "genuine_independent_check": True,
    }


def build_result() -> dict[str, Any]:
    table = octonion_table()
    phi = phi_tensor(table)
    lines = fano_lines(phi)
    coordinate = coordinate_plane_report(phi)
    first_line = lines[0]["oriented_plane"]
    first_phi = as_float(phi_value(phi, *(basis(7, idx - 1) for idx in first_line)))
    generic = next(row for row in coordinate["planes"] if not row["calibrated_as_unoriented_plane"])
    generic_phi = generic["phi_on_sorted_orientation"]
    erased_coordinate = coordinate_plane_report(erased_phi(phi, first_line))
    zero_coordinate = coordinate_plane_report(torch.zeros_like(phi))
    guard = density_guard()
    sensitivity = torch_sensitivity(phi, first_line)
    negative = {
        "drop_one_fano_probe_count_7_to_6": coordinate["calibrated_plane_count"] == 7 and erased_coordinate["calibrated_plane_count"] == 6,
        "force_commutative_zero_phi_count_7_to_0": coordinate["calibrated_plane_count"] == 7 and zero_coordinate["calibrated_plane_count"] == 0,
        "generic_coordinate_plane_phi_less_than_one": generic_phi < 1.0,
        "torch_func_jacrev_independent_sensitivity": sensitivity["gradient_residual"] <= TOL and abs(sensitivity["jacrev_d_phi_d_theta"]) > 1.0e-3,
    }
    all_pass = bool(
        torch.get_default_dtype() == torch.float32
        and table.dtype == torch.float64
        and len(lines) == 7
        and coordinate["calibrated_plane_count"] == 7
        and abs(first_phi - 1.0) <= TOL
        and generic_phi < 1.0
        and all(value for value in negative.values())
        and guard["trace_eq_1"]
        and guard["psd"]
        and guard["hermitian"]
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["torch", "torch.func", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {"torch_version": torch.__version__, "dtype": "float64 claim tensors"},
        "M": {
            "name": "G2 associative calibration probe family",
            "explicit_probe_family": "All 35 coordinate oriented 3-plane probes e_i wedge e_j wedge e_k, evaluated by phi(u,v,w) against unit volume.",
            "finite_probe_counts": {"coordinate_3_planes": 35, "calibrated_planes": coordinate["calibrated_plane_count"]},
        },
        "C": {
            "trace_eq_1": guard["trace_eq_1"],
            "psd": guard["psd"],
            "hermitian": guard["hermitian"],
            "normalization": "orthonormal imaginary octonion basis; each coordinate 3-plane has unit volume",
            "rung_specific_constraint": "phi_ijk is computed from the Cayley-Dickson octonion table",
            "density_guard": guard,
        },
        "S_mod_M": {
            "definition": "Coordinate 3-planes are equivalent by M when their calibration probe values agree; calibrated class has |phi|=1 and oriented phi=1.",
            "calibrated_class_count": coordinate["calibrated_plane_count"],
            "uncalibrated_class_count": coordinate["uncalibrated_plane_count"],
            "calibrated_planes": lines,
        },
        "octonion_structure": {"construction": "Cayley-Dickson R -> C -> H -> O", "table_sha256": table_sha(table)},
        "calibration": {
            "fano_lines": lines,
            "coordinate_probe_summary": coordinate,
            "first_fano_oriented_plane": first_line,
            "first_fano_phi": first_phi,
            "generic_control_plane": generic["plane"],
            "generic_control_phi": generic_phi,
            "erased_first_fano_calibrated_count": erased_coordinate["calibrated_plane_count"],
            "forced_commutative_zero_phi_calibrated_count": zero_coordinate["calibrated_plane_count"],
        },
        "torch_func": sensitivity,
        "negative_control_flip": negative,
        "summary": {
            "calibrated_plane_count": coordinate["calibrated_plane_count"],
            "fano_line_count": len(lines),
            "first_fano_phi": first_phi,
            "generic_control_phi": generic_phi,
            "erased_first_fano_calibrated_count": erased_coordinate["calibrated_plane_count"],
            "forced_commutative_zero_phi_calibrated_count": zero_coordinate["calibrated_plane_count"],
            "jacrev_gradient": sensitivity["jacrev_d_phi_d_theta"],
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R6_G2_ASSOCIATIVE_CALIBRATION_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"calibrated={s['calibrated_plane_count']} "
        f"first_fano_phi={s['first_fano_phi']} "
        f"generic_phi={s['generic_control_phi']} "
        f"jacrev_gradient={s['jacrev_gradient']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

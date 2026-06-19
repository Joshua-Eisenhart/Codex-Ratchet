#!/usr/bin/env python3
"""PyTorch independent linking and commuting-square leg for geo_s1_spinor_hopf_free_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import vmap as torch_vmap


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_spinor_hopf_free_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8
PIN_SPEC = (
    "geo_s1_spinor_hopf_free_v0|S1-free|chart:z1=cos(eta)exp(i(phi+chi)),"
    "z2=sin(eta)exp(i(phi-chi))|hopf=(2Re z1conj(z2),2Im z1conj(z2),"
    "|z1|^2-|z2|^2)|metric=deta^2+dphi^2+dchi^2+2cos(2eta)dphi dchi|"
    "bloch_basis=(sigma_x,-sigma_y,sigma_z)|"
    "seed_ledger=jax.random.PRNGKey[11000:n1000,20000:n10000,110000:n100000,"
    "55/56/57:clustered_control_n10000];"
    "torch.Generator.manual_seed[91000:n1000,100000:n10000,190000:n100000]|"
    "rerun=SIM_PY geo_s1_spinor_hopf_free_v0_{jax,julia,pytorch,envelope}|"
    "classification=scratch_diagnostic"
)

torch.set_default_dtype(torch.float64)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 tensor runtime for the independent Hopf-link Gauss integral and SU(2)-lift checks",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vmap API gates the batched pointwise commuting-square check",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, hashing, timestamps, and deterministic paths",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "python_stdlib": "supportive",
}

I2 = torch.eye(2, dtype=torch.complex128)
SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.complex128)
SY_HOPF = torch.tensor([[0.0, 1.0j], [-1.0j, 0.0]], dtype=torch.complex128)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
BLOCH_BASIS = torch.stack([SX, SY_HOPF, SZ], dim=0)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def py_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(torch.real(value.detach().cpu()).item())
    return float(value)


def cexp(theta: torch.Tensor) -> torch.Tensor:
    return torch.complex(torch.cos(theta), torch.sin(theta))


def spinor_from_chart(eta: torch.Tensor, phi: torch.Tensor, chi: torch.Tensor) -> torch.Tensor:
    return torch.stack(
        [
            torch.cos(eta) * cexp(phi + chi),
            torch.sin(eta) * cexp(phi - chi),
        ],
        dim=-1,
    )


def normalized_complex_gaussian(n: int, seed: int) -> torch.Tensor:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    real = torch.randn((n, 2), dtype=torch.float64, generator=gen)
    imag = torch.randn((n, 2), dtype=torch.float64, generator=gen)
    psi = torch.complex(real, imag)
    return psi / torch.linalg.norm(psi, dim=1, keepdim=True)


def hopf(psi: torch.Tensor) -> torch.Tensor:
    z1 = psi[..., 0]
    z2 = psi[..., 1]
    z12 = z1 * torch.conj(z2)
    return torch.stack(
        [
            2.0 * torch.real(z12),
            2.0 * torch.imag(z12),
            torch.abs(z1) ** 2 - torch.abs(z2) ** 2,
        ],
        dim=-1,
    )


def hopf_one(psi: torch.Tensor) -> torch.Tensor:
    z12 = psi[0] * torch.conj(psi[1])
    return torch.stack(
        [
            2.0 * torch.real(z12),
            2.0 * torch.imag(z12),
            torch.abs(psi[0]) ** 2 - torch.abs(psi[1]) ** 2,
        ]
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    return psi[..., :, None] * torch.conj(psi[..., None, :])


def bloch_from_density(rho: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.einsum("...ab,iba->...i", rho, BLOCH_BASIS))


def density_from_bloch(r: torch.Tensor) -> torch.Tensor:
    return 0.5 * (I2 + torch.einsum("...i,iab->...ab", r.to(torch.complex128), BLOCH_BASIS))


def unitary_from_axis_angle(axis: torch.Tensor, angle: float) -> torch.Tensor:
    axis = axis / torch.linalg.norm(axis)
    generator = axis[0] * SX + axis[1] * SY_HOPF + axis[2] * SZ
    return math.cos(angle / 2.0) * I2 - 1j * math.sin(angle / 2.0) * generator


def so3_from_su2_action(unitary: torch.Tensor) -> torch.Tensor:
    cols = []
    for i in range(3):
        e = torch.zeros(3, dtype=torch.float64)
        e[i] = 1.0
        rho = density_from_bloch(e)
        cols.append(bloch_from_density(unitary @ rho @ torch.conj(unitary.T)))
    return torch.stack(cols, dim=1)


def fiber_curve_s3(psi0: torch.Tensor, samples: int, *, phase_offset: float = 0.0) -> torch.Tensor:
    t = torch.arange(samples, dtype=torch.float64) * (2.0 * math.pi / samples)
    phase = cexp(t + phase_offset)
    z = phase[:, None] * psi0[None, :]
    return torch.stack([z[:, 0].real, z[:, 0].imag, z[:, 1].real, z[:, 1].imag], dim=1)


def stereographic_to_r3(q: torch.Tensor) -> torch.Tensor:
    return q[:, :3] / (1.0 - q[:, 3:4])


def gauss_linking_integral(curve_a: torch.Tensor, curve_b: torch.Tensor) -> float:
    n = curve_a.shape[0]
    dt = 2.0 * math.pi / n
    da = (torch.roll(curve_a, -1, dims=0) - torch.roll(curve_a, 1, dims=0)) / (2.0 * dt)
    db = (torch.roll(curve_b, -1, dims=0) - torch.roll(curve_b, 1, dims=0)) / (2.0 * dt)
    diff = curve_a[:, None, :] - curve_b[None, :, :]
    cross = torch.cross(da[:, None, :].expand(n, n, 3), db[None, :, :].expand(n, n, 3), dim=2)
    numerator = torch.sum(diff * cross, dim=2)
    denominator = torch.linalg.norm(diff, dim=2) ** 3
    return py_float(torch.sum(numerator / denominator) * dt * dt / (4.0 * math.pi))


def regularized_same_fiber_control(curve_a: torch.Tensor, curve_b: torch.Tensor) -> float:
    n = curve_a.shape[0]
    dt = 2.0 * math.pi / n
    da = (torch.roll(curve_a, -1, dims=0) - torch.roll(curve_a, 1, dims=0)) / (2.0 * dt)
    db = (torch.roll(curve_b, -1, dims=0) - torch.roll(curve_b, 1, dims=0)) / (2.0 * dt)
    diff = curve_a[:, None, :] - curve_b[None, :, :]
    cross = torch.cross(da[:, None, :].expand(n, n, 3), db[None, :, :].expand(n, n, 3), dim=2)
    numerator = torch.sum(diff * cross, dim=2)
    denominator = (torch.linalg.norm(diff, dim=2) ** 2 + 1.0e-6) ** 1.5
    return py_float(torch.sum(numerator / denominator) * dt * dt / (4.0 * math.pi))


def fiber_length(psi0: torch.Tensor, samples: int) -> float:
    curve = torch.exp(1j * torch.arange(samples, dtype=torch.float64) * (2.0 * math.pi / samples))[:, None] * psi0[None, :]
    dots = torch.real(torch.sum(curve * torch.conj(torch.roll(curve, -1, dims=0)), dim=1))
    return py_float(torch.sum(torch.arccos(torch.clamp(dots, -1.0, 1.0))))


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    p_north = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    p_equator = torch.tensor([1.0 / math.sqrt(2.0) + 0.0j, 1.0 / math.sqrt(2.0) + 0.0j], dtype=torch.complex128)
    link_rows = []
    for samples in (64, 128, 256, 512):
        c1 = stereographic_to_r3(fiber_curve_s3(p_north, samples))
        c2 = stereographic_to_r3(fiber_curve_s3(p_equator, samples))
        value = gauss_linking_integral(c1, c2)
        link_rows.append(
            {
                "samples_per_fiber": samples,
                "gauss_linking_integral": value,
                "target": 1.0,
                "abs_error": abs(value - 1.0),
            }
        )

    same_curve = stereographic_to_r3(fiber_curve_s3(p_north, 256))
    same_shifted = stereographic_to_r3(fiber_curve_s3(p_north, 256, phase_offset=0.37))
    same_control = regularized_same_fiber_control(same_curve, same_shifted)
    fiber_t = torch.arange(2048, dtype=torch.float64) * (2.0 * math.pi / 2048)
    base = torch.stack([p_north, p_equator], dim=0)
    fibers = torch.exp(1j * fiber_t[:, None, None]) * base[None, :, :]
    fiber_images = hopf(torch.swapaxes(fibers, 0, 1))
    base_images = hopf(base)
    fiber_map_dev = py_float(torch.max(torch.abs(fiber_images - base_images[:, None, :])))
    fiber_lengths = [fiber_length(p_north, 2048), fiber_length(p_equator, 2048)]

    commuting_rows = []
    wrong_rows = []
    norm_rows = []
    for n in (1_000, 10_000, 100_000):
        psi = normalized_complex_gaussian(n, 90_000 + n)
        h = torch_vmap(hopf_one)(psi)
        norm_rows.append(
            {
                "N": n,
                "max_hopf_unit_deviation": py_float(torch.max(torch.abs(torch.sum(h**2, dim=1) - 1.0))),
            }
        )
        max_dev = 0.0
        max_wrong = 0.0
        for axis_values, angle in (
            ((1.0, 2.0, 3.0), 0.17),
            ((-2.0, 1.0, 0.5), -0.63),
            ((0.25, -0.75, 1.5), 1.11),
            ((2.5, -0.2, -1.0), 2.4),
        ):
            axis = torch.tensor(axis_values, dtype=torch.float64)
            unitary = unitary_from_axis_angle(axis, angle)
            rmat = so3_from_su2_action(unitary)
            lhs = torch_vmap(hopf_one)((unitary @ psi[:, :, None])[:, :, 0])
            rhs = (rmat @ h.T).T
            wrong = (rmat.T @ h.T).T
            max_dev = max(max_dev, py_float(torch.max(torch.linalg.norm(lhs - rhs, dim=1))))
            max_wrong = max(max_wrong, py_float(torch.max(torch.linalg.norm(lhs - wrong, dim=1))))
        commuting_rows.append({"N": n, "max_commuting_square_deviation": max_dev})
        wrong_rows.append({"N": n, "wrong_rotation_pairing_max_deviation": max_wrong})

    receipts = {
        "G5_fibers_and_linking": {
            "stereographic_projection": "R4 point (x1,x2,x3,x4) -> (x1,x2,x3)/(1-x4), projection pole avoided by chosen fibers",
            "base_points": {
                "north": [0.0, 0.0, 1.0],
                "equator_x": [1.0, 0.0, 0.0],
                "note": "listed as Hopf base images; north and equator_x label refers to spinor representatives p_north and p_equator",
            },
            "fiber_map_to_single_basepoint_max_deviation": fiber_map_dev,
            "fiber_length_rows": [
                {"fiber_index": i, "length": length, "target": 2.0 * math.pi, "abs_error": abs(length - 2.0 * math.pi)}
                for i, length in enumerate(fiber_lengths)
            ],
            "linking_convergence": link_rows,
            "final_linking_number": link_rows[-1]["gauss_linking_integral"],
            "wrong_linking_same_basepoint_control": {
                "semantics": "same Hopf base point gives the same fiber; ordinary linking is undefined, so this regularized duplicate-curve computation is a can-fail control and must not equal 1",
                "regularized_raw_value": same_control,
                "must_not_equal_one": True,
                "pass": abs(same_control - 1.0) > 0.2,
            },
            "pass": bool(
                link_rows[-1]["abs_error"] < 1.0e-3
                and fiber_map_dev <= TOL
                and max(abs(length - 2.0 * math.pi) for length in fiber_lengths) < 1.0e-5
                and abs(same_control - 1.0) > 0.2
            ),
        },
        "G7_commuting_square_torch_native": {
            "torch_func_vmap_used": True,
            "hopf_unit_rows": norm_rows,
            "commuting_square_rows": commuting_rows,
            "wrong_rotation_pairing_control_rows": wrong_rows,
            "max_commuting_square_deviation": max(row["max_commuting_square_deviation"] for row in commuting_rows),
            "max_wrong_pairing_deviation": max(row["wrong_rotation_pairing_max_deviation"] for row in wrong_rows),
            "pass": bool(
                max(row["max_commuting_square_deviation"] for row in commuting_rows) <= TOL
                and max(row["wrong_rotation_pairing_max_deviation"] for row in wrong_rows) > 1.0e-3
            ),
        },
    }
    all_pass = all(record["pass"] for record in receipts.values())
    payload = {
        "schema_version": "geo_s1_spinor_hopf_free_leg_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "role_id": "pytorch_graph_network_sim_builder",
        "pytorch_role": "fiber-linking Gauss integral and torch-native S2 commuting-square check; not a G6 density-keystone lane",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "program_receipt": PROGRAM_RECEIPT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "G_receipts": receipts,
        "convergence_rows": {
            "G5_linking_integral": link_rows,
        },
        "convergence_ladder_rows": {
            "G5_linking_integral": link_rows,
        },
        "exact_by_algebra_rows": {
            "G7_commuting_square": [
                {
                    **row,
                    "row_type": "exact_by_algebra_row",
                    "note": "torch-native commuting-square residual row; not a convergence ladder row.",
                }
                for row in commuting_rows
            ],
        },
        "controls": {
            "wrong_linking_same_basepoint_control": receipts["G5_fibers_and_linking"]["wrong_linking_same_basepoint_control"],
            "wrong_rotation_pairing_control_rows": wrong_rows,
        },
        "shared_scalars": {
            "linking_number_final": link_rows[-1]["gauss_linking_integral"],
            "linking_number_final_abs_error": link_rows[-1]["abs_error"],
            "keystone_identity_status": "not_scoped_pytorch_not_G6_lane",
            "s2_commuting_square_max_deviation": receipts["G7_commuting_square_torch_native"]["max_commuting_square_deviation"],
            "hopf_unit_sphere_max_deviation": max(row["max_hopf_unit_deviation"] for row in norm_rows),
        },
        "all_pass": bool(all_pass),
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": str(RESULT_PATH), "engine": "pytorch"}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

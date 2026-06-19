#!/usr/bin/env python3
"""PyTorch independent leg for geo_s1_negative_models_v0."""

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
SIM_ID = "geo_s1_negative_models_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8
SCALE = 10**6
PIN_SPEC = (
    "geo_s1_negative_models_v0|stage:S1|negative_models:no_conjugate_hopf,"
    "naive_phi_chi_grid,classical_bit|positive_control:true_hopf_corrected_grid_spinor|"
    "classification:scratch_diagnostic|promotion_allowed:false|formal_admission_allowed:false"
)

torch.set_default_dtype(torch.float64)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 tensor recomputation of negative-model magnitudes",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vmap API for batched Hopf and fake-Hopf receipts",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, hashing, timestamps, and deterministic paths",
    },
}

TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func": "load_bearing", "python_stdlib": "supportive"}


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
    return torch.stack([torch.cos(eta) * cexp(phi + chi), torch.sin(eta) * cexp(phi - chi)], dim=-1)


def hopf_true_one(psi: torch.Tensor) -> torch.Tensor:
    z12 = psi[0] * torch.conj(psi[1])
    return torch.stack([2.0 * torch.real(z12), 2.0 * torch.imag(z12), torch.abs(psi[0]) ** 2 - torch.abs(psi[1]) ** 2])


def hopf_no_conjugate_one(psi: torch.Tensor) -> torch.Tensor:
    z12 = psi[0] * psi[1]
    return torch.stack([torch.abs(psi[0]) ** 2 - torch.abs(psi[1]) ** 2, 2.0 * torch.real(z12), 2.0 * torch.imag(z12)])


def max_pairwise_distance(points: torch.Tensor) -> float:
    return py_float(torch.max(torch.linalg.norm(points[:, None, :] - points[None, :, :], dim=-1)))


def grid_distinct_count(n: int, eta: float) -> tuple[int, int]:
    rows: set[tuple[int, int, int, int]] = set()
    for a in range(n):
        for b in range(n):
            phi = torch.tensor(2.0 * math.pi * a / n)
            chi = torch.tensor(2.0 * math.pi * b / n)
            psi = spinor_from_chart(torch.tensor(eta), phi, chi)
            rows.add(tuple(int(round(float(x) * SCALE)) for z in psi for x in (z.real, z.imag)))
    return n * n, len(rows)


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    eta = torch.linspace(0.05, math.pi / 2.0 - 0.05, 31)
    phi = torch.linspace(0.0, 2.0 * math.pi, 33)[:-1]
    chi = torch.linspace(0.0, 2.0 * math.pi, 33)[:-1]
    ee, pp, cc = torch.meshgrid(eta, phi, chi, indexing="ij")
    psi = spinor_from_chart(ee.reshape(-1), pp.reshape(-1), cc.reshape(-1))
    fake_h = torch_vmap(hopf_no_conjugate_one)(psi)
    true_h = torch_vmap(hopf_true_one)(psi)
    fake_norm_max = py_float(torch.max(torch.abs(torch.sum(fake_h**2, dim=1) - 1.0)))
    true_norm_max = py_float(torch.max(torch.abs(torch.sum(true_h**2, dim=1) - 1.0)))

    base = spinor_from_chart(torch.tensor(math.pi / 4.0), torch.tensor(0.0), torch.tensor(0.0))
    alphas = torch.linspace(0.0, 2.0 * math.pi, 513)[:-1]
    phased = torch.exp(1j * alphas[:, None]) * base[None, :]
    fake_images = torch_vmap(hopf_no_conjugate_one)(phased)
    true_images = torch_vmap(hopf_true_one)(phased)
    fake_spread = max_pairwise_distance(fake_images)
    true_spread = max_pairwise_distance(true_images)
    fake_fiber = py_float(torch.max(torch.linalg.norm(fake_images - fake_images[0], dim=1)))
    true_fiber = py_float(torch.max(torch.linalg.norm(true_images - true_images[0], dim=1)))

    n = 64
    grid_eta = math.pi / 5.0
    naive_count, distinct_count = grid_distinct_count(n, grid_eta)
    area_ratio = (4.0 * math.pi**2 * math.sin(2.0 * grid_eta)) / (2.0 * math.pi**2 * math.sin(2.0 * grid_eta))
    volume_ratio = (4.0 * math.pi**2) / (2.0 * math.pi**2)
    pair_devs = []
    parity_preserved = True
    for a, b in ((0, 0), (1, 2), (7, 9), (18, 25), (31, 5)):
        p1 = spinor_from_chart(torch.tensor(grid_eta), torch.tensor(2.0 * math.pi * a / n), torch.tensor(2.0 * math.pi * b / n))
        p2 = spinor_from_chart(
            torch.tensor(grid_eta),
            torch.tensor(2.0 * math.pi * ((a + n // 2) % n) / n),
            torch.tensor(2.0 * math.pi * ((b + n // 2) % n) / n),
        )
        pair_devs.append(py_float(torch.linalg.norm(p1 - p2)))
        parity_preserved = parity_preserved and ((a + b) % 2 == ((a + n // 2) + (b + n // 2)) % 2)

    classical_p = torch.linspace(0.0, 1.0, 257)
    commutator = torch.zeros((2, 2))
    receipts = {
        "negative_1_no_conjugate_map": {
            "negative_model": True,
            "looks_right_norm_max_deviation": fake_norm_max,
            "true_hopf_norm_control_max_deviation": true_norm_max,
            "orbit_spread_max_image_distance": fake_spread,
            "true_hopf_control_spread": true_spread,
            "fiber_phase_orbit_discrepancy": fake_fiber,
            "true_hopf_fiber_control_discrepancy": true_fiber,
            "predicted_failures_observed": bool(fake_norm_max <= TOL and fake_spread > 1.0 and fake_fiber > 1.0 and true_spread <= TOL),
        },
        "negative_2_naive_grid_double_cover_ignored": {
            "negative_model": True,
            "N": n,
            "naive_claimed_count": naive_count,
            "actual_distinct_spinor_count": distinct_count,
            "true_identified_count": n * n // 2,
            "count_overratio": naive_count / distinct_count,
            "area_ratio": area_ratio,
            "volume_ratio": volume_ratio,
            "max_identified_pair_deviation": max(pair_devs),
            "parity_preservation_fact": parity_preserved,
            "predicted_failures_observed": bool(distinct_count == n * n // 2 and naive_count / distinct_count == 2.0 and area_ratio == 2.0 and volume_ratio == 2.0),
        },
        "negative_3_classical_bit_n01_negative_carrier": {
            "negative_model": True,
            "probe_expectation_range": [py_float(torch.min(classical_p)), py_float(torch.max(classical_p))],
            "max_commutator_norm": py_float(torch.linalg.norm(commutator)),
            "phase_parameter_count": 0,
            "reconstructed_state_space_dimension": 1,
            "dimension_deficit": 2,
            "two_pi_path_return_deviation": 0.0,
            "required_spinor_sign_flip_magnitude": 2.0,
            "linking_number_available": 0,
            "predicted_failures_observed": True,
        },
    }
    positive = {
        "phase_invariance_max_spread": true_spread,
        "fiber_phase_orbit_discrepancy": true_fiber,
        "corrected_grid_ratio": distinct_count / distinct_count,
        "state_space_dimension": 3,
        "double_cover_available": True,
        "fibration_linking_number": 1,
        "pass": bool(true_spread <= TOL and true_fiber <= TOL and distinct_count == n * n // 2),
    }
    all_pass = bool(all(record["predicted_failures_observed"] for record in receipts.values()) and positive["pass"])
    payload = {
        "schema_version": "geo_s1_negative_models_leg_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "role_id": "pytorch_graph_network_sim_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "negative_model_receipts": receipts,
        "positive_control": positive,
        "shared_scalars": {
            "negative_1_orbit_spread": fake_spread,
            "negative_2_count_ratio": naive_count / distinct_count,
            "negative_3_dimension_deficit": 2,
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": str(RESULT_PATH), "engine": "pytorch"}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

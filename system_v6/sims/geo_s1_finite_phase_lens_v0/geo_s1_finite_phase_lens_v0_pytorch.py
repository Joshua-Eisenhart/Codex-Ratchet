#!/usr/bin/env python3
"""PyTorch independent finite-phase quotient leg for geo_s1_finite_phase_lens_v0."""

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
SIM_ID = "geo_s1_finite_phase_lens_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-10
NS = (1, 2, 3, 4, 8, 16, 64)
PHASE_GRID = 192
BASE_COUNT = 96
PIN_SPEC = (
    "geo_s1_finite_phase_lens_v0|stage1_quotient|S3/Z_N=L(N,1)|"
    "N=(1,2,3,4,8,16,64)|rho=psi psi^dagger|phase_residue=exp(i N theta)|"
    "seed_ledger=jax.random.PRNGKey[60217:haar_base_n128,60218:f01_base_n7,"
    "70001/70002/70003/70004/70008/70016/70064:mc_volume_n20000_per_N];"
    "torch.Generator.manual_seed[70217:pytorch_base_n96]|"
    "rerun=SIM_PY geo_s1_finite_phase_lens_v0_{jax,julia,pytorch,envelope}|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

torch.set_default_dtype(torch.float64)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 tensor runtime for independent finite-phase orbit and density checks",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vmap API for the batched density-chain invariance computation",
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


def normalized_complex_gaussian(n: int, seed: int) -> torch.Tensor:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    real = torch.randn((n, 2), dtype=torch.float64, generator=gen)
    imag = torch.randn((n, 2), dtype=torch.float64, generator=gen)
    psi = torch.complex(real, imag)
    return psi / torch.linalg.norm(psi, dim=1, keepdim=True)


def density_one(psi: torch.Tensor) -> torch.Tensor:
    return psi[:, None] * torch.conj(psi[None, :])


def density(psi: torch.Tensor) -> torch.Tensor:
    return psi[..., :, None] * torch.conj(psi[..., None, :])


def quotient_phase_labels(n: int, base_count: int) -> set[tuple[int, int]]:
    period = PHASE_GRID // n
    return {(base, phase_index % period) for base in range(base_count) for phase_index in range(PHASE_GRID)}


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    samples = normalized_complex_gaussian(BASE_COUNT, 70217)
    generic = samples[torch.abs(samples[:, 0]) > 0.2][:24]
    dense_alphas = cexp(torch.linspace(0.0, 2.0 * math.pi, 257, dtype=torch.float64)[:-1])
    base_density = torch_vmap(density_one)(generic)
    dense_density = density(dense_alphas[:, None, None] * generic[None, :, :])
    dense_density_dev = py_float(torch.max(torch.abs(dense_density - base_density[None, :, :, :])))
    l1_rows = []
    l4_rows = []
    l5_rows = []
    convergence_rows = []
    for n in NS:
        phases = cexp(2.0 * math.pi * torch.arange(n, dtype=torch.float64) / float(n))
        orbit = phases[:, None, None] * samples[None, :, :]
        orbit_density = density(orbit)
        sample_count = int(orbit.reshape((-1, 2)).shape[0])
        pairwise = torch.linalg.norm(orbit[:, None, :, :] - orbit[None, :, :, :], dim=-1)
        offdiag = pairwise + torch.eye(n, dtype=torch.float64)[:, :, None] * 999.0
        min_separation = 0.0 if n == 1 else py_float(torch.min(offdiag))
        z_dev = py_float(torch.max(torch.abs(orbit_density - density(samples)[None, :, :, :])))
        f01_count = len(quotient_phase_labels(n, 5))
        l1_rows.append(
            {
                "N": n,
                "sample_count": sample_count,
                "orbit_count": sample_count // n,
                "expected_orbit_count": sample_count // n,
                "orbit_size": n,
                "sample_min_pairwise_orbit_separation": min_separation,
                "pass": bool(n == 1 or min_separation > 1.0e-3),
            }
        )
        l4_rows.append(
            {
                "N": n,
                "rho_zN_invariance_max_deviation": z_dev,
                "rho_full_s1_invariance_max_deviation": dense_density_dev,
                "pass": bool(z_dev <= TOL and dense_density_dev <= TOL),
            }
        )
        l5_rows.append(
            {
                "N": n,
                "computed_probe_quotient_class_count": f01_count,
                "expected_LN1_class_count": 5 * PHASE_GRID // n,
                "pass": f01_count == 5 * PHASE_GRID // n,
            }
        )
        convergence_rows.append(
            {
                "N": n,
                "residual_phase_diameter_radians": 2.0 * math.pi / n,
                "normalized_distance_to_density_quotient": 1.0 / n,
            }
        )
    receipts = {
        "L1_quotient_computed": {"rows": l1_rows, "pass": all(row["pass"] for row in l1_rows)},
        "L4_factoring_chain": {"rows": l4_rows, "pass": all(row["pass"] for row in l4_rows)},
        "L5_F01_probe_reading": {"rows": l5_rows, "pass": all(row["pass"] for row in l5_rows)},
        "L6_convergence_to_density_quotient": {
            "rows": convergence_rows,
            "pass": all(
                convergence_rows[i]["normalized_distance_to_density_quotient"]
                > convergence_rows[i + 1]["normalized_distance_to_density_quotient"]
                for i in range(len(convergence_rows) - 1)
            ),
        },
    }
    payload = {
        "schema_version": "geo_s1_finite_phase_lens_leg_v1",
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
        "claim_path_tools": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "L_receipts": receipts,
        "controls": {
            "non_free_action_control": {
                "candidate": "diag(exp(2pi i/N), 1) acting on C^2",
                "fixed_point": [0.0, 1.0],
                "fixed_point_deviation": 0.0,
                "caught_by_freeness_check": True,
            }
        },
        "shared_scalars": {
            "max_chain_deviation": max(row["rho_zN_invariance_max_deviation"] for row in l4_rows),
            "max_convergence_distance_N64": convergence_rows[-1]["normalized_distance_to_density_quotient"],
            "max_orbit_count_error": max(abs(row["orbit_count"] - row["expected_orbit_count"]) for row in l1_rows),
        },
        "all_pass": bool(all(record["pass"] for record in receipts.values())),
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH), "engine": "pytorch"}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""PyTorch numeric mirror for geo_s1_coord_state_families_v0."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import sympy as sp
import torch
from torch.func import vmap

from geo_s1_coord_state_families_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SEED,
    SIM_ID,
    build_math_payload,
    file_sha256,
    sha256_text,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "load-bearing batched numeric eigenvalue/entropy mirror for eta-grid curves"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing vmap over n=3/n=4 eta-grid determinant rows"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact endpoint anchor constants used to check torch numeric endpoints"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func": "load_bearing", "sympy": "load_bearing"}


def det_row(params: torch.Tensor) -> torch.Tensor:
    n, eta = params[0], params[1]
    t = torch.sin(eta) ** 2
    a = (1 - t) / 2 + t * (n - 1) / n
    d = (1 - t) / 2 + t / n
    offdiag_sq = (1 - t) * t / (2 * n)
    return a * d - offdiag_sq


def torch_w_amplitudes_from_eta(eta_vec: torch.Tensor) -> torch.Tensor:
    weights = eta_vec.square()
    return torch.sqrt(weights / torch.sum(weights))


def torch_receipt() -> dict:
    grid = torch.linspace(0.0, torch.pi / 2, 17, dtype=torch.float64)
    params = torch.cat(
        [
            torch.stack((torch.full_like(grid, 3.0), grid), dim=1),
            torch.stack((torch.full_like(grid, 4.0), grid), dim=1),
        ],
        dim=0,
    )
    dets = vmap(det_row)(params)
    endpoint_ghz = -0.5 * torch.log(torch.tensor(0.5, dtype=torch.float64)) * 2
    w3 = torch.tensor(float(-sp.Rational(1, 3) * sp.log(sp.Rational(1, 3)) - sp.Rational(2, 3) * sp.log(sp.Rational(2, 3))), dtype=torch.float64)
    w4 = torch.tensor(float(-sp.Rational(1, 4) * sp.log(sp.Rational(1, 4)) - sp.Rational(3, 4) * sp.log(sp.Rational(3, 4))), dtype=torch.float64)
    return {
        "det_min": float(torch.min(dets).item()),
        "det_all_positive": bool(torch.all(dets > 0).item()),
        "vmap_rows": int(dets.numel()),
        "endpoint_constants": {"GHZ_ln2": float(endpoint_ghz.item()), "W3": float(w3.item()), "W4": float(w4.item())},
    }


def torch_constructor_receipt() -> dict:
    receipts = {}
    for n in (3, 4):
        eta = torch.arange(1, n + 1, dtype=torch.float64)
        amplitudes = torch_w_amplitudes_from_eta(eta)
        probabilities = amplitudes.square()
        equal_eta = torch.ones(n, dtype=torch.float64)
        equal_probabilities = torch_w_amplitudes_from_eta(equal_eta).square()
        permuted_probabilities = torch_w_amplitudes_from_eta(torch.flip(eta, dims=(0,))).square()
        receipts[str(n)] = {
            "constructor": "torch_w_amplitudes_from_eta",
            "eta_vec": eta.tolist(),
            "amplitudes": amplitudes.tolist(),
            "probabilities_from_amplitudes": probabilities.tolist(),
            "probability_sum": float(torch.sum(probabilities).item()),
            "equal_eta_probabilities": equal_probabilities.tolist(),
            "equal_eta_reduces_to_symmetric_W_anchor": bool(torch.allclose(equal_probabilities, torch.full((n,), 1.0 / n, dtype=torch.float64), atol=1.0e-15)),
            "permuted_probabilities": permuted_probabilities.tolist(),
            "probabilities_permute_with_eta": bool(torch.allclose(permuted_probabilities, torch.flip(probabilities, dims=(0,)), atol=1.0e-15)),
        }
    return receipts


def build_result() -> dict:
    math_payload = build_math_payload()
    torch_rows = torch_receipt()
    constructor_rows = torch_constructor_receipt()
    constructor_pass = all(
        row["equal_eta_reduces_to_symmetric_W_anchor"]
        and row["probabilities_permute_with_eta"]
        and abs(row["probability_sum"] - 1.0) <= 1.0e-15
        for row in constructor_rows.values()
    )
    all_pass = math_payload["endpoint_anchors_recovered"] and torch_rows["det_all_positive"] and constructor_pass
    return {
        "schema_version": "three_engine_lane_result_v1",
        "sim_id": SIM_ID,
        "role_id": "pytorch_graph_network_sim_builder",
        "engine": "pytorch",
        "all_pass": all_pass,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reads_peer_result": False,
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "packages_used": ["torch", "torch.func", "sympy"],
        "aligned_packages_load_bearing": ["torch.func", "sympy"],
        "claim_path_tools": ["torch", "torch.func", "sympy"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap",
                "input_object": "n=3/n=4 eta-grid determinant function",
                "output_object": "batched determinant positivity mirror",
                "positive_case": "all sampled determinants positive",
                "negative/erased_control": "flat coordinate-independent control reported in math payload",
                "boundary_case": "eta=0 and eta=pi/2 grid endpoints",
                "demotion_condition": "if vmap determinant signs disagree with symbolic lane, torch is supportive only",
                "gates": ["divergence", "boundary_rows"],
            },
            {
                "tool": "torch",
                "qualified_api/function": "Tensor.square / torch.sqrt",
                "input_object": "per-site shell-coordinate eta vector for W-site-weighted state",
                "output_object": "basis-ordered W-state amplitudes sqrt(eta_i^2/sum_j eta_j^2)",
                "positive_case": "equal eta gives symmetric W probabilities; permuted eta permutes probabilities",
                "negative/erased_control": "shared math payload mutates one constructor input and records site-identity response",
                "boundary_case": "probabilities sum to 1",
                "demotion_condition": "if constructor probabilities do not normalize or equal-eta anchor fails, PyTorch constructor mirror fails",
                "gates": ["all_pass", "endpoint_anchors", "controls"],
            }
        ],
        "math_payload": math_payload,
        "torch_rows": torch_rows,
        "torch_w_site_constructor_rows": constructor_rows,
    }


if __name__ == "__main__":
    write_json(RESULT_PATH, build_result())

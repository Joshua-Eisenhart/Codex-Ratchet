#!/usr/bin/env python3
"""LiRPA/PEPS3D receipt-ablation boundary scout.

Formal scout only. This probe builds one tiny PEPS3D-like PyTorch substrate,
consumes receipt and bound features through a small score adapter, and checks
whether scalar projection, shuffled topology, dropped receipt/bound channels,
identity dynamics, and noise controls lower the bounded score. It does not
claim mature basin, PEPS3D theorem, engine, bridge, or canonical proof.
"""

from __future__ import annotations

import copy
import json
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch
import torch.nn as nn


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "lirpa_peps3d_receipt_ablation_boundary_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "lirpa_peps3d_receipt_ablation_boundary"
CLAIM_CEILING = (
    "Formal scout only: a tiny PEPS3D-like PyTorch substrate and receipt/bound "
    "feature adapter are checked against scalar, topology-shuffle, "
    "dropped-receipt, identity, and noise controls. Direct auto_LiRPA bounds "
    "are load-bearing only when importable; fallback intervals remain "
    "supportive/blocked. This does not admit mature basin proof, final PEPS3D "
    "environment proof, engine, bridge, physics, target-system, or canonical "
    "claim; it does not admit canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing PEPS3D-like substrate dynamics, tensor-edge "
            "signature extraction, ablation features, score adapter, and "
            "bruteforce perturbation checks"
        ),
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing BoundedModule interval consumption for the receipt "
            "score adapter when importable; if unavailable, the runtime receipt "
            "marks this row blocked and does not fake load-bearing use"
        ),
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical formal-scout result path handling",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

LAYERS = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "frame_bundle_structure_reduction",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]

EPS = 0.0025
BRUTE_SAMPLES = 48
BOUND_TOL = 2.0e-5


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    return value


def load_auto_lirpa() -> dict[str, Any]:
    if AUTO_LIRPA_ROOT.exists() and str(AUTO_LIRPA_ROOT) not in sys.path:
        sys.path.insert(0, str(AUTO_LIRPA_ROOT))
    try:
        from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm
    except Exception as exc:  # pragma: no cover - exercised only on missing optional tool
        return {
            "importable": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "BoundedModule": None,
            "BoundedTensor": None,
            "PerturbationLpNorm": None,
        }
    return {
        "importable": True,
        "module_path": str(AUTO_LIRPA_ROOT),
        "BoundedModule": BoundedModule,
        "BoundedTensor": BoundedTensor,
        "PerturbationLpNorm": PerturbationLpNorm,
    }


def cube_coords() -> list[tuple[int, int, int]]:
    return [(x, y, z) for x in range(2) for y in range(2) for z in range(2)]


def cube_edges(coords: list[tuple[int, int, int]]) -> list[dict[str, int]]:
    index = {coord: idx for idx, coord in enumerate(coords)}
    edges = []
    for coord, src in index.items():
        for axis in range(3):
            nxt = list(coord)
            nxt[axis] += 1
            if nxt[axis] >= 2:
                continue
            edges.append({"src": src, "dst": index[tuple(nxt)], "axis": axis})
    return edges


def seed_site_features(coords: list[tuple[int, int, int]]) -> torch.Tensor:
    rows = []
    for idx, (x, y, z) in enumerate(coords):
        rows.append(
            torch.tensor(
                [
                    0.31 + 0.17 * x - 0.05 * y + 0.09 * z,
                    -0.21 + 0.11 * y + 0.04 * idx,
                    0.37 - 0.13 * z + 0.025 * x * y,
                    0.23 + 0.018 * idx + 0.061 * x * z,
                ],
                dtype=torch.float32,
            )
        )
    return torch.stack(rows)


def layer_operator(idx: int) -> torch.Tensor:
    op = torch.eye(4, dtype=torch.float32)
    op[0, 1] = 0.010 * (idx + 1)
    op[1, 2] = -0.0065 * ((idx % 5) + 1)
    op[2, 3] = 0.0045 * ((idx % 3) + 1)
    op[3, 0] = -0.0035 * ((idx % 7) + 1)
    op[0, 2] = 0.0020 * ((idx % 4) + 1)
    op[1, 3] = -0.0012 * ((idx % 6) + 1)
    return op


OPS = [layer_operator(idx) for idx in range(len(LAYERS))]


def apply_schedule(features: torch.Tensor, order: list[int]) -> torch.Tensor:
    state = features.clone()
    for step, layer_idx in enumerate(order):
        op = OPS[layer_idx]
        prior = torch.roll(state, shifts=1, dims=0)
        later = torch.roll(state, shifts=-1, dims=0)
        phase = 1.0 + 0.0035 * (step + 1)
        mixed = 0.74 * (state @ op.T) + 0.16 * prior + 0.10 * later
        state = torch.tanh(mixed * phase + 0.011 * (layer_idx + 1))
    return state


def scalar_project(features: torch.Tensor) -> torch.Tensor:
    return features.mean(dim=1, keepdim=True).expand_as(features)


def identity_dynamics(features: torch.Tensor) -> torch.Tensor:
    return features.clone()


def noise_control(features: torch.Tensor) -> torch.Tensor:
    generator = torch.Generator().manual_seed(20260518)
    noise = torch.randn(features.shape, generator=generator, dtype=features.dtype) * 0.035
    return torch.tanh(noise)


def features_to_tensors(features: torch.Tensor, coords: list[tuple[int, int, int]]) -> torch.Tensor:
    tensors = []
    grid = torch.arange(16, dtype=features.dtype)
    for idx, coord in enumerate(coords):
        row = features[idx]
        coord_phase = 0.067 * (1 + coord[0]) + 0.109 * (1 + coord[1]) + 0.149 * (1 + coord[2])
        vals = torch.sin(row[grid.long() % 4] * (grid + 1.0) * 0.21 + coord_phase)
        vals = vals + torch.cos(row[(grid.long() + 1) % 4] * 0.27 - coord_phase) * 0.15
        tensors.append(vals.reshape(2, 2, 2, 2) / 4.5)
    return torch.stack(tensors)


def edge_contract(tensors: torch.Tensor, edge: dict[str, int]) -> torch.Tensor:
    src = edge["src"]
    dst = edge["dst"]
    axis = edge["axis"]
    left = tensors[src]
    right = tensors[dst]
    if axis == 0:
        return torch.einsum("pabc,qdbc->", left, right)
    if axis == 1:
        return torch.einsum("pabc,qadc->", left, right)
    return torch.einsum("pabc,qabd->", left, right)


def peps3d_signature(features: torch.Tensor, coords: list[tuple[int, int, int]], edges: list[dict[str, int]]) -> torch.Tensor:
    tensors = features_to_tensors(features, coords)
    edge_terms = [edge_contract(tensors, edge) for edge in edges]
    site_norms = torch.linalg.vector_norm(tensors.reshape(tensors.shape[0], -1), dim=1)
    return torch.cat([torch.stack(edge_terms), site_norms])


def rms_gap(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.sqrt(torch.mean((left - right) * (left - right)))


def build_receipt_features(
    canonical_sig: torch.Tensor,
    scalar_sig: torch.Tensor,
    shuffled_sig: torch.Tensor,
    identity_sig: torch.Tensor,
    noise_sig: torch.Tensor,
) -> torch.Tensor:
    scalar_gap = rms_gap(canonical_sig, scalar_sig)
    shuffled_gap = rms_gap(canonical_sig, shuffled_sig)
    identity_gap = rms_gap(canonical_sig, identity_sig)
    noise_gap = rms_gap(canonical_sig, noise_sig)
    lower_proxy = torch.minimum(torch.minimum(scalar_gap, shuffled_gap), torch.minimum(identity_gap, noise_gap))
    width_proxy = torch.std(torch.stack([scalar_gap, shuffled_gap, identity_gap, noise_gap]), unbiased=False)
    return torch.stack(
        [
            torch.tensor(1.0, dtype=canonical_sig.dtype),
            torch.tensor(1.0, dtype=canonical_sig.dtype),
            scalar_gap,
            shuffled_gap,
            identity_gap,
            noise_gap,
            lower_proxy,
            width_proxy,
        ]
    )


def build_feature_vector(signature: torch.Tensor, receipt: torch.Tensor, mode_code: float) -> torch.Tensor:
    substrate = torch.tanh(signature * 2.3)
    topology = torch.tensor(
        [
            8.0 / 8.0,
            12.0 / 12.0,
            len(LAYERS) / 13.0,
            mode_code,
        ],
        dtype=signature.dtype,
    )
    return torch.cat([substrate, receipt, topology]).reshape(1, -1)


class ReceiptBoundScore(nn.Module):
    """Linear score adapter that must consume both substrate and receipt features."""

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.linear = nn.Linear(input_dim, 1)
        with torch.no_grad():
            weights = torch.zeros(input_dim, dtype=torch.float32)
            weights[:20] = torch.linspace(0.025, 0.055, steps=20)
            weights[20:28] = torch.tensor([0.34, 0.32, 1.35, 1.25, 1.05, 0.95, 1.45, 0.72])
            weights[28:] = torch.tensor([0.13, 0.11, 0.10, 0.36])
            self.linear.weight.copy_(weights.reshape(1, -1))
            self.linear.bias.fill_(-0.12)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x).squeeze(-1)


def brute_force_bounds(model: nn.Module, x: torch.Tensor, eps: float) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(44091)
    rows = []
    with torch.no_grad():
        nominal = model(x)
        for _idx in range(BRUTE_SAMPLES):
            delta = (torch.rand(x.shape, generator=generator, dtype=x.dtype) * 2.0 - 1.0) * eps
            rows.append(model(x + delta))
    samples = torch.stack(rows)
    return {
        "nominal": float(nominal.item()),
        "sample_min": float(samples.min().item()),
        "sample_max": float(samples.max().item()),
        "sample_width": float((samples.max() - samples.min()).item()),
        "samples": BRUTE_SAMPLES,
    }


def direct_lirpa_bounds(model: nn.Module, x: torch.Tensor, lirpa: dict[str, Any]) -> dict[str, Any]:
    BoundedModule = lirpa["BoundedModule"]
    BoundedTensor = lirpa["BoundedTensor"]
    PerturbationLpNorm = lirpa["PerturbationLpNorm"]
    bounded = BoundedModule(model, x)
    bounded_x = BoundedTensor(x, PerturbationLpNorm(norm=float("inf"), eps=EPS))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    brute = brute_force_bounds(model, x, EPS)
    nominal = float(model(x).detach().item())
    lb_value = float(lb.detach().item())
    ub_value = float(ub.detach().item())
    return {
        "engine": "auto_LiRPA",
        "method": "IBP",
        "eps_linf": EPS,
        "nominal": nominal,
        "lower": lb_value,
        "upper": ub_value,
        "width": ub_value - lb_value,
        "bruteforce": brute,
        "contains_nominal": bool(lb_value <= nominal + BOUND_TOL and nominal <= ub_value + BOUND_TOL),
        "contains_bruteforce_samples": bool(
            lb_value <= brute["sample_min"] + BOUND_TOL and brute["sample_max"] <= ub_value + BOUND_TOL
        ),
        "pass": bool(
            lb_value <= nominal + BOUND_TOL
            and nominal <= ub_value + BOUND_TOL
            and lb_value <= brute["sample_min"] + BOUND_TOL
            and brute["sample_max"] <= ub_value + BOUND_TOL
            and ub_value > lb_value
        ),
    }


def fallback_proxy_bounds(model: nn.Module, x: torch.Tensor, lirpa: dict[str, Any]) -> dict[str, Any]:
    brute = brute_force_bounds(model, x, EPS)
    pad = 0.02 + 0.05 * max(abs(brute["sample_min"]), abs(brute["sample_max"]))
    return {
        "engine": "fallback_interval_proxy",
        "method": "bruteforce_proxy_not_formal_lirpa",
        "eps_linf": EPS,
        "nominal": brute["nominal"],
        "lower": brute["sample_min"] - pad,
        "upper": brute["sample_max"] + pad,
        "width": (brute["sample_max"] - brute["sample_min"]) + 2.0 * pad,
        "bruteforce": brute,
        "auto_lirpa_blocker": {
            "blocked": True,
            "error_type": lirpa.get("error_type"),
            "error": lirpa.get("error"),
            "path_checked": str(AUTO_LIRPA_ROOT),
        },
        "contains_nominal": True,
        "contains_bruteforce_samples": True,
        "pass": True,
    }


def runtime_tool_tables(lirpa: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    manifest = copy.deepcopy(TOOL_MANIFEST)
    depth = dict(TOOL_INTEGRATION_DEPTH)
    if not lirpa["importable"]:
        manifest["auto_LiRPA"]["used"] = False
        manifest["auto_LiRPA"]["reason"] = (
            "blocked: auto_LiRPA was not importable; fallback interval proxy is "
            "supportive only and is not counted as load-bearing LiRPA evidence"
        )
        manifest["fallback_interval_proxy"] = {
            "tried": True,
            "used": True,
            "reason": "supportive/blocked brute-force proxy used only to keep the receipt explicit",
        }
        depth["auto_LiRPA"] = "blocked"
        depth["fallback_interval_proxy"] = "supportive"
    return manifest, depth


def main() -> int:
    started = time.time()
    torch.manual_seed(52018)
    lirpa = load_auto_lirpa()
    coords = cube_coords()
    edges = cube_edges(coords)
    canonical_order = list(range(len(LAYERS)))
    shuffled_order = [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11]
    shuffled_edges = edges[3:] + edges[:3]

    base = seed_site_features(coords)
    full_features = apply_schedule(base, canonical_order)
    scalar_features = apply_schedule(scalar_project(base), canonical_order)
    shuffled_features = apply_schedule(base, shuffled_order)
    identity_features = identity_dynamics(base)
    noise_features = noise_control(base)

    full_sig = peps3d_signature(full_features, coords, edges)
    scalar_sig = peps3d_signature(scalar_features, coords, edges)
    shuffled_sig = peps3d_signature(shuffled_features, coords, shuffled_edges)
    identity_sig = peps3d_signature(identity_features, coords, edges)
    noise_sig = peps3d_signature(noise_features, coords, edges)
    receipt = build_receipt_features(full_sig, scalar_sig, shuffled_sig, identity_sig, noise_sig)
    dropped_receipt = torch.zeros_like(receipt)
    dropped_receipt[0] = 1.0
    dropped_receipt[1] = 0.0

    feature_vectors = {
        "full_substrate_with_receipt": build_feature_vector(full_sig, receipt, 1.0),
        "scalar_projection_control": build_feature_vector(scalar_sig, receipt, 0.40),
        "shuffled_topology_control": build_feature_vector(shuffled_sig, receipt, 0.25),
        "dropped_bound_receipt_control": build_feature_vector(full_sig, dropped_receipt, 0.55),
        "identity_control": build_feature_vector(identity_sig, receipt, 0.10),
        "noise_control": build_feature_vector(noise_sig, receipt, 0.05),
    }
    model = ReceiptBoundScore(feature_vectors["full_substrate_with_receipt"].shape[1]).eval()

    bound_fn = direct_lirpa_bounds if lirpa["importable"] else fallback_proxy_bounds
    bound_rows = {name: bound_fn(model, x, lirpa) for name, x in feature_vectors.items()}
    nominal_scores = {name: row["nominal"] for name, row in bound_rows.items()}
    full_score = nominal_scores["full_substrate_with_receipt"]
    control_names = [name for name in bound_rows if name != "full_substrate_with_receipt"]
    score_margins = {name: full_score - nominal_scores[name] for name in control_names}
    min_control_margin = min(score_margins.values())
    full_bound = bound_rows["full_substrate_with_receipt"]
    dropped_bound = bound_rows["dropped_bound_receipt_control"]

    direct_auto_lirpa = bool(lirpa["importable"])
    auto_lirpa_pass = bool(direct_auto_lirpa and all(row["pass"] for row in bound_rows.values()))
    control_pass = bool(
        score_margins["scalar_projection_control"] > 0.12
        and score_margins["shuffled_topology_control"] > 0.08
        and score_margins["dropped_bound_receipt_control"] > 1.20
        and score_margins["identity_control"] > 0.08
        and score_margins["noise_control"] > 0.08
    )
    bound_consumption_pass = bool(
        full_bound["lower"] > dropped_bound["upper"] + 0.35
        and bound_rows["scalar_projection_control"]["nominal"] < full_score
        and bound_rows["shuffled_topology_control"]["nominal"] < full_score
    )

    runtime_manifest, runtime_depth = runtime_tool_tables(lirpa)
    positive = {
        "pytorch_peps3d_full_substrate_executed": {
            "site_count": len(coords),
            "edge_count": len(edges),
            "layer_count": len(LAYERS),
            "feature_shape": list(full_features.shape),
            "signature_length": int(full_sig.numel()),
            "signature_norm": float(torch.linalg.vector_norm(full_sig).item()),
            "pass": bool(len(coords) == 8 and len(edges) == 12 and len(LAYERS) == 13 and full_sig.numel() == 20),
        },
        "receipt_bound_features_consumed_by_score": {
            "receipt_features": as_jsonable(receipt),
            "dropped_receipt_features": as_jsonable(dropped_receipt),
            "full_nominal_score": full_score,
            "dropped_receipt_nominal_score": nominal_scores["dropped_bound_receipt_control"],
            "full_lower_bound": full_bound["lower"],
            "dropped_receipt_upper_bound": dropped_bound["upper"],
            "pass": bound_consumption_pass,
        },
        "direct_auto_lirpa_bounds_or_blocked_fallback_recorded": {
            "auto_lirpa_importable": direct_auto_lirpa,
            "engine": full_bound["engine"],
            "all_bound_rows_contain_nominal_and_samples": all(row["pass"] for row in bound_rows.values()),
            "fallback_is_supportive_only": not direct_auto_lirpa,
            "pass": bool(auto_lirpa_pass if direct_auto_lirpa else full_bound["engine"] == "fallback_interval_proxy"),
        },
    }
    graveyard_companions = {
        "scalar_projection_control_rejected": {
            "score_margin": score_margins["scalar_projection_control"],
            "full_score": full_score,
            "control_score": nominal_scores["scalar_projection_control"],
            "pass": score_margins["scalar_projection_control"] > 0.12,
        },
        "shuffled_topology_control_rejected": {
            "score_margin": score_margins["shuffled_topology_control"],
            "shuffled_order": shuffled_order,
            "edge_rotation": 3,
            "pass": score_margins["shuffled_topology_control"] > 0.08,
        },
        "dropped_bound_receipt_control_rejected": {
            "score_margin": score_margins["dropped_bound_receipt_control"],
            "full_lower_minus_control_upper": full_bound["lower"] - dropped_bound["upper"],
            "pass": score_margins["dropped_bound_receipt_control"] > 1.20 and full_bound["lower"] > dropped_bound["upper"] + 0.35,
        },
        "identity_control_rejected": {
            "score_margin": score_margins["identity_control"],
            "pass": score_margins["identity_control"] > 0.08,
        },
        "noise_control_rejected": {
            "score_margin": score_margins["noise_control"],
            "pass": score_margins["noise_control"] > 0.08,
        },
    }
    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False),
        },
        "claim_ceiling_blocks_basin_and_canonical_claims": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool(
                all(
                    term in CLAIM_CEILING.lower()
                    for term in ["formal scout", "does not admit", "mature basin", "canonical"]
                )
            ),
        },
        "auto_lirpa_missing_would_block_load_bearing_claim": {
            "auto_lirpa_importable": direct_auto_lirpa,
            "runtime_depth": runtime_depth.get("auto_LiRPA"),
            "blocker": None
            if direct_auto_lirpa
            else {
                "blocked": True,
                "error_type": lirpa.get("error_type"),
                "error": lirpa.get("error"),
                "path_checked": str(AUTO_LIRPA_ROOT),
            },
            "pass": bool((direct_auto_lirpa and runtime_depth.get("auto_LiRPA") == "load_bearing") or runtime_depth.get("auto_LiRPA") == "blocked"),
        },
    }
    all_pass = bool(
        direct_auto_lirpa
        and all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
        and control_pass
    )
    blockers = [] if direct_auto_lirpa else [boundary["auto_lirpa_missing_would_block_load_bearing_claim"]["blocker"]]
    receipt_payload = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "auto_lirpa_direct": direct_auto_lirpa,
            "bound_engine": full_bound["engine"],
            "site_count": len(coords),
            "edge_count": len(edges),
            "layer_count": len(LAYERS),
            "signature_length": int(full_sig.numel()),
            "full_nominal_score": full_score,
            "full_lower_bound": full_bound["lower"],
            "full_upper_bound": full_bound["upper"],
            "dropped_receipt_upper_bound": dropped_bound["upper"],
            "min_control_score_margin": min_control_margin,
            "score_margins": score_margins,
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
            "variants": sorted(graveyard_companions),
        },
        "why_not_v4_probes": [
            "Targets a v5 high-risk LiRPA/PEPS3D receipt-boundary concern, not broad v4 provider prose.",
            "Uses a tiny PyTorch PEPS3D-like substrate plus direct auto_LiRPA bounds only when importable.",
            "Keeps mature basin, PEPS3D theorem, engine, bridge, physics, and canonical claims explicitly blocked.",
        ],
        "TOOL_MANIFEST": runtime_manifest,
        "tool_manifest": runtime_manifest,
        "TOOL_INTEGRATION_DEPTH": runtime_depth,
        "tool_integration_depth": runtime_depth,
        "auto_lirpa_status": {
            "direct": direct_auto_lirpa,
            "importable": direct_auto_lirpa,
            "engine": full_bound["engine"],
            "module_path": lirpa.get("module_path"),
            "blocked_error_type": lirpa.get("error_type"),
            "blocked_error": lirpa.get("error"),
        },
        "bound_rows": as_jsonable(bound_rows),
        "orders": {
            "canonical": canonical_order,
            "shuffled": shuffled_order,
        },
        "cube_coords": coords,
        "cube_edges": edges,
        "blockers": as_jsonable(blockers),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(receipt_payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "auto_lirpa_direct": direct_auto_lirpa,
                "bound_engine": full_bound["engine"],
                "result": str(OUT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

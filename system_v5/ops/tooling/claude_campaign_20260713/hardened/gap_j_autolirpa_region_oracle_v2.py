#!/usr/bin/env python3
"""Hardened Gap J: fixed-network CROWN bounds vs exhaustive region LP.

This is a finite numerical audit of one frozen 2-4-1 ReLU network and one box.
It deliberately does not call a 20-sample check a soundness proof.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import auto_LiRPA
import numpy as np
import scipy
import torch
import torch.nn as nn
from auto_LiRPA import BoundedModule, BoundedTensor
from auto_LiRPA.perturbations import PerturbationLpNorm
from scipy.optimize import linprog


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "results" / "gap_j_autolirpa_region_oracle_v2_results.json"
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
AUTO_LIRPA_REPO = Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
EXPECTED_AUTO_LIRPA_HEAD = "ca767f1d8c0a6b125a292ba165adb2319bbaf615"
TOLERANCE = 2e-7


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(AUTO_LIRPA_REPO), *args],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout.strip()


def frozen_network() -> nn.Sequential:
    torch.manual_seed(0)
    return nn.Sequential(nn.Linear(2, 4), nn.ReLU(), nn.Linear(4, 1)).eval()


def model_digest(net: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(net.state_dict().items()):
        values = tensor.detach().cpu().contiguous().numpy()
        digest.update(name.encode())
        digest.update(str(values.shape).encode())
        digest.update(str(values.dtype).encode())
        digest.update(values.tobytes())
    return digest.hexdigest()


def lirpa_bounds(bounded: BoundedModule, center: torch.Tensor, epsilon: float, method: str) -> tuple[float, float]:
    perturbation = PerturbationLpNorm(norm=float("inf"), eps=epsilon)
    value = BoundedTensor(center, perturbation)
    lower, upper = bounded.compute_bounds(x=(value,), method=method)
    return float(lower.item()), float(upper.item())


def region_oracle(net: nn.Sequential, center: torch.Tensor, epsilon: float) -> dict[str, Any]:
    first: nn.Linear = net[0]
    last: nn.Linear = net[2]
    w1 = first.weight.detach().double().numpy()
    b1 = first.bias.detach().double().numpy()
    w2 = last.weight.detach().double().numpy()[0]
    b2 = float(last.bias.detach().double().numpy()[0])
    center_np = center.detach().double().numpy()[0]
    lower_box = center_np - epsilon
    upper_box = center_np + epsilon

    feasible: list[dict[str, Any]] = []
    global_min = float("inf")
    global_max = -float("inf")
    min_point: list[float] | None = None
    max_point: list[float] | None = None
    min_mask: str | None = None
    max_mask: str | None = None
    for bits in itertools.product((0, 1), repeat=4):
        mask = np.asarray(bits, dtype=np.float64)
        inequalities: list[np.ndarray] = []
        limits: list[float] = []
        for active, row, bias in zip(mask, w1, b1, strict=True):
            if active:
                inequalities.append(-row)
                limits.append(float(bias))
            else:
                inequalities.append(row)
                limits.append(float(-bias))
        objective = (w2 * mask) @ w1
        offset = float((w2 * mask) @ b1 + b2)
        common = {
            "A_ub": np.asarray(inequalities),
            "b_ub": np.asarray(limits),
            "bounds": list(zip(lower_box, upper_box, strict=True)),
            "method": "highs",
        }
        minimum = linprog(objective, **common)
        maximum = linprog(-objective, **common)
        if not minimum.success and not maximum.success:
            continue
        if minimum.success != maximum.success:
            raise RuntimeError(f"inconsistent feasibility for activation mask {bits}")
        low_value = float(minimum.fun + offset)
        high_value = float(-maximum.fun + offset)
        key = "".join(str(bit) for bit in bits)
        feasible.append({
            "mask": key,
            "minimum": low_value,
            "maximum": high_value,
            "minimum_point": minimum.x.tolist(),
            "maximum_point": maximum.x.tolist(),
        })
        if low_value < global_min:
            global_min = low_value
            min_point = minimum.x.tolist()
            min_mask = key
        if high_value > global_max:
            global_max = high_value
            max_point = maximum.x.tolist()
            max_mask = key
    if min_point is None or max_point is None:
        raise RuntimeError("no feasible ReLU activation region")
    return {
        "epsilon": epsilon,
        "patterns_enumerated": 16,
        "feasible_pattern_count": len(feasible),
        "minimum": global_min,
        "minimum_point": min_point,
        "minimum_mask": min_mask,
        "maximum": global_max,
        "maximum_point": max_point,
        "maximum_mask": max_mask,
        "regions": feasible,
    }


def contains(bounds: tuple[float, float], oracle: dict[str, Any], tolerance: float = TOLERANCE) -> bool:
    return bounds[0] <= oracle["minimum"] + tolerance and bounds[1] >= oracle["maximum"] - tolerance


def direct_value(net: nn.Module, point: list[float]) -> float:
    with torch.no_grad():
        return float(net(torch.tensor([point], dtype=torch.float32)).item())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if Path(sys.executable).resolve() != Path(PYTHON).resolve():
        raise RuntimeError(f"wrong Python runtime: {sys.executable}")

    auto_head = git_value("rev-parse", "HEAD")
    auto_status = git_value("status", "--short")
    net = frozen_network()
    center = torch.tensor([[0.3, -0.2]], dtype=torch.float32)
    bounded = BoundedModule(net, torch.zeros_like(center))

    primary_epsilon = 0.5
    shrink_epsilon = 0.25
    zero_epsilon = 0.0
    crown = lirpa_bounds(bounded, center, primary_epsilon, "CROWN")
    ibp = lirpa_bounds(bounded, center, primary_epsilon, "IBP")
    crown_shrink = lirpa_bounds(bounded, center, shrink_epsilon, "CROWN")
    crown_zero = lirpa_bounds(bounded, center, zero_epsilon, "CROWN")
    oracle = region_oracle(net, center, primary_epsilon)
    oracle_shrink = region_oracle(net, center, shrink_epsilon)
    oracle_zero = region_oracle(net, center, zero_epsilon)

    minimum_direct = direct_value(net, oracle["minimum_point"])
    maximum_direct = direct_value(net, oracle["maximum_point"])
    center_direct = direct_value(net, center[0].tolist())
    forged_lower = (oracle["minimum"] + 1e-4, crown[1])
    forged_upper = (crown[0], oracle["maximum"] - 1e-4)

    checks = {
        "canonical_runtime_imports_editable_auto_lirpa": Path(auto_LiRPA.__file__).resolve().is_relative_to(AUTO_LIRPA_REPO),
        "auto_lirpa_source_is_clean_pinned_commit": auto_head == EXPECTED_AUTO_LIRPA_HEAD and auto_status == "",
        "all_relu_patterns_enumerated": oracle["patterns_enumerated"] == 16 and oracle["feasible_pattern_count"] > 0,
        "crown_encloses_exhaustive_region_lp_extrema": contains(crown, oracle),
        "ibp_encloses_exhaustive_region_lp_extrema": contains(ibp, oracle),
        "oracle_extrema_match_direct_network_evaluation": abs(minimum_direct - oracle["minimum"]) < 2e-6 and abs(maximum_direct - oracle["maximum"]) < 2e-6,
        "shrunk_crown_encloses_shrunk_oracle": contains(crown_shrink, oracle_shrink),
        "shrink_is_nested_and_strict": crown_shrink[0] >= crown[0] - TOLERANCE and crown_shrink[1] <= crown[1] + TOLERANCE and (crown_shrink[0] > crown[0] + TOLERANCE or crown_shrink[1] < crown[1] - TOLERANCE),
        "zero_box_crown_matches_direct_center": abs(crown_zero[0] - center_direct) < 2e-6 and abs(crown_zero[1] - center_direct) < 2e-6,
        "zero_box_oracle_matches_direct_center": abs(oracle_zero["minimum"] - center_direct) < 2e-6 and abs(oracle_zero["maximum"] - center_direct) < 2e-6,
        "forged_inward_lower_bound_is_rejected": not contains(forged_lower, oracle),
        "forged_inward_upper_bound_is_rejected": not contains(forged_upper, oracle),
    }
    all_pass = all(checks.values())
    source_path = Path(__file__).resolve()
    command = [PYTHON, str(source_path), "--output", str(args.output.resolve())]
    result = {
        "schema": "codex-ratchet.gap-j-autolirpa-region-oracle-result.v2",
        "sim_id": "gap_j_fixed_relu_crown_region_oracle",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "runner_identity": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "torch_version": torch.__version__,
            "scipy_version": scipy.__version__,
            "auto_lirpa_version": getattr(auto_LiRPA, "__version__", None),
            "auto_lirpa_module_file": auto_LiRPA.__file__,
            "auto_lirpa_repo_head": auto_head,
            "auto_lirpa_repo_clean": auto_status == "",
        },
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source": {
            "probe_path": str(source_path),
            "probe_sha256": sha256_file(source_path),
            "network_constructor": "torch.manual_seed(0); Linear(2,4)-ReLU-Linear(4,1)",
            "network_state_sha256": model_digest(net),
            "network_state": {name: value.detach().cpu().tolist() for name, value in net.state_dict().items()},
        },
        "fixed_object": {
            "center": center[0].tolist(),
            "primary_epsilon_linf": primary_epsilon,
            "network": "2-4-1 ReLU",
        },
        "auto_lirpa": {
            "crown_primary": {"lower": crown[0], "upper": crown[1]},
            "ibp_primary": {"lower": ibp[0], "upper": ibp[1]},
            "crown_shrunk": {"lower": crown_shrink[0], "upper": crown_shrink[1]},
            "crown_zero_box": {"lower": crown_zero[0], "upper": crown_zero[1]},
        },
        "independent_region_lp_oracle": {
            "description": "all 16 ReLU activation masks; affine extrema per feasible polytope via scipy.optimize.linprog(method=highs)",
            "primary": oracle,
            "shrunk": oracle_shrink,
            "zero_box": oracle_zero,
            "direct_extrema_values": {"minimum": minimum_direct, "maximum": maximum_direct, "center": center_direct},
        },
        "controls": {
            "forged_inward_lower": {"bounds": list(forged_lower), "accepted": contains(forged_lower, oracle)},
            "forged_inward_upper": {"bounds": list(forged_upper), "accepted": contains(forged_upper, oracle)},
            "shrunken_box": {"epsilon": shrink_epsilon},
            "zero_width_box": {"epsilon": zero_epsilon},
        },
        "checks": checks,
        "all_pass": all_pass,
        "tool_manifest": {
            "auto_LiRPA": "claim_load_bearing for CROWN and IBP candidate outer bounds on this fixed object",
            "scipy.optimize.linprog": "independent exhaustive activation-region numerical oracle",
            "torch": "fixed network definition and direct evaluation",
        },
        "tool_calls": [
            {
                "tool": "auto_LiRPA",
                "api": "BoundedModule.compute_bounds with CROWN and IBP",
                "input": "frozen 2-4-1 ReLU network and L_inf box",
                "output": "candidate output intervals",
                "negative_control": "forged inward lower and upper intervals must be rejected by the independent oracle",
                "gates": ["all_pass"],
            },
            {
                "tool": "scipy",
                "api": "scipy.optimize.linprog(method=highs)",
                "input": "all 16 activation-region affine programs",
                "output": "global finite-box extrema and witnesses",
                "boundary_control": "zero-width box agrees with direct center evaluation",
                "gates": ["all_pass"],
            },
        ],
        "claim_ceiling": (
            "Finite numerical containment evidence for CROWN and IBP on one pinned, fixed-seed "
            "2-4-1 ReLU network and three nested boxes, checked by exhaustive activation-region LP. "
            "This is not a general auto_LiRPA soundness proof and admits no scientific Ratchet claim."
        ),
        "blocked_consumers": ["general verifier soundness", "scientific canon", "Ratchet rung promotion", "Lev graph mutation"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "receipt": str(args.output.resolve()), "failed": [name for name, value in checks.items() if not value]}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

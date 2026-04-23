#!/usr/bin/env python3
"""
sim_torch_ga_capability.py -- Tool-capability isolation sim for torch_ga.
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import torch
import torch_ga


classification = "canonical"
divergence_log = (
    "Capability isolation witness for torch_ga: geometric tensor conversion and "
    "roundtrip stability are exercised here so broader bridge sims can treat "
    "torch_ga as an admitted GA surface instead of a speculative package import."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "supportive tensor carrier for torch_ga capability"},
    "torch_ga": {"tried": True, "used": True, "reason": "capability under test -- geometric tensor roundtrip"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supportive",
    "torch_ga": "load_bearing",
}

WITNESS_INFO = {
    "witness_use_cases": [
        "system_v4/probes/sim_integration_quantum_open_entangle_correlator_mega_stack.py",
        "system_v4/probes/sim_integration_quantum_ga_correlator_stack.py",
        "system_v4/probes/sim_integration_torch_clifford_ga_rotor_bridge.py",
    ]
}


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def run_positive_tests() -> dict[str, dict[str, object]]:
    algebra = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
    to_geo = torch_ga.TensorToGeometric(algebra, [1, 2, 3])
    to_tensor = torch_ga.GeometricToTensor(algebra, [1, 2, 3])
    vec = torch.tensor([[1.0, -2.0, 0.5]], dtype=torch.float32)
    geo = to_geo(vec)
    roundtrip = to_tensor(geo)
    return {
        "roundtrip_preserved": {
            "pass": bool(torch.allclose(roundtrip, vec)),
            "roundtrip": roundtrip.tolist(),
        },
        "blade_width_matches_algebra": {
            "pass": int(geo.shape[-1]) == int(algebra.num_blades),
            "blade_width": int(geo.shape[-1]),
            "num_blades": int(algebra.num_blades),
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    algebra = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
    to_geo = torch_ga.TensorToGeometric(algebra, [1, 2, 3])
    bad = torch.tensor([[1.0, 2.0]], dtype=torch.float32)
    raised = False
    err = None
    try:
        to_geo(bad)
    except Exception as exc:  # pragma: no cover - exercised at runtime
        raised = True
        err = type(exc).__name__
    return {
        "shape_mismatch_raises": {
            "pass": raised,
            "error_type": err,
        }
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    algebra = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
    to_geo = torch_ga.TensorToGeometric(algebra, [1, 2, 3])
    tiny = torch.tensor([[1e-10, -1e-10, 2e-10]], dtype=torch.float32)
    geo = to_geo(tiny)
    return {
        "tiny_tensor_finite": {
            "pass": bool(torch.isfinite(geo).all()),
            "norm": float(torch.linalg.norm(geo)),
        }
    }


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())
    results = {
        "name": "sim_torch_ga_capability",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_ga_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")

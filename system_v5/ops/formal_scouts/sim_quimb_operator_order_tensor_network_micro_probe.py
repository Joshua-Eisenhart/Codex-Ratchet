#!/usr/bin/env python3
"""quimb operator-order tensor-network micro-probe."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "quimb_operator_order_tensor_network_micro_probe_results.json"

NAME = "quimb_operator_order_tensor_network_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: quimb is probed as a tensor-network operator-order surface. "
    "Noncommutation is a bounded receipt, not a promoted manifold, basin, or physics claim."
)
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor controls for the order comparison"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing Pauli operator source"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
}
NEARBY_VARIANTS = {
    "total": 1,
    "passed": 1,
    "variants": ["same_operator_twice_identity_control"],
}
WHY_NOT_V4_PROBES = [
    "This is a v5 formal scout for a tiny quimb operator-order micro fixture.",
    "It records bounded tool behavior only; it does not promote a v4 canonical probe, manifold, basin, or physics claim.",
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        return value.detach().cpu().tolist()
    return value


def blocked_receipt(started: float, blocker: str, detail: str) -> dict[str, Any]:
    return {
        "name": NAME,
        "schema": "formal_scout_result_v1",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": {
            "pytorch": TOOL_MANIFEST["pytorch"],
            "quimb": {"tried": True, "used": False, "reason": blocker},
        },
        "TOOL_MANIFEST": {
            "pytorch": TOOL_MANIFEST["pytorch"],
            "quimb": {"tried": True, "used": False, "reason": blocker},
        },
        "tool_integration_depth": {"pytorch": TOOL_INTEGRATION_DEPTH["pytorch"], "quimb": None},
        "TOOL_INTEGRATION_DEPTH": {"pytorch": TOOL_INTEGRATION_DEPTH["pytorch"], "quimb": None},
        "positive": {},
        "graveyard_companions": {},
        "boundary": {"blocked_before_quimb_operator_execution": {"pass": False, "detail": detail}},
        "nearby_variants": {"total": 0, "passed": 0, "variants": []},
        "why_not_v4_probes": WHY_NOT_V4_PROBES,
        "blockers": [{"kind": blocker, "detail": detail}],
        "elapsed_seconds": time.time() - started,
        "all_pass": False,
    }


def run_probe() -> dict[str, Any]:
    import quimb as qu

    state = torch.tensor([1.0, 0.0], dtype=torch.complex64)
    x_gate = torch.tensor(qu.pauli("X").A.tolist(), dtype=torch.complex64)
    z_gate = torch.tensor(qu.pauli("Z").A.tolist(), dtype=torch.complex64)
    xz = x_gate @ (z_gate @ state)
    zx = z_gate @ (x_gate @ state)
    commutator_gap = torch.linalg.vector_norm(xz - zx)
    xx = x_gate @ (x_gate @ state)
    identity_gap = torch.linalg.vector_norm(xx - state)
    positive = {
        "quimb_pauli_operator_surface_imports": {
            "pass": bool(x_gate.shape == (2, 2) and z_gate.shape == (2, 2)),
            "quimb_version": getattr(qu, "__version__", "unknown"),
        },
        "operator_order_noncommutation_observed": {
            "pass": bool(commutator_gap.item() > 1.0),
            "xz_zx_l2": float(commutator_gap.real.item()),
        },
    }
    graveyard = {
        "same_operator_twice_identity_control": {
            "pass": bool(identity_gap.item() < 1.0e-6),
            "xx_identity_l2": float(identity_gap.real.item()),
        }
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": {"operator_count": 2, "root_constraint_wording": "not promoted beyond micro operator-order receipt"},
        "blockers": [],
        "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()),
    }


def main() -> int:
    started = time.time()
    try:
        body = run_probe()
        result = {
            "name": NAME,
            "schema": "formal_scout_result_v1",
            "classification": CLASSIFICATION,
            "sim_execution_kind": SIM_EXECUTION_KIND,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "tool_manifest": TOOL_MANIFEST,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "nearby_variants": NEARBY_VARIANTS,
            "why_not_v4_probes": WHY_NOT_V4_PROBES,
            "elapsed_seconds": time.time() - started,
            **body,
        }
    except ImportError as exc:
        result = blocked_receipt(started, "missing_import", f"quimb import failed: {exc}")
    except Exception as exc:
        result = blocked_receipt(started, "runtime_error", f"quimb micro probe failed: {type(exc).__name__}: {exc}")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

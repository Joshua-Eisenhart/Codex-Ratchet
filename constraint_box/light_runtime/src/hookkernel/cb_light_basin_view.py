"""Stdlib-only current BasinView reader for the Light gate.

Does not import src/constraintbox. Reads the gap-plan JSON the map campaign
already writes. Missing/SPLIT/UNMAPPED → HOLD_BASIN_FIELD_INCOMPLETE.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

HOLD = "HOLD_BASIN_FIELD_INCOMPLETE"
DEFAULT_OPERATION = "tool_matrix"


def require_enabled() -> bool:
    raw = os.environ.get("CB_REQUIRE_BASIN_VIEW", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def default_plan_path() -> Path:
    env = os.environ.get("CB_BASIN_VIEW_PLAN")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "receipts" / "box" / "probe_field" / "gap_plan.json"
        if cand.is_file():
            return cand
    return here.parents[1] / "receipts" / "box" / "probe_field" / "gap_plan.json"


def read_current_view(
    operation: str = DEFAULT_OPERATION,
    *,
    plan_path: Path | None = None,
) -> dict[str, Any]:
    path = plan_path or default_plan_path()
    if not path.is_file():
        return {
            "operation": operation,
            "status": "UNMAPPED",
            "reason": "gap_plan_missing",
            "ok": False,
            "reason_code": HOLD,
            "path": str(path),
        }
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "operation": operation,
            "status": "UNMAPPED",
            "reason": type(exc).__name__,
            "ok": False,
            "reason_code": HOLD,
            "path": str(path),
        }
    sources = body.get("sources") if isinstance(body.get("sources"), dict) else {}
    for path_key, sha_key in (("field_jsonl", "field_sha256"), ("tool_matrix", "tool_matrix_sha256")):
        raw_path = sources.get(path_key)
        expected = sources.get(sha_key)
        if not raw_path or not expected:
            continue
        src = Path(str(raw_path))
        if not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest() != expected:
            return {
                "operation": operation,
                "status": "UNMAPPED",
                "reason": f"stale_{path_key}",
                "ok": False,
                "reason_code": HOLD,
                "path": str(path),
            }
    for leg in body.get("legs") or []:
        if not isinstance(leg, dict) or leg.get("operation") != operation:
            continue
        raw = leg.get("projection")
        proj = raw if isinstance(raw, dict) else {}
        status = proj.get("status")
        return {
            "operation": operation,
            "status": status,
            "reason": proj.get("reason"),
            "ok": status == "BASIN",
            "reason_code": "ADMIT_CURRENT_BASIN_VIEW" if status == "BASIN" else HOLD,
            "path": str(path),
        }
    return {
        "operation": operation,
        "status": "UNMAPPED",
        "reason": "operation_absent",
        "ok": False,
        "reason_code": HOLD,
        "path": str(path),
    }


def apply_view_hold(body: dict[str, Any], view: dict[str, Any], *, require: bool | None = None) -> dict[str, Any]:
    """Attach the view. If required and not BASIN, override disposition."""
    out = dict(body)
    out["basin_view"] = view
    must = require_enabled() if require is None else require
    if must and not view.get("ok"):
        out["disposition"] = "HOLD"
        out["reason_code"] = HOLD
        out["claim_ceiling"] = (
            "Light select force-uses current BasinView; "
            "missing/split/unmapped field is HOLD, not admission"
        )
    return out


def hold_result_if_incomplete(*, operation: str = DEFAULT_OPERATION) -> dict[str, Any] | None:
    """Pre-DB/pre-write HOLD payload, or None if the current view is usable."""
    view = read_current_view(operation)
    if not require_enabled() or view.get("ok"):
        return None
    return {
        "disposition": "HOLD",
        "reason_code": HOLD,
        "detail": str(view.get("reason") or HOLD),
        "basin_view": view,
        "promotion_allowed": False,
    }

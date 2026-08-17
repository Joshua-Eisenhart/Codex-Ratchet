"""Side-effect valve: spawn/write only if the current BasinView is BASIN.

Complements the map kernel. Does not admit tools, promote, or spawn LLMs.
Missing / stale / SPLIT / UNMAPPED / DESTROYED → HOLD_BASIN_FIELD_INCOMPLETE.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

CLAIM = (
    "force-use of a current operation-specific BasinView; "
    "not global admission, not promotion, not hook-live proof"
)
HOLD = "HOLD_BASIN_FIELD_INCOMPLETE"
DEFAULT_PLAN = (
    Path(__file__).resolve().parents[2] / "receipts" / "box" / "probe_field" / "gap_plan.json"
)


class BasinViewHold(Exception):
    def __init__(self, reason_code: str, detail: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail
        self.payload = payload or {}


def _require_enabled() -> bool:
    raw = os.environ.get("CB_REQUIRE_BASIN_VIEW", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def load_gap_plan(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_PLAN
    if not p.is_file():
        raise BasinViewHold(HOLD, f"gap plan missing: {p}", {"path": str(p)})
    body = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(body, dict) or not isinstance(body.get("legs"), list):
        raise BasinViewHold(HOLD, "gap plan has no legs", {"path": str(p)})
    return body


def assert_plan_current(plan: dict[str, Any]) -> None:
    """HOLD if stamped source bytes no longer match (stale view)."""
    sources = plan.get("sources")
    if not isinstance(sources, dict) or not sources:
        return
    pairs = (
        ("field_jsonl", "field_sha256"),
        ("tool_matrix", "tool_matrix_sha256"),
    )
    for path_key, sha_key in pairs:
        raw_path = sources.get(path_key)
        expected = sources.get(sha_key)
        if not raw_path or not expected:
            continue
        path = Path(str(raw_path))
        if not path.is_file():
            raise BasinViewHold(HOLD, f"stale: missing {path_key} {path}")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != expected:
            raise BasinViewHold(HOLD, f"stale: {path_key} sha mismatch")
    source_files = sources.get("source_files")
    if not isinstance(source_files, dict) or not source_files:
        raise BasinViewHold(HOLD, "stale: source_files binding missing")
    for raw_path, expected in sorted(source_files.items()):
        path = Path(str(raw_path))
        if not path.is_file():
            raise BasinViewHold(HOLD, f"stale: missing source file {path}")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != expected:
            raise BasinViewHold(HOLD, f"stale: source file sha mismatch {path}")


def current_view(operation: str, *, plan: dict[str, Any] | None = None) -> dict[str, Any]:
    body = plan if plan is not None else load_gap_plan()
    for leg in body.get("legs") or []:
        if isinstance(leg, dict) and leg.get("operation") == operation:
            raw_proj = leg.get("projection")
            proj = raw_proj if isinstance(raw_proj, dict) else {}
            return {
                "operation": operation,
                "status": proj.get("status"),
                "reason": proj.get("reason"),
                "n_in": leg.get("n_in"),
                "in_components": leg.get("in_components"),
                "promotion_allowed": False,
                "claim_ceiling": CLAIM,
            }
    raise BasinViewHold(HOLD, f"no BasinView for operation {operation!r}")


def require_basin_view(
    operation: str,
    *,
    plan_path: Path | None = None,
    require: bool | None = None,
) -> dict[str, Any]:
    """Fail closed unless the named operation currently projects BASIN."""
    must = _require_enabled() if require is None else require
    try:
        plan = load_gap_plan(plan_path)
        assert_plan_current(plan)
        view = current_view(operation, plan=plan)
    except BasinViewHold:
        if must:
            raise
        return {
            "ok": False,
            "required": must,
            "reason_code": HOLD,
            "operation": operation,
            "promotion_allowed": False,
            "claim_ceiling": CLAIM,
        }
    if view.get("status") != "BASIN":
        if must:
            raise BasinViewHold(
                HOLD,
                f"{operation} status is {view.get('status')!r} ({view.get('reason')})",
                view,
            )
        view["ok"] = False
        view["reason_code"] = HOLD
        return view
    view["ok"] = True
    view["reason_code"] = "ADMIT_CURRENT_BASIN_VIEW"
    view["required"] = must
    return view

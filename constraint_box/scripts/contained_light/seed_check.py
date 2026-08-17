#!/usr/bin/env python3
"""Recompute the time-first seed. Stdlib only. No venv. No promotion.

Loads manifold_foundation by file so a fat package __init__ cannot block
the first Light verb. ADMIT is not contained-Light admission.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import types
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "light" / "fixtures" / "cr").is_dir() or (
            parent / "fixtures" / "cr"
        ).is_dir() or (
            parent / "PROJECT" / "constraint_box" / "fixtures" / "cr"
        ).is_dir():
            return parent
    return Path.cwd().resolve()


def find_seed(root: Path) -> Path:
    for candidate in (
        root / "light" / "fixtures" / "cr" / "manifold_time_first_seed_v1.json",
        root / "fixtures" / "cr" / "manifold_time_first_seed_v1.json",
        root
        / "PROJECT"
        / "constraint_box"
        / "fixtures"
        / "cr"
        / "manifold_time_first_seed_v1.json",
    ):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("time-first seed fixture is missing")


def find_src(root: Path) -> Path:
    for candidate in (
        root / "light" / "src",
        root / "src",
        root / "integrated_system" / "runtime" / "controller_src",
        root / "PROJECT" / "constraint_box" / "src",
    ):
        package = candidate / "constraintbox"
        if (package / "manifold_foundation.py").is_file() and (
            package / "intake.py"
        ).is_file():
            return candidate
    raise FileNotFoundError("constraintbox source tree is missing")


def load_foundation(src: Path):
    package_dir = src / "constraintbox"
    pkg = types.ModuleType("constraintbox")
    pkg.__path__ = [str(package_dir)]
    sys.modules["constraintbox"] = pkg

    def _load(modname: str, filename: str):
        path = package_dir / filename
        spec = importlib.util.spec_from_file_location(modname, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[modname] = module
        spec.loader.exec_module(module)
        return module

    _load("constraintbox.intake", "intake.py")
    return _load("constraintbox.manifold_foundation", "manifold_foundation.py")


def recompute_capacity(counts: list[int]) -> tuple[list[float], list[float]]:
    bits = [math.log2(n) for n in counts]
    delta = [bits[index + 1] - bits[index] for index in range(len(bits) - 1)]
    return bits, delta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Time-first seed check")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    root = find_root(args.root)
    foundation = load_foundation(find_src(root))
    seed = find_seed(root)
    try:
        receipt = foundation.validate_foundation_file(seed)
    except foundation.ManifoldFoundationError as exc:
        print(f"REFUSE: seed failed validation: {exc}", file=sys.stderr)
        return 3

    payload = json.loads(seed.read_text(encoding="utf-8"))
    counts = [int(value) for value in payload["time"]["support_counts"]]
    bits, delta = recompute_capacity(counts)
    declared_bits = [float(value) for value in payload["time"]["capacity_bits"]]
    declared_delta = [float(value) for value in payload["time"]["delta_capacity_bits"]]
    bits_err = max(abs(left - right) for left, right in zip(bits, declared_bits, strict=True))
    delta_err = max(
        abs(left - right) for left, right in zip(delta, declared_delta, strict=True)
    )

    collapsed = json.loads(json.dumps(payload))
    collapsed["dual_engines"]["right_output"] = collapsed["dual_engines"]["left_output"]
    collapsed_ok = False
    try:
        collapsed_receipt = foundation.validate_foundation(collapsed)
        collapsed_ok = bool(collapsed_receipt.get("checks", {}).get("dual_order_gap"))
    except foundation.ManifoldFoundationError:
        collapsed_ok = False

    checks = receipt.get("checks") or {}
    refuses: list[str] = []
    if receipt.get("status") != "PASS":
        refuses.append("status_not_pass")
    if receipt.get("promotion_allowed") is not False:
        refuses.append("promotion_not_false")
    if not checks.get("finite_first"):
        refuses.append("not_finite")
    if not checks.get("positive_capacity_gradient"):
        refuses.append("gradient_not_positive")
    if not checks.get("dual_order_gap"):
        refuses.append("order_gap_collapsed")
    if bits_err > 1e-12 or delta_err > 1e-12:
        refuses.append("capacity_not_recomputed")
    if checks.get("dual_order_gap") and collapsed_ok:
        refuses.append("collapsed_hands_still_report_gap")

    out = {
        "schema": "constraintbox.seed-check.v1",
        "captured_at": _now(),
        "disposition": "ADMIT" if not refuses else "REFUSE",
        "foundation_id": receipt.get("foundation_id"),
        "K": bits,
        "delta_K": delta,
        "support_counts": counts,
        "left_order": payload["dual_engines"]["left_order"],
        "right_order": payload["dual_engines"]["right_order"],
        "dual_order_gap": bool(checks.get("dual_order_gap")),
        "capacity_recompute_abs_error": bits_err,
        "delta_recompute_abs_error": delta_err,
        "collapsed_hands_still_gap": collapsed_ok,
        "refuses": refuses,
        "claim_ceiling": (
            "time-first seed recompute only; not chirality, not measured "
            "distinguishability, not contained Light, not promotion"
        ),
        "honest_entropy": "Hartley_Renyi0_K_equals_log2_W",
        "promotion_allowed": False,
        "source_sha256": receipt.get("source_sha256"),
        "validator_status": receipt.get("status"),
    }
    dest = args.out or (root / "RUNS" / "seed-check" / "SEED_CHECK.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    return 0 if not refuses else 4


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the JAX-native standalone geometry wave and write aggregate receipts."""

from __future__ import annotations

import concurrent.futures
import json
import os
import pathlib
import time
from typing import Any

import jax_native_geometry_engine as engine


ROOT = pathlib.Path(__file__).resolve().parent
REPORT_PATH = ROOT / "jax_native_geometry_math_deep_run_report_20260530.json"
MATRIX_PATH = ROOT / "jax_native_geometry_math_deep_matrix_20260530.json"
CLASSIFICATION = "formal_scout"
TOOL_MANIFEST = {
    "concurrent.futures": {"reason": "Runs independent JAX geometry targets in bounded parallel workers."},
    "json": {"reason": "Writes aggregate run and matrix receipts."},
    "pathlib": {"reason": "Resolves canonical formal_scouts receipt paths."},
}
TOOL_INTEGRATION_DEPTH = {
    "concurrent.futures": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
}


def _run_one(target: str) -> dict[str, Any]:
    try:
        result = engine.run_target(target)
        return {
            "target": target,
            "ok": bool(result["all_pass"]),
            "result_path": result["result_path"],
            "failed_scales": result["failed_scales"],
            "summary": result["summary"],
        }
    except Exception as exc:  # noqa: BLE001 - receipt must capture the failed target.
        return {
            "target": target,
            "ok": False,
            "result_path": None,
            "failed_scales": ["exception"],
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    started = time.time()
    targets = list(engine.TARGETS)
    max_workers = int(os.environ.get("JAX_GEOMETRY_MAX_WORKERS", "4"))
    max_workers = max(1, min(max_workers, len(targets)))
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_one, target): target for target in targets}
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            status = "PASS" if row["ok"] else "FAIL"
            print(json.dumps({"target": row["target"], "status": status, "failed_scales": row["failed_scales"]}, sort_keys=True))
    rows.sort(key=lambda row: row["target"])
    passed = [row["target"] for row in rows if row["ok"]]
    failed = [row for row in rows if not row["ok"]]
    report = {
        "kind": "jax_native_geometry_math_deep_run_report",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "claim_boundary": "JAX-native standalone geometry execution wave only; not G-structure selection, not layer completion, not stacking, not Axis0, not flux, not physics.",
        "targets_total": len(targets),
        "targets_passed": len(passed),
        "targets_failed": len(failed),
        "max_workers": max_workers,
        "scales": engine.SCALES,
        "target_order": targets,
        "rows": rows,
        "failed": failed,
        "elapsed_seconds": round(time.time() - started, 6),
    }
    matrix = {
        "kind": "jax_native_geometry_math_deep_matrix",
        "created_at": report["created_at"],
        "claim_boundary": report["claim_boundary"],
        "rows": {
            row["target"]: {
                "status": "passes_local_run" if row["ok"] else "failed_local_run",
                "result_path": row["result_path"],
                "failed_scales": row["failed_scales"],
                "max_scale_attempted": row.get("summary", {}).get("max_scale_attempted"),
                "min_order_gap": row.get("summary", {}).get("min_order_gap"),
                "min_scrambled_control_delta": row.get("summary", {}).get("min_scrambled_control_delta"),
                "max_target_invariant_residual": row.get("summary", {}).get("max_target_invariant_residual"),
                "min_edge_entanglement_entropy": row.get("summary", {}).get("min_edge_entanglement_entropy"),
            }
            for row in rows
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MATRIX_PATH.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT_PATH), "matrix": str(MATRIX_PATH), "passed": len(passed), "failed": len(failed)}, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Read-only integrity and coverage gate for a local basin-field ensemble.

The gate verifies that a finite local map was actually produced from compatible
source and summary inputs.  It deliberately does not decide tool adoption,
invoke a model, write SQLite, or treat a map as a promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from . import basin_field


GATE_SCHEMA = "constraintbox.basin-field-gate.v1"


class FieldGateRequest(BaseModel):
    """Per-run acceptance floor; none of these values are a package policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ensemble_path: Path
    min_density: int = Field(ge=1)
    min_rounds: int = Field(ge=1)
    min_seed_count: int = Field(ge=2)
    min_region_stability: float = Field(ge=0.0, le=1.0)
    min_stable_regions: int = Field(ge=1)
    required_tool_ids: tuple[str, ...] = ()
    outer_tool_matrix_path: Path | None = None
    required_outer_probe_tool_ids: tuple[str, ...] = ()


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hold(request: FieldGateRequest, reasons: list[str], detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": GATE_SCHEMA,
        "profile": "cb_light",
        "disposition": "HOLD",
        "reason_codes": sorted(set(reasons)),
        "request": request.model_dump(mode="json"),
        "detail": detail,
        "promotion_allowed": False,
        "claim_ceiling": (
            "read-only local field-map verification only; no selection, adoption, host-hook, provider, "
            "model, portability, CB Heavy, promotion, or release claim"
        ),
    }


def verify_ensemble(request: FieldGateRequest) -> dict[str, Any]:
    """Verify custody and declared local coverage of an ensemble and its inputs."""

    path = request.ensemble_path
    if not path.is_file():
        return _hold(request, ["HOLD_FIELD_ENSEMBLE_MISSING"], {"path": str(path)})
    try:
        ensemble = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _hold(
            request,
            ["HOLD_FIELD_ENSEMBLE_INVALID_JSON"],
            {"path": str(path), "exception_type": type(exc).__name__},
        )
    if ensemble.get("schema") != "constraintbox.basin-field-ensemble.v1":
        return _hold(request, ["HOLD_FIELD_ENSEMBLE_SCHEMA"], {"observed": ensemble.get("schema")})
    if ensemble.get("promotion_allowed") is not False:
        return _hold(request, ["HOLD_FIELD_ENSEMBLE_CLAIM_CEILING"], {})

    current_source_sha = _sha256_path(Path(basin_field.__file__))
    reasons: list[str] = []
    detail: dict[str, Any] = {
        "ensemble_sha256": _sha256_path(path),
        "ensemble_source_sha256": ensemble.get("source_sha256"),
        "current_field_source_sha256": current_source_sha,
    }
    if ensemble.get("source_sha256") != current_source_sha:
        reasons.append("HOLD_FIELD_SOURCE_DRIFT")

    config = ensemble.get("config_without_seed")
    if not isinstance(config, dict):
        reasons.append("HOLD_FIELD_ENSEMBLE_CONFIG")
        config = {}
    else:
        detail["config_without_seed"] = config
        if int(config.get("density", 0)) < request.min_density:
            reasons.append("HOLD_FIELD_DENSITY_BELOW_REQUEST")
        if int(config.get("rounds", 0)) < request.min_rounds:
            reasons.append("HOLD_FIELD_ROUNDS_BELOW_REQUEST")

    inputs = ensemble.get("inputs")
    bound_outer_hashes: set[str] = set()
    if not isinstance(inputs, list) or len(inputs) < request.min_seed_count:
        reasons.append("HOLD_FIELD_SEED_COUNT_BELOW_REQUEST")
        inputs = []
    else:
        seeds: set[int] = set()
        input_errors: list[dict[str, Any]] = []
        for record in inputs:
            if not isinstance(record, dict):
                input_errors.append({"reason": "record_not_object"})
                continue
            input_path = Path(str(record.get("path", "")))
            if not input_path.is_file():
                input_errors.append({"path": str(input_path), "reason": "missing"})
                continue
            observed_sha = _sha256_path(input_path)
            if observed_sha != record.get("sha256"):
                input_errors.append({"path": str(input_path), "reason": "sha256_mismatch"})
                continue
            try:
                summary = json.loads(input_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                input_errors.append({"path": str(input_path), "reason": "invalid_json"})
                continue
            if (
                summary.get("schema") != basin_field.FIELD_SCHEMA
                or summary.get("promotion_allowed") is not False
                or summary.get("runtime", {}).get("source_sha256") != current_source_sha
                or summary.get("config", {}).get("seed") != record.get("seed")
            ):
                input_errors.append({"path": str(input_path), "reason": "summary_binding_invalid"})
                continue
            outer = summary.get("outer_tool_matrix")
            if isinstance(outer, dict) and isinstance(outer.get("sha256"), str):
                bound_outer_hashes.add(outer["sha256"])
            seeds.add(int(record["seed"]))
        if input_errors or len(seeds) < request.min_seed_count:
            reasons.append("HOLD_FIELD_INPUT_BINDING")
        detail["input_errors"] = input_errors
        detail["unique_seed_count"] = len(seeds)

    stability = ensemble.get("candidate_region_stability")
    if not isinstance(stability, dict):
        reasons.append("HOLD_FIELD_REGION_STABILITY_MISSING")
        stability = {}
    else:
        detail["candidate_region_stability"] = stability
        if float(stability.get("jaccard", -1.0)) < request.min_region_stability:
            reasons.append("HOLD_FIELD_REGION_STABILITY_BELOW_REQUEST")
        if int(stability.get("intersection", 0)) < request.min_stable_regions:
            reasons.append("HOLD_FIELD_STABLE_REGIONS_BELOW_REQUEST")

    tool_rows = ensemble.get("tool_stability")
    observed_tools = {
        str(row.get("tool_id")) for row in tool_rows if isinstance(row, dict) and row.get("tool_id")
    } if isinstance(tool_rows, list) else set()
    missing_tools = sorted(set(request.required_tool_ids) - observed_tools)
    detail["observed_tool_ids"] = sorted(observed_tools)
    if missing_tools:
        reasons.append("HOLD_FIELD_REQUIRED_TOOL_UNOBSERVED")
        detail["missing_tool_ids"] = missing_tools

    if request.outer_tool_matrix_path is not None or request.required_outer_probe_tool_ids:
        outer_path = request.outer_tool_matrix_path
        if outer_path is None or not outer_path.is_file():
            reasons.append("HOLD_FIELD_OUTER_MATRIX_MISSING")
        else:
            outer_sha = _sha256_path(outer_path)
            detail["outer_tool_matrix_sha256"] = outer_sha
            if bound_outer_hashes != {outer_sha}:
                reasons.append("HOLD_FIELD_OUTER_MATRIX_BINDING")
                detail["bound_outer_matrix_hashes"] = sorted(bound_outer_hashes)
            try:
                outer_payload = json.loads(outer_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                outer_payload = None
            if (
                not isinstance(outer_payload, dict)
                or outer_payload.get("schema") != "constraintbox.cb-light-tool-probes.v1"
                or not isinstance(outer_payload.get("tool_decisions"), list)
            ):
                reasons.append("HOLD_FIELD_OUTER_MATRIX_INVALID")
            else:
                rows = {
                    str(row.get("normalized_name")): row
                    for row in outer_payload["tool_decisions"]
                    if isinstance(row, dict) and row.get("normalized_name")
                }
                outer_failures: list[str] = []
                for tool_id in request.required_outer_probe_tool_ids:
                    row = rows.get(tool_id)
                    facts = row.get("facts") if isinstance(row, dict) else None
                    if (
                        not isinstance(row, dict)
                        or row.get("disposition") != "ADMIT"
                        or not isinstance(facts, dict)
                        or not all(value is True for value in facts.values())
                        or row.get("replay", {}).get("equal") is not True
                        or row.get("severance", {}).get("payload", {}).get("severance", {}).get("passed") is not True
                    ):
                        outer_failures.append(tool_id)
                if outer_failures:
                    reasons.append("HOLD_FIELD_OUTER_PROBE_CONSTRAINTS")
                    detail["outer_probe_failures"] = sorted(outer_failures)

    if reasons:
        return _hold(request, reasons, detail)
    return {
        "schema": GATE_SCHEMA,
        "profile": "cb_light",
        "disposition": "FIELD_MAP_READY_LOCAL",
        "reason_codes": ["FIELD_ENSEMBLE_CUSTODY_AND_COVERAGE_VERIFIED"],
        "request": request.model_dump(mode="json"),
        "detail": detail,
        "promotion_allowed": False,
        "claim_ceiling": (
            "read-only local field-map verification only; no selection, adoption, host-hook, provider, "
            "model, portability, CB Heavy, promotion, or release claim"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify one bounded CB Light basin-field ensemble.")
    parser.add_argument("--ensemble", type=Path, required=True)
    parser.add_argument("--min-density", type=int, required=True)
    parser.add_argument("--min-rounds", type=int, required=True)
    parser.add_argument("--min-seeds", type=int, required=True)
    parser.add_argument("--min-region-stability", type=float, required=True)
    parser.add_argument("--min-stable-regions", type=int, required=True)
    parser.add_argument("--require-tool", dest="required_tool_ids", action="append", default=[])
    parser.add_argument("--outer-tool-matrix", type=Path)
    parser.add_argument("--require-outer-tool", dest="required_outer_probe_tool_ids", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request = FieldGateRequest(
        ensemble_path=args.ensemble,
        min_density=args.min_density,
        min_rounds=args.min_rounds,
        min_seed_count=args.min_seeds,
        min_region_stability=args.min_region_stability,
        min_stable_regions=args.min_stable_regions,
        required_tool_ids=tuple(args.required_tool_ids),
        outer_tool_matrix_path=args.outer_tool_matrix,
        required_outer_probe_tool_ids=tuple(args.required_outer_probe_tool_ids),
    )
    result = verify_ensemble(request)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["disposition"] == "FIELD_MAP_READY_LOCAL" else 2


if __name__ == "__main__":  # pragma: no cover - exercised through module invocation.
    raise SystemExit(main())

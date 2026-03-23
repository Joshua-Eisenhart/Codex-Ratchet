#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from family_slice_runtime_validation import validate_family_slice_runtime_semantics
from stage2_schema_gate import _validate_with_jsonschema_or_fallback
from validate_a1_worker_launch_packet import validate as validate_packet


SCHEMA = "A2_TO_A1_FAMILY_SLICE_v1"
ALLOWED_QUEUE_STATUSES = {
    "READY_FROM_NEW_A2_HANDOFF",
    "READY_FROM_EXISTING_FUEL",
    "READY_FROM_A2_PREBUILT_BATCH",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_family_slice_schema() -> Path:
    return _repo_root() / "work" / "audit_tmp" / "spec_object_drafts" / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"


def _default_a1_boot() -> Path:
    return _repo_root() / "system_v3" / "specs" / "31_A1_THREAD_BOOT__v1.md"


def _default_spec_graph_python() -> Path:
    return _repo_root() / ".venv_spec_graph" / "bin" / "python"


def _default_a1_reload_artifacts() -> list[Path]:
    specs_root = _repo_root() / "system_v3" / "specs"
    return [
        specs_root / "77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md",
        specs_root / "78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md",
    ]


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _require_abs_existing(path_str: str, key: str) -> str:
    path = Path(path_str)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    if not path.exists():
        raise SystemExit(f"missing_path_{key}:{path}")
    return str(path)


def _require_abs_path(path_str: str, key: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    return path


def _require_nonempty_text(value: str, key: str) -> str:
    text = value.strip()
    if not text:
        raise SystemExit(f"missing_{key}")
    return text


def _require_nonnegative(value: int, key: str) -> int:
    if value < 0:
        raise SystemExit(f"negative_{key}")
    return value


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _build_validation_requested_provenance(requested_mode: str) -> dict[str, str]:
    return {
        "mode": _require_nonempty_text(requested_mode, "family_slice_validation_requested_mode"),
    }


def _build_validation_resolved_provenance(resolved_mode: str, validation_source: str) -> dict[str, str]:
    return {
        "mode": _require_nonempty_text(resolved_mode, "family_slice_validation_resolved_mode"),
        "source": _require_nonempty_text(validation_source, "family_slice_validation_source"),
    }


def _validate_family_slice(family_slice: dict[str, Any], schema_path: Path) -> str:
    if family_slice.get("schema") != SCHEMA:
        raise SystemExit("invalid_family_slice_schema")
    schema = _load_json(schema_path)
    errors = _validate_with_jsonschema_or_fallback(instance=family_slice, schema=schema)
    if errors:
        raise SystemExit(f"family_slice_schema_validation_failed:{errors[0]}")
    try:
        return validate_family_slice_runtime_semantics(family_slice)
    except ValueError as exc:
        raise SystemExit(f"family_slice_semantic_validation_failed:{exc}") from exc


def _validate_family_slice_with_local_pydantic(family_slice_path: Path, spec_graph_python: Path) -> str:
    if not spec_graph_python.is_absolute():
        raise SystemExit("non_absolute_spec_graph_python")
    if not spec_graph_python.exists():
        raise SystemExit(f"missing_spec_graph_python:{spec_graph_python}")
    audit_script = _repo_root() / "system_v3" / "tools" / "audit_a2_to_a1_family_slice_pydantic.py"
    env = os.environ.copy()
    env.pop("__PYVENV_LAUNCHER__", None)
    env.pop("PYTHONEXECUTABLE", None)
    proc = subprocess.run(
        [
            str(spec_graph_python),
            str(audit_script),
            "--family-slice-json",
            str(family_slice_path),
        ],
        capture_output=True,
        env=env,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout or "").strip() or "family_slice_local_pydantic_validation_failed")
    return "local_pydantic_audit"


def _resolve_validation_mode(requested_mode: str, spec_graph_python: Path) -> str:
    if requested_mode != "auto":
        return requested_mode
    return "local_pydantic" if spec_graph_python.exists() else "jsonschema"


def _effective_dispatch_id(explicit_dispatch_id: str, family_slice: dict[str, Any]) -> str:
    if explicit_dispatch_id.strip():
        return explicit_dispatch_id.strip()
    dispatch_id = str(family_slice.get("dispatch_id", "")).strip()
    if not dispatch_id or dispatch_id.startswith("DRAFT_ONLY__"):
        raise SystemExit("dispatch_id_required_for_family_slice_compilation")
    return dispatch_id


def _source_artifacts_from_family_slice(
    family_slice_path: Path,
    family_slice: dict[str, Any],
) -> list[str]:
    declared = list(family_slice.get("source_a2_artifacts", []))
    ordered = [str(family_slice_path), *declared]
    return _dedupe_preserve_order(ordered)


def build_prompt_to_send(
    *,
    family_slice_path: Path,
    family_slice: dict[str, Any],
    required_a1_boot: str,
    a1_reload_artifacts: list[str],
    source_a2_artifacts: list[str],
) -> str:
    required_lanes = ", ".join(family_slice.get("required_lanes", []))
    primary_terms = ", ".join(family_slice.get("primary_target_terms", []))
    negative_classes = ", ".join(family_slice.get("required_negative_classes", []))
    run_mode = str(family_slice.get("run_mode", "")).strip()
    family_id = str(family_slice.get("family_id", "")).strip()
    family_label = str(family_slice.get("family_label", "")).strip()
    target_a1_role = str(family_slice.get("target_a1_role", "")).strip()
    stop_rule = str(family_slice.get("stop_rule", "")).strip()

    lines = [
        "Use the current A1 boot:",
        f"- {required_a1_boot}",
        "",
        "Read these A1 reload artifacts before acting:",
        *(f"- {path}" for path in a1_reload_artifacts),
        "",
        "Use this bounded A2-derived family slice as the governing campaign object:",
        f"- {family_slice_path}",
        "",
        "Use only these A2 fuel surfaces:",
        *(f"- {path}" for path in source_a2_artifacts),
        "",
        f"Run one bounded {target_a1_role} pass only.",
        "",
        "Family slice identity:",
        f"- slice_id: {family_slice['slice_id']}",
        f"- family_id: {family_id}",
        f"- family_label: {family_label}",
        f"- run_mode: {run_mode}",
        f"- required_lanes: {required_lanes}",
        f"- primary_target_terms: {primary_terms}",
        f"- required_negative_classes: {negative_classes}",
        "",
        "Task:",
        f"- generate one bounded {target_a1_role} family campaign from the supplied family slice",
        "- obey the slice lane obligations, branch requirements, graveyard/rescue policy, admissibility, and sim hooks",
        "- preserve contradictions and remain proposal-only",
        "",
        "Rules:",
        "- no A2 refinery",
        "- no canon claims",
        "- no lower-loop claims",
        "- no hidden-memory continuation",
        "- fail closed if family-slice obligations are missing",
        f"- stop_rule: {stop_rule}",
    ]
    return "\n".join(lines)


def build_packet(
    *,
    family_slice_path: Path,
    family_slice: dict[str, Any],
    model: str,
    queue_status: str,
    dispatch_id: str,
    required_a1_boot: str,
    a1_reload_artifacts: list[str],
    go_on_count: int,
    go_on_budget: int,
    family_slice_validation_requested_mode: str,
    family_slice_validation_resolved_mode: str,
    family_slice_validation_source: str,
) -> dict[str, Any]:
    source_a2_artifacts = _source_artifacts_from_family_slice(
        family_slice_path=family_slice_path,
        family_slice=family_slice,
    )
    prompt_to_send = build_prompt_to_send(
        family_slice_path=family_slice_path,
        family_slice=family_slice,
        required_a1_boot=required_a1_boot,
        a1_reload_artifacts=a1_reload_artifacts,
        source_a2_artifacts=source_a2_artifacts,
    )
    return {
        "schema": "A1_WORKER_LAUNCH_PACKET_v1",
        "model": _require_nonempty_text(model, "model"),
        "thread_class": "A1_WORKER",
        "mode": "PROPOSAL_ONLY",
        "queue_status": _require_nonempty_text(queue_status, "queue_status"),
        "dispatch_id": _require_nonempty_text(dispatch_id, "dispatch_id"),
        "target_a1_role": _require_nonempty_text(str(family_slice["target_a1_role"]), "target_a1_role"),
        "required_a1_boot": required_a1_boot,
        "a1_reload_artifacts": a1_reload_artifacts,
        "source_a2_artifacts": source_a2_artifacts,
        "bounded_scope": _require_nonempty_text(str(family_slice["bounded_scope"]), "bounded_scope"),
        "prompt_to_send": prompt_to_send,
        "stop_rule": _require_nonempty_text(str(family_slice["stop_rule"]), "stop_rule"),
        "go_on_count": _require_nonnegative(go_on_count, "go_on_count"),
        "go_on_budget": _require_nonnegative(go_on_budget, "go_on_budget"),
        "family_slice_validation_requested_mode": _require_nonempty_text(
            family_slice_validation_requested_mode,
            "family_slice_validation_requested_mode",
        ),
        "family_slice_validation_resolved_mode": _require_nonempty_text(
            family_slice_validation_resolved_mode,
            "family_slice_validation_resolved_mode",
        ),
        "family_slice_validation_source": _require_nonempty_text(
            family_slice_validation_source,
            "family_slice_validation_source",
        ),
        "family_slice_validation_requested_provenance": _build_validation_requested_provenance(
            family_slice_validation_requested_mode
        ),
        "family_slice_validation_resolved_provenance": _build_validation_resolved_provenance(
            family_slice_validation_resolved_mode,
            family_slice_validation_source,
        ),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Compile one A1_WORKER_LAUNCH_PACKET_v1 from one bounded A2_TO_A1_FAMILY_SLICE_v1 object."
    )
    parser.add_argument("--family-slice-json", required=True)
    parser.add_argument("--family-slice-schema-json", default=str(_default_family_slice_schema()))
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--queue-status",
        default="READY_FROM_NEW_A2_HANDOFF",
        choices=sorted(ALLOWED_QUEUE_STATUSES),
    )
    parser.add_argument("--dispatch-id", default="")
    parser.add_argument("--required-a1-boot", default=str(_default_a1_boot()))
    parser.add_argument("--a1-reload-artifact", action="append", default=[])
    parser.add_argument(
        "--family-slice-validation-mode",
        choices=("jsonschema", "local_pydantic", "auto"),
        default="auto",
    )
    parser.add_argument("--spec-graph-python", default=str(_default_spec_graph_python()))
    parser.add_argument("--go-on-count", type=int, default=0)
    parser.add_argument("--go-on-budget", type=int, default=1)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    family_slice_path = Path(args.family_slice_json)
    schema_path = Path(args.family_slice_schema_json)
    out_path = Path(args.out_json)
    if not family_slice_path.is_absolute():
        raise SystemExit("non_absolute_family_slice_json")
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_json")

    family_slice = _load_json(family_slice_path)
    if not isinstance(family_slice, dict):
        raise SystemExit("family_slice_must_be_object")
    spec_graph_python = _require_abs_path(args.spec_graph_python, "spec_graph_python")
    resolved_validation_mode = _resolve_validation_mode(args.family_slice_validation_mode, spec_graph_python)
    if resolved_validation_mode == "jsonschema":
        if not schema_path.is_absolute():
            raise SystemExit("non_absolute_family_slice_schema_json")
        validation_source = _validate_family_slice(family_slice, schema_path)
    else:
        validation_source = _validate_family_slice_with_local_pydantic(
            family_slice_path=family_slice_path,
            # Keep the venv launcher path intact; resolving the symlink collapses it
            # back to the base Homebrew interpreter and defeats the local stack.
            spec_graph_python=spec_graph_python.expanduser(),
        )

    required_a1_boot = _require_abs_existing(args.required_a1_boot, "required_a1_boot")
    reload_artifact_paths = args.a1_reload_artifact or [str(path) for path in _default_a1_reload_artifacts()]
    a1_reload_artifacts = [
        _require_abs_existing(path, f"a1_reload_artifact_{index}")
        for index, path in enumerate(reload_artifact_paths, start=1)
    ]
    packet = build_packet(
        family_slice_path=family_slice_path,
        family_slice=family_slice,
        model=args.model,
        queue_status=args.queue_status,
        dispatch_id=_effective_dispatch_id(args.dispatch_id, family_slice),
        required_a1_boot=required_a1_boot,
        a1_reload_artifacts=a1_reload_artifacts,
        go_on_count=args.go_on_count,
        go_on_budget=args.go_on_budget,
        family_slice_validation_requested_mode=args.family_slice_validation_mode,
        family_slice_validation_resolved_mode=resolved_validation_mode,
        family_slice_validation_source=validation_source,
    )
    validation = validate_packet(packet)
    if not validation.get("valid"):
        raise SystemExit(f"compiled_packet_invalid:{validation['errors'][0]}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

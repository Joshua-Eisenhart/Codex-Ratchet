#!/usr/bin/env python3
"""Rehearse QIT micro-admission in a disposable canonical-shaped temp repo."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def disposable_out_dir(path: Path) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    tmp_root = Path("/tmp").resolve(strict=False)
    try:
        rel = resolved.relative_to(tmp_root)
    except ValueError as exc:
        raise ValueError("out_dir_not_under_tmp_codex_ratchet_prefix") from exc
    if not rel.parts or not rel.parts[0].startswith("codex_ratchet_"):
        raise ValueError("out_dir_not_under_tmp_codex_ratchet_prefix")
    return resolved


def run(command: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    return {"command": command, "returncode": proc.returncode, "stdout": proc.stdout[-4000:]}


def first_load_bearing_tool(payload: dict[str, Any]) -> str:
    depths = payload.get("tool_integration_depth") or payload.get("TOOL_INTEGRATION_DEPTH") or {}
    if isinstance(depths, dict):
        for tool, depth in depths.items():
            if str(depth) == "load_bearing":
                return str(tool).split(".", 1)[0].lower()
    return "tool"


def result_function_surface(payload: dict[str, Any], tool: str) -> str:
    positive = payload.get("positive") or {}
    if isinstance(positive, dict):
        surface = positive.get("function_surface")
        if surface:
            return str(surface)
        for item in positive.values():
            if isinstance(item, dict) and item.get("function_surface"):
                return str(item["function_surface"])
    return f"{tool}.micro_fixture"


def result_passed(payload: dict[str, Any]) -> bool:
    if "all_passed" in payload:
        return bool(payload.get("all_passed"))
    if "all_pass" in payload:
        return bool(payload.get("all_pass"))
    summary = payload.get("summary") or {}
    if isinstance(summary, dict) and {"passed", "total"} <= set(summary):
        return summary.get("passed") == summary.get("total")
    return False


def build_admission(
    *,
    tmp_repo: Path,
    basename: str,
    sim_rel: str,
    result_path: Path,
    artifact_path: Path,
    payload: dict[str, Any],
    function_surface_override: str | None = None,
) -> dict[str, Any]:
    tool = first_load_bearing_tool(payload)
    function_surface = function_surface_override or result_function_surface(payload, tool)
    claim_ceiling = str(payload.get("claim_ceiling") or "tool_micro_only")
    demotion = str(payload.get("demotion_condition") or "demote if this micro fixture fails")
    out_of_scope = payload.get("out_of_scope") if isinstance(payload.get("out_of_scope"), list) else ["no promotion"]
    return {
        "schema": "wizard_sim_admission_v4_2",
        "basename": basename,
        "sim_path": sim_rel,
        "status": "queue_ready",
        "admitted_by": "guard.receipt_audit",
        "admission_artifact": str(artifact_path),
        "controller_read_artifacts": [str(artifact_path), str(result_path)],
        "bounded_work_compile_gate": {"status": "ready_for_execution"},
        "sim_packet_compile_gate": {"status": "queue_candidate"},
        "sim_admissibility_gate": {"result": "one_exact_packet"},
        "formal_sim_profile": {
            "stage": "micro",
            "claim": claim_ceiling,
            "carrier_fixture": basename,
            "exact_tool_or_function": function_surface,
            "positive_check": "result positive checks pass",
            "negative_or_boundary_check": "result negative and boundary checks pass",
            "expected_result_path": str(result_path),
        },
        "management_parent_surfaces": [
            "queue_liveness",
            "runner_preflight",
            "sim_admissibility",
            "queue_readiness",
            "formal_sim_profile",
            "stage_gate",
            "expected_result_surface",
            "controller_read_artifacts",
        ],
        "packet_contract": {
            "type": "MICRO",
            "tool_target": tool,
            "function_surface": function_surface,
            "micro_claim": claim_ceiling,
            "lego_target": str(payload.get("next_lego_target") or basename),
            "function_receipt": "new",
            "prior_function_receipts": [],
            "why_this_lego": "the fixture exposes one bounded micro surface without broad promotion",
            "positive_case": "positive checks pass",
            "negative_case": "negative checks pass",
            "boundary_case": "boundary checks pass",
            "demotion_condition": demotion,
            "out_of_scope": out_of_scope,
            "claim_ceiling": claim_ceiling,
            "next_lego_target": str(payload.get("next_lego_target") or "strict canonical admission before coupling work"),
            "promotion_condition": str(payload.get("promotion_condition") or "requires later admitted row and stage-gate approval"),
            "blocked_until": str(payload.get("blocked_until") or "exact canonical result hash is admitted"),
            "promotion_boundary": "no promotion beyond tool_micro without a later admitted packet",
        },
    }


def prepare_tmp_repo(*, out_dir: Path, basename: str, result_path: Path, sim_path: Path | None) -> tuple[Path, Path, Path]:
    out_dir = disposable_out_dir(out_dir)
    if out_dir.exists():
        if not out_dir.is_dir():
            raise ValueError("out_dir_exists_and_is_not_directory")
        shutil.rmtree(out_dir)
    canonical_dir = out_dir / "system_v4" / "probes" / "a2_state" / "sim_results"
    canonical_dir.mkdir(parents=True)
    (out_dir / "system_v5" / "ops" / "wizard_admissions").mkdir(parents=True)
    (out_dir / "receipts").mkdir(parents=True)
    scripts_dir = out_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    stage_gate = scripts_dir / "stage_gate.py"
    stage_gate.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
    stage_gate.chmod(0o755)
    tmp_result = canonical_dir / f"{basename}_results.json"
    shutil.copy2(result_path, tmp_result)
    if sim_path and sim_path.exists():
        tmp_source = out_dir / "system_v4" / "probes" / f"{basename}.py"
        tmp_source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sim_path, tmp_source)
    return out_dir, tmp_result, out_dir / "receipts" / f"{basename}_admission_artifact.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--basename", required=True)
    parser.add_argument("--result", required=True, help="Existing result JSON to rehearse as canonical evidence")
    parser.add_argument("--sim-path", help="Source sim path to bind inside the temp repo")
    parser.add_argument("--function-surface", help="Exact function/API surface for the generated admission packet")
    parser.add_argument("--out-dir", default="/tmp/codex_ratchet_qit_admission_rehearsal")
    args = parser.parse_args()

    basename = args.basename
    result = Path(args.result)
    if not result.is_absolute():
        result = REPO_ROOT / result
    sim_path = Path(args.sim_path) if args.sim_path else REPO_ROOT / "system_v4" / "probes" / f"{basename}.py"
    if not sim_path.is_absolute():
        sim_path = REPO_ROOT / sim_path
    if not result.exists():
        print(json.dumps({"ok": False, "finding": "result_missing", "result": str(result)}, indent=2))
        return 2

    payload = load_json(result)
    try:
        tmp_repo, tmp_result, artifact = prepare_tmp_repo(
            out_dir=Path(args.out_dir),
            basename=basename,
            result_path=result,
            sim_path=sim_path if sim_path.exists() else None,
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "finding": str(exc), "out_dir": args.out_dir}, indent=2))
        return 2
    result_hash = sha256(tmp_result)
    write_json(artifact, {"result_path": str(tmp_result), "result_sha256": result_hash})
    admission = build_admission(
        tmp_repo=tmp_repo,
        basename=basename,
        sim_rel=f"system_v4/probes/{basename}.py",
        result_path=tmp_result,
        artifact_path=artifact,
        payload=payload,
        function_surface_override=args.function_surface,
    )
    admission_path = tmp_repo / "system_v5" / "ops" / "wizard_admissions" / f"{basename}.json"
    write_json(admission_path, admission)

    receipt_validation = run(
        [
            sys.executable,
            "scripts/validate_receipt.py",
            "--strict-scope",
            "--require-executable",
            "--require-run-boundary",
            str(tmp_result),
        ]
    )
    admission_validation = run(
        [
            sys.executable,
            "scripts/wizard_sim_admission.py",
            "--repo-root",
            str(tmp_repo),
            "--basename",
            basename,
            "--sim-path",
            f"system_v4/probes/{basename}.py",
        ]
    )
    index_path = tmp_repo / "qit_engine_evidence_index.json"
    index_run = run(
        [
            sys.executable,
            "scripts/qit_engine_evidence_index.py",
            "--repo-root",
            str(tmp_repo),
            "--out",
            str(index_path),
            "--require-accepted",
        ]
    )
    index_payload = load_json(index_path)
    accepted = int(((index_payload.get("summary") or {}).get("accepted") or 0))
    ok = (
        result_passed(payload)
        and receipt_validation["returncode"] == 0
        and admission_validation["returncode"] == 0
        and index_run["returncode"] == 0
        and accepted > 0
    )
    report = {
        "ok": ok,
        "tmp_repo": str(tmp_repo),
        "basename": basename,
        "result_sha256": result_hash,
        "result_passed": result_passed(payload),
        "tmp_result": str(tmp_result),
        "admission": str(admission_path),
        "qit_index": str(index_path),
        "accepted": accepted,
        "admitted_micro_entries": int(((index_payload.get("summary") or {}).get("admitted_micro_entries") or 0)),
        "operational_status": index_payload.get("operational_status"),
        "receipt_validation": receipt_validation,
        "admission_validation": admission_validation,
        "index_run": index_run,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

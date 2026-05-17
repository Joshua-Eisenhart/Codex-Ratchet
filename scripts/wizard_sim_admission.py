#!/usr/bin/env python3
"""Validate Wizard sim-admission packets before queue execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import receipt_schema


NONCLASSICAL_LOAD_BEARING_TOOLS = {"z3", "cvc5", "clifford", "torch", "pytorch", "pyg", "qiskit", "qutip"}
HIDDEN_NONCLASSICAL_TOKENS = ("rho_ab", "rho_AB", "Phi0", "phi0", "Xi", "xi", "coupling witness")
CANONICAL_SCHEMA = "wizard_sim_admission_v4_2"
LEGACY_SCHEMA = "wizard_sim_admission_v4_1"
_STAGE_GATE_CACHE: dict[tuple[str, str, int], str | None] = {}
_HIDDEN_NONCLASSICAL_PATTERNS = tuple(
    re.compile(rf"(?<![A-Za-z0-9_]){re.escape(token.lower())}(?![A-Za-z0-9_])")
    for token in HIDDEN_NONCLASSICAL_TOKENS
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_or_abs(root: Path, value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else root / p


def expected_result(root: Path, basename: str) -> Path:
    return root / "system_v4" / "probes" / "a2_state" / "sim_results" / f"{basename}_results.json"


def _canonical_results_dir(root: Path) -> Path:
    return root / "system_v4" / "probes" / "a2_state" / "sim_results"


def _allowed_payload_named_result(root: Path, basename: str, profile_expected_path: str) -> Path | None:
    if not profile_expected_path:
        return None
    candidate = rel_or_abs(root, profile_expected_path)
    try:
        candidate.resolve().relative_to(_canonical_results_dir(root).resolve())
    except ValueError:
        return None
    if not candidate.name.endswith("_results.json"):
        return None
    payload = _load_json(candidate)
    if payload.get("name") != basename:
        return None
    if not (root / "system_v4" / "probes" / f"{basename}.py").exists():
        return None
    return candidate


def resolve_expected_result(root: Path, basename: str, profile_expected_path: str, override: str | Path | None = None) -> Path:
    if override:
        return rel_or_abs(root, override)
    alternate = _allowed_payload_named_result(root, basename, profile_expected_path)
    if alternate:
        return alternate
    return expected_result(root, basename)


def stage_claim(stage: str) -> str:
    if stage in {"micro", "tool_micro"}:
        return "tool_micro"
    if stage in {"integration_micro", "tool_integration_micro"}:
        return "tool_integration_micro"
    if stage in {"qit", "engine", "bridge", "axis"}:
        return "engine" if stage in {"qit", "engine"} else stage
    return "tool_micro"


def check_stage_gate(root: Path, claim: str) -> str | None:
    script = root / "scripts" / "stage_gate.py"
    if not script.exists():
        return "stage_gate_missing_for_tool_micro" if claim == "tool_micro" else "stage_gate_missing_for_engine"
    try:
        cache_key = (str(script.resolve(strict=False)), claim, script.stat().st_mtime_ns)
    except OSError:
        cache_key = (str(script.resolve(strict=False)), claim, -1)
    if cache_key in _STAGE_GATE_CACHE:
        return _STAGE_GATE_CACHE[cache_key]
    proc = subprocess.run([sys.executable, str(script), "--claim", claim], cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if proc.returncode != 0:
        finding = "stage_gate_rejects_engine" if claim == "engine" else f"stage_gate_rejects_{claim}"
        _STAGE_GATE_CACHE[cache_key] = finding
        return finding
    _STAGE_GATE_CACHE[cache_key] = None
    return None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _tool_family(value: str) -> str:
    return receipt_schema.canonical_tool_name(value)


def _load_bearing_tool_families(result_payload: dict[str, Any]) -> set[str]:
    depths = result_payload.get("tool_integration_depth") or result_payload.get("TOOL_INTEGRATION_DEPTH") or {}
    return {
        _tool_family(str(tool))
        for tool, depth in depths.items()
        if str(depth) == "load_bearing"
    }


def _tool_role_sources(result_payload: dict[str, Any]) -> dict[str, str]:
    manifest = result_payload.get("tool_manifest") or result_payload.get("TOOL_MANIFEST") or {}
    raw = result_payload.get("tool_role_source") or result_payload.get("TOOL_ROLE_SOURCE") or {}
    sources: dict[str, str] = {}
    if isinstance(raw, dict):
        sources.update(
            {
                str(tool): str(source).strip().lower().replace("_", "-")
                for tool, source in raw.items()
            }
        )
    if isinstance(manifest, dict):
        for tool, entry in manifest.items():
            if not isinstance(entry, dict):
                continue
            source = (
                entry.get("role_source")
                or entry.get("tool_role_source")
                or entry.get("integration_source")
            )
            if source:
                sources.setdefault(str(tool), str(source).strip().lower().replace("_", "-"))
                continue
            reason = str(entry.get("reason") or "").lower()
            if "transitive" in reason or "through enginecore" in reason or "through engine_core" in reason:
                sources.setdefault(str(tool), "transitive")
    return sources


def _local_load_bearing_tool_families(result_payload: dict[str, Any]) -> set[str]:
    depths = result_payload.get("tool_integration_depth") or result_payload.get("TOOL_INTEGRATION_DEPTH") or {}
    sources = _tool_role_sources(result_payload)
    local_tools: set[str] = set()
    for tool, depth in depths.items():
        if str(depth) != "load_bearing":
            continue
        source = sources.get(str(tool)) or sources.get(_tool_family(str(tool)))
        if source in {"transitive", "upstream", "imported", "delegated", "engine-core", "engine_core"}:
            continue
        local_tools.add(_tool_family(str(tool)))
    return local_tools


def _result_execution_kind(result_payload: dict[str, Any]) -> str:
    summary = result_payload.get("summary") if isinstance(result_payload.get("summary"), dict) else {}
    return receipt_schema.normalized_execution_kind(
        result_payload.get("sim_execution_kind")
        or result_payload.get("SIM_EXECUTION_KIND")
        or summary.get("sim_execution_kind")
        or summary.get("SIM_EXECUTION_KIND")
    )


def _has_hidden_nonclassical_signal(root: Path, sim_path: str, result_payload: dict[str, Any]) -> bool:
    text = json.dumps(result_payload, sort_keys=True)
    source = rel_or_abs(root, sim_path)
    if source.exists():
        try:
            text += "\n" + source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass
    lowered = text.lower()
    return any(pattern.search(lowered) for pattern in _HIDDEN_NONCLASSICAL_PATTERNS)


def validate_admission(
    payload: dict[str, Any],
    *,
    root: Path,
    basename: str,
    sim_path: str,
    expected_result_path: str | Path | None = None,
    allow_legacy_v4_1: bool = False,
) -> list[str]:
    findings: list[str] = []
    schema = payload.get("schema")
    if schema == LEGACY_SCHEMA and not allow_legacy_v4_1:
        findings.append("schema_legacy_v4_1_requires_explicit_recovery")
    elif schema not in {CANONICAL_SCHEMA, LEGACY_SCHEMA}:
        findings.append("schema_not_wizard_sim_admission_v4_2")
    if payload.get("basename") != basename:
        findings.append("basename_mismatch")
    payload_sim_path = str(payload.get("sim_path") or "")
    if rel_or_abs(root, payload_sim_path).resolve() != rel_or_abs(root, sim_path).resolve():
        findings.append("sim_path_mismatch")
    if payload.get("status") != "queue_ready":
        findings.append("status_not_queue_ready")
    if payload.get("admitted_by") in {"runner", "sim_runner", "queue_claim"}:
        findings.append("admitted_by_not_independent")

    profile = payload.get("formal_sim_profile") or {}
    contract = payload.get("packet_contract")
    if not isinstance(contract, dict):
        findings.append("missing_packet_contract")
        contract = {}

    stage = str(profile.get("stage") or "micro")
    gate_finding = check_stage_gate(root, stage_claim(stage))
    if gate_finding:
        findings.append(gate_finding)

    exp = str(profile.get("expected_result_path") or "")
    canonical = resolve_expected_result(root, basename, exp, expected_result_path)
    if exp and rel_or_abs(root, exp).resolve() != canonical.resolve():
        findings.append("formal_sim_profile_expected_result_path_not_canonical")

    admission_artifact = payload.get("admission_artifact")
    artifact_payload: dict[str, Any] = {}
    if admission_artifact:
        artifact_path = rel_or_abs(root, admission_artifact)
        if artifact_path.exists():
            artifact_payload = _load_json(artifact_path)
            if canonical.exists():
                if "result_path" not in artifact_payload:
                    findings.append("admission_artifact_missing_result_path")
                if "result_sha256" not in artifact_payload:
                    findings.append("admission_artifact_missing_result_sha256")
                elif artifact_payload.get("result_sha256") != sha256(canonical):
                    findings.append("admission_artifact_result_sha256_mismatch")
        else:
            findings.append("admission_artifact_missing")

    controller = [str(item) for item in payload.get("controller_read_artifacts") or []]
    if admission_artifact and str(admission_artifact) not in controller:
        findings.append("controller_read_artifacts_missing_admission_artifact")
    if str(canonical) not in controller:
        findings.append("controller_read_artifacts_missing_expected_result")

    result_payload = _load_json(canonical) if canonical.exists() else {}
    load_bearing = _load_bearing_tool_families(result_payload)
    local_load_bearing = _local_load_bearing_tool_families(result_payload)
    contract_tool = _tool_family(str(contract.get("tool_target") or ""))
    if contract_tool and load_bearing and contract_tool not in load_bearing:
        findings.append("admission_artifact_tool_target_not_load_bearing")

    if "promotion_boundary" not in contract:
        findings.append("packet_contract_missing_promotion_boundary")

    prior = contract.get("prior_function_receipts") or []
    if stage in {"integration_micro", "qit", "engine", "bridge", "axis"}:
        if prior and not all(str(item).startswith("system_v4/probes/a2_state/sim_results/") and str(item).endswith("_results.json") for item in prior):
            findings.append("packet_contract_parent_receipts_not_exact_result_paths")
        for item in prior:
            parent = rel_or_abs(root, item)
            if not parent.exists():
                findings.append("packet_contract_parent_receipt_missing")
                continue
            expected_hash = (contract.get("parent_receipt_sha256") or {}).get(item)
            if expected_hash and expected_hash != sha256(parent):
                findings.append("packet_contract_parent_receipt_hash_mismatch")
            parent_payload = _load_json(parent)
            if parent_payload.get("classification") != "canonical":
                findings.append("packet_contract_parent_receipt_not_canonical")

    tool = _tool_family(str(contract.get("tool_target") or profile.get("exact_tool_or_function") or ""))
    claim_text = " ".join(
        [
            basename,
            str(profile.get("claim", "")),
            *[str(contract.get(k, "")) for k in ("claim_ceiling", "micro_claim", "integration_question", "type")],
        ]
    ).lower()
    hidden_nonclassical = _has_hidden_nonclassical_signal(root, sim_path, result_payload)
    result_execution_kind = _result_execution_kind(result_payload)
    if (any(token in claim_text for token in ("qit", "engine", "nonclassical")) or hidden_nonclassical) and tool and tool not in NONCLASSICAL_LOAD_BEARING_TOOLS:
        findings.append("nonclassical_suitable_load_bearing_tool_missing")
    strict_nonclassical = (
        result_execution_kind == "nonclassical"
        or "nonclassical" in claim_text
        or hidden_nonclassical
    )
    if strict_nonclassical and "pytorch" not in local_load_bearing:
        findings.append("nonclassical_requires_local_load_bearing_pytorch")
    if hidden_nonclassical and result_payload.get("classification") == "classical_baseline":
        baseline_ceiling = " ".join(
            str(contract.get(k, "")) for k in ("nonclassical_claim_ceiling", "claim_ceiling", "promotion_boundary")
        ).lower()
        if "baseline_only" not in baseline_ceiling:
            findings.append("nonclassical_baseline_missing_baseline_only_ceiling")
    return sorted(set(findings))


def admission_path(root: Path, basename: str) -> Path:
    return root / "system_v5" / "ops" / "wizard_admissions" / f"{basename}.json"


def load_and_validate(
    *,
    root: Path,
    basename: str,
    sim_path: str,
    admission_file: str | None = None,
    expected_result_path: str | Path | None = None,
    allow_legacy_v4_1: bool = False,
) -> dict[str, Any]:
    path = Path(admission_file) if admission_file else admission_path(root, basename)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        return {"ok": False, "path": str(path), "findings": ["admission_missing"]}
    payload = _load_json(path)
    findings = validate_admission(
        payload,
        root=root,
        basename=basename,
        sim_path=sim_path,
        expected_result_path=expected_result_path,
        allow_legacy_v4_1=allow_legacy_v4_1,
    )
    return {"ok": not findings, "path": str(path), "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--basename", required=True)
    parser.add_argument("--sim-path", required=True)
    parser.add_argument("--admission-file")
    parser.add_argument("--expected-result-path")
    parser.add_argument(
        "--allow-legacy-v4-1",
        action="store_true",
        help="Recovery-only: allow legacy wizard_sim_admission_v4_1 packets instead of the live v4.2 schema.",
    )
    parser.add_argument(
        "--path-only",
        action="store_true",
        help="On successful validation, print only the resolved admission path.",
    )
    args = parser.parse_args()
    report = load_and_validate(
        root=Path(args.repo_root),
        basename=args.basename,
        sim_path=args.sim_path,
        admission_file=args.admission_file,
        expected_result_path=args.expected_result_path,
        allow_legacy_v4_1=args.allow_legacy_v4_1,
    )
    if args.path_only and report.get("ok"):
        print(report["path"])
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

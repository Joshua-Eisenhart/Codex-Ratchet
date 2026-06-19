#!/usr/bin/env python3
"""Real-object program-binding gate for Codex Ratchet sims.

Ceiling: this gate checks only membership, location, and lineage binding. It
does NOT prove execution, source/result freshness, runner identity, or notary
authenticity; those need the separate executor/notary layer.

Normal output is JSON: {"ok": bool, "findings": [...]}.
Exit 0 iff the checked target is bound to the actual lego program.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = (
    ROOT / "system_v4" / "probes" / "a2_state" / "sim_results" / "actual_lego_registry.json"
)
CANONICAL_TREES = (
    ROOT / "system_v5" / "legos",
    ROOT / "system_v4" / "probes",
    ROOT / "system_v7" / "sims",
)
TOY_ORDER_SENSITIVITY = (
    ROOT
    / "system_v7"
    / "sims"
    / "order_sensitivity_noncommutation_floor_v0"
    / "order_sensitivity_scratch_diagnostic.py"
)
TMP_FAKE = Path("/tmp/fake_obj.py")

ID_KEYS = {
    "object_id",
    "object_ids",
    "lego_id",
    "lego_ids",
    "primary_lego_id",
    "primary_lego_ids",
    "sim_id",
    "name",
}
PATH_KEYS = {
    "canonical_sim_path",
    "sim_path",
    "source_path",
    "path",
    "result_path",
    "canonical_path",
}
PARENT_KEYS = {
    "parents",
    "parent",
    "parent_lego_id",
    "parent_lego_ids",
    "parent_legos",
    "prior_function_receipts",
    "prior_receipts",
}
STAGE_KEYS = {
    "stage",
    "sim_stage",
    "claim_stage",
    "requested_claim",
    "classification",
    "sim_execution_kind",
    "tier",
}
FLOOR_STAGES = {
    "tool_micro",
    "tool_function_micro",
    "tool_integration_micro",
    "tool_lego_fit",
    "tool_lego_fit_probe",
}
FLOOR_CLASSIFICATIONS = {
    "tool_micro",
    "tool_function_micro",
    "tool_lego_fit_probe",
}
FLOOR_LEGO_TYPES = {
    "root/admission",
    "carrier/admission",
}


@dataclass(frozen=True)
class RegistryMatch:
    row: dict[str, Any]
    via: str
    value: str


@dataclass
class TargetMetadata:
    ids: set[str]
    paths: set[str]
    parents: list[Any]
    stages: set[str]


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def resolve_input(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve(strict=False)


def rel_or_abs(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def canonical_location(path: Path) -> bool:
    return any(_is_relative_to(path, tree.resolve(strict=False)) for tree in CANONICAL_TREES)


def finding(kind: str, path: Path | None = None, detail: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"kind": kind}
    if path is not None:
        out["path"] = rel_or_abs(path)
    if detail:
        out["detail"] = detail
    return out


def load_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("actual_lego_registry rows must be a list")
    return [row for row in rows if isinstance(row, dict)]


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().strip("`").strip()
    return text or None


def path_tokens(value: Any) -> set[str]:
    text = normalize_text(value)
    if not text:
        return set()
    raw = Path(text)
    if raw.is_absolute():
        resolved = raw.resolve(strict=False)
        tokens = {rel_or_abs(resolved), resolved.as_posix()}
    else:
        normalized = raw.as_posix().lstrip("./")
        tokens = {normalized}
        if "/" not in normalized:
            tokens.add(f"system_v4/probes/{normalized}")
            tokens.add(f"system_v4/probes/a2_state/sim_results/{normalized}")
    tokens.add(raw.name)
    if raw.suffix:
        tokens.add(raw.stem)
    return {token for token in tokens if token}


def collect_string_values(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        text = normalize_text(value)
        if text:
            out.append(text)
    elif isinstance(value, dict):
        for key in (*ID_KEYS, *PATH_KEYS):
            if key in value:
                out.extend(collect_string_values(value[key]))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            out.extend(collect_string_values(item))
    return out


class RegistryIndex:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.by_id: dict[str, list[dict[str, Any]]] = {}
        self.by_path: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            for key in ("lego_id", "object_id", "sim_id"):
                text = normalize_text(row.get(key))
                if text:
                    self.by_id.setdefault(text, []).append(row)
            for key in (
                "canonical_sim_path",
                "sim_path",
                "machine_best_probe",
                "machine_suggested_first_probe",
                "suggested_first_probe",
                "best_existing_result",
                "machine_best_result",
                "machine_best_existing_result",
                "result_path",
            ):
                for token in path_tokens(row.get(key)):
                    self.by_path.setdefault(token, []).append(row)

    def match_ids(self, ids: set[str]) -> list[RegistryMatch]:
        matches: list[RegistryMatch] = []
        for object_id in sorted(ids):
            for row in self.by_id.get(object_id, []):
                matches.append(RegistryMatch(row=row, via="object_id", value=object_id))
        return matches

    def match_paths(self, paths: set[str]) -> list[RegistryMatch]:
        matches: list[RegistryMatch] = []
        for token in sorted(paths):
            for row in self.by_path.get(token, []):
                matches.append(RegistryMatch(row=row, via="path", value=token))
        return matches


def literal_assignments(path: Path) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".py":
        return {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return {}
    values: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            name_lower = name.lower()
            if (
                name_lower not in ID_KEYS
                and name_lower not in PATH_KEYS
                and name_lower not in PARENT_KEYS
                and name_lower not in STAGE_KEYS
            ):
                continue
            try:
                values[name_lower] = ast.literal_eval(node.value)
            except Exception:
                continue
    return values


def read_result(path: Path) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".json":
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def merge_metadata_from_dict(meta: TargetMetadata, data: dict[str, Any]) -> None:
    for key in ID_KEYS:
        if key in data:
            meta.ids.update(collect_string_values(data[key]))
    for key in PATH_KEYS:
        if key in data:
            for text in collect_string_values(data[key]):
                meta.paths.update(path_tokens(text))
    for key in PARENT_KEYS:
        if key in data:
            value = data[key]
            if isinstance(value, list):
                meta.parents.extend(value)
            elif value not in (None, "", {}):
                meta.parents.append(value)
    for key in STAGE_KEYS:
        if key in data:
            meta.stages.update(collect_string_values(data[key]))
    lineage = data.get("lineage")
    if isinstance(lineage, dict):
        merge_metadata_from_dict(meta, lineage)


def collect_metadata(sim_path: Path | None, result_path: Path | None) -> TargetMetadata:
    meta = TargetMetadata(ids=set(), paths=set(), parents=[], stages=set())
    for path in (sim_path, result_path):
        if path is None:
            continue
        meta.paths.update(path_tokens(rel_or_abs(path)))
        meta.paths.update(path_tokens(path.name))
        if path.suffix == ".py":
            merge_metadata_from_dict(meta, literal_assignments(path))
        elif path.suffix == ".json":
            merge_metadata_from_dict(meta, read_result(path))
    return meta


def unique_matches(matches: list[RegistryMatch]) -> list[RegistryMatch]:
    seen: set[tuple[str, str]] = set()
    out: list[RegistryMatch] = []
    for match in matches:
        row_id = str(match.row.get("lego_id", id(match.row)))
        key = (row_id, match.via)
        if key in seen:
            continue
        seen.add(key)
        out.append(match)
    return out


def resolve_membership(index: RegistryIndex, meta: TargetMetadata) -> list[RegistryMatch]:
    id_matches = index.match_ids(meta.ids)
    if id_matches:
        return unique_matches(id_matches)
    return unique_matches(index.match_paths(meta.paths))


def parent_resolves(index: RegistryIndex, parent: Any) -> bool:
    tokens = collect_string_values(parent)
    ids = {token for token in tokens if "/" not in token and not token.endswith((".py", ".json"))}
    paths: set[str] = set()
    for token in tokens:
        paths.update(path_tokens(token))
    return bool(index.match_ids(ids) or index.match_paths(paths))


def is_floor_row(row: dict[str, Any], stages: set[str]) -> bool:
    row_type = normalize_text(row.get("lego_type")) or ""
    row_type = row_type.lower()
    if row_type in FLOOR_LEGO_TYPES:
        return True
    if "tool" in row_type and "micro" in row_type:
        return True
    normalized_stages = {stage.lower() for stage in stages}
    if normalized_stages & FLOOR_STAGES:
        return True
    if normalized_stages & FLOOR_CLASSIFICATIONS:
        return True
    return False


def requires_lineage(matches: list[RegistryMatch], meta: TargetMetadata) -> bool:
    if not matches:
        return False
    return not any(is_floor_row(match.row, meta.stages) for match in matches)


def check_lineage(index: RegistryIndex, matches: list[RegistryMatch], meta: TargetMetadata) -> list[dict[str, Any]]:
    if not requires_lineage(matches, meta):
        return []
    parents = list(meta.parents)
    for match in matches:
        for key in PARENT_KEYS:
            value = match.row.get(key)
            if isinstance(value, list):
                parents.extend(value)
            elif value not in (None, "", {}):
                parents.append(value)
    if not parents:
        joined = ", ".join(sorted({str(match.row.get("lego_id")) for match in matches}))
        return [
            finding(
                "lineage_empty_or_off_program",
                detail=f"registry member(s) above floor have no prior_function_receipts/parents: {joined}",
            )
        ]
    off_program = [parent for parent in parents if not parent_resolves(index, parent)]
    if off_program:
        return [
            finding(
                "lineage_empty_or_off_program",
                detail=f"unresolved parent(s): {off_program}",
            )
        ]
    return []


def evaluate(
    sim_path_text: str | None,
    result_path_text: str | None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> tuple[dict[str, Any], int]:
    sim_path = resolve_input(sim_path_text) if sim_path_text else None
    result_path = resolve_input(result_path_text) if result_path_text else None
    findings: list[dict[str, Any]] = []
    targets = [path for path in (sim_path, result_path) if path is not None]

    if not targets:
        findings.append(finding("missing_input", detail="provide --sim-path and/or --result-path"))
        return {"ok": False, "findings": findings}, 1

    for path in targets:
        if not canonical_location(path):
            findings.append(
                finding(
                    "off_canonical_location",
                    path=path,
                    detail="path is outside system_v5/legos, system_v4/probes, and system_v7/sims",
                )
            )

    try:
        rows = load_registry(registry_path)
    except Exception as exc:
        findings.append(finding("registry_unavailable", path=registry_path, detail=str(exc)))
        return {"ok": False, "findings": findings}, 1

    index = RegistryIndex(rows)
    meta = collect_metadata(sim_path, result_path)
    matches = resolve_membership(index, meta)
    if not matches:
        primary_path = sim_path or result_path
        findings.append(
            finding(
                "not_registry_member",
                path=primary_path,
                detail="no declared object id or canonical sim/result path resolved to actual_lego_registry.json",
            )
        )
    else:
        findings.extend(check_lineage(index, matches, meta))

    ok = not findings
    return {"ok": ok, "findings": findings}, 0 if ok else 1


def find_real_registry_member(registry_path: Path) -> Path:
    rows = load_registry(registry_path)
    candidate_keys = (
        "canonical_sim_path",
        "sim_path",
        "machine_best_probe",
        "machine_suggested_first_probe",
        "suggested_first_probe",
    )
    for row in rows:
        for key in candidate_keys:
            value = normalize_text(row.get(key))
            if not value:
                continue
            raw = Path(value)
            candidates = [raw] if raw.is_absolute() else [ROOT / value]
            if "/" not in value:
                candidates.append(ROOT / "system_v4" / "probes" / value)
            for candidate in candidates:
                resolved = candidate.resolve(strict=False)
                if resolved.exists() and canonical_location(resolved):
                    return resolved
    raise RuntimeError("no registry-member canonical sim path exists")


def finding_kinds(payload: dict[str, Any]) -> set[str]:
    return {str(item.get("kind")) for item in payload.get("findings", [])}


def run_self_test(registry_path: Path) -> tuple[dict[str, Any], int]:
    real_path = find_real_registry_member(registry_path)
    specs = (
        ("real_registry_member", real_path),
        ("toy_order_sensitivity", TOY_ORDER_SENSITIVITY),
        ("tmp_fake", TMP_FAKE),
    )
    cases: list[dict[str, Any]] = []
    for label, path in specs:
        payload, exit_code = evaluate(path.as_posix(), None, registry_path)
        cases.append(
            {
                "label": label,
                "path": rel_or_abs(path.resolve(strict=False)),
                "ok": payload["ok"],
                "exit_code": exit_code,
                "findings": payload["findings"],
            }
        )

    by_label = {case["label"]: case for case in cases}
    real_ok = by_label["real_registry_member"]["ok"] is True
    toy_kinds = finding_kinds(by_label["toy_order_sensitivity"])
    fake_kinds = finding_kinds(by_label["tmp_fake"])
    toy_ok = (
        by_label["toy_order_sensitivity"]["ok"] is False
        and "not_registry_member" in toy_kinds
        and "off_canonical_location" not in toy_kinds
    )
    fake_ok = (
        by_label["tmp_fake"]["ok"] is False
        and {"off_canonical_location", "not_registry_member"} <= fake_kinds
    )
    ok = real_ok and toy_ok and fake_ok
    return {"ok": ok, "cases": cases}, 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim-path", help="Sim source path to bind")
    parser.add_argument("--result-path", help="Result JSON path to bind")
    parser.add_argument(
        "--registry-path",
        default=DEFAULT_REGISTRY_PATH.as_posix(),
        help="Path to actual_lego_registry.json",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run real/toy/tmp adversarial discrimination self-test",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry_path = resolve_input(args.registry_path)
    if args.self_test:
        payload, exit_code = run_self_test(registry_path)
    else:
        payload, exit_code = evaluate(args.sim_path, args.result_path, registry_path)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail closed when scout evidence is narrated as layer completion.

This validator is intentionally narrow. It does not prove a layer is complete.
It blocks the known failure mode where `formal_scout` receipts, green reruns, or
tool manifests get described as full layer, stack, G-structure, Axis0, or final
manifold completion.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATUS = ROOT / "system_v5" / "ops" / "formal_scouts" / (
    "layer_g_structure_entropy_individual_sim_status_20260528.json"
)

SCOUT_CLASSIFICATIONS = {
    "diagnostic_only",
    "formal_scout",
    "formal_scout_status",
    "tool_lego_fit_probe",
}

DOWNSTREAM_CONSUMERS = {
    "axis0",
    "fep",
    "fep/holodeck",
    "final_manifold_admission",
    "flux",
    "holodeck/fep",
    "layer_embedding_in_selected_g_structure",
    "layer_stacking",
    "official_g_structure_selection",
    "peps3d_closure_theorem",
    "physics/gravity",
    "stacking",
    "xi/phi0",
}

TERMINAL_TRUE_KEYS = {
    "campaign_terminal",
    "downstream_admission_terminal",
    "final_manifold_admission",
    "final_manifold_admitted",
    "layer_embedding_admitted",
    "layer_stacking_unlocked",
    "official_g_structure_selected",
    "stacking_unlocked",
}

ADMISSION_ARRAY_KEYS = {
    "admitted_layers",
    "admitted_rows",
    "admitted_g_structures",
    "layers_admitted",
    "full_layers_admitted",
    "g_structures_admitted",
    "completed_layers",
    "parent_complete_layers",
}

NO_CONTINUATION_FALSE_KEYS = {
    "continuation_required",
    "downstream_continuation_required",
    "next_packet_required",
}

FULL_LAYER_CLASSIFICATIONS = {
    "canonical",
    "admitted_full_layer",
    "full_layer_completion",
    "parent_complete",
}

REQUIRED_FULL_TOOLS = {
    "clifford",
    "cotengra",
    "cvc5",
    "gudhi",
    "pyg",
    "quimb",
    "rustworkx",
    "sympy",
    "toponetx",
    "torch",
    "xgi",
    "z3",
}

REQUIRED_CARRIER_VIEWS = {"mps", "peps2d", "peps3d", "pyg"}
REQUIRED_SITE_COUNTS = {8, 16, 32, 64}
REQUIRED_ENTROPY_TERMS = (
    "von_neumann",
    "mutual_information",
    "conditional_entropy",
    "coherent_information",
    "log_negativity",
)
CLAIM_TEXT_KEYS = {
    "allowed_claims",
    "claim",
    "claim_text",
    "claims",
    "claim_ceiling",
    "completion_claim",
    "completion_status",
    "promotion_status",
    "result_summary",
    "status",
    "summary",
}
TOOL_ALIASES = {"pytorch": "torch"}
SELF_PROMOTION_TRUE_KEYS = TERMINAL_TRUE_KEYS | {
    "axis0_unlocked",
    "fep_unlocked",
    "flux_unlocked",
    "layer_admitted",
    "layer_complete",
    "manifold_admitted",
    "parent_complete",
    "physics_unlocked",
    "xi_phi0_unlocked",
}
TRUTHY_CLAIM_VALUES = {"1", "yes", "true", "done", "complete", "completed", "admitted"}

COMPLETION_PATTERN = re.compile(
    r"\b("
    r"admitted|admission|"
    r"accepted|approved|canonized|cleared|"
    r"closed[-\s]?out|"
    r"complete(?:d|ly)?|"
    r"done|finished|proven|"
    r"end[-\s]?state|"
    r"final\s+form|"
    r"finalized|greenlit|"
    r"fully\s+sim(?:ed|med|ulated)?|"
    r"full\s+(?:proper\s+)?(?:layer\s+)?sim|"
    r"green\s+across|"
    r"graduated|"
    r"qualified|"
    r"landed|"
    r"parent[-\s]?complete|"
    r"promoted|"
    r"ratified|"
    r"ready[-\s]?to[-\s]?merge|"
    r"sealed|"
    r"settled|"
    r"shipped|"
    r"signed[-\s]?off|"
    r"wrapped|"
    r"merged[-\s]?to[-\s]?canonical|"
    r"stack[-\s]?ready|"
    r"unlocked|"
    r"official\s+g[-\s]?structure\s+selected|"
    r"true\s+g[-\s]?structure\s+(?:rows\s+)?completed|"
    r"validated\s+as\s+(?:full|complete)"
    r")\b",
    re.IGNORECASE,
)

SUBJECT_PATTERN = re.compile(
    r"\b("
    r"l[0-9]\b|layer|layers|weyl|hopf|terrain|operator|substage|entropy|"
    r"groupoid|g[-\s]?structure|manifold|axis0|xi|phi0|flux|fep|physics|"
    r"peps3d|spinor|spinor[-\s]?network|carrier|cl6|clifford|engine|bridge|"
    r"stack|stacking"
    r")\b",
    re.IGNORECASE,
)

NEGATION_MARKERS = (
    " not ",
    " no ",
    " zero ",
    " false",
    "blocked",
    "remain locked",
    "remains locked",
    "not full",
    "not complete",
    "not completed",
    "not yet",
    "does not admit",
    "doesn't admit",
    "do not treat",
    "must not be reported",
    "bounded formal-scout",
    "bounded formal scout",
    "formal scout only",
    "formal-scout coverage",
    "promotion_allowed=false",
    "promotion_allowed = false",
)

ZERO_VALUE_PATTERN = re.compile(r"[:=]\s*(?:0|false)\b", re.IGNORECASE)
FUTURE_WORK_PATTERN = re.compile(
    r"^\s*(?:"
    r"finish|deepen|finish/deepen|build|write|run|repair|validate|test|"
    r"create|add|lift"
    r")\b|"
    r"\b(?:until\s+it\s+becomes|next\s+work|must\s+be|should\s+be|needs?\s+to)\b",
    re.IGNORECASE,
)
CLAIM_SEGMENT_SPLIT_PATTERN = re.compile(
    r"(?:[.;]\s+|\b(?:but|however|yet|actually)\b)", re.IGNORECASE
)


@dataclass
class Evidence:
    path: Path
    data: Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def iter_json_strings(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_json_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_strings(child)
    elif isinstance(value, str):
        yield value


def iter_claim_value_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from iter_claim_value_strings(child)


def iter_claim_field_strings(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).strip().lower() in CLAIM_TEXT_KEYS:
                yield from iter_claim_value_strings(child)
            if isinstance(child, (dict, list)):
                yield from iter_claim_field_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_claim_field_strings(child)


def find_numeric_keys(data: Any, key: str) -> list[float]:
    values: list[float] = []
    for obj in walk_json(data):
        if key in obj:
            try:
                values.append(float(obj[key]))
            except (TypeError, ValueError):
                pass
    return values


def find_bool_keys(data: Any, key: str) -> list[bool]:
    values: list[bool] = []
    for obj in walk_json(data):
        if isinstance(obj, dict) and key in obj and isinstance(obj[key], bool):
            values.append(obj[key])
    return values


def find_nonempty_list_keys(data: Any, key: str) -> list[list[Any]]:
    values: list[list[Any]] = []
    for obj in walk_json(data):
        if isinstance(obj, dict) and key in obj and isinstance(obj[key], list) and obj[key]:
            values.append(obj[key])
    return values


def find_values(data: Any, key: str) -> list[Any]:
    values: list[Any] = []
    for obj in walk_json(data):
        if isinstance(obj, dict) and key in obj:
            values.append(obj[key])
    return values


def normalized_key_text(key: Any) -> str:
    return re.sub(r"[_\-]+", " ", str(key)).strip()


def value_is_truthy_claim(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        return value.strip().lower() in TRUTHY_CLAIM_VALUES
    return False


def key_self_promotion_claims(data: Any) -> list[str]:
    claims: list[str] = []
    for obj in walk_json(data):
        if not isinstance(obj, dict):
            continue
        for key, value in obj.items():
            text = normalized_key_text(key)
            value_text = str(value)
            key_claim = value_is_truthy_claim(value) and line_has_completion_claim(text)
            key_value_claim = (
                value_is_truthy_claim(value)
                and bool(SUBJECT_PATTERN.search(text))
                and bool(COMPLETION_PATTERN.search(value_text))
            )
            if key_claim or key_value_claim:
                claims.append(f"{key}={value}")
    return claims


def status_receipt_paths(status: Evidence) -> list[Path]:
    data = status.data
    if not isinstance(data, dict):
        return []
    paths: list[Path] = []
    layers = data.get("layers")
    if isinstance(layers, dict):
        for row in layers.values():
            if isinstance(row, dict):
                for maybe_path in row.values():
                    if isinstance(maybe_path, str) and maybe_path.endswith(".json"):
                        path = Path(maybe_path)
                        paths.append(path if path.is_absolute() else ROOT / path)
    return paths


def evidence_is_unpromoted(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    classifications = [
        str(obj.get("classification", "")).strip().lower()
        for obj in walk_json(data)
        if isinstance(obj, dict) and "classification" in obj
    ]
    if any(cls in SCOUT_CLASSIFICATIONS for cls in classifications):
        return True
    for obj in walk_json(data):
        if not isinstance(obj, dict):
            continue
        if obj.get("promotion_allowed") is False:
            return True
        ceiling = str(obj.get("claim_ceiling", "")).lower()
        if any(
            marker in ceiling
            for marker in (
                "formal scout only",
                "bounded formal-scout",
                "does not admit",
                "no stacking",
                "no final manifold",
                "remain locked",
                "remains locked",
            )
        ):
            return True
        consumers = {
            str(item).strip().lower()
            for key in ("blocked_consumers", "downstream_blocks")
            for item in as_list(obj.get(key))
        }
        if consumers & DOWNSTREAM_CONSUMERS:
            return True
    return False


def line_is_negated(line: str) -> bool:
    padded = f" {line.lower()} "
    if any(marker in padded for marker in (" not just ", " not only ", " not merely ")):
        return False
    return any(marker in padded for marker in NEGATION_MARKERS) or bool(
        ZERO_VALUE_PATTERN.search(line)
    )


def raw_completion_claim(line: str, subject_context: bool = False) -> bool:
    return bool(COMPLETION_PATTERN.search(line) and (subject_context or SUBJECT_PATTERN.search(line)))


def line_has_completion_claim(line: str) -> bool:
    if FUTURE_WORK_PATTERN.search(line):
        return False
    subject_context = bool(SUBJECT_PATTERN.search(line))
    for segment in CLAIM_SEGMENT_SPLIT_PATTERN.split(line):
        segment = segment.strip()
        if segment and raw_completion_claim(segment, subject_context) and not line_is_negated(segment):
            return True
    if line_is_negated(line):
        return False
    return raw_completion_claim(line)


def claim_chunks(text: str):
    candidate_lines: list[tuple[int, str]] = []
    in_fence = False
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith(">"):
            continue
        line = re.sub(r"`[^`]*`", "", line)
        candidate_lines.append((index, line))
        yield index, line
    for (first_index, first_line), (second_index, second_line) in zip(
        candidate_lines, candidate_lines[1:]
    ):
        if second_index != first_index + 1:
            continue
        if first_line.rstrip().endswith((".", "!", "?")):
            continue
        if not re.match(
            r"^\s*(?:(?:is|are|was|were|has|have|had)\s+)?"
            r"(?:(?:now|actually)\s+)?(?:been\s+)?"
            r"(?:accepted|admitted|approved|canonized|cleared|complete|completed|"
            r"finalized|fully|full|greenlit|parent[-\s]?complete|ratified|"
            r"stack[-\s]?ready|unlocked|validated)",
            second_line,
            re.IGNORECASE,
        ):
            continue
        joined = " ".join(part.strip() for part in (first_line, second_line))
        yield first_index, joined


def completion_claim_strings(data: Any) -> list[str]:
    strings = list(iter_claim_field_strings(data))
    strings.extend(iter_json_strings(data))
    seen: set[str] = set()
    claims: list[str] = []
    for text in strings:
        if text in seen:
            continue
        seen.add(text)
        if line_has_completion_claim(text):
            claims.append(text)
    return claims


def load_bearing_tools(data: Any) -> set[str]:
    tools: set[str] = set()
    for obj in walk_json(data):
        if not isinstance(obj, dict):
            continue
        depth = obj.get("TOOL_INTEGRATION_DEPTH")
        if isinstance(depth, dict):
            for name, role in depth.items():
                if str(role).strip().lower() == "load_bearing":
                    normalized = str(name).strip().lower()
                    tools.add(TOOL_ALIASES.get(normalized, normalized))
        manifest = obj.get("TOOL_MANIFEST")
        if isinstance(manifest, dict):
            for name, row in manifest.items():
                if isinstance(row, dict):
                    role = str(row.get("role", "")).strip().lower()
                    if row.get("used") is True and role == "load_bearing":
                        normalized = str(name).strip().lower()
                        tools.add(TOOL_ALIASES.get(normalized, normalized))
    return tools


def full_layer_contract_missing(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["json_object"]

    missing: list[str] = []
    json_text = json.dumps(data, sort_keys=True).lower()
    classifications = {
        str(obj.get("classification", "")).strip().lower()
        for obj in walk_json(data)
        if isinstance(obj, dict) and "classification" in obj
    }

    if classifications & SCOUT_CLASSIFICATIONS:
        missing.append("classification_not_scout")
    if not (classifications & FULL_LAYER_CLASSIFICATIONS):
        missing.append("full_layer_classification")
    if not any(obj.get("promotion_allowed") is True for obj in walk_json(data) if isinstance(obj, dict)):
        missing.append("promotion_allowed_true")
    if not any(isinstance(value, str) and value.strip() for value in find_values(data, "finite_map")):
        missing.append("finite_map")
    if not any(isinstance(value, str) and value.strip() for value in find_values(data, "domain")):
        missing.append("domain")
    if not any(
        isinstance(value, str) and value.strip()
        for value in find_values(data, "codomain_or_output")
    ):
        missing.append("codomain_or_output")
    if "f01" not in json_text or "n01" not in json_text:
        missing.append("F01_N01_witnesses")
    if "torch" not in json_text or "spinor" not in json_text:
        missing.append("torch_native_spinor_state")
    if "peps3d" not in json_text:
        missing.append("PEPS3D_anchor")
    if not REQUIRED_CARRIER_VIEWS <= set(re.findall(r"\b(?:mps|peps2d|peps3d|pyg)\b", json_text)):
        missing.append("MPS_PEPS2D_PEPS3D_PyG_views")
    site_counts = {
        int(value)
        for obj in walk_json(data)
        if isinstance(obj, dict)
        for value in as_list(obj.get("finite_site_counts")) + as_list(obj.get("site_counts"))
        if isinstance(value, int)
    }
    if not REQUIRED_SITE_COUNTS <= site_counts:
        missing.append("scale_8_16_32_64")
    missing_tools = REQUIRED_FULL_TOOLS - load_bearing_tools(data)
    if missing_tools:
        missing.append(f"load_bearing_tools:{','.join(sorted(missing_tools))}")
    if not all(term in json_text for term in REQUIRED_ENTROPY_TERMS):
        missing.append("qit_entropy_family")
    non_vacuous_ablations = [
        obj
        for obj in walk_json(data)
        if isinstance(obj, dict)
        and obj.get("non_vacuous") is True
        and str(obj.get("claim_delta", "")).strip()
    ]
    if len(non_vacuous_ablations) < 5:
        missing.append("five_non_vacuous_ablations")
    return missing


def collect_claim_violations(claim_files: list[Path], unpromoted: list[Evidence]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for path in claim_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            violations.append(
                {
                    "code": "claim.empty_claim_file",
                    "path": str(path),
                    "line": 1,
                    "text": "",
                    "evidence_paths": [],
                }
            )
            continue
        for index, line in claim_chunks(text):
            if not line_has_completion_claim(line):
                continue
            if unpromoted:
                violations.append(
                    {
                        "code": "claim.promotes_unpromoted_evidence",
                        "path": str(path),
                        "line": index,
                        "text": line.strip(),
                        "evidence_paths": [str(item.path) for item in unpromoted[:8]],
                    }
                )
            else:
                violations.append(
                    {
                        "code": "claim.completion_without_completion_evidence",
                        "path": str(path),
                        "line": index,
                        "text": line.strip(),
                        "evidence_paths": [],
                    }
                )
    return violations


def collect_self_promotion_violations(evidence: list[Evidence]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for item in evidence:
        self_claims = completion_claim_strings(item.data)
        key_claims = key_self_promotion_claims(item.data)
        numeric_completion = any(
            find_numeric_keys(item.data, key)
            and any(value > 0 for value in find_numeric_keys(item.data, key))
            for key in ("fully_complete_layer_rows", "true_g_structure_rows_completed")
        )
        boolean_completion = any(
            values and any(values)
            for values in (
                find_bool_keys(item.data, key) for key in SELF_PROMOTION_TRUE_KEYS
            )
        )
        if not self_claims and not key_claims and not numeric_completion and not boolean_completion:
            continue
        missing = full_layer_contract_missing(item.data)
        if missing:
            violations.append(
                {
                    "code": "evidence.self_promotes_without_full_contract",
                    "path": str(item.path),
                    "claim_strings": [*self_claims, *key_claims][:8],
                    "numeric_completion_claim": numeric_completion,
                    "boolean_completion_claim": boolean_completion,
                    "missing_contract": missing,
                }
            )
    return violations


def collect_status_violations(statuses: list[Evidence], all_evidence: list[Evidence]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    unpromoted = [item for item in all_evidence if evidence_is_unpromoted(item.data)]
    for status in statuses:
        complete_rows = find_numeric_keys(status.data, "fully_complete_layer_rows")
        if any(value > 0 for value in complete_rows) and unpromoted:
            violations.append(
                {
                    "code": "status.complete_rows_conflict_with_scouts",
                    "path": str(status.path),
                    "detail": "fully_complete_layer_rows is positive while cited evidence remains unpromoted/scout evidence",
                    "evidence_paths": [str(item.path) for item in unpromoted[:8]],
                }
            )
        g_rows = find_numeric_keys(status.data, "true_g_structure_rows_completed")
        if any(value > 0 for value in g_rows) and unpromoted:
            violations.append(
                {
                    "code": "status.g_structure_rows_conflict_with_scouts",
                    "path": str(status.path),
                    "detail": "true_g_structure_rows_completed is positive while cited evidence remains unpromoted/scout evidence",
                    "evidence_paths": [str(item.path) for item in unpromoted[:8]],
                }
            )
        for key in TERMINAL_TRUE_KEYS:
            values = find_bool_keys(status.data, key)
            if any(values) and unpromoted:
                violations.append(
                    {
                        "code": "status.terminal_campaign_conflicts_with_scouts",
                        "path": str(status.path),
                        "detail": f"{key} is true while cited evidence remains unpromoted/scout evidence",
                        "evidence_paths": [str(item.path) for item in unpromoted[:8]],
                    }
                )
        for key in NO_CONTINUATION_FALSE_KEYS:
            values = find_bool_keys(status.data, key)
            if values and any(value is False for value in values) and unpromoted:
                violations.append(
                    {
                        "code": "status.no_continuation_conflicts_with_scouts",
                        "path": str(status.path),
                        "detail": f"{key} is false while cited evidence remains unpromoted/scout evidence",
                        "evidence_paths": [str(item.path) for item in unpromoted[:8]],
                    }
                )
        for key in ADMISSION_ARRAY_KEYS:
            values = find_nonempty_list_keys(status.data, key)
            if values and unpromoted:
                violations.append(
                    {
                        "code": "status.admission_array_conflicts_with_scouts",
                        "path": str(status.path),
                        "detail": f"{key} is non-empty while cited evidence remains unpromoted/scout evidence",
                        "evidence_paths": [str(item.path) for item in unpromoted[:8]],
                    }
                )
    return violations


def read_evidence(paths: list[Path]) -> tuple[list[Evidence], list[dict[str, Any]]]:
    evidence: list[Evidence] = []
    errors: list[dict[str, Any]] = []
    for path in paths:
        try:
            evidence.append(Evidence(path=path, data=load_json(path)))
        except Exception as exc:  # noqa: BLE001 - validator reports file failures as gate errors.
            errors.append({"code": "evidence.read_failed", "path": str(path), "detail": str(exc)})
    return evidence, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-file", action="append", type=Path, default=[])
    parser.add_argument("--evidence", action="append", type=Path, default=[])
    parser.add_argument("--status", action="append", type=Path, default=[])
    parser.add_argument("--resolve-status-receipts", action="store_true")
    parser.add_argument(
        "--use-default-status",
        action="store_true",
        help="include the current layer/G-structure status file if present",
    )
    parser.add_argument(
        "--require-status",
        action="store_true",
        help="fail if no status JSON could be loaded",
    )
    args = parser.parse_args(argv)

    no_sources_requested = not (
        args.claim_file or args.evidence or args.status or args.use_default_status
    )
    status_paths = list(args.status)
    if args.use_default_status and DEFAULT_STATUS.exists():
        status_paths.append(DEFAULT_STATUS)

    statuses, status_errors = read_evidence(status_paths)
    if no_sources_requested:
        status_errors.append(
            {
                "code": "input.no_sources",
                "path": "",
                "detail": "at least one claim file, evidence JSON, or status JSON is required",
            }
        )
    if args.require_status and not statuses:
        status_errors.append(
            {
                "code": "status.required_status_missing",
                "path": str(DEFAULT_STATUS if args.use_default_status else status_paths[0] if status_paths else ""),
                "detail": "required layer/G-structure status JSON was not loaded",
            }
        )
    evidence_paths = list(args.evidence)
    if args.resolve_status_receipts:
        for status in statuses:
            evidence_paths.extend(status_receipt_paths(status))

    evidence, evidence_errors = read_evidence(evidence_paths)
    all_evidence = [*statuses, *evidence]
    unpromoted = [item for item in all_evidence if evidence_is_unpromoted(item.data)]

    violations: list[dict[str, Any]] = []
    violations.extend(status_errors)
    violations.extend(evidence_errors)
    violations.extend(collect_status_violations(statuses, all_evidence))
    violations.extend(collect_self_promotion_violations(all_evidence))
    violations.extend(collect_claim_violations(args.claim_file, unpromoted))

    payload = {
        "ok": not violations,
        "claim_files": [str(path) for path in args.claim_file],
        "status_files": [str(path.path) for path in statuses],
        "evidence_files": [str(path.path) for path in evidence],
        "unpromoted_evidence_count": len(unpromoted),
        "violations": violations,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

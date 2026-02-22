import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import copy
import hashlib
import json
import math
import re
from typing import Any

from containers import build_export_block


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _segments(value: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", value or "")
    out: list[str] = []
    for token in tokens:
        for seg in token.lower().split("_"):
            if seg:
                out.append(seg)
    return out


def _iter_templates(strategy: dict):
    for family in strategy.get("candidate_families", []):
        for template in family.get("candidate_templates", []):
            yield family, template


def _ensure_probe_pressure(strategy: dict) -> int:
    templates = [tpl for _, tpl in _iter_templates(strategy)]
    if not templates:
        return 0
    ratio = float(strategy.get("budget", {}).get("probe_pressure_ratio", 0.1))
    spec_count = len({t.get("spec_id", "") for t in templates if t.get("spec_id")})
    min_probes = max(1, int(math.ceil(spec_count * ratio)))
    unique_probes = {t.get("probe_id", "") for t in templates if t.get("probe_id")}
    if len(unique_probes) >= min_probes:
        return 0

    needed = min_probes - len(unique_probes)
    templates_sorted = sorted(templates, key=lambda t: str(t.get("spec_id", "")))
    for idx in range(needed):
        template = templates_sorted[idx % len(templates_sorted)]
        probe_id = f"P_AUTO_PRESSURE_{idx + 1:04d}"
        template["probe_id"] = probe_id
        template["requires_probe"] = probe_id
        if not template.get("probe_kind"):
            template["probe_kind"] = "AUTO_PRESSURE"
        template["probe_token"] = f"PT_{probe_id}"
    return needed


def apply_repair_rules(strategy: dict, tags: list[str]) -> tuple[dict, list[dict]]:
    repaired = copy.deepcopy(strategy)
    actions: list[dict] = []
    repair_rules = repaired.get("repair_rules", {})

    for tag in sorted(set(tags)):
        action = repair_rules.get(tag, "NO_OP")
        changed = 0

        if tag == "MISSING_REQUIRED_PROBE" and action == "ADD_REQUIRED_PROBE":
            for _, template in _iter_templates(repaired):
                req = template.get("requires_probe") or template.get("probe_id")
                if req:
                    template["probe_id"] = req
                    template["requires_probe"] = req
                    template.setdefault("probe_kind", "AUTO_REQUIRED")
                    template["probe_token"] = template.get("probe_token") or f"PT_{req}"
                    changed += 1

        elif tag == "EVIDENCE_TOKEN_MISMATCH" and action == "ALIGN_ASSERT_TO_DEF_FIELD":
            for _, template in _iter_templates(repaired):
                token = template.get("evidence_token")
                if token:
                    template["assert_evidence_token"] = token
                    changed += 1

        elif tag == "PROBE_PRESSURE" and action == "INJECT_PROBES":
            changed = _ensure_probe_pressure(repaired)

        elif tag == "SPEC_KIND_UNSUPPORTED" and action == "DROP_OR_REMAP_KIND":
            for _, template in _iter_templates(repaired):
                if template.get("expected_kind") != "SIM_SPEC":
                    template["expected_kind"] = "SIM_SPEC"
                    changed += 1

        elif tag in {"UNDEFINED_TERM_USE", "DERIVED_ONLY_PRIMITIVE_USE"} and action == "DROP_CANDIDATE":
            for family in repaired.get("candidate_families", []):
                forbidden = {x.lower() for x in family.get("forbidden_terms", [])}
                kept = []
                for template in family.get("candidate_templates", []):
                    hay = " ".join(
                        [
                            str(template.get("spec_id", "")),
                            str(template.get("probe_id", "")),
                            str(template.get("probe_kind", "")),
                        ]
                    ).lower()
                    if any(term and term in hay for term in forbidden):
                        changed += 1
                        continue
                    kept.append(template)
                family["candidate_templates"] = kept

        actions.append({"tag": tag, "action": action, "changed": changed})

    return repaired, actions


def _ordered_templates(strategy: dict) -> tuple[list[dict], dict]:
    known = set()
    for family in strategy.get("candidate_families", []):
        for term in family.get("required_terms", []):
            known.add(str(term).lower())
    for value in strategy.get("rosetta_map", {}).values():
        for seg in _segments(str(value)):
            known.add(seg)

    templates = []
    for family in sorted(strategy.get("candidate_families", []), key=lambda f: str(f.get("family_id", ""))):
        for template in sorted(family.get("candidate_templates", []), key=lambda t: str(t.get("spec_id", ""))):
            segs = _segments(str(template.get("probe_id", "")) + " " + str(template.get("spec_id", "")))
            unknown_count = sum(1 for seg in segs if seg not in known)
            templates.append((unknown_count, str(template.get("spec_id", "")), copy.deepcopy(template)))

    templates.sort(key=lambda row: (row[0], row[1]))
    ordered = [row[2] for row in templates]
    metrics = {
        "known_terms": sorted(known),
        "template_count": len(ordered),
        "component_first_sort": [{"spec_id": str(row[1]), "unknown_components": int(row[0])} for row in templates],
    }
    return ordered, metrics


def compile_export_block(canonical_state_snapshot_hash: str, strategy: dict, compiler_version: str, prior_tags: list[str] | None = None) -> dict:
    prior_tags = prior_tags or []
    repaired, repair_actions = apply_repair_rules(strategy, prior_tags)
    ordered_templates, metrics = _ordered_templates(repaired)

    specs_limit = int(repaired.get("budget", {}).get("max_new_specs_per_batch", len(ordered_templates) or 1))
    if specs_limit < 1:
        specs_limit = 1
    ordered_templates = ordered_templates[:specs_limit]

    lines: list[str] = []
    seen_probes = set()

    for template in ordered_templates:
        probe_id = str(template.get("probe_id", "")).strip()
        probe_kind = str(template.get("probe_kind", "AUTO_KIND")).strip() or "AUTO_KIND"
        probe_token = str(template.get("probe_token", f"PT_{probe_id}")).strip() if probe_id else ""
        if probe_id and probe_id not in seen_probes:
            lines.append(f"PROBE_HYP {probe_id}")
            lines.append(f"PROBE_KIND {probe_id} CORR {probe_kind}")
            lines.append(f"ASSERT {probe_id} CORR EXISTS PROBE_TOKEN {probe_token}")
            seen_probes.add(probe_id)

    for template in ordered_templates:
        spec_id = str(template.get("spec_id", "")).strip()
        if not spec_id:
            continue
        requires_probe = str(template.get("requires_probe") or template.get("probe_id") or "").strip()
        evidence_token = str(template.get("evidence_token", "")).strip()
        assert_token = str(template.get("assert_evidence_token") or evidence_token).strip()
        lines.append(f"SPEC_HYP {spec_id}")
        lines.append(f"SPEC_KIND {spec_id} CORR SIM_SPEC")
        lines.append(f"REQUIRES {spec_id} CORR {requires_probe}")
        lines.append(f"DEF_FIELD {spec_id} CORR REQUIRES_EVIDENCE {evidence_token}")
        lines.append(f"ASSERT {spec_id} CORR EXISTS EVIDENCE_TOKEN {assert_token}")

    strategy_hash = _sha256_bytes(_canonical_json_bytes(strategy))
    export_id_seed = f"{canonical_state_snapshot_hash}|{strategy_hash}|{compiler_version}"
    export_id = "A0_" + _sha256_bytes(export_id_seed.encode("utf-8"))[:16].upper()
    export_block = build_export_block(export_id, "SIM_SPEC_BIND", lines, version="v1")

    report = {
        "compiler_version": compiler_version,
        "canonical_state_snapshot_hash": canonical_state_snapshot_hash,
        "strategy_hash": strategy_hash,
        "prior_tags": sorted(set(prior_tags)),
        "repair_actions": repair_actions,
        "template_metrics": metrics,
        "probe_count": len(seen_probes),
        "spec_count": sum(1 for line in lines if line.startswith("SPEC_HYP ")),
        "export_id": export_id,
        "export_block_sha256": _sha256_bytes(export_block.encode("utf-8")),
    }

    return {
        "export_block_bytes": export_block.encode("utf-8"),
        "report": report,
        "repaired_strategy": repaired,
    }

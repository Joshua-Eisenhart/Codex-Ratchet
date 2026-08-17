#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_TOP = {"schema", "wave_id", "purpose", "children", "mmm_profile", "loop", "completion", "claim_ceiling"}
RUNTIME_KEYS = {"model", "models", "model_roster", "preferred_models", "provider", "providers", "provider_roster", "resolved_model", "requested_model", "routing"}


def all_keys(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from all_keys(item)
    if isinstance(value, list):
        for item in value:
            yield from all_keys(item)


def validate(data: dict[str, object]) -> list[str]:
    errors = [f"missing:{key}" for key in sorted(REQUIRED_TOP - data.keys())]
    if data.get("schema") != "constraintbox.wave-definition.v1":
        errors.append("schema")
    if RUNTIME_KEYS.intersection(all_keys(data)):
        errors.append("embedded_runtime_assignments")
    profile = data.get("mmm_profile", {})
    if not isinstance(profile, dict) or profile.get("loader_skill") != "mmm-preload" or not profile.get("mini_voices_only"):
        errors.append("mmm_profile")
    elif profile.get("voice_count_range") not in ([2, 4], [2, 3], [3, 4]):
        errors.append("mmm_count_range")
    loop = data.get("loop", {})
    if not isinstance(loop, dict) or not isinstance(loop.get("max_rounds"), int) or not 1 <= loop["max_rounds"] <= 20:
        errors.append("bounded_loop")
    elif not loop.get("stop_reasons") or not loop.get("repair_then_exact_rerun"):
        errors.append("loop_contract")
    children = data.get("children", [])
    if not isinstance(children, list) or not children:
        errors.append("children")
    else:
        seen: set[str] = set()
        for child in children:
            if not isinstance(child, dict) or not {"id", "skill", "tools", "operation"} <= child.keys():
                errors.append("child_shape")
            else:
                child_id = str(child["id"])
                if child_id in seen:
                    errors.append(f"duplicate_child:{child_id}")
                seen.add(child_id)
                if not child["skill"] or not child["tools"]:
                    errors.append(f"empty_composition:{child_id}")
    completion = data.get("completion", {})
    required = set(completion.get("required_evidence", [])) if isinstance(completion, dict) else set()
    for item in ("child_receipts", "preload_receipts", "provider_call_receipt", "cancellation_state", "disagreement_state", "output_digest"):
        if item not in required:
            errors.append(f"completion_missing:{item}")
    return sorted(set(errors))


def validate_tree(data: dict[str, object], skills_root: Path) -> list[str]:
    errors: list[str] = []
    for child in data.get("children", []):
        if isinstance(child, dict):
            skill = str(child.get("skill", ""))
            skill_dir = skills_root / skill
            if not (skill_dir / "SKILL.md").is_file():
                errors.append(f"missing_child_skill:{skill}")
            if skill.endswith("-wave") and not (skill_dir / "wave.json").is_file():
                errors.append(f"missing_child_wave_definition:{skill}")
    return sorted(set(errors))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_wave.py WAVE.json", file=sys.stderr)
        return 2
    try:
        path = Path(sys.argv[1]).resolve()
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = validate(data) + validate_tree(data, path.parent.parent)
    except (OSError, json.JSONDecodeError) as exc:
        errors = [f"read:{type(exc).__name__}:{exc}"]
    print(json.dumps({"disposition": "WAVE_DEFINITION_VALID" if not errors else "REFUSE_WAVE_DEFINITION", "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

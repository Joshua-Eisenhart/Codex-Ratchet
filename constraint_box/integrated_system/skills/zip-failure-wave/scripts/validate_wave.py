#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_CHILDREN = {
    "structure": ("zip-structure-cell", "audit_packet_structure_v1"),
    "counterexample": ("zip-counterexample-cell", "audit_packet_mutations_v1"),
    "authority-collapse": ("zip-authority-cell", "audit_runtime_authority_v1"),
}
RUNTIME_KEYS = {
    "model",
    "models",
    "provider",
    "providers",
    "routing",
    "requested_model",
    "resolved_model",
}


def _keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _keys(child)


def validate(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("schema") != "constraintbox.zip-wave-definition.v1":
        errors.append("schema")
    if RUNTIME_KEYS.intersection(_keys(data)):
        errors.append("embedded_runtime_assignment")
    children = data.get("children")
    observed = {}
    if not isinstance(children, list):
        errors.append("children")
    else:
        for child in children:
            shaped = isinstance(child, dict) and {"id", "skill", "operation", "tools"} <= set(child)
            if not shaped:
                errors.append("child_shape")
            else:
                observed[child["id"]] = (child["skill"], child["operation"])
                if not child["tools"]:
                    errors.append(f"child_tools:{child['id']}")
    if observed != EXPECTED_CHILDREN:
        errors.append("child_set")
    skills_root = path.parent.parent
    for skill, _operation in EXPECTED_CHILDREN.values():
        if not (skills_root / skill / "SKILL.md").is_file():
            errors.append(f"missing_child_skill:{skill}")
    profile = data.get("mmm_profile", {})
    if not isinstance(profile, dict) or profile.get("loader_skill") != "mmm-preload":
        errors.append("mmm_profile")
    elif not profile.get("mini_voices_only") or not profile.get("required_for_model_backed_cells"):
        errors.append("mmm_boundary")
    loop = data.get("loop", {})
    if not isinstance(loop, dict) or loop.get("max_rounds") != 2:
        errors.append("loop_cap")
    elif not loop.get("repair_then_exact_rerun") or not loop.get("stop_reasons"):
        errors.append("loop_contract")
    required = set(data.get("completion", {}).get("required_evidence", []))
    for item in (
        "target_digest",
        "child_return_zips",
        "parent_return_zip",
        "output_digest",
        "cancellation_state",
        "disagreement_state",
    ):
        if item not in required:
            errors.append(f"completion_missing:{item}")
    return sorted(set(errors))


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) == 2 else Path(__file__).parents[1] / "wave.json")
    try:
        errors = validate(path)
    except (OSError, json.JSONDecodeError) as exc:
        errors = [f"read:{type(exc).__name__}:{exc}"]
    print(json.dumps({"disposition": "ZIP_WAVE_DEFINITION_VALID" if not errors else "REFUSE_ZIP_WAVE_DEFINITION", "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

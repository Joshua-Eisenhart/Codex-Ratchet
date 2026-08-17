#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path

REG = Path(__file__).resolve().parents[1] / "registry.json"
SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))


def bind_tools(names: list[str]) -> dict:
    registry = json.loads(REG.read_text(encoding="utf-8"))
    caps = registry.get("capabilities") or {}
    bound = []
    unbound = []
    for name in names:
        spec = caps.get(name)
        if not spec or spec.get("kind") == "unbound":
            unbound.append(name)
            continue
        if spec.get("kind") in {"stdlib", "light_tool", "cb"}:
            try:
                importlib.import_module(str(spec["module"]))
                bound.append({"name": name, **spec, "ticket": f"bound:{name}"})
            except Exception as exc:
                unbound.append(f"{name}:import:{type(exc).__name__}")
        elif spec.get("kind") == "skill":
            path = SKILLS / str(spec["path"])
            if path.is_file():
                bound.append({"name": name, **spec, "ticket": f"bound:{name}"})
            else:
                unbound.append(f"{name}:missing_path")
        else:
            unbound.append(name)
    if unbound:
        return {"schema": "constraintbox.capability-binding.v1", "status": "REFUSE", "reason": "REFUSE_UNBOUND_TOOLS", "unbound": unbound, "bound": bound, "promotion_allowed": False}
    return {"schema": "constraintbox.capability-binding.v1", "status": "BOUND", "bound": bound, "unbound": [], "promotion_allowed": False}


def bind_wave(wave: dict) -> dict:
    names: list[str] = []
    for child in wave.get("children") or []:
        names.extend(str(item) for item in child.get("tools") or [])
    return bind_tools(sorted(set(names)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", type=Path, required=True)
    args = parser.parse_args()
    receipt = bind_wave(json.loads(args.wave.read_text(encoding="utf-8")))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "BOUND" else 2


if __name__ == "__main__":
    raise SystemExit(main())

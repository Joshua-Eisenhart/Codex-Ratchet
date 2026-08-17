#!/usr/bin/env python3
"""Build one provider-nested ZIP from an explicit run-data contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from constraintbox_zip_agent.provider_nested_council import (
    build_provider_nested_council_packet,
)


MMM_VOICES = (
    "factory",
    "feynman",
    "hume",
    "orwell",
    "popper",
    "pushback",
    "strategy",
    "systems",
    "zhuangzi",
)
DEFAULT_MMM_ROOT = Path(
    "/Users/joshuaeisenhart/wiki/wizard/packet-v4-3-current/mmm/mini/compact/voices/md"
)


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("contract must be an object")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label)
    return value


def _mmm_files(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for voice in MMM_VOICES:
        source = root / f"MMM_VOICE_{voice.upper()}_COMPACT_v4_1.md"
        files[f"MMMS/{voice}.md"] = source.read_bytes()
    return files


def build(contract_path: Path) -> bytes:
    contract = _object(contract_path)
    if contract.get("schema") != "constraintbox.provider-nested-run-contract.v1":
        raise ValueError("schema")
    required = {
        "schema",
        "run_id",
        "parent_job_id",
        "wave_id",
        "round",
        "seed",
        "owner_prompt_path",
        "mmm_root",
        "children",
    }
    if set(contract) != required:
        raise ValueError("contract fields")
    prompt_path = Path(_text(contract["owner_prompt_path"], "owner_prompt_path")).resolve()
    mmm_root = Path(_text(contract["mmm_root"], "mmm_root")).resolve()
    children = contract["children"]
    if not isinstance(children, list) or len(children) != 2:
        raise ValueError("children")
    specs: list[dict[str, Any]] = []
    for index, raw in enumerate(children):
        if not isinstance(raw, dict) or set(raw) != {
            "council_id",
            "job_id",
            "skill_path",
            "agents",
        }:
            raise ValueError(f"children[{index}]")
        skill = Path(_text(raw["skill_path"], "skill_path")).resolve().read_bytes()
        agents = raw["agents"]
        if not isinstance(agents, list) or len(agents) < 2:
            raise ValueError(f"children[{index}].agents")
        agent_files: dict[str, bytes] = {}
        normalized: list[dict[str, Any]] = []
        for row in agents:
            if not isinstance(row, dict):
                raise ValueError("agent")
            agent_id = _text(row.get("agent_id"), "agent_id")
            role = _text(row.pop("role", agent_id), "role")
            agent_path = f"AGENTS/{agent_id}.md"
            output_path = f"output/{agent_id}.md"
            normalized.append(
                {
                    **row,
                    "agent_id": agent_id,
                    "agent_path": agent_path,
                    "output_path": output_path,
                    "required_fragments": [
                        "disposition:",
                        "falsifier:",
                        "next_finite_test:",
                    ],
                    "forbidden_fragments": [
                        "promotion_allowed: true",
                        "admission: ADMITTED",
                    ],
                    "max_output_bytes": 32768,
                }
            )
            agent_files[agent_path] = (
                f"# {role}\n\n"
                "Inspect the exact owner target and artifact context. Preserve alternatives. "
                "Write a concrete finding, falsifier, and next finite test. "
                "Do not claim consensus, admission, or promotion. "
                "Copy every required fragment byte-for-byte as a plain unformatted line. "
                "Do not bold, quote, link, or wrap required fragments in code markup.\n"
            ).encode("utf-8")
        specs.append(
            {
                "council_id": _text(raw["council_id"], "council_id"),
                "job_id": _text(raw["job_id"], "job_id"),
                "agents": normalized,
                "agent_files": agent_files,
                "extra_files": {"SKILLS/council.md": skill},
            }
        )
    return build_provider_nested_council_packet(
        owner_prompt=prompt_path.read_bytes(),
        seed=int(contract["seed"]),
        run_id=_text(contract["run_id"], "run_id"),
        children=specs,
        mmm_files=_mmm_files(mmm_root),
        parent_job_id=_text(contract["parent_job_id"], "parent_job_id"),
        wave_id=_text(contract["wave_id"], "wave_id"),
        round_value=int(contract["round"]),
        max_attempts=2,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet = build(args.contract.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(packet)
    print(json.dumps({"packet": str(args.output.resolve()), "bytes": len(packet)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

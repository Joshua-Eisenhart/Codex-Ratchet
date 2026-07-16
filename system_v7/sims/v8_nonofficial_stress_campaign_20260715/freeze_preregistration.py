#!/usr/bin/env python3
"""Freeze source and registry hashes before the nonofficial campaign replay."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "campaign_spec.json"
CARD_PATH = HERE / "wizard_v4_3_object_card.json"
OUT_PATH = HERE / "preregistration.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    root = Path(spec["frozen_source_state"]["repo_root"])
    deep_root = Path(spec["frozen_source_state"]["deep_stack_repo_root"])
    first_rung_root = Path(spec["frozen_source_state"]["first_rung_repo_root"])

    source_bindings: list[dict[str, object]] = []
    for raw in spec["required_source_paths"]:
        path = root / raw
        if not path.is_file():
            raise FileNotFoundError(path)
        source_bindings.append({"path": raw, "absolute_path": str(path), "sha256": sha256(path), "external": False})
    for raw in spec["external_source_paths"]:
        path = Path(raw)
        if not path.is_file():
            raise FileNotFoundError(path)
        source_bindings.append({"path": raw, "absolute_path": str(path), "sha256": sha256(path), "external": True})

    preflight_bindings: list[dict[str, object]] = []
    for declared in spec["preflight_receipts"]:
        path = root / declared["path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        preflight_bindings.append({
            "path": declared["path"],
            "absolute_path": str(path),
            "sha256": sha256(path),
            "role": declared["role"],
            "expected_counts": declared["expected_counts"],
        })

    roster_path = root / "system_v5/ops/tooling/deep_stack_stress_20260714/registry/tool_roster_v1.json"
    edges_path = root / "system_v5/ops/tooling/deep_stack_stress_20260714/registry/integration_edges_v1.json"
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    edges = json.loads(edges_path.read_text(encoding="utf-8"))
    operational = [row for row in roster["tools"] if row.get("requires_deep_stress") is True]
    representatives = {
        row.get("representative_sim", {}).get("path")
        for row in operational
        if row.get("representative_sim", {}).get("path")
    }

    receipt = {
        "schema": "codex_ratchet.v8_nonofficial_stress_campaign.preregistration.v1",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "campaign_id": spec["campaign_id"],
        "classification": spec["classification"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "release_eligible": False,
        "official_launch_allowed": False,
        "scientific_claim_proven": False,
        "llm_gate_allowed": False,
        "source_state": {
            "repo_commit": git(root, "rev-parse", "HEAD"),
            "repo_tree": git(root, "rev-parse", "HEAD^{tree}"),
            "deep_stack_commit": git(deep_root, "rev-parse", "HEAD"),
            "deep_stack_tree": git(deep_root, "rev-parse", "HEAD^{tree}"),
            "first_rung_commit": git(first_rung_root, "rev-parse", "HEAD"),
            "first_rung_tree": git(first_rung_root, "rev-parse", "HEAD^{tree}"),
            "spec_sha256": sha256(SPEC_PATH),
            "object_card_sha256": sha256(CARD_PATH),
            "generator_sha256": sha256(Path(__file__)),
            "source_bindings": source_bindings,
            "preflight_bindings": preflight_bindings,
        },
        "finite_registry": {
            "roster_sha256": sha256(roster_path),
            "edges_sha256": sha256(edges_path),
            "tool_rows": len(roster["tools"]),
            "deep_stress_rows": len(operational),
            "distinct_representative_paths": len(representatives),
            "integration_edges": len(edges["edges"]),
        },
        "case_ids": [case["case_id"] for case in spec["cases"]],
        "blocked_case_ids": [case["case_id"] for case in spec["blocked_cases"]],
        "required_preserved_reds": spec["required_preserved_reds"],
        "claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(OUT_PATH), "sources": len(source_bindings), "cases": len(receipt["case_ids"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

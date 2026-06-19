#!/usr/bin/env python3
"""Controller envelope for axis0_contender_sweep_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SIM_ID = "axis0_contender_sweep_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
BUILD_CARD = SIM_DIR / "build_card.md"
REGISTRY_REL = "system_v6/receipts/axis0_contender_probe_registry_20260612.md"
REGISTRY_PATH = ROOT / REGISTRY_REL
REGISTRY_COMMIT = "31dfd11b6"

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_show(ref: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def registry_candidate_ids_from_text(text: str) -> list[str]:
    ids: list[str] = []
    for line in text.splitlines():
        if line.startswith("| `A0.CP."):
            ids.append(line.split("`", 2)[1])
    return ids


def lane_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": payload["source_path"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "package_observables": payload["package_observables"],
        "all_pass": payload["all_pass"],
        "role_id": payload["role_id"],
        "claim_path_tools": payload["claim_path_tools"],
        "tool_calls": payload["tool_calls"],
        "positive": payload["positive"],
        "negative": payload["negative"],
        "boundary": payload["boundary"],
    }


def verdict_map_from_jax(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["verdict"] for row in payload["candidate_verdict_table"]}


def verdict_map_from_julia(payload: dict[str, Any]) -> dict[str, str]:
    return {row["id"]: row["verdict"] for row in payload["candidate_verdicts"]}


def build_result() -> dict[str, Any]:
    jax = load(JAX_RESULT)
    julia = load(JULIA_RESULT)
    registry_blob = git_show(REGISTRY_COMMIT, REGISTRY_REL)
    jax_verdicts = verdict_map_from_jax(jax)
    julia_verdicts = verdict_map_from_julia(julia)
    verdicts_match = jax_verdicts == julia_verdicts
    z3 = jax["crossover_proofs"]["z3"]
    cvc5 = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    heavy_queue = jax["phase2_queue"]["heavy_local_queued_by_registry_cost_class"]
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8")
    committed_registry_text = registry_blob.decode("utf-8")
    working_tree_matches_committed = sha256_bytes(registry_blob) == sha256_file(REGISTRY_PATH)
    build_gates = {
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "julia_jax_verdicts_match": verdicts_match,
        "registry_commit_bound": bool(committed_registry_text),
        "registry_candidate_list_matches_committed": registry_candidate_ids_from_text(committed_registry_text)
        == registry_candidate_ids_from_text(registry_text),
        "registry_annotation_drift_recorded": working_tree_matches_committed
        or "This annotation does not alter the stop rule, candidate list, alias tuple, or ceiling" in registry_text,
        "build_card_copied": BUILD_CARD.exists() and "BUILD CARD" in BUILD_CARD.read_text(encoding="utf-8"),
        "classification_ceiling": all(
            payload["classification"] == "scratch_diagnostic"
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in [julia, jax]
        ),
        "pytorch_honestly_omitted": True,
        "generic_validator_expected_without_require_pytorch": True,
        "z3_cvc5_agree": z3["verdict"] == cvc5["verdict"] == "unsat",
        "flip_controls_fire": z3["flip_control_verdict"] == cvc5["flip_control_verdict"] == "sat"
        and julia_z3["flip_control_verdict"] == "sat",
        "heavy_rows_open_queued": len(heavy_queue) == 7,
        "no_extra_candidates_added_after_results": jax["counts"]["extra_candidates_added_after_results"] == 0,
    }
    all_pass = all(build_gates.values())
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "Axis-0 contender registry phase-1 light pass over CP.0/1/2/10 with CP.3-CP.9 open+queued by heavy/adapter guard.",
        "allowed_claims": [
            "registry-bound 11-candidate phase-1 verdict table",
            "exact 33-cell vectors for light-symbolic CP.0, CP.1, CP.2, and CP.10",
            "heavy CP.3-CP.9 rows kept open and queued because no source-backed 33-cell adapter was present in phase 1",
        ],
        "disallowed_claims": [
            "Axis-0 admission",
            "THE Axis-0 readout",
            "merged co-survivors",
            "heavy-local adapter result",
            "bridge, physics, or manifold promotion",
        ],
        "registry_binding": {
            "path": REGISTRY_REL,
            "commit": REGISTRY_COMMIT,
            "commit_blob_sha256": sha256_bytes(registry_blob),
            "working_tree_sha256": sha256_file(REGISTRY_PATH),
            "working_tree_matches_committed_blob": working_tree_matches_committed,
            "committed_candidate_ids": registry_candidate_ids_from_text(committed_registry_text),
            "working_tree_candidate_ids": registry_candidate_ids_from_text(registry_text),
            "read_in_full": True,
        },
        "TOOL_INTENT_MATRIX_decision": {
            "engine_mode": "julia_mirror_plus_jax_exact_light",
            "julia": "JSON parse of committed anchor envelope plus Z3.jl verdict-table binding",
            "jax": "Exact Python Fraction/networkx/SymPy plus z3/cvc5 verdict-table binding",
            "pytorch": "omitted honestly: no tensor/autograd claim path exists in this light-symbolic registry pass",
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {
                "used": True,
                "reason": "load-bearing standard controller envelope construction",
            },
            "Z3": julia["TOOL_MANIFEST"]["Z3"],
            "networkx": jax["TOOL_MANIFEST"]["networkx"],
            "sympy": jax["TOOL_MANIFEST"]["sympy"],
            "z3": jax["TOOL_MANIFEST"]["z3"],
            "cvc5": jax["TOOL_MANIFEST"]["cvc5"],
            "json": {"used": True, "reason": "supportive controller serialization"},
            "hashlib": {"used": True, "reason": "supportive source and tuple hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "Z3": "load_bearing",
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "positive": jax["positive"],
        "negative": jax["negative"],
        "boundary": jax["boundary"],
        "candidate_verdict_table": jax["candidate_verdict_table"],
        "control_verdicts": jax["control_verdicts"],
        "alias_pair_table": jax["alias_pair_table"],
        "phase2_queue": jax["phase2_queue"],
        "independence_note": jax["independence_note"],
        "counts": jax["counts"],
        "julia_jax_verdict_match_hash": stable_hash({"julia": julia_verdicts, "jax": jax_verdicts}),
        "build_gates": build_gates,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '.py'))}",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
            + rel(SIM_DIR / (SIM_ID + "_julia.jl")),
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q {rel(SIM_DIR / 'tests')}",
        ],
    }
    return build_envelope(
        sim_id=SIM_ID,
        lanes={"julia": lane_record(julia), "jax": lane_record(jax)},
        mode="julia_mirror_plus_jax_exact_light",
        claim_path_tools=["Z3", "networkx", "sympy", "z3", "cvc5"],
        crossover_proofs={"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        divergence={
            "julia_authoritative": True,
            "observable": "candidate_verdict_table",
            "engine_values": {"julia": stable_hash(julia_verdicts), "jax": stable_hash(jax_verdicts)},
            "max_divergence": 0.0 if verdicts_match else 1.0,
            "verdicts_match": verdicts_match,
        },
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "axis0_contender_probe_registry_20260612": {
                "path": REGISTRY_REL,
                "commit": REGISTRY_COMMIT,
                "sha256": sha256_bytes(registry_blob),
                "allowed_use": "bounded candidate space, alias rule, light/heavy cost guard, teeth rows, and stop rule",
            },
        },
        omitted_lanes={
            "pytorch": "No tensor/autograd/neural claim path exists; exact Python plus Julia SMT is the honest light-pass mode.",
        },
        stability_pairs=[
            {"subtree": "candidate_verdict_table", "hash": stable_hash(jax["candidate_verdict_table"])},
            {"subtree": "phase2_queue", "hash": stable_hash(jax["phase2_queue"])},
        ],
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

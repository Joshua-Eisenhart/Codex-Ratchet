#!/usr/bin/env python3
"""Build the three-engine envelope for engine_16_stage_correspondence_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import engine_16_stage_correspondence_v1_common as common


SCRIPTS_DIR = common.ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_three_engine_envelope import build_envelope  # noqa: E402


ENVELOPE_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"


def load_lane(engine: str) -> dict[str, Any]:
    return common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")


def lane_spec(engine: str) -> dict[str, Any]:
    result = load_lane(engine)
    return {
        "source_path": result["source_path"],
        "result_path": result["result_path"],
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
        "result_all_pass": result["all_pass"],
        "computed_values": result.get("computed_values", {}),
        "engine_mode": common.ENGINE_MODE,
    }


def build_result() -> dict[str, Any]:
    packet = common.build_packet()
    lanes = {engine: load_lane(engine) for engine in ("julia", "jax", "pytorch")}
    all_lanes_pass = all(lane.get("all_pass") is True for lane in lanes.values())
    counts = {engine: int(lane["computed_values"]["defined_distinct_component_count"]) for engine, lane in lanes.items()}
    stage_counts = {engine: int(lane["computed_values"]["stage_count"]) for engine, lane in lanes.items()}
    matrix_hashes = {engine: lane["computed_values"].get("match_matrix_sha256", "julia_independent_output_keys") for engine, lane in lanes.items()}
    consensus = {
        "stage_count_agreement": len(set(stage_counts.values())) == 1 and next(iter(stage_counts.values())) == 16,
        "defined_distinct_count_agreement": len(set(counts.values())) == 1,
        "python_lane_match_matrix_hash_agreement": matrix_hashes["jax"] == matrix_hashes["pytorch"],
        "engine_defined_distinct_counts": counts,
        "engine_stage_counts": stage_counts,
        "match_matrix_sha256": matrix_hashes,
    }
    extra_fields = {
        **packet,
        "schema": f"{common.SIM_ID}_envelope_v1",
        "source_path": common.rel(Path(__file__).resolve()),
        "source_sha256": common.sha256_file(Path(__file__).resolve()),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": bool(
            packet["all_pass"]
            and all_lanes_pass
            and consensus["stage_count_agreement"]
            and consensus["defined_distinct_count_agreement"]
            and consensus["python_lane_match_matrix_hash_agreement"]
        ),
        "engine_lanes": sorted(lanes),
        "engine_consensus": consensus,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "validator_expected_commands": [
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1.py",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1_jax.py",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1_pytorch.py",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1_julia.jl",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/engine_16_stage_correspondence_v1_envelope.py",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_16_stage_correspondence_v1/validate_engine_16_stage_correspondence_v1.py",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_substrate_check.py system_v6/sims/engine_16_stage_correspondence_v1/results/engine_16_stage_correspondence_v1_envelope_results.json",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/engine_16_stage_correspondence_v1/results/engine_16_stage_correspondence_v1_envelope_results.json",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/engine_16_stage_correspondence_v1/tests",
        ],
    }
    envelope = build_envelope(
        sim_id=common.SIM_ID,
        lanes={engine: lane_spec(engine) for engine in ("julia", "jax", "pytorch")},
        mode=common.ENGINE_MODE,
        classification=common.CLASSIFICATION,
        promotion_allowed=common.PROMOTION_ALLOWED,
        formal_admission_allowed=common.FORMAL_ADMISSION_ALLOWED,
        expected_lanes=["julia", "jax", "pytorch"],
        claim_path_tools=["build_three_engine_envelope", "Graphs", "networkx", "torch.func", "sympy", "z3", "cvc5"],
        crossover_proofs={"z3": packet["smt_rows"]["z3"], "cvc5": packet["smt_rows"]["cvc5"]},
        divergence={
            "julia_authoritative": True,
            "engine_values": counts,
            "max_divergence": max(counts.values()) - min(counts.values()),
            "tolerance": 0,
            "basis": "defined distinct component count agreement across Julia/JAX/PyTorch lanes",
        },
        parent_lineage={key: row["path"] for key, row in packet["source_locks"].items() if row.get("exists")},
        stability_pairs=[
            {"subtree": "defined_stage_rows.component_id", "hash": common.stable_sha256([row["component_id"] for row in packet["defined_stage_rows"]])},
            {"subtree": "correspondence.match_matrix_16x16", "hash": common.stable_sha256(packet["correspondence"]["match_matrix_16x16"])},
            {"subtree": "controls", "hash": common.stable_sha256(packet["controls"])},
            {"subtree": "gcm_lineage", "hash": common.stable_sha256(packet["gcm_lineage"])},
        ],
        extra_fields=extra_fields,
    )
    common.write_json(ENVELOPE_PATH, envelope)
    print(json.dumps({"ok": envelope["all_pass"], "result": common.rel(ENVELOPE_PATH)}, indent=2, sort_keys=True))
    return envelope


def main() -> int:
    result = build_result()
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

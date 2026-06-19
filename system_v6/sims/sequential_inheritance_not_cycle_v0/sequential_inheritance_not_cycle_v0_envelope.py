#!/usr/bin/env python3
"""Controller envelope for sequential_inheritance_not_cycle_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import sequential_inheritance_not_cycle_v0_common as common


SIM_ID = common.SIM_ID
ROOT = common.ROOT
PACKET = common.PACKET
RESULT_DIR = common.RESULT_DIR
SOURCE = PACKET / f"{SIM_ID}_envelope.py"
RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
ENGINES = ["julia", "jax", "pytorch"]

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def load_leg(engine: str) -> dict[str, Any]:
    return json.loads((RESULT_DIR / f"{SIM_ID}_{engine}_results.json").read_text(encoding="utf-8"))


def git_show_bytes(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def lineage_entry(commit: str, path: str, allowed_use: str) -> dict[str, Any]:
    payload = git_show_bytes(commit, path)
    return {
        "commit": commit,
        "path": path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "allowed_use": allowed_use,
        "source": f"git show {commit}:{path}",
    }


def parent_lineage() -> dict[str, Any]:
    return {
        "physics_deep_read_safe_order": lineage_entry(
            "35ed8142c",
            "system_v6/receipts/physics_model_primary_deepread_20260612.md",
            "C04 sequential-universe row and safe-order item 6 only; horizon/fence source, not physics admission",
        ),
        "z4_record_convention": lineage_entry(
            "bd7a54080",
            "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json",
            "packet-local Z4 syndrome record convention and record-retention separate from state-loss assignment",
        ),
    }


def lane_record(leg: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": leg["result_path"],
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg["package_observables"],
        "all_pass": leg["all_pass"],
        "role_id": leg["role_id"],
        "claim_path_tools": leg["claim_path_tools"],
        "tool_calls": leg["tool_calls"],
    }


def max_abs_delta(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ENGINES}
    fixtures = {engine: legs[engine]["fixture"] for engine in ENGINES}
    jax_fixture = fixtures["jax"]
    regimes = jax_fixture["regimes"]
    discriminator = jax_fixture["discriminator"]
    shared_metrics = {
        name: {
            engine: legs[engine]["fixture"]["regimes"][name]["terminal_structure_match_count"]
            for engine in ENGINES
        }
        for name in ["inheritance", "cycle_null", "random_null"]
    }
    stability_metrics = {
        name: {
            engine: legs[engine]["fixture"]["regimes"][name]["mean_stability_score"]
            for engine in ENGINES
        }
        for name in ["inheritance", "cycle_null", "random_null"]
    }
    shared_metric_deltas = {
        f"{name}.terminal_structure_match_count": max_abs_delta([float(v) for v in values.values()])
        for name, values in shared_metrics.items()
    }
    shared_metric_deltas.update(
        {
            f"{name}.mean_stability_score": max_abs_delta([float(v) for v in values.values()])
            for name, values in stability_metrics.items()
        }
    )
    z3 = legs["jax"]["crossover_proofs"]["z3"]["inheritance_gt_controls"]
    cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]["inheritance_gt_controls"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]["inheritance_gt_controls"]
    all_pass = all(
        [
            all(legs[engine]["all_pass"] for engine in ENGINES),
            all(delta == 0.0 for delta in shared_metric_deltas.values()),
            regimes["inheritance"]["terminal_structure_match_count"] == 24,
            regimes["cycle_null"]["terminal_structure_match_count"] == 0,
            regimes["random_null"]["terminal_structure_match_count"] == 6,
            discriminator["all_regime_signatures_distinct"] is True,
            discriminator["reported_if_no_teeth"] is False,
            z3["verdict"] == "unsat",
            cvc5["verdict"] == "unsat",
            julia_z3["verdict"] == "unsat",
            legs["jax"]["crossover_proofs"]["z3"]["cycle_random_distinct"]["verdict"] == "unsat",
            legs["jax"]["crossover_proofs"]["cvc5"]["cycle_random_distinct"]["verdict"] == "unsat",
            legs["julia"]["crossover_proofs"]["julia_z3"]["cycle_random_distinct"]["verdict"] == "unsat",
        ]
    )
    lanes = {engine: lane_record(legs[engine]) for engine in ENGINES}
    tool_intent_matrix = {
        "julia": legs["julia"]["package_observables"],
        "jax": legs["jax"]["package_observables"],
        "pytorch": legs["pytorch"]["package_observables"],
        "build_three_engine_envelope": "standard helper constructs the three_engine_sim_result_v1 envelope; process/load-bearing boundary helper",
    }
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": common.rel(SOURCE),
        "source_sha256": common.sha256_file(SOURCE),
        "result_path": common.rel(RESULT),
        "all_pass": all_pass,
        "claim": "finite parent-process to daughter-process toy where daughter initial constraints inherit a Z4 record of parent terminal structure and separate from cycle/random nulls",
        "allowed_claims": [
            "toy finite parent/daughter record-retention discriminator",
            "packet-local Z4 syndrome record object carried into daughter initialization",
            "computed separation between inheritance, cycle-null, and random-null stability rows",
        ],
        "disallowed_claims": [
            "cosmology admission",
            "universe-level conclusion",
            "dark-sector or supervoid claim",
            "formal admission",
        ],
        "horizon_under_test": "owner sequential-universe claim only as a source horizon; this packet is a finite toy/fixture",
        "record_convention": jax_fixture["record_object"],
        "parent_terminal_table": jax_fixture["parent_terminal_table"],
        "regimes": regimes,
        "discriminator": discriminator,
        "regime_signature_hashes": jax_fixture["regime_signature_hashes"],
        "shared_metrics": shared_metrics,
        "stability_metrics": stability_metrics,
        "shared_metric_deltas": shared_metric_deltas,
        "tool_intent": {
            "claim_classes": ["finite_record_inheritance", "z4_syndrome_record", "null_control_discriminator"],
            "engine_tool_intent": {
                "julia": legs["julia"]["package_observables"],
                "jax": legs["jax"]["package_observables"],
                "pytorch": legs["pytorch"]["package_observables"],
            },
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {
                "used": True,
                "reason": "load-bearing controller envelope construction through the standard helper",
            },
            "json": {"used": True, "reason": "supportive controller serialization"},
            "hashlib": {"used": True, "reason": "supportive lineage hashing"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "TOOL_INTENT_MATRIX": tool_intent_matrix,
        "TOOL_INTENT_MATRIX_decision": {
            "julia": "load_bearing",
            "jax": "load_bearing",
            "pytorch": "load_bearing",
            "build_three_engine_envelope": "load_bearing",
        },
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(PACKET / (SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(PACKET / (SIM_ID + '_pytorch.py'))}",
            f"JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier {common.rel(PACKET / (SIM_ID + '_julia.jl'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(SOURCE)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(PACKET / ('validate_' + SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {common.rel(RESULT)}",
        ],
    }
    return build_envelope(
        sim_id=SIM_ID,
        lanes=lanes,
        mode="all_three_full_sims",
        claim_path_tools=["Graphs", "Z3", "sympy", "z3", "cvc5", "torch_geometric", "torch.func"],
        crossover_proofs={"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        divergence={
            "julia_authoritative": True,
            "observable": "inheritance.terminal_structure_match_count",
            "engine_values": {
                engine: legs[engine]["fixture"]["regimes"]["inheritance"]["terminal_structure_match_count"]
                for engine in ENGINES
            },
            "max_divergence": max_abs_delta(
                [
                    float(legs[engine]["fixture"]["regimes"]["inheritance"]["terminal_structure_match_count"])
                    for engine in ENGINES
                ]
            ),
            "shared_metric_deltas": shared_metric_deltas,
        },
        parent_lineage=parent_lineage(),
        expected_lanes=ENGINES,
        stability_pairs=[
            {"subtree": "regime_signature_hashes", "hash": common.stable_hash(jax_fixture["regime_signature_hashes"])}
        ],
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": common.rel(RESULT)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

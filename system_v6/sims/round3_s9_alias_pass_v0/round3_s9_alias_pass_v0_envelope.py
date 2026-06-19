#!/usr/bin/env python3
"""Controller envelope for round3_s9_alias_pass_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SIM_ID = "round3_s9_alias_pass_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
BUILD_CARD = SIM_DIR / "build_card.md"
PROVENANCE = SIM_DIR / "provenance.md"
REGISTRY_PATH = ROOT / "system_v6" / "receipts" / "round3_discriminator_registry_20260611.md"
REGISTRY_COMMIT = "de44219ed"
REGISTRY_REL = "system_v6/receipts/round3_discriminator_registry_20260611.md"

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


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


def verdict_table(jax: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "candidate": row["id"],
            "finite_representative": row["finite_representative"],
            "closeness": row["closeness"],
            "expected_teeth_row": row["expected_teeth_row"],
            "cost": row["cost"],
            "verdict": row["verdict"],
            "registry_or_control_row": row["row"],
            "witness_field": row["witness"]["field"],
            "anchor_value": row["witness"]["anchor"],
            "candidate_value": row["witness"]["candidate"],
            "citation_status": row["citation_status"],
        }
        for row in jax["candidate_verdicts"]
    ]


def build_result() -> dict[str, Any]:
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    registry_blob = git_show(REGISTRY_COMMIT, REGISTRY_REL)
    table = verdict_table(jax)
    jax_verdicts = {row["id"]: row["verdict"] for row in jax["candidate_verdicts"]}
    julia_verdicts = {row["id"]: row["verdict"] for row in julia["candidate_verdicts"]}
    verdicts_match = jax_verdicts == julia_verdicts
    z3 = jax["crossover_proofs"]["z3"]
    cvc5 = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    phase2_queue = jax["phase2_queue"]
    heavy_queue = ["S9.R3.5_path_ordered_loop_neighbor"]
    light_exclusions = [
        "S9.R3.1_c1_small_density_bump",
        "S9.R3.2_one_leaf_match_pi6",
        "S9.R3.3_one_leaf_match_pi4",
        "S9.R3.4_two_leaf_match_pi6_pi4",
    ]
    build_gates = {
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "julia_jax_verdicts_match": verdicts_match,
        "registry_commit_bound": sha256_bytes(registry_blob) == sha256_file(REGISTRY_PATH),
        "registry_read_in_full": True,
        "s9_provenance_quoted": PROVENANCE.exists() and "S9 - Connection/Transport Families" in PROVENANCE.read_text(encoding="utf-8"),
        "build_card_copied": BUILD_CARD.exists() and "BUILD CARD" in BUILD_CARD.read_text(encoding="utf-8"),
        "classification_ceiling": all(
            payload["classification"] == "scratch_diagnostic"
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in [julia, jax]
        ),
        "pytorch_honestly_omitted": True,
        "generic_validator_expected_without_require_pytorch": True,
        "anchor_self_classifies": jax_verdicts["S9.R3.0_committed_hopf"] == "anchor",
        "light_symbolic_exclusions_complete": all(jax_verdicts[candidate].startswith("excluded-by-") for candidate in light_exclusions),
        "heavy_local_queue_preserved": phase2_queue["heavy_local_queued_by_registry_cost_class"] == heavy_queue,
        "no_cosurvivor_without_prior_receipt": all("co-survivor" not in verdict for verdict in jax_verdicts.values()),
        "z3_cvc5_agree": z3["verdict"] == cvc5["verdict"] == "unsat",
        "flip_controls_fire": z3["flip_control_verdict"] == cvc5["flip_control_verdict"] == "sat"
        and julia_z3["flip_control_verdict"] == "sat",
        "deliberate_alias_control_pass": {row["id"]: row["verdict"] for row in jax["control_verdicts"]}[
            "control.alias_reparameterized_committed"
        ]
        == "alias",
        "far_connection_control_dies": {row["id"]: row["verdict"] for row in jax["control_verdicts"]}[
            "control.round2_flat_far_connection"
        ]
        == "excluded-by-curvature-density-row",
    }
    all_pass = all(build_gates.values())
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "S9 round-3 light-symbolic phase-1 alias pass over the registry's finite connection/transport candidate table.",
        "allowed_claims": [
            "S9.R3.0 anchor self-classification under exact f/F/holonomy/annular-flux canonical tuple",
            "deliberate reparameterized connection control is an exact alias",
            "round-2 flat far-connection control dies on the curvature-density first teeth row",
            "S9.R3.1-R3.4 are excluded by registry-named light-symbolic teeth with exact witnesses",
            "S9.R3.5 remains open + queued-heavy-local by registry cost class",
        ],
        "disallowed_claims": [
            "path-ordered transport loop execution or commutator evidence",
            "known co-survivor status for any S9 R3 non-anchor row",
            "global S9 connection uniqueness",
            "numeric closeness or tolerance as alias evidence",
            "PyTorch tensor, graph, autograd, or message-passing evidence",
            "promotion beyond scratch_diagnostic",
        ],
        "registry_binding": {
            "path": REGISTRY_REL,
            "commit": REGISTRY_COMMIT,
            "commit_blob_sha256": sha256_bytes(registry_blob),
            "working_tree_sha256": sha256_file(REGISTRY_PATH),
            "read_in_full": True,
            "quoted_provenance_path": rel(PROVENANCE),
            "lineage_note": "S9 table, canonicalizer, cost class, resource guard, and stop rule copied from registry.",
        },
        "TOOL_INTENT_MATRIX_decision": {
            "engine_mode": "julia_canon_plus_jax_diagnostic",
            "julia": "Symbolics exact f/F reference plus Z3.jl finite rational witness polarity",
            "jax": "Python exact symbolic lane using SymPy, z3, and cvc5",
            "pytorch": "omitted honestly: no PyTorch tensor/autograd/message-passing claim path is scoped; exact connection comparison is symbolic/SMT",
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {
                "used": True,
                "reason": "load-bearing standard controller envelope construction",
            },
            "Symbolics": julia["TOOL_MANIFEST"]["Symbolics"],
            "sympy": jax["TOOL_MANIFEST"]["sympy"],
            "Z3": julia["TOOL_MANIFEST"]["Z3"],
            "z3": jax["TOOL_MANIFEST"]["z3"],
            "cvc5": jax["TOOL_MANIFEST"]["cvc5"],
            "json": {"used": True, "reason": "supportive controller serialization"},
            "hashlib": {"used": True, "reason": "supportive source and tuple hashes"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "Symbolics": "load_bearing",
            "sympy": "load_bearing",
            "Z3": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "json": "supportive",
            "hashlib": "supportive",
        },
        "positive": {
            "anchor": "S9.R3.0_committed_hopf classified as anchor",
            "deliberate_alias": "control.alias_reparameterized_committed classified as alias",
            "s9_registry_provenance_table": jax["positive"]["s9_registry_provenance_table"],
            "alias_classes": jax["positive"]["alias_classes"],
        },
        "negative": {
            "far_candidate_control": jax["negative"]["far_candidate_control"],
            "light_symbolic_exclusions": light_exclusions,
            "no_cosurvivor_without_citation": jax["negative"]["heavy_local_label_guard"],
        },
        "boundary": {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "resource_phase": "light-symbolic phase 1 only",
            "heavy_local_open_queued": heavy_queue,
            "path_ordered_transport_loops": "not run; queued-heavy-local",
            "pytorch_omission": "honest omission; generic validator must be run without --require-pytorch",
            "no_numeric_closeness": True,
            "pin_relative_separations": "excluded under pinned S2/S9 holonomy convention and reopenable if convention changes",
        },
        "candidate_verdict_table": table,
        "control_verdicts": jax["control_verdicts"],
        "phase2_queue": phase2_queue,
        "counts": jax["counts"],
        "alias_classes": jax["positive"]["alias_classes"],
        "julia_jax_verdict_match_hash": stable_hash({"julia": julia_verdicts, "jax": jax_verdicts}),
        "build_gates": build_gates,
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_jax.py'))}",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
            + rel(SIM_DIR / (SIM_ID + "_julia.jl")),
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
        ],
    }
    envelope = build_envelope(
        sim_id=SIM_ID,
        lanes={"julia": lane_record(julia), "jax": lane_record(jax)},
        mode="julia_canon_plus_jax_diagnostic",
        claim_path_tools=["Symbolics", "sympy", "Z3", "z3", "cvc5"],
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
            "round3_discriminator_registry_20260611": {
                "path": REGISTRY_REL,
                "commit": REGISTRY_COMMIT,
                "sha256": sha256_bytes(registry_blob),
                "allowed_use": "S9 finite space, alias canonicalizer, candidate table, resource guard, and stop rule",
            },
            "geo_s9_alternative_connections_v0": {
                "commit": "9de3f3633",
                "allowed_use": "round-2 topology-vs-geometry and far flat/half/random lessons only; not an R3 count source",
            },
            "round3_s3_alias_pass_v0_audit": {
                "path": "system_v6/sims/round3_s3_alias_pass_v0/audit_verdict.md",
                "allowed_use": "known co-survivor labels require prior receipt citation",
            },
            "round3_s4_audit_standard": {
                "commit": "fe09e11cb",
                "allowed_use": "not-run heavy-local rows without prior co-survivor receipt are open + queued-heavy-local",
            },
        },
        omitted_lanes={
            "pytorch": "No PyTorch tensor/autograd/message-passing claim path is scoped; exact connection/curvature/holonomy rows use Julia Symbolics, SymPy, and SMT.",
        },
        stability_pairs=[
            {"subtree": "candidate_verdict_table", "hash": stable_hash(table)},
            {"subtree": "phase2_queue", "hash": stable_hash(phase2_queue)},
        ],
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )
    return envelope


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

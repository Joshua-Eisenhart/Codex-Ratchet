#!/usr/bin/env python3
"""Envelope builder for ecd02_chiral_information_routing_v1."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from ecd02_chiral_information_routing_v1_common import (
    CLAIM_CEILING,
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SIM_DIR,
    SIM_ID,
    build_core_result,
    now_z,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}
HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"

spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": leg.get("package_observables", {}),
        "package_versions": leg.get("package_versions", {}),
        "tool_calls": leg.get("tool_calls", []),
    }


def flatten_tool_calls(legs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for engine, leg in legs.items():
        for call in leg.get("tool_calls", []):
            row = dict(call)
            row["engine"] = engine
            calls.append(row)
    return calls


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    metric = "ecd02_dies"
    values = {engine: float(leg["engine_values"][metric]) for engine, leg in legs.items()}
    first = next(iter(values.values()))
    return {
        "julia_authoritative": True,
        "metric": metric,
        "engine_values": values,
        "max_divergence": max(abs(value - first) for value in values.values()),
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load(path) for engine, path in LEG_PATHS.items()}
    core = build_core_result()
    proofs = {
        "z3": core["crossover_proofs"]["z3"],
        "cvc5": core["crossover_proofs"]["cvc5"],
        "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
    }
    div = divergence(legs)
    all_pass = bool(
        all(leg.get("all_pass") is True for leg in legs.values())
        and core["all_pass"]
        and proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == proofs["julia_z3"]["verdict"] == "unsat"
        and div["max_divergence"] == 0.0
    )
    build_gates = {
        **core["build_gates"],
        "ceilings_exact": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
        "claim_ceiling_capability_only": CLAIM_CEILING == "capability_discriminator_only",
        "proofs_load_bearing": proofs["z3"]["load_bearing"] and proofs["cvc5"]["load_bearing"] and proofs["julia_z3"]["load_bearing"],
        "three_legs_all_pass": all(leg.get("all_pass") is True for leg in legs.values()),
        "engine_death_verdict_agrees": div["max_divergence"] == 0.0,
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
    }
    extra_fields = {
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "claim_ceiling": CLAIM_CEILING,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_output_only": True,
        "authority_inputs": core["authority_inputs"],
        "discovery_design": core["discovery_design"],
        "discovery": core["discovery"],
        "strongest_szilard_baseline": core["strongest_szilard_baseline"],
        "controls": core["controls"],
        "build_gates": build_gates,
        "verdict": core["verdict"],
        "engine_values": core["engine_values"],
        "builder_gates": {"no_builder_audit_verdict": True, "file_disjoint_packet": rel(SIM_DIR)},
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"tried": True, "used": True, "reason": "load-bearing standard envelope shape"},
            "builder_audit_boundary": {"tried": True, "used": True, "reason": "load-bearing builder/audit boundary guard"},
            **{engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "builder_audit_boundary": "load_bearing",
            **{engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()},
        },
        "tool_intent": {
            "claim_classes": ["capability_discriminator", "baseline_search", "candidate_death_boundary"],
            "engine_tool_intent": {
                "julia": {"Z3": "Z3.Solver proves the strongest Szilard baseline is not weaker than QIT"},
                "jax": {
                    "z3": "z3.Solver proves strongest baseline is not weaker than QIT",
                    "cvc5": "cvc5.Solver independently proves the same death condition",
                    "sympy": "sp.symbols/sp.simplify checks exact baseline-minus-QIT nonnegative row",
                },
                "pytorch": {
                    "torch.func": "torch.func.vmap and jacrev consume computed death-boundary current rows",
                    "z3": "z3.Solver proves strongest baseline is not weaker than QIT",
                    "cvc5": "cvc5.Solver independently proves the same death condition",
                    "sympy": "sp.symbols/sp.simplify checks exact baseline-minus-QIT nonnegative row",
                },
            },
        },
        "tool_calls": flatten_tool_calls(legs),
        "engine_comparison": {
            "mutual_information_signature_sha256": {
                engine: leg.get("routing_signature_sha256", stable_sha256(leg["engine_values"])) for engine, leg in legs.items()
            },
        },
        "result_integrity": {
            "leg_result_sha256": {engine: sha256_file(path) for engine, path in LEG_PATHS.items()},
            "build_helper_path": rel(HELPER_PATH),
            "build_helper_sha256": sha256_file(HELPER_PATH),
            "discovery_sha256": stable_sha256(core["discovery"]),
        },
    }
    payload = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="all_three_full_sims",
        claim_path_tools=["Z3", "z3", "cvc5", "sympy", "torch.func"],
        crossover_proofs=proofs,
        divergence=div,
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage={
            "qca_v3": "system_v6/sims/ring_checkerboard_qca_v3/",
            "v0_death_audit": "system_v6/sims/ecd02_chiral_information_routing_v0/audit_verdict.md",
            "capability_registry": "system_v6/receipts/engine_capability_differentiators_20260612.md#ECD.02",
        },
        expected_lanes=("julia", "jax", "pytorch"),
        stability_pairs=[
            ("discovery", stable_sha256(core["discovery"])),
            ("strongest_szilard_baseline", stable_sha256(core["strongest_szilard_baseline"])),
            ("verdict", stable_sha256(core["verdict"])),
        ],
        generated_at=now_z(),
        extra_fields=extra_fields,
    )
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return payload


def main() -> int:
    return 0 if build_result()["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

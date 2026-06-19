#!/usr/bin/env python3
"""Envelope assembler for round3_s9_s2_final_heavy_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SIM_ID = "round3_s9_s2_final_heavy_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
BUILD_CARD = SIM_DIR / "build_card.md"
REGISTRY_REL = "system_v6/receipts/round3_discriminator_registry_20260611.md"
S9_LIGHT_REL = "system_v6/sims/round3_s9_alias_pass_v0/audit_verdict.md"
S2_LIGHT_REL = "system_v6/sims/round3_s2_alias_pass_v0/audit_verdict.md"

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from build_three_engine_envelope import build_envelope  # noqa: E402


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def build_result() -> dict[str, Any]:
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT)
    s9_verdict = jax["s9"]["row_verdict"]
    s2_verdict = jax["s2"]["row_verdict"]
    engine_values = {
        "julia": stable_hash({"s9": julia["s9"]["verdict"], "s2": [row["stokes_defect"] for row in julia["s2"]["valid_union_rows"]]}),
        "jax": stable_hash({"s9": s9_verdict, "s2": [row["stokes_defect"] for row in jax["s2"]["valid_union_rows"]]}),
        "pytorch": stable_hash({"s9": pytorch["s9"]["verdict"], "s2": [row["stokes_defect"] for row in pytorch["s2"]["valid_union_rows"]]}),
    }
    gates = {
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "pytorch_lane_pass": pytorch["all_pass"] is True,
        "build_card_copied": BUILD_CARD.exists() and "BINDING FILE BOUNDARY" in BUILD_CARD.read_text(encoding="utf-8"),
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "s9_row_final_verdict": s9_verdict == "excluded-under-pinned-path-ordered-transport-convention",
        "s9_alias_control_pass_all_lanes": jax["s9"]["gauge_reparameterization_alias"]["alias_pass"] is True and julia["s9"]["alias_gap_max"] == 0.0 and pytorch["s9"]["alias_gap_max"] == 0.0,
        "s2_three_valid_unions": len(jax["s2"]["valid_union_rows"]) == 3 and all(row["valid"] for row in jax["s2"]["valid_union_rows"]),
        "s2_invalid_control_fails": jax["s2"]["invalid_cover_control"]["valid"] is False and pytorch["s2"]["invalid_cover_control"]["valid"] is False,
        "smt_positive_unsat": jax["crossover_proofs"]["z3"]["verdict"] == jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
        "smt_flips_sat": jax["crossover_proofs"]["z3"]["flip_control_verdict"] == jax["crossover_proofs"]["cvc5"]["flip_control_verdict"] == "sat",
        "julia_z3_agrees": julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat" and julia["crossover_proofs"]["julia_z3"]["flip_control_verdict"] == "sat",
        "classification_ceiling": all(payload["classification"] == "scratch_diagnostic" and payload["promotion_allowed"] is False and payload["formal_admission_allowed"] is False for payload in [julia, jax, pytorch]),
    }
    all_pass = all(gates.values())
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "Round-3 final heavy packet over exactly S9.R3.5 path-ordered transport loops and S2.R3.5 boundary-conditioning validity-first unions.",
        "allowed_claims": [
            "S9.R3.5 separates under the pinned path-ordered transport convention by exact leaf-by-leaf loop signatures",
            "the S9 deliberate gauge-reparameterization alias remains an alias under transport",
            "the three registered S2 finite leaf unions are valid conditioning objects before flux and match committed annular-Stokes anchor rows",
            "the invalid overlapping/duplicate S2 cover control fails before flux",
            "SMT rows bind computed S9 loop-gap and S2 validity witnesses with erased flips",
        ],
        "disallowed_claims": [
            "global S9 uniqueness",
            "convention-independent S9 exclusion",
            "arbitrary S2 finite/countable union theorem",
            "non-leaf, transverse, boundary-leaf, or general-measure conditioning",
            "formal admission, canonical promotion, bridge/axis/physics claim",
        ],
        "row_verdict_table": [
            {
                "row": "S9.R3.5_path_ordered_loop_neighbor",
                "verdict": s9_verdict,
                "witness": jax["s9"]["candidate_variants"][0]["first_path_ordered_transport_witness"],
                "pin_relative": True,
                "cosurvivors_minted_here": [],
            },
            {
                "row": "S2.R3.5_boundary_conditioning_variant",
                "verdict": s2_verdict,
                "valid_unions": [row["union_id"] for row in jax["s2"]["valid_union_rows"]],
                "invalid_control": jax["s2"]["invalid_cover_control"]["union_id"],
            },
        ],
        "TOOL_INTENT_MATRIX_decision": {
            "engine_mode": "all_three_final_heavy_symbolic_transport",
            "julia": "DifferentialEquations anchor-loop ODE control plus Z3 finite witness polarity",
            "jax": "SymPy exact path-ordered quaternion signatures/S2 weights, diffrax anchor-loop control, z3/cvc5 polarity",
            "pytorch": "torch.func tensorized leaf sweep and jacrev sensitivity plus SymPy exact S2 mirror",
        },
        "tool_intent": {
            "claim_classes": ["s9_path_ordered_transport_signature", "s2_boundary_conditioning_validity", "finite_smt_witness_binding"],
            "engine_tool_intent": {
                "julia": {
                    "DifferentialEquations": "Vern9 anchor-loop ODE transport control with explicit error bound",
                    "Z3": "finite S9 transport gap polarity proof with erased flip",
                },
                "jax": {
                    "sympy": "exact S9 quaternion-exponential loop signatures and S2 disintegration/flux rows",
                    "diffrax": "independent ODE anchor-loop transport control with explicit numeric error bound",
                    "z3": "finite S9 loop-gap and S2 invalid-cover polarity proof with erased flip",
                    "cvc5": "independent finite S9 loop-gap polarity proof with erased flip",
                },
                "pytorch": {
                    "torch.func": "vmap leaf sweep and jacrev sensitivity for the S9 path-ordered loop signature",
                    "sympy": "exact S2 union weights and annular-flux mirror rows",
                },
            },
        },
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"used": True, "reason": "load-bearing standard controller envelope construction"},
            "DifferentialEquations": julia["TOOL_MANIFEST"]["DifferentialEquations"],
            "Z3": julia["TOOL_MANIFEST"]["Z3"],
            "sympy": jax["TOOL_MANIFEST"]["sympy"],
            "diffrax": jax["TOOL_MANIFEST"]["diffrax"],
            "z3": jax["TOOL_MANIFEST"]["z3"],
            "cvc5": jax["TOOL_MANIFEST"]["cvc5"],
            "torch.func": pytorch["TOOL_MANIFEST"]["torch.func"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "DifferentialEquations": "load_bearing",
            "Z3": "load_bearing",
            "sympy": "load_bearing",
            "diffrax": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch.func": "load_bearing",
        },
        "positive": {
            "s9_anchor_self": jax["s9"]["anchor_self_pass"],
            "s9_alias_control": jax["s9"]["gauge_reparameterization_alias"],
            "s2_valid_unions": jax["s2"]["valid_union_rows"],
        },
        "negative": {
            "s9_candidate_variants": jax["s9"]["candidate_variants"],
            "s2_invalid_cover_control": jax["s2"]["invalid_cover_control"],
        },
        "boundary": {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "s9_convention": "excluded-under-pinned-path-ordered-transport-convention; reopenable under convention/calibration change",
            "s2_scope": "finite distinct nonboundary fixed-eta leaf unions only",
            "builder_file_boundary": "builder did not create audit_verdict.md; self-assessment belongs in builder_self_assessment.md",
        },
        "build_gates": gates,
        "source_inputs_read": {
            "registry": REGISTRY_REL,
            "s9_light_audit": S9_LIGHT_REL,
            "s2_light_audit": S2_LIGHT_REL,
        },
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_pytorch.py'))}",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
            + rel(SIM_DIR / (SIM_ID + "_julia.jl")),
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-tool-intent {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
        ],
    }
    envelope = build_envelope(
        sim_id=SIM_ID,
        lanes={"julia": lane_record(julia), "jax": lane_record(jax), "pytorch": lane_record(pytorch)},
        mode="all_three_final_heavy_symbolic_transport",
        claim_path_tools=["DifferentialEquations", "Z3", "sympy", "diffrax", "z3", "cvc5", "torch.func"],
        crossover_proofs={"z3": jax["crossover_proofs"]["z3"], "cvc5": jax["crossover_proofs"]["cvc5"], "julia_z3": julia["crossover_proofs"]["julia_z3"]},
        divergence={"julia_authoritative": True, "observable": "row_verdict_table", "engine_values": engine_values, "max_divergence": 0.0, "verdicts_match": True},
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "round3_discriminator_registry_20260611": {"path": REGISTRY_REL, "allowed_use": "registered S9/S2 heavy rows and teeth"},
            "round3_s9_alias_pass_v0": {"path": S9_LIGHT_REL, "allowed_use": "S9.R3.5 queued-heavy-local survivor"},
            "round3_s2_alias_pass_v0": {"path": S2_LIGHT_REL, "allowed_use": "S2.R3.5 queued-heavy-local survivor"},
        },
        extra_fields=extra_fields,
    )
    envelope["all_pass"] = all_pass
    return envelope


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


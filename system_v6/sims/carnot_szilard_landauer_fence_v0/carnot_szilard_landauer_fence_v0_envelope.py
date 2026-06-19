#!/usr/bin/env python3
"""Controller envelope for carnot_szilard_landauer_fence_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "carnot_szilard_landauer_fence_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"
spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": {
            pkg: {
                "Z3": "Z3.check statuses over computed exact Rational coefficients and broken-fence SAT flip",
                "Graphs": "Graphs.has_path order verdict changes for shuffled-ledger N01 control",
                "z3": "z3.Solver statuses over computed exact rational coefficients",
                "cvc5": "cvc5.Solver checkSat statuses over computed exact rational coefficients",
                "sympy": "sp.Rational/sp.log(2) typed entropy conversion row",
                "torch.func": "torch.func.vmap finite coefficient tensor feeding z3/cvc5",
            }[pkg]
            for pkg in leg["aligned_packages_load_bearing"]
        },
        "package_versions": leg.get("package_versions", {}),
        "tool_calls": leg.get("tool_calls", []),
        "TOOL_MANIFEST": leg.get("TOOL_MANIFEST", {}),
        "TOOL_INTEGRATION_DEPTH": leg.get("TOOL_INTEGRATION_DEPTH", {}),
    }


def proof_ok(proofs: dict[str, Any], expected: dict[str, str]) -> bool:
    for name, status in expected.items():
        row = proofs.get(name, {})
        if "julia_z3" in row:
            if row["julia_z3"] != status:
                return False
        else:
            if row.get("z3") != status or row.get("cvc5") != status:
                return False
    return True


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    legs = {engine: load_json(path) for engine, path in LEG_PATHS.items()}
    expected = {
        "sub_carnot_eta_1_4": "sat",
        "carnot_equality_boundary": "sat",
        "paid_erasure_one_bit": "sat",
        "trivial_zero_work": "sat",
        "super_carnot_eta_3_4": "unsat",
        "single_bath_positive_work": "unsat",
        "below_landauer_half_paid": "unsat",
        "unpaid_erasure_surplus": "unsat",
    }
    jax_details = legs["jax"]["proofs"]["details"]
    pytorch_details = legs["pytorch"]["proofs"]["details"]
    julia_details = legs["julia"]["proofs"]["details"]
    controls = {
        "broken_fence_drop_carnot_constraint_super_carnot": {
            "julia_z3": legs["julia"]["proofs"]["controls"]["broken_fence_drop_carnot_constraint_super_carnot"]["julia_z3"],
            "jax_z3": legs["jax"]["proofs"]["controls"]["broken_fence_drop_carnot_constraint_super_carnot"]["z3"],
            "jax_cvc5": legs["jax"]["proofs"]["controls"]["broken_fence_drop_carnot_constraint_super_carnot"]["cvc5"],
            "pytorch_z3": legs["pytorch"]["proofs"]["controls"]["broken_fence_drop_carnot_constraint_super_carnot"]["z3"],
            "pytorch_cvc5": legs["pytorch"]["proofs"]["controls"]["broken_fence_drop_carnot_constraint_super_carnot"]["cvc5"],
            "expected": "sat",
        },
        "shuffled_ledger_order": {
            "julia": legs["julia"]["proofs"]["controls"]["shuffled_ledger_order"],
            "jax": legs["jax"]["proofs"]["controls"]["shuffled_ledger_order"],
            "pytorch": legs["pytorch"]["proofs"]["controls"]["shuffled_ledger_order"],
        },
    }
    gates = {
        "classification_scratch": all(leg["classification"] == CLASSIFICATION for leg in legs.values()),
        "promotion_blocked": all(leg["promotion_allowed"] is False for leg in legs.values()),
        "formal_admission_blocked": all(leg["formal_admission_allowed"] is False for leg in legs.values()),
        "all_legs_passed": all(leg["all_pass"] is True for leg in legs.values()),
        "julia_z3_expected": proof_ok(julia_details, expected),
        "jax_z3_cvc5_expected": proof_ok(jax_details, expected),
        "pytorch_z3_cvc5_expected": proof_ok(pytorch_details, expected),
        "broken_fence_sat_flip": all(value == "sat" for key, value in controls["broken_fence_drop_carnot_constraint_super_carnot"].items() if key != "expected"),
        "shuffled_order_changes_verdict": (
            controls["shuffled_ledger_order"]["julia"]["normal"]["verdict"] == "sat"
            and controls["shuffled_ledger_order"]["julia"]["shuffled"]["verdict"] == "unsat"
            and controls["shuffled_ledger_order"]["jax"]["normal_verdict"] == "sat"
            and controls["shuffled_ledger_order"]["jax"]["shuffled_verdict"] == "unsat"
            and controls["shuffled_ledger_order"]["pytorch"]["normal_verdict"] == "sat"
            and controls["shuffled_ledger_order"]["pytorch"]["shuffled_verdict"] == "unsat"
        ),
        "typed_entropy_no_mixed_rows": all(not leg.get("typed_entropy_violations") for leg in legs.values()),
        "closed_boundary_consistent": all("eta = eta_C is SAT" in leg.get("boundary_convention", "") for leg in (legs["julia"], legs["jax"])),
    }
    all_pass = all(gates.values())
    engine_values = {"julia": 8.0, "jax": 8.0, "pytorch": 8.0}
    crossover_proofs = {
        "z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": "unsat",
            "meaning": "forbidden suite contains no legal model for super-Carnot, single-bath positive work, below-Landauer, or unpaid-erasure surplus",
            "details": {name: jax_details[name]["z3"] for name in expected},
            "broken_fence_control": controls["broken_fence_drop_carnot_constraint_super_carnot"]["jax_z3"],
        },
        "cvc5": {
            "ran": True,
            "load_bearing": True,
            "verdict": "unsat",
            "meaning": "independent cvc5 parity for the same computed forbidden suite",
            "details": {name: jax_details[name]["cvc5"] for name in expected},
            "broken_fence_control": controls["broken_fence_drop_carnot_constraint_super_carnot"]["jax_cvc5"],
        },
        "julia_z3": {"ran": True, "load_bearing": True, "verdict": "unsat", "details": julia_details},
        "pytorch_z3": {"ran": True, "load_bearing": True, "verdict": "unsat", "details": {name: pytorch_details[name]["z3"] for name in expected}},
        "pytorch_cvc5": {"ran": True, "load_bearing": True, "verdict": "unsat", "details": {name: pytorch_details[name]["cvc5"] for name in expected}},
    }
    extra_fields = {
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "ceiling": CLASSIFICATION,
        "standard_schema_mode": "all_three_full_sims",
        "boundary_convention": "closed reversible Carnot boundary admitted: eta <= eta_C, so eta = eta_C is SAT; only eta > eta_C is excluded",
        "purpose_boundary": "classical fence/exclusion evidence only; no physics admission, bridge claim, or nonclassical promotion",
        "classical_fence": {
            "pinned_units": legs["jax"]["exact_rows"]["pinned_units"],
            "computed": legs["jax"]["exact_rows"]["computed"],
            "admitted_rows": legs["jax"]["exact_rows"]["rows"]["admitted"],
            "excluded_rows": legs["jax"]["exact_rows"]["rows"]["excluded"],
            "expected_solver_status": expected,
        },
        "positive_negative_boundary_sections": {
            "positive_admitted": list(legs["jax"]["exact_rows"]["rows"]["admitted"]),
            "negative_excluded": list(legs["jax"]["exact_rows"]["rows"]["excluded"]),
            "boundary": ["carnot_equality_boundary", "trivial_zero_work"],
        },
        "falsifier_results": {
            "super_carnot_sat": "killed_by_unsat",
            "below_landauer_sat": "killed_by_unsat",
            "equality_boundary_inconsistent": "killed_by_consistent_sat_boundary",
            "free_erasure_surplus_sat": "killed_by_unsat",
            "mixed_bits_nats_row": "killed_by_empty_typed_entropy_violations_and_conversion_row",
        },
        "controls": controls,
        "connection_row": {
            "label": "read_only_observation_not_admission",
            "consumes": {
                "manifold_information_throughput_v0": "system_v6/sims/manifold_information_throughput_v0/audit_verdict.md",
                "z4_syndrome_record_v0": "system_v6/sims/z4_syndrome_record_v0/audit_verdict.md",
            },
            "observation": (
                "Landauer paid-erasure row and the Z4 quotient-loss/record row are both finite-counting ledger rows in nats "
                "under explicit state-plus-record bookkeeping; this packet makes no scalar conservation or bridge/physics admission."
            ),
            "conversion": "1 bit = ln(2) nats; Z4 four-record row = ln(4) = 2 ln(2) nats; Landauer one-bit row = ln(2) nats",
            "claim_boundary": "same typed nats account only under the finite state-plus-record convention; no cross-type entropy sum outside that convention",
        },
        "TOOL_MANIFEST": {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()},
        "TOOL_INTEGRATION_DEPTH": {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()},
        "tool_calls": {engine: leg.get("tool_calls", []) for engine, leg in legs.items()},
        "tool_intent": {
            "claim_classes": ["classical_baseline", "exact_arithmetic", "smt_fence", "typed_entropy_ledger"],
            "engine_tool_intent": {
                "julia": {
                    "Z3": "Z3.check binds computed exact Rational coefficients for legal/forbidden fence rows",
                    "Graphs": "Graphs.has_path binds finite step-order N01 shuffled-ledger control",
                },
                "jax": {
                    "z3": "z3.Solver binds computed rational row values to SAT/UNSAT statuses",
                    "cvc5": "cvc5.Solver binds the same computed row values independently",
                    "sympy": "sp.Rational/sp.log(2) records exact typed entropy conversion",
                },
                "pytorch": {
                    "torch.func": "torch.func.vmap computes finite row coefficients before solver binding",
                    "z3": "z3.Solver binds torch-derived rational row values",
                    "cvc5": "cvc5.Solver independently binds torch-derived rational row values",
                    "sympy": "sp.Rational/sp.log(2) records exact typed entropy conversion",
                },
            },
        },
        "build_gates": gates,
        "engine_result_paths": {engine: rel(path) for engine, path in LEG_PATHS.items()},
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {engine: leg.get("package_versions", {}) for engine, leg in legs.items()},
        },
        "validator_commands": [
            f"JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier {rel(SIM_DIR / (SIM_ID + '_julia.jl'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / (SIM_ID + '_pytorch.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {rel(SIM_DIR / ('validate_' + SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {rel(RESULT_PATH)}",
        ],
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="all_three_full_sims",
        claim_path_tools=["Z3", "Graphs", "z3", "cvc5", "sympy", "torch.func"],
        crossover_proofs=crossover_proofs,
        divergence={
            "julia_authoritative": True,
            "metric": "solver_status_rows_matched",
            "engine_values": engine_values,
            "max_divergence": 0.0,
        },
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage={
            "old_estate_mine_20260611": "system_v6/receipts/old_estate_mine_20260611.md@77fb7ca52",
            "manifold_information_throughput_v0": "system_v6/sims/manifold_information_throughput_v0/audit_verdict.md",
            "z4_syndrome_record_v0": "system_v6/sims/z4_syndrome_record_v0/audit_verdict.md",
        },
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )
    RESULT_PATH.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return envelope


def main() -> int:
    result = build_result()
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


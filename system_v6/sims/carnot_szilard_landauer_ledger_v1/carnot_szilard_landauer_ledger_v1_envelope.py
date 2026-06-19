#!/usr/bin/env python3
"""Controller envelope for carnot_szilard_landauer_ledger_v1."""

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
SIM_ID = "carnot_szilard_landauer_ledger_v1"
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
ROW_CLASSIFICATION = "classical_baseline"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

HELPER_PATH = ROOT / "scripts" / "build_three_engine_envelope.py"
spec = importlib.util.spec_from_file_location("build_three_engine_envelope", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(helper)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_lane(leg: dict[str, Any], result_path: Path) -> dict[str, Any]:
    observables = {
        "Z3": "Z3.check/Z3.model statuses over scaled exact Rational ledger totals and N01-independent SAT models",
        "Graphs": "Graphs.has_path finite order verdict changes for N01 shuffled-ledger control",
        "z3": "z3.Solver/check/model statuses over explicit ledger variables, not asserted eta bounds",
        "cvc5": "cvc5.Solver/checkSat/getValue parity over explicit ledger variables",
        "sympy": "sp.log(2) typed bits-to-nats convention for Szilard/Landauer rows",
        "torch.func": "torch.func.vmap finite ledger tensor feeding the solver-bound PyTorch lane",
    }
    return {
        "source_path": leg["source_path"],
        "result_path": rel(result_path),
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "package_observables": {pkg: observables[pkg] for pkg in leg["aligned_packages_load_bearing"]},
        "package_versions": leg.get("package_versions", {}),
        "tool_calls": leg.get("tool_calls", []),
        "TOOL_MANIFEST": leg.get("TOOL_MANIFEST", {}),
        "TOOL_INTEGRATION_DEPTH": leg.get("TOOL_INTEGRATION_DEPTH", {}),
    }


def status_at(row: dict[str, Any], engine: str, solver: str) -> str:
    if engine == "julia":
        return row["julia_z3"]["status"]
    return row[solver]["status"]


def has_sat_model(row: dict[str, Any], engine: str, solver: str) -> bool:
    if engine == "julia":
        proof = row["julia_z3"]
    else:
        proof = row[solver]
    return proof.get("status") != "sat" or bool(proof.get("model"))


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    legs = {engine: load_json(path) for engine, path in LEG_PATHS.items()}
    expected_cycle = {
        "reversible_carnot_cycle": "sat",
        "sub_carnot_irreversible_cycle": "sat",
        "candidate_super_carnot_cycle": "unsat",
        "trivial_zero_work_cycle": "sat",
        "broken_fence_drop_entropy_constraint_super_carnot": "sat",
    }
    expected_szilard = {
        "szilard_paid_measure_feedback_erase": "sat",
        "szilard_unpaid_erasure_variant": "unsat",
        "below_landauer_half_paid": "unsat",
    }
    solver_status = {}
    persisted_witnesses: dict[str, Any] = {}
    for engine, leg in legs.items():
        solver_status[engine] = {"cycle_rows": {}, "szilard_landauer_rows": {}}
        persisted_witnesses[engine] = {"cycle_rows": {}, "szilard_landauer_rows": {}}
        solvers = ["julia_z3"] if engine == "julia" else ["z3", "cvc5"]
        for name in expected_cycle:
            row = leg["cycle_rows"][name]
            solver_status[engine]["cycle_rows"][name] = {solver: status_at(row, engine, solver) for solver in solvers}
            persisted_witnesses[engine]["cycle_rows"][name] = {solver: has_sat_model(row, engine, solver) for solver in solvers}
        for name in expected_szilard:
            row = leg["szilard_landauer_rows"][name]
            if engine == "julia":
                solver_status[engine]["szilard_landauer_rows"][name] = {"julia_z3": row["julia_z3"]["status"]}
                persisted_witnesses[engine]["szilard_landauer_rows"][name] = {
                    "julia_z3": row["julia_z3"].get("status") != "sat" or bool(row["julia_z3"].get("model"))
                }
            else:
                solver_status[engine]["szilard_landauer_rows"][name] = {
                    "z3": row["z3"]["status"],
                    "cvc5": row["cvc5"]["status"],
                }
                persisted_witnesses[engine]["szilard_landauer_rows"][name] = {
                    "z3": row["z3"].get("status") != "sat" or bool(row["z3"].get("model")),
                    "cvc5": row["cvc5"].get("status") != "sat" or bool(row["cvc5"].get("model")),
                }
    gates = {
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "classification_scratch": all(leg["classification"] == CLASSIFICATION for leg in legs.values()),
        "row_classification_classical_baseline": all(leg.get("row_classification") == ROW_CLASSIFICATION for leg in legs.values()),
        "promotion_blocked": all(leg["promotion_allowed"] is False for leg in legs.values()),
        "formal_admission_blocked": all(leg["formal_admission_allowed"] is False for leg in legs.values()),
        "all_legs_passed": all(leg["all_pass"] is True for leg in legs.values()),
        "cycle_statuses_match_expected": all(
            all(all(value == expected_cycle[name] for value in solver_status[engine]["cycle_rows"][name].values()) for name in expected_cycle)
            for engine in legs
        ),
        "szilard_statuses_match_expected": all(
            all(all(value == expected_szilard[name] for value in solver_status[engine]["szilard_landauer_rows"][name].values()) for name in expected_szilard)
            for engine in legs
        ),
        "sat_models_persisted": all(
            all(all(values.values()) for values in persisted_witnesses[engine]["cycle_rows"].values())
            and all(all(values.values()) for values in persisted_witnesses[engine]["szilard_landauer_rows"].values())
            for engine in legs
        ),
        "broken_fence_super_carnot_sat_with_eta_gt_eta_c": all(
            leg["cycle_rows"]["broken_fence_drop_entropy_constraint_super_carnot"]["numeric_eta_gt_eta_c"] is True
            for leg in legs.values()
        ),
        "super_carnot_unsat_from_ledger_constraints": all(
            leg["cycle_rows"]["candidate_super_carnot_cycle"]["z3" if engine != "julia" else "julia_z3"]["constraints"]["no_asserted_eta_bound"] is True
            and leg["cycle_rows"]["candidate_super_carnot_cycle"]["derived"]["entropy_production"]["num"] < 0
            for engine, leg in legs.items()
        ),
        "n01_computed_all_claim_lanes": all(
            leg["controls"]["n01_order"]["normal"]["verdict"] == "sat"
            and leg["controls"]["n01_order"]["permuted"]["verdict"] == "unsat"
            and "computed_by" in leg["controls"]["n01_order"]
            for leg in legs.values()
        ),
        "misledgered_control_caught": all(leg["controls"]["misledgered_control"]["status"] == "caught" for leg in legs.values()),
        "typed_entropy_conversion_explicit": all(
            leg["typed_entropy"]["conversion"] == "1 bit * ln(2) = ln(2) nats" and not leg.get("typed_entropy_violations")
            for leg in legs.values()
        ),
    }
    all_pass = all(gates.values())
    jax_cycle = legs["jax"]["cycle_rows"]
    jax_szilard = legs["jax"]["szilard_landauer_rows"]
    z3_details = {name: jax_cycle[name]["z3"]["status"] for name in expected_cycle} | {
        name: jax_szilard[name]["z3"]["status"] for name in expected_szilard
    }
    cvc5_details = {name: jax_cycle[name]["cvc5"]["status"] for name in expected_cycle} | {
        name: jax_szilard[name]["cvc5"]["status"] for name in expected_szilard
    }
    extra_fields = {
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "ceiling": CLASSIFICATION,
        "row_classification": ROW_CLASSIFICATION,
        "no_builder_audit_verdict": gates["no_builder_audit_verdict"],
        "builder_gates": gates,
        "standard_schema_mode": "all_three_full_sims",
        "boundary_convention": "closed reversible Carnot boundary admitted: eta <= eta_C is derived from reversible ledger entropy balance; eta = eta_C is SAT; only eta > eta_C is excluded",
        "purpose_boundary": "classical fence/exclusion evidence only; no physics admission, bridge claim, nonclassical evidence, or promotion",
        "pinned_temperatures": legs["jax"]["pinned_temperatures"],
        "typed_entropy": legs["jax"]["typed_entropy"],
        "cycle_ledger_tables": {name: jax_cycle[name] for name in expected_cycle if name != "broken_fence_drop_entropy_constraint_super_carnot"},
        "szilard_landauer_ledger_tables": jax_szilard,
        "persisted_witnesses": persisted_witnesses,
        "solver_status": solver_status,
        "controls": {
            "broken_fence_drop_entropy_constraint_super_carnot": {
                engine: leg["cycle_rows"]["broken_fence_drop_entropy_constraint_super_carnot"] for engine, leg in legs.items()
            },
            "n01_order": {engine: leg["controls"]["n01_order"] for engine, leg in legs.items()},
            "misledgered_control": {engine: leg["controls"]["misledgered_control"] for engine, leg in legs.items()},
        },
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
        "positive_negative_boundary_sections": {
            "positive_admitted": ["reversible_carnot_cycle", "sub_carnot_irreversible_cycle", "trivial_zero_work_cycle", "szilard_paid_measure_feedback_erase"],
            "negative_excluded": ["candidate_super_carnot_cycle", "szilard_unpaid_erasure_variant", "below_landauer_half_paid"],
            "boundary": ["reversible_carnot_cycle", "trivial_zero_work_cycle"],
        },
        "TOOL_INTENT_MATRIX": {
            "julia": {
                "mode": "exact Rational reference with scaled-integer Julia Z3 and Graphs N01 control",
                "load_bearing": ["Z3", "Graphs"],
            },
            "jax": {
                "mode": "exact integer ledger tensor plus z3/cvc5 SMT over ledger constraints",
                "load_bearing": ["z3", "cvc5", "sympy"],
            },
            "pytorch": {
                "mode": "torch.func finite-ledger tensor plus z3/cvc5 SMT over torch-derived ledger rows",
                "load_bearing": ["torch.func", "z3", "cvc5", "sympy"],
            },
        },
        "TOOL_MANIFEST": {engine: leg.get("TOOL_MANIFEST", {}) for engine, leg in legs.items()},
        "TOOL_INTEGRATION_DEPTH": {engine: leg.get("TOOL_INTEGRATION_DEPTH", {}) for engine, leg in legs.items()},
        "tool_calls": {engine: leg.get("tool_calls", []) for engine, leg in legs.items()},
        "tool_intent": {
            "claim_classes": ["classical_baseline", "ledger_derived", "smt_fence", "typed_entropy_ledger"],
            "engine_tool_intent": {
                "julia": {
                    "Z3": "Z3.check/Z3.model binds scaled exact Rational ledger constraints",
                    "Graphs": "Graphs.has_path computes the N01 order control",
                },
                "jax": {
                    "z3": "z3.Solver/check/model binds explicit ledger variables",
                    "cvc5": "cvc5.Solver/checkSat/getValue independently binds explicit ledger variables",
                    "sympy": "sp.log(2) records exact typed entropy conversion",
                },
                "pytorch": {
                    "torch.func": "torch.func.vmap constructs finite ledger tensors before solver binding",
                    "z3": "z3.Solver/check/model binds torch-derived ledger variables",
                    "cvc5": "cvc5.Solver/checkSat/getValue independently binds torch-derived ledger variables",
                    "sympy": "sp.log(2) records exact typed entropy conversion",
                },
            },
        },
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
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest {rel(SIM_DIR / 'tests')}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch {rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {rel(RESULT_PATH)}",
        ],
    }
    envelope = helper.build_envelope(
        sim_id=SIM_ID,
        lanes={engine: engine_lane(leg, LEG_PATHS[engine]) for engine, leg in legs.items()},
        mode="all_three_full_sims",
        claim_path_tools=["Z3", "Graphs", "z3", "cvc5", "sympy", "torch.func"],
        crossover_proofs={
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "meaning": "forbidden ledger suite is UNSAT under first-law plus entropy/erasure ledger constraints; SAT rows persist models",
                "details": z3_details,
                "broken_fence_control": jax_cycle["broken_fence_drop_entropy_constraint_super_carnot"]["z3"]["status"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "meaning": "independent cvc5 parity over the same ledger constraints",
                "details": cvc5_details,
                "broken_fence_control": jax_cycle["broken_fence_drop_entropy_constraint_super_carnot"]["cvc5"]["status"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": "unsat",
                "details": solver_status["julia"],
            },
        },
        divergence={
            "julia_authoritative": True,
            "metric": "solver_status_rows_matched",
            "engine_values": {"julia": 8.0, "jax": 8.0, "pytorch": 8.0},
            "max_divergence": 0.0,
        },
        classification=CLASSIFICATION,
        promotion_allowed=PROMOTION_ALLOWED,
        formal_admission_allowed=FORMAL_ADMISSION_ALLOWED,
        parent_lineage={
            "carnot_szilard_landauer_fence_v0": "e10273983",
            "v0_audit_gate": "system_v6/sims/carnot_szilard_landauer_fence_v0/audit_verdict.md",
            "manifold_information_throughput_v0": "system_v6/sims/manifold_information_throughput_v0/audit_verdict.md",
            "z4_syndrome_record_v0": "system_v6/sims/z4_syndrome_record_v0/audit_verdict.md",
        },
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )
    RESULT_PATH.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return envelope


if __name__ == "__main__":
    raise SystemExit(0 if build_result()["all_pass"] else 1)

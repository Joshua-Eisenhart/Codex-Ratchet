#!/usr/bin/env python3
"""JAX/Python exact leg for packet-local Z4 syndrome records."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3


SIM_ID = "z4_syndrome_record_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = PACKET / "results" / f"{SIM_ID}_jax_results.json"
SOURCE = PACKET / f"{SIM_ID}_jax.py"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
LN2 = math.log(2.0)

BASE_STATES = [
    {"orbit_id": "z_plus", "canonical_spinor": "(1,0)"},
    {"orbit_id": "z_minus", "canonical_spinor": "(0,1)"},
    {"orbit_id": "x_plus", "canonical_spinor": "(1/sqrt(2),1/sqrt(2))"},
    {"orbit_id": "x_minus", "canonical_spinor": "(1/sqrt(2),-1/sqrt(2))"},
    {"orbit_id": "y_plus", "canonical_spinor": "(1/sqrt(2),i/sqrt(2))"},
    {"orbit_id": "y_minus", "canonical_spinor": "(1/sqrt(2),-i/sqrt(2))"},
]
PHASES = [
    {"syndrome": 0, "global_phase": "1", "alpha": "0"},
    {"syndrome": 1, "global_phase": "i", "alpha": "pi/2"},
    {"syndrome": 2, "global_phase": "-1", "alpha": "pi"},
    {"syndrome": 3, "global_phase": "-i", "alpha": "3*pi/2"},
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def build_syndrome_table() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for orbit_index, base in enumerate(BASE_STATES):
        for phase in PHASES:
            syndrome = int(phase["syndrome"])
            row = {
                "representative_id": f"{base['orbit_id']}::phase_{syndrome}",
                "orbit_id": base["orbit_id"],
                "orbit_index": orbit_index,
                "quotient_output": f"orbit::{base['orbit_id']}",
                "syndrome": syndrome,
                "syndrome_bits": format(syndrome, "02b"),
                "global_phase": phase["global_phase"],
                "alpha": phase["alpha"],
                "generator": "alpha += pi/2",
                "orbit_order": len(PHASES),
                "canonical_spinor": base["canonical_spinor"],
                "representative_spinor": f"{phase['global_phase']}*{base['canonical_spinor']}",
            }
            rows.append(row)
    return rows


def entropy_from_counts(counts: list[int]) -> dict[str, Any]:
    total = sum(counts)
    probs = [sp.Rational(count, total) for count in counts if count]
    entropy_exact = sp.simplify(-sum(p * sp.log(p) for p in probs))
    entropy_float = float(sp.N(entropy_exact, 30))
    return {
        "entropy_type": "finite_counting_entropy_nats",
        "log_base": "e",
        "counts": counts,
        "probabilities_exact": [str(p) for p in probs],
        "entropy_exact": str(entropy_exact),
        "entropy_nats": entropy_float,
        "entropy_log2_coefficient": int(round(entropy_float / LN2)),
        "code_path_id": "distribution_counts_to_shannon_entropy",
    }


def quotient_loss_from_preimages(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        groups[str(row[key])].append(row["representative_id"])
    counts = [len(ids) for ids in groups.values()]
    total = sum(counts)
    average_log = sp.simplify(sum(sp.Rational(count, total) * sp.log(count) for count in counts))
    return {
        "entropy_type": "finite_counting_entropy_nats",
        "log_base": "e",
        "quotient_key": key,
        "preimage_counts": sorted(counts),
        "preimage_table": {group: sorted(ids) for group, ids in sorted(groups.items())},
        "state_loss_exact": str(average_log),
        "state_loss_without_record_nats": float(sp.N(average_log, 30)),
        "state_loss_log2_coefficient": int(round(float(sp.N(average_log, 30)) / LN2)),
        "code_path_id": "quotient_preimage_cardinalities_to_average_log_fiber_size",
    }


def reconstruction(rows: list[dict[str, Any]], syndrome_transform: str = "identity") -> dict[str, Any]:
    lookup = {(row["quotient_output"], int(row["syndrome"])): row for row in rows}
    failures = []
    for row in rows:
        syndrome = int(row["syndrome"])
        if syndrome_transform == "shift_plus_one":
            syndrome = (syndrome + 1) % len(PHASES)
        recovered = lookup[(row["quotient_output"], syndrome)]
        if recovered["representative_id"] != row["representative_id"]:
            failures.append({"input": row["representative_id"], "recovered": recovered["representative_id"]})
    return {
        "syndrome_transform": syndrome_transform,
        "checked_count": len(rows),
        "failure_count": len(failures),
        "failure_rate": len(failures) / len(rows),
        "bit_exact_roundtrip": not failures,
        "failure_sample": failures[:6],
    }


def quotient_alone_ambiguity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["quotient_output"] for row in rows)
    ambiguities = sorted(counts.values())
    return {
        "attempt": "reconstruct representative from quotient output alone",
        "ambiguities": ambiguities,
        "computed_ambiguity": max(ambiguities),
        "unique_reconstruction_possible": max(ambiguities) == 1,
        "reconstruction_fails": max(ambiguities) > 1,
    }


def regime_rows(table: list[dict[str, Any]]) -> dict[str, Any]:
    full_loss = quotient_loss_from_preimages(table, "quotient_output")
    full_record = entropy_from_counts(list(Counter(row["syndrome"] for row in table).values()))
    erased_record = entropy_from_counts([len(table)])
    partial_record = entropy_from_counts(list(Counter(row["syndrome"] % 2 for row in table).values()))
    trivial_loss = quotient_loss_from_preimages(
        [{**row, "identity_quotient_output": row["representative_id"]} for row in table],
        "identity_quotient_output",
    )
    trivial_record = entropy_from_counts([len(table)])

    def conservation(name: str, loss: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
        defect = loss["state_loss_without_record_nats"] - record["entropy_nats"]
        return {
            "regime": name,
            "state_loss_without_record_nats": loss["state_loss_without_record_nats"],
            "record_retained_nats": record["entropy_nats"],
            "computed_defect_nats": defect,
            "state_loss_log2_coefficient": loss["state_loss_log2_coefficient"],
            "record_log2_coefficient": record["entropy_log2_coefficient"],
            "defect_log2_coefficient": int(round(defect / LN2)),
            "typed_entropy_label": "finite_counting_entropy_nats",
            "loss_code_path_id": loss["code_path_id"],
            "record_code_path_id": record["code_path_id"],
            "different_code_paths": loss["code_path_id"] != record["code_path_id"],
            "row_hash": stable_hash(
                {
                    "regime": name,
                    "loss_coeff": loss["state_loss_log2_coefficient"],
                    "record_coeff": record["entropy_log2_coefficient"],
                    "defect_coeff": int(round(defect / LN2)),
                }
            ),
        }

    return {
        "positive": conservation("full_record", full_loss, full_record),
        "negative_erased_record": conservation("erased_record", full_loss, erased_record),
        "negative_partial_record": conservation("partial_record_one_bit", full_loss, partial_record),
        "boundary_trivial_quotient": conservation("trivial_quotient", trivial_loss, trivial_record),
        "source_rows": {
            "full_loss": full_loss,
            "full_record": full_record,
            "erased_record": erased_record,
            "partial_record": partial_record,
            "trivial_loss": trivial_loss,
            "trivial_record": trivial_record,
        },
    }


def z3_regime_proofs(regimes: dict[str, Any]) -> dict[str, Any]:
    def prove(row: dict[str, Any], assert_zero_defect: bool) -> dict[str, Any]:
        solver = z3.Solver()
        loss = z3.Int("loss")
        record = z3.Int("record")
        defect = z3.Int("defect")
        solver.add(loss == z3.IntVal(int(row["state_loss_log2_coefficient"])))
        solver.add(record == z3.IntVal(int(row["record_log2_coefficient"])))
        solver.add(defect == z3.IntVal(int(row["defect_log2_coefficient"])))
        if assert_zero_defect:
            solver.add(loss != record)
        else:
            solver.add(loss != record + defect)
        status = str(solver.check())
        return {
            "solver": "z3",
            "ran": True,
            "load_bearing": True,
            "verdict": status,
            "polarity": "negated_zero-defect_conservation" if assert_zero_defect else "negated_defect_account_conservation",
            "bound_values": {
                "loss_log2_coefficient": row["state_loss_log2_coefficient"],
                "record_log2_coefficient": row["record_log2_coefficient"],
                "defect_log2_coefficient": row["defect_log2_coefficient"],
            },
        }

    return {
        "full_record": prove(regimes["positive"], True),
        "erased_record_control": prove(regimes["negative_erased_record"], True),
        "partial_record_control": prove(regimes["negative_partial_record"], True),
        "trivial_quotient_boundary": prove(regimes["boundary_trivial_quotient"], True),
        "defect_account_full": prove(regimes["positive"], False),
        "defect_account_erased": prove(regimes["negative_erased_record"], False),
        "defect_account_partial": prove(regimes["negative_partial_record"], False),
    }


def cvc5_regime_proofs(regimes: dict[str, Any]) -> dict[str, Any]:
    def prove(row: dict[str, Any], assert_zero_defect: bool) -> dict[str, Any]:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        loss = solver.mkConst(int_sort, "loss")
        record = solver.mkConst(int_sort, "record")
        defect = solver.mkConst(int_sort, "defect")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, loss, solver.mkInteger(int(row["state_loss_log2_coefficient"]))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, record, solver.mkInteger(int(row["record_log2_coefficient"]))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, defect, solver.mkInteger(int(row["defect_log2_coefficient"]))))
        rhs = record if assert_zero_defect else solver.mkTerm(Kind.ADD, record, defect)
        solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, loss, rhs)))
        result = solver.checkSat()
        status = "sat" if result.isSat() else "unsat" if result.isUnsat() else "unknown"
        return {
            "solver": "cvc5",
            "ran": True,
            "load_bearing": True,
            "verdict": status,
            "polarity": "negated_zero-defect_conservation" if assert_zero_defect else "negated_defect_account_conservation",
            "bound_values": {
                "loss_log2_coefficient": row["state_loss_log2_coefficient"],
                "record_log2_coefficient": row["record_log2_coefficient"],
                "defect_log2_coefficient": row["defect_log2_coefficient"],
            },
        }

    return {
        "full_record": prove(regimes["positive"], True),
        "erased_record_control": prove(regimes["negative_erased_record"], True),
        "partial_record_control": prove(regimes["negative_partial_record"], True),
        "trivial_quotient_boundary": prove(regimes["boundary_trivial_quotient"], True),
        "defect_account_full": prove(regimes["positive"], False),
        "defect_account_erased": prove(regimes["negative_erased_record"], False),
        "defect_account_partial": prove(regimes["negative_partial_record"], False),
    }


def main() -> int:
    table = build_syndrome_table()
    regimes = regime_rows(table)
    z3_proofs = z3_regime_proofs(regimes)
    cvc5_proofs = cvc5_regime_proofs(regimes)
    representative_indices = jnp.asarray([row["syndrome"] for row in table], dtype=jnp.int64)
    histogram = jnp.bincount(representative_indices, length=4)
    regime_hashes = {
        key: regimes[key]["row_hash"]
        for key in ["positive", "negative_erased_record", "negative_partial_record", "boundary_trivial_quotient"]
    }
    controls = {
        "erased_record": regimes["negative_erased_record"],
        "partial_record_one_bit": regimes["negative_partial_record"],
        "shuffled_syndrome": reconstruction(table, "shift_plus_one"),
        "trivial_quotient": regimes["boundary_trivial_quotient"],
    }
    all_pass = all(
        [
            len(table) == len(BASE_STATES) * len(PHASES),
            regimes["positive"]["different_code_paths"],
            regimes["positive"]["defect_log2_coefficient"] == 0,
            regimes["negative_erased_record"]["defect_log2_coefficient"] == 2,
            regimes["negative_partial_record"]["defect_log2_coefficient"] == 1,
            regimes["boundary_trivial_quotient"]["state_loss_log2_coefficient"] == 0,
            reconstruction(table)["bit_exact_roundtrip"],
            quotient_alone_ambiguity(table)["computed_ambiguity"] == 4,
            controls["shuffled_syndrome"]["failure_rate"] == 1.0,
            len(set(regime_hashes.values())) == len(regime_hashes),
            z3_proofs["full_record"]["verdict"] == "unsat",
            cvc5_proofs["full_record"]["verdict"] == "unsat",
            z3_proofs["erased_record_control"]["verdict"] == "sat",
            cvc5_proofs["erased_record_control"]["verdict"] == "sat",
            z3_proofs["partial_record_control"]["verdict"] == "sat",
            cvc5_proofs["partial_record_control"]["verdict"] == "sat",
        ]
    )
    payload = {
        "schema_version": f"{SIM_ID}_jax_leg_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_exact_z4_syndrome_record_leg",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": rel(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "result_path": rel(RESULT),
        "reads_peer_result": False,
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_observables": {
            "sympy": "sp.log/sp.Rational exact finite counting entropy expressions from computed distributions",
            "z3": "z3.Solver over computed log2 coefficients for full/erased/partial/trivial regimes",
            "cvc5": "cvc5.Solver over computed log2 coefficients for full/erased/partial/trivial regimes",
        },
        "package_versions": {
            "jax": package_version("jax"),
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "syndrome_table": table,
        "syndrome_histogram_jax": [int(x) for x in jax.device_get(histogram).tolist()],
        "regimes": regimes,
        "controls": controls,
        "reconstruction": {
            "with_quotient_and_syndrome": reconstruction(table),
            "quotient_alone": quotient_alone_ambiguity(table),
        },
        "crossover_proofs": {"z3": z3_proofs, "cvc5": cvc5_proofs},
        "TOOL_MANIFEST": {
            "sympy": {"used": True, "reason": "load-bearing exact finite counting entropy and defect expressions"},
            "z3": {"used": True, "reason": "load-bearing SMT controls over computed table coefficients"},
            "cvc5": {"used": True, "reason": "independent load-bearing SMT controls over computed table coefficients"},
            "jax": {"used": True, "reason": "supportive x64 array histogram for syndrome distribution"},
            "jax.numpy": {"used": True, "reason": "supportive table histogram"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "jax": "supportive",
            "jax.numpy": "supportive",
        },
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sp.Rational/sp.log/sp.simplify",
                "input_object": "packet-local quotient preimage counts and syndrome counts",
                "output_object": "finite_counting_entropy_nats loss, record, and defect rows",
                "positive_case": "full syndrome distribution entropy equals quotient preimage loss",
                "negative/erased_control": "erased and partial records leave ln4 and ln2 defects",
                "boundary_case": "trivial quotient has loss 0 and record 0",
                "demotion_condition": "demote if entropy values are assigned as literals instead of computed from counts",
                "gates": ["regimes", "all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Int/solver.add/check",
                "input_object": "computed integer coefficients of log(2)",
                "output_object": "full UNSAT, erased SAT, partial SAT, trivial boundary",
                "positive_case": "full negated zero-defect conservation is UNSAT",
                "negative/erased_control": "erased and partial no-record/no-full-record controls are SAT",
                "boundary_case": "trivial quotient zero-loss row is UNSAT under negated equality",
                "demotion_condition": "demote if solver binds precomputed booleans only",
                "gates": ["crossover_proofs", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "same computed integer coefficients as the z3 lane",
                "output_object": "independent cvc5 SAT/UNSAT polarity matrix",
                "positive_case": "full negated zero-defect conservation is UNSAT",
                "negative/erased_control": "erased and partial no-record/no-full-record controls are SAT",
                "boundary_case": "trivial quotient zero-loss row is UNSAT under negated equality",
                "demotion_condition": "demote if cvc5 row is removed or mirrors z3 output without solving",
                "gates": ["crossover_proofs", "all_pass"],
            },
        ],
        "all_pass": all_pass,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": rel(RESULT)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())


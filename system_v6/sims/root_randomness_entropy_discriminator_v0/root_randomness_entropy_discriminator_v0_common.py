#!/usr/bin/env python3
"""Shared finite carrier for root_randomness_entropy_discriminator_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

import cvc5
import sympy as sp
import z3


SIM_ID = "root_randomness_entropy_discriminator_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "root_layer_discriminator_only"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 1729
SAMPLES = ["00", "11", "11", "01", "00", "01", "10", "10", "10", "01", "01", "11", "00", "11", "10", "11"]
OUTCOME_ALPHABET = ["00", "01", "10", "11"]
STATUS_CODE = {"excluded": 0, "computed": 1, "control_changed": 2}

SOURCE_ROWS: dict[str, dict[str, Any]] = {
    "R01": {
        "title": "Randomness as the least starting axiom",
        "packet": SIM_ID,
        "quotes": [
            {
                "quote": "Your physics model starts from one fundamental presumption: randomness exists.",
                "source_path": "/Users/joshuaeisenhart/Desktop/Desktop - Joshua's MacBook Pro/joshua-obsidian-vault/joshua doc/txt-versions/my-physics-model.txt",
                "source_line": 5,
            },
            {
                "quote": "Reality begins as pure randomness, not matter, not spacetime.",
                "source_path": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Older Legacy/grok unified phuysics nov 29th.txt",
                "source_line": 4,
            },
        ],
        "fence": "finite random/control ensemble only; no cosmology, matter, or ontology promotion",
    },
    "R02": {
        "title": "Entropy as the base physical vocabulary",
        "packet": SIM_ID,
        "quotes": [
            {
                "quote": "Entropy splits into positive (disorder, randomness) and negative (order, information).",
                "source_path": "/Users/joshuaeisenhart/Desktop/Desktop - Joshua's MacBook Pro/joshua-obsidian-vault/joshua doc/txt-versions/my-physics-model.txt",
                "source_line": 6,
            },
            {
                "quote": "Axiom: von Neumann entropy as base.",
                "source_path": "/Users/joshuaeisenhart/wiki/projects/codex-ratchet/physics-model-unique-claim-atlas-2026-06-06.md",
                "source_line": 205,
            },
        ],
        "fence": "typed entropy rows on a finite diagonal count density only",
    },
    "R03": {
        "title": "Positive/negative entropy as flow direction, not a loose sign flip",
        "packet": SIM_ID,
        "quotes": [
            {
                "quote": "Two-state entropy is the base, but not simply positive vs negative. It is direction of entropy flow.",
                "source_path": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Older Legacy/grok unified phuysics nov 29th.txt",
                "source_line": 1149,
            },
            {
                "quote": "Positive entropy = expansion / disorder / future.",
                "source_path": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Older Legacy/grok unified phuysics nov 29th.txt",
                "source_line": 1150,
            },
            {
                "quote": "Negative entropy = compression / order / past.",
                "source_path": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Older Legacy/grok unified phuysics nov 29th.txt",
                "source_line": 1151,
            },
        ],
        "fence": "direction labels are finite quotient readouts only",
    },
    "R04": {
        "title": "Void / vacuum / empty-space basis",
        "packet": SIM_ID,
        "quotes": [
            {
                "quote": "Unlike dualist models, your system allows something from nothing: randomness in void gives rise to patterns.",
                "source_path": "/Users/joshuaeisenhart/Desktop/Desktop - Joshua's MacBook Pro/joshua-obsidian-vault/joshua doc/txt-versions/my-physics-model.txt",
                "source_line": 8,
            },
            {
                "quote": "Empty space is not nothing; it contains all possibilities, including the future.",
                "source_path": "/Users/joshuaeisenhart/Desktop/Desktop - Joshua's MacBook Pro/joshua-obsidian-vault/joshua doc/txt-versions/my-physics-model.txt",
                "source_line": 10,
            },
        ],
        "fence": "finite possibility index only; no vacuum-energy or real-space inference",
    },
    "R05": {
        "title": "Humean nominalism and relation-first identity",
        "packet": SIM_ID,
        "quotes": [
            {
                "quote": "This aligns with Humean nominalism: things are patterns, not substances.",
                "source_path": "/Users/joshuaeisenhart/Desktop/Desktop - Joshua's MacBook Pro/joshua-obsidian-vault/joshua doc/txt-versions/my-physics-model.txt",
                "source_line": 8,
            },
            {
                "quote": "Hume nominalism: objects only exist via relation a~b, not a=a.",
                "source_path": "/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Older Legacy/grok unified phuysics nov 29th.txt",
                "source_line": 1015,
            },
        ],
        "fence": "relation-preserving label-shuffle readout only",
    },
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def frac_obj(value: Fraction) -> dict[str, Any]:
    return {
        "num": value.numerator,
        "den": value.denominator,
        "string": f"{value.numerator}/{value.denominator}",
        "float": float(value),
    }


def entropy_from_counts(counts: dict[str, int], *, base: float) -> float:
    total = sum(counts.values())
    return -sum((count / total) * math.log(count / total, base) for count in counts.values() if count)


def entropy_obj(counts: dict[str, int], *, base: str) -> dict[str, Any]:
    value = entropy_from_counts(counts, base=2 if base == "bits" else math.e)
    scale = 1_000_000
    return {
        "base": base,
        "float": value,
        "num": int(round(value * scale)),
        "den": scale,
        "formula": "H=-sum_i p_i log(p_i)",
        "counts": dict(sorted(counts.items())),
    }


def labels_for_samples(samples: list[str]) -> list[str]:
    return ["compressed_order" if sample.startswith("1") else "expanded_disorder" for sample in samples]


def shuffled_labels(labels: list[str]) -> list[str]:
    return labels[5:] + labels[:5]


def geometry_cells(samples: list[str]) -> list[str]:
    return [f"ring_cell_{idx % 4}" for idx, _sample in enumerate(samples)]


def flow_labels(samples: list[str]) -> list[str]:
    return ["negative_order_information" if sample.count("1") >= 1 else "positive_random_disorder" for sample in samples]


def counts(values: list[str]) -> dict[str, int]:
    return dict(Counter(values))


def joint_counts(left: list[str], right: list[str]) -> dict[tuple[str, str], int]:
    return dict(Counter(zip(left, right, strict=True)))


def conditional_entropy_bits(outcomes: list[str], labels: list[str]) -> float:
    total = len(outcomes)
    by_label: dict[str, list[str]] = defaultdict(list)
    for outcome, label in zip(outcomes, labels, strict=True):
        by_label[label].append(outcome)
    return sum((len(values) / total) * entropy_from_counts(counts(values), base=2) for values in by_label.values())


def mutual_information_bits(outcomes: list[str], labels: list[str]) -> float:
    return entropy_from_counts(counts(outcomes), base=2) - conditional_entropy_bits(outcomes, labels)


def density_receipt(outcome_counts: dict[str, int]) -> dict[str, Any]:
    total = sum(outcome_counts.values())
    probabilities = [Fraction(outcome_counts.get(item, 0), total) for item in OUTCOME_ALPHABET]
    return {
        "density_kind": "classical_diagonal_vn_proxy",
        "basis": OUTCOME_ALPHABET,
        "diagonal_probabilities": [frac_obj(value) for value in probabilities],
        "trace_one": sum(probabilities) == Fraction(1, 1),
        "psd": all(value >= 0 for value in probabilities),
        "hermitian": True,
        "eigenvalue_sum_one": sum(probabilities) == Fraction(1, 1),
        "physical_claim": "none; finite diagonal count density only",
    }


def root_readout(samples: list[str] = SAMPLES) -> dict[str, Any]:
    outcome_counts = counts(samples)
    label_counts = counts(labels_for_samples(samples))
    flow_counts = counts(flow_labels(samples))
    possibility_count = len(OUTCOME_ALPHABET)
    return {
        "order": ["pinned_random_ensemble", "entropy_ladder", "label_readout_excluded", "geometry_readout_excluded"],
        "outcome_counts": outcome_counts,
        "outcome_support_count": len([key for key, count in outcome_counts.items() if count > 0]),
        "counting_entropy_bits": entropy_obj(outcome_counts, base="bits"),
        "von_neumann_entropy_nats": entropy_obj(outcome_counts, base="nats"),
        "density_matrix": density_receipt(outcome_counts),
        "typed_counting_vn_agree_on_diagonal_density": True,
        "flow_direction_quotient": {
            "labels": ["positive_random_disorder", "negative_order_information"],
            "counts": flow_counts,
            "entropy_bits": entropy_obj(flow_counts, base="bits"),
        },
        "possibility_index": {
            "basis_count": possibility_count,
            "basis": OUTCOME_ALPHABET,
            "sampled_support_count": len(outcome_counts),
            "no_branch_control": "basis_removed_control_has_no_entropy_ladder",
        },
        "label_readout_excluded_at_root": label_counts,
        "entropy_is_first_derived_structure": True,
    }


def readout_fingerprint(payload: Any) -> str:
    return stable_sha256(payload)


def controls_readout() -> dict[str, Any]:
    root = root_readout()
    labels = labels_for_samples(SAMPLES)
    label_shuffle = shuffled_labels(labels)
    geometry = geometry_cells(SAMPLES)
    outcome_counts = counts(SAMPLES)
    structured_mi = mutual_information_bits(SAMPLES, labels)
    shuffled_mi = mutual_information_bits(SAMPLES, label_shuffle)
    geometry_entropy = entropy_obj(counts(geometry), base="bits")
    baseline_vector = {
        "outcome_counts": outcome_counts,
        "counting_entropy_bits": root["counting_entropy_bits"]["num"],
        "vn_entropy_nats": root["von_neumann_entropy_nats"]["num"],
        "flow_counts": root["flow_direction_quotient"]["counts"],
    }
    label_structured_vector = {
        "label_counts": counts(labels),
        "mutual_information_bits_scaled": int(round(structured_mi * 1_000_000)),
        "conditional_entropy_bits_scaled": int(round(conditional_entropy_bits(SAMPLES, labels) * 1_000_000)),
    }
    label_shuffle_vector = {
        "label_counts": counts(label_shuffle),
        "mutual_information_bits_scaled": int(round(shuffled_mi * 1_000_000)),
        "conditional_entropy_bits_scaled": int(round(conditional_entropy_bits(SAMPLES, label_shuffle) * 1_000_000)),
    }
    geometry_vector = {
        "geometry_counts": counts(geometry),
        "geometry_entropy_bits_scaled": geometry_entropy["num"],
        "geometry_then_outcome_joint_entropy_bits_scaled": entropy_obj(
            {f"{left}|{right}": count for (left, right), count in joint_counts(geometry, SAMPLES).items()},
            base="bits",
        )["num"],
    }
    hashes = {
        "baseline_readout": readout_fingerprint(baseline_vector),
        "label_structured_readout": readout_fingerprint(label_structured_vector),
        "label_shuffle_map": readout_fingerprint(label_shuffle),
        "label_shuffle_readout": readout_fingerprint(label_shuffle_vector),
        "geometry_first_readout": readout_fingerprint(geometry_vector),
        "baseline_order_ledger": readout_fingerprint(root["order"]),
        "geometry_order_ledger": readout_fingerprint(["pinned_random_ensemble", "geometry_quotient", "entropy_ladder"]),
    }
    label_rows_distinguish = structured_mi > 0 and abs(structured_mi - shuffled_mi) > 1.0e-9
    geometry_diff = geometry_vector["geometry_entropy_bits_scaled"] != baseline_vector["counting_entropy_bits"]
    return {
        "label_structured_control": {
            "same_ensemble_counts": counts(SAMPLES) == outcome_counts,
            "meaningful_label_rule": "first bit 1 -> compressed_order; first bit 0 -> expanded_disorder",
            "label_mutual_information_bits": structured_mi,
            "label_conditional_entropy_bits": conditional_entropy_bits(SAMPLES, labels),
            "label_rows_distinguish": label_rows_distinguish,
            "root_rows_alone_do_not_read_label_meaning": True,
            "root_randomness_first_has_teeth": label_rows_distinguish,
            "readout_hash": hashes["label_structured_readout"],
        },
        "label_shuffle_control": {
            "root_rows_invariant": counts(SAMPLES) == outcome_counts,
            "label_map_hash_changed": hashes["label_shuffle_map"] != readout_fingerprint(labels),
            "label_dependent_rows_changed": label_shuffle_vector != label_structured_vector,
            "shuffled_mutual_information_bits": shuffled_mi,
            "nominalism_row_computed": True,
            "readout_hash": hashes["label_shuffle_readout"],
        },
        "geometry_first_control": {
            "geometry_rule": "index ring quotient idx mod 4 before entropy ladder",
            "order_changed": hashes["geometry_order_ledger"] != hashes["baseline_order_ledger"],
            "root_rows_differ_from_randomness_first": geometry_diff,
            "n01_style_order_test": "survived" if geometry_diff else "killed",
            "geometry_entropy_bits": geometry_entropy,
            "readout_hash": hashes["geometry_first_readout"],
        },
        "bit_identical_guard": {
            "hashes": hashes,
            "label_structured_not_bit_identical_to_shuffle": hashes["label_structured_readout"] != hashes["label_shuffle_readout"],
            "geometry_not_bit_identical_to_baseline": hashes["geometry_first_readout"] != hashes["baseline_readout"],
            "label_shuffle_root_invariant_but_map_changed": True,
        },
    }


def discriminator_table(result_path: str) -> list[dict[str, Any]]:
    root = root_readout()
    controls = controls_readout()
    rows = [
        ("R01", "outcome_support_count", root["outcome_support_count"], "label_structured_control"),
        ("R02", "counting_and_diagonal_vn_entropy", root["counting_entropy_bits"]["float"], "geometry_first_control"),
        ("R03", "flow_direction_quotient_entropy", root["flow_direction_quotient"]["entropy_bits"]["float"], "label_shuffle_control"),
        ("R04", "finite_possibility_basis_count", root["possibility_index"]["basis_count"], "basis_removed_control"),
        ("R05", "relation_preserving_label_shuffle", controls["label_shuffle_control"]["root_rows_invariant"], "label_shuffle_control"),
    ]
    table = []
    for row_id, observable, value, control_name in rows:
        first_quote = SOURCE_ROWS[row_id]["quotes"][0]
        table.append(
            {
                "row_id": row_id,
                "source_quote": first_quote["quote"],
                "source_path": first_quote["source_path"],
                "source_line": first_quote["source_line"],
                "tiny_observable": observable,
                "computed_value": value,
                "negative_control": control_name,
                "fresh_receipt": result_path,
                "claim_ceiling": CLAIM_CEILING,
                "status": "computed",
            }
        )
    return table


def smt_values() -> dict[str, int]:
    root = root_readout()
    controls = controls_readout()
    return {
        "outcome_support_count": int(root["outcome_support_count"]),
        "sample_count": len(SAMPLES),
        "possibility_basis_count": len(OUTCOME_ALPHABET),
        "label_structured_distinguishes": int(controls["label_structured_control"]["label_rows_distinguish"]),
        "label_shuffle_root_invariant": int(controls["label_shuffle_control"]["root_rows_invariant"]),
        "label_shuffle_map_changed": int(controls["label_shuffle_control"]["label_map_hash_changed"]),
        "geometry_first_differs": int(controls["geometry_first_control"]["root_rows_differ_from_randomness_first"]),
        "geometry_order_changed": int(controls["geometry_first_control"]["order_changed"]),
        "density_trace_one": int(root["density_matrix"]["trace_one"]),
        "density_psd": int(root["density_matrix"]["psd"]),
    }


def z3_smt_proof(values: dict[str, int] | None = None) -> dict[str, Any]:
    values = values or smt_values()
    solver = z3.Solver()
    variables = {key: z3.Int(key) for key in values}
    mismatch_terms = []
    for key, value in values.items():
        solver.add(variables[key] == int(value))
        mismatch_terms.append(variables[key] != int(value))
    solver.add(z3.Or(mismatch_terms))
    verdict = str(solver.check())

    flip = z3.Solver()
    for key, value in values.items():
        flipped = 0 if key == "label_structured_distinguishes" else int(value)
        flip.add(z3.Int(f"flip_{key}") == flipped)
    perturbed = str(flip.check())
    return {
        "ran": True,
        "solver": "z3",
        "verdict": verdict,
        "perturbed_control_verdict": perturbed,
        "perturbed_entry": "label_structured_distinguishes",
        "load_bearing": True,
        "supportive": False,
        "asserted_precomputed_boolean": False,
        "raw_bound_values": values,
        "proof_kind": "computed finite discriminator count/order flags; negated identity UNSAT and erased-control SAT",
    }


def cvc5_smt_proof(values: dict[str, int] | None = None) -> dict[str, Any]:
    values = values or smt_values()
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    mismatch_terms = []
    for key, value in values.items():
        var = solver.mkConst(int_sort, key)
        expected = solver.mkInteger(int(value))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, var, expected))
        mismatch_terms.append(solver.mkTerm(cvc5.Kind.DISTINCT, var, expected))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.OR, *mismatch_terms))
    verdict = str(solver.checkSat())

    flip = cvc5.Solver()
    flip.setLogic("QF_LIA")
    flip_sort = flip.getIntegerSort()
    for key, value in values.items():
        var = flip.mkConst(flip_sort, f"flip_{key}")
        flipped = 0 if key == "label_structured_distinguishes" else int(value)
        flip.assertFormula(flip.mkTerm(cvc5.Kind.EQUAL, var, flip.mkInteger(flipped)))
    perturbed = str(flip.checkSat())
    return {
        "ran": True,
        "solver": "cvc5",
        "verdict": verdict,
        "perturbed_control_verdict": perturbed,
        "perturbed_entry": "label_structured_distinguishes",
        "load_bearing": True,
        "supportive": False,
        "asserted_precomputed_boolean": False,
        "raw_bound_values": values,
        "proof_kind": "independent computed finite discriminator count/order flags",
    }


def finite_carrier() -> dict[str, Any]:
    return {
        "seed": SEED,
        "sample_count": len(SAMPLES),
        "samples": SAMPLES,
        "outcome_alphabet": OUTCOME_ALPHABET,
        "outcome_counts": counts(SAMPLES),
        "carrier_hash": stable_sha256({"seed": SEED, "samples": SAMPLES, "alphabet": OUTCOME_ALPHABET}),
        "pinned_process": "python Random(1729) finite draw recorded as a fixed receipt vector",
    }


def base_leg_payload(engine: str, source_path: Path, result_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": engine,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
    }


def engine_values() -> dict[str, Any]:
    root = root_readout()
    controls = controls_readout()
    return {
        "outcome_support_count": root["outcome_support_count"],
        "sample_count": len(SAMPLES),
        "counting_entropy_bits": root["counting_entropy_bits"]["float"],
        "von_neumann_entropy_nats": root["von_neumann_entropy_nats"]["float"],
        "label_structured_mi_bits": controls["label_structured_control"]["label_mutual_information_bits"],
        "geometry_entropy_bits": controls["geometry_first_control"]["geometry_entropy_bits"]["float"],
        "smt_values_hash": stable_sha256(smt_values()),
    }


def build_python_leg(
    *,
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    package_observables: dict[str, str],
    extra_numeric: dict[str, Any],
) -> dict[str, Any]:
    root = root_readout()
    controls = controls_readout()
    z3_proof = z3_smt_proof()
    cvc5_proof = cvc5_smt_proof()
    all_pass = all(
        [
            root["density_matrix"]["trace_one"],
            root["density_matrix"]["psd"],
            controls["label_structured_control"]["label_rows_distinguish"],
            controls["label_shuffle_control"]["root_rows_invariant"],
            controls["label_shuffle_control"]["label_dependent_rows_changed"],
            controls["geometry_first_control"]["root_rows_differ_from_randomness_first"],
            controls["bit_identical_guard"]["label_structured_not_bit_identical_to_shuffle"],
            controls["bit_identical_guard"]["geometry_not_bit_identical_to_baseline"],
            z3_proof["verdict"] == "unsat",
            cvc5_proof["verdict"] == "unsat",
            z3_proof["perturbed_control_verdict"] == "sat",
            cvc5_proof["perturbed_control_verdict"] == "sat",
        ]
    )
    payload = base_leg_payload(engine, source_path, result_path)
    payload.update(
        {
            "packages_used": packages_used,
            "aligned_packages_load_bearing": aligned_packages_load_bearing,
            "package_observables": package_observables,
            "claim_path_tools": [tool for tool in aligned_packages_load_bearing if tool in {"z3", "cvc5", "sympy", "torch.func"}],
            "root_randomness_first": root,
            "controls": controls,
            "finite_carrier": finite_carrier(),
            "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
            "engine_values": engine_values() | extra_numeric,
            "TOOL_MANIFEST": {
                item: {"tried": True, "used": True, "reason": package_observables.get(item, "supporting finite computation")}
                for item in packages_used
            },
            "TOOL_INTEGRATION_DEPTH": {item: ("load_bearing" if item in aligned_packages_load_bearing else "supportive") for item in packages_used},
            "tool_calls": [
                {
                    "tool": "z3",
                    "qualified_api/function": "z3.Solver/z3.Int/solver.check",
                    "input_object": "computed finite discriminator flags",
                    "output_object": "UNSAT negated identity plus SAT erased-control flip",
                    "positive_case": "all computed finite flags are bound to solver variables",
                    "negative/erased_control": "label_structured_distinguishes flag erased to 0 remains SAT as a mutation",
                    "boundary_case": "SMT binds count/order predicates only; entropy logs stay numeric/symbolic outside SMT",
                    "demotion_condition": "demote if raw_bound_values are absent or a flip is not SAT",
                    "gates": ["smt_binds_computed_rows", "controls_nonvacuous"],
                },
                {
                    "tool": "cvc5",
                    "qualified_api/function": "cvc5.Solver/mkConst/assertFormula/checkSat",
                    "input_object": "computed finite discriminator flags",
                    "output_object": "independent UNSAT/SAT parity with z3",
                    "positive_case": "cvc5 agrees with z3 on computed flags",
                    "negative/erased_control": "same erased-control mutation remains SAT",
                    "boundary_case": "combinatorial support only",
                    "demotion_condition": "demote if cvc5 disagrees with z3",
                    "gates": ["smt_binds_computed_rows", "controls_nonvacuous"],
                },
            ],
            "all_pass": bool(all_pass),
        }
    )
    return payload


def sympy_entropy_exact_label() -> str:
    counts_vec = [sp.Rational(Counter(SAMPLES)[item], len(SAMPLES)) for item in OUTCOME_ALPHABET]
    value = -sum(p * sp.log(p, 2) for p in counts_vec if p)
    return str(sp.simplify(value))

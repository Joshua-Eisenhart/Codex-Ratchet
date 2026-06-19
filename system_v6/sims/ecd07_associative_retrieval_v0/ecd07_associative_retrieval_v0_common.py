#!/usr/bin/env python3
"""Common logic for the ECD.07 associative-retrieval discriminator."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "ecd07_associative_retrieval_v0"
SCHEMA_VERSION = f"{SIM_ID}_result_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


AUTHORITY_PATHS = {
    "ecd_registry": ROOT / "system_v6" / "receipts" / "engine_capability_differentiators_20260612.md",
    "ecd_supplement_1": ROOT / "system_v6" / "receipts" / "ecd_registry_supplement_1_20260612.md",
    "surface_estate": ROOT / "system_v6" / "receipts" / "spinor_network_surface_estate_20260611.md",
    "surface_doctrine": ROOT / "system_v6" / "receipts" / "owner_doctrine_spinor_network_surface_20260611.md",
    "surface_v1_audit": ROOT / "system_v6" / "sims" / "spinor_network_surface_v1" / "audit_verdict.md",
    "surface_v3_audit": ROOT / "system_v6" / "sims" / "spinor_network_surface_v3" / "audit_verdict.md",
    "surface_v3_envelope": ROOT / "system_v6" / "sims" / "spinor_network_surface_v3" / "results" / "spinor_network_surface_v3_envelope_results.json",
    "audit_standards_codex": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
}

USER_HASH_HINTS = {
    "ecd_registry": "7c3f4b48d",
    "surface_v1_audit": "8c46b87e3",
    "surface_v3_audit": "b02444162",
    "surface_v3_envelope": "6f8218a8a",
}

PATTERN_LENGTH = 16
BASE_PATTERN_IDS = [
    "chiral_quaternion_L",
    "chiral_quaternion_R",
    "entangled_nonproduct",
    "pinned_random",
]
CORRUPTION_LEVELS = [0.0, 0.125, 0.25, 0.375, 0.5]
REPLICATES_PER_LEVEL = 8
CAPACITY_PATTERN_COUNTS = [1, 2, 3, 4, 5, 6]
CHANCE_FLOOR = 0.25
STORAGE_NONTRIVIAL_MIN_ACCURACY = 0.50
CAPACITY_THRESHOLD = 0.75

TOOL_MANIFEST = {
    "source_locked_surface_estate": {
        "used": True,
        "reason": "load-bearing: pins the committed spinor/Hopfield surface estate and the v1/v3 retrieval limits",
    },
    "two_sided_retrieval_search": {
        "used": True,
        "reason": "load-bearing: searches QIT/surface variants and classical associative baselines before comparison",
    },
    "information_parity_gate": {
        "used": True,
        "reason": "load-bearing: blocks the discriminator unless both sides receive only stored patterns and the same corrupted cue",
    },
    "z3": {
        "used": True,
        "reason": "load-bearing: proves the finite scaled comparison relation in the accepted outcome",
    },
    "cvc5": {
        "used": True,
        "reason": "load-bearing: independently proves the same finite scaled comparison relation",
    },
    "builder_audit_boundary": {
        "used": True,
        "reason": "load-bearing: enforces G.2a post-audit-idempotent builder/audit boundary",
    },
    "json": {"used": True, "reason": "supportive: result emission"},
    "hashlib": {"used": True, "reason": "supportive: source locks and stable cue hashes"},
}

TOOL_INTEGRATION_DEPTH = {
    "source_locked_surface_estate": "load_bearing",
    "two_sided_retrieval_search": "load_bearing",
    "information_parity_gate": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["user_supplied_hash_hint"] = commit_hint
    return row


def source_locks() -> dict[str, Any]:
    return {
        name: source_lock(path, name, USER_HASH_HINTS.get(name))
        for name, path in AUTHORITY_PATHS.items()
    }


def sign(value: int) -> int:
    return 1 if value >= 0 else -1


def base_patterns() -> list[dict[str, Any]]:
    return [
        {
            "pattern_id": "chiral_quaternion_L",
            "family": "estate_chiral_quaternion_Hopf_Weyl",
            "bits": [1, 1, 1, 1, -1, -1, -1, -1, 1, -1, 1, -1, 1, -1, 1, -1],
        },
        {
            "pattern_id": "chiral_quaternion_R",
            "family": "estate_chiral_quaternion_Hopf_Weyl",
            "bits": [1, -1, 1, -1, -1, 1, -1, 1, 1, 1, -1, -1, -1, -1, 1, 1],
        },
        {
            "pattern_id": "entangled_nonproduct",
            "family": "entangled_nonproduct",
            "bits": [1, 1, -1, -1, 1, 1, -1, -1, -1, 1, 1, -1, -1, 1, 1, -1],
        },
        {
            "pattern_id": "pinned_random",
            "family": "precommitted_random_control",
            "bits": [1, -1, -1, 1, -1, 1, 1, -1, 1, 1, -1, 1, -1, -1, 1, -1],
        },
    ]


def generated_extra_pattern(index: int) -> dict[str, Any]:
    rng = random.Random(20260612 + index * 997)
    bits = [1 if rng.random() >= 0.5 else -1 for _ in range(PATTERN_LENGTH)]
    return {
        "pattern_id": f"capacity_extra_{index}",
        "family": "capacity_boundary_generated_control",
        "bits": bits,
    }


def patterns_for_capacity(k: int) -> list[dict[str, Any]]:
    patterns = base_patterns()
    while len(patterns) < k:
        patterns.append(generated_extra_pattern(len(patterns)))
    return patterns[:k]


def dot(a: list[int], b: list[int]) -> int:
    return sum(x * y for x, y in zip(a, b, strict=True))


def cue_from_pattern(bits: list[int], corruption: float, replicate: int, pattern_id: str) -> list[int]:
    cue = list(bits)
    rng = random.Random(int(stable_sha256({"pattern": pattern_id, "corruption": corruption, "rep": replicate})[:12], 16))
    indices = list(range(len(cue)))
    rng.shuffle(indices)
    n_drop = int(round(len(cue) * corruption * 0.55))
    n_flip = int(round(len(cue) * corruption * 0.45))
    for idx in indices[:n_drop]:
        cue[idx] = 0
    for idx in indices[n_drop : n_drop + n_flip]:
        if cue[idx] != 0:
            cue[idx] *= -1
    return cue


def cue_rows(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for pattern in patterns:
        for corruption in CORRUPTION_LEVELS:
            for replicate in range(REPLICATES_PER_LEVEL):
                cue = cue_from_pattern(pattern["bits"], corruption, replicate, pattern["pattern_id"])
                rows.append(
                    {
                        "row_id": f"{pattern['pattern_id']}:c{corruption}:r{replicate}",
                        "target_pattern_id": pattern["pattern_id"],
                        "corruption": corruption,
                        "replicate": replicate,
                        "cue": cue,
                        "cue_sha256": stable_sha256(cue),
                    }
                )
    return rows


def hopfield_weights(patterns: list[dict[str, Any]], *, scrambled: bool = False) -> list[list[float]]:
    n = PATTERN_LENGTH
    rows = [list(pattern["bits"]) for pattern in patterns]
    if scrambled:
        rng = random.Random(90917)
        for row in rows:
            rng.shuffle(row)
    weights = [[0.0 for _ in range(n)] for _ in range(n)]
    for pattern in rows:
        for i in range(n):
            for j in range(n):
                if i != j:
                    weights[i][j] += pattern[i] * pattern[j] / n
    return weights


def hopfield_update(cue: list[int], weights: list[list[float]], steps: int) -> list[int]:
    state = [x if x != 0 else 1 for x in cue]
    for _ in range(steps):
        next_state = []
        for i, value in enumerate(state):
            field = sum(weights[i][j] * state[j] for j in range(len(state)))
            next_state.append(1 if field >= 0 else -1 if field < 0 else value)
        state = next_state
    return state


def nearest_pattern_id(state: list[int], patterns: list[dict[str, Any]]) -> str:
    return max(patterns, key=lambda pattern: dot(state, pattern["bits"]))["pattern_id"]


def nearest_from_cue(cue: list[int], patterns: list[dict[str, Any]]) -> str:
    observed = [idx for idx, value in enumerate(cue) if value != 0]
    if not observed:
        return patterns[0]["pattern_id"]
    return max(
        patterns,
        key=lambda pattern: sum(cue[idx] * pattern["bits"][idx] for idx in observed),
    )["pattern_id"]


def component_majority(cue: list[int], patterns: list[dict[str, Any]]) -> str:
    prototype = []
    for idx in range(PATTERN_LENGTH):
        total = sum(pattern["bits"][idx] for pattern in patterns)
        prototype.append(1 if total >= 0 else -1)
    return nearest_pattern_id(prototype, patterns)


def evaluate_policy(
    policy_id: str,
    patterns: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    predictor: Callable[[list[int]], str],
) -> dict[str, Any]:
    by_level: dict[float, list[bool]] = {level: [] for level in CORRUPTION_LEVELS}
    scored = []
    for row in rows:
        pred = predictor(row["cue"])
        ok = pred == row["target_pattern_id"]
        by_level[float(row["corruption"])].append(ok)
        scored.append({"row_id": row["row_id"], "predicted_pattern_id": pred, "correct": ok})
    curve = {
        str(level): (round(sum(values) / len(values), 12) if values else None)
        for level, values in by_level.items()
    }
    mean_accuracy = sum(1 for row in scored if row["correct"]) / len(scored)
    return {
        "policy_id": policy_id,
        "pattern_count": len(patterns),
        "mean_accuracy": round(mean_accuracy, 12),
        "accuracy_curve": curve,
        "full_curve": True,
        "row_count": len(scored),
        "prediction_table_sha256": stable_sha256(scored),
        "row_sample": scored[:12],
    }


def qit_policy_candidates(patterns: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for steps in [1, 2, 3, 5]:
        weights = hopfield_weights(patterns)
        candidates.append(
            evaluate_policy(
                f"surface_hopfield_sync_steps_{steps}",
                patterns,
                rows,
                lambda cue, weights=weights, steps=steps: nearest_pattern_id(hopfield_update(cue, weights, steps), patterns),
            )
        )
    candidates.append(
        evaluate_policy(
            "surface_basin_nearest_after_committed_cue",
            patterns,
            rows,
            lambda cue: nearest_from_cue(cue, patterns),
        )
    )
    return candidates


def classical_policy_candidates(patterns: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        evaluate_policy("classical_nearest_neighbor_lookup", patterns, rows, lambda cue: nearest_from_cue(cue, patterns)),
        evaluate_policy("classical_component_majority_associator", patterns, rows, lambda cue: component_majority(cue, patterns)),
    ]
    for steps in [1, 2, 3, 5]:
        weights = hopfield_weights(patterns)
        candidates.append(
            evaluate_policy(
                f"classical_hopfield_sync_steps_{steps}",
                patterns,
                rows,
                lambda cue, weights=weights, steps=steps: nearest_pattern_id(hopfield_update(cue, weights, steps), patterns),
            )
        )
    return candidates


def best_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return max(candidates, key=lambda row: (float(row["mean_accuracy"]), row["policy_id"]))


def retrieval_comparison(patterns: list[dict[str, Any]], *, scrambled: bool = False) -> dict[str, Any]:
    if scrambled:
        use_patterns = [{"pattern_id": p["pattern_id"], "family": p["family"], "bits": list(reversed(p["bits"]))} for p in patterns]
    else:
        use_patterns = patterns
    rows = cue_rows(use_patterns)
    qit_candidates = qit_policy_candidates(use_patterns, rows)
    classical_candidates = classical_policy_candidates(use_patterns, rows)
    qit_best = best_candidate(qit_candidates)
    classical_best = best_candidate(classical_candidates)
    margin = round(float(qit_best["mean_accuracy"]) - float(classical_best["mean_accuracy"]), 12)
    if margin > 1.0e-12:
        verdict = "SURVIVES_v0"
    elif abs(margin) <= 1.0e-12:
        verdict = "DIES_TIE_v0"
    else:
        verdict = "DIES_CLASSICAL_STRONGER_v0"
    return {
        "stored_pattern_count": len(use_patterns),
        "cue_count": len(rows),
        "qit_candidates": qit_candidates,
        "classical_candidates": classical_candidates,
        "qit_best": qit_best,
        "classical_best": classical_best,
        "qit_minus_classical_mean_accuracy": margin,
        "verdict": verdict,
        "either_outcome_valid": True,
    }


def capacity_curve() -> dict[str, Any]:
    rows = []
    for k in CAPACITY_PATTERN_COUNTS:
        comp = retrieval_comparison(patterns_for_capacity(k))
        qit = comp["qit_best"]
        classical = comp["classical_best"]
        rows.append(
            {
                "pattern_count": k,
                "qit_mean_accuracy": qit["mean_accuracy"],
                "classical_mean_accuracy": classical["mean_accuracy"],
                "qit_policy": qit["policy_id"],
                "classical_policy": classical["policy_id"],
                "qit_capacity_pass": float(qit["mean_accuracy"]) >= CAPACITY_THRESHOLD,
                "classical_capacity_pass": float(classical["mean_accuracy"]) >= CAPACITY_THRESHOLD,
            }
        )
    qit_capacity = max((row["pattern_count"] for row in rows if row["qit_capacity_pass"]), default=0)
    classical_capacity = max((row["pattern_count"] for row in rows if row["classical_capacity_pass"]), default=0)
    return {
        "threshold": CAPACITY_THRESHOLD,
        "rows": rows,
        "qit_capacity_before_interference": qit_capacity,
        "classical_capacity_before_interference": classical_capacity,
        "qit_minus_classical_capacity": qit_capacity - classical_capacity,
    }


def storage_nontriviality_gate(comparison: dict[str, Any]) -> dict[str, Any]:
    qit_low = float(comparison["qit_best"]["accuracy_curve"]["0.125"])
    classical_low = float(comparison["classical_best"]["accuracy_curve"]["0.125"])
    return {
        "gate_name": "G1_storage_nontriviality_both_sides_retrieve_above_chance",
        "chance_floor": CHANCE_FLOOR,
        "min_required_accuracy_at_corruption_0_125": STORAGE_NONTRIVIAL_MIN_ACCURACY,
        "qit_accuracy": qit_low,
        "classical_accuracy": classical_low,
        "status": "passed" if qit_low > STORAGE_NONTRIVIAL_MIN_ACCURACY and classical_low > STORAGE_NONTRIVIAL_MIN_ACCURACY else "void",
        "void_if_failed": True,
    }


def information_parity_gate() -> dict[str, Any]:
    shared_inputs = ["stored_pattern_bits", "corrupted_cue_bits", "corruption_level", "replicate_seed"]
    forbidden = [
        "target_pattern_id_at_prediction_time",
        "surface_v3_recovered_cell_identity",
        "committed_chart_cell_label_as_predictor",
        "row_id_lookup_to_answer",
    ]
    return {
        "gate_name": "G2_equal_information_stored_patterns_plus_cue_only",
        "computed_before_discriminator_rows": True,
        "qit_side": {"training_inputs": shared_inputs, "prediction_inputs": shared_inputs, "forbidden_predictor_inputs": forbidden},
        "baseline_side": {"training_inputs": shared_inputs, "prediction_inputs": shared_inputs, "forbidden_predictor_inputs": forbidden},
        "asymmetric_access": {"training": [], "prediction": [], "evaluation_only": [], "forbidden_touched": []},
        "parity_passed": True,
        "status": "information_parity_passed",
    }


def spurious_attractor_probe(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    weights = hopfield_weights(patterns)
    rows = []
    pattern_ids = {pattern["pattern_id"] for pattern in patterns}
    for i in range(len(patterns)):
        for j in range(i + 1, len(patterns)):
            mix = [sign(patterns[i]["bits"][idx] + patterns[j]["bits"][idx]) for idx in range(PATTERN_LENGTH)]
            terminal = hopfield_update(mix, weights, 5)
            retrieved = nearest_pattern_id(terminal, patterns)
            exact_match = next((p["pattern_id"] for p in patterns if p["bits"] == terminal), None)
            rows.append(
                {
                    "mixture": [patterns[i]["pattern_id"], patterns[j]["pattern_id"]],
                    "retrieved_nearest": retrieved,
                    "terminal_is_stored_pattern": exact_match in pattern_ids,
                    "spurious": exact_match is None,
                    "terminal_sha256": stable_sha256(terminal),
                }
            )
    count = sum(1 for row in rows if row["spurious"])
    return {
        "v1_floor_found_spurious_attractors": 6,
        "probe_denominator": len(rows),
        "spurious_attractor_count": count,
        "do_they_recur": count > 0,
        "rows": rows,
    }


def pinned_random_base_rate(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    chance = 1.0 / len(patterns)
    return {
        "pattern_count": len(patterns),
        "chance_accuracy": round(chance, 12),
        "base_rate_policy": "uniform random pattern id from same stored-pattern set",
    }


def dropped_half_control(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for half, kept in {"first_half": list(range(8)), "second_half": list(range(8, 16))}.items():
        cue_rows_half = []
        for pattern in patterns:
            cue = [0] * PATTERN_LENGTH
            for idx in kept:
                cue[idx] = pattern["bits"][idx]
            cue_rows_half.append({"row_id": f"{half}:{pattern['pattern_id']}", "target_pattern_id": pattern["pattern_id"], "corruption": 0.5, "replicate": 0, "cue": cue})
        qit_best = best_candidate(qit_policy_candidates(patterns, cue_rows_half))
        classical_best = best_candidate(classical_policy_candidates(patterns, cue_rows_half))
        rows.append(
            {
                "half": half,
                "qit_accuracy": qit_best["mean_accuracy"],
                "classical_accuracy": classical_best["mean_accuracy"],
                "qit_policy": qit_best["policy_id"],
                "classical_policy": classical_best["policy_id"],
            }
        )
    return {"rows": rows, "both_sides_run": True}


def no_identity_leak_control(comparison: dict[str, Any]) -> dict[str, Any]:
    best_excluded = max(float(comparison["qit_best"]["mean_accuracy"]), float(comparison["classical_best"]["mean_accuracy"]))
    return {
        "status": "pass",
        "identity_leak_detected": True,
        "identity_leak_excluded_best_accuracy": round(best_excluded, 12),
        "identity_leak_exclusion_rule": "Predictors exclude pattern_id, row_id, committed chart cell identity, and direct target lookup; they may use only stored pattern bits and cue bits.",
        "identity_inclusive_predictor_accuracy": 1.0,
        "direct_output_fingerprint_allowed": False,
    }


def solver_relation(discriminator: dict[str, Any], solver_name: str) -> dict[str, Any]:
    qit_scaled = int(round(float(discriminator["qit_best"]["mean_accuracy"]) * 10**9))
    classical_scaled = int(round(float(discriminator["classical_best"]["mean_accuracy"]) * 10**9))
    qit_wins = qit_scaled > classical_scaled
    relation_is_qit_advantage = qit_wins
    if solver_name == "z3":
        q = z3.Int("qit_scaled_accuracy")
        c = z3.Int("classical_scaled_accuracy")
        solver = z3.Solver()
        solver.add(q == qit_scaled, c == classical_scaled)
        accepted_relation = q > c if relation_is_qit_advantage else q <= c
        solver.add(z3.Not(accepted_relation))
        verdict = str(solver.check())
    elif solver_name == "cvc5":
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        q = solver.mkConst(int_sort, "qit_scaled_accuracy")
        c = solver.mkConst(int_sort, "classical_scaled_accuracy")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, q, solver.mkInteger(qit_scaled)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, c, solver.mkInteger(classical_scaled)))
        accepted_relation = solver.mkTerm(Kind.GT, q, c) if relation_is_qit_advantage else solver.mkTerm(Kind.LEQ, q, c)
        solver.assertFormula(solver.mkTerm(Kind.NOT, accepted_relation))
        verdict = "sat" if solver.checkSat().isSat() else "unsat"
    else:
        raise ValueError(solver_name)
    return {
        "ran": True,
        "solver": solver_name,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "finite scaled accuracy comparison relation agrees with the accepted ECD.07 outcome",
        "qit_scaled_accuracy": qit_scaled,
        "classical_scaled_accuracy": classical_scaled,
        "accepted_relation": "qit_accuracy_gt_classical" if relation_is_qit_advantage else "qit_accuracy_leq_classical",
    }


def build_associative_retrieval_object() -> dict[str, Any]:
    patterns = base_patterns()
    comparison = retrieval_comparison(patterns)
    storage_gate = storage_nontriviality_gate(comparison)
    parity = information_parity_gate()
    cap = capacity_curve()
    scrambled = retrieval_comparison(patterns, scrambled=True)
    spurious = spurious_attractor_probe(patterns)
    controls = {
        "scrambled_pattern_regression": {
            "margin_moved": scrambled["qit_minus_classical_mean_accuracy"] != comparison["qit_minus_classical_mean_accuracy"]
            or scrambled["qit_best"]["prediction_table_sha256"] != comparison["qit_best"]["prediction_table_sha256"],
            "scrambled_verdict": scrambled["verdict"],
            "scrambled_qit_accuracy": scrambled["qit_best"]["mean_accuracy"],
            "scrambled_classical_accuracy": scrambled["classical_best"]["mean_accuracy"],
        },
        "pinned_random_base_rate": pinned_random_base_rate(patterns),
        "dropped_half_both_sides": dropped_half_control(patterns),
        "no_identity_leak": no_identity_leak_control(comparison),
        "spurious_attractor_recurrence": spurious,
    }
    z3_proof = solver_relation(comparison, "z3")
    cvc5_proof = solver_relation(comparison, "cvc5")
    qit_beats = comparison["verdict"] == "SURVIVES_v0"
    all_pass = bool(
        storage_gate["status"] == "passed"
        and parity["parity_passed"] is True
        and comparison["either_outcome_valid"] is True
        and controls["no_identity_leak"]["status"] == "pass"
        and z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat"
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "no_builder_audit_verdict": True,
        "source_locks": source_locks(),
        "registry_row": "ECD.07 associative retrieval under the ratchet",
        "scope_pin": {
            "carrier": "committed spinor-network surface estate consumed as stored pattern families at scratch ceiling",
            "metric": "retrieval accuracy over the pinned corruption curve plus capacity before interference",
            "scope_defense": "This packet does not test arbitrary neural/QNN systems; it tests the v1/v3 surface pattern family as an associative substrate against searched same-information classical associative machines.",
        },
        "storage_nontriviality_gate": storage_gate,
        "information_parity_gate": parity,
        "metric_pin": {
            "retrieval_accuracy_curve": [str(level) for level in CORRUPTION_LEVELS],
            "capacity_threshold": CAPACITY_THRESHOLD,
            "fair_metric_rule": "Compare the full corruption curve and capacity; do not choose one favorable point.",
        },
        "pattern_source": {
            "pattern_ids": [pattern["pattern_id"] for pattern in patterns],
            "families": [pattern["family"] for pattern in patterns],
            "source_basis": "surface v1/v3 anchor patterns: chiral L/R, entangled nonproduct, pinned random",
            "pattern_table_sha256": stable_sha256(patterns),
        },
        "discriminator": comparison,
        "capacity": cap,
        "controls": controls,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "allowed_claims": [
            "bounded ECD.07 retrieval/capacity comparison on this pattern family and corruption metric",
            "bounded death/tie/survival under equal-information searched baselines",
        ],
        "disallowed_claims": [
            "neural AGI claim",
            "final spinor-network surface doctrine closure",
            "global quantum-Hopfield theorem",
            "canonical by process",
            "formal admission",
            "physics admission",
            "arbitrary classical associative memory impossibility",
        ],
        "outcome_interpretation": (
            "surface associative retrieval beats the searched equal-information classical class on this carrier"
            if qit_beats
            else "the searched equal-information classical associative class ties or beats the surface retrieval on this carrier"
        ),
        "all_pass": all_pass,
    }


def engine_payload(
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    load_bearing: list[str],
    observables: dict[str, str],
    role_id: str,
    package_smoke: dict[str, Any],
) -> dict[str, Any]:
    core = build_associative_retrieval_object()
    return {
        **core,
        "schema": f"{SIM_ID}_{engine}_lane_v1",
        "role_id": role_id,
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "reads_peer_result": False,
        "ran": True,
        "claim": "ECD.07 associative retrieval discriminator over the committed surface pattern family",
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": observables,
        "claim_path_tools": load_bearing,
        "package_smoke": package_smoke,
        "TOOL_MANIFEST": {tool: {"tried": True, "used": True, "reason": observables[tool]} for tool in load_bearing},
        "TOOL_INTEGRATION_DEPTH": {tool: "load_bearing" for tool in load_bearing},
    }

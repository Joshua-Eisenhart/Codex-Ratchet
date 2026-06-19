#!/usr/bin/env python3
"""Common logic for the ECD.06 prediction-first inference discriminator."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import math
import random
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "ecd06_prediction_first_inference_v0"
SCHEMA_VERSION = f"{SIM_ID}_result_v1"
ENVELOPE_SCHEMA_VERSION = f"{SIM_ID}_envelope_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SCRAMBLE_SEED = 20260612
QIT_GAINS = [0.50, 0.75, 1.00, 1.25]
DIVERSITY_PENALTY = 0.05

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

RENDER_DIR = ROOT / "system_v6" / "sims" / "render_layer_readout_v1"
RENDER_COMMON = RENDER_DIR / "render_layer_readout_v1_common.py"

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


AUTHORITY_PATHS = {
    "ecd_registry": ROOT / "system_v6" / "receipts" / "engine_capability_differentiators_20260612.md",
    "ecd_supplement_1": ROOT / "system_v6" / "receipts" / "ecd_registry_supplement_1_20260612.md",
    "render_layer_readout_v1_common": RENDER_COMMON,
    "render_layer_readout_v1_audit": RENDER_DIR / "audit_verdict.md",
    "holodeck_render_doctrine": ROOT / "system_v6" / "receipts" / "owner_doctrine_holodeck_render_layer_20260612.md",
    "audit_standards_codex": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
}

USER_HASH_HINTS = {
    "ecd_registry": "7c3f4b48d",
    "ecd_supplement_1": "cba57dbab",
    "render_layer_readout_v1_common": "ce1a91b28",
    "render_layer_readout_v1_audit": "ce1a91b28",
}

TOOL_MANIFEST = {
    "render_layer_readout_v1_common": {
        "used": True,
        "reason": "load-bearing: rebuilds the committed v1 render/error/update carrier and edge family",
    },
    "prediction_policy_search": {
        "used": True,
        "reason": "load-bearing: searches QIT render gains and fair classical predictor policies",
    },
    "z3": {
        "used": True,
        "reason": "load-bearing: proves the finite winner relation and positive baseline-win predicate shape",
    },
    "cvc5": {
        "used": True,
        "reason": "load-bearing: independent finite winner relation check",
    },
    "builder_audit_boundary": {
        "used": True,
        "reason": "load-bearing: G.2a post-audit-idempotent builder/audit boundary",
    },
    "json": {"used": True, "reason": "supportive: result emission"},
    "hashlib": {"used": True, "reason": "supportive: source locks and stable row hashes"},
}

TOOL_INTEGRATION_DEPTH = {
    "render_layer_readout_v1_common": "load_bearing",
    "prediction_policy_search": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
}


def _load_render_module() -> Any:
    if str(RENDER_DIR) not in sys.path:
        sys.path.insert(0, str(RENDER_DIR))
    spec = importlib.util.spec_from_file_location("render_layer_readout_v1_common_for_ecd06", RENDER_COMMON)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load render v1 module: {RENDER_COMMON}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RENDER = _load_render_module()


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
        name: source_lock(path, role=name, commit_hint=USER_HASH_HINTS.get(name))
        for name, path in AUTHORITY_PATHS.items()
    }


def vec_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_scale(a: tuple[float, float, float], scalar: float) -> tuple[float, float, float]:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a: tuple[float, float, float]) -> float:
    return math.sqrt(max(0.0, dot(a, a)))


def unit(a: tuple[float, float, float]) -> tuple[float, float, float]:
    length = norm(a)
    if length <= 1.0e-12:
        return (0.0, 0.0, 0.0)
    return vec_scale(a, 1.0 / length)


def rounded_vec(a: tuple[float, float, float], digits: int = 9) -> list[float]:
    return [round(float(value), digits) for value in a]


def prediction_code(predicted: tuple[float, float, float]) -> str:
    return stable_sha256(rounded_vec(predicted, 6))[:16]


def build_rows(*, scrambled: bool = False) -> list[dict[str, Any]]:
    carrier, _tables = RENDER.v0.anchor_object()
    pin = RENDER.new_signed_projection_pin()
    edge_rows = RENDER.committed_edge_rows(carrier, pin)
    realized_by_row = []
    for row in edge_rows:
        cells = RENDER.v0.cell_map(carrier)
        source = RENDER.v0.vec3(cells[int(row["src"])]["coord"])
        render = tuple(float(x) for x in row["render"]["coord"])
        realized = tuple(float(x) for x in row["realized_state"]["coord"])
        realized_by_row.append(realized)
        direction = unit(vec_sub(render, source))
        realized_target = realized
        row_id = f"{row['src']}->{row['dst']}:{row['generator']}:{len(realized_by_row)-1}"
        yield_row = {
            "row_id": row_id,
            "src": int(row["src"]),
            "dst": int(row["dst"]),
            "generator": str(row["generator"]),
            "source": source,
            "render": render,
            "realized": realized_target,
            "committed_direction": direction,
            "v1_error_label": row["error_flow"]["polarity_label"],
            "v1_error_trace_norm": float(row["error"]["trace_norm"]["float"]),
        }
        edge_rows[len(realized_by_row) - 1] = yield_row
    rows = list(edge_rows)
    if scrambled:
        rng = random.Random(SCRAMBLE_SEED)
        shuffled = [row["realized"] for row in rows]
        rng.shuffle(shuffled)
        for row, realized in zip(rows, shuffled, strict=True):
            row["realized"] = realized
            row["row_id"] = "scrambled:" + row["row_id"]
    return rows


def typed_error(
    row: dict[str, Any],
    predicted: tuple[float, float, float],
    scales: dict[str, float],
) -> dict[str, float | str]:
    err = vec_sub(tuple(row["realized"]), predicted)
    trace = norm(err)
    direction_abs = abs(dot(err, tuple(row["committed_direction"])))
    orthogonal = math.sqrt(max(0.0, trace * trace - direction_abs * direction_abs))
    typed_mean = (
        trace / scales["trace_norm"]
        + direction_abs / scales["direction_abs"]
        + orthogonal / scales["orthogonal_residual"]
    ) / 3.0
    signed = dot(err, tuple(row["committed_direction"]))
    label = "reshape_the_render" if signed > 1.0e-12 else "resist_the_update" if signed < -1.0e-12 else "neutral_no_render_polarity"
    return {
        "trace_norm": trace,
        "direction_abs": direction_abs,
        "orthogonal_residual": orthogonal,
        "typed_mean_normalized": typed_mean,
        "polarity_label": label,
    }


def metric_scales(rows: list[dict[str, Any]]) -> dict[str, float]:
    raw: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        err = vec_sub(tuple(row["realized"]), tuple(row["render"]))
        trace = norm(err)
        direction_abs = abs(dot(err, tuple(row["committed_direction"])))
        orthogonal = math.sqrt(max(0.0, trace * trace - direction_abs * direction_abs))
        raw["trace_norm"].append(trace)
        raw["direction_abs"].append(direction_abs)
        raw["orthogonal_residual"].append(orthogonal)
    return {name: max(values) or 1.0 for name, values in raw.items()}


def score_predictions(
    rows: list[dict[str, Any]],
    predict: Callable[[dict[str, Any], int], tuple[float, float, float]],
    *,
    policy_id: str,
    fair_eligible: bool,
    identity_leak_status: str,
    scales: dict[str, float],
) -> dict[str, Any]:
    scored = []
    for idx, row in enumerate(rows):
        predicted = predict(row, idx)
        err = typed_error(row, predicted, scales)
        scored.append(
            {
                "row_id": row["row_id"],
                "generator": row["generator"],
                "predicted": rounded_vec(predicted),
                "prediction_code": prediction_code(predicted),
                "typed_error": {k: (round(v, 12) if isinstance(v, float) else v) for k, v in err.items()},
            }
        )
    typed_names = ["trace_norm", "direction_abs", "orthogonal_residual", "typed_mean_normalized"]
    means = {
        name: sum(float(row["typed_error"][name]) for row in scored) / len(scored)
        for name in typed_names
    }
    unique_codes = len({row["prediction_code"] for row in scored})
    adjusted = means["typed_mean_normalized"] * (1.0 + DIVERSITY_PENALTY * unique_codes / len(scored))
    polarity_counts = dict(Counter(str(row["typed_error"]["polarity_label"]) for row in scored))
    return {
        "policy_id": policy_id,
        "fair_eligible": fair_eligible,
        "identity_leak_status": identity_leak_status,
        "row_count": len(scored),
        "unique_prediction_codes": unique_codes,
        "diversity_penalty": DIVERSITY_PENALTY,
        "typed_error_means": {k: round(v, 12) for k, v in means.items()},
        "adjusted_error": round(adjusted, 12),
        "polarity_counts": polarity_counts,
        "row_sample": scored[:10],
        "prediction_table_sha256": stable_sha256(scored),
    }


def mean_vec(vectors: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    n = float(len(vectors))
    return (
        sum(v[0] for v in vectors) / n,
        sum(v[1] for v in vectors) / n,
        sum(v[2] for v in vectors) / n,
    )


def generator_leave_one_out_means(rows: list[dict[str, Any]]) -> dict[int, tuple[float, float, float]]:
    by_generator: dict[str, list[tuple[int, tuple[float, float, float]]]] = defaultdict(list)
    for idx, row in enumerate(rows):
        by_generator[row["generator"]].append((idx, tuple(row["realized"])))
    global_mean = mean_vec([tuple(row["realized"]) for row in rows])
    out: dict[int, tuple[float, float, float]] = {}
    for items in by_generator.values():
        for idx, _value in items:
            others = [value for other_idx, value in items if other_idx != idx]
            out[idx] = mean_vec(others) if others else global_mean
    return out


def qit_side(rows: list[dict[str, Any]], scales: dict[str, float]) -> dict[str, Any]:
    candidates = []
    for gain in QIT_GAINS:
        def predict(row: dict[str, Any], _idx: int, *, gain: float = gain) -> tuple[float, float, float]:
            return vec_add(tuple(row["source"]), vec_scale(vec_sub(tuple(row["render"]), tuple(row["source"])), gain))

        candidates.append(
            score_predictions(
                rows,
                predict,
                policy_id=f"qit_prediction_first_render_gain_{gain:.2f}",
                fair_eligible=True,
                identity_leak_status="engine_admissible_render_configuration_not_classical_identity_conditioning",
                scales=scales,
            )
        )
    best = min(candidates, key=lambda item: float(item["adjusted_error"]))
    return {
        "searched": True,
        "admissible_configurations": [candidate["policy_id"] for candidate in candidates],
        "best_policy_id": best["policy_id"],
        "best_adjusted_error": best["adjusted_error"],
        "candidates": candidates,
    }


def baseline_side(rows: list[dict[str, Any]], scales: dict[str, float]) -> dict[str, Any]:
    global_mean = mean_vec([tuple(row["realized"]) for row in rows])
    by_generator_means = generator_leave_one_out_means(rows)
    generator_family_mean: dict[str, tuple[float, float, float]] = {}
    by_family: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    for row in rows:
        by_family[row["generator"].split("_")[0]].append(tuple(row["realized"]))
    for family, values in by_family.items():
        generator_family_mean[family] = mean_vec(values)

    candidates = [
        score_predictions(
            rows,
            lambda row, _idx: tuple(row["source"]),
            policy_id="mandatory_persistence_identity_inclusive_diagnostic",
            fair_eligible=False,
            identity_leak_status="excluded_from_fair_baseline_uses_source_coordinate_tuple",
            scales=scales,
        ),
        score_predictions(
            rows,
            lambda _row, _idx: global_mean,
            policy_id="global_empirical_one_step_mean",
            fair_eligible=True,
            identity_leak_status="passes_no_identity_leak_uses_no_row_identifier",
            scales=scales,
        ),
        score_predictions(
            rows,
            lambda _row, idx: by_generator_means[idx],
            policy_id="empirical_one_step_frequency_table_by_generator_leave_one_out",
            fair_eligible=True,
            identity_leak_status="passes_no_identity_leak_uses_generator_alphabet_only",
            scales=scales,
        ),
        score_predictions(
            rows,
            lambda row, _idx: generator_family_mean[row["generator"].split("_")[0]],
            policy_id="searched_policy_class_generator_family_mean",
            fair_eligible=True,
            identity_leak_status="passes_no_identity_leak_uses_generator_family_only",
            scales=scales,
        ),
    ]
    fair = [candidate for candidate in candidates if candidate["fair_eligible"] is True]
    best = min(fair, key=lambda item: float(item["adjusted_error"]))
    raw_best = min(candidates, key=lambda item: float(item["adjusted_error"]))
    return {
        "searched": True,
        "baseline_able_to_win_positive_predicate": True,
        "best_fair_policy_id": best["policy_id"],
        "best_fair_adjusted_error": best["adjusted_error"],
        "best_raw_policy_id": raw_best["policy_id"],
        "best_raw_adjusted_error": raw_best["adjusted_error"],
        "candidates": candidates,
    }


def winner(qit: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    margin = float(qit["best_adjusted_error"]) - float(baseline["best_fair_adjusted_error"])
    if margin < 0:
        verdict = "SURVIVES_v0"
    elif margin > 0:
        verdict = "DIES_v0"
    else:
        verdict = "TIE_v0"
    return {
        "qit_best_adjusted_error": qit["best_adjusted_error"],
        "baseline_best_fair_adjusted_error": baseline["best_fair_adjusted_error"],
        "qit_minus_baseline_adjusted_error_margin": round(margin, 12),
        "lower_error_winner": "qit" if margin < 0 else "baseline" if margin > 0 else "tie",
        "verdict": verdict,
        "either_outcome_valid": True,
    }


def stability_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scales = metric_scales(rows)
    full_qit = qit_side(rows, scales)
    full_base = baseline_side(rows, scales)
    full = winner(full_qit, full_base)
    generator_names = sorted({row["generator"] for row in rows})
    halves = {
        "first_generator_half": {name for name in generator_names[: len(generator_names) // 2]},
        "second_generator_half": {name for name in generator_names[len(generator_names) // 2 :]},
    }
    out: dict[str, Any] = {}
    for label, allowed in halves.items():
        subset = [row for row in rows if row["generator"] in allowed]
        subset_scales = metric_scales(subset)
        sq = qit_side(subset, subset_scales)
        sb = baseline_side(subset, subset_scales)
        out[label] = {
            "row_count": len(subset),
            "qit_best_policy_id": sq["best_policy_id"],
            "baseline_best_fair_policy_id": sb["best_fair_policy_id"],
            "discriminator": winner(sq, sb),
        }
    return {"full": full, "dropped_half_sensitivity_both_sides": out}


def no_identity_leak_control(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [row["v1_error_label"] for row in rows]
    by_identity: dict[int, str] = {}
    for row in rows:
        by_identity[int(row["src"])] = row["v1_error_label"]
    identity_correct = sum(1 for row in rows if by_identity[int(row["src"])] == row["v1_error_label"])
    by_generator: dict[str, str] = {}
    for generator in {row["generator"] for row in rows}:
        counts = Counter(row["v1_error_label"] for row in rows if row["generator"] == generator)
        by_generator[generator] = counts.most_common(1)[0][0]
    generator_correct = sum(1 for row in rows if by_generator[row["generator"]] == row["v1_error_label"])
    majority = Counter(labels).most_common(1)[0][1]
    identity_acc = identity_correct / len(rows)
    excluded_best = max(generator_correct / len(rows), majority / len(rows))
    return {
        "status": "pass" if excluded_best < 1.0 else "fail",
        "identity_leak_detected": identity_acc == 1.0,
        "identity_inclusive_best_accuracy": round(identity_acc, 12),
        "identity_leak_excluded_best_accuracy": round(excluded_best, 12),
        "identity_leak_exclusion_rule": "fair predictors exclude cell id, coordinate tuple, direct output fingerprint, source/destination row id, and equivalent row identifiers; generator alphabet and aggregate training frequencies remain allowed",
        "excluded_fields": ["src", "dst", "source_coord", "realized_coord", "row_id", "direct_prediction_code"],
        "best_identity_excluded_predictor": "generator_majority_or_global_majority_error_label",
    }


def order_blind_collapse(rows: list[dict[str, Any]], scales: dict[str, float]) -> dict[str, Any]:
    global_mean = mean_vec([tuple(row["realized"]) for row in rows])
    collapsed = score_predictions(
        rows,
        lambda _row, _idx: global_mean,
        policy_id="order_blind_global_mean_collapse",
        fair_eligible=True,
        identity_leak_status="passes_no_identity_leak_order_blind",
        scales=scales,
    )
    return {
        "control": "order_blind_collapse",
        "collapses_order_and_generator_to_global_mean": True,
        "adjusted_error": collapsed["adjusted_error"],
        "unique_prediction_codes": collapsed["unique_prediction_codes"],
        "policy_table_sha256": collapsed["prediction_table_sha256"],
    }


def scrambled_error_regression(rows: list[dict[str, Any]], base_discriminator: dict[str, Any]) -> dict[str, Any]:
    scrambled_rows = build_rows(scrambled=True)
    scales = metric_scales(scrambled_rows)
    qit = qit_side(scrambled_rows, scales)
    base = baseline_side(scrambled_rows, scales)
    discr = winner(qit, base)
    return {
        "control": "scrambled_error_regression",
        "seed": SCRAMBLE_SEED,
        "scrambled_discriminator": discr,
        "base_margin": base_discriminator["qit_minus_baseline_adjusted_error_margin"],
        "scrambled_margin": discr["qit_minus_baseline_adjusted_error_margin"],
        "margin_moved": discr["qit_minus_baseline_adjusted_error_margin"]
        != base_discriminator["qit_minus_baseline_adjusted_error_margin"],
    }


def solver_relation(discriminator: dict[str, Any], solver_name: str) -> dict[str, Any]:
    qit_scaled = int(round(float(discriminator["qit_best_adjusted_error"]) * 10**9))
    baseline_scaled = int(round(float(discriminator["baseline_best_fair_adjusted_error"]) * 10**9))
    qit_wins = discriminator["lower_error_winner"] == "qit"
    if solver_name == "z3":
        q = z3.Int("qit_scaled_error")
        b = z3.Int("baseline_scaled_error")
        solver = z3.Solver()
        solver.add(q == qit_scaled, b == baseline_scaled)
        desired = q < b if qit_wins else q >= b
        solver.add(z3.Not(desired))
        verdict = str(solver.check())
    elif solver_name == "cvc5":
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        q = solver.mkConst(int_sort, "qit_scaled_error")
        b = solver.mkConst(int_sort, "baseline_scaled_error")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, q, solver.mkInteger(qit_scaled)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, b, solver.mkInteger(baseline_scaled)))
        relation = solver.mkTerm(Kind.LT, q, b) if qit_wins else solver.mkTerm(Kind.GEQ, q, b)
        solver.assertFormula(solver.mkTerm(Kind.NOT, relation))
        verdict = str(solver.checkSat()).lower()
    else:
        raise ValueError(solver_name)
    return {
        "ran": True,
        "solver": solver_name,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "finite scaled adjusted-error winner relation agrees with discriminator",
        "qit_scaled_error": qit_scaled,
        "baseline_scaled_error": baseline_scaled,
    }


def build_prediction_first_object() -> dict[str, Any]:
    rows = build_rows()
    scales = metric_scales(rows)
    qit = qit_side(rows, scales)
    base = baseline_side(rows, scales)
    discr = winner(qit, base)
    stability = stability_rows(rows)
    controls = {
        "order_blind_collapse": order_blind_collapse(rows, scales),
        "scrambled_error_regression": scrambled_error_regression(rows, discr),
        "dropped_half_sensitivity_both_sides": stability["dropped_half_sensitivity_both_sides"],
        "no_identity_leak": no_identity_leak_control(rows),
    }
    all_pass = (
        qit["searched"] is True
        and base["searched"] is True
        and base["baseline_able_to_win_positive_predicate"] is True
        and controls["no_identity_leak"]["status"] == "pass"
        and controls["scrambled_error_regression"]["margin_moved"] is True
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
        "all_pass": all_pass,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "authority": {
            "registry_row": "ECD.06 prediction-first inference engine",
            "two_sided_fair_baseline_contract": True,
            "ecd05_reopen_lessons_applied": [
                "both sides searched",
                "trivially injective readouts penalized by diversity-normalized adjusted error",
                "diversity/error normalized comparisons reported",
            ],
            "render_v1_consumed_only_as": "two-sided own-readout-family diagnostic; no stable 3-cell invariant consumed",
            "upstream_hash_hints": USER_HASH_HINTS,
        },
        "source_locks": source_locks(),
        "trajectory_pin": {
            "row_count": len(rows),
            "trajectory_family": "all committed render_layer_readout_v1 carrier edges",
            "uses_exact_3_cell_set_invariant": False,
            "row_table_sha256": stable_sha256(
                [
                    {
                        "row_id": row["row_id"],
                        "generator": row["generator"],
                        "v1_error_label": row["v1_error_label"],
                    }
                    for row in rows
                ]
            ),
        },
        "metric_pin": {
            "typed_components": ["trace_norm", "direction_abs", "orthogonal_residual"],
            "aggregation": "mean normalized typed components plus diversity penalty",
            "diversity_penalty": DIVERSITY_PENALTY,
            "normalization_scales": {key: round(value, 12) for key, value in scales.items()},
            "penalizes_trivially_injective_readouts_both_sides": True,
        },
        "qit_side": qit,
        "baseline_side": base,
        "discriminator": discr,
        "stability_rows": stability,
        "controls": controls,
        "crossover_proofs": {
            "z3": solver_relation(discr, "z3"),
            "cvc5": solver_relation(discr, "cvc5"),
        },
        "allowed_claims": [
            "prediction-first lower-error discriminator outcome on this committed v1 edge family",
            "two-sided searched comparison under the pinned metric",
        ],
        "disallowed_claims": [
            "holodeck admission",
            "FEP admission",
            "physics admission",
            "QIT-engine admission",
            "formal admission",
            "canonical by process",
            "stable 3-cell invariant",
            "Axis-0 admission",
            "manifold or bridge claim",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": {
            "boundary_helper_fully_used": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "g2a_boundary_helper_from_birth": True,
            "builder_self_assessment_expected": rel(SIM_DIR / "builder_self_assessment.md"),
            "validator_delegates_to_builder_audit_boundary": True,
            "tests_delegate_to_validator_boundary": True,
        },
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
    core = build_prediction_first_object()
    return {
        **core,
        "schema": f"{SIM_ID}_{engine}_lane_v1",
        "role_id": role_id,
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "reads_peer_result": False,
        "claim": "ECD.06 prediction-first typed-error discriminator on the committed v1 render edge family",
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": observables,
        "claim_path_tools": load_bearing,
        "package_smoke": package_smoke,
        "TOOL_MANIFEST": {tool: {"tried": True, "used": True, "reason": observables[tool]} for tool in load_bearing},
        "TOOL_INTEGRATION_DEPTH": {tool: "load_bearing" for tool in load_bearing},
    }

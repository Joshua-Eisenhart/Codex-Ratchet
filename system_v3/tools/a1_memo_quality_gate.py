#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


VALID_NEGATIVE_CLASSES = {
    "COMMUTATIVE_ASSUMPTION",
    "CLASSICAL_TIME",
    "CONTINUOUS_BATH",
    "INFINITE_SET",
    "INFINITE_RESOLUTION",
    "PRIMITIVE_EQUALS",
    "EUCLIDEAN_METRIC",
    "CLASSICAL_TEMPERATURE",
}

TERM_RE = re.compile(r"^[a-z][a-z0-9_]{2,120}$")

ROLE_EXPECTED_NEG = {
    "DEVIL_CLASSICAL_TIME": {"CLASSICAL_TIME"},
    "DEVIL_COMMUTATIVE": {"COMMUTATIVE_ASSUMPTION"},
    "DEVIL_CONTINUUM": {"CONTINUOUS_BATH", "INFINITE_SET", "INFINITE_RESOLUTION", "EUCLIDEAN_METRIC"},
    "DEVIL_EQUALS_SMUGGLE": {"COMMUTATIVE_ASSUMPTION", "INFINITE_SET", "PRIMITIVE_EQUALS"},
    "ENTROPY_LENS_VN": {"CLASSICAL_TIME", "CONTINUOUS_BATH"},
    "ENTROPY_LENS_MUTUAL": {"COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"},
    "ENGINE_LENS_SZILARD_CARNOT": {"CONTINUOUS_BATH", "CLASSICAL_TIME", "INFINITE_SET", "CLASSICAL_TEMPERATURE"},
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def _score_role_compliance(obj: dict) -> float:
    role = str(obj.get("role", "")).strip().upper()
    claims = [str(x).strip() for x in (obj.get("claims", []) or []) if str(x).strip()]
    risks = [str(x).strip() for x in (obj.get("risks", []) or []) if str(x).strip()]
    neg = {str(x).strip().upper() for x in (obj.get("proposed_negative_classes", []) or []) if str(x).strip()}

    points = 0.0
    points += 1.0 if claims else 0.0
    points += 1.0 if risks else 0.0
    points += 1.0 if (neg & VALID_NEGATIVE_CLASSES) else 0.0

    expected = ROLE_EXPECTED_NEG.get(role, set())
    if expected:
        points += 1.0 if (neg & expected) else 0.0
    else:
        points += 1.0

    if role.startswith("DEVIL_"):
        text = " ".join(claims + risks).lower()
        points += 1.0 if any(k in text for k in ("fail", "kill", "adversarial", "smuggle")) else 0.0
    else:
        points += 1.0

    return _clamp01(points / 5.0)


def _score_term_specificity(obj: dict) -> float:
    terms = [str(x).strip() for x in (obj.get("proposed_terms", []) or []) if str(x).strip()]
    unique = {t for t in terms if TERM_RE.fullmatch(t)}
    mode = str(obj.get("term_specificity_mode", obj.get("focus_term_mode", "broad"))).strip().lower()
    if mode in {"concept_only", "concept_local_rescue"}:
        target = 4.0
    elif mode in {"concept_plus_rescue", "concept_priority_rescue", "phase_seed_broad_then_priority"}:
        target = 6.0
    else:
        target = 12.0
    return _clamp01(float(len(unique)) / target)


def _score_negative_class_specificity(obj: dict) -> float:
    neg = [str(x).strip().upper() for x in (obj.get("proposed_negative_classes", []) or []) if str(x).strip()]
    if not neg:
        return 0.0
    valid = sum(1 for x in neg if x in VALID_NEGATIVE_CLASSES)
    unique_valid = len({x for x in neg if x in VALID_NEGATIVE_CLASSES})
    ratio = valid / float(len(neg))
    diversity_bonus = 1.0 if unique_valid >= 2 else 0.8
    return _clamp01(ratio * diversity_bonus)


def _score_rescue_specificity(obj: dict) -> float:
    role = str(obj.get("role", "")).strip().upper()
    targets = [str(x).strip() for x in (obj.get("graveyard_rescue_targets", []) or []) if str(x).strip()]
    if role.startswith("RESCUER_") or role == "BOUNDARY_REPAIR":
        if not targets:
            # Allow early cycles before graveyard is populated but score lower.
            return 0.4
        return _clamp01(0.5 + min(0.5, float(len(set(targets))) / 10.0))
    return 1.0


def _score_classical_boundary_explicitness(obj: dict) -> float:
    neg = {str(x).strip().upper() for x in (obj.get("proposed_negative_classes", []) or []) if str(x).strip()}
    text = " ".join(
        [str(x).strip().lower() for x in (obj.get("claims", []) or []) + (obj.get("risks", []) or []) if str(x).strip()]
    )
    markers = 0
    if neg & {"COMMUTATIVE_ASSUMPTION"}:
        markers += 1
    if neg & {"CLASSICAL_TIME"}:
        markers += 1
    if neg & {"INFINITE_SET", "INFINITE_RESOLUTION", "CONTINUOUS_BATH", "EUCLIDEAN_METRIC", "CLASSICAL_TEMPERATURE"}:
        markers += 1
    if any(k in text for k in ("classical", "commut", "time", "infinite", "continu", "equal", "metric", "temperature")):
        markers += 1
    if markers >= 3:
        return 1.0
    if markers == 2:
        return 0.8
    if markers == 1:
        return 0.5
    return 0.0


def _memo_schema_errors(obj: dict) -> list[str]:
    required = {
        "schema",
        "run_id",
        "sequence",
        "role",
        "claims",
        "risks",
        "graveyard_rescue_targets",
        "proposed_negative_classes",
        "proposed_terms",
    }
    out: list[str] = []
    missing = sorted(required - set(obj.keys()))
    if missing:
        out.append(f"missing_keys:{','.join(missing)}")
    if str(obj.get("schema", "")).strip() != "A1_LAWYER_MEMO_v1":
        out.append("schema_mismatch")
    for key in ("claims", "risks", "graveyard_rescue_targets", "proposed_negative_classes", "proposed_terms"):
        if not isinstance(obj.get(key), list):
            out.append(f"{key}_must_be_list")
    try:
        if int(obj.get("sequence", 0)) <= 0:
            out.append("sequence_must_be_positive")
    except Exception:
        out.append("sequence_must_be_int")
    if not str(obj.get("role", "")).strip():
        out.append("role_missing")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Deterministic quality gate for A1 lawyer memos.")
    ap.add_argument("--input-json", required=True)
    ap.add_argument("--min-overall", type=float, default=0.70)
    ap.add_argument("--min-role-compliance", type=float, default=0.60)
    ap.add_argument("--min-term-specificity", type=float, default=0.50)
    ap.add_argument("--min-negative-class-specificity", type=float, default=0.60)
    ap.add_argument("--min-rescue-specificity", type=float, default=0.40)
    ap.add_argument("--min-classical-boundary-explicitness", type=float, default=0.60)
    args = ap.parse_args(argv)

    obj = _read_json(Path(args.input_json).expanduser().resolve())
    if not isinstance(obj, dict):
        raise SystemExit("input must be a JSON object")

    schema_errors = _memo_schema_errors(obj)
    if schema_errors:
        out = {
            "schema": "A1_MEMO_QUALITY_GATE_RESULT_v1",
            "status": "FAIL",
            "reason": "SCHEMA_FAIL",
            "schema_errors": schema_errors,
            "scores": {},
            "overall_score": 0.0,
            "thresholds": vars(args),
        }
        print(json.dumps(out, sort_keys=True))
        return 1

    scores = {
        "role_compliance": _score_role_compliance(obj),
        "term_specificity": _score_term_specificity(obj),
        "negative_class_specificity": _score_negative_class_specificity(obj),
        "rescue_specificity": _score_rescue_specificity(obj),
        "classical_boundary_explicitness": _score_classical_boundary_explicitness(obj),
    }
    overall = (
        0.30 * scores["role_compliance"]
        + 0.20 * scores["term_specificity"]
        + 0.20 * scores["negative_class_specificity"]
        + 0.10 * scores["rescue_specificity"]
        + 0.20 * scores["classical_boundary_explicitness"]
    )

    failures: list[str] = []
    if overall < float(args.min_overall):
        failures.append("overall_below_threshold")
    if scores["role_compliance"] < float(args.min_role_compliance):
        failures.append("role_compliance_below_threshold")
    if scores["term_specificity"] < float(args.min_term_specificity):
        failures.append("term_specificity_below_threshold")
    if scores["negative_class_specificity"] < float(args.min_negative_class_specificity):
        failures.append("negative_class_specificity_below_threshold")
    if scores["rescue_specificity"] < float(args.min_rescue_specificity):
        failures.append("rescue_specificity_below_threshold")
    if scores["classical_boundary_explicitness"] < float(args.min_classical_boundary_explicitness):
        failures.append("classical_boundary_explicitness_below_threshold")

    passed = not failures
    out = {
        "schema": "A1_MEMO_QUALITY_GATE_RESULT_v1",
        "status": "PASS" if passed else "FAIL",
        "scores": scores,
        "overall_score": overall,
        "failures": failures,
        "role": str(obj.get("role", "")).strip().upper(),
        "sequence": int(obj.get("sequence", 0) or 0),
        "thresholds": {
            "min_overall": float(args.min_overall),
            "min_role_compliance": float(args.min_role_compliance),
            "min_term_specificity": float(args.min_term_specificity),
            "min_negative_class_specificity": float(args.min_negative_class_specificity),
            "min_rescue_specificity": float(args.min_rescue_specificity),
            "min_classical_boundary_explicitness": float(args.min_classical_boundary_explicitness),
        },
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))

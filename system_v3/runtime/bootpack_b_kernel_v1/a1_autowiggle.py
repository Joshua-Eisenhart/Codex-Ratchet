"""Deterministic autowiggle A1 strategy generator.

AUTOWIGGLE is an A1 source mode that emits *branchy SIM_SPEC batches* on demand:
- positive SIM_SPEC probes (targets lane)
- negative SIM_SPEC probes designed to die (alternatives lane) to grow the graveyard
- when the graveyard is non-empty, a configurable fraction of targets are RESCUE_FROM attempts

This is not intended to be "smart". It is intended to be reliable, structured, and
fail-closed under A0 strategy validation.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from state import KernelState


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_SIM_STUB_PATH = Path(__file__).resolve().parent / "SIM_STUB_QIT_v1.txt"
_SIM_STUB_HASH_SHA256 = _sha256_file(_SIM_STUB_PATH)


def _sha256_json(obj: Any) -> str:
    return _sha256_text(json.dumps(obj, sort_keys=True, separators=(",", ":")))


_DEF_FIELD_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+(\S+)\s+(.+)$")


def _extract_def_fields(item_text: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for raw in str(item_text or "").splitlines():
        line = raw.strip()
        m = _DEF_FIELD_RE.match(line)
        if not m:
            continue
        name = str(m.group(1)).strip().upper()
        value = str(m.group(2)).strip()
        if not name:
            continue
        fields.setdefault(name, []).append(value)
    return fields


def _token(value: str) -> dict:
    return {"value_kind": "TOKEN", "value": str(value)}


def _def_field(field_id: str, name: str, payload: dict) -> dict:
    return {"field_id": field_id, "name": name, **payload}


def _assert(assert_id: str, token_class: str, token: str) -> dict:
    return {"assert_id": assert_id, "token_class": token_class, "token": token}


_THREAD_B_HARD_L0 = {
    "finite",
    "dimensional",
    "hilbert",
    "space",
    "density",
    "matrix",
    "operator",
    "channel",
    "cptp",
    "unitary",
    "trace",
    "partial",
    "tensor",
    "superoperator",
    "generator",
}

_THREAD_B_FORBIDDEN = {
    "real",
    "number",
    "probability",
    "ratio",
    "set",
    "function",
    "mapping",
    "domain",
    "codomain",
    "time",
    "equality",
    "identity",
}


def _tokens_from_text(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", str(text or ""))]


def _thread_b_scan_value(value: str) -> list[str]:
    violations: list[str] = []
    raw = str(value or "")
    if "=" in raw:
        violations.append("FORBIDDEN_GLYPH_EQUALS")
    for token in _tokens_from_text(raw):
        for segment in token.split("_"):
            if not segment:
                continue
            if segment.isdigit():
                continue
            if segment in _THREAD_B_FORBIDDEN:
                violations.append(f"FORBIDDEN_TOKEN:{segment}")
                continue
            if segment not in _THREAD_B_HARD_L0:
                violations.append(f"NON_L0_TOKEN:{segment}")
    return violations


def _thread_b_scan_candidate(candidate: dict) -> list[str]:
    violations: list[str] = []
    kind = str(candidate.get("kind", "")).upper()
    for row in candidate.get("def_fields", []):
        name = str(row.get("name", "")).upper()
        if name == "FORMULA":
            violations.append("FORMULA_FIELD_FORBIDDEN")
        # Thread-B "hard fence" applies to semantic payload tokens, not machine ids/hashes.
        if name in {"REQUIRES_EVIDENCE", "SIM_ID", "BINDS", "SIM_CODE_HASH_SHA256", "RESCUE_FROM"}:
            continue
        violations.extend([f"{kind}:{name}:{v}" for v in _thread_b_scan_value(str(row.get("value", "")))])
    return violations


def _make_sim_spec(
    *,
    item_id: str,
    probe_id: str,
    evidence_token: str,
    probe_term: str,
    rescue_from: str = "",
) -> dict:
    def_fields: list[dict] = [
        _def_field("F_EVID", "REQUIRES_EVIDENCE", _token(evidence_token)),
        _def_field("F_SIMID", "SIM_ID", _token(item_id)),
        _def_field("F_PTERM", "PROBE_TERM", _token(probe_term)),
    ]
    if rescue_from:
        def_fields.append(_def_field("F_RFROM", "RESCUE_FROM", _token(rescue_from)))

    asserts = [
        _assert("A_EVID", "EVIDENCE_TOKEN", evidence_token),
        _assert("A_PROBE", "PROBE_TOKEN", f"PT_{probe_id}"),
    ]
    return {
        "item_class": "SPEC_HYP",
        "id": item_id,
        "kind": "SIM_SPEC",
        "requires": [probe_id],
        "def_fields": def_fields,
        "asserts": asserts,
        "operator_id": "OP_REPAIR_DEF_FIELD",
    }


def _make_math_def(*, item_id: str, probe_id: str, sim_code_hash_sha256: str) -> dict:
    # Kernel requires DOMAIN/CODOMAIN fields. Values remain Thread B fenced.
    def_fields: list[dict] = [
        _def_field("F_OBJ", "OBJECTS", _token("density_matrix")),
        _def_field("F_OPS", "OPERATIONS", _token("partial_trace cptp_channel unitary_operator")),
        _def_field("F_INV", "INVARIANTS", _token("trace")),
        _def_field("F_DOM", "DOMAIN", _token("finite dimensional hilbert space")),
        _def_field("F_COD", "CODOMAIN", _token("density matrix")),
        _def_field("F_HASH", "SIM_CODE_HASH_SHA256", _token(sim_code_hash_sha256)),
    ]
    asserts = [_assert("A_MATH", "MATH_TOKEN", f"MT_{item_id}")]
    return {
        "item_class": "SPEC_HYP",
        "id": item_id,
        "kind": "MATH_DEF",
        "requires": [probe_id],
        "def_fields": def_fields,
        "asserts": asserts,
        "operator_id": "OP_REPAIR_DEF_FIELD",
    }


def _make_term_def(*, item_id: str, math_def_id: str, term_literal: str) -> dict:
    def_fields: list[dict] = [
        _def_field("F_TERM", "TERM", _token(term_literal)),
        _def_field("F_BINDS", "BINDS", _token(math_def_id)),
    ]
    asserts = [_assert("A_TERM", "TERM_TOKEN", f"TT_{term_literal}")]
    return {
        "item_class": "SPEC_HYP",
        "id": item_id,
        "kind": "TERM_DEF",
        "requires": [math_def_id],
        "def_fields": def_fields,
        "asserts": asserts,
        "operator_id": "OP_REPAIR_DEF_FIELD",
    }


def _make_canon_permit(*, item_id: str, term_def_id: str, term_literal: str, evidence_token: str) -> dict:
    def_fields: list[dict] = [
        _def_field("F_TERM", "TERM", _token(term_literal)),
        _def_field("F_EVID", "REQUIRES_EVIDENCE", _token(evidence_token)),
    ]
    asserts = [_assert("A_PERMIT", "PERMIT_TOKEN", f"PT_{item_id}")]
    return {
        "item_class": "SPEC_HYP",
        "id": item_id,
        "kind": "CANON_PERMIT",
        "requires": [term_def_id],
        "def_fields": def_fields,
        "asserts": asserts,
        "operator_id": "OP_REPAIR_DEF_FIELD",
    }


def _make_canonical_ascent_unit(*, step: int, index: int) -> list[dict]:
    # (A) MATH_DEF, (B) TERM_DEF, (C) CANON_PERMIT, (D) SIM_SPEC (evidence source)
    probe_id = _probe_id(step, 50000 + index)
    sim_code_hash = _SIM_STUB_HASH_SHA256
    math_id = _spec_id("MATH_ASCENT", step, index)
    term_id = _spec_id("TERM_ASCENT", step, index)
    permit_id = _spec_id("PERMIT_ASCENT", step, index)
    sim_id = _spec_id("SIM_ASCENT", step, index)
    evidence = f"E_{sim_id}"

    math_def = _make_math_def(item_id=math_id, probe_id=probe_id, sim_code_hash_sha256=sim_code_hash)
    term_literal = "density_matrix_generator"
    term_def = _make_term_def(item_id=term_id, math_def_id=math_id, term_literal=term_literal)
    permit = _make_canon_permit(item_id=permit_id, term_def_id=term_id, term_literal=term_literal, evidence_token=evidence)
    sim_spec = _make_sim_spec(
        item_id=sim_id,
        probe_id=probe_id,
        evidence_token=evidence,
        probe_term="density_matrix",
    )
    return [math_def, term_def, permit, sim_spec]


@dataclass(frozen=True)
class AutowiggleConfig:
    # How many candidates A0 will emit into the EXPORT_BLOCK.
    max_items: int = 140
    # How many SIM tasks will be executed per step.
    max_sims: int = 110
    # Strategy population sizing.
    target_count: int = 90
    alternative_count: int = 50
    # When graveyard is non-empty, >= this fraction of targets should be rescues.
    graveyard_rescue_fraction: float = 0.50
    max_graveyard_rescue: int = 400


def _probe_id(step: int, index: int) -> str:
    # Must match a0_compiler.py _PROBE_ID_RE: ^P_[A-Za-z0-9_]+$
    return f"P_AUTOWIGGLE_{step:06d}_{index:05d}"


def _spec_id(prefix: str, step: int, index: int) -> str:
    return f"S{step:06d}_{prefix}_{index:05d}"


def _engine_cycle_sweep(step: int, count: int, *, start_index: int = 1) -> list[dict]:
    outer_seqs = ["SE NE NI SI", "NE NI SI SE", "NI SI SE NE", "SI SE NE NI"]
    inner_seqs = ["SI NI NE SE", "SE SI NI NE", "NE SE SI NI", "NI NE SE SI"]
    classes = [("DEDUCTIVE", "INDUCTIVE"), ("INDUCTIVE", "DEDUCTIVE")]
    gammas = ["0_12", "0_20", "0_35", "0_55"]
    ps = ["0_10", "0_25", "0_40"]
    qs = ["0_05", "0_15", "0_30"]
    thetas = ["0_25", "0_50", "0_75"]

    out: list[dict] = []
    for i in range(count):
        idx = start_index + i
        item_id = _spec_id("SIM_ENGINE", step, idx)
        probe_id = _probe_id(step, idx)
        evidence = f"E_{item_id}"

        outer_seq = outer_seqs[(idx + step) % len(outer_seqs)]
        inner_seq = inner_seqs[(idx * 3 + step) % len(inner_seqs)]
        outer_class, inner_class = classes[(idx + step) % len(classes)]
        semantic = {
            "ENGINE_OUTER_SEQ": outer_seq,
            "ENGINE_INNER_SEQ": inner_seq,
            "ENGINE_OUTER_CLASS": outer_class,
            "ENGINE_INNER_CLASS": inner_class,
            "ENGINE_GAMMA": gammas[idx % len(gammas)],
            "ENGINE_P": ps[idx % len(ps)],
            "ENGINE_Q": qs[idx % len(qs)],
            "ENGINE_THETA": thetas[idx % len(thetas)],
            "WIGGLE_SEED": f"V{step:04d}_{idx:05d}",
        }
        out.append(
            _make_sim_spec(
                item_id=item_id,
                probe_id=probe_id,
                evidence_token=evidence,
                probe_term="engine_cycle",
                tier="T5_ENGINE",
                family="ENGINE_CYCLE_SWEEP",
                target_class="TC_ENGINE",
                branch_track="TRACK_ENGINE_CYCLE",
                semantic_fields=semantic,
            )
        )
    return out


def _operator_order_sweep(step: int, count: int, *, start_index: int = 1) -> list[dict]:
    terms = [
        "noncommutative_composition_order",
        "variance_order",
        "trajectory_correlation",
        "correlation_polarity",
    ]
    families = ["ORDER_STRESS", "PERTURBATION_CLASSIFIER", "BOUNDARY_SWEEP", "COMPOSITION_STRESS"]
    out: list[dict] = []
    for i in range(count):
        idx = start_index + i
        term = terms[(idx + step) % len(terms)]
        family = families[(idx * 7 + step) % len(families)]
        item_id = _spec_id("SIM_ORDER", step, idx)
        probe_id = _probe_id(step, 10000 + idx)
        evidence = f"E_{item_id}"
        semantic = {"ORDER_FAMILY": family, "ORDER_SEED": f"O{step:04d}_{idx:05d}"}
        out.append(
            _make_sim_spec(
                item_id=item_id,
                probe_id=probe_id,
                evidence_token=evidence,
                probe_term=term,
                tier="T2_OPERATOR",
                family=family,
                target_class="TC_ORDER",
                branch_track="TRACK_OPERATOR_ORDER",
                semantic_fields=semantic,
            )
        )
    return out


def _witness_sweep(step: int, count: int, *, start_index: int = 1) -> list[dict]:
    terms = ["information_work_extraction_bound", "density_entropy", "density_purity", "entropy_production_rate"]
    out: list[dict] = []
    for i in range(count):
        idx = start_index + i
        term = terms[(idx + 3 * step) % len(terms)]
        item_id = _spec_id("SIM_WIT", step, idx)
        probe_id = _probe_id(step, 20000 + idx)
        evidence = f"E_{item_id}"
        semantic = {"WITNESS_SEED": f"W{step:04d}_{idx:05d}"}
        out.append(
            _make_sim_spec(
                item_id=item_id,
                probe_id=probe_id,
                evidence_token=evidence,
                probe_term=term,
                tier="T3_STRUCTURE",
                family="WITNESS_SWEEP",
                target_class="TC_WITNESS",
                branch_track="TRACK_WITNESS",
                semantic_fields=semantic,
            )
        )
    return out


def _negative_poison_sims(step: int, count: int, *, start_index: int = 1) -> list[dict]:
    # Thread B fences forbid the earlier poison tokens. Keep an alternatives lane with
    # structurally distinct SIM_SPEC variants but no derived-only tokens.
    patterns = [
        ("density_matrix", "ALT_A"),
        ("finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator", "ALT_B"),
    ]
    out: list[dict] = []
    for i in range(count):
        idx = start_index + i
        probe_term, family = patterns[(idx + step) % len(patterns)]
        item_id = _spec_id("SIM_NEG", step, idx)
        probe_id = _probe_id(step, 30000 + idx)
        evidence = f"E_{item_id}"
        out.append(
            _make_sim_spec(
                item_id=item_id,
                probe_id=probe_id,
                evidence_token=evidence,
                probe_term=probe_term,
            )
        )
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / float(len(union))


def _build_graveyard_rescues(state: KernelState, step: int, limit: int) -> list[dict]:
    items = list(state.graveyard.values())
    items.sort(key=lambda row: (str(row.get("killed_in_batch_id", "")), str(row.get("id", ""))), reverse=True)
    rescues: list[dict] = []
    for index, row in enumerate(items[:limit], start=1):
        killed_id = str(row.get("id", "")).strip()
        if not killed_id:
            continue
        killed_text = str(row.get("item_text", ""))
        # Rescue mutation rule: mutate structure deterministically using Thread-B-safe tokens.
        semantic: dict[str, str] = {}
        if (index + step) % 3 == 0:
            probe_term = "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator"
            semantic["MUTATION"] = "unitary"
        elif (index + step) % 3 == 1:
            probe_term = "density_matrix"
            semantic["MUTATION"] = "partial"
        else:
            probe_term = "density_matrix"
            semantic["MUTATION"] = "trace"
        semantic["RESCUE_SEED"] = f"R{step:04d}_{index:05d}"

        parent_tokens = set(_tokens_from_text(killed_text))
        child_tokens = set(_tokens_from_text(" ".join([probe_term, semantic.get("MUTATION", ""), killed_id])))
        if _jaccard(parent_tokens, child_tokens) > 0.80:
            continue

        item_id = _spec_id("SIM_RESCUE", step, index)
        probe_id = _probe_id(step, 40000 + index)
        evidence = f"E_{item_id}"

        rescues.append(
            _make_sim_spec(
                item_id=item_id,
                probe_id=probe_id,
                evidence_token=evidence,
                probe_term=probe_term,
                rescue_from=killed_id,
            )
        )
    return rescues


def generate_autowiggle_strategy(
    *,
    state: KernelState,
    step: int,
    last_tags: list[str] | None = None,
    config: AutowiggleConfig | None = None,
) -> dict:
    last_tags = last_tags or []
    config = config or AutowiggleConfig()

    targets: list[dict] = []
    # Emit canonical ascent unit(s) first - ALWAYS emit to satisfy precheck requirements.
    ascent_units = 1  # Always emit at least 1 canonical ascent unit per step
    if int(getattr(state, "unchanged_ledger_streak", 0) or 0) >= 5:
        ascent_units = max(ascent_units, 2)
    graveyard_size = len(state.graveyard)
    registry_size = len(state.term_registry)
    reduce_alternatives = graveyard_size > max(1, registry_size) * 3
    for idx in range(1, ascent_units + 1):
        targets.extend(_make_canonical_ascent_unit(step=step, index=idx))

    if state.graveyard:
        rescues = _build_graveyard_rescues(state, step, limit=min(config.max_graveyard_rescue, config.target_count))
        min_rescue = int(math.ceil(config.target_count * max(0.0, min(1.0, config.graveyard_rescue_fraction))))
        targets.extend(rescues[:min_rescue])

    remaining = max(0, config.target_count - len(targets))
    for i in range(remaining):
        idx = 1 + len(targets)
        item_id = _spec_id("SIM_EXPLORE", step, idx)
        probe_id = _probe_id(step, 60000 + idx)
        evidence = f"E_{item_id}"
        probe_term = "density_matrix" if (idx + step) % 2 == 0 else "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator"
        targets.append(
            _make_sim_spec(
                item_id=item_id,
                probe_id=probe_id,
                evidence_token=evidence,
                probe_term=probe_term,
            )
        )

    alt_count = max(1, config.alternative_count)
    if reduce_alternatives:
        alt_count = max(1, alt_count // 2)
    alternatives = _negative_poison_sims(step, alt_count, start_index=1)

    strategy: dict[str, Any] = {
        "schema": "A1_STRATEGY_v1",
        "strategy_id": f"AUTOWIGGLE_STEP_{step:06d}",
        "inputs": {
            "state_hash": state.hash(),
            "fuel_slice_hashes": [],
            "bootpack_rules_hash": _sha256_text("bootpack_b_kernel_v1"),
            "pinned_ruleset_sha256": str(getattr(state, "active_ruleset_sha256", "") or ""),
            "pinned_megaboot_sha256": str(getattr(state, "active_megaboot_sha256", "") or ""),
        },
        "budget": {"max_items": int(config.max_items), "max_sims": int(config.max_sims)},
        "policy": {
            "forbid_fields": ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"],
            "overlay_ban_terms": ["axis", "igt", "mbti", "jung"],
            "require_try_to_fail": True,
            # Optional substance gates enforced by A0 compiler.
            "enforce_graveyard_rescue_share": True,
            "min_graveyard_rescue_share": 0.50,
            "min_sim_spec_count": 60,
            "required_probe_terms": [
                "density_matrix",
            ],
        },
        "targets": targets,
        "alternatives": alternatives,
        "sims": {"positive": [], "negative": []},
        "self_audit": {
            "strategy_hash": "",
            "compile_lane_digest": "",
            "candidate_count": len(targets),
            "alternative_count": len(alternatives),
            "operator_ids_used": ["OP_REPAIR_DEF_FIELD"],
        },
    }

    strategy["self_audit"]["compile_lane_digest"] = _sha256_json(
        {
            "targets": [c["id"] for c in targets[:20]],
            "alternatives": [c["id"] for c in alternatives[:20]],
            "graveyard_size": len(state.graveyard),
            "step": step,
        }
    )

    # Pre-emission validation (Thread B fences + required ascent unit).
    candidates = targets + alternatives
    kinds = [str(c.get("kind", "")).upper() for c in candidates]
    if "MATH_DEF" not in kinds:
        raise ValueError("AUTOWIGGLE_PRECHECK_FAIL:MATH_DEF_MISSING")
    if "TERM_DEF" not in kinds:
        raise ValueError("AUTOWIGGLE_PRECHECK_FAIL:TERM_DEF_MISSING")
    if "CANON_PERMIT" not in kinds:
        raise ValueError("AUTOWIGGLE_PRECHECK_FAIL:CANON_PERMIT_MISSING")
    if "SIM_SPEC" not in kinds:
        raise ValueError("AUTOWIGGLE_PRECHECK_FAIL:SIM_SPEC_MISSING")

    permit_evidence = set()
    for c in candidates:
        if str(c.get("kind", "")).upper() != "CANON_PERMIT":
            continue
        for row in c.get("def_fields", []):
            if str(row.get("name", "")).upper() == "REQUIRES_EVIDENCE":
                permit_evidence.add(str(row.get("value", "")).strip())
    sim_evidence = set()
    for c in candidates:
        if str(c.get("kind", "")).upper() != "SIM_SPEC":
            continue
        for row in c.get("def_fields", []):
            if str(row.get("name", "")).upper() == "REQUIRES_EVIDENCE":
                sim_evidence.add(str(row.get("value", "")).strip())
    if not (permit_evidence & sim_evidence):
        raise ValueError("AUTOWIGGLE_PRECHECK_FAIL:PERMIT_SIM_EVIDENCE_DISJOINT")

    violations: list[str] = []
    for c in candidates:
        violations.extend(_thread_b_scan_candidate(c))
    if violations:
        raise ValueError("AUTOWIGGLE_THREAD_B_FENCE_FAIL:" + "|".join(sorted(set(violations))[:40]))
    return strategy

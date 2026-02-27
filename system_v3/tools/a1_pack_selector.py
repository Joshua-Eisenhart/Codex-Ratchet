#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
import re


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"

BOOTPACK = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1"
PLANNER_PATH = BOOTPACK / "tools" / "a1_adaptive_ratchet_planner.py"
CORE_PROBE_ANCHORS = (
    "density_matrix",
    "probe_operator",
    "cptp_channel",
    "unitary_operator",
    "partial_trace",
    "correlation_polarity",
    "qit_master_conjunction",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_state(run_dir: Path) -> dict:
    state_path = run_dir / "state.json"
    if not state_path.exists():
        return {}
    return _read_json(state_path)


def _canonical_terms(state: dict) -> set[str]:
    term_registry = state.get("term_registry", {}) if isinstance(state.get("term_registry", {}), dict) else {}
    out: set[str] = set()
    for term, row in term_registry.items():
        if not isinstance(row, dict):
            continue
        if str(row.get("state", "")) == "CANONICAL_ALLOWED":
            out.add(str(term))
    return out


_DEF_FIELD_PROBE_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+PROBE_TERM\s+(.+)$")
_DEF_FIELD_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+TERM\s+(.+)$")
_DEF_FIELD_GOAL_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+GOAL_TERM\s+(.+)$")
_TERM_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{0,120}$")


def _extract_term_from_item_text(item_text: str) -> str:
    goal_term = ""
    term_field = ""
    probe_term = ""
    for raw_line in str(item_text or "").splitlines():
        line = raw_line.strip()
        m = _DEF_FIELD_GOAL_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if _TERM_TOKEN_RE.fullmatch(value):
                goal_term = value
                continue
        m = _DEF_FIELD_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if _TERM_TOKEN_RE.fullmatch(value):
                term_field = value
                continue
        m = _DEF_FIELD_PROBE_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if _TERM_TOKEN_RE.fullmatch(value):
                probe_term = value
                continue
    return goal_term or term_field or probe_term


def _rescue_terms_from_targets(state: dict, targets: list[str]) -> list[str]:
    if not targets:
        return []
    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    survivor = state.get("survivor_ledger", {}) if isinstance(state.get("survivor_ledger", {}), dict) else {}
    parked = state.get("park_set", {}) if isinstance(state.get("park_set", {}), dict) else {}
    out: list[str] = []
    for raw in targets:
        target = str(raw).strip()
        if not target:
            continue
        if _TERM_TOKEN_RE.fullmatch(target):
            out.append(target)
            continue
        row = graveyard.get(target) or survivor.get(target) or parked.get(target)
        if isinstance(row, dict):
            term = _extract_term_from_item_text(str(row.get("item_text", "")))
            if term:
                out.append(term)
    dedup: list[str] = []
    seen: set[str] = set()
    for term in out:
        if term in seen:
            continue
        seen.add(term)
        dedup.append(term)
    return dedup


def _graveyard_terms(state: dict) -> set[str]:
    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    out: set[str] = set()
    for row in graveyard.values():
        if not isinstance(row, dict):
            continue
        term = _extract_term_from_item_text(str(row.get("item_text", "")))
        if term:
            out.add(term)
    return out


def _negative_markers_for_class(neg_cls: str) -> tuple[tuple[str, str], ...]:
    c = str(neg_cls).strip().upper()
    if c == "CLASSICAL_TIME":
        return (("TIME_PARAM", "T"),)
    if c == "INFINITE_SET":
        return (("ASSUME_INFINITE", "TRUE"), ("INFINITE_SET", "TRUE"))
    if c == "CONTINUOUS_BATH":
        return (("CONTINUOUS_BATH", "TRUE"),)
    if c == "INFINITE_RESOLUTION":
        return (("INFINITE_RESOLUTION", "TRUE"),)
    if c == "PRIMITIVE_EQUALS":
        return (("EQUALS_PRIMITIVE", "TRUE"), ("ASSUME_IDENTITY_EQUIVALENCE", "TRUE"))
    if c == "EUCLIDEAN_METRIC":
        return (("EUCLIDEAN_METRIC", "TRUE"), ("CARTESIAN_COORDINATE", "TRUE"))
    if c == "CLASSICAL_TEMPERATURE":
        return (("TEMPERATURE_BATH", "TRUE"), ("TEMPERATURE_PARAM", "K"))
    # Default: commutation smuggle.
    return (("ASSUME_COMMUTATIVE", "TRUE"),)


def _parse_csv_terms(raw: str) -> set[str]:
    out: set[str] = set()
    for part in str(raw or "").split(","):
        t = part.strip()
        if not t:
            continue
        if _TERM_TOKEN_RE.fullmatch(t):
            out.add(t)
    return out


@dataclass(frozen=True)
class Goal:
    term: str
    track: str
    negative_class: str
    negative_markers: tuple[tuple[str, str], ...]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Select a batch from cold-core proposals and emit A1_STRATEGY_v1 (schema-valid).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT), help="Override runs root (default: system_v3/runs).")
    ap.add_argument("--cold-core", default="", help="Path to A1_COLD_CORE_PROPOSALS_v1.json. Default: run sandbox cold_core latest.")
    ap.add_argument("--sequence", type=int, default=0, help="Sequence for naming only (0 means infer from cold-core).")
    ap.add_argument("--track", default="ENGINE_ENTROPY_EXPLORATION")
    ap.add_argument("--debate-mode", choices=["balanced", "graveyard_first", "graveyard_recovery"], default="graveyard_first")
    ap.add_argument("--goal-selection", choices=["interleaved", "closure_first"], default="interleaved")
    ap.add_argument(
        "--graveyard-fill-policy",
        choices=["anchor_replay", "fuel_full_load"],
        default="anchor_replay",
        help="In graveyard_first mode, choose anchor replay (legacy) or fuel_full_load (prioritize un-graveyarded fuel terms).",
    )
    ap.add_argument(
        "--forbid-rescue-in-graveyard-first",
        action="store_true",
        help="If set, remove RESCUE_FROM bindings from alternatives while in graveyard_first mode.",
    )
    ap.add_argument(
        "--max-terms",
        type=int,
        default=0,
        help="Optional override for max number of term goals selected in this strategy.",
    )
    ap.add_argument(
        "--graveyard-library-terms",
        default="",
        help="Comma-separated term tokens that should be treated as graveyard-library only (never rescued).",
    )
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    runs_root = Path(args.runs_root).expanduser().resolve()
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise SystemExit(f"missing run dir: {run_dir}")

    sandbox_root = run_dir / "a1_sandbox"
    cold_core_path = Path(args.cold_core).expanduser().resolve() if str(args.cold_core).strip() else None
    if cold_core_path is None:
        cold_dir = sandbox_root / "cold_core"
        candidates = sorted(cold_dir.glob("*_A1_COLD_CORE_PROPOSALS_v1.json"))
        if not candidates:
            raise SystemExit(f"no cold core proposals found in {cold_dir}")
        cold_core_path = candidates[-1]

    proposals = _read_json(cold_core_path)
    if str(proposals.get("schema", "")).strip() != "A1_COLD_CORE_PROPOSALS_v1":
        raise SystemExit("cold-core schema mismatch")

    sequence = int(args.sequence) if int(args.sequence) > 0 else int(proposals.get("sequence", 0) or 0)
    if sequence <= 0:
        sequence = 1

    state = _load_state(run_dir)
    canon = _canonical_terms(state)

    raw_candidates = [t for t in proposals.get("admissible_term_candidates", []) if isinstance(t, str) and t.strip()]
    rescue_targets = [t for t in proposals.get("graveyard_rescue_targets", []) if isinstance(t, str) and t.strip()]
    rescue_terms = _rescue_terms_from_targets(state, rescue_targets)
    graveyard_library_terms = _parse_csv_terms(str(args.graveyard_library_terms))
    if graveyard_library_terms:
        rescue_terms = [t for t in rescue_terms if t not in graveyard_library_terms]
    graveyard_terms = _graveyard_terms(state)

    term_candidates = [t for t in raw_candidates if t not in canon]
    canonical_nonroot = sorted({t for t in canon if t not in {"f01_finitude", "n01_noncommutation"}})
    fuel_unseen_set: set[str] = set()
    if str(args.debate_mode) == "graveyard_first" and str(args.graveyard_fill_policy) == "anchor_replay":
        # Graveyard-fill should primarily exercise already-admitted anchors so the
        # run builds failure topology first, then recovers. Only bootstrap fresh
        # terms when there are not enough canonical anchors yet.
        anchor_candidates = rescue_terms if rescue_terms else canonical_nonroot
        if anchor_candidates and len(canonical_nonroot) >= 4:
            term_candidates = list(anchor_candidates)
    if str(args.debate_mode) == "graveyard_first" and str(args.graveyard_fill_policy) == "fuel_full_load":
        unseen_terms = [t for t in term_candidates if t not in graveyard_terms]
        seen_terms = [t for t in term_candidates if t in graveyard_terms]
        fuel_unseen_set = set(unseen_terms)
        if unseen_terms:
            term_candidates = unseen_terms + seen_terms
    if str(args.debate_mode) == "graveyard_recovery" and rescue_terms:
        # Recovery mode intentionally allows canonical terms as anchors, because
        # rescue lanes are about re-working killed branches around those anchors.
        merged: list[str] = []
        for term in rescue_terms + raw_candidates:
            if term and term not in merged:
                merged.append(term)
        term_candidates = merged
    if str(args.debate_mode) == "graveyard_recovery":
        # Planner intentionally skips rescue expansion when the goal term is master conjunction.
        # In recovery phase we prioritize non-master rescue targets to force active graveyard work,
        # but allow periodic master-conjunction attempts so recovery can still close the top witness.
        allow_master = (
            "qit_master_conjunction" not in canon
            and len(canon) >= 20
            and (int(sequence) % 5 == 0)
        )
        non_master = [t for t in term_candidates if t != "qit_master_conjunction" or allow_master]
        if non_master:
            term_candidates = non_master
    if str(args.debate_mode) == "graveyard_recovery" and graveyard_library_terms:
        term_candidates = [t for t in term_candidates if t not in graveyard_library_terms]
    if not term_candidates:
        # Recovery mode needs to keep moving even when all proposed terms are already canonical.
        # In that case, we re-target a canonical term (preferably a “system segment” term)
        # to generate explicit rescue SIMs via the planner's graveyard_recovery wiring.
        if str(args.debate_mode) == "graveyard_recovery":
            fallback = sorted({t for t in canon if t and t not in {"f01_finitude", "n01_noncommutation"}})
            if graveyard_library_terms:
                fallback = [t for t in fallback if t not in graveyard_library_terms]
            if fallback:
                term_candidates = fallback
        if not term_candidates:
            raise SystemExit("no admissible term candidates (all canonical or filtered)")

    neg_classes = [c for c in proposals.get("proposed_negative_classes", []) if isinstance(c, str) and c.strip()]
    neg_classes = [c.strip().upper() for c in neg_classes]
    # Prefer commutation-smuggling as baseline, but in graveyard-first mode we
    # intentionally rotate across all available negative classes to build a wider
    # classical-failure graveyard surface.
    track_upper = str(args.track).upper()
    if str(args.debate_mode) == "graveyard_first" and neg_classes:
        sequence_idx = max(0, int(sequence) - 1)
        primary_neg = neg_classes[sequence_idx % len(neg_classes)]
    else:
        if "SZILARD" in track_upper or "CARNOT" in track_upper:
            if "CONTINUOUS_BATH" in neg_classes:
                primary_neg = "CONTINUOUS_BATH"
            elif "CLASSICAL_TIME" in neg_classes:
                primary_neg = "CLASSICAL_TIME"
            elif "COMMUTATIVE_ASSUMPTION" in neg_classes:
                primary_neg = "COMMUTATIVE_ASSUMPTION"
            else:
                primary_neg = neg_classes[0] if neg_classes else "COMMUTATIVE_ASSUMPTION"
        else:
            if "COMMUTATIVE_ASSUMPTION" in neg_classes:
                primary_neg = "COMMUTATIVE_ASSUMPTION"
            else:
                primary_neg = neg_classes[0] if neg_classes else "COMMUTATIVE_ASSUMPTION"
    if primary_neg not in {
        "COMMUTATIVE_ASSUMPTION",
        "CLASSICAL_TIME",
        "INFINITE_SET",
        "CONTINUOUS_BATH",
        "INFINITE_RESOLUTION",
        "PRIMITIVE_EQUALS",
        "EUCLIDEAN_METRIC",
        "CLASSICAL_TEMPERATURE",
    }:
        primary_neg = "COMMUTATIVE_ASSUMPTION"

    preferred = (
        "finite_dimensional_hilbert_space",
        "density_matrix",
        "probe_operator",
        "cptp_channel",
        "unitary_operator",
        "partial_trace",
        "correlation_polarity",
        # “Glue” term needed for higher-tier probes/sims and the semantic gate.
        "qit_master_conjunction",
        "nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
        "information_work_extraction_bound",
        "erasure_channel_entropy_cost_lower_bound",
        # Szilard/Carnot bridge primitives (ratchet-safe: have real SIM probes).
        "measurement_operator",
        "observable_operator",
        "projector_operator",
        "pauli_operator",
        "bloch_sphere",
        "hopf_fibration",
        "hopf_torus",
        "berry_flux",
        "spinor_double_cover",
        "left_weyl_spinor",
        "right_weyl_spinor",
        "left_action_superoperator",
        "right_action_superoperator",
        "noncommutative_composition_order",
        "lindblad_generator",
        "liouvillian_superoperator",
        "channel_realization",
        "left_right_action_entropy_production_rate_orthogonality",
        "variance_order_trajectory_correlation_orthogonality",
        "channel_realization_correlation_polarity_orthogonality",
        "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator",
        "kraus_representation",
        "density_purity",
        "density_entropy",
        "von_neumann_entropy",
        "coherence_decoherence",
        "trajectory_correlation",
        "entropy_production_rate",
        "engine_cycle",
        "kraus_operator",
        "kraus_channel",
        "measurement_operator",
        "observable_operator",
        "commutator_operator",
        "von_neumann_entropy",
        "eigenvalue_spectrum",
        "positive_semidefinite",
        "trace_one",
        "lindblad_generator",
        "hamiltonian_operator",
        "noncommutative_composition_order",
    )
    probe_capable_terms = set(preferred)
    rank = {t: i for i, t in enumerate(preferred)}
    rescue_rank = {t: i for i, t in enumerate(rescue_terms)}
    term_candidates = sorted(
        term_candidates,
        key=lambda t: (
            (0 if (str(args.debate_mode) == "graveyard_first" and str(args.graveyard_fill_policy) == "fuel_full_load" and t in fuel_unseen_set) else 1),
            0 if t in rescue_rank else 1,
            rescue_rank.get(t, 10_000),
            rank.get(t, 10_000),
            t,
        ),
    )
    if str(args.debate_mode) == "graveyard_recovery":
        rescue_bucket = [t for t in term_candidates if t in rescue_rank]
        frontier_bucket = [
            t for t in term_candidates if t not in rescue_rank and t in raw_candidates and t not in canon
        ]
        other_bucket = [t for t in term_candidates if t not in rescue_bucket and t not in frontier_bucket]
        # Recovery must stay tied to graveyard, but still advance frontier terms.
        blended = rescue_bucket[:8] + frontier_bucket[:8]
        for t in rescue_bucket[8:] + frontier_bucket[8:] + other_bucket:
            if t not in blended:
                blended.append(t)
        term_candidates = blended
        # Recovery mode should primarily exercise terms with real probe implementations
        # so semantic pressure reflects math behavior rather than fallback probe noise.
        probe_first = [t for t in term_candidates if t in probe_capable_terms]
        non_probe_tail = [t for t in term_candidates if t not in probe_capable_terms]
        if probe_first:
            term_candidates = probe_first + non_probe_tail[:2]

    max_terms = int(args.max_terms) if int(args.max_terms) > 0 else (24 if str(args.debate_mode) == "graveyard_first" else 16)
    if str(args.debate_mode) == "graveyard_first" and str(args.graveyard_fill_policy) == "fuel_full_load":
        anchor_candidates: list[str] = []
        source_pool = list(raw_candidates) + list(canonical_nonroot) + list(canon)
        for t in CORE_PROBE_ANCHORS:
            if t in source_pool:
                anchor_candidates.append(t)
        anchor_set = set(anchor_candidates)
        non_anchor = [t for t in term_candidates if t not in anchor_set]
        unseen_now = [t for t in non_anchor if t not in graveyard_terms]
        seen_now = [t for t in non_anchor if t in graveyard_terms]
        if unseen_now and len(unseen_now) > max_terms:
            # Deterministic rotation prevents starvation of long unseen-term frontiers.
            block = max(1, int(max_terms))
            offset = ((max(1, int(sequence)) - 1) * block) % len(unseen_now)
            unseen_now = unseen_now[offset:] + unseen_now[:offset]
        ordered = anchor_candidates + unseen_now + seen_now
        dedup: list[str] = []
        seen_terms: set[str] = set()
        for t in ordered:
            if t in seen_terms:
                continue
            seen_terms.add(t)
            dedup.append(t)
        term_candidates = dedup

    goals: list[Goal] = []
    for term in term_candidates[: max_terms]:
        goals.append(
            Goal(
                term=str(term),
                track=str(args.track),
                negative_class=str(primary_neg),
                negative_markers=_negative_markers_for_class(primary_neg),
            )
        )

    # Import planner builder directly (keeps strategy schema identical to known-good emission).
    # Use sys.path import to avoid dataclass issues from ad-hoc module loading.
    tools_dir = (BOOTPACK / "tools").resolve()
    bootpack_base = BOOTPACK.resolve()
    for p in (str(tools_dir), str(bootpack_base)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import a1_adaptive_ratchet_planner as mod  # type: ignore
    except Exception as exc:
        raise SystemExit(f"failed to import planner: {exc}")

    strategy = mod.build_strategy_from_state(
        state=state,
        run_id=run_id,
        sequence=int(sequence),
        goals=tuple(goals),
        goal_selection=str(args.goal_selection),
        debate_mode=str(args.debate_mode),
    )

    if str(args.debate_mode) == "graveyard_first" and bool(args.forbid_rescue_in_graveyard_first):
        for item in strategy.get("alternatives", []) if isinstance(strategy, dict) else []:
            if not isinstance(item, dict):
                continue
            defs = item.get("def_fields", [])
            if not isinstance(defs, list):
                continue
            item["def_fields"] = [
                row
                for row in defs
                if not (isinstance(row, dict) and str(row.get("name", "")).strip() == "RESCUE_FROM")
            ]

    out_dir = sandbox_root / "outgoing"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{sequence:06d}_A1_STRATEGY_v1__PACK_SELECTOR.json"
    out_path.write_text(json.dumps(strategy, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": "A1_PACK_SELECTOR_RESULT_v1", "out": str(out_path), "cold_core": str(cold_core_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))

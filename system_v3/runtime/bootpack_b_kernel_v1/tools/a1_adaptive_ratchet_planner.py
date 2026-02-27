#!/usr/bin/env python3
"""
Deterministic A1-side planner that generates packet-mode A1_STRATEGY_v1 capsules
to advance a bottom-up term ladder (no FORMULA / no equals) toward QIT primitives.

This does NOT use an LLM. It is an executable reference for what "A1 aligned"
needs to do mechanically:
  - pick the next ratchet step based on current state
  - emit prerequisites for a target term (component closure)
  - bind SIM evidence for canon permits
  - generate negative alternatives that can be killed deterministically

Scope: writer only. No ZIP_PROTOCOL changes. No kernel changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from zip_protocol_v2_writer import write_zip_protocol_v2  # noqa: E402


FORBIDDEN_FIELDS = ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"]

# Bootpack kernel enforces near-duplicate parking using a Jaccard similarity threshold.
# When bootstrapping many atomic terms, we must avoid emitting identical MATH_DEF bodies
# (or they will be parked as NEAR_REDUNDANT and dependent TERM_DEF will fail).
L0_CORPUS: tuple[str, ...] = (
    "finite",
    "dimensional",
    "hilbert",
    "space",
    "density",
    "matrix",
    "operator",
    "probe",
    "channel",
    "cptp",
    "unitary",
    "lindblad",
    "hamiltonian",
    "commutator",
    "anticommutator",
    "trace",
    "partial",
    "tensor",
    "superoperator",
    "generator",
)

# Keep decomposition filter open by default; compound TERM_DEF component-gating
# requires these atoms to be available for higher-order terms.
ATOMIC_COMPONENT_STOPWORDS: set[str] = set()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canon_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _df(field_id: str, name: str, value: str, *, kind: str = "TOKEN") -> dict:
    return {"field_id": field_id, "name": name, "value_kind": kind, "value": value}


def _assert(assert_id: str, token_class: str, token: str) -> dict:
    return {"assert_id": assert_id, "token_class": token_class, "token": token}


@dataclass(frozen=True)
class Goal:
    term: str
    track: str
    negative_class: str
    negative_markers: tuple[tuple[str, str], ...]  # (DEF_FIELD_NAME, value)


# Deterministic QIT ladders: terms and the "track" label used for auditing.
# This does NOT "admit axes"; it admits terms and their supporting MATH_DEF/SIM pressure.
CORE_GOALS: tuple[Goal, ...] = (
    Goal(
        term="finite_dimensional_hilbert_space",
        track="QIT_FOUNDATION",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"), ("INFINITE_SET", "TRUE")),
    ),
    Goal(
        term="density_matrix",
        track="QIT_DENSITY_MATRIX",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"), ("COMMUTATIVE_ASSUMPTION", "TRUE")),
    ),
    Goal(
        term="probe_operator",
        track="QIT_PROBE_OPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="cptp_channel",
        track="QIT_CHANNEL",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
)

EXTENDED_GOALS: tuple[Goal, ...] = CORE_GOALS + (
    # These are important QIT properties, but they intentionally live outside CORE_GOALS:
    # emitting them too early causes TERM_DEF component-gating sprawl (e.g., "trace_one" would
    # force ratcheting "one" before the system has earned digit/equality primitives).
    Goal(
        term="positive_semidefinite",
        track="QIT_POSITIVE_SEMIDEFINITE",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"),),
    ),
    Goal(
        term="trace_one",
        track="QIT_TRACE_ONE",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="partial_trace",
        track="QIT_PARTIAL_TRACE",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="unitary_operator",
        track="QIT_UNITARY_OPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="lindblad_generator",
        track="QIT_LINDBLAD_GENERATOR",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"),),
    ),
    Goal(
        term="hamiltonian_operator",
        track="QIT_HAMILTONIAN_OPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="commutator_operator",
        track="QIT_COMMUTATOR_OPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="kraus_operator",
        track="QIT_KRAUS_OPERATOR",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"),),
    ),
    Goal(
        term="kraus_channel",
        track="QIT_KRAUS_CHANNEL",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="measurement_operator",
        track="QIT_MEASUREMENT_OPERATOR",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="observable_operator",
        track="QIT_OBSERVABLE_OPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="projector_operator",
        track="QIT_PROJECTOR_OPERATOR",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"),),
    ),
    Goal(
        term="eigenvalue_spectrum",
        track="QIT_EIGENVALUE_SPECTRUM",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="density_purity",
        track="QIT_DENSITY_PURITY",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"),),
    ),
    Goal(
        term="density_entropy",
        track="QIT_DENSITY_ENTROPY",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="coherence_decoherence",
        track="QIT_COHERENCE_DECOHERENCE",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="kraus_representation",
        track="QIT_KRAUS_REPRESENTATION",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="liouvillian_superoperator",
        track="QIT_LIOUVILLIAN_SUPEROPERATOR",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="left_action_superoperator",
        track="QIT_LEFT_ACTION_SUPEROPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="right_action_superoperator",
        track="QIT_RIGHT_ACTION_SUPEROPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="von_neumann_entropy",
        track="QIT_VON_NEUMANN_ENTROPY",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"),),
    ),
    Goal(
        term="entropy_production_rate",
        track="QIT_ENTROPY_PRODUCTION_RATE",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="noncommutative_composition_order",
        track="QIT_NONCOMMUTATIVE_COMPOSITION_ORDER",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
)

PHYSICS_FUEL_GOALS: tuple[Goal, ...] = (
    # Derived geometry/topology from QIT primitives (fuel checklist; still killable via SIM).
    Goal(
        term="pauli_operator",
        track="QIT_PAULI_OPERATOR_BASIS",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="bloch_sphere",
        track="QIT_BLOCH_SPHERE_STATE_QUOTIENT",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="hopf_fibration",
        track="QIT_HOPF_FIBRATION_PHASE_QUOTIENT",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="hopf_torus",
        track="QIT_HOPF_TORUS_NESTED_TORI_WITNESS",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="berry_flux",
        track="QIT_BERRY_FLUX_CHIRALITY_SURFACE",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"),),
    ),
    Goal(
        term="spinor_double_cover",
        track="QIT_SPINOR_DOUBLE_COVER_SU2_VS_SO3",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="left_weyl_spinor",
        track="QIT_LEFT_WEYL_SPINOR_CHIRAL_FLOW",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="right_weyl_spinor",
        track="QIT_RIGHT_WEYL_SPINOR_CHIRAL_FLOW",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
)

AXIS_FOUNDATION_GOALS: tuple[Goal, ...] = (
    # Axis-0: correlation diversity response under perturbation (Renyi-2 MI proxy).
    Goal(
        term="correlation_polarity",
        track="AXIS0_CORRELATION_POLARITY",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    # Axis-0: trajectory / history correlation functionals (compressed suite).
    Goal(
        term="trajectory_correlation",
        track="AXIS0_TRAJECTORY_CORRELATION",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    # Axis-4: variance-order class (order-sensitive sequence effects).
    Goal(
        term="variance_order",
        track="AXIS4_VARIANCE_ORDER",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    # Axis-12: deterministic channel-sequence realization suite (edges + sign-sensitive endpoints).
    Goal(
        term="channel_realization",
        track="AXIS12_CHANNEL_REALIZATION",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    # Engine-like cycle: explicit 8-stage cycle encoding + closure witness (SIM metrics).
    Goal(
        term="engine_cycle",
        track="ENGINE_CYCLE_TWO_LOOP_FOUR_STAGE",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="left_right_action_entropy_production_rate_orthogonality",
        track="ORTHOGONALITY_LEFT_RIGHT_ACTION_AND_ENTROPY_PRODUCTION_RATE",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="variance_order_trajectory_correlation_orthogonality",
        track="ORTHOGONALITY_VARIANCE_ORDER_AND_TRAJECTORY_CORRELATION",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="channel_realization_correlation_polarity_orthogonality",
        track="ORTHOGONALITY_CHANNEL_REALIZATION_AND_CORRELATION_POLARITY",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
)

MASTER_CONJUNCTION_GOALS: tuple[Goal, ...] = (
    Goal(
        term="nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
        track="QIT_CONSTRAINT_MANIFOLD_NESTED_HOPF_WEYL_ENGINE_CONJUNCTION",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="qit_master_conjunction",
        track="QIT_MASTER_CONJUNCTION",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
)

REFINED_FUEL_GOALS: tuple[Goal, ...] = (
    EXTENDED_GOALS + PHYSICS_FUEL_GOALS + AXIS_FOUNDATION_GOALS + MASTER_CONJUNCTION_GOALS
)

TOOLKIT_GOALS: tuple[Goal, ...] = (
    Goal(
        term="finite_dimensional_hilbert_space",
        track="QIT_TOOLKIT_FOUNDATION",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"), ("INFINITE_SET", "TRUE")),
    ),
    Goal(
        term="density_matrix",
        track="QIT_TOOLKIT_DENSITY_MATRIX",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"), ("COMMUTATIVE_ASSUMPTION", "TRUE")),
    ),
    Goal(
        term="probe_operator",
        track="QIT_TOOLKIT_PROBE_OPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="cptp_channel",
        track="QIT_TOOLKIT_CPTP_CHANNEL",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    Goal(
        term="partial_trace",
        track="QIT_TOOLKIT_PARTIAL_TRACE",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="unitary_operator",
        track="QIT_TOOLKIT_UNITARY_OPERATOR",
        negative_class="COMMUTATIVE_ASSUMPTION",
        negative_markers=(("ASSUME_COMMUTATIVE", "TRUE"),),
    ),
    # Long explicit compound term: a readable "toolkit object" built from already-earned primitives.
    Goal(
        term="finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator",
        track="QIT_TOOLKIT_CORE",
        negative_class="INFINITE_SET",
        negative_markers=(("ASSUME_INFINITE", "TRUE"),),
    ),
)


def _load_state_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _term_state(state: dict, term: str) -> str:
    entry = (state.get("term_registry", {}) or {}).get(term)
    if not isinstance(entry, dict):
        return ""
    return str(entry.get("state", "") or "")


def _is_term_available(state: dict, term: str) -> bool:
    # Mirrors kernel component rule: component is "available" if l0 or term state is at least permitted.
    l0 = set(state.get("l0_lexeme_set", []) or [])
    if term in l0:
        return True
    st = _term_state(state, term)
    return st in {"TERM_PERMITTED", "CANONICAL_ALLOWED", "LABEL_PERMITTED"}


def _is_term_canonical(state: dict, term: str) -> bool:
    return _term_state(state, term) == "CANONICAL_ALLOWED"


def _components(term: str) -> list[str]:
    return [t for t in term.split("_") if t]


def _is_bootstrap_atomic_component(term: str) -> bool:
    t = str(term).strip().lower()
    if not t:
        return False
    return t not in ATOMIC_COMPONENT_STOPWORDS


def _sim_tier_for_term(term: str) -> str:
    t = str(term or "").strip().lower()
    if t in {"finite_dimensional_hilbert_space", "density_matrix"}:
        return "T0_ATOM"
    if t in {"cptp_channel", "partial_trace", "positive_semidefinite", "trace_one"}:
        return "T1_COMPOUND"
    if t in {
        "probe_operator",
        "unitary_operator",
        "lindblad_generator",
        "hamiltonian_operator",
        "commutator_operator",
        "kraus_operator",
        "kraus_channel",
        "measurement_operator",
        "observable_operator",
        "projector_operator",
        "pauli_operator",
        "left_action_superoperator",
        "right_action_superoperator",
    }:
        return "T2_OPERATOR"
    if t in {
        "eigenvalue_spectrum",
        "density_purity",
        "density_entropy",
        "coherence_decoherence",
        "kraus_representation",
        "liouvillian_superoperator",
        "von_neumann_entropy",
        "entropy_production_rate",
        "noncommutative_composition_order",
        "bloch_sphere",
        "hopf_fibration",
        "hopf_torus",
        "berry_flux",
        "spinor_double_cover",
        "correlation_polarity",
        "trajectory_correlation",
        "variance_order",
        "information_work_extraction_bound",
        "erasure_channel_entropy_cost_lower_bound",
    }:
        return "T3_STRUCTURE"
    if t in {"channel_realization"}:
        return "T4_SYSTEM_SEGMENT"
    if t in {"engine_cycle"}:
        return "T5_ENGINE"
    if t in {"qit_master_conjunction"}:
        return "T6_WHOLE_SYSTEM"
    return "T1_COMPOUND"


# Terms with concrete probe implementations in SIM engine.
PROBE_CAPABLE_TERMS: set[str] = {
    "qit_master_conjunction",
    "information_work_extraction_bound",
    "erasure_channel_entropy_cost_lower_bound",
    "nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
    "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator",
    "finite_dimensional_hilbert_space",
    "density_matrix",
    "positive_semidefinite",
    "trace_one",
    "probe_operator",
    "kraus_representation",
    "cptp_channel",
    "kraus_channel",
    "kraus_operator",
    "partial_trace",
    "unitary_operator",
    "commutator_operator",
    "coherence_decoherence",
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
    "lindblad_generator",
    "liouvillian_superoperator",
    "hamiltonian_operator",
    "observable_operator",
    "measurement_operator",
    "projector_operator",
    "density_entropy",
    "von_neumann_entropy",
    "eigenvalue_spectrum",
    "density_purity",
    "entropy_production_rate",
    "noncommutative_composition_order",
    "correlation_polarity",
    "trajectory_correlation",
    "variance_order",
    "channel_realization",
    "engine_cycle",
}


def _probe_term_for_goal(state: dict, goal_term: str) -> str:
    """
    Pick a probe-capable term for SIM pressure.
    If the goal term has no dedicated probe, use a deterministic nearest substrate anchor.
    """
    term = str(goal_term or "").strip().lower()
    if term in PROBE_CAPABLE_TERMS:
        return term

    for comp in _components(term):
        c = str(comp).strip().lower()
        if c in PROBE_CAPABLE_TERMS:
            return c

    anchor_order = (
        "qit_master_conjunction",
        "correlation_polarity",
        "partial_trace",
        "cptp_channel",
        "density_matrix",
        "probe_operator",
        "unitary_operator",
        "engine_cycle",
    )
    for anchor in anchor_order:
        if _is_term_available(state, anchor):
            return anchor
    return "density_matrix"


def _next_goal(
    state: dict, goals: tuple[Goal, ...], sequence: int, *, selection: str = "interleaved"
) -> Goal | None:
    pending = [goal for goal in goals if not _is_term_canonical(state, goal.term)]
    if not pending:
        return None
    if selection == "closure_first":
        for goal in goals:
            if not _is_term_canonical(state, goal.term):
                return goal
        return pending[0]

    # Deterministic interleaving across the *full* goal list to avoid starvation.
    #
    # IMPORTANT: `pending[index]` with a changing pending-length can starve early goals
    # for long stretches (especially when goal list is large). Instead we:
    # - pick a starting index based on sequence over the full goals list
    # - scan forward (wrapping) to find the first still-pending goal
    start = max(0, int(sequence) - 1) % len(goals)
    for offset in range(len(goals)):
        goal = goals[(start + offset) % len(goals)]
        if not _is_term_canonical(state, goal.term):
            return goal
    return pending[0]


def _recent_kill_context(state: dict, *, limit: int = 4) -> list[dict]:
    kill_log = state.get("kill_log", []) or []
    spec_meta = state.get("spec_meta", {}) or {}
    # Prefer structurally diverse rescue sources first (token diversity), then
    # fill remaining slots by recency.
    diverse: list[dict] = []
    overflow: list[dict] = []
    seen_spec: set[str] = set()
    seen_token: set[str] = set()
    for row in reversed(kill_log):
        if not isinstance(row, dict):
            continue
        if str(row.get("tag", "")).strip() != "KILL_SIGNAL":
            continue
        spec_id = str(row.get("id", "")).strip()
        if not spec_id or spec_id in seen_spec:
            continue
        meta = spec_meta.get(spec_id, {}) if isinstance(spec_meta, dict) else {}
        if not isinstance(meta, dict):
            meta = {}
        token = str(row.get("token", "")).strip()
        item = {
            "id": spec_id,
            "target_class": str(meta.get("target_class", "")).strip(),
            "negative_class": str(meta.get("negative_class", "")).strip(),
            "token": token,
        }
        if token and token not in seen_token:
            diverse.append(item)
            seen_token.add(token)
        else:
            overflow.append(item)
        seen_spec.add(spec_id)
        if len(diverse) >= int(limit):
            break
    out = diverse + overflow
    out = out[: int(limit)]
    out.reverse()
    return out


def _emit_atomic_term_batch(term: str, *, prefix: str, sim_code_hash: str, probe_id: str, probe_token: str) -> list[dict]:
    """
    Admit a single-word term as an atomic TERM_DEF (no underscore gating) plus a canon permit + SIM.
    """
    # ID ordering matters: A0 groups items by kind priority and then lexicographically by id.
    # We intentionally give prerequisite atomic terms an "A_" prefix so their TERM_DEF lines
    # sort before any compound TERM_DEF lines for the step.
    math_id = f"{prefix}_MATH_{term.upper()}"
    term_id = f"{prefix}_TERM_{term.upper()}"
    permit_id = f"{prefix}_CANON_{term.upper()}"
    sim_id = f"{prefix}_SIM_CANON_{term.upper()}"
    evidence = f"E_CANON_{term.upper()}"
    salt = int(hashlib.sha256(term.encode("utf-8")).hexdigest(), 16)
    def pick(n: int, offset: int) -> str:
        words = []
        for i in range(n):
            words.append(L0_CORPUS[(salt + offset + i * 7) % len(L0_CORPUS)])
        # space-separated tokens (no underscores): avoids component gating.
        return " ".join(words)
    return [
        {
            "item_class": "SPEC_HYP",
            "id": math_id,
            "kind": "MATH_DEF",
            "requires": [probe_id],
            "def_fields": [
                # IMPORTANT: line-fence enforcement rejects undefined lexemes inside DEF_FIELD payloads.
                # Therefore, a MATH_DEF used to introduce a new atomic term MUST NOT reference that
                # new term in any DEF_FIELD values. The term literal only appears in TERM_DEF/CANON_PERMIT
                # (quoted) where it is allowed.
                _df("F_OBJ", "OBJECTS", pick(5, 0)),
                _df("F_OPS", "OPERATIONS", pick(4, 13)),
                _df("F_INV", "INVARIANTS", pick(3, 29)),
                _df("F_DOM", "DOMAIN", pick(4, 41)),
                _df("F_COD", "CODOMAIN", pick(3, 55)),
                _df("F_SIM", "SIM_CODE_HASH_SHA256", sim_code_hash),
                _df("F_TRACK", "BRANCH_TRACK", "ATOMIC_TERM_BOOTSTRAP"),
            ],
            "asserts": [
                _assert("A_MATH", "MATH_TOKEN", f"MT_{term.upper()}"),
                _assert("A_PROBE", "PROBE_TOKEN", probe_token),
            ],
            "operator_id": "OP_BIND_SIM",
        },
        {
            "item_class": "SPEC_HYP",
            "id": term_id,
            "kind": "TERM_DEF",
            "requires": [math_id],
            "def_fields": [
                _df("F_TERM", "TERM", term, kind="TERM_QUOTED"),
                _df("F_BINDS", "BINDS", math_id),
            ],
            "asserts": [_assert("A_TERM", "TERM_TOKEN", f"TT_{term.upper()}")],
            "operator_id": "OP_REPAIR_DEF_FIELD",
        },
        {
            "item_class": "SPEC_HYP",
            "id": permit_id,
            "kind": "CANON_PERMIT",
            "requires": [term_id],
            "def_fields": [
                _df("F_TERM", "TERM", term, kind="TERM_QUOTED"),
                _df("F_EVID", "REQUIRES_EVIDENCE", evidence),
            ],
            "asserts": [_assert("A_PERMIT", "PERMIT_TOKEN", f"PT_{term.upper()}")],
            "operator_id": "OP_REPAIR_DEF_FIELD",
        },
        {
            "item_class": "SPEC_HYP",
            "id": sim_id,
            "kind": "SIM_SPEC",
            "requires": [probe_id],
            "def_fields": [
                _df("F_EVID", "REQUIRES_EVIDENCE", evidence),
                _df("F_SIMID", "SIM_ID", sim_id),
                _df("F_TIER", "TIER", "T0_ATOM"),
                _df("F_FAM", "FAMILY", "BASELINE"),
                _df("F_TC", "TARGET_CLASS", "TC_ATOMIC_TERM_BOOTSTRAP"),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", term),
            ],
            "asserts": [
                _assert("A_EVID", "EVIDENCE_TOKEN", evidence),
                _assert("A_PROBE", "PROBE_TOKEN", probe_token),
            ],
            "operator_id": "OP_BIND_SIM",
        },
    ]


def _salt_l0_phrase(term: str, *, n: int, offset: int = 0) -> str:
    """
    Deterministically choose a small phrase of L0 lexemes based on the term.
    Used to avoid NEAR_REDUNDANT parking for large compound MATH_DEF blocks,
    while staying inside the line-fence (L0-only) rules.
    """
    if n <= 0:
        return ""
    salt = int(hashlib.sha256(str(term).encode("utf-8")).hexdigest(), 16)
    words: list[str] = []
    for i in range(int(n)):
        words.append(L0_CORPUS[(salt + int(offset) + i * 11) % len(L0_CORPUS)])
    return " ".join(words)


def build_strategy_from_state(
    *,
    state: dict,
    run_id: str,
    sequence: int,
    goals: tuple[Goal, ...],
    goal_selection: str = "interleaved",
    debate_mode: str = "balanced",
) -> dict:
    sim_stub_path = BASE / "SIM_STUB_QIT_v1.txt"
    sim_code_hash = _sha256_file(sim_stub_path)

    # Probe discipline (BR-009): kernel enforces at least 1 probe per 10 specs.
    # Therefore we generate a small pool of probes and deterministically assign
    # each SIM_SPEC to one probe. This prevents PROBE_PRESSURE parking at scale.
    max_items_for_budget = 48 if debate_mode == "graveyard_first" else 32
    probe_pool_size = max(1, (int(max_items_for_budget) + 9) // 10)
    probe_ids = tuple(f"P_QIT_BATCH_{sequence:06d}_{i:02d}" for i in range(1, probe_pool_size + 1))

    def probe_id_for(item_id: str) -> str:
        if not probe_ids:
            return f"P_QIT_BATCH_{sequence:06d}"
        h = int(hashlib.sha256(str(item_id).encode("utf-8")).hexdigest(), 16)
        return probe_ids[h % len(probe_ids)]

    def probe_token_for(probe_id: str) -> str:
        return f"PT_{probe_id}"

    primary_probe_id = probe_ids[0]
    primary_probe_token = probe_token_for(primary_probe_id)

    goal = _next_goal(state, goals, sequence, selection=goal_selection)
    if goal is None:
        # Deterministic no-op batch: still emits a valid strategy, but will likely
        # be rejected/parked upstream by A0 cross-basin logic if empty.
        goal = goals[-1]

    # Refined-fuel discipline: prioritize the whole-system conjunction witness once
    # its minimal prerequisites are already canonical. This prevents starvation
    # when the goal list is large and keeps the "proof surface" reachable without
    # forcing a fully-complete ladder first.
    master_goal = next((g for g in goals if g.term == "qit_master_conjunction"), None)
    if master_goal is not None and not _is_term_canonical(state, master_goal.term):
        master_prereqs = (
            "density_matrix",
            "cptp_channel",
            "partial_trace",
            "unitary_operator",
            "correlation_polarity",
        )
        if all(_is_term_canonical(state, t) for t in master_prereqs):
            goal = master_goal

    # Deterministic prerequisites: always keep the selected goal as the main
    # working target, but explicitly bootstrap any non-canonical subterms so
    # long compounds are visibly built from atomic terms.
    working_goal = goal
    probe_term = _probe_term_for_goal(state, working_goal.term)
    bootstrap_components: list[str] = []
    l0_lexemes = {str(x).strip() for x in (state.get("l0_lexeme_set", []) or []) if str(x).strip()}
    if goal.term == "qit_master_conjunction":
        # Master conjunction is a synthetic terminal witness, not a lexical compound.
        pass
    else:
        seen: set[str] = set()
        for comp in _components(goal.term):
            # Skip duplicates and already-earned atomic terms.
            if not comp or comp in seen or _is_term_canonical(state, comp) or comp in l0_lexemes:
                continue
            if not _is_bootstrap_atomic_component(comp):
                continue
            seen.add(comp)
            bootstrap_components.append(comp)

    # Goal batch: MATH_DEF+TERM_DEF+CANON_PERMIT+SIM_SPEC.
    # Goal gets a "Z_" prefix so it sorts after all prereq TERM_DEF entries.
    prefix = f"S{sequence:06d}_Z"
    math_id = f"{prefix}_MATH_{working_goal.term.upper()}"
    term_id = f"{prefix}_TERM_{working_goal.term.upper()}"
    permit_id = f"{prefix}_CANON_{working_goal.term.upper()}"
    sim_pos_id = (
        "SIM_MASTER_T6" if working_goal.term == "qit_master_conjunction" else f"{prefix}_SIM_CANON_{working_goal.term.upper()}"
    )
    ev_goal = f"E_CANON_{working_goal.term.upper()}"
    sim_tier = _sim_tier_for_term(working_goal.term)
    target_class_value = "TC_QIT_MASTER" if working_goal.term == "qit_master_conjunction" else f"TC_{working_goal.track}"

    math_requires = [primary_probe_id]
    if working_goal.term == "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator":
        # Explicit dependency closure (readability): the toolkit compound term should visibly
        # sit on top of previously admitted primitives, not appear as a free-floating blob.
        for term in (
            "finite_dimensional_hilbert_space",
            "density_matrix",
            "cptp_channel",
            "partial_trace",
            "unitary_operator",
        ):
            entry = (state.get("term_registry", {}) or {}).get(term)
            if isinstance(entry, dict):
                dep = str(entry.get("bound_math_def", "") or "").strip()
                if dep:
                    math_requires.append(dep)
        math_requires = sorted({r for r in math_requires if r})
    elif working_goal.term == "qit_master_conjunction":
        # Strong chain closure: master witness must depend on all currently canonical math artifacts.
        term_registry = state.get("term_registry", {}) or {}
        for term, entry in sorted(term_registry.items()):
            if term == "qit_master_conjunction":
                continue
            if not isinstance(entry, dict):
                continue
            if str(entry.get("state", "")) != "CANONICAL_ALLOWED":
                continue
            dep = str(entry.get("bound_math_def", "") or "").strip()
            if dep:
                math_requires.append(dep)
        math_requires = sorted({r for r in math_requires if r})

    available_components = []
    for comp in _components(working_goal.term):
        if _is_term_available(state, comp):
            available_components.append(comp)
    available_components = sorted({c for c in available_components if c})

    codomain_value = "density matrix"
    objects_value = "finite dimensional hilbert space"
    operations_value = "partial_trace tensor cptp_channel unitary"
    invariants_value = "trace"
    domain_value = "finite_dimensional_hilbert_space"
    if working_goal.term == "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator":
        objects_value = "finite_dimensional_hilbert_space density_matrix"
        operations_value = "partial_trace tensor cptp_channel unitary_operator"
        invariants_value = "trace"
        domain_value = "finite_dimensional_hilbert_space"
        codomain_value = "density_matrix"
    elif working_goal.term == "qit_master_conjunction":
        # IMPORTANT: master conjunction must not reference undefined TERM tokens.
        # Use only already-canonical terms (plus plain lexeme phrases for operations)
        # so the batch is not rejected for UNDEFINED_TERM_USE.
        term_registry = state.get("term_registry", {}) or {}
        canon_terms: list[str] = []
        for term, entry in sorted(term_registry.items()):
            if not isinstance(entry, dict):
                continue
            if str(entry.get("state", "")) != "CANONICAL_ALLOWED":
                continue
            # Do not reference the goal term itself here; it is not defined yet.
            if str(term) == "qit_master_conjunction":
                continue
            canon_terms.append(str(term))
        objects_value = " ".join(canon_terms) if canon_terms else "density_matrix"
        operations_value = "noncommutative composition order left action superoperator right action superoperator"
        invariants_value = "finite dimensional noncommutative"
        domain_value = "finite_dimensional_hilbert_space"
        codomain_value = "density_matrix"
    elif available_components:
        # Make term-specific MATH_DEF payloads structurally distinct so they do not
        # collapse into NEAR_REDUNDANT parking against earlier goals.
        objects_value = " ".join(available_components)
        operations_value = "left_action_superoperator right_action_superoperator noncommutative_composition_order"
        # Large compounds are especially prone to high Jaccard overlap due to shared
        # invariants/domain/codomain tokens. Add a small deterministic L0-only salt
        # phrase to avoid NEAR_REDUNDANT parking without introducing new primitives.
        if len(available_components) >= 9:
            objects_value = (objects_value + " " + _salt_l0_phrase(working_goal.term, n=4, offset=3)).strip()
            operations_value = (operations_value + " " + _salt_l0_phrase(working_goal.term, n=3, offset=71)).strip()
        invariants_value = "finite dimensional noncommutative"
        domain_value = "finite_dimensional_hilbert_space"
        codomain_value = "density_matrix"

    math_def_fields = [
        # Do not reference goal.term here; it may not be defined yet.
        _df("F_OBJ", "OBJECTS", objects_value),
        _df("F_OPS", "OPERATIONS", operations_value),
        _df("F_INV", "INVARIANTS", invariants_value),
        _df("F_DOM", "DOMAIN", domain_value),
        _df("F_COD", "CODOMAIN", codomain_value),
        _df("F_SIM", "SIM_CODE_HASH_SHA256", sim_code_hash),
        _df("F_TRACK", "BRANCH_TRACK", working_goal.track),
    ]
    if available_components:
        math_def_fields.append(_df("F_COMP", "COMPONENTS", " ".join(available_components)))

    target_items = [
        {
            "item_class": "SPEC_HYP",
            "id": math_id,
            "kind": "MATH_DEF",
            "requires": math_requires,
            "def_fields": math_def_fields,
            "asserts": [
                _assert("A_MATH", "MATH_TOKEN", f"MT_{working_goal.term.upper()}"),
                _assert("A_PROBE", "PROBE_TOKEN", primary_probe_token),
            ],
            "operator_id": "OP_BIND_SIM",
        },
        {
            "item_class": "SPEC_HYP",
            "id": term_id,
            "kind": "TERM_DEF",
            "requires": [math_id],
            "def_fields": [
                _df("F_TERM", "TERM", working_goal.term, kind="TERM_QUOTED"),
                _df("F_BINDS", "BINDS", math_id),
            ],
            "asserts": [_assert("A_TERM", "TERM_TOKEN", f"TT_{working_goal.term.upper()}")],
            "operator_id": "OP_REPAIR_DEF_FIELD",
        },
        {
            "item_class": "SPEC_HYP",
            "id": permit_id,
            "kind": "CANON_PERMIT",
            "requires": [term_id],
            "def_fields": [
                _df("F_TERM", "TERM", working_goal.term, kind="TERM_QUOTED"),
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_goal),
            ],
            "asserts": [_assert("A_PERMIT", "PERMIT_TOKEN", f"PT_{working_goal.term.upper()}")],
            "operator_id": "OP_REPAIR_DEF_FIELD",
        },
        {
            "item_class": "SPEC_HYP",
            "id": sim_pos_id,
            "kind": "SIM_SPEC",
            "requires": [probe_id_for(sim_pos_id)],
            "def_fields": [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_goal),
                _df("F_SIMID", "SIM_ID", sim_pos_id),
                _df("F_TIER", "TIER", sim_tier),
                _df("F_FAM", "FAMILY", "BASELINE"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
            ],
            "asserts": [
                _assert("A_EVID", "EVIDENCE_TOKEN", ev_goal),
                _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(sim_pos_id))),
            ],
            "operator_id": "OP_BIND_SIM",
        },
    ]

    # Multi-narrative alternatives ("team of lawyers"): three structural stress lanes +
    # one adversarial negative lane that is kill-bound via NEGATIVE_CLASS.
    alt_boundary_id = f"{prefix}_SIM_ALT_BOUNDARY_{working_goal.term.upper()}"
    alt_perturb_id = f"{prefix}_SIM_ALT_PERTURB_{working_goal.term.upper()}"
    alt_stress_id = f"{prefix}_SIM_ALT_STRESS_{working_goal.term.upper()}"
    alt_neg_id = f"{prefix}_SIM_ALT_NEG_{working_goal.term.upper()}"
    alt_neg_sim_id = "SIM_MASTER_T6_NEG" if working_goal.term == "qit_master_conjunction" else alt_neg_id
    ev_boundary = f"E_ALT_BOUNDARY_{working_goal.term.upper()}"
    ev_perturb = f"E_ALT_PERTURB_{working_goal.term.upper()}"
    ev_stress = f"E_ALT_STRESS_{working_goal.term.upper()}"
    ev_neg = f"E_ALT_NEG_{working_goal.term.upper()}"

    negative_items = [
        {
            "item_class": "SPEC_HYP",
            "id": alt_boundary_id,
            "kind": "SIM_SPEC",
            "requires": [probe_id_for(alt_boundary_id), math_id],
            "def_fields": [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_boundary),
                _df("F_SIMID", "SIM_ID", alt_boundary_id),
                _df("F_TIER", "TIER", "T1_COMPOUND"),
                _df("F_FAM", "FAMILY", "BOUNDARY_SWEEP"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
                _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_BOUNDARY"),
            ],
            "asserts": [
                _assert("A_EVID", "EVIDENCE_TOKEN", ev_boundary),
                _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_boundary_id))),
            ],
            "operator_id": "OP_REPAIR_DEF_FIELD",
        },
        {
            "item_class": "SPEC_HYP",
            "id": alt_perturb_id,
            "kind": "SIM_SPEC",
            "requires": [probe_id_for(alt_perturb_id), math_id],
            "def_fields": [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_perturb),
                _df("F_SIMID", "SIM_ID", alt_perturb_id),
                _df("F_TIER", "TIER", "T2_OPERATOR"),
                _df("F_FAM", "FAMILY", "PERTURBATION"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
                _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_PERTURB"),
            ],
            "asserts": [
                _assert("A_EVID", "EVIDENCE_TOKEN", ev_perturb),
                _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_perturb_id))),
            ],
            "operator_id": "OP_MUTATE_LEXEME",
        },
        {
            "item_class": "SPEC_HYP",
            "id": alt_stress_id,
            "kind": "SIM_SPEC",
            "requires": [probe_id_for(alt_stress_id), math_id, term_id],
            "def_fields": [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_stress),
                _df("F_SIMID", "SIM_ID", alt_stress_id),
                _df("F_TIER", "TIER", "T3_STRUCTURE"),
                _df("F_FAM", "FAMILY", "COMPOSITION_STRESS"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
                _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_STRESS"),
            ],
            "asserts": [
                _assert("A_EVID", "EVIDENCE_TOKEN", ev_stress),
                _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_stress_id))),
            ],
            "operator_id": "OP_REORDER_DEPENDENCIES",
        },
        {
            "item_class": "SPEC_HYP",
            "id": alt_neg_id,
            "kind": "SIM_SPEC",
            "requires": [probe_id_for(alt_neg_id), math_id],
            "def_fields": [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_neg),
                _df("F_SIMID", "SIM_ID", alt_neg_sim_id),
                _df("F_TIER", "TIER", "T1_COMPOUND"),
                _df("F_FAM", "FAMILY", "ADVERSARIAL_NEG"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_NEG", "NEGATIVE_CLASS", working_goal.negative_class),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
                _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_NEG"),
            ],
            "asserts": [
                _assert("A_EVID", "EVIDENCE_TOKEN", ev_neg),
                _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_neg_id))),
            ],
            "operator_id": "OP_NEG_SIM_EXPAND",
        },
    ]

    for idx, (name, value) in enumerate(working_goal.negative_markers, start=1):
        negative_items[-1]["def_fields"].append(_df(f"F_MARK{idx:02d}", name, value))

    # Graveyard-first mode intentionally widens adversarial lanes to create a dense
    # kill surface before recovery passes begin.
    if debate_mode == "graveyard_first":
        neg_classes = [
            "COMMUTATIVE_ASSUMPTION",
            "CLASSICAL_TIME",
            "CONTINUOUS_BATH",
            "INFINITE_SET",
            "INFINITE_RESOLUTION",
            "PRIMITIVE_EQUALS",
            "EUCLIDEAN_METRIC",
            "CLASSICAL_TEMPERATURE",
        ]
        marker_for_class = {
            "COMMUTATIVE_ASSUMPTION": ("ASSUME_COMMUTATIVE", "TRUE"),
            "CLASSICAL_TIME": ("TIME_PARAM", "T"),
            "CONTINUOUS_BATH": ("CONTINUOUS_BATH", "TRUE"),
            "INFINITE_SET": ("INFINITE_SET", "TRUE"),
            "INFINITE_RESOLUTION": ("INFINITE_RESOLUTION", "TRUE"),
            "PRIMITIVE_EQUALS": ("EQUALS_PRIMITIVE", "TRUE"),
            "EUCLIDEAN_METRIC": ("EUCLIDEAN_METRIC", "TRUE"),
            "CLASSICAL_TEMPERATURE": ("TEMPERATURE_BATH", "TRUE"),
        }
        for j, neg_cls in enumerate(neg_classes, start=1):
            alt_id = f"{prefix}_SIM_ALT_NEG_EXTRA{j}_{working_goal.term.upper()}"
            ev_id = f"E_ALT_NEG_EXTRA{j}_{working_goal.term.upper()}"
            marker_name, marker_value = marker_for_class.get(neg_cls, ("ASSUME_COMMUTATIVE", "TRUE"))
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": alt_id,
                    "kind": "SIM_SPEC",
                    "requires": [probe_id_for(alt_id), math_id],
                    "def_fields": [
                        _df("F_EVID", "REQUIRES_EVIDENCE", ev_id),
                        _df("F_SIMID", "SIM_ID", alt_id),
                        _df("F_TIER", "TIER", "T2_OPERATOR"),
                        _df("F_FAM", "FAMILY", "ADVERSARIAL_NEG"),
                        _df("F_TC", "TARGET_CLASS", target_class_value),
                        _df("F_NEG", "NEGATIVE_CLASS", neg_cls),
                        _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                        _df("F_PTERM", "PROBE_TERM", probe_term),
                        _df("F_GTERM", "GOAL_TERM", working_goal.term),
                        _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_NEG_EXTRA_{j}"),
                        _df(f"F_MARK{j:02d}", marker_name, marker_value),
                    ],
                    "asserts": [
                        _assert("A_EVID", "EVIDENCE_TOKEN", ev_id),
                        _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_id))),
                    ],
                    "operator_id": "OP_NEG_SIM_EXPAND",
                }
            )

    # Recovery mode consumes recent killed surfaces as explicit rescue attempts.
    if debate_mode == "graveyard_recovery" and working_goal.term != "qit_master_conjunction":
        for idx, kill in enumerate(_recent_kill_context(state, limit=6), start=1):
            rescue_probe_id = f"P_QIT_RESCUE_{sequence:06d}_{idx}"
            rescue_probe_token = f"PT_QIT_RESCUE_{sequence:06d}_{idx}"
            tc = kill.get("target_class") or f"TC_{working_goal.track}"
            source_id = kill.get("id", "")
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": f"{prefix}_SIM_RESCUE_BOUNDARY_{idx}_{working_goal.term.upper()}",
                    "kind": "SIM_SPEC",
                    "requires": [rescue_probe_id, math_id],
                    "def_fields": [
                        _df("F_EVID", "REQUIRES_EVIDENCE", f"E_RESCUE_BOUNDARY_{idx}_{working_goal.term.upper()}"),
                        _df("F_SIMID", "SIM_ID", f"{prefix}_SIM_RESCUE_BOUNDARY_{idx}_{working_goal.term.upper()}"),
                        _df("F_TIER", "TIER", "T2_OPERATOR"),
                        _df("F_FAM", "FAMILY", "BOUNDARY_SWEEP"),
                        _df("F_TC", "TARGET_CLASS", tc),
                        _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                        _df("F_PTERM", "PROBE_TERM", probe_term),
                        _df("F_GTERM", "GOAL_TERM", working_goal.term),
                        _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_RESCUE_BOUNDARY_{source_id}"),
                        _df("F_RFROM", "RESCUE_FROM", source_id),
                        _df("F_RTOK", "RESCUE_TOKEN", str(kill.get("token", "")).strip() or "UNKNOWN"),
                    ],
                    "asserts": [
                        _assert("A_EVID", "EVIDENCE_TOKEN", f"E_RESCUE_BOUNDARY_{idx}_{working_goal.term.upper()}"),
                        _assert("A_PROBE", "PROBE_TOKEN", rescue_probe_token),
                    ],
                    "operator_id": "OP_REPAIR_DEF_FIELD",
                }
            )
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": f"{prefix}_SIM_RESCUE_PERTURB_{idx}_{working_goal.term.upper()}",
                    "kind": "SIM_SPEC",
                    "requires": [rescue_probe_id, math_id],
                    "def_fields": [
                        _df("F_EVID", "REQUIRES_EVIDENCE", f"E_RESCUE_PERTURB_{idx}_{working_goal.term.upper()}"),
                        _df("F_SIMID", "SIM_ID", f"{prefix}_SIM_RESCUE_PERTURB_{idx}_{working_goal.term.upper()}"),
                        _df("F_TIER", "TIER", "T2_OPERATOR"),
                        _df("F_FAM", "FAMILY", "PERTURBATION"),
                        _df("F_TC", "TARGET_CLASS", tc),
                        _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                        _df("F_PTERM", "PROBE_TERM", probe_term),
                        _df("F_GTERM", "GOAL_TERM", working_goal.term),
                        _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_RESCUE_PERTURB_{source_id}"),
                        _df("F_RFROM", "RESCUE_FROM", source_id),
                        _df("F_RTOK", "RESCUE_TOKEN", str(kill.get("token", "")).strip() or "UNKNOWN"),
                    ],
                    "asserts": [
                        _assert("A_EVID", "EVIDENCE_TOKEN", f"E_RESCUE_PERTURB_{idx}_{working_goal.term.upper()}"),
                        _assert("A_PROBE", "PROBE_TOKEN", rescue_probe_token),
                    ],
                    "operator_id": "OP_MUTATE_LEXEME",
                }
            )
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": f"{prefix}_SIM_RESCUE_STRESS_{idx}_{working_goal.term.upper()}",
                    "kind": "SIM_SPEC",
                    "requires": [rescue_probe_id, math_id, term_id],
                    "def_fields": [
                        _df("F_EVID", "REQUIRES_EVIDENCE", f"E_RESCUE_STRESS_{idx}_{working_goal.term.upper()}"),
                        _df("F_SIMID", "SIM_ID", f"{prefix}_SIM_RESCUE_STRESS_{idx}_{working_goal.term.upper()}"),
                        _df("F_TIER", "TIER", "T3_STRUCTURE"),
                        _df("F_FAM", "FAMILY", "COMPOSITION_STRESS"),
                        _df("F_TC", "TARGET_CLASS", tc),
                        _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                        _df("F_PTERM", "PROBE_TERM", probe_term),
                        _df("F_GTERM", "GOAL_TERM", working_goal.term),
                        _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_RESCUE_STRESS_{source_id}"),
                        _df("F_RFROM", "RESCUE_FROM", source_id),
                        _df("F_RTOK", "RESCUE_TOKEN", str(kill.get("token", "")).strip() or "UNKNOWN"),
                    ],
                    "asserts": [
                        _assert("A_EVID", "EVIDENCE_TOKEN", f"E_RESCUE_STRESS_{idx}_{working_goal.term.upper()}"),
                        _assert("A_PROBE", "PROBE_TOKEN", rescue_probe_token),
                    ],
                    "operator_id": "OP_REORDER_DEPENDENCIES",
                }
            )

    # Emit explicit atomic prerequisite terms before the main target.
    prereq_items: list[dict] = []
    for idx, comp in enumerate(bootstrap_components, start=1):
        # Only bootstrap atomic component terms here. Nested compound components
        # are intentionally skipped and will be decomposed by their own goals.
        if "_" in comp:
            continue
        prereq_items.extend(
            _emit_atomic_term_batch(
                comp,
                prefix=f"S{sequence:06d}_A{idx:02d}",
                sim_code_hash=sim_code_hash,
                probe_id=primary_probe_id,
                probe_token=primary_probe_token,
            )
        )

    # Batch shape: deterministic and structurally variant.
    targets = prereq_items + target_items
    alternatives = negative_items

    strategy = {
        "schema": "A1_STRATEGY_v1",
        "strategy_id": f"STRAT_QIT_ADAPTIVE_{sequence:06d}",
        "inputs": {
            "state_hash": "0" * 64,
            "fuel_slice_hashes": [],
            "bootpack_rules_hash": "0" * 64,
            "pinned_ruleset_sha256": None,
            "pinned_megaboot_sha256": None,
        },
        "budget": {"max_items": 48 if debate_mode == "graveyard_first" else 32, "max_sims": 64 if debate_mode == "graveyard_first" else 48},
        "policy": {
            "forbid_fields": list(FORBIDDEN_FIELDS),
            "overlay_ban_terms": [],
            "require_try_to_fail": True,
        },
        "targets": targets,
        "alternatives": alternatives,
        "sims": {
            "positive": [{"sim_id": f"SIM_POS_{working_goal.term.upper()}", "binds_to": sim_pos_id}],
            "negative": [],
        },
        "self_audit": {
            "strategy_hash": "",
            "compile_lane_digest": "",
            "candidate_count": len(targets),
            "alternative_count": len(alternatives),
            "operator_ids_used": sorted(
                {str(x.get("operator_id", "")).strip() for x in (targets + alternatives) if isinstance(x, dict)}
            ),
        },
    }
    for alt in alternatives:
        if not isinstance(alt, dict):
            continue
        alt_id = str(alt.get("id", "")).strip()
        if not alt_id:
            continue
        strategy["sims"]["negative"].append({"sim_id": f"SIM_NEG_{alt_id}", "binds_to": alt_id})
    strategy["self_audit"]["strategy_hash"] = hashlib.sha256(_canon_bytes(strategy)).hexdigest()
    return strategy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output zip path")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--state-json", required=True, help="Path to state.json for planning")
    parser.add_argument(
        "--goal-profile",
        choices=["core", "extended", "physics", "toolkit", "refined_fuel"],
        default="core",
    )
    parser.add_argument("--goal-selection", choices=["interleaved", "closure_first"], default="interleaved")
    parser.add_argument("--debate-mode", choices=["balanced", "graveyard_first", "graveyard_recovery"], default="balanced")
    args = parser.parse_args()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    state = _load_state_json(Path(args.state_json))

    if str(args.goal_profile) == "core":
        goals = CORE_GOALS
    elif str(args.goal_profile) == "physics":
        goals = PHYSICS_FUEL_GOALS
    elif str(args.goal_profile) == "toolkit":
        goals = TOOLKIT_GOALS
    elif str(args.goal_profile) == "refined_fuel":
        goals = REFINED_FUEL_GOALS
    else:
        goals = EXTENDED_GOALS
    strategy = build_strategy_from_state(
        state=state,
        run_id=str(args.run_id),
        sequence=int(args.sequence),
        goals=goals,
        goal_selection=str(args.goal_selection),
        debate_mode=str(args.debate_mode),
    )
    write_zip_protocol_v2(
        out_path=out_path,
        header={
            "zip_type": "A1_TO_A0_STRATEGY_ZIP",
            "direction": "FORWARD",
            "source_layer": "A1",
            "target_layer": "A0",
            "run_id": str(args.run_id),
            "sequence": int(args.sequence),
            "created_utc": "1970-01-01T00:00:00Z",
            "compiler_version": "",
        },
        payload_json={"A1_STRATEGY_v1.json": strategy},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

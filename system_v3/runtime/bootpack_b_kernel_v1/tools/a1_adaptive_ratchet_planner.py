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

REPO_ROOT = BASE.parents[2]
FAMILY_SLICE_SCHEMA_PATH = (
    REPO_ROOT / "work" / "audit_tmp" / "spec_object_drafts" / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"
)

FORBIDDEN_FIELDS = ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"]
FULL_CYCLE_LANES: set[str] = {
    "STEELMAN",
    "ALT_FORMALISM",
    "BOUNDARY_REPAIR",
    "ADVERSARIAL_NEG",
    "RESCUER",
}
REQUIRED_STRESS_SIM_FAMILIES: tuple[str, ...] = (
    "BASELINE",
    "BOUNDARY_SWEEP",
    "PERTURBATION",
    "ADVERSARIAL_NEG",
    "COMPOSITION_STRESS",
)
LIVE_SIM_FAMILY_TIER_DEFAULTS: dict[str, str] = {
    "BASELINE": "T0_ATOM",
    "BOUNDARY_SWEEP": "T1_COMPOUND",
    "PERTURBATION": "T2_OPERATOR",
    "ADVERSARIAL_NEG": "T1_COMPOUND",
    "COMPOSITION_STRESS": "T3_STRUCTURE",
}
LIVE_STRATEGY_BUDGET_DEFAULTS: dict[str, dict[str, int]] = {
    "balanced": {"max_items": 32, "max_sims": 48},
    "graveyard_first": {"max_items": 48, "max_sims": 64},
    "graveyard_recovery": {"max_items": 32, "max_sims": 48},
}
NEGATIVE_MARKERS_BY_CLASS: dict[str, tuple[tuple[str, str], ...]] = {
    "COMMUTATIVE_ASSUMPTION": (("ASSUME_COMMUTATIVE", "TRUE"),),
    "CLASSICAL_TIME": (("TIME_PARAM", "T"),),
    "CONTINUOUS_BATH": (("CONTINUOUS_BATH", "TRUE"),),
    "INFINITE_SET": (("ASSUME_INFINITE", "TRUE"), ("INFINITE_SET", "TRUE")),
    "INFINITE_RESOLUTION": (("INFINITE_RESOLUTION", "TRUE"),),
    "PRIMITIVE_EQUALS": (("EQUALS_PRIMITIVE", "TRUE"),),
    "EUCLIDEAN_METRIC": (("EUCLIDEAN_METRIC", "TRUE"),),
    "CLASSICAL_TEMPERATURE": (("TEMPERATURE_BATH", "TRUE"),),
    "PRIMITIVE_PROBABILITY": (("PRIMITIVE_PROBABILITY", "TRUE"),),
}

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

ENTROPY_BRIDGE_GOALS: tuple[Goal, ...] = (
    Goal(
        term="correlation_polarity",
        track="ENTROPY_BRIDGE_CORRELATION_POLARITY",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="entropy_production_rate",
        track="ENTROPY_BRIDGE_ENTROPY_PRODUCTION_RATE",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="information_work_extraction_bound",
        track="ENTROPY_BRIDGE_INFORMATION_WORK_EXTRACTION_BOUND",
        negative_class="CLASSICAL_TEMPERATURE",
        negative_markers=(("TEMPERATURE_BATH", "TRUE"),),
    ),
    Goal(
        term="erasure_channel_entropy_cost_lower_bound",
        track="ENTROPY_BRIDGE_ERASURE_CHANNEL_ENTROPY_COST_LOWER_BOUND",
        negative_class="CLASSICAL_TEMPERATURE",
        negative_markers=(("TEMPERATURE_BATH", "TRUE"),),
    ),
)

ENTROPY_BOOKKEEPING_BRIDGE_GOALS: tuple[Goal, ...] = (
    Goal(
        term="density_entropy",
        track="ENTROPY_BOOKKEEPING_BRIDGE_DENSITY_ENTROPY",
        negative_class="CLASSICAL_TIME",
        negative_markers=(("TIME_PARAM", "T"),),
    ),
    Goal(
        term="information_work_extraction_bound",
        track="ENTROPY_BOOKKEEPING_BRIDGE_INFORMATION_WORK_EXTRACTION_BOUND",
        negative_class="CLASSICAL_TEMPERATURE",
        negative_markers=(("TEMPERATURE_BATH", "TRUE"),),
    ),
    Goal(
        term="erasure_channel_entropy_cost_lower_bound",
        track="ENTROPY_BOOKKEEPING_BRIDGE_ERASURE_CHANNEL_ENTROPY_COST_LOWER_BOUND",
        negative_class="CLASSICAL_TEMPERATURE",
        negative_markers=(("TEMPERATURE_BATH", "TRUE"),),
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

# Compatibility profile mode is now explicitly scaffold-only. These reduced term
# libraries are intentionally smaller than the historical hardcoded goal tables:
# they provide a minimal bridge for legacy callers while keeping real family
# meaning in bounded A2-derived family-slice inputs.
COMPATIBILITY_SCAFFOLD_TERMS_BY_PROFILE: dict[str, tuple[str, ...]] = {
    "core": (
        "finite_dimensional_hilbert_space",
        "density_matrix",
        "probe_operator",
        "cptp_channel",
        "partial_trace",
    ),
    "extended": (
        "finite_dimensional_hilbert_space",
        "density_matrix",
        "probe_operator",
        "cptp_channel",
        "partial_trace",
        "unitary_operator",
    ),
    "physics": (
        "finite_dimensional_hilbert_space",
        "density_matrix",
        "pauli_operator",
        "bloch_sphere",
    ),
    "toolkit": (
        "finite_dimensional_hilbert_space",
        "density_matrix",
        "probe_operator",
        "cptp_channel",
        "partial_trace",
        "unitary_operator",
    ),
    "refined_fuel": (
        "finite_dimensional_hilbert_space",
        "density_matrix",
        "probe_operator",
        "cptp_channel",
        "partial_trace",
        "unitary_operator",
    ),
    "entropy_bridge": (
        "correlation_polarity",
    ),
    "entropy_bookkeeping_bridge": (
        "correlation_polarity",
        "density_entropy",
    ),
}

_KNOWN_GOAL_BY_TERM: dict[str, Goal] = {}
for _goal_group in (
    CORE_GOALS,
    EXTENDED_GOALS,
    PHYSICS_FUEL_GOALS,
    AXIS_FOUNDATION_GOALS,
    MASTER_CONJUNCTION_GOALS,
    ENTROPY_BRIDGE_GOALS,
    ENTROPY_BOOKKEEPING_BRIDGE_GOALS,
    TOOLKIT_GOALS,
):
    for _goal in _goal_group:
        _KNOWN_GOAL_BY_TERM.setdefault(_goal.term, _goal)


MINIMAL_SUBSTRATE_MATH_SURFACES: dict[str, dict[str, str]] = {
    "finite_dimensional_hilbert_space": {
        "objects": "finite dimensional hilbert space",
        "operations": "tensor unitary partial trace cptp channel",
        "invariants": "finite dimensional",
        "domain": "finite dimensional hilbert space",
        "codomain": "operator space",
    },
    "density_matrix": {
        "objects": "finite dimensional hilbert space density matrix",
        "operations": "partial trace tensor cptp channel unitary",
        "invariants": "trace finite dimensional",
        "domain": "finite dimensional hilbert space",
        "codomain": "density matrix",
    },
    "probe_operator": {
        "objects": "density matrix operator",
        "operations": "partial trace tensor unitary",
        "invariants": "finite operator",
        "domain": "density matrix",
        "codomain": "operator space",
    },
    "cptp_channel": {
        "objects": "density matrix cptp channel",
        "operations": "partial trace tensor cptp channel",
        "invariants": "trace finite",
        "domain": "density matrix",
        "codomain": "density matrix",
    },
    "partial_trace": {
        "objects": "density matrix partial trace",
        "operations": "partial trace tensor",
        "invariants": "trace finite",
        "domain": "finite dimensional hilbert space",
        "codomain": "density matrix",
    },
    "unitary_operator": {
        "objects": "finite dimensional hilbert space unitary operator",
        "operations": "tensor unitary",
        "invariants": "finite operator",
        "domain": "finite dimensional hilbert space",
        "codomain": "operator space",
    },
    "commutator_operator": {
        "objects": "operator commutator",
        "operations": "commutator tensor",
        "invariants": "finite operator",
        "domain": "operator space",
        "codomain": "operator space",
    },
    "hamiltonian_operator": {
        "objects": "hamiltonian operator density matrix",
        "operations": "unitary commutator",
        "invariants": "finite operator",
        "domain": "density matrix",
        "codomain": "operator space",
    },
    "lindblad_generator": {
        "objects": "lindblad generator density matrix",
        "operations": "cptp channel partial trace",
        "invariants": "finite generator",
        "domain": "density matrix",
        "codomain": "density matrix",
    },
    "density_entropy": {
        "objects": "density matrix",
        "operations": "partial trace cptp channel unitary",
        "invariants": "trace finite dimensional",
        "domain": "density matrix",
        "codomain": "operator space",
    },
    "von_neumann_entropy": {
        "objects": "density matrix unitary operator",
        "operations": "partial trace unitary",
        "invariants": "trace finite dimensional",
        "domain": "density matrix",
        "codomain": "operator space",
    },
    "entropy_production_rate": {
        "objects": "density matrix cptp channel",
        "operations": "cptp channel partial trace",
        "invariants": "trace finite dimensional",
        "domain": "density matrix",
        "codomain": "density matrix",
    },
    "information_work_extraction_bound": {
        "objects": "density matrix cptp channel unitary operator",
        "operations": "cptp channel partial trace unitary",
        "invariants": "trace finite dimensional",
        "domain": "density matrix",
        "codomain": "density matrix",
    },
    "erasure_channel_entropy_cost_lower_bound": {
        "objects": "density matrix cptp channel partial trace",
        "operations": "cptp channel partial trace",
        "invariants": "trace finite dimensional",
        "domain": "density matrix",
        "codomain": "density matrix",
    },
    "correlation_polarity": {
        "objects": "finite dimensional hilbert space",
        "operations": "partial_trace tensor cptp_channel unitary",
        "invariants": "finite dimensional",
        "domain": "finite dimensional hilbert space",
        "codomain": "operator space",
    },
    "correlation_diversity_functional": {
        "objects": "density matrix finite dimensional hilbert space",
        "operations": "partial_trace tensor cptp_channel unitary",
        "invariants": "finite dimensional noncommutative",
        "domain": "density matrix",
        "codomain": "operator space",
    },
    "probe_induced_partition_boundary": {
        "objects": "density matrix finite dimensional hilbert space probe operator",
        "operations": "partial_trace tensor cptp_channel",
        "invariants": "finite dimensional noncommutative",
        "domain": "density matrix",
        "codomain": "operator space",
    },
    "channel_realization": {
        "objects": "density matrix cptp channel unitary operator",
        "operations": "cptp channel partial_trace unitary",
        "invariants": "trace finite dimensional",
        "domain": "density matrix",
        "codomain": "density matrix",
    },
    "channel_realization_correlation_polarity_orthogonality": {
        "objects": "channel_realization correlation_polarity",
        "operations": "cptp channel partial_trace unitary",
        "invariants": "finite operator",
        "domain": "density matrix",
        "codomain": "operator space",
    },
}


def _load_state_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        return {}
    heavy_path = path.with_name("state.heavy.json")
    if heavy_path.exists():
        try:
            heavy = json.loads(heavy_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            heavy = {}
        if isinstance(heavy, dict):
            data.update(heavy)
    return data


def _sha256_json(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


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


SIM_TIER_ORDER: tuple[str, ...] = (
    "T0_ATOM",
    "T1_COMPOUND",
    "T2_OPERATOR",
    "T3_STRUCTURE",
    "T4_SYSTEM_SEGMENT",
    "T5_ENGINE",
    "T6_WHOLE_SYSTEM",
)


def _sim_tier_rank(tier: str) -> int:
    token = str(tier).strip().upper()
    try:
        return SIM_TIER_ORDER.index(token)
    except ValueError:
        return -1


def _negative_markers_for_class(negative_class: str) -> tuple[tuple[str, str], ...]:
    return NEGATIVE_MARKERS_BY_CLASS.get(str(negative_class).strip().upper(), (("ASSUME_COMMUTATIVE", "TRUE"),))


def _ordered_unique_terms(*groups: list[str] | tuple[str, ...]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for raw in group:
            term = str(raw).strip()
            if not term or term in seen:
                continue
            seen.add(term)
            out.append(term)
    return out


def _track_token(value: str) -> str:
    token = "".join(ch if ch.isalnum() else "_" for ch in str(value).strip().upper())
    token = "_".join(part for part in token.split("_") if part)
    return token or "UNSPECIFIED"


def _family_slice_track(term: str, family_slice: dict) -> str:
    family_token = _track_token(
        str(family_slice.get("family_id", "") or family_slice.get("family_kind", "") or "FAMILY_SLICE")
    )
    return f"FAMILY_SLICE_{family_token}_{_track_token(term)}"


def _family_slice_target_class_prefix(family_slice: dict) -> str:
    family_token = _track_token(
        str(family_slice.get("family_id", "") or family_slice.get("family_kind", "") or "FAMILY_SLICE")
    )
    return f"TC_FAMILY_{family_token}"


def _family_slice_target_class(term: str, family_slice: dict) -> str:
    return f"{_family_slice_target_class_prefix(family_slice)}_{_track_token(term)}"


def _family_slice_negative_classes(family_slice: dict) -> tuple[str, ...]:
    emphasis = [
        str(x).strip().upper()
        for x in ((family_slice.get("negative_emphasis_classes", []) or []))
        if str(x).strip()
    ]
    required = [
        str(x).strip().upper()
        for x in ((family_slice.get("required_negative_classes", []) or []))
        if str(x).strip()
    ]
    return tuple(_ordered_unique_terms(emphasis, required))


def _family_slice_required_sim_families(family_slice: dict) -> tuple[str, ...]:
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    required = [
        str(x).strip().upper()
        for x in (sim_hooks.get("required_sim_families", []) or [])
        if str(x).strip()
    ]
    return tuple(_ordered_unique_terms(required))


def _family_slice_declared_probe_terms(family_slice: dict) -> tuple[str, ...]:
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    required = [
        str(x).strip().lower()
        for x in (sim_hooks.get("required_probe_terms", []) or [])
        if str(x).strip()
    ]
    return tuple(_ordered_unique_terms(required))


def _family_slice_math_surface_for_term(family_slice: dict, term: str) -> dict[str, str]:
    term_math_surfaces = family_slice.get("term_math_surfaces", {}) or {}
    surface = term_math_surfaces.get(str(term).strip(), {}) if isinstance(term_math_surfaces, dict) else {}
    if not isinstance(surface, dict):
        return {}
    required_keys = {"objects", "operations", "invariants", "domain", "codomain"}
    if not required_keys.issubset(set(surface.keys())):
        return {}
    out: dict[str, str] = {}
    for key in required_keys:
        value = str(surface.get(key, "")).strip()
        if not value:
            return {}
        out[key] = value
    return out


def _family_slice_term_sim_tier(family_slice: dict, term: str) -> str:
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    term_sim_tiers = sim_hooks.get("term_sim_tiers", {}) or {}
    if not isinstance(term_sim_tiers, dict):
        return ""
    return str(term_sim_tiers.get(str(term).strip(), "")).strip().upper()


def _family_slice_sim_family_tier(family_slice: dict, family: str, *, default: str = "") -> str:
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    sim_family_tiers = sim_hooks.get("sim_family_tiers", {}) or {}
    if isinstance(sim_family_tiers, dict):
        cleaned = str(sim_family_tiers.get(str(family).strip().upper(), "")).strip().upper()
        if cleaned:
            return cleaned
    return str(default).strip().upper()


def _family_slice_recovery_sim_families(family_slice: dict | None) -> tuple[str, ...]:
    default = ("BOUNDARY_SWEEP", "PERTURBATION", "COMPOSITION_STRESS")
    if not family_slice:
        return default
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    raw = sim_hooks.get("recovery_sim_families", []) or []
    out: list[str] = []
    seen: set[str] = set()
    allowed = {"BOUNDARY_SWEEP", "PERTURBATION", "COMPOSITION_STRESS"}
    required = set(_family_slice_required_sim_families(family_slice))
    for family in raw:
        token = str(family).strip().upper()
        if not token or token in seen or token not in allowed:
            continue
        if token not in required:
            continue
        seen.add(token)
        out.append(token)
    return tuple(out)


def _family_slice_rescue_source_limit(family_slice: dict | None) -> int:
    if not family_slice:
        return 6
    rescue_start = family_slice.get("rescue_start_conditions", {}) or {}
    try:
        limit = int(rescue_start.get("max_rescue_sources", 6) or 6)
    except Exception:
        limit = 6
    return max(1, limit)


def _family_slice_graveyard_negative_expansion_limit(family_slice: dict | None) -> int:
    if not family_slice:
        return 0
    rescue_start = family_slice.get("rescue_start_conditions", {}) or {}
    raw = rescue_start.get("graveyard_negative_expansion_limit", None)
    if raw in (None, ""):
        return 0
    try:
        limit = int(raw)
    except Exception:
        return 0
    return max(1, limit)


def _strategy_budget_for_mode(family_slice: dict | None, debate_mode: str) -> tuple[dict[str, int], str]:
    mode = str(debate_mode).strip()
    defaults = LIVE_STRATEGY_BUDGET_DEFAULTS.get(mode, LIVE_STRATEGY_BUDGET_DEFAULTS["balanced"])
    budget = {"max_items": int(defaults["max_items"]), "max_sims": int(defaults["max_sims"])}
    if not family_slice:
        return budget, "planner_default"
    rescue_start = family_slice.get("rescue_start_conditions", {}) or {}
    override_keys = {
        "balanced": ("balanced_max_items", "balanced_max_sims"),
        "graveyard_first": ("graveyard_first_max_items", "graveyard_first_max_sims"),
        "graveyard_recovery": ("graveyard_recovery_max_items", "graveyard_recovery_max_sims"),
    }
    keys = override_keys.get(mode)
    if not keys:
        return budget, "planner_default"
    max_items_key, max_sims_key = keys
    source = "planner_default"
    raw_items = rescue_start.get(max_items_key, None)
    raw_sims = rescue_start.get(max_sims_key, None)
    if raw_items not in (None, ""):
        try:
            budget["max_items"] = max(1, int(raw_items))
            source = "family_slice_override"
        except Exception:
            pass
    if raw_sims not in (None, ""):
        try:
            budget["max_sims"] = max(1, int(raw_sims))
            source = "family_slice_override"
        except Exception:
            pass
    return budget, source


def _family_slice_probe_term_override(family_slice: dict, goal_term: str) -> str:
    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    probe_term_overrides = sim_hooks.get("probe_term_overrides", {}) or {}
    if not isinstance(probe_term_overrides, dict):
        return ""
    return str(probe_term_overrides.get(str(goal_term).strip(), "")).strip().lower()


def _graveyard_negative_classes_for_mode(family_slice: dict | None) -> tuple[str, ...]:
    if family_slice:
        classes = _family_slice_negative_classes(family_slice)
        if classes:
            limit = _family_slice_graveyard_negative_expansion_limit(family_slice)
            return tuple(classes[:limit]) if limit > 0 else classes
    return (
        "COMMUTATIVE_ASSUMPTION",
        "CLASSICAL_TIME",
        "CONTINUOUS_BATH",
        "INFINITE_SET",
        "INFINITE_RESOLUTION",
        "PRIMITIVE_EQUALS",
        "EUCLIDEAN_METRIC",
        "CLASSICAL_TEMPERATURE",
    )


def _validate_family_slice_semantics(family_slice: dict) -> None:
    if str(family_slice.get("schema", "")).strip() != "A2_TO_A1_FAMILY_SLICE_v1":
        raise ValueError("invalid_family_slice_schema")
    required_lanes = {str(x).strip() for x in (family_slice.get("required_lanes", []) or []) if str(x).strip()}
    missing_lanes = sorted(FULL_CYCLE_LANES.difference(required_lanes))
    if missing_lanes:
        raise ValueError(f"family_slice_missing_required_lanes:{','.join(missing_lanes)}")
    lane_minimums = family_slice.get("lane_minimums", {}) or {}
    if lane_minimums and not isinstance(lane_minimums, dict):
        raise ValueError("family_slice_invalid_lane_minimums")
    visible_lane_minimums = {
        str(lane).strip(): int((payload or {}).get("min_branches", 0) or 0)
        for lane, payload in (lane_minimums.items() if isinstance(lane_minimums, dict) else [])
        if str(lane).strip()
    }
    missing_lane_minimums = sorted(required_lanes.difference(visible_lane_minimums.keys()))
    if missing_lane_minimums:
        raise ValueError(f"family_slice_missing_lane_minimums:{','.join(missing_lane_minimums)}")
    invalid_lane_minimums = sorted(lane for lane, value in visible_lane_minimums.items() if int(value) < 1)
    if invalid_lane_minimums:
        raise ValueError(f"family_slice_invalid_lane_minimums:{','.join(invalid_lane_minimums)}")

    admissibility = family_slice.get("admissibility", {}) or {}
    hints = family_slice.get("family_admissibility_hints", {}) or {}
    strategy_head_terms = {str(x).strip() for x in (hints.get("strategy_head_terms", []) or []) if str(x).strip()}
    if not strategy_head_terms:
        strategy_head_terms = {str(x).strip() for x in (admissibility.get("executable_head", []) or []) if str(x).strip()}
    if not strategy_head_terms:
        raise ValueError("family_slice_missing_strategy_head_terms")

    forbidden_head_terms = {
        str(x).strip() for x in (hints.get("forbid_strategy_head_terms", []) or []) if str(x).strip()
    }
    witness_only_terms = {
        str(x).strip() for x in (admissibility.get("witness_only_terms", []) or []) if str(x).strip()
    }.union({str(x).strip() for x in (hints.get("witness_only_terms", []) or []) if str(x).strip()})
    residue_only_terms = {str(x).strip() for x in (hints.get("residue_only_terms", []) or []) if str(x).strip()}
    blocked_heads = sorted(strategy_head_terms.intersection(forbidden_head_terms.union(witness_only_terms).union(residue_only_terms)))
    if blocked_heads:
        raise ValueError(f"family_slice_blocked_strategy_head_terms:{','.join(blocked_heads)}")

    sim_hooks = family_slice.get("sim_hooks", {}) or {}
    required_sim_families = _family_slice_required_sim_families(family_slice)
    missing_sim_families = sorted(set(REQUIRED_STRESS_SIM_FAMILIES).difference(set(required_sim_families)))
    if missing_sim_families:
        raise ValueError(f"family_slice_missing_required_sim_families:{','.join(missing_sim_families)}")
    unknown_sim_families = sorted(set(required_sim_families).difference(set(REQUIRED_STRESS_SIM_FAMILIES)))
    if unknown_sim_families:
        raise ValueError(f"family_slice_unknown_sim_families:{','.join(unknown_sim_families)}")
    required_probe_terms = set(_family_slice_declared_probe_terms(family_slice))
    probe_term_overrides = sim_hooks.get("probe_term_overrides", {}) or {}
    if probe_term_overrides and not isinstance(probe_term_overrides, dict):
        raise ValueError("family_slice_invalid_probe_term_overrides")
    for goal_term, probe_term_raw in (probe_term_overrides.items() if isinstance(probe_term_overrides, dict) else []):
        probe_term = str(probe_term_raw).strip().lower()
        if not probe_term:
            raise ValueError(f"family_slice_empty_probe_term_override:{goal_term}")
        if probe_term not in required_probe_terms:
            raise ValueError(f"family_slice_probe_override_not_declared:{goal_term}:{probe_term}")
        if probe_term not in PROBE_CAPABLE_TERMS:
            raise ValueError(f"family_slice_probe_override_not_probe_capable:{goal_term}:{probe_term}")

    expected_tier_floor = str(sim_hooks.get("expected_tier_floor", "")).strip().upper()
    term_sim_tiers = sim_hooks.get("term_sim_tiers", {}) or {}
    if term_sim_tiers and not isinstance(term_sim_tiers, dict):
        raise ValueError("family_slice_invalid_term_sim_tiers")
    for goal_term, tier_raw in (term_sim_tiers.items() if isinstance(term_sim_tiers, dict) else []):
        tier = str(tier_raw).strip().upper()
        if _sim_tier_rank(tier) < 0:
            raise ValueError(f"family_slice_invalid_term_sim_tier:{goal_term}:{tier}")
        if expected_tier_floor and _sim_tier_rank(tier) < _sim_tier_rank(expected_tier_floor):
            raise ValueError(f"family_slice_term_sim_tier_below_floor:{goal_term}:{tier}:{expected_tier_floor}")
    sim_family_tiers = sim_hooks.get("sim_family_tiers", {}) or {}
    if sim_family_tiers and not isinstance(sim_family_tiers, dict):
        raise ValueError("family_slice_invalid_sim_family_tiers")
    for family_raw, tier_raw in (sim_family_tiers.items() if isinstance(sim_family_tiers, dict) else []):
        family = str(family_raw).strip().upper()
        tier = str(tier_raw).strip().upper()
        if family not in required_sim_families:
            raise ValueError(f"family_slice_sim_family_tier_unknown_family:{family}")
        if _sim_tier_rank(tier) < 0:
            raise ValueError(f"family_slice_invalid_sim_family_tier:{family}:{tier}")
        if expected_tier_floor and _sim_tier_rank(tier) < _sim_tier_rank(expected_tier_floor):
            raise ValueError(f"family_slice_sim_family_tier_below_floor:{family}:{tier}:{expected_tier_floor}")
    recovery_sim_families_raw = sim_hooks.get("recovery_sim_families", []) or []
    if not recovery_sim_families_raw:
        raise ValueError("family_slice_missing_recovery_sim_families")
    if not isinstance(recovery_sim_families_raw, list):
        raise ValueError("family_slice_invalid_recovery_sim_families")
    allowed_recovery_families = {"BOUNDARY_SWEEP", "PERTURBATION", "COMPOSITION_STRESS"}
    for family_raw in recovery_sim_families_raw if isinstance(recovery_sim_families_raw, list) else []:
        family = str(family_raw).strip().upper()
        if family not in allowed_recovery_families:
            raise ValueError(f"family_slice_unsupported_recovery_sim_family:{family}")
        if family not in required_sim_families:
            raise ValueError(f"family_slice_recovery_sim_family_not_declared:{family}")


def _sim_family_tier_map(items: list[dict]) -> dict[str, list[str]]:
    by_family: dict[str, set[str]] = {}
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        family = ""
        tier = ""
        for field in (item.get("def_fields", []) or []):
            if not isinstance(field, dict):
                continue
            name = str(field.get("name", "")).strip()
            value = str(field.get("value", "")).strip().upper()
            if name == "FAMILY" and value:
                family = value
            elif name == "TIER" and value:
                tier = value
        if not family or not tier:
            continue
        by_family.setdefault(family, set()).add(tier)
    return {family: sorted(values) for family, values in sorted(by_family.items())}


def _candidate_def_field_map(candidate: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for field in (candidate.get("def_fields", []) or []):
        if not isinstance(field, dict):
            continue
        name = str(field.get("name", "")).strip().upper()
        value = str(field.get("value", "")).strip()
        if name and value:
            out[name] = value
    return out


def _is_rescue_candidate(candidate: dict) -> bool:
    field_map = _candidate_def_field_map(candidate)
    return any(
        str(field_map.get(name, "")).strip()
        for name in ("RESCUE_FROM", "RESCUE_FAILURE_MODE", "RESCUE_LIBRARY_TERM", "RESCUE_MODE")
    )


def _family_slice_lane_minimums(family_slice: dict | None) -> dict[str, int]:
    raw = ((family_slice or {}).get("lane_minimums", {}) or {})
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for lane, payload in raw.items():
        lane_token = str(lane).strip()
        if not lane_token:
            continue
        try:
            min_branches = int((payload or {}).get("min_branches", 0) or 0)
        except Exception:
            min_branches = 0
        if min_branches > 0:
            out[lane_token] = min_branches
    return out


def _family_slice_branch_requirements(family_slice: dict | None) -> dict[str, str]:
    slice_payload = family_slice or {}
    return {
        "primary": str(slice_payload.get("primary_branch_requirement", "") or "").strip(),
        "alternative": str(slice_payload.get("alternative_branch_requirement", "") or "").strip(),
        "negative": str(slice_payload.get("negative_branch_requirement", "") or "").strip(),
        "rescue": str(slice_payload.get("rescue_branch_requirement", "") or "").strip(),
    }


def _family_slice_lineage_requirements(family_slice: dict | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in (((family_slice or {}).get("lineage_requirements", []) or [])):
        token = str(raw).strip().lower()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _family_slice_forbid_rescue_during_fill(family_slice: dict | None) -> bool:
    guardrails = ((family_slice or {}).get("planner_guardrails", {}) or {})
    if not isinstance(guardrails, dict):
        return False
    return bool(guardrails.get("forbid_rescue_during_fill", False))


def _family_slice_branch_lineage_requirements(family_slice: dict | None) -> list[str]:
    return [token for token in _family_slice_lineage_requirements(family_slice) if token != "rescue_linkage"]


def _append_branch_lineage_fields(
    def_fields: list[dict],
    *,
    lineage_requirements: list[str],
    branch_id: str,
    parent_branch_id: str,
    feedback_refs: list[str],
) -> None:
    required = set(_family_slice_branch_lineage_requirements({"lineage_requirements": lineage_requirements}))
    if "branch_id" in required:
        def_fields.append(_df("F_BID", "BRANCH_ID", str(branch_id).strip() or "NONE"))
    if "parent_branch_id" in required:
        def_fields.append(_df("F_PBID", "PARENT_BRANCH_ID", str(parent_branch_id).strip() or "NONE"))
    if "feedback_refs" in required:
        refs = [str(ref).strip() for ref in feedback_refs if str(ref).strip()]
        def_fields.append(_df("F_FBACK", "FEEDBACK_REFS", json.dumps(refs), kind="JSON"))


def _append_rescue_lineage_fields(
    def_fields: list[dict],
    *,
    lineage_requirements: list[str],
    branch_id: str,
    parent_branch_id: str,
    feedback_refs: list[str],
    rescue_linkage: str,
) -> None:
    required = set(_family_slice_lineage_requirements({"lineage_requirements": lineage_requirements}))
    _append_branch_lineage_fields(
        def_fields,
        lineage_requirements=lineage_requirements,
        branch_id=branch_id,
        parent_branch_id=parent_branch_id,
        feedback_refs=feedback_refs,
    )
    if "rescue_linkage" in required and str(rescue_linkage).strip():
        def_fields.append(_df("F_RLINK", "RESCUE_LINKAGE", str(rescue_linkage).strip()))


def _lane_for_candidate(candidate: dict) -> str:
    if not isinstance(candidate, dict) or str(candidate.get("kind", "")).strip() != "SIM_SPEC":
        return ""
    field_map = _candidate_def_field_map(candidate)
    if _is_rescue_candidate(candidate):
        return "RESCUER"
    family = str(field_map.get("FAMILY", "")).strip().upper()
    if family == "BASELINE":
        return "STEELMAN"
    if family == "BOUNDARY_SWEEP":
        return "BOUNDARY_REPAIR"
    if family in {"PERTURBATION", "COMPOSITION_STRESS"}:
        return "ALT_FORMALISM"
    if family == "ADVERSARIAL_NEG":
        return "ADVERSARIAL_NEG"
    return ""


def _lane_branch_sim_ids(items: list[dict]) -> dict[str, list[str]]:
    by_lane: dict[str, set[str]] = {lane: set() for lane in sorted(FULL_CYCLE_LANES)}
    for item in items:
        lane = _lane_for_candidate(item)
        if not lane:
            continue
        field_map = _candidate_def_field_map(item)
        sim_id = str(field_map.get("SIM_ID", "")).strip() or str(item.get("id", "")).strip()
        if not sim_id:
            continue
        by_lane.setdefault(lane, set()).add(sim_id)
    return {lane: sorted(values) for lane, values in sorted(by_lane.items())}


def _lane_branch_counts(items: list[dict]) -> dict[str, int]:
    return {lane: len(values) for lane, values in _lane_branch_sim_ids(items).items()}


def _rescue_sim_families_used(items: list[dict]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        is_rescue = _is_rescue_candidate(item)
        family = ""
        for field in (item.get("def_fields", []) or []):
            if not isinstance(field, dict):
                continue
            name = str(field.get("name", "")).strip()
            value = str(field.get("value", "")).strip()
            if name == "FAMILY" and value:
                family = value.upper()
        if not is_rescue or not family or family in seen:
            continue
        seen.add(family)
        out.append(family)
    return out


def _rescue_source_count(items: list[dict]) -> int:
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        for field in (item.get("def_fields", []) or []):
            if not isinstance(field, dict):
                continue
            if str(field.get("name", "")).strip() != "RESCUE_FROM":
                continue
            value = str(field.get("value", "")).strip()
            if value:
                seen.add(value)
    return len(seen)


def _rescue_linkages_used(items: list[dict]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        if not _is_rescue_candidate(item):
            continue
        field_map = _candidate_def_field_map(item)
        linkage = str(field_map.get("RESCUE_LINKAGE", "")).strip()
        if not linkage or linkage in seen:
            continue
        seen.add(linkage)
        out.append(linkage)
    return out


def _rescue_lineage_fields_used(items: list[dict]) -> list[str]:
    visible: set[str] = set()
    lineage_names = {"BRANCH_ID", "PARENT_BRANCH_ID", "FEEDBACK_REFS", "RESCUE_LINKAGE"}
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        if not _is_rescue_candidate(item):
            continue
        for field in (item.get("def_fields", []) or []):
            if not isinstance(field, dict):
                continue
            name = str(field.get("name", "")).strip().upper()
            value = str(field.get("value", "")).strip()
            if name in lineage_names and value:
                visible.add(name.lower())
    return sorted(visible)


def _branch_lineage_fields_used(items: list[dict]) -> list[str]:
    visible: set[str] = set()
    lineage_names = {"BRANCH_ID", "PARENT_BRANCH_ID", "FEEDBACK_REFS"}
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        if _is_rescue_candidate(item):
            continue
        for field in (item.get("def_fields", []) or []):
            if not isinstance(field, dict):
                continue
            name = str(field.get("name", "")).strip().upper()
            value = str(field.get("value", "")).strip()
            if name in lineage_names and value:
                visible.add(name.lower())
    return sorted(visible)


def _non_rescue_branch_parentage_map(items: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        if _is_rescue_candidate(item):
            continue
        field_map = _candidate_def_field_map(item)
        branch_id = str(field_map.get("BRANCH_ID", "")).strip()
        if not branch_id:
            continue
        out[branch_id] = str(field_map.get("PARENT_BRANCH_ID", "")).strip() or "NONE"
    return {branch_id: out[branch_id] for branch_id in sorted(out)}


def _non_rescue_root_branch_ids(items: list[dict]) -> list[str]:
    parentage = _non_rescue_branch_parentage_map(items)
    return sorted([branch_id for branch_id, parent in parentage.items() if parent == "NONE"])


def _non_rescue_branch_child_counts(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for parent in _non_rescue_branch_parentage_map(items).values():
        token = str(parent).strip() or "NONE"
        counts[token] = counts.get(token, 0) + 1
    return {parent: counts[parent] for parent in sorted(counts)}


def _branch_group_for_goal(family_slice: dict | None, working_goal: Goal) -> str:
    family_token = _track_token(
        str((family_slice or {}).get("family_id", "") or (family_slice or {}).get("family_kind", "") or "FAMILY")
    )
    goal_token = _track_token(working_goal.term)
    if family_slice:
        return f"BG_FAMILY_{family_token}_{goal_token}"
    track_token = _track_token(working_goal.track)
    return f"BG_TRACK_{track_token}_{goal_token}"


def _branch_group_map(items: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        field_map = _candidate_def_field_map(item)
        branch_id = str(field_map.get("BRANCH_ID", "")).strip() or str(field_map.get("SIM_ID", "")).strip()
        branch_group = str(field_map.get("BRANCH_GROUP", "")).strip()
        if not branch_id or not branch_group:
            continue
        out[branch_id] = branch_group
    return {branch_id: out[branch_id] for branch_id in sorted(out)}


def _branch_groups_used(items: list[dict]) -> list[str]:
    return sorted({group for group in _branch_group_map(items).values() if str(group).strip()})


def _branch_track_map(items: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        field_map = _candidate_def_field_map(item)
        branch_id = str(field_map.get("BRANCH_ID", "")).strip() or str(field_map.get("SIM_ID", "")).strip()
        branch_track = str(field_map.get("BRANCH_TRACK", "")).strip()
        if not branch_id or not branch_track:
            continue
        out[branch_id] = branch_track
    return {branch_id: out[branch_id] for branch_id in sorted(out)}


def _branch_tracks_used(items: list[dict]) -> list[str]:
    return sorted({track for track in _branch_track_map(items).values() if str(track).strip()})


def _load_family_slice(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"family_slice_not_found:{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"family_slice_invalid_json:{path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("family_slice_not_object")
    if not FAMILY_SLICE_SCHEMA_PATH.exists():
        raise FileNotFoundError(f"family_slice_schema_not_found:{FAMILY_SLICE_SCHEMA_PATH}")
    try:
        import jsonschema
    except Exception as exc:  # pragma: no cover - import availability is environment-specific
        raise RuntimeError("jsonschema_required_for_family_slice_validation") from exc
    schema = json.loads(FAMILY_SLICE_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)
    _validate_family_slice_semantics(payload)
    return payload


def _goal_for_term(term: str, *, family_slice: dict | None = None) -> Goal:
    normalized_term = str(term).strip()
    known = _KNOWN_GOAL_BY_TERM.get(str(term).strip())
    if family_slice is not None:
        family_negative_classes = _family_slice_negative_classes(family_slice)
        negative_class = next(
            iter(family_negative_classes),
            str(known.negative_class).strip().upper() if known is not None else "COMMUTATIVE_ASSUMPTION",
        )
        return Goal(
            term=normalized_term,
            track=_family_slice_track(normalized_term, family_slice),
            negative_class=negative_class,
            negative_markers=_negative_markers_for_class(negative_class),
        )
    if known is not None:
        return known
    required_negative_classes = [
        str(x).strip().upper()
        for x in ((family_slice or {}).get("required_negative_classes", []) or [])
        if str(x).strip()
    ]
    negative_class = required_negative_classes[0] if required_negative_classes else "COMMUTATIVE_ASSUMPTION"
    return Goal(
        term=normalized_term,
        track=f"FAMILY_SLICE_{_track_token(normalized_term)}",
        negative_class=negative_class,
        negative_markers=_negative_markers_for_class(negative_class),
    )


def _goals_from_family_slice(family_slice: dict) -> tuple[Goal, ...]:
    admissibility = family_slice.get("admissibility", {}) or {}
    hints = family_slice.get("family_admissibility_hints", {}) or {}
    companion_floor = [str(x).strip() for x in (admissibility.get("active_companion_floor", []) or []) if str(x).strip()]
    head_terms = [str(x).strip() for x in (hints.get("strategy_head_terms", []) or []) if str(x).strip()]
    if not head_terms:
        head_terms = [str(x).strip() for x in (admissibility.get("executable_head", []) or []) if str(x).strip()]
    late_passengers = [str(x).strip() for x in (hints.get("late_passenger_terms", []) or []) if str(x).strip()]
    if not late_passengers:
        late_passengers = [str(x).strip() for x in (admissibility.get("late_passengers", []) or []) if str(x).strip()]
    primary_terms = [str(x).strip() for x in (family_slice.get("primary_target_terms", []) or []) if str(x).strip()]
    blocked_terms = {
        str(x).strip() for x in (hints.get("forbid_strategy_head_terms", []) or []) if str(x).strip()
    }
    blocked_terms.update(str(x).strip() for x in (admissibility.get("witness_only_terms", []) or []) if str(x).strip())
    blocked_terms.update(str(x).strip() for x in (hints.get("witness_only_terms", []) or []) if str(x).strip())
    blocked_terms.update(str(x).strip() for x in (hints.get("residue_only_terms", []) or []) if str(x).strip())

    ordered_terms = [
        term
        for term in _ordered_unique_terms(companion_floor, head_terms, late_passengers, primary_terms)
        if term not in blocked_terms
    ]
    if not ordered_terms:
        raise ValueError("family_slice_has_no_plannable_terms")
    return tuple(_goal_for_term(term, family_slice=family_slice) for term in ordered_terms)


def _resolve_debate_mode_from_family_slice(family_slice: dict, requested_mode: str) -> str:
    mode = str(requested_mode).strip()
    run_mode = str(family_slice.get("run_mode", "")).strip()
    if run_mode == "GRAVEYARD_VALIDITY" and mode == "balanced":
        return "graveyard_first"
    return mode


def _compatibility_goals_for_profile(goal_profile: str) -> tuple[Goal, ...]:
    return tuple(_goal_for_term(term) for term in _compatibility_scaffold_terms_for_profile(goal_profile))


def _compatibility_scaffold_terms_for_profile(goal_profile: str) -> tuple[str, ...]:
    profile = str(goal_profile).strip()
    return COMPATIBILITY_SCAFFOLD_TERMS_BY_PROFILE.get(
        profile,
        COMPATIBILITY_SCAFFOLD_TERMS_BY_PROFILE["extended"],
    )


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


def _family_slice_probe_term_for_goal(state: dict, goal_term: str, family_slice: dict | None) -> tuple[str, str]:
    if family_slice:
        override = _family_slice_probe_term_override(family_slice, goal_term)
        if override:
            return override, "family_slice_override"
        goal_token = str(goal_term).strip().lower()
        declared_probe_terms = list(_family_slice_declared_probe_terms(family_slice))
        declared_probe_term_set = set(declared_probe_terms)
        if goal_token in declared_probe_term_set and goal_token in PROBE_CAPABLE_TERMS:
            return goal_token, "family_slice_goal_term"
        declared_components = [
            comp
            for comp in (str(x).strip().lower() for x in _components(goal_term))
            if comp in declared_probe_term_set and comp in PROBE_CAPABLE_TERMS
        ]
        if declared_components:
            available_components = [comp for comp in declared_components if _is_term_available(state, comp)]
            if available_components:
                return available_components[0], "family_slice_component_available"
            return declared_components[0], "family_slice_component_declared"
        admissibility = family_slice.get("admissibility", {}) or {}
        family_probe_candidates = _ordered_unique_terms(
            [str(x).strip().lower() for x in (admissibility.get("active_companion_floor", []) or []) if str(x).strip()],
            [str(x).strip().lower() for x in (admissibility.get("executable_head", []) or []) if str(x).strip()],
            [str(x).strip().lower() for x in (family_slice.get("primary_target_terms", []) or []) if str(x).strip()],
            declared_probe_terms,
        )
        family_probe_candidates = [
            term for term in family_probe_candidates if term in declared_probe_term_set and term in PROBE_CAPABLE_TERMS
        ]
        available_candidates = [term for term in family_probe_candidates if _is_term_available(state, term)]
        if available_candidates:
            return available_candidates[0], "family_slice_declared_available"
        if family_probe_candidates:
            return family_probe_candidates[0], "family_slice_declared_fallback"
    return _probe_term_for_goal(state, goal_term), "global_default"


def _sim_families_used(items: list[dict]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        family = ""
        for field in (item.get("def_fields", []) or []):
            if not isinstance(field, dict):
                continue
            if str(field.get("name", "")).strip() != "FAMILY":
                continue
            family = str(field.get("value", "")).strip().upper()
            break
        if family and family not in seen:
            seen.add(family)
            out.append(family)
    return out


def _sim_family_operator_map(items: list[dict]) -> dict[str, list[str]]:
    by_family: dict[str, set[str]] = {}
    for item in items:
        if not isinstance(item, dict) or str(item.get("kind", "")).strip() != "SIM_SPEC":
            continue
        family = ""
        for field in (item.get("def_fields", []) or []):
            if not isinstance(field, dict):
                continue
            if str(field.get("name", "")).strip() != "FAMILY":
                continue
            family = str(field.get("value", "")).strip().upper()
            break
        operator_id = str(item.get("operator_id", "")).strip().upper()
        if not family or not operator_id:
            continue
        by_family.setdefault(family, set()).add(operator_id)
    return {family: sorted(operators) for family, operators in sorted(by_family.items())}


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


def _emit_atomic_term_batch(
    term: str,
    *,
    prefix: str,
    sim_code_hash: str,
    probe_id: str,
    probe_token: str,
    lineage_requirements: list[str] | None = None,
    parent_branch_id: str = "NONE",
    branch_group: str = "",
    branch_track: str = "",
) -> list[dict]:
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
    sim_def_fields = [
        _df("F_EVID", "REQUIRES_EVIDENCE", evidence),
        _df("F_SIMID", "SIM_ID", sim_id),
        _df("F_TIER", "TIER", "T0_ATOM"),
        _df("F_FAM", "FAMILY", "BASELINE"),
        _df("F_TC", "TARGET_CLASS", "TC_ATOMIC_TERM_BOOTSTRAP"),
        _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
        _df("F_PTERM", "PROBE_TERM", term),
    ]
    if str(branch_group).strip():
        sim_def_fields.append(_df("F_BG", "BRANCH_GROUP", str(branch_group).strip()))
    if str(branch_track).strip():
        sim_def_fields.append(_df("F_TRACK", "BRANCH_TRACK", str(branch_track).strip()))
    _append_branch_lineage_fields(
        sim_def_fields,
        lineage_requirements=(lineage_requirements or []),
        branch_id=sim_id,
        parent_branch_id=parent_branch_id,
        feedback_refs=[evidence],
    )
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
            "def_fields": sim_def_fields,
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


def _existing_math_def_id_for_term(state: dict, term: str) -> str:
    """
    If a MATH_DEF for `term` was already admitted earlier (but TERM_DEF/CANON_PERMIT
    later failed due to undefined lexemes / missing evidence), re-use that math id
    instead of emitting a near-duplicate MATH_DEF that will be parked as NEAR_REDUNDANT.
    """
    term_upper = str(term).upper()
    needle = f"_MATH_{term_upper}"
    spec_meta = state.get("spec_meta", {}) or {}
    candidates: list[str] = []
    if isinstance(spec_meta, dict):
        for item_id, meta in spec_meta.items():
            if not isinstance(item_id, str) or needle not in item_id:
                continue
            if isinstance(meta, dict) and str(meta.get("kind", "")) == "MATH_DEF":
                candidates.append(item_id)
    if not candidates:
        return ""
    # Deterministic pick: earliest id wins (stable across runs).
    return sorted(candidates)[0]


def build_strategy_from_state(
    *,
    state: dict,
    run_id: str,
    sequence: int,
    goals: tuple[Goal, ...],
    goal_selection: str = "interleaved",
    debate_mode: str = "balanced",
    family_slice: dict | None = None,
) -> dict:
    sim_stub_path = BASE / "SIM_STUB_QIT_v1.txt"
    sim_code_hash = _sha256_file(sim_stub_path)
    strategy_budget, strategy_budget_source = _strategy_budget_for_mode(family_slice, debate_mode)
    family_slice_lineage_requirements = _family_slice_lineage_requirements(family_slice)

    # Probe discipline (BR-009): kernel enforces at least 1 probe per 10 specs.
    # Therefore we generate a small pool of probes and deterministically assign
    # each SIM_SPEC to one probe. This prevents PROBE_PRESSURE parking at scale.
    max_items_for_budget = int(strategy_budget["max_items"])
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
    goal_priority_source = "next_goal"
    if goal is None:
        # Deterministic no-op batch: still emits a valid strategy, but will likely
        # be rejected/parked upstream by A0 cross-basin logic if empty.
        goal = goals[-1]
        goal_priority_source = "goals_tail_fallback"

    # Refined-fuel discipline: prioritize the whole-system conjunction witness once
    # its minimal prerequisites are already canonical. This prevents starvation
    # when the goal list is large and keeps the "proof surface" reachable without
    # forcing a fully-complete ladder first.
    master_goal = next((g for g in goals if g.term == "qit_master_conjunction"), None)
    if not family_slice and master_goal is not None and not _is_term_canonical(state, master_goal.term):
        master_prereqs = (
            "density_matrix",
            "cptp_channel",
            "partial_trace",
            "unitary_operator",
            "correlation_polarity",
        )
        if all(_is_term_canonical(state, t) for t in master_prereqs):
            goal = master_goal
            goal_priority_source = "compatibility_master_override"

    # Deterministic prerequisites: always keep the selected goal as the main
    # working target, but explicitly bootstrap any non-canonical subterms so
    # long compounds are visibly built from atomic terms.
    working_goal = goal
    probe_term, probe_source = _family_slice_probe_term_for_goal(state, working_goal.term, family_slice)
    sim_family_selection = (
        list(_family_slice_required_sim_families(family_slice))
        if family_slice
        else list(REQUIRED_STRESS_SIM_FAMILIES)
    )
    enabled_sim_families = set(sim_family_selection)
    bootstrap_components: list[str] = []
    l0_lexemes = {str(x).strip() for x in (state.get("l0_lexeme_set", []) or []) if str(x).strip()}
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
    existing_math_id = _existing_math_def_id_for_term(state, working_goal.term)
    math_id = existing_math_id or f"{prefix}_MATH_{working_goal.term.upper()}"
    term_id = f"{prefix}_TERM_{working_goal.term.upper()}"
    permit_id = f"{prefix}_CANON_{working_goal.term.upper()}"
    sim_pos_id = (
        "SIM_MASTER_T6" if working_goal.term == "qit_master_conjunction" else f"{prefix}_SIM_CANON_{working_goal.term.upper()}"
    )
    ev_goal = f"E_CANON_{working_goal.term.upper()}"
    sim_tier = _family_slice_term_sim_tier(family_slice or {}, working_goal.term) or _sim_tier_for_term(working_goal.term)
    if family_slice:
        target_class_value = _family_slice_target_class(working_goal.term, family_slice)
    else:
        target_class_value = "TC_QIT_MASTER" if working_goal.term == "qit_master_conjunction" else f"TC_{working_goal.track}"
    branch_group_value = _branch_group_for_goal(family_slice, working_goal)
    baseline_track_value = working_goal.track

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
    family_surface = _family_slice_math_surface_for_term(family_slice or {}, working_goal.term)
    if family_surface:
        objects_value = family_surface["objects"]
        operations_value = family_surface["operations"]
        invariants_value = family_surface["invariants"]
        domain_value = family_surface["domain"]
        codomain_value = family_surface["codomain"]
    elif working_goal.term in MINIMAL_SUBSTRATE_MATH_SURFACES:
        minimal = MINIMAL_SUBSTRATE_MATH_SURFACES[working_goal.term]
        objects_value = minimal["objects"]
        operations_value = minimal["operations"]
        invariants_value = minimal["invariants"]
        domain_value = minimal["domain"]
        codomain_value = minimal["codomain"]
    elif working_goal.term == "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator":
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

    target_items: list[dict] = []
    if not existing_math_id:
        target_items.append(
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
            }
        )
    target_items.extend(
        [
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
        ]
    )
    if "BASELINE" in enabled_sim_families:
        baseline_def_fields = [
            _df("F_EVID", "REQUIRES_EVIDENCE", ev_goal),
            _df("F_SIMID", "SIM_ID", sim_pos_id),
            _df("F_TIER", "TIER", sim_tier),
            _df("F_FAM", "FAMILY", "BASELINE"),
            _df("F_TC", "TARGET_CLASS", target_class_value),
            _df("F_BG", "BRANCH_GROUP", branch_group_value),
            _df("F_TRACK", "BRANCH_TRACK", baseline_track_value),
            _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
            _df("F_PTERM", "PROBE_TERM", probe_term),
            _df("F_GTERM", "GOAL_TERM", working_goal.term),
        ]
        _append_branch_lineage_fields(
            baseline_def_fields,
            lineage_requirements=family_slice_lineage_requirements,
            branch_id=sim_pos_id,
            parent_branch_id="NONE",
            feedback_refs=[ev_goal],
        )
        target_items.append(
            {
                "item_class": "SPEC_HYP",
                "id": sim_pos_id,
                "kind": "SIM_SPEC",
                "requires": [probe_id_for(sim_pos_id)],
                "def_fields": baseline_def_fields,
                "asserts": [
                    _assert("A_EVID", "EVIDENCE_TOKEN", ev_goal),
                    _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(sim_pos_id))),
                ],
                "operator_id": "OP_BIND_SIM",
            }
        )

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

    negative_items: list[dict] = []
    for family in sim_family_selection:
        if family == "BASELINE" or family not in enabled_sim_families:
            continue
        if family == "BOUNDARY_SWEEP":
            family_tier = _family_slice_sim_family_tier(
                family_slice or {},
                "BOUNDARY_SWEEP",
                default=LIVE_SIM_FAMILY_TIER_DEFAULTS["BOUNDARY_SWEEP"],
            )
            boundary_def_fields = [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_boundary),
                _df("F_SIMID", "SIM_ID", alt_boundary_id),
                _df("F_TIER", "TIER", family_tier),
                _df("F_FAM", "FAMILY", "BOUNDARY_SWEEP"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_BG", "BRANCH_GROUP", branch_group_value),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
                _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_BOUNDARY"),
            ]
            _append_branch_lineage_fields(
                boundary_def_fields,
                lineage_requirements=family_slice_lineage_requirements,
                branch_id=alt_boundary_id,
                parent_branch_id=sim_pos_id,
                feedback_refs=[ev_boundary],
            )
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": alt_boundary_id,
                    "kind": "SIM_SPEC",
                    "requires": [probe_id_for(alt_boundary_id), math_id],
                    "def_fields": boundary_def_fields,
                    "asserts": [
                        _assert("A_EVID", "EVIDENCE_TOKEN", ev_boundary),
                        _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_boundary_id))),
                    ],
                    "operator_id": "OP_REPAIR_DEF_FIELD",
                }
            )
        elif family == "PERTURBATION":
            family_tier = _family_slice_sim_family_tier(
                family_slice or {},
                "PERTURBATION",
                default=LIVE_SIM_FAMILY_TIER_DEFAULTS["PERTURBATION"],
            )
            perturb_def_fields = [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_perturb),
                _df("F_SIMID", "SIM_ID", alt_perturb_id),
                _df("F_TIER", "TIER", family_tier),
                _df("F_FAM", "FAMILY", "PERTURBATION"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_BG", "BRANCH_GROUP", branch_group_value),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
                _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_PERTURB"),
            ]
            _append_branch_lineage_fields(
                perturb_def_fields,
                lineage_requirements=family_slice_lineage_requirements,
                branch_id=alt_perturb_id,
                parent_branch_id=sim_pos_id,
                feedback_refs=[ev_perturb],
            )
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": alt_perturb_id,
                    "kind": "SIM_SPEC",
                    "requires": [probe_id_for(alt_perturb_id), math_id],
                    "def_fields": perturb_def_fields,
                    "asserts": [
                        _assert("A_EVID", "EVIDENCE_TOKEN", ev_perturb),
                        _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_perturb_id))),
                    ],
                    "operator_id": "OP_MUTATE_LEXEME",
                }
            )
        elif family == "COMPOSITION_STRESS":
            family_tier = _family_slice_sim_family_tier(
                family_slice or {},
                "COMPOSITION_STRESS",
                default=LIVE_SIM_FAMILY_TIER_DEFAULTS["COMPOSITION_STRESS"],
            )
            stress_def_fields = [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_stress),
                _df("F_SIMID", "SIM_ID", alt_stress_id),
                _df("F_TIER", "TIER", family_tier),
                _df("F_FAM", "FAMILY", "COMPOSITION_STRESS"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_BG", "BRANCH_GROUP", branch_group_value),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
                _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_STRESS"),
            ]
            _append_branch_lineage_fields(
                stress_def_fields,
                lineage_requirements=family_slice_lineage_requirements,
                branch_id=alt_stress_id,
                parent_branch_id=sim_pos_id,
                feedback_refs=[ev_stress],
            )
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": alt_stress_id,
                    "kind": "SIM_SPEC",
                    "requires": [probe_id_for(alt_stress_id), math_id, term_id],
                    "def_fields": stress_def_fields,
                    "asserts": [
                        _assert("A_EVID", "EVIDENCE_TOKEN", ev_stress),
                        _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_stress_id))),
                    ],
                    "operator_id": "OP_REORDER_DEPENDENCIES",
                }
            )
        elif family == "ADVERSARIAL_NEG":
            family_tier = _family_slice_sim_family_tier(
                family_slice or {},
                "ADVERSARIAL_NEG",
                default=LIVE_SIM_FAMILY_TIER_DEFAULTS["ADVERSARIAL_NEG"],
            )
            neg_def_fields = [
                _df("F_EVID", "REQUIRES_EVIDENCE", ev_neg),
                _df("F_SIMID", "SIM_ID", alt_neg_sim_id),
                _df("F_TIER", "TIER", family_tier),
                _df("F_FAM", "FAMILY", "ADVERSARIAL_NEG"),
                _df("F_TC", "TARGET_CLASS", target_class_value),
                _df("F_BG", "BRANCH_GROUP", branch_group_value),
                _df("F_NEG", "NEGATIVE_CLASS", working_goal.negative_class),
                _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                _df("F_PTERM", "PROBE_TERM", probe_term),
                _df("F_GTERM", "GOAL_TERM", working_goal.term),
                _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_NEG"),
            ]
            _append_branch_lineage_fields(
                neg_def_fields,
                lineage_requirements=family_slice_lineage_requirements,
                branch_id=alt_neg_id,
                parent_branch_id=sim_pos_id,
                feedback_refs=[ev_neg],
            )
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": alt_neg_id,
                    "kind": "SIM_SPEC",
                    "requires": [probe_id_for(alt_neg_id), math_id],
                    "def_fields": neg_def_fields,
                    "asserts": [
                        _assert("A_EVID", "EVIDENCE_TOKEN", ev_neg),
                        _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(alt_neg_id))),
                    ],
                    "operator_id": "OP_NEG_SIM_EXPAND",
                }
            )

    for item in negative_items:
        if str(item.get("id", "")).strip() != alt_neg_id:
            continue
        for idx, (name, value) in enumerate(working_goal.negative_markers, start=1):
            item["def_fields"].append(_df(f"F_MARK{idx:02d}", name, value))
        break

    # Graveyard-first mode intentionally widens adversarial lanes to create a dense
    # kill surface before recovery passes begin.
    if debate_mode == "graveyard_first" and "ADVERSARIAL_NEG" in enabled_sim_families:
        neg_classes = list(_graveyard_negative_classes_for_mode(family_slice))
        graveyard_neg_tier = _family_slice_sim_family_tier(
            family_slice or {},
            "ADVERSARIAL_NEG",
            default="T2_OPERATOR",
        )
        for j, neg_cls in enumerate(neg_classes, start=1):
            alt_id = f"{prefix}_SIM_ALT_NEG_EXTRA{j}_{working_goal.term.upper()}"
            ev_id = f"E_ALT_NEG_EXTRA{j}_{working_goal.term.upper()}"
            marker_name, marker_value = _negative_markers_for_class(neg_cls)[0]
            negative_items.append(
                {
                    "item_class": "SPEC_HYP",
                    "id": alt_id,
                    "kind": "SIM_SPEC",
                    "requires": [probe_id_for(alt_id), math_id],
                    "def_fields": [
                        _df("F_EVID", "REQUIRES_EVIDENCE", ev_id),
                        _df("F_SIMID", "SIM_ID", alt_id),
                        _df("F_TIER", "TIER", graveyard_neg_tier),
                        _df("F_FAM", "FAMILY", "ADVERSARIAL_NEG"),
                        _df("F_TC", "TARGET_CLASS", target_class_value),
                        _df("F_BG", "BRANCH_GROUP", branch_group_value),
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
            _append_branch_lineage_fields(
                negative_items[-1]["def_fields"],
                lineage_requirements=family_slice_lineage_requirements,
                branch_id=alt_id,
                parent_branch_id=alt_neg_id,
                feedback_refs=[ev_id],
            )

    # Recovery mode consumes recent killed surfaces as explicit rescue attempts.
    if debate_mode == "graveyard_recovery" and working_goal.term != "qit_master_conjunction":
        recovery_sim_families = set(_family_slice_recovery_sim_families(family_slice))
        rescue_source_limit = _family_slice_rescue_source_limit(family_slice)
        for idx, kill in enumerate(_recent_kill_context(state, limit=rescue_source_limit), start=1):
            rescue_probe_id = f"P_QIT_RESCUE_{sequence:06d}_{idx}"
            rescue_probe_token = f"PT_QIT_RESCUE_{sequence:06d}_{idx}"
            tc = kill.get("target_class") or f"TC_{working_goal.track}"
            source_id = kill.get("id", "")
            feedback_refs = [str(kill.get("token", "")).strip(), f"E_RESCUE_{idx}_{working_goal.term.upper()}"]
            if "BOUNDARY_SWEEP" in enabled_sim_families and "BOUNDARY_SWEEP" in recovery_sim_families:
                rescue_boundary_tier = _family_slice_sim_family_tier(
                    family_slice or {},
                    "BOUNDARY_SWEEP",
                    default="T2_OPERATOR",
                )
                rescue_boundary_evidence = f"E_RESCUE_BOUNDARY_{idx}_{working_goal.term.upper()}"
                rescue_boundary_id = f"{prefix}_SIM_RESCUE_BOUNDARY_{idx}_{working_goal.term.upper()}"
                rescue_boundary_linkage = f"GRAVEYARD::{source_id}::BOUNDARY_SWEEP::{idx}"
                rescue_boundary_fields = [
                    _df("F_EVID", "REQUIRES_EVIDENCE", rescue_boundary_evidence),
                    _df("F_SIMID", "SIM_ID", rescue_boundary_id),
                    _df("F_TIER", "TIER", rescue_boundary_tier),
                    _df("F_FAM", "FAMILY", "BOUNDARY_SWEEP"),
                    _df("F_TC", "TARGET_CLASS", tc),
                    _df("F_BG", "BRANCH_GROUP", branch_group_value),
                    _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                    _df("F_PTERM", "PROBE_TERM", probe_term),
                    _df("F_GTERM", "GOAL_TERM", working_goal.term),
                    _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_RESCUE_BOUNDARY_{source_id}"),
                    _df("F_RMODE", "RESCUE_MODE", "GRAVEYARD_RECOVERY"),
                    _df("F_RFROM", "RESCUE_FROM", source_id),
                    _df("F_RTOK", "RESCUE_TOKEN", str(kill.get("token", "")).strip() or "UNKNOWN"),
                ]
                _append_rescue_lineage_fields(
                    rescue_boundary_fields,
                    lineage_requirements=family_slice_lineage_requirements,
                    branch_id=rescue_boundary_id,
                    parent_branch_id=source_id,
                    feedback_refs=[str(kill.get("token", "")).strip(), rescue_boundary_evidence],
                    rescue_linkage=rescue_boundary_linkage,
                )
                negative_items.append(
                    {
                        "item_class": "SPEC_HYP",
                        "id": rescue_boundary_id,
                        "kind": "SIM_SPEC",
                        "requires": [rescue_probe_id, math_id],
                        "def_fields": rescue_boundary_fields,
                        "asserts": [
                            _assert("A_EVID", "EVIDENCE_TOKEN", rescue_boundary_evidence),
                            _assert("A_PROBE", "PROBE_TOKEN", rescue_probe_token),
                        ],
                        "operator_id": "OP_REPAIR_DEF_FIELD",
                    }
                )
            if "PERTURBATION" in enabled_sim_families and "PERTURBATION" in recovery_sim_families:
                rescue_perturb_tier = _family_slice_sim_family_tier(
                    family_slice or {},
                    "PERTURBATION",
                    default="T2_OPERATOR",
                )
                rescue_perturb_evidence = f"E_RESCUE_PERTURB_{idx}_{working_goal.term.upper()}"
                rescue_perturb_id = f"{prefix}_SIM_RESCUE_PERTURB_{idx}_{working_goal.term.upper()}"
                rescue_perturb_linkage = f"GRAVEYARD::{source_id}::PERTURBATION::{idx}"
                rescue_perturb_fields = [
                    _df("F_EVID", "REQUIRES_EVIDENCE", rescue_perturb_evidence),
                    _df("F_SIMID", "SIM_ID", rescue_perturb_id),
                    _df("F_TIER", "TIER", rescue_perturb_tier),
                    _df("F_FAM", "FAMILY", "PERTURBATION"),
                    _df("F_TC", "TARGET_CLASS", tc),
                    _df("F_BG", "BRANCH_GROUP", branch_group_value),
                    _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                    _df("F_PTERM", "PROBE_TERM", probe_term),
                    _df("F_GTERM", "GOAL_TERM", working_goal.term),
                    _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_RESCUE_PERTURB_{source_id}"),
                    _df("F_RMODE", "RESCUE_MODE", "GRAVEYARD_RECOVERY"),
                    _df("F_RFROM", "RESCUE_FROM", source_id),
                    _df("F_RTOK", "RESCUE_TOKEN", str(kill.get("token", "")).strip() or "UNKNOWN"),
                ]
                _append_rescue_lineage_fields(
                    rescue_perturb_fields,
                    lineage_requirements=family_slice_lineage_requirements,
                    branch_id=rescue_perturb_id,
                    parent_branch_id=source_id,
                    feedback_refs=[str(kill.get("token", "")).strip(), rescue_perturb_evidence],
                    rescue_linkage=rescue_perturb_linkage,
                )
                negative_items.append(
                    {
                        "item_class": "SPEC_HYP",
                        "id": rescue_perturb_id,
                        "kind": "SIM_SPEC",
                        "requires": [rescue_probe_id, math_id],
                        "def_fields": rescue_perturb_fields,
                        "asserts": [
                            _assert("A_EVID", "EVIDENCE_TOKEN", rescue_perturb_evidence),
                            _assert("A_PROBE", "PROBE_TOKEN", rescue_probe_token),
                        ],
                        "operator_id": "OP_MUTATE_LEXEME",
                    }
                )
            if "COMPOSITION_STRESS" in enabled_sim_families and "COMPOSITION_STRESS" in recovery_sim_families:
                rescue_stress_tier = _family_slice_sim_family_tier(
                    family_slice or {},
                    "COMPOSITION_STRESS",
                    default="T3_STRUCTURE",
                )
                rescue_stress_evidence = f"E_RESCUE_STRESS_{idx}_{working_goal.term.upper()}"
                rescue_stress_id = f"{prefix}_SIM_RESCUE_STRESS_{idx}_{working_goal.term.upper()}"
                rescue_stress_linkage = f"GRAVEYARD::{source_id}::COMPOSITION_STRESS::{idx}"
                rescue_stress_fields = [
                    _df("F_EVID", "REQUIRES_EVIDENCE", rescue_stress_evidence),
                    _df("F_SIMID", "SIM_ID", rescue_stress_id),
                    _df("F_TIER", "TIER", rescue_stress_tier),
                    _df("F_FAM", "FAMILY", "COMPOSITION_STRESS"),
                    _df("F_TC", "TARGET_CLASS", tc),
                    _df("F_BG", "BRANCH_GROUP", branch_group_value),
                    _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                    _df("F_PTERM", "PROBE_TERM", probe_term),
                    _df("F_GTERM", "GOAL_TERM", working_goal.term),
                    _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_RESCUE_STRESS_{source_id}"),
                    _df("F_RMODE", "RESCUE_MODE", "GRAVEYARD_RECOVERY"),
                    _df("F_RFROM", "RESCUE_FROM", source_id),
                    _df("F_RTOK", "RESCUE_TOKEN", str(kill.get("token", "")).strip() or "UNKNOWN"),
                ]
                _append_rescue_lineage_fields(
                    rescue_stress_fields,
                    lineage_requirements=family_slice_lineage_requirements,
                    branch_id=rescue_stress_id,
                    parent_branch_id=source_id,
                    feedback_refs=[str(kill.get("token", "")).strip(), rescue_stress_evidence],
                    rescue_linkage=rescue_stress_linkage,
                )
                negative_items.append(
                    {
                        "item_class": "SPEC_HYP",
                        "id": rescue_stress_id,
                        "kind": "SIM_SPEC",
                        "requires": [rescue_probe_id, math_id, term_id],
                        "def_fields": rescue_stress_fields,
                        "asserts": [
                            _assert("A_EVID", "EVIDENCE_TOKEN", rescue_stress_evidence),
                            _assert("A_PROBE", "PROBE_TOKEN", rescue_probe_token),
                        ],
                        "operator_id": "OP_REORDER_DEPENDENCIES",
                    }
                )

    if family_slice:
        existing_rescue_count = sum(1 for item in negative_items if _is_rescue_candidate(item))
        required_rescue_branches = max(1, _family_slice_lane_minimums(family_slice).get("RESCUER", 1))
        scaffold_rescue_count = max(0, required_rescue_branches - existing_rescue_count)
        recovery_sim_families = [
            family for family in _family_slice_recovery_sim_families(family_slice) if family in enabled_sim_families
        ]
        rescue_failure_modes = [
            str(value).strip()
            for value in ((family_slice.get("expected_failure_modes", []) or []))
            if str(value).strip()
        ] or ["family_slice_declared_failure"]
        rescue_library_terms = [
            str(value).strip()
            for value in ((family_slice.get("graveyard_library_terms", []) or []))
            if str(value).strip()
        ]
        allow_scaffold_rescue = not (
            debate_mode == "graveyard_first" and _family_slice_forbid_rescue_during_fill(family_slice)
        )
        if recovery_sim_families and scaffold_rescue_count > 0 and allow_scaffold_rescue:
            for rescue_index in range(1, scaffold_rescue_count + 1):
                rescue_family = recovery_sim_families[(rescue_index - 1) % len(recovery_sim_families)]
                rescue_failure_mode = rescue_failure_modes[(rescue_index - 1) % len(rescue_failure_modes)]
                rescue_library_term = (
                    rescue_library_terms[(rescue_index - 1) % len(rescue_library_terms)] if rescue_library_terms else ""
                )
                rescue_id = (
                    f"{prefix}_SIM_RESCUE_SCAFFOLD_{rescue_index}_{rescue_family}_{working_goal.term.upper()}"
                )
                rescue_evidence = (
                    f"E_RESCUE_SCAFFOLD_{rescue_index}_{rescue_family}_{working_goal.term.upper()}"
                )
                rescue_tier = _family_slice_sim_family_tier(
                    family_slice or {},
                    rescue_family,
                    default=LIVE_SIM_FAMILY_TIER_DEFAULTS.get(rescue_family, "T2_OPERATOR"),
                )
                rescue_requires = [probe_id_for(rescue_id), math_id]
                rescue_operator_id = "OP_REPAIR_DEF_FIELD"
                if rescue_family == "PERTURBATION":
                    rescue_operator_id = "OP_MUTATE_LEXEME"
                elif rescue_family == "COMPOSITION_STRESS":
                    rescue_operator_id = "OP_REORDER_DEPENDENCIES"
                    rescue_requires.append(term_id)
                rescue_def_fields = [
                    _df("F_EVID", "REQUIRES_EVIDENCE", rescue_evidence),
                    _df("F_SIMID", "SIM_ID", rescue_id),
                    _df("F_TIER", "TIER", rescue_tier),
                    _df("F_FAM", "FAMILY", rescue_family),
                    _df("F_TC", "TARGET_CLASS", target_class_value),
                    _df("F_BG", "BRANCH_GROUP", branch_group_value),
                    _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                    _df("F_PTERM", "PROBE_TERM", probe_term),
                    _df("F_GTERM", "GOAL_TERM", working_goal.term),
                    _df("F_TRACK", "BRANCH_TRACK", f"{working_goal.track}_RESCUE_SCAFFOLD_{rescue_family}_{rescue_index}"),
                    _df("F_RMODE", "RESCUE_MODE", "SCAFFOLD_ATTACHMENT"),
                    _df("F_RFAIL", "RESCUE_FAILURE_MODE", rescue_failure_mode),
                ]
                _append_rescue_lineage_fields(
                    rescue_def_fields,
                    lineage_requirements=family_slice_lineage_requirements,
                    branch_id=rescue_id,
                    parent_branch_id=sim_pos_id,
                    feedback_refs=[rescue_evidence],
                    rescue_linkage=f"SCAFFOLD::{rescue_family}::{rescue_failure_mode}::{rescue_index}",
                )
                if rescue_library_term:
                    rescue_def_fields.append(_df("F_RLIB", "RESCUE_LIBRARY_TERM", rescue_library_term))
                negative_items.append(
                    {
                        "item_class": "SPEC_HYP",
                        "id": rescue_id,
                        "kind": "SIM_SPEC",
                        "requires": rescue_requires,
                        "def_fields": rescue_def_fields,
                        "asserts": [
                            _assert("A_EVID", "EVIDENCE_TOKEN", rescue_evidence),
                            _assert("A_PROBE", "PROBE_TOKEN", probe_token_for(probe_id_for(rescue_id))),
                        ],
                        "operator_id": rescue_operator_id,
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
                lineage_requirements=family_slice_lineage_requirements,
                parent_branch_id=sim_pos_id if family_slice else "NONE",
                branch_group=branch_group_value if family_slice else "",
                branch_track="ATOMIC_TERM_BOOTSTRAP",
            )
        )

    # Batch shape: deterministic and structurally variant.
    targets = prereq_items + target_items
    alternatives = negative_items

    strategy = {
        "schema": "A1_STRATEGY_v1",
        "strategy_id": f"STRAT_QIT_ADAPTIVE_{sequence:06d}",
        "inputs": {
            "state_hash": _sha256_json(state),
            "fuel_slice_hashes": [],
            "bootpack_rules_hash": _sha256_file(Path(__file__).resolve()),
            "pinned_ruleset_sha256": None,
            "pinned_megaboot_sha256": None,
            "family_slice_id": str((family_slice or {}).get("slice_id", "") or ""),
            "family_slice_hash": _sha256_json(family_slice) if family_slice else "",
            "family_slice_run_mode": str((family_slice or {}).get("run_mode", "") or ""),
        },
        "budget": strategy_budget,
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
            "planning_mode": "family_slice_controlled" if family_slice else "compatibility_profile_scaffold",
            "debate_mode": debate_mode,
            "legacy_goal_profile_mode": not bool(family_slice),
            "family_slice_present": bool(family_slice),
            "family_slice_required_lanes": sorted(
                {str(x).strip() for x in ((family_slice or {}).get("required_lanes", []) or []) if str(x).strip()}
            ),
            "family_slice_lane_minimums": _family_slice_lane_minimums(family_slice),
            "family_slice_branch_requirements": _family_slice_branch_requirements(family_slice),
            "family_slice_lineage_requirements": list(_family_slice_lineage_requirements(family_slice)),
            "family_slice_rescue_lineage_required": bool((family_slice or {}).get("rescue_lineage_required", False)),
            "family_slice_strategy_head_terms": [
                str(x).strip()
                for x in (
                    ((family_slice or {}).get("family_admissibility_hints", {}) or {}).get("strategy_head_terms", [])
                    or []
                )
                if str(x).strip()
            ],
            "family_slice_required_negative_classes": list(_family_slice_negative_classes(family_slice or {})),
            "family_slice_math_surface_terms": sorted(
                {
                    str(term).strip()
                    for term in (((family_slice or {}).get("term_math_surfaces", {}) or {}).keys())
                    if str(term).strip()
                }
            ),
            "family_slice_declared_probe_terms": sorted(
                {
                    str(term).strip()
                    for term in ((((family_slice or {}).get("sim_hooks", {}) or {}).get("required_probe_terms", []) or []))
                    if str(term).strip()
                }
            ),
            "family_slice_required_sim_families": list(_family_slice_required_sim_families(family_slice or {})),
            "family_slice_sim_family_tiers": {
                str(family).strip().upper(): str(tier).strip().upper()
                for family, tier in ((((family_slice or {}).get("sim_hooks", {}) or {}).get("sim_family_tiers", {}) or {}).items())
                if str(family).strip() and str(tier).strip()
            },
            "family_slice_recovery_sim_families": list(_family_slice_recovery_sim_families(family_slice)),
            "family_slice_rescue_source_limit": _family_slice_rescue_source_limit(family_slice),
            "family_slice_graveyard_negative_expansion_limit": _family_slice_graveyard_negative_expansion_limit(family_slice),
            "family_slice_budget_max_items": int(strategy_budget["max_items"]) if family_slice else 0,
            "family_slice_budget_max_sims": int(strategy_budget["max_sims"]) if family_slice else 0,
            "family_slice_budget_source": strategy_budget_source if family_slice else "",
            "family_slice_term_sim_tier_terms": sorted(
                {
                    str(term).strip()
                    for term in ((((family_slice or {}).get("sim_hooks", {}) or {}).get("term_sim_tiers", {}) or {}).keys())
                    if str(term).strip()
                }
            ),
            "family_slice_target_class_prefix": _family_slice_target_class_prefix(family_slice or {}) if family_slice else "",
            "strategy_target_class": target_class_value,
            "graveyard_negative_classes_used": list(_graveyard_negative_classes_for_mode(family_slice) if debate_mode == "graveyard_first" else ()),
            "goal_term": working_goal.term,
            "goal_priority_source": goal_priority_source,
            "goal_probe_term": probe_term,
            "goal_probe_source": probe_source,
            "goal_sim_tier": sim_tier,
            "goal_negative_class": str(working_goal.negative_class).strip(),
            "sim_families_used": _sim_families_used(targets + alternatives),
            "sim_family_tier_map": _sim_family_tier_map(targets + alternatives),
            "lane_branch_counts": _lane_branch_counts(targets + alternatives),
            "lane_branch_sim_ids": _lane_branch_sim_ids(targets + alternatives),
            "branch_lineage_fields_used": _branch_lineage_fields_used(targets + alternatives),
            "branch_parentage_map": _non_rescue_branch_parentage_map(targets + alternatives),
            "branch_group_map": _branch_group_map(targets + alternatives),
            "branch_groups_used": _branch_groups_used(targets + alternatives),
            "branch_track_map": _branch_track_map(targets + alternatives),
            "branch_tracks_used": _branch_tracks_used(targets + alternatives),
            "root_branch_ids": _non_rescue_root_branch_ids(targets + alternatives),
            "branch_child_counts": _non_rescue_branch_child_counts(targets + alternatives),
            "rescue_sim_families_used": _rescue_sim_families_used(targets + alternatives),
            "rescue_source_count": _rescue_source_count(targets + alternatives),
            "rescue_linkages_used": _rescue_linkages_used(targets + alternatives),
            "rescue_lineage_fields_used": _rescue_lineage_fields_used(targets + alternatives),
            "sim_family_operator_map": _sim_family_operator_map(targets + alternatives),
            "operator_policy_sources": [
                "ENUM_REGISTRY_v1",
                "A1_REPAIR_OPERATOR_MAPPING_v1",
            ],
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
        "--family-slice-json",
        default=None,
        help="Optional bounded A2-derived family-slice JSON. When present, it outranks goal-profile selection.",
    )
    parser.add_argument(
        "--goal-profile",
        choices=["core", "extended", "physics", "toolkit", "refined_fuel", "entropy_bridge", "entropy_bookkeeping_bridge"],
        default="core",
    )
    parser.add_argument(
        "--allow-legacy-goal-profile-mode",
        action="store_true",
        help="Compatibility override for hardcoded profile-ladder planning. Without this override, --family-slice-json is required.",
    )
    parser.add_argument("--goal-selection", choices=["interleaved", "closure_first"], default="interleaved")
    parser.add_argument("--debate-mode", choices=["balanced", "graveyard_first", "graveyard_recovery"], default="balanced")
    args = parser.parse_args()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    state = _load_state_json(Path(args.state_json))
    family_slice = None
    resolved_debate_mode = str(args.debate_mode)

    if args.family_slice_json and str(args.family_slice_json).strip():
        family_slice = _load_family_slice(Path(str(args.family_slice_json)).expanduser().resolve())
        goals = _goals_from_family_slice(family_slice)
        resolved_debate_mode = _resolve_debate_mode_from_family_slice(family_slice, resolved_debate_mode)
    else:
        if not bool(args.allow_legacy_goal_profile_mode):
            raise SystemExit("family_slice_json_required_unless_allow_legacy_goal_profile_mode")
        goals = _compatibility_goals_for_profile(str(args.goal_profile))
    strategy = build_strategy_from_state(
        state=state,
        run_id=str(args.run_id),
        sequence=int(args.sequence),
        goals=goals,
        goal_selection=str(args.goal_selection),
        debate_mode=resolved_debate_mode,
        family_slice=family_slice,
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

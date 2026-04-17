#!/usr/bin/env python3
"""
Shared fail-closed contract checks for the current Axis 0 bridge handoff seam.
"""

from __future__ import annotations

from collections.abc import Mapping


EXPECTED_BRIDGE_OWNER_ALIGNMENT = {
    "status": "axis_internal_candidate_not_final_owner_law",
    "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
    "owner_dependency": "must_bind_under_xi_hist_signed_law",
    "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
    "winner": "Xi_chiral_entangle",
    "runner_up": "Xi_chiral_hist_entangle",
}

EXPECTED_SIGNED_BRIDGE_HANDOFF = {
    "candidate": "Xi_chiral_entangle",
    "status": "provisional_handoff_ready",
    "placement_contract": "downstream_axis_internal_bridge_candidate_only",
    "owner_dependency": "must_bind_under_xi_hist_signed_law",
    "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
    "consumer_status": "allowed_for_entropy_readout_not_final_owner_xi",
}

EXPECTED_NON_OWNER_RESERVATION = {
    "status": "explicit_non_owner_reservation",
    "final_xi_owner_law": "reserved_for_future_owner_doctrine_not_claimed_by_c1",
    "shell_doctrine": "reserved_for_future_shell_doctrine_not_claimed_by_c1",
    "history_law_replacement": "reserved_for_future_history_law_replacement_not_claimed_by_c1",
    "entropy_family_owner_doctrine": "reserved_for_future_entropy_owner_doctrine_not_claimed_by_c1",
    "owner_dependency": "must_bind_under_xi_hist_signed_law",
    "consumer_scope": "downstream_readout_only",
}

EXPECTED_OWNER_READ = {
    "status": "admitted_executable_candidate_not_final_owner_law",
}

EXPECTED_AXIS_INTERNAL_READOUT = {
    "I_c_A_to_B": "readout",
    "S_A_given_B": "readout",
    "Xi_chiral_entangle": "current_bridge_candidate",
    "Xi_chiral_entangle_relation": "downstream_of_xi_hist_signed_law_not_alternate_owner_law",
}

CURRENT_BRIDGE_GATE_NAME = "E10_current_bridge_candidate_is_explicit_and_provisional"
CURRENT_BRIDGE_OBJECT_STATUS = "admitted_bridge_object_for_downstream_readout_not_final_owner_law"


def _matches(payload: Mapping[str, object], expected: Mapping[str, object]) -> bool:
    return all(payload.get(key) == value for key, value in expected.items())


def bridge_owner_alignment_ok(bridge_alignment: Mapping[str, object]) -> bool:
    return bool(bridge_alignment.get("pass") and _matches(bridge_alignment, EXPECTED_BRIDGE_OWNER_ALIGNMENT))


def signed_bridge_handoff_ok(handoff: Mapping[str, object]) -> bool:
    return _matches(handoff, EXPECTED_SIGNED_BRIDGE_HANDOFF)


def build_signed_bridge_handoff(
    *,
    bridge_owner_alignment: Mapping[str, object] | None = None,
    extra_fields: Mapping[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = dict(EXPECTED_SIGNED_BRIDGE_HANDOFF)
    if bridge_owner_alignment is not None:
        payload["bridge_owner_alignment"] = dict(bridge_owner_alignment)
    if extra_fields:
        overlap = set(EXPECTED_SIGNED_BRIDGE_HANDOFF).intersection(extra_fields)
        if overlap:
            raise ValueError(f"extra_fields may not override canonical handoff keys: {sorted(overlap)}")
        payload.update(dict(extra_fields))
    return payload


def non_owner_reservation_ok(payload: Mapping[str, object]) -> bool:
    return _matches(payload, EXPECTED_NON_OWNER_RESERVATION)


def build_non_owner_reservation(
    extra_fields: Mapping[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = dict(EXPECTED_NON_OWNER_RESERVATION)
    if extra_fields:
        overlap = set(EXPECTED_NON_OWNER_RESERVATION).intersection(extra_fields)
        if overlap:
            raise ValueError(f"extra_fields may not override canonical reservation keys: {sorted(overlap)}")
        payload.update(dict(extra_fields))
    return payload


def owner_read_ok(payload: Mapping[str, object]) -> bool:
    return _matches(payload, EXPECTED_OWNER_READ)


def build_owner_read(*, note: str, extra_fields: Mapping[str, object] | None = None) -> dict[str, object]:
    payload: dict[str, object] = dict(EXPECTED_OWNER_READ)
    if extra_fields:
        overlap = set(EXPECTED_OWNER_READ).intersection(extra_fields)
        if overlap:
            raise ValueError(f"extra_fields may not override canonical owner_read keys: {sorted(overlap)}")
        payload.update(dict(extra_fields))
    payload["note"] = note
    return payload


def axis_internal_readout_ok(payload: Mapping[str, object]) -> bool:
    return _matches(payload, EXPECTED_AXIS_INTERNAL_READOUT)


def axis_internal_candidate_status() -> str:
    return str(EXPECTED_BRIDGE_OWNER_ALIGNMENT["status"])


def axis_internal_candidate_relation() -> str:
    return str(EXPECTED_AXIS_INTERNAL_READOUT["Xi_chiral_entangle_relation"])


def axis_internal_candidate_placement() -> str:
    return str(EXPECTED_BRIDGE_OWNER_ALIGNMENT["placement_relation"])


def axis_internal_mapping_ok(
    mapping: Mapping[str, object],
    *,
    candidate: str = "Xi_chiral_entangle",
) -> bool:
    return mapping.get(candidate) == axis_internal_candidate_status()


def axis_internal_placement_ok(
    placement_relations: Mapping[str, object],
    *,
    candidate: str = "Xi_chiral_entangle",
) -> bool:
    return placement_relations.get(candidate) == axis_internal_candidate_placement()


def build_axis_internal_readout(
    extra_fields: Mapping[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = dict(EXPECTED_AXIS_INTERNAL_READOUT)
    if extra_fields:
        overlap = set(EXPECTED_AXIS_INTERNAL_READOUT).intersection(extra_fields)
        if overlap:
            raise ValueError(f"extra_fields may not override canonical axis_internal_readout keys: {sorted(overlap)}")
        payload.update(dict(extra_fields))
    return payload


def current_bridge_gate_status() -> str:
    return EXPECTED_OWNER_READ["status"]


def current_bridge_gate_name() -> str:
    return CURRENT_BRIDGE_GATE_NAME


def current_bridge_object_status() -> str:
    return CURRENT_BRIDGE_OBJECT_STATUS


def c1_signed_bridge_handoff_read() -> str:
    return (
        "Xi_chiral_entangle remains the current downstream signed bridge candidate handoff "
        "for readout use, but it is not a final owner law."
    )


def c1_bridge_object_read() -> str:
    return (
        "Xi_chiral_entangle is the current admitted bridge object for downstream readout use. "
        "It is not a final Xi owner law, shell doctrine, history-law replacement, or "
        "entropy-family owner doctrine."
    )


def c1_signed_candidate_owner_note() -> str:
    return (
        "This C1 surface packages the current signed bridge candidate without replacing "
        "xi_hist signed law or promoting Xi_chiral_entangle to final owner doctrine."
    )

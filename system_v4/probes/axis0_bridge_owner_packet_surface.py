#!/usr/bin/env python3
"""
Shared fail-closed loader for the Axis 0 bridge-owner packet surface.

This keeps the lower-ladder C1/pre-entropy/entropy/stack owner-contract seam
as one reusable surface so higher-level lambda/cosmology witnesses can depend
on the same packet doctrine instead of reconstructing it ad hoc.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from axis0_bridge_owner_alignment_contract import (
    axis_internal_candidate_placement,
    axis_internal_candidate_relation,
    axis_internal_candidate_status,
    bridge_owner_alignment_ok,
    current_bridge_gate_name,
    current_bridge_gate_status,
    current_bridge_object_status,
    non_owner_reservation_ok,
    owner_read_ok,
    signed_bridge_handoff_ok,
)

DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"

_C1S3 = "C1S3_support_chain_is_closed_before_candidate_packaging"
_C1S4 = "C1S4_candidate_stays_provisional_and_does_not_overpromote"
_C1B1 = "C1B1_bridge_object_is_explicit_and_downstream_only"
_C1B3 = "C1B3_bridge_object_is_bound_to_the_existing_support_contract"
_C1B4 = "C1B4_bridge_object_keeps_owner_doctrine_questions_open"
_P22 = "P22_c1_signed_bridge_candidate_is_explicit_and_provisional"
_P23 = "P23_xi_chiral_entangle_remains_downstream_of_xi_hist_signed_law"
_P24 = "P24_carrier_handoff_matches_pre_entropy_downstream_mapping"
_P25 = "P25_standalone_c1_bridge_object_matches_pre_entropy_contract"
_S5 = "S5_axis0_ladder_is_mechanically_traversable"
_S6 = "S6_xi_chiral_entangle_remains_axis_internal_and_not_owner_law"
_S7 = "S7_axis0_stack_explicitly_consumes_named_contract_gates"
_S9 = "S9_axis0_stack_consumes_standalone_c1_bridge_object_contract"


def _artifact_paths(root: Path) -> dict[str, Path]:
    return {
        "c1_signed_result": root / "c1_signed_bridge_candidate_search_results.json",
        "c1_signed_validation": root / "c1_signed_bridge_candidate_search_validation.json",
        "c1_bridge_result": root / "c1_bridge_object_packet_results.json",
        "c1_bridge_validation": root / "c1_bridge_object_packet_validation.json",
        "pre_entropy_validation": root / "pre_entropy_packet_validation.json",
        "entropy_validation": root / "entropy_readout_packet_validation.json",
        "stack_validation": root / "axis0_stack_packet_validation.json",
    }


def _refresh_artifact(name: str) -> None:
    script_map = {
        "c1_signed_result": "sim_c1_signed_bridge_candidate_search.py",
        "c1_signed_validation": "validate_c1_signed_bridge_candidate_search.py",
        "c1_bridge_result": "sim_c1_bridge_object_packet.py",
        "c1_bridge_validation": "validate_c1_bridge_object_packet.py",
        "pre_entropy_validation": "validate_pre_entropy_packet.py",
        "entropy_validation": "validate_entropy_readout_packet.py",
        "stack_validation": "validate_axis0_stack_packet.py",
    }
    script_name = script_map.get(name)
    if script_name is None:
        raise KeyError(f"Unknown bridge-owner artifact: {name}")
    script_path = Path(__file__).resolve().parent / script_name
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(script_path.parent),
    )
    if proc.returncode != 0:
        detail = (proc.stdout + "\n" + proc.stderr).strip()
        raise RuntimeError(
            f"Refresh for bridge-owner artifact {name} failed with code {proc.returncode}\n{detail}"
        )


def ensure_bridge_owner_packet_artifacts(results_dir: str | Path | None = None) -> list[str]:
    root = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    allow_refresh = root.resolve() == DEFAULT_RESULTS_DIR.resolve()
    refreshed: list[str] = []
    for name, path in _artifact_paths(root).items():
        if path.exists():
            continue
        if not allow_refresh:
            raise FileNotFoundError(f"Bridge-owner artifact missing: {path}")
        _refresh_artifact(name)
        if not path.exists():
            raise FileNotFoundError(f"Bridge-owner artifact still missing after refresh: {path}")
        refreshed.append(name)
    return refreshed


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate_map(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(item["name"]): dict(item)
        for item in payload.get("gates", [])
    }


def _gate_pass(gate_map: dict[str, dict[str, object]], name: str) -> bool:
    return bool(gate_map.get(name, {}).get("pass"))


def load_bridge_owner_packet_surface(results_dir: str | Path | None = None) -> dict[str, object]:
    root = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    refreshed = ensure_bridge_owner_packet_artifacts(root)
    paths = _artifact_paths(root)

    c1_signed_result = _load_json(paths["c1_signed_result"])
    c1_signed_validation = _load_json(paths["c1_signed_validation"])
    c1_bridge_result = _load_json(paths["c1_bridge_result"])
    c1_bridge_validation = _load_json(paths["c1_bridge_validation"])
    pre_entropy_validation = _load_json(paths["pre_entropy_validation"])
    entropy_validation = _load_json(paths["entropy_validation"])
    stack_validation = _load_json(paths["stack_validation"])

    c1_signed_gate_map = _gate_map(c1_signed_validation)
    c1_bridge_gate_map = _gate_map(c1_bridge_validation)
    pre_entropy_gate_map = _gate_map(pre_entropy_validation)
    entropy_gate_map = _gate_map(entropy_validation)
    stack_gate_map = _gate_map(stack_validation)

    search_support = dict(c1_signed_result["support_chain"])
    search_handoff = dict(c1_signed_result["downstream_handoff"])
    search_unresolved = dict(c1_signed_result["unresolved"])
    owner_read = dict(c1_signed_result["owner_read"])

    bridge_object = dict(c1_bridge_result["bridge_object"])
    bridge_support = dict(c1_bridge_result["support_contract"])
    bridge_alignment = dict(bridge_support["bridge_owner_alignment"])
    bridge_handoff = dict(bridge_support["carrier_handoff"])
    bridge_non_claims = dict(c1_bridge_result["non_claims"])

    pass_flag = bool(
        bridge_owner_alignment_ok(bridge_alignment)
        and signed_bridge_handoff_ok(search_handoff)
        and signed_bridge_handoff_ok(bridge_handoff)
        and non_owner_reservation_ok(search_unresolved)
        and non_owner_reservation_ok(bridge_non_claims)
        and owner_read_ok(owner_read)
        and bridge_support.get("carrier_selection_handoff_matches_search")
        and bridge_object.get("status") == current_bridge_object_status()
        and search_support.get("pre_entropy_mapping") == axis_internal_candidate_status()
        and search_support.get("pre_entropy_relation") == axis_internal_candidate_relation()
        and search_support.get("pre_entropy_placement") == axis_internal_candidate_placement()
        and search_support.get("entropy_readout_current_bridge_gate") == current_bridge_gate_name()
        and bridge_support.get("pre_entropy_mapping") == axis_internal_candidate_status()
        and bridge_support.get("pre_entropy_relation") == axis_internal_candidate_relation()
        and bridge_support.get("pre_entropy_placement") == axis_internal_candidate_placement()
        and bridge_support.get("entropy_gate_name") == current_bridge_gate_name()
        and bridge_support.get("entropy_gate_status") == current_bridge_gate_status()
        and _gate_pass(c1_signed_gate_map, _C1S3)
        and _gate_pass(c1_signed_gate_map, _C1S4)
        and _gate_pass(c1_bridge_gate_map, _C1B1)
        and _gate_pass(c1_bridge_gate_map, _C1B3)
        and _gate_pass(c1_bridge_gate_map, _C1B4)
        and _gate_pass(pre_entropy_gate_map, _P22)
        and _gate_pass(pre_entropy_gate_map, _P23)
        and _gate_pass(pre_entropy_gate_map, _P24)
        and _gate_pass(pre_entropy_gate_map, _P25)
        and _gate_pass(entropy_gate_map, current_bridge_gate_name())
        and _gate_pass(stack_gate_map, _S5)
        and _gate_pass(stack_gate_map, _S6)
        and _gate_pass(stack_gate_map, _S7)
        and _gate_pass(stack_gate_map, _S9)
    )

    return {
        "pass": pass_flag,
        "current_bridge_gate": current_bridge_gate_name(),
        "current_bridge_status": current_bridge_gate_status(),
        "current_bridge_object_status": current_bridge_object_status(),
        "bridge_owner_alignment_pass": bool(bridge_owner_alignment_ok(bridge_alignment)),
        "search_handoff_pass": bool(signed_bridge_handoff_ok(search_handoff)),
        "bridge_handoff_pass": bool(signed_bridge_handoff_ok(bridge_handoff)),
        "search_reservation_pass": bool(non_owner_reservation_ok(search_unresolved)),
        "bridge_reservation_pass": bool(non_owner_reservation_ok(bridge_non_claims)),
        "owner_read_pass": bool(owner_read_ok(owner_read)),
        "carrier_selection_handoff_matches_search": bool(
            bridge_support.get("carrier_selection_handoff_matches_search")
        ),
        "search_surface": {
            "pre_entropy_mapping": search_support.get("pre_entropy_mapping"),
            "pre_entropy_relation": search_support.get("pre_entropy_relation"),
            "pre_entropy_placement": search_support.get("pre_entropy_placement"),
            "entropy_readout_current_bridge_gate": search_support.get("entropy_readout_current_bridge_gate"),
        },
        "bridge_surface": {
            "pre_entropy_mapping": bridge_support.get("pre_entropy_mapping"),
            "pre_entropy_relation": bridge_support.get("pre_entropy_relation"),
            "pre_entropy_placement": bridge_support.get("pre_entropy_placement"),
            "entropy_gate_name": bridge_support.get("entropy_gate_name"),
            "entropy_gate_status": bridge_support.get("entropy_gate_status"),
        },
        "gate_passes": {
            _C1S3: _gate_pass(c1_signed_gate_map, _C1S3),
            _C1S4: _gate_pass(c1_signed_gate_map, _C1S4),
            _C1B1: _gate_pass(c1_bridge_gate_map, _C1B1),
            _C1B3: _gate_pass(c1_bridge_gate_map, _C1B3),
            _C1B4: _gate_pass(c1_bridge_gate_map, _C1B4),
            _P22: _gate_pass(pre_entropy_gate_map, _P22),
            _P23: _gate_pass(pre_entropy_gate_map, _P23),
            _P24: _gate_pass(pre_entropy_gate_map, _P24),
            _P25: _gate_pass(pre_entropy_gate_map, _P25),
            current_bridge_gate_name(): _gate_pass(entropy_gate_map, current_bridge_gate_name()),
            _S5: _gate_pass(stack_gate_map, _S5),
            _S6: _gate_pass(stack_gate_map, _S6),
            _S7: _gate_pass(stack_gate_map, _S7),
            _S9: _gate_pass(stack_gate_map, _S9),
        },
        "row_source": "packet_results",
        "refreshed_missing_artifacts": refreshed,
    }

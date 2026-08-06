"""Finite paired whole-extension fixture validation.

This is a controller-side nominalist reference for one L1 candidate carrier.
It operates on explicit finite supports, relations, and records only.  The
result is a scratch diagnostic; it does not select a physical manifold or an
engine semantics.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .intake import canonical_json, parse_json_object


FIXTURE_SCHEMA = "constraintbox.paired-whole-extension-fixture.v1"
RECEIPT_SCHEMA = "constraintbox.paired-whole-extension-validation.v1"


class PairedExtensionError(ValueError):
    """Raised when a paired-extension fixture is not a finite typed object."""


def _exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PairedExtensionError(f"{path} must be an object")
    actual = set(value)
    if actual != expected:
        raise PairedExtensionError(
            f"{path} fields differ: missing={sorted(expected - actual)!r}, "
            f"extra={sorted(actual - expected)!r}"
        )
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PairedExtensionError(f"{path} must be non-empty text")
    return value


def _int_list(value: Any, path: str) -> list[int]:
    if not isinstance(value, list) or any(
        isinstance(item, bool) or not isinstance(item, int) for item in value
    ):
        raise PairedExtensionError(f"{path} must be an integer array")
    if value != sorted(value) or len(set(value)) != len(value):
        raise PairedExtensionError(f"{path} must be sorted and unique")
    return list(value)


def _text_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise PairedExtensionError(f"{path} must be a non-empty-text array")
    if value != sorted(value) or len(set(value)) != len(value):
        raise PairedExtensionError(f"{path} must be sorted and unique")
    return list(value)


def _ordered_text_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise PairedExtensionError(f"{path} must be a non-empty-text array")
    if len(set(value)) != len(value):
        raise PairedExtensionError(f"{path} must be unique")
    return list(value)


def _metric(value: float) -> str:
    return f"{value:.12f}"


def _capacity_gain(after: int, before: int) -> str:
    if after <= 0 or before <= 0:
        raise PairedExtensionError("capacity counts must be positive")
    return _metric(math.log2(after) - math.log2(before))


def build_observation(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate one fixture and return its canonical finite observation."""

    root = _exact_keys(
        payload,
        {
            "schema",
            "fixture_id",
            "claim_ceiling",
            "promotion_allowed",
            "carrier",
            "whole",
            "demands",
            "controls",
            "mss_candidates",
            "probes",
        },
        "$",
    )
    if root["schema"] != FIXTURE_SCHEMA:
        raise PairedExtensionError("unsupported paired-extension fixture schema")
    fixture_id = _text(root["fixture_id"], "$.fixture_id")
    claim_ceiling = _text(root["claim_ceiling"], "$.claim_ceiling")
    if root["promotion_allowed"] is not False:
        raise PairedExtensionError("$.promotion_allowed must be false")

    carrier = _exact_keys(
        root["carrier"],
        {
            "ambient_support",
            "settled_support",
            "newly_opened",
            "binding_admits",
            "history_words",
        },
        "$.carrier",
    )
    ambient = set(_int_list(carrier["ambient_support"], "$.carrier.ambient_support"))
    settled = set(_int_list(carrier["settled_support"], "$.carrier.settled_support"))
    newly_opened = set(_int_list(carrier["newly_opened"], "$.carrier.newly_opened"))
    binding_admits = set(_int_list(carrier["binding_admits"], "$.carrier.binding_admits"))
    if not ambient or not settled or not newly_opened or not binding_admits:
        raise PairedExtensionError("carrier supports must be non-empty")
    if not settled <= ambient or not newly_opened <= ambient or not binding_admits <= ambient:
        raise PairedExtensionError("carrier supports must lie inside ambient_support")
    history_words = _exact_keys(
        carrier["history_words"], {"ob", "bo"}, "$.carrier.history_words"
    )
    if history_words != {"ob": ["open", "bind"], "bo": ["bind", "open"]}:
        raise PairedExtensionError("history_words must declare open-bind and bind-open")

    whole = _exact_keys(
        root["whole"],
        {"completion_ids", "extension_by_history", "extension_after_history_deletion"},
        "$.whole",
    )
    completion_ids = set(_text_list(whole["completion_ids"], "$.whole.completion_ids"))
    extension_by_history = _exact_keys(
        whole["extension_by_history"], {"ob", "bo"}, "$.whole.extension_by_history"
    )
    extension_after_deletion = _exact_keys(
        whole["extension_after_history_deletion"],
        {"ob", "bo"},
        "$.whole.extension_after_history_deletion",
    )
    extensions: dict[str, list[str]] = {}
    deleted_extensions: dict[str, list[str]] = {}
    for label, values in extension_by_history.items():
        extensions[label] = _text_list(values, f"$.whole.extension_by_history.{label}")
        if not set(extensions[label]) <= completion_ids:
            raise PairedExtensionError("extension ids must be declared in completion_ids")
    for label, values in extension_after_deletion.items():
        deleted_extensions[label] = _text_list(
            values, f"$.whole.extension_after_history_deletion.{label}"
        )
        if not set(deleted_extensions[label]) <= completion_ids:
            raise PairedExtensionError("deleted extension ids must be declared")

    demands = _exact_keys(root["demands"], {"order_scar", "future_extension"}, "$.demands")
    demanded_scar = _int_list(demands["order_scar"], "$.demands.order_scar")
    demanded_future = _text_list(demands["future_extension"], "$.demands.future_extension")

    controls = _exact_keys(
        root["controls"],
        {"no_opening_scar", "no_binding_scar", "relabel_map", "reversal"},
        "$.controls",
    )
    expected_no_open = _int_list(controls["no_opening_scar"], "$.controls.no_opening_scar")
    expected_no_bind = _int_list(controls["no_binding_scar"], "$.controls.no_binding_scar")
    relabel_raw = _exact_keys(
        controls["relabel_map"], {str(value) for value in sorted(ambient)}, "$.controls.relabel_map"
    )
    relabel = {int(key): value for key, value in relabel_raw.items()}
    if set(relabel) != ambient or set(relabel.values()) != ambient:
        raise PairedExtensionError("relabel_map must be a permutation of ambient_support")
    reversal = _exact_keys(controls["reversal"], {"ob", "bo"}, "$.controls.reversal")
    if reversal != {"ob": "bo", "bo": "ob"}:
        raise PairedExtensionError("reversal must swap ob and bo")

    mss_candidates = _exact_keys(
        root["mss_candidates"],
        {"weak_no_binding", "minimal_exclude_scar", "strong_exclude_scar_and_extra"},
        "$.mss_candidates",
    )
    candidate_sets = {
        name: set(_int_list(values, f"$.mss_candidates.{name}"))
        for name, values in mss_candidates.items()
    }
    if any(not values <= ambient for values in candidate_sets.values()):
        raise PairedExtensionError("MSS candidates must lie inside ambient_support")
    probes = _ordered_text_list(root["probes"], "$.probes")

    opened = settled | newly_opened
    open_then_bind = opened & binding_admits
    bind_then_open = (settled & binding_admits) | newly_opened
    order_scar = sorted(bind_then_open - open_then_bind)
    no_open_scar = sorted(
        ((settled & binding_admits) | set()) - (settled & binding_admits)
    )
    no_bind_scar = sorted(opened - opened)
    relabel_scar = sorted(relabel[value] for value in order_scar)
    extension_difference = sorted(set(extensions["bo"]) - set(extensions["ob"]))
    deleted_difference = sorted(
        set(deleted_extensions["bo"]) - set(deleted_extensions["ob"])
    )
    reversed_scar_by_history = {"ob": [], "bo": []}
    reversed_scar_by_history[reversal["bo"]] = order_scar
    reversed_scar_by_history[reversal["ob"]] = []

    mss_rows: list[dict[str, Any]] = []
    for name, admitted in candidate_sets.items():
        result = opened & admitted
        sufficient = set(demanded_scar).isdisjoint(result) and settled <= result
        mss_rows.append(
            {
                "candidate": name,
                "result": sorted(result),
                "sufficient": sufficient,
                "binding_cost_bits": _capacity_gain(len(opened), len(result)),
            }
        )
    sufficient_rows = [row for row in mss_rows if row["sufficient"]]
    least_cost = min(float(row["binding_cost_bits"]) for row in sufficient_rows)
    mss_frontier = sorted(
        str(row["candidate"])
        for row in sufficient_rows
        if math.isclose(float(row["binding_cost_bits"]), least_cost, abs_tol=1e-12)
    )

    tests = {
        "finite_nonempty_supports": all(
            0 < len(values) for values in (ambient, settled, newly_opened, opened, open_then_bind, bind_then_open)
        ),
        "strict_raw_growth": len(opened) > len(settled),
        "orders_differ": open_then_bind != bind_then_open,
        "scar_exact": order_scar == demanded_scar == [3],
        "future_extension_changes": extension_difference == demanded_future,
        "history_deletion_collapses": deleted_difference == [],
        "relabel_preserves_structure": len(relabel_scar) == len(order_scar),
        "reversal_moves_scar": reversed_scar_by_history == {"ob": order_scar, "bo": []},
        "delete_opening_removes_scar": no_open_scar == expected_no_open == [],
        "delete_binding_removes_scar": no_bind_scar == expected_no_bind == [],
        "minimal_sufficient_frontier": mss_frontier == ["minimal_exclude_scar"],
        "history_is_load_bearing": extension_difference and deleted_difference == [],
    }

    observation = {
        "fixture_id": fixture_id,
        "probes": probes,
        "opened": sorted(opened),
        "open_then_bind": sorted(open_then_bind),
        "bind_then_open": sorted(bind_then_open),
        "order_scar": order_scar,
        "extension_ob": extensions["ob"],
        "extension_bo": extensions["bo"],
        "extension_difference": extension_difference,
        "extension_difference_after_history_deletion": deleted_difference,
        "no_opening_scar": no_open_scar,
        "no_binding_scar": no_bind_scar,
        "relabel_scar": relabel_scar,
        "reversal_order_scar_by_history": reversed_scar_by_history,
        "mss_frontier": mss_frontier,
        "mss_rows": mss_rows,
        "raw_opening_gain_bits": _capacity_gain(len(opened), len(settled)),
        "binding_cost_bits": _capacity_gain(len(opened), len(open_then_bind)),
        "net_settled_gain_bits": _capacity_gain(len(open_then_bind), len(settled)),
        "history_is_load_bearing": bool(tests["history_is_load_bearing"]),
    }
    observation["all_tests_passed"] = all(bool(value) for value in tests.values())
    return {"observation": observation, "tests": tests, "claim_ceiling": claim_ceiling}


def validate_paired_fixture(payload: dict[str, Any]) -> dict[str, Any]:
    built = build_observation(payload)
    return {
        "schema": RECEIPT_SCHEMA,
        "fixture_id": payload["fixture_id"],
        "status": "PASS" if built["observation"]["all_tests_passed"] else "FAIL",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": built["claim_ceiling"],
        "checks": built["tests"],
        "canonical_observation": built["observation"],
    }


def validate_paired_fixture_file(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve(strict=True)
    payload = parse_json_object(path.read_bytes())
    receipt = validate_paired_fixture(payload)
    receipt["source_path"] = str(path)
    receipt["source_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt["input_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return receipt

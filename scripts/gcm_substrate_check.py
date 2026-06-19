#!/usr/bin/env python3
"""Shared substrate-consumption check for GCM nested packets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_REGISTRY_BODY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_3Q_REGISTRY_BODY_SHA256 = "623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0"
EXPECTED_4Q_REGISTRY_BODY_SHA256 = "bf92c850a2880e26011080c900879cf729f8394ffc2e5d00bf1f70ed786020de"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _collect_known_ids(registry: dict[str, Any]) -> dict[str, set[str]]:
    frozen = registry.get("frozen_registry", {})
    known = {
        "survivor_ids": {row.get("survivor_id") for row in frozen.get("survivors", []) if row.get("survivor_id")},
        "quotient_class_ids": {
            row.get("quotient_class_id") for row in frozen.get("quotient_classes", []) if row.get("quotient_class_id")
        },
        "candidate_region_ids": {
            row.get("candidate_region_id") for row in frozen.get("candidate_regions", []) if row.get("candidate_region_id")
        },
        "gcm_2q_survivor_ids": set(),
        "gcm_2q_quotient_class_ids": set(),
        "gcm_2q_candidate_region_ids": set(),
        "gcm_3q_survivor_ids": set(),
        "gcm_3q_quotient_class_ids": set(),
        "gcm_3q_candidate_region_ids": set(),
        "gcm_4q_survivor_ids": set(),
        "gcm_4q_quotient_class_ids": set(),
        "gcm_4q_candidate_region_ids": set(),
    }
    frozen_2q = registry.get("frozen_2q_registry", {})
    known["gcm_2q_survivor_ids"] = {
        row.get("gcm_2q_survivor_id") for row in frozen_2q.get("survivors", []) if row.get("gcm_2q_survivor_id")
    }
    known["gcm_2q_quotient_class_ids"] = {
        row.get("gcm_2q_quotient_class_id")
        for row in frozen_2q.get("quotient_classes", [])
        if row.get("gcm_2q_quotient_class_id")
    }
    known["gcm_2q_candidate_region_ids"] = {
        row.get("gcm_2q_candidate_region_id")
        for row in frozen_2q.get("candidate_regions", [])
        if row.get("gcm_2q_candidate_region_id")
    }
    frozen_3q = registry.get("frozen_3q_registry", {})
    known["gcm_3q_survivor_ids"] = {
        row.get("gcm_3q_survivor_id") for row in frozen_3q.get("survivors", []) if row.get("gcm_3q_survivor_id")
    }
    known["gcm_3q_quotient_class_ids"] = {
        row.get("gcm_3q_quotient_class_id")
        for row in frozen_3q.get("quotient_classes", [])
        if row.get("gcm_3q_quotient_class_id")
    }
    known["gcm_3q_candidate_region_ids"] = {
        row.get("gcm_3q_candidate_region_id")
        for row in frozen_3q.get("candidate_regions", [])
        if row.get("gcm_3q_candidate_region_id")
    }
    frozen_4q = registry.get("frozen_4q_registry", {})
    known["gcm_4q_survivor_ids"] = {
        row.get("gcm_4q_survivor_id") for row in frozen_4q.get("survivors", []) if row.get("gcm_4q_survivor_id")
    }
    known["gcm_4q_quotient_class_ids"] = {
        row.get("gcm_4q_quotient_class_id")
        for row in frozen_4q.get("quotient_classes", [])
        if row.get("gcm_4q_quotient_class_id")
    }
    known["gcm_4q_candidate_region_ids"] = {
        row.get("gcm_4q_candidate_region_id")
        for row in frozen_4q.get("candidate_regions", [])
        if row.get("gcm_4q_candidate_region_id")
    }
    return known


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _iter_cited_ids(payload: dict[str, Any]) -> dict[str, list[str]]:
    lineage = payload.get("gcm_lineage") if isinstance(payload.get("gcm_lineage"), dict) else payload
    cited = {
        "survivor_ids": _string_list(lineage.get("survivor_ids")),
        "quotient_class_ids": _string_list(lineage.get("quotient_class_ids")),
        "candidate_region_ids": _string_list(lineage.get("candidate_region_ids")) + _string_list(lineage.get("region_ids")),
        "gcm_2q_survivor_ids": _string_list(lineage.get("gcm_2q_survivor_ids")),
        "gcm_2q_quotient_class_ids": _string_list(lineage.get("gcm_2q_quotient_class_ids")),
        "gcm_2q_candidate_region_ids": _string_list(lineage.get("gcm_2q_candidate_region_ids"))
        + _string_list(lineage.get("gcm_2q_region_ids")),
        "gcm_3q_survivor_ids": _string_list(lineage.get("gcm_3q_survivor_ids")),
        "gcm_3q_quotient_class_ids": _string_list(lineage.get("gcm_3q_quotient_class_ids")),
        "gcm_3q_candidate_region_ids": _string_list(lineage.get("gcm_3q_candidate_region_ids"))
        + _string_list(lineage.get("gcm_3q_region_ids")),
        "gcm_4q_survivor_ids": _string_list(lineage.get("gcm_4q_survivor_ids")),
        "gcm_4q_quotient_class_ids": _string_list(lineage.get("gcm_4q_quotient_class_ids")),
        "gcm_4q_candidate_region_ids": _string_list(lineage.get("gcm_4q_candidate_region_ids"))
        + _string_list(lineage.get("gcm_4q_region_ids")),
    }
    object_maps = lineage.get("object_maps", [])
    if isinstance(object_maps, list):
        for row in object_maps:
            if not isinstance(row, dict):
                continue
            for singular, plural in (
                ("survivor_id", "survivor_ids"),
                ("quotient_class_id", "quotient_class_ids"),
                ("candidate_region_id", "candidate_region_ids"),
                ("region_id", "candidate_region_ids"),
                ("gcm_2q_survivor_id", "gcm_2q_survivor_ids"),
                ("gcm_2q_quotient_class_id", "gcm_2q_quotient_class_ids"),
                ("gcm_2q_candidate_region_id", "gcm_2q_candidate_region_ids"),
                ("gcm_2q_region_id", "gcm_2q_candidate_region_ids"),
                ("gcm_3q_survivor_id", "gcm_3q_survivor_ids"),
                ("gcm_3q_quotient_class_id", "gcm_3q_quotient_class_ids"),
                ("gcm_3q_candidate_region_id", "gcm_3q_candidate_region_ids"),
                ("gcm_3q_region_id", "gcm_3q_candidate_region_ids"),
                ("gcm_4q_survivor_id", "gcm_4q_survivor_ids"),
                ("gcm_4q_quotient_class_id", "gcm_4q_quotient_class_ids"),
                ("gcm_4q_candidate_region_id", "gcm_4q_candidate_region_ids"),
                ("gcm_4q_region_id", "gcm_4q_candidate_region_ids"),
            ):
                value = row.get(singular)
                if isinstance(value, str):
                    cited[plural].append(value)
                elif isinstance(value, list):
                    cited[plural].extend(item for item in value if isinstance(item, str))
    return cited


def gcm_substrate_check(payload: dict[str, Any], registry_path: str | Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    """Validate that a nested payload consumes the current frozen GCM object.

    The payload may put lineage fields at top level or under ``gcm_lineage``. The
    required object identity is ``gcm_object_id``. The payload must cite the
    frozen registry body hash and consume at least one frozen survivor, quotient
    class, or candidate-region/region lineage id. Cited lineage ids are checked
    against the frozen registry.
    """

    errors: list[str] = []
    error_codes: list[str] = []

    def add_error(code: str, message: str) -> None:
        error_codes.append(code)
        errors.append(message)

    registry_file = Path(registry_path)
    if not registry_file.is_absolute():
        registry_file = ROOT / registry_file
    if not registry_file.is_file():
        return {
            "ok": False,
            "errors": [f"registry missing: {registry_file}"],
            "error_codes": ["GCM_REGISTRY_MISSING"],
        }

    registry = _load_json(registry_file)
    lineage = payload.get("gcm_lineage") if isinstance(payload.get("gcm_lineage"), dict) else payload
    cited_object_id = lineage.get("gcm_object_id") or payload.get("gcm_object_id")
    cited_2q_object_id = lineage.get("gcm_2q_object_id") or payload.get("gcm_2q_object_id")
    cited_3q_object_id = lineage.get("gcm_3q_object_id") or payload.get("gcm_3q_object_id")
    cited_4q_object_id = lineage.get("gcm_4q_object_id") or payload.get("gcm_4q_object_id")
    registry_object_id = registry.get("gcm_object_id")
    registry_2q_object_id = registry.get("gcm_2q_object_id")
    registry_3q_object_id = registry.get("gcm_3q_object_id")
    registry_4q_object_id = registry.get("gcm_4q_object_id")
    acceptable_object_ids = {
        value
        for value in (registry_object_id, registry_2q_object_id, registry_3q_object_id, registry_4q_object_id)
        if isinstance(value, str) and value
    }
    cited_object_ids = {
        value
        for value in (cited_object_id, cited_2q_object_id, cited_3q_object_id, cited_4q_object_id)
        if isinstance(value, str) and value
    }
    cites_2q_object = isinstance(registry_2q_object_id, str) and registry_2q_object_id in cited_object_ids
    cites_3q_object = isinstance(registry_3q_object_id, str) and registry_3q_object_id in cited_object_ids
    cites_4q_object = isinstance(registry_4q_object_id, str) and registry_4q_object_id in cited_object_ids
    if not acceptable_object_ids.intersection(cited_object_ids):
        add_error(
            "GCM_OBJECT_ID_MISMATCH",
            "gcm_object_id mismatch: "
            f"cited={sorted(cited_object_ids)!r} registry={sorted(acceptable_object_ids)!r}",
        )

    for row in registry.get("carve_hashes", []):
        rel_path = row.get("path")
        expected = row.get("sha256")
        if not rel_path or not expected:
            add_error("GCM_REGISTRY_CARVE_HASH_ROW_MALFORMED", "registry carve hash row missing path or sha256")
            continue
        source_path = ROOT / rel_path
        if not source_path.is_file():
            add_error("GCM_CARVE_SOURCE_MISSING", f"carve source missing: {rel_path}")
            continue
        actual = _sha256_file(source_path)
        if actual != expected:
            add_error("GCM_CARVE_HASH_DRIFT", f"carve hash drift: {rel_path} expected={expected} actual={actual}")

    body_hash = registry.get("registry_body_sha256")
    actual_body_hash = None
    if not isinstance(body_hash, str) or not body_hash:
        add_error("GCM_REGISTRY_BODY_SHA256_MISSING", "registry_body_sha256 missing from registry")
    else:
        registry_without_hash = dict(registry)
        registry_without_hash.pop("registry_body_sha256", None)
        actual_body_hash = hashlib.sha256(_canonical(registry_without_hash)).hexdigest()
        if actual_body_hash != body_hash:
            add_error("GCM_REGISTRY_BODY_HASH_MISMATCH", f"registry body hash mismatch: expected={body_hash} actual={actual_body_hash}")
        if registry_4q_object_id:
            base_body_hash = registry.get("base_registry_body_sha256")
            if base_body_hash != EXPECTED_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM4Q_REGISTRY_BASE_IDENTITY_MISMATCH",
                    "4Q registry base identity mismatch: "
                    f"expected_base_body_sha256={EXPECTED_REGISTRY_BODY_SHA256} actual={base_body_hash}",
                )
            two_q_body_hash = registry.get("gcm_2q_registry_body_sha256")
            if two_q_body_hash != EXPECTED_2Q_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM4Q_REGISTRY_2Q_IDENTITY_MISMATCH",
                    "4Q registry 2Q identity mismatch: "
                    f"expected_2q_body_sha256={EXPECTED_2Q_REGISTRY_BODY_SHA256} actual={two_q_body_hash}",
                )
            three_q_body_hash = registry.get("gcm_3q_registry_body_sha256")
            if three_q_body_hash != EXPECTED_3Q_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM4Q_REGISTRY_3Q_IDENTITY_MISMATCH",
                    "4Q registry 3Q identity mismatch: "
                    f"expected_3q_body_sha256={EXPECTED_3Q_REGISTRY_BODY_SHA256} actual={three_q_body_hash}",
                )
            if actual_body_hash != EXPECTED_4Q_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM4Q_REGISTRY_IDENTITY_MISMATCH",
                    "4Q registry identity mismatch: "
                    f"expected_body_sha256={EXPECTED_4Q_REGISTRY_BODY_SHA256} actual={actual_body_hash}",
                )
        elif registry_3q_object_id:
            base_body_hash = registry.get("base_registry_body_sha256")
            if base_body_hash != EXPECTED_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM3Q_REGISTRY_BASE_IDENTITY_MISMATCH",
                    "3Q registry base identity mismatch: "
                    f"expected_base_body_sha256={EXPECTED_REGISTRY_BODY_SHA256} actual={base_body_hash}",
                )
            two_q_body_hash = registry.get("gcm_2q_registry_body_sha256")
            if two_q_body_hash != EXPECTED_2Q_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM3Q_REGISTRY_2Q_IDENTITY_MISMATCH",
                    "3Q registry 2Q identity mismatch: "
                    f"expected_2q_body_sha256={EXPECTED_2Q_REGISTRY_BODY_SHA256} actual={two_q_body_hash}",
                )
            if actual_body_hash != EXPECTED_3Q_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM3Q_REGISTRY_IDENTITY_MISMATCH",
                    "3Q registry identity mismatch: "
                    f"expected_body_sha256={EXPECTED_3Q_REGISTRY_BODY_SHA256} actual={actual_body_hash}",
                )
        elif registry_2q_object_id:
            base_body_hash = registry.get("base_registry_body_sha256")
            if base_body_hash != EXPECTED_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM2Q_REGISTRY_BASE_IDENTITY_MISMATCH",
                    "2Q registry base identity mismatch: "
                    f"expected_base_body_sha256={EXPECTED_REGISTRY_BODY_SHA256} actual={base_body_hash}",
                )
            if actual_body_hash != EXPECTED_2Q_REGISTRY_BODY_SHA256:
                add_error(
                    "GCM2Q_REGISTRY_IDENTITY_MISMATCH",
                    "2Q registry identity mismatch: "
                    f"expected_body_sha256={EXPECTED_2Q_REGISTRY_BODY_SHA256} actual={actual_body_hash}",
                )
        elif actual_body_hash != EXPECTED_REGISTRY_BODY_SHA256:
            add_error(
                "GCM_REGISTRY_IDENTITY_MISMATCH",
                "registry identity mismatch: "
                f"expected_body_sha256={EXPECTED_REGISTRY_BODY_SHA256} actual={actual_body_hash}",
            )

    cited_body_hash = lineage.get("registry_body_sha256") or payload.get("registry_body_sha256")
    cited_2q_body_hash = (
        lineage.get("gcm_2q_registry_body_sha256")
        or payload.get("gcm_2q_registry_body_sha256")
        or lineage.get("two_q_registry_body_sha256")
        or payload.get("two_q_registry_body_sha256")
    )
    cited_3q_body_hash = (
        lineage.get("gcm_3q_registry_body_sha256")
        or payload.get("gcm_3q_registry_body_sha256")
        or lineage.get("three_q_registry_body_sha256")
        or payload.get("three_q_registry_body_sha256")
    )
    cited_4q_body_hash = (
        lineage.get("gcm_4q_registry_body_sha256")
        or payload.get("gcm_4q_registry_body_sha256")
        or lineage.get("four_q_registry_body_sha256")
        or payload.get("four_q_registry_body_sha256")
    )
    if registry_4q_object_id:
        if cited_4q_body_hash != body_hash:
            add_error(
                "GCM4Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH",
                f"lineage 4Q registry_body_sha256 mismatch: registry={body_hash} cited={cited_4q_body_hash}",
            )
        cited_base_hash = (
            lineage.get("base_registry_body_sha256")
            or payload.get("base_registry_body_sha256")
            or lineage.get("one_q_registry_body_sha256")
            or payload.get("one_q_registry_body_sha256")
            or (cited_body_hash if cited_body_hash == EXPECTED_REGISTRY_BODY_SHA256 else None)
        )
        if cited_base_hash != EXPECTED_REGISTRY_BODY_SHA256:
            add_error(
                "GCM_LINEAGE_BASE_REGISTRY_BODY_SHA256_MISMATCH",
                "lineage base registry_body_sha256 mismatch: "
                f"expected={EXPECTED_REGISTRY_BODY_SHA256} cited={cited_base_hash}",
            )
        if cited_2q_body_hash != EXPECTED_2Q_REGISTRY_BODY_SHA256:
            add_error(
                "GCM4Q_LINEAGE_2Q_REGISTRY_BODY_SHA256_MISMATCH",
                "lineage 2Q registry_body_sha256 mismatch for 4Q packet: "
                f"expected={EXPECTED_2Q_REGISTRY_BODY_SHA256} cited={cited_2q_body_hash}",
            )
        if cited_3q_body_hash != EXPECTED_3Q_REGISTRY_BODY_SHA256:
            add_error(
                "GCM4Q_LINEAGE_3Q_REGISTRY_BODY_SHA256_MISMATCH",
                "lineage 3Q registry_body_sha256 mismatch for 4Q packet: "
                f"expected={EXPECTED_3Q_REGISTRY_BODY_SHA256} cited={cited_3q_body_hash}",
            )
    elif registry_3q_object_id:
        if cited_3q_body_hash != body_hash:
            add_error(
                "GCM3Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH",
                f"lineage 3Q registry_body_sha256 mismatch: registry={body_hash} cited={cited_3q_body_hash}",
            )
        cited_base_hash = (
            lineage.get("base_registry_body_sha256")
            or payload.get("base_registry_body_sha256")
            or lineage.get("one_q_registry_body_sha256")
            or payload.get("one_q_registry_body_sha256")
            or (cited_body_hash if cited_body_hash == EXPECTED_REGISTRY_BODY_SHA256 else None)
        )
        if cited_base_hash != EXPECTED_REGISTRY_BODY_SHA256:
            add_error(
                "GCM_LINEAGE_BASE_REGISTRY_BODY_SHA256_MISMATCH",
                "lineage base registry_body_sha256 mismatch: "
                f"expected={EXPECTED_REGISTRY_BODY_SHA256} cited={cited_base_hash}",
            )
        if cited_2q_body_hash != EXPECTED_2Q_REGISTRY_BODY_SHA256:
            add_error(
                "GCM3Q_LINEAGE_2Q_REGISTRY_BODY_SHA256_MISMATCH",
                "lineage 2Q registry_body_sha256 mismatch for 3Q packet: "
                f"expected={EXPECTED_2Q_REGISTRY_BODY_SHA256} cited={cited_2q_body_hash}",
            )
    elif registry_2q_object_id:
        cited_hashes = {
            value for value in (cited_body_hash, cited_2q_body_hash) if isinstance(value, str) and value
        }
        if body_hash and body_hash not in cited_hashes:
            add_error(
                "GCM2Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH",
                f"lineage 2Q registry_body_sha256 mismatch: registry={body_hash} cited={sorted(cited_hashes)!r}",
            )
        cited_base_hash = (
            lineage.get("base_registry_body_sha256")
            or payload.get("base_registry_body_sha256")
            or lineage.get("one_q_registry_body_sha256")
            or payload.get("one_q_registry_body_sha256")
            or (cited_body_hash if cited_body_hash == EXPECTED_REGISTRY_BODY_SHA256 else None)
        )
        if cited_base_hash != EXPECTED_REGISTRY_BODY_SHA256:
            add_error(
                "GCM_LINEAGE_BASE_REGISTRY_BODY_SHA256_MISMATCH",
                "lineage base registry_body_sha256 mismatch: "
                f"expected={EXPECTED_REGISTRY_BODY_SHA256} cited={cited_base_hash}",
            )
    else:
        if not isinstance(cited_body_hash, str) or not cited_body_hash:
            add_error("GCM_LINEAGE_REGISTRY_BODY_SHA256_MISSING", "registry_body_sha256 missing from lineage")
        elif cited_body_hash != EXPECTED_REGISTRY_BODY_SHA256:
            add_error(
                "GCM_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH",
                "lineage registry_body_sha256 mismatch: "
                f"expected={EXPECTED_REGISTRY_BODY_SHA256} cited={cited_body_hash}",
            )
        elif body_hash and cited_body_hash != body_hash:
            add_error(
                "GCM_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH",
                f"lineage registry_body_sha256 mismatch: registry={body_hash} cited={cited_body_hash}",
            )

    known = _collect_known_ids(registry)
    cited = _iter_cited_ids(payload)
    resolved_lineage_count = 0
    resolved_2q_lineage_count = 0
    resolved_3q_lineage_count = 0
    resolved_4q_lineage_count = 0
    for key, values in cited.items():
        if not known[key] and key.startswith("gcm_2q_"):
            continue
        if not known[key] and key.startswith("gcm_3q_"):
            continue
        if not known[key] and key.startswith("gcm_4q_"):
            continue
        for value in values:
            if value in known[key]:
                resolved_lineage_count += 1
                if key.startswith("gcm_2q_"):
                    resolved_2q_lineage_count += 1
                if key.startswith("gcm_3q_"):
                    resolved_3q_lineage_count += 1
                if key.startswith("gcm_4q_"):
                    resolved_4q_lineage_count += 1
            else:
                singular = key[:-1] if key.endswith("s") else key
                add_error(f"UNKNOWN_{singular.upper()}", f"unknown {singular}: {value}")
    if resolved_lineage_count == 0:
        add_error(
            "GCM_LINEAGE_CONSUMPTION_MISSING",
            "missing lineage consumption: require at least one survivor_id, "
            "quotient_class_id, candidate_region_id, or region_id resolving against frozen registry",
        )
    if cites_2q_object and resolved_2q_lineage_count == 0:
        add_error(
            "GCM2Q_LINEAGE_CONSUMPTION_MISSING",
            "missing 2Q lineage consumption: payload citing gcm_2q_object_id must include at least one "
            "gcm_2q_survivor_id, gcm_2q_quotient_class_id, or gcm_2q_candidate_region_id resolving "
            "against frozen 2Q registry",
        )
    if cites_3q_object and resolved_3q_lineage_count == 0:
        add_error(
            "GCM3Q_LINEAGE_CONSUMPTION_MISSING",
            "missing 3Q lineage consumption: payload citing gcm_3q_object_id must include at least one "
            "gcm_3q_survivor_id, gcm_3q_quotient_class_id, or gcm_3q_candidate_region_id resolving "
            "against frozen 3Q registry",
        )
    if cites_4q_object and resolved_4q_lineage_count == 0:
        add_error(
            "GCM4Q_LINEAGE_CONSUMPTION_MISSING",
            "missing 4Q lineage consumption: payload citing gcm_4q_object_id must include at least one "
            "gcm_4q_survivor_id, gcm_4q_quotient_class_id, or gcm_4q_candidate_region_id resolving "
            "against frozen 4Q registry",
        )

    result = {
        "ok": not errors,
        "errors": errors,
        "error_codes": error_codes,
        "registry_path": _display_path(registry_file),
        "gcm_object_id": registry_object_id,
        "gcm_2q_object_id": registry_2q_object_id,
        "gcm_3q_object_id": registry_3q_object_id,
        "registry_body_sha256": actual_body_hash,
    }
    if registry_4q_object_id:
        result["gcm_4q_object_id"] = registry_4q_object_id
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check a nested packet against the frozen GCM substrate registry.")
    parser.add_argument("payload", help="JSON payload to validate")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH), help="registry JSON path")
    args = parser.parse_args()
    result = gcm_substrate_check(_load_json(Path(args.payload)), args.registry)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)

#!/usr/bin/env python3
"""Build the standard three-engine result envelope shape.

This module centralizes envelope shape so sim builders do not hand-roll
`three_engine_sim_result_v1` records.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "three_engine_sim_result_v1"
DEFAULT_EXPECTED_LANES = ("julia", "jax", "pytorch")
DEFAULT_CLASSIFICATION = "scratch_diagnostic"
BUILDER_OWNED_FIELDS = frozenset(
    {
        "schema_version",
        "sim_id",
        "object_id",
        "generated_at",
        "mode",
        "classification",
        "promotion_allowed",
        "formal_admission_allowed",
        "claim_path_tools",
        "engine_contract",
        "engines",
        "crossover_proofs",
        "divergence",
        "parent_lineage",
        "stability_pairs",
    }
)

# Per-lane evidence kinds for the engine-independence annotation.
# See system_v6/receipts/engine_consensus_relabel_20260613.md for the motivation:
# ~43 packets shipped a cross-engine "agreement" / `max_divergence: 0.0` that is
# guaranteed-by-construction because the JAX and PyTorch lanes both call a shared
# Python core-compute and then only VERIFY its one payload. Only a lane that
# INDEPENDENTLY recomputes the core is a real second opinion.
LANE_EVIDENCE_INDEPENDENT = "independent_recompute"
LANE_EVIDENCE_VERIFY = "verify_payload"
LANE_EVIDENCE_UNSPECIFIED = "unspecified"
_LANE_EVIDENCE_KINDS = frozenset(
    {LANE_EVIDENCE_INDEPENDENT, LANE_EVIDENCE_VERIFY, LANE_EVIDENCE_UNSPECIFIED}
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_relative(path: str | Path, repo_root: Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return str(candidate.resolve().relative_to(repo_root))
    return str(candidate)


def _path_for_hash(path: str | Path, repo_root: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _reject_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not permitted: {value}")


def _load_json_strict(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_object,
        parse_constant=_reject_non_finite_constant,
    )


def _normalize_stability_pairs(stability_pairs: Iterable[Any] | None) -> list[dict[str, str]]:
    if stability_pairs is None:
        return []
    normalized: list[dict[str, str]] = []
    for pair in stability_pairs:
        if isinstance(pair, Mapping):
            subtree = pair.get("subtree")
            hash_value = pair.get("hash")
        else:
            try:
                subtree, hash_value = pair
            except Exception as exc:  # pragma: no cover - defensive shape guard.
                raise ValueError("stability_pairs entries must be mappings or (subtree, hash) pairs") from exc
        if not _non_empty_string(subtree) or not _non_empty_string(hash_value):
            raise ValueError("stability_pairs entries require non-empty subtree and hash")
        normalized.append({"subtree": str(subtree), "hash": str(hash_value)})
    return normalized


def _string_list(value: Any, name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    normalized = [str(item) for item in value]
    if any(not item.strip() for item in normalized):
        raise ValueError(f"{name} entries must be non-empty strings")
    return normalized


def _normalize_package_observables(
    name: str,
    lane: Mapping[str, Any],
    load_bearing: Sequence[str],
) -> dict[str, str]:
    if not load_bearing:
        return {}
    observables = lane.get("package_observables")
    if not isinstance(observables, Mapping):
        raise ValueError(f"lanes.{name}.package_observables is required for load-bearing packages")
    normalized: dict[str, str] = {}
    for package in load_bearing:
        observable = observables.get(package)
        if not _non_empty_string(observable):
            raise ValueError(f"lanes.{name}.package_observables.{package} must name the exact observable")
        normalized[package] = str(observable)
    return normalized


def _build_lane_record(
    name: str,
    lane: Mapping[str, Any],
    *,
    repo_root: Path,
    classification: str,
    promotion_allowed: bool,
    formal_admission_allowed: bool,
) -> dict[str, Any]:
    if not isinstance(lane, Mapping):
        raise ValueError(f"lanes.{name} must be an object")
    if lane.get("reads_peer_result") is not False:
        raise ValueError(f"lanes.{name}.reads_peer_result must be explicitly false")
    source_path = lane.get("source_path")
    result_path = lane.get("result_path")
    if not _non_empty_string(source_path):
        raise ValueError(f"lanes.{name}.source_path is required")
    if not _non_empty_string(result_path):
        raise ValueError(f"lanes.{name}.result_path is required")

    source_rel = _repo_relative(str(source_path), repo_root)
    result_rel = _repo_relative(str(result_path), repo_root)
    source_abs = _path_for_hash(source_rel, repo_root)
    result_abs = _path_for_hash(result_rel, repo_root)
    if not source_abs.is_file():
        raise ValueError(f"lanes.{name}.source_path does not exist: {source_rel}")
    if not result_abs.is_file():
        raise ValueError(f"lanes.{name}.result_path does not exist: {result_rel}")
    packages_used = _string_list(lane.get("packages_used"), f"lanes.{name}.packages_used")
    load_bearing = _string_list(
        lane.get("aligned_packages_load_bearing"),
        f"lanes.{name}.aligned_packages_load_bearing",
    )
    package_observables = _normalize_package_observables(name, lane, load_bearing)

    record = copy.deepcopy(dict(lane))
    record.update(
        {
            "ran": True,
            "source_path": source_rel,
            "source_sha256": _sha256_file(source_abs),
            "result_path": result_rel,
            "result_sha256": _sha256_file(result_abs),
            "reads_peer_result": False,
            "classification": classification,
            "promotion_allowed": promotion_allowed,
            "formal_admission_allowed": formal_admission_allowed,
        }
    )
    record["packages_used"] = packages_used
    record["aligned_packages_load_bearing"] = load_bearing
    record["package_observables"] = package_observables
    return record


def _validate_omissions(
    lanes: Mapping[str, Any],
    *,
    expected_lanes: Sequence[str],
    omitted_lanes: Mapping[str, str] | None,
) -> dict[str, str]:
    expected = [str(lane_name) for lane_name in expected_lanes]
    if len(set(expected)) != len(expected):
        raise ValueError("expected_lanes must not contain duplicates")
    present = {str(lane_name) for lane_name in lanes}
    absent = set(expected) - present

    raw_omitted = {} if omitted_lanes is None else omitted_lanes
    if not isinstance(raw_omitted, Mapping):
        raise ValueError("omitted_lanes must be an object")
    omitted = {str(key): value for key, value in raw_omitted.items()}
    for lane_name in sorted(absent):
        omission = omitted.get(lane_name)
        if not _non_empty_string(omission):
            raise ValueError(f"omitted_lanes.{lane_name} requires honest omission text")

    omitted_names = set(omitted)
    if omitted_names != absent:
        contradictory = sorted(omitted_names & present)
        unexpected = sorted(omitted_names - absent - present)
        details: list[str] = []
        if contradictory:
            details.append(f"contradicts present lanes {contradictory}")
        if unexpected:
            details.append(f"contains non-absent lanes {unexpected}")
        raise ValueError(
            "omitted_lanes keys must exactly match absent expected lanes"
            + (f"; {'; '.join(details)}" if details else "")
        )
    return {key: str(value) for key, value in omitted.items()}


def _normalize_lane_evidence(
    lane_evidence: Mapping[str, str] | None,
    lane_names: Sequence[str],
) -> dict[str, str]:
    """Map each lane to a declared evidence kind, defaulting to `unspecified`.

    `unspecified` is the conservative default: a caller that does not declare a
    lane's evidence kind does NOT get an honest "independent" claim by silence.
    """
    declared = dict(lane_evidence or {})
    for key in declared:
        if key not in lane_names:
            raise ValueError(f"lane_evidence references unknown lane: {key}")
    normalized: dict[str, str] = {}
    for name in lane_names:
        kind = declared.get(name, LANE_EVIDENCE_UNSPECIFIED)
        if kind not in _LANE_EVIDENCE_KINDS:
            raise ValueError(
                f"lane_evidence.{name} must be one of {sorted(_LANE_EVIDENCE_KINDS)}; got {kind!r}"
            )
        normalized[name] = kind
    return normalized


def _engine_independence_annotation(
    lane_evidence: Mapping[str, str],
    max_divergence: Any,
) -> dict[str, Any]:
    """Honest independence annotation distinguishing recompute vs verify lanes.

    Per system_v6/receipts/engine_consensus_relabel_20260613.md: `max_divergence`
    over verify-payload lanes is a tautological 0 (they consume one shared
    payload), not an independence signal. A genuine cross-engine independence
    signal requires at least two lanes that INDEPENDENTLY recompute the core.
    """
    independent = sorted(n for n, k in lane_evidence.items() if k == LANE_EVIDENCE_INDEPENDENT)
    verify = sorted(n for n, k in lane_evidence.items() if k == LANE_EVIDENCE_VERIFY)
    unspecified = sorted(n for n, k in lane_evidence.items() if k == LANE_EVIDENCE_UNSPECIFIED)
    independent_signal = len(independent) >= 2
    if unspecified:
        max_div_meaning = (
            "independence-unverified: one or more lanes did not declare whether they "
            "independently recompute or only verify a shared payload; treat max_divergence "
            "as a SHAPE/agreement check, not an independence signal."
        )
    elif independent_signal:
        max_div_meaning = (
            "max_divergence over the independent-recompute lanes is a genuine cross-engine "
            "independence signal."
        )
    elif independent:
        max_div_meaning = (
            "only one lane independently recomputes; max_divergence across the verify-payload "
            "lanes is structural (shared payload), not an independence signal — the single "
            "independent lane is the only second opinion."
        )
    else:
        max_div_meaning = (
            "structural (shared payload), not an independence signal: every lane only verifies "
            "one shared core-compute payload, so max_divergence is tautologically ~0."
        )
    return {
        "independent_recompute_lanes": independent,
        "verify_payload_lanes": verify,
        "unspecified_lanes": unspecified,
        "independent_signal": independent_signal,
        "max_divergence_meaning": max_div_meaning,
        "note": (
            "Lanes that call a shared core-compute and only verify its payload cannot diverge "
            "on that payload; their agreement is structural. See "
            "system_v6/receipts/engine_consensus_relabel_20260613.md."
        ),
    }


def _guard_extra_fields_independence(
    extra_fields: Mapping[str, Any] | None,
    independent_signal: bool,
) -> None:
    """Catch the receipt's disease at the single point the builder can see it.

    A caller must not inject `engine_consensus.independent = true` (or a top-level
    `independent = true` consensus claim) through `extra_fields` unless the
    declared lane evidence actually supports an independence signal (>=2
    independent-recompute lanes).
    """
    if not extra_fields or independent_signal:
        return
    consensus = extra_fields.get("engine_consensus")
    if isinstance(consensus, Mapping) and consensus.get("independent") is True:
        raise ValueError(
            "extra_fields.engine_consensus.independent=true is not permitted without >=2 "
            "lanes declared lane_evidence=independent_recompute; cross-engine 'independence' "
            "over shared-payload verify lanes is structural, not an independence signal "
            "(system_v6/receipts/engine_consensus_relabel_20260613.md)."
        )


def _guard_extra_field_collisions(extra_fields: Mapping[str, Any] | None) -> None:
    if extra_fields is None:
        return
    if not isinstance(extra_fields, Mapping):
        raise ValueError("extra_fields must be an object")
    collisions = sorted(BUILDER_OWNED_FIELDS & {str(key) for key in extra_fields})
    if collisions:
        raise ValueError(
            "extra_fields may not override builder-owned fields: " + ", ".join(collisions)
        )


def build_envelope(
    *,
    sim_id: str,
    lanes: Mapping[str, Mapping[str, Any]],
    mode: str,
    claim_path_tools: Sequence[str],
    crossover_proofs: Mapping[str, Any],
    divergence: Mapping[str, Any],
    classification: str = DEFAULT_CLASSIFICATION,
    promotion_allowed: bool = False,
    formal_admission_allowed: bool = False,
    parent_lineage: Mapping[str, str] | None = None,
    omitted_lanes: Mapping[str, str] | None = None,
    expected_lanes: Sequence[str] = DEFAULT_EXPECTED_LANES,
    stability_pairs: Iterable[Any] | None = None,
    generated_at: str | None = None,
    lane_evidence: Mapping[str, str] | None = None,
    extra_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a standard `three_engine_sim_result_v1` envelope dict.

    `mode` is always emitted as a field; it never changes `schema_version`.
    Missing expected lanes require an explicit omission statement.

    `lane_evidence` maps each lane name to one of `independent_recompute`,
    `verify_payload`, or `unspecified` (the conservative default). The builder
    uses it to attach an honest `divergence.engine_independence` annotation that
    distinguishes independent-recompute lanes from verify-payload lanes and
    labels `max_divergence` accordingly. It never emits
    `engine_consensus.independent=true` itself, and rejects a caller that injects
    that claim via `extra_fields` without >=2 independent-recompute lanes.
    """

    if not _non_empty_string(sim_id):
        raise ValueError("sim_id is required")
    if not _non_empty_string(mode):
        raise ValueError("mode is required")
    if not isinstance(lanes, Mapping) or not lanes:
        raise ValueError("lanes must be a non-empty object")
    _guard_extra_field_collisions(extra_fields)
    repo_root = _repo_root()
    omissions = _validate_omissions(lanes, expected_lanes=expected_lanes, omitted_lanes=omitted_lanes)

    engine_records = {
        str(name): _build_lane_record(
            str(name),
            lane,
            repo_root=repo_root,
            classification=classification,
            promotion_allowed=promotion_allowed,
            formal_admission_allowed=formal_admission_allowed,
        )
        for name, lane in lanes.items()
    }

    generated = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lane_names = sorted(engine_records)

    normalized_lane_evidence = _normalize_lane_evidence(lane_evidence, lane_names)
    divergence_record = copy.deepcopy(dict(divergence))
    max_divergence = divergence_record.get("max_divergence")
    if (
        type(max_divergence) not in (int, float)
        or not math.isfinite(max_divergence)
        or max_divergence < 0
    ):
        raise ValueError("divergence.max_divergence must be a finite nonnegative number")
    independence_annotation = _engine_independence_annotation(
        normalized_lane_evidence, max_divergence
    )
    divergence_record["lane_evidence"] = normalized_lane_evidence
    divergence_record["engine_independence"] = independence_annotation
    _guard_extra_fields_independence(extra_fields, independence_annotation["independent_signal"])

    envelope: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "sim_id": sim_id,
        "object_id": sim_id,
        "generated_at": generated,
        "mode": mode,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_path_tools": list(claim_path_tools),
        "engine_contract": {
            "mode": mode,
            "lanes": lane_names,
            "omitted_lanes": omissions,
            "classification": classification,
            "promotion_allowed": promotion_allowed,
            "formal_admission_allowed": formal_admission_allowed,
        },
        "engines": engine_records,
        "crossover_proofs": copy.deepcopy(dict(crossover_proofs)),
        "divergence": divergence_record,
        "parent_lineage": copy.deepcopy(dict(parent_lineage or {})),
        "stability_pairs": _normalize_stability_pairs(stability_pairs),
    }
    if extra_fields:
        for key, value in extra_fields.items():
            envelope[str(key)] = copy.deepcopy(value)
    return envelope


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec_json", type=Path, help="JSON object containing build_envelope keyword arguments")
    args = parser.parse_args()
    spec = _load_json_strict(args.spec_json)
    if not isinstance(spec, dict):
        raise ValueError("spec_json must contain a JSON object")
    print(json.dumps(build_envelope(**spec), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

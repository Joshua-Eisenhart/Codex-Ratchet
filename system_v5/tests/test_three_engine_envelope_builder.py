import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_three_engine_envelope import build_envelope
from validate_three_engine_sim_result import validate


GEO_S3_ENVELOPE = (
    ROOT
    / "system_v6/sims/geo_s3_alternative_probe_families_v0/results/"
    / "geo_s3_alternative_probe_families_v0_envelope_results.json"
)


def _rel(path: str) -> str:
    return str((ROOT / path).relative_to(ROOT))


def _package_observables(load_bearing: list[str]) -> dict[str, str]:
    return {package: f"{package} carries a test observable" for package in load_bearing}


def test_build_envelope_rebuilds_committed_geo_s3_shape_from_parts() -> None:
    committed = json.loads(GEO_S3_ENVELOPE.read_text(encoding="utf-8"))
    lanes = {
        name: {
            "source_path": record["source_path"],
            "result_path": record["result_path"],
            "role_id": record["role_id"],
            "packages_used": record["packages_used"],
            "aligned_packages_load_bearing": record["aligned_packages_load_bearing"],
            "package_observables": _package_observables(record["aligned_packages_load_bearing"]),
            "tool_manifest": record["tool_manifest"],
            "tool_integration_depth": record["tool_integration_depth"],
            "tool_calls": record["tool_calls"],
        }
        for name, record in committed["engines"].items()
    }

    rebuilt = build_envelope(
        sim_id=committed["sim_id"],
        lanes=lanes,
        mode=committed["engine_contract"]["mode"],
        claim_path_tools=committed["claim_path_tools"],
        crossover_proofs=committed["crossover_proofs"],
        divergence=committed["divergence"],
        parent_lineage=committed["parent_lineage"],
        omitted_lanes=committed["engine_contract"]["omitted_lanes"],
    )

    assert rebuilt["schema_version"] == "three_engine_sim_result_v1"
    assert rebuilt["mode"] == committed["engine_contract"]["mode"]
    assert rebuilt["classification"] == "scratch_diagnostic"
    assert rebuilt["promotion_allowed"] is False
    assert rebuilt["formal_admission_allowed"] is False
    assert rebuilt["engine_contract"]["omitted_lanes"]["pytorch"]
    assert rebuilt["engines"]["julia"]["source_sha256"]
    assert rebuilt["engines"]["julia"]["result_sha256"]
    assert validate(rebuilt) == []


def test_build_envelope_requires_package_observables_for_load_bearing_packages() -> None:
    committed = json.loads(GEO_S3_ENVELOPE.read_text(encoding="utf-8"))
    lanes = {
        "julia": {
            **committed["engines"]["julia"],
            "package_observables": _package_observables(committed["engines"]["julia"]["aligned_packages_load_bearing"]),
        },
        "jax": committed["engines"]["jax"],
    }

    try:
        build_envelope(
            sim_id="missing_package_observable",
            lanes=lanes,
            mode="julia_canon_plus_jax_diagnostic",
            claim_path_tools=committed["claim_path_tools"],
            crossover_proofs=committed["crossover_proofs"],
            divergence=committed["divergence"],
            omitted_lanes={"pytorch": "not scoped; no graph/network/autograd claim path"},
        )
    except ValueError as exc:
        assert "lanes.jax.package_observables" in str(exc)
    else:
        raise AssertionError("missing package_observables should be rejected")


def test_build_envelope_requires_honest_omission_text_for_absent_lane() -> None:
    committed = json.loads(GEO_S3_ENVELOPE.read_text(encoding="utf-8"))
    lanes = {
        "julia": {
            **committed["engines"]["julia"],
            "package_observables": _package_observables(committed["engines"]["julia"]["aligned_packages_load_bearing"]),
        },
        "jax": {
            **committed["engines"]["jax"],
            "package_observables": _package_observables(committed["engines"]["jax"]["aligned_packages_load_bearing"]),
        },
    }

    try:
        build_envelope(
            sim_id="missing_omission_text",
            lanes=lanes,
            mode="julia_canon_plus_jax_diagnostic",
            claim_path_tools=committed["claim_path_tools"],
            crossover_proofs=committed["crossover_proofs"],
            divergence=committed["divergence"],
            expected_lanes=("julia", "jax", "pytorch"),
        )
    except ValueError as exc:
        assert "omitted_lanes.pytorch" in str(exc)
    else:
        raise AssertionError("missing honest omission text should be rejected")


def test_build_envelope_supports_subtree_hash_stability_pairs() -> None:
    committed = json.loads(GEO_S3_ENVELOPE.read_text(encoding="utf-8"))

    envelope = build_envelope(
        sim_id="stability_pair_probe",
        lanes={
            "julia": {
                **committed["engines"]["julia"],
                "package_observables": _package_observables(committed["engines"]["julia"]["aligned_packages_load_bearing"]),
            },
            "jax": {
                **committed["engines"]["jax"],
                "package_observables": _package_observables(committed["engines"]["jax"]["aligned_packages_load_bearing"]),
            },
        },
        mode="julia_canon_plus_jax_diagnostic",
        claim_path_tools=committed["claim_path_tools"],
        crossover_proofs=committed["crossover_proofs"],
        divergence=committed["divergence"],
        omitted_lanes={"pytorch": "not scoped; no graph/network/autograd claim path"},
        stability_pairs=[
            {"subtree": "divergence.engine_values", "hash": "abc123"},
            ("anchor_rows.hashes", "def456"),
        ],
    )

    assert envelope["stability_pairs"] == [
        {"subtree": "divergence.engine_values", "hash": "abc123"},
        {"subtree": "anchor_rows.hashes", "hash": "def456"},
    ]


def test_deliberately_wrong_builder_call_produces_validator_failing_envelope() -> None:
    source_path = _rel("system_v6/sims/geo_s3_alternative_probe_families_v0/geo_s3_alternative_probe_families_v0.py")
    result_path = _rel(
        "system_v6/sims/geo_s3_alternative_probe_families_v0/results/"
        "geo_s3_alternative_probe_families_v0_envelope_results.json"
    )
    bad = build_envelope(
        sim_id="bad_envelope_probe",
        lanes={
            "julia": {
                "source_path": source_path,
                "result_path": result_path,
                "packages_used": ["numpy"],
                "aligned_packages_load_bearing": ["numpy"],
                "package_observables": {"numpy": "negative control aggregate"},
            },
            "jax": {
                "source_path": source_path,
                "result_path": result_path,
                "packages_used": ["jax.numpy"],
                "aligned_packages_load_bearing": ["jax.numpy"],
                "package_observables": {"jax.numpy": "negative control aggregate"},
            },
        },
        mode="negative_validator_probe",
        claim_path_tools=["z3", "cvc5"],
        crossover_proofs={
            "z3": {"ran": True, "verdict": "sat", "load_bearing": True},
            "cvc5": {"ran": True, "verdict": "sat", "load_bearing": True},
        },
        divergence={
            "julia_authoritative": True,
            "engine_values": {"julia": 1.0, "jax": 1.0},
            "max_divergence": 0.0,
        },
        omitted_lanes={"pytorch": "not scoped for this negative validator probe"},
    )

    errors = validate(bad)

    assert errors
    assert "julia must have at least one aligned load-bearing package" in errors[0]

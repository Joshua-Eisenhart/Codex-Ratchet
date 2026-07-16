import gzip
import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest


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


def _valid_builder_kwargs() -> dict:
    committed = json.loads(GEO_S3_ENVELOPE.read_text(encoding="utf-8"))
    lanes = {
        name: {
            **committed["engines"][name],
            "package_observables": _package_observables(
                committed["engines"][name]["aligned_packages_load_bearing"]
            ),
        }
        for name in ("julia", "jax")
    }
    return {
        "sim_id": "generic_builder_hardening_probe",
        "lanes": lanes,
        "mode": "julia_canon_plus_jax_diagnostic",
        "claim_path_tools": committed["claim_path_tools"],
        "crossover_proofs": committed["crossover_proofs"],
        "divergence": committed["divergence"],
        "omitted_lanes": {"pytorch": "not scoped; no graph/network/autograd claim path"},
    }


def _run_builder(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/build_three_engine_envelope.py", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


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
            "reads_peer_result": record["reads_peer_result"],
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
                "reads_peer_result": False,
            },
            "jax": {
                "source_path": source_path,
                "result_path": result_path,
                "packages_used": ["jax.numpy"],
                "aligned_packages_load_bearing": ["jax.numpy"],
                "package_observables": {"jax.numpy": "negative control aggregate"},
                "reads_peer_result": False,
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


@pytest.mark.parametrize(
    "core_field",
    [
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
    ],
)
def test_build_envelope_rejects_extra_field_collisions(core_field: str) -> None:
    with pytest.raises(ValueError, match="may not override builder-owned fields"):
        build_envelope(**_valid_builder_kwargs(), extra_fields={core_field: "tampered"})


def test_build_envelope_rejects_negative_max_divergence() -> None:
    kwargs = _valid_builder_kwargs()
    kwargs["divergence"] = {**kwargs["divergence"], "max_divergence": -1.0}

    with pytest.raises(ValueError, match="finite nonnegative number"):
        build_envelope(**kwargs)


@pytest.mark.parametrize(
    "omitted_lanes",
    [
        {
            "pytorch": "not scoped; no graph/network/autograd claim path",
            "jax": "contradicts the present jax lane",
        },
        {
            "pytorch": "not scoped; no graph/network/autograd claim path",
            "unknown": "not an absent expected lane",
        },
    ],
)
def test_build_envelope_requires_exact_omission_keys(omitted_lanes: dict[str, str]) -> None:
    kwargs = _valid_builder_kwargs()
    kwargs["omitted_lanes"] = omitted_lanes

    with pytest.raises(ValueError, match="keys must exactly match absent expected lanes"):
        build_envelope(**kwargs)


@pytest.mark.parametrize("declaration", ["missing", "true"])
def test_build_envelope_requires_explicit_false_reads_peer_result(declaration: str) -> None:
    kwargs = _valid_builder_kwargs()
    if declaration == "missing":
        kwargs["lanes"]["jax"].pop("reads_peer_result")
    else:
        kwargs["lanes"]["jax"]["reads_peer_result"] = True

    with pytest.raises(ValueError, match="lanes.jax.reads_peer_result must be explicitly false"):
        build_envelope(**kwargs)


def test_builder_cli_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"sim_id":"first","sim_id":"second"}', encoding="utf-8")

    result = _run_builder(path)

    assert result.returncode != 0
    assert "duplicate JSON key: sim_id" in result.stderr


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_builder_cli_rejects_non_finite_json_constants(tmp_path: Path, constant: str) -> None:
    path = tmp_path / "non_finite.json"
    path.write_text(f'{{"value":{constant}}}', encoding="utf-8")

    result = _run_builder(path)

    assert result.returncode != 0
    assert f"non-finite JSON constant is not permitted: {constant}" in result.stderr


def test_all_committed_builder_specs_use_hardened_contract() -> None:
    migrated = 0
    for path in sorted(ROOT.glob("system_v*/sims/**/*envelope_spec.json")):
        relative = str(path.relative_to(ROOT))
        if "mss_anti_thing_tournament_v0" in path.parts:
            continue
        spec = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(spec, dict) or not {"sim_id", "lanes", "mode"} <= spec.keys():
            continue
        envelope = build_envelope(**spec)
        assert validate(envelope) == [], relative
        migrated += 1

    assert migrated == 34


def test_migrated_spec_generators_replay_hardened_contract_without_canonical_writes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Replay the 33 legacy generators through a temporary file overlay.

    Some archived inputs are committed as ``.json.gz`` and eight generators
    refresh trajectory artifacts while building their specs. The overlay
    materializes compressed reads and redirects every repo-local write under
    ``tmp_path`` so the real generator logic runs without touching canon.
    """

    original_open = Path.open
    original_exists = Path.exists
    original_is_file = Path.is_file
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text
    original_write_bytes = Path.write_bytes
    original_write_text = Path.write_text
    overlay_root = tmp_path / "generator-overlay"

    def overlay_path(path: Path) -> Path | None:
        try:
            return overlay_root / path.resolve().relative_to(ROOT)
        except ValueError:
            return None

    def materialize_read(path: Path) -> Path:
        overlaid = overlay_path(path)
        if overlaid is None:
            return path
        if original_exists(overlaid):
            return overlaid
        if original_exists(path):
            return path
        compressed = Path(f"{path}.gz")
        if original_is_file(compressed):
            overlaid.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(compressed, "rb") as handle:
                original_write_bytes(overlaid, handle.read())
            return overlaid
        return path

    def redirect_write(path: Path) -> Path:
        overlaid = overlay_path(path)
        if overlaid is None:
            return path
        overlaid.parent.mkdir(parents=True, exist_ok=True)
        return overlaid

    def patched_open(path: Path, mode: str = "r", *args: object, **kwargs: object):
        write_mode = any(flag in mode for flag in "wax+")
        target = redirect_write(path) if write_mode else materialize_read(path)
        return original_open(target, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", patched_open)
    monkeypatch.setattr(Path, "exists", lambda path: original_exists(materialize_read(path)))
    monkeypatch.setattr(Path, "is_file", lambda path: original_is_file(materialize_read(path)))
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda path: original_read_bytes(materialize_read(path)),
    )
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *args, **kwargs: original_read_text(materialize_read(path), *args, **kwargs),
    )
    monkeypatch.setattr(
        Path,
        "write_bytes",
        lambda path, data: original_write_bytes(redirect_write(path), data),
    )
    monkeypatch.setattr(
        Path,
        "write_text",
        lambda path, data, *args, **kwargs: original_write_text(
            redirect_write(path), data, *args, **kwargs
        ),
    )
    monkeypatch.setattr(sys, "dont_write_bytecode", True)

    cases: list[tuple[Path, Path]] = []
    for spec_path in sorted(ROOT.glob("system_v6/sims/**/*_envelope_spec.json")):
        if "s8_local_information_table_v0" in spec_path.parts:
            continue
        payload = json.loads(original_read_text(spec_path, encoding="utf-8"))
        if not isinstance(payload, dict) or not {"sim_id", "lanes", "mode"} <= payload.keys():
            continue
        sim_dir = spec_path.parent.parent if spec_path.parent.name == "results" else spec_path.parent
        writer_path = sim_dir / "write_envelope_spec.py"
        assert original_is_file(writer_path), writer_path
        cases.append((spec_path, writer_path))

    assert len(cases) == 33
    failures: list[str] = []
    for index, (spec_path, writer_path) in enumerate(cases):
        module_name = f"_envelope_spec_regen_{index}"
        monkeypatch.syspath_prepend(str(writer_path.parent))
        module_spec = importlib.util.spec_from_file_location(module_name, writer_path)
        assert module_spec is not None and module_spec.loader is not None
        module = importlib.util.module_from_spec(module_spec)
        try:
            module_spec.loader.exec_module(module)
            parameters = inspect.signature(module.build_spec).parameters
            if not parameters:
                generated_spec = module.build_spec()
            elif tuple(parameters) == ("packet",):
                packet = module.common.load_json(module.common.RESULT_PATH)
                generated_spec = module.build_spec(packet)
            else:
                raise AssertionError(f"unsupported build_spec signature: {tuple(parameters)}")
            assert all(
                lane.get("reads_peer_result") is False
                for lane in generated_spec["lanes"].values()
            )
            envelope = build_envelope(**generated_spec)
            assert validate(envelope) == []
        except Exception as exc:  # collect every broken generator in one replay
            failures.append(f"{spec_path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")

    assert failures == []

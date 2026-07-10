#!/usr/bin/env python3
"""Validate ALCO oracle output against independent local exact formulas."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import local_j3o_exact as local


HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "alco_j3o_exact_oracle_result.json"
VALIDATION_PATH = HERE / "alco_j3o_exact_oracle_validation.json"
EXPECTED_SEEDS = (7, 29, 101, 20260709)
EXPECTED_AUTHORITY_EXCLUSIONS = {
    "spectral_log",
    "entropy",
    "channel",
    "DPI",
    "engine",
    "Axis0",
    "perception",
    "object",
    "physics",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file() and ".git" not in candidate.parts):
        relative = item.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(item)))
        digest.update(b"\0")
    return digest.hexdigest()


def tracked_tree_sha256(path: Path) -> str:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=path,
        check=True,
        capture_output=True,
    ).stdout
    digest = hashlib.sha256()
    for raw_relative in sorted(item for item in output.split(b"\0") if item):
        relative = raw_relative.decode("utf-8")
        digest.update(raw_relative)
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path / relative)))
        digest.update(b"\0")
    return digest.hexdigest()


def _current_hash(entry: dict[str, Any]) -> str:
    path = Path(entry["path"])
    kind = entry["kind"]
    if kind == "file":
        return sha256_file(path)
    if kind == "tree":
        return tree_sha256(path)
    if kind == "git_tracked_tree":
        return tracked_tree_sha256(path)
    raise ValueError(f"unsupported provenance kind: {kind}")


def _q(value: str) -> local.Q:
    return local.q(value)


def _qlist(value: list[str]) -> local.Albert:
    return local.parse_qlist(value)


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, evidence: Any) -> None:
        checks.append({"name": name, "pass": bool(passed), "evidence": evidence})

    record("schema", result.get("schema") == "codex_ratchet.alco_j3o_exact_oracle_result.v1", result.get("schema"))
    record("classification", result.get("classification") == "scratch_diagnostic", result.get("classification"))
    record(
        "promotion_fences",
        result.get("promotion_allowed") is False and result.get("formal_admission_allowed") is False,
        {
            "promotion_allowed": result.get("promotion_allowed"),
            "formal_admission_allowed": result.get("formal_admission_allowed"),
        },
    )
    record(
        "authority_exclusions",
        set(result.get("authority_exclusions", [])) == EXPECTED_AUTHORITY_EXCLUSIONS,
        sorted(result.get("authority_exclusions", [])),
    )

    oracle = result["oracle"]
    metadata = oracle["metadata"]
    record(
        "package_metadata",
        metadata.get("gap_version") == "4.16.0"
        and metadata.get("alco_version") == "1.1.2"
        and bool(metadata.get("resclasses_version"))
        and metadata.get("field") == "Rationals"
        and metadata.get("albert_dimension") == "27"
        and metadata.get("albert_rank") == "3"
        and metadata.get("albert_degree") == "8",
        metadata,
    )
    record(
        "coordinate_map",
        metadata.get("coordinate_roundtrip_pass") is True
        and metadata.get("octonion_map_fano_pass") is True,
        {
            "coordinate_roundtrip_pass": metadata.get("coordinate_roundtrip_pass"),
            "octonion_map_fano_pass": metadata.get("octonion_map_fano_pass"),
            "map": oracle.get("map"),
        },
    )
    record(
        "simple_eja_4_8_boundary",
        oracle["boundaries"].get("simple_eja_4_8_is_fail") is True,
        oracle["boundaries"],
    )
    record(
        "oracle_execution",
        result["oracle_execution"].get("exit_code") == 0
        and result["oracle_execution"].get("stderr_empty") is True,
        result["oracle_execution"],
    )
    record(
        "upstream_alco_tests",
        result["upstream_tests"].get("pass") is True
        and result["upstream_tests"].get("failures") == 0
        and result["upstream_tests"].get("files") == 6,
        result["upstream_tests"],
    )

    expected_labels = [f"seed_{seed}" for seed in EXPECTED_SEEDS] + ["kill_fano_e1_e2"]
    actual_labels = [case["label"] for case in oracle["cases"]]
    record("case_set", actual_labels == expected_labels, {"expected": expected_labels, "actual": actual_labels})

    category_passes: dict[str, list[bool]] = {
        "input_reproduction": [],
        "product": [],
        "trace": [],
        "determinant": [],
        "minimal_polynomial": [],
        "quadratic_representation": [],
        "quadratic_identities": [],
    }
    case_evidence: list[dict[str, Any]] = []
    corrupt_product_mismatches: list[str] = []

    for case in oracle["cases"]:
        label = case["label"]
        x, y, z = _qlist(case["x"]), _qlist(case["y"]), _qlist(case["z"])
        expected_vectors = local.kill_vectors() if label == "kill_fano_e1_e2" else local.seeded_vectors(int(case["seed"]))
        inputs_pass = (x, y, z) == expected_vectors
        category_passes["input_reproduction"].append(inputs_pass)

        product = local.jordan(x, y)
        product_pass = product == _qlist(case["product"])
        category_passes["product"].append(product_pass)

        ux_y = local.quadratic(x, y)
        uy_x = local.quadratic(y, x)
        quadratic_pass = ux_y == _qlist(case["u_x_y"]) and uy_x == _qlist(case["u_y_x"])
        category_passes["quadratic_representation"].append(quadratic_pass)

        trace_pass = (
            local.trace(x) == _q(case["trace_x"])
            and local.trace(y) == _q(case["trace_y"])
            and local.trace(ux_y) == _q(case["trace_u_x_y"])
        )
        category_passes["trace"].append(trace_pass)

        det_x = local.determinant(x)
        det_y = local.determinant(y)
        det_u = local.determinant(ux_y)
        determinant_pass = det_x == _q(case["det_x"]) and det_y == _q(case["det_y"]) and det_u == _q(case["det_u_x_y"])
        category_passes["determinant"].append(determinant_pass)

        minpoly_x = local.minimal_polynomial(x)
        minpoly_y = local.minimal_polynomial(y)
        minpoly_pass = minpoly_x == _qlist(case["minpoly_x"]) and minpoly_y == _qlist(case["minpoly_y"])
        category_passes["minimal_polynomial"].append(minpoly_pass)

        local_ch_x = local.polynomial_value(minpoly_x, x) == local.zero()
        local_ch_y = local.polynomial_value(minpoly_y, y) == local.zero()
        local_u_unit = local.quadratic(x, local.unit()) == local.jordan(x, x)
        local_u_homogeneous = local.quadratic(local.scale(x, local.Q(2)), y) == local.scale(ux_y, local.Q(4))
        local_det_identity = det_u == det_x * det_x * det_y
        local_fundamental = local.quadratic(ux_y, z) == local.quadratic(
            x, local.quadratic(y, local.quadratic(x, z))
        )
        oracle_identity_values = [
            case["cayley_hamilton_x"],
            case["cayley_hamilton_y"],
            case["u_unit_identity"],
            case["u_homogeneity"],
            case["u_determinant_identity"],
            case["fundamental_formula"],
        ]
        local_identity_values = [
            local_ch_x,
            local_ch_y,
            local_u_unit,
            local_u_homogeneous,
            local_det_identity,
            local_fundamental,
        ]
        identities_pass = all(oracle_identity_values) and all(local_identity_values)
        category_passes["quadratic_identities"].append(identities_pass)

        corrupt_product = local.jordan(x, y, corrupt=True)
        if corrupt_product != _qlist(case["product"]):
            corrupt_product_mismatches.append(label)

        case_evidence.append(
            {
                "label": label,
                "input_reproduction": inputs_pass,
                "product": product_pass,
                "trace": trace_pass,
                "determinant": determinant_pass,
                "minimal_polynomial": minpoly_pass,
                "quadratic_representation": quadratic_pass,
                "quadratic_identities": identities_pass,
            }
        )

    for category, values in category_passes.items():
        record(category, bool(values) and all(values), {"passed": sum(values), "total": len(values)})

    record(
        "corrupted_product_kill",
        "kill_fano_e1_e2" in corrupt_product_mismatches,
        {"mismatch_cases": corrupt_product_mismatches, "required_witness": "kill_fano_e1_e2"},
    )

    provenance = result["provenance"]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=provenance["alco_checkout"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    record(
        "alco_commit_pin",
        commit == provenance["expected_alco_commit"] == provenance["observed_alco_commit"],
        {"expected": provenance["expected_alco_commit"], "observed": commit},
    )
    record(
        "alco_install_binding",
        Path(provenance["alco_install_path"]).resolve() == Path(provenance["alco_checkout"]).resolve()
        and provenance["alco_install_realpath"] == str(Path(provenance["alco_checkout"]).resolve()),
        {
            "install_path": provenance["alco_install_path"],
            "install_realpath": provenance["alco_install_realpath"],
            "checkout": provenance["alco_checkout"],
        },
    )
    record(
        "alco_tracked_sources_clean",
        provenance.get("alco_tracked_status_short") == "",
        provenance.get("alco_tracked_status_short"),
    )

    hash_rows: list[dict[str, Any]] = []
    for group_name in ("sources", "dependencies"):
        for name, entry in sorted(provenance[group_name].items()):
            current = _current_hash(entry)
            hash_rows.append(
                {
                    "group": group_name,
                    "name": name,
                    "path": entry["path"],
                    "kind": entry["kind"],
                    "expected_sha256": entry["sha256"],
                    "current_sha256": current,
                    "pass": current == entry["sha256"],
                }
            )
    record("source_dependency_hashes", all(row["pass"] for row in hash_rows), hash_rows)
    record(
        "deterministic_contract",
        result.get("deterministic") is True and "generated_at" not in result and "timestamp" not in result,
        {"deterministic": result.get("deterministic"), "top_level_keys": sorted(result)},
    )

    all_pass = all(check["pass"] for check in checks)
    return {
        "schema": "codex_ratchet.alco_j3o_exact_oracle_validation.v1",
        "sim_id": result["sim_id"],
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "case_evidence": case_evidence,
        "checks": checks,
        "gate_counts": {
            "passed": sum(1 for check in checks if check["pass"]),
            "failed": sum(1 for check in checks if not check["pass"]),
            "total": len(checks),
        },
        "all_pass": all_pass,
        "accepted_status_label": "passes local rerun" if all_pass else "runs",
        "found_fabrication": False,
        "fabrication_audit_scope": "mechanical wrong-product and exact-equality controls only; no independent fresh-context semantic auditor ran",
        "authority_statement": result["authority_statement"],
        "blocked_consumers": result["blocked_consumers"],
    }


def write_validation(result_path: Path = RESULT_PATH, validation_path: Path = VALIDATION_PATH) -> dict[str, Any]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    validation = validate_result(result)
    validation["validated_result"] = {
        "path": str(result_path),
        "sha256": sha256_file(result_path),
    }
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return validation


def main() -> int:
    validation = write_validation()
    print(
        "ALCO_J3O_EXACT_ORACLE_VALIDATION "
        f"passed={validation['gate_counts']['passed']} "
        f"failed={validation['gate_counts']['failed']} "
        f"all_pass={validation['all_pass']}"
    )
    print(f"wrote: {VALIDATION_PATH}")
    return 0 if validation["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

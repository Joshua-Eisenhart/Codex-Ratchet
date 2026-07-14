#!/usr/bin/env python3
"""Closed-schema, hash-bound validator for the full-surface campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "codex-ratchet.full-surface-campaign-envelope.v1"
EXPECTED_LEV_COMMIT = "856acb1a5de42528a9a54272435d98a9fe226186"
EXPECTED_JULIA_EXECUTABLE = "/opt/homebrew/bin/julia"
EXPECTED_JULIA_CORRECTION_PROJECT = Path(
    "/Users/joshuaeisenhart/.julia/environments/v1.12/Project.toml"
)
EXPECTED_JULIA_CORRECTION_PROJECT_SHA256 = "227ee35210c2aa0939f0d175a606279ab194a1a4835f30e3b0051188d79d50a6"
EXPECTED_JULIA_CORRECTION_MANIFEST_SHA256 = "3aea8d29321024ed71d8de46b292a3ab03247214c40575ca8ca6ad9620aeff18"
EXPECTED_JULIA_CANDIDATE_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier"
EXPECTED_ENZYME_VERSION = "0.13.154"
EXPECTED_ENZYME_CANDIDATE_CODE = (
    "using Enzyme; f(x)=sin(x)^2; autodiff(Reverse,f,Active,Active(0.3))"
)
EXPECTED_SUITE_BINDING_PATHS = [
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/flow.yaml",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/full_surface_campaign.eval.js",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/target.md",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/lev/zero_execution.eval.js",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/test_validate_full_surface.py",
    "system_v5/ops/tooling/claude_campaign_20260713/full_surface/validate_full_surface.py",
]
EXPECTED_ARCHIVE_MEMBERS = {
    "julia_canon/src/ExceptionalAlgebraCanon.jl",
    "sims_and_scripts/living_purgatory_ledger_r2_results.json",
    "sims_and_scripts/ontological_finitude_cosmogenesis_ratchet_sim.py",
}
TOP_KEYS = {
    "schema",
    "campaign_id",
    "created_at",
    "started_at",
    "duration_seconds",
    "command",
    "runner_identity",
    "lev_executor",
    "source",
    "archive",
    "artifact_root",
    "classification",
    "promotion_allowed",
    "partial_promotion_allowed",
    "formal_admission_allowed",
    "provider_advisory_is_evidence",
    "projection_only",
    "runner_all_completed",
    "bounded_observations_all_pass",
    "all_pass",
    "truth_state",
    "summary",
    "groups",
    "set_coverage",
    "blocked_inventory",
    "tool_calls",
    "claim_ceiling",
    "blocked_consumers",
}
GROUP_KEYS = {
    "id",
    "kind",
    "classification",
    "sources",
    "commands",
    "artifacts",
    "required_artifact_count",
    "execution_completed",
    "bounded_pass",
    "science_evidence",
    "status",
    "claim_ceiling",
    "blockers",
    "blocked_consumers",
    "red_preservation_required",
}
COMMAND_KEYS = {
    "command",
    "cwd",
    "environment_overrides",
    "started_at",
    "finished_at",
    "duration_seconds",
    "exit_code",
    "timed_out",
    "stdout_path",
    "stdout_sha256",
    "stderr_path",
    "stderr_sha256",
}
ARTIFACT_KEYS = {"path", "sha256"}
FILE_SOURCE_KEYS = {"kind", "path", "sha256", "provenance"}
ARCHIVE_SOURCE_KEYS = {"kind", "path", "member", "sha256", "provenance"}
EVIDENCE_KEYS = {
    "kind",
    "artifact_path",
    "json_pointer",
    "command_index",
    "observed",
    "pass_value",
}
SUMMARY_KEYS = {
    "group_count",
    "command_count",
    "executed_command_count",
    "execution_failed_count",
    "bounded_pass_count",
    "bounded_red_count",
    "bounded_not_assessed_count",
    "blocked_inventory_count",
    "set_count",
    "set_evidence_complete_count",
    "set_bounded_green_count",
    "set_red_count",
    "set_partial_count",
    "set_execution_blocked_count",
}
SET_KEYS = {
    "set_id",
    "group_ids",
    "status",
    "blockers",
    "findings",
    "observations",
    "promotion_allowed",
}
SET_OBSERVATION_KEYS = {
    "observation_id",
    "group_id",
    "kind",
    "artifact_path",
    "json_pointer",
    "observed",
    "pass_value",
}
INVENTORY_KEYS = {"id", "status", "source_count", "sources", "reason"}
INVENTORY_SOURCE_KEYS = {"path", "sha256", "reason"}
TOOL_CALL_KEYS = {"tool", "function", "observable"}
RUNNER_IDENTITY_KEYS = {
    "python_executable",
    "python_version",
    "platform",
    "pid",
}
LEV_EXECUTOR_KEYS = {
    "worktree",
    "git_commit",
    "git_tree",
    "suite_bindings",
    "expected_status",
    "expected_suite_status",
    "projection_only",
    "release_eligible",
}
BINDING_KEYS = {"path", "sha256"}
CORRECTION_RECEIPT_KEYS = {
    "schema",
    "created_at",
    "command",
    "runtime",
    "project",
    "sources",
    "checks",
    "all_pass",
    "claim_ceiling",
    "promotion_allowed",
}
CORRECTION_RUNTIME_KEYS = {
    "julia_executable",
    "julia_version",
    "active_project",
    "enzyme_path",
    "enzyme_version",
}
CORRECTION_PROJECT_KEYS = {
    "project_toml_path",
    "project_toml_sha256",
    "manifest_toml_path",
    "manifest_toml_sha256",
}
CORRECTION_SOURCES_KEYS = {"correction_script", "archive_canon"}
CORRECTION_SOURCE_KEYS = {"path", "sha256"}
CORRECTION_CHECK_KEYS = {
    "candidate_failure_reproduced",
    "observed",
    "tolerance",
    "corrected_pass",
    "must_fail_control_fired",
}
CORRECTION_CHECK_IDS = {
    "albert_component_norm",
    "clifford_rotor_identity",
    "enzyme_reverse_gradient",
}
CORRECTION_OBSERVED_KEYS = {
    "albert_component_norm": {
        "component_norm",
        "candidate_error",
        "synthetic_component_norm",
    },
    "clifford_rotor_identity": {
        "gp_squared",
        "one_gp",
        "e1_squared",
        "candidate_error",
    },
    "enzyme_reverse_gradient": {
        "gradient_error",
        "shifted_target_error",
        "candidate_command",
        "candidate_julia_project",
        "candidate_exit_code",
    },
}
FORBIDDEN_AUTHORITY_KEYS = {
    "provider_as_evidence",
    "provider_evidence",
    "provider_gate_pass",
    "provider_authority",
    "advisory_gate_pass",
    "provisional_promotion",
    "partial_promotion",
    "partial_promotion_status",
    "projection_pass",
    "projection_authority",
    "replay_allowed",
    "authority_override",
    "candidate_hash_override",
}
GROUP_CONTRACTS = {
    "hardened_d_f_j_k_h": ("hardened_stress_chain", 1, "artifact_json", "/all_pass", None, True, True),
    "imported_python_battery": ("imported_candidate_battery", 1, "artifact_json", "/fail", None, 0, True),
    "imported_fit_sweep": ("imported_candidate_battery", 1, "artifact_json", "/fail", None, 0, True),
    "imported_julia_battery": ("imported_candidate_battery", 1, "artifact_json", "/fail", None, 0, True),
    "julia_correction_probes": ("source_backed_correction_probe", 3, "artifact_json", "/all_pass", None, True, True),
    "foundation_entropy_gradient": ("foundation_scratch_diagnostic", 1, "artifact_json", "/FOLLOWS_RATCHET_RULES", None, True, True),
    "foundation_forcing_robustness": ("foundation_scratch_diagnostic", 1, "artifact_json", "/policy_eval/FOUNDATIONS_EARNED_FORCED_ROBUST_LOADBEARING", None, True, True),
    "foundation_drive_mss_tiebreak": ("foundation_scratch_diagnostic", 1, "artifact_json", "/policy_eval/ROOT_DRIVE_AND_TIEBREAK_AUDITED", None, True, True),
    "manifold_dual_ratchet_foundations_v0": ("cross_runtime_foundation_diagnostic", 1, "artifact_json", "/parity_passed", None, True, True),
    "manifold_dual_ratchet_foundations_v0_1": ("cross_runtime_foundation_diagnostic", 1, "artifact_json", "/parity_passed", None, True, True),
    "legacy_engine_1q": ("legacy_cross_substrate_engine_diagnostic", 4, "command_exit", None, 4, 0, True),
    "legacy_engine_3q": ("legacy_cross_substrate_engine_diagnostic", 4, "command_exit", None, 4, 0, True),
    "ratchet_process_v1_tests": ("process_gate_test", 0, "command_exit", None, 0, 0, True),
    "qics_entropy_dpi_oracle": ("pinned_external_oracle_diagnostic", 1, "artifact_json", "/all_tests_pass", None, True, True),
    "lean_formal_surface": ("formal_build", 0, "command_exit", None, 0, 0, True),
    "grok45_advisory_validation": ("provider_advisory_validation", 0, "command_exit", None, 0, 0, False),
}
BASE_GROUP_IDS = set(GROUP_CONTRACTS) - {"grok45_advisory_validation"}
SET_CONTRACTS = {
    "A": {
        "group_ids": ["imported_python_battery"],
        "blockers": [],
        "findings": [],
        "observations": {
            "A_z3_flip": ("imported_python_battery", "artifact_json", "/results/z3_unsat_sat_flip/status", "PASS"),
            "A_cvc5_flip": ("imported_python_battery", "artifact_json", "/results/cvc5_unsat_sat_flip/status", "PASS"),
            "A_solver_agreement": ("imported_python_battery", "artifact_json", "/results/z3_cvc5_agreement/status", "PASS"),
            "A_sympy_identity": ("imported_python_battery", "artifact_json", "/results/sympy_exact_identity/status", "PASS"),
        },
    },
    "B": {
        "group_ids": ["julia_correction_probes", "imported_julia_battery"],
        "blockers": [],
        "findings": [
            "frozen imported Julia battery remains 12/15 red; corrected Albert, Clifford, and Enzyme probes show candidate API/environment defects"
        ],
        "observations": {
            "B_albert_identity": ("julia_correction_probes", "artifact_json", "/checks/albert_component_norm/corrected_pass", True),
            "B_octonion_associator": ("imported_julia_battery", "artifact_json", "/results/canon_module_octonion_associator/status", "PASS"),
        },
    },
    "C": {
        "group_ids": ["imported_python_battery", "legacy_engine_1q", "legacy_engine_3q"],
        "blockers": [],
        "findings": [],
        "observations": {
            "C_jax_torch_agreement": ("imported_python_battery", "artifact_json", "/results/jax_torch_numerical_agreement/status", "PASS"),
            "C_legacy_1q": ("legacy_engine_1q", "group_bounded_pass", None, True),
            "C_legacy_3q": ("legacy_engine_3q", "group_bounded_pass", None, True),
        },
    },
    "D": {
        "group_ids": ["hardened_d_f_j_k_h"],
        "blockers": [],
        "findings": [],
        "observations": {"D_basin_chain": ("hardened_d_f_j_k_h", "artifact_json", "/lanes/0/receipt_all_pass", True)},
    },
    "E": {
        "group_ids": ["imported_python_battery"],
        "blockers": ["fixture-level Maude only"],
        "findings": [],
        "observations": {"E_maude_bracketing": ("imported_python_battery", "artifact_json", "/results/maude_t01_bracketing_flip/status", "PASS")},
    },
    "F": {
        "group_ids": ["hardened_d_f_j_k_h"],
        "blockers": [],
        "findings": [],
        "observations": {"F_structured_transport": ("hardened_d_f_j_k_h", "artifact_json", "/lanes/1/receipt_all_pass", True)},
    },
    "G": {
        "group_ids": ["imported_fit_sweep", "imported_julia_battery"],
        "blockers": [],
        "findings": [],
        "observations": {
            "G_dynamiqs_qutip": ("imported_fit_sweep", "artifact_json", "/results/dynamiqs_qutip_cross_agreement/status", "PASS"),
            "G_quantumoptics_trace": ("imported_julia_battery", "artifact_json", "/results/quantumoptics_lindblad_trace/status", "PASS"),
        },
    },
    "H": {
        "group_ids": ["hardened_d_f_j_k_h"],
        "blockers": [],
        "findings": ["native ledger accepts a cycle and no ancestry-DAG rule was found"],
        "observations": {"H_lineage_semantics": ("hardened_d_f_j_k_h", "artifact_json", "/lanes/4/receipt_all_pass", True)},
    },
    "I": {
        "group_ids": ["imported_fit_sweep"],
        "blockers": ["Flux/Lux consumer chain not executed"],
        "findings": [],
        "observations": {
            "I_e3nn_equivariance": ("imported_fit_sweep", "artifact_json", "/results/e3nn_exact_equivariance/status", "PASS"),
            "I_pyg_equivariance": ("imported_fit_sweep", "artifact_json", "/results/pyg_permutation_equivariance/status", "PASS"),
            "I_learning_control": ("imported_fit_sweep", "artifact_json", "/results/torch_learning_with_shuffle_control/status", "PASS"),
        },
    },
    "J": {
        "group_ids": ["hardened_d_f_j_k_h", "imported_fit_sweep"],
        "blockers": ["Julia IntervalArithmetic leg not executed"],
        "findings": [],
        "observations": {
            "J_autolirpa": ("hardened_d_f_j_k_h", "artifact_json", "/lanes/2/receipt_all_pass", True),
            "J_interval_fixture": ("imported_fit_sweep", "artifact_json", "/results/interval_certified_bound/status", "PASS"),
        },
    },
    "K": {
        "group_ids": ["hardened_d_f_j_k_h", "imported_fit_sweep", "imported_julia_battery"],
        "blockers": [],
        "findings": [],
        "observations": {
            "K_hardened_tensor_chain": ("hardened_d_f_j_k_h", "artifact_json", "/lanes/3/receipt_all_pass", True),
            "K_quimb_entropy": ("imported_fit_sweep", "artifact_json", "/results/quimb_ghz_cut_entropy/status", "PASS"),
            "K_itensors_norm": ("imported_julia_battery", "artifact_json", "/results/itensors_mps_norm/status", "PASS"),
        },
    },
    "L": {
        "group_ids": ["lean_formal_surface", "qics_entropy_dpi_oracle"],
        "blockers": ["ALCO and physlib legs blocked"],
        "findings": [],
        "observations": {
            "L_lean_build": ("lean_formal_surface", "group_bounded_pass", None, True),
            "L_qics_oracle": ("qics_entropy_dpi_oracle", "group_bounded_pass", None, True),
        },
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def closed(errors: list[str], value: Any, keys: set[str], label: str) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    extra = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    if extra:
        errors.append(f"{label} unknown fields: {', '.join(extra)}")
    if missing:
        errors.append(f"{label} missing fields: {', '.join(missing)}")
    return not extra and not missing


def validate_julia_correction_receipt(
    payload: Any,
    row: dict[str, Any],
    errors: list[str],
    label: str,
) -> None:
    receipt_label = f"{label}.correction_receipt"
    if not closed(errors, payload, CORRECTION_RECEIPT_KEYS, receipt_label):
        return
    add(
        errors,
        payload["schema"] == "codex-ratchet.julia-correction-probes.v1",
        f"{receipt_label} schema mismatch",
    )
    add(errors, timestamp_ok(payload["created_at"]), f"{receipt_label} timestamp invalid")
    add(errors, payload["command"] == row["commands"][0]["command"], f"{receipt_label} command mismatch")
    add(errors, payload["promotion_allowed"] is False, f"{receipt_label} promotion must remain false")
    add(
        errors,
        payload["claim_ceiling"]
        == "Machine-local Julia API/environment correction probes only; no scientific admission or portable/canonical environment claim.",
        f"{receipt_label} claim ceiling mismatch",
    )

    runtime = payload["runtime"]
    if closed(errors, runtime, CORRECTION_RUNTIME_KEYS, f"{receipt_label}.runtime"):
        add(
            errors,
            runtime["julia_executable"] == EXPECTED_JULIA_EXECUTABLE
            == row["commands"][0]["command"][0],
            f"{receipt_label} Julia executable mismatch",
        )
        add(errors, runtime["julia_version"] == "1.12.6", f"{receipt_label} Julia version mismatch")
        add(
            errors,
            runtime["active_project"] == str(EXPECTED_JULIA_CORRECTION_PROJECT),
            f"{receipt_label} active project mismatch",
        )
        enzyme_path = Path(str(runtime["enzyme_path"]))
        add(
            errors,
            bool(
                re.fullmatch(
                    r"/Users/joshuaeisenhart/\.julia/packages/Enzyme/[^/]+/src/Enzyme\.jl",
                    str(enzyme_path),
                )
            ),
            f"{receipt_label} Enzyme package path mismatch",
        )
        add(errors, runtime["enzyme_version"] == EXPECTED_ENZYME_VERSION, f"{receipt_label} Enzyme version mismatch")

    project = payload["project"]
    if closed(errors, project, CORRECTION_PROJECT_KEYS, f"{receipt_label}.project"):
        project_path = Path(str(project["project_toml_path"]))
        manifest_path = Path(str(project["manifest_toml_path"]))
        add(errors, project_path == EXPECTED_JULIA_CORRECTION_PROJECT, f"{receipt_label} Project.toml path mismatch")
        add(
            errors,
            manifest_path == EXPECTED_JULIA_CORRECTION_PROJECT.with_name("Manifest.toml"),
            f"{receipt_label} Manifest.toml path mismatch",
        )
        add(
            errors,
            project["project_toml_sha256"] == EXPECTED_JULIA_CORRECTION_PROJECT_SHA256,
            f"{receipt_label} pinned Project.toml hash mismatch",
        )
        add(
            errors,
            project["manifest_toml_sha256"] == EXPECTED_JULIA_CORRECTION_MANIFEST_SHA256,
            f"{receipt_label} pinned Manifest.toml hash mismatch",
        )
        add(
            errors,
            isinstance(runtime, dict) and runtime.get("active_project") == str(project_path),
            f"{receipt_label} active project mismatch",
        )
        add(
            errors,
            row["commands"][0]["command"][2] == f"--project={project_path.parent}",
            f"{receipt_label} project command mismatch",
        )
        project_artifact = next(
            (
                artifact
                for artifact in row["artifacts"]
                if artifact.get("path", "").endswith("julia_correction_Project.toml")
            ),
            None,
        )
        manifest_artifact = next(
            (
                artifact
                for artifact in row["artifacts"]
                if artifact.get("path", "").endswith("julia_correction_Manifest.toml")
            ),
            None,
        )
        add(errors, project_artifact is not None, f"{receipt_label} Project.toml snapshot missing")
        add(errors, manifest_artifact is not None, f"{receipt_label} Manifest.toml snapshot missing")
        if project_artifact is not None:
            add(
                errors,
                project_artifact.get("sha256") == project["project_toml_sha256"],
                f"{receipt_label} Project.toml snapshot hash mismatch",
            )
        if manifest_artifact is not None:
            add(
                errors,
                manifest_artifact.get("sha256") == project["manifest_toml_sha256"],
                f"{receipt_label} Manifest.toml snapshot hash mismatch",
            )

    sources = payload["sources"]
    if closed(errors, sources, CORRECTION_SOURCES_KEYS, f"{receipt_label}.sources"):
        for source_id in sorted(CORRECTION_SOURCES_KEYS):
            closed(errors, sources[source_id], CORRECTION_SOURCE_KEYS, f"{receipt_label}.sources.{source_id}")
        file_source = next(
            (source for source in row["sources"] if source.get("kind") == "file"),
            None,
        )
        archive_source_record = next(
            (source for source in row["sources"] if source.get("kind") == "archive_member"),
            None,
        )
        if file_source is not None:
            add(
                errors,
                sources["correction_script"].get("sha256") == file_source.get("sha256"),
                f"{receipt_label} correction source hash mismatch",
            )
        else:
            errors.append(f"{receipt_label} correction source missing")
        if archive_source_record is not None:
            add(
                errors,
                sources["archive_canon"].get("sha256") == archive_source_record.get("sha256"),
                f"{receipt_label} archive canon hash mismatch",
            )
        else:
            errors.append(f"{receipt_label} archive canon source missing")

    checks = payload["checks"]
    add(errors, isinstance(checks, dict) and set(checks) == CORRECTION_CHECK_IDS, f"{receipt_label} check inventory mismatch")
    structurally_valid = isinstance(checks, dict)
    if isinstance(checks, dict):
        for check_id in sorted(CORRECTION_CHECK_IDS):
            check = checks.get(check_id)
            check_label = f"{receipt_label}.checks.{check_id}"
            if not closed(errors, check, CORRECTION_CHECK_KEYS, check_label):
                structurally_valid = False
                continue
            observed = check["observed"]
            if not closed(errors, observed, CORRECTION_OBSERVED_KEYS[check_id], f"{check_label}.observed"):
                structurally_valid = False
            for field in (
                "candidate_failure_reproduced",
                "corrected_pass",
                "must_fail_control_fired",
            ):
                add(errors, isinstance(check[field], bool), f"{check_label}.{field} invalid")

    def finite_number(value: Any) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )

    derived_flags: dict[str, tuple[bool, bool, bool]] = {}
    if structurally_valid and isinstance(checks, dict):
        albert = checks["albert_component_norm"]
        albert_observed = albert["observed"]
        albert_candidate = (
            isinstance(albert_observed["candidate_error"], str)
            and "MethodError" in albert_observed["candidate_error"]
            and "isless(::Albert" in albert_observed["candidate_error"]
        )
        albert_corrected = (
            albert["tolerance"] == 1.0e-12
            and finite_number(albert_observed["component_norm"])
            and 0.0 <= float(albert_observed["component_norm"]) < 1.0e-12
        )
        albert_control = (
            finite_number(albert_observed["synthetic_component_norm"])
            and float(albert_observed["synthetic_component_norm"]) >= 1.0e-12
        )
        derived_flags["albert_component_norm"] = (
            albert_candidate,
            albert_corrected,
            albert_control,
        )

        clifford = checks["clifford_rotor_identity"]
        clifford_observed = clifford["observed"]
        clifford_candidate = (
            isinstance(clifford_observed["candidate_error"], str)
            and "MethodError" in clifford_observed["candidate_error"]
            and "one(::CliffordAlgebra" in clifford_observed["candidate_error"]
        )
        clifford_corrected = (
            clifford["tolerance"] is None
            and clifford_observed["gp_squared"] == "-1 ∈ Cl(3, 0, 0)"
            and clifford_observed["one_gp"] == "+1 ∈ Cl(3, 0, 0)"
        )
        clifford_control = clifford_observed["e1_squared"] == "+1 ∈ Cl(3, 0, 0)"
        derived_flags["clifford_rotor_identity"] = (
            clifford_candidate,
            clifford_corrected,
            clifford_control,
        )

        enzyme = checks["enzyme_reverse_gradient"]
        enzyme_observed = enzyme["observed"]
        expected_candidate_command = [
            EXPECTED_JULIA_EXECUTABLE,
            "--startup-file=no",
            "-e",
            EXPECTED_ENZYME_CANDIDATE_CODE,
        ]
        enzyme_candidate = (
            enzyme_observed["candidate_command"] == expected_candidate_command
            and enzyme_observed["candidate_julia_project"] == EXPECTED_JULIA_CANDIDATE_PROJECT
            and isinstance(enzyme_observed["candidate_exit_code"], int)
            and not isinstance(enzyme_observed["candidate_exit_code"], bool)
            and enzyme_observed["candidate_exit_code"] != 0
        )
        enzyme_corrected = (
            enzyme["tolerance"] == 1.0e-12
            and finite_number(enzyme_observed["gradient_error"])
            and 0.0 <= float(enzyme_observed["gradient_error"]) < 1.0e-12
        )
        enzyme_control = (
            finite_number(enzyme_observed["shifted_target_error"])
            and float(enzyme_observed["shifted_target_error"]) >= 1.0e-12
        )
        derived_flags["enzyme_reverse_gradient"] = (
            enzyme_candidate,
            enzyme_corrected,
            enzyme_control,
        )

        for check_id, expected in derived_flags.items():
            check = checks[check_id]
            for field, derived in zip(
                (
                    "candidate_failure_reproduced",
                    "corrected_pass",
                    "must_fail_control_fired",
                ),
                expected,
                strict=True,
            ):
                add(
                    errors,
                    check[field] is derived,
                    f"{receipt_label}.checks.{check_id}.{field} observation mismatch",
                )
    derived_pass = (
        structurally_valid
        and set(derived_flags) == CORRECTION_CHECK_IDS
        and all(all(flags) for flags in derived_flags.values())
    )
    add(errors, payload["all_pass"] is derived_pass, f"{receipt_label} all_pass mismatch")


def timestamp_ok(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def pointer(payload: Any, path: str) -> Any:
    value = payload
    for token in path.strip("/").split("/") if path != "/" else []:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def scan_forbidden(value: Any, errors: list[str], prefix: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_AUTHORITY_KEYS:
                errors.append(f"forbidden authority alias at {prefix}.{key}")
            if lowered.startswith("partial_promotion") and lowered != "partial_promotion_allowed":
                errors.append(f"forbidden partial-promotion alias at {prefix}.{key}")
            scan_forbidden(child, errors, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_forbidden(child, errors, f"{prefix}[{index}]")


def validate_source(
    record: Any,
    errors: list[str],
    label: str,
    *,
    source_commit: str,
    repo_root: Path,
    provider_advisory: bool,
) -> None:
    if not isinstance(record, dict):
        errors.append(f"{label} must be an object")
        return
    kind = record.get("kind")
    expected = FILE_SOURCE_KEYS if kind == "file" else ARCHIVE_SOURCE_KEYS if kind == "archive_member" else set()
    if not expected:
        errors.append(f"{label}.kind invalid")
        return
    closed(errors, record, expected, label)
    path = Path(str(record.get("path", "")))
    if kind == "file":
        if provider_advisory:
            add(errors, path.is_file(), f"{label} advisory file missing")
            if path.is_file():
                add(
                    errors,
                    sha256_file(path) == record.get("sha256"),
                    f"{label} advisory file hash mismatch",
                )
        else:
            try:
                relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                relative = ""
            add(errors, bool(relative), f"{label} non-advisory file must be repo-bound")
            if relative:
                result = subprocess.run(
                    ["git", "show", f"{source_commit}:{relative}"],
                    cwd=repo_root,
                    capture_output=True,
                    check=False,
                )
                add(errors, result.returncode == 0, f"{label} absent from source commit")
                if result.returncode == 0:
                    add(
                        errors,
                        hashlib.sha256(result.stdout).hexdigest() == record.get("sha256"),
                        f"{label} commit hash mismatch or replayed source",
                    )
    else:
        member = record.get("member")
        add(errors, path.is_file(), f"{label} archive missing")
        try:
            with zipfile.ZipFile(path) as bundle:
                data = bundle.read(str(member))
            add(errors, hashlib.sha256(data).hexdigest() == record.get("sha256"), f"{label} archive member hash mismatch")
        except (OSError, KeyError, zipfile.BadZipFile):
            errors.append(f"{label} archive member unreadable")


def validate_artifact(
    record: Any,
    errors: list[str],
    label: str,
    *,
    artifact_root: Path,
) -> None:
    if not closed(errors, record, ARTIFACT_KEYS, label):
        return
    path = Path(str(record["path"]))
    try:
        path.resolve().relative_to(artifact_root.resolve())
        contained = True
    except ValueError:
        contained = False
    add(errors, contained, f"{label} outside artifact root")
    add(errors, path.is_file(), f"{label} missing")
    if path.is_file():
        add(errors, sha256_file(path) == record["sha256"], f"{label} hash mismatch")


def validate_command(
    record: Any,
    errors: list[str],
    label: str,
    *,
    artifact_root: Path,
) -> None:
    if not closed(errors, record, COMMAND_KEYS, label):
        return
    add(errors, isinstance(record["command"], list) and bool(record["command"]), f"{label}.command invalid")
    add(errors, isinstance(record["environment_overrides"], dict), f"{label}.environment_overrides invalid")
    add(errors, timestamp_ok(record["started_at"]), f"{label}.started_at invalid")
    add(errors, timestamp_ok(record["finished_at"]), f"{label}.finished_at invalid")
    add(errors, isinstance(record["duration_seconds"], (int, float)) and record["duration_seconds"] >= 0, f"{label}.duration invalid")
    add(errors, isinstance(record["timed_out"], bool), f"{label}.timed_out invalid")
    add(errors, record["exit_code"] is None or isinstance(record["exit_code"], int), f"{label}.exit_code invalid")
    for stream in ("stdout", "stderr"):
        path = Path(str(record[f"{stream}_path"]))
        try:
            path.resolve().relative_to(artifact_root.resolve())
            contained = True
        except ValueError:
            contained = False
        add(errors, contained, f"{label}.{stream} outside artifact root")
        add(errors, path.is_file(), f"{label}.{stream} missing")
        if path.is_file():
            add(errors, sha256_file(path) == record[f"{stream}_sha256"], f"{label}.{stream} hash mismatch")


def validate_group(
    row: Any,
    errors: list[str],
    index: int,
    *,
    source_commit: str,
    repo_root: Path,
    artifact_root: Path,
) -> None:
    label = f"groups[{index}]"
    if not closed(errors, row, GROUP_KEYS, label):
        return
    add(errors, row["classification"] == "integration_diagnostic", f"{label} classification mismatch")
    add(errors, isinstance(row["id"], str) and bool(row["id"]), f"{label}.id invalid")
    add(errors, isinstance(row["commands"], list) and bool(row["commands"]), f"{label}.commands invalid")
    add(errors, isinstance(row["sources"], list) and bool(row["sources"]), f"{label}.sources invalid")
    add(errors, isinstance(row["artifacts"], list), f"{label}.artifacts invalid")
    add(
        errors,
        isinstance(row["required_artifact_count"], int)
        and not isinstance(row["required_artifact_count"], bool)
        and row["required_artifact_count"] >= 0,
        f"{label}.required_artifact_count invalid",
    )
    add(errors, isinstance(row["blockers"], list), f"{label}.blockers invalid")
    add(errors, isinstance(row["blocked_consumers"], list) and bool(row["blocked_consumers"]), f"{label}.blocked_consumers invalid")
    add(errors, isinstance(row["claim_ceiling"], str) and bool(row["claim_ceiling"]), f"{label}.claim_ceiling invalid")
    add(
        errors,
        isinstance(row["red_preservation_required"], bool),
        f"{label}.red_preservation_required invalid",
    )
    contract = GROUP_CONTRACTS.get(row["id"])
    add(errors, contract is not None, f"{label} unexpected group id")
    if contract is not None:
        (
            expected_kind,
            required_count,
            evidence_kind,
            evidence_pointer,
            contract_command_index,
            pass_value,
            preserve_red,
        ) = contract
        add(errors, row["kind"] == expected_kind, f"{label}.kind contract mismatch")
        add(
            errors,
            row["required_artifact_count"] == required_count,
            f"{label}.required_artifact_count contract mismatch",
        )
        add(
            errors,
            row["red_preservation_required"] is preserve_red,
            f"{label}.red preservation contract mismatch",
        )
    provider_advisory = row["kind"] == "provider_advisory_validation"
    for source_index, source in enumerate(row["sources"]):
        validate_source(
            source,
            errors,
            f"{label}.sources[{source_index}]",
            source_commit=source_commit,
            repo_root=repo_root,
            provider_advisory=provider_advisory,
        )
    for command_index, command in enumerate(row["commands"]):
        validate_command(
            command,
            errors,
            f"{label}.commands[{command_index}]",
            artifact_root=artifact_root,
        )
    for artifact_index, artifact in enumerate(row["artifacts"]):
        validate_artifact(
            artifact,
            errors,
            f"{label}.artifacts[{artifact_index}]",
            artifact_root=artifact_root,
        )
    derived_execution = all(
        command.get("timed_out") is False and command.get("exit_code") is not None
        for command in row["commands"]
    ) and len(row["artifacts"]) >= row["required_artifact_count"]
    add(errors, row["execution_completed"] is derived_execution, f"{label}.execution_completed mismatch")
    evidence = row["science_evidence"]
    if not closed(errors, evidence, EVIDENCE_KEYS, f"{label}.science_evidence"):
        return
    if contract is not None:
        add(errors, evidence["kind"] == evidence_kind, f"{label} evidence kind contract mismatch")
        add(
            errors,
            evidence["json_pointer"] == evidence_pointer,
            f"{label} evidence pointer contract mismatch",
        )
        add(
            errors,
            evidence["command_index"] == contract_command_index,
            f"{label} evidence command contract mismatch",
        )
        add(
            errors,
            evidence["pass_value"] == pass_value,
            f"{label} evidence pass value contract mismatch",
        )
    observed = None
    payload: Any = None
    if evidence["kind"] == "artifact_json":
        artifact_paths = {artifact["path"] for artifact in row["artifacts"] if isinstance(artifact, dict)}
        add(errors, evidence["artifact_path"] in artifact_paths, f"{label} evidence artifact not declared")
        try:
            payload = json.loads(Path(evidence["artifact_path"]).read_text(encoding="utf-8"))
            observed = pointer(payload, evidence["json_pointer"])
        except (OSError, json.JSONDecodeError, KeyError, IndexError, TypeError):
            errors.append(f"{label} evidence JSON/pointer unreadable")
        add(errors, evidence["command_index"] is None, f"{label} artifact evidence command_index must be null")
    elif evidence["kind"] == "command_exit":
        command_index = evidence["command_index"]
        add(errors, isinstance(command_index, int) and 0 <= command_index < len(row["commands"]), f"{label} evidence command_index invalid")
        if isinstance(command_index, int) and 0 <= command_index < len(row["commands"]):
            observed = row["commands"][command_index]["exit_code"]
        add(errors, evidence["artifact_path"] is None and evidence["json_pointer"] is None, f"{label} command evidence paths must be null")
    else:
        errors.append(f"{label} science evidence kind invalid")
    add(errors, observed == evidence["observed"], f"{label} evidence observed value mismatch")
    if row["id"] == "julia_correction_probes":
        validate_julia_correction_receipt(payload, row, errors, label)
    if provider_advisory:
        add(errors, row["bounded_pass"] is None, f"{label} provider advisory cannot be a bounded pass")
        expected_status = "bounded_not_assessed" if derived_execution else "execution_failed"
    else:
        derived_bounded = observed == evidence["pass_value"]
        add(errors, row["bounded_pass"] is derived_bounded, f"{label} bounded pass mismatch")
        expected_status = (
            "execution_failed"
            if not derived_execution
            else "bounded_pass"
            if derived_bounded
            else "bounded_red"
        )
    add(errors, row["status"] == expected_status, f"{label} status mismatch")


def validate(raw: dict[str, Any], *, envelope_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not closed(errors, raw, TOP_KEYS, "$"):
        return errors
    scan_forbidden(raw, errors)
    add(errors, raw["schema"] == EXPECTED_SCHEMA, "schema mismatch")
    add(errors, raw["campaign_id"] == "claude_campaign_20260713_full_surface_v1", "campaign id mismatch")
    add(errors, raw["classification"] == "integration_diagnostic", "classification mismatch")
    add(errors, raw["promotion_allowed"] is False, "promotion must remain false")
    add(errors, raw["partial_promotion_allowed"] is False, "partial promotion must remain false")
    add(errors, raw["formal_admission_allowed"] is False, "formal admission must remain false")
    add(errors, raw["provider_advisory_is_evidence"] is False, "provider advice must not be evidence")
    add(errors, raw["projection_only"] is False, "projection-only state cannot satisfy execution")
    add(errors, raw["all_pass"] is False, "campaign all_pass must remain false")
    add(errors, raw["truth_state"] == "host_recomputed_blocked", "truth_state mismatch")
    add(errors, timestamp_ok(raw["created_at"]) and timestamp_ok(raw["started_at"]), "timestamps invalid")
    add(errors, isinstance(raw["duration_seconds"], (int, float)) and raw["duration_seconds"] >= 0, "duration invalid")
    add(errors, isinstance(raw["claim_ceiling"], str) and bool(raw["claim_ceiling"]), "claim ceiling missing")
    add(errors, isinstance(raw["blocked_consumers"], list) and bool(raw["blocked_consumers"]), "blocked consumers missing")
    add(errors, isinstance(raw["tool_calls"], list) and bool(raw["tool_calls"]), "tool calls missing")
    for index, tool_call in enumerate(raw["tool_calls"]):
        closed(errors, tool_call, TOOL_CALL_KEYS, f"tool_calls[{index}]")

    runner_identity = raw["runner_identity"]
    if closed(errors, runner_identity, RUNNER_IDENTITY_KEYS, "runner_identity"):
        add(errors, isinstance(runner_identity["python_executable"], str), "runner python executable invalid")
        add(errors, isinstance(runner_identity["python_version"], str), "runner python version invalid")
        add(errors, isinstance(runner_identity["platform"], str), "runner platform invalid")
        add(errors, isinstance(runner_identity["pid"], int) and runner_identity["pid"] > 0, "runner pid invalid")

    lev_executor = raw["lev_executor"]
    if closed(errors, lev_executor, LEV_EXECUTOR_KEYS, "lev_executor"):
        lev_worktree = Path(str(lev_executor["worktree"]))
        add(errors, lev_worktree.is_dir(), "Lev executor worktree missing")
        lev_commit = str(lev_executor["git_commit"])
        add(errors, bool(re.fullmatch(r"[0-9a-f]{40}", lev_commit)), "Lev executor commit invalid")
        add(errors, lev_commit == EXPECTED_LEV_COMMIT, "Lev executor pinned commit mismatch")
        lev_object = subprocess.run(
            ["git", "cat-file", "-e", f"{lev_commit}^{{commit}}"],
            cwd=lev_worktree if lev_worktree.is_dir() else Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        add(errors, lev_object.returncode == 0, "Lev executor historical commit missing")
        lev_tree = subprocess.run(
            ["git", "rev-parse", f"{lev_commit}^{{tree}}"],
            cwd=lev_worktree if lev_worktree.is_dir() else Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        add(errors, lev_tree.returncode == 0, "Lev executor tree unreadable")
        if lev_tree.returncode == 0:
            add(errors, lev_tree.stdout.strip() == lev_executor["git_tree"], "Lev executor tree hash mismatch")
        suite_bindings = lev_executor["suite_bindings"]
        add(errors, isinstance(suite_bindings, list), "Lev suite bindings invalid")
        if isinstance(suite_bindings, list):
            for index, binding in enumerate(suite_bindings):
                closed(errors, binding, BINDING_KEYS, f"lev_executor.suite_bindings[{index}]")
            add(
                errors,
                [binding.get("path") for binding in suite_bindings if isinstance(binding, dict)]
                == EXPECTED_SUITE_BINDING_PATHS,
                "Lev suite binding inventory mismatch",
            )
        add(errors, lev_executor["expected_status"] == "projected", "Lev expected status mismatch")
        add(errors, lev_executor["expected_suite_status"] == "passed", "Lev expected suite status mismatch")
        add(errors, lev_executor["projection_only"] is True, "Lev projection fence missing")
        add(errors, lev_executor["release_eligible"] is False, "Lev release fence missing")

    artifact_root = Path(str(raw["artifact_root"]))
    add(errors, artifact_root.is_dir(), "artifact root missing")

    source = raw["source"]
    if closed(errors, source, {"path", "sha256", "git_commit"}, "source"):
        runner = Path(str(source["path"]))
        add(errors, runner.is_file(), "runner source missing")
        add(errors, bool(re.fullmatch(r"[0-9a-f]{40}", str(source["git_commit"]))), "source commit invalid")
        root_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=runner.parent if runner.is_file() else Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        repo_root = Path(root_result.stdout.strip()) if root_result.returncode == 0 else Path.cwd()
        try:
            runner_relative = runner.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            runner_relative = ""
        add(errors, bool(runner_relative), "runner source is outside repository")
        result = subprocess.run(
            ["git", "show", f"{source['git_commit']}:{runner_relative}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        ) if runner.is_file() and runner_relative else None
        add(errors, result is not None and result.returncode == 0, "runner absent from source commit")
        if result is not None and result.returncode == 0:
            add(errors, hashlib.sha256(result.stdout).hexdigest() == source["sha256"], "runner/source commit hash mismatch")
    else:
        repo_root = Path.cwd()

    if isinstance(lev_executor, dict) and isinstance(lev_executor.get("suite_bindings"), list):
        for index, binding in enumerate(lev_executor["suite_bindings"]):
            if not isinstance(binding, dict):
                continue
            path_value = binding.get("path")
            if not isinstance(path_value, str) or not path_value:
                continue
            committed_suite = subprocess.run(
                ["git", "show", f"{source.get('git_commit', '')}:{path_value}"],
                cwd=repo_root,
                capture_output=True,
                check=False,
            )
            add(errors, committed_suite.returncode == 0, f"Lev suite binding[{index}] absent from source commit")
            if committed_suite.returncode == 0:
                add(
                    errors,
                    hashlib.sha256(committed_suite.stdout).hexdigest() == binding.get("sha256"),
                    f"Lev suite binding[{index}] source hash mismatch",
                )

    archive = raw["archive"]
    if closed(errors, archive, {"path", "sha256", "members"}, "archive"):
        archive_path = Path(str(archive["path"]))
        add(errors, archive_path.is_file(), "archive missing")
        if archive_path.is_file():
            add(errors, sha256_file(archive_path) == archive["sha256"], "archive hash mismatch")
        add(errors, isinstance(archive["members"], list) and len(archive["members"]) == 3, "archive members mismatch")
        add(
            errors,
            {
                member.get("member")
                for member in archive["members"]
                if isinstance(member, dict)
            }
            == EXPECTED_ARCHIVE_MEMBERS,
            "archive member identities mismatch",
        )
        for index, member in enumerate(archive["members"] if isinstance(archive["members"], list) else []):
            validate_source(member, errors, f"archive.members[{index}]", source_commit=source.get("git_commit", ""), repo_root=repo_root, provider_advisory=False)

    command = raw["command"]
    add(errors, isinstance(command, list) and len(command) == 8, "top-level command shape invalid")
    if isinstance(command, list) and len(command) == 8:
        add(
            errors,
            Path(str(command[0])).resolve()
            == Path(str(runner_identity.get("python_executable", ""))).resolve(),
            "command/runtime mismatch",
        )
        add(errors, Path(str(command[1])).resolve() == Path(str(source.get("path", ""))).resolve(), "command/runner mismatch")
        add(errors, command[2:7:2] == ["--archive", "--output", "--artifact-dir"], "command option order mismatch")
        add(errors, Path(str(command[3])).resolve() == Path(str(archive.get("path", ""))).resolve(), "command/archive mismatch")
        add(errors, Path(str(command[7])).resolve() == artifact_root.resolve(), "command/artifact-root mismatch")

    groups = raw["groups"]
    add(errors, isinstance(groups, list) and bool(groups), "groups missing")
    if not isinstance(groups, list):
        return errors
    ids = [row.get("id") for row in groups if isinstance(row, dict)]
    add(errors, len(ids) == len(set(ids)), "duplicate group ids")
    observed_ids = set(ids)
    add(
        errors,
        frozenset(observed_ids)
        in {frozenset(BASE_GROUP_IDS), frozenset(GROUP_CONTRACTS)},
        "group inventory does not match the bounded campaign contract",
    )
    for index, row in enumerate(groups):
        validate_group(
            row,
            errors,
            index,
            source_commit=source.get("git_commit", ""),
            repo_root=repo_root,
            artifact_root=artifact_root,
        )

    sets = raw["set_coverage"]
    add(errors, isinstance(sets, list) and len(sets) == 12, "set coverage must contain A-L")
    group_ids = set(ids)
    if isinstance(sets, list):
        add(errors, {row.get("set_id") for row in sets if isinstance(row, dict)} == set("ABCDEFGHIJKL"), "set ids mismatch")
        for index, row in enumerate(sets):
            if not closed(errors, row, SET_KEYS, f"set_coverage[{index}]"):
                continue
            add(errors, row["promotion_allowed"] is False, f"set {row['set_id']} promotion must be false")
            add(errors, isinstance(row["group_ids"], list) and all(group_id in group_ids for group_id in row["group_ids"]), f"set {row['set_id']} group ids invalid")
            add(errors, row["status"] in {"execution_blocked", "partial", "red", "bounded_green", "not_assessed"}, f"set {row['set_id']} status invalid")
            add(errors, isinstance(row["blockers"], list), f"set {row['set_id']} blockers invalid")
            add(errors, isinstance(row["findings"], list), f"set {row['set_id']} findings invalid")
            add(errors, isinstance(row["observations"], list) and bool(row["observations"]), f"set {row['set_id']} observations invalid")
            expected_set = SET_CONTRACTS.get(row["set_id"])
            add(errors, expected_set is not None, f"set {row['set_id']} is outside the contract")
            if expected_set is not None:
                add(errors, row["group_ids"] == expected_set["group_ids"], f"set {row['set_id']} group contract mismatch")
                add(errors, row["blockers"] == expected_set["blockers"], f"set {row['set_id']} blocker contract mismatch")
                add(errors, row["findings"] == expected_set["findings"], f"set {row['set_id']} finding contract mismatch")
            selected = [
                group
                for group in groups
                if group.get("id") in row["group_ids"]
            ]
            execution = (
                len(selected) == len(row["group_ids"])
                and all(group.get("execution_completed") is True for group in selected)
            )
            observations_pass: list[bool] = []
            observation_ids: list[str] = []
            by_group_id = {group.get("id"): group for group in groups if isinstance(group, dict)}
            for observation_index, observation in enumerate(row["observations"]):
                observation_label = f"set_coverage[{index}].observations[{observation_index}]"
                if not closed(errors, observation, SET_OBSERVATION_KEYS, observation_label):
                    continue
                observation_id = observation["observation_id"]
                observation_ids.append(observation_id)
                expected_observation = (
                    expected_set["observations"].get(observation_id)
                    if expected_set is not None
                    else None
                )
                add(errors, expected_observation is not None, f"{observation_label} outside contract")
                if expected_observation is not None:
                    add(errors, observation["group_id"] == expected_observation[0], f"{observation_label} group mismatch")
                    add(errors, observation["kind"] == expected_observation[1], f"{observation_label} kind mismatch")
                    add(errors, observation["json_pointer"] == expected_observation[2], f"{observation_label} pointer mismatch")
                    add(errors, observation["pass_value"] == expected_observation[3], f"{observation_label} pass value mismatch")
                source_group = by_group_id.get(observation["group_id"])
                add(errors, source_group is not None, f"{observation_label} source group missing")
                observed = None
                if source_group is not None and observation["kind"] == "artifact_json":
                    artifact_paths = {
                        artifact.get("path")
                        for artifact in source_group.get("artifacts", [])
                        if isinstance(artifact, dict)
                    }
                    add(errors, observation["artifact_path"] in artifact_paths, f"{observation_label} artifact undeclared")
                    try:
                        observed = pointer(
                            json.loads(Path(observation["artifact_path"]).read_text(encoding="utf-8")),
                            observation["json_pointer"],
                        )
                    except (OSError, json.JSONDecodeError, KeyError, IndexError, TypeError):
                        errors.append(f"{observation_label} artifact evidence unreadable")
                elif source_group is not None and observation["kind"] == "group_bounded_pass":
                    add(errors, observation["artifact_path"] is None and observation["json_pointer"] is None, f"{observation_label} group evidence paths must be null")
                    observed = source_group.get("bounded_pass")
                else:
                    errors.append(f"{observation_label} kind invalid")
                add(errors, observed == observation["observed"], f"{observation_label} observed mismatch")
                observations_pass.append(observed == observation["pass_value"])
            if expected_set is not None:
                add(
                    errors,
                    observation_ids == list(expected_set["observations"]),
                    f"set {row['set_id']} observation inventory mismatch",
                )
            expected_status = (
                "execution_blocked"
                if not execution
                else "red"
                if any(value is False for value in observations_pass)
                else "partial"
                if row["blockers"]
                else "bounded_green"
                if observations_pass and all(observations_pass)
                else "not_assessed"
            )
            add(errors, row["status"] == expected_status, f"set {row['set_id']} status mismatch")

    inventory = raw["blocked_inventory"]
    add(errors, isinstance(inventory, list), "blocked inventory invalid")
    if isinstance(inventory, list):
        for index, row in enumerate(inventory):
            if not closed(errors, row, INVENTORY_KEYS, f"blocked_inventory[{index}]"):
                continue
            add(errors, row["status"] == "blocked", f"blocked_inventory[{index}] status invalid")
            add(errors, row["source_count"] == len(row["sources"]), f"blocked_inventory[{index}] source count mismatch")
            for source_index, record in enumerate(row["sources"]):
                source_label = f"blocked_inventory[{index}].sources[{source_index}]"
                if not closed(errors, record, INVENTORY_SOURCE_KEYS, source_label):
                    continue
                inventory_path = Path(str(record["path"]))
                add(errors, inventory_path.is_file(), f"{source_label} missing")
                if inventory_path.is_file():
                    add(errors, sha256_file(inventory_path) == record["sha256"], f"{source_label} hash mismatch")
                    try:
                        relative = inventory_path.resolve().relative_to(repo_root.resolve()).as_posix()
                    except ValueError:
                        relative = ""
                    add(errors, bool(relative), f"{source_label} outside repository")
                    if relative:
                        committed = subprocess.run(
                            ["git", "show", f"{source.get('git_commit', '')}:{relative}"],
                            cwd=repo_root,
                            capture_output=True,
                            check=False,
                        )
                        add(errors, committed.returncode == 0, f"{source_label} absent from source commit")
                        if committed.returncode == 0:
                            add(
                                errors,
                                hashlib.sha256(committed.stdout).hexdigest() == record["sha256"],
                                f"{source_label} commit hash mismatch",
                            )

    summary = raw["summary"]
    if closed(errors, summary, SUMMARY_KEYS, "summary"):
        bounded = [row["bounded_pass"] for row in groups if row.get("bounded_pass") is not None]
        derived = {
            "group_count": len(groups),
            "command_count": sum(len(row["commands"]) for row in groups),
            "executed_command_count": sum(
                1
                for row in groups
                for command in row["commands"]
                if command["timed_out"] is False and command["exit_code"] is not None
            ),
            "execution_failed_count": sum(row["execution_completed"] is not True for row in groups),
            "bounded_pass_count": sum(value is True for value in bounded),
            "bounded_red_count": sum(value is False for value in bounded),
            "bounded_not_assessed_count": sum(row["bounded_pass"] is None for row in groups),
            "blocked_inventory_count": len(inventory),
            "set_count": len(sets),
            "set_evidence_complete_count": sum(row["status"] in {"bounded_green", "red"} for row in sets),
            "set_bounded_green_count": sum(row["status"] == "bounded_green" for row in sets),
            "set_red_count": sum(row["status"] == "red" for row in sets),
            "set_partial_count": sum(row["status"] == "partial" for row in sets),
            "set_execution_blocked_count": sum(row["status"] == "execution_blocked" for row in sets),
        }
        add(errors, summary == derived, "summary does not recompute from children")
        runner_completed = derived["execution_failed_count"] == 0 and derived["executed_command_count"] == derived["command_count"]
        bounded_all = (
            bool(bounded)
            and all(bounded)
            and derived["set_partial_count"] == 0
            and derived["set_execution_blocked_count"] == 0
            and derived["set_red_count"] == 0
        )
        add(errors, raw["runner_all_completed"] is runner_completed, "runner_all_completed mismatch")
        add(
            errors,
            raw["bounded_observations_all_pass"] is bounded_all,
            "bounded_observations_all_pass mismatch",
        )
        add(errors, derived["executed_command_count"] > 0, "zero execution is not acceptable")
    if envelope_path is not None:
        add(errors, Path(raw["command"][raw["command"].index("--output") + 1]).resolve() == envelope_path.resolve(), "command/output envelope path mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args()
    try:
        raw = json.loads(args.envelope.read_text(encoding="utf-8"))
        errors = validate(raw, envelope_path=args.envelope)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        errors = [f"parse failure: {error}"]
    print(json.dumps({"ok": not errors, "errors": errors, "envelope": str(args.envelope.resolve())}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

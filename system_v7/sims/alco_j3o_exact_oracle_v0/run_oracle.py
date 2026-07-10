#!/usr/bin/env python3
"""Run the pinned GAP/ALCO oracle and emit deterministic packet artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from validate_oracle import sha256_file, tracked_tree_sha256, tree_sha256, validate_result, write_validation


HERE = Path(__file__).resolve().parent
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
ALCO_CHECKOUT = Path("/Users/joshuaeisenhart/GitHub/alco")
EXPECTED_ALCO_COMMIT = "e10ec05acbdf6e7d312d3d35d757771b9fdbc7ec"
GAP_ROOT = Path("/Users/joshuaeisenhart/.local/share/codex-ratchet/gap/alco-1.1.2/gap-4.16.0")
GAP_BINARY = GAP_ROOT / "gap"
GAP_HOME = Path("/Users/joshuaeisenhart/.local/share/codex-ratchet/gap/alco-1.1.2/home")
ALCO_INSTALL = GAP_ROOT / "pkg/alco"
RESCLASSES_INSTALL = GAP_ROOT / "pkg/resclasses"

ORACLE_PATH = HERE / "alco_j3o_exact_oracle.g"
RESULT_PATH = HERE / "alco_j3o_exact_oracle_result.json"
VALIDATION_PATH = HERE / "alco_j3o_exact_oracle_validation.json"
RESULTS_PATH = HERE / "RESULTS.md"

AUTHORITY_STATEMENT = (
    "ALCO has no spectral log, entropy, channel, DPI, engine, Axis0, perception, "
    "object, or physics authority."
)
AUTHORITY_EXCLUSIONS = [
    "spectral_log",
    "entropy",
    "channel",
    "DPI",
    "engine",
    "Axis0",
    "perception",
    "object",
    "physics",
]
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "GAP": {"used": True, "depth": "load_bearing", "reason": "exact package runtime"},
    "ALCO": {
        "used": True,
        "depth": "load_bearing",
        "reason": "AlbertAlgebra, product, Trace, Determinant, GenericMinimalPolynomial, and JordanQuadraticOperator",
    },
    "ResClasses": {"used": True, "depth": "supportive", "reason": "required ALCO package dependency loaded by GAP"},
    "python_fraction": {"used": True, "depth": "load_bearing", "reason": "independent exact local formulas and equality validator"},
    "python_stdlib": {"used": True, "depth": "supportive", "reason": "process control, hashing, JSON, and deterministic report generation"},
}
TOOL_INTEGRATION_DEPTH = {
    "GAP": "load_bearing",
    "ALCO": "load_bearing",
    "ResClasses": "supportive",
    "python_fraction": "load_bearing",
    "python_stdlib": "supportive",
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ALCO_CHECKOUT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _entry(path: Path, kind: str = "file") -> dict[str, str]:
    if kind == "file":
        digest = sha256_file(path)
    elif kind == "tree":
        digest = tree_sha256(path)
    elif kind == "git_tracked_tree":
        digest = tracked_tree_sha256(path)
    else:
        raise ValueError(kind)
    return {"path": str(path), "kind": kind, "sha256": digest}


def _parse_bool(value: str) -> bool | str:
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def parse_oracle_stdout(stdout: str) -> dict[str, Any]:
    normalized = stdout.replace("\\\n", "")
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    if not lines or lines[0] != "ALCO_ORACLE_V1" or lines[-1] != "END_ORACLE":
        raise RuntimeError(f"unexpected oracle envelope: first={lines[:1]} last={lines[-1:]}")

    metadata: dict[str, Any] = {}
    boundaries: dict[str, Any] = {}
    maps: dict[str, str] = {}
    cases: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    list_fields = {"x", "y", "z", "product", "u_x_y", "u_y_x", "minpoly_x", "minpoly_y"}
    bool_fields = {
        "cayley_hamilton_x",
        "cayley_hamilton_y",
        "u_unit_identity",
        "u_homogeneity",
        "u_determinant_identity",
        "fundamental_formula",
    }

    for line in lines[1:-1]:
        parts = line.split("|")
        tag = parts[0]
        if tag == "META":
            metadata[parts[1]] = _parse_bool(parts[2])
        elif tag == "BOUNDARY":
            boundaries[parts[1]] = _parse_bool(parts[2])
        elif tag == "MAP":
            maps[parts[1]] = parts[2]
        elif tag == "CASE":
            if current is not None:
                raise RuntimeError("nested CASE records")
            current = {"label": parts[1], "seed": int(parts[2])}
        elif tag == "ENDCASE":
            if current is None:
                raise RuntimeError("ENDCASE without CASE")
            cases.append(current)
            current = None
        else:
            if current is None:
                raise RuntimeError(f"case field outside CASE: {line}")
            key = tag.lower()
            value = parts[1]
            if key in list_fields:
                current[key] = value.split(",") if value else []
            elif key in bool_fields:
                current[key] = _parse_bool(value)
            else:
                current[key] = value

    if current is not None:
        raise RuntimeError("unterminated CASE")
    return {
        "metadata": metadata,
        "boundaries": boundaries,
        "map": maps,
        "cases": cases,
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        "stdout_line_count": len(lines),
    }


def run_gap_oracle() -> tuple[dict[str, Any], dict[str, Any]]:
    environment = os.environ.copy()
    environment["HOME"] = str(GAP_HOME)
    completed = subprocess.run(
        [str(GAP_BINARY), "-A", "-q", "-x", "100000", str(ORACLE_PATH)],
        cwd=HERE,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"GAP oracle failed ({completed.returncode}):\n{completed.stderr}\n{completed.stdout}")
    parsed = parse_oracle_stdout(completed.stdout)
    execution = {
        "command": [str(GAP_BINARY), "-A", "-q", "-x", "100000", str(ORACLE_PATH)],
        "cwd": str(HERE),
        "home": str(GAP_HOME),
        "exit_code": completed.returncode,
        "stderr_empty": completed.stderr == "",
    }
    return parsed, execution


def run_upstream_tests() -> dict[str, Any]:
    environment = os.environ.copy()
    environment["HOME"] = str(GAP_HOME)
    test_file = ALCO_CHECKOUT / "tst/testall.g"
    completed = subprocess.run(
        [str(GAP_BINARY), "-A", "-q", str(test_file)],
        cwd=ALCO_CHECKOUT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    match = re.search(r"(\d+) failures in (\d+) files", completed.stdout)
    failures = int(match.group(1)) if match else None
    files = int(match.group(2)) if match else None
    return {
        "command": [str(GAP_BINARY), "-A", "-q", str(test_file)],
        "exit_code": completed.returncode,
        "failures": failures,
        "files": files,
        "pass": completed.returncode == 0 and failures == 0 and files == 6,
    }


def provenance() -> dict[str, Any]:
    packet_sources = {
        "gap_oracle": ORACLE_PATH,
        "local_exact_formulas": HERE / "local_j3o_exact.py",
        "python_controller": HERE / "run_oracle.py",
        "python_validator": HERE / "validate_oracle.py",
        "packet_readme": HERE / "README.md",
        "local_j3o_bloch_source": ROOT / "system_v7/constraint_core/sims_and_scripts/j3o_bloch_body_entropy_pawl_sim.py",
        "local_jordan_dpi_source": ROOT / "system_v7/constraint_core/sims_and_scripts/jordan_dpi_probe_v4_sim.py",
        "local_engine_field_albert_source": ROOT / "system_v7/constraint_core/sims_and_scripts/engine_field_choi_jordan_albert_probe_sim.py",
        "alco_package_info": ALCO_CHECKOUT / "PackageInfo.g",
        "alco_declarations": ALCO_CHECKOUT / "lib/alco.gd",
        "alco_implementation": ALCO_CHECKOUT / "lib/alco.gi",
        "alco_upstream_test_driver": ALCO_CHECKOUT / "tst/testall.g",
    }
    dependencies = {
        "gap_binary": _entry(GAP_BINARY),
        "python_executable": _entry(Path(sys.executable).resolve()),
        "alco_complete_tracked_tree": _entry(ALCO_CHECKOUT, "git_tracked_tree"),
        "resclasses_complete_package_tree": _entry(RESCLASSES_INSTALL, "tree"),
    }
    return {
        "expected_alco_commit": EXPECTED_ALCO_COMMIT,
        "observed_alco_commit": _git("rev-parse", "HEAD"),
        "observed_alco_git_tree": _git("rev-parse", "HEAD^{tree}"),
        "alco_checkout": str(ALCO_CHECKOUT),
        "alco_tracked_status_short": _git("status", "--short", "--untracked-files=no"),
        "alco_install_path": str(ALCO_INSTALL),
        "alco_install_realpath": str(ALCO_INSTALL.resolve()),
        "sources": {name: _entry(path) for name, path in packet_sources.items()},
        "dependencies": dependencies,
    }


def build_result() -> dict[str, Any]:
    oracle, execution = run_gap_oracle()
    upstream_tests = run_upstream_tests()
    result: dict[str, Any] = {
        "schema": "codex_ratchet.alco_j3o_exact_oracle_result.v1",
        "sim_id": "alco_j3o_exact_oracle_v0",
        "name": "ALCO exact-rational J3(O) oracle",
        "version": "0.1.0",
        "tier": "tool capability anchor / exact algebra diagnostic",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "promotion_status": "diagnostic_only",
        "deterministic": True,
        "sim_execution_kind": "classical",
        "sim_class": "tool_capability_anchor",
        "purpose": "Compare pinned package-native ALCO Albert arithmetic with independent exact-rational local J3(O) formulas.",
        "scientific_question": "Do the frozen local Albert product and cubic/quadratic invariants agree exactly with ALCO on multiple deterministic rational witnesses?",
        "root_constraints_in_force": [
            "finite 27-coordinate rational witnesses only",
            "explicit nonassociative local Fano multiplication order",
            "exact equality only; no floating tolerance",
        ],
        "carrier_layer": "J3(O) / Albert algebra exact rational coordinates",
        "geometry_layer": "none",
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "Exact parity of product, trace, determinant, cubic minimal polynomial, and Jordan quadratic representation.",
        "branch_status_before_run": "new isolated scratch diagnostic",
        "allowed_claims": [
            "The frozen local rational Albert formulas match pinned ALCO on the emitted cases when every validation gate passes.",
            "The corrupted local e1*e2 product is rejected by the structured kill witness.",
            "ALCO exposes the rank-4 octonionic boundary as SimpleEuclideanJordanAlgebra(4,8)=fail.",
        ],
        "promotion_blockers": [
            "finite deterministic witnesses are not a formal proof",
            "no independent fresh-context semantic audit",
            "no admission or claim gate is requested or run",
        ],
        "required_tools": ["GAP", "ALCO", "ResClasses", "python_fraction"],
        "actual_tools_used": ["GAP", "ALCO", "ResClasses", "python_fraction", "python_stdlib"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": [
            "three named local J3(O)/Jordan implementations",
            "ALCO commit e10ec05acbdf6e7d312d3d35d757771b9fdbc7ec",
            "GAP 4.16.0 with ALCO 1.1.2 and ResClasses",
        ],
        "data_or_artifact_dependencies": [],
        "required_negatives": ["corrupted local e1*e2 multiplication entry", "rank-4 octonionic constructor boundary"],
        "kill_conditions": [
            "any exact ALCO/local mismatch on the valid product or invariant surfaces",
            "corrupted-product witness fails to diverge",
            "SimpleEuclideanJordanAlgebra(4,8) does not return fail",
            "any source/dependency hash or commit pin differs",
        ],
        "required_artifacts": [
            "alco_j3o_exact_oracle_result.json",
            "alco_j3o_exact_oracle_validation.json",
            "README.md",
            "RESULTS.md",
        ],
        "artifacts_emitted": [str(RESULT_PATH), str(VALIDATION_PATH), str(HERE / "README.md"), str(RESULTS_PATH)],
        "witness_trace_id": "alco-j3o-exact-oracle-v0-seeds-7-29-101-20260709",
        "seed_algorithm": "LCG state=(1103515245*state+12345) mod 2^31; rational numerators mod 9 minus 4; denominators [1,2,3,5,7]",
        "seeds": [7, 29, 101, 20260709],
        "oracle_execution": execution,
        "upstream_tests": upstream_tests,
        "oracle": oracle,
        "provenance": provenance(),
        "authority_exclusions": AUTHORITY_EXCLUSIONS,
        "authority_statement": AUTHORITY_STATEMENT,
        "eligible_consumers": [],
        "blocked_consumers": [
            "spectral-log or entropy implementation claims",
            "channel or DPI claims",
            "engine, Axis0, perception, or object claims",
            "bridge, manifold, or physics claims",
            "canonical-by-process or formal admission",
        ],
        "pass_rule": "All exact comparison, identity, boundary, corruption-kill, commit, and hash gates pass.",
        "fail_rule": "Any failed gate keeps the packet at runs and marks all downstream consumers blocked.",
        "claim_ceiling": "Scratch diagnostic package-native exact-oracle parity on five frozen cases only; no theorem or admission.",
    }
    preliminary = validate_result(result)
    result["negatives_run"] = {
        "corrupted_product_kill": next(check for check in preliminary["checks"] if check["name"] == "corrupted_product_kill"),
        "simple_eja_4_8_boundary": next(check for check in preliminary["checks"] if check["name"] == "simple_eja_4_8_boundary"),
    }
    result["validation_summary"] = preliminary["gate_counts"]
    result["all_pass"] = preliminary["all_pass"] and upstream_tests["pass"]
    result["result_summary"] = (
        "All exact ALCO/local oracle gates and upstream dependency tests pass."
        if result["all_pass"]
        else "One or more exact oracle or dependency gates failed."
    )
    return result


def write_results(result: dict[str, Any], validation: dict[str, Any]) -> None:
    gate_lines = "\n".join(
        f"| `{check['name']}` | {'PASS' if check['pass'] else 'FAIL'} |"
        for check in validation["checks"]
    )
    text = f"""# RESULTS

## Verdict

- Classification: `scratch_diagnostic`
- Accepted status: `{validation['accepted_status_label']}`
- Validation: `{validation['gate_counts']['passed']}/{validation['gate_counts']['total']}` gates passed
- Upstream ALCO tests: `{result['upstream_tests']['failures']}` failures in `{result['upstream_tests']['files']}` files
- Promotion allowed: `false`
- Formal admission allowed: `false`

{AUTHORITY_STATEMENT}

## Gates

| Gate | Verdict |
|---|---|
{gate_lines}

## Exact cases

- Seeded cases: `7`, `29`, `101`, `20260709`
- Structured kill: `kill_fano_e1_e2`
- Compared surfaces: product, trace, determinant, generic cubic minimal polynomial, `U_x(y)`, `U_y(x)`, Cayley-Hamilton, quadratic homogeneity, determinant covariance, and the fundamental formula.
- Boundary: `SimpleEuclideanJordanAlgebra(4,8)=fail`

## Artifact hashes

- `alco_j3o_exact_oracle_result.json`: `{sha256_file(RESULT_PATH)}`
- `alco_j3o_exact_oracle_validation.json`: `{sha256_file(VALIDATION_PATH)}`

Every named source and dependency hash is recorded and rechecked in the JSON provenance gate. `RESULTS.md` is generated after those artifacts and is intentionally not included in the self-referential source manifest.

## Role ceiling

- Builder: GAP oracle and Python exact-formula controller ran.
- Mechanical gatekeeper: `validate_oracle.py` ran exact comparisons and provenance checks.
- Fabrication control: corrupted-product kill ran and flipped the structured witness.
- Independent fresh-context semantic auditor: not run.
- Canonical/admission gates: not run and not applicable to this packet's requested ceiling.
"""
    RESULTS_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation = write_validation(RESULT_PATH, VALIDATION_PATH)
    write_results(result, validation)
    print(
        "ALCO_J3O_EXACT_ORACLE "
        f"cases={len(result['oracle']['cases'])} "
        f"passed={validation['gate_counts']['passed']} "
        f"failed={validation['gate_counts']['failed']} "
        f"upstream={result['upstream_tests']['failures']}/{result['upstream_tests']['files']} "
        f"all_pass={result['all_pass'] and validation['all_pass']}"
    )
    print(f"wrote: {RESULT_PATH}")
    print(f"wrote: {VALIDATION_PATH}")
    print(f"wrote: {RESULTS_PATH}")
    return 0 if result["all_pass"] and validation["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

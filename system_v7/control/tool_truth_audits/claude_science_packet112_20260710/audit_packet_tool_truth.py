#!/usr/bin/env python3
"""Conservative import/API/receipt audit for an external simulation packet."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


CLASSIFICATION = "audit"
TOOL_MANIFEST = {
    "python.ast": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact import, module-assignment, and qualified-call inventory without executing packet sources",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing strict result-field and canonical rerun-report inspection",
    },
}
TOOL_INTEGRATION_DEPTH = {"python.ast": "load_bearing", "json": "load_bearing"}

TRACKED_ROOTS = (
    "numpy", "scipy", "jax", "torch", "sympy", "z3", "cvc5", "qutip",
    "networkx", "pysindy", "pykoopman",
)
RESULT_RECEIPT_FIELDS = (
    "TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "tool_calls",
    "claim_path_tools", "all_pass", "classification",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = qualified_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def source_row(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    imports: set[str] = set()
    module_assignments: set[str] = set()
    calls: Counter[str] = Counter()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    module_assignments.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            module_assignments.add(node.target.id)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = qualified_name(node.func)
            if name:
                calls[name] += 1
    tracked = sorted(root for root in TRACKED_ROOTS if root in imports)
    engine_roots = sorted(set(tracked) & {"jax", "torch"})
    return {
        "file": path.name,
        "source_sha256": sha256(path),
        "tracked_import_roots": tracked,
        "engine_roots": engine_roots,
        "has_tool_manifest": "TOOL_MANIFEST" in module_assignments,
        "has_tool_integration_depth": "TOOL_INTEGRATION_DEPTH" in module_assignments,
        "qualified_calls_for_engine_roots": [
            {"qualified_api": name, "count": count}
            for name, count in sorted(calls.items())
            if name.split(".")[0] in engine_roots
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--packet-zip", type=Path, required=True)
    parser.add_argument("--canonical-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sim_root = args.packet_root / "sims_and_scripts"
    sources = [source_row(path) for path in sorted(sim_root.glob("*.py"))]
    julia_sources = sorted(sim_root.glob("*.jl"))
    result_paths = sorted(sim_root.glob("*_results.json"))
    result_field_counts = Counter({field: 0 for field in RESULT_RECEIPT_FIELDS})
    result_parse_failures: list[str] = []
    for path in result_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            result_parse_failures.append(f"{path.name}: {exc}")
            continue
        if isinstance(data, dict):
            for field in RESULT_RECEIPT_FIELDS:
                result_field_counts[field] += int(field in data)

    import_counts = {
        root: sum(root in row["tracked_import_roots"] for row in sources)
        for root in TRACKED_ROOTS
    }
    engine_files = [row for row in sources if row["engine_roots"]]
    run_all_text = (args.packet_root / "run_all.py").read_text(encoding="utf-8")
    report = json.loads(args.canonical_report.read_text(encoding="utf-8"))
    summary = report.get("summary", {})
    harness_counts = {
        "pass": int(summary.get("pass", -1)),
        "fail": int(summary.get("fail", -1)),
        "skip": int(summary.get("skip", -1)),
    }

    checks = {
        "packet_sources_parse": len(sources) == 144,
        "canonical_report_is_143_0_0": harness_counts == {"pass": 143, "fail": 0, "skip": 0},
        "numpy_dominates_sources": import_counts["numpy"] >= 0.9 * len(sources),
        "engine_source_count_at_most_three": len(engine_files) <= 3,
        "no_julia_sim_sources": not julia_sources,
        "no_source_tool_manifests": not any(row["has_tool_manifest"] for row in sources),
        "no_source_tool_depth_maps": not any(row["has_tool_integration_depth"] for row in sources),
        "no_result_function_receipts": all(result_field_counts[field] == 0 for field in ("TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "tool_calls", "claim_path_tools")),
        "harness_uses_console_string_assertions": '("contains"' in run_all_text and '("approx"' in run_all_text,
    }

    output = {
        "schema": "codex_ratchet.external_packet_tool_truth_audit.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "packet_zip_sha256": sha256(args.packet_zip),
        "packet_root": str(args.packet_root),
        "canonical_report_sha256": sha256(args.canonical_report),
        "observed": {
            "python_sim_source_count": len(sources),
            "julia_sim_source_count": len(julia_sources),
            "result_json_count": len(result_paths),
            "result_parse_failures": result_parse_failures,
            "import_counts_nonexclusive": import_counts,
            "source_tool_manifest_count": sum(row["has_tool_manifest"] for row in sources),
            "source_tool_integration_depth_count": sum(row["has_tool_integration_depth"] for row in sources),
            "result_top_level_field_counts": dict(result_field_counts),
            "harness_assertion_counts": {
                "contains": len(re.findall(r'\(\"contains\"', run_all_text)),
                "approx": len(re.findall(r'\(\"approx\"', run_all_text)),
            },
            "canonical_harness_counts": harness_counts,
        },
        "engine_files": engine_files,
        "checks": checks,
        "all_pass": all(checks.values()),
        "tool_truth_verdict": "NUMPY_DOMINATED_UNRECEIPTED_EXTERNAL_SCRIPT_ESTATE_NOT_A_REAL_MULTI_ENGINE_RUN",
        "claim_ceiling": "packet_112_143_0_0_is_a_local_console_harness_rerun_not_evidence_that_qit_or_dual_ratchet_engines_ran",
        "required_repair": [
            "structured result schema instead of console substring success",
            "Julia semantic owner for algebra, QIT, or attractor claims",
            "JAX batched workhorse role with claim-path API receipts",
            "PyTorch graph or autograd role only when nonredundant",
            "positive, boundary, erased, and mutation controls per load-bearing API",
            "removal or bypass demotion test for every claimed engine tool",
        ],
        "blocked_claims": [
            "engines running",
            "three-engine corroboration",
            "sixteen unique intelligences",
            "four substages or sixty-four engine stages",
            "perception or object formation",
            "cross-domain attractor unification",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

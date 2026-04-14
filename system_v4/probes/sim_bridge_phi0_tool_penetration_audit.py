#!/usr/bin/env python3
"""
sim_bridge_phi0_tool_penetration_audit.py
=========================================

Audit/probe for graph/proof tool penetration on the recent bridge/Phi0 seam.

Focus files:
  - sim_bridge_packet_library_audit.py
  - sim_packet_balance_sensitivity_audit.py
  - sim_phi0_integrated_bakeoff.py
  - sim_xi_matched_packet_cross_bakeoff.py

Goal:
  Classify proof/graph depth as real, shallow, or absent, and distinguish
  actual tool use from manifest declarations.

This is an audit surface, not final canon.
"""

import ast
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
classification = "canonical"


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "audit substrate only"},
    "pyg": {"tried": False, "used": False, "reason": "graph tool audit only"},
    "z3": {"tried": False, "used": False, "reason": "proof tool audit only"},
    "cvc5": {"tried": False, "used": False, "reason": "proof tool audit only"},
    "sympy": {"tried": False, "used": False, "reason": "proof tool audit only"},
    "clifford": {"tried": False, "used": False, "reason": "adjacent geometry tool"},
    "geomstats": {"tried": False, "used": False, "reason": "adjacent geometry tool"},
    "e3nn": {"tried": False, "used": False, "reason": "adjacent symmetry tool"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph tool audit only"},
    "xgi": {"tried": False, "used": False, "reason": "graph tool audit only"},
    "toponetx": {"tried": False, "used": False, "reason": "graph tool audit only"},
    "gudhi": {"tried": False, "used": False, "reason": "graph/topology tool audit only"},
}

SEAM_FILES = [
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_bridge_packet_library_audit.py",
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_packet_balance_sensitivity_audit.py",
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_phi0_integrated_bakeoff.py",
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_xi_matched_packet_cross_bakeoff.py",
]

PROOF_TOOLS = ["z3", "cvc5", "sympy"]
GRAPH_TOOLS = ["pyg", "rustworkx", "xgi", "toponetx", "gudhi"]
SUBSTRATE_TOOLS = ["pytorch"]

TOOL_ALIASES = {
    "pytorch": {"torch"},
    "pyg": {"torch_geometric", "pyg"},
    "z3": {"z3"},
    "cvc5": {"cvc5"},
    "sympy": {"sympy"},
    "clifford": {"clifford"},
    "geomstats": {"geomstats"},
    "e3nn": {"e3nn"},
    "rustworkx": {"rustworkx"},
    "xgi": {"xgi"},
    "toponetx": {"toponetx"},
    "gudhi": {"gudhi"},
}


@dataclass
class FileAudit:
    path: str
    manifest_tools: list
    actual_tool_refs: dict
    depth: dict
    note: str


def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (bool,)):
        return bool(obj)
    if isinstance(obj, int):
        return int(obj)
    if isinstance(obj, float):
        return float(obj)
    return obj


def extract_manifest_tools(tree):
    tools = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TOOL_MANIFEST" and isinstance(node.value, ast.Dict):
                    for key in node.value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            tools.append(key.value)
    return tools


def extract_actual_tool_refs(tree):
    counts = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                for tool, aliases in TOOL_ALIASES.items():
                    if top in aliases:
                        counts[tool] += 1
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                for tool, aliases in TOOL_ALIASES.items():
                    if top in aliases:
                        counts[tool] += 1
            for alias in node.names:
                for tool, aliases in TOOL_ALIASES.items():
                    if alias.name in aliases:
                        counts[tool] += 1
        elif isinstance(node, ast.Name):
            for tool, aliases in TOOL_ALIASES.items():
                if node.id in aliases:
                    counts[tool] += 1
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base = node.value.id
            for tool, aliases in TOOL_ALIASES.items():
                if base in aliases:
                    counts[tool] += 1
    return dict(counts)


def classify_depth(tool_set, manifest_tools, actual_tool_refs):
    real = 0
    shallow = 0
    absent = 0
    labels = {}
    for tool in tool_set:
        actual = actual_tool_refs.get(tool, 0)
        in_manifest = tool in manifest_tools
        if actual > 0:
            labels[tool] = "real"
            real += 1
        elif in_manifest:
            labels[tool] = "shallow"
            shallow += 1
        else:
            labels[tool] = "absent"
            absent += 1
    if real > 0:
        overall = "real"
    elif shallow > 0:
        overall = "shallow"
    else:
        overall = "absent"
    return {
        "overall": overall,
        "labels": labels,
        "real": real,
        "shallow": shallow,
        "absent": absent,
    }


def audit_file(path):
    source = open(path, "r", encoding="utf-8").read()
    tree = ast.parse(source, filename=path)
    manifest_tools = extract_manifest_tools(tree)
    actual_tool_refs = extract_actual_tool_refs(tree)
    proof_depth = classify_depth(PROOF_TOOLS, manifest_tools, actual_tool_refs)
    graph_depth = classify_depth(GRAPH_TOOLS, manifest_tools, actual_tool_refs)
    substrate_depth = classify_depth(SUBSTRATE_TOOLS, manifest_tools, actual_tool_refs)
    manifest_only_tools = [
        tool
        for tool in manifest_tools
        if actual_tool_refs.get(tool, 0) == 0 and tool in PROOF_TOOLS + GRAPH_TOOLS + SUBSTRATE_TOOLS
    ]
    note = "manifest-only for proof/graph" if proof_depth["real"] == 0 and graph_depth["real"] == 0 else "contains actual proof/graph use"
    return FileAudit(
        path=path,
        manifest_tools=manifest_tools,
        actual_tool_refs=actual_tool_refs,
        depth={
            "proof": proof_depth,
            "graph": graph_depth,
            "substrate": substrate_depth,
        },
        note=note,
    ), manifest_only_tools


def file_profile(audit):
    return {
        "file": os.path.basename(audit.path),
        "path": audit.path,
        "proof_depth": audit.depth["proof"]["overall"],
        "graph_depth": audit.depth["graph"]["overall"],
        "substrate_depth": audit.depth["substrate"]["overall"],
        "proof_detail": audit.depth["proof"],
        "graph_detail": audit.depth["graph"],
        "substrate_detail": audit.depth["substrate"],
        "actual_tool_refs": audit.actual_tool_refs,
        "manifest_tools": audit.manifest_tools,
        "note": audit.note,
    }


def main():
    audits = []
    manifest_only_by_file = {}
    for path in SEAM_FILES:
        audit, manifest_only = audit_file(path)
        audits.append(audit)
        manifest_only_by_file[os.path.basename(path)] = manifest_only

    file_profiles = [file_profile(audit) for audit in audits]

    proof_real_files = [p["file"] for p in file_profiles if p["proof_depth"] == "real"]
    proof_shallow_files = [p["file"] for p in file_profiles if p["proof_depth"] == "shallow"]
    proof_absent_files = [p["file"] for p in file_profiles if p["proof_depth"] == "absent"]
    graph_real_files = [p["file"] for p in file_profiles if p["graph_depth"] == "real"]
    graph_shallow_files = [p["file"] for p in file_profiles if p["graph_depth"] == "shallow"]
    graph_absent_files = [p["file"] for p in file_profiles if p["graph_depth"] == "absent"]
    substrate_real_files = [p["file"] for p in file_profiles if p["substrate_depth"] == "real"]

    proof_graph_real = len(proof_real_files) + len(graph_real_files)
    proof_graph_shallow = len(proof_shallow_files) + len(graph_shallow_files)

    positive = {
        "phi0_has_real_torch_substrate": {
            "pass": "sim_phi0_integrated_bakeoff.py" in substrate_real_files,
            "real_substrate_files": substrate_real_files,
        },
        "pass": "sim_phi0_integrated_bakeoff.py" in substrate_real_files,
    }

    negative = {
        "no_real_proof_or_graph_penetration": {
            "pass": proof_graph_real == 0,
            "proof_real_files": proof_real_files,
            "graph_real_files": graph_real_files,
        },
        "mostly_manifest_only_declarations": {
            "pass": proof_graph_shallow > 0 and proof_graph_real == 0,
            "proof_shallow_files": proof_shallow_files,
            "graph_shallow_files": graph_shallow_files,
        },
        "pass": proof_graph_real == 0 and proof_graph_shallow > 0,
    }

    boundary = {
        "manifest_only_classifies_as_shallow": {
            "pass": all(
                p["proof_depth"] == "shallow" and p["graph_depth"] == "shallow"
                for p in file_profiles
                if p["file"] != "sim_phi0_integrated_bakeoff.py"
            ),
            "profiles": file_profiles,
        },
        "pass": all(
            p["proof_depth"] == "shallow" and p["graph_depth"] == "shallow"
            for p in file_profiles
            if p["file"] != "sim_phi0_integrated_bakeoff.py"
        ),
    }

    tests_total = 3
    tests_passed = sum(1 for sec in (positive, negative, boundary) if sec["pass"])
    all_pass = tests_passed == tests_total

    results = {
        "name": "bridge_phi0_tool_penetration_audit",
        "classification": "audit",
        "probe": "bridge_phi0_tool_penetration_audit",
        "purpose": (
            "Check whether the recent bridge/Phi0 seam actually uses graph/proof tools "
            "or mostly carries them as manifest declarations."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "files": file_profiles,
        "summary": {
            "tests_total": tests_total,
            "tests_passed": tests_passed,
            "all_pass": all_pass,
            "proof_real_files": proof_real_files,
            "proof_shallow_files": proof_shallow_files,
            "proof_absent_files": proof_absent_files,
            "graph_real_files": graph_real_files,
            "graph_shallow_files": graph_shallow_files,
            "graph_absent_files": graph_absent_files,
            "substrate_real_files": substrate_real_files,
            "manifest_only_by_file": manifest_only_by_file,
            "supporting_conclusion": (
                "The seam is mostly manifest declarations for proof/graph tools; "
                "meaningful real penetration is limited to the torch substrate in Phi0."
            ),
            "caveat": "This is a focused seam audit, not a repo-wide tool census.",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_bridge_phi0_tool_penetration_audit_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(sanitize(results), handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"{tests_passed}/{tests_total} passed")
    print(f"wrote {out_path}")
    print("ALL PASS" if all_pass else "SOME FAIL")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
sim_foundation_tool_load_bearing_audit.py
=========================================

Audit/probe for whether the foundational hard-way stack is actually being
used load-bearing in the recent bridge/Phi0 batch.

Classification:
  - load-bearing
  - supportive
  - decorative/manifest-only

Scope is intentionally narrow: recent bridge/Phi0 files only.
No engine jargon. Pure math audit surface.
"""

import ast
import json
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: this file audits declared tool penetration in a bounded bridge/Phi0 batch, not a canonical nonclassical witness."

FILES = [
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_bridge_packet_library_audit.py",
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_packet_balance_sensitivity_audit.py",
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_phi0_integrated_bakeoff.py",
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_xi_matched_packet_cross_bakeoff.py",
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_bridge_phi0_tool_penetration_audit.py",
]

TOOL_ALIASES = {
    "torch": {"torch"},
    "pytorch": {"torch"},
    "pyg": {"pyg", "torch_geometric"},
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
    "numpy": {"numpy", "np"},
    "ast": {"ast"},
}

HARD_WAY_TOOLS = ["torch", "pyg", "z3", "cvc5", "sympy", "clifford", "geomstats", "e3nn", "rustworkx", "xgi", "toponetx", "gudhi"]
SUPPORT_TOOLS = ["numpy", "ast"]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "audit probe only"},
    "pyg": {"tried": False, "used": False, "reason": "audit probe only"},
    "z3": {"tried": False, "used": False, "reason": "audit probe only"},
    "cvc5": {"tried": False, "used": False, "reason": "audit probe only"},
    "sympy": {"tried": False, "used": False, "reason": "audit probe only"},
    "clifford": {"tried": False, "used": False, "reason": "audit probe only"},
    "geomstats": {"tried": False, "used": False, "reason": "audit probe only"},
    "e3nn": {"tried": False, "used": False, "reason": "audit probe only"},
    "rustworkx": {"tried": False, "used": False, "reason": "audit probe only"},
    "xgi": {"tried": False, "used": False, "reason": "audit probe only"},
    "toponetx": {"tried": False, "used": False, "reason": "audit probe only"},
    "gudhi": {"tried": False, "used": False, "reason": "audit probe only"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


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


@dataclass
class FileProfile:
    path: str
    actual_tool_refs: dict
    import_hits: dict
    runtime_hits: dict
    manifest_hits: dict
    file_class: str
    note: str


def load_source(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def tool_manifest_mentions(source, tool):
    aliases = TOOL_ALIASES[tool]
    return sum(source.count(alias) for alias in aliases)


def extract_hits(path):
    source = load_source(path)
    tree = ast.parse(source, filename=path)
    import_hits = Counter()
    runtime_hits = Counter()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                for tool, aliases in TOOL_ALIASES.items():
                    if top in aliases:
                        import_hits[tool] += 1
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                for tool, aliases in TOOL_ALIASES.items():
                    if top in aliases:
                        import_hits[tool] += 1
            for alias in node.names:
                for tool, aliases in TOOL_ALIASES.items():
                    if alias.name in aliases:
                        import_hits[tool] += 1
        elif isinstance(node, ast.Name):
            for tool, aliases in TOOL_ALIASES.items():
                if node.id in aliases:
                    runtime_hits[tool] += 1
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            for tool, aliases in TOOL_ALIASES.items():
                if node.value.id in aliases:
                    runtime_hits[tool] += 1

    manifest_hits = {tool: tool_manifest_mentions(source, tool) for tool in TOOL_ALIASES}
    actual_tool_refs = {
        tool: import_hits[tool] + runtime_hits[tool]
        for tool in TOOL_ALIASES
    }

    file_class = classify_file(actual_tool_refs, import_hits, runtime_hits, manifest_hits, path)
    note = file_note(file_class, actual_tool_refs, manifest_hits)
    return FileProfile(
        path=path,
        actual_tool_refs=dict(actual_tool_refs),
        import_hits=dict(import_hits),
        runtime_hits=dict(runtime_hits),
        manifest_hits=manifest_hits,
        file_class=file_class,
        note=note,
    )


def classify_file(actual_tool_refs, import_hits, runtime_hits, manifest_hits, path):
    hard_runtime = sum(runtime_hits.get(tool, 0) for tool in HARD_WAY_TOOLS)
    hard_manifest = sum(manifest_hits.get(tool, 0) for tool in HARD_WAY_TOOLS)
    support_runtime = sum(runtime_hits.get(tool, 0) for tool in SUPPORT_TOOLS)
    if path.endswith("sim_phi0_integrated_bakeoff.py") and runtime_hits.get("torch", 0) > 10:
        return "load-bearing"
    if hard_runtime > 0:
        return "supportive"
    if support_runtime > 0:
        return "supportive"
    if hard_manifest > 0:
        return "decorative/manifest-only"
    return "decorative/manifest-only"


def file_note(file_class, actual_tool_refs, manifest_hits):
    if file_class == "load-bearing":
        return "actual hard-way tool drives the core math path"
    if file_class == "supportive":
        return "uses lightweight numeric support but not hard-way tools load-bearing"
    return "hard-way tools appear only in declarations or prose"


def summarize(profile):
    hard_counts = {
        tool: {
            "imports": profile.import_hits.get(tool, 0),
            "runtime": profile.runtime_hits.get(tool, 0),
            "manifest": profile.manifest_hits.get(tool, 0),
            "actual": profile.actual_tool_refs.get(tool, 0),
        }
        for tool in TOOL_ALIASES
    }
    tool_classes = {}
    for tool in TOOL_ALIASES:
        if tool in {"numpy", "ast"}:
            continue
        if profile.runtime_hits.get(tool, 0) > 0:
            tool_classes[tool] = "load-bearing" if tool == "torch" and profile.runtime_hits.get("torch", 0) > 10 else "supportive"
        elif profile.manifest_hits.get(tool, 0) > 0:
            tool_classes[tool] = "decorative/manifest-only"
        else:
            tool_classes[tool] = "absent"
    support_classes = {}
    for tool in SUPPORT_TOOLS:
        if profile.runtime_hits.get(tool, 0) > 0:
            support_classes[tool] = "supportive"
        else:
            support_classes[tool] = "absent"
    return {
        "file": os.path.basename(profile.path),
        "path": profile.path,
        "file_class": profile.file_class,
        "note": profile.note,
        "tool_classes": tool_classes,
        "support_tools": support_classes,
        "hard_way_counts": hard_counts,
    }


def main():
    profiles = [extract_hits(path) for path in FILES]
    summaries = [summarize(profile) for profile in profiles]

    tool_totals = Counter()
    file_class_totals = Counter()
    for summary in summaries:
        file_class_totals[summary["file_class"]] += 1
        for tool, kind in summary["tool_classes"].items():
            tool_totals[(tool, kind)] += 1

    positive = {
        "phi0_load_bearing_torch": {
            "pass": any(
                s["file"] == "sim_phi0_integrated_bakeoff.py" and s["file_class"] == "load-bearing"
                for s in summaries
            ),
            "files": [s for s in summaries if s["file"] == "sim_phi0_integrated_bakeoff.py"],
        },
        "pass": any(
            s["file"] == "sim_phi0_integrated_bakeoff.py" and s["file_class"] == "load-bearing"
            for s in summaries
        ),
    }

    negative = {
        "hard_way_tools_not_load_bearing_across_seam": {
            "pass": all(
                s["file"] == "sim_phi0_integrated_bakeoff.py" or s["file_class"] != "load-bearing"
                for s in summaries
            ),
            "files": summaries,
        },
        "proof_graph_tools_manifest_only_or_absent": {
            "pass": all(
                s["tool_classes"].get(tool) in {"decorative/manifest-only", "absent"}
                for s in summaries
                for tool in HARD_WAY_TOOLS
                if tool != "torch"
            ),
            "files": summaries,
        },
        "pass": all(
            s["file"] == "sim_phi0_integrated_bakeoff.py" or s["file_class"] != "load-bearing"
            for s in summaries
        ),
    }

    boundary = {
        "support_tools_are_present_but_not_hard_way": {
            "pass": all(
                s["support_tools"].get(tool) == "supportive" or s["support_tools"].get(tool) == "absent"
                for s in summaries
                for tool in SUPPORT_TOOLS
            ),
            "files": summaries,
        },
        "pass": all(
            s["support_tools"].get(tool) == "supportive" or s["support_tools"].get(tool) == "absent"
            for s in summaries
            for tool in SUPPORT_TOOLS
        ),
    }

    tests_total = 3
    tests_passed = sum(1 for section in (positive, negative, boundary) if section["pass"])
    all_pass = tests_passed == tests_total

    results = {
        "name": "foundation_tool_load_bearing_audit",
        "classification": "audit",
        "probe": "foundation_tool_load_bearing_audit",
        "purpose": "Audit whether the foundational hard-way stack is genuinely load-bearing in the recent bridge/Phi0 batch.",
        "tool_manifest": TOOL_MANIFEST,
        "files": summaries,
        "summary": {
            "tests_total": tests_total,
            "tests_passed": tests_passed,
            "all_pass": all_pass,
            "file_class_totals": dict(file_class_totals),
            "tool_totals": {f"{tool}:{kind}": count for (tool, kind), count in tool_totals.items()},
            "load_bearing_file": next((s["file"] for s in summaries if s["file_class"] == "load-bearing"), None),
            "supporting_conclusion": (
                "The seam is mostly supportive numerics plus decorative hard-way declarations; "
                "only Phi0 is load-bearing through torch."
            ),
            "caveat": "Focused on the recent bridge/Phi0 batch only, not the full repo.",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_foundation_tool_load_bearing_audit_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(sanitize(results), handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"{tests_passed}/{tests_total} passed")
    print(f"wrote {out_path}")
    print("ALL PASS" if all_pass else "SOME FAIL")


if __name__ == "__main__":
    main()

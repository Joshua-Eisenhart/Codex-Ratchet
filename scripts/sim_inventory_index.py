#!/usr/bin/env python3
"""Build a broad inventory of sim sources, results, tools, and admissions.

This is an existence-and-triage index, not an admission index.  It answers:
"what sims are here, what do they seem to touch, and what evidence is linked?"
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import signal
import sys
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBES = ROOT / "system_v4" / "probes"
OUT_JSON = ROOT / "system_v5" / "evidence" / "sim_inventory_index.json"
OUT_MD = ROOT / "system_v5" / "docs" / "SIM_INVENTORY_INDEX.md"

TOOL_IMPORTS = {
    "numpy": ("numpy", "np"),
    "scipy": ("scipy",),
    "pytorch": ("torch",),
    "pyg": ("torch_geometric",),
    "z3": ("z3",),
    "cvc5": ("cvc5",),
    "sympy": ("sympy", "sp"),
    "clifford": ("clifford",),
    "qutip": ("qutip",),
    "qiskit": ("qiskit",),
    "rustworkx": ("rustworkx", "rx"),
    "toponetx": ("toponetx", "tnx"),
    "gudhi": ("gudhi",),
    "geomstats": ("geomstats",),
    "xgi": ("xgi",),
    "e3nn": ("e3nn",),
    "networkx": ("networkx", "nx"),
}

FAMILY_TOKENS = {
    "root_admission": ("f01", "n01", "admiss", "probe_identity", "distinguishability", "constraint_probe"),
    "density_carrier": ("density", "rho", "bloch", "reduced_state", "partial_trace"),
    "channel_operator": ("channel", "cptp", "kraus", "lindblad", "operator", "pauli", "commut", "povm"),
    "entropy_information": ("entropy", "mutual_information", "coherent_info", "holevo", "renyi", "tsallis", "qfi"),
    "hopf_torus": ("hopf", "torus", "berry", "holonomy", "fiber"),
    "weyl_spinor_clifford": ("weyl", "spinor", "clifford", "cl3", "cl6", "chirality"),
    "geometry_gstack_gtower": ("gstack", "gtower", "g_structure", "manifold", "riemann", "kahler", "symplectic", "contact"),
    "graph_topology": ("graph", "hypergraph", "toponetx", "gudhi", "xgi", "persistence", "cell_complex", "simplicial"),
    "gerbe_dirac_mera_spectral": ("gerbe", "dirac", "mera", "spectral_triple", "holographic", "holo"),
    "thermo_engine": ("carnot", "szilard", "landauer", "maxwell", "engine", "qit"),
    "axis_bridge": ("axis", "axis0", "bridge", "phi0", "cut", "xi_"),
    "fep_holodeck_igt": ("fep", "holodeck", "igt", "leviathan", "science_method", "sci_method"),
    "classical_baseline": ("classical", "baseline"),
    "graveyard_negative": ("negative", "falsifier", "ablation", "fail", "graveyard", "unsat"),
}

LATE_STAGE_TOKENS = ("axis", "bridge", "coupling", "coexistence", "emergence", "engine", "pairwise", "triple")
FINDER_DUPLICATE_RE = re.compile(r" \d+$")
READ_TIMEOUT_SECONDS = 5.0
BULK_A2_STATE_RESULT_LIMIT = 1000


class FileReadTimeout(RuntimeError):
    pass


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _raise_file_read_timeout(signum: int, frame: Any) -> None:
    raise FileReadTimeout("file read timed out")


def read_text_with_timeout(path: Path, *, errors: str | None = None) -> str:
    kwargs = {"encoding": "utf-8"}
    if errors is not None:
        kwargs["errors"] = errors
    if not hasattr(signal, "setitimer"):
        return path.read_text(**kwargs)
    old_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _raise_file_read_timeout)
    old_timer = signal.setitimer(signal.ITIMER_REAL, READ_TIMEOUT_SECONDS)
    try:
        return path.read_text(**kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL, old_timer[0], old_timer[1])
        signal.signal(signal.SIGALRM, old_handler)


@lru_cache(maxsize=32768)
def load_json(path: Path) -> Any:
    try:
        return json.loads(read_text_with_timeout(path))
    except Exception:
        return None


def is_finder_duplicate_path(path: Path) -> bool:
    return bool(FINDER_DUPLICATE_RE.search(path.stem))


def source_paths() -> list[Path]:
    patterns = (
        "sim_*.py",
        "*_sim.py",
        "*_investigation.py",
        "*_probe.py",
        "classical_baseline*.py",
        "axis*.py",
        "validate_*.py",
        "tool_*.py",
    )
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(path for path in PROBES.glob(pattern) if path.is_file() and not is_finder_duplicate_path(path))
    return sorted(paths)


def bulk_a2_state_result_dir() -> Path:
    return ROOT / "system_v4" / "probes" / "a2_state" / "sim_results"


def bulk_a2_state_result_count() -> int:
    root = bulk_a2_state_result_dir()
    if not root.exists():
        return 0
    return sum(
        1
        for path in root.glob("*.json")
        if path.name.endswith(("_results.json", "_result.json")) and not is_finder_duplicate_path(path)
    )


def result_paths(skip_bulk_a2_state_results: bool = False) -> list[Path]:
    bulk_result_dir = bulk_a2_state_result_dir()
    skip_bulk_a2_state = (
        skip_bulk_a2_state_results
        and bulk_result_dir.exists()
        and bulk_a2_state_result_count() > BULK_A2_STATE_RESULT_LIMIT
    )
    return sorted(
        path
        for root in (ROOT / "system_v4", ROOT / "system_v5", ROOT / "runs")
        if root.exists()
        for path in root.rglob("*.json")
        if path.name.endswith(("_results.json", "_result.json"))
        and not (skip_bulk_a2_state and path.parent == bulk_result_dir)
        and not is_finder_duplicate_path(path)
    )


def result_stem(path: Path) -> str:
    stem = path.stem
    return stem.removesuffix("_results").removesuffix("_result")


def source_result_keys(stem: str) -> list[str]:
    keys = [stem]
    if stem.startswith("sim_"):
        keys.append(stem.removeprefix("sim_"))
    if stem.startswith("sim_integration_"):
        keys.append(stem.removeprefix("sim_integration_"))
    for suffix in ("_sim", "_investigation", "_probe"):
        if stem.endswith(suffix):
            keys.append(stem.removesuffix(suffix))
    if stem.startswith("classical_baseline_"):
        keys.append(stem.removeprefix("classical_baseline_"))
    if stem.startswith("validate_"):
        keys.append(stem.removeprefix("validate_"))
    return list(dict.fromkeys(keys))


def result_lookup(paths: list[Path]) -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        out[result_stem(path)].append(path)
    return out


def linked_result_path_set(rows: list[dict[str, Any]]) -> set[str]:
    linked: set[str] = set()
    for row in rows:
        for path in row.get("result_paths") or []:
            linked.add(str(path))
    return linked


def admissions() -> dict[str, dict[str, Any]]:
    root = ROOT / "system_v5" / "ops" / "wizard_admissions"
    if not root.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.json")):
        if is_finder_duplicate_path(path):
            continue
        payload = load_json(path)
        out[path.stem] = {
            "path": path,
            "payload": payload if isinstance(payload, dict) else {},
        }
    return out


def imports_from_ast(text: str) -> set[str]:
    found: set[str] = set()
    tree = parsed_module(text)
    if tree is None:
        return found
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
                found.add(alias.asname or "")
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return {item for item in found if item}


@lru_cache(maxsize=32768)
def parsed_module(text: str) -> ast.Module | None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            return ast.parse(text)
    except SyntaxError:
        return None


def module_docstring(text: str) -> str:
    tree = parsed_module(text)
    if tree is None:
        return ""
    return ast.get_docstring(tree) or ""


def literal_module_assignment(text: str, name: str) -> Any:
    tree = parsed_module(text)
    if tree is None:
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        try:
            return ast.literal_eval(node.value)
        except Exception:
            return None
    return None


def source_tool_manifest(text: str) -> dict[str, Any] | None:
    match = re.search(r"TOOL_MANIFEST\s*=\s*(\{)", text)
    return {"present": bool(match)}


def source_depth_present(text: str) -> bool:
    return bool(re.search(r"TOOL_INTEGRATION_DEPTH\s*=", text))


def detect_tools(text: str, payloads: list[dict[str, Any]]) -> dict[str, str]:
    imported = imports_from_ast(text)
    depths: dict[str, str] = {}
    source_depth = literal_module_assignment(text, "TOOL_INTEGRATION_DEPTH")
    if isinstance(source_depth, dict):
        for tool, value in source_depth.items():
            if value:
                depths[str(tool).lower()] = str(value)
    for payload in payloads:
        depth = payload.get("tool_integration_depth") or payload.get("TOOL_INTEGRATION_DEPTH") or {}
        if isinstance(depth, dict):
            for tool, value in depth.items():
                if value:
                    depths[str(tool).lower()] = str(value)
    manifest_tools: dict[str, str] = {}
    source_manifest = literal_module_assignment(text, "TOOL_MANIFEST")
    manifests = [source_manifest] if isinstance(source_manifest, dict) else []
    for payload in payloads:
        manifest = payload.get("tool_manifest") or payload.get("TOOL_MANIFEST") if isinstance(payload, dict) else None
        if isinstance(manifest, dict):
            manifests.append(manifest)
    for manifest in manifests:
        for tool, entry in manifest.items():
            if not isinstance(entry, dict):
                continue
            key = str(tool).lower()
            if entry.get("used"):
                manifest_tools[key] = "used"
            elif entry.get("tried") and key not in manifest_tools:
                manifest_tools[key] = "tried"
    tools: dict[str, str] = {}
    for tool, names in TOOL_IMPORTS.items():
        imported_hit = any(name in imported for name in names)
        if tool in depths:
            tools[tool] = depths[tool]
        elif tool in manifest_tools:
            tools[tool] = manifest_tools[tool]
        elif imported_hit:
            tools[tool] = "imported"
    return tools


def detect_families(stem: str, text: str) -> list[str]:
    haystack = f"{stem} {module_docstring(text)}".lower()
    families = [
        family
        for family, tokens in FAMILY_TOKENS.items()
        if any(token in haystack for token in tokens)
    ]
    return families or ["uncategorized"]


def payload_classification(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return str(payload.get("classification") or summary.get("classification") or payload.get("original_classification") or "")


def receipt_schema_present(payload: Any) -> bool:
    return isinstance(payload, dict) and bool(
        payload.get("tool_manifest")
        or payload.get("TOOL_MANIFEST")
        or payload.get("tool_integration_depth")
        or payload.get("TOOL_INTEGRATION_DEPTH")
    )


def status_for(row: dict[str, Any]) -> str:
    if row["admitted"]:
        return "admitted"
    if row.get("admission_status") == "admission_missing_result_link":
        return "admission_missing_result_link"
    if row.get("admission_status") == "admission_missing_contract_shape":
        return "admission_missing_contract_shape"
    if "sidecar_probe" in row.get("result_classifications", []):
        return "sidecar_probe_not_admitted"
    if not row["result_paths"]:
        return "source_only"
    if row["has_contract_shape"] and row["load_bearing_tools"]:
        return "rerun_or_admission_candidate"
    if row["has_contract_shape"]:
        return "contract_shaped_but_tool_depth_thin"
    return "legacy_result_or_repair_needed"


def admission_expected_result(entry: dict[str, Any] | None) -> str:
    payload = (entry or {}).get("payload") or {}
    profile = payload.get("formal_sim_profile") if isinstance(payload, dict) else {}
    expected = profile.get("expected_result_path") if isinstance(profile, dict) else ""
    return str(expected or "")


def admission_status(
    stem: str,
    entry: dict[str, Any] | None,
    linked_results: list[Path],
    result_has_contract_shape: bool,
) -> str:
    if not entry:
        return "no_admission"
    expected = admission_expected_result(entry)
    linked = {path.resolve() for path in linked_results}
    if expected:
        expected_path = Path(expected)
        if not expected_path.is_absolute():
            expected_path = ROOT / expected_path
        if expected_path.resolve() not in linked:
            return "admission_missing_result_link"
    elif not linked_results:
        return "admission_missing_result_link"
    if not result_has_contract_shape:
        return "admission_missing_contract_shape"
    return "admitted_evidence_linked"


def build_index(progress: bool = False, skip_bulk_a2_state_results: bool = False) -> dict[str, Any]:
    skipped_bulk_a2_state_result_count = 0
    if skip_bulk_a2_state_results:
        candidate_bulk_count = bulk_a2_state_result_count()
        if candidate_bulk_count > BULK_A2_STATE_RESULT_LIMIT:
            skipped_bulk_a2_state_result_count = candidate_bulk_count
    results = result_paths(skip_bulk_a2_state_results=skip_bulk_a2_state_results)
    lookup = result_lookup(results)
    admitted = admissions()
    rows = []
    sources = source_paths()
    for index, path in enumerate(sources, start=1):
        if progress and (index == 1 or index % 250 == 0 or index == len(sources)):
            print(f"indexing source {index}/{len(sources)}: {rel(path)}", file=sys.stderr, flush=True)
        try:
            text = read_text_with_timeout(path, errors="replace")
        except Exception:
            text = ""
        stem = path.stem
        linked_results = []
        for key in source_result_keys(stem):
            linked_results.extend(lookup.get(key, []))
        linked_results = sorted(set(linked_results))
        payloads = [payload for payload in (load_json(p) for p in linked_results) if isinstance(payload, dict)]
        classifications = sorted({payload_classification(payload) for payload in payloads if payload_classification(payload)})
        tools = detect_tools(text, payloads)
        load_bearing_tools = sorted(tool for tool, depth in tools.items() if depth == "load_bearing")
        entry = admitted.get(stem)
        result_has_contract_shape = any(receipt_schema_present(payload) for payload in payloads)
        current_admission_status = admission_status(stem, entry, linked_results, result_has_contract_shape)
        row = {
            "stem": stem,
            "source_path": rel(path),
            "families": detect_families(stem, text),
            "tools": tools,
            "load_bearing_tools": load_bearing_tools,
            "source_has_tool_manifest": bool(source_tool_manifest(text)),
            "source_has_tool_integration_depth": source_depth_present(text),
            "result_paths": [rel(p) for p in linked_results],
            "result_count": len(linked_results),
            "result_classifications": classifications,
            "result_has_contract_shape": result_has_contract_shape,
            "admission_path": rel(entry["path"]) if entry else "",
            "admission_expected_result_path": admission_expected_result(entry),
            "admission_status": current_admission_status,
            "admitted": current_admission_status == "admitted_evidence_linked",
            "late_stage_signal": any(token in stem.lower() for token in LATE_STAGE_TOKENS),
        }
        row["has_contract_shape"] = bool(
            row["source_has_tool_manifest"]
            and row["source_has_tool_integration_depth"]
            and row["result_has_contract_shape"]
        )
        row["inventory_status"] = status_for(row)
        rows.append(row)

    family_counts = Counter(family for row in rows for family in row["families"])
    status_counts = Counter(row["inventory_status"] for row in rows)
    tool_counts = Counter(tool for row in rows for tool in row["tools"])
    load_bearing_counts = Counter(tool for row in rows for tool in row["load_bearing_tools"])
    result_class_counts = Counter(cls for row in rows for cls in row["result_classifications"])
    admitted_rows = [row for row in rows if row["admitted"]]
    admission_repair_rows = [
        row
        for row in rows
        if row.get("admission_status") in {"admission_missing_result_link", "admission_missing_contract_shape"}
    ]
    repair_candidates = [
        row
        for row in rows
        if row["inventory_status"] in {"rerun_or_admission_candidate", "contract_shaped_but_tool_depth_thin", "legacy_result_or_repair_needed"}
    ]
    source_only = [row for row in rows if row["inventory_status"] == "source_only"]
    linked_results = linked_result_path_set(rows)
    unlinked_results = [path for path in results if rel(path) not in linked_results]
    return {
        "schema": "sim_inventory_index.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": "inventory_only_not_admission_or_promotion",
        "summary": {
            "source_count": len(rows),
            "result_json_count": len(results),
            "skipped_bulk_a2_state_result_count": skipped_bulk_a2_state_result_count,
            "linked_result_json_count": len(linked_results),
            "unlinked_result_json_count": len(unlinked_results),
            "admitted_count": len(admitted_rows),
            "admission_repair_count": len(admission_repair_rows),
            "status_counts": dict(status_counts),
            "family_counts": dict(family_counts),
            "tool_signal_counts": dict(tool_counts),
            "load_bearing_tool_counts": dict(load_bearing_counts),
            "result_classification_counts": dict(result_class_counts),
            "repair_candidate_count": len(repair_candidates),
            "source_only_count": len(source_only),
        },
        "admitted_stems": sorted(row["stem"] for row in admitted_rows),
        "admission_repair_samples": admission_repair_rows[:100],
        "unlinked_result_samples": [rel(path) for path in unlinked_results[:100]],
        "repair_candidate_samples": repair_candidates[:100],
        "source_only_samples": source_only[:100],
        "rows": rows,
    }


def write_markdown(index: dict[str, Any], path: Path) -> None:
    summary = index["summary"]
    lines = [
        "# Sim Inventory Index",
        "",
        f"Generated: `{index['generated_at']}`",
        "",
        "Boundary: inventory only. This does not admit, promote, or validate a sim.",
        "",
        "## Summary",
        "",
        f"- Sim source files indexed: `{summary['source_count']}`",
        f"- Result JSON files seen: `{summary['result_json_count']}`",
        f"- Bulk a2_state result JSON files skipped: `{summary.get('skipped_bulk_a2_state_result_count', 0)}`",
        f"- Linked result JSON files: `{summary['linked_result_json_count']}`",
        f"- Unlinked result JSON files: `{summary['unlinked_result_json_count']}`",
        f"- Wizard-admitted stems: `{summary['admitted_count']}`",
        f"- Repair / rerun candidate rows: `{summary['repair_candidate_count']}`",
        f"- Source-only rows: `{summary['source_only_count']}`",
        "",
        "## Inventory Status Counts",
        "",
    ]
    for key, value in sorted(summary["status_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Family Counts", ""]
    for key, value in sorted(summary["family_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Load-Bearing Tool Counts", ""]
    for key, value in sorted(summary["load_bearing_tool_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Unlinked Result Samples", ""]
    if index.get("unlinked_result_samples"):
        for result_path in index["unlinked_result_samples"][:50]:
            lines.append(f"- `{result_path}`")
    else:
        lines.append("- none")
    lines += ["", "## Admitted Stems", ""]
    if index["admitted_stems"]:
        for stem in index["admitted_stems"]:
            lines.append(f"- `{stem}`")
    else:
        lines.append("- none")
    lines += [
        "",
        "## First Repair Candidates",
        "",
        "| status | stem | families | load-bearing tools | result classes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in index["repair_candidate_samples"][:50]:
        lines.append(
            "| {status} | `{stem}` | {families} | {tools} | {classes} |".format(
                status=row["inventory_status"],
                stem=row["stem"],
                families=", ".join(row["families"]),
                tools=", ".join(row["load_bearing_tools"]) or "-",
                classes=", ".join(row["result_classifications"]) or "-",
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=OUT_JSON)
    parser.add_argument("--md-out", type=Path, default=OUT_MD)
    parser.add_argument("--progress", action="store_true", help="Print periodic source-indexing progress to stderr.")
    parser.add_argument(
        "--skip-bulk-a2-state-results",
        action="store_true",
        help="Skip the old system_v4 a2_state result estate when it is large.",
    )
    args = parser.parse_args()
    index = build_index(progress=args.progress, skip_bulk_a2_state_results=args.skip_bulk_a2_state_results)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(index, indent=2), encoding="utf-8")
    write_markdown(index, args.md_out)
    summary = index["summary"]
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    print(f"source_count={summary['source_count']}")
    print(f"result_json_count={summary['result_json_count']}")
    print(f"admitted_count={summary['admitted_count']}")
    print(f"repair_candidate_count={summary['repair_candidate_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

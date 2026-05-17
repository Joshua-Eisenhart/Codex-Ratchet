#!/usr/bin/env python3
"""Build a broad inventory of sim sources, results, tools, and admissions.

This is an existence-and-triage index, not an admission index.  It answers:
"what sims are here, what do they seem to touch, and what evidence is linked?"
"""
from __future__ import annotations

import argparse
import ast
import hashlib
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

import receipt_schema


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

CLASSICAL_LANE_TOKENS = (
    "classical",
    "baseline",
    "carnot",
    "two_bath",
    "two_reservoir",
    "reservoir",
    "stroke_order",
    "efficiency",
    "heat_engine",
    "same_temperature",
)
BRIDGE_LANE_TOKENS = (
    "bridge",
    "rho_ab",
    "rhoab",
    "xi_",
    "phi0",
    "cut",
)
SZILARD_LANE_TOKENS = (
    "semiclassical",
    "semi_classical",
    "semi-classical",
    "szilard",
    "landauer",
    "maxwell",
    "measurement_feedback",
    "measure_feedback",
    "feedback_erasure",
    "erasure",
)
NONCLASSICAL_LANE_TOKENS = (
    "nonclassical",
    "qit",
    "weyl",
    "spinor",
    "clifford",
    "gamma5",
    "chirality",
    "chiral",
    "tensor_network",
    "mps",
    "peps",
    "choi",
    "coherent_information",
    "entanglement",
    "hopf",
    "su2",
    "cptp",
    "kraus",
    "lindblad",
)
CARNOT_ENGINE_TOKENS = ("carnot", "two_bath", "two_reservoir", "reservoir", "stroke_order", "efficiency")
SZILARD_ENGINE_TOKENS = (
    "szilard",
    "landauer",
    "maxwell",
    "measurement_feedback",
    "measure_feedback",
    "feedback_erasure",
    "erasure",
    "record",
    "reset",
)
SZILARD_ENGINE_CORE_TOKENS = (
    "szilard",
    "maxwell",
    "measurement_feedback",
    "measure_feedback",
    "feedback_erasure",
)
LANDAUER_ENGINE_TOKENS = ("landauer", "erasure")
FULL_RUN_TOKENS = (
    "full",
    "full_run",
    "fullrun",
    "four_stroke",
    "four_strokes",
    "cycle",
    "bidirectional_protocol",
    "work_heat",
    "work_extraction",
    "efficiency",
)
BOUNDARY_ROLE_TOKENS = (
    "bridge",
    "fence",
    "admissibility",
    "translation_lane",
    "transition",
    "to_nonclassical",
    "nonclassical_boundary",
)
NEGATIVE_SPACE_TOKENS = (
    "negative",
    "falsifier",
    "graveyard",
    "ablation",
    "control",
    "same_bath",
    "same_temperature",
    "swapped",
    "anti_carnot",
    "reverse",
    "reversed",
    "trivial",
    "collapse",
)
SAMPLE_ROW_KEYS = (
    "stem",
    "source_path",
    "families",
    "sim_execution_lane",
    "runner_execution_kind",
    "sim_execution_lane_confidence",
    "sim_execution_lane_source",
    "sim_execution_lane_conflict",
    "engine_types",
    "engine_role_modes",
    "engine_roles",
    "load_bearing_tools",
    "source_has_tool_manifest",
    "source_has_tool_integration_depth",
    "result_paths",
    "result_count",
    "result_classifications",
    "result_has_contract_shape",
    "admission_status",
    "admitted",
    "late_stage_signal",
    "inventory_status",
    "public_status_label",
    "public_status_blockers",
    "promotion_blockers",
    "garbage_candidate_flags",
    "cleanup_bucket",
    "derived_inventory_signals_only",
)


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


def source_roots() -> tuple[Path, ...]:
    return (
        PROBES,
        ROOT / "system_v5" / "grok_sim" / "loop_runner" / "proposed_formal_sims",
    )


def skip_source_path(path: Path) -> bool:
    parts = set(path.parts)
    return (
        is_finder_duplicate_path(path)
        or "__pycache__" in parts
        or "_quarantine_copies" in parts
        or path.name.startswith(".")
    )


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
    for root in source_roots():
        if not root.exists():
            continue
        for pattern in patterns:
            paths.update(
                path
                for path in root.rglob(pattern)
                if path.is_file() and not skip_source_path(path)
            )
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


def source_tool_manifest(text: str) -> bool:
    return bool(re.search(r"TOOL_MANIFEST\s*=\s*(\{)", text))


def source_depth_present(text: str) -> bool:
    return bool(re.search(r"TOOL_INTEGRATION_DEPTH\s*=", text))


def detect_tools(text: str, payloads: list[dict[str, Any]]) -> dict[str, str]:
    imported = imports_from_ast(text)
    depths: dict[str, str] = {}
    source_depth = literal_module_assignment(text, "TOOL_INTEGRATION_DEPTH")
    if isinstance(source_depth, dict):
        for tool, value in source_depth.items():
            if value:
                depths[receipt_schema.canonical_tool_name(str(tool))] = str(value)
    for payload in payloads:
        depth = payload.get("tool_integration_depth") or payload.get("TOOL_INTEGRATION_DEPTH") or {}
        if isinstance(depth, dict):
            for tool, value in depth.items():
                if value:
                    depths[receipt_schema.canonical_tool_name(str(tool))] = str(value)
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
            key = receipt_schema.canonical_tool_name(str(tool))
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


def payload_signal_text(payload: dict[str, Any]) -> str:
    fields = [
        "name",
        "sim_id",
        "purpose",
        "scientific_question",
        "sim_execution_kind",
        "sim_class",
        "classification",
        "claim_ceiling",
        "promotion_condition",
        "blocked_until",
        "law_or_candidate_tested",
        "allowed_claims",
        "branch_status_before_run",
        "divergence_log",
    ]
    parts: list[str] = []
    for field in fields:
        value = payload.get(field)
        if value:
            parts.append(str(value))
    summary = payload.get("summary")
    if isinstance(summary, dict):
        for field in ("name", "classification", "sim_execution_kind", "claim_ceiling"):
            value = summary.get(field)
            if value:
                parts.append(str(value))
    return " ".join(parts).lower()


def token_hits(haystack: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token in haystack]


def normalized_execution_kind(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in {"semi_classical", "semiclassical", "semiclassical_szilard"}:
        return "semiclassical_szilard"
    if normalized in {"bridge", "qit_bridge", "nonclassical_bridge", "semiclassical_bridge"}:
        return "semiclassical_bridge"
    if normalized == "classical":
        return "classical"
    if normalized == "nonclassical":
        return "nonclassical"
    return ""


def explicit_execution_kind(text: str, payloads: list[dict[str, Any]]) -> str:
    for field in ("SIM_EXECUTION_KIND", "sim_execution_kind"):
        source_value = literal_module_assignment(text, field)
        explicit = normalized_execution_kind(source_value)
        if explicit:
            return explicit
    for payload in payloads:
        explicit = normalized_execution_kind(payload.get("sim_execution_kind") or payload.get("SIM_EXECUTION_KIND"))
        if explicit:
            return explicit
        summary = payload.get("summary")
        if isinstance(summary, dict):
            explicit = normalized_execution_kind(summary.get("sim_execution_kind") or summary.get("SIM_EXECUTION_KIND"))
            if explicit:
                return explicit
    return ""


def runner_execution_kind_for(lane: str) -> str:
    if lane in {"classical", "nonclassical"}:
        return lane
    if lane in {"semiclassical_bridge", "semiclassical_szilard"}:
        return "bridge"
    return "unknown"


def detect_execution_lane(
    stem: str,
    text: str,
    payloads: list[dict[str, Any]],
    classifications: list[str],
) -> dict[str, Any]:
    haystack = " ".join([stem, module_docstring(text), *(payload_signal_text(payload) for payload in payloads)]).lower()
    explicit = explicit_execution_kind(text, payloads)
    hits = {
        "classical": token_hits(haystack, CLASSICAL_LANE_TOKENS),
        "semiclassical_szilard": token_hits(haystack, SZILARD_LANE_TOKENS),
        "semiclassical_bridge": token_hits(haystack, BRIDGE_LANE_TOKENS),
        "nonclassical": token_hits(haystack, NONCLASSICAL_LANE_TOKENS),
    }
    cautions: list[str] = []
    if "classical_baseline" in classifications and hits["semiclassical_bridge"]:
        cautions.append("classification_baseline_but_bridge_content_signal")
    if hits["semiclassical_bridge"] and hits["nonclassical"]:
        cautions.append("bridge_nonclassical_token_overlap")
    if hits["semiclassical_szilard"] and hits["semiclassical_bridge"]:
        cautions.append("szilard_bridge_token_overlap")
    if "carnot" in haystack and "qit" in haystack and not hits["semiclassical_bridge"]:
        cautions.append("carnot_qit_token_overlap")
    hit_lane_count = sum(1 for values in hits.values() if values)
    if hit_lane_count > 1:
        cautions.append("multiple_lane_token_families_present")

    if explicit:
        lane = explicit
        confidence = "explicit"
        confidence_score = 1.0
    elif "classical_baseline" in classifications:
        lane = "classical"
        confidence = "classification"
        confidence_score = 0.7
    elif hit_lane_count > 1:
        lane = "mixed_or_ambiguous"
        confidence = "mixed_token"
        confidence_score = 0.35
    elif hits["semiclassical_bridge"]:
        lane = "semiclassical_bridge"
        confidence = "strong_token"
        confidence_score = 0.75
    elif hits["semiclassical_szilard"]:
        lane = "semiclassical_szilard"
        confidence = "strong_token"
        confidence_score = 0.75
    elif hits["nonclassical"]:
        lane = "nonclassical"
        confidence = "strong_token"
        confidence_score = 0.75
    elif hits["classical"]:
        lane = "classical"
        confidence = "token"
        confidence_score = 0.55
    else:
        lane = "unknown"
        confidence = "unknown"
        confidence_score = 0.0

    decision_hash = hashlib.sha256(
        json.dumps(
            {
                "stem": stem,
                "classifications": classifications,
                "explicit": explicit,
                "lane": lane,
                "lane_signals": hits,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    return {
        "sim_execution_lane": lane,
        "runner_execution_kind": runner_execution_kind_for(lane),
        "sim_execution_lane_confidence": confidence,
        "sim_execution_lane_confidence_score": confidence_score,
        "sim_execution_lane_source": "explicit" if explicit else "derived",
        "sim_execution_lane_conflict": hit_lane_count > 1 and not explicit,
        "lane_decision_hash": decision_hash,
        "lane_signals": hits,
        "lane_cautions": cautions,
    }


def detect_engine_types(stem: str, text: str, payloads: list[dict[str, Any]]) -> list[str]:
    haystack = " ".join([stem, module_docstring(text), *(payload_signal_text(payload) for payload in payloads)]).lower()
    engine_types: list[str] = []
    if token_hits(haystack, CARNOT_ENGINE_TOKENS):
        engine_types.append("carnot")
    if token_hits(haystack, SZILARD_ENGINE_CORE_TOKENS):
        engine_types.append("szilard")
    if token_hits(haystack, LANDAUER_ENGINE_TOKENS) and "szilard" not in engine_types:
        engine_types.append("landauer")
    return sorted(set(engine_types)) or ["none"]


def detect_engine_role_modes(stem: str, text: str, payloads: list[dict[str, Any]]) -> list[str]:
    haystack = " ".join([stem, module_docstring(text), *(payload_signal_text(payload) for payload in payloads)]).lower()
    modes: list[str] = []
    if token_hits(haystack, FULL_RUN_TOKENS):
        modes.append("full_run_signal")
    if token_hits(haystack, LANDAUER_ENGINE_TOKENS):
        modes.append("landauer_erasure_signal")
    if token_hits(haystack, BOUNDARY_ROLE_TOKENS):
        modes.append("boundary_to_nonclassical_signal")
    if token_hits(haystack, NEGATIVE_SPACE_TOKENS):
        modes.append("negative_space_or_graveyard_control")
    return modes or ["unspecified"]


def detect_engine_roles(
    stem: str,
    text: str,
    payloads: list[dict[str, Any]],
    lane: str,
    engine_types: list[str],
    engine_role_modes: list[str],
) -> list[str]:
    roles: list[str] = []
    if "carnot" in engine_types:
        roles.append("classical_carnot_engine_token_match")
    if "szilard" in engine_types or "landauer" in engine_types:
        roles.append("semiclassical_szilard_engine_token_match")
    if "negative_space_or_graveyard_control" in engine_role_modes:
        roles.append("negative_space_or_graveyard_control_signal")
    if lane == "nonclassical" or "boundary_to_nonclassical_signal" in engine_role_modes:
        roles.append("nonclassical_inspiration_or_boundary_signal")
    return roles or ["not_engine_related"]


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


def public_status_label_for(row: dict[str, Any]) -> str:
    # Inventory reads files only; it never executes a sim or proves local rerun.
    return "exists"


def public_status_blockers_for(row: dict[str, Any]) -> list[str]:
    blockers = ["inventory_only_no_execution", "fresh_local_rerun_not_performed", "canonical_process_not_evaluated"]
    if not row["result_paths"]:
        blockers.append("no_linked_result_json")
    if not row["admitted"]:
        blockers.append("wizard_admission_not_accepted")
    return blockers


def promotion_blockers_for(row: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if row.get("admission_status") == "no_admission":
        blockers.append("wizard_admission_missing")
    elif row.get("admission_status") != "admitted_evidence_linked":
        blockers.append(f"wizard_admission_{row.get('admission_status')}")
    if not row["result_paths"]:
        blockers.append("linked_result_missing")
    if not row["result_has_contract_shape"]:
        blockers.append("result_contract_shape_missing")
    if row["source_has_tool_manifest"] is False:
        blockers.append("source_tool_manifest_missing")
    if row["source_has_tool_integration_depth"] is False:
        blockers.append("source_tool_integration_depth_missing")
    if row["result_paths"] and not row["load_bearing_tools"]:
        blockers.append("load_bearing_tool_depth_missing")
    if row["late_stage_signal"] and not row["admitted"]:
        blockers.append("late_stage_signal_requires_gate_and_decomposition")
    if "classical_baseline" in row.get("result_classifications", []):
        blockers.append("classical_baseline_cannot_support_bridge_or_nonclassical_promotion")
    if "translation_lane" in row.get("result_classifications", []):
        blockers.append("translation_lane_should_be_sim_class_not_classification")
    if row.get("runner_execution_kind") in {"bridge", "nonclassical"} and "numpy" in row.get("load_bearing_tools", []):
        blockers.append("numpy_load_bearing_blocked_for_bridge_or_nonclassical")
    if row.get("runner_execution_kind") == "nonclassical" and "pytorch" not in row.get("load_bearing_tools", []):
        blockers.append("nonclassical_requires_load_bearing_pytorch")
    if row.get("sim_execution_lane_source") == "derived" and row.get("sim_execution_lane") == "unknown":
        blockers.append("execution_lane_metadata_missing_or_derived")
    if row.get("sim_execution_lane_conflict"):
        blockers.append("execution_lane_conflict_requires_manual_review")
    return sorted(set(blockers))


def garbage_candidate_flags_for(row: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if row["inventory_status"] == "source_only" and "graveyard_negative" in row["families"]:
        flags.append("source_only_negative_or_graveyard")
    if row["inventory_status"] == "legacy_result_or_repair_needed":
        flags.append("legacy_result_or_repair_needed")
    if row["late_stage_signal"] and not row["admitted"]:
        flags.append("late_stage_unadmitted")
    if row.get("sim_execution_lane_conflict"):
        flags.append("ambiguous_execution_lane")
    if "numpy_load_bearing_blocked_for_bridge_or_nonclassical" in row.get("promotion_blockers", []):
        flags.append("bridge_or_nonclassical_numpy_load_bearing")
    if "nonclassical_requires_load_bearing_pytorch" in row.get("promotion_blockers", []):
        flags.append("nonclassical_missing_load_bearing_pytorch")
    if "canonical" in row.get("result_classifications", []) and row.get("sim_execution_lane_source") == "derived":
        flags.append("canonical_result_not_execution_lane_evidence")
    if "graveyard_negative" in row["families"] and row.get("sim_execution_lane") == "semiclassical_bridge":
        flags.append("negative_probe_has_bridge_signal")
    return sorted(set(flags))


def cleanup_bucket_for(row: dict[str, Any]) -> str:
    if row["admitted"]:
        return "keep_admitted_receipt_linked"
    if row.get("admission_status") == "admission_missing_result_link":
        return "repair_admission_result_link"
    if row.get("admission_status") == "admission_missing_contract_shape":
        return "repair_admission_contract_shape"
    if row["inventory_status"] == "source_only":
        if "graveyard_negative" in row["families"]:
            return "source_only_negative_or_graveyard_manifest_before_archive_decision"
        return "source_only_rerun_or_archive_decision"
    if row["late_stage_signal"] and not row["admitted"]:
        return "late_stage_blocked_decompose_before_rerun"
    if row["inventory_status"] == "rerun_or_admission_candidate":
        return "rerun_or_admission_candidate_review"
    if row["inventory_status"] == "contract_shaped_but_tool_depth_thin":
        return "tool_depth_repair_before_admission"
    if row["inventory_status"] == "legacy_result_or_repair_needed":
        return "legacy_result_repair_or_quarantine"
    return "keep_indexed"


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


def sample_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row[key] for key in SAMPLE_ROW_KEYS if key in row}


def build_index(
    progress: bool = False,
    skip_bulk_a2_state_results: bool = False,
    include_rows: bool = True,
) -> dict[str, Any]:
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
        lane = detect_execution_lane(stem, text, payloads, classifications)
        engine_types = detect_engine_types(stem, text, payloads)
        engine_role_modes = detect_engine_role_modes(stem, text, payloads)
        engine_roles = detect_engine_roles(
            stem,
            text,
            payloads,
            lane["sim_execution_lane"],
            engine_types,
            engine_role_modes,
        )
        entry = admitted.get(stem)
        result_has_contract_shape = any(receipt_schema_present(payload) for payload in payloads)
        current_admission_status = admission_status(stem, entry, linked_results, result_has_contract_shape)
        row = {
            "stem": stem,
            "source_path": rel(path),
            "families": detect_families(stem, text),
            **lane,
            "engine_types": engine_types,
            "engine_role_modes": engine_role_modes,
            "engine_role_conflict": len([item for item in engine_types if item != "none"]) > 1,
            "engine_roles": engine_roles,
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
            "derived_inventory_signals_only": True,
        }
        row["has_contract_shape"] = bool(
            row["source_has_tool_manifest"]
            and row["source_has_tool_integration_depth"]
            and row["result_has_contract_shape"]
        )
        row["inventory_status"] = status_for(row)
        row["public_status_label"] = public_status_label_for(row)
        row["public_status_blockers"] = public_status_blockers_for(row)
        row["promotion_blockers"] = promotion_blockers_for(row)
        row["garbage_candidate_flags"] = garbage_candidate_flags_for(row)
        row["cleanup_bucket"] = cleanup_bucket_for(row)
        rows.append(row)

    family_counts = Counter(family for row in rows for family in row["families"])
    status_counts = Counter(row["inventory_status"] for row in rows)
    public_status_counts = Counter(row["public_status_label"] for row in rows)
    lane_counts = Counter(row["sim_execution_lane"] for row in rows)
    runner_kind_counts = Counter(row["runner_execution_kind"] for row in rows)
    promotion_blocker_counts = Counter(blocker for row in rows for blocker in row["promotion_blockers"])
    garbage_candidate_counts = Counter(flag for row in rows for flag in row["garbage_candidate_flags"])
    engine_type_counts = Counter(engine_type for row in rows for engine_type in row["engine_types"])
    engine_role_mode_counts = Counter(mode for row in rows for mode in row["engine_role_modes"])
    engine_role_counts = Counter(role for row in rows for role in row["engine_roles"])
    cleanup_bucket_counts = Counter(row["cleanup_bucket"] for row in rows)
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
    garbage_candidates = [row for row in rows if row["garbage_candidate_flags"]]
    source_only = [row for row in rows if row["inventory_status"] == "source_only"]
    linked_results = linked_result_path_set(rows)
    unlinked_results = [path for path in results if rel(path) not in linked_results]
    index = {
        "schema": "sim_inventory_index.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": "inventory_only_not_admission_or_promotion",
        "row_detail_policy": {
            "full_rows_included": include_rows,
            "full_row_count": len(rows),
            "tracked_default": "summary_and_samples_only",
            "full_rows_command_flag": "--include-rows",
        },
        "summary": {
            "source_count": len(rows),
            "result_json_count": len(results),
            "skipped_bulk_a2_state_result_count": skipped_bulk_a2_state_result_count,
            "linked_result_json_count": len(linked_results),
            "unlinked_result_json_count": len(unlinked_results),
            "admitted_count": len(admitted_rows),
            "admission_repair_count": len(admission_repair_rows),
            "status_counts": dict(status_counts),
            "public_status_counts": dict(public_status_counts),
            "sim_execution_lane_counts": dict(lane_counts),
            "runner_execution_kind_counts": dict(runner_kind_counts),
            "engine_type_counts": dict(engine_type_counts),
            "engine_role_mode_counts": dict(engine_role_mode_counts),
            "engine_role_counts": dict(engine_role_counts),
            "cleanup_bucket_counts": dict(cleanup_bucket_counts),
            "promotion_blocker_counts": dict(promotion_blocker_counts),
            "garbage_candidate_counts": dict(garbage_candidate_counts),
            "family_counts": dict(family_counts),
            "tool_signal_counts": dict(tool_counts),
            "load_bearing_tool_counts": dict(load_bearing_counts),
            "result_classification_counts": dict(result_class_counts),
            "repair_candidate_count": len(repair_candidates),
            "garbage_candidate_count": len(garbage_candidates),
            "source_only_count": len(source_only),
        },
        "admitted_stems": sorted(row["stem"] for row in admitted_rows),
        "admission_repair_samples": [sample_row(row) for row in admission_repair_rows[:100]],
        "unlinked_result_samples": [rel(path) for path in unlinked_results[:100]],
        "repair_candidate_samples": [sample_row(row) for row in repair_candidates[:100]],
        "garbage_candidate_samples": [sample_row(row) for row in garbage_candidates[:100]],
        "cleanup_bucket_samples": {
            bucket: [sample_row(row) for row in rows if row["cleanup_bucket"] == bucket][:25]
            for bucket in sorted(cleanup_bucket_counts)
        },
        "source_only_samples": [sample_row(row) for row in source_only[:100]],
    }
    if include_rows:
        index["rows"] = rows
    return index


def write_markdown(index: dict[str, Any], path: Path) -> None:
    summary = index["summary"]
    lines = [
        "# Sim Inventory Index",
        "",
        f"Generated: `{index['generated_at']}`",
        "",
        "Boundary: inventory only. This does not admit, promote, or validate a sim.",
        "",
        "Tracked JSON keeps summary and samples by default; run with `--include-rows` for local full-row audits.",
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
        "## Public Status Counts",
        "",
        "Inventory only proves `exists`; it does not execute sims or promote results.",
        "",
    ]
    for key, value in sorted(summary["public_status_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## Sim Execution Lane Counts",
        "",
    ]
    for key, value in sorted(summary["sim_execution_lane_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## Runner Execution Kind Counts",
        "",
        "These use the repo runner contract vocabulary while detailed lane labels remain inventory-only signals.",
        "",
    ]
    for key, value in sorted(summary["runner_execution_kind_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Engine Type Counts", ""]
    for key, value in sorted(summary["engine_type_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Engine Role Mode Counts", ""]
    for key, value in sorted(summary["engine_role_mode_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Engine Role Counts", ""]
    for key, value in sorted(summary["engine_role_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Cleanup Bucket Counts", ""]
    for key, value in sorted(summary["cleanup_bucket_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Promotion Blocker Counts", ""]
    for key, value in sorted(summary["promotion_blocker_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Garbage Candidate Flag Counts", ""]
    for key, value in sorted(summary["garbage_candidate_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines += [
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
    lines += [
        "",
        "## First Garbage Candidate Flags",
        "",
        "| flags | stem | lane | cleanup bucket | blockers |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in index.get("garbage_candidate_samples", [])[:50]:
        lines.append(
            "| {flags} | `{stem}` | `{lane}` | `{bucket}` | {blockers} |".format(
                flags=", ".join(row["garbage_candidate_flags"]),
                stem=row["stem"],
                lane=row["sim_execution_lane"],
                bucket=row["cleanup_bucket"],
                blockers=", ".join(row["promotion_blockers"][:4]) or "-",
            )
        )
    lines += [
        "",
        "## First Cleanup Buckets",
        "",
        "| bucket | stem | lane | engine types | role modes | public status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    cleanup_rows: list[dict[str, Any]] = []
    for bucket_rows in (index.get("cleanup_bucket_samples") or {}).values():
        cleanup_rows.extend(bucket_rows[:3])
    for row in cleanup_rows[:75]:
        lines.append(
            "| {bucket} | `{stem}` | `{lane}` | {engine_types} | {role_modes} | `{status}` |".format(
                bucket=row["cleanup_bucket"],
                stem=row["stem"],
                lane=row["sim_execution_lane"],
                engine_types=", ".join(row["engine_types"]),
                role_modes=", ".join(row["engine_role_modes"]),
                status=row["public_status_label"],
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
    parser.add_argument(
        "--include-rows",
        action="store_true",
        help="Include every indexed row in the JSON output. The tracked default is summary and samples only.",
    )
    args = parser.parse_args()
    index = build_index(
        progress=args.progress,
        skip_bulk_a2_state_results=args.skip_bulk_a2_state_results,
        include_rows=args.include_rows,
    )
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

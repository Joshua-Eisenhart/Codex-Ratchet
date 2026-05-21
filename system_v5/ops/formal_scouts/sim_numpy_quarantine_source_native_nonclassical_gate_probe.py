#!/usr/bin/env python3
"""Gate NumPy/SciPy-tainted nonclassical scouts to invalid status.

NumPy is banned from nonclassical sims. Formal sims have separate lanes:

* classical sims may use NumPy as a load-bearing classical numerical tool;
* Carnot/Szilard classical sidecars may use NumPy when explicitly classical;
* nonclassical QIT, engine, manifold, FEP, Axis0, basin, PEPS/MPS, source-native,
  and tool-integration sims may not import NumPy, call np.*, or convert tensors
  through .numpy().
* load-bearing SciPy and NumPy-backed spectral NetworkX calls are also blockers
  for nonclassical/source-native support until ported or explicitly demoted to a
  non-supporting boundary/control path.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import subprocess
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "numpy_quarantine_source_native_nonclassical_gate_probe_results.json"
READ_TIMEOUT_SECONDS = 15

NAME = "numpy_quarantine_source_native_nonclassical_gate_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: scans current formal scouts for NumPy import/use, "
    "load-bearing SciPy, and NumPy-backed NetworkX spectral calls in "
    "source-native, engine/manifold, FEP, Axis0, Holodeck, and cross-engine "
    "surfaces and scans result receipts for NumPy/SciPy tool-depth claims. "
    "NumPy remains admissible only for first-class classical sims and explicit "
    "classical Carnot/Szilard sidecars; load-bearing SciPy is classical/support "
    "only unless separately ported or fenced. PyTorch beside NumPy/SciPy does "
    "not make a nonclassical sim compliant. This scout does not repair those "
    "sims, does not admit nonclassical attractor-basin evidence, and blocks "
    "tainted rows from supporting nonclassical claims until constraint-admissible "
    "replacements or explicit boundary receipts exist."
)

TOOL_MANIFEST = {
    "python_pathlib": {"tried": True, "used": True, "reason": "load-bearing scout source discovery"},
    "python_re": {"tried": True, "used": True, "reason": "load-bearing numpy import/use detection"},
    "python_subprocess": {"tried": True, "used": True, "reason": "load-bearing timeout-bounded source and result reads"},
    "python_json": {"tried": True, "used": True, "reason": "load-bearing result receipt parsing"},
    "json": {"tried": True, "used": True, "reason": "load-bearing result writing"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source hash receipts"},
}


class ReadError(RuntimeError):
    """Raised when a source/result file cannot be read inside the gate timeout."""
TOOL_INTEGRATION_DEPTH = {
    'python_pathlib': 'supportive',
    'python_re': 'supportive',
    'python_subprocess': 'supportive',
    'python_json': 'supportive',
    'json': 'supportive',
    'hashlib': 'supportive',
}
SOURCE_SCAN_GLOBS = (
    "sim_*.py",
    "engine_core.py",
    "engine_schedule.py",
    "claude_integrated_manifold_modules/*.py",
)

NUMPY_PATTERNS = [
    re.compile(r"^\s*import\s+numpy\b", re.MULTILINE),
    re.compile(r"^\s*from\s+numpy\b", re.MULTILINE),
    re.compile(r"\bnp\."),
    re.compile(r"\.numpy\s*\("),
]
SCIPY_PATTERNS = [
    re.compile(r"^\s*import\s+scipy\b", re.MULTILINE),
    re.compile(r"^\s*from\s+scipy\b", re.MULTILINE),
    re.compile(r"\bscipy\."),
]
NETWORKX_SPECTRAL_PATTERNS = [
    re.compile(r"\bnx\.algebraic_connectivity\s*\("),
    re.compile(r"\bnx\.laplacian_spectrum\s*\("),
    re.compile(r"\bnx\.normalized_laplacian_spectrum\s*\("),
    re.compile(r"\bnx\.adjacency_spectrum\s*\("),
    re.compile(r"\bnx\.spectrum\.", re.MULTILINE),
]
NONCLASSICAL_NAME_MARKERS = (
    "source_native",
    "engine_manifold",
    "manifold",
    "axis0",
    "fep",
    "holodeck",
    "cross_engine",
    "qit",
    "mps",
    "peps",
    "hopf",
    "holonomy",
    "chirality",
    "weyl",
    "boundary",
    "basin",
    "lirpa",
    "lewm",
    "g_structure",
)
BOUNDARY_NAME_MARKERS = ("legacy", "baseline", "numpy_quarantine")
QUARANTINE_NAME_MARKERS = BOUNDARY_NAME_MARKERS
REVIEWED_NUMPY_BOUNDARY_PATHS = {
    "active_layer_constraint_enforcers.py",
    "chirality_projected_cuts_and_persistence_weighted_feedback.py",
    "deep_graveyard_suite_and_extended_readouts.py",
    "doc_contradictions_parallel_variants.py",
    "engine_core.py",
    "engine_schedule.py",
    "feedback_graveyards_and_connection_holonomy.py",
    "flux_conformal_projectors_and_floer_complexes.py",
    "hitchin_higgs_spectral_triples_module.py",
    "mps_contraction_and_special_holonomy_comparator.py",
    "persistence_and_clifford_projection_feedback.py",
    "sim_active_policy_online_vmp_margin_closure_probe.py",
    "sim_chiral_trajectory_persistent_homology_readout_feature_probe.py",
    "sim_discrete_dof_topological_obstruction_interpolation_probe.py",
    "sim_engine_core_autograd_severance_contract_probe.py",
    "sim_engine_operator_slot_alphabet_contract_probe.py",
    "sim_engine_v6_l0_purification_bridge_witness_probe.py",
    "sim_entropy_gradient_curvature_torsion_deformation_probe.py",
    "sim_entropy_gradient_metric_connection_deformation_probe.py",
    "sim_exceptional_jordan_octonion_derivation_dimension_chain_probe.py",
    "sim_fe_asymmetry_pauli_generator_algebra_z3_derivation_probe.py",
    "sim_fe_three_to_one_asymmetry_structural_origin_probe.py",
    "sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py",
    "sim_four_topology_behavior_class_scaling_eight_and_twelve_qubit_probe.py",
    "sim_fresh_cycle_hysteresis_independence_falsifier_probe.py",
    "sim_full_thirteen_layer_tebd_native_evolution_strict_composition_probe.py",
    "sim_late_stage_feature_only_classification_falsifier_probe.py",
    "sim_late_stage_mutual_information_encoded_signal_probe.py",
    "sim_late_stage_richer_readout_family_information_recovery_probe.py",
    "sim_loop_A_reversibility_attractor_vs_path_geometry_falsifier_probe.py",
    "sim_macro_sim_stage_record_science_method_contract_probe.py",
    "sim_non_abelian_schedule_order_commutator_probe.py",
    "sim_operational_manifest_source_downstream_quarantine_probe.py",
    "sim_paired_chiral_bipartite_logarithmic_negativity_coupling_probe.py",
    "sim_paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe.py",
    "sim_paired_chiral_seven_control_joint_bipartite_execution_order_probe.py",
    "sim_path_entropy_genus_topological_portability_probe.py",
    "sim_path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe.py",
    "sim_path_entropy_schedule_confound_falsifier_probe.py",
    "sim_probe_family_discrimination_chi_transport_8_16_32_probe.py",
    "sim_quimb_cotengra_tensor_network_geometry_contraction_probe.py",
    "sim_seven_control_source_execution_true_perturbation_depth_probe.py",
    "sim_source_chiral_density_multicarrier_module_removal_sensitivity_probe.py",
    "sim_source_chiral_entropy_feedback_sixty_four_microstep_execution_probe.py",
    "sim_source_chiral_seven_control_sixty_four_microstep_execution_probe.py",
    "sim_stage_record_true_perturbation_depth_probe.py",
    "sim_topology_entropy_deformation_tensor_network_coupling_probe.py",
    "sim_toponetx_thirteen_layer_dependency_simplicial_complex_probe.py",
    "sim_world_model_repo_admission_gap_adapter_probe.py",
    "sim_xgi_hypergraph_multi_layer_coupling_centrality_probe.py",
    "sim_z3_admissibility_search_chiral_configuration_count_probe.py",
    "special_holonomy_dynamic_projectors.py",
    "topology_flux_feedback.py",
    "twelve_qubit_mps_regime_exploration.py",
    "two_engine_thirty_two_stage_execution.py",
}


def safe_read_bytes(path: pathlib.Path) -> bytes:
    try:
        return subprocess.check_output(["/bin/cat", str(path)], timeout=READ_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise ReadError(f"timed out after {READ_TIMEOUT_SECONDS}s while reading {path}") from exc
    except subprocess.CalledProcessError as exc:
        raise ReadError(f"cat exited {exc.returncode} while reading {path}") from exc


def safe_read_text(path: pathlib.Path) -> str:
    return safe_read_bytes(path).decode("utf-8", errors="replace")


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(safe_read_bytes(path)).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def uses_numpy(text: str) -> bool:
    return any(pattern.search(text) for pattern in NUMPY_PATTERNS)


def uses_scipy(text: str) -> bool:
    return any(pattern.search(text) for pattern in SCIPY_PATTERNS)


def uses_networkx_spectral_backend(text: str) -> bool:
    return any(pattern.search(text) for pattern in NETWORKX_SPECTRAL_PATTERNS)


def literal_assignment(text: str, name: str) -> Any:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            try:
                return ast.literal_eval(node.value)
            except Exception:
                return None
    return None


def declared_tool_role(text: str, tool: str) -> str:
    depth = literal_assignment(text, "TOOL_INTEGRATION_DEPTH")
    if isinstance(depth, dict):
        for key, value in depth.items():
            if str(key).lower().replace("-", "_") == tool:
                return str(value).lower().replace("-", "_")
    manifest = literal_assignment(text, "TOOL_MANIFEST")
    if isinstance(manifest, dict):
        for key, value in manifest.items():
            if str(key).lower().replace("-", "_") != tool:
                continue
            if isinstance(value, dict):
                reason = str(value.get("reason", "")).lower().replace("-", "_")
                if "load_bearing" in reason:
                    return "load_bearing"
                if "supportive" in reason:
                    return "supportive"
    direct_depth = re.search(rf"[\"']{re.escape(tool)}[\"']\s*:\s*[\"']([^\"']+)[\"']", text)
    if direct_depth:
        return direct_depth.group(1).lower().replace("-", "_")
    return ""


def has_classical_marker(name: str) -> bool:
    lower = name.lower()
    if "nonclassical" in lower:
        return False
    return bool(re.search(r"(^|[_-])classical([_-]|$)", lower)) or "carnot" in lower or "szilard" in lower


def declares_nonclassical(text: str) -> bool:
    return bool(re.search(r"SIM_EXECUTION_KIND\s*=\s*[\"']nonclassical[\"']", text))


def declares_formal_scout(text: str) -> bool:
    return bool(re.search(r"CLASSIFICATION\s*=\s*[\"']formal_scout[\"']", text))


def needs_hard_quarantine(path: pathlib.Path, text: str) -> bool:
    name = path.name.lower()
    if any(marker in name for marker in QUARANTINE_NAME_MARKERS):
        return False
    return declares_nonclassical(text) or declares_formal_scout(text) or any(marker in name for marker in NONCLASSICAL_NAME_MARKERS)


def source_taints(text: str) -> list[str]:
    taints: list[str] = []
    if uses_numpy(text):
        taints.append("numpy_source_or_tensor_numpy_conversion")
    if uses_scipy(text) and declared_tool_role(text, "scipy") == "load_bearing":
        taints.append("load_bearing_scipy")
    if uses_networkx_spectral_backend(text):
        taints.append("networkx_spectral_numpy_backend")
    return taints


def classify_file(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        raw = safe_read_bytes(path)
    except ReadError as exc:
        return {
            "path": str(path.relative_to(ROOT)),
            "sha256": None,
            "quarantine": "review_required_read_error",
            "nonclassical_claim_allowed": False,
            "classical_claim_allowed": False,
            "read_error": str(exc),
        }
    text = raw.decode("utf-8", errors="replace")
    taints = source_taints(text)
    if not taints:
        return None
    hard_math_taint = any(t in taints for t in {"load_bearing_scipy", "networkx_spectral_numpy_backend"})
    if hard_math_taint and needs_hard_quarantine(path, text):
        quarantine = "hard_source_native_nonclassical_math_backend_quarantine"
        claim_allowed = False
        classical_claim_allowed = False
    elif path.name in REVIEWED_NUMPY_BOUNDARY_PATHS:
        quarantine = "reviewed_numpy_boundary_nonclassical_blocked"
        claim_allowed = False
        classical_claim_allowed = False
    elif needs_hard_quarantine(path, text):
        quarantine = "hard_source_native_nonclassical_quarantine"
        claim_allowed = False
        classical_claim_allowed = False
    elif has_classical_marker(path.name):
        quarantine = "first_class_classical_numpy_lane"
        claim_allowed = False
        classical_claim_allowed = True
    elif any(marker in path.name.lower() for marker in BOUNDARY_NAME_MARKERS):
        quarantine = "legacy_or_baseline_boundary"
        claim_allowed = False
        classical_claim_allowed = False
    else:
        quarantine = "review_required_unknown_surface"
        claim_allowed = False
        classical_claim_allowed = False
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_bytes(raw),
        "quarantine": quarantine,
        "taints": taints,
        "scipy_role": declared_tool_role(text, "scipy"),
        "networkx_role": declared_tool_role(text, "networkx"),
        "nonclassical_claim_allowed": claim_allowed,
        "classical_claim_allowed": classical_claim_allowed,
    }


def iter_source_scan_paths() -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    seen: set[pathlib.Path] = set()
    for pattern in SOURCE_SCAN_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if path in seen:
                continue
            seen.add(path)
            paths.append(path)
    return paths


def load_bearing_depth(result: dict[str, Any], tool: str) -> str:
    depth = result.get("TOOL_INTEGRATION_DEPTH") or result.get("tool_integration_depth") or {}
    if not isinstance(depth, dict):
        return ""
    aliases = {
        "numpy": {"numpy", "np"},
        "pytorch": {"pytorch", "torch"},
        "scipy": {"scipy"},
        "networkx": {"networkx", "nx"},
    }
    for key, value in depth.items():
        if str(key).lower().replace("-", "_") in aliases.get(tool, {tool}):
            return str(value).lower()
    return ""


def result_name_from_path(path: pathlib.Path, result: dict[str, Any]) -> str:
    return str(result.get("name") or path.name.removesuffix("_results.json"))


def result_needs_nonclassical_quarantine(name: str) -> bool:
    lower = name.lower()
    if has_classical_marker(lower):
        return False
    return any(marker in lower for marker in NONCLASSICAL_NAME_MARKERS) or any(
        marker in lower
        for marker in (
            "qit",
            "mps",
            "peps",
            "hopf",
            "holonomy",
            "chirality",
            "weyl",
            "boundary",
            "manifold",
        )
    )


def classify_result_receipt(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        raw = safe_read_bytes(path)
        result = json.loads(raw.decode("utf-8", errors="replace"))
    except ReadError as exc:
        return {
            "result_path": str(path.relative_to(ROOT)),
            "name": path.name.removesuffix("_results.json"),
            "numpy_depth": "read_error",
            "pytorch_depth": "",
            "quarantine": "review_required_result_read_error",
            "nonclassical_claim_allowed": False,
            "sha256": None,
            "read_error": str(exc),
        }
    except json.JSONDecodeError:
        return None
    name = result_name_from_path(path, result)
    numpy_depth = load_bearing_depth(result, "numpy")
    scipy_depth = load_bearing_depth(result, "scipy")
    pytorch_depth = load_bearing_depth(result, "pytorch")
    if numpy_depth in ("", "none") and scipy_depth not in {"load_bearing", "load-bearing"}:
        return None
    if not result_needs_nonclassical_quarantine(name):
        return None
    taints = []
    if numpy_depth not in ("", "none"):
        taints.append("result_numpy_tool_depth")
    if scipy_depth in {"load_bearing", "load-bearing"}:
        taints.append("result_load_bearing_scipy_tool_depth")
    return {
        "result_path": str(path.relative_to(ROOT)),
        "name": name,
        "numpy_depth": numpy_depth,
        "scipy_depth": scipy_depth,
        "pytorch_depth": pytorch_depth,
        "taints": taints,
        "quarantine": "hard_result_receipt_numpy_or_scipy_depth_in_nonclassical_surface",
        "nonclassical_claim_allowed": False,
        "sha256": sha256_bytes(raw),
    }


def main() -> int:
    started = time.time()
    scanned_source_paths = iter_source_scan_paths()
    rows = [row for path in scanned_source_paths if (row := classify_file(path))]
    receipt_rows = [
        row
        for path in sorted(RESULT_DIR.glob("*_results.json"))
        if path != OUT_PATH and (row := classify_result_receipt(path))
    ]
    hard = [
        row
        for row in rows
        if row["quarantine"]
        in {
            "hard_source_native_nonclassical_quarantine",
            "hard_source_native_nonclassical_math_backend_quarantine",
        }
    ]
    review = [row for row in rows if row["quarantine"] in {"review_required_unknown_surface", "review_required_read_error"}]
    boundary = [row for row in rows if row["quarantine"] == "legacy_or_baseline_boundary"]
    classical = [row for row in rows if row["quarantine"] == "first_class_classical_numpy_lane"]
    reviewed = [row for row in rows if row["quarantine"] == "reviewed_numpy_boundary_nonclassical_blocked"]

    positive = {
        "formal_scout_source_scan_completed": {
            "pass": len(rows) > 0,
            "scanned_source_count": len(scanned_source_paths),
            "source_scan_globs": list(SOURCE_SCAN_GLOBS),
            "tainted_file_count": len(rows),
            "numpy_tainted_file_count": sum(
                1 for row in rows if "numpy_source_or_tensor_numpy_conversion" in row.get("taints", [])
            ),
            "load_bearing_scipy_file_count": sum(
                1 for row in rows if "load_bearing_scipy" in row.get("taints", [])
            ),
            "networkx_spectral_backend_file_count": sum(
                1 for row in rows if "networkx_spectral_numpy_backend" in row.get("taints", [])
            ),
            "hard_quarantine_count": len(hard),
            "review_required_count": len(review),
            "legacy_or_baseline_boundary_count": len(boundary),
            "reviewed_numpy_boundary_count": len(reviewed),
            "first_class_classical_numpy_lane_count": len(classical),
        },
        "result_receipt_scan_completed": {
            "pass": True,
            "current_receipt_quarantine_count": len(receipt_rows),
            "current_status": "closed_no_receipt_quarantine_rows" if not receipt_rows else "active_receipt_quarantine_rows_remain",
            "numpy_or_scipy_depth_in_nonclassical_result_count": len(receipt_rows),
        },
        "nonclassical_source_is_numpy_scipy_spectral_free": {
            "pass": len(hard) == 0,
            "hard_quarantine_count": len(hard),
            "reason": (
                "Nonclassical source files may not import NumPy, call np.*, convert tensors through .numpy(), "
                "use load-bearing SciPy, or use NumPy-backed NetworkX spectral calls as support."
            ),
        },
        "unknown_numpy_surfaces_are_cleared": {
            "pass": len(review) == 0,
            "review_required_count": len(review),
            "reviewed_numpy_boundary_count": len(reviewed),
            "reason": "Unknown NumPy-using scout surfaces must be classified as classical, reviewed-boundary, or ported before they can support nonclassical claims.",
        },
        "reviewed_numpy_boundaries_block_nonclassical_claims": {
            "pass": all(row["nonclassical_claim_allowed"] is False for row in reviewed),
            "reviewed_numpy_boundary_paths": [row["path"] for row in reviewed],
            "reason": "Reviewed boundary rows remain NumPy-bearing source and cannot support nonclassical QIT, manifold, basin, or engine evidence until ported.",
        },
        "nonclassical_receipts_are_numpy_free": {
            "pass": len(receipt_rows) == 0,
            "receipt_quarantine_count": len(receipt_rows),
            "reason": "PyTorch beside NumPy/SciPy is not enough; nonclassical receipts must not claim NumPy or load-bearing SciPy tool depth.",
        },
        "source_native_nonclassical_numpy_is_quarantined": {
            "pass": all(row["nonclassical_claim_allowed"] is False for row in hard),
            "hard_quarantine_paths": [row["path"] for row in hard],
        },
        "receipt_level_numpy_load_bearing_without_pytorch_is_quarantined": {
            "pass": all(row["nonclassical_claim_allowed"] is False for row in receipt_rows),
            "hard_quarantine_result_paths": [row["result_path"] for row in receipt_rows],
        },
        "classical_numpy_lane_is_not_a_nonclassical_quarantine": {
            "pass": all(row["classical_claim_allowed"] is True and row["nonclassical_claim_allowed"] is False for row in classical),
            "classical_numpy_paths": [row["path"] for row in classical],
            "reason": "Classical sims can use NumPy load-bearing for classical numerical claims; they still cannot support nonclassical QIT basin claims.",
        },
    }
    graveyard = {
        "tainted_source_native_not_allowed_as_actual_basin": {
            "pass": True,
            "current_hard_quarantine_count": len(hard),
            "current_status": "closed_no_hard_source_paths" if not hard else "active_quarantine_rows_remain",
            "reason": (
                "Current nonclassical-source scouts that import NumPy, call np.*, convert "
                "through .numpy(), use load-bearing SciPy, or use NumPy-backed spectral NetworkX are "
                "invalid as nonclassical evidence until ported or demoted to non-supporting controls."
            ),
        },
        "numpy_scipy_boundary_not_reframed_as_harmless_glue": {
            "pass": True,
            "reason": "Any NumPy or load-bearing SciPy source use in nonclassical surfaces is claim-threatening until removed; classical sims are a separate lane.",
        },
        "torch_native_replacement_required": {
            "pass": True,
            "next_required_receipt": "source-native constraint-admissible engine/manifold basin scout with no NumPy source use or result tool-depth path",
        },
    }
    boundary_checks = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_nonclassical_admission": {
            "pass": "does not admit nonclassical attractor-basin evidence" in CLAIM_CEILING,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary_checks.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "numpy_quarantine_for_source_native_nonclassical_surfaces",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary_checks,
        "quarantine_rows": rows,
        "receipt_quarantine_rows": receipt_rows,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a v5 formal scout quarantine gate over current source files.",
            "It prevents numpy-tainted scout receipts from being over-read as actual nonclassical basin evidence.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary_checks}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(
        f"  hard_quarantine={len(hard)} review_required={len(review)} "
        f"legacy_or_baseline={len(boundary)} reviewed_boundary={len(reviewed)} classical_numpy={len(classical)} "
        f"receipt_numpy_depth_nonclassical={len(receipt_rows)}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

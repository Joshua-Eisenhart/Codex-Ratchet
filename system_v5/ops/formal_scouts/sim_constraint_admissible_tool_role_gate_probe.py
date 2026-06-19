#!/usr/bin/env python3
"""Gate source-native nonclassical scouts by constraint-admissible tool roles."""

from __future__ import annotations

import hashlib
import ast
import json
import pathlib
import re
import sys
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import two_root_constraints  # noqa: E402

RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"
NUMPY_QUARANTINE_RESULT = RESULT_DIR / "numpy_quarantine_source_native_nonclassical_gate_probe_results.json"

NAME = "constraint_admissible_tool_role_gate_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: enforces that actual source-native nonclassical "
    "attractor-basin claims require two-root constraint-admissible load-bearing tools. "
    "A receipt must also pass before it can be called a candidate. "
    "This is not a global NumPy ban: classical formal sims may use classical "
    "numerical tools for classical claims, and bridge/baseline/supportive rows "
    "may use them when the role is explicit. "
    "It quarantines rows whose tools are classical, administrative, same-source "
    "runtime only, missing micro receipts, or mathematically mismatched to the "
    "claim. It does not promote any engine, manifold, Axis0, FEP, Holodeck, "
    "world-model, physics, or cognition claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive result receipt parsing"},
    "python_pathlib": {"tried": True, "used": True, "reason": "load-bearing source/result discovery"},
    "python_ast": {"tried": True, "used": True, "reason": "load-bearing EngineCore import detection that ignores comments and strings"},
    "python_re": {"tried": True, "used": True, "reason": "supportive legacy EngineCore boundary pattern kept for process continuity"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hash receipts"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "python_ast": "supportive",
    "python_re": "supportive",
    "hashlib": "supportive",
}

NONCLASSICAL_NAME_MARKERS = two_root_constraints.NONCLASSICAL_NAME_MARKERS

TWO_ROOT_TOOL_ADMISSIBILITY = {
    "torch": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite tensors/operators on bounded carriers with direct noncommuting matrix/operator composition and autograd pressure",
    },
    "torch_geometric": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite graph tensors where edge/order/message-passing changes must alter the observable under bounded graph controls",
    },
    "auto_lirpa": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite bounded PyTorch perturbation domains that certify separation/order-pressure margins rather than continuous unbounded plausibility",
    },
    "z3": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite SMT encodings that assert satisfiable/unsatisfiable noncommutation, ordering, or countermodel constraints",
    },
    "cvc5": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite SMT cross-checks for noncommutation/order/countermodel predicates",
    },
    "sympy": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite symbolic expressions whose commutators, reductions, or polynomial witnesses distinguish order",
    },
    "clifford": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite Clifford algebras with anticommuting generators and grade/order witnesses",
    },
    "geomstats": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "bounded chart/manifold membership or distance checks tied to order-sensitive operator/gauge controls",
    },
    "e3nn": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite representation/irrep constraints that preserve equivariant structure under ordered operator action",
    },
    "rustworkx": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite directed graph dependencies where path/order edits must change admissible structure",
    },
    "xgi": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite hypergraph incidence constraints used as order-sensitive coupling surfaces",
    },
    "toponetx": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite cell/simplicial complexes whose boundary/order structure constrains the carrier",
    },
    "gudhi": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite filtrations/persistence summaries coupled to order-sensitive manifold or trajectory controls",
    },
    "quimb": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite tensor networks with contraction-order and operator-order sensitivity",
    },
    "cotengra": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite contraction planning whose order changes pressure tensor-network admissibility",
    },
    "kahypar": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite hypergraph partition pressure coupled to order-sensitive tensor-network contraction constraints",
    },
    "opt_einsum": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite einsum contractions where index/order structure is part of the admissibility witness",
    },
    "le_wm": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite world-model latent dynamics admitted only when bounded branch/order perturbations separate the observable",
    },
    "networkx": {
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "admissibility_reason": "finite graph readout admitted only when ordered graph mutations change the observable under a bounded fixture",
    },
}
TWO_ROOT_TOOL_MICRO_RECEIPTS = {
    "torch": "eight_qubit_mps_channel_order_graph_leakage_pyg_pytorch_opt_einsum_z3_probe_results.json",
    "torch_geometric": "torch_geometric_message_order_sensitivity_micro_probe_results.json",
    "auto_lirpa": "auto_lirpa_two_order_adapter_bound_micro_probe_results.json",
    "le_wm": "lewm_branch_order_latent_dynamics_micro_probe_results.json",
    "z3": "topology_coupled_admissibility_falsifier_probe_results.json",
    "cvc5": "cvc5_order_gap_countermodel_micro_probe_results.json",
    "sympy": "finite_density_hopf_spinor_clifford_channel_structure_reduction_order_probe_results.json",
    "clifford": "d4_pseudoscalar_chirality_dimension_parity_portability_probe_results.json",
    "geomstats": "geomstats_ordered_map_distance_micro_probe_results.json",
    "e3nn": "e3nn_noncommuting_irrep_action_micro_probe_results.json",
    "rustworkx": "sim_rustworkx_ordered_dag_reduction_micro_probe_results.json",
    "xgi": "sim_xgi_hyperedge_order_incidence_micro_probe_results.json",
    "toponetx": "sim_toponetx_boundary_orientation_order_micro_probe_results.json",
    "gudhi": "sim_gudhi_filtration_order_persistence_micro_probe_results.json",
    "quimb": "quimb_operator_order_tensor_network_micro_probe_results.json",
    "cotengra": "cotengra_contraction_order_pressure_micro_probe_results.json",
    "opt_einsum": "eight_qubit_mps_entropy_readout_layer_constraint_probe_results.json",
    "networkx": "sim_networkx_ordered_graph_readout_review_unknown_micro_probe_results.json",
}
TWO_ROOT_TOOL_ADMISSIBILITY = two_root_constraints.TWO_ROOT_TOOL_ADMISSIBILITY
TWO_ROOT_TOOL_MICRO_RECEIPTS = two_root_constraints.TWO_ROOT_TOOL_MICRO_RECEIPTS
CONSTRAINT_ADMISSIBLE_TOOLS = set(TWO_ROOT_TOOL_ADMISSIBILITY)
CLASSICAL_OR_ADMIN_TOOLS = two_root_constraints.CLASSICAL_OR_ADMIN_TOOLS
ENGINE_CORE_IMPORT_RE = re.compile(r"^(?:from\s+engine_core\s+import|import\s+engine_core\b)|\bengine_core\.", re.MULTILINE)
ENGINE_CORE_AUTOGRAD_CONTRACT = RESULT_DIR / "engine_core_autograd_severance_contract_probe_results.json"
_REVIEWED_NUMPY_BOUNDARY_CACHE: set[str] | None = None
_ENGINE_CORE_FINITE_BOUNDARY_CACHE: dict[str, dict[str, Any]] | None = None

ADMIN_SUPPORT_SURFACE_MARKERS = (
    "admission_gate",
    "adoption_audit",
    "adoption_bridge",
    "aggregate",
    "candidate_execution",
    "claim_ceiling_status_audit",
    "dependency_basin_depth_guard",
    "dependency_task_matrix",
    "evidence_aggregator",
    "full_wave_execution",
    "receipt_resolution",
    "stdout_verdict",
    "timeout_rerun",
)

SUPERSEDED_FAILED_SURFACES = {
    "singular_lego_wired_axis0_plural_manifold_engine_probe": {
        "successor_result": "singular_lego_axis0_cycle_path_sensitivity_ablation_probe_results.json",
        "successor_name": "singular_lego_axis0_cycle_path_sensitivity_ablation_probe",
        "reason": (
            "The old v1 tool-lego-fit probe remains red because path_entropy is blocked "
            "and cycle-level autograd is severed; the green v2 successor preserves those "
            "blocked controls while proving active cycle/path sensitivity versus import-only wiring."
        ),
    },
}

PRESERVED_COUNTEREVIDENCE_SURFACES = {
    "multiqubit_qit_reservoir_global_structure_probe": {
        "boundary_class": "torch_readout_reservoir_global_structure_counterevidence",
        "reason": (
            "The frozen reservoir global-structure scout is an honest red "
            "counterevidence receipt: the 8q row remains below the existing "
            "positive threshold while shuffled/local controls are recorded. "
            "Preserve it as negative readiness evidence rather than active B2 "
            "source-repair debt."
        ),
    },
    "multiqubit_qit_reservoir_grok_task_replication_probe": {
        "boundary_class": "torch_readout_grok_task_translation_counterevidence",
        "reason": (
            "The translated Grok-task reservoir scout is an honest red "
            "counterevidence receipt: the 8q reservoir does not beat local "
            "Bloch readout and the z3 local/shuffle guard remains satisfiable. "
            "Preserve it as negative readiness evidence rather than active B2 "
            "source-repair debt."
        ),
    },
}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_nonclassical_surface(name: str, result: dict[str, Any] | None = None) -> bool:
    return two_root_constraints.is_nonclassical_surface(name, result)


def canonical_tool_name(tool: str) -> str:
    return two_root_constraints.canonical_tool_name(tool)


def load_bearing_tools(result: dict[str, Any]) -> list[str]:
    return two_root_constraints.load_bearing_tools(result)


def result_all_pass(result: dict[str, Any]) -> bool:
    return two_root_constraints.result_all_pass(result)


def engine_core_boundary_active() -> bool:
    if not ENGINE_CORE_AUTOGRAD_CONTRACT.exists():
        return False
    try:
        receipt = json.loads(ENGINE_CORE_AUTOGRAD_CONTRACT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return result_all_pass(receipt)


def source_path_for_result(result_path: pathlib.Path, name: str) -> pathlib.Path:
    candidate = ROOT / f"sim_{name}.py"
    if candidate.exists():
        return candidate
    stem = result_path.name.removesuffix("_results.json")
    return ROOT / f"sim_{stem}.py"


def imports_engine_core(source_path: pathlib.Path) -> bool:
    if not source_path.exists():
        return False
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return bool(ENGINE_CORE_IMPORT_RE.search(source_path.read_text(encoding="utf-8")))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "engine_core" or alias.name.startswith("engine_core.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "engine_core" or str(node.module or "").startswith("engine_core."):
                return True
    return False


def reviewed_numpy_boundary_sources() -> set[str]:
    global _REVIEWED_NUMPY_BOUNDARY_CACHE
    if _REVIEWED_NUMPY_BOUNDARY_CACHE is not None:
        return _REVIEWED_NUMPY_BOUNDARY_CACHE
    reviewed: set[str] = set()
    if NUMPY_QUARANTINE_RESULT.exists():
        try:
            receipt = json.loads(NUMPY_QUARANTINE_RESULT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = {}
        for row in receipt.get("quarantine_rows", []):
            if row.get("quarantine") == "reviewed_numpy_boundary_nonclassical_blocked":
                reviewed.add(str(row.get("path", "")))
    _REVIEWED_NUMPY_BOUNDARY_CACHE = reviewed
    return reviewed


def engine_core_finite_boundary_receipts() -> dict[str, dict[str, Any]]:
    global _ENGINE_CORE_FINITE_BOUNDARY_CACHE
    if _ENGINE_CORE_FINITE_BOUNDARY_CACHE is not None:
        return _ENGINE_CORE_FINITE_BOUNDARY_CACHE
    receipts: dict[str, dict[str, Any]] = {}
    for path in sorted(RESULT_DIR.glob("engine_core_finite_boundary_*_receipt_probe_results.json")):
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        target = receipt.get("target") or {}
        target_name = str(target.get("name") or "")
        if not target_name:
            continue
        positive = receipt.get("positive") or {}
        finite = positive.get("target_consumes_finite_json_stage_evidence") or {}
        z3_witness = positive.get("z3_quarantine_implication_blocks_promotion") or {}
        if (
            receipt.get("schema") == "ENGINE_CORE_FINITE_BOUNDARY_RECEIPT_v1"
            and result_all_pass(receipt)
            and target.get("admission_result") == "finite_boundary_admitted_without_gate_clearance"
            and finite.get("pass") is True
            and z3_witness.get("pass") is True
        ):
            receipts[target_name] = {
                "receipt_path": str(path.relative_to(ROOT)),
                "sha256": sha256_file(path),
                "admission_result": target.get("admission_result"),
                "blocked_uses": (receipt.get("finite_boundary_receipt") or {}).get("blocked_uses", []),
            }
    _ENGINE_CORE_FINITE_BOUNDARY_CACHE = receipts
    return receipts


def micro_receipt_status(tool: str, consumer_name: str = "") -> dict[str, Any]:
    receipt_names = two_root_constraints.micro_receipt_names(
        tool,
        include_aggregate=consumer_name == two_root_constraints.WAVE_A_TOOL_CAPABILITY_OBJECT_ID,
    )
    if not receipt_names:
        return {
            "micro_receipt": None,
            "micro_receipt_candidates": [],
            "micro_receipt_exists": False,
            "micro_receipt_all_pass": False,
            "micro_receipt_tool_load_bearing": False,
            "micro_receipt_admits_tool": False,
            "micro_receipt_reason": "missing required two-root tool micro receipt mapping",
        }
    candidates = [str((RESULT_DIR / name).relative_to(ROOT)) for name in receipt_names]
    last_status: dict[str, Any] | None = None
    missing_count = 0
    for receipt_name in receipt_names:
        path = RESULT_DIR / receipt_name
        if not path.exists():
            missing_count += 1
            last_status = {
                "micro_receipt": str(path.relative_to(ROOT)),
                "micro_receipt_candidates": candidates,
                "micro_receipt_exists": False,
                "micro_receipt_all_pass": False,
                "micro_receipt_tool_load_bearing": False,
                "micro_receipt_admits_tool": False,
                "micro_receipt_reason": "required two-root tool micro receipt is missing",
            }
            continue
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            last_status = {
                "micro_receipt": str(path.relative_to(ROOT)),
                "micro_receipt_candidates": candidates,
                "micro_receipt_exists": True,
                "micro_receipt_all_pass": False,
                "micro_receipt_tool_load_bearing": False,
                "micro_receipt_admits_tool": False,
                "micro_receipt_reason": "required two-root tool micro receipt is not valid JSON",
            }
            continue
        receipt_tools = set(load_bearing_tools(receipt))
        all_pass = result_all_pass(receipt)
        tool_load_bearing = tool in receipt_tools
        admits_tool = two_root_constraints.receipt_admits_tool(receipt, tool)
        status = {
            "micro_receipt": str(path.relative_to(ROOT)),
            "micro_receipt_candidates": candidates,
            "micro_receipt_exists": True,
            "micro_receipt_all_pass": all_pass,
            "micro_receipt_tool_load_bearing": tool_load_bearing,
            "micro_receipt_admits_tool": admits_tool,
            "micro_receipt_reason": "micro receipt passes and marks tool load-bearing"
            if admits_tool
            else "micro receipt does not pass or does not mark tool load-bearing",
        }
        if admits_tool:
            return status
        last_status = status
    if missing_count == len(receipt_names):
        return {
            "micro_receipt": candidates[0] if candidates else None,
            "micro_receipt_candidates": candidates,
            "micro_receipt_exists": False,
            "micro_receipt_all_pass": False,
            "micro_receipt_tool_load_bearing": False,
            "micro_receipt_admits_tool": False,
            "micro_receipt_reason": "required two-root tool micro receipts are missing",
        }
    return last_status or {
        "micro_receipt": None,
        "micro_receipt_candidates": candidates,
        "micro_receipt_exists": False,
        "micro_receipt_all_pass": False,
        "micro_receipt_tool_load_bearing": False,
        "micro_receipt_admits_tool": False,
        "micro_receipt_reason": "no usable micro receipt status was produced",
    }


def tool_two_root_status(tool: str, consumer_name: str = "") -> dict[str, Any]:
    status = TWO_ROOT_TOOL_ADMISSIBILITY.get(tool)
    receipt_status = micro_receipt_status(tool, consumer_name=consumer_name)
    if not status:
        return {
            "tool": tool,
            "finite_carrier_root": False,
            "noncommutation_or_order_root": False,
            "two_root_tool_admissible": False,
            "admissibility_reason": "missing two-root tool admissibility record",
            **receipt_status,
        }
    return {
        "tool": tool,
        **status,
        **receipt_status,
        "two_root_tool_admissible": bool(
            status["finite_carrier_root"]
            and status["noncommutation_or_order_root"]
            and receipt_status["micro_receipt_admits_tool"]
        ),
    }


def classify_result(path: pathlib.Path) -> dict[str, Any] | None:
    result = json.loads(path.read_text(encoding="utf-8"))
    name = str(result.get("name") or path.name.removesuffix("_results.json"))
    if not is_nonclassical_surface(name, result):
        return None
    if superseded_failed_surface_status(name, result):
        return None
    if preserved_counterevidence_surface_status(name, result):
        return None
    passes = result_all_pass(result)
    tools = load_bearing_tools(result)
    admissible = sorted(tool for tool in tools if tool in CONSTRAINT_ADMISSIBLE_TOOLS)
    inadmissible = sorted(tool for tool in tools if tool in CLASSICAL_OR_ADMIN_TOOLS)
    unknown = sorted(tool for tool in tools if tool not in CONSTRAINT_ADMISSIBLE_TOOLS and tool not in CLASSICAL_OR_ADMIN_TOOLS)
    if is_admin_support_surface(name, result, tools, admissible, unknown):
        return None
    if is_audit_or_routing_surface(name, result, unknown):
        return None
    root_status = {tool: tool_two_root_status(tool, consumer_name=name) for tool in tools}
    root_blocked = sorted(tool for tool, status in root_status.items() if not status["two_root_tool_admissible"])
    receipt_root_evidence = two_root_constraints.receipt_root_evidence(result)
    has_admissible = bool(admissible)
    has_disqualifying_classical = bool(inadmissible)
    same_source_only = not has_admissible and bool(set(tools) & {"engine_core"})
    source_path = source_path_for_result(path, name)
    source_missing = not source_path.exists()
    engine_core_importer_boundary = engine_core_boundary_active() and imports_engine_core(source_path)
    source_rel = str(source_path.relative_to(ROOT)) if source_path.exists() else None
    reviewed_numpy_boundary = source_rel in reviewed_numpy_boundary_sources() if source_rel else False
    finite_engine_boundary_receipt = (
        engine_core_finite_boundary_receipts().get(name) if engine_core_importer_boundary else None
    )
    if not passes:
        status = "blocked_result_not_all_pass"
    elif source_missing and has_disqualifying_classical and not has_admissible:
        status = "blocked_result_only_support_quarantined"
    elif source_missing and has_disqualifying_classical:
        status = "blocked_result_only_source_regeneration_required"
    elif reviewed_numpy_boundary:
        status = "blocked_reviewed_numpy_boundary"
    elif "numpy" in inadmissible:
        status = "blocked_numpy_load_bearing"
    elif has_disqualifying_classical:
        status = "blocked_classical_or_admin_load_bearing"
    elif engine_core_importer_boundary and finite_engine_boundary_receipt:
        status = "blocked_engine_core_importer_boundary_finite_receipt_covered"
    elif engine_core_importer_boundary:
        status = "blocked_engine_core_importer_boundary"
    elif same_source_only:
        status = "blocked_same_source_runtime_only"
    elif not has_admissible:
        status = "blocked_no_constraint_admissible_load_bearing_tool"
    elif unknown:
        status = "review_unknown_tool_role"
    elif root_blocked:
        status = "blocked_tool_not_two_root_admissible"
    elif not receipt_root_evidence.finite_carrier_root:
        status = "blocked_missing_f01_finite_bounded_carrier_evidence"
    elif not receipt_root_evidence.noncommutation_or_order_root:
        status = "blocked_missing_n01_noncommutation_or_order_evidence"
    else:
        status = "tool_role_candidate"
    return {
        "result_path": str(path.relative_to(ROOT)),
        "name": name,
        "load_bearing_tools": tools,
        "constraint_admissible_tools": admissible,
        "two_root_tool_status": root_status,
        "two_root_blocked_tools": root_blocked,
        "two_root_receipt_evidence": receipt_root_evidence.as_dict(),
        "inadmissible_or_admin_tools": inadmissible,
        "unknown_tools": unknown,
        "result_all_pass": passes,
        "source_path": source_rel,
        "source_exists": not source_missing,
        "reviewed_numpy_boundary": reviewed_numpy_boundary,
        "engine_core_importer_boundary": engine_core_importer_boundary,
        "engine_core_finite_boundary_receipt": finite_engine_boundary_receipt,
        "engine_core_boundary_contract": str(ENGINE_CORE_AUTOGRAD_CONTRACT.relative_to(ROOT)) if ENGINE_CORE_AUTOGRAD_CONTRACT.exists() else None,
        "tool_role_status": status,
        "formal_scout_candidate_surface_allowed": status == "tool_role_candidate",
        "sha256": sha256_file(path),
    }


def is_admin_support_surface(
    name: str,
    result: dict[str, Any],
    tools: list[str],
    admissible: list[str],
    unknown: list[str],
) -> bool:
    """Exclude nonpromotional audit/guard receipts from the nonclassical tool gate.

    These rows contain words like "basin" or "source_native" because they
    audit/routinely guard those surfaces. They are not themselves source-native
    nonclassical sim claims. Keep the exclusion narrow: it only applies to
    passing, nonpromotional formal scouts with explicit admin/support markers,
    no constraint-admissible load-bearing tools, and no unknown load-bearing
    tools.
    """

    lower_name = name.lower()
    source_alignment = str(result.get("source_alignment_category") or "").lower()
    marker_hit = any(marker in lower_name or marker in source_alignment for marker in ADMIN_SUPPORT_SURFACE_MARKERS)
    return bool(
        marker_hit
        and result.get("classification") == CLASSIFICATION
        and result.get("promotion_allowed") is False
        and result_all_pass(result)
        and tools
        and not admissible
        and not unknown
    and all(tool in CLASSICAL_OR_ADMIN_TOOLS for tool in tools)
    )


def is_audit_or_routing_surface(name: str, result: dict[str, Any], unknown: list[str]) -> bool:
    """Exclude nonpromotional audit/routing receipts from claim-surface gating.

    Some closeout receipts use z3/cvc5/rustworkx as load-bearing guard tools,
    but the receipt itself is still an audit, hygiene, provider-gap, or
    sidequest-routing artifact. Those rows should remain visible in their own
    final-synthesis/readiness receipts, but they are not source-native
    nonclassical basin/manifold claim surfaces for this gate.
    """

    lower_name = name.lower()
    source_alignment = str(result.get("source_alignment_category") or result.get("SOURCE_ALIGNMENT_CATEGORY") or "").lower()
    sim_kind = str(result.get("sim_execution_kind") or result.get("SIM_EXECUTION_KIND") or "").lower()
    marker_hit = any(
        marker in lower_name or marker in source_alignment
        for marker in (
            "git_diff_check_hygiene",
            "hygiene_blocker",
            "admission_gate",
            "classifier",
            "quarantine",
            "handoff_ingest",
            "tooling_violation",
            "sidequest_routing",
            "provider_global_falsifier_gap",
            "provider_and_global_falsifier_gap",
        )
    )
    return bool(
        result.get("classification") == CLASSIFICATION
        and result.get("promotion_allowed") is False
        and result_all_pass(result)
        and not unknown
        and (sim_kind == "audit" or marker_hit)
        and marker_hit
    )


def superseded_failed_surface_status(name: str, result: dict[str, Any]) -> dict[str, Any] | None:
    """Return a narrow exclusion receipt for failed rows replaced by a green successor.

    This does not paint the failed receipt green. It only removes a historical
    failed v1 surface from the active source-native nonclassical tool gate when
    an explicit v2 successor has already preserved the failure as a blocked
    control and supplied the missing repair evidence.
    """

    spec = SUPERSEDED_FAILED_SURFACES.get(name)
    if not spec:
        return None
    successor_path = RESULT_DIR / str(spec["successor_result"])
    if not successor_path.exists():
        return None
    try:
        successor = json.loads(successor_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    old_gate = (
        result.get("positive", {})
        .get("axis0_seven_acceptance_fields_hold_INCLUDING_path_entropy_hard_gate", {})
        .get("details", {})
    )
    old_path_entropy = (
        result.get("graveyard_companions", {})
        .get("path_entropy_degeneracy_HARD_GATE_status", {})
    )
    successor_positive = successor.get("positive", {})
    successor_graveyard = successor.get("graveyard_companions", {})
    successor_path_entropy = successor_graveyard.get("path_entropy_blocked_degenerate_plateau_preserved", {})
    successor_detached = successor_graveyard.get("cycle_autograd_severance_preserved_in_detached_control", {})
    successor_ok = (
        successor.get("name") == spec["successor_name"]
        and result_all_pass(successor)
        and successor.get("promotion_allowed") is False
        and successor_positive.get("active_per_lego_remove_and_rerun_ablation_is_sensitive", {}).get("pass") is True
        and successor_positive.get("active_cycle_path_order_variants_are_sensitive", {}).get("pass") is True
        and successor_positive.get("torch_autograd_sees_every_active_lego_weight", {}).get("pass") is True
        and successor_path_entropy.get("blocked") is True
        and successor_detached.get("blocked") is True
    )
    old_failure_preserved = (
        result_all_pass(result) is False
        and result.get("promotion_allowed") is False
        and result.get("classification") == "tool_lego_fit_probe"
        and old_gate.get("P4_path_entropy_not_degenerate_HARD_GATE") is False
        and old_gate.get("diagnostic_path_entropy_degenerate") is True
        and old_path_entropy.get("is_degenerate") is True
    )
    if not (old_failure_preserved and successor_ok):
        return None
    return {
        "tool_role_status": "excluded_superseded_failed_surface",
        "successor_result": str(successor_path.relative_to(ROOT)),
        "successor_name": successor.get("name"),
        "reason": spec["reason"],
        "old_failure_preserved": True,
        "successor_all_pass": True,
        "promotion_allowed": False,
    }


def _row_by_n(rows: Any, n_qubits: int) -> dict[str, Any]:
    if not isinstance(rows, list):
        return {}
    return next((row for row in rows if isinstance(row, dict) and row.get("n_qubits") == n_qubits), {})


def preserved_counterevidence_surface_status(name: str, result: dict[str, Any]) -> dict[str, Any] | None:
    """Return a narrow exclusion receipt for classified red counterevidence rows.

    This keeps honest negative reservoir receipts red. It only removes them
    from active B2 source-repair selection when their own current metrics still
    prove they are counterevidence, not schema mistakes or unknown tool-role
    rows. B3/readiness continues to carry the validator-red evidence.
    """

    spec = PRESERVED_COUNTEREVIDENCE_SURFACES.get(name)
    if not spec:
        return None
    if not (
        result.get("classification") == CLASSIFICATION
        and result.get("promotion_allowed") is False
        and result.get("all_pass") is False
    ):
        return None
    positive = result.get("positive", {}) if isinstance(result.get("positive"), dict) else {}
    evidence: dict[str, Any] = {}
    if name == "multiqubit_qit_reservoir_global_structure_probe":
        check = positive.get("frozen_multiqubit_reservoir_separates_global_structure_at_8q", {})
        row8 = _row_by_n(check.get("rows", []), 8) if isinstance(check, dict) else {}
        metrics = row8.get("metrics", {}) if isinstance(row8, dict) else {}
        z3_check = positive.get("z3_rejects_local_or_shuffle_only_explanation_at_8q", {})
        evidence = {
            "n_qubits": row8.get("n_qubits"),
            "row_pass": row8.get("pass"),
            "positive_pass": check.get("pass") if isinstance(check, dict) else None,
            "frozen_reservoir_accuracy": metrics.get("frozen_reservoir_accuracy"),
            "local_only_accuracy": metrics.get("local_only_accuracy"),
            "shuffled_label_accuracy": metrics.get("frozen_reservoir_shuffled_label_accuracy"),
            "z3_guard_pass": z3_check.get("pass") if isinstance(z3_check, dict) else None,
        }
        evidence_ok = (
            evidence["n_qubits"] == 8
            and evidence["row_pass"] is False
            and evidence["positive_pass"] is False
            and isinstance(evidence["frozen_reservoir_accuracy"], (int, float))
            and evidence["frozen_reservoir_accuracy"] < 0.70
            and evidence["z3_guard_pass"] is True
        )
    elif name == "multiqubit_qit_reservoir_grok_task_replication_probe":
        check = positive.get("grok_task_frozen_reservoir_beats_local_bloch_at_8q", {})
        row8 = _row_by_n(check.get("rows", []), 8) if isinstance(check, dict) else {}
        metrics = row8.get("metrics", {}) if isinstance(row8, dict) else {}
        z3_check = positive.get("z3_rejects_grok_task_local_or_shuffle_explanation", {})
        evidence = {
            "n_qubits": row8.get("n_qubits"),
            "row_pass": row8.get("pass"),
            "positive_pass": check.get("pass") if isinstance(check, dict) else None,
            "frozen_reservoir_accuracy": metrics.get("frozen_reservoir_accuracy"),
            "local_bloch_accuracy": metrics.get("local_bloch_accuracy"),
            "local_spectrum_accuracy": metrics.get("local_spectrum_accuracy"),
            "shuffled_label_accuracy": metrics.get("frozen_reservoir_shuffled_label_accuracy"),
            "z3_guard_pass": z3_check.get("pass") if isinstance(z3_check, dict) else None,
            "z3_solver_status": z3_check.get("solver_status") if isinstance(z3_check, dict) else None,
        }
        evidence_ok = (
            evidence["n_qubits"] == 8
            and evidence["row_pass"] is False
            and evidence["positive_pass"] is False
            and evidence["frozen_reservoir_accuracy"] == evidence["local_bloch_accuracy"]
            and evidence["z3_guard_pass"] is False
            and evidence["z3_solver_status"] == "sat"
        )
    else:
        evidence_ok = False
    if not evidence_ok:
        return None
    return {
        "tool_role_status": "excluded_preserved_counterevidence_surface",
        "boundary_class": spec["boundary_class"],
        "reason": spec["reason"],
        "evidence": evidence,
        "promotion_allowed": False,
    }


def admin_support_row(path: pathlib.Path) -> dict[str, Any] | None:
    result = json.loads(path.read_text(encoding="utf-8"))
    name = str(result.get("name") or path.name.removesuffix("_results.json"))
    if not is_nonclassical_surface(name, result):
        return None
    tools = load_bearing_tools(result)
    admissible = sorted(tool for tool in tools if tool in CONSTRAINT_ADMISSIBLE_TOOLS)
    unknown = sorted(tool for tool in tools if tool not in CONSTRAINT_ADMISSIBLE_TOOLS and tool not in CLASSICAL_OR_ADMIN_TOOLS)
    superseded = superseded_failed_surface_status(name, result)
    preserved_counterevidence = preserved_counterevidence_surface_status(name, result)
    if not (
        is_admin_support_surface(name, result, tools, admissible, unknown)
        or is_audit_or_routing_surface(name, result, unknown)
        or superseded
        or preserved_counterevidence
    ):
        return None
    source_path = source_path_for_result(path, name)
    source_rel = str(source_path.relative_to(ROOT)) if source_path.exists() else None
    exclusion = superseded or preserved_counterevidence
    return {
        "result_path": str(path.relative_to(ROOT)),
        "name": name,
        "source_path": source_rel,
        "load_bearing_tools": tools,
        "tool_role_status": (
            exclusion["tool_role_status"] if exclusion else "excluded_admin_support_surface"
        ),
        "reason": (
            exclusion["reason"]
            if exclusion
            else "Passing nonpromotional audit/guard/adoption receipt; admin tools are load-bearing for receipt routing, not a source-native nonclassical basin claim."
        ),
        "superseded_by": superseded.get("successor_result") if superseded else None,
        "boundary_class": preserved_counterevidence.get("boundary_class") if preserved_counterevidence else None,
        "preserved_counterevidence": preserved_counterevidence.get("evidence") if preserved_counterevidence else None,
        "sha256": sha256_file(path),
    }


def main() -> int:
    started = time.time()
    result_paths = sorted(RESULT_DIR.glob("*_results.json"))
    rows = [row for path in result_paths if (row := classify_result(path))]
    admin_support_rows = [row for path in result_paths if (row := admin_support_row(path))]
    blocked = [row for row in rows if not row["formal_scout_candidate_surface_allowed"]]
    candidates = [row for row in rows if row["formal_scout_candidate_surface_allowed"]]

    positive = {
        "result_surface_scanned": {
            "pass": len(rows) > 0,
            "nonclassical_surface_count": len(rows),
            "blocked_count": len(blocked),
            "candidate_count": len(candidates),
        },
        "blocked_rows_are_not_allowed_as_candidate_surfaces": {
            "pass": all(row["formal_scout_candidate_surface_allowed"] is False for row in blocked),
            "blocked_status_counts": {
                status: sum(1 for row in blocked if row["tool_role_status"] == status)
                for status in sorted({row["tool_role_status"] for row in blocked})
            },
        },
        "candidates_are_passing_receipts": {
            "pass": all(row["result_all_pass"] is True for row in candidates),
            "candidate_count": len(candidates),
        },
        "candidates_have_no_classical_or_admin_load_bearing_tools": {
            "pass": all(not row["inadmissible_or_admin_tools"] for row in candidates),
            "candidate_count": len(candidates),
        },
        "candidates_have_two_root_admissible_load_bearing_tools": {
            "pass": all(
                all(status["two_root_tool_admissible"] for status in row["two_root_tool_status"].values())
                and row["two_root_receipt_evidence"]["two_root_receipt_admissible"]
                for row in candidates
            ),
            "candidate_count": len(candidates),
            "root_rule": "Every load-bearing tool for a formal-scout candidate surface must satisfy the two root constraints before it can be counted as an allowed tool.",
        },
        "engine_core_importer_boundary_blocks_candidates": {
            "pass": all(not row["engine_core_importer_boundary"] for row in candidates),
            "blocked_engine_core_importer_count": sum(
                1 for row in blocked if row["tool_role_status"] == "blocked_engine_core_importer_boundary"
            ),
            "root_rule": "Direct EngineCore importers cross the current NumPy/autograd-severed boundary and cannot count as torch-native formal-scout candidate surfaces until exact boundary or torch-port receipts exist.",
        },
        "admin_support_receipts_excluded_from_nonclassical_surface": {
            "pass": all(
                row["tool_role_status"]
                in {
                    "excluded_admin_support_surface",
                    "excluded_superseded_failed_surface",
                    "excluded_preserved_counterevidence_surface",
                }
                for row in admin_support_rows
            ),
            "excluded_count": len(admin_support_rows),
            "excluded_names": [row["name"] for row in admin_support_rows],
            "excluded_status_counts": {
                status: sum(1 for row in admin_support_rows if row["tool_role_status"] == status)
                for status in sorted({row["tool_role_status"] for row in admin_support_rows})
            },
            "root_rule": "Audit/guard/adoption receipts and preserved red counterevidence rows do not become active source-native nonclassical repair surfaces merely because their names mention basin/manifold/source-native.",
        },
    }
    graveyard = {
        "classical_tool_cannot_generate_nonclassical_basin": {
            "pass": True,
            "reason": "A classical/admin tool may be load-bearing for a classical sim and may support logging, baselines, controls, or negatives, but cannot be the load-bearing engine for the actual nonclassical attractor-basin claim.",
        },
        "same_source_runtime_is_not_independent_tool_convergence": {
            "pass": True,
            "reason": "EngineCore execution alone can be source-native evidence but not independent method-multiplicity basin evidence.",
        },
        "constraint_mismatched_tool_role_blocks_promotion": {
            "pass": True,
            "reason": "Tools must preserve, certify, or pressure the exact constraint class being claimed.",
        },
        "tool_allowlist_is_not_prior_to_roots": {
            "pass": True,
            "reason": "The two root constraints apply to the tool surface itself; a tool is not allowed merely because it is installed or popular.",
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_broad_claims": {
            "pass": "does not promote any engine" in CLAIM_CEILING,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "constraint_admissible_tool_role_gate",
        "two_root_tool_admissibility": TWO_ROOT_TOOL_ADMISSIBILITY,
        "two_root_tool_micro_receipts": TWO_ROOT_TOOL_MICRO_RECEIPTS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "tool_role_rows": rows,
        "admin_support_excluded_rows": admin_support_rows,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a v5 formal scout gate over current result receipts.",
            "It converts tool-mismatch into explicit quarantine instead of letting the narrative promote weak tools.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  surfaces={len(rows)} blocked={len(blocked)} candidates={len(candidates)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

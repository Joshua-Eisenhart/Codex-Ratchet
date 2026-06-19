#!/usr/bin/env python3
"""Shared two-root constraint metadata for sim/tool admission.

F01 is the finite/bounded-carrier root. N01 is the noncommuting or
order-sensitive-structure root. This module is intentionally stdlib-only so it
can be imported by receipt validators, admission guards, and formal-scout
probes without pulling in sim dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


F01_ROOT = "F01_FINITE_BOUNDED_CARRIER"
N01_ROOT = "N01_NONCOMMUTATION_OR_ORDER_SENSITIVITY"

TOOL_ALIASES = {
    "np": "numpy",
    "numpy": "numpy",
    "numpy_linalg": "numpy",
    "np_linalg": "numpy",
    "scipy": "scipy",
    "scipy_linalg": "scipy",
    "torch": "pytorch",
    "torch_autograd": "pytorch",
    "pytorch": "pytorch",
    "pytorch_autograd": "pytorch",
    "pyg": "torch_geometric",
    "torch_geometric": "torch_geometric",
    "torch_geometric_nn": "torch_geometric",
    "autolirpa": "auto_lirpa",
    "auto_lirpa": "auto_lirpa",
    "auto_lirpa_bound": "auto_lirpa",
    "lewm": "le_wm",
    "le_wm": "le_wm",
    "le_wm_module": "le_wm",
    "z3": "z3",
    "z3_solver": "z3",
    "cvc5": "cvc5",
    "sympy": "sympy",
    "clifford": "clifford",
    "torch_ga": "clifford",
    "geomstats": "geomstats",
    "e3nn": "e3nn",
    "rustworkx": "rustworkx",
    "networkx": "networkx",
    "xgi": "xgi",
    "toponetx": "toponetx",
    "gudhi": "gudhi",
    "quimb": "quimb",
    "cotengra": "cotengra",
    "kahypar": "kahypar",
    "opt_einsum": "opt_einsum",
    "json": "python_json",
    "python_json": "python_json",
    "pathlib": "python_pathlib",
    "python_pathlib": "python_pathlib",
    "re": "python_re",
    "python_re": "python_re",
    "hashlib": "hashlib",
    "time": "time",
    "subprocess": "subprocess",
    "concurrent_futures": "concurrent_futures",
    "axis0_guard_utils": "axis0_guard_utils",
    "holodeck_fep_engine_hopf_map": "holodeck_fep_engine_hopf_map",
    "engine_core": "engine_core",
    "engine_v6_reference": "engine_v6_reference",
    "engine_v7_reference": "engine_v7_reference",
    "sklearn": "sklearn",
    "scikit_learn": "sklearn",
    "composed_manifold_scout": "composed_manifold_scout",
    "multitool_carrier_scout": "multitool_carrier_scout",
    "source_density_scout": "source_density_scout",
    "special_form_constraints": "special_form_constraints",
}

CAPABILITY_PROBE_STEMS = {
    "pytorch": "pytorch",
    "torch_geometric": "pyg",
    "auto_lirpa": "auto_lirpa",
    "le_wm": "lewm",
    "z3": "z3",
    "cvc5": "cvc5",
    "sympy": "sympy",
    "clifford": "clifford",
    "geomstats": "geomstats",
    "e3nn": "e3nn",
    "rustworkx": "rustworkx",
    "networkx": "networkx",
    "xgi": "xgi",
    "toponetx": "toponetx",
    "gudhi": "gudhi",
    "quimb": "quimb",
    "cotengra": "cotengra",
    "kahypar": "kahypar",
    "opt_einsum": "opt_einsum",
}

CLASSICAL_OR_ADMIN_TOOLS = {
    "numpy",
    "scipy",
    "python_json",
    "python_pathlib",
    "python_re",
    "hashlib",
    "time",
    "subprocess",
    "concurrent_futures",
    "axis0_guard_utils",
    "holodeck_fep_engine_hopf_map",
    "engine_core",
    "engine_v6_reference",
    "engine_v7_reference",
    "sklearn",
    "composed_manifold_scout",
    "multitool_carrier_scout",
    "source_density_scout",
    "special_form_constraints",
}

TRANSITIVE_ROLE_VALUES = {
    "transitive",
    "upstream",
    "imported",
    "delegated",
    "engine_core",
    "engine-core",
}

TWO_ROOT_TOOL_ADMISSIBILITY: dict[str, dict[str, Any]] = {
    "pytorch": {
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
    "pytorch": "eight_qubit_mps_channel_order_graph_leakage_pyg_pytorch_opt_einsum_z3_probe_results.json",
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
    "opt_einsum": "opt_einsum_index_order_contraction_micro_probe_results.json",
    "networkx": "sim_networkx_ordered_graph_readout_review_unknown_micro_probe_results.json",
    "jax": "three_spinor_associator_lifted_bracketing_probe_results.json",
    "julia": "three_spinor_associator_lifted_bracketing_probe_results.json",
}

WAVE_A_TOOL_CAPABILITY_OBJECT_ID = "wave_a_cs_ai_no_install_micro_probes"
WAVE_A_TOOL_CAPABILITY_RECEIPT = f"{WAVE_A_TOOL_CAPABILITY_OBJECT_ID}_results.json"

AGGREGATE_TOOL_CAPABILITY_RECEIPTS = {
    WAVE_A_TOOL_CAPABILITY_RECEIPT: frozenset(
        {
            "cvc5",
            "gudhi",
            "pytorch",
            "rustworkx",
            "toponetx",
            "torch_geometric",
            "xgi",
        }
    )
}

NONCLASSICAL_NAME_MARKERS = (
    "source_native",
    "engine_manifold",
    "manifold",
    "thirteen_layer",
    "axis0",
    "fep",
    "holodeck",
    "cross_engine",
    "multicarrier",
    "peps",
    "mps",
    "two_root",
    "constraint_selector",
    "basin",
    "g_structure",
    "qit",
)

FINITE_EVIDENCE_TOKENS = (
    "f01",
    "finite",
    "bounded",
    "carrier",
    "dimension",
    "site_count",
    "n_qubits",
    "width",
    "boundary",
    "fixture",
    "tensor",
    "graph",
    "hypergraph",
    "simplicial",
    "cell",
    "mps",
    "peps",
    "peps3d",
)

ORDER_EVIDENCE_TOKENS = (
    "n01",
    "noncommutation",
    "noncommuting",
    "noncommutative",
    "anticommut",
    "commutator",
    "order",
    "ordering",
    "order_sensitive",
    "order-sensitive",
    "ordered",
    "reversal",
    "reverse",
    "permutation",
    "orientation",
    "holonomy",
    "chirality",
    "g_structure",
    "operator_order",
    "contraction_order",
    "message_order",
    "schedule_order",
    "path_order",
)


@dataclass(frozen=True)
class ReceiptRootEvidence:
    finite_carrier_root: bool
    noncommutation_or_order_root: bool
    finite_evidence: tuple[str, ...]
    noncommutation_or_order_evidence: tuple[str, ...]

    @property
    def two_root_receipt_admissible(self) -> bool:
        return self.finite_carrier_root and self.noncommutation_or_order_root

    def as_dict(self) -> dict[str, Any]:
        return {
            "finite_carrier_root": self.finite_carrier_root,
            "noncommutation_or_order_root": self.noncommutation_or_order_root,
            "two_root_receipt_admissible": self.two_root_receipt_admissible,
            "finite_evidence": list(self.finite_evidence),
            "noncommutation_or_order_evidence": list(self.noncommutation_or_order_evidence),
        }


def canonical_tool_name(tool: str) -> str:
    normalized = str(tool).strip().lower().replace("-", "_").replace(".", "_")
    family = normalized.split("/", 1)[0]
    return TOOL_ALIASES.get(family, family)


def capability_probe_stem(tool: str) -> str:
    canonical = canonical_tool_name(tool)
    return CAPABILITY_PROBE_STEMS.get(canonical, canonical)


def is_two_root_tool(tool: str) -> bool:
    return canonical_tool_name(tool) in TWO_ROOT_TOOL_ADMISSIBILITY


def micro_receipt_names(tool: str, *, include_aggregate: bool = False) -> list[str]:
    """Return primary plus aggregate tool-capability receipts for a tool.

    Aggregate receipts are scratch diagnostics only; they can prove the named
    tool/function capability exists, but they do not promote a lego or claim.
    """

    canonical = canonical_tool_name(tool)
    names: list[str] = []
    primary = TWO_ROOT_TOOL_MICRO_RECEIPTS.get(canonical)
    if primary:
        names.append(primary)
    if include_aggregate:
        for receipt_name, tools in AGGREGATE_TOOL_CAPABILITY_RECEIPTS.items():
            if canonical in tools:
                names.append(receipt_name)
    return list(dict.fromkeys(names))


def receipt_admits_tool(payload: dict[str, Any], tool: str) -> bool:
    canonical = canonical_tool_name(tool)
    if not result_all_pass(payload):
        return False
    if canonical in set(load_bearing_tools(payload)):
        return True
    object_id = str(payload.get("object_id") or payload.get("name") or "")
    if (
        object_id == WAVE_A_TOOL_CAPABILITY_OBJECT_ID
        and payload.get("classification") == "scratch_diagnostic"
        and payload.get("evidence_level") == "tool_capability"
        and canonical in AGGREGATE_TOOL_CAPABILITY_RECEIPTS[
            WAVE_A_TOOL_CAPABILITY_RECEIPT
        ]
    ):
        return True
    return False


def is_classical_or_admin_tool(tool: str) -> bool:
    return canonical_tool_name(tool) in CLASSICAL_OR_ADMIN_TOOLS


def nonclassical_tool_names() -> set[str]:
    return set(TWO_ROOT_TOOL_ADMISSIBILITY)


def normalized_execution_kind(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in {
        "bridge",
        "qit_bridge",
        "nonclassical_bridge",
        "semiclassical",
        "semi_classical",
        "semiclassical_bridge",
        "semiclassical_szilard",
    }:
        return "bridge"
    if normalized == "nonclassical":
        return "nonclassical"
    if normalized == "classical":
        return "classical"
    return ""


def payload_execution_kind(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return normalized_execution_kind(
        payload.get("sim_execution_kind")
        or payload.get("SIM_EXECUTION_KIND")
        or summary.get("sim_execution_kind")
        or summary.get("SIM_EXECUTION_KIND")
    )


def is_nonclassical_surface(name: str, payload: dict[str, Any] | None = None) -> bool:
    if isinstance(payload, dict) and payload_execution_kind(payload) == "nonclassical":
        return True
    lower = str(name).lower()
    return any(marker in lower for marker in NONCLASSICAL_NAME_MARKERS)


def load_bearing_tools(payload: dict[str, Any]) -> list[str]:
    depth = payload.get("TOOL_INTEGRATION_DEPTH") or payload.get("tool_integration_depth") or {}
    if not isinstance(depth, dict):
        return []
    return sorted(
        canonical_tool_name(str(tool))
        for tool, role in depth.items()
        if str(role).lower() == "load_bearing"
    )


def tool_role_sources(payload: dict[str, Any], manifest: dict[str, Any] | None = None) -> dict[str, str]:
    raw = payload.get("tool_role_source") or payload.get("TOOL_ROLE_SOURCE") or {}
    role_sources: dict[str, str] = {}
    if isinstance(raw, dict):
        for tool, source in raw.items():
            folded = str(source).strip().lower().replace("_", "-")
            role_sources[str(tool)] = folded
            role_sources[canonical_tool_name(str(tool))] = folded
    manifest_payload = manifest if manifest is not None else payload.get("tool_manifest") or payload.get("TOOL_MANIFEST") or {}
    if isinstance(manifest_payload, dict):
        for tool, entry in manifest_payload.items():
            if not isinstance(entry, dict):
                continue
            source = (
                entry.get("role_source")
                or entry.get("tool_role_source")
                or entry.get("integration_source")
            )
            if source:
                folded = str(source).strip().lower().replace("_", "-")
                role_sources.setdefault(str(tool), folded)
                role_sources.setdefault(canonical_tool_name(str(tool)), folded)
                continue
            reason = str(entry.get("reason") or "").lower()
            if "transitive" in reason or "through enginecore" in reason or "through engine_core" in reason:
                role_sources.setdefault(str(tool), "transitive")
                role_sources.setdefault(canonical_tool_name(str(tool)), "transitive")
    return role_sources


def is_transitive_role(tool: str, role_sources: dict[str, str]) -> bool:
    values = {
        role_sources.get(str(tool)),
        role_sources.get(canonical_tool_name(str(tool))),
    }
    return any(value in TRANSITIVE_ROLE_VALUES for value in values if value)


def local_load_bearing_tools(payload: dict[str, Any]) -> list[str]:
    depth = payload.get("TOOL_INTEGRATION_DEPTH") or payload.get("tool_integration_depth") or {}
    if not isinstance(depth, dict):
        return []
    role_sources = tool_role_sources(payload)
    return sorted(
        canonical_tool_name(str(tool))
        for tool, role in depth.items()
        if str(role).lower() == "load_bearing" and not is_transitive_role(str(tool), role_sources)
    )


def result_all_pass(payload: dict[str, Any]) -> bool:
    if payload.get("all_pass") is True:
        return True
    if payload.get("pass") is True:
        return True
    summary = payload.get("summary")
    if isinstance(summary, dict):
        if summary.get("all_pass") is True or summary.get("all_passed") is True:
            return True
    return legacy_sections_all_pass(payload)


def section_all_pass(section: Any) -> bool:
    if section is None:
        return True
    if isinstance(section, dict):
        for value in section.values():
            if isinstance(value, dict):
                if value.get("pass") is not True:
                    return False
            elif isinstance(value, bool):
                if value is not True:
                    return False
        return True
    if isinstance(section, list):
        for value in section:
            if isinstance(value, dict) and value.get("pass") is not True:
                return False
            if isinstance(value, bool) and value is not True:
                return False
        return True
    return False


def nearby_all_pass(payload: dict[str, Any]) -> bool:
    nearby = payload.get("nearby_variants")
    if nearby is None:
        return True
    if not isinstance(nearby, dict):
        return False
    if nearby.get("all_pass") is True:
        return True
    total = nearby.get("total")
    passed = nearby.get("passed")
    return isinstance(total, int) and isinstance(passed, int) and total == passed


def legacy_sections_all_pass(payload: dict[str, Any]) -> bool:
    """Infer success for old formal-scout receipts with pass-shaped sections.

    This deliberately stays narrower than the validator. It only lets legacy
    receipts count as passing when positive/graveyard/boundary sections all have
    explicit passing entries, nearby variants are all passed when present, and
    blockers are absent or empty. Honest red receipts with any failed predicate
    remain blocked.
    """

    if payload.get("classification") != "formal_scout":
        return False
    if payload.get("promotion_allowed") is not False:
        return False
    blockers = payload.get("blockers")
    if blockers not in (None, [], {}):
        return False
    positive = payload.get("positive")
    if not positive:
        return False
    if not section_all_pass(positive):
        return False
    if not section_all_pass(payload.get("graveyard_companions")):
        return False
    if not section_all_pass(payload.get("boundary")):
        return False
    if not nearby_all_pass(payload):
        return False
    return True


def _record_evidence(hit: str, target: list[str]) -> None:
    if hit not in target and len(target) < 12:
        target.append(hit)


def _scan_for_tokens(
    obj: Any,
    *,
    finite_hits: list[str],
    order_hits: list[str],
    path: str = "$",
    max_nodes: int = 4000,
    state: dict[str, int] | None = None,
) -> None:
    tracker = state if state is not None else {"nodes": 0}
    if tracker["nodes"] >= max_nodes:
        return
    tracker["nodes"] += 1
    if isinstance(obj, dict):
        for key, value in obj.items():
            text = str(key).lower()
            for token in FINITE_EVIDENCE_TOKENS:
                if token in text:
                    _record_evidence(f"{path}.{key}", finite_hits)
                    break
            for token in ORDER_EVIDENCE_TOKENS:
                if token in text:
                    _record_evidence(f"{path}.{key}", order_hits)
                    break
            _scan_for_tokens(
                value,
                finite_hits=finite_hits,
                order_hits=order_hits,
                path=f"{path}.{key}",
                max_nodes=max_nodes,
                state=tracker,
            )
    elif isinstance(obj, list):
        for index, value in enumerate(obj[:200]):
            _scan_for_tokens(
                value,
                finite_hits=finite_hits,
                order_hits=order_hits,
                path=f"{path}[{index}]",
                max_nodes=max_nodes,
                state=tracker,
            )
    elif isinstance(obj, str):
        text = obj.lower()
        for token in FINITE_EVIDENCE_TOKENS:
            if token in text:
                _record_evidence(path, finite_hits)
                break
        for token in ORDER_EVIDENCE_TOKENS:
            if token in text:
                _record_evidence(path, order_hits)
                break


def receipt_root_evidence(payload: dict[str, Any]) -> ReceiptRootEvidence:
    finite_hits: list[str] = []
    order_hits: list[str] = []
    root = payload.get("two_root_constraints") or payload.get("root_constraints")
    if isinstance(root, dict):
        if root.get("finite_carrier_root") is True or root.get("F01") is True:
            _record_evidence("$.root_constraints.explicit_f01", finite_hits)
        if root.get("noncommutation_or_order_root") is True or root.get("N01") is True:
            _record_evidence("$.root_constraints.explicit_n01", order_hits)
    _scan_for_tokens(payload, finite_hits=finite_hits, order_hits=order_hits)
    return ReceiptRootEvidence(
        finite_carrier_root=bool(finite_hits),
        noncommutation_or_order_root=bool(order_hits),
        finite_evidence=tuple(finite_hits),
        noncommutation_or_order_evidence=tuple(order_hits),
    )

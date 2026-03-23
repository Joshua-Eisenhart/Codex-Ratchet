#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

FULL_CYCLE_LANES: set[str] = {
    "STEELMAN",
    "ALT_FORMALISM",
    "BOUNDARY_REPAIR",
    "ADVERSARIAL_NEG",
    "RESCUER",
}
REQUIRED_STRESS_SIM_FAMILIES: tuple[str, ...] = (
    "BASELINE",
    "BOUNDARY_SWEEP",
    "PERTURBATION",
    "ADVERSARIAL_NEG",
    "COMPOSITION_STRESS",
)
KNOWN_SIM_TIERS: tuple[str, ...] = (
    "T0_ATOM",
    "T1_COMPOUND",
    "T2_OPERATOR",
    "T3_STRUCTURE",
    "T4_SYSTEM_SEGMENT",
    "T5_ENGINE",
    "T6_WHOLE_SYSTEM",
)


def _tier_rank(name: str) -> int:
    try:
        return KNOWN_SIM_TIERS.index(name)
    except ValueError:
        return -1


class LaneMinimum(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_branches: int = Field(ge=1)


class RescueStartConditions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_graveyard_count: int = Field(ge=0)
    min_kill_diversity: int = Field(ge=0)
    min_canonical_count: int = Field(ge=0)
    max_rescue_sources: int = Field(default=6, ge=1)
    graveyard_negative_expansion_limit: int | None = Field(default=None, ge=1)
    balanced_max_items: int | None = Field(default=None, ge=1)
    balanced_max_sims: int | None = Field(default=None, ge=1)
    graveyard_first_max_items: int | None = Field(default=None, ge=1)
    graveyard_first_max_sims: int | None = Field(default=None, ge=1)
    graveyard_recovery_max_items: int | None = Field(default=None, ge=1)
    graveyard_recovery_max_sims: int | None = Field(default=None, ge=1)


class AdmissibilityBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executable_head: list[str]
    active_companion_floor: list[str]
    late_passengers: list[str]
    witness_only_terms: list[str]
    residue_terms: list[str]
    landing_blockers: dict[str, str]
    witness_floor: list[str]
    current_readiness_status: str


class FamilyAdmissibilityHints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_head_terms: list[str]
    forbid_strategy_head_terms: list[str]
    late_passenger_terms: list[str]
    witness_only_terms: list[str]
    residue_only_terms: list[str]
    landing_blocker_overrides: dict[str, str]


class TermMathSurface(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objects: str
    operations: str
    invariants: str
    domain: str
    codomain: str


class SimHooks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_sim_families: list[str]
    required_probe_terms: list[str]
    probe_term_overrides: dict[str, str]
    term_sim_tiers: dict[str, str]
    sim_family_tiers: dict[str, str] = Field(default_factory=dict)
    recovery_sim_families: list[str]
    expected_tier_floor: str
    promotion_contract_refs: list[str]

    @field_validator("required_sim_families")
    @classmethod
    def _validate_required_sim_families(cls, value: list[str]) -> list[str]:
        missing = sorted(set(REQUIRED_STRESS_SIM_FAMILIES).difference(value))
        if missing:
            raise ValueError(f"missing_required_sim_families:{','.join(missing)}")
        unknown = sorted(set(value).difference(REQUIRED_STRESS_SIM_FAMILIES))
        if unknown:
            raise ValueError(f"unknown_sim_families:{','.join(unknown)}")
        return value

    @field_validator("expected_tier_floor")
    @classmethod
    def _validate_expected_tier_floor(cls, value: str) -> str:
        normalized = value.strip().upper()
        if _tier_rank(normalized) < 0:
            raise ValueError(f"invalid_expected_tier_floor:{value}")
        return normalized

    @field_validator("term_sim_tiers")
    @classmethod
    def _normalize_term_sim_tiers(cls, value: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for term, tier in value.items():
            cleaned = str(tier).strip().upper()
            if _tier_rank(cleaned) < 0:
                raise ValueError(f"invalid_term_sim_tier:{term}:{tier}")
            normalized[str(term).strip()] = cleaned
        return normalized

    @field_validator("sim_family_tiers")
    @classmethod
    def _normalize_sim_family_tiers(cls, value: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for family, tier in value.items():
            family_token = str(family).strip().upper()
            cleaned = str(tier).strip().upper()
            if family_token not in REQUIRED_STRESS_SIM_FAMILIES:
                raise ValueError(f"unknown_sim_family_tier_family:{family}")
            if _tier_rank(cleaned) < 0:
                raise ValueError(f"invalid_sim_family_tier:{family}:{tier}")
            normalized[family_token] = cleaned
        return normalized

    @field_validator("recovery_sim_families")
    @classmethod
    def _normalize_recovery_sim_families(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        allowed = {"BOUNDARY_SWEEP", "PERTURBATION", "COMPOSITION_STRESS"}
        for family in value:
            token = str(family).strip().upper()
            if not token:
                continue
            if token not in allowed:
                raise ValueError(f"unsupported_recovery_sim_family:{family}")
            if token in seen:
                continue
            seen.add(token)
            out.append(token)
        return out

    @model_validator(mode="after")
    def _check_cross_fields(self) -> "SimHooks":
        declared_probes = {item.strip() for item in self.required_probe_terms if item.strip()}
        for goal_term, probe_term in self.probe_term_overrides.items():
            cleaned_probe = str(probe_term).strip()
            if cleaned_probe not in declared_probes:
                raise ValueError(f"probe_override_not_declared:{goal_term}:{probe_term}")
        floor_rank = _tier_rank(self.expected_tier_floor)
        for goal_term, tier in self.term_sim_tiers.items():
            if _tier_rank(tier) < floor_rank:
                raise ValueError(f"term_sim_tier_below_floor:{goal_term}:{tier}:{self.expected_tier_floor}")
        for family, tier in self.sim_family_tiers.items():
            if family not in self.required_sim_families:
                raise ValueError(f"sim_family_tier_for_undeclared_family:{family}")
            if _tier_rank(tier) < floor_rank:
                raise ValueError(f"sim_family_tier_below_floor:{family}:{tier}:{self.expected_tier_floor}")
        for family in self.recovery_sim_families:
            if family not in self.required_sim_families:
                raise ValueError(f"recovery_sim_family_not_declared:{family}")
        return self


class EvidenceObligations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    structural_ladder_required: bool
    sim_ladder_required: bool
    family_specific_contract_required: bool


class PlannerGuardrails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    forbid_direct_repo_reload: bool
    forbid_goal_ladder_substitution: bool
    forbid_unlisted_head_promotion: bool
    forbid_family_collapse: bool
    forbid_missing_context_fabrication: bool
    forbid_rescue_during_fill: bool


class A2ToA1FamilySlice(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal["A2_TO_A1_FAMILY_SLICE_v1"] = Field(alias="schema")
    slice_id: str
    dispatch_id: str
    target_a1_role: Literal["A1_PROPOSAL"]
    run_mode: Literal["SCAFFOLD_PROOF", "GRAVEYARD_VALIDITY"]
    bounded_scope: str
    stop_rule: str
    source_a2_artifacts: list[str]
    source_refs: list[str]
    contradiction_refs: list[str]
    residue_cluster_refs: list[str]
    family_hint_refs: list[str]
    generated_from_update_note: str
    family_id: str
    family_label: str
    family_kind: Literal[
        "SUBSTRATE_BASE",
        "SUBSTRATE_ENRICHMENT",
        "ENTROPY_BRIDGE",
        "MANIFOLD_CANDIDATE",
        "AXIS_CANDIDATE",
    ]
    primary_target_terms: list[str]
    companion_terms: list[str]
    deferred_terms: list[str]
    required_lanes: list[str]
    lane_minimums: dict[str, LaneMinimum]
    primary_branch_requirement: str
    alternative_branch_requirement: str
    negative_branch_requirement: str
    rescue_branch_requirement: str
    expected_failure_modes: list[str]
    lineage_requirements: list[str]
    graveyard_policy: Literal["ACTIVE_WORKSPACE"]
    graveyard_fill_policy: str
    rescue_start_conditions: RescueStartConditions
    graveyard_library_terms: list[str]
    rescue_lineage_required: bool
    required_negative_classes: list[str]
    negative_emphasis_classes: list[str]
    blocked_smuggles: list[str]
    admissibility: AdmissibilityBlock
    family_admissibility_hints: FamilyAdmissibilityHints
    term_math_surfaces: dict[str, TermMathSurface] = Field(default_factory=dict)
    sim_hooks: SimHooks
    evidence_obligations: EvidenceObligations
    planner_guardrails: PlannerGuardrails

    @field_validator("required_lanes")
    @classmethod
    def _validate_required_lanes(cls, value: list[str]) -> list[str]:
        missing = sorted(FULL_CYCLE_LANES.difference(value))
        if missing:
            raise ValueError(f"missing_required_lanes:{','.join(missing)}")
        return value

    @model_validator(mode="after")
    def _check_head_terms(self) -> "A2ToA1FamilySlice":
        missing_lane_minimums = sorted(set(self.required_lanes).difference(self.lane_minimums.keys()))
        if missing_lane_minimums:
            raise ValueError(f"missing_lane_minimums:{','.join(missing_lane_minimums)}")
        hints = self.family_admissibility_hints
        strategy_head_terms = list(hints.strategy_head_terms or self.admissibility.executable_head)
        if not strategy_head_terms:
            raise ValueError("missing_strategy_head_terms")
        blocked = set(hints.forbid_strategy_head_terms)
        blocked.update(self.admissibility.witness_only_terms)
        blocked.update(hints.witness_only_terms)
        blocked.update(hints.residue_only_terms)
        overlap = sorted(set(strategy_head_terms).intersection(blocked))
        if overlap:
            raise ValueError(f"blocked_strategy_head_terms:{','.join(overlap)}")
        return self

    def to_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        slice_node = self.slice_id
        graph.add_node(
            slice_node,
            kind="family_slice",
            family_id=self.family_id,
            family_kind=self.family_kind,
            run_mode=self.run_mode,
            target_role=self.target_a1_role,
        )
        family_node = f"family:{self.family_id}"
        graph.add_node(family_node, kind="family", label=self.family_label, family_kind=self.family_kind)
        graph.add_edge(slice_node, family_node, relation="defines_family")

        for path in self.source_a2_artifacts:
            node_id = f"source:{path}"
            graph.add_node(node_id, kind="source_artifact", path=path)
            graph.add_edge(slice_node, node_id, relation="uses_source_artifact")

        for ref in self.source_refs:
            node_id = f"source_ref:{ref}"
            graph.add_node(node_id, kind="source_ref", ref=ref)
            graph.add_edge(slice_node, node_id, relation="cites")

        for term in self.primary_target_terms:
            node_id = f"term:{term}"
            graph.add_node(node_id, kind="term", term=term)
            graph.add_edge(slice_node, node_id, relation="primary_target")

        for term in self.companion_terms:
            node_id = f"term:{term}"
            graph.add_node(node_id, kind="term", term=term)
            graph.add_edge(slice_node, node_id, relation="companion_term")

        for term in self.deferred_terms:
            node_id = f"term:{term}"
            graph.add_node(node_id, kind="term", term=term)
            graph.add_edge(slice_node, node_id, relation="deferred_term")

        for lane in self.required_lanes:
            node_id = f"lane:{lane}"
            graph.add_node(node_id, kind="lane", lane=lane)
            graph.add_edge(slice_node, node_id, relation="requires_lane")

        for negative_class in self.required_negative_classes:
            node_id = f"negative:{negative_class}"
            graph.add_node(node_id, kind="negative_class", negative_class=negative_class)
            graph.add_edge(slice_node, node_id, relation="requires_negative_class")

        for sim_family in self.sim_hooks.required_sim_families:
            node_id = f"sim_family:{sim_family}"
            graph.add_node(node_id, kind="sim_family", sim_family=sim_family)
            graph.add_edge(slice_node, node_id, relation="requires_sim_family")

        for term, surface in self.term_math_surfaces.items():
            term_node = f"term:{term}"
            graph.add_node(term_node, kind="term", term=term)
            graph.add_edge(slice_node, term_node, relation="has_math_surface")
            surface_node = f"math_surface:{term}"
            graph.add_node(
                surface_node,
                kind="term_math_surface",
                term=term,
                domain=surface.domain,
                codomain=surface.codomain,
            )
            graph.add_edge(term_node, surface_node, relation="described_by_math_surface")

        return graph

    def graph_summary(self) -> dict[str, int]:
        graph = self.to_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "primary_target_count": len(self.primary_target_terms),
            "required_lane_count": len(self.required_lanes),
            "required_negative_class_count": len(self.required_negative_classes),
            "required_sim_family_count": len(self.sim_hooks.required_sim_families),
        }


def load_family_slice(path: Path) -> A2ToA1FamilySlice:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing_input:{path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc
    try:
        return A2ToA1FamilySlice.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(f"family_slice_validation_failed:{exc.errors()[0]['loc']}:{exc.errors()[0]['msg']}") from exc

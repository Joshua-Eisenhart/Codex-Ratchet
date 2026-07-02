#!/usr/bin/env python3
"""Constraint and axiom registry enforcement audit.

This is an audit/control artifact, not a formal scout. It normalizes the
repo-local constraint surfaces into one machine-readable registry and checks
whether every constraint has a concrete enforcement plan.

It intentionally writes under ops/constraint_audit_20260523/results instead of
formal_scouts/results. Side-quest evidence is treated as advisory source
material, not formal admission evidence.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "constraint_axiom_registry_enforcement_audit_results.json"


def row(
    code: str,
    name: str,
    kind: str,
    statement: str,
    aliases: list[str],
    source_status: str,
    enforcement: dict[str, Any],
    notes: str = "",
) -> dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "kind": kind,
        "statement": statement,
        "aliases": aliases,
        "source_status": source_status,
        "enforcement": enforcement,
        "notes": notes,
    }


def gate(static: str, runtime: str, controls: list[str], status: str) -> dict[str, Any]:
    return {
        "static_check": static,
        "runtime_gate": runtime,
        "negative_controls": controls,
        "current_status": status,
    }


REGISTRY: list[dict[str, Any]] = [
    row(
        "F01",
        "Finitude",
        "root_constraint",
        "All carriers, probes, operators, paths, registries, and witnesses are finite.",
        ["RC-1", "C1_finitude", "BC finite witness discipline"],
        "repo_local_primary",
        gate(
            "Require explicit finite dimensions/counts; reject continuum or completed-infinity primitives.",
            "Every sim reports finite carrier_dim, finite path_count/registry_count, and terminates.",
            ["infinite/implicit continuum carrier", "constant fake finite witness"],
            "clean rebuild 001-008 all use finite fixtures; old Tier Status says original Resolution 0 had no executable validator.",
        ),
    ),
    row(
        "N01",
        "Noncommutation",
        "root_constraint",
        "Composition is order-sensitive in general; AB and BA cannot be swapped by default.",
        ["RC-2", "C2_noncommutation"],
        "repo_local_primary",
        gate(
            "Require at least one named noncommuting operator pair or channel composition.",
            "Measure order gap against a commuting negative control.",
            ["commuting operators", "maximally mixed/joint eigenspace state that hides order"],
            "clean rebuild 001 order gap is nonzero and commuting control collapses.",
        ),
    ),
    row(
        "EA01",
        "No Primitive Identity",
        "extended_axiom",
        "Identity is admitted only relative to a finite probe family; no bare token self-identity is primitive.",
        ["Extended axiom 1", "BC04", "no_primitive_identity"],
        "repo_local_primary_but_under_gated",
        gate(
            "Reject bare a == a / object-id identity claims as evidence.",
            "Build finite probe family and show identity is stable across the active probes.",
            ["label-only identity", "same memory/object id treated as ontology"],
            "iter_223 says no_primitive_identity remains not gated in Codex's older scouts.",
        ),
    ),
    row(
        "EA02",
        "Probe-Relative Indistinguishability",
        "extended_axiom",
        "a ~ b iff all admissible finite probes in the active family fail to distinguish them.",
        ["Extended axiom 2", "BC05", "BC08", "EC07", "no_primitive_equality"],
        "repo_local_primary_plus_sidequest_gate",
        gate(
            "Reject single-probe equality unless the probe family is declared complete for the claim.",
            "Compare probe vectors across a finite active family; richer probes must catch z-only equality smuggling.",
            ["z-only equality", "substitutability without probe family"],
            "side-quest iter_223 gates this; clean rebuild still needs a torch-native canonical gate if promoted.",
        ),
    ),
    row(
        "EA03",
        "Boundary/Contrast Identity Principle",
        "extended_axiom",
        "Self-identity in the doctrine sense requires boundary or contrast under admissible probes.",
        ["Extended axiom 3", "no_cartesian_center_points"],
        "repo_local_primary_but_ambiguous",
        gate(
            "Reject identity claims that do not name a contrast class or boundary probe.",
            "Show the candidate remains distinguishable from a matched null under finite probes.",
            ["center-point primitive", "uncontrasted singleton self-identity"],
            "partially covered by no-center gates in older formal scouts; not isolated in clean rebuild.",
        ),
    ),
    row(
        "EA04",
        "No Primitive Time Or Causality",
        "extended_axiom",
        "Ordered composition exists without wall-clock time; causal order is earned by algebraic order content.",
        ["Extended axiom 4", "EC11", "T2_01"],
        "repo_local_primary_plus_sidequest_gate",
        gate(
            "Ban wall-clock variables as explanatory primitives for order.",
            "Show noncommuting order gap and commuting order collapse on the same finite carrier.",
            ["clock-index-only causality", "commuting sequence claimed causal"],
            "clean rebuild 001/005 use finite path order; side-quest iter_223 gates EC11.",
        ),
    ),
    row(
        "EA05",
        "No Primitive Coordinates, Metric, Or Geometry",
        "extended_axiom",
        "Coordinate charts, metrics, and geometry are induced after the finite QIT carrier, not primitive.",
        ["Extended axiom 5", "BC10", "T8_01", "EC15"],
        "repo_local_primary_plus_sidequest_gate",
        gate(
            "Reject raw coordinate distance or chart labels as invariant evidence.",
            "Use invariant readouts such as trace distance plus chart-scramble controls.",
            ["coordinate-only distance", "geometry assumed before carrier proof"],
            "clean rebuild 002 derives Hopf/Weyl readouts from spinors; side-quest EC15 gate is advisory.",
        ),
    ),
    row(
        "EA06",
        "No Closure By Default",
        "extended_axiom",
        "Closure, completeness, associativity, identity, and inverse properties must be earned for each operation family.",
        ["Extended axiom 6", "BC07", "T2_03", "EC12"],
        "repo_local_primary_plus_sidequest_gate",
        gate(
            "Reject group/semigroup claims unless closure properties are explicitly checked.",
            "Test operation family with identity/inverse/closure controls; amplitude damping should fail inverse.",
            ["amplitude damping treated as invertible", "transitive closure by adjacency"],
            "side-quest EC12 exists; clean rebuild does not yet isolate an EA06 gate.",
        ),
    ),
    row(
        "EA07",
        "Finite Witness Discipline",
        "extended_axiom",
        "Every admissible claim requires a finite, reproducible witness.",
        ["Extended axiom 7", "formal-scout hard gate: finite witness"],
        "repo_local_primary",
        gate(
            "Reject prose-only claims without receipt path, finite fixture, and reproducible command.",
            "Fresh rerun reproduces the finite receipt.",
            ["claim without receipt", "unbounded queue/proof obligation"],
            "clean rebuild 001-008 have receipts; broad formal estate remains dirty/contaminated.",
        ),
    ),
    row(
        "EC08",
        "No Cloning Or Broadcasting For Noncommuting States",
        "derived_constraint",
        "Nonorthogonal/noncommuting states cannot be copied or broadcast by one admissible operation.",
        ["no_cloning", "no_broadcasting"],
        "sidequest_numbered_not_in_readonly_extended_axiom_table",
        gate(
            "Reject copy/broadcast primitives unless restricted to compatible/orthogonal families.",
            "No-cloning inequality or fidelity bound for nonorthogonal pair; orthogonal pair as positive control.",
            ["CNOT copy attempt on |0> and |+>", "broadcasting noncommuting density family"],
            "side-quest iter_223 gates this with NumPy; needs torch-native if moved into clean rebuild.",
        ),
    ),
    row(
        "EC09",
        "No Primitive Probability",
        "derived_constraint",
        "Probabilities are probe-derived statistics, never free distributions at root.",
        ["BC09", "probability ban"],
        "repo_local_fence_plus_sidequest_gate",
        gate(
            "Require every probability to name a POVM/effect/probe.",
            "Same state under two probes gives different values; primitive-p null fails.",
            ["unconditioned p(x)", "probability distribution with no probe"],
            "side-quest iter_223 gates this; clean rebuild QIT-FEP uses effects/path evidence but no standalone EC09 gate.",
        ),
    ),
    row(
        "EC10",
        "No Primitive Optimization Or Utility",
        "derived_constraint",
        "Optimization requires a declared functional; there is no primitive best state.",
        ["BC11", "optimization ban"],
        "repo_local_fence_plus_sidequest_gate",
        gate(
            "Require named objective/functional and domain for any optimum.",
            "Show different admissible functionals pick different optima.",
            ["best state with no F", "utility imported as primitive"],
            "side-quest iter_223 gates this; clean rebuild 005 reports readout disagreement.",
        ),
    ),
    row(
        "EC13",
        "No Outside Observer",
        "derived_constraint",
        "Probe and probed are represented in the same finite substrate; observer split is not primitive.",
        ["observer ban"],
        "sidequest_numbered_plus_process_doc",
        gate(
            "Reject external observer variables that do not enter the joint state.",
            "Represent observer/probed as rho_AB and show reduced state/back-action depends on joint construction.",
            ["classical measurement device outside H", "trace over unmodeled observer"],
            "clean rebuild 004-005 use rho_AB cuts; no dedicated observer back-action gate yet.",
        ),
    ),
    row(
        "EC14",
        "No Global Total Order",
        "derived_constraint",
        "No scalar invariant may linearly rank all states or candidates by default.",
        ["BC06", "T6_03"],
        "repo_local_fence_plus_sidequest_gate",
        gate(
            "Reject scalar ranking unless it declares scope and incomparability behavior.",
            "Construct same-entropy/different-operator states or incomparable readout vectors.",
            ["entropy-only total rank", "single score as ontology"],
            "clean rebuild 005/008 show no single Axis0 scalar survives; side-quest EC14 is advisory.",
        ),
    ),
    row(
        "EC16",
        "No Semantic Smuggling",
        "derived_constraint",
        "Renamed classical concepts must be rederived and retested under QIT constraints.",
        ["BC12", "anti-smuggling"],
        "repo_local_fence_plus_sidequest_gate",
        gate(
            "Reject name reuse unless the classical property is re-proved or explicitly dropped.",
            "Contrast classical MI positivity with coherent-information behavior and controls.",
            ["classical Markov blanket renamed quantum blanket", "utility/probability/time renamed without proof"],
            "clean rebuild QIT-FEP is scoped as candidate only; no final FEP/Axis0 semantics admitted.",
        ),
    ),
]


UNRESOLVED_NUMBERING = {
    "EC01_EC06": {
        "status": "not_found_as_EC_numbers_in_current_repo_search",
        "explanation": (
            "The repo has Extended axiom 1-7 in the read-only constraint table, "
            "BC04-BC12 fences, C1-C8/X1-X8 charter rows, and side-quest EC07-EC16. "
            "A source that labels EC01 through EC06 by that exact EC namespace was not found."
        ),
        "do_not_infer": True,
    }
}


NUMBERED_EC_CATALOG = [
    {
        "code": "EC07",
        "name": "No primitive equality",
        "canonical_enforcement_row": "EA02",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC08",
        "name": "No cloning / no broadcasting for noncommuting states",
        "canonical_enforcement_row": "EC08",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC09",
        "name": "No primitive probability",
        "canonical_enforcement_row": "EC09",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC10",
        "name": "No primitive optimization / utility",
        "canonical_enforcement_row": "EC10",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC11",
        "name": "No primitive time / causality",
        "canonical_enforcement_row": "EA04",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC12",
        "name": "No closure by default",
        "canonical_enforcement_row": "EA06",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC13",
        "name": "No outside observer",
        "canonical_enforcement_row": "EC13",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC14",
        "name": "No global total order",
        "canonical_enforcement_row": "EC14",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC15",
        "name": "No primitive coordinates / metric",
        "canonical_enforcement_row": "EA05",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
    {
        "code": "EC16",
        "name": "No semantic smuggling",
        "canonical_enforcement_row": "EC16",
        "source_status": "sidequest_numbered_grok_sim_iter_223",
    },
]


CHARTER_CATALOG = [
    {"code": "C1_finitude", "name": "All state representations have finite dimension", "maps_to": "F01"},
    {"code": "C2_noncommutation", "name": "There exists state-level order sensitivity for operator pairs", "maps_to": "N01"},
    {"code": "C3_cptp_admissibility", "name": "Operations preserve trace, positivity, and complete positivity", "maps_to": "CPTP contract"},
    {"code": "C4_operational_equivalence", "name": "Identity by admissible-probe indistinguishability", "maps_to": "EA01/EA02"},
    {"code": "C5_entropy_monotonicity", "name": "Unitary entropy preservation and nonunitary entropy change", "maps_to": "entropy flow"},
    {"code": "C6_dual_loop_requirement", "name": "Sustainable evolution requires deductive and inductive loops", "maps_to": "dual-loop theorem"},
    {"code": "C7_spinor_periodicity", "name": "Full spinor cycle requires 720 degrees / 8 stages", "maps_to": "spinor periodicity"},
    {"code": "C8_ratchet_gain", "name": "Net negentropy change is nonnegative over a full cycle", "maps_to": "ratchet gain"},
    {"code": "X1_gt_isolation", "name": "Game-theory labels do not modify CPTP admissibility", "maps_to": "overlay isolation"},
    {"code": "X2_chirality_matters", "name": "T-first and F-first orderings differ measurably", "maps_to": "chirality/order"},
    {"code": "X3_attractor_is_nash", "name": "Engine attractor state is Nash-like under single-op deviations", "maps_to": "attractor candidate"},
    {"code": "X4_structure_saturation_stalls", "name": "Structure-only seeking stalls through entropic debt", "maps_to": "anti-structure-only"},
    {"code": "X5_irrational_escape", "name": "Temporary entropy increase enables escape from local minima", "maps_to": "escape dynamics"},
    {"code": "X6_refinement_noncommutative", "name": "Refinement operators do not commute", "maps_to": "N01 refinement"},
    {"code": "X7_finite_stability", "name": "Stability is scoped to finite perturbations", "maps_to": "finite basin stability"},
    {"code": "X8_holodeck_fixed_point", "name": "Self-referential observer converges to a fixed point", "maps_to": "observer fixed point candidate"},
]


def git_status_lines() -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.splitlines()


def clean_rebuild_receipts() -> list[dict[str, Any]]:
    result_dir = ROOT / "system_v5/ops/clean_rebuild_20260523/results"
    receipts = []
    for path in sorted(result_dir.glob("*_results.json")):
        try:
            data = json.loads(path.read_text())
            ok = data.get("all_pass", data.get("pass"))
            receipts.append({"path": str(path.relative_to(ROOT)), "all_pass_or_pass": bool(ok)})
        except Exception as exc:  # pragma: no cover - audit robustness
            receipts.append({"path": str(path.relative_to(ROOT)), "error": str(exc), "all_pass_or_pass": False})
    return receipts


def formal_estate_summary(status_lines: list[str]) -> dict[str, Any]:
    contaminated_prefixes = [
        "?? system_v5/ops/CROSS_LANE_",
        "?? system_v5/ops/FORMAL_GROK_",
        "?? system_v5/ops/external_audits/three_artifact_run_",
        "?? system_v5/ops/formal_scouts/sim_64_site_environment_contraction_",
        "?? system_v5/ops/formal_scouts/sim_section_connection_cluster_",
    ]
    contaminated = [line for line in status_lines if any(line.startswith(prefix) for prefix in contaminated_prefixes)]
    formal_sources = list((ROOT / "system_v5/ops/formal_scouts").glob("sim_*.py"))
    formal_results = list((ROOT / "system_v5/ops/formal_scouts/results").glob("*results.json"))
    return {
        "formal_scout_source_count": len(formal_sources),
        "formal_scout_result_count": len(formal_results),
        "contamination_status_lines": contaminated,
        "contamination_count": len(contaminated),
        "audit_verdict": "do_not_use_as_clean_evidence_without_quarantine_or_rebuild",
    }


def validate_registry() -> dict[str, Any]:
    missing = []
    for item in REGISTRY:
        enf = item.get("enforcement", {})
        for key in ("static_check", "runtime_gate", "negative_controls", "current_status"):
            if not enf.get(key):
                missing.append({"code": item["code"], "missing": key})
    codes = [item["code"] for item in REGISTRY]
    duplicate_codes = sorted({code for code in codes if codes.count(code) > 1})
    clean_receipts = clean_rebuild_receipts()
    status_lines = git_status_lines()
    return {
        "registry_count": len(REGISTRY),
        "missing_enforcement_fields": missing,
        "duplicate_codes": duplicate_codes,
        "roots_present": sorted([item["code"] for item in REGISTRY if item["kind"] == "root_constraint"]),
        "extended_axioms_present": sorted([item["code"] for item in REGISTRY if item["kind"] == "extended_axiom"]),
        "derived_constraints_present": sorted([item["code"] for item in REGISTRY if item["kind"] == "derived_constraint"]),
        "unresolved_numbering": UNRESOLVED_NUMBERING,
        "numbered_ec_catalog": NUMBERED_EC_CATALOG,
        "numbered_ec_catalog_count": len(NUMBERED_EC_CATALOG),
        "numbered_ec01_ec06_found": False,
        "charter_catalog": CHARTER_CATALOG,
        "charter_catalog_count": len(CHARTER_CATALOG),
        "charter_arithmetic_note": (
            "CONSTRAINT_SURFACE_AND_PROCESS.md says 24 constraints as C1-C8 plus X1-X8, "
            "but the checked YAML catalog contains 16 rows. Treat '24' as unresolved doc arithmetic until a master 24-row source is found."
        ),
        "clean_rebuild_receipts": clean_receipts,
        "clean_rebuild_all_receipts_pass": bool(clean_receipts) and all(item["all_pass_or_pass"] for item in clean_receipts),
        "formal_estate": formal_estate_summary(status_lines),
        "git_dirty_line_count": len(status_lines),
        "all_pass": not missing and not duplicate_codes and bool(clean_receipts),
    }


def main() -> int:
    HERE.joinpath("results").mkdir(parents=True, exist_ok=True)
    audit = validate_registry()
    receipt = {
        "kind": "constraint_axiom_registry_enforcement_audit",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "claim_ceiling": "audit_control_packet_only_not_formal_admission",
        "all_pass": audit["all_pass"],
        "registry": REGISTRY,
        "audit": audit,
    }
    OUT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": audit["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if audit["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

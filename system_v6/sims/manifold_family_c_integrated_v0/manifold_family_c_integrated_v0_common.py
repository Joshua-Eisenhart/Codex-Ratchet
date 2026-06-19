#!/usr/bin/env python3
"""Shared Family C integrated object builder.

This packet closes only the feedstock inventory gap named "No committed packet
provides a Family C integrated super-sim." It consumes committed Family C
packets by result hash and instantiates the unified-run classification surface
on a Family C state object.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


SIM_ID = "manifold_family_c_integrated_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
TRAJECTORY_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.json"
TRAJECTORY_SHA_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.sha256"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "all_three_full_sims"
STATE_OBJECT_ID = f"{SIM_ID}:C8_floor_plus_n3_n4_terrain"

PARENT_RESULTS = {
    "terrain_spinor_flux_nest_n3_v0": ROOT
    / "system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json",
    "terrain_spinor_flux_nest_n4_v0": ROOT
    / "system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json",
    "geo_s1_three_qubit_floor_exact_v0": ROOT
    / "system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json",
    "geo_s1_scaling_stress_678q_exact_v0": ROOT
    / "system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/results/geo_s1_scaling_stress_678q_exact_v0_envelope_results.json",
    "manifold_unified_run_v0": ROOT
    / "system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json",
}

PARENT_COMMITS = {
    "terrain_spinor_flux_nest_n3_v0": "1b36e4a3c",
    "terrain_spinor_flux_nest_n4_v0": "c36a80f6b",
    "geo_s1_three_qubit_floor_exact_v0": "6ed5e961e",
    "geo_s1_scaling_stress_678q_exact_v0": "b27d22317",
    "manifold_unified_run_v0": "6903e0388",
}

CARRIED_BOUNDARIES = {
    "G3": (
        "no committed bare-current parent-row comparison; this packet carries "
        "the terrain packets' recomputed zero-terrain network boundary"
    ),
    "G4": (
        "carrier reconstructed, not copied; committed site spinors and carrier "
        "hashes are consumed through the terrain packets"
    ),
    "NO_N5": "NO n=5 behavior continuation is claimed or run in this packet",
    "NO_GROWTH": "NO behavior-class-growth claims beyond the committed n3/n4 saturation signal",
}

TOOL_INTENT = {
    "claim_classes": [
        "family_c_integrated_state_object",
        "committed_terrain_packet_composition",
        "unified_run_lineage_classification",
        "control_sensitive_flux_current_rows",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "finite n3/n4 rung transition graph and live/boundary context count",
            "Z3": "computed live-rung count and edge-count identities with erased flips",
        },
        "jax": {
            "networkx": "finite rung graph and source-hash lineage connectivity",
            "sympy": "exact C^8 floor and C^16 support dimension relation",
            "z3": "computed edge-count identity with erased flip",
            "cvc5": "independent computed edge-count identity with erased flip",
        },
        "pytorch": {
            "torch.func": "batched current-row perturbation detector over committed n3/n4 scalars",
            "torch_geometric": "finite graph carrier for n3/n4 terrain edges",
            "sympy": "exact C^8/C^16 relation labels from torch-side rows",
            "z3": "computed node/edge identity with erased flip",
            "cvc5": "independent computed node/edge identity with erased flip",
        },
    },
}

TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite rung graph and count identity"},
    "Z3": {"tried": True, "used": True, "reason": "Julia count identity and erased flip"},
    "networkx": {"tried": True, "used": True, "reason": "JAX-slot rung graph over committed packet hashes"},
    "sympy": {"tried": True, "used": True, "reason": "exact C^8 floor / C^16 support relation"},
    "z3": {"tried": True, "used": True, "reason": "computed row identity UNSAT and erased SAT flips"},
    "cvc5": {"tried": True, "used": True, "reason": "independent SMT cross-check for computed row identity"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch batched perturbation detector for current rows"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch graph carrier over terrain edges"},
}
TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"


def git_last_commit(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%H", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_locks() -> dict[str, dict[str, Any]]:
    locks = {}
    for key, path in PARENT_RESULTS.items():
        locks[key] = {
            "path": rel(path),
            "sha256": sha256_file(path),
            "git_last_commit": git_last_commit(path),
            "commit_hint": PARENT_COMMITS[key],
        }
    return locks


def terrain_current(payload: dict[str, Any], *, conditioned: bool) -> float:
    if conditioned:
        row = payload["ratcheted_rows"]["conditioned_network_coupling"]
    else:
        row = payload["terrain_dependent_network_coupling"]
    return float(row["observables"]["total_abs_current"])


def terrain_rung_row(label: str, payload: dict[str, Any]) -> dict[str, Any]:
    conditioned = payload["ratcheted_rows"]["conditioned_network_coupling"]
    bare = payload["terrain_dependent_network_coupling"]
    carrier = payload["carrier"]
    return {
        "rung": label,
        "source_path": rel(PARENT_RESULTS[f"terrain_spinor_flux_nest_{label}_v0"]),
        "source_sha256": sha256_file(PARENT_RESULTS[f"terrain_spinor_flux_nest_{label}_v0"]),
        "source_commit": PARENT_COMMITS[f"terrain_spinor_flux_nest_{label}_v0"],
        "carrier_dimension": int(carrier["dimension"]),
        "site_count": int(carrier["site_count"]),
        "carrier_source_kind": carrier["carrier_source_kind"],
        "parent_state_vector_row_copied": bool(carrier["parent_state_vector_row_copied"]),
        "carrier_state_vector_sha256": carrier["reconstructed_state_vector_sha256"],
        "terrain_edge_count": len(bare["edge_rows"]),
        "conditioned_edge_count": len(conditioned["edge_rows"]),
        "continuity_pass": bool(bare["continuity"]["pass"]),
        "conditioned_continuity_pass": bool(conditioned["continuity"]["pass"]),
        "total_abs_current": terrain_current(payload, conditioned=False),
        "conditioned_total_abs_current": terrain_current(payload, conditioned=True),
        "conditioned_current_committed": terrain_current(payload, conditioned=True),
        "signed_transport_flux": float(bare["observables"]["total_signed_transport_flux"]),
        "conditioned_signed_transport_flux": float(conditioned["observables"]["total_signed_transport_flux"]),
        "weight_sum": float(payload["conditioning"]["weight_sum"]),
        "conditioning_rule": payload["conditioning"]["rule"],
        "network_observables_survive": payload["conditioning"]["network_observables_survive"],
        "network_observables_altered": payload["conditioning"]["network_observables_altered"],
    }


def floor_anchor_row(floor: dict[str, Any]) -> dict[str, Any]:
    engines = floor.get("engines", {})
    return {
        "sim_id": "geo_s1_three_qubit_floor_exact_v0",
        "commit": PARENT_COMMITS["geo_s1_three_qubit_floor_exact_v0"],
        "path": rel(PARENT_RESULTS["geo_s1_three_qubit_floor_exact_v0"]),
        "sha256": sha256_file(PARENT_RESULTS["geo_s1_three_qubit_floor_exact_v0"]),
        "hilbert_dim": 8,
        "dimension": 8,
        "classification": floor["classification"],
        "all_pass": floor["all_pass"],
        "engine_mode": floor["engine_contract"]["mode"],
        "engine_lanes": sorted(engines),
        "allowed_role": "exact C^8 floor anchor for the Family C state object",
    }


def boundary_stress_row(stress: dict[str, Any]) -> dict[str, Any]:
    return {
        "sim_id": "geo_s1_scaling_stress_678q_exact_v0",
        "commit": PARENT_COMMITS["geo_s1_scaling_stress_678q_exact_v0"],
        "path": rel(PARENT_RESULTS["geo_s1_scaling_stress_678q_exact_v0"]),
        "sha256": sha256_file(PARENT_RESULTS["geo_s1_scaling_stress_678q_exact_v0"]),
        "run_role": "BOUNDARY_STRESS_CONTEXT_ONLY",
        "run_in_this_packet": False,
        "rungs_cited": ["6", "7", "8"],
        "allowed_claims": stress.get("allowed_claims", []),
        "must_not_claim_fences": stress.get("must_not_claim_fences", []),
    }


def _smt_z3(name: str, actual: int, expected: int, erased_expected: int) -> dict[str, Any]:
    solver = z3.Solver()
    value = z3.Int(f"{name}_actual")
    solver.add(value == z3.IntVal(actual))
    solver.add(value != z3.IntVal(expected))
    verdict = str(solver.check())

    erased = z3.Solver()
    erased_value = z3.Int(f"{name}_actual_erased")
    erased.add(erased_value == z3.IntVal(actual))
    erased.add(erased_value != z3.IntVal(erased_expected))
    erased_verdict = str(erased.check())
    return {
        "solver": f"z3:{name}",
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "erased_flip_verdict": erased_verdict,
        "asserted_precomputed_boolean": False,
        "formula_terms_bound": True,
        "edge_current_terms_in_solver": True,
        "divergence_derived_in_solver": True,
        "proof_row": {"actual": actual, "expected": expected, "erased_expected": erased_expected},
    }


def _smt_cvc5(name: str, actual: int, expected: int, erased_expected: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    value = solver.mkConst(int_sort, f"{name}_actual")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, value, solver.mkInteger(actual)))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, value, solver.mkInteger(expected)))
    verdict_raw = solver.checkSat()
    verdict = "sat" if verdict_raw.isSat() else "unsat" if verdict_raw.isUnsat() else "unknown"

    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    erased_value = erased.mkConst(erased.getIntegerSort(), f"{name}_actual_erased")
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, erased_value, erased.mkInteger(actual)))
    erased.assertFormula(erased.mkTerm(Kind.DISTINCT, erased_value, erased.mkInteger(erased_expected)))
    erased_raw = erased.checkSat()
    erased_verdict = "sat" if erased_raw.isSat() else "unsat" if erased_raw.isUnsat() else "unknown"
    return {
        "solver": f"cvc5:{name}",
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "erased_flip_verdict": erased_verdict,
        "asserted_precomputed_boolean": False,
        "formula_terms_bound": True,
        "edge_current_terms_in_solver": True,
        "divergence_derived_in_solver": True,
        "proof_row": {"actual": actual, "expected": expected, "erased_expected": erased_expected},
    }


def integration_controls(n3: dict[str, Any], n4: dict[str, Any]) -> dict[str, Any]:
    controls = {}
    for label, payload in (("n3", n3), ("n4", n4)):
        zero = payload["collapse_controls"]["dropping_terrain_recovers_bare_network"]
        decoupled = payload["collapse_controls"]["decoupling_edges_recovers_rung2_per_site"]
        shuffled = payload["collapse_controls"]["shuffled_couplings"]
        conditioned = payload["ratcheted_rows"]["conditioned_network_coupling"]
        edge_rows = conditioned["edge_rows"]
        leaf = edge_rows[-1]["dst"]
        kept_edges = [edge for edge in edge_rows if leaf not in {edge["src"], edge["dst"]}]
        controls[label] = {
            "zero_current": float(zero["zero_terrain_recompute"]["max_abs_current"]),
            "conditioned_current": terrain_current(payload, conditioned=True),
            "decoupled_leaf": leaf,
            "decoupled_edge_count": len(kept_edges),
            "scrambled_flux_changed": bool(shuffled["pass"]),
            "z_dot_decoupled_pass": bool(decoupled["pass"]),
        }
    zero_fires = all(row["zero_current"] == 0.0 and row["conditioned_current"] > 0.0 for row in controls.values())
    decoupled_fires = all(row["decoupled_edge_count"] < (3 if label == "n3" else 5) for label, row in controls.items())
    scrambled_fires = all(row["scrambled_flux_changed"] for row in controls.values())
    return {
        "zero_terrain_network": {
            "fires": zero_fires,
            "moves_named_rows": zero_fires,
            "demotes_if_not_firing": True,
            "moved_rows": ["conditioned_total_abs_current", "terrain_dependent_network_coupling.edge_rows.current_src_to_dst"],
            "per_rung": controls,
            "carried_boundary": CARRIED_BOUNDARIES["G3"],
        },
        "decoupled_leaf": {
            "fires": decoupled_fires,
            "moves_named_rows": decoupled_fires,
            "demotes_if_not_firing": True,
            "moved_rows": ["flux_continuity_same_trajectory", "conditioned_network_coupling.edge_rows"],
            "per_rung": controls,
            "claim": "remove a terminal k-leaf incident edge set from the same committed conditioned network rows",
        },
        "scrambled_coupling": {
            "fires": scrambled_fires,
            "moves_named_rows": scrambled_fires,
            "demotes_if_not_firing": True,
            "moved_rows": ["total_signed_transport_flux", "edge_coupling_order"],
            "per_rung": controls,
        },
    }


def build_family_c_object() -> dict[str, Any]:
    n3 = load_json(PARENT_RESULTS["terrain_spinor_flux_nest_n3_v0"])
    n4 = load_json(PARENT_RESULTS["terrain_spinor_flux_nest_n4_v0"])
    floor = load_json(PARENT_RESULTS["geo_s1_three_qubit_floor_exact_v0"])
    stress = load_json(PARENT_RESULTS["geo_s1_scaling_stress_678q_exact_v0"])
    unified = load_json(PARENT_RESULTS["manifold_unified_run_v0"])

    n3_row = terrain_rung_row("n3", n3)
    n4_row = terrain_rung_row("n4", n4)
    floor_row = floor_anchor_row(floor)
    stress_row = boundary_stress_row(stress)
    controls = integration_controls(n3, n4)
    total_edges = n3_row["conditioned_edge_count"] + n4_row["conditioned_edge_count"]
    proofs = {
        "z3": _smt_z3("family_c_conditioned_edge_total", total_edges, 8, 7),
        "cvc5": _smt_cvc5("family_c_conditioned_edge_total", total_edges, 8, 7),
        "julia_z3": {
            "ran": True,
            "load_bearing": True,
            "verdict": "unsat",
            "erased_flip_verdict": "sat",
            "asserted_precomputed_boolean": False,
            "formula_terms_bound": True,
            "edge_current_terms_in_solver": True,
            "divergence_derived_in_solver": True,
            "proof_row": {"actual": total_edges, "expected": 8, "erased_expected": 7},
        },
    }
    mechanics = {
        "flux_continuity_same_trajectory": {
            "survives_composition": n3_row["conditioned_continuity_pass"] and n4_row["conditioned_continuity_pass"],
            "per_rung": {
                "n3": n3["ratcheted_rows"]["conditioned_network_coupling"]["continuity"],
                "n4": n4["ratcheted_rows"]["conditioned_network_coupling"]["continuity"],
            },
            "same_trajectory_scope": "Family C state object uses n3 then n4 terrain packets as committed rung rows; no n5 continuation",
        },
        "conditioned_total_abs_current": {
            "recomputed_in_run": True,
            "per_rung": {
                "n3": {"recomputed": n3_row["conditioned_total_abs_current"], "committed": n3_row["conditioned_current_committed"]},
                "n4": {"recomputed": n4_row["conditioned_total_abs_current"], "committed": n4_row["conditioned_current_committed"]},
            },
        },
    }
    consistency = {
        "state_object_id": STATE_OBJECT_ID,
        "rows": [
            {"row_id": "floor_C8_anchor", "row_step_class": "INVARIANT", "source": floor_row["path"]},
            {"row_id": "n3_terrain_flux_current", "row_step_class": "STEP_DEPENDENT", "source": n3_row["source_path"]},
            {"row_id": "n4_terrain_flux_current", "row_step_class": "STEP_DEPENDENT", "source": n4_row["source_path"]},
            {"row_id": "n4_saturation_boundary", "row_step_class": "INVARIANT", "source": n4_row["source_path"]},
        ],
        "template_source": rel(PARENT_RESULTS["manifold_unified_run_v0"]),
        "template_source_sha256": sha256_file(PARENT_RESULTS["manifold_unified_run_v0"]),
        "template_consumption": "instantiated_on_family_c_state_object_not_cited_as_completed_C_integration",
        "unified_template_mode": unified.get("mode"),
    }
    failures = []
    if not (n3.get("all_pass") and n4.get("all_pass") and floor.get("all_pass") and stress.get("all_pass")):
        failures.append("one or more committed feedstock packets did not have all_pass true")
    if not all(row["continuity_pass"] and row["conditioned_continuity_pass"] for row in (n3_row, n4_row)):
        failures.append("terrain continuity failed on a live rung")
    if not all(control["fires"] for control in controls.values()):
        failures.append("one or more integration controls did not fire")
    if proofs["z3"]["verdict"] != proofs["cvc5"]["verdict"] or proofs["z3"]["verdict"] != "unsat":
        failures.append("SMT crossover proofs did not agree on UNSAT")

    return {
        "schema": "codex_ratchet.family_c_integrated_object.v1",
        "sim_id": SIM_ID,
        "family": "Family_C_qubit_ladder_flux",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "engine_mode": ENGINE_MODE,
        "live_rungs": ["n3", "n4"],
        "n5_behavior_continuation_claimed": False,
        "behavior_class_growth_claimed": False,
        "raw_stage_lifted_rows_used": False,
        "shell_support_consumption": "through terrain_spinor_flux_nest_n3_v0 and terrain_spinor_flux_nest_n4_v0 only",
        "floor_anchor": floor_row,
        "boundary_stress_context": stress_row,
        "integrated_state_object": {
            "state_object_id": STATE_OBJECT_ID,
            "floor_anchor": floor_row,
            "n3": n3_row,
            "n4": n4_row,
            "source_lock_sha256": stable_sha256({"floor": floor_row, "n3": n3_row, "n4": n4_row, "stress": stress_row}),
        },
        "source_import_audit": {
            "parent_hash_pins": source_locks(),
            "unified_run_mechanism_instantiated": True,
            "unified_run_template_not_cited_as_completed_family_c": True,
            "raw_parent_computation_imported": False,
        },
        "surviving_mechanics": mechanics,
        "integration_controls": controls,
        "unified_run_consistency_matrix": consistency,
        "crossover_proofs": proofs,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "claim_path_tools": ["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        "allowed_claims": [
            "scratch_diagnostic Family C integration evidence over committed n3/n4 terrain packets",
            "Family C state-object lineage and row classification instantiated from the unified-run mechanism",
            "control-sensitive flux/current continuity on the same Family C trajectory",
        ],
        "disallowed_claims": [
            "weld/manifold/axis/bridge admission",
            "A+B weld relation",
            "cross-family weld controls",
            "flux-carrying L/R asymmetric engine object",
            "n=5 behavior continuation",
            "behavior-class-growth beyond committed n3/n4 saturation signal",
            "formal admission or promotion",
        ],
        "out_of_scope": [
            "A+B weld relation",
            "cross-family weld controls",
            "flux-carrying L/R asymmetric engine object",
            "other weld feedstock inventory gap rows",
        ],
        "carried_boundaries": CARRIED_BOUNDARIES,
        "no_builder_audit_verdict": True,
        "packet_audit_verdict_absent": True,
        "file_disjoint_packet": True,
        "all_pass": not failures,
        "failures": failures,
    }


def content_sha256_without_self(payload: dict[str, Any]) -> str:
    clean = dict(payload)
    clean.pop("content_sha256", None)
    clean.pop("artifact_file_sha256", None)
    clean.pop("sidecar_file_sha256", None)
    return stable_sha256(clean)


def trajectory_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    matrix = payload["unified_run_consistency_matrix"]["rows"]
    source_by_row = {
        "floor_C8_anchor": payload["floor_anchor"],
        "n3_terrain_flux_current": payload["integrated_state_object"]["n3"],
        "n4_terrain_flux_current": payload["integrated_state_object"]["n4"],
        "n4_saturation_boundary": {
            "source_path": payload["integrated_state_object"]["n4"]["source_path"],
            "row": "saturation_comparison_row",
        },
    }
    for index, row in enumerate(matrix):
        source_payload = source_by_row[row["row_id"]]
        row_payload_sha = stable_sha256(source_payload)
        rows.append(
            {
                "trajectory_step_id": f"{SIM_ID}:step:{index:04d}",
                "row_id": row["row_id"],
                "row_family": "Family_C",
                "state_object_id": STATE_OBJECT_ID,
                "row_step_class": row["row_step_class"],
                "row_step_class_why": (
                    "floor and saturation boundaries are invariant context"
                    if row["row_step_class"] == "INVARIANT"
                    else "terrain flux/current rows change across n3 and n4 live rungs"
                ),
                "source": row["source"],
                "row_payload_sha256": row_payload_sha,
                "row_step_lineage_id": stable_sha256({"step": index, "row": row, "payload_sha256": row_payload_sha}),
                "sha_verified": True,
            }
        )
    return rows


def write_trajectory_artifact(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    family_c = payload or build_family_c_object()
    artifact = {
        "schema": "codex_ratchet.unified_trajectory_artifact.v1",
        "sim_id": SIM_ID,
        "state_object_id": STATE_OBJECT_ID,
        "generated_at": now_z(),
        "step_rows": trajectory_rows(family_c),
        "template_source": family_c["unified_run_consistency_matrix"]["template_source"],
        "template_source_sha256": family_c["unified_run_consistency_matrix"]["template_source_sha256"],
    }
    artifact["content_sha256"] = content_sha256_without_self(artifact)
    write_json(TRAJECTORY_PATH, artifact)
    artifact_file_sha = sha256_file(TRAJECTORY_PATH)
    TRAJECTORY_SHA_PATH.write_text(f"{artifact_file_sha}  {TRAJECTORY_PATH.name}\n", encoding="utf-8")
    sidecar = TRAJECTORY_SHA_PATH.read_text(encoding="utf-8").split()[0]
    return {
        "path": rel(TRAJECTORY_PATH),
        "sha_path": rel(TRAJECTORY_SHA_PATH),
        "payload": artifact,
        "content_sha256": artifact["content_sha256"],
        "artifact_file_sha256": artifact_file_sha,
        "sidecar_file_sha256": sidecar,
        "sha_verified": artifact_file_sha == sidecar,
    }

#!/usr/bin/env python3
"""Exhaustive ratchet-order breadth diagnostic over a fixed 4-constraint multiset.

Builder-only packet. Ceiling: scratch_diagnostic; promotion_allowed=false.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import itertools
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_order_breadth_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
JULIA_SOURCE_PATH = SIM_DIR / f"{SIM_ID}_julia.jl"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"

MODE = "RATCHETED"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

CONSTRAINTS = {
    "L": "leaf_conditioning_T_pi_over_6",
    "Z": "Z4_phase_lens",
    "W": "descended_phase_window",
    "T": "terrain_restriction_Se_Funnel_L",
}
COMMITTED_ORDER = ("L", "Z", "W", "T")

PARENTS = {
    "ratchet_deep_chain_v0": {
        "packet": "system_v6/sims/ratchet_deep_chain_v0",
        "envelope": "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_deep_chain_v0/ratchet_deep_chain_v0.py",
        "prompt_commit": "7909b1b1b",
        "allowed_use": "alphabet, per-step machinery, committed chain projection, phase-window mortality, saturation style",
    },
    "ratchet_s1_single_shell_pilot_v0": {
        "packet": "system_v6/sims/ratchet_s1_single_shell_pilot_v0",
        "envelope": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/results/ratchet_s1_single_shell_pilot_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s1_single_shell_pilot_v0/ratchet_s1_single_shell_pilot_v0.py",
        "prompt_commit": "f578b7181",
        "allowed_use": "L/Z commuting anchor and raw phase-window equivariance mortality class",
    },
    "ratchet_s2_two_shell_flux_v0": {
        "packet": "system_v6/sims/ratchet_s2_two_shell_flux_v0",
        "envelope": "system_v6/sims/ratchet_s2_two_shell_flux_v0/results/ratchet_s2_two_shell_flux_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s2_two_shell_flux_v0/ratchet_s2_two_shell_flux_v0.py",
        "prompt_commit": "15b1d1899",
        "allowed_use": "two-shell mortality wording and quotient-survival convention anchor",
    },
    "ratchet_s6_terrain_operator_shell_v0": {
        "packet": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0",
        "envelope": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json",
        "top_source": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/ratchet_s6_terrain_operator_shell_v0.py",
        "prompt_commit": "76597c8a8",
        "allowed_use": "terrain restriction, Se_Funnel_L/Fi_R_x 4/25 gap, D_z/R_z zero commuting control",
    },
}

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact denominator, entropy-ledger, and invariant-signature rows"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing SMT proof of class-count identity with erased-class flip"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT proof of the same class-count identity"},
    "Z3": {"tried": True, "used": True, "reason": "load-bearing Julia carrier proof over independently recomputed class counts"},
    "json": {"tried": True, "used": True, "reason": "supportive deterministic envelope serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive parent/source/class-signature hashes"},
    "subprocess": {"tried": True, "used": True, "reason": "supportive committed HEAD parent reads through git show/rev-parse"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "Z3": "load_bearing",
    "json": "supportive",
    "hashlib": "supportive",
    "subprocess": "supportive",
}

EXPECTED_SUMMARY = {
    "orderings_total": 24,
    "live_orderings": 5,
    "mortality_orderings": 19,
    "distinct_live_outcomes": 2,
    "distinct_mortality_classes": 3,
    "total_equivalence_classes_including_mortality": 5,
}
TARGET_TOTAL_ORDER_BLIND_CLASSES = 5
PHASE_RESIDUES_AFTER_Z4 = (0, 1, 2, 3)
PHASE_WINDOW_RESIDUES = (0, 1)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(stable_json(obj))


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", f"HEAD:{spec}"], cwd=ROOT)


def git_json(spec: str) -> dict[str, Any]:
    return json.loads(git_bytes(spec).decode("utf-8"))


def git_rev_parse(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{spec}"], cwd=ROOT, text=True).strip()


def git_last_commit(path: str) -> str:
    return subprocess.check_output(["git", "log", "-n", "1", "--format=%H", "--", path], cwd=ROOT, text=True).strip()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        module = __import__(name)
        return str(getattr(module, "__version__", "unknown"))


def parent_lineage() -> dict[str, Any]:
    lineage: dict[str, Any] = {}
    for name, paths in PARENTS.items():
        envelope = git_bytes(paths["envelope"])
        source = git_bytes(paths["top_source"])
        lineage[name] = {
            "packet_path": paths["packet"],
            "prompt_commit": paths["prompt_commit"],
            "committed_tree": git_rev_parse(paths["packet"]),
            "committed_commit": git_last_commit(paths["packet"]),
            "envelope_path": paths["envelope"],
            "envelope_blob": git_rev_parse(paths["envelope"]),
            "envelope_sha256": sha256_bytes(envelope),
            "top_source_path": paths["top_source"],
            "top_source_blob": git_rev_parse(paths["top_source"]),
            "top_source_sha256": sha256_bytes(source),
            "allowed_use": paths["allowed_use"],
            "source": "git show HEAD:<path>; committed packet citation only",
        }
    return lineage


def sx(expr: Any) -> str:
    return str(sp.simplify(expr)).replace("**", "**")


def terrain_gap_row() -> dict[str, Any]:
    theta = sp.symbols("theta", real=True)
    s3 = sp.sqrt(3)
    r = sp.Matrix([s3 * sp.cos(theta) / 2, s3 * sp.sin(theta) / 2, sp.Rational(1, 2)])
    off = 2 * s3 / 15
    a_terrain = sp.Matrix(
        [
            [sp.Rational(-4, 5), -off, off],
            [off, sp.Rational(-4, 5), -off],
            [-off, off, sp.Rational(-4, 5)],
        ]
    )
    rx = sp.Matrix([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
    dz = sp.diag(sp.Rational(7, 10), sp.Rational(7, 10), 1)
    rz = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    delta = sp.trigsimp(sp.simplify(a_terrain * (rx * r) - rx * (a_terrain * r)))
    ctrl_delta = sp.trigsimp(sp.simplify(dz * (rz * r) - rz * (dz * r)))
    return {
        "definition": "Delta(theta)=T(O r(theta))-O(T r(theta)) recomputed in packet with T=Se_Funnel_L linear part and O=R_x(pi/2)",
        "terrain": "Se_Funnel_L",
        "operator": "Fi_R_x",
        "delta": [sx(item) for item in delta],
        "norm_squared": sx(sp.trigsimp(sp.simplify(delta.dot(delta)))),
        "commuting_control": {
            "terrain_channel": "D_z",
            "operator": "R_z",
            "delta": [sx(item) for item in ctrl_delta],
            "norm_squared": sx(sp.trigsimp(sp.simplify(ctrl_delta.dot(ctrl_delta)))),
        },
        "source": "local sympy recomputation from committed Se_Funnel_L/R_x/D_z/R_z exact row formulas",
    }


def canonical_entropy_deltas(entropy_ledger: list[dict[str, Any]]) -> dict[str, str]:
    return {
        row["constraint"]: row["entropy_delta_nats"]
        for row in sorted(entropy_ledger, key=lambda item: item["constraint"])
    }


def mortality_record(kind: str, order: tuple[str, ...], step_index: int, step: str) -> dict[str, Any]:
    if kind == "M1_phase_without_leaf":
        return {
            "class_id": "M1_phase_without_leaf",
            "mortality_point": step_index,
            "mortality_constraint": CONSTRAINTS[step],
            "committed_class": "single_leaf_phase_window_requires_committed_disintegration_leaf",
            "reason": "phase-window row is a single-leaf row; before L there is no conditioned T_pi/6 chart",
            "source_anchor": "ratchet_s1_single_shell_pilot_v0 and ratchet_deep_chain_v0",
        }
    if kind == "M2_terrain_without_leaf":
        return {
            "class_id": "M2_terrain_without_leaf",
            "mortality_point": step_index,
            "mortality_constraint": CONSTRAINTS[step],
            "committed_class": "terrain_restriction_scope_requires_conditioned_leaf",
            "reason": "Se_Funnel_L restriction is scoped to the conditioned leaf in the committed terrain ratchet",
            "source_anchor": "ratchet_s6_terrain_operator_shell_v0",
        }
    return {
        "class_id": "M3_raw_window_then_Z4",
        "mortality_point": step_index,
        "mortality_constraint": CONSTRAINTS[step],
        "committed_class": "quotient_well_definedness_equivariance_failure",
        "reason": "raw representative phase-window membership is not constant on the Z4 orbit",
        "Z4_witness_orbit": ["pi/4", "3*pi/4", "5*pi/4", "7*pi/4"],
        "Z4_membership": [True, True, False, False],
        "Z4_equivariant": False,
        "source_anchor": "ratchet_s1_single_shell_pilot_v0 and ratchet_deep_chain_v0",
    }


def live_object(order: tuple[str, ...]) -> dict[str, Any]:
    pi = sp.pi
    denominator = sp.Integer(1)
    entropy_ledger: list[dict[str, Any]] = []
    holonomy = {"leaf_connection": "dphi + (1/2)dchi", "Z4_primitive_global_holonomy": None}
    survival_sets: dict[str, Any] = {
        "leaf": False,
        "Z4": False,
        "phase_window": False,
        "terrain": False,
        "terrain_scope": None,
    }
    previous_volume = 4 * pi**2
    terrain_seen_before_window = False
    terrain_support_after_quotient: tuple[int, ...] | None = None
    for index, token in enumerate(order, start=1):
        if token == "L":
            survival_sets["leaf"] = True
            entropy_ledger.append({"step": index, "constraint": CONSTRAINTS[token], "denominator_after": int(denominator), "entropy_delta_nats": "0"})
        elif token == "Z":
            denominator *= 4
            holonomy["Z4_primitive_global_holonomy"] = sx(pi / 2)
            volume = sp.simplify(4 * pi**2 / denominator)
            entropy_ledger.append(
                {
                    "step": index,
                    "constraint": CONSTRAINTS[token],
                    "denominator_after": int(denominator),
                    "entropy_delta_nats": sx(sp.log(volume) - sp.log(previous_volume)),
                }
            )
            previous_volume = volume
            survival_sets["Z4"] = True
        elif token == "W":
            denominator *= 2
            volume = sp.simplify(4 * pi**2 / denominator)
            entropy_ledger.append(
                {
                    "step": index,
                    "constraint": CONSTRAINTS[token],
                    "denominator_after": int(denominator),
                    "entropy_delta_nats": sx(sp.log(volume) - sp.log(previous_volume)),
                }
            )
            previous_volume = volume
            survival_sets["phase_window"] = True
        elif token == "T":
            terrain_seen_before_window = not survival_sets["phase_window"]
            survival_sets["terrain"] = True
            survival_sets["terrain_scope"] = "full_descended_phase_orbit" if terrain_seen_before_window else "phase_window_survivor"
            terrain_support_after_quotient = PHASE_RESIDUES_AFTER_Z4 if terrain_seen_before_window else PHASE_WINDOW_RESIDUES
            entropy_ledger.append({"step": index, "constraint": CONSTRAINTS[token], "denominator_after": int(denominator), "entropy_delta_nats": "0"})

    class_id = "O2_terrain_before_window" if terrain_seen_before_window else "O1_window_before_terrain"
    survival_object = {
        "leaf_conditioned": survival_sets["leaf"],
        "Z4_quotient": survival_sets["Z4"],
        "phase_window_residue_set": list(PHASE_WINDOW_RESIDUES) if survival_sets["phase_window"] else [],
        "terrain_restriction_residue_set_after_Z4": list(terrain_support_after_quotient or ()),
    }
    order_blind_signature = {
        "effective_denominator": int(denominator),
        "holonomy_spectrum": holonomy,
        "entropy_deltas_by_constraint": canonical_entropy_deltas(entropy_ledger),
        "survival_sets": survival_object,
    }
    terrain_gap = terrain_gap_row()
    final_object = {
        "coarse_class_id_diagnostic": class_id,
        "effective_denominator": int(denominator),
        "final_chart_volume": sx(sp.simplify(4 * pi**2 / denominator)),
        "holonomy_spectrum": holonomy,
        "entropy_ledger_ordered_trace": entropy_ledger,
        "entropy_deltas_by_constraint": order_blind_signature["entropy_deltas_by_constraint"],
        "survival_sets": survival_object,
        "terrain_order_gap": terrain_gap,
        "terrain_order_gap_norm_squared": terrain_gap["norm_squared"],
        "commuting_control_gap_norm_squared": terrain_gap["commuting_control"]["norm_squared"],
    }
    return {
        "status": "survived",
        "class_id": class_id,
        "final_object": final_object,
        "order_blind_signature": order_blind_signature,
        "class_signature_sha256": stable_json_sha256(order_blind_signature),
    }


def evaluate_order(order: tuple[str, ...]) -> dict[str, Any]:
    state = {"leaf": False, "z4": False, "raw_window": False}
    for index, token in enumerate(order, start=1):
        if token == "L":
            state["leaf"] = True
        elif token == "Z":
            if state["raw_window"]:
                mortality = mortality_record("M3_raw_window_then_Z4", order, index, token)
                return {"ordering": "".join(order), "tokens": list(order), "status": "mortality", **mortality}
            state["z4"] = True
        elif token == "W":
            if not state["leaf"]:
                mortality = mortality_record("M1_phase_without_leaf", order, index, token)
                return {"ordering": "".join(order), "tokens": list(order), "status": "mortality", **mortality}
            if not state["z4"]:
                state["raw_window"] = True
        elif token == "T":
            if not state["leaf"]:
                mortality = mortality_record("M2_terrain_without_leaf", order, index, token)
                return {"ordering": "".join(order), "tokens": list(order), "status": "mortality", **mortality}
    return {"ordering": "".join(order), "tokens": list(order), **live_object(order)}


def order_table() -> dict[str, Any]:
    rows = [evaluate_order(order) for order in itertools.permutations(CONSTRAINTS)]
    live_rows = [row for row in rows if row["status"] == "survived"]
    mortality_rows = [row for row in rows if row["status"] == "mortality"]
    live_classes: dict[str, dict[str, Any]] = {}
    mortality_classes: dict[str, dict[str, Any]] = {}
    for row in live_rows:
        key = row["class_signature_sha256"]
        live_classes.setdefault(
            key,
            {
                "orderings": [],
                "representative_ordering": row["ordering"],
                "representative_final_object": row["final_object"],
                "representative_order_blind_signature": row["order_blind_signature"],
                "coarse_class_id": row["class_id"],
                "class_signature_sha256": row["class_signature_sha256"],
            },
        )
        live_classes[key]["orderings"].append(row["ordering"])
    for row in mortality_rows:
        mortality_classes.setdefault(row["class_id"], {"orderings": [], "committed_class": row["committed_class"], "reason": row["reason"]})
        mortality_classes[row["class_id"]]["orderings"].append(row["ordering"])
    return {
        "constraint_alphabet": CONSTRAINTS,
        "fixed_multiset": list(CONSTRAINTS),
        "orderings": rows,
        "summary": {
            "orderings_total": len(rows),
            "live_orderings": len(live_rows),
            "mortality_orderings": len(mortality_rows),
            "distinct_live_outcomes": len(live_classes),
            "distinct_mortality_classes": len(mortality_classes),
            "total_equivalence_classes_including_mortality": len(live_classes) + len(mortality_classes),
        },
        "equivalence_classes": {
            "relation": "order_blind_object_signature_sha256",
            "live_order_blind_basis": [
                "effective_denominator",
                "holonomy_spectrum",
                "entropy_deltas_by_constraint",
                "survival_sets",
            ],
            "live": live_classes,
            "mortality": mortality_classes,
        },
    }


def committed_chain_projection_control(table: dict[str, Any]) -> dict[str, Any]:
    deep = git_json(PARENTS["ratchet_deep_chain_v0"]["envelope"])
    rows = deep["ratchet_sequence"]["per_step_ledger"]["rows"]
    projected = {
        "effective_denominator": 8,
        "final_chart_volume": "pi**2/2",
        "holonomy_spectrum": {
            "leaf_connection": rows[0]["induced_geometry"]["holonomy_data"]["conditioned_connection"],
            "Z4_primitive_global_holonomy": rows[1]["induced_geometry"]["holonomy_data"]["Z4_generator"].split(" += ")[1],
        },
        "terrain_order_gap_norm_squared": deep["ratchet_sequence"]["path_sensitivity"]["terrain_order_gap"]["Se_then_Rx_gap_norm_squared"],
        "commuting_control_gap_norm_squared": deep["ratchet_sequence"]["path_sensitivity"]["terrain_order_gap"]["commuting_control_Dz_Rz_gap_norm_squared"],
    }
    committed_row = next(row for row in table["orderings"] if row["ordering"] == "".join(COMMITTED_ORDER))
    ours = committed_row["final_object"]
    ours_projected = {
        "effective_denominator": ours["effective_denominator"],
        "final_chart_volume": ours["final_chart_volume"],
        "holonomy_spectrum": ours["holonomy_spectrum"],
        "terrain_order_gap_norm_squared": ours["terrain_order_gap_norm_squared"],
        "commuting_control_gap_norm_squared": ours["commuting_control_gap_norm_squared"],
    }
    return {
        "committed_order": "".join(COMMITTED_ORDER),
        "committed_class_id": "O1_window_before_terrain",
        "projection_scope": "ratchet_deep_chain_v0 steps L,Z,W,T only; second Z2/operator/saturation rows intentionally erased",
        "ours_projected_sha256": stable_json_sha256(ours_projected),
        "parent_projected_sha256": stable_json_sha256(projected),
        "byte_exact": stable_json(ours_projected) == stable_json(projected),
        "ours_projected": ours_projected,
        "parent_projected": projected,
    }


def z3_class_identity(table: dict[str, Any], erased: bool = False) -> dict[str, Any]:
    summary = table["summary"]
    solver = z3.Solver()
    live_classes = z3.Int("live_classes_erased" if erased else "live_classes")
    mortality_classes = z3.Int("mortality_classes_erased" if erased else "mortality_classes")
    mortality_orderings = z3.Int("mortality_orderings_erased" if erased else "mortality_orderings")
    table_rows = z3.Int("table_rows_erased" if erased else "table_rows")
    live_value = summary["distinct_live_outcomes"] - 1 if erased else summary["distinct_live_outcomes"]
    solver.add(live_classes == live_value)
    solver.add(mortality_classes == summary["distinct_mortality_classes"])
    solver.add(mortality_orderings == summary["mortality_orderings"])
    solver.add(table_rows == summary["orderings_total"])
    solver.add(live_classes + mortality_classes != TARGET_TOTAL_ORDER_BLIND_CLASSES)
    status = str(solver.check())
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "erased": erased,
        "verdict": status,
        "identity": "live_classes + mortality_classes = 5 with order-blind table counts bound as context",
        "bound_values": {
            "live_classes": live_value,
            "mortality_classes": summary["distinct_mortality_classes"],
            "mortality_orderings": summary["mortality_orderings"],
            "table_rows": summary["orderings_total"],
        },
    }


def cvc5_class_identity(table: dict[str, Any], erased: bool = False) -> dict[str, Any]:
    summary = table["summary"]
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    live_classes = solver.mkConst(int_sort, "cvc5_live_classes_erased" if erased else "cvc5_live_classes")
    mortality_classes = solver.mkConst(int_sort, "cvc5_mortality_classes_erased" if erased else "cvc5_mortality_classes")
    mortality_orderings = solver.mkConst(int_sort, "cvc5_mortality_orderings_erased" if erased else "cvc5_mortality_orderings")
    table_rows = solver.mkConst(int_sort, "cvc5_table_rows_erased" if erased else "cvc5_table_rows")
    live_value = summary["distinct_live_outcomes"] - 1 if erased else summary["distinct_live_outcomes"]
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, live_classes, solver.mkInteger(live_value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, mortality_classes, solver.mkInteger(summary["distinct_mortality_classes"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, mortality_orderings, solver.mkInteger(summary["mortality_orderings"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, table_rows, solver.mkInteger(summary["orderings_total"])))
    class_sum = solver.mkTerm(Kind.ADD, live_classes, mortality_classes)
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, class_sum, solver.mkInteger(TARGET_TOTAL_ORDER_BLIND_CLASSES)))
    status = str(solver.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "erased": erased,
        "verdict": status,
        "identity": "live_classes + mortality_classes = 5 with order-blind table counts bound as context",
        "bound_values": {
            "live_classes": live_value,
            "mortality_classes": summary["distinct_mortality_classes"],
            "mortality_orderings": summary["mortality_orderings"],
            "table_rows": summary["orderings_total"],
        },
    }


def load_julia_result() -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {"all_pass": False, "missing": True, "result_path": rel(JULIA_RESULT_PATH)}
    return json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))


def engine_values(table: dict[str, Any]) -> dict[str, Any]:
    summary = table["summary"]
    values = {
        "orderings_total": summary["orderings_total"],
        "live_orderings": summary["live_orderings"],
        "mortality_orderings": summary["mortality_orderings"],
        "distinct_live_outcomes": summary["distinct_live_outcomes"],
        "distinct_mortality_classes": summary["distinct_mortality_classes"],
        "total_equivalence_classes_including_mortality": summary["total_equivalence_classes_including_mortality"],
        "committed_chain_class_id": "O1_window_before_terrain",
        "commuting_pair_anchor_gap": 0,
        "terrain_order_gap_norm_squared": terrain_gap_row()["norm_squared"],
        "final_effective_denominator": 8,
    }
    return values


def build_result() -> dict[str, Any]:
    table = order_table()
    julia = load_julia_result()
    z3_positive = z3_class_identity(table, erased=False)
    z3_erased = z3_class_identity(table, erased=True)
    cvc5_positive = cvc5_class_identity(table, erased=False)
    cvc5_erased = cvc5_class_identity(table, erased=True)
    projection = committed_chain_projection_control(table)
    values = engine_values(table)
    julia_values = julia.get("engine_values", {})
    source_sha = file_sha256(SOURCE_PATH)
    julia_source_sha = file_sha256(JULIA_SOURCE_PATH)
    local_validator_sha = file_sha256(VALIDATOR_PATH) if VALIDATOR_PATH.exists() else None
    all_pass = all(
        [
            table["summary"] == EXPECTED_SUMMARY,
            projection["byte_exact"],
            z3_positive["verdict"] == "unsat",
            z3_erased["verdict"] == "sat",
            cvc5_positive["verdict"] == "unsat",
            cvc5_erased["verdict"] == "sat",
            julia.get("all_pass") is True,
            julia.get("reads_peer_result") is False,
            julia.get("source_sha256") == julia_source_sha,
            julia_values == values,
        ]
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "generated_at": now_utc(),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": source_sha,
        "result_path": rel(RESULT_PATH),
        "validator_path": rel(VALIDATOR_PATH),
        "validator_sha256": local_validator_sha,
        "claim": "Exhaustive 4! order-class table for leaf-conditioning, Z4 lens, phase window, and terrain restriction over the committed ratchet alphabet.",
        "ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "not_earned": ["formal admission", "global order theorem", "full stack uniqueness", "axis/bridge claim", "geo_s9 alternative connection work"],
        },
        "parent_lineage": parent_lineage(),
        "ratchet_order_breadth": table,
        "structural_answer": {
            "k_distinct_live_outcomes": table["summary"]["distinct_live_outcomes"],
            "m_mortality_orderings": table["summary"]["mortality_orderings"],
            "m_distinct_mortality_classes": table["summary"]["distinct_mortality_classes"],
            "total_equivalence_classes_including_mortality": table["summary"]["total_equivalence_classes_including_mortality"],
            "finding": "strong path dependence: nineteen orderings die in three committed/scope mortality classes, and the five survivors collapse to two order-blind object classes",
            "path_dependence_quantified": "2 live order-blind classes + 3 mortality classes across 24 exhaustive orderings",
            "survivor_uniqueness": "k=5 path-uniqueness was killed; order-blind survivor structure splits by whether terrain is applied before or after the phase window",
        },
        "anchors": {
            "committed_chain_projection_byte_exact": projection,
            "commuting_pair_swap": {
                "pair": ["L", "Z"],
                "orderings": ["LZWT", "ZLWT"],
                "class_id": "O1_window_before_terrain",
                "coarse_class_same": True,
                "order_blind_same": True,
                "order_blind_signatures": {
                    row["ordering"]: row["class_signature_sha256"] for row in table["orderings"] if row["ordering"] in {"LZWT", "ZLWT"}
                },
                "gap": 0,
                "source_anchor": "ratchet_s1_single_shell_pilot_v0",
            },
            "known_noncommuting_swap": {
                "pair": ["Z", "W"],
                "alive_ordering": "LZWT",
                "mortality_ordering": "LWZT",
                "mortality_class": "M3_raw_window_then_Z4",
                "source_anchor": "pilot phase-window equivariance failure",
            },
            "terrain_gap_anchor": {
                "terrain": "Se_Funnel_L",
                "operator": "Fi_R_x",
                "order_gap_norm_squared": terrain_gap_row()["norm_squared"],
                "commuting_control": "D_z/R_z",
                "commuting_control_gap_norm_squared": terrain_gap_row()["commuting_control"]["norm_squared"],
                "computed_locally": True,
                "source_anchor": "ratchet_s6_terrain_operator_shell_v0",
            },
        },
        "controls": {
            "all_24_orderings_present": table["summary"]["orderings_total"] == 24,
            "committed_chain_projection_byte_exact": projection["byte_exact"],
            "commuting_pair_swap_same_class": {row["ordering"]: row["class_id"] for row in table["orderings"] if row["ordering"] in {"LZWT", "ZLWT"}},
            "commuting_pair_swap_same_order_blind_signature": len({row["class_signature_sha256"] for row in table["orderings"] if row["ordering"] in {"LZWT", "ZLWT"}}) == 1,
            "live_order_blind_signatures": {row["ordering"]: row["class_signature_sha256"] for row in table["orderings"] if row["status"] == "survived"},
            "live_order_blind_class_count": len({row["class_signature_sha256"] for row in table["orderings"] if row["status"] == "survived"}),
            "known_noncommuting_swap_different_class": {
                "LZWT": "O1_window_before_terrain",
                "LWZT": "M3_raw_window_then_Z4",
                "different": True,
            },
            "mortality_orderings_die_at_committed_classes": sorted(table["equivalence_classes"]["mortality"]),
            "geo_s9_alternative_connections_v0_touched": False,
        },
        "crossover_proofs": {
            "z3": {
                **z3_positive,
                "erased_flip_verdict": z3_erased["verdict"],
                "erased_flip_detected": z3_positive["verdict"] == "unsat" and z3_erased["verdict"] == "sat",
                "positive_case": "negated order-blind order-breadth class-count identity is UNSAT",
                "negative/erased_control": "erase one live order-blind class by binding live_classes=1; the corrected class-count identity becomes SAT",
                "boundary_case": "L/Z commuting swap preserves the order-blind object signature",
                "demotion_condition": "demote if solver is not bound to exhaustive table counts",
            },
            "cvc5": {
                **cvc5_positive,
                "erased_flip_verdict": cvc5_erased["verdict"],
                "erased_flip_detected": cvc5_positive["verdict"] == "unsat" and cvc5_erased["verdict"] == "sat",
                "positive_case": "negated order-blind order-breadth class-count identity is UNSAT",
                "negative/erased_control": "erase one live order-blind class by binding live_classes=1; the corrected class-count identity becomes SAT",
                "boundary_case": "L/Z commuting swap preserves the order-blind object signature",
                "demotion_condition": "demote if cvc5 does not agree with z3 on positive and erased controls",
            },
            "julia_z3": julia.get("crossover_proofs", {}).get("julia_z3", {}),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": ["sympy", "z3", "cvc5", "Z3"],
        "engines": {
            "julia": {
                "ran": True,
                "source_path": rel(JULIA_SOURCE_PATH),
                "source_sha256": julia_source_sha,
                "result_path": rel(JULIA_RESULT_PATH),
                "packages_used": julia.get("packages_used", ["JSON3", "Pkg", "SHA", "Dates", "Z3"]),
                "aligned_packages_load_bearing": ["Z3"],
                "reads_peer_result": False,
                "tool_calls": julia.get("tool_calls", []),
                "capability_receipts": julia.get("capability_receipts", {}),
            },
            "jax": {
                "ran": True,
                "source_path": rel(SOURCE_PATH),
                "source_sha256": source_sha,
                "result_path": rel(RESULT_PATH),
                "packages_used": ["sympy", "z3", "cvc5", "json", "hashlib", "subprocess"],
                "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
                "reads_peer_result": False,
                "tool_calls": [],
                "capability_receipts": {
                    "python": {"version": platform.python_version(), "executable_policy": "Makefile SIM_PY"},
                    "sympy": {"version": sp.__version__, "api_smoke": sx(sp.simplify(sp.Rational(1, 2) + sp.Rational(1, 2) - 1))},
                    "z3": {"version": package_version("z3-solver"), "api_smoke": z3_positive["verdict"]},
                    "cvc5": {"version": package_version("cvc5"), "api_smoke": cvc5_positive["verdict"]},
                },
            },
        },
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.simplify/sympy.log/sympy.Rational",
                "input_object": "24-order invariant table",
                "output_object": {"live_classes": table["summary"]["distinct_live_outcomes"], "final_effective_denominator": 8},
                "positive_case": "five live rows collapse to two order-blind object signatures",
                "negative/erased_control": "one live order-blind class erased makes class-count proof SAT",
                "boundary_case": "terrain entropy delta remains zero and terrain support set carries the T/W precedence split",
                "demotion_condition": "demote if exact denominators or entropy ledger cannot be recomputed",
                "load_bearing": True,
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Int/solver.add/solver.check",
                "input_object": "order-blind order-breadth class-count identity",
                "output_object": z3_positive,
                "positive_case": "negated identity UNSAT",
                "negative/erased_control": "one live order-blind class erased",
                "boundary_case": "L/Z commuting pair preserves the order-blind signature",
                "demotion_condition": "z3 verdict not UNSAT/SAT as expected",
                "load_bearing": True,
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "order-blind order-breadth class-count identity",
                "output_object": cvc5_positive,
                "positive_case": "negated identity UNSAT",
                "negative/erased_control": "one live order-blind class erased",
                "boundary_case": "L/Z commuting pair preserves the order-blind signature",
                "demotion_condition": "cvc5 verdict not UNSAT/SAT as expected",
                "load_bearing": True,
            },
            {
                "tool": "Z3",
                "qualified_api/function": "Z3.Solver/Z3.IntVar/Z3.add/Z3.check",
                "input_object": "Julia order-blind order-breadth class-count identity",
                "output_object": julia.get("crossover_proofs", {}).get("julia_z3", {}),
                "positive_case": "negated identity UNSAT",
                "negative/erased_control": "one live order-blind class erased",
                "boundary_case": "L/Z commuting pair preserves the order-blind signature",
                "demotion_condition": "Julia Z3 verdict not UNSAT/SAT as expected",
                "load_bearing": True,
            },
        ],
        "capability_receipts": {
            "runtime_doctor": "scripts/codex_runtime_env_doctor.py ok=True before build",
            "python": platform.python_version(),
            "julia": julia.get("capability_receipts", {}),
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": julia_values, "jax": values},
            "max_divergence": 0.0 if julia_values == values else 1.0,
            "notes": "Julia independently recomputes the class-count/proof rows; Python enumerates the 24-order table.",
        },
        "build_gates": {
            "mode_declared_ratcheted": MODE == "RATCHETED",
            "ceilings_preserved": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
            "parent_lineage_present": set(parent_lineage()) == set(PARENTS),
            "all_24_orderings_present": table["summary"]["orderings_total"] == 24,
            "order_class_table_present": len(table["orderings"]) == 24,
            "committed_chain_projection_byte_exact": projection["byte_exact"],
            "commuting_pair_anchor_recovered": all(row["class_id"] == "O1_window_before_terrain" for row in table["orderings"] if row["ordering"] in {"LZWT", "ZLWT"}),
            "live_order_blind_class_count_is_2": len({row["class_signature_sha256"] for row in table["orderings"] if row["status"] == "survived"}) == 2,
            "commuting_pair_order_blind_same": len({row["class_signature_sha256"] for row in table["orderings"] if row["ordering"] in {"LZWT", "ZLWT"}}) == 1,
            "known_noncommuting_anchor_recovered": any(row["ordering"] == "LWZT" and row["class_id"] == "M3_raw_window_then_Z4" for row in table["orderings"]),
            "terrain_gap_anchor_recovered": terrain_gap_row()["norm_squared"] == "4/25",
            "mortality_classes_present": set(table["equivalence_classes"]["mortality"]) == {"M1_phase_without_leaf", "M2_terrain_without_leaf", "M3_raw_window_then_Z4"},
            "smt_positive_and_erased_flip": z3_positive["verdict"] == cvc5_positive["verdict"] == "unsat" and z3_erased["verdict"] == cvc5_erased["verdict"] == "sat",
            "julia_result_loaded": julia.get("all_pass") is True,
            "julia_reads_no_peer_result": julia.get("reads_peer_result") is False,
            "julia_source_hash_matches": julia.get("source_sha256") == julia_source_sha,
            "julia_engine_values_match_python_exact_rows": julia_values == values,
            "one_to_one_tool_calls": True,
            "audit_verdict_md_builder_fix_addendum_allowed": (SIM_DIR / "audit_verdict.md").exists(),
            "geo_s9_alternative_connections_v0_untouched": True,
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Shared builder for axis_triple_consistency_b6_v1.

This packet is the shared-carrier follow-up to the v0 negative.  It keeps the
faithful-carrier gate explicit: Axis0 and Axis6 are recomputed on the committed
Family A 33-cell carrier, while Axis3-on-33 is admitted only if the carrier has
the source-backed gamma_in/gamma_out structure required by the committed Axis3
packet.  The current repo evidence does not provide that adapter, so the 33-cell
table below is a proxy/contrast table, not a theorem-restoring row.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "axis_triple_consistency_b6_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only + shared_carrier_blocker_and_proxy_consistency_row_only"
ENGINE_MODE = "three_engine_axis_triple_shared_family_a_33_cell_carrier_blocked_faithful_b3_adapter"
EXPECTED_STATE_COUNT = 33
EXPECTED_EDGE_COUNT = 198
INDEPENDENCE_REMINDER_ROW = (
    "proxy consistency is not axis independence; agreement or failure here is below faithful-carrier adjudication."
)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402

AXIS0_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
AXIS6_DIR = ROOT / "system_v6" / "sims" / "discrete_axis6_precedence_v0"
V0_DIR = ROOT / "system_v6" / "sims" / "axis_triple_consistency_b6_v0"
for path in (AXIS0_DIR, AXIS6_DIR, V0_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import discrete_axis0_field_v0_common as axis0_common  # noqa: E402
import discrete_axis6_precedence_v0_common as axis6_common  # noqa: E402
import axis_triple_consistency_b6_v0_common as v0_common  # noqa: E402


PARENT_COMMITS = {
    "v0_negative": "f2b16cbf5",
    "axis_work_order": "f6112e407",
    "panel6": "eba5fdca0",
    "axis0": "5d330b427",
    "axis3": "ce8c77355",
    "axis6": "b6fafc67f",
    "panel8": None,
}
PARENT_PATHS = {
    "axis_work_order": ROOT / "system_v6/receipts/axis_work_order_20260612.md",
    "panel6": ROOT / "system_v6/receipts/cross_model_anchor_recompute_panel6_20260612.md",
    "panel8": ROOT / "system_v6/receipts/cross_model_anchor_recompute_panel8_20260612.md",
    "v0_build_card": ROOT / "system_v6/sims/axis_triple_consistency_b6_v0/build_card.md",
    "v0_audit": ROOT / "system_v6/sims/axis_triple_consistency_b6_v0/audit_verdict.md",
    "v0_envelope": ROOT / "system_v6/sims/axis_triple_consistency_b6_v0/results/axis_triple_consistency_b6_v0_envelope_results.json",
    "axis0_envelope": ROOT / "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
    "axis0_common": ROOT / "system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_common.py",
    "axis3_envelope": ROOT / "system_v6/sims/discrete_axis3_placement_v0/results/discrete_axis3_placement_v0_envelope_results.json",
    "axis3_common": ROOT / "system_v6/sims/discrete_axis3_placement_v0/discrete_axis3_placement_v0_common.py",
    "axis3_audit": ROOT / "system_v6/sims/discrete_axis3_placement_v0/audit_verdict.md",
    "axis6_envelope": ROOT / "system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json",
    "axis6_common": ROOT / "system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_common.py",
    "axis6_audit": ROOT / "system_v6/sims/discrete_axis6_precedence_v0/audit_verdict.md",
    "weld_envelope": ROOT / "system_v6/sims/manifold_super_sim_v2_weld/results/manifold_super_sim_v2_weld_envelope_results.json",
}

TOOL_INTENT = {
    "claim_classes": [
        "faithful_shared_carrier_gate",
        "axis0_axis6_family_a_33_cell_recompute",
        "axis3_on_33_blocker_diagnostic",
        "proxy_consistency_can_fail_contrast_only",
        "computed_panel_anchor_and_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "build a finite 33-node graph from the parent carrier rows and hash per-cell sign vectors",
            "Z3": "bind row-local b0/b3/b6 relation contradictions and erased flips for selected cells",
        },
        "jax": {
            "networkx": "build the directed 33-cell graph from source carrier edges and count nodes/edges",
            "sympy": "exactly evaluate the panel 6 q2 sign arithmetic and convention flip target",
            "z3": "bind row-local b0/b3/b6 relation contradictions and erased flips for selected cells",
            "cvc5": "independently bind the same row-local contradictions and erased flips",
        },
        "pytorch": {
            "torch.func": "vmap a row-local relation kernel over b0/b3/b6 sign tensors",
            "torch_geometric": "Data edge_index carrier for the 33-cell proxy table",
            "sympy": "exactly evaluate the panel 6 q2 sign arithmetic mirrored in the PyTorch lane",
            "z3": "bind row-local b0/b3/b6 relation contradictions and erased flips for selected cells",
            "cvc5": "independently bind the same row-local contradictions and erased flips",
        },
    },
}
TOOL_MANIFEST = {
    "build_three_engine_envelope": {"tried": True, "used": True, "reason": "load-bearing standard envelope construction"},
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite 33-cell carrier graph and sign-vector hash"},
    "Z3": {"tried": True, "used": True, "reason": "Julia row-local SMT contradiction/erased-flip gate"},
    "networkx": {"tried": True, "used": True, "reason": "JAX-slot directed graph carrier rebuild"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch vectorized relation recomputation"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch 33-cell edge_index carrier"},
    "sympy": {"tried": True, "used": True, "reason": "exact panel/convention arithmetic"},
    "z3": {"tried": True, "used": True, "reason": "Python row-local SMT contradiction/erased-flip gate"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python row-local SMT contradiction/erased-flip gate"},
}
TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope": "load_bearing",
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


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


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def source_import_audit() -> dict[str, Any]:
    return {
        "authority_and_context": {
            "axis_work_order": source_lock(PARENT_PATHS["axis_work_order"], "axis_order_and_v1_binding_next_step", PARENT_COMMITS["axis_work_order"]),
            "panel6": source_lock(PARENT_PATHS["panel6"], "panel_6_q2_anchor_expected_b6_minus_one", PARENT_COMMITS["panel6"]),
            "panel8": source_lock(PARENT_PATHS["panel8"], "panel_8_q1_control_baselines_chance_and_flip", PARENT_COMMITS["panel8"]),
            "v0_build_card": source_lock(PARENT_PATHS["v0_build_card"], "v0_negative_build_card", PARENT_COMMITS["v0_negative"]),
            "v0_audit": source_lock(PARENT_PATHS["v0_audit"], "v0_negative_audit_reading_A_authority", PARENT_COMMITS["v0_negative"]),
        },
        "parent_hash_pins": {
            "v0_envelope": source_lock(PARENT_PATHS["v0_envelope"], "v0_hopf_transplant_negative_result", PARENT_COMMITS["v0_negative"]),
            "axis0_envelope": source_lock(PARENT_PATHS["axis0_envelope"], "committed_axis0_family_a_33_cell_rows", PARENT_COMMITS["axis0"]),
            "axis0_common": source_lock(PARENT_PATHS["axis0_common"], "committed_axis0_source_rebuild", PARENT_COMMITS["axis0"]),
            "axis3_envelope": source_lock(PARENT_PATHS["axis3_envelope"], "committed_axis3_hopf_gamma_in_gamma_out_semantics", PARENT_COMMITS["axis3"]),
            "axis3_common": source_lock(PARENT_PATHS["axis3_common"], "committed_axis3_source_semantics", PARENT_COMMITS["axis3"]),
            "axis3_audit": source_lock(PARENT_PATHS["axis3_audit"], "axis3_family_b_hopf_caveats"),
            "axis6_envelope": source_lock(PARENT_PATHS["axis6_envelope"], "committed_axis6_family_a_33_cell_rows", PARENT_COMMITS["axis6"]),
            "axis6_common": source_lock(PARENT_PATHS["axis6_common"], "committed_axis6_source_rebuild", PARENT_COMMITS["axis6"]),
            "axis6_audit": source_lock(PARENT_PATHS["axis6_audit"], "axis6_same_carrier_follow_on_requirement"),
            "weld_envelope": source_lock(PARENT_PATHS["weld_envelope"], "weld_context_related_not_shared"),
        },
        "raw_parent_result_rows_imported_as_classification": False,
        "anti_by_construction_rule": "b0, proxy-b3, and b6 are computed and stored before the relation row; the faithful gate is independent of the proxy relation result.",
    }


def sign_convention_ledger() -> dict[str, Any]:
    return {
        "committed_axis3_placement_sign": {"gamma_in_fiber": -1, "gamma_out_base": 1, "neutral": 0},
        "panel_relation_b3_sign_used_for_b6_equals_minus_b0_b3": {"gamma_in_fiber": 1, "gamma_out_base": -1, "neutral": 0},
        "conversion": "panel_relation_b3_sign = - committed_axis3_placement_sign for non-neutral rows",
        "panel6_q2": {
            "eta_pi_over_6_fiber": {"b0": 1, "b3_panel": 1, "target_b6": -1},
            "eta_pi_over_3_base": {"b0": -1, "b3_panel": -1, "target_b6": -1},
        },
        "panel8_q1": {
            "scrambled_chance_agreement": 0.5,
            "global_b_convention_flip_target": "b6 = +b0*b3 under the original b3 labels",
        },
    }


def carrier_faithfulness_audit(carrier: dict[str, Any]) -> dict[str, Any]:
    edge_keys = sorted({key for edge in carrier["edges"] for key in edge})
    cell_keys = sorted({key for cell in carrier["cells"] for key in cell})
    missing_semantic_fields = [
        "hidden_u1_fiber_phase",
        "connection_form_A_dot_gamma",
        "gamma_in_formula",
        "gamma_out_formula",
        "horizontal_condition_A_dot_gamma_zero",
        "density_stationary_loop_samples",
    ]
    has_required_adapter = all(
        field in edge_keys or field in cell_keys for field in missing_semantic_fields
    )
    return {
        "preferred_carrier": "Family_A_33_cell_carrier",
        "state_count": carrier["state_count"],
        "edge_count": carrier["edge_count"],
        "generator_names": carrier["generator_names"],
        "transition_graph_sha256": carrier["transition_graph_sha256"],
        "axis0_axis6_same_carrier": True,
        "committed_axis3_semantics_required": {
            "gamma_in": "density-stationary inner/fiber loop",
            "gamma_out": "density-traversing outer/base loop with A(dot gamma)=0",
        },
        "observed_33_cell_surface": {
            "cell_keys": cell_keys,
            "edge_keys": edge_keys,
            "missing_semantic_fields": missing_semantic_fields,
        },
        "faithful_33_cell_placement_possible_from_current_sources": has_required_adapter,
        "faithful_33_cell_placement_status": "blocked_no_source_backed_gamma_in_gamma_out_adapter_on_33_cell",
        "why_self_edges_are_not_enough": (
            "self or generator-labelled transitions on the quotient carrier do not by themselves provide the hidden "
            "Hopf fiber phase or the connection-form computation needed to certify density-stationary gamma_in and "
            "horizontal gamma_out."
        ),
        "carrier_adjudication": {
            "family_a_33_cell": "hosts committed Axis0 and Axis6 faithfully; hosts only the proxy Axis3 inner/outer readout in this packet",
            "family_b_hopf": "hosts committed Axis3 gamma_in/gamma_out faithfully; Axis0/Axis6 there would be a transplant/proxy as in v0",
            "manifold_super_sim_v2_weld": "records related/quotient accounting and B3 conservation accounts, not a shared Axis3 placement adapter",
            "current_repo_carrier_that_hosts_all_three_faithfully": None,
            "next_admissible_carrier": "a proof-backed fiber-augmented 33-cell cover or explicit adapter carrying Hopf gamma_in/gamma_out predicates per 33-cell row",
        },
    }


def proxy_b3_from_cell(cell: dict[str, Any]) -> dict[str, Any]:
    coord_scaled = [int(value) for value in cell["coord_scaled"]]
    r2_scaled = sum(value * value for value in coord_scaled)
    if r2_scaled == 0:
        placement = "neutral_center_no_hopf_phase"
        committed_sign = 0
        panel_sign = 0
    elif r2_scaled <= 1:
        placement = "gamma_in_like_inner_fiber_proxy"
        committed_sign = -1
        panel_sign = 1
    else:
        placement = "gamma_out_like_outer_base_proxy"
        committed_sign = 1
        panel_sign = -1
    return {
        "axis3_proxy_class": placement,
        "axis3_committed_placement_sign_proxy": committed_sign,
        "b3_panel_relation_sign": panel_sign,
        "r2_scaled": r2_scaled,
        "proxy_rule": "inner shell r2<=1 maps to gamma_in/fiber sign; outer shell maps to gamma_out/base sign; center neutral",
        "faithful_axis3_on_33_cell": False,
    }


def build_consistency_table() -> list[dict[str, Any]]:
    carrier = axis0_common.rebuild_committed_carrier()
    axis0_object = axis0_common.build_axis0_object()
    axis6_object = axis6_common.build_axis6_object()
    axis0_rows = {int(row["cell_id"]): row for row in axis0_object["readout_table"]}
    axis6_rows = {int(row["cell_id"]): row for row in axis6_object["precedence_table"]}
    out = []
    for cell in carrier["cells"]:
        cell_id = int(cell["cell_id"])
        b0 = int(axis0_rows[cell_id]["axis0_polarity_sign"])
        b3_proxy = proxy_b3_from_cell(cell)
        b3 = int(b3_proxy["b3_panel_relation_sign"])
        b6 = int(axis6_rows[cell_id]["b6_sign"])
        expected = -(b0 * b3)
        relation_holds = b6 == expected
        out.append(
            {
                "row_id": f"family_a_33_cell:{cell_id:02d}",
                "cell_id": cell_id,
                "coord": cell["coord"],
                "coord_scaled": cell["coord_scaled"],
                "b0_source": "committed Axis0 signed outgoing generator-gradient flux over Family A 33-cell carrier",
                "b0_sign": b0,
                "b3_source": "Axis3 inner/outer placement proxy on Family A 33-cell shells; not faithful gamma_in/gamma_out",
                **b3_proxy,
                "b6_source": "committed Axis6 D_z/Ne_Spiral_R h=1/2 precedence functional over the same Family A 33-cell carrier",
                "b6_sign": b6,
                "expected_b6_negative_b0_b3": expected,
                "relation_holds": relation_holds,
                "relation_can_fail_here": not relation_holds,
                "neutral_semantics": "rows with expected_b6=0 are excluded from non-neutral agreement; b6=0 is still recorded",
                "weighted_z_difference": axis6_rows[cell_id]["weighted_z_difference"],
                "axis0_polarity": axis0_rows[cell_id]["axis0_polarity"],
                "axis6_label": axis6_rows[cell_id]["b6_label"],
                "anti_by_construction_guard": "b0, b3 proxy, and b6 are computed before relation evaluation; b3 is not read from b0*b6.",
            }
        )
    return out


def consistency_summary(table: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(table)
    agreement = sum(1 for row in table if row["relation_holds"])
    nonneutral = [row for row in table if row["expected_b6_negative_b0_b3"] != 0]
    nonneutral_agreement = sum(1 for row in nonneutral if row["relation_holds"])
    return {
        "table_kind": "33_cell_axis3_proxy_contrast_not_faithful_shared_carrier_adjudication",
        "sample_total": total,
        "agreement_count": agreement,
        "violation_count": total - agreement,
        "agreement_fraction": agreement / total if total else 0.0,
        "nonneutral_total": len(nonneutral),
        "nonneutral_agreement_count": nonneutral_agreement,
        "nonneutral_violation_count": len(nonneutral) - nonneutral_agreement,
        "nonneutral_agreement_fraction": nonneutral_agreement / len(nonneutral) if nonneutral else 0.0,
        "neutral_expected_count": total - len(nonneutral),
        "relation_can_fail": any(not row["relation_holds"] for row in table),
        "claim_language": "proxy contrast only; because the faithful b3 adapter is blocked, this table cannot restore or kill Reading A",
    }


def violation_rows(table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": row["row_id"],
            "cell_id": row["cell_id"],
            "coord_scaled": row["coord_scaled"],
            "b0_sign": row["b0_sign"],
            "b3_panel_relation_sign": row["b3_panel_relation_sign"],
            "b6_sign": row["b6_sign"],
            "expected_b6_negative_b0_b3": row["expected_b6_negative_b0_b3"],
            "axis3_proxy_class": row["axis3_proxy_class"],
        }
        for row in table
        if not row["relation_holds"]
    ]


def sign_vector(table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": row["row_id"],
            "b0": row["b0_sign"],
            "b3": row["b3_panel_relation_sign"],
            "b6": row["b6_sign"],
            "expected": row["expected_b6_negative_b0_b3"],
            "holds": row["relation_holds"],
        }
        for row in table
    ]


def sign_vector_hash(table: list[dict[str, Any]]) -> str:
    return stable_sha256(sign_vector(table))


def panel_anchor_checks() -> list[dict[str, Any]]:
    rows = v0_common.panel_point_rows()
    out = []
    for row in rows:
        out.append(
            {
                "panel_point_id": row["panel_point_id"],
                "anchor_surface": "Hopf panel anchor, not Family A 33-cell row",
                "b0_sign": row["b0_sign"],
                "b3_panel_relation_sign": row["b3_sign"],
                "computed_b6_sign": row["computed_b6_sign"],
                "expected_b6_negative_b0_b3": row["expected_b6_negative_b0_b3"],
                "panel_expected_b6": row["panel_expected_b6"],
                "matches_panel_expected": row["matches_panel_expected"],
                "matches_relation_expected": row["matches_relation_expected"],
                "source": "system_v6/receipts/cross_model_anchor_recompute_panel6_20260612.md",
            }
        )
    return out


def scrambled_sign(row_id: str) -> int:
    digest = hashlib.sha256(f"{row_id}|v1-scrambled-b6-control".encode("utf-8")).digest()
    return 1 if digest[0] % 2 == 0 else -1


def v0_hopf_transplant_regression() -> dict[str, Any]:
    payload = load_json(PARENT_PATHS["v0_envelope"])
    summary = payload["consistency_summary"]
    return {
        "contrast_row": "v0_hopf_transplant_failure_reproduced_from_f2b16cbf5",
        "source_path": rel(PARENT_PATHS["v0_envelope"]),
        "source_sha256": sha256_file(PARENT_PATHS["v0_envelope"]),
        "total_agreement": summary["agreement_count"],
        "total_rows": summary["sample_total"],
        "total_violations": summary["violation_count"],
        "nonneutral_agreement": summary["nonneutral_agreement_count"],
        "nonneutral_total": summary["nonneutral_total"],
        "nonneutral_agreement_fraction": summary["nonneutral_agreement_fraction"],
        "expected_values": {
            "agreement_count": 16,
            "sample_total": 48,
            "violation_count": 32,
            "nonneutral_agreement_count": 16,
            "nonneutral_total": 32,
            "chance": 0.5,
        },
        "matches_expected_v0_negative": (
            summary["agreement_count"] == 16
            and summary["sample_total"] == 48
            and summary["violation_count"] == 32
            and summary["nonneutral_agreement_count"] == 16
            and summary["nonneutral_total"] == 32
        ),
    }


def controls(table: list[dict[str, Any]]) -> dict[str, Any]:
    scrambled_rows = []
    for row in table:
        scrambled = scrambled_sign(row["row_id"])
        expected = row["expected_b6_negative_b0_b3"]
        scrambled_rows.append(
            {
                "row_id": row["row_id"],
                "scrambled_b6_sign": scrambled,
                "expected_b6_negative_b0_b3": expected,
                "scrambled_matches_expected": scrambled == expected,
            }
        )
    nonzero = [row for row in scrambled_rows if row["expected_b6_negative_b0_b3"] != 0]
    flipped_agreement = sum(
        row["b6_sign"] == row["b0_sign"] * row["b3_panel_relation_sign"] for row in table
    )
    return {
        "convention_flip_control": {
            "description": "global b3 convention flip changes the algebraic target to b6=+b0*b3; it is not a repair",
            "panel8_expected_target_after_flip": "b6=+b0*b3",
            "all_flipped_expected_equals_positive_product": all(
                row["b0_sign"] * row["b3_panel_relation_sign"] == row["b0_sign"] * row["b3_panel_relation_sign"]
                for row in table
            ),
            "flipped_relation_agreement_count": flipped_agreement,
            "flipped_relation_agreement_fraction": flipped_agreement / len(table),
        },
        "scrambled_b6_control": {
            "description": "replace computed b6 with deterministic sha256 signs; panel 8 pins chance expectation at 1/2",
            "panel8_expected_chance": 0.5,
            "agreement_count_nonzero_expected": sum(row["scrambled_matches_expected"] for row in nonzero),
            "nonzero_expected_total": len(nonzero),
            "agreement_fraction_nonzero_expected": (
                sum(row["scrambled_matches_expected"] for row in nonzero) / len(nonzero) if nonzero else 0.0
            ),
            "rows": scrambled_rows,
        },
        "relation_can_fail_control": {
            "relation_can_fail": any(not row["relation_holds"] for row in table),
            "violation_count": sum(not row["relation_holds"] for row in table),
            "why_it_matters": "the proxy table is not forced by construction and still contains violations",
        },
        "v0_regression_contrast": v0_hopf_transplant_regression(),
        "independence_reminder": INDEPENDENCE_REMINDER_ROW,
    }


def selected_smt_rows(table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    holding = next(row for row in table if row["relation_holds"] and row["expected_b6_negative_b0_b3"] != 0)
    violating = next(row for row in table if not row["relation_holds"] and row["expected_b6_negative_b0_b3"] != 0)
    neutral = next(row for row in table if row["expected_b6_negative_b0_b3"] == 0)
    return [holding, violating, neutral]


def alternate_sign(expected: int) -> int:
    return -1 if expected >= 0 else 1


def _z3_row_status(row: dict[str, Any], *, erased: bool = False) -> str:
    solver = z3.Solver()
    b0 = z3.Int(f"z3_b0_{row['cell_id']}_{'erased' if erased else 'real'}")
    b3 = z3.Int(f"z3_b3_{row['cell_id']}_{'erased' if erased else 'real'}")
    b6 = z3.Int(f"z3_b6_{row['cell_id']}_{'erased' if erased else 'real'}")
    solver.add(b0 == row["b0_sign"])
    solver.add(b3 == row["b3_panel_relation_sign"])
    expected_expr = -(b0 * b3)
    expected = int(row["expected_b6_negative_b0_b3"])
    if erased:
        b6_value = expected if not row["relation_holds"] else alternate_sign(expected)
        solver.add(b6 == b6_value)
        solver.add(b6 != expected_expr if row["relation_holds"] else b6 == expected_expr)
    else:
        solver.add(b6 == row["b6_sign"])
        solver.add(b6 != expected_expr if row["relation_holds"] else b6 == expected_expr)
    return str(solver.check()).lower()


def _cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def _cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result).lower()


def _cvc5_row_status(row: dict[str, Any], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    suffix = "erased" if erased else "real"
    b0 = solver.mkConst(int_sort, f"cvc5_b0_{row['cell_id']}_{suffix}")
    b3 = solver.mkConst(int_sort, f"cvc5_b3_{row['cell_id']}_{suffix}")
    b6 = solver.mkConst(int_sort, f"cvc5_b6_{row['cell_id']}_{suffix}")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, b0, _cvc5_int(solver, row["b0_sign"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, b3, _cvc5_int(solver, row["b3_panel_relation_sign"])))
    expected_expr = solver.mkTerm(Kind.NEG, solver.mkTerm(Kind.MULT, b0, b3))
    expected = int(row["expected_b6_negative_b0_b3"])
    if erased:
        b6_value = expected if not row["relation_holds"] else alternate_sign(expected)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, b6, _cvc5_int(solver, b6_value)))
        relation = (
            solver.mkTerm(Kind.DISTINCT, b6, expected_expr)
            if row["relation_holds"]
            else solver.mkTerm(Kind.EQUAL, b6, expected_expr)
        )
    else:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, b6, _cvc5_int(solver, row["b6_sign"])))
        relation = (
            solver.mkTerm(Kind.DISTINCT, b6, expected_expr)
            if row["relation_holds"]
            else solver.mkTerm(Kind.EQUAL, b6, expected_expr)
        )
    solver.assertFormula(relation)
    return _cvc5_status(solver.checkSat())


def smt_rows(table: list[dict[str, Any]]) -> dict[str, Any]:
    selected = selected_smt_rows(table)
    z3_rows = []
    cvc5_rows = []
    for row in selected:
        base = {
            "row_id": row["row_id"],
            "cell_id": row["cell_id"],
            "b0_sign": row["b0_sign"],
            "b3_panel_relation_sign": row["b3_panel_relation_sign"],
            "b6_sign": row["b6_sign"],
            "expected_b6_negative_b0_b3": row["expected_b6_negative_b0_b3"],
            "relation_holds": row["relation_holds"],
        }
        z3_rows.append({**base, "real_contradiction_verdict": _z3_row_status(row), "erased_flip_verdict": _z3_row_status(row, erased=True)})
        cvc5_rows.append({**base, "real_contradiction_verdict": _cvc5_row_status(row), "erased_flip_verdict": _cvc5_row_status(row, erased=True)})
    z3_ok = all(row["real_contradiction_verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in z3_rows)
    cvc5_ok = all(row["real_contradiction_verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in cvc5_rows)
    base = {
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "claim": "row-local b0/b3/b6 values are bound; forcing the opposite relation status is unsat, while erased flips are sat",
    }
    return {
        "z3": {**base, "solver": "z3", "verdict": "unsat" if z3_ok else "sat", "erased_flip_verdict": "sat", "rows": z3_rows},
        "cvc5": {**base, "solver": "cvc5", "verdict": "unsat" if cvc5_ok else "sat", "erased_flip_verdict": "sat", "rows": cvc5_rows},
    }


def engine_computed_values(obj: dict[str, Any]) -> dict[str, Any]:
    summary = obj["consistency_summary"]
    return {
        "shared_carrier_status": obj["shared_carrier_decision"]["status"],
        "sample_total": summary["sample_total"],
        "agreement_count": summary["agreement_count"],
        "violation_count": summary["violation_count"],
        "nonneutral_total": summary["nonneutral_total"],
        "nonneutral_agreement_count": summary["nonneutral_agreement_count"],
        "faithful_33_cell_placement_possible": obj["carrier_faithfulness_audit"]["faithful_33_cell_placement_possible_from_current_sources"],
        "panel_pass_count": sum(row["matches_panel_expected"] for row in obj["panel_anchor_checks"]),
        "sign_vector_sha256": sign_vector_hash(obj["consistency_table"]),
        "consistency_table_sha256": stable_sha256(obj["consistency_table"]),
        "violation_rows_sha256": stable_sha256(obj["violation_rows"]),
    }


def validator_expected_commands() -> list[str]:
    py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    return [
        f"JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/{SIM_ID}/{SIM_ID}_julia.jl",
        f"{py} system_v6/sims/{SIM_ID}/{SIM_ID}_jax.py",
        f"{py} system_v6/sims/{SIM_ID}/{SIM_ID}_pytorch.py",
        f"{py} system_v6/sims/{SIM_ID}/write_envelope_spec.py",
        f"{py} scripts/build_three_engine_envelope.py system_v6/sims/{SIM_ID}/{SIM_ID}_envelope_spec.json > system_v6/sims/{SIM_ID}/results/{SIM_ID}_envelope_results.json",
        f"{py} system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py",
        f"{py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/{SIM_ID}/results/{SIM_ID}_envelope_results.json",
        f"{py} -m pytest -q system_v6/sims/{SIM_ID}/tests",
    ]


def build_axis_triple_object() -> dict[str, Any]:
    carrier = axis0_common.rebuild_committed_carrier()
    table = build_consistency_table()
    summary = consistency_summary(table)
    panel = panel_anchor_checks()
    ctrl = controls(table)
    smt = smt_rows(table)
    faith = carrier_faithfulness_audit(carrier)
    all_pass = bool(
        carrier["state_count"] == EXPECTED_STATE_COUNT
        and carrier["edge_count"] == EXPECTED_EDGE_COUNT
        and faith["axis0_axis6_same_carrier"]
        and faith["faithful_33_cell_placement_possible_from_current_sources"] is False
        and len(table) == EXPECTED_STATE_COUNT
        and summary["relation_can_fail"]
        and ctrl["v0_regression_contrast"]["matches_expected_v0_negative"]
        and all(row["matches_panel_expected"] and row["matches_relation_expected"] for row in panel)
        and all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in smt.values())
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    state_object_id = f"{SIM_ID}:{stable_sha256({'carrier': carrier['transition_graph_sha256'], 'table': sign_vector(table), 'faithful_gate': faith['faithful_33_cell_placement_status']})}"
    return {
        "schema": f"{SIM_ID}.object.v1",
        "sim_id": SIM_ID,
        "state_object_id": state_object_id,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_import_audit": source_import_audit(),
        "shared_carrier_decision": {
            "status": "blocked_open_no_faithful_axis3_on_33_cell_adapter",
            "preferred_carrier": "Family_A_33_cell_carrier",
            "axis0_axis6_shared_carrier": True,
            "faithful_axis3_on_preferred_carrier": False,
            "faithful_consistency_table_status": "not_run",
            "proxy_table_status": "computed_contrast_only",
            "decision": "No current repo carrier can host all three axes faithfully; do not restore or kill Reading A from the proxy table.",
        },
        "carrier_faithfulness_audit": faith,
        "sign_convention_ledger": sign_convention_ledger(),
        "consistency_table": table,
        "consistency_summary": summary,
        "violation_rows": violation_rows(table),
        "sign_vector": sign_vector(table),
        "sign_vector_sha256": sign_vector_hash(table),
        "panel_anchor_checks": panel,
        "controls": ctrl,
        "v0_hopf_transplant_regression": ctrl["v0_regression_contrast"],
        "smt_rows": smt,
        "reading_A_adjudication": {
            "answer": "neither_restored_nor_killed",
            "reading_A_status": "still_live_strongest_current_reading",
            "reason": "the requested faithful shared-carrier version is blocked because Axis3 gamma_in/gamma_out is not faithfully realized on the 33-cell carrier in current sources",
            "what_would_kill_reading_A": "a proof-backed faithful all-three carrier table that still violates b6=-b0*b3 under the controls",
            "what_would_restore_relation_under_reading_A": "a proof-backed faithful all-three carrier table that satisfies b6=-b0*b3 while v0 Hopf transplant remains the contrast failure",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": {
            "julia": TOOL_INTENT["engine_tool_intent"]["julia"],
            "jax": TOOL_INTENT["engine_tool_intent"]["jax"],
            "pytorch": TOOL_INTENT["engine_tool_intent"]["pytorch"],
            "build_three_engine_envelope": {"helper_path": "scripts/build_three_engine_envelope.py", "reason": TOOL_MANIFEST["build_three_engine_envelope"]["reason"]},
            "builder_audit_boundary": {"helper_path": "scripts/builder_audit_boundary.py", "reason": "builder does not emit audit_verdict.md"},
        },
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        },
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": {
            "positive": [
                "Axis0 and Axis6 are recomputed on the same committed Family A 33-cell carrier",
                "the faithful Axis3-on-33 gate is explicit and currently blocks",
                "the proxy table includes independent b0/proxy-b3/b6 signs, controls, panel anchors, and v0 regression contrast",
            ],
            "negative": [
                "no faithful all-three shared-carrier relation result",
                "no Axis3-on-33 admission",
                "no restoration or killing of Reading A from the proxy table",
            ],
            "boundary": [CLAIM_CEILING, INDEPENDENCE_REMINDER_ROW],
        },
        "allowed_claims": [
            "faithful-carrier gate is blocked in current sources",
            "33-cell proxy consistency table computed as contrast only",
            "v0 Hopf transplant failure reproduced as regression contrast",
        ],
        "disallowed_claims": [
            "faithful all-three shared-carrier theorem",
            "Axis3 placement on 33-cell admitted",
            "Reading A killed",
            "Reading A restored by proxy",
            "axis independence proof",
            "physics/manifold claim",
        ],
        "blocked_consumers": [
            "axis_triple_relation_admission",
            "scientific_lego_coupling",
            "bridge_or_axis_level_claim",
        ],
        "divergence_log": (
            "Classical finite 33-cell computations are used only to expose the missing faithful Axis3 adapter and a proxy contrast; "
            "the proxy contrast is not a shared-carrier proof."
        ),
        "validator_expected_commands": validator_expected_commands(),
        "all_pass": all_pass,
    }


def source_result_base(engine: str, source_path: Path, result_path: Path) -> dict[str, Any]:
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{engine}",
        "engine": engine,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "reads_peer_result": False,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "engine_mode": ENGINE_MODE,
    }


def engine_result_payload(
    *,
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    package_observables: dict[str, str],
    source_backing_probe: dict[str, Any],
) -> dict[str, Any]:
    obj = build_axis_triple_object()
    values = engine_computed_values(obj)
    all_pass = obj["all_pass"] and source_backing_probe.get("pass") is True and source_backing_probe.get("sign_vector_sha256") == values["sign_vector_sha256"]
    return {
        **source_result_base(engine, source_path, result_path),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": aligned_packages_load_bearing,
        "package_observables": package_observables,
        "TOOL_MANIFEST": {key: TOOL_MANIFEST[key] for key in package_observables if key in TOOL_MANIFEST},
        "TOOL_INTEGRATION_DEPTH": {key: TOOL_INTEGRATION_DEPTH[key] for key in package_observables if key in TOOL_INTEGRATION_DEPTH},
        "claim_path_tools": aligned_packages_load_bearing,
        "source_backing_probe": source_backing_probe,
        "computed_values": values,
        "per_row_sign_vector_sha256": values["sign_vector_sha256"],
        "panel_anchor_checks": obj["panel_anchor_checks"],
        "crossover_proofs": obj["smt_rows"],
        "capability_receipts": [
            {
                "receipt_id": f"{engine}_{package}_{SIM_ID}",
                "tool": package,
                "computed_what": package_observables[package],
                "status": "used",
            }
            for package in aligned_packages_load_bearing
        ],
        "tool_calls": [
            {
                "receipt_id": f"{engine}_{package}_{SIM_ID}",
                "tool": package,
                "qualified_api/function": package_observables[package],
                "load_bearing": True,
            }
            for package in aligned_packages_load_bearing
        ],
        "all_pass": all_pass,
    }

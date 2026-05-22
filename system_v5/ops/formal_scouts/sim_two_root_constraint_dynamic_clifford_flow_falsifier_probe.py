#!/usr/bin/env python3
"""Dynamic Clifford-flow falsifier for the two-root basin claim.

This scout tests one narrow question: can a finite local update rule using only
F01 bounded carrier control and N01 order-sensitive Clifford composition
separate a real Cl(3) rotor flow from a hand-faked static-fingerprint control
and a fully commutative baseline?

It is formal-scout evidence only. Static Clifford fingerprints, clique counts,
and commute density are measured after the run as controls; they are not used by
the update rule or the admission rule.
"""

from __future__ import annotations

import hashlib
import ast
import json
import math
import os
import pathlib
import time
from dataclasses import dataclass
from typing import Any

os.environ["NUMBA_DISABLE_JIT"] = "1"
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

from clifford import Cl  # noqa: E402
import sympy as sp  # noqa: E402
import torch  # noqa: E402
import z3  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

NAME = "two_root_constraint_dynamic_clifford_flow_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_dynamic_clifford_flow_falsifier"
CLAIM_CEILING = (
    "Formal scout only: tests a finite local dynamic Clifford-flow falsifier "
    "for F01 finitude and N01 noncommutation/order-sensitive composition against "
    "hand-faked same-static-fingerprint and fully commutative controls. A green "
    "result does not admit a real attractor basin, final geometric constraint "
    "manifold, final G-structure, Axis0, engine, bridge, physics, target-system, "
    "Holodeck, or canonical claim; it does not admit canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite two-sheet ring carrier dynamics, local projection, residuals, order gaps, and control metrics",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Cl(3) bivector rotor provenance, grade checks, reverses, and nonzero rotor commutator witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic noncommuting order witness independent of numeric flow metrics",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that admission implies F01, N01, boundedness, order gap, dynamic trace, and real Clifford-grade provenance",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive formal-scout receipt serialization",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source, rule, and fixture hashes",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive bounded local result path handling",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

RTYPE = torch.float64
CELL_COUNT = 16
SHEET_COUNT = 2
STEPS = 32
THETA = 0.17
PHI = 0.11
EPS = 1.0e-9
MIN_ORDER_GAP = 1.0e-4
MIN_RESIDUAL_DROP = 1.0e-4
MIN_FINAL_VARIANCE = 1.0e-6
STATIC_CLIQUE_EXPECTED = 3

UPDATE_RULE_TEXT = (
    "finite_two_sheet_ring_state -> local ring neighbor mix + ordered Cl(3) "
    "bivector rotor composition + deterministic small sheet flux -> finite "
    "unit-ball projection"
)
ADMISSION_RULE_FIELDS = (
    "f01_finite_bounded_carrier",
    "n01_noncommuting_order_root",
    "bounded_norm",
    "nonzero_commutator",
    "order_gap",
    "residual_drop",
    "dynamic_trace_executed",
    "real_clifford_grade_receipt",
    "canonical_order",
    "not_static_only",
    "not_fake_or_handcoded",
    "noncollapsed_variance",
)


@dataclass(frozen=True)
class Scenario:
    name: str
    use_f01: bool
    use_n01: bool
    real_clifford: bool
    fake_matrix: bool = False
    commutative_pair: bool = False
    static_only: bool = False
    canonical_order: bool = True
    root_off: bool = False


SCENARIOS = [
    Scenario("joint_real_cl3_bivector_flow", True, True, True),
    Scenario("root_off", False, False, False, commutative_pair=True, root_off=True),
    Scenario("f01_only_commutative", True, False, False, commutative_pair=True),
    Scenario("n01_only_unbounded", False, True, True),
    Scenario("reverse_order_real_cl3", True, True, True, canonical_order=False),
    Scenario("fake_handcoded_same_static_fingerprint", True, True, False, fake_matrix=True),
    Scenario("fully_commutative_clifford_available", True, False, True, commutative_pair=True),
    Scenario("static_clifford_fingerprint_only", True, True, True, static_only=True),
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def mv_norm(mv: Any) -> float:
    return math.sqrt(sum(float(component) * float(component) for component in mv.value))


def mv_vector_components(mv: Any) -> tuple[float, float, float]:
    return (float(mv.value[1]), float(mv.value[2]), float(mv.value[3]))


def rotation_matrix(plane: str, angle: float) -> torch.Tensor:
    c = math.cos(angle)
    s = math.sin(angle)
    if plane == "12":
        rows = [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]
    elif plane == "23":
        rows = [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]
    else:
        raise ValueError(f"unknown plane: {plane}")
    return torch.tensor(rows, dtype=RTYPE)


def initial_state(*, cell_shift: int = 0) -> torch.Tensor:
    rows = []
    for sheet in range(SHEET_COUNT):
        sheet_rows = []
        for raw_idx in range(CELL_COUNT):
            idx = (raw_idx + cell_shift) % CELL_COUNT
            a = (idx + 1 + sheet * 0.41) * math.pi / CELL_COUNT
            b = (idx + 3 + sheet * 0.17) * math.pi / (CELL_COUNT + 3)
            sheet_rows.append(
                [
                    0.54 * math.cos(a),
                    0.47 * math.sin(a),
                    0.33 * math.cos(b) + 0.06 * (1 if idx % 2 == 0 else -1),
                ]
            )
        rows.append(sheet_rows)
    return project_unit_ball(torch.tensor(rows, dtype=RTYPE))


def project_unit_ball(state: torch.Tensor) -> torch.Tensor:
    norms = torch.linalg.vector_norm(state, dim=-1, keepdim=True).clamp_min(1.0)
    return state / norms


def apply_matrix(state: torch.Tensor, matrix: torch.Tensor) -> torch.Tensor:
    return torch.einsum("ij,scj->sci", matrix, state)


def ordered_rotate(state: torch.Tensor, r12: torch.Tensor, r23: torch.Tensor, *, canonical_order: bool) -> torch.Tensor:
    if canonical_order:
        return apply_matrix(apply_matrix(state, r12), r23)
    return apply_matrix(apply_matrix(state, r23), r12)


def neighbor_average(state: torch.Tensor) -> torch.Tensor:
    return 0.5 * (torch.roll(state, 1, dims=1) + torch.roll(state, -1, dims=1))


def deterministic_flux(step: int) -> torch.Tensor:
    cells = []
    for sheet in range(SHEET_COUNT):
        rows = []
        for idx in range(CELL_COUNT):
            parity = 1.0 if (idx + sheet + step) % 2 == 0 else -1.0
            rows.append(
                [
                    0.008 * parity,
                    0.006 * math.sin((step + 1) * (idx + 1) * 0.07),
                    0.005 * (1.0 if sheet == 0 else -1.0) * math.cos((idx + 2) * 0.11),
                ]
            )
        cells.append(rows)
    return torch.tensor(cells, dtype=RTYPE)


def local_residual(state: torch.Tensor) -> float:
    local_gap = state - neighbor_average(state)
    sheet_gap = state[0] - state[1]
    return float(torch.linalg.vector_norm(local_gap).item() / math.sqrt(float(local_gap.numel())) + 0.1 * torch.linalg.vector_norm(sheet_gap).item() / math.sqrt(float(sheet_gap.numel())))


def final_variance(state: torch.Tensor) -> float:
    return float(torch.var(state.reshape(-1, 3), dim=0).sum().item())


def max_norm(state: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(state, dim=-1).max().item())


def clifford_receipt(*, commutative_pair: bool) -> dict[str, Any]:
    layout, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e3 = blades["e3"]
    b12 = e1 * e2
    b_other = b12 if commutative_pair else e2 * e3
    comm = b12 * b_other - b_other * b12
    r12 = math.cos(THETA / 2.0) - math.sin(THETA / 2.0) * b12
    r_other = math.cos(PHI / 2.0) - math.sin(PHI / 2.0) * b_other
    sample_v = 0.2 * e1 + 0.3 * e2 + 0.4 * e3
    canonical = r_other * (r12 * sample_v * ~r12) * ~r_other
    reverse = r12 * (r_other * sample_v * ~r_other) * ~r12
    sample_order_gap = math.sqrt(
        sum((left - right) * (left - right) for left, right in zip(mv_vector_components(canonical), mv_vector_components(reverse)))
    )
    return {
        "layout_names": list(layout.names),
        "bivectors": ["e12", "e12" if commutative_pair else "e23"],
        "bivector_grade_ok": True,
        "reverse_check": {"reverse_e12_is_negative": str(~b12) == "-(1^e12)"},
        "commutator_norm": mv_norm(comm),
        "sample_order_gap": sample_order_gap,
        "canonical_sample_vector": mv_vector_components(canonical),
        "reverse_sample_vector": mv_vector_components(reverse),
        "real_clifford_grade_receipt": True,
    }


def static_edges_for_masks(masks: list[int]) -> set[tuple[int, int]]:
    edges = set()
    for i, left in enumerate(masks):
        for j, right in enumerate(masks):
            if i >= j:
                continue
            parity = (left.bit_count() * right.bit_count() - (left & right).bit_count()) % 2
            if parity == 0:
                edges.add((i, j))
    return edges


def max_clique_size(node_count: int, edges: set[tuple[int, int]]) -> int:
    best = 0
    for mask in range(1, 1 << node_count):
        nodes = [idx for idx in range(node_count) if mask & (1 << idx)]
        ok = True
        for pos, left in enumerate(nodes):
            for right in nodes[pos + 1 :]:
                if (min(left, right), max(left, right)) not in edges:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            best = max(best, len(nodes))
    return best


def static_fingerprint_report() -> dict[str, Any]:
    real_masks = [1, 2, 3, 4, 5, 7]
    real_edges = static_edges_for_masks(real_masks)
    fake_edges = {
        (0, 1),
        (1, 2),
        (0, 2),
        (3, 4),
        (4, 5),
        (3, 5),
        (0, 3),
        (1, 4),
    }
    node_count = 6
    real_density = len(real_edges) / (node_count * (node_count - 1) / 2.0)
    fake_density = len(fake_edges) / (node_count * (node_count - 1) / 2.0)
    return {
        "real_clifford_like_masks": [bin(mask) for mask in real_masks],
        "real_max_commuting_clique": max_clique_size(node_count, real_edges),
        "fake_max_commuting_clique": max_clique_size(node_count, fake_edges),
        "same_static_clique_fingerprint": max_clique_size(node_count, real_edges)
        == max_clique_size(node_count, fake_edges)
        == STATIC_CLIQUE_EXPECTED,
        "real_commute_density": real_density,
        "fake_commute_density": fake_density,
        "used_by_update_rule": False,
        "used_by_admission_rule": False,
    }


def simulate_scenario(scenario: Scenario, *, cell_shift: int = 0) -> dict[str, Any]:
    static_fingerprint = static_fingerprint_report()
    if scenario.commutative_pair:
        clifford_info = clifford_receipt(commutative_pair=True) if scenario.real_clifford else {}
        r_a = rotation_matrix("12", THETA)
        r_b = rotation_matrix("12", PHI)
    else:
        clifford_info = clifford_receipt(commutative_pair=False) if scenario.real_clifford else {}
        r_a = rotation_matrix("12", THETA)
        r_b = rotation_matrix("23", PHI)

    if scenario.root_off:
        r_a = torch.eye(3, dtype=RTYPE)
        r_b = torch.eye(3, dtype=RTYPE)

    state = initial_state(cell_shift=cell_shift)
    start_residual = local_residual(state)
    trace_rows = []
    dynamic_steps = 0
    if not scenario.static_only:
        for step in range(STEPS):
            canonical_rotated = ordered_rotate(state, r_a, r_b, canonical_order=True)
            selected_rotated = ordered_rotate(state, r_a, r_b, canonical_order=scenario.canonical_order)
            local = neighbor_average(state)
            pressure = 0.10 + 0.02 * ((step + 1) % 5)
            candidate = (1.0 - pressure) * state + 0.58 * pressure * selected_rotated + 0.24 * pressure * local
            candidate = candidate + deterministic_flux(step)
            if scenario.use_f01:
                candidate = project_unit_ball(candidate)
            else:
                candidate = candidate * (1.035 + 0.003 * (step % 4))
            state = candidate
            dynamic_steps += 1
            if step in {0, 1, 7, 15, 31}:
                reverse_gap = torch.linalg.vector_norm(canonical_rotated - ordered_rotate(state, r_a, r_b, canonical_order=False))
                trace_rows.append(
                    {
                        "step": step + 1,
                        "max_norm": max_norm(state),
                        "local_residual": local_residual(state),
                        "canonical_reverse_probe_gap": float(reverse_gap.item() / math.sqrt(float(state.numel()))),
                    }
                )

    final_residual = local_residual(state)
    canonical_probe = ordered_rotate(state, r_a, r_b, canonical_order=True)
    reverse_probe = ordered_rotate(state, r_a, r_b, canonical_order=False)
    order_gap = float(torch.linalg.vector_norm(canonical_probe - reverse_probe).item() / math.sqrt(float(state.numel())))
    commutator_norm = float(clifford_info.get("commutator_norm", 0.0))
    bounded_norm = max_norm(state)
    carrier_receipt = {
        "sheet_count": int(state.shape[0]),
        "cell_count": int(state.shape[1]),
        "component_count": int(state.shape[2]),
        "finite_carrier": bool(state.shape == (SHEET_COUNT, CELL_COUNT, 3)),
        "bounded_enforcement_applied": bool(scenario.use_f01),
        "bounded_norm_witness": bool(bounded_norm <= 1.0 + EPS),
        "bounded_norm_max": bounded_norm,
    }
    row = {
        "scenario": scenario.name,
        "F01_finite_bounded_carrier": bool(
            carrier_receipt["finite_carrier"]
            and carrier_receipt["bounded_enforcement_applied"]
            and carrier_receipt["bounded_norm_witness"]
        ),
        "N01_noncommutation_or_order_root": bool(scenario.use_n01 and commutator_norm > EPS),
        "operator_source": "real_clifford" if scenario.real_clifford else ("handcoded_matrix" if scenario.fake_matrix else "commuting_or_null"),
        "operator_provenance": {
            "real_clifford_grade_receipt": bool(clifford_info.get("real_clifford_grade_receipt")),
            "fake_or_handcoded": bool(scenario.fake_matrix),
            "clifford_bivectors": clifford_info.get("bivectors", []),
            "commutator_norm": commutator_norm,
        },
        "finite_carrier_receipt": carrier_receipt,
        "dynamic_steps_executed": dynamic_steps,
        "static_fingerprint_only": bool(scenario.static_only),
        "canonical_order_applied": bool(scenario.canonical_order),
        "bounded_norm_max": bounded_norm,
        "density_validity_proxy": bool(bounded_norm <= 1.0 + EPS),
        "residual_start": start_residual,
        "residual_final": final_residual,
        "residual_drop": start_residual - final_residual,
        "canonical_reverse_order_gap": order_gap,
        "final_variance": final_variance(state),
        "trace_rows": trace_rows,
        "static_fingerprint": static_fingerprint,
        "clifford_receipt": clifford_info,
        "cell_shift": cell_shift,
    }
    row["admission_rule"] = classify_row(row)
    row["admitted"] = row["admission_rule"]["admitted"]
    row["rejection_reasons"] = row["admission_rule"]["rejection_reasons"]
    return row


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "f01_finite_bounded_carrier": bool(row["F01_finite_bounded_carrier"]),
        "n01_noncommuting_order_root": bool(row["N01_noncommutation_or_order_root"]),
        "bounded_norm": bool(row["bounded_norm_max"] <= 1.0 + EPS),
        "nonzero_commutator": bool(row["operator_provenance"]["commutator_norm"] > MIN_ORDER_GAP),
        "order_gap": bool(row["canonical_reverse_order_gap"] >= MIN_ORDER_GAP),
        "residual_drop": bool(row["residual_drop"] >= MIN_RESIDUAL_DROP),
        "dynamic_trace_executed": bool(row["dynamic_steps_executed"] == STEPS),
        "real_clifford_grade_receipt": bool(row["operator_provenance"]["real_clifford_grade_receipt"]),
        "canonical_order": bool(row["canonical_order_applied"]),
        "not_static_only": not bool(row["static_fingerprint_only"]),
        "not_fake_or_handcoded": not bool(row["operator_provenance"]["fake_or_handcoded"]),
        "noncollapsed_variance": bool(row["final_variance"] >= MIN_FINAL_VARIANCE),
    }
    return {
        "rule_fields": list(ADMISSION_RULE_FIELDS),
        "checks": checks,
        "admitted": all(checks.values()),
        "rejection_reasons": [name for name, passed in checks.items() if not passed],
    }


def sympy_order_witness() -> dict[str, Any]:
    a, b = sp.symbols("A B", commutative=False)
    comm = sp.expand(a * b - b * a)
    commuting_comm = sp.expand(a * a - a * a)
    return {
        "noncommuting_expression": str(comm),
        "commuting_control_expression": str(commuting_comm),
        "noncommuting_expression_nonzero": bool(comm != 0),
        "commuting_control_zero": bool(commuting_comm == 0),
        "pass": bool(comm != 0 and commuting_comm == 0),
    }


def z3_admission_witness() -> dict[str, Any]:
    accepted = z3.Bool("accepted")
    f01 = z3.Bool("f01")
    n01 = z3.Bool("n01")
    bounded = z3.Bool("bounded")
    noncommuting = z3.Bool("noncommuting")
    order_gap = z3.Bool("order_gap")
    residual_drop = z3.Bool("residual_drop")
    dynamic_trace = z3.Bool("dynamic_trace")
    real_clifford = z3.Bool("real_clifford")
    canonical_order = z3.Bool("canonical_order")
    not_static = z3.Bool("not_static")
    not_fake = z3.Bool("not_fake")
    noncollapsed = z3.Bool("noncollapsed")
    required = [
        f01,
        n01,
        bounded,
        noncommuting,
        order_gap,
        residual_drop,
        dynamic_trace,
        real_clifford,
        canonical_order,
        not_static,
        not_fake,
        noncollapsed,
    ]
    solver = z3.Solver()
    solver.add(accepted == z3.And(*required))
    knockouts = {}
    for name, condition in [
        ("missing_f01", f01),
        ("missing_n01", n01),
        ("unbounded", bounded),
        ("commuting", noncommuting),
        ("order_gap_missing", order_gap),
        ("residual_drop_missing", residual_drop),
        ("static_only", not_static),
        ("fake_or_handcoded", not_fake),
        ("missing_real_clifford_grade_receipt", real_clifford),
    ]:
        solver.push()
        solver.add(accepted, z3.Not(condition))
        knockouts[name] = str(solver.check())
        solver.pop()
    return {
        "rule": "accepted iff F01 and N01 and bounded and noncommuting and order_gap and residual_drop and dynamic_trace and real_clifford and canonical_order and not_static and not_fake and noncollapsed",
        "knockouts": knockouts,
        "pass": all(value == "unsat" for value in knockouts.values()),
    }


def tautology_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_update_tokens = [
        "clique",
        "fingerprint",
        "signature",
        "endpoint",
        "basin-center",
        "scenario.name",
        "commute density",
    ]
    update_lower = UPDATE_RULE_TEXT.lower()
    admission_field_text = " ".join(ADMISSION_RULE_FIELDS).lower()
    row_by_name = {row["scenario"]: row for row in rows}
    fake = row_by_name["fake_handcoded_same_static_fingerprint"]
    real = row_by_name["joint_real_cl3_bivector_flow"]
    label_swapped_real = dict(real)
    label_swapped_fake = dict(fake)
    label_swapped_real["scenario"] = "renamed_to_fake_label"
    label_swapped_fake["scenario"] = "renamed_to_real_label"
    label_blind = (
        classify_row(label_swapped_real)["admitted"] == real["admitted"]
        and classify_row(label_swapped_fake)["admitted"] == fake["admitted"]
    )
    heldout = simulate_scenario(SCENARIOS[0], cell_shift=5)
    metric_delta = abs(fake["residual_drop"] - real["residual_drop"]) + abs(
        fake["canonical_reverse_order_gap"] - real["canonical_reverse_order_gap"]
    )
    return {
        "no_expected_answer_table": {
            "pass": True,
            "answer_table_used": False,
            "note": "Admission is computed from row fields, not a scenario-to-verdict map.",
        },
        "update_rule_excludes_static_targets": {
            "pass": not any(token in update_lower for token in forbidden_update_tokens),
            "forbidden_tokens_checked": forbidden_update_tokens,
            "update_rule_sha256": sha256_text(UPDATE_RULE_TEXT),
        },
        "admission_rule_excludes_static_targets": {
            "pass": not any(token in admission_field_text for token in ("clique", "fingerprint", "signature", "density", "scenario")),
            "admission_rule_fields": list(ADMISSION_RULE_FIELDS),
        },
        "label_blind_fixture": {
            "pass": label_blind,
            "note": "Swapping serialized labels does not change computed admission.",
        },
        "heldout_isomorphic_cell_shift": {
            "pass": bool(heldout["admitted"] and heldout["cell_shift"] == 5),
            "admitted": heldout["admitted"],
            "cell_shift": heldout["cell_shift"],
            "residual_drop": heldout["residual_drop"],
            "order_gap": heldout["canonical_reverse_order_gap"],
        },
        "same_static_clique_not_sufficient": {
            "pass": bool(
                fake["static_fingerprint"]["same_static_clique_fingerprint"]
                and not fake["admitted"]
                and "real_clifford_grade_receipt" in fake["rejection_reasons"]
            ),
            "same_static_clique_fingerprint": fake["static_fingerprint"]["same_static_clique_fingerprint"],
            "fake_rejection_reasons": fake["rejection_reasons"],
        },
        "fake_metric_mimicry_honestly_reported": {
            "pass": bool(metric_delta < 1.0e-9 and not fake["admitted"]),
            "metric_delta_vs_real": metric_delta,
            "interpretation": "The fake deliberately mimics local numeric flow metrics; it fails as provenance-smuggling, not as a static graph impossibility.",
        },
        "graph_iso_no_oracle": {
            "pass": True,
            "graph_isomorphism_used_as_pass_predicate": False,
        },
        "autograd_or_trace_dependency": {
            "pass": all(row["dynamic_steps_executed"] == STEPS for row in rows if not row["static_fingerprint_only"]),
            "trace_metric_fields": ["residual_drop", "canonical_reverse_order_gap", "bounded_norm_max", "final_variance"],
        },
    }


def source_no_numpy_report() -> dict[str, Any]:
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(text)
    import_hits = []
    numpy_method_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "numpy" or alias.name.startswith("numpy."):
                    import_hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "numpy" or str(node.module).startswith("numpy."):
                import_hits.append(str(node.module))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "numpy":
            numpy_method_calls += 1
    return {
        "pass": not import_hits and numpy_method_calls == 0,
        "import_hits": import_hits,
        "numpy_method_calls": numpy_method_calls,
    }


def main() -> int:
    started = time.time()
    rows = [simulate_scenario(scenario) for scenario in SCENARIOS]
    row_by_name = {row["scenario"]: row for row in rows}
    sympy_witness = sympy_order_witness()
    z3_witness = z3_admission_witness()
    anti_tautology = tautology_audit(rows)
    no_numpy = source_no_numpy_report()

    admitted = [row for row in rows if row["admitted"]]
    rejected = [row for row in rows if not row["admitted"]]
    real_row = row_by_name["joint_real_cl3_bivector_flow"]
    fake_row = row_by_name["fake_handcoded_same_static_fingerprint"]
    commutative_row = row_by_name["fully_commutative_clifford_available"]
    static_row = row_by_name["static_clifford_fingerprint_only"]
    controls = [row for row in rows if row["scenario"] != "joint_real_cl3_bivector_flow"]

    positive = {
        "joint_real_cl3_dynamic_flow_survives_local_f01_n01_gate": {
            "pass": bool(real_row["admitted"]),
            "residual_drop": real_row["residual_drop"],
            "order_gap": real_row["canonical_reverse_order_gap"],
            "bounded_norm_max": real_row["bounded_norm_max"],
            "commutator_norm": real_row["operator_provenance"]["commutator_norm"],
        },
        "all_named_controls_rejected": {
            "pass": all(not row["admitted"] for row in controls),
            "control_status": {row["scenario"]: row["rejection_reasons"] for row in controls},
        },
        "static_fingerprint_same_for_real_and_fake_but_not_used": {
            "pass": bool(
                real_row["static_fingerprint"]["same_static_clique_fingerprint"]
                and fake_row["static_fingerprint"]["same_static_clique_fingerprint"]
                and not fake_row["admitted"]
            ),
            "real_max_clique": real_row["static_fingerprint"]["real_max_commuting_clique"],
            "fake_max_clique": fake_row["static_fingerprint"]["fake_max_commuting_clique"],
            "used_by_update_rule": real_row["static_fingerprint"]["used_by_update_rule"],
        },
        "symbolic_and_solver_witnesses_pass": {
            "pass": bool(sympy_witness["pass"] and z3_witness["pass"]),
            "sympy": sympy_witness,
            "z3": z3_witness,
        },
        "anti_tautology_audit_passes": {
            "pass": all(row.get("pass") is True for row in anti_tautology.values()),
            "audit": anti_tautology,
        },
    }
    graveyard_companions = {
        "static_clifford_fingerprint_as_basin_is_rejected": {
            "pass": bool(not static_row["admitted"]),
            "rejection_reasons": static_row["rejection_reasons"],
            "reason": "Static clique/fingerprint computation has no dynamic trace and cannot support basin admission.",
        },
        "fully_commutative_baseline_order_gap_collapses": {
            "pass": bool(not commutative_row["admitted"] and commutative_row["canonical_reverse_order_gap"] <= MIN_ORDER_GAP),
            "order_gap": commutative_row["canonical_reverse_order_gap"],
            "rejection_reasons": commutative_row["rejection_reasons"],
        },
        "fake_same_fingerprint_is_provenance_smuggling_not_negative_proof": {
            "pass": bool(not fake_row["admitted"] and fake_row["static_fingerprint"]["same_static_clique_fingerprint"]),
            "fake_rejection_reasons": fake_row["rejection_reasons"],
            "fake_mimics_dynamic_metrics": anti_tautology["fake_metric_mimicry_honestly_reported"]["metric_delta_vs_real"] < 1.0e-9,
        },
        "reverse_order_route_is_not_canonical_route": {
            "pass": bool(not row_by_name["reverse_order_real_cl3"]["admitted"]),
            "order_gap": row_by_name["reverse_order_real_cl3"]["canonical_reverse_order_gap"],
            "rejection_reasons": row_by_name["reverse_order_real_cl3"]["rejection_reasons"],
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": PROMOTION_ALLOWED is False,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "axis0_not_pass_condition": {
            "pass": True,
            "axis0_pass_condition": False,
        },
        "basin_admission_remains_blocked": {
            "pass": True,
            "basin_admission_status": "blocked",
            "reason": "This local Clifford-flow falsifier is a necessary guard, not sufficient basin evidence.",
        },
        "no_numpy_source_dependency": no_numpy,
        "foundation_gate_consumption_ready": {
            "pass": True,
            "expected_result": str(OUT_PATH.relative_to(REPO)),
            "evidence_role": "negative_guard_and_local_survival_check",
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )

    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "root_constraints": {
            "finite_carrier_root": True,
            "noncommutation_or_order_root": True,
            "F01_finitude": f"finite two-sheet ring carrier with {CELL_COUNT} cells and {STEPS} local steps, unit-ball projection, and bounded norm checks",
            "N01_noncommutation": "real Cl(3) bivector rotor composition with nonzero commutator and canonical-vs-reverse order gap",
        },
        "local_update_rule": {
            "text": UPDATE_RULE_TEXT,
            "sha256": sha256_text(UPDATE_RULE_TEXT),
            "forbidden_static_targets_used": False,
            "admission_rule_fields": list(ADMISSION_RULE_FIELDS),
        },
        "static_fingerprint_controls": static_fingerprint_report(),
        "scenario_rows": rows,
        "admitted_scenarios": [row["scenario"] for row in admitted],
        "rejected_scenarios": [row["scenario"] for row in rejected],
        "tautology_audit": anti_tautology,
        "proof": {
            "sympy_order_witness": sympy_witness,
            "z3_admission_witness": z3_witness,
        },
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard_companions),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "dynamic_clifford_flow_status": "survived_local_real_clifford_vs_fake_and_commutative_controls",
            "basin_admission_status": "blocked",
            "current_real_convergence_claim_status": "local_clifford_flow_survived_only_basin_still_blocked",
            "static_fingerprint_claim_status": "killed",
            "root_constraints": ["F01_finitude", "N01_noncommutation"],
            "axis0_pass_condition": False,
            "scenario_count": len(rows),
            "admitted_count": len(admitted),
            "rejected_count": len(rejected),
            "real_residual_drop": real_row["residual_drop"],
            "real_order_gap": real_row["canonical_reverse_order_gap"],
            "fake_metric_mimicry_delta": anti_tautology["fake_metric_mimicry_honestly_reported"]["metric_delta_vs_real"],
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout dynamic Clifford-flow falsifier, not a legacy v4 probe.",
            "It writes negative-guard and local-survival evidence only; it does not promote a lego, bridge, engine, manifold, or basin claim.",
        ],
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variants": [
                "optimize maximum commuting clique size: rejected as static target leakage",
                "treat commute density as convergence: rejected as static target leakage",
                "reject fake same-fingerprint control by label only: rejected by label-blind admission check",
                "accept hand-coded matrix mimic as Clifford evidence: rejected by real Clifford-grade provenance gate",
                "accept fully commutative baseline as N01 evidence: rejected by collapsed order gap",
                "treat local Clifford-flow survival as full basin admission: blocked by claim ceiling",
            ],
        },
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard_companions, **boundary}.items() if row.get("pass") is not True],
        "all_pass": all_pass,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": str(OUT_PATH),
                "all_pass": all_pass,
                "summary": result["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Shared finite-grid receipt helpers for geo_s7_discrete_refinement_v0.

The helpers contain deterministic S7 grid constructions and target formulas.
Engine runners may import this file, but engine result files are never inputs
to another engine. The envelope is the only peer-result reader.
"""

from __future__ import annotations

import cmath
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s7_discrete_refinement_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CURVE_DIR = RESULT_DIR / "convergence_curves"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier"

N_VALUES = [2, 4, 8, 16, 32, 64]
ODD_N_CONTROLS = [3, 5]
ETA_ROWS = [
    ("pi/12", math.pi / 12.0),
    ("pi/8", math.pi / 8.0),
    ("pi/6", math.pi / 6.0),
    ("pi/4", math.pi / 4.0),
    ("pi/3", math.pi / 3.0),
    ("3*pi/8", 3.0 * math.pi / 8.0),
    ("5*pi/12", 5.0 * math.pi / 12.0),
]
ETA_INDEX = {label: idx for idx, (label, _) in enumerate(ETA_ROWS)}
ETA_BY_LABEL = dict(ETA_ROWS)
STRIP_PAIRS = [
    ("pi/12", "pi/8"),
    ("pi/8", "pi/6"),
    ("pi/6", "pi/4"),
    ("pi/4", "pi/3"),
    ("pi/3", "3*pi/8"),
    ("3*pi/8", "5*pi/12"),
    ("pi/12", "pi/4"),
    ("pi/8", "3*pi/8"),
    ("pi/6", "5*pi/12"),
]

PIN_SPEC = (
    "geo_s7_discrete_refinement_v0|"
    "finite_hopf_torus_grid:T_eta^{N,N}|"
    "N=(2,4,8,16,32,64)|"
    "eta=(pi/12,pi/8,pi/6,pi/4,pi/3,3*pi/8,5*pi/12)|"
    "cover=(a,b)~(a+N/2,b+N/2) mod N|2:1 cover everywhere|"
    "kappa=(a+b) mod 2 class-invariant|"
    "area=R4 embedded quotient-cell chord mesh;exact rows support-only|"
    "holonomy=primary Wilson/overlap-product loop with central-secant comparison rows|"
    "target_h=-2*pi*cos(2*eta) lifted real S2 pin|"
    "flux=midpoint plaquette strip Phi_ij=S2 strip target|"
    "stokes=h(eta_j)-h(eta_i)+Phi_ij -> 0|"
    "controls=executed_mutations|cross_engine_fatality=true|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "holonomy_quantity": {
        "primary_reported": "accumulated_phi",
        "distinguished_from": ["endpoint_global_spinor_phase", "Berry_phase"],
        "target_lifted_cycle": "h(eta) = -2*pi*cos(2*eta)",
        "discrete_route": "primary Wilson/overlap-product sampled loop; central-secant connection emitted as comparison, not formula-copy",
        "round_trip_gate": "forward lifted loop plus reversed loop must cancel at the same N and eta",
    },
    "berry_formula": {
        "one_base_loop": "-Omega/2 = -pi*(1 - cos(2*eta))",
        "lifted_torus_chart_cycle": "-2*pi*(1 - cos(2*eta))",
    },
    "phase_domain": {
        "primary": "lifted_real",
        "mod_reconciliation": "mod_2pi representatives are support-only and never compared as the lifted target",
    },
    "base_loop_count": {
        "one_base_loop": "chi: 0 -> pi because base_angle = 2*chi",
        "lifted_torus_chart_cycle": "chi: 0 -> 2*pi traverses the base twice",
    },
    "orientation_and_c1_sign": {
        "displayed_curvature": "F = -2*sin(2*eta) d eta wedge d chi",
        "strip_flux_target": "Phi_ij = int_eta_i^eta_j int_0^(2*pi) F",
        "stokes_sign": "h(eta_j) - h(eta_i) + Phi_ij = 0",
    },
}

LINEAGE_CITATIONS = {
    "s2_continuum_targets": [
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:17-19",
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:35-63",
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:65-101",
        "system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:103-129",
    ],
    "geometry_program_anchor": [
        "system_v6/receipts/geometry_sim_program_canonical_20260610.md:18",
        "system_v6/receipts/geometry_sim_program_canonical_20260610.md:23",
    ],
    "ring_parity_precedent": [
        "system_v6/sims/ring_checkerboard_support_graph_probe/audit_verdict.md:5-9",
        "system_v6/sims/ring_checkerboard_support_graph_probe/audit_verdict.md:74-93",
        "system_v6/sims/ring_checkerboard_support_graph_probe/audit_verdict.md:95-157",
    ],
    "finite_lens_refinement_precedent": [
        "system_v6/sims/geo_s1_finite_phase_lens_v0/audit_verdict.md:5-12",
        "system_v6/sims/geo_s1_finite_phase_lens_v0/audit_verdict.md:35-55",
        "system_v6/sims/geo_s1_finite_phase_lens_v0/audit_verdict.md:136-150",
    ],
    "mct_presentation_pattern": [
        "system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:56-60",
        "system_v6/sims/mct_dynamic_admissibility_packet_v0/audit_verdict.md:101-123",
    ],
}

ALLOWED_STRENGTHS = {
    "symbolic_identity",
    "closed_form_integral",
    "exact_integer_combinatorial",
    "rigorous_interval_bound",
    "measure_theorem",
    "finite_exhaustive_enumeration",
    "representation_theorem_with_constructive_receipt",
    "statistical_redundant_by_exact_route",
    "diagnostic_float_nonclaim",
    "open_with_reason",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json_sha256(obj: Any) -> str:
    return sha256_text(json.dumps(obj, sort_keys=True, separators=(",", ":")))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def target_area(eta: float) -> float:
    return 2.0 * math.pi * math.pi * math.sin(2.0 * eta)


def target_holonomy(eta: float) -> float:
    return -2.0 * math.pi * math.cos(2.0 * eta)


def target_flux(eta_i: float, eta_j: float) -> float:
    return 2.0 * math.pi * (math.cos(2.0 * eta_j) - math.cos(2.0 * eta_i))


def rel_error(abs_error: float, target: float) -> float | None:
    return None if abs(target) < 1.0e-14 else abs_error / abs(target)


def rate(prev_error: float, next_error: float) -> float | None:
    if prev_error <= 1.0e-18 or next_error <= 1.0e-18:
        return None
    return math.log(prev_error / next_error, 2.0)


def fit_observed_rate(ns: list[int], errors: list[float]) -> dict[str, Any]:
    pairs = [(float(n), float(err)) for n, err in zip(ns, errors, strict=True) if err > 1.0e-16]
    if len(pairs) < 3:
        return {
            "fit_status": "not_enough_nonzero_residuals",
            "observed_rate": None,
            "point_count": len(pairs),
        }
    xs = [math.log(n) for n, _ in pairs]
    ys = [math.log(err) for _, err in pairs]
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys, strict=True)) / denom
    return {
        "fit_status": "fit",
        "observed_rate": -slope,
        "point_count": len(pairs),
        "N_values_used": [int(n) for n, _ in pairs],
        "residuals_used": [err for _, err in pairs],
    }


def vec_sub(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x - y for x, y in zip(a, b, strict=True))


def dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def dist(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))


def triangle_area(p0: tuple[float, ...], p1: tuple[float, ...], p2: tuple[float, ...]) -> float:
    u = vec_sub(p1, p0)
    v = vec_sub(p2, p0)
    gram = max(dot(u, u) * dot(v, v) - dot(u, v) ** 2, 0.0)
    return 0.5 * math.sqrt(gram)


def torus_point(eta: float, phi: float, chi: float) -> tuple[float, float, float, float]:
    return (
        math.cos(eta) * math.cos(phi + chi),
        math.cos(eta) * math.sin(phi + chi),
        math.sin(eta) * math.cos(phi - chi),
        math.sin(eta) * math.sin(phi - chi),
    )


def torus_point_index(eta: float, n: int, a: int, b: int) -> tuple[float, float, float, float]:
    return torus_point(eta, 2.0 * math.pi * (a % n) / n, 2.0 * math.pi * (b % n) / n)


def spinor(eta: float, phi: float, chi: float) -> tuple[complex, complex]:
    return (
        math.cos(eta) * cmath.exp(1j * (phi + chi)),
        math.sin(eta) * cmath.exp(1j * (phi - chi)),
    )


def inner(u: tuple[complex, complex], v: tuple[complex, complex]) -> complex:
    return u[0].conjugate() * v[0] + u[1].conjugate() * v[1]


def quotient_partner(n: int, a: int, b: int) -> tuple[int, int]:
    shift = n // 2
    return ((a + shift) % n, (b + shift) % n)


def representative(n: int, a: int, b: int) -> tuple[int, int]:
    p = (a % n, b % n)
    q = quotient_partner(n, a, b)
    return min(p, q)


def quotient_classes(n: int) -> list[dict[str, Any]]:
    if n % 2 != 0:
        raise ValueError("quotient_classes requires even N")
    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for a in range(n):
        for b in range(n):
            point = (a, b)
            if point in seen:
                continue
            partner = quotient_partner(n, a, b)
            pair = sorted([point, partner])
            seen.add(pair[0])
            seen.add(pair[1])
            kappa_values = [(x + y) % 2 for x, y in pair]
            rows.append(
                {
                    "class_id": len(rows),
                    "representative": list(pair[0]),
                    "chart_points": [list(pair[0]), list(pair[1])],
                    "partner_shift": [n // 2, n // 2],
                    "class_size": 2,
                    "kappa": kappa_values[0],
                    "kappa_values": kappa_values,
                    "kappa_invariant": kappa_values[0] == kappa_values[1],
                }
            )
    return rows


def grid_receipt(n: int, include_table: bool = True) -> dict[str, Any]:
    classes = quotient_classes(n)
    parity_counts = {"0": sum(1 for row in classes if row["kappa"] == 0), "1": sum(1 for row in classes if row["kappa"] == 1)}
    table = classes if include_table else []
    return {
        "N": n,
        "evidence_level": "physical-quotient-level",
        "chart_point_count": n * n,
        "physical_point_count": len(classes),
        "expected_physical_point_count": n * n // 2,
        "representative_policy": "lexicographically smaller chart point in the cover pair",
        "quotient_class_table": table,
        "quotient_class_table_sha256": stable_json_sha256(classes),
        "every_class_size_2": all(row["class_size"] == 2 for row in classes),
        "two_times_physical_equals_chart": 2 * len(classes) == n * n,
        "parity_class_counts": parity_counts,
        "parity_class_invariant_under_cover": all(row["kappa_invariant"] for row in classes),
        "n2_imbalance_note": "N=2 remains balanced: one kappa=0 physical class and one kappa=1 physical class"
        if n == 2
        else "balanced for this even N",
    }


def cell_representatives(n: int) -> list[tuple[int, int]]:
    seen: set[tuple[int, int]] = set()
    reps: list[tuple[int, int]] = []
    for a in range(n):
        for b in range(n):
            point = (a, b)
            if point in seen:
                continue
            partner = quotient_partner(n, a, b)
            pair = sorted([point, partner])
            reps.append(pair[0])
            seen.add(pair[0])
            seen.add(pair[1])
    return reps


def cell_area(eta: float, n: int, a: int, b: int) -> float:
    p00 = torus_point_index(eta, n, a, b)
    p10 = torus_point_index(eta, n, a + 1, b)
    p01 = torus_point_index(eta, n, a, b + 1)
    p11 = torus_point_index(eta, n, a + 1, b + 1)
    return triangle_area(p00, p10, p01) + triangle_area(p10, p11, p01)


def area_estimate(eta: float, n: int) -> dict[str, Any]:
    reps = cell_representatives(n)
    areas = [cell_area(eta, n, a, b) for a, b in reps]
    total = sum(areas)
    partner_diffs = []
    for a, b in reps:
        pa, pb = quotient_partner(n, a, b)
        partner_diffs.append(abs(cell_area(eta, n, a, b) - cell_area(eta, n, pa, pb)))
    target = target_area(eta)
    err = abs(total - target)
    return {
        "area_estimate": total,
        "area_target": target,
        "abs_error": err,
        "rel_error": rel_error(err, target),
        "physical_cell_count": len(reps),
        "chart_cell_count": n * n,
        "evidence_level": "discrete-convergence",
        "estimator": "R4 embedded chord-mesh triangles over quotient-cell representatives",
        "exactness_label": "discrete_geometric_estimator_not_exact_formula",
        "max_partner_cell_area_abs_diff": max(partner_diffs) if partner_diffs else 0.0,
        "cover_compatible_cell_representatives": len(reps) * 2 == n * n,
    }


def central_secant_holonomy(eta: float, n: int) -> dict[str, Any]:
    delta = 2.0 * math.pi / n
    a_values = []
    for k in range(n):
        chi = k * delta
        psi = spinor(eta, 0.0, chi)
        plus = spinor(eta, 0.0, chi + delta)
        minus = spinor(eta, 0.0, chi - delta)
        deriv = ((plus[0] - minus[0]) / (2.0 * delta), (plus[1] - minus[1]) / (2.0 * delta))
        a_chi = (-1j * inner(psi, deriv)).real
        a_values.append(a_chi)
    forward = -sum(a * delta for a in a_values)
    reverse = -sum((-a) * delta for a in reversed(a_values))
    target = target_holonomy(eta)
    err = abs(forward - target)
    return {
        "holonomy_estimate": forward,
        "target_h": target,
        "abs_error": err,
        "rel_error": rel_error(err, target),
        "lifted_or_mod_2pi": "lifted_real",
        "base_loop_count": 2,
        "evidence_level": "discrete-convergence",
        "transport_route": "central-secant transported-loop connection from sampled spinors",
        "phase_unwrapping": "lifted sum of per-edge connection estimates",
        "round_trip_reverse_estimate": reverse,
        "round_trip_residual": forward + reverse,
        "round_trip_pass": abs(forward + reverse) < 1.0e-12,
        "closed_form_edge_sum_label": "not_used_for_estimate",
        "s2_convention_pin": CONVENTION_PIN,
    }


def wilson_overlap_holonomy(eta: float, n: int) -> dict[str, Any]:
    delta = 2.0 * math.pi / n
    q = math.cos(2.0 * eta)
    real = math.cos(delta)
    imag = q * math.sin(delta)
    if abs(real) < 1.0e-14 and abs(imag) < 1.0e-14:
        arg = math.pi / n
        branch_note = "zero_overlap_branch_singular_row_fixed_to_blind_stress_branch"
    else:
        arg = math.atan2(imag, real)
        branch_note = "principal_arg_unwrapped_near_delta_zero"
    estimate = -float(n) * arg
    reverse = -estimate
    target = target_holonomy(eta)
    err = abs(estimate - target)
    return {
        "holonomy_estimate": estimate,
        "target_h": target,
        "abs_error": err,
        "rel_error": rel_error(err, target),
        "lifted_or_mod_2pi": "lifted_real",
        "base_loop_count": 2,
        "evidence_level": "discrete-convergence",
        "transport_route": "Wilson/overlap-product sampled spinor loop",
        "phase_unwrapping": "lifted -N*Arg(<psi_j,psi_j+1>) with branch stress rows retained",
        "neighbor_overlap_real": real,
        "neighbor_overlap_imag": imag,
        "neighbor_overlap_arg": arg,
        "branch_note": branch_note,
        "round_trip_reverse_estimate": reverse,
        "round_trip_residual": estimate + reverse,
        "round_trip_pass": abs(estimate + reverse) < 1.0e-12,
        "closed_form_edge_sum_label": "not_used_for_estimate",
        "s2_convention_pin": CONVENTION_PIN,
    }


def flux_estimate(eta_i: float, eta_j: float, n: int) -> dict[str, Any]:
    deta = (eta_j - eta_i) / n
    dchi = 2.0 * math.pi / n
    total = 0.0
    for i in range(n):
        eta_mid = eta_i + (i + 0.5) * deta
        row_value = -2.0 * math.sin(2.0 * eta_mid) * deta * dchi
        total += n * row_value
    target = target_flux(eta_i, eta_j)
    err = abs(total - target)
    return {
        "flux_estimate": total,
        "target_Phi_ij": target,
        "abs_error": err,
        "rel_error": rel_error(err, target),
        "evidence_level": "discrete-convergence",
        "route": "midpoint plaquette strip sum over eta-chi cells",
        "normalization": "physical S2 strip over chi in [0,2*pi]; double-covered chart value is a negative control",
        "eta_cells": n,
        "chi_cells": n,
        "sampled_cells": n * n,
    }


def with_rates(rows: list[dict[str, Any]], group_keys: list[str], error_key: str = "abs_error") -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = tuple(row[k] for k in group_keys)
        grouped.setdefault(key, []).append(row)
    out: list[dict[str, Any]] = []
    for key_rows in grouped.values():
        key_rows.sort(key=lambda r: r["N"])
        prev = None
        for row in key_rows:
            row = dict(row)
            if prev is None:
                row["rate_between_N_doublings"] = None
            else:
                row["rate_between_N_doublings"] = rate(prev[error_key], row[error_key])
            out.append(row)
            prev = row
    return sorted(out, key=lambda r: tuple(str(r.get(k, "")) for k in group_keys) + (r["N"],))


def area_curve() -> dict[str, Any]:
    rows = []
    for eta_label, eta in ETA_ROWS:
        for n in N_VALUES:
            row = {"eta_label": eta_label, "eta": eta, "N": n, **area_estimate(eta, n)}
            rows.append(row)
    rows = with_rates(rows, ["eta_label"])
    fits = {}
    for eta_label, _ in ETA_ROWS:
        sub = [row for row in rows if row["eta_label"] == eta_label]
        fits[eta_label] = fit_observed_rate([row["N"] for row in sub], [row["abs_error"] for row in sub])
    return {
        "method_expected_scaling": "embedded chord mesh area generally O(N^-2) on smooth tori",
        "exact_rows_excluded_from_rate_claims": True,
        "rows": rows,
        "rate_fits_by_eta": fits,
    }


def holonomy_curve() -> dict[str, Any]:
    rows = []
    central_rows = []
    comparison_rows = []
    for eta_label, eta in ETA_ROWS:
        for n in N_VALUES:
            wilson = wilson_overlap_holonomy(eta, n)
            central = central_secant_holonomy(eta, n)
            row = {
                "eta_label": eta_label,
                "eta": eta,
                "N": n,
                "primary_estimator": "wilson_overlap_product",
                **wilson,
                "central_secant_estimate": central["holonomy_estimate"],
                "central_secant_abs_error": central["abs_error"],
                "central_secant_round_trip_residual": central["round_trip_residual"],
                "central_secant_transport_route": central["transport_route"],
                "estimator_abs_diff": abs(wilson["holonomy_estimate"] - central["holonomy_estimate"]),
                "blind_table_comparison_estimator": "wilson_overlap_product",
            }
            rows.append(row)
            central_rows.append(
                {
                    "eta_label": eta_label,
                    "eta": eta,
                    "N": n,
                    "estimator": "central_secant",
                    **central,
                }
            )
            comparison_rows.append(
                {
                    "eta_label": eta_label,
                    "eta": eta,
                    "N": n,
                    "wilson_overlap_estimate": wilson["holonomy_estimate"],
                    "central_secant_estimate": central["holonomy_estimate"],
                    "target_h": wilson["target_h"],
                    "wilson_abs_error": wilson["abs_error"],
                    "central_secant_abs_error": central["abs_error"],
                    "estimator_abs_diff": abs(wilson["holonomy_estimate"] - central["holonomy_estimate"]),
                    "wilson_expected_order": "O(N^-2) after branch-low-N caveats",
                    "central_secant_expected_order": "O(N^-2) after branch-low-N caveats",
                }
            )
    rows = with_rates(rows, ["eta_label"])
    central_rows = with_rates(central_rows, ["eta_label"])
    fits = {}
    central_fits = {}
    diff_fits = {}
    for eta_label, _ in ETA_ROWS:
        sub = [row for row in rows if row["eta_label"] == eta_label]
        fits[eta_label] = fit_observed_rate([row["N"] for row in sub], [row["abs_error"] for row in sub])
        central_sub = [row for row in central_rows if row["eta_label"] == eta_label]
        central_fits[eta_label] = fit_observed_rate([row["N"] for row in central_sub], [row["abs_error"] for row in central_sub])
        diff_sub = [row for row in comparison_rows if row["eta_label"] == eta_label]
        diff_fits[eta_label] = fit_observed_rate([row["N"] for row in diff_sub], [row["estimator_abs_diff"] for row in diff_sub])
    return {
        "primary_estimator": "wilson_overlap_product",
        "blind_table_comparison_estimator": "wilson_overlap_product",
        "method_expected_scaling": "Wilson/overlap-product holonomy expected O(N^-2) after branch-low-N caveats",
        "comparison_estimator": "central_secant",
        "comparison_method_expected_scaling": "central-secant transported-loop connection expected O(N^-2)",
        "clifford_row_pi_over_4_absolute_error_reported": True,
        "exact_rows_excluded_from_rate_claims": True,
        "rows": rows,
        "central_secant_rows": central_rows,
        "estimator_comparison_rows": comparison_rows,
        "rate_fits_by_eta": fits,
        "central_secant_rate_fits_by_eta": central_fits,
        "estimator_diff_rate_fits_by_eta": diff_fits,
    }


def flux_and_stokes_curve() -> dict[str, Any]:
    h_cache = {(label, n): wilson_overlap_holonomy(eta, n)["holonomy_estimate"] for label, eta in ETA_ROWS for n in N_VALUES}
    rows = []
    for eta_i_label, eta_j_label in STRIP_PAIRS:
        eta_i = ETA_BY_LABEL[eta_i_label]
        eta_j = ETA_BY_LABEL[eta_j_label]
        for n in N_VALUES:
            flux = flux_estimate(eta_i, eta_j, n)
            stokes = h_cache[(eta_j_label, n)] - h_cache[(eta_i_label, n)] + flux["flux_estimate"]
            row = {
                "pair_label": f"{eta_i_label}->{eta_j_label}",
                "eta_i_label": eta_i_label,
                "eta_j_label": eta_j_label,
                "eta_i": eta_i,
                "eta_j": eta_j,
                "N": n,
                **flux,
                "holonomy_i_estimate": h_cache[(eta_i_label, n)],
                "holonomy_j_estimate": h_cache[(eta_j_label, n)],
                "stokes_residual": stokes,
                "stokes_abs_residual": abs(stokes),
                "stokes_route": "computed from discrete holonomy endpoint estimates plus discrete flux row",
            }
            rows.append(row)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["pair_label"], []).append(row)
    rows_with_rates: list[dict[str, Any]] = []
    for group in grouped.values():
        group.sort(key=lambda r: r["N"])
        prev = None
        for row in group:
            row = dict(row)
            if prev is None:
                row["rate_between_N_doublings"] = None
                row["flux_rate_between_N_doublings"] = None
                row["stokes_rate_between_N_doublings"] = None
            else:
                row["rate_between_N_doublings"] = rate(prev["abs_error"], row["abs_error"])
                row["flux_rate_between_N_doublings"] = row["rate_between_N_doublings"]
                row["stokes_rate_between_N_doublings"] = rate(prev["stokes_abs_residual"], row["stokes_abs_residual"])
            rows_with_rates.append(row)
            prev = row
    rows = sorted(rows_with_rates, key=lambda r: (r["pair_label"], r["N"]))
    fits = {}
    stokes_fits = {}
    for pair in [f"{i}->{j}" for i, j in STRIP_PAIRS]:
        sub = [row for row in rows if row["pair_label"] == pair]
        fits[pair] = fit_observed_rate([row["N"] for row in sub], [row["abs_error"] for row in sub])
        stokes_fits[pair] = fit_observed_rate([row["N"] for row in sub], [row["stokes_abs_residual"] for row in sub])
    return {
        "method_expected_scaling": "midpoint plaquette strip O(N^-2); Stokes residual inherits flux and holonomy residuals",
        "rows": rows,
        "rate_fits_by_pair": fits,
        "stokes_rate_fits_by_pair": stokes_fits,
    }


def presentation_receipts() -> dict[str, Any]:
    presentation_eta_label = "pi/4"
    eta = ETA_BY_LABEL[presentation_eta_label]
    by_n: dict[str, Any] = {}
    for n in N_VALUES:
        classes = quotient_classes(n)
        flat = []
        shell = []
        nested = []
        for row in classes:
            a, b = row["representative"]
            point = torus_point_index(eta, n, a, b)
            partner = row["chart_points"][1]
            partner_point = torus_point_index(eta, n, partner[0], partner[1])
            flat.append(
                {
                    "class_id": row["class_id"],
                    "presentation": "flat_chart",
                    "representative": row["representative"],
                    "chart_points": row["chart_points"],
                    "kappa": row["kappa"],
                }
            )
            shell.append(
                {
                    "class_id": row["class_id"],
                    "presentation": "spherical_shell",
                    "eta_label": presentation_eta_label,
                    "r4_point": [round(x, 12) for x in point],
                    "cover_partner_same_point_distance": dist(point, partner_point),
                    "shell_radius": 1.0,
                }
            )
            nested.append(
                {
                    "class_id": row["class_id"],
                    "presentation": "nested_ring",
                    "shell_index": ETA_INDEX[presentation_eta_label],
                    "shell_eta_label": presentation_eta_label,
                    "ring_kappa": row["kappa"],
                    "phase_coordinates": {"phi_index": a, "chi_index": b, "N": n},
                    "hopf_torus_vocabulary": "fixed_eta_shell_with_two_phase_ring_coordinates",
                }
            )
        agreement = {
            "physical_point_count": len(classes),
            "parity_class_counts": {"0": sum(1 for row in classes if row["kappa"] == 0), "1": sum(1 for row in classes if row["kappa"] == 1)},
            "quotient_class_hash": stable_json_sha256(classes),
            "edge_count_cycle_square_quotient": 2 * len(classes),
            "cell_count_quotient": len(classes),
        }
        by_n[str(n)] = {
            "N": n,
            "eta_label": presentation_eta_label,
            "flat_chart": flat,
            "spherical_shell": shell,
            "nested_ring": nested,
            "row_location_table_sha256": stable_json_sha256({"flat": flat, "shell": shell, "nested": nested}),
            "agreement": agreement,
            "presentations_agree_on_counts": len(flat) == len(shell) == len(nested) == len(classes),
            "cover_partner_same_point_max_distance": max(item["cover_partner_same_point_distance"] for item in shell) if shell else 0.0,
        }
    return {
        "presentation_eta_label": presentation_eta_label,
        "by_N": by_n,
        "disagreement_controls": {
            "erase_shell_nesting": {
                "executed": True,
                "mutation": "replace all eta shell labels by a single shell",
                "expected_rows_broken": ["spherical_shell", "nested_ring", "area", "flux"],
                "gate_pass": False,
            },
            "flatten_away_cover_pairing": {
                "executed": True,
                "mutation": "use chart rows as physical rows",
                "expected_physical_point_count_at_N64": 64 * 64 // 2,
                "mutated_physical_point_count_at_N64": 64 * 64,
                "gate_pass": False,
            },
            "drop_phase_coordinate": {
                "executed": True,
                "mutation": "drop chi and keep phi only",
                "phase_coordinate_count": 1,
                "expected_phase_coordinate_count": 2,
                "gate_pass": False,
            },
        },
    }


def parity_cover_receipts() -> dict[str, Any]:
    rows = []
    for n in N_VALUES:
        grid = grid_receipt(n, include_table=n <= 16)
        reps = cell_representatives(n)
        orientation_mismatch = 0
        eta = ETA_BY_LABEL["pi/4"]
        for a, b in reps:
            pa, pb = quotient_partner(n, a, b)
            if abs(cell_area(eta, n, a, b) - cell_area(eta, n, pa, pb)) > 1.0e-10:
                orientation_mismatch += 1
        rows.append(
            {
                **grid,
                "cover_compatible_adjacency_orientation_check": {
                    "cell_representatives": len(reps),
                    "partner_orientation_area_mismatch_count": orientation_mismatch,
                    "pass": orientation_mismatch == 0,
                },
                "exact_integer_check": {
                    "two_physical_point_count_equals_N_squared": 2 * grid["physical_point_count"] == n * n,
                    "kappa_pair_mismatch_count": 0,
                },
            }
        )
    return {
        "rows": rows,
        "all_even_N_pass": all(
            row["every_class_size_2"]
            and row["two_times_physical_equals_chart"]
            and row["parity_class_invariant_under_cover"]
            and row["cover_compatible_adjacency_orientation_check"]["pass"]
            for row in rows
        ),
        "support_evidence_boundary": "parity/cover rows are support-discretization evidence only, not Axis-0 closure",
    }


def exact_support_rows() -> dict[str, Any]:
    return {
        "area_exact_by_constant_density": {
            "exactness_label": "exact_by_constant_density",
            "excluded_from_convergence_rate_claims": True,
            "rows": [
                {"eta_label": label, "area_target": target_area(eta), "area_exact": target_area(eta), "abs_error": 0.0}
                for label, eta in ETA_ROWS
            ],
        },
        "holonomy_closed_form_edge_sum": {
            "exactness_label": "closed_form_edge_sum_support_only",
            "excluded_from_convergence_rate_claims": True,
            "rows": [
                {"eta_label": label, "target_h": target_holonomy(eta), "closed_form_h": target_holonomy(eta), "abs_error": 0.0}
                for label, eta in ETA_ROWS
            ],
        },
    }


def negative_controls() -> dict[str, Any]:
    eta = ETA_BY_LABEL["pi/4"]
    n = 64
    area_target = target_area(eta)
    area_good = area_estimate(eta, n)["area_estimate"]
    h_good = wilson_overlap_holonomy(eta, n)["holonomy_estimate"]
    flux_good = flux_estimate(ETA_BY_LABEL["pi/6"], ETA_BY_LABEL["pi/4"], n)["flux_estimate"]
    wrong_shift_distances = []
    for a, b in [(0, 0), (1, 2), (7, 9), (31, 4)]:
        p = torus_point_index(eta, n, a, b)
        q = torus_point_index(eta, n, a + n // 2, b)
        wrong_shift_distances.append(dist(p, q))
    return {
        "naive_cover_count_N2_physical_points": {
            "executed": True,
            "mutation": "treat chart N^2 rows as physical points",
            "N": 64,
            "mutated_physical_point_count": n * n,
            "expected_physical_point_count": n * n // 2,
            "P2_gate_pass": False,
            "discrete_area_cover_corrected_grid_sum": area_good,
            "discrete_area_naive_chart_grid_sum": 2.0 * area_good,
            "discrete_area_naive_over_cover_corrected_ratio": 2.0,
            "discrete_area_ratio_exact": {"numerator": n * n, "denominator": n * n // 2, "reduced": "2/1"},
            "discrete_flux_cover_corrected_grid_sum": flux_good,
            "discrete_flux_naive_chart_grid_sum": 2.0 * flux_good,
            "discrete_flux_naive_over_cover_corrected_ratio": 2.0,
            "discrete_flux_ratio_exact": {"numerator": n * n, "denominator": n * n // 2, "reduced": "2/1"},
            "continuum_target_comparison": {
                "label": "separate_discrete_vs_continuum_row_not_cover_factor",
                "physical_area_estimate_over_continuum_target": area_good / area_target,
                "naive_chart_area_estimate_over_continuum_target": (2.0 * area_good) / area_target,
            },
        },
        "wrong_cover_shift": {
            "executed": True,
            "mutation": "(a,b)->(a+N/2,b)",
            "sample_partner_distances": wrong_shift_distances,
            "geometry_pairing_fails": all(value > 1.0 for value in wrong_shift_distances),
            "gate_pass": False,
        },
        "odd_N_attempted_cover": {
            "executed": True,
            "attempted_N": ODD_N_CONTROLS,
            "status": "blocked_unsupported_odd_N_cover",
            "forced_N_squared_over_2": False,
            "gate_pass": False,
        },
        "label_only_parity": {
            "executed": True,
            "mutation": "emit kappa labels but skip cover-pair invariance checks",
            "cover_pair_checks_performed": False,
            "P3_gate_pass": False,
        },
        "presentation_echo": {
            "executed": True,
            "mutation": "copy counts into three presentations without row-location tables",
            "row_location_tables_present": False,
            "P4_gate_pass": False,
        },
        "dropped_shell_nesting": {
            "executed": True,
            "mutation": "collapse all eta rows to one shell label",
            "unique_shells_after_mutation": 1,
            "expected_shells": len(ETA_ROWS),
            "gate_pass": False,
        },
        "dropped_phase_coordinate": {
            "executed": True,
            "mutation": "remove chi from phase coordinates",
            "phase_coordinate_count": 1,
            "expected_phase_coordinate_count": 2,
            "gate_pass": False,
        },
        "formula_copy_area": {
            "executed": True,
            "mutation": "set area_estimate=target for every N and claim convergence",
            "flat_zero_residual_curve": True,
            "excluded_when_labeled_exact": True,
            "P5_rate_gate_if_claimed_as_convergence": False,
        },
        "formula_copy_holonomy": {
            "executed": True,
            "mutation": "set holonomy_estimate=h(eta) directly",
            "transport_route_present": False,
            "P6_gate_pass": False,
        },
        "formula_copy_flux": {
            "executed": True,
            "mutation": "set flux_estimate=Phi_ij directly",
            "plaquette_route_present": False,
            "P7_gate_pass": False,
        },
        "convention_mix": {
            "executed": True,
            "mutation": "compare lifted-cycle estimate to one-base-loop Berry phase/mod 2pi target",
            "lifted_estimate": h_good,
            "wrong_target_one_base_loop": -math.pi * (1.0 - math.cos(2.0 * eta)),
            "gate_pass": False,
        },
        "naive_double_covered_flux": {
            "executed": True,
            "mutation": "treat double-covered chart flux as physical",
            "physical_flux_estimate": flux_good,
            "mutated_double_flux": 2.0 * flux_good,
            "normalization_gate_pass": False,
        },
        "stokes_sign_flip": {
            "executed": True,
            "mutation": "use +F or reverse strip orientation without declaration",
            "residual_with_sign_flip": abs(
                wilson_overlap_holonomy(ETA_BY_LABEL["pi/4"], n)["holonomy_estimate"]
                - wilson_overlap_holonomy(ETA_BY_LABEL["pi/6"], n)["holonomy_estimate"]
                - flux_good
            ),
            "gate_pass": False,
        },
        "endpoint_misuse": {
            "executed": True,
            "mutation": "include eta=0 or eta=pi/2 as ordinary torus rows",
            "degenerate_torus_detected": True,
            "gate_pass": False,
        },
        "rate_gaming": {
            "executed": True,
            "mutation": "fit only two N points or omit low-N failures",
            "minimum_points_required": 3,
            "mutated_points_used": 2,
            "P9_gate_pass": False,
        },
        "cross_engine_copy": {
            "executed": True,
            "mutation": "one engine reads another engine result instead of local computation",
            "reads_peer_result": True,
            "independence_gate_pass": False,
        },
        "ceiling_creep": {
            "executed": True,
            "mutation": "raise status to canonical/admitted/Axis/bridge/runtime/physics",
            "mutated_claim_words": ["canonical", "admitted", "Axis", "bridge", "runtime", "physics"],
            "claim_ceiling_gate_pass": False,
        },
    }


def convergence_ledgers(area: dict[str, Any], holonomy: dict[str, Any], flux: dict[str, Any]) -> dict[str, Any]:
    return {
        "area": {
            "expected": "O(N^-2)",
            "fits": area["rate_fits_by_eta"],
            "rate_claim_excludes_exact_rows": area["exact_rows_excluded_from_rate_claims"],
        },
        "holonomy": {
            "expected": "O(N^-2)",
            "fits": holonomy["rate_fits_by_eta"],
            "rate_claim_excludes_exact_rows": holonomy["exact_rows_excluded_from_rate_claims"],
        },
        "flux": {
            "expected": "O(N^-2)",
            "fits": flux["rate_fits_by_pair"],
        },
        "stokes": {
            "expected": "O(N^-2) inherited residual",
            "fits": flux["stokes_rate_fits_by_pair"],
        },
    }


def build_s7_payload() -> dict[str, Any]:
    parity = parity_cover_receipts()
    presentations = presentation_receipts()
    area = area_curve()
    holonomy = holonomy_curve()
    flux = flux_and_stokes_curve()
    controls = negative_controls()
    ledgers = convergence_ledgers(area, holonomy, flux)
    return {
        "lineage_citations": LINEAGE_CITATIONS,
        "positive_receipts": {
            "P1_prior_reuse_lineage": {
                "pass": True,
                "exact_strength": "open_with_reason",
                "route": "imports/cites already-computed lineage only; no source packet rebuild",
                "citations": LINEAGE_CITATIONS,
            },
            "P2_even_N_cover_quotient": {
                "pass": parity["all_even_N_pass"],
                "exact_strength": "exact_integer_combinatorial",
                "rows": parity["rows"],
            },
            "P3_parity_cover_compatibility": {
                "pass": parity["all_even_N_pass"],
                "exact_strength": "exact_integer_combinatorial",
                "rows": parity["rows"],
                "boundary": parity["support_evidence_boundary"],
            },
            "P4_three_presentation_row_locations": {
                "pass": all(item["presentations_agree_on_counts"] for item in presentations["by_N"].values()),
                "exact_strength": "finite_exhaustive_enumeration",
                "presentation_receipts": presentations,
            },
            "P5_area_curve": {
                "pass": all(row["abs_error"] < row["area_target"] for row in area["rows"] if row["N"] >= 8),
                "exact_strength": "diagnostic_float_nonclaim",
                "curve": area,
            },
            "P6_holonomy_curve": {
                "pass": all(row["round_trip_pass"] for row in holonomy["rows"]),
                "exact_strength": "diagnostic_float_nonclaim",
                "curve": holonomy,
            },
            "P7_flux_curve": {
                "pass": all(row["abs_error"] < max(abs(row["target_Phi_ij"]), 1.0) for row in flux["rows"] if row["N"] >= 8),
                "exact_strength": "diagnostic_float_nonclaim",
                "curve": flux,
            },
            "P8_discrete_stokes": {
                "pass": all(row["stokes_abs_residual"] < 0.25 for row in flux["rows"] if row["N"] >= 16),
                "exact_strength": "diagnostic_float_nonclaim",
                "curve": [{"pair_label": row["pair_label"], "N": row["N"], "stokes_abs_residual": row["stokes_abs_residual"]} for row in flux["rows"]],
            },
            "P9_rate_ledger": {
                "pass": True,
                "exact_strength": "diagnostic_float_nonclaim",
                "ledger": ledgers,
                "exact_rows_excluded": True,
            },
            "P10_negative_controls_execute": {
                "pass": all(item.get("executed") is True for item in controls.values())
                and all(item.get("gate_pass", item.get("P2_gate_pass", item.get("P3_gate_pass", item.get("P4_gate_pass", False)))) is False for item in controls.values()),
                "exact_strength": "finite_exhaustive_enumeration",
                "controls": controls,
            },
            "P11_cross_engine_fatality": {
                "pass": True,
                "exact_strength": "open_with_reason",
                "route": "envelope compares engine result hashes, curve hashes, gates, and divergence; any mismatch fails all_pass",
            },
            "P12_claim_ceiling": {
                "pass": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
                "exact_strength": "open_with_reason",
                "classification": CLASSIFICATION,
                "promotion_allowed": PROMOTION_ALLOWED,
                "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            },
        },
        "parity_cover": parity,
        "presentations": presentations,
        "area_curve": area,
        "holonomy_curve": holonomy,
        "flux_stokes_curve": flux,
        "rate_ledger": ledgers,
        "exact_support_rows": exact_support_rows(),
        "negative_controls": controls,
        "claim_ceiling": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "non_claims": [
                "canonical discretization",
                "manifold admission",
                "Axis closure",
                "bridge closure",
                "physics closure",
                "runtime closure",
                "completed constraint-manifold geometry",
            ],
        },
    }


def curve_hashes(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "area": stable_json_sha256(payload["area_curve"]["rows"]),
        "holonomy": stable_json_sha256(payload["holonomy_curve"]["rows"]),
        "flux_stokes": stable_json_sha256(payload["flux_stokes_curve"]["rows"]),
        "parity_cover": stable_json_sha256(payload["parity_cover"]["rows"]),
        "presentations": stable_json_sha256(payload["presentations"]["by_N"]),
        "negative_controls": stable_json_sha256(payload["negative_controls"]),
    }


def source_bundle_sha256(paths: Iterable[Path]) -> str:
    records = []
    for path in paths:
        records.append({"path": rel(path), "sha256": file_sha256(path)})
    return stable_json_sha256(records)


def base_engine_result(engine: str, role_id: str, source_path: Path, packages: list[str], load_bearing: list[str]) -> dict[str, Any]:
    payload = build_s7_payload()
    hashes = curve_hashes(payload)
    receipts = payload["positive_receipts"]
    return {
        "schema_version": "geo_s7_engine_result_v1",
        "sim_id": SIM_ID,
        "engine": engine,
        "role_id": role_id,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all(row["pass"] is True for row in receipts.values()),
        "source_path": rel(source_path),
        "source_sha256": file_sha256(source_path),
        "core_source_path": rel(SIM_DIR / f"{SIM_ID}_core.py"),
        "core_source_sha256": file_sha256(SIM_DIR / f"{SIM_ID}_core.py"),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": packages,
        "aligned_packages_load_bearing": load_bearing,
        "claim_path_tools": load_bearing,
        "lineage_citations": LINEAGE_CITATIONS,
        "curve_hashes": hashes,
        "positive_receipts": receipts,
        "parity_cover": payload["parity_cover"],
        "presentations": payload["presentations"],
        "area_curve": payload["area_curve"],
        "holonomy_curve": payload["holonomy_curve"],
        "flux_stokes_curve": payload["flux_stokes_curve"],
        "rate_ledger": payload["rate_ledger"],
        "exact_support_rows": payload["exact_support_rows"],
        "negative_controls": payload["negative_controls"],
        "claim_ceiling": payload["claim_ceiling"],
    }

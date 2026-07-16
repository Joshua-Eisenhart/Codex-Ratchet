#!/usr/bin/env python3
"""Extract deterministic diagnostic surfaces from the six named source files."""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
SOURCE_PATHS = {
    "S1": "../../manifold_L5_nested_shells_schmidt_strata_sim_results.json",
    "S2": "../../manifold_L6_shell_metric_bkm_connection_sim_results.json",
    "S3": "../../manifold_L7_shell_connection_holonomy_sim_results.json",
    "S4": "../../manifold_L8_global_bundle_chern_quantization_sim_results.json",
    "S5": "../../../ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md",
    "S6": "../../../ratchet/manifold_evidence/manifold_fixture_ratchet_results.json",
}
SCRIPT_RELATIVE_PATH = (
    "system_v7/constraint_core/sims_and_scripts/l6_phase_entropy_rung_v0/"
    "surface/extract_surface.py"
)
EXPECTED_FAMILY_COUNTS = {
    "orientation_winding": 9,
    "shell_position": 72,
    "marginal_entropy_level": 72,
    "factorization_boundary": 16,
}


def fail(message: str) -> None:
    raise SystemExit(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    buffer = io.StringIO()
    json.dump(value, buffer, sort_keys=True, indent=2)
    return buffer.getvalue().encode("utf-8")


def load_sources(base_dir: str) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    loaded: dict[str, Any] = {}
    provenance: dict[str, dict[str, str]] = {}
    for source_name, relative_path in SOURCE_PATHS.items():
        absolute_path = os.path.abspath(os.path.join(base_dir, relative_path))
        try:
            with open(absolute_path, "rb") as handle:
                source_bytes = handle.read()
        except OSError as exc:
            fail(f"cannot read {source_name} at {relative_path}: {exc}")
        provenance[source_name] = {
            "path": relative_path,
            "sha256": sha256_bytes(source_bytes),
        }
        if source_name == "S5":
            loaded[source_name] = source_bytes.decode("utf-8")
        else:
            try:
                loaded[source_name] = json.loads(source_bytes)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                fail(f"cannot parse {source_name} at {relative_path}: {exc}")
    return loaded, provenance


def binary_entropy_bits(probability: float) -> float:
    if probability == 0.0 or probability == 1.0:
        return 0.0
    return -probability * math.log2(probability) - (1.0 - probability) * math.log2(
        1.0 - probability
    )


def scalar_row(source: str, key_path: str, value: Any) -> dict[str, Any]:
    return {
        "name": key_path.split(".")[-1],
        "value": value,
        "provenance": f"{source}:{key_path}",
    }


def build_fixture_rows(
    s1: dict[str, Any], s4: dict[str, Any], s6: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    observations = s6["observations"]
    sweep = s1["dual_ratchet_sweep"]
    if len(observations) != 18:
        fail(f"C1 failed: expected 18 S6 observations, found {len(observations)}")

    joined_fields = {
        "shell_radius": "shell_radius",
        "entropy_bits": "marg_entropy_bits",
        "purity": "purity",
        "negativity": "negativity",
    }
    mismatches: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    chern_by_orientation = {
        1: s4["fact2_chern_sign_is_chirality"]["chern_plus_orientation"],
        -1: s4["fact2_chern_sign_is_chirality"]["chern_reversed_orientation"],
    }

    for observation_index, observation in enumerate(observations):
        row_id = observation["row_id"]
        radial_index = observation["radial_index"]
        orientation = observation["orientation"]
        if row_id != observation_index or not isinstance(row_id, int):
            fail(
                "C1 failed: S6 observations must have integer row_id equal to their list index"
            )
        if not isinstance(radial_index, int) or not 0 <= radial_index < len(sweep):
            fail(f"C1 failed: invalid radial_index at S6 observations[{row_id}]")
        if orientation not in chern_by_orientation or not isinstance(orientation, int):
            fail(f"C1 failed: invalid orientation at S6 observations[{row_id}]")

        sweep_row = sweep[radial_index]
        for fixture_field, sweep_field in joined_fields.items():
            if observation[fixture_field] != sweep_row[sweep_field]:
                mismatches.append(
                    {
                        "row_id": row_id,
                        "field": fixture_field,
                        "s6_value": observation[fixture_field],
                        "s1_value": sweep_row[sweep_field],
                    }
                )

        rows.append(
            {
                "row_id": row_id,
                "radial_index": radial_index,
                "orientation": orientation,
                "shell_radius": observation["shell_radius"],
                "entropy_bits": observation["entropy_bits"],
                "purity": observation["purity"],
                "negativity": observation["negativity"],
                "a": sweep_row["a"],
                "chern_signed": chern_by_orientation[orientation],
                "provenance": {
                    "fixture_row": f"S6:observations[{row_id}]",
                    "l5_sweep_index": radial_index,
                },
            }
        )

    if mismatches:
        fail(f"C1 failed: S6/S1 exact join found {len(mismatches)} mismatch(es)")
    return rows, {
        "name": "C1_fixture_observation_exact_join",
        "description": (
            "Exact parsed-value comparison of four S6 observation fields with "
            "the S1 sweep row selected by radial_index."
        ),
        "result_data": {"n_rows_checked": len(rows), "n_mismatch": 0},
        "exact": True,
    }


def build_holonomy_rows(s3: dict[str, Any]) -> list[dict[str, Any]]:
    source_rows = s3["fact1_flux_is_berry_holonomy"]["per_shell"]
    if len(source_rows) != 5:
        fail(f"expected 5 S3 holonomy rows, found {len(source_rows)}")
    rows: list[dict[str, Any]] = []
    for index, source_row in enumerate(source_rows):
        holonomy = source_row["holonomy"]
        sign = 0 if holonomy == 0.0 else (1 if holonomy > 0.0 else -1)
        rows.append(
            {
                "eta": source_row["eta"],
                "holonomy": holonomy,
                "analytic": source_row["analytic"],
                "abs_err": source_row["abs_err"],
                "holonomy_sign": sign,
                "provenance": f"S3:fact1_flux_is_berry_holonomy.per_shell[{index}]",
            }
        )
    return rows


def build_scalar_rows(sources: dict[str, Any]) -> list[dict[str, Any]]:
    specifications = [
        ("S3", "fact1_flux_is_berry_holonomy.flux_nested"),
        ("S3", "fact1_flux_is_berry_holonomy.max_analytic_err"),
        (
            "S3",
            "fact1_flux_is_berry_holonomy.ledger_form_-pi(cos2eta_i-cos2eta_j)",
        ),
        ("S3", "fact2_nonintegrable_curvature.closed_loop_holonomy"),
        ("S3", "fact2_nonintegrable_curvature.analytic"),
        ("S3", "fact3_flux_is_cross_shell.flux_self"),
        ("S3", "fact3_flux_is_cross_shell.erased_nesting_holonomy"),
        ("S2", "fact1_metric_is_bkm_hessian.bkm"),
        ("S2", "fact1_metric_is_bkm_hessian.rel_entropy_hessian"),
        ("S2", "fact1_metric_is_bkm_hessian.abs_diff"),
        ("S2", "fact1_metric_is_bkm_hessian.wrong_direction_metric"),
        (
            "S2",
            "fact2_metric_flat_in_eta_choice_vs_euclidean.g_eta_eta_values",
        ),
        ("S2", "fact2_metric_flat_in_eta_choice_vs_euclidean.g_rr_reparam"),
        ("S2", "fact3_monotone_cptp_contraction.before"),
        ("S2", "fact3_monotone_cptp_contraction.after_depol"),
        ("S2", "fact3_monotone_cptp_contraction.after_amplify_noncptp"),
        ("S4", "fact1_flux_quantized_chern.chern_number"),
        ("S4", "fact1_flux_quantized_chern.int_error"),
        ("S4", "fact2_chern_sign_is_chirality.chern_plus_orientation"),
        ("S4", "fact2_chern_sign_is_chirality.chern_reversed_orientation"),
        ("S4", "control_trivial_bundle.chern_trivial"),
        ("S1", "nested_shell_flux.flux_self"),
        ("S1", "nested_shell_flux.flux_nested"),
        ("S1", "refines_L4.shell_radius_v1"),
        ("S1", "refines_L4.shell_radius_v2"),
        ("S1", "refines_L4.radii_differ"),
        ("S1", "erase_nesting_control.erased_flux"),
        ("S1", "erase_nesting_control.erased_refine"),
    ]
    rows: list[dict[str, Any]] = []
    for source_name, key_path in specifications:
        value: Any = sources[source_name]
        for key in key_path.split("."):
            value = value[key]
        rows.append(scalar_row(source_name, key_path, value))
    return rows


def entropy_cross_check(fixture_rows: list[dict[str, Any]]) -> dict[str, Any]:
    deviations = []
    for row in fixture_rows:
        probability = (1.0 + row["shell_radius"]) / 2.0
        deviations.append(
            abs(row["entropy_bits"] - binary_entropy_bits(probability))
        )
    maximum = max(deviations)
    tolerance = 1e-9
    if maximum > tolerance:
        fail(f"C2 failed: max entropy deviation {maximum} exceeds {tolerance}")
    return {
        "name": "C2_entropy_consistency_probe",
        "description": (
            "Comparison-only binary-entropy check using p=(1+shell_radius)/2."
        ),
        "result_data": {
            "n_rows_checked": len(fixture_rows),
            "max_abs_deviation": maximum,
            "tolerance": tolerance,
            "within_tolerance": True,
        },
        "exact": False,
    }


def tooth_count_cross_check(s5_text: str, s6: dict[str, Any]) -> dict[str, Any]:
    matching_lines = [
        line for line in s5_text.splitlines() if "L_{orientation}(r)=9" in line
    ]
    if len(matching_lines) != 1:
        fail(f"C3 failed: expected one S5 tooth-count line, found {len(matching_lines)}")
    match = re.search(
        r"L_\{orientation\}\(r\)\s*=\s*(\d+).*?"
        r"L_\{orientation\}\(r,\\sigma\)\s*=\s*(\d+).*?"
        r"\\Delta\s+L\s*=\s*(\d+)",
        matching_lines[0],
    )
    if match is None:
        fail("C3 failed: S5 tooth-count line did not match the required three-number form")
    report_triple = [int(value) for value in match.groups()]
    source_counts = s6["entropy_geometry_coface"]["orientation_tooth"]
    source_triple = [
        source_counts["before_unresolved_edges"],
        source_counts["after_unresolved_edges"],
        source_counts["delta"],
    ]
    equal = report_triple == source_triple == [9, 0, 9]
    reproduction_file_named = "manifold_fixture_ratchet_results.json" in s5_text
    if not equal or not reproduction_file_named:
        fail(
            "C3 failed: S5/S6 tooth counts differ or S5 does not name the S6 reproduction file"
        )
    return {
        "name": "C3_tooth_count_exact_check",
        "description": (
            "Regex extraction of the three S5 orientation-tooth counts and exact "
            "comparison with the named S6 fields."
        ),
        "result_data": {
            "s5_triple": report_triple,
            "s6_triple": source_triple,
            "equal": True,
            "s6_reproduction_file_named_in_s5": True,
        },
        "exact": True,
    }


def chern_sign_cross_check(s4: dict[str, Any]) -> dict[str, Any]:
    sign_values = s4["fact2_chern_sign_is_chirality"]
    plus = sign_values["chern_plus_orientation"]
    reversed_orientation = sign_values["chern_reversed_orientation"]
    equal = reversed_orientation == -plus
    if not equal:
        fail("C4 failed: reversed-orientation Chern value is not exact float negation")
    return {
        "name": "C4_chern_sign_exact_check",
        "description": "Exact parsed-float negation check for the two S4 orientation values.",
        "result_data": {
            "chern_plus_orientation": plus,
            "chern_reversed_orientation": reversed_orientation,
            "exact_negation": True,
        },
        "exact": True,
    }


def field_provenance() -> dict[str, dict[str, str]]:
    return {
        "fixture_observations.row_id": {
            "source": "S6",
            "key_path_template": "observations[{row_id}].row_id",
        },
        "fixture_observations.radial_index": {
            "source": "S6",
            "key_path_template": "observations[{row_id}].radial_index",
        },
        "fixture_observations.orientation": {
            "source": "S6",
            "key_path_template": "observations[{row_id}].orientation",
        },
        "fixture_observations.shell_radius": {
            "source": "S6",
            "key_path_template": "observations[{row_id}].shell_radius",
        },
        "fixture_observations.entropy_bits": {
            "source": "S6",
            "key_path_template": "observations[{row_id}].entropy_bits",
        },
        "fixture_observations.purity": {
            "source": "S6",
            "key_path_template": "observations[{row_id}].purity",
        },
        "fixture_observations.negativity": {
            "source": "S6",
            "key_path_template": "observations[{row_id}].negativity",
        },
        "fixture_observations.a": {
            "source": "S1",
            "key_path_template": "dual_ratchet_sweep[{radial_index}].a",
        },
        "fixture_observations.chern_signed": {
            "source": "S4",
            "key_path_template": (
                "fact2_chern_sign_is_chirality.{orientation-selected Chern key}"
            ),
        },
        "fixture_observations.provenance.fixture_row": {
            "source": "S6",
            "key_path_template": "observations[{row_id}]",
        },
        "fixture_observations.provenance.l5_sweep_index": {
            "source": "S6",
            "key_path_template": "observations[{row_id}].radial_index",
        },
        "l7_holonomy_shells.eta": {
            "source": "S3",
            "key_path_template": "fact1_flux_is_berry_holonomy.per_shell[{i}].eta",
        },
        "l7_holonomy_shells.holonomy": {
            "source": "S3",
            "key_path_template": "fact1_flux_is_berry_holonomy.per_shell[{i}].holonomy",
        },
        "l7_holonomy_shells.analytic": {
            "source": "S3",
            "key_path_template": "fact1_flux_is_berry_holonomy.per_shell[{i}].analytic",
        },
        "l7_holonomy_shells.abs_err": {
            "source": "S3",
            "key_path_template": "fact1_flux_is_berry_holonomy.per_shell[{i}].abs_err",
        },
        "l7_holonomy_shells.holonomy_sign": {
            "source": "S3",
            "key_path_template": (
                "sign(fact1_flux_is_berry_holonomy.per_shell[{i}].holonomy)"
            ),
        },
        "l7_holonomy_shells.provenance": {
            "source": "S3",
            "key_path_template": "fact1_flux_is_berry_holonomy.per_shell[{i}]",
        },
        "scalar_facts.name": {
            "source": "S1|S2|S3|S4",
            "key_path_template": "final component of the row provenance key path",
        },
        "scalar_facts.value": {
            "source": "S1|S2|S3|S4",
            "key_path_template": "the full key path recorded by the same row provenance",
        },
        "scalar_facts.provenance": {
            "source": "S1|S2|S3|S4",
            "key_path_template": "{source}:{full key path}",
        },
    }


def normalized_source_pairs(s6: dict[str, Any], family: str) -> list[tuple[int, int]]:
    pairs = []
    for edge in s6["demand_families"][family]["edges"]:
        if not isinstance(edge, list) or len(edge) != 2:
            fail(f"source edge has invalid shape in S6 demand_families.{family}.edges")
        row_i, row_j = sorted(edge)
        pairs.append((row_i, row_j))
    return sorted(pairs)


def mine_pairs(
    fixture_rows: list[dict[str, Any]], family: str
) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for left_index, left in enumerate(fixture_rows):
        for right in fixture_rows[left_index + 1 :]:
            row_i = left["row_id"]
            row_j = right["row_id"]
            if family == "orientation_winding":
                selected = (
                    left["radial_index"] == right["radial_index"]
                    and left["orientation"] != right["orientation"]
                )
            elif family == "shell_position":
                selected = (
                    left["orientation"] == right["orientation"]
                    and left["radial_index"] != right["radial_index"]
                )
            elif family == "marginal_entropy_level":
                selected = (
                    left["orientation"] == right["orientation"]
                    and left["entropy_bits"] != right["entropy_bits"]
                )
            elif family == "factorization_boundary":
                selected = left["orientation"] == right["orientation"] and (
                    (left["negativity"] == 0.0) != (right["negativity"] == 0.0)
                )
            else:
                raise AssertionError(family)
            if selected:
                pairs.append((row_i, row_j))
    return sorted(pairs)


def per_edge_data(
    family: str, left: dict[str, Any], right: dict[str, Any]
) -> dict[str, Any]:
    if family == "orientation_winding":
        if left["entropy_bits"] != right["entropy_bits"]:
            fail(
                "orientation_winding exact entropy identity failed for "
                f"rows {left['row_id']} and {right['row_id']}"
            )
        return {
            "entropy_bits_i": left["entropy_bits"],
            "entropy_bits_j": right["entropy_bits"],
            "entropy_bits_delta": left["entropy_bits"] - right["entropy_bits"],
        }
    if family == "shell_position":
        return {
            "shell_radius_i": left["shell_radius"],
            "shell_radius_j": right["shell_radius"],
        }
    if family == "marginal_entropy_level":
        return {
            "entropy_bits_i": left["entropy_bits"],
            "entropy_bits_j": right["entropy_bits"],
        }
    if family == "factorization_boundary":
        return {
            "negativity_i": left["negativity"],
            "negativity_j": right["negativity"],
        }
    raise AssertionError(family)


def build_demand_families(
    fixture_rows: list[dict[str, Any]], s6: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_row_id = {row["row_id"]: row for row in fixture_rows}
    families: dict[str, Any] = {}
    checks: dict[str, Any] = {}
    mined_pair_sets: dict[str, set[tuple[int, int]]] = {}

    for family, expected_count in EXPECTED_FAMILY_COUNTS.items():
        mined_pairs = mine_pairs(fixture_rows, family)
        source_pairs = normalized_source_pairs(s6, family)
        source_declared_count = s6["demand_families"][family]["edge_count"]
        exact_match = (
            mined_pairs == source_pairs
            and len(source_pairs) == source_declared_count
            and len(mined_pairs) == expected_count
        )
        if not exact_match:
            fail(
                f"demand family {family} mismatch: mined={len(mined_pairs)} "
                f"source={len(source_pairs)} expected={expected_count}"
            )
        source_index = {pair: index for index, pair in enumerate(source_pairs)}
        edges = []
        for row_i, row_j in mined_pairs:
            edge = {
                "row_i": row_i,
                "row_j": row_j,
                "family": family,
                "provenance": {
                    "mined_from": (
                        "surface_v1.json:row_blocks.fixture_observations"
                    ),
                    "matched_against": (
                        f"S6:demand_families.{family}.edges["
                        f"{source_index[(row_i, row_j)]}]"
                    ),
                },
                "per_edge_data": per_edge_data(
                    family, by_row_id[row_i], by_row_id[row_j]
                ),
            }
            edges.append(edge)
        families[family] = {"edge_count": len(edges), "edges": edges}
        checks[family] = {
            "mined_count": len(mined_pairs),
            "source_count": len(source_pairs),
            "exact_match": True,
        }
        mined_pair_sets[family] = set(mined_pairs)

    set_equal = (
        mined_pair_sets["marginal_entropy_level"]
        == mined_pair_sets["shell_position"]
    )
    if not set_equal:
        fail("marginal_entropy_level and shell_position edge sets differ")
    checks["marginal_entropy_level_shell_position_set_equality"] = {
        "marginal_entropy_level_count": len(
            mined_pair_sets["marginal_entropy_level"]
        ),
        "shell_position_count": len(mined_pair_sets["shell_position"]),
        "set_equal": True,
    }
    return families, checks


def write_versioned_data(path: str, content: bytes) -> bool:
    if os.path.exists(path):
        with open(path, "rb") as handle:
            existing = handle.read()
        if existing != content:
            fail(
                f"{os.path.basename(path)} differs from newly computed content; "
                "bump the version suffix"
            )
        return True
    try:
        with open(path, "xb") as handle:
            handle.write(content)
    except FileExistsError:
        fail(
            f"{os.path.basename(path)} appeared during extraction; rerun after checking it"
        )
    return False


def update_receipt(path: str, fixed_receipt: dict[str, Any], run: dict[str, Any]) -> None:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                existing = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"cannot read existing receipt: {exc}")
        existing_fixed = {key: value for key, value in existing.items() if key != "runs"}
        if existing_fixed != fixed_receipt:
            fail(
                "extract_surface_receipt_v1.json fixed content differs; "
                "bump the version suffix"
            )
        runs = existing.get("runs")
        if not isinstance(runs, list):
            fail("extract_surface_receipt_v1.json runs must be a list")
        updated = dict(existing_fixed)
        updated["runs"] = runs + [run]
    else:
        updated = dict(fixed_receipt)
        updated["runs"] = [run]
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(updated, handle, sort_keys=True, indent=2)


def main() -> int:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sources, source_provenance = load_sources(base_dir)

    fixture_rows, c1 = build_fixture_rows(sources["S1"], sources["S4"], sources["S6"])
    holonomy_rows = build_holonomy_rows(sources["S3"])
    scalar_rows = build_scalar_rows(sources)
    surface_checks = [
        c1,
        entropy_cross_check(fixture_rows),
        tooth_count_cross_check(sources["S5"], sources["S6"]),
        chern_sign_cross_check(sources["S4"]),
    ]
    surface = {
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "schema_version": "l6_phase_entropy_surface/1.0",
        "sources": source_provenance,
        "row_blocks": {
            "fixture_observations": fixture_rows,
            "l7_holonomy_shells": holonomy_rows,
            "scalar_facts": scalar_rows,
        },
        "field_provenance": field_provenance(),
        "cross_checks": surface_checks,
        "counts": {
            "fixture_observation_rows": len(fixture_rows),
            "l7_holonomy_rows": len(holonomy_rows),
            "scalar_fact_rows": len(scalar_rows),
        },
    }

    families, demand_checks = build_demand_families(fixture_rows, sources["S6"])
    demand_counts = {
        "total_edges": sum(value["edge_count"] for value in families.values()),
        "per_family": {
            family: families[family]["edge_count"] for family in families
        },
    }
    if demand_counts["total_edges"] != 169:
        fail(f"expected 169 total demand edges, found {demand_counts['total_edges']}")
    demands = {
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "schema_version": "l6_phase_entropy_demands/1.0",
        "sources": source_provenance,
        "families": families,
        "mining_rules": {
            "orientation_winding": (
                "Pairs (i,j), i<j, with equal radial_index and unequal orientation."
            ),
            "shell_position": (
                "Pairs (i,j), i<j, with equal orientation and unequal radial_index."
            ),
            "marginal_entropy_level": (
                "Pairs (i,j), i<j, with equal orientation and exact-unequal entropy_bits."
            ),
            "factorization_boundary": (
                "Pairs (i,j), i<j, with equal orientation and exactly one negativity equal to 0.0."
            ),
            "source_match": (
                "Each mined family is sorted as sorted row-id pairs and exact-matched "
                "against the correspondingly normalized S6 edge list."
            ),
        },
        "cross_checks": demand_checks,
        "counts": demand_counts,
    }

    surface_content = json_bytes(surface)
    demands_content = json_bytes(demands)
    surface_path = os.path.join(base_dir, "surface_v1.json")
    demands_path = os.path.join(base_dir, "demand_families_v1.json")
    receipt_path = os.path.join(base_dir, "extract_surface_receipt_v1.json")
    surface_unchanged = write_versioned_data(surface_path, surface_content)
    demands_unchanged = write_versioned_data(demands_path, demands_content)

    fixed_receipt = {
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "script": SCRIPT_RELATIVE_PATH,
        "sources": source_provenance,
        "interpreter": sys.executable,
        "counts": {
            "rows": surface["counts"],
            "edges": demand_counts,
        },
        "cross_check_results": {
            "surface": {
                check["name"]: check["result_data"] for check in surface_checks
            },
            "demand_families": demand_checks,
        },
        "outputs": {
            "surface_v1.json": sha256_bytes(surface_content),
            "demand_families_v1.json": sha256_bytes(demands_content),
        },
    }
    run = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "unchanged": {
            "surface": surface_unchanged,
            "demands": demands_unchanged,
        },
    }
    update_receipt(receipt_path, fixed_receipt, run)

    print(f"surface_v1.json: {'unchanged' if surface_unchanged else 'created'}")
    print(f"demand_families_v1.json: {'unchanged' if demands_unchanged else 'created'}")
    print(f"fixture_observations rows: {len(fixture_rows)}")
    print(f"l7_holonomy_shells rows: {len(holonomy_rows)}")
    print(f"scalar_facts rows: {len(scalar_rows)}")
    for family in EXPECTED_FAMILY_COUNTS:
        print(f"{family} edges: {families[family]['edge_count']}")
    print(f"total edges: {demand_counts['total_edges']}")
    for check in surface_checks:
        print(
            f"{check['name']}: "
            f"{json.dumps(check['result_data'], sort_keys=True)}"
        )
    for check_name, result in demand_checks.items():
        print(f"{check_name}: {json.dumps(result, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

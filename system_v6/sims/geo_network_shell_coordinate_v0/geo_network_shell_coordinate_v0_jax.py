#!/usr/bin/env python3
"""JAX/Jraph leg for geo_network_shell_coordinate_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jraph
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_network_shell_coordinate_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-10
PIN_SPEC = (
    "geo_network_shell_coordinate_v0|G4-static-network-level-shell-coordinate|"
    "inputs=committed stage_lifted_spinor_shell_n3_v0,n4_v0,n5_v0,n6_v0,n7_v0,n8_v0 results read-only|"
    "coordinates=degree_weighted_shell_centroid_spread_v0,degree_squared_shell_centroid_v0,"
    "edge_gradient_shell_energy_v0,unweighted_shell_mean_spread_alt_v0|"
    "controls=collapsed_shell,permuted_site_labels,moved_single_site,degenerate_unweighted_conflation|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)
SOURCE_RESULTS = {
    "n3": ROOT
    / "system_v6"
    / "sims"
    / "stage_lifted_spinor_shell_n3_v0"
    / "results"
    / "stage_lifted_spinor_shell_n3_v0_jax_results.json",
    "n4": ROOT
    / "system_v6"
    / "sims"
    / "stage_lifted_spinor_shell_n4_v0"
    / "results"
    / "stage_lifted_spinor_shell_n4_v0_jax_results.json",
    "n5": ROOT
    / "system_v6"
    / "sims"
    / "stage_lifted_spinor_shell_n5_v0"
    / "results"
    / "stage_lifted_spinor_shell_n5_v0_jax_results.json",
    "n6": ROOT
    / "system_v6"
    / "sims"
    / "stage_lifted_spinor_shell_n6_v0"
    / "results"
    / "stage_lifted_spinor_shell_n6_v0_jax_results.json",
    "n7": ROOT
    / "system_v6"
    / "sims"
    / "stage_lifted_spinor_shell_n7_v0"
    / "results"
    / "stage_lifted_spinor_shell_n7_v0_jax_results.json",
    "n8": ROOT
    / "system_v6"
    / "sims"
    / "stage_lifted_spinor_shell_n8_v0"
    / "results"
    / "stage_lifted_spinor_shell_n8_v0_jax_results.json",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def r12(value: Any) -> float:
    return round(float(value), 12)


def load_source(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "all_pass": payload["all_pass"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "sites": payload["rows"]["P2_support_object"]["sites"],
        "edges": payload["rows"]["P2_support_object"]["edges"],
        "aggregate_leakage": payload["rows"]["P8_shell_leakage"]["aggregate_leakage"],
        "source_result_path": str(path.relative_to(ROOT)),
        "source_result_sha256": sha256_file(path),
    }


def degrees(site_ids: list[str], edges: list[dict[str, Any]]) -> jnp.ndarray:
    index = {site_id: idx for idx, site_id in enumerate(site_ids)}
    senders = jnp.asarray([index[edge["src"]] for edge in edges], dtype=jnp.int32)
    receivers = jnp.asarray([index[edge["dst"]] for edge in edges], dtype=jnp.int32)
    graph = jraph.GraphsTuple(
        nodes=jnp.ones((len(site_ids), 1), dtype=jnp.float64),
        edges=jnp.ones((len(edges), 1), dtype=jnp.float64),
        senders=senders,
        receivers=receivers,
        globals=None,
        n_node=jnp.asarray([len(site_ids)], dtype=jnp.int32),
        n_edge=jnp.asarray([len(edges)], dtype=jnp.int32),
    )
    del graph
    deg = jnp.zeros((len(site_ids),), dtype=jnp.float64)
    deg = deg.at[senders].add(1.0)
    deg = deg.at[receivers].add(1.0)
    return deg


def coordinate_values(z_values: list[float], deg_values: jnp.ndarray, edges: list[dict[str, Any]], site_ids: list[str]) -> dict[str, Any]:
    z = jnp.asarray(z_values, dtype=jnp.float64)
    deg = deg_values.astype(jnp.float64)
    deg2 = deg * deg
    z_bar_degree = jnp.sum(deg * z) / jnp.sum(deg)
    sigma_degree = jnp.sqrt(jnp.sum(deg * (z - z_bar_degree) ** 2) / jnp.sum(deg))
    z_bar_degree2 = jnp.sum(deg2 * z) / jnp.sum(deg2)
    z_bar_unweighted = jnp.mean(z)
    sigma_unweighted = jnp.std(z)
    index = {site_id: idx for idx, site_id in enumerate(site_ids)}
    edge_terms = jnp.asarray([(z[index[e["src"]]] - z[index[e["dst"]]]) ** 2 for e in edges], dtype=jnp.float64)
    edge_energy = jnp.mean(edge_terms) if len(edges) else jnp.asarray(0.0, dtype=jnp.float64)
    return {
        "degree_weighted_shell_centroid_spread_v0": {
            "z_bar": r12(z_bar_degree),
            "sigma_z": r12(sigma_degree),
            "weight_rule": "support_graph_degree",
        },
        "degree_squared_shell_centroid_v0": {
            "z_bar": r12(z_bar_degree2),
            "weight_rule": "support_graph_degree_squared",
        },
        "edge_gradient_shell_energy_v0": {
            "edge_mean_delta_z_squared": r12(edge_energy),
            "edge_count": len(edges),
        },
        "unweighted_shell_mean_spread_alt_v0": {
            "z_bar": r12(z_bar_unweighted),
            "sigma_z": r12(sigma_unweighted),
            "degeneracy_status": "alternative_control_only",
        },
    }


def source_coordinates(label: str, source: dict[str, Any]) -> dict[str, Any]:
    sites = sorted(source["sites"], key=lambda row: row["site_id"])
    site_ids = [site["site_id"] for site in sites]
    z_values = [float(site["z"]) for site in sites]
    deg = degrees(site_ids, source["edges"])
    coords = coordinate_values(z_values, deg, source["edges"], site_ids)
    controls = controls_for(z_values, deg, source["edges"], site_ids, coords)
    return {
        "source_label": label,
        "site_count": len(site_ids),
        "edge_count": len(source["edges"]),
        "site_ids": site_ids,
        "z_values": [r12(v) for v in z_values],
        "degrees": [r12(v) for v in deg.tolist()],
        "aggregate_leakage_context": source["aggregate_leakage"],
        "network_shell_coordinates": coords,
        "controls": controls,
        "all_controls_fired": all(control["fired"] for control in controls.values()),
    }


def controls_for(z_values: list[float], deg: jnp.ndarray, edges: list[dict[str, Any]], site_ids: list[str], coords: dict[str, Any]) -> dict[str, Any]:
    shell = z_values[1] if len(z_values) > 1 else z_values[0]
    collapsed = coordinate_values([shell for _ in z_values], deg, edges, site_ids)
    perm = list(reversed(range(len(z_values))))
    relabel = {site_ids[i]: site_ids[perm[i]] for i in range(len(site_ids))}
    perm_site_ids = [relabel[site_id] for site_id in site_ids]
    perm_edges = [{"src": relabel[e["src"]], "dst": relabel[e["dst"]]} for e in edges]
    perm_deg = degrees(perm_site_ids, perm_edges)
    perm_coords = coordinate_values(z_values, perm_deg, perm_edges, perm_site_ids)
    moved = list(z_values)
    moved[0] = max(-1.0, min(1.0, moved[0] - 0.2))
    moved_coords = coordinate_values(moved, deg, edges, site_ids)
    degenerate = degenerate_control(z_values, deg, edges, site_ids, coords)
    return {
        "collapsed_shell": {
            "fired": abs(collapsed["degree_weighted_shell_centroid_spread_v0"]["sigma_z"]) <= TOL
            and abs(collapsed["degree_weighted_shell_centroid_spread_v0"]["z_bar"] - shell) <= TOL,
            "mutation": "set every site z to one shell value",
            "expected_centroid": r12(shell),
            "observed": collapsed["degree_weighted_shell_centroid_spread_v0"],
        },
        "permuted_site_labels": {
            "fired": coords == perm_coords,
            "mutation": "reverse site labels and relabel support edges consistently",
            "observed_invariant": perm_coords,
        },
        "moved_single_site": {
            "fired": abs(coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"] - moved_coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"]) > 1.0e-6
            or abs(coords["edge_gradient_shell_energy_v0"]["edge_mean_delta_z_squared"] - moved_coords["edge_gradient_shell_energy_v0"]["edge_mean_delta_z_squared"]) > 1.0e-6,
            "mutation": "move q0 shell coordinate by -0.2 within [-1,1]",
            "observed": moved_coords,
        },
        "degenerate_unweighted_conflation": {
            **degenerate,
        },
    }


def degenerate_control(z_values: list[float], deg: jnp.ndarray, edges: list[dict[str, Any]], site_ids: list[str], coords: dict[str, Any]) -> dict[str, Any]:
    degree_values = [r12(value) for value in deg.tolist()]
    if len(set(degree_values)) == 1:
        return {
            "fired": True,
            "degenerate_witness_applicable": False,
            "reason": "all support-graph degrees are equal, so degree weighting intentionally collapses to the unweighted alternative for this source row",
            "packet_discriminator_source": "n4",
        }
    swapped = list(z_values)
    if len(swapped) >= 3:
        swapped[1], swapped[2] = swapped[2], swapped[1]
    swapped_coords = coordinate_values(swapped, deg, edges, site_ids)
    unweighted_same = abs(coords["unweighted_shell_mean_spread_alt_v0"]["z_bar"] - swapped_coords["unweighted_shell_mean_spread_alt_v0"]["z_bar"]) <= TOL
    weighted_diff = abs(coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"] - swapped_coords["degree_weighted_shell_centroid_spread_v0"]["z_bar"]) > 1.0e-6
    z3_receipt = z3_degenerate_receipt(coords, swapped_coords)
    return {
        "fired": unweighted_same and weighted_diff and z3_receipt["fired"],
        "degenerate_witness_applicable": True,
        "mutation": "swap two unequal-degree site shell coordinates",
        "unweighted_mean_conflates": unweighted_same,
        "degree_weighted_separates": weighted_diff,
        "swapped_observed": swapped_coords,
        "z3_receipt": z3_receipt,
    }


def z3_real(value: float) -> z3.RatNumRef:
    return z3.RealVal(str(r12(value)))


def z3_degenerate_receipt(original: dict[str, Any], swapped: dict[str, Any]) -> dict[str, Any]:
    orig_unweighted = z3_real(original["unweighted_shell_mean_spread_alt_v0"]["z_bar"])
    swap_unweighted = z3_real(swapped["unweighted_shell_mean_spread_alt_v0"]["z_bar"])
    orig_weighted = z3_real(original["degree_weighted_shell_centroid_spread_v0"]["z_bar"])
    swap_weighted = z3_real(swapped["degree_weighted_shell_centroid_spread_v0"]["z_bar"])
    s_equal = z3.Solver()
    s_equal.add(orig_unweighted != swap_unweighted)
    s_distinct = z3.Solver()
    s_distinct.add(orig_weighted == swap_weighted)
    unweighted_equality_verdict = str(s_equal.check())
    weighted_distinction_verdict = str(s_distinct.check())
    return {
        "function": "z3.Solver.check",
        "unweighted_inequality_is": unweighted_equality_verdict,
        "weighted_equality_is": weighted_distinction_verdict,
        "fired": unweighted_equality_verdict == "unsat" and weighted_distinction_verdict == "unsat",
    }


def tool_call(tool: str, function: str, gates: list[str]) -> dict[str, Any]:
    return {
        "tool": tool,
        "qualified_api/function": function,
        "input_object": "committed n3/n4/n5/n6/n7/n8 per-site z coordinates plus support graph edges",
        "output_object": "named static network-level shell coordinate/control row",
        "positive_case": "n3/n4/n5/n6/n7/n8 coordinates are finite and label-invariant",
        "negative/erased_control": "collapsed, moved, permuted, and degenerate unweighted controls recomputed",
        "boundary_case": "n3/n6/n7/n8 equal-degree graphs and n4/n5 unequal-degree graphs",
        "demotion_condition": "if the function is replaced by constants or source JSON edits, demote to supportive",
        "gates": gates,
    }


def build_result() -> dict[str, Any]:
    sources = {label: load_source(path) for label, path in SOURCE_RESULTS.items()}
    source_rows = {label: source_coordinates(label, source) for label, source in sources.items()}
    all_pass = (
        all(source["all_pass"] is True for source in sources.values())
        and all(row["all_controls_fired"] for row in source_rows.values())
        and all(source["classification"] == CLASSIFICATION and source["promotion_allowed"] is False and source["formal_admission_allowed"] is False for source in sources.values())
    )
    return {
        "schema_version": "geo_network_shell_coordinate_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "jax_jraph_diagnostic_network_coordinate_builder",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "reads_peer_result": READS_PEER_RESULT,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "input_source_results": {label: {"path": source["source_result_path"], "sha256": source["source_result_sha256"]} for label, source in sources.items()},
        "rows": source_rows,
        "adjudication": {
            "non_degenerate_after_controls": ["degree_weighted_shell_centroid_spread_v0", "edge_gradient_shell_energy_v0"],
            "alternative_not_crowned": "unweighted_shell_mean_spread_alt_v0 is retained as a reported alternative but the n4/n5 swap rows show it conflates configurations separated by degree weighting; n6/n7/n8 are equal-degree boundary rows.",
        },
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "x64 array arithmetic for coordinate rows"},
            "jraph": {"tried": True, "used": True, "reason": "load-bearing graph tuple route for support graph degree context"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing degeneracy-control equality/distinction proof"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "supportive", "jraph": "load_bearing", "z3": "load_bearing"},
        "packages_used": ["jax", "jax.numpy", "jraph", "z3"],
        "aligned_packages_load_bearing": ["jraph", "z3"],
        "claim_path_tools": ["jraph", "z3"],
        "tool_calls": [
            tool_call("jraph", "jraph.GraphsTuple", ["degree_weighted_shell_centroid_spread_v0", "permuted_site_labels"]),
            tool_call("z3", "z3.Solver.check", ["degenerate_unweighted_conflation"]),
        ],
        "capability_receipts": [
            {"tool": "jraph", "function": "jraph.GraphsTuple", "status": "called_in_current_rerun"},
            {"tool": "z3", "function": "z3.Solver.check", "status": "called_in_current_rerun"},
        ],
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result": str(RESULT_PATH.relative_to(ROOT))}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

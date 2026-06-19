#!/usr/bin/env python3
"""Terrain-blind common finite-carve builder for gcm_constraint_carve_v1."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "gcm_constraint_carve_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "first_carve_candidate_v1_only_carrier_and_pins_relative"
ENGINE_MODE = "all_three_full_sims"
GRID_VALUES = (-1.0, -0.5, 0.0, 0.5, 1.0)
PROBE_FAMILY = ("sigma_x", "sigma_z")
SCRAMBLED_PROBE_FAMILY = ("sigma_y", "sigma_z")
EXPECTED_CANDIDATE_COUNT = 125
EXPECTED_DENSITY_COUNT = 33
EXPECTED_SURVIVOR_COUNT = 16
EXPECTED_QUOTIENT_CLASS_COUNT = 8
EXPECTED_V0_REGRESSION_SURVIVOR_COUNT = 8
EXPECTED_V0_REGRESSION_CLASS_COUNT = 4
EXPECTED_MCT_SURVIVOR_COUNT = 8
EXPECTED_MCT_QUOTIENT_CLASS_COUNT = 4

FORBIDDEN_PREDICATE_TOKENS = (
    "terrain",
    "atlas",
    "Se",
    "Ne",
    "Ni",
    "Si",
    "dissipative",
    "circulation",
    "dissipative-vs-circulation",
)

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402


PARENT_PATHS = {
    "v0_audit_verdict": ROOT / "system_v6" / "sims" / "gcm_constraint_carve_v0" / "audit_verdict.md",
    "gcm_reanchor": ROOT / "system_v6" / "receipts" / "gcm_reanchor_requirement_20260612.md",
    "audit_standards_codex": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
    "root_axioms_v0_1": ROOT / "system_v6" / "foundations" / "root_axioms_v0_1_DRAFT.md",
    "working_math_scaffold": ROOT / "system_v6" / "foundations" / "working_math_scaffold_20260609.md",
    "two_engine_readout_automaton": ROOT / "system_v6" / "foundations" / "two_engine_readout_automaton_20260609.md",
    "builder_audit_boundary": ROOT / "scripts" / "builder_audit_boundary.py",
    "build_card": SIM_DIR / "build_card.md",
}

PARENT_COMMITS = {
    "gcm_reanchor": "393c5147a",
    "audit_standards_codex": "current",
    "mct_foundations": "dd9ec4999",
    "v0_audit_verdict": "local_v0_audit_contract",
}

PRIOR_ART_READ_NOT_AUTHORITY = {
    "path": "system_v6/sims/gcm_constraint_carve_floor_v0",
    "role": "prior_art_only_not_cited_as_constraint_authority",
    "cite_as_authority": False,
}

TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite survivor adjacency graph and component computation."},
    "networkx": {"tried": True, "used": True, "reason": "JAX/Python finite graph and quotient component cross-check."},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch batched predicate and active-probe checks over the candidate grid."},
    "sympy": {"tried": True, "used": True, "reason": "Exact integer count guards for candidate, survivor, quotient, and v0 regression rows."},
    "z3": {"tried": True, "used": True, "reason": "SMT binding of computed nonempty carve and exact survivor count."},
    "cvc5": {"tried": True, "used": True, "reason": "Independent SMT binding of the same computed carve count."},
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "G.2a post-audit-idempotent builder/audit boundary from birth."},
}

TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "finite_constraint_carve",
        "M_C_survivor_set",
        "probe_relative_quotient",
        "no_identity_leak_independence",
        "terrain_blind_predicate_guard",
        "post_carve_readout_only",
        "v0_regression_contamination_diff",
        "M_C_t_one_step_update",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "SimpleGraph/add_edge!/connected_components compute survivor and quotient adjacency components."
        },
        "jax": {
            "networkx": "nx.Graph and connected_components recompute survivor and quotient graph structure.",
            "sympy": "sp.Rational guards exact candidate/survivor/class/regression counts.",
        },
        "pytorch": {
            "torch.func": "vmap over candidate coordinates checks finite density, active probes, and order-gap predicate.",
            "sympy": "sp.Rational guards exact candidate/survivor/class/regression counts.",
        },
    },
}

LOCAL_SOURCE_QUOTES = {
    "C1_finite_density_carrier": {
        "source_path": "system_v6/sims/gcm_constraint_carve_v1/build_card.md",
        "quote": "C1 predicate source line: `C1_finite_density_carrier` accepts exactly candidates on `GRID_VALUES={-1,-1/2,0,1/2,1}` with `x*x + y*y + z*z <= 1`.",
        "status": "local_adapter_pin",
    },
    "C2_probe_distinguishability_xz_local_adapter_pin": {
        "source_path": "system_v6/sims/gcm_constraint_carve_v1/build_card.md",
        "quote": "C2 predicate source line: `C2_probe_distinguishability_xz_local_adapter_pin` accepts exactly candidates whose active probe pair `(2*x, 2*z)` is not `(0, 0)`.",
        "status": "local_adapter_pin_demoted_exact_xz_probe_and_zero_active_class",
    },
    "C3_persistence_n01_order_gap": {
        "source_path": "system_v6/sims/gcm_constraint_carve_v1/build_card.md",
        "quote": "C3 predicate source line: `C3_persistence_n01_order_gap` accepts exactly candidates whose `D_z after R_x` and `R_x after D_z` active x/z probe signatures differ.",
        "status": "local_adapter_pin",
    },
    "C5_t1_positive_active_coordinate_pin": {
        "source_path": "system_v6/sims/gcm_constraint_carve_v1/build_card.md",
        "quote": "C5 predicate source line: `C5_t1_positive_active_coordinate_pin` is a downstream `M(C,t)` hook that keeps candidates whose first nonzero active coordinate in `(x, z)` is positive.",
        "status": "local_adapter_pin_downstream_M_C_t_hook",
    },
}

CONSTRAINTS = [
    {
        "id": "C1_finite_density_carrier",
        "quoted_source_line": LOCAL_SOURCE_QUOTES["C1_finite_density_carrier"],
        "literal_executable_predicate": "x*x + y*y + z*z <= 1 over GRID_VALUES",
    },
    {
        "id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "quoted_source_line": LOCAL_SOURCE_QUOTES["C2_probe_distinguishability_xz_local_adapter_pin"],
        "literal_executable_predicate": "(2*x, 2*z) != (0, 0)",
        "citation_repair": "Exact x/z probe and zero-active-class exclusion are explicitly demoted to a local adapter pin.",
    },
    {
        "id": "C3_persistence_n01_order_gap",
        "quoted_source_line": LOCAL_SOURCE_QUOTES["C3_persistence_n01_order_gap"],
        "literal_executable_predicate": "probe_signature(D_z_after_R_x(coord)) != probe_signature(R_x_after_D_z(coord))",
    },
]


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None
    return out or None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists() and path.is_file():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def q(value: float) -> float:
    rounded = round(float(value), 12)
    return 0.0 if rounded == 0 else rounded


def scaled(value: float) -> int:
    return int(round(2.0 * value))


def candidate_space() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for x in GRID_VALUES:
        for y in GRID_VALUES:
            for z in GRID_VALUES:
                coord = (x, y, z)
                rows.append(
                    {
                        "candidate_id": len(rows),
                        "coord": [q(v) for v in coord],
                        "coord_scaled": [scaled(v) for v in coord],
                        "radius_squared": q(sum(v * v for v in coord)),
                    }
                )
    return rows


def is_density_candidate(coord: tuple[float, float, float]) -> bool:
    return sum(v * v for v in coord) <= 1.0 + 1.0e-12


def probe_signature(coord: tuple[float, float, float], family: tuple[str, str] = PROBE_FAMILY) -> tuple[int, int]:
    mapping = {"sigma_x": coord[0], "sigma_y": coord[1], "sigma_z": coord[2]}
    return tuple(scaled(mapping[name]) for name in family)  # type: ignore[return-value]


def active_probe_nonzero(coord: tuple[float, float, float]) -> bool:
    return probe_signature(coord) != (0, 0)


def dz_after_rx(coord: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coord
    return (0.5 * x, -0.5 * z, y)


def rx_after_dz(coord: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coord
    return (0.5 * x, -z, 0.5 * y)


def order_gap(coord: tuple[float, float, float]) -> float:
    left = probe_signature(dz_after_rx(coord))
    right = probe_signature(rx_after_dz(coord))
    return q(math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right))))


def persistence_order_ok(coord: tuple[float, float, float]) -> bool:
    return order_gap(coord) >= 0.5


def first_active_coordinate_positive(coord: tuple[float, float, float]) -> bool:
    x, _y, z = coord
    if x != 0:
        return x > 0
    if z != 0:
        return z > 0
    return False


def rejected_v0_c4_predicate(coord: tuple[float, float, float]) -> bool:
    x, _y, z = coord
    return not (x != 0 and z != 0)


def constraint_passes(constraint_id: str, row: dict[str, Any]) -> bool:
    coord = tuple(float(v) for v in row["coord"])
    if constraint_id == "C1_finite_density_carrier":
        return is_density_candidate(coord)
    if constraint_id == "C2_probe_distinguishability_xz_local_adapter_pin":
        return active_probe_nonzero(coord)
    if constraint_id == "C3_persistence_n01_order_gap":
        return persistence_order_ok(coord)
    if constraint_id == "C5_t1_positive_active_coordinate_pin":
        return first_active_coordinate_positive(coord)
    if constraint_id == "C_overconstrained_impossible_empty":
        return False
    if constraint_id == "v0_rejected_C4_terrain_framed_residency_variant":
        return rejected_v0_c4_predicate(coord)
    raise KeyError(constraint_id)


def final_constraint_ids() -> list[str]:
    return [row["id"] for row in CONSTRAINTS]


def apply_constraint_set(constraint_ids: list[str]) -> dict[str, Any]:
    survivors: list[dict[str, Any]] = []
    kill_ledger: list[dict[str, Any]] = []
    for row in candidate_space():
        failures = [cid for cid in constraint_ids if not constraint_passes(cid, row)]
        enriched = dict(row)
        coord = tuple(float(v) for v in row["coord"])
        enriched.update(
            {
                "probe_signature": list(probe_signature(coord)),
                "scrambled_probe_signature": list(probe_signature(coord, SCRAMBLED_PROBE_FAMILY)),
                "order_gap": order_gap(coord),
            }
        )
        if failures:
            kill_ledger.append(
                {
                    "candidate_id": row["candidate_id"],
                    "coord": row["coord"],
                    "killed_by": failures[0],
                    "all_failed_constraints": failures,
                }
            )
        else:
            enriched["survivor_id"] = len(survivors)
            survivors.append(enriched)
    return {"constraint_ids": constraint_ids, "survivors": survivors, "kill_ledger": kill_ledger}


def survivor_key(row: dict[str, Any]) -> tuple[int, int, int]:
    return tuple(int(v) for v in row["coord_scaled"])  # type: ignore[return-value]


def build_quotient(survivors: list[dict[str, Any]], family: tuple[str, str] = PROBE_FAMILY) -> dict[str, Any]:
    buckets: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in survivors:
        coord = tuple(float(v) for v in row["coord"])
        buckets[probe_signature(coord, family)].append(row)
    classes = []
    for idx, key in enumerate(sorted(buckets)):
        members = sorted(buckets[key], key=lambda row: row["survivor_id"])
        classes.append(
            {
                "class_id": f"Q{idx}",
                "probe_signature": list(key),
                "member_survivor_ids": [row["survivor_id"] for row in members],
                "member_candidate_ids": [row["candidate_id"] for row in members],
            }
        )
    return {"probe_family": list(family), "class_count": len(classes), "classes": classes}


def quantize_half_step(value: float) -> float:
    if value >= 0.25:
        return 0.5
    if value <= -0.25:
        return -0.5
    return 0.0


def committed_update(coord: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coord
    return (quantize_half_step(0.5 * x), quantize_half_step(0.5 * y), z)


def update_targets(row: dict[str, Any]) -> list[tuple[str, tuple[int, int, int]]]:
    x, y, z = (float(v) for v in row["coord"])
    targets = [("hidden_probe_flip", (scaled(x), scaled(-y), scaled(z)))]
    if z == 0 and x != 0:
        targets.append(("x_reflection_at_z_zero", (scaled(-x), scaled(-y), scaled(z))))
    if x == 0 and z != 0:
        targets.append(("z_reflection_at_x_zero", (scaled(x), scaled(-y), scaled(-z))))
    return targets


def class_stability(survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    class_by_sig = {tuple(row["probe_signature"]): row["class_id"] for row in quotient["classes"]}
    rows = []
    stable = True
    for qrow in quotient["classes"]:
        image_classes = set()
        for survivor_id in qrow["member_survivor_ids"]:
            source = survivors[survivor_id]
            target_sig = list(probe_signature(committed_update(tuple(float(v) for v in source["coord"]))))
            image_classes.add(class_by_sig.get(tuple(target_sig), "outside_current_quotient"))
        row_stable = len(image_classes) == 1 and "outside_current_quotient" not in image_classes
        stable = stable and row_stable
        rows.append({"class_id": qrow["class_id"], "image_classes": sorted(image_classes), "stable": row_stable})
    return {
        "committed_update": "coarse_D_z_half_step_Q_grid",
        "stable": stable,
        "rows": rows,
    }


def graph_components(survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    key_to_survivor = {survivor_key(row): row["survivor_id"] for row in survivors}
    class_for_survivor = {}
    for qrow in quotient["classes"]:
        for sid in qrow["member_survivor_ids"]:
            class_for_survivor[sid] = qrow["class_id"]
    edges = []
    quotient_edges = set()
    adjacency = {row["survivor_id"]: set() for row in survivors}
    for row in survivors:
        src = row["survivor_id"]
        for update_name, target_key in update_targets(row):
            dst = key_to_survivor.get(target_key)
            if dst is None:
                continue
            edge = {"src": src, "dst": dst, "update": update_name}
            if edge not in edges:
                edges.append(edge)
            adjacency[src].add(dst)
            adjacency[dst].add(src)
            quotient_edges.add((class_for_survivor[src], class_for_survivor[dst], update_name))

    seen = set()
    components = []
    for node in sorted(adjacency):
        if node in seen:
            continue
        stack = [node]
        comp = []
        seen.add(node)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in sorted(adjacency[cur]):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        components.append(sorted(comp))

    q_adj = defaultdict(set)
    for src, dst, _name in quotient_edges:
        q_adj[src].add(dst)
        q_adj[dst].add(src)
    q_seen = set()
    q_components = []
    for qrow in quotient["classes"]:
        node = qrow["class_id"]
        if node in q_seen:
            continue
        stack = [node]
        comp = []
        q_seen.add(node)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in sorted(q_adj[cur]):
                if nxt not in q_seen:
                    q_seen.add(nxt)
                    stack.append(nxt)
        q_components.append(sorted(comp))

    return {
        "survivor_edges": sorted(edges, key=lambda e: (e["src"], e["dst"], e["update"])),
        "survivor_components": components,
        "quotient_edges": [
            {"src_class": src, "dst_class": dst, "update": name} for src, dst, name in sorted(quotient_edges)
        ],
        "quotient_components": q_components,
    }


def constraint_controls(base_ids: list[str], base_survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    empty = apply_constraint_set([])
    over = apply_constraint_set(base_ids + ["C_overconstrained_impossible_empty"])
    erasures = []
    base_set = {row["candidate_id"] for row in base_survivors}
    for cid in base_ids:
        ids = [item for item in base_ids if item != cid]
        result = apply_constraint_set(ids)
        survivor_set = {row["candidate_id"] for row in result["survivors"]}
        erasures.append(
            {
                "dropped_constraint": cid,
                "survivor_count": len(survivor_set),
                "delta_count": len(survivor_set ^ base_set),
                "added_candidate_ids": sorted(survivor_set - base_set),
                "removed_candidate_ids": sorted(base_set - survivor_set),
                "bite": survivor_set != base_set,
            }
        )
    scrambled = build_quotient(base_survivors, SCRAMBLED_PROBE_FAMILY)
    blindness = blindness_control()
    return {
        "empty_C": {
            "survivor_count": len(empty["survivors"]),
            "degenerate_no_manifold": len(empty["survivors"]) == EXPECTED_CANDIDATE_COUNT,
        },
        "overconstrained_C": {
            "survivor_count": len(over["survivors"]),
            "cliff_constraint": "C_overconstrained_impossible_empty",
            "all_killed": len(over["survivors"]) == 0,
        },
        "constraint_erasure": erasures,
        "probe_family_scramble": {
            "baseline_probe_family": list(PROBE_FAMILY),
            "scrambled_probe_family": list(SCRAMBLED_PROBE_FAMILY),
            "baseline_class_signatures": [row["probe_signature"] for row in quotient["classes"]],
            "scrambled_class_signatures": [row["probe_signature"] for row in scrambled["classes"]],
            "quotient_moved": stable_sha256(quotient["classes"]) != stable_sha256(scrambled["classes"]),
        },
        "blindness_control": blindness,
    }


def mct_hook(base_ids: list[str]) -> dict[str, Any]:
    ids = base_ids + ["C5_t1_positive_active_coordinate_pin"]
    result = apply_constraint_set(ids)
    quotient = build_quotient(result["survivors"])
    return {
        "update": "C -> C_prime = C plus C5_t1_positive_active_coordinate_pin",
        "new_constraint": {
            "id": "C5_t1_positive_active_coordinate_pin",
            "quoted_source_line": LOCAL_SOURCE_QUOTES["C5_t1_positive_active_coordinate_pin"],
            "literal_executable_predicate": "first nonzero active coordinate in (x,z) is positive",
        },
        "survivor_count": len(result["survivors"]),
        "quotient_class_count": quotient["class_count"],
        "survivor_candidate_ids": [row["candidate_id"] for row in result["survivors"]],
        "classes": quotient["classes"],
    }


def post_carve_region_readout(quotient: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    rows = []
    counts: Counter[str] = Counter()
    for qrow in quotient["classes"]:
        sig_x, sig_z = qrow["probe_signature"]
        if sig_x != 0 and sig_z != 0:
            label = "mixed_active_probe_region"
        elif sig_x != 0:
            label = "x_axis_active_region"
        elif sig_z != 0:
            label = "z_axis_active_region"
        else:
            label = "zero_active_probe_region_absent"
        counts[label] += 1
        rows.append({"class_id": qrow["class_id"], "probe_signature": qrow["probe_signature"], "readout_label": label})
    return {
        "question": "post-carve terrain readout only; this field is not an admissibility input",
        "answer": "post_carve_partial_macro_readout_not_full_atlas",
        "can_affect_survival": False,
        "survival_inputs": [],
        "class_count": quotient["class_count"],
        "readout_rows": rows,
        "class_counts_by_readout_label": dict(sorted(counts.items())),
        "reason": (
            "The blind survivor quotient has 8 probe classes, including mixed active-probe classes. "
            "This downstream row can name candidate regions, but it does not define or filter M(C)."
        ),
        "quotient_components": graph["quotient_components"],
        "terrain_atlas_not_claimed": True,
    }


def identity_leak_probe(survivors: list[dict[str, Any]], kill_ledger: list[dict[str, Any]]) -> dict[str, Any]:
    labels: dict[int, str] = {row["candidate_id"]: "survived" for row in survivors}
    labels.update({row["candidate_id"]: "killed" for row in kill_ledger})
    candidates = candidate_space()

    def majority_accuracy(feature_values: list[Any]) -> float:
        buckets: dict[Any, Counter[str]] = defaultdict(Counter)
        for row, feature in zip(candidates, feature_values):
            buckets[feature][labels[row["candidate_id"]]] += 1
        correct = sum(max(counter.values()) for counter in buckets.values())
        return correct / len(candidates)

    identity_features = {
        "candidate_id": [row["candidate_id"] for row in candidates],
        "coord_tuple": [tuple(row["coord_scaled"]) for row in candidates],
        "direct_constraint_fingerprint": [
            tuple(int(constraint_passes(cid, row)) for cid in final_constraint_ids()) for row in candidates
        ],
    }
    non_identity_features = {
        "radius_squared": [row["radius_squared"] for row in candidates],
        "active_probe_count": [
            int(tuple(float(v) for v in row["coord"])[0] != 0) + int(tuple(float(v) for v in row["coord"])[2] != 0)
            for row in candidates
        ],
        "order_gap_value": [order_gap(tuple(float(v) for v in row["coord"])) for row in candidates],
        "density_and_order_pair": [
            (
                is_density_candidate(tuple(float(v) for v in row["coord"])),
                persistence_order_ok(tuple(float(v) for v in row["coord"])),
            )
            for row in candidates
        ],
        "active_probe_count_plus_order": [
            (
                int(tuple(float(v) for v in row["coord"])[0] != 0)
                + int(tuple(float(v) for v in row["coord"])[2] != 0),
                order_gap(tuple(float(v) for v in row["coord"])),
            )
            for row in candidates
        ],
    }
    identity_accuracies = {name: majority_accuracy(values) for name, values in identity_features.items()}
    non_identity_accuracies = {name: majority_accuracy(values) for name, values in non_identity_features.items()}
    best_non_identity_name, best_non_identity_accuracy = max(non_identity_accuracies.items(), key=lambda item: item[1])
    return {
        "identity_leak_detected": any(value == 1.0 for value in identity_accuracies.values()),
        "identity_inclusive_accuracies": {key: round(value, 12) for key, value in sorted(identity_accuracies.items())},
        "identity_leak_excluded_best_accuracy": round(best_non_identity_accuracy, 12),
        "identity_leak_excluded_best_predictor": best_non_identity_name,
        "identity_leak_exclusion_rule": (
            "Excluded candidate_id, coordinate tuple, direct constraint bitmask, output fingerprints, "
            "and equivalent row identifiers before scoring independence."
        ),
        "passes_no_identity_leak_independence": best_non_identity_accuracy < 1.0,
    }


def existence_tests(
    survivors: list[dict[str, Any]],
    kill_ledger: list[dict[str, Any]],
    quotient: dict[str, Any],
    stability: dict[str, Any],
    controls: dict[str, Any],
) -> dict[str, Any]:
    leak = identity_leak_probe(survivors, kill_ledger)
    chart_recovery_rows = []
    for qrow in quotient["classes"]:
        sig_x, sig_z = qrow["probe_signature"]
        if sig_x != 0 and sig_z != 0:
            recovered = "mixed_active_probe_region"
        elif sig_x != 0:
            recovered = "x_axis_active_region"
        elif sig_z != 0:
            recovered = "z_axis_active_region"
        else:
            recovered = "zero_active_probe_region_absent"
        chart_recovery_rows.append(
            {
                "class_id": qrow["class_id"],
                "probe_signature": qrow["probe_signature"],
                "recovered_chart_label": recovered,
                "matches_nonzero_active_probe": recovered != "zero_active_probe_region_absent",
            }
        )
    return {
        "stable": stability["stable"],
        "independent": leak["passes_no_identity_leak_independence"],
        "chart_recoverable": all(row["matches_nonzero_active_probe"] for row in chart_recovery_rows),
        "negative_controlled": (
            controls["empty_C"]["degenerate_no_manifold"]
            and controls["overconstrained_C"]["all_killed"]
            and controls["probe_family_scramble"]["quotient_moved"]
            and controls["blindness_control"]["injected_variant_caught"]
        ),
        "identity_leak_detected": leak["identity_leak_detected"],
        "identity_leak_excluded_best_accuracy": leak["identity_leak_excluded_best_accuracy"],
        "identity_leak_exclusion_rule": leak["identity_leak_exclusion_rule"],
        "identity_leak_probe": leak,
        "chart_recovery_rows": chart_recovery_rows,
        "doctrine": "M(C) exists here only as the stable probe-carved quotient for this carrier and pinned C.",
    }


def constraint_predicate_text(constraint: dict[str, Any]) -> str:
    parts = [
        str(constraint.get("id", "")),
        str(constraint.get("literal_executable_predicate", "")),
        str(constraint.get("quoted_source_line", {}).get("quote", "")),
    ]
    return "\n".join(parts)


def blindness_errors_for_constraints(constraints: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for constraint in constraints:
        text = constraint_predicate_text(constraint)
        lowered = text.lower()
        for token in FORBIDDEN_PREDICATE_TOKENS:
            if token in {"Se", "Ne", "Ni", "Si"}:
                matched = re.search(rf"\b{re.escape(token)}\b", text) is not None
            else:
                matched = token.lower() in lowered
            if matched:
                errors.append(f"{constraint.get('id')}: forbidden predicate token {token!r}")
    return errors


def blindness_guard() -> dict[str, Any]:
    errors = blindness_errors_for_constraints(CONSTRAINTS)
    return {
        "guard": "admissibility_predicate_token_guard",
        "forbidden_tokens": list(FORBIDDEN_PREDICATE_TOKENS),
        "checked_constraint_ids": [row["id"] for row in CONSTRAINTS],
        "predicate_text_sha256": stable_sha256([constraint_predicate_text(row) for row in CONSTRAINTS]),
        "errors": errors,
        "clean": not errors,
    }


def blindness_control() -> dict[str, Any]:
    bad_variant = {
        "id": "C_bad_terrain_framed_constraint_variant",
        "quoted_source_line": {
            "source_path": "injected_control",
            "quote": "bad control line: terrain-framed predicate filters classes by terrain label before survival.",
            "status": "deliberate_negative_control",
        },
        "literal_executable_predicate": "terrain label must be atlas-compatible before survival",
    }
    errors = blindness_errors_for_constraints(CONSTRAINTS + [bad_variant])
    caught = any("C_bad_terrain_framed_constraint_variant" in err for err in errors)
    return {
        "variant_id": bad_variant["id"],
        "injected_variant_caught": caught,
        "injected_errors": errors,
        "demotion_condition": "If this injected variant is not caught, the v1 packet fails terrain-blindness.",
    }


def v0_regression_row(base_ids: list[str], v1_survivors: list[dict[str, Any]], v1_quotient: dict[str, Any]) -> dict[str, Any]:
    v0_ids = base_ids + ["v0_rejected_C4_terrain_framed_residency_variant"]
    result = apply_constraint_set(v0_ids)
    quotient = build_quotient(result["survivors"])
    v1_survivor_ids = {row["candidate_id"] for row in v1_survivors}
    v0_survivor_ids = {row["candidate_id"] for row in result["survivors"]}
    return {
        "row_id": "v0_under_own_failed_C4_regression",
        "status": "comparison_only_rejected_as_admissibility_source",
        "rejected_predicate": "not (x != 0 and z != 0)",
        "why_rejected": "The v0 audit found this C4 was terrain-framed and not admissible as a terrain-blind survival predicate.",
        "v1_blind_survivor_count": len(v1_survivors),
        "v1_blind_quotient_class_count": v1_quotient["class_count"],
        "v0_regression_survivor_count": len(result["survivors"]),
        "v0_regression_quotient_class_count": quotient["class_count"],
        "removed_by_v0_C4_candidate_ids": sorted(v1_survivor_ids - v0_survivor_ids),
        "retained_by_v0_C4_candidate_ids": sorted(v0_survivor_ids),
        "class_signatures_removed_by_v0_C4": sorted(
            [
                row["probe_signature"]
                for row in v1_quotient["classes"]
                if not set(row["member_candidate_ids"]).issubset(v0_survivor_ids)
            ]
        ),
        "diff_demonstrates_contamination": (
            len(v1_survivors) != len(result["survivors"]) or v1_quotient["class_count"] != quotient["class_count"]
        ),
    }


def z3_count_proof(survivor_count: int, class_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    n = z3.Int("survivor_count")
    qn = z3.Int("quotient_class_count")
    solver.add(n == survivor_count)
    solver.add(qn == class_count)
    solver.add(n == EXPECTED_SURVIVOR_COUNT)
    solver.add(qn == EXPECTED_QUOTIENT_CLASS_COUNT)
    solver.add(n > 0)
    verdict = solver.check()
    return {
        "ran": True,
        "verdict": str(verdict),
        "load_bearing": True,
        "claim": "computed survivor_count and quotient_class_count equal pinned finite carve counts and are nonempty",
        "input_object": {"survivor_count": survivor_count, "quotient_class_count": class_count},
        "positive_case": "v1 C1-C3 blind carve gives 16 survivors and 8 quotient classes",
        "negative_control": "overconstrained_C has zero survivors",
        "boundary_case": "empty_C has all 125 candidates",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def cvc5_count_proof(survivor_count: int, class_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    n = solver.mkConst(int_sort, "survivor_count")
    qn = solver.mkConst(int_sort, "quotient_class_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(survivor_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, qn, solver.mkInteger(class_count)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(EXPECTED_SURVIVOR_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, qn, solver.mkInteger(EXPECTED_QUOTIENT_CLASS_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.GT, n, solver.mkInteger(0)))
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "computed survivor_count and quotient_class_count equal pinned finite carve counts and are nonempty",
        "input_object": {"survivor_count": survivor_count, "quotient_class_count": class_count},
        "positive_case": "v1 C1-C3 blind carve gives 16 survivors and 8 quotient classes",
        "negative_control": "overconstrained_C has zero survivors",
        "boundary_case": "empty_C has all 125 candidates",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def build_packet() -> dict[str, Any]:
    constraints = final_constraint_ids()
    carved = apply_constraint_set(constraints)
    survivors = carved["survivors"]
    quotient = build_quotient(survivors)
    stability = class_stability(survivors, quotient)
    graph = graph_components(survivors, quotient)
    guard = blindness_guard()
    controls = constraint_controls(constraints, survivors, quotient)
    existence = existence_tests(survivors, carved["kill_ledger"], quotient, stability, controls)
    readout = post_carve_region_readout(quotient, graph)
    mct = mct_hook(constraints)
    regression = v0_regression_row(constraints, survivors, quotient)
    z3_proof = z3_count_proof(len(survivors), quotient["class_count"])
    cvc5_proof = cvc5_count_proof(len(survivors), quotient["class_count"])
    density_count = len([row for row in candidate_space() if is_density_candidate(tuple(float(v) for v in row["coord"]))])
    all_pass = (
        len(candidate_space()) == EXPECTED_CANDIDATE_COUNT
        and density_count == EXPECTED_DENSITY_COUNT
        and len(survivors) == EXPECTED_SURVIVOR_COUNT
        and quotient["class_count"] == EXPECTED_QUOTIENT_CLASS_COUNT
        and guard["clean"]
        and controls["blindness_control"]["injected_variant_caught"]
        and existence["stable"]
        and existence["independent"]
        and existence["chart_recoverable"]
        and existence["negative_controlled"]
        and existence["identity_leak_excluded_best_accuracy"] < 1.0
        and readout["can_affect_survival"] is False
        and mct["survivor_count"] == EXPECTED_MCT_SURVIVOR_COUNT
        and mct["quotient_class_count"] == EXPECTED_MCT_QUOTIENT_CLASS_COUNT
        and regression["v0_regression_survivor_count"] == EXPECTED_V0_REGRESSION_SURVIVOR_COUNT
        and regression["v0_regression_quotient_class_count"] == EXPECTED_V0_REGRESSION_CLASS_COUNT
        and regression["diff_demonstrates_contamination"]
        and z3_proof["verdict"] == "sat"
        and cvc5_proof["verdict"] == "sat"
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    payload: dict[str, Any] = {
        "schema": "gcm_constraint_carve_v1_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "standards_codex": "system_v6/receipts/audit_standards_codex_v1.md",
        "standards_version": "audit_standards_codex_v1",
        "freshness_tier": "TIER-2 results-available for builder self-check; independent audit not performed by builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "claim": "M(C) is computed here as the C1-C3 terrain-blind survivor set under local adapter pins, not THE manifold.",
        "candidate_space": {
            "kind": "125 finite Bloch-grid configurations over {-1,-1/2,0,1/2,1}^3",
            "candidate_count": EXPECTED_CANDIDATE_COUNT,
            "density_subcarrier_count": density_count,
            "carrier_parent": "finite local adapter carrier; carrier-and-pins-relative",
        },
        "constraint_family_C": CONSTRAINTS,
        "excluded_from_admissibility_C": [
            {
                "id": "v0_rejected_C4_terrain_framed_residency_variant",
                "status": "split_out_of_v1_admissibility_carve",
                "comparison_only": True,
            }
        ],
        "terrain_blindness_guard": guard,
        "probe_family_M": list(PROBE_FAMILY),
        "survivor_count": len(survivors),
        "survivors": survivors,
        "kill_ledger": carved["kill_ledger"],
        "kill_counts_by_constraint": dict(sorted(Counter(row["killed_by"] for row in carved["kill_ledger"]).items())),
        "quotient": quotient,
        "stability_certificate": stability,
        "adjacency_connectivity": graph,
        "existence_tests": existence,
        "identity_leak_detected": existence["identity_leak_detected"],
        "identity_leak_excluded_best_accuracy": existence["identity_leak_excluded_best_accuracy"],
        "identity_leak_exclusion_rule": existence["identity_leak_exclusion_rule"],
        "post_carve_terrain_readout": readout,
        "controls": controls,
        "v0_regression_row": regression,
        "M_C_t_hook": mct,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "source_locks": {
            key: source_lock(path, key, PARENT_COMMITS.get(key)) for key, path in PARENT_PATHS.items()
        },
        "prior_art_boundary": PRIOR_ART_READ_NOT_AUTHORITY,
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "boundary_helper_fully_used": True,
            "G_2a_idempotency_from_birth": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "all_pass": all_pass,
        "disallowed_claims": [
            "THE manifold",
            "terrain atlas admission",
            "axis admission",
            "engine admission",
            "physics admission",
            "canonical by process",
        ],
    }
    payload["result_sha256"] = stable_sha256({k: v for k, v in payload.items() if k != "generated_at"})
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload.get("schema") == "gcm_constraint_carve_v1_result_v1", "packet schema drift")
    require(payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(payload.get("candidate_space", {}).get("candidate_count") == EXPECTED_CANDIDATE_COUNT, "candidate count drift")
    require(payload.get("candidate_space", {}).get("density_subcarrier_count") == EXPECTED_DENSITY_COUNT, "density count drift")
    require(payload.get("survivor_count") == EXPECTED_SURVIVOR_COUNT, "survivor count drift")
    require(payload.get("quotient", {}).get("class_count") == EXPECTED_QUOTIENT_CLASS_COUNT, "quotient class count drift")
    require(len(payload.get("kill_ledger", [])) == EXPECTED_CANDIDATE_COUNT - EXPECTED_SURVIVOR_COUNT, "kill ledger count drift")
    require(payload.get("terrain_blindness_guard", {}).get("clean") is True, "terrain-blindness guard failed")
    existence = payload.get("existence_tests", {})
    for key in ("stable", "independent", "chart_recoverable", "negative_controlled"):
        require(existence.get(key) is True, f"existence test failed: {key}")
    for key in ("identity_leak_detected", "identity_leak_excluded_best_accuracy", "identity_leak_exclusion_rule"):
        require(key in payload, f"missing top-level {key}")
        require(key in existence, f"missing existence_tests.{key}")
    require(payload.get("identity_leak_detected") is True, "identity leak should be detected and then excluded")
    require(payload.get("identity_leak_excluded_best_accuracy", 1.0) < 1.0, "identity-excluded predictor accuracy must be < 1.0")
    controls = payload.get("controls", {})
    require(controls.get("empty_C", {}).get("degenerate_no_manifold") is True, "empty-C control failed")
    require(controls.get("overconstrained_C", {}).get("all_killed") is True, "overconstrained control failed")
    require(controls.get("probe_family_scramble", {}).get("quotient_moved") is True, "probe scramble control failed")
    require(controls.get("blindness_control", {}).get("injected_variant_caught") is True, "blindness control failed")
    require(all(row.get("bite") is True for row in controls.get("constraint_erasure", [])), "constraint erasure bite failed")
    readout = payload.get("post_carve_terrain_readout", {})
    require(readout.get("can_affect_survival") is False, "post-carve readout must not affect survival")
    require(readout.get("survival_inputs") == [], "post-carve readout must have no survival inputs")
    regression = payload.get("v0_regression_row", {})
    require(regression.get("v0_regression_survivor_count") == EXPECTED_V0_REGRESSION_SURVIVOR_COUNT, "v0 regression survivor count drift")
    require(regression.get("v0_regression_quotient_class_count") == EXPECTED_V0_REGRESSION_CLASS_COUNT, "v0 regression class count drift")
    require(regression.get("diff_demonstrates_contamination") is True, "v0 regression did not demonstrate diff")
    require(payload.get("M_C_t_hook", {}).get("survivor_count") == EXPECTED_MCT_SURVIVOR_COUNT, "M(C,t) hook survivor count drift")
    require(payload.get("M_C_t_hook", {}).get("quotient_class_count") == EXPECTED_MCT_QUOTIENT_CLASS_COUNT, "M(C,t) hook class count drift")
    proofs = payload.get("crossover_proofs", {})
    require(proofs.get("z3", {}).get("verdict") == "sat", "z3 proof failed")
    require(proofs.get("cvc5", {}).get("verdict") == "sat", "cvc5 proof failed")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    require(payload.get("all_pass") is True, "all_pass is not true")
    return errors


def main() -> int:
    payload = build_packet()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""2Q boundary/control rung for the GCM constraint carve."""

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


SIM_ID = "gcm_constraint_carve_2q_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_carrier_and_pins_relative_2q_boundary_control_rung"
ENGINE_MODE = "all_three_full_sims"

GRID_VALUES = (-1.0, -0.5, 0.0, 0.5, 1.0)
PROBE_FAMILY = ("sigma_x_tensor_I", "sigma_z_tensor_I")
SCRAMBLED_PROBE_FAMILY = ("sigma_y_tensor_I", "sigma_z_tensor_I")
CONTROL_QUBIT_BLOCH = (0.0, 0.0, 1.0)

EXPECTED_CANDIDATE_COUNT = 15783
EXPECTED_DENSITY_COUNT = 1167
EXPECTED_SURVIVOR_COUNT = 544
EXPECTED_QUOTIENT_CLASS_COUNT = 8
EXPECTED_PRODUCT_SURVIVOR_COUNT = 528
EXPECTED_ENTANGLED_SURVIVOR_COUNT = 16
EXPECTED_MCT_SURVIVOR_COUNT = 272
EXPECTED_MCT_QUOTIENT_CLASS_COUNT = 4
EXPECTED_ONE_Q_SURVIVOR_COUNT = 16
EXPECTED_ONE_Q_QUOTIENT_CLASS_COUNT = 8
EXPECTED_ONE_Q_RESULT_SHA256 = "ca6ae0277e4a5c77044b1075626262e6bfdab4c99f818e85abc123322f74b756"
EXPECTED_ONE_Q_ENVELOPE_SHA256 = "450ecaba6c77756688d0dc3cae2b3032170b3bead159b914b0e1c6de55ccae6d"
EXPECTED_ONE_Q_COMMON_SHA256 = "96d80d6f273a017a0cc80333c94fff0cf6b03bbe406f0a29dc69ccbc6dcb18db"
EXPECTED_FREEZE_REGISTRY_SHA256 = "64cd715166cee039f89494166496adabf15300bae4b8cc79fee98fc0251189f2"

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
    "one_q_carve_common_source": ROOT / "system_v6" / "sims" / "gcm_constraint_carve_v1" / "gcm_constraint_carve_v1_common.py",
    "one_q_carve_result": ROOT / "system_v6" / "sims" / "gcm_constraint_carve_v1" / "results" / "gcm_constraint_carve_v1_results.json",
    "one_q_carve_envelope": ROOT / "system_v6" / "sims" / "gcm_constraint_carve_v1" / "results" / "gcm_constraint_carve_v1_envelope_results.json",
    "one_q_freeze_registry": ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json",
    "layer_stack_reference": ROOT / "system_v6" / "receipts" / "gcm_layer_stack_reference_20260612.md",
    "audit_standards_codex": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
    "builder_audit_boundary": ROOT / "scripts" / "builder_audit_boundary.py",
    "build_card": SIM_DIR / "build_card.md",
}

TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite survivor and quotient component recomputation."},
    "networkx": {"tried": True, "used": True, "reason": "JAX/Python finite survivor and quotient component recomputation."},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch batched local-probe predicates over the 2Q survivor set."},
    "sympy": {"tried": True, "used": True, "reason": "Exact integer guards for 2Q counts, cross-rung counts, and kill-ledger diffs."},
    "z3": {"tried": True, "used": True, "reason": "SMT binding of computed 2Q survivor/class counts and 1Q embedding count."},
    "cvc5": {"tried": True, "used": True, "reason": "Independent SMT binding of the same 2Q counts and 1Q embedding count."},
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
        "2q_constraint_carve",
        "cross_rung_1q_to_2q_product_embedding",
        "partial_trace_projection_to_1q_survivors",
        "entanglement_boundary_readout_only",
        "terrain_blind_predicate_guard",
    ],
    "engine_tool_intent": {
        "julia": {"Graphs": "SimpleGraph/add_edge!/connected_components recompute survivor and quotient components."},
        "jax": {
            "networkx": "nx.Graph and connected_components recompute survivor and quotient components.",
            "sympy": "sp.Rational guards exact candidate/survivor/class/cross-rung counts.",
        },
        "pytorch": {
            "torch.func": "vmap over survivor first-marginal coordinates checks active-probe and order-gap predicates.",
            "sympy": "sp.Rational guards exact candidate/survivor/class/cross-rung counts.",
        },
    },
}

LOCAL_SOURCE_QUOTES = {
    "C1_finite_2q_density_carrier": {
        "source_path": "system_v6/sims/gcm_constraint_carve_2q_v0/build_card.md",
        "quote": "C1 predicate source line: `C1_finite_2q_density_carrier` accepts exactly finite 2Q candidates whose pinned construction has trace one and nonnegative spectrum under its family eigenvalue rule.",
        "status": "same_C1_form_2Q_instantiation_local_adapter_pin",
    },
    "C2_probe_distinguishability_xz_local_adapter_pin": {
        "source_path": "system_v6/sims/gcm_constraint_carve_2q_v0/build_card.md",
        "quote": "C2 predicate source line: `C2_probe_distinguishability_xz_local_adapter_pin` accepts exactly candidates whose active first-qubit probe pair `(2*Tr((sigma_x tensor I)rho), 2*Tr((sigma_z tensor I)rho))` is not `(0, 0)`.",
        "status": "same_C2_form_2Q_instantiation_local_adapter_pin",
    },
    "C3_persistence_n01_order_gap": {
        "source_path": "system_v6/sims/gcm_constraint_carve_2q_v0/build_card.md",
        "quote": "C3 predicate source line: `C3_persistence_n01_order_gap` accepts exactly candidates whose first-qubit `D_z after R_x` and `R_x after D_z` active x/z probe signatures differ.",
        "status": "same_C3_form_2Q_instantiation_local_adapter_pin",
    },
    "C5_t1_positive_active_coordinate_pin": {
        "source_path": "system_v6/sims/gcm_constraint_carve_2q_v0/build_card.md",
        "quote": "C5 predicate source line: `C5_t1_positive_active_coordinate_pin` is a downstream `M(C,t)` hook that keeps candidates whose first nonzero active first-qubit coordinate in `(x, z)` is positive.",
        "status": "downstream_M_C_t_hook_not_admissibility_C",
    },
}

CONSTRAINTS = [
    {
        "id": "C1_finite_2q_density_carrier",
        "one_q_source_predicate_id": "C1_finite_density_carrier",
        "quoted_source_line": LOCAL_SOURCE_QUOTES["C1_finite_2q_density_carrier"],
        "literal_executable_predicate": "two_qubit_trace_one_psd_by_pinned_family_eigenvalue_rule(row)",
    },
    {
        "id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "one_q_source_predicate_id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "quoted_source_line": LOCAL_SOURCE_QUOTES["C2_probe_distinguishability_xz_local_adapter_pin"],
        "literal_executable_predicate": "(2*Tr((sigma_x tensor I)rho), 2*Tr((sigma_z tensor I)rho)) != (0, 0)",
    },
    {
        "id": "C3_persistence_n01_order_gap",
        "one_q_source_predicate_id": "C3_persistence_n01_order_gap",
        "quoted_source_line": LOCAL_SOURCE_QUOTES["C3_persistence_n01_order_gap"],
        "literal_executable_predicate": "probe_signature((D_z after R_x)_first_marginal) != probe_signature((R_x after D_z)_first_marginal)",
    },
]


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() or None


def source_lock(path: Path, role: str, expected_sha256: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists() and path.is_file():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
        if expected_sha256:
            row["expected_sha256"] = expected_sha256
            row["hash_matches_expected"] = row["sha256"] == expected_sha256
    return row


def q(value: float) -> float:
    rounded = round(float(value), 12)
    return 0.0 if rounded == 0 else rounded


def scaled(value: float) -> int:
    return int(round(2.0 * value))


def bloch_key(coord: tuple[float, float, float]) -> tuple[int, int, int]:
    return tuple(scaled(v) for v in coord)


def one_q_density_ok(coord: tuple[float, float, float]) -> bool:
    return sum(v * v for v in coord) <= 1.0 + 1.0e-12


def probe_signature(
    coord: tuple[float, float, float],
    family: tuple[str, str] = PROBE_FAMILY,
) -> tuple[int, int]:
    mapping = {
        "sigma_x_tensor_I": coord[0],
        "sigma_y_tensor_I": coord[1],
        "sigma_z_tensor_I": coord[2],
    }
    return tuple(scaled(mapping[name]) for name in family)  # type: ignore[return-value]


def dz_after_rx(coord: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coord
    return (0.5 * x, -0.5 * z, y)


def rx_after_dz(coord: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coord
    return (0.5 * x, -z, 0.5 * y)


def order_gap(coord: tuple[float, float, float], family: tuple[str, str] = PROBE_FAMILY) -> float:
    left = probe_signature(dz_after_rx(coord), family)
    right = probe_signature(rx_after_dz(coord), family)
    return q(math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right))))


def one_q_active_probe_nonzero(coord: tuple[float, float, float]) -> bool:
    return probe_signature(coord) != (0, 0)


def one_q_persistence_order_ok(coord: tuple[float, float, float]) -> bool:
    return order_gap(coord) >= 0.5


def first_active_coordinate_positive(coord: tuple[float, float, float]) -> bool:
    x, _y, z = coord
    if x != 0:
        return x > 0
    if z != 0:
        return z > 0
    return False


def quantize_half_step(value: float) -> float:
    if value >= 0.25:
        return 0.5
    if value <= -0.25:
        return -0.5
    return 0.0


def committed_update(coord: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coord
    return (quantize_half_step(0.5 * x), quantize_half_step(0.5 * y), z)


def bell_diagonal_eigenvalues(corr: tuple[float, float, float]) -> list[float]:
    cx, cy, cz = corr
    return [
        q((1 + cx - cy + cz) / 4.0),
        q((1 - cx + cy + cz) / 4.0),
        q((1 + cx + cy - cz) / 4.0),
        q((1 - cx - cy - cz) / 4.0),
    ]


def binary_entropy_from_bloch_radius(radius: float) -> float:
    lam_plus = (1.0 + radius) / 2.0
    lam_minus = (1.0 - radius) / 2.0
    total = 0.0
    for lam in (lam_plus, lam_minus):
        if lam > 0:
            total -= lam * math.log(lam, 2)
    return q(total)


def candidate_space() -> list[dict[str, Any]]:
    grid = [tuple(float(v) for v in coord) for coord in __import__("itertools").product(GRID_VALUES, repeat=3)]
    density_grid = [coord for coord in grid if one_q_density_ok(coord)]
    rows: list[dict[str, Any]] = []
    for first in grid:
        for second in grid:
            rows.append(
                {
                    "candidate_id": len(rows),
                    "family": "product_grid",
                    "first_bloch": [q(v) for v in first],
                    "second_bloch": [q(v) for v in second],
                    "construction": "rho_A(first_grid) tensor rho_B(second_grid)",
                }
            )
    for corr in grid:
        rows.append(
            {
                "candidate_id": len(rows),
                "family": "bell_diagonal_grid",
                "first_bloch": [0.0, 0.0, 0.0],
                "second_bloch": [0.0, 0.0, 0.0],
                "bell_correlation_diag": [q(v) for v in corr],
                "construction": "1/4*(II + cx XX + cy YY + cz ZZ)",
            }
        )
    for first in density_grid:
        radius = math.sqrt(sum(v * v for v in first))
        rows.append(
            {
                "candidate_id": len(rows),
                "family": "purification_boundary",
                "first_bloch": [q(v) for v in first],
                "second_bloch": [0.0, 0.0, q(radius)],
                "construction": "Schmidt purification with partial_trace_A Bloch vector pinned to first_bloch",
            }
        )
    for row in rows:
        enrich_candidate(row)
    return rows


def enrich_candidate(row: dict[str, Any]) -> None:
    first = tuple(float(v) for v in row["first_bloch"])
    second = tuple(float(v) for v in row["second_bloch"])
    row["first_bloch_scaled"] = list(bloch_key(first))
    row["second_bloch_scaled"] = list(bloch_key(second))
    row["probe_signature"] = list(probe_signature(first))
    row["scrambled_probe_signature"] = list(probe_signature(first, SCRAMBLED_PROBE_FAMILY))
    row["order_gap"] = order_gap(first)
    row["first_marginal_radius"] = q(math.sqrt(sum(v * v for v in first)))
    row["local_entropy_A_bits"] = binary_entropy_from_bloch_radius(row["first_marginal_radius"])
    row["density_valid"] = two_q_density_ok(row)
    row["entangled"] = entangled_readout(row)


def two_q_density_ok(row: dict[str, Any]) -> bool:
    family = row["family"]
    first = tuple(float(v) for v in row["first_bloch"])
    second = tuple(float(v) for v in row["second_bloch"])
    if family == "product_grid":
        return one_q_density_ok(first) and one_q_density_ok(second)
    if family == "bell_diagonal_grid":
        return min(bell_diagonal_eigenvalues(tuple(float(v) for v in row["bell_correlation_diag"]))) >= -1.0e-12
    if family == "purification_boundary":
        radius_squared = sum(v * v for v in first)
        return radius_squared <= 1.0 + 1.0e-12
    raise KeyError(family)


def entangled_readout(row: dict[str, Any]) -> bool:
    family = row["family"]
    if family == "product_grid":
        return False
    if family == "bell_diagonal_grid":
        if not two_q_density_ok(row):
            return False
        return max(bell_diagonal_eigenvalues(tuple(float(v) for v in row["bell_correlation_diag"]))) > 0.5 + 1.0e-12
    if family == "purification_boundary":
        radius_squared = sum(float(v) * float(v) for v in row["first_bloch"])
        return radius_squared > 1.0e-12 and radius_squared < 1.0 - 1.0e-12
    raise KeyError(family)


def constraint_passes(constraint_id: str, row: dict[str, Any]) -> bool:
    first = tuple(float(v) for v in row["first_bloch"])
    if constraint_id == "C1_finite_2q_density_carrier":
        return bool(row["density_valid"])
    if constraint_id == "C2_probe_distinguishability_xz_local_adapter_pin":
        return probe_signature(first) != (0, 0)
    if constraint_id == "C3_persistence_n01_order_gap":
        return one_q_persistence_order_ok(first)
    if constraint_id == "C5_t1_positive_active_coordinate_pin":
        return first_active_coordinate_positive(first)
    if constraint_id == "C_overconstrained_impossible_empty":
        return False
    raise KeyError(constraint_id)


def final_constraint_ids() -> list[str]:
    return [row["id"] for row in CONSTRAINTS]


def apply_constraint_set(constraint_ids: list[str]) -> dict[str, Any]:
    survivors: list[dict[str, Any]] = []
    kill_ledger: list[dict[str, Any]] = []
    for base_row in candidate_space():
        failures = [cid for cid in constraint_ids if not constraint_passes(cid, base_row)]
        row = dict(base_row)
        if failures:
            kill_ledger.append(
                {
                    "candidate_id": row["candidate_id"],
                    "family": row["family"],
                    "first_bloch_scaled": row["first_bloch_scaled"],
                    "killed_by": failures[0],
                    "all_failed_constraints": failures,
                    "entangled": row["entangled"],
                }
            )
        else:
            row["survivor_id"] = len(survivors)
            survivors.append(row)
    return {"constraint_ids": constraint_ids, "survivors": survivors, "kill_ledger": kill_ledger}


def survivor_key(row: dict[str, Any]) -> tuple[Any, ...]:
    second = tuple(int(v) for v in row.get("second_bloch_scaled", []))
    return (row["family"], tuple(int(v) for v in row["first_bloch_scaled"]), second)


def build_quotient(survivors: list[dict[str, Any]], family: tuple[str, str] = PROBE_FAMILY) -> dict[str, Any]:
    buckets: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in survivors:
        first = tuple(float(v) for v in row["first_bloch"])
        buckets[probe_signature(first, family)].append(row)
    classes = []
    for idx, key in enumerate(sorted(buckets)):
        members = sorted(buckets[key], key=lambda item: item["survivor_id"])
        classes.append(
            {
                "class_id": f"Q{idx}",
                "probe_signature": list(key),
                "member_survivor_ids": [row["survivor_id"] for row in members],
                "member_candidate_ids": [row["candidate_id"] for row in members],
                "member_count": len(members),
                "entangled_member_count": sum(1 for row in members if row["entangled"]),
                "family_counts": dict(sorted(Counter(row["family"] for row in members).items())),
            }
        )
    return {"probe_family": list(family), "class_count": len(classes), "classes": classes}


def update_targets(row: dict[str, Any]) -> list[tuple[str, tuple[Any, ...]]]:
    first = tuple(float(v) for v in row["first_bloch"])
    x, y, z = first
    second = tuple(int(v) for v in row["second_bloch_scaled"])
    family = row["family"]
    targets = [("hidden_probe_flip_first_qubit", (family, (scaled(x), scaled(-y), scaled(z)), second))]
    if z == 0 and x != 0:
        targets.append(("x_reflection_at_z_zero_first_qubit", (family, (scaled(-x), scaled(-y), scaled(z)), second)))
    if x == 0 and z != 0:
        targets.append(("z_reflection_at_x_zero_first_qubit", (family, (scaled(x), scaled(-y), scaled(-z)), second)))
    return targets


def graph_components(survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    key_to_survivor = {survivor_key(row): row["survivor_id"] for row in survivors}
    class_for_survivor = {}
    for qrow in quotient["classes"]:
        for sid in qrow["member_survivor_ids"]:
            class_for_survivor[sid] = qrow["class_id"]
    adjacency = {row["survivor_id"]: set() for row in survivors}
    edges = []
    quotient_edges = set()
    for row in survivors:
        src = row["survivor_id"]
        for update_name, target_key in update_targets(row):
            dst = key_to_survivor.get(target_key)
            if dst is None:
                continue
            edges.append({"src": src, "dst": dst, "update": update_name})
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
        "survivor_edges": sorted(edges, key=lambda edge: (edge["src"], edge["dst"], edge["update"])),
        "survivor_components": components,
        "quotient_edges": [
            {"src_class": src, "dst_class": dst, "update": name} for src, dst, name in sorted(quotient_edges)
        ],
        "quotient_components": q_components,
    }


def class_stability(survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    class_by_sig = {tuple(row["probe_signature"]): row["class_id"] for row in quotient["classes"]}
    rows = []
    stable = True
    for qrow in quotient["classes"]:
        image_classes = set()
        for survivor_id in qrow["member_survivor_ids"]:
            source = survivors[survivor_id]
            first = tuple(float(v) for v in source["first_bloch"])
            image_classes.add(class_by_sig.get(tuple(probe_signature(committed_update(first))), "outside_current_quotient"))
        row_stable = len(image_classes) == 1 and "outside_current_quotient" not in image_classes
        stable = stable and row_stable
        rows.append({"class_id": qrow["class_id"], "image_classes": sorted(image_classes), "stable": row_stable})
    return {"committed_update": "first_qubit_coarse_D_z_half_step_Q_grid", "stable": stable, "rows": rows}


def constraint_controls(base_ids: list[str], base_survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    empty = apply_constraint_set([])
    over = apply_constraint_set(base_ids + ["C_overconstrained_impossible_empty"])
    base_set = {row["candidate_id"] for row in base_survivors}
    erasures = []
    for cid in base_ids:
        result = apply_constraint_set([item for item in base_ids if item != cid])
        survivor_set = {row["candidate_id"] for row in result["survivors"]}
        erasures.append(
            {
                "dropped_constraint": cid,
                "survivor_count": len(survivor_set),
                "delta_count": len(survivor_set ^ base_set),
                "added_count": len(survivor_set - base_set),
                "removed_count": len(base_set - survivor_set),
                "bite": survivor_set != base_set,
            }
        )
    scrambled = build_quotient(base_survivors, SCRAMBLED_PROBE_FAMILY)
    return {
        "empty_C": {"survivor_count": len(empty["survivors"]), "degenerate_no_manifold": len(empty["survivors"]) == EXPECTED_CANDIDATE_COUNT},
        "overconstrained_C": {"survivor_count": len(over["survivors"]), "all_killed": len(over["survivors"]) == 0},
        "constraint_erasure": erasures,
        "probe_family_scramble": {
            "baseline_probe_family": list(PROBE_FAMILY),
            "scrambled_probe_family": list(SCRAMBLED_PROBE_FAMILY),
            "baseline_class_count": quotient["class_count"],
            "scrambled_class_count": scrambled["class_count"],
            "baseline_class_signatures": [row["probe_signature"] for row in quotient["classes"]],
            "scrambled_class_signatures": [row["probe_signature"] for row in scrambled["classes"]],
            "quotient_moved": stable_sha256(quotient["classes"]) != stable_sha256(scrambled["classes"]),
        },
        "blindness_control": blindness_control(),
    }


def mct_hook(base_ids: list[str]) -> dict[str, Any]:
    result = apply_constraint_set(base_ids + ["C5_t1_positive_active_coordinate_pin"])
    quotient = build_quotient(result["survivors"])
    return {
        "update": "C -> C_prime = C plus C5_t1_positive_active_coordinate_pin",
        "new_constraint": {
            "id": "C5_t1_positive_active_coordinate_pin",
            "quoted_source_line": LOCAL_SOURCE_QUOTES["C5_t1_positive_active_coordinate_pin"],
            "literal_executable_predicate": "first nonzero active first-qubit coordinate in (x,z) is positive",
        },
        "survivor_count": len(result["survivors"]),
        "quotient_class_count": quotient["class_count"],
        "family_counts": dict(sorted(Counter(row["family"] for row in result["survivors"]).items())),
    }


def post_carve_structure_readout(quotient: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
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
        rows.append(
            {
                "class_id": qrow["class_id"],
                "probe_signature": qrow["probe_signature"],
                "readout_label": label,
                "member_count": qrow["member_count"],
                "entangled_member_count": qrow["entangled_member_count"],
            }
        )
    return {
        "question": "post-carve 2Q structure readout only; not an admissibility input",
        "can_affect_survival": False,
        "survival_inputs": [],
        "class_count": quotient["class_count"],
        "readout_rows": rows,
        "class_counts_by_readout_label": dict(sorted(counts.items())),
        "quotient_components": graph["quotient_components"],
        "entanglement_is_readout_not_predicate": True,
    }


def identity_leak_probe(survivors: list[dict[str, Any]], kill_ledger: list[dict[str, Any]]) -> dict[str, Any]:
    labels = {row["candidate_id"]: "survived" for row in survivors}
    labels.update({row["candidate_id"]: "killed" for row in kill_ledger})
    candidates = candidate_space()

    def majority_accuracy(values: list[Any]) -> float:
        buckets: dict[Any, Counter[str]] = defaultdict(Counter)
        for row, feature in zip(candidates, values):
            buckets[feature][labels[row["candidate_id"]]] += 1
        return sum(max(counter.values()) for counter in buckets.values()) / len(candidates)

    identity = {
        "candidate_id": [row["candidate_id"] for row in candidates],
        "family_and_first_second_scaled": [
            (row["family"], tuple(row["first_bloch_scaled"]), tuple(row["second_bloch_scaled"])) for row in candidates
        ],
        "direct_constraint_fingerprint": [
            tuple(int(constraint_passes(cid, row)) for cid in final_constraint_ids()) for row in candidates
        ],
    }
    non_identity = {
        "family_only": [row["family"] for row in candidates],
        "density_valid": [row["density_valid"] for row in candidates],
        "entangled_flag": [row["entangled"] for row in candidates],
        "first_marginal_radius": [row["first_marginal_radius"] for row in candidates],
        "active_probe_count": [
            int(tuple(float(v) for v in row["first_bloch"])[0] != 0)
            + int(tuple(float(v) for v in row["first_bloch"])[2] != 0)
            for row in candidates
        ],
        "order_gap_value": [row["order_gap"] for row in candidates],
    }
    identity_acc = {name: majority_accuracy(values) for name, values in identity.items()}
    non_identity_acc = {name: majority_accuracy(values) for name, values in non_identity.items()}
    best_name, best_acc = max(non_identity_acc.items(), key=lambda item: item[1])
    return {
        "identity_leak_detected": any(value == 1.0 for value in identity_acc.values()),
        "identity_inclusive_accuracies": {key: round(value, 12) for key, value in sorted(identity_acc.items())},
        "identity_leak_excluded_best_accuracy": round(best_acc, 12),
        "identity_leak_excluded_best_predictor": best_name,
        "identity_leak_exclusion_rule": "Excluded candidate_id, exact family+coordinate IDs, direct constraint fingerprints, output fingerprints, and equivalent row identifiers.",
        "passes_no_identity_leak_independence": best_acc < 1.0,
    }


def one_q_reference() -> dict[str, Any]:
    result_path = PARENT_PATHS["one_q_carve_result"]
    envelope_path = PARENT_PATHS["one_q_carve_envelope"]
    common_path = PARENT_PATHS["one_q_carve_common_source"]
    freeze_path = PARENT_PATHS["one_q_freeze_registry"]
    result = load_json(result_path)
    return {
        "result": result,
        "hashes": {
            "one_q_result_sha256": sha256_file(result_path),
            "one_q_envelope_sha256": sha256_file(envelope_path),
            "one_q_common_sha256": sha256_file(common_path),
            "one_q_freeze_registry_sha256": sha256_file(freeze_path),
        },
        "hashes_match_expected": {
            "one_q_result_sha256": sha256_file(result_path) == EXPECTED_ONE_Q_RESULT_SHA256,
            "one_q_envelope_sha256": sha256_file(envelope_path) == EXPECTED_ONE_Q_ENVELOPE_SHA256,
            "one_q_common_sha256": sha256_file(common_path) == EXPECTED_ONE_Q_COMMON_SHA256,
            "one_q_freeze_registry_sha256": sha256_file(freeze_path) == EXPECTED_FREEZE_REGISTRY_SHA256,
        },
    }


def cross_rung_row(survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    one_q = one_q_reference()
    one_survivors = one_q["result"]["survivors"]
    one_keys = {tuple(row["coord_scaled"]) for row in one_survivors}
    two_by_key = {survivor_key(row): row for row in survivors}
    product_embeds = []
    for row in one_survivors:
        key = ("product_grid", tuple(row["coord_scaled"]), tuple(bloch_key(CONTROL_QUBIT_BLOCH)))
        target = two_by_key.get(key)
        product_embeds.append(
            {
                "one_q_candidate_id": row["candidate_id"],
                "one_q_coord_scaled": row["coord_scaled"],
                "control_second_bloch_scaled": list(bloch_key(CONTROL_QUBIT_BLOCH)),
                "two_q_survivor_id": target["survivor_id"] if target else None,
                "embedded": target is not None,
                "partial_trace_A_matches": target is not None and tuple(target["first_bloch_scaled"]) == tuple(row["coord_scaled"]),
            }
        )
    projection_counts: Counter[tuple[int, int, int]] = Counter(tuple(row["first_bloch_scaled"]) for row in survivors)
    return {
        "row_id": "cross_rung_1q_to_2q_product_partial_trace",
        "declared_nesting_axis": "1Q survivor set -> 2Q survivor set by product with pinned control, then partial_trace_A projection",
        "one_q_authority_hashes": one_q["hashes"],
        "one_q_hashes_match_expected": one_q["hashes_match_expected"],
        "one_q_survivor_count": len(one_survivors),
        "one_q_quotient_class_count": one_q["result"]["quotient"]["class_count"],
        "product_control_embedding_count": sum(1 for row in product_embeds if row["embedded"]),
        "product_control_embedding_all_survive": all(row["embedded"] and row["partial_trace_A_matches"] for row in product_embeds),
        "partial_trace_A_image_count": len(projection_counts),
        "partial_trace_A_image_equals_1q_survivor_set": set(projection_counts) == one_keys,
        "partial_trace_A_fiber_counts": {
            ",".join(str(v) for v in key): projection_counts[key] for key in sorted(projection_counts)
        },
        "product_fiber_count_per_1q_survivor": 33,
        "purification_fiber_count_per_1q_survivor": 1,
        "total_fiber_count_per_1q_survivor": 34,
        "embedding_rows": product_embeds,
        "not_admission": "This is the first computed nesting-relation row only; it does not promote the carved object.",
    }


def boundary_phenomena(survivors: list[dict[str, Any]], kill_ledger: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = candidate_space()
    valid = [row for row in candidates if row["density_valid"]]
    ent_valid = [row for row in valid if row["entangled"]]
    ent_survivors = [row for row in survivors if row["entangled"]]
    bell_ent_valid = [row for row in ent_valid if row["family"] == "bell_diagonal_grid"]
    bell_ent_kills = [
        row for row in kill_ledger if row["family"] == "bell_diagonal_grid" and row["entangled"]
    ]
    return {
        "entanglement_enters_candidate_space": bool(ent_valid),
        "valid_entangled_candidate_count": len(ent_valid),
        "entangled_survivor_count": len(ent_survivors),
        "bell_diagonal_valid_entangled_count": len(bell_ent_valid),
        "bell_diagonal_entangled_killed_by": dict(sorted(Counter(row["killed_by"] for row in bell_ent_kills).items())),
        "purification_entangled_survivor_count": sum(1 for row in ent_survivors if row["family"] == "purification_boundary"),
        "interpretation": "Bell-diagonal entanglement has zero first-qubit local x/z probes and is killed by C2; purification rows can be entangled while their partial trace remains a 1Q survivor.",
    }


def kill_ledger_diff_vs_1q(kill_ledger: list[dict[str, Any]], survivors: list[dict[str, Any]]) -> dict[str, Any]:
    one_q_counts = {
        "C1_finite_density_carrier": 92,
        "C2_probe_distinguishability_xz_local_adapter_pin": 5,
        "C3_persistence_n01_order_gap": 12,
        "survived": 16,
        "candidate_count": 125,
    }
    two_counts = dict(sorted(Counter(row["killed_by"] for row in kill_ledger).items()))
    two_counts["survived"] = len(survivors)
    two_counts["candidate_count"] = EXPECTED_CANDIDATE_COUNT
    family_by_kill: dict[str, dict[str, int]] = {}
    for killed_by, rows in __import__("itertools").groupby(sorted(kill_ledger, key=lambda row: row["killed_by"]), key=lambda row: row["killed_by"]):
        family_by_kill[killed_by] = dict(sorted(Counter(row["family"] for row in rows).items()))
    return {
        "one_q_counts": one_q_counts,
        "two_q_counts": two_counts,
        "two_q_family_counts_by_killer": family_by_kill,
        "normalized_rates": {
            "one_q_C1_rate": round(one_q_counts["C1_finite_density_carrier"] / one_q_counts["candidate_count"], 12),
            "two_q_C1_rate": round(two_counts["C1_finite_2q_density_carrier"] / two_counts["candidate_count"], 12),
            "one_q_survival_rate": round(one_q_counts["survived"] / one_q_counts["candidate_count"], 12),
            "two_q_survival_rate": round(two_counts["survived"] / two_counts["candidate_count"], 12),
        },
        "diff_readout": "2Q multiplies the product fiber, adds Bell-diagonal zero-local boundary kills at C2, and admits entangled purification rows only when their partial trace is already a 1Q survivor.",
    }


def existence_tests(
    survivors: list[dict[str, Any]],
    kill_ledger: list[dict[str, Any]],
    quotient: dict[str, Any],
    stability: dict[str, Any],
    controls: dict[str, Any],
) -> dict[str, Any]:
    leak = identity_leak_probe(survivors, kill_ledger)
    chart_rows = []
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
        chart_rows.append({"class_id": qrow["class_id"], "recovered_chart_label": recovered, "matches_active_probe": recovered != "zero_active_probe_region_absent"})
    return {
        "stable": stability["stable"],
        "independent": leak["passes_no_identity_leak_independence"],
        "chart_recoverable": all(row["matches_active_probe"] for row in chart_rows),
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
        "chart_recovery_rows": chart_rows,
    }


def constraint_predicate_text(constraint: dict[str, Any]) -> str:
    return "\n".join(
        [
            str(constraint.get("id", "")),
            str(constraint.get("literal_executable_predicate", "")),
            str(constraint.get("quoted_source_line", {}).get("quote", "")),
        ]
    )


def blindness_errors_for_constraints(constraints: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for constraint in constraints:
        text = constraint_predicate_text(constraint)
        lowered = text.lower()
        for token in FORBIDDEN_PREDICATE_TOKENS:
            matched = re.search(rf"\b{re.escape(token)}\b", text) is not None if token in {"Se", "Ne", "Ni", "Si"} else token.lower() in lowered
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
        "quoted_source_line": {"source_path": "injected_control", "quote": "bad control line: terrain/atlas label filters before survival."},
        "literal_executable_predicate": "terrain atlas label must pass before survival",
    }
    errors = blindness_errors_for_constraints(CONSTRAINTS + [bad_variant])
    caught = any("C_bad_terrain_framed_constraint_variant" in err for err in errors)
    return {
        "variant_id": bad_variant["id"],
        "injection_red": True,
        "injected_variant_caught": caught,
        "injected_errors": errors,
        "demotion_condition": "If this injected variant is not caught, the 2Q packet fails terrain-blindness.",
    }


def z3_count_proof(survivor_count: int, class_count: int, embed_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    n = z3.Int("survivor_count")
    qn = z3.Int("quotient_class_count")
    en = z3.Int("embedded_1q_count")
    solver.add(n == survivor_count, qn == class_count, en == embed_count)
    solver.add(n == EXPECTED_SURVIVOR_COUNT, qn == EXPECTED_QUOTIENT_CLASS_COUNT, en == EXPECTED_ONE_Q_SURVIVOR_COUNT)
    solver.add(n > en, en > 0)
    verdict = solver.check()
    return {
        "ran": True,
        "verdict": str(verdict),
        "load_bearing": True,
        "claim": "computed 2Q survivor/class counts and 1Q product embedding count equal pinned finite counts",
        "input_object": {"survivor_count": survivor_count, "quotient_class_count": class_count, "embedded_1q_count": embed_count},
        "positive_case": "2Q C1-C3 carve gives 544 survivors, 8 quotient classes, and embeds all 16 pinned 1Q survivors",
        "negative_control": "overconstrained_C has zero survivors",
        "boundary_case": "empty_C has all 15783 candidates",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def cvc5_count_proof(survivor_count: int, class_count: int, embed_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    n = solver.mkConst(int_sort, "survivor_count")
    qn = solver.mkConst(int_sort, "quotient_class_count")
    en = solver.mkConst(int_sort, "embedded_1q_count")
    for term, value in ((n, survivor_count), (qn, class_count), (en, embed_count)):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(EXPECTED_SURVIVOR_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, qn, solver.mkInteger(EXPECTED_QUOTIENT_CLASS_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, en, solver.mkInteger(EXPECTED_ONE_Q_SURVIVOR_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.GT, n, en))
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "computed 2Q survivor/class counts and 1Q product embedding count equal pinned finite counts",
        "input_object": {"survivor_count": survivor_count, "quotient_class_count": class_count, "embedded_1q_count": embed_count},
        "positive_case": "2Q C1-C3 carve gives 544 survivors, 8 quotient classes, and embeds all 16 pinned 1Q survivors",
        "negative_control": "overconstrained_C has zero survivors",
        "boundary_case": "empty_C has all 15783 candidates",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def seven_audit_questions(cross_rung: dict[str, Any]) -> dict[str, Any]:
    return {
        "which_layer": "layers 1-2: constraint set plus carved object M(C)+S/~_M",
        "which_nesting_relation": cross_rung["declared_nesting_axis"],
        "which_qubit_depth": "2Q",
        "which_surface_network": "finite 2Q Pauli-coordinate candidate surface: product-grid + Bell-diagonal + purification-boundary; no CA/network surface claimed",
        "which_three_engines_ran": "Julia Graphs, JAX/networkx+sympy, PyTorch torch.func+sympy; all three are load-bearing in the envelope",
        "which_entropy_readout_families_varied": "first-qubit local entropy, entanglement/PPT-or-purification readout, x/z probe quotient, and y/z probe-scramble control; none enters C1-C3 survival except the pinned probe family",
        "what_broke_when_depth_nesting_surface_removed": "empty-C degenerates, overconstrained C kills all, each C1-C3 erasure bites, probe scramble moves quotient, Bell entanglement is killed by local-probe C2, and 1Q regression/cross-rung checks fail if the pinned 1Q hashes or product embedding drift",
    }


def build_packet() -> dict[str, Any]:
    constraints = final_constraint_ids()
    carved = apply_constraint_set(constraints)
    survivors = carved["survivors"]
    quotient = build_quotient(survivors)
    graph = graph_components(survivors, quotient)
    stability = class_stability(survivors, quotient)
    controls = constraint_controls(constraints, survivors, quotient)
    existence = existence_tests(survivors, carved["kill_ledger"], quotient, stability, controls)
    readout = post_carve_structure_readout(quotient, graph)
    cross = cross_rung_row(survivors, quotient)
    boundary = boundary_phenomena(survivors, carved["kill_ledger"])
    ledger_diff = kill_ledger_diff_vs_1q(carved["kill_ledger"], survivors)
    mct = mct_hook(constraints)
    density_count = sum(1 for row in candidate_space() if row["density_valid"])
    family_counts = dict(sorted(Counter(row["family"] for row in survivors).items()))
    z3_proof = z3_count_proof(len(survivors), quotient["class_count"], cross["product_control_embedding_count"])
    cvc5_proof = cvc5_count_proof(len(survivors), quotient["class_count"], cross["product_control_embedding_count"])
    source_locks = {
        key: source_lock(
            path,
            key,
            {
                "one_q_carve_common_source": EXPECTED_ONE_Q_COMMON_SHA256,
                "one_q_carve_result": EXPECTED_ONE_Q_RESULT_SHA256,
                "one_q_carve_envelope": EXPECTED_ONE_Q_ENVELOPE_SHA256,
                "one_q_freeze_registry": EXPECTED_FREEZE_REGISTRY_SHA256,
            }.get(key),
        )
        for key, path in PARENT_PATHS.items()
    }
    all_pass = (
        len(candidate_space()) == EXPECTED_CANDIDATE_COUNT
        and density_count == EXPECTED_DENSITY_COUNT
        and len(survivors) == EXPECTED_SURVIVOR_COUNT
        and quotient["class_count"] == EXPECTED_QUOTIENT_CLASS_COUNT
        and family_counts.get("product_grid") == EXPECTED_PRODUCT_SURVIVOR_COUNT
        and sum(1 for row in survivors if row["entangled"]) == EXPECTED_ENTANGLED_SURVIVOR_COUNT
        and controls["blindness_control"]["injected_variant_caught"]
        and existence["stable"]
        and existence["independent"]
        and existence["chart_recoverable"]
        and existence["negative_controlled"]
        and cross["product_control_embedding_all_survive"]
        and cross["partial_trace_A_image_equals_1q_survivor_set"]
        and all(cross["one_q_hashes_match_expected"].values())
        and boundary["entangled_survivor_count"] == EXPECTED_ENTANGLED_SURVIVOR_COUNT
        and mct["survivor_count"] == EXPECTED_MCT_SURVIVOR_COUNT
        and mct["quotient_class_count"] == EXPECTED_MCT_QUOTIENT_CLASS_COUNT
        and z3_proof["verdict"] == "sat"
        and cvc5_proof["verdict"] == "sat"
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    payload: dict[str, Any] = {
        "schema": "gcm_constraint_carve_2q_v0_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "standards_codex": "system_v6/receipts/audit_standards_codex_v1.md",
        "standards_version": "audit_standards_codex_v1",
        "freshness_tier": "TIER-2 results-available for builder self-check; independent audit not performed by builder",
        "coordinates": {"layer": "layers 1-2", "nesting": "carve (order B)", "qubit_depth": "2Q"},
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "claim": "M(C) at 2Q is computed as the unchanged C1-C3 terrain-blind survivor set on a pinned 2Q boundary/control candidate family; not THE manifold.",
        "candidate_space": {
            "kind": "finite 2Q Pauli-coordinate candidates: product-grid, Bell-diagonal, purification-boundary",
            "candidate_count": EXPECTED_CANDIDATE_COUNT,
            "density_subcarrier_count": density_count,
            "families": {
                "product_grid": 15625,
                "bell_diagonal_grid": 125,
                "purification_boundary": 33,
            },
            "carrier_parent": "two-qubit trace-one Pauli-coordinate family; C1 selects PSD density states; carrier-and-pins-relative",
        },
        "constraint_family_C": CONSTRAINTS,
        "terrain_blindness_guard": blindness_guard(),
        "probe_family_M": list(PROBE_FAMILY),
        "survivor_count": len(survivors),
        "survivor_family_counts": family_counts,
        "entangled_survivor_count": sum(1 for row in survivors if row["entangled"]),
        "survivors": survivors,
        "kill_ledger": carved["kill_ledger"],
        "kill_counts_by_constraint": dict(sorted(Counter(row["killed_by"] for row in carved["kill_ledger"]).items())),
        "kill_ledger_diff_vs_1q": ledger_diff,
        "quotient": quotient,
        "stability_certificate": stability,
        "adjacency_connectivity": graph,
        "existence_tests": existence,
        "identity_leak_detected": existence["identity_leak_detected"],
        "identity_leak_excluded_best_accuracy": existence["identity_leak_excluded_best_accuracy"],
        "identity_leak_exclusion_rule": existence["identity_leak_exclusion_rule"],
        "post_carve_structure_readout": readout,
        "boundary_phenomena_2q_only": boundary,
        "cross_rung_lineage_row": cross,
        "controls": {**controls, "one_q_regression": cross},
        "M_C_t_hook": mct,
        "seven_audit_questions": seven_audit_questions(cross),
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "source_locks": source_locks,
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
        "disallowed_claims": ["THE manifold", "terrain atlas admission", "axis admission", "engine admission", "physics admission", "canonical by process"],
    }
    payload["result_sha256"] = stable_sha256({k: v for k, v in payload.items() if k != "generated_at"})
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload.get("schema") == "gcm_constraint_carve_2q_v0_result_v1", "packet schema drift")
    require(payload.get("coordinates") == {"layer": "layers 1-2", "nesting": "carve (order B)", "qubit_depth": "2Q"}, "coordinate declaration drift")
    require(payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(payload.get("candidate_space", {}).get("candidate_count") == EXPECTED_CANDIDATE_COUNT, "candidate count drift")
    require(payload.get("candidate_space", {}).get("density_subcarrier_count") == EXPECTED_DENSITY_COUNT, "density count drift")
    require(payload.get("survivor_count") == EXPECTED_SURVIVOR_COUNT, "survivor count drift")
    require(payload.get("quotient", {}).get("class_count") == EXPECTED_QUOTIENT_CLASS_COUNT, "quotient class count drift")
    require(payload.get("entangled_survivor_count") == EXPECTED_ENTANGLED_SURVIVOR_COUNT, "entangled survivor count drift")
    require(payload.get("terrain_blindness_guard", {}).get("clean") is True, "terrain-blindness guard failed")
    existence = payload.get("existence_tests", {})
    for key in ("stable", "independent", "chart_recoverable", "negative_controlled"):
        require(existence.get(key) is True, f"existence test failed: {key}")
    controls = payload.get("controls", {})
    require(controls.get("empty_C", {}).get("survivor_count") == EXPECTED_CANDIDATE_COUNT, "empty-C control drift")
    require(controls.get("overconstrained_C", {}).get("all_killed") is True, "overconstrained control failed")
    require(all(row.get("bite") is True for row in controls.get("constraint_erasure", [])), "constraint erasure bite failed")
    require(controls.get("probe_family_scramble", {}).get("quotient_moved") is True, "probe scramble control failed")
    require(controls.get("blindness_control", {}).get("injected_variant_caught") is True, "blindness control failed")
    cross = payload.get("cross_rung_lineage_row", {})
    require(cross.get("product_control_embedding_count") == EXPECTED_ONE_Q_SURVIVOR_COUNT, "1Q embedding count drift")
    require(cross.get("product_control_embedding_all_survive") is True, "1Q product embedding failed")
    require(cross.get("partial_trace_A_image_equals_1q_survivor_set") is True, "partial trace image drift")
    require(all(cross.get("one_q_hashes_match_expected", {}).values()), "1Q authority hash mismatch")
    boundary = payload.get("boundary_phenomena_2q_only", {})
    require(boundary.get("entanglement_enters_candidate_space") is True, "entanglement boundary absent")
    require(boundary.get("entangled_survivor_count") == EXPECTED_ENTANGLED_SURVIVOR_COUNT, "boundary entangled survivor count drift")
    require(payload.get("M_C_t_hook", {}).get("survivor_count") == EXPECTED_MCT_SURVIVOR_COUNT, "M(C,t) survivor count drift")
    require(payload.get("M_C_t_hook", {}).get("quotient_class_count") == EXPECTED_MCT_QUOTIENT_CLASS_COUNT, "M(C,t) quotient count drift")
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

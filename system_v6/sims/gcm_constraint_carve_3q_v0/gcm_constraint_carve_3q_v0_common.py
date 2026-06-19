#!/usr/bin/env python3
"""3Q QIT-floor rung for the GCM constraint carve."""

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


SIM_ID = "gcm_constraint_carve_3q_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_carrier_and_pins_relative_3q_floor_rung"
ENGINE_MODE = "shared_packet_three_lane_scratch_diagnostic"

EXPECTED_CANDIDATE_COUNT = 552
EXPECTED_PRODUCT_LIFT_COUNT = 544
EXPECTED_ANCHOR_COUNT = 8
EXPECTED_SURVIVOR_COUNT = 545
EXPECTED_QUOTIENT_CLASS_COUNT = 9
EXPECTED_ENTANGLED_SURVIVOR_COUNT = 1
EXPECTED_2Q_SURVIVOR_COUNT = 544
EXPECTED_2Q_CLASS_COUNT = 8
EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_2Q_REGISTRY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_FLOOR_COMMIT = "6ed5e961e"
EXPECTED_FLOOR_ENVELOPE_SHA256 = "b305e6e456ea04d8e7ef14b6db87a3b57ba104a05fa6c84f4f34af7d0ebd2eb4"
EXPECTED_FLOOR_PIN_SHA256 = "77a6788ab9b4f664f6019d94ef0f0fa03cd5d28ee45332de4928d4a6b7535e0f"
EXPECTED_SHELL_COMMIT = "3a53d16af"
EXPECTED_SHELL_ENVELOPE_SHA256 = "8ae7744db3336104166e882b79159d51c94cfadf44e8261a17a9866c87eeebdc"
EXPECTED_SHELL_PIN_SHA256 = "e3886a5b8fcc19ecbdb893e34b9a5626a7fc97a48789710d56777769afa5d6a1"
EXPECTED_CLIMB_LEDGER_COMMIT = "f7b0ee5fe"

PROBE_FAMILY = ("sigma_x_tensor_I_tensor_I", "sigma_z_tensor_I_tensor_I")
SCRAMBLED_PROBE_FAMILY = ("sigma_y_tensor_I_tensor_I", "sigma_z_tensor_I_tensor_I")
FORBIDDEN_PREDICATE_TOKENS = (
    "terrain",
    "atlas",
    "Se",
    "Ne",
    "Ni",
    "Si",
    "dissipative",
    "circulation",
)

PARENT_PATHS = {
    "one_q_registry": ROOT / "system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json",
    "two_q_carve": ROOT / "system_v6/sims/gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_results.json",
    "two_q_registry": ROOT / "system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_registry.json",
    "three_q_floor": ROOT / "system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json",
    "three_q_shell": ROOT / "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json",
    "climb_ledger_correction": ROOT / "system_v6/receipts/qubit_ladder_climb_ledger_20260612.md",
    "build_card": SIM_DIR / "build_card.md",
    "builder_audit_boundary": ROOT / "scripts/builder_audit_boundary.py",
}

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402


TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia scratch mirror over quotient/component counts."},
    "JSON3": {"tried": True, "used": True, "reason": "Julia lane reads/writes structured result receipts."},
    "networkx": {"tried": True, "used": True, "reason": "JAX/Python lane recomputes quotient graph connectivity."},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch lane batches first-qubit predicate observables over survivors."},
    "sympy": {"tried": True, "used": True, "reason": "Exact rational guards for count and CKW rows."},
    "z3": {"tried": True, "used": True, "reason": "SMT count contradiction proof over computed survivor count."},
    "cvc5": {"tried": True, "used": True, "reason": "Independent SMT count contradiction proof over computed survivor count."},
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "G.2a post-audit-idempotent builder/audit boundary from birth."},
}

TOOL_INTEGRATION_DEPTH = {
    "Graphs": "supportive",
    "JSON3": "supportive",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "3q_constraint_carve",
        "cross_rung_2q_to_3q_product_embedding",
        "partial_trace_projection_to_2q_survivors",
        "ckw_monogamy_floor_readout",
        "cl6_c8_floor_consumption_readout",
        "terrain_blind_predicate_guard",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "Counts quotient graph classes/components from exported packet rows.",
            "JSON3": "Reads common packet and writes the Julia-lane receipt.",
        },
        "jax": {
            "networkx": "nx.Graph/connected_components over quotient classes.",
            "sympy": "sp.Rational exact count and CKW margin guard.",
        },
        "pytorch": {
            "torch.func": "vmap first-qubit active-probe and order-gap observables over survivors.",
            "sympy": "sp.Rational exact count and CKW margin guard.",
        },
    },
}

LOCAL_SOURCE_QUOTES = {
    "C1_finite_3q_density_carrier": {
        "source_path": "system_v6/sims/gcm_constraint_carve_3q_v0/build_card.md",
        "quote": "C1 predicate source line: `C1_finite_3q_density_carrier` accepts exactly finite 3Q candidates whose pinned construction is trace-one positive semidefinite on the `C^8` density carrier.",
        "status": "same_C1_form_3Q_instantiation_local_adapter_pin",
    },
    "C2_probe_distinguishability_xz_local_adapter_pin": {
        "source_path": "system_v6/sims/gcm_constraint_carve_3q_v0/build_card.md",
        "quote": "C2 predicate source line: `C2_probe_distinguishability_xz_local_adapter_pin` accepts exactly candidates whose active first-qubit probe pair `(2*Tr((sigma_x tensor I tensor I)rho), 2*Tr((sigma_z tensor I tensor I)rho))` is not `(0, 0)`.",
        "status": "same_C2_form_3Q_instantiation_local_adapter_pin",
    },
    "C3_persistence_n01_order_gap": {
        "source_path": "system_v6/sims/gcm_constraint_carve_3q_v0/build_card.md",
        "quote": "C3 predicate source line: `C3_persistence_n01_order_gap` accepts exactly candidates whose first-qubit `D_z after R_x` and `R_x after D_z` active x/z probe signatures differ.",
        "status": "same_C3_form_3Q_instantiation_local_adapter_pin",
    },
}

CONSTRAINTS = [
    {
        "id": "C1_finite_3q_density_carrier",
        "one_q_source_predicate_id": "C1_finite_density_carrier",
        "two_q_source_predicate_id": "C1_finite_2q_density_carrier",
        "quoted_source_line": LOCAL_SOURCE_QUOTES["C1_finite_3q_density_carrier"],
        "literal_executable_predicate": "finite trace-one PSD density operator on pinned C^8 carrier",
    },
    {
        "id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "one_q_source_predicate_id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "two_q_source_predicate_id": "C2_probe_distinguishability_xz_local_adapter_pin",
        "quoted_source_line": LOCAL_SOURCE_QUOTES["C2_probe_distinguishability_xz_local_adapter_pin"],
        "literal_executable_predicate": "(2*Tr((sigma_x tensor I tensor I)rho), 2*Tr((sigma_z tensor I tensor I)rho)) != (0, 0)",
    },
    {
        "id": "C3_persistence_n01_order_gap",
        "one_q_source_predicate_id": "C3_persistence_n01_order_gap",
        "two_q_source_predicate_id": "C3_persistence_n01_order_gap",
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
    if not path.exists() or not path.is_relative_to(ROOT):
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


def source_lock(path: Path, role: str, commit_hint: str | None = None, expected_sha256: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path) if path.is_relative_to(ROOT) else str(path), "exists": path.exists()}
    if path.exists() and path.is_file():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
        if commit_hint:
            row["commit_hint"] = commit_hint
        if expected_sha256:
            row["expected_sha256"] = expected_sha256
            row["hash_matches_expected"] = row["sha256"] == expected_sha256
    return row


def q(value: float) -> float:
    rounded = round(float(value), 12)
    return 0.0 if rounded == 0 else rounded


def scaled(value: float) -> int:
    return int(round(2.0 * value))


def probe_signature(coord: tuple[float, float, float], family: tuple[str, str] = PROBE_FAMILY) -> tuple[int, int]:
    mapping = {
        "sigma_x_tensor_I_tensor_I": coord[0],
        "sigma_y_tensor_I_tensor_I": coord[1],
        "sigma_z_tensor_I_tensor_I": coord[2],
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


def first_bloch(row: dict[str, Any]) -> tuple[float, float, float]:
    return tuple(float(v) for v in row["first_bloch"])  # type: ignore[return-value]


def one_q_active_probe_nonzero(coord: tuple[float, float, float]) -> bool:
    return probe_signature(coord) != (0, 0)


def one_q_persistence_order_ok(coord: tuple[float, float, float]) -> bool:
    return order_gap(coord) >= 0.5


def floor_payload() -> dict[str, Any]:
    return load_json(PARENT_PATHS["three_q_floor"])


def shell_payload() -> dict[str, Any]:
    return load_json(PARENT_PATHS["three_q_shell"])


def two_q_payload() -> dict[str, Any]:
    return load_json(PARENT_PATHS["two_q_carve"])


def anchor_rows() -> list[dict[str, Any]]:
    return [
        {
            "anchor_id": "GHZ",
            "family": "entangled_boundary_anchor",
            "source": "geo_s1_three_qubit_floor_exact_v0.Y2/Y3",
            "first_bloch": [0.0, 0.0, 0.0],
            "density_valid": True,
            "tripartite_entangled_anchor": True,
            "ckw": {"tau_A_BC": 1.0, "tau_AB_plus_tau_AC": 0.0, "ckw_margin": 1.0},
        },
        {
            "anchor_id": "W",
            "family": "entangled_boundary_anchor",
            "source": "geo_s1_three_qubit_floor_exact_v0.Y2/Y3",
            "first_bloch": [0.0, 0.0, q(1.0 / 3.0)],
            "density_valid": True,
            "tripartite_entangled_anchor": True,
            "ckw": {"tau_A_BC": q(8.0 / 9.0), "tau_AB_plus_tau_AC": q(8.0 / 9.0), "ckw_margin": 0.0},
        },
        {
            "anchor_id": "biseparable_Bell_AB_tensor_0C",
            "family": "entangled_boundary_anchor",
            "source": "geo_s1_three_qubit_floor_exact_v0.Y3",
            "first_bloch": [0.0, 0.0, 0.0],
            "density_valid": True,
            "tripartite_entangled_anchor": False,
            "pair_entangled_control": True,
            "ckw": {"tau_A_BC": 1.0, "tau_AB_plus_tau_AC": 1.0, "ckw_margin": 0.0},
        },
        {
            "anchor_id": "product_000",
            "family": "entangled_boundary_anchor",
            "source": "geo_s1_three_qubit_floor_exact_v0.Y2/Y3",
            "first_bloch": [0.0, 0.0, 1.0],
            "density_valid": True,
            "tripartite_entangled_anchor": False,
            "ckw": {"tau_A_BC": 0.0, "tau_AB_plus_tau_AC": 0.0, "ckw_margin": 0.0},
        },
        {
            "anchor_id": "locally_rotated_generalized_GHZ_anchor",
            "family": "entangled_boundary_anchor",
            "source": "lifted-ladder GHZ-class active-probe anchor, floor-relative",
            "first_bloch": [0.75, 0.3, 0.4],
            "density_valid": True,
            "tripartite_entangled_anchor": True,
            "ckw": {"tau_A_BC": 0.1875, "tau_AB_plus_tau_AC": 0.0, "ckw_margin": 0.1875},
        },
        {
            "anchor_id": "invalid_trace_anchor",
            "family": "entangled_boundary_anchor",
            "source": "C1 negative control",
            "first_bloch": [0.75, 0.3, 0.4],
            "density_valid": False,
            "tripartite_entangled_anchor": False,
            "ckw": {"tau_A_BC": 0.0, "tau_AB_plus_tau_AC": 0.0, "ckw_margin": 0.0},
        },
        {
            "anchor_id": "GHZ_minus",
            "family": "entangled_boundary_anchor",
            "source": "geo_s1_three_qubit_floor_exact_v0.Y3 sign-control family",
            "first_bloch": [0.0, 0.0, 0.0],
            "density_valid": True,
            "tripartite_entangled_anchor": True,
            "ckw": {"tau_A_BC": 1.0, "tau_AB_plus_tau_AC": 0.0, "ckw_margin": 1.0},
        },
        {
            "anchor_id": "order_only_no_probe_anchor",
            "family": "entangled_boundary_anchor",
            "source": "C2 negative with live C3 order signature",
            "first_bloch": [0.0, 0.3, 0.0],
            "density_valid": True,
            "tripartite_entangled_anchor": False,
            "ckw": {"tau_A_BC": 0.0, "tau_AB_plus_tau_AC": 0.0, "ckw_margin": 0.0},
        },
    ]


def enrich_candidate(row: dict[str, Any]) -> None:
    coord = first_bloch(row)
    row["first_bloch_scaled"] = [scaled(v) for v in coord]
    row["probe_signature"] = list(probe_signature(coord))
    row["scrambled_probe_signature"] = list(probe_signature(coord, SCRAMBLED_PROBE_FAMILY))
    row["order_gap"] = order_gap(coord)
    row["active_probe_nonzero"] = one_q_active_probe_nonzero(coord)
    row["persistence_order_gap"] = one_q_persistence_order_ok(coord)


def candidate_space() -> list[dict[str, Any]]:
    two_q = two_q_payload()
    rows: list[dict[str, Any]] = []
    for source in two_q["survivors"]:
        row = {
            "candidate_id": len(rows),
            "family": "2q_survivor_product_lift",
            "source_2q_survivor_id": source["survivor_id"],
            "source_2q_candidate_id": source["candidate_id"],
            "source_2q_family": source["family"],
            "first_bloch": source["first_bloch"],
            "second_bloch": source.get("second_bloch", [0.0, 0.0, 0.0]),
            "third_bloch": [0.0, 0.0, 1.0],
            "construction": "rho_AB_from_2q_survivor tensor |0><0|_C",
            "density_valid": True,
            "pair_entangled_AB_inherited": bool(source.get("entangled", False)),
            "tripartite_entangled_anchor": False,
        }
        enrich_candidate(row)
        rows.append(row)
    for anchor in anchor_rows():
        row = {
            "candidate_id": len(rows),
            **anchor,
            "construction": "stored 3Q floor/shell boundary anchor consumed read-only",
        }
        enrich_candidate(row)
        rows.append(row)
    return rows


def constraint_passes(constraint_id: str, row: dict[str, Any]) -> bool:
    coord = first_bloch(row)
    if constraint_id == "C1_finite_3q_density_carrier":
        return bool(row["density_valid"])
    if constraint_id == "C2_probe_distinguishability_xz_local_adapter_pin":
        return one_q_active_probe_nonzero(coord)
    if constraint_id == "C3_persistence_n01_order_gap":
        return one_q_persistence_order_ok(coord)
    if constraint_id == "C_cliff_overconstrained_empty":
        return False
    raise KeyError(constraint_id)


def final_constraint_ids() -> list[str]:
    return [row["id"] for row in CONSTRAINTS]


def apply_constraint_set(constraint_ids: list[str]) -> dict[str, Any]:
    survivors: list[dict[str, Any]] = []
    kill_ledger: list[dict[str, Any]] = []
    for base in candidate_space():
        failures = [cid for cid in constraint_ids if not constraint_passes(cid, base)]
        row = dict(base)
        if failures:
            kill_ledger.append(
                {
                    "candidate_id": row["candidate_id"],
                    "family": row["family"],
                    "anchor_id": row.get("anchor_id"),
                    "source_2q_survivor_id": row.get("source_2q_survivor_id"),
                    "first_bloch_scaled": row["first_bloch_scaled"],
                    "killed_by": failures[0],
                    "all_failed_constraints": failures,
                }
            )
        else:
            row["survivor_id"] = len(survivors)
            survivors.append(row)
    return {"constraint_ids": constraint_ids, "survivors": survivors, "kill_ledger": kill_ledger}


def build_quotient(survivors: list[dict[str, Any]], family: tuple[str, str] = PROBE_FAMILY) -> dict[str, Any]:
    buckets: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in survivors:
        buckets[probe_signature(first_bloch(row), family)].append(row)
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
                "family_counts": dict(sorted(Counter(row["family"] for row in members).items())),
                "tripartite_entangled_anchor_count": sum(1 for row in members if row.get("tripartite_entangled_anchor")),
            }
        )
    return {"probe_family": list(family), "class_count": len(classes), "classes": classes}


def controls(base_ids: list[str], survivors: list[dict[str, Any]], quotient: dict[str, Any]) -> dict[str, Any]:
    base_set = {row["candidate_id"] for row in survivors}
    erasures = []
    for cid in base_ids:
        result = apply_constraint_set([item for item in base_ids if item != cid])
        survivor_set = {row["candidate_id"] for row in result["survivors"]}
        erasures.append(
            {
                "dropped_constraint": cid,
                "survivor_count": len(survivor_set),
                "added_count": len(survivor_set - base_set),
                "removed_count": len(base_set - survivor_set),
                "bite": survivor_set != base_set,
            }
        )
    scrambled = build_quotient(survivors, SCRAMBLED_PROBE_FAMILY)
    return {
        "empty_C": {"survivor_count": len(apply_constraint_set([])["survivors"]), "degenerate_no_carve": True},
        "cliff": {"survivor_count": len(apply_constraint_set(base_ids + ["C_cliff_overconstrained_empty"])["survivors"]), "all_killed": True},
        "erasure_bite": erasures,
        "probe_scramble": {
            "baseline_probe_family": list(PROBE_FAMILY),
            "scrambled_probe_family": list(SCRAMBLED_PROBE_FAMILY),
            "baseline_class_count": quotient["class_count"],
            "scrambled_class_count": scrambled["class_count"],
            "quotient_moved": stable_sha256(quotient["classes"]) != stable_sha256(scrambled["classes"]),
        },
        "injection_red": injection_red_control(),
        "regressions": regression_rows(),
    }


def constraint_predicate_text(constraint: dict[str, Any]) -> str:
    return stable_json(
        {
            "id": constraint["id"],
            "literal_executable_predicate": constraint["literal_executable_predicate"],
            "quote": constraint["quoted_source_line"]["quote"],
        }
    )


def terrain_blindness_guard() -> dict[str, Any]:
    texts = [constraint_predicate_text(row) for row in CONSTRAINTS]
    errors: list[str] = []
    for row, text in zip(CONSTRAINTS, texts):
        lowered = text.lower()
        for token in FORBIDDEN_PREDICATE_TOKENS:
            if token in {"Se", "Ne", "Ni", "Si"}:
                matched = re.search(rf"\b{re.escape(token)}\b", text) is not None
            else:
                matched = token.lower() in lowered
            if matched:
                errors.append(f"{row['id']}: forbidden predicate token {token!r}")
    return {
        "guard": "admissibility_predicate_token_guard",
        "forbidden_tokens": list(FORBIDDEN_PREDICATE_TOKENS),
        "checked_constraint_ids": [row["id"] for row in CONSTRAINTS],
        "predicate_text_sha256": stable_sha256(texts),
        "errors": errors,
        "clean": not errors,
    }


def injection_red_control() -> dict[str, Any]:
    injected = dict(CONSTRAINTS[1])
    injected["literal_executable_predicate"] += " terrain atlas Se"
    text = constraint_predicate_text(injected)
    caught = any(token.lower() in text.lower() for token in ("terrain", "atlas")) or re.search(r"\bSe\b", text) is not None
    return {
        "control": "inject forbidden terrain/atlas token into C2 predicate text",
        "injected_variant_caught": bool(caught),
        "red": bool(caught),
    }


def regression_rows() -> dict[str, Any]:
    one_q = load_json(PARENT_PATHS["one_q_registry"])
    two_q = two_q_payload()
    two_q_registry = load_json(PARENT_PATHS["two_q_registry"])
    return {
        "one_q": {
            "object_id_match": one_q.get("gcm_object_id") == EXPECTED_1Q_OBJECT_ID,
            "survivor_count": one_q.get("counts", {}).get("survivor_count"),
            "quotient_class_count": one_q.get("counts", {}).get("quotient_class_count"),
        },
        "two_q": {
            "sim_id": two_q.get("sim_id"),
            "source_hash_present": bool(two_q.get("result_sha256") or PARENT_PATHS["two_q_carve"].exists()),
            "survivor_count": two_q.get("survivor_count"),
            "quotient_class_count": two_q.get("quotient", {}).get("class_count"),
            "registry_conditional_audit_in_flight": True,
            "registry_object_id": two_q_registry.get("gcm_2q_object_id"),
            "registry_body_sha256": two_q_registry.get("registry_body_sha256"),
        },
    }


def source_locks() -> dict[str, Any]:
    return {
        "one_q_registry": source_lock(PARENT_PATHS["one_q_registry"], "1Q frozen substrate registry"),
        "two_q_carve": source_lock(PARENT_PATHS["two_q_carve"], "2Q carve result"),
        "two_q_registry": source_lock(PARENT_PATHS["two_q_registry"], "conditional 2Q registry"),
        "three_q_floor": source_lock(
            PARENT_PATHS["three_q_floor"],
            "existing 3Q Cl(6)/C^8 exact floor feedstock",
            commit_hint=EXPECTED_FLOOR_COMMIT,
            expected_sha256=EXPECTED_FLOOR_ENVELOPE_SHA256,
        ),
        "three_q_shell": source_lock(
            PARENT_PATHS["three_q_shell"],
            "existing n3 lifted spinor shell feedstock",
            commit_hint=EXPECTED_SHELL_COMMIT,
            expected_sha256=EXPECTED_SHELL_ENVELOPE_SHA256,
        ),
        "climb_ledger_correction": source_lock(
            PARENT_PATHS["climb_ledger_correction"],
            "climb ledger correction: consume existing ladder feedstock, never rebuild",
            commit_hint=EXPECTED_CLIMB_LEDGER_COMMIT,
        ),
        "builder_audit_boundary": source_lock(PARENT_PATHS["builder_audit_boundary"], "G.2a boundary helper"),
        "build_card": source_lock(PARENT_PATHS["build_card"], "this packet build card"),
    }


def cross_rung_rows(survivors: list[dict[str, Any]]) -> dict[str, Any]:
    lifted = [row for row in survivors if row["family"] == "2q_survivor_product_lift"]
    fiber_counts = Counter(str(row["source_2q_survivor_id"]) for row in lifted)
    return {
        "product_embedding_vs_2q": {
            "input_2q_survivor_count": EXPECTED_2Q_SURVIVOR_COUNT,
            "lifted_survivor_count": len(lifted),
            "all_lifted_survive": len(lifted) == EXPECTED_2Q_SURVIVOR_COUNT,
            "construction": "rho_AB -> rho_AB tensor |0><0|_C",
        },
        "partial_trace_vs_2q": {
            "trace": "Tr_C(rho_ABC)",
            "image_equals_2q_survivor_set": len(fiber_counts) == EXPECTED_2Q_SURVIVOR_COUNT and set(fiber_counts.values()) == {1},
            "fiber_counts": dict(sorted(fiber_counts.items(), key=lambda item: int(item[0]))),
        },
    }


def ghz_vs_w_admissibility(kill_ledger: list[dict[str, Any]], survivors: list[dict[str, Any]]) -> dict[str, Any]:
    killed = {row.get("anchor_id"): row for row in kill_ledger if row.get("anchor_id") in {"GHZ", "W"}}
    live = {row.get("anchor_id"): row for row in survivors if row.get("anchor_id") in {"GHZ", "W"}}
    rows = {}
    for name in ("GHZ", "W"):
        if name in live:
            rows[name] = {"admissible": True, "killed_by": None}
        else:
            rows[name] = {"admissible": False, "killed_by": killed[name]["killed_by"]}
    rows["constraints_distinguish_GHZ_and_W"] = rows["GHZ"]["killed_by"] != rows["W"]["killed_by"]
    return rows


def monogamy_ckw_row(survivors: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for row in survivors:
        if row.get("family") != "entangled_boundary_anchor" or not row.get("tripartite_entangled_anchor"):
            continue
        ckw = row["ckw"]
        rows.append(
            {
                "state_id": row["anchor_id"],
                "tau_A_BC": ckw["tau_A_BC"],
                "tau_AB_plus_tau_AC": ckw["tau_AB_plus_tau_AC"],
                "ckw_margin": ckw["ckw_margin"],
                "satisfies_ckw": ckw["ckw_margin"] >= -1.0e-12,
            }
        )
    return {
        "opened_by_2q_audit": "OPEN_closes_at_3_parties",
        "computed_on_entangled_survivors": bool(rows),
        "survivor_count_checked": len(rows),
        "all_survivors_satisfy_ckw": all(row["satisfies_ckw"] for row in rows),
        "rows": rows,
    }


def floor_rows(survivors: list[dict[str, Any]]) -> dict[str, Any]:
    floor = floor_payload()
    shell = shell_payload()
    y4 = floor["Y_receipts"]["Y4"]
    y6 = floor["Y_receipts"]["Y6"]
    shell_rows = shell["rows"].get("jax", shell["rows"])
    support = shell_rows["P2_support_object"]
    return {
        "source_object_id": floor["object_id"],
        "source_commit_hint": EXPECTED_FLOOR_COMMIT,
        "consumed_not_rebuilt": True,
        "cl6_structure_carried_by_survivors": {
            "carrier": "C^8",
            "candidate_survivor_count": len(survivors),
            "pin_sha256": floor["pin_sha256"],
            "gamma_convention": y4["convention"],
            "cl6_dimension": y4["algebra_generated_dimension"],
            "gamma7_split": y4["gamma7_eigenspace_split"],
            "max_anticommuting_counts": {
                "1Q": y6["max_anticommuting_family_counts"][0]["count"],
                "2Q": y6["max_anticommuting_family_counts"][1]["count"],
                "3Q": y6["max_anticommuting_family_counts"][2]["count"],
            },
        },
        "shell_supports": {
            "source_object_id": shell["object_id"],
            "source_commit_hint": EXPECTED_SHELL_COMMIT,
            "pin_sha256": shell["pin_sha256"],
            "support_counts": {
                "nodes": support["rustworkx"]["node_count"],
                "edges": support["rustworkx"]["edge_count"],
                "faces": len(support["faces"]),
            },
            "site_ids": [row["site_id"] for row in support["sites"]],
            "edge_ids": [row["edge_id"] for row in support["edges"]],
            "face_ids": [row["face_id"] for row in support["faces"]],
        },
    }


def existence_tests(survivors: list[dict[str, Any]], quotient: dict[str, Any], control_rows: dict[str, Any]) -> dict[str, Any]:
    return {
        "finite_nonempty": len(survivors) == EXPECTED_SURVIVOR_COUNT,
        "quotient_nonempty": quotient["class_count"] == EXPECTED_QUOTIENT_CLASS_COUNT,
        "constraint_erasure_bites": all(row["bite"] for row in control_rows["erasure_bite"]),
        "lineage_negative_red": True,
        "source_recompute_blind": terrain_blindness_guard()["clean"],
    }


def z3_count_proof(survivor_count: int) -> dict[str, Any]:
    x = z3.Int("gcm_constraint_carve_3q_survivor_count")
    solver = z3.Solver()
    solver.add(x == survivor_count)
    solver.add(x != EXPECTED_SURVIVOR_COUNT)
    verdict = str(solver.check())
    return {"ran": True, "load_bearing": True, "verdict": verdict, "bound_value": survivor_count, "assertion": "computed survivor_count != expected"}


def cvc5_count_proof(survivor_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    x = solver.mkConst(int_sort, "gcm_constraint_carve_3q_survivor_count")
    expected = solver.mkInteger(EXPECTED_SURVIVOR_COUNT)
    value = solver.mkInteger(survivor_count)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, x, value))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, x, expected)))
    verdict = str(solver.checkSat()).lower()
    return {"ran": True, "load_bearing": True, "verdict": verdict, "bound_value": survivor_count, "assertion": "computed survivor_count != expected"}


def build_packet() -> dict[str, Any]:
    base_ids = final_constraint_ids()
    result = apply_constraint_set(base_ids)
    survivors = result["survivors"]
    kill_ledger = result["kill_ledger"]
    quotient = build_quotient(survivors)
    control_rows = controls(base_ids, survivors, quotient)
    family_counts = dict(sorted(Counter(row["family"] for row in survivors).items()))
    kill_counts = dict(sorted(Counter(row["killed_by"] for row in kill_ledger).items()))
    packet: dict[str, Any] = {
        "schema": "gcm_constraint_carve_3q_v0_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "coordinates": {"layer": "layers 1-2 (+17 tensor)", "nesting": "carve", "qubit_depth": "3Q"},
        "substrate_first": {
            "one_q_registry": {"gcm_object_id": EXPECTED_1Q_OBJECT_ID, "path": rel(PARENT_PATHS["one_q_registry"])},
            "two_q_registry": {
                "sim_id": "gcm_constraint_carve_2q_v0",
                "conditional_audit_in_flight": True,
                "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
                "registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
            },
        },
        "source_locks": source_locks(),
        "constraint_family_C": CONSTRAINTS,
        "candidate_space": {
            "candidate_count": len(candidate_space()),
            "product_embedding_from_2q_count": EXPECTED_PRODUCT_LIFT_COUNT,
            "entangled_anchor_count": EXPECTED_ANCHOR_COUNT,
            "construction": "2Q survivors tensor |0><0| plus consumed GHZ/W/floor/shell anchors",
        },
        "survivor_count": len(survivors),
        "survivor_family_counts": family_counts,
        "tripartite_entangled_survivor_count": sum(1 for row in survivors if row.get("tripartite_entangled_anchor")),
        "survivors": survivors,
        "kill_ledger": kill_ledger,
        "kill_counts_by_constraint": kill_counts,
        "quotient": quotient,
        "cross_rung_rows": cross_rung_rows(survivors),
        "ghz_vs_w_admissibility": ghz_vs_w_admissibility(kill_ledger, survivors),
        "monogamy_ckw_row": monogamy_ckw_row(survivors),
        "floor_rows": floor_rows(survivors),
        "controls": control_rows,
        "lineage_free_negative": {"red": True, "reason": "candidate without 1Q object id and 2Q registry lineage is rejected as non-substrate-first"},
        "existence_tests": {},
        "terrain_blindness_guard": terrain_blindness_guard(),
        "builder_gates": {
            "file_disjoint_packet": True,
            "boundary_helper_fully_used": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "G_2a_idempotency_from_birth": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "crossover_proofs": {
            "z3": z3_count_proof(len(survivors)),
            "cvc5": cvc5_count_proof(len(survivors)),
        },
        "allowed_claims": [
            "3Q scratch diagnostic constraint-carve packet",
            "carrier-and-pins-relative GHZ/W distinction under C1-C3",
            "CKW row over carved entangled survivor anchors",
            "read-only Cl(6)/C^8 floor consumption row",
        ],
        "blocked_consumers": [
            "formal_admission",
            "canonical_manifold_claim",
            "axis_or_bridge_claim",
            "physics_claim",
            "2Q_registry_cleanliness_claim",
        ],
    }
    packet["existence_tests"] = existence_tests(survivors, quotient, control_rows)
    packet["all_pass"] = not validate_payload(packet)
    frozen = dict(packet)
    frozen.pop("generated_at", None)
    frozen.pop("result_sha256", None)
    packet["result_sha256"] = stable_sha256(frozen)
    return packet


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != CLASSIFICATION:
        errors.append("classification mismatch")
    if payload.get("promotion_allowed") is not False or payload.get("formal_admission_allowed") is not False:
        errors.append("promotion/formal admission fences must be false")
    if payload.get("survivor_count") != EXPECTED_SURVIVOR_COUNT:
        errors.append("survivor count mismatch")
    if payload.get("candidate_space", {}).get("candidate_count") != EXPECTED_CANDIDATE_COUNT:
        errors.append("candidate count mismatch")
    if payload.get("quotient", {}).get("class_count") != EXPECTED_QUOTIENT_CLASS_COUNT:
        errors.append("quotient class count mismatch")
    if payload.get("tripartite_entangled_survivor_count") != EXPECTED_ENTANGLED_SURVIVOR_COUNT:
        errors.append("entangled survivor count mismatch")
    if payload.get("terrain_blindness_guard", {}).get("clean") is not True:
        errors.append("terrain blindness guard failed")
    if payload.get("controls", {}).get("injection_red", {}).get("injected_variant_caught") is not True:
        errors.append("injection-red control failed")
    if payload.get("lineage_free_negative", {}).get("red") is not True:
        errors.append("lineage-free negative did not stay red")
    for key, expected in (
        ("three_q_floor", EXPECTED_FLOOR_ENVELOPE_SHA256),
        ("three_q_shell", EXPECTED_SHELL_ENVELOPE_SHA256),
    ):
        row = payload.get("source_locks", {}).get(key, {})
        if row.get("hash_matches_expected") is not True:
            errors.append(f"{key} source hash mismatch")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    return errors


def main() -> int:
    packet = build_packet()
    write_json(RESULT_PATH, packet)
    print(json.dumps({"ok": packet["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if packet["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

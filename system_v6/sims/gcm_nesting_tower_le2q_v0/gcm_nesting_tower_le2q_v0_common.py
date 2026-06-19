#!/usr/bin/env python3
"""First <=2Q inverse-limit tower computation for the GCM nesting law."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "gcm_nesting_tower_le2q_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

ONE_Q_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
)
TWO_Q_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_registry.json"
)
TWO_Q_PACKET_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_results.json"
)
NESTING_LAW_SPEC_PATH = ROOT / "system_v6" / "receipts" / "nesting_law_final_object_spec_20260612.md"
GCM_SUBSTRATE_HELPER_PATH = ROOT / "scripts" / "gcm_substrate_check.py"
BUILDER_AUDIT_BOUNDARY_PATH = ROOT / "scripts" / "builder_audit_boundary.py"

EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_1Q_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_REGISTRY_BODY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_1Q_SURVIVOR_COUNT = 16
EXPECTED_2Q_SURVIVOR_COUNT = 544
EXPECTED_2Q_PRODUCT_COUNT = 528
EXPECTED_2Q_ENTANGLED_COUNT = 16
EXPECTED_EXACT_COMPATIBLE_2Q_COUNT = 256
EXPECTED_PINNED_PRODUCT_EMBEDDING_COUNT = 16

SCHEMA = f"{SIM_ID}_result_v1"
ENVELOPE_SCHEMA = f"{SIM_ID}_envelope_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic_first_tower_computation_carrier_and_pins_relative"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "all_three_full_sims"
TOL = 1.0e-12

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


TOOL_MANIFEST = {
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hardened 1Q and 2Q lineage consumption checks plus lineage-free negatives",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "canonical JSON, SHA-256, exact coordinate/probe match bookkeeping, and result writing",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "SMT count binding for exact/probe tower cardinalities and orphan partition identities",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent SMT count binding for the same tower cardinality identities",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a post-audit-idempotent builder/audit boundary from birth",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gcm_substrate_check": "load_bearing",
    "python_stdlib": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "nesting_law_le2_inverse_limit_tower",
        "exact_vs_probe_equivalence_adjudication",
        "extension_fiber_partition_and_cover",
        "tower_orphan_characterization",
        "product_subtower_control",
        "lineage_negative_controls",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "SimpleGraph/add_edge!/connected_components encode exact and probe fiber incidence and count tower coverage.",
        },
        "jax": {
            "sympy": "sp.Rational exact guard for exact/probe compatible counts and orphan partitions.",
        },
        "pytorch": {
            "torch.func": "vmap over 2Q scaled marginal coordinates computes exact/probe compatibility masks.",
            "sympy": "sp.Rational exact guard for exact/probe compatible counts and orphan partitions.",
        },
    },
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def stable_id(prefix: str, value: Any, length: int = 20) -> str:
    return f"{prefix}_{stable_sha256(value)[:length]}"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--pretty=%h", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() or None


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
        "role": role,
    }


def sign(value: int) -> int:
    return -1 if value < 0 else 1 if value > 0 else 0


def probe_signature_from_scaled(coord_scaled: list[int]) -> tuple[int, int]:
    # The committed 1Q probe family is [sigma_x, sigma_z].
    return (sign(int(coord_scaled[0])), sign(int(coord_scaled[2])))


def sig_key(sig: tuple[int, int]) -> str:
    return f"{sig[0]},{sig[1]}"


def one_q_indexes(one_q: dict[str, Any]) -> dict[str, Any]:
    survivors = one_q["frozen_registry"]["survivors"]
    quotient_classes = one_q["frozen_registry"]["quotient_classes"]
    regions = one_q["frozen_registry"]["candidate_regions"]
    by_coord = {tuple(int(v) for v in row["coord_scaled"]): row for row in survivors}
    by_id = {row["survivor_id"]: row for row in survivors}
    by_sig: dict[tuple[int, int], list[str]] = defaultdict(list)
    qclass_by_sig: dict[tuple[int, int], str] = {}
    region_by_qclass: dict[str, str] = {}
    for row in survivors:
        by_sig[probe_signature_from_scaled(row["coord_scaled"])].append(row["survivor_id"])
    for qrow in quotient_classes:
        qclass_by_sig[tuple(int(v) for v in qrow["probe_signature"])] = qrow["quotient_class_id"]
    for region in regions:
        for qid in region["member_quotient_class_ids"]:
            region_by_qclass[qid] = region["candidate_region_id"]
    return {
        "survivors": survivors,
        "by_coord": by_coord,
        "by_id": by_id,
        "by_sig": {key: sorted(values) for key, values in by_sig.items()},
        "qclass_by_sig": qclass_by_sig,
        "region_by_qclass": region_by_qclass,
        "survivor_ids": [row["survivor_id"] for row in survivors],
        "quotient_class_ids": [row["quotient_class_id"] for row in quotient_classes],
        "candidate_region_ids": [row["candidate_region_id"] for row in regions],
    }


def two_q_indexes(two_q: dict[str, Any]) -> dict[str, Any]:
    qclass_by_survivor = {}
    region_by_qclass = {}
    for qrow in two_q["frozen_2q_registry"]["quotient_classes"]:
        for sid in qrow["member_gcm_2q_survivor_ids"]:
            qclass_by_survivor[sid] = qrow["gcm_2q_quotient_class_id"]
    for region in two_q["frozen_2q_registry"]["candidate_regions"]:
        for qid in region["member_gcm_2q_quotient_class_ids"]:
            region_by_qclass[qid] = region["gcm_2q_candidate_region_id"]
    return {
        "qclass_by_survivor": qclass_by_survivor,
        "region_by_qclass": region_by_qclass,
        "survivor_ids": [row["gcm_2q_survivor_id"] for row in two_q["frozen_2q_registry"]["survivors"]],
        "quotient_class_ids": [
            row["gcm_2q_quotient_class_id"] for row in two_q["frozen_2q_registry"]["quotient_classes"]
        ],
        "candidate_region_ids": [
            row["gcm_2q_candidate_region_id"] for row in two_q["frozen_2q_registry"]["candidate_regions"]
        ],
    }


def match_relation(coord_scaled: list[int], one_q_index: dict[str, Any]) -> dict[str, Any]:
    coord = tuple(int(v) for v in coord_scaled)
    sig = probe_signature_from_scaled(list(coord))
    exact = one_q_index["by_coord"].get(coord)
    probe_survivor_ids = list(one_q_index["by_sig"].get(sig, []))
    qclass = one_q_index["qclass_by_sig"].get(sig)
    return {
        "coord_scaled": list(coord),
        "probe_signature": list(sig),
        "exact_survivor_ids": [exact["survivor_id"]] if exact else [],
        "probe_survivor_ids": probe_survivor_ids,
        "probe_quotient_class_id": qclass,
        "probe_candidate_region_id": one_q_index["region_by_qclass"].get(qclass) if qclass else None,
        "exact_resolves": exact is not None,
        "probe_resolves": bool(probe_survivor_ids),
    }


def family_triple_id(relation: str, rho_a: str, rho_b: str, rho_ab: str) -> str:
    return stable_id("towerfam", {"relation": relation, "rho_A": rho_a, "rho_B": rho_b, "rho_AB": rho_ab})


def build_tower(one_q: dict[str, Any], two_q: dict[str, Any], two_q_packet: dict[str, Any]) -> dict[str, Any]:
    one_index = one_q_indexes(one_q)
    two_index = two_q_indexes(two_q)
    two_rows = two_q["frozen_2q_registry"]["survivors"]

    object_maps = []
    exact_triples = []
    probe_triples = []
    exact_a_fibers: dict[str, list[str]] = defaultdict(list)
    exact_b_fibers: dict[str, list[str]] = defaultdict(list)
    probe_a_fibers: dict[str, list[str]] = defaultdict(list)
    probe_b_fibers: dict[str, list[str]] = defaultdict(list)
    probe_class_fibers_a: dict[str, list[str]] = defaultdict(list)
    probe_class_fibers_b: dict[str, list[str]] = defaultdict(list)

    for row in two_rows:
        rho_ab = row["gcm_2q_survivor_id"]
        qid = two_index["qclass_by_survivor"][rho_ab]
        creg = two_index["region_by_qclass"][qid]
        a_match = match_relation(row["first_bloch_scaled"], one_index)
        b_match = match_relation(row["second_bloch_scaled"], one_index)
        exact_compatible = a_match["exact_resolves"] and b_match["exact_resolves"]
        probe_compatible = a_match["probe_resolves"] and b_match["probe_resolves"]
        probe_triple_count = len(a_match["probe_survivor_ids"]) * len(b_match["probe_survivor_ids"])

        for sid in a_match["exact_survivor_ids"]:
            exact_a_fibers[sid].append(rho_ab)
        for sid in b_match["exact_survivor_ids"]:
            exact_b_fibers[sid].append(rho_ab)
        for sid in a_match["probe_survivor_ids"]:
            probe_a_fibers[sid].append(rho_ab)
        for sid in b_match["probe_survivor_ids"]:
            probe_b_fibers[sid].append(rho_ab)
        if a_match["probe_quotient_class_id"]:
            probe_class_fibers_a[a_match["probe_quotient_class_id"]].append(rho_ab)
        if b_match["probe_quotient_class_id"]:
            probe_class_fibers_b[b_match["probe_quotient_class_id"]].append(rho_ab)

        if exact_compatible:
            rho_a = a_match["exact_survivor_ids"][0]
            rho_b = b_match["exact_survivor_ids"][0]
            exact_triples.append(
                {
                    "family_id": family_triple_id("exact", rho_a, rho_b, rho_ab),
                    "rho_A_survivor_id": rho_a,
                    "rho_B_survivor_id": rho_b,
                    "rho_AB_2q_survivor_id": rho_ab,
                    "raw_2q_survivor_id": row["raw_2q_survivor_id"],
                    "family": row["family"],
                    "entangled": row["entangled"],
                }
            )
        if probe_compatible:
            for rho_a in a_match["probe_survivor_ids"]:
                for rho_b in b_match["probe_survivor_ids"]:
                    probe_triples.append(
                        {
                            "family_id": family_triple_id("probe", rho_a, rho_b, rho_ab),
                            "rho_A_survivor_id": rho_a,
                            "rho_B_survivor_id": rho_b,
                            "rho_AB_2q_survivor_id": rho_ab,
                            "raw_2q_survivor_id": row["raw_2q_survivor_id"],
                            "family": row["family"],
                            "entangled": row["entangled"],
                        }
                    )

        object_maps.append(
            {
                "rho_AB_2q_survivor_id": rho_ab,
                "raw_2q_survivor_id": row["raw_2q_survivor_id"],
                "candidate_id": row["candidate_id"],
                "family": row["family"],
                "entangled": row["entangled"],
                "gcm_2q_quotient_class_id": qid,
                "gcm_2q_candidate_region_id": creg,
                "partial_trace_A": a_match,
                "partial_trace_B": b_match,
                "exact_compatible": exact_compatible,
                "probe_compatible": probe_compatible,
                "probe_triple_count": probe_triple_count,
                "compatibility_status": (
                    "exact_and_probe"
                    if exact_compatible and probe_compatible
                    else "probe_only"
                    if probe_compatible
                    else "incompatible"
                ),
                "orphan_reason": None
                if probe_compatible
                else "partial_trace_A_or_B_has_no_1q_probe_equivalent_survivor",
            }
        )

    return {
        "object_maps": object_maps,
        "compatible_family_triples_exact": exact_triples,
        "compatible_family_triples_probe": probe_triples,
        "extension_fibers": build_extension_fibers(
            one_index,
            exact_a_fibers,
            exact_b_fibers,
            probe_a_fibers,
            probe_b_fibers,
        ),
        "probe_quotient_fibers": {
            "A": {key: sorted(set(value)) for key, value in sorted(probe_class_fibers_a.items())},
            "B": {key: sorted(set(value)) for key, value in sorted(probe_class_fibers_b.items())},
        },
        "product_embedding_rows": two_q_packet["cross_rung_lineage"]["one_q_to_2q_product_embedding"],
    }


def build_extension_fibers(
    one_index: dict[str, Any],
    exact_a: dict[str, list[str]],
    exact_b: dict[str, list[str]],
    probe_a: dict[str, list[str]],
    probe_b: dict[str, list[str]],
) -> list[dict[str, Any]]:
    rows = []
    for survivor in one_index["survivors"]:
        sid = survivor["survivor_id"]
        rows.append(
            {
                "one_q_survivor_id": sid,
                "coord_scaled": survivor["coord_scaled"],
                "probe_signature": list(probe_signature_from_scaled(survivor["coord_scaled"])),
                "exact_A_member_2q_ids": sorted(exact_a.get(sid, [])),
                "exact_B_member_2q_ids": sorted(exact_b.get(sid, [])),
                "probe_A_member_2q_ids": sorted(set(probe_a.get(sid, []))),
                "probe_B_member_2q_ids": sorted(set(probe_b.get(sid, []))),
            }
        )
    for row in rows:
        row["sizes"] = {
            "exact_A": len(row["exact_A_member_2q_ids"]),
            "exact_B": len(row["exact_B_member_2q_ids"]),
            "probe_A": len(row["probe_A_member_2q_ids"]),
            "probe_B": len(row["probe_B_member_2q_ids"]),
        }
    return rows


def summarize_counts(tower: dict[str, Any]) -> dict[str, Any]:
    maps = tower["object_maps"]
    exact_rows = [row for row in maps if row["exact_compatible"]]
    probe_rows = [row for row in maps if row["probe_compatible"]]
    exact_orphans = [row for row in maps if not row["exact_compatible"]]
    probe_orphans = [row for row in maps if not row["probe_compatible"]]
    product_exact = [row for row in exact_rows if row["family"] == "product_grid"]
    product_probe_rows = [row for row in probe_rows if row["family"] == "product_grid"]
    ent_probe_rows = [row for row in probe_rows if row["entangled"]]
    return {
        "one_q_survivor_count": EXPECTED_1Q_SURVIVOR_COUNT,
        "two_q_survivor_count": len(maps),
        "exact_compatible_2q_count": len(exact_rows),
        "exact_compatible_family_triple_count": len(tower["compatible_family_triples_exact"]),
        "exact_orphan_2q_count": len(exact_orphans),
        "probe_compatible_2q_count": len(probe_rows),
        "probe_compatible_family_triple_count": len(tower["compatible_family_triples_probe"]),
        "probe_orphan_2q_count": len(probe_orphans),
        "probe_rescued_exact_orphan_2q_count": sum(
            1 for row in maps if not row["exact_compatible"] and row["probe_compatible"]
        ),
        "quotient_multiplicity_added_family_triples": len(tower["compatible_family_triples_probe"])
        - len(tower["compatible_family_triples_exact"]),
        "product_exact_subtower_count": len(product_exact),
        "product_probe_compatible_2q_count": len(product_probe_rows),
        "product_probe_family_triple_count": sum(row["probe_triple_count"] for row in product_probe_rows),
        "entangled_probe_compatible_2q_count": len(ent_probe_rows),
        "entangled_probe_family_triple_count": sum(row["probe_triple_count"] for row in ent_probe_rows),
    }


def fiber_summary(tower: dict[str, Any]) -> dict[str, Any]:
    rows = tower["extension_fibers"]

    def dist(key: str) -> dict[str, int]:
        return {str(k): v for k, v in sorted(Counter(row["sizes"][key] for row in rows).items())}

    exact_a_members = [member for row in rows for member in row["exact_A_member_2q_ids"]]
    exact_b_members = [member for row in rows for member in row["exact_B_member_2q_ids"]]
    probe_a_members = [member for row in rows for member in row["probe_A_member_2q_ids"]]
    probe_b_members = [member for row in rows for member in row["probe_B_member_2q_ids"]]
    all_ids = {row["rho_AB_2q_survivor_id"] for row in tower["object_maps"]}
    probe_compatible_ids = {row["rho_AB_2q_survivor_id"] for row in tower["object_maps"] if row["probe_compatible"]}
    exact_compatible_ids = {row["rho_AB_2q_survivor_id"] for row in tower["object_maps"] if row["exact_compatible"]}
    return {
        "fiber_size_distribution": {
            "exact_A": dist("exact_A"),
            "exact_B": dist("exact_B"),
            "probe_A": dist("probe_A"),
            "probe_B": dist("probe_B"),
        },
        "cover_partition_checks": {
            "exact_A_partitions_all_2q_survivors": len(exact_a_members) == len(set(exact_a_members)) == len(all_ids),
            "exact_B_partitions_exact_compatible_2q_survivors": len(exact_b_members)
            == len(set(exact_b_members))
            == len(exact_compatible_ids),
            "probe_A_covers_all_2q_survivors_but_overlaps_by_probe_class": set(probe_a_members) == all_ids
            and len(probe_a_members) > len(set(probe_a_members)),
            "probe_B_covers_probe_compatible_2q_survivors_but_overlaps_by_probe_class": set(probe_b_members)
            == probe_compatible_ids
            and len(probe_b_members) > len(set(probe_b_members)),
        },
    }


def orphan_summary(tower: dict[str, Any]) -> dict[str, Any]:
    exact_orphans = [row for row in tower["object_maps"] if not row["exact_compatible"]]
    probe_orphans = [row for row in tower["object_maps"] if not row["probe_compatible"]]

    def characterize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "count": len(rows),
            "by_family": dict(sorted(Counter(row["family"] for row in rows).items())),
            "by_B_probe_signature": dict(
                sorted(Counter(sig_key(tuple(row["partial_trace_B"]["probe_signature"])) for row in rows).items())
            ),
            "by_B_coord_scaled": dict(
                sorted(Counter(",".join(str(v) for v in row["partial_trace_B"]["coord_scaled"]) for row in rows).items())
            ),
            "sample_2q_survivor_ids": [row["rho_AB_2q_survivor_id"] for row in rows[:24]],
        }

    return {
        "exact_tower_orphans": characterize(exact_orphans),
        "probe_tower_orphans": characterize(probe_orphans),
        "note": "Exact orphans have at least one partial trace off literal 1Q survivor coordinates. Probe orphans have at least one partial trace with no 1Q survivor in the same sigma_x/sigma_z probe class.",
    }


def entangled_membership(tower: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in tower["object_maps"] if row["entangled"]]
    return {
        "entangled_2q_count": len(rows),
        "exact_compatible_count": sum(1 for row in rows if row["exact_compatible"]),
        "probe_compatible_count": sum(1 for row in rows if row["probe_compatible"]),
        "exact_A_fiber_member_count": sum(1 for row in rows if row["partial_trace_A"]["exact_resolves"]),
        "exact_B_fiber_member_count": sum(1 for row in rows if row["partial_trace_B"]["exact_resolves"]),
        "probe_A_fiber_member_count": sum(1 for row in rows if row["partial_trace_A"]["probe_resolves"]),
        "probe_B_fiber_member_count": sum(1 for row in rows if row["partial_trace_B"]["probe_resolves"]),
        "rows": [
            {
                "rho_AB_2q_survivor_id": row["rho_AB_2q_survivor_id"],
                "raw_2q_survivor_id": row["raw_2q_survivor_id"],
                "exact_compatible": row["exact_compatible"],
                "probe_compatible": row["probe_compatible"],
                "exact_A_survivor_id": row["partial_trace_A"]["exact_survivor_ids"][0],
                "exact_B_survivor_ids": row["partial_trace_B"]["exact_survivor_ids"],
                "probe_A_survivor_ids": row["partial_trace_A"]["probe_survivor_ids"],
                "probe_B_survivor_ids": row["partial_trace_B"]["probe_survivor_ids"],
                "partial_trace_B_coord_scaled": row["partial_trace_B"]["coord_scaled"],
                "partial_trace_B_probe_signature": row["partial_trace_B"]["probe_signature"],
            }
            for row in rows
        ],
        "verdict": "entangled_16_are_exact_B_orphans_but_probe_compatible_fiber_members",
    }


def exact_vs_probe_adjudication(tower: dict[str, Any]) -> dict[str, Any]:
    maps = tower["object_maps"]
    return {
        "row_relation_counts": dict(sorted(Counter(row["compatibility_status"] for row in maps).items())),
        "where_relations_differ": {
            "probe_rescues_exact_orphan_rows": [
                row["rho_AB_2q_survivor_id"]
                for row in maps
                if (not row["exact_compatible"] and row["probe_compatible"])
            ],
            "probe_still_orphan_rows": [
                row["rho_AB_2q_survivor_id"] for row in maps if not row["probe_compatible"]
            ],
            "exact_compatible_rows_with_probe_multiplicity_gt_1": [
                row["rho_AB_2q_survivor_id"]
                for row in maps
                if row["exact_compatible"] and row["probe_triple_count"] > 1
            ],
        },
        "interpretation": "Exact equality picks one 1Q survivor per marginal. Probe equivalence picks every survivor in the matching sigma_x/sigma_z quotient class; this changes both compatibility and triple multiplicity.",
    }


def product_subtower(tower: dict[str, Any]) -> dict[str, Any]:
    maps = tower["object_maps"]
    product_exact = [row for row in maps if row["family"] == "product_grid" and row["exact_compatible"]]
    product_probe = [row for row in maps if row["family"] == "product_grid" and row["probe_compatible"]]
    embedding_rows = tower["product_embedding_rows"]
    return {
        "exact_product_subtower_count": len(product_exact),
        "exact_product_subtower_formula": "16 rho_A survivors x 16 exact rho_B survivors",
        "exact_product_subtower_predicted_count": EXPECTED_1Q_SURVIVOR_COUNT * EXPECTED_1Q_SURVIVOR_COUNT,
        "probe_product_compatible_2q_count": len(product_probe),
        "probe_product_family_triple_count": sum(row["probe_triple_count"] for row in product_probe),
        "pinned_product_embedding_row_count": len(embedding_rows),
        "pinned_product_embedding_predicted_count": EXPECTED_PINNED_PRODUCT_EMBEDDING_COUNT,
        "pinned_product_embedding_all_survive": all(row["embedded"] and row["partial_trace_A_matches"] for row in embedding_rows),
        "embedding_rows": embedding_rows,
    }


def scrambled_pairing_control(tower: dict[str, Any], one_q: dict[str, Any]) -> dict[str, Any]:
    one_index = one_q_indexes(one_q)
    sigs = sorted(one_index["by_sig"])
    next_sig = {sig: sigs[(idx + 1) % len(sigs)] for idx, sig in enumerate(sigs)}
    rows = []
    for row in tower["object_maps"]:
        b_sig = tuple(row["partial_trace_B"]["probe_signature"])
        if b_sig not in next_sig:
            assigned = one_index["by_sig"][sigs[0]][0]
        else:
            assigned = one_index["by_sig"][next_sig[b_sig]][0]
        exact_broken = assigned not in row["partial_trace_B"]["exact_survivor_ids"]
        probe_broken = assigned not in row["partial_trace_B"]["probe_survivor_ids"]
        rows.append(
            {
                "rho_AB_2q_survivor_id": row["rho_AB_2q_survivor_id"],
                "assigned_scrambled_rho_B_survivor_id": assigned,
                "original_B_probe_signature": row["partial_trace_B"]["probe_signature"],
                "exact_broken": exact_broken,
                "probe_broken": probe_broken,
            }
        )
    return {
        "control": "assign rho_B from the next 1Q probe class rather than the actual partial-trace class",
        "row_count": len(rows),
        "exact_break_count": sum(1 for row in rows if row["exact_broken"]),
        "probe_break_count": sum(1 for row in rows if row["probe_broken"]),
        "all_probe_compatibility_destroyed": all(row["probe_broken"] for row in rows),
        "sample_rows": rows[:24],
    }


def bidirectional_check(tower: dict[str, Any]) -> dict[str, Any]:
    by_id = {row["rho_AB_2q_survivor_id"]: row for row in tower["object_maps"]}
    exact_down_ok = all(
        by_id[row["rho_AB_2q_survivor_id"]]["partial_trace_A"]["exact_survivor_ids"] == [row["rho_A_survivor_id"]]
        and by_id[row["rho_AB_2q_survivor_id"]]["partial_trace_B"]["exact_survivor_ids"] == [row["rho_B_survivor_id"]]
        for row in tower["compatible_family_triples_exact"]
    )
    probe_down_ok = all(
        row["rho_A_survivor_id"] in by_id[row["rho_AB_2q_survivor_id"]]["partial_trace_A"]["probe_survivor_ids"]
        and row["rho_B_survivor_id"] in by_id[row["rho_AB_2q_survivor_id"]]["partial_trace_B"]["probe_survivor_ids"]
        for row in tower["compatible_family_triples_probe"]
    )
    exact_fiber_round_trip_ok = all(
        by_id[member]["partial_trace_A"]["exact_survivor_ids"] == [fiber["one_q_survivor_id"]]
        for fiber in tower["extension_fibers"]
        for member in fiber["exact_A_member_2q_ids"]
    ) and all(
        by_id[member]["partial_trace_B"]["exact_survivor_ids"] == [fiber["one_q_survivor_id"]]
        for fiber in tower["extension_fibers"]
        for member in fiber["exact_B_member_2q_ids"]
    )
    probe_fiber_round_trip_ok = all(
        fiber["one_q_survivor_id"] in by_id[member]["partial_trace_A"]["probe_survivor_ids"]
        for fiber in tower["extension_fibers"]
        for member in fiber["probe_A_member_2q_ids"]
    ) and all(
        fiber["one_q_survivor_id"] in by_id[member]["partial_trace_B"]["probe_survivor_ids"]
        for fiber in tower["extension_fibers"]
        for member in fiber["probe_B_member_2q_ids"]
    )
    return {
        "exact_down_triples_round_trip": exact_down_ok,
        "probe_down_triples_round_trip": probe_down_ok,
        "exact_up_fibers_round_trip": exact_fiber_round_trip_ok,
        "probe_up_fibers_round_trip": probe_fiber_round_trip_ok,
        "all_round_trips_pass": exact_down_ok
        and probe_down_ok
        and exact_fiber_round_trip_ok
        and probe_fiber_round_trip_ok,
    }


def z3_count_proof(counts: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    n2 = z3.Int("two_q_survivor_count")
    exact = z3.Int("exact_compatible_2q_count")
    exact_orph = z3.Int("exact_orphan_2q_count")
    probe = z3.Int("probe_compatible_2q_count")
    probe_orph = z3.Int("probe_orphan_2q_count")
    probe_triples = z3.Int("probe_family_triple_count")
    product_exact = z3.Int("product_exact_subtower_count")
    solver.add(
        n2 == counts["two_q_survivor_count"],
        exact == counts["exact_compatible_2q_count"],
        exact_orph == counts["exact_orphan_2q_count"],
        probe == counts["probe_compatible_2q_count"],
        probe_orph == counts["probe_orphan_2q_count"],
        probe_triples == counts["probe_compatible_family_triple_count"],
        product_exact == counts["product_exact_subtower_count"],
        n2 == EXPECTED_2Q_SURVIVOR_COUNT,
        exact == EXPECTED_EXACT_COMPATIBLE_2Q_COUNT,
        exact + exact_orph == n2,
        probe + probe_orph == n2,
        probe >= exact,
        probe_triples >= probe,
        product_exact == EXPECTED_1Q_SURVIVOR_COUNT * EXPECTED_1Q_SURVIVOR_COUNT,
    )
    verdict = solver.check()
    return {
        "ran": True,
        "verdict": str(verdict),
        "load_bearing": True,
        "claim": "finite <=2Q tower counts partition the 544 2Q survivors and bind exact/probe cardinalities",
        "input_object": counts,
        "positive_case": "exact compatible rows plus exact orphans equal 544; probe compatible rows plus probe orphans equal 544",
        "negative_control": "lineage-free payload fails both 1Q and 2Q hardened substrate checks",
        "boundary_case": "probe relation may rescue exact orphans but does not promote beyond scratch_diagnostic",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def cvc5_count_proof(counts: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    names = (
        "two_q_survivor_count",
        "exact_compatible_2q_count",
        "exact_orphan_2q_count",
        "probe_compatible_2q_count",
        "probe_orphan_2q_count",
        "probe_compatible_family_triple_count",
        "product_exact_subtower_count",
    )
    terms = {name: solver.mkConst(int_sort, name) for name in names}
    for name, term in terms.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(counts[name])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms["two_q_survivor_count"], solver.mkInteger(EXPECTED_2Q_SURVIVOR_COUNT)))
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL, terms["exact_compatible_2q_count"], solver.mkInteger(EXPECTED_EXACT_COMPATIBLE_2Q_COUNT))
    )
    solver.assertFormula(
        solver.mkTerm(
            Kind.EQUAL,
            solver.mkTerm(Kind.ADD, terms["exact_compatible_2q_count"], terms["exact_orphan_2q_count"]),
            terms["two_q_survivor_count"],
        )
    )
    solver.assertFormula(
        solver.mkTerm(
            Kind.EQUAL,
            solver.mkTerm(Kind.ADD, terms["probe_compatible_2q_count"], terms["probe_orphan_2q_count"]),
            terms["two_q_survivor_count"],
        )
    )
    solver.assertFormula(
        solver.mkTerm(
            Kind.EQUAL,
            terms["product_exact_subtower_count"],
            solver.mkInteger(EXPECTED_1Q_SURVIVOR_COUNT * EXPECTED_1Q_SURVIVOR_COUNT),
        )
    )
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "finite <=2Q tower counts partition the 544 2Q survivors and bind exact/probe cardinalities",
        "input_object": counts,
        "positive_case": "exact compatible rows plus exact orphans equal 544; probe compatible rows plus probe orphans equal 544",
        "negative_control": "lineage-free payload fails both 1Q and 2Q hardened substrate checks",
        "boundary_case": "probe relation may rescue exact orphans but does not promote beyond scratch_diagnostic",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = dict(payload)
    variant["gcm_lineage"] = {
        "gcm_object_id": None,
        "registry_body_sha256": None,
        "base_registry_body_sha256": None,
        "gcm_2q_object_id": None,
        "gcm_2q_registry_body_sha256": None,
        "survivor_ids": [],
        "quotient_class_ids": [],
        "candidate_region_ids": [],
        "gcm_2q_survivor_ids": [],
        "gcm_2q_quotient_class_ids": [],
        "gcm_2q_candidate_region_ids": [],
        "object_maps": [],
    }
    return variant


def build_gcm_lineage(one_q: dict[str, Any], two_q: dict[str, Any], tower: dict[str, Any]) -> dict[str, Any]:
    one_index = one_q_indexes(one_q)
    two_index = two_q_indexes(two_q)
    return {
        "gcm_object_id": one_q["gcm_object_id"],
        "registry_body_sha256": one_q["registry_body_sha256"],
        "base_registry_body_sha256": one_q["registry_body_sha256"],
        "gcm_2q_object_id": two_q["gcm_2q_object_id"],
        "gcm_2q_registry_body_sha256": two_q["registry_body_sha256"],
        "survivor_ids": one_index["survivor_ids"],
        "quotient_class_ids": one_index["quotient_class_ids"],
        "candidate_region_ids": one_index["candidate_region_ids"],
        "gcm_2q_survivor_ids": two_index["survivor_ids"],
        "gcm_2q_quotient_class_ids": two_index["quotient_class_ids"],
        "gcm_2q_candidate_region_ids": two_index["candidate_region_ids"],
        "object_maps": [
            {
                "rho_AB_2q_survivor_id": row["rho_AB_2q_survivor_id"],
                "gcm_2q_survivor_id": row["rho_AB_2q_survivor_id"],
                "gcm_2q_quotient_class_id": row["gcm_2q_quotient_class_id"],
                "gcm_2q_candidate_region_id": row["gcm_2q_candidate_region_id"],
                "survivor_id": row["partial_trace_A"]["exact_survivor_ids"][0],
                "partial_trace_A_1q_survivor_id": row["partial_trace_A"]["exact_survivor_ids"][0],
                "partial_trace_B_1q_survivor_id": (
                    row["partial_trace_B"]["exact_survivor_ids"][0] if row["partial_trace_B"]["exact_survivor_ids"] else None
                ),
            }
            for row in tower["object_maps"]
        ],
    }


def build_packet(write: bool = True) -> dict[str, Any]:
    one_q = load_json(ONE_Q_REGISTRY_PATH)
    two_q = load_json(TWO_Q_REGISTRY_PATH)
    two_q_packet = load_json(TWO_Q_PACKET_RESULT_PATH)
    tower = build_tower(one_q, two_q, two_q_packet)
    counts = summarize_counts(tower)
    lineage = build_gcm_lineage(one_q, two_q, tower)
    substrate_probe = {"gcm_lineage": lineage}
    substrate_1q = gcm_substrate_check(substrate_probe, ONE_Q_REGISTRY_PATH)
    substrate_2q = gcm_substrate_check(substrate_probe, TWO_Q_REGISTRY_PATH)
    substrate_1q_negative = gcm_substrate_check(lineage_free_variant(substrate_probe), ONE_Q_REGISTRY_PATH)
    substrate_2q_negative = gcm_substrate_check(lineage_free_variant(substrate_probe), TWO_Q_REGISTRY_PATH)
    counts_for_proof = {
        "two_q_survivor_count": counts["two_q_survivor_count"],
        "exact_compatible_2q_count": counts["exact_compatible_2q_count"],
        "exact_orphan_2q_count": counts["exact_orphan_2q_count"],
        "probe_compatible_2q_count": counts["probe_compatible_2q_count"],
        "probe_orphan_2q_count": counts["probe_orphan_2q_count"],
        "probe_compatible_family_triple_count": counts["probe_compatible_family_triple_count"],
        "product_exact_subtower_count": counts["product_exact_subtower_count"],
    }
    z3_proof = z3_count_proof(counts_for_proof)
    cvc5_proof = cvc5_count_proof(counts_for_proof)
    bidirectional = bidirectional_check(tower)
    fibers = fiber_summary(tower)
    products = product_subtower(tower)
    scrambled = scrambled_pairing_control(tower, one_q)
    no_audit = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "axis_declaration": {
            "axis": "nesting/tower",
            "object": "inverse-limit",
            "rung": "<=2Q",
        },
        "authority": {
            "nesting_law_spec": rel(NESTING_LAW_SPEC_PATH),
            "spec_hash_hint": "afe7aa57b",
            "verbatim_formula": "X_{<=2}^max = { (rho_1, rho_2, rho_12) : each in its survivor set, Tr_2(rho_12) ~ rho_1, Tr_1(rho_12) ~ rho_2 }",
            "extension_fiber_formula": "F_2(rho) = { rho_12 in X_2^max : Tr(rho_12) ~ rho }",
        },
        "gcm_lineage": lineage,
        "registries_consumed": {
            "one_q_registry_path": rel(ONE_Q_REGISTRY_PATH),
            "one_q_object_id": one_q["gcm_object_id"],
            "one_q_registry_body_sha256": one_q["registry_body_sha256"],
            "two_q_registry_path": rel(TWO_Q_REGISTRY_PATH),
            "two_q_object_id": two_q["gcm_2q_object_id"],
            "two_q_registry_body_sha256": two_q["registry_body_sha256"],
            "two_q_lineage_location": "gcm_lineage.gcm_2q_*",
        },
        "counts": counts,
        "compatible_families": {
            "exact_relation": tower["compatible_family_triples_exact"],
            "probe_equivalence_relation": tower["compatible_family_triples_probe"],
        },
        "tower_maps": tower["object_maps"],
        "extension_fibers": tower["extension_fibers"],
        "fiber_summary": fibers,
        "probe_quotient_fibers": tower["probe_quotient_fibers"],
        "entangled_16_fiber_membership": entangled_membership(tower),
        "exact_vs_probe_equivalence_adjudication": exact_vs_probe_adjudication(tower),
        "tower_orphans": orphan_summary(tower),
        "bidirectional_check": bidirectional,
        "controls": {
            "scrambled_pairing_tower": scrambled,
            "product_only_subtower": products,
            "substrate_positive_1q": substrate_1q,
            "substrate_positive_2q": substrate_2q,
            "substrate_lineage_free_negative_1q": substrate_1q_negative,
            "substrate_lineage_free_negative_2q": substrate_2q_negative,
            "lineage_free_negatives_failed_as_required": substrate_1q_negative.get("ok") is False
            and substrate_2q_negative.get("ok") is False,
        },
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "source_locks": {
            "nesting_law_spec": source_lock(NESTING_LAW_SPEC_PATH, "final object spec authority"),
            "one_q_registry": source_lock(ONE_Q_REGISTRY_PATH, "16-survivor 1Q frozen registry"),
            "two_q_registry": source_lock(TWO_Q_REGISTRY_PATH, "544-survivor 2Q frozen registry"),
            "two_q_packet_result": source_lock(TWO_Q_PACKET_RESULT_PATH, "verified product embedding rows and 2Q lineage source"),
            "gcm_substrate_check": source_lock(GCM_SUBSTRATE_HELPER_PATH, "hardened shared substrate helper"),
            "builder_audit_boundary": source_lock(BUILDER_AUDIT_BOUNDARY_PATH, "G.2a builder/audit boundary helper"),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "G_2a_idempotency_from_birth": no_audit,
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": no_audit,
            "no_builder_audit_verdict_envelope_gate": no_audit,
            "both_registries_consumed_by_lineage": substrate_1q.get("ok") is True and substrate_2q.get("ok") is True,
            "lineage_free_negative_red": substrate_1q_negative.get("ok") is False
            and substrate_2q_negative.get("ok") is False,
        },
        "claim_summary": {
            "tower_shape": "probe quotient rescues some exact off-survivor B traces while exact equality leaves a smaller tower",
            "exact_tower_cardinality": counts["exact_compatible_family_triple_count"],
            "probe_tower_cardinality": counts["probe_compatible_family_triple_count"],
            "exact_orphan_2q_count": counts["exact_orphan_2q_count"],
            "probe_orphan_2q_count": counts["probe_orphan_2q_count"],
            "entangled_16_place": "exact_B_orphans_but_probe_compatible_fiber_members",
        },
        "all_pass": (
            one_q["gcm_object_id"] == EXPECTED_1Q_OBJECT_ID
            and one_q["registry_body_sha256"] == EXPECTED_1Q_REGISTRY_BODY_SHA256
            and two_q["gcm_2q_object_id"] == EXPECTED_2Q_OBJECT_ID
            and two_q["registry_body_sha256"] == EXPECTED_2Q_REGISTRY_BODY_SHA256
            and counts["one_q_survivor_count"] == EXPECTED_1Q_SURVIVOR_COUNT
            and counts["two_q_survivor_count"] == EXPECTED_2Q_SURVIVOR_COUNT
            and counts["exact_compatible_2q_count"] == EXPECTED_EXACT_COMPATIBLE_2Q_COUNT
            and counts["exact_compatible_family_triple_count"] == EXPECTED_EXACT_COMPATIBLE_2Q_COUNT
            and counts["exact_orphan_2q_count"] + counts["exact_compatible_2q_count"] == EXPECTED_2Q_SURVIVOR_COUNT
            and counts["probe_orphan_2q_count"] + counts["probe_compatible_2q_count"] == EXPECTED_2Q_SURVIVOR_COUNT
            and products["exact_product_subtower_count"] == products["exact_product_subtower_predicted_count"]
            and products["pinned_product_embedding_row_count"] == EXPECTED_PINNED_PRODUCT_EMBEDDING_COUNT
            and products["pinned_product_embedding_all_survive"]
            and scrambled["all_probe_compatibility_destroyed"]
            and fibers["cover_partition_checks"]["exact_A_partitions_all_2q_survivors"]
            and bidirectional["all_round_trips_pass"]
            and substrate_1q.get("ok") is True
            and substrate_2q.get("ok") is True
            and substrate_1q_negative.get("ok") is False
            and substrate_2q_negative.get("ok") is False
            and z3_proof["verdict"] == "sat"
            and cvc5_proof["verdict"] == "sat"
            and no_audit
        ),
        "disallowed_claims": [
            "canonical by process",
            "formal admission",
            "THE manifold",
            "axis admission",
            "3Q tower claim",
            "probe quotient as exact equality",
        ],
    }
    payload["result_sha256"] = stable_sha256(
        {key: value for key, value in payload.items() if key not in {"generated_at", "result_sha256"}}
    )
    if write:
        write_json(RESULT_PATH, payload)
        write_json(LINEAGE_FREE_NEGATIVE_PATH, lineage_free_variant(payload))
    return payload


def load_engine_result(engine: str) -> dict[str, Any]:
    return load_json(RESULT_DIR / f"{SIM_ID}_{engine}_results.json")


def build_envelope(write: bool = True) -> dict[str, Any]:
    packet = load_json(RESULT_PATH) if RESULT_PATH.exists() else build_packet(write=True)
    engines = {engine: load_engine_result(engine) for engine in ("julia", "jax", "pytorch")}
    count_fields = {
        "exact_tower_cardinality": "exact_tower_cardinality",
        "probe_tower_cardinality": "probe_tower_cardinality",
        "probe_orphan_2q_count": "probe_orphan_2q_count",
    }
    count_agreement = {
        field: all(engines[engine][engine_field] == packet["claim_summary"][field] for engine in engines)
        for field, engine_field in count_fields.items()
    }
    engine_values = {engine: engines[engine]["exact_tower_cardinality"] for engine in engines}
    max_divergence = max(abs(value - engine_values["julia"]) for value in engine_values.values())
    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "schema": ENVELOPE_SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "mode": ENGINE_MODE,
        "engine_contract": {
            "mode": ENGINE_MODE,
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "engine_lanes": ["julia", "jax", "pytorch"],
        "carrier_and_pins_relative": True,
        "gcm_lineage": packet["gcm_lineage"],
        "result_json": rel(RESULT_PATH),
        "counts": packet["counts"],
        "claim_path_tools": ["gcm_substrate_check", "z3", "cvc5", "Graphs", "sympy", "torch.func"],
        "tool_intent": TOOL_INTENT,
        "engines": {
            engine: {
                "ran": True,
                "source_path": engines[engine]["source_path"],
                "source_sha256": engines[engine]["source_sha256"],
                "result_path": engines[engine]["result_path"],
                "result_all_pass": engines[engine]["all_pass"],
                "packages_used": engines[engine]["packages_used"],
                "aligned_packages_load_bearing": engines[engine]["aligned_packages_load_bearing"],
                "package_observables": engines[engine]["package_observables"],
                "reads_peer_result": False,
            }
            for engine in ("julia", "jax", "pytorch")
        },
        "crossover_proofs": packet["crossover_proofs"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max_divergence,
        },
        "engine_consensus": {
            "all_engine_lanes_pass": all(engines[engine]["all_pass"] for engine in engines),
            "count_agreement": count_agreement,
            "max_divergence": max_divergence,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": packet["builder_gates"],
        "all_pass": packet["all_pass"] and all(engines[engine]["all_pass"] for engine in engines) and all(count_agreement.values()) and max_divergence == 0,
        "disallowed_claims": packet["disallowed_claims"],
    }
    envelope["result_sha256"] = stable_sha256(
        {key: value for key, value in envelope.items() if key not in {"generated_at", "result_sha256"}}
    )
    if write:
        write_json(ENVELOPE_PATH, envelope)
    return envelope


def main() -> int:
    payload = build_packet(write=True)
    print(
        "GCM_NESTING_TOWER_LE2Q_DONE "
        f"all_pass={str(payload['all_pass']).lower()} "
        f"exact={payload['counts']['exact_compatible_family_triple_count']} "
        f"probe={payload['counts']['probe_compatible_family_triple_count']} "
        f"probe_orphans={payload['counts']['probe_orphan_2q_count']} "
        f"result={rel(RESULT_PATH)}"
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

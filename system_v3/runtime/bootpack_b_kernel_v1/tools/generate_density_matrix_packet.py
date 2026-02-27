#!/usr/bin/env python3
"""
Generate a single A1_TO_A0_STRATEGY_ZIP packet that ratchets concrete QIT-aligned
terms (e.g. density_matrix) without introducing FORMULA/equality primitives.

This is an A1-side artifact generator (high entropy), but it emits strict
A1_STRATEGY_v1 JSON and uses ZIP_PROTOCOL_v2 capsules for transport.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from zip_protocol_v2_writer import write_zip_protocol_v2  # noqa: E402


FORBIDDEN_FIELDS = ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _df(field_id: str, name: str, value: str, *, kind: str = "TOKEN") -> dict:
    return {"field_id": field_id, "name": name, "value_kind": kind, "value": value}


def _assert(assert_id: str, token_class: str, token: str) -> dict:
    return {"assert_id": assert_id, "token_class": token_class, "token": token}


def build_density_matrix_strategy(*, run_id: str, sequence: int) -> dict:
    sim_stub_path = BASE / "SIM_STUB_QIT_v1.txt"
    sim_code_hash = _sha256_file(sim_stub_path)

    # Concrete ladder: MATH_DEF -> TERM_DEF -> CANON_PERMIT, plus SIM_SPEC that emits
    # the evidence token needed to canonize the term in term_registry.
    #
    # No FORMULA used; no equals_sign attempts.
    math_id = "S_MATH_DENSITY_MATRIX_V1"
    term_id = "S_TERM_DENSITY_MATRIX_V1"
    permit_id = "S_CANON_DENSITY_MATRIX_V1"
    sim_pos_id = "S_SIM_CANON_DENSITY_MATRIX_V1"

    # Adversarial negative alternative: explicitly declares commutative assumption.
    math_alt_comm_id = "S_MATH_DENSITY_MATRIX_COMMUTATIVE_ALT_V1"
    sim_neg_comm_id = "S_SIM_KILL_COMMUTATIVE_ALT_V1"

    evidence_token_density = "E_CANON_DENSITY_MATRIX"
    evidence_token_neg = "E_NEG_COMMUTATIVE_ALT"

    base_inputs = {
        "state_hash": "0" * 64,
        "fuel_slice_hashes": [],
        "bootpack_rules_hash": "0" * 64,
        "pinned_ruleset_sha256": None,
        "pinned_megaboot_sha256": None,
    }

    # NOTE: bootpack kernel enforces PROBE_PRESSURE (BR-009): at least 1 PROBE_HYP
    # per 10 accepted SPEC_HYP items. Since A1_STRATEGY_v1 only admits SPEC_HYP,
    # we satisfy probe pressure by having A0 emit a shared PROBE_HYP from a shared
    # P_* dependency present on every candidate.
    probe_id = "P_DENSITY_MATRIX_FOUNDATION_V1"
    probe_token = "PT_DENSITY_MATRIX_FOUNDATION_V1"

    strategy = {
        "schema": "A1_STRATEGY_v1",
        "strategy_id": f"STRAT_DENSITY_MATRIX_S{sequence:04d}",
        "inputs": base_inputs,
        "budget": {"max_items": 32, "max_sims": 8},
        "policy": {
            "forbid_fields": list(FORBIDDEN_FIELDS),
            "overlay_ban_terms": [],
            "require_try_to_fail": True,
        },
        "targets": [
            {
                "item_class": "SPEC_HYP",
                "id": math_id,
                "kind": "MATH_DEF",
                "requires": [probe_id],
                "def_fields": [
                    _df("F_OBJ", "OBJECTS", "finite_dimensional_hilbert_space density_matrix"),
                    _df("F_OPS", "OPERATIONS", "partial_trace tensor cptp_channel unitary"),
                    _df("F_INV", "INVARIANTS", "trace"),
                    _df("F_DOM", "DOMAIN", "finite_dimensional_hilbert_space"),
                    _df("F_COD", "CODOMAIN", "density_matrix"),
                    _df("F_SIM", "SIM_CODE_HASH_SHA256", sim_code_hash),
                    _df("F_TRACK", "BRANCH_TRACK", "DENSITY_MATRIX_FOUNDATION"),
                ],
                "asserts": [
                    _assert("A_MATH", "MATH_TOKEN", "MT_DENSITY_MATRIX_V1"),
                    _assert("A_PROBE", "PROBE_TOKEN", probe_token),
                ],
                "operator_id": "OP_BIND_SIM",
            },
            {
                "item_class": "SPEC_HYP",
                "id": term_id,
                "kind": "TERM_DEF",
                "requires": [math_id],
                "def_fields": [
                    _df("F_TERM", "TERM", "density_matrix", kind="TERM_QUOTED"),
                    _df("F_BINDS", "BINDS", math_id),
                ],
                "asserts": [_assert("A_TERM", "TERM_TOKEN", "TT_DENSITY_MATRIX_V1")],
                "operator_id": "OP_REPAIR_DEF_FIELD",
            },
            {
                "item_class": "SPEC_HYP",
                "id": permit_id,
                "kind": "CANON_PERMIT",
                "requires": [term_id],
                "def_fields": [
                    _df("F_TERM", "TERM", "density_matrix", kind="TERM_QUOTED"),
                    _df("F_EVID", "REQUIRES_EVIDENCE", evidence_token_density),
                ],
                "asserts": [_assert("A_PERMIT", "PERMIT_TOKEN", "PT_CANON_DENSITY_MATRIX_V1")],
                "operator_id": "OP_REPAIR_DEF_FIELD",
            },
            {
                "item_class": "SPEC_HYP",
                "id": sim_pos_id,
                "kind": "SIM_SPEC",
                "requires": [probe_id],
                "def_fields": [
                    _df("F_EVID", "REQUIRES_EVIDENCE", evidence_token_density),
                    _df("F_SIMID", "SIM_ID", sim_pos_id),
                    _df("F_TIER", "TIER", "T0_ATOM"),
                    _df("F_FAM", "FAMILY", "BASELINE"),
                    _df("F_TC", "TARGET_CLASS", "TC_DENSITY_MATRIX_FOUNDATION"),
                    _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                ],
                "asserts": [
                    _assert("A_EVID", "EVIDENCE_TOKEN", evidence_token_density),
                    _assert("A_PROBE", "PROBE_TOKEN", probe_token),
                ],
                "operator_id": "OP_BIND_SIM",
            },
        ],
        "alternatives": [
            {
                "item_class": "SPEC_HYP",
                "id": math_alt_comm_id,
                "kind": "MATH_DEF",
                "requires": [math_id],
                "def_fields": [
                    _df("F_OBJ", "OBJECTS", "finite_dimensional_hilbert_space density_matrix"),
                    _df("F_OPS", "OPERATIONS", "partial_trace tensor cptp_channel"),
                    _df("F_INV", "INVARIANTS", "trace"),
                    _df("F_DOM", "DOMAIN", "finite_dimensional_hilbert_space"),
                    _df("F_COD", "CODOMAIN", "density_matrix"),
                    _df("F_SIM", "SIM_CODE_HASH_SHA256", sim_code_hash),
                    _df("F_NEG", "NEGATIVE_CLASS", "COMMUTATIVE_ASSUMPTION"),
                    # Bind the kernel kill condition for this alt to the negative SIM spec.
                    # Without this, kernel would require sim_id == target_id to execute KILL_IF.
                    _df("F_KB", "KILL_BIND", sim_neg_comm_id),
                    _df("F_MARK1", "ASSUME_COMMUTATIVE", "TRUE"),
                    _df("F_MARK2", "COMMUTATIVE_ASSUMPTION", "TRUE"),
                    _df("F_TRACK", "BRANCH_TRACK", "DENSITY_MATRIX_COMMUTATIVE_ALT"),
                ],
                "asserts": [_assert("A_MATH", "MATH_TOKEN", "MT_DENSITY_MATRIX_COMM_ALT_V1")],
                "operator_id": "OP_NEG_SIM_EXPAND",
            },
            {
                "item_class": "SPEC_HYP",
                "id": sim_neg_comm_id,
                "kind": "SIM_SPEC",
                "requires": [probe_id],
                "def_fields": [
                    _df("F_EVID", "REQUIRES_EVIDENCE", evidence_token_neg),
                    _df("F_SIMID", "SIM_ID", sim_neg_comm_id),
                    _df("F_TIER", "TIER", "T1_COMPOUND"),
                    _df("F_FAM", "FAMILY", "ADVERSARIAL_NEG"),
                    _df("F_TC", "TARGET_CLASS", "TC_DENSITY_MATRIX_FOUNDATION"),
                    _df("F_NEG", "NEGATIVE_CLASS", "COMMUTATIVE_ASSUMPTION"),
                    _df("F_DEP", "DEPENDS_ON", math_alt_comm_id),
                    _df("F_KT", "KILL_TARGET", math_alt_comm_id),
                    _df("F_PK", "PROBE_KIND", "A1_GENERATED"),
                ],
                "asserts": [
                    _assert("A_EVID", "EVIDENCE_TOKEN", evidence_token_neg),
                    _assert("A_PROBE", "PROBE_TOKEN", probe_token),
                ],
                "operator_id": "OP_NEG_SIM_EXPAND",
            },
        ],
        "sims": {
            "positive": [{"sim_id": "SIM_POS_DENSITY_MATRIX", "binds_to": sim_pos_id}],
            "negative": [{"sim_id": "SIM_NEG_COMMUTATIVE_ALT", "binds_to": sim_neg_comm_id}],
        },
        "self_audit": {
            "strategy_hash": "",
            "compile_lane_digest": "",
            "candidate_count": 4,
            "alternative_count": 2,
            "operator_ids_used": sorted(
                {
                    "OP_BIND_SIM",
                    "OP_REPAIR_DEF_FIELD",
                    "OP_NEG_SIM_EXPAND",
                }
            ),
        },
    }

    # The runtime fills strategy_hash during replay/ollama, but packet mode expects
    # A1 to provide a fully-valid strategy already. Keep it deterministic here.
    encoded = json.dumps(strategy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    strategy["self_audit"]["strategy_hash"] = hashlib.sha256(encoded).hexdigest()
    return strategy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output zip path")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sequence", type=int, required=True)
    args = parser.parse_args()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    strategy = build_density_matrix_strategy(run_id=str(args.run_id), sequence=int(args.sequence))
    write_zip_protocol_v2(
        out_path=out_path,
        header={
            "zip_type": "A1_TO_A0_STRATEGY_ZIP",
            "direction": "FORWARD",
            "source_layer": "A1",
            "target_layer": "A0",
            "run_id": str(args.run_id),
            "sequence": int(args.sequence),
            "created_utc": "1970-01-01T00:00:00Z",
            "compiler_version": "",
        },
        payload_json={"A1_STRATEGY_v1.json": strategy},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

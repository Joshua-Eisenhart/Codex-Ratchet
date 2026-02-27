#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RUNS_ROOT = BASE.parents[1] / "runs"
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from zip_protocol_v2_writer import write_zip_protocol_v2


FORBIDDEN_FIELDS = ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"]
L0_TERMS = [
    "finite",
    "dimensional",
    "hilbert",
    "space",
    "density",
    "matrix",
    "operator",
    "channel",
    "cptp",
    "unitary",
    "lindblad",
    "hamiltonian",
    "commutator",
    "anticommutator",
    "trace",
    "partial",
    "tensor",
    "superoperator",
    "generator",
]


def _next_unique(corpus: list[str], used: set[str], start_index: int) -> tuple[str, int]:
    idx = start_index
    while idx < len(corpus):
        term = corpus[idx]
        idx += 1
        if term in used:
            continue
        used.add(term)
        return term, idx
    return "", idx


def _fallback_atomic_term(used: set[str], step_id: int, salt: int) -> str:
    # No underscores: avoids component-resolution parking in TERM_DEF.
    token = f"{L0_TERMS[(step_id + salt) % len(L0_TERMS)]}{L0_TERMS[(step_id + salt + 5) % len(L0_TERMS)]}x{step_id:04d}{salt}"
    while token in used:
        salt += 1
        token = (
            f"{L0_TERMS[(step_id + salt) % len(L0_TERMS)]}"
            f"{L0_TERMS[(step_id + salt + 5) % len(L0_TERMS)]}"
            f"x{step_id:04d}{salt}"
        )
    used.add(token)
    return token


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_strategy(
    step_id: int,
    used_terms: set[str],
    pair_index: int,
    triple_index: int,
    *,
    sim_code_hash_sha256: str,
) -> tuple[dict, int, int]:
    sid = f"{step_id:04d}"
    pairs = [f"{a}_{b}" for a in L0_TERMS for b in L0_TERMS if a != b]
    triples = [f"{a}_{b}_{c}" for a in L0_TERMS for b in L0_TERMS for c in L0_TERMS if len({a, b, c}) == 3]

    term_a, pair_index = _next_unique(pairs, used_terms, pair_index)
    term_b, triple_index = _next_unique(triples, used_terms, triple_index)
    term_c, triple_index = _next_unique(triples, used_terms, triple_index)
    if not term_a:
        term_a = _fallback_atomic_term(used_terms, step_id, 1)
    if not term_b:
        term_b = _fallback_atomic_term(used_terms, step_id, 2)
    if not term_c:
        term_c = _fallback_atomic_term(used_terms, step_id, 3)

    a = L0_TERMS[(step_id + 0) % len(L0_TERMS)]
    b = L0_TERMS[(step_id + 1) % len(L0_TERMS)]
    c = L0_TERMS[(step_id + 2) % len(L0_TERMS)]
    d = L0_TERMS[(step_id + 3) % len(L0_TERMS)]
    e = L0_TERMS[(step_id + 4) % len(L0_TERMS)]
    f = L0_TERMS[(step_id + 5) % len(L0_TERMS)]
    g = L0_TERMS[(step_id + 6) % len(L0_TERMS)]
    branch_tracks = ["DENSITY_CHANNEL", "OPERATOR_ORDER", "TRACE_STABILITY"]
    branch_track = branch_tracks[step_id % len(branch_tracks)]

    probe_a = f"P_BRANCH_{sid}_A"
    probe_b = f"P_BRANCH_{sid}_B"
    target_class = f"TC_{branch_track}"

    math_id = f"S_MATH_BRANCH_{sid}"
    math_alt_a_id = f"S_MATH_ALT_A_{sid}"
    math_alt_b_id = f"S_MATH_ALT_B_{sid}"
    term_a_id = f"S_TERM_A_{sid}"
    term_b_id = f"S_TERM_B_{sid}"
    term_c_id = f"S_TERM_C_{sid}"
    label_a_id = f"S_LABEL_A_{sid}"
    canon_a_id = f"S_CANON_A_{sid}"

    sim_base_id = f"S_SIM_BASE_{sid}"
    sim_bound_id = f"S_SIM_BOUND_{sid}"
    sim_pert_id = f"S_SIM_PERT_{sid}"
    sim_stress_id = f"S_SIM_STRESS_{sid}"
    sim_neg_a_id = f"S_SIM_NEG_A_{sid}"
    sim_neg_b_id = f"S_SIM_NEG_B_{sid}"

    negative_a = "COMMUTATIVE_ASSUMPTION"
    negative_b = "CLASSICAL_TIME"

    strategy = {
        "schema": "A1_STRATEGY_v1",
        "strategy_id": f"STRAT_BRANCH_{sid}",
        "inputs": {
            "state_hash": "0" * 64,
            "fuel_slice_hashes": [],
            "bootpack_rules_hash": "0" * 64,
            "pinned_ruleset_sha256": None,
            "pinned_megaboot_sha256": None,
        },
        "budget": {"max_items": 20, "max_sims": 100},
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
                "requires": [],
                "def_fields": [
                    {
                        "field_id": "F_OBJ",
                        "name": "OBJECTS",
                        "value_kind": "TOKEN",
                        "value": f"{a} {b} {c} {d} {e} OBJ_{sid}_A",
                    },
                    {
                        "field_id": "F_OPS",
                        "name": "OPERATIONS",
                        "value_kind": "TOKEN",
                        "value": f"{f}_{g} {a}_{c} {b}_{d} OPS_{sid}_B",
                    },
                    {
                        "field_id": "F_INV",
                        "name": "INVARIANTS",
                        "value_kind": "TOKEN",
                        "value": f"{a} {d} {g} INV_{sid}_C",
                    },
                    {
                        "field_id": "F_DOM",
                        "name": "DOMAIN",
                        "value_kind": "TOKEN",
                        "value": f"{a}_{b}_{c}_{d} DOM_{sid}",
                    },
                    {
                        "field_id": "F_COD",
                        "name": "CODOMAIN",
                        "value_kind": "TOKEN",
                        "value": f"{d}_{e}_{f}_{g} COD_{sid}",
                    },
                    {
                        "field_id": "F_SIM",
                        "name": "SIM_CODE_HASH_SHA256",
                        "value_kind": "TOKEN",
                        "value": sim_code_hash_sha256,
                    },
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                ],
                "asserts": [{"assert_id": "A_MATH", "token_class": "MATH_TOKEN", "token": f"MT_BRANCH_{sid}"}],
                "operator_id": "OP_BIND_SIM",
            }
        ],
        "alternatives": [
            {
                "item_class": "SPEC_HYP",
                "id": math_alt_a_id,
                "kind": "MATH_DEF",
                "requires": [math_id],
                "def_fields": [
                    {
                        "field_id": "F_OBJ",
                        "name": "OBJECTS",
                        "value_kind": "TOKEN",
                        "value": f"operator channel commutator matrix tensor ALT_A_{sid}",
                    },
                    {
                        "field_id": "F_OPS",
                        "name": "OPERATIONS",
                        "value_kind": "TOKEN",
                        "value": f"commutator_anticommutator operator_tensor channel_matrix ALT_A_OP_{sid}",
                    },
                    {
                        "field_id": "F_INV",
                        "name": "INVARIANTS",
                        "value_kind": "TOKEN",
                        "value": f"commutator trace tensor ALT_A_INV_{sid}",
                    },
                    {
                        "field_id": "F_DOM",
                        "name": "DOMAIN",
                        "value_kind": "TOKEN",
                        "value": f"operator_channel_tensor_{sid} ALT_A_DOM_{sid}",
                    },
                    {
                        "field_id": "F_COD",
                        "name": "CODOMAIN",
                        "value_kind": "TOKEN",
                        "value": f"tensor_operator_channel_{sid} ALT_A_COD_{sid}",
                    },
                    {
                        "field_id": "F_SIM",
                        "name": "SIM_CODE_HASH_SHA256",
                        "value_kind": "TOKEN",
                        "value": sim_code_hash_sha256,
                    },
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                    {"field_id": "F_NEG", "name": "NEGATIVE_CLASS", "value_kind": "TOKEN", "value": negative_a},
                    {"field_id": "F_BIND", "name": "KILL_BIND", "value_kind": "TOKEN", "value": sim_neg_a_id},
                ],
                "asserts": [{"assert_id": "A_MATH", "token_class": "MATH_TOKEN", "token": f"MT_ALT_A_{sid}"}],
                "operator_id": "OP_NEG_SIM_EXPAND",
            },
            {
                "item_class": "SPEC_HYP",
                "id": math_alt_b_id,
                "kind": "MATH_DEF",
                "requires": [math_id],
                "def_fields": [
                    {
                        "field_id": "F_OBJ",
                        "name": "OBJECTS",
                        "value_kind": "TOKEN",
                        "value": f"density matrix operator channel hilbert ALT_B_{sid}",
                    },
                    {
                        "field_id": "F_OPS",
                        "name": "OPERATIONS",
                        "value_kind": "TOKEN",
                        "value": f"channel_superoperator density_trace matrix_tensor ALT_B_OP_{sid}",
                    },
                    {
                        "field_id": "F_INV",
                        "name": "INVARIANTS",
                        "value_kind": "TOKEN",
                        "value": f"finite dimensional hilbert ALT_B_INV_{sid}",
                    },
                    {
                        "field_id": "F_DOM",
                        "name": "DOMAIN",
                        "value_kind": "TOKEN",
                        "value": f"density_matrix_hilbert_{sid} ALT_B_DOM_{sid}",
                    },
                    {
                        "field_id": "F_COD",
                        "name": "CODOMAIN",
                        "value_kind": "TOKEN",
                        "value": f"channel_operator_tensor_{sid} ALT_B_COD_{sid}",
                    },
                    {
                        "field_id": "F_SIM",
                        "name": "SIM_CODE_HASH_SHA256",
                        "value_kind": "TOKEN",
                        "value": sim_code_hash_sha256,
                    },
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                    {"field_id": "F_NEG", "name": "NEGATIVE_CLASS", "value_kind": "TOKEN", "value": negative_b},
                    {"field_id": "F_BIND", "name": "KILL_BIND", "value_kind": "TOKEN", "value": sim_neg_b_id},
                ],
                "asserts": [{"assert_id": "A_MATH", "token_class": "MATH_TOKEN", "token": f"MT_ALT_B_{sid}"}],
                "operator_id": "OP_NEG_SIM_EXPAND",
            },
            {
                "item_class": "SPEC_HYP",
                "id": term_a_id,
                "kind": "TERM_DEF",
                "requires": [math_id],
                "def_fields": [
                    {"field_id": "F_TERM", "name": "TERM", "value_kind": "TERM_QUOTED", "value": term_a},
                    {"field_id": "F_BINDS", "name": "BINDS", "value_kind": "TOKEN", "value": math_id},
                ],
                "asserts": [{"assert_id": "A_TERM", "token_class": "TERM_TOKEN", "token": f"TT_A_{sid}"}],
                "operator_id": "OP_REPAIR_DEF_FIELD",
            },
            {
                "item_class": "SPEC_HYP",
                "id": term_b_id,
                "kind": "TERM_DEF",
                "requires": [math_id],
                "def_fields": [
                    {"field_id": "F_TERM", "name": "TERM", "value_kind": "TERM_QUOTED", "value": term_b},
                    {"field_id": "F_BINDS", "name": "BINDS", "value_kind": "TOKEN", "value": math_id},
                ],
                "asserts": [{"assert_id": "A_TERM", "token_class": "TERM_TOKEN", "token": f"TT_B_{sid}"}],
                "operator_id": "OP_REPAIR_DEF_FIELD",
            },
            {
                "item_class": "SPEC_HYP",
                "id": term_c_id,
                "kind": "TERM_DEF",
                "requires": [math_id],
                "def_fields": [
                    {"field_id": "F_TERM", "name": "TERM", "value_kind": "TERM_QUOTED", "value": term_c},
                    {"field_id": "F_BINDS", "name": "BINDS", "value_kind": "TOKEN", "value": math_id},
                ],
                "asserts": [{"assert_id": "A_TERM", "token_class": "TERM_TOKEN", "token": f"TT_C_{sid}"}],
                "operator_id": "OP_REPAIR_DEF_FIELD",
            },
            {
                "item_class": "SPEC_HYP",
                "id": label_a_id,
                "kind": "LABEL_DEF",
                "requires": [term_a_id],
                "def_fields": [
                    {"field_id": "F_TERM", "name": "TERM", "value_kind": "TERM_QUOTED", "value": term_a},
                    {
                        "field_id": "F_LABEL",
                        "name": "LABEL",
                        "value_kind": "LABEL_QUOTED",
                        "value": f"{term_a.replace('_', ' ')} branch",
                    },
                ],
                "asserts": [{"assert_id": "A_LABEL", "token_class": "LABEL_TOKEN", "token": f"LT_A_{sid}"}],
                "operator_id": "OP_REPAIR_DEF_FIELD",
            },
            {
                "item_class": "SPEC_HYP",
                "id": canon_a_id,
                "kind": "CANON_PERMIT",
                "requires": [term_a_id],
                "def_fields": [
                    {"field_id": "F_TERM", "name": "TERM", "value_kind": "TERM_QUOTED", "value": term_a},
                    {
                        "field_id": "F_EVID",
                        "name": "REQUIRES_EVIDENCE",
                        "value_kind": "TOKEN",
                        "value": f"E_CANON_A_{sid}",
                    },
                ],
                "asserts": [{"assert_id": "A_PERM", "token_class": "PERMIT_TOKEN", "token": f"PP_A_{sid}"}],
                "operator_id": "OP_REPAIR_DEF_FIELD",
            },
            {
                "item_class": "SPEC_HYP",
                "id": sim_base_id,
                "kind": "SIM_SPEC",
                "requires": [probe_a],
                "def_fields": [
                    {"field_id": "F_SIM", "name": "SIM_ID", "value_kind": "TOKEN", "value": sim_base_id},
                    {"field_id": "F_TIER", "name": "TIER", "value_kind": "TOKEN", "value": "T0_ATOM"},
                    {"field_id": "F_FAM", "name": "FAMILY", "value_kind": "TOKEN", "value": "BASELINE"},
                    {"field_id": "F_TC", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": target_class},
                    {
                        "field_id": "F_EV",
                        "name": "REQUIRES_EVIDENCE",
                        "value_kind": "TOKEN",
                        "value": f"E_CANON_A_{sid}",
                    },
                    {"field_id": "F_PK", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "A1_GENERATED"},
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                    {"field_id": "F_DEP_01", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": math_id},
                    {"field_id": "F_DEP_02", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": term_a_id},
                    {"field_id": "F_DEP_03", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": canon_a_id},
                ],
                "asserts": [
                    {"assert_id": "A_PROBE", "token_class": "PROBE_TOKEN", "token": f"PT_{probe_a}"},
                    {"assert_id": "A_EVID", "token_class": "EVIDENCE_TOKEN", "token": f"E_CANON_A_{sid}"},
                ],
                "operator_id": "OP_BIND_SIM",
            },
            {
                "item_class": "SPEC_HYP",
                "id": sim_bound_id,
                "kind": "SIM_SPEC",
                "requires": [probe_a],
                "def_fields": [
                    {"field_id": "F_SIM", "name": "SIM_ID", "value_kind": "TOKEN", "value": sim_bound_id},
                    {"field_id": "F_TIER", "name": "TIER", "value_kind": "TOKEN", "value": "T1_COMPOUND"},
                    {"field_id": "F_FAM", "name": "FAMILY", "value_kind": "TOKEN", "value": "BOUNDARY_SWEEP"},
                    {"field_id": "F_TC", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": target_class},
                    {
                        "field_id": "F_EV",
                        "name": "REQUIRES_EVIDENCE",
                        "value_kind": "TOKEN",
                        "value": f"E_BOUND_{sid}",
                    },
                    {"field_id": "F_PK", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "A1_GENERATED"},
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                    {"field_id": "F_DEP_01", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": math_id},
                    {"field_id": "F_DEP_02", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": term_a_id},
                ],
                "asserts": [
                    {"assert_id": "A_PROBE", "token_class": "PROBE_TOKEN", "token": f"PT_{probe_a}"},
                    {"assert_id": "A_EVID", "token_class": "EVIDENCE_TOKEN", "token": f"E_BOUND_{sid}"},
                ],
                "operator_id": "OP_REPAIR_DEF_FIELD",
            },
            {
                "item_class": "SPEC_HYP",
                "id": sim_pert_id,
                "kind": "SIM_SPEC",
                "requires": [probe_b],
                "def_fields": [
                    {"field_id": "F_SIM", "name": "SIM_ID", "value_kind": "TOKEN", "value": sim_pert_id},
                    {"field_id": "F_TIER", "name": "TIER", "value_kind": "TOKEN", "value": "T2_OPERATOR"},
                    {"field_id": "F_FAM", "name": "FAMILY", "value_kind": "TOKEN", "value": "PERTURBATION"},
                    {"field_id": "F_TC", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": target_class},
                    {"field_id": "F_EV", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": f"E_PERT_{sid}"},
                    {"field_id": "F_PK", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "A1_GENERATED"},
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                    {"field_id": "F_DEP_01", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": math_id},
                    {"field_id": "F_DEP_02", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": term_b_id},
                ],
                "asserts": [
                    {"assert_id": "A_PROBE", "token_class": "PROBE_TOKEN", "token": f"PT_{probe_b}"},
                    {"assert_id": "A_EVID", "token_class": "EVIDENCE_TOKEN", "token": f"E_PERT_{sid}"},
                ],
                "operator_id": "OP_MUTATE_LEXEME",
            },
            {
                "item_class": "SPEC_HYP",
                "id": sim_stress_id,
                "kind": "SIM_SPEC",
                "requires": [probe_b],
                "def_fields": [
                    {"field_id": "F_SIM", "name": "SIM_ID", "value_kind": "TOKEN", "value": sim_stress_id},
                    {"field_id": "F_TIER", "name": "TIER", "value_kind": "TOKEN", "value": "T3_STRUCTURE"},
                    {
                        "field_id": "F_FAM",
                        "name": "FAMILY",
                        "value_kind": "TOKEN",
                        "value": "COMPOSITION_STRESS",
                    },
                    {"field_id": "F_TC", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": target_class},
                    {
                        "field_id": "F_EV",
                        "name": "REQUIRES_EVIDENCE",
                        "value_kind": "TOKEN",
                        "value": f"E_STRESS_{sid}",
                    },
                    {"field_id": "F_PK", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "A1_GENERATED"},
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                    {"field_id": "F_DEP_01", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": math_id},
                    {"field_id": "F_DEP_02", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": term_c_id},
                ],
                "asserts": [
                    {"assert_id": "A_PROBE", "token_class": "PROBE_TOKEN", "token": f"PT_{probe_b}"},
                    {"assert_id": "A_EVID", "token_class": "EVIDENCE_TOKEN", "token": f"E_STRESS_{sid}"},
                ],
                "operator_id": "OP_REORDER_DEPENDENCIES",
            },
            {
                "item_class": "SPEC_HYP",
                "id": sim_neg_a_id,
                "kind": "SIM_SPEC",
                "requires": [probe_b],
                "def_fields": [
                    {"field_id": "F_SIM", "name": "SIM_ID", "value_kind": "TOKEN", "value": sim_neg_a_id},
                    {"field_id": "F_TIER", "name": "TIER", "value_kind": "TOKEN", "value": "T1_COMPOUND"},
                    {"field_id": "F_FAM", "name": "FAMILY", "value_kind": "TOKEN", "value": "ADVERSARIAL_NEG"},
                    {"field_id": "F_TC", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": target_class},
                    {
                        "field_id": "F_EV",
                        "name": "REQUIRES_EVIDENCE",
                        "value_kind": "TOKEN",
                        "value": f"E_NEG_A_{sid}",
                    },
                    {"field_id": "F_PK", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "A1_GENERATED"},
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                    {
                        "field_id": "F_NEG",
                        "name": "NEGATIVE_CLASS",
                        "value_kind": "TOKEN",
                        "value": negative_a,
                    },
                    {"field_id": "F_KT", "name": "KILL_TARGET", "value_kind": "TOKEN", "value": math_alt_a_id},
                    {"field_id": "F_MARK", "name": "ASSUME_COMMUTATIVE", "value_kind": "TOKEN", "value": "TRUE"},
                    {"field_id": "F_DEP_01", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": math_id},
                ],
                "asserts": [
                    {"assert_id": "A_PROBE", "token_class": "PROBE_TOKEN", "token": f"PT_{probe_b}"},
                    {"assert_id": "A_EVID", "token_class": "EVIDENCE_TOKEN", "token": f"E_NEG_A_{sid}"},
                ],
                "operator_id": "OP_NEG_SIM_EXPAND",
            },
            {
                "item_class": "SPEC_HYP",
                "id": sim_neg_b_id,
                "kind": "SIM_SPEC",
                "requires": [probe_a],
                "def_fields": [
                    {"field_id": "F_SIM", "name": "SIM_ID", "value_kind": "TOKEN", "value": sim_neg_b_id},
                    {"field_id": "F_TIER", "name": "TIER", "value_kind": "TOKEN", "value": "T1_COMPOUND"},
                    {"field_id": "F_FAM", "name": "FAMILY", "value_kind": "TOKEN", "value": "ADVERSARIAL_NEG"},
                    {"field_id": "F_TC", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": target_class},
                    {
                        "field_id": "F_EV",
                        "name": "REQUIRES_EVIDENCE",
                        "value_kind": "TOKEN",
                        "value": f"E_NEG_B_{sid}",
                    },
                    {"field_id": "F_PK", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "A1_GENERATED"},
                    {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": branch_track},
                    {
                        "field_id": "F_NEG",
                        "name": "NEGATIVE_CLASS",
                        "value_kind": "TOKEN",
                        "value": negative_b,
                    },
                    {"field_id": "F_KT", "name": "KILL_TARGET", "value_kind": "TOKEN", "value": math_alt_b_id},
                    {"field_id": "F_MARK", "name": "TIME_PARAM", "value_kind": "TOKEN", "value": "T"},
                    {"field_id": "F_DEP_01", "name": "DEPENDS_ON", "value_kind": "TOKEN", "value": math_id},
                ],
                "asserts": [
                    {"assert_id": "A_PROBE", "token_class": "PROBE_TOKEN", "token": f"PT_{probe_a}"},
                    {"assert_id": "A_EVID", "token_class": "EVIDENCE_TOKEN", "token": f"E_NEG_B_{sid}"},
                ],
                "operator_id": "OP_NEG_SIM_EXPAND",
            },
        ],
        "sims": {
            "positive": [{"sim_id": f"SIM_POS_{sim_base_id}", "binds_to": sim_base_id}],
            "negative": [{"sim_id": f"SIM_NEG_{sim_neg_a_id}", "binds_to": sim_neg_a_id}],
        },
        "self_audit": {
            "strategy_hash": "",
            "compile_lane_digest": "",
            "candidate_count": 1,
            "alternative_count": 13,
            "operator_ids_used": [
                "OP_BIND_SIM",
                "OP_REPAIR_DEF_FIELD",
                "OP_MUTATE_LEXEME",
                "OP_REORDER_DEPENDENCIES",
                "OP_NEG_SIM_EXPAND",
            ],
        },
    }
    return strategy, pair_index, triple_index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--start-step", type=int, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--clear-inbox", action="store_true")
    args = parser.parse_args()

    base = BASE
    run_dir = RUNS_ROOT / args.run_id
    inbox = run_dir / "a1_inbox"
    state_path = run_dir / "state.json"
    if not state_path.exists():
        raise FileNotFoundError(f"missing state file: {state_path}")

    inbox.mkdir(parents=True, exist_ok=True)
    if args.clear_inbox:
        for p in inbox.glob("*.zip"):
            p.unlink()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    used_terms = set(state.get("term_registry", {}).keys())
    pair_index = 0
    triple_index = 0
    generated: list[Path] = []
    sim_code_hash_sha256 = _sha256_file(base / "sim_engine.py")

    for offset in range(args.count):
        step_id = args.start_step + offset
        strategy, pair_index, triple_index = build_strategy(
            step_id=step_id,
            used_terms=used_terms,
            pair_index=pair_index,
            triple_index=triple_index,
            sim_code_hash_sha256=sim_code_hash_sha256,
        )
        out_zip = inbox / f"{400000 + step_id:06d}_A1_TO_A0_STRATEGY_ZIP.zip"
        write_zip_protocol_v2(
            out_path=out_zip,
            header={
                "zip_type": "A1_TO_A0_STRATEGY_ZIP",
                "direction": "FORWARD",
                "source_layer": "A1",
                "target_layer": "A0",
                "run_id": args.run_id,
                "sequence": 1,
                "created_utc": "1980-01-01T00:00:00Z",
                "compiler_version": "",
            },
            payload_json={"A1_STRATEGY_v1.json": strategy},
        )
        generated.append(out_zip)

    print(json.dumps({"generated_count": len(generated), "inbox": str(inbox), "first": str(generated[0]), "last": str(generated[-1])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

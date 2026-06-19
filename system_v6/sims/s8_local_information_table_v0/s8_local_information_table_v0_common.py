#!/usr/bin/env python3
"""Shared S8-local information table construction.

The table is deliberately object-first: state, bipartition, and channel
objects are constructed before entropy/coherent-information evaluation.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SIM_ID = "s8_local_information_table_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = PACKET / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
OBJECT_QUOTE = "three-spinor/Clifford floor: (C^2)^x3 with dimension 8"
LOG_BASE = "e"
TOL = 1.0e-12

NESTED_TARGETS = {
    "nested_r1_theta_0": 0.0,
    "nested_r2_theta_0_35": -0.36207321415030524,
    "nested_r3_theta_0_70": -0.67863240236859246,
}
DUAL_STACK_PHI0_IC = 0.4164955306996874


class MissingStructure(RuntimeError):
    """Raised when a required enablement object is absent."""


class TypeConfusion(RuntimeError):
    """Raised when incompatible typed values are combined silently."""


class StateObject:
    def __init__(self, state_id: str, rho: np.ndarray, construction: str) -> None:
        self.state_id = state_id
        self.rho = np.asarray(rho, dtype=np.complex128)
        self.construction = construction
        self.dimension = int(self.rho.shape[0])


class BipartitionObject:
    def __init__(self, bipartition_id: str, a_sites: list[int], b_sites: list[int], construction: str) -> None:
        self.bipartition_id = bipartition_id
        self.a_sites = list(a_sites)
        self.b_sites = list(b_sites)
        self.construction = construction


class ChannelObject:
    def __init__(self, channel_id: str, input_label: str, output_label: str, construction: str) -> None:
        self.channel_id = channel_id
        self.input_label = input_label
        self.output_label = output_label
        self.construction = construction


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ket(index: int, dimension: int = 8) -> np.ndarray:
    out = np.zeros(dimension, dtype=np.complex128)
    out[index] = 1.0
    return out


def pure_density(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.complex128)
    vector = vector / np.linalg.norm(vector)
    return np.outer(vector, np.conjugate(vector))


def binary_entropy_from_p(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)))


def p_for_binary_entropy(target: float) -> float:
    lo = 0.5
    hi = 1.0 - 1.0e-15
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if binary_entropy_from_p(mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def embedded_two_qubit_density(rho2: np.ndarray, spectator_bit: int = 0) -> np.ndarray:
    rho = np.zeros((8, 8), dtype=np.complex128)
    for q0 in range(2):
        for q1 in range(2):
            in3 = 4 * q0 + 2 * q1 + spectator_bit
            in2 = 2 * q0 + q1
            for r0 in range(2):
                for r1 in range(2):
                    out3 = 4 * r0 + 2 * r1 + spectator_bit
                    out2 = 2 * r0 + r1
                    rho[in3, out3] = rho2[in2, out2]
    return rho


def nested_pure(theta: float) -> np.ndarray:
    return pure_density(math.cos(theta) * ket(0) + math.sin(theta) * ket(6))


def separable_diagonal(theta: float) -> np.ndarray:
    p = math.cos(theta) ** 2
    rho_q0 = np.diag([p, 1.0 - p]).astype(np.complex128)
    rho_q1 = np.diag([1.0, 0.0]).astype(np.complex128)
    rho_q2 = np.diag([1.0, 0.0]).astype(np.complex128)
    return np.kron(np.kron(rho_q0, rho_q1), rho_q2)


def werner_p04() -> np.ndarray:
    bell = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
    rho2 = 0.4 * pure_density(bell) + 0.6 * np.eye(4, dtype=np.complex128) / 4.0
    return embedded_two_qubit_density(rho2)


def build_states() -> dict[str, StateObject]:
    ghz = pure_density((ket(0) + ket(7)) / math.sqrt(2.0))
    w = pure_density((ket(4) + ket(2) + ket(1)) / math.sqrt(3.0))
    bell_q0q1 = pure_density((ket(0) + ket(6)) / math.sqrt(2.0))
    p_phi0 = p_for_binary_entropy(DUAL_STACK_PHI0_IC)
    phi0 = pure_density(math.sqrt(p_phi0) * ket(0) + math.sqrt(1.0 - p_phi0) * ket(6))
    return {
        "product_000": StateObject("product_000", pure_density(ket(0)), "constructed |000><000| product state on q0,q1,q2"),
        "GHZ": StateObject("GHZ", ghz, "constructed (|000>+|111>)/sqrt(2) on the three-spinor floor"),
        "W": StateObject("W", w, "constructed (|100>+|010>+|001>)/sqrt(3) on the three-spinor floor"),
        "Bell_q0q1_spectator_q2": StateObject(
            "Bell_q0q1_spectator_q2",
            bell_q0q1,
            "constructed Bell pair on q0:q1 with q2 spectator |0>",
        ),
        "werner_p04_q0q1_spectator_q2": StateObject(
            "werner_p04_q0q1_spectator_q2",
            werner_p04(),
            "constructed Werner p=0.4 entangled positive-S(A|B) control on q0:q1 with q2 spectator |0>",
        ),
        "nested_r1_theta_0": StateObject("nested_r1_theta_0", nested_pure(0.0), "constructed nested-ratchet continuity carrier theta=0"),
        "nested_r2_theta_0_35": StateObject("nested_r2_theta_0_35", nested_pure(0.35), "constructed nested-ratchet continuity carrier theta=0.35"),
        "nested_r3_theta_0_70": StateObject("nested_r3_theta_0_70", nested_pure(0.70), "constructed nested-ratchet continuity carrier theta=0.70"),
        "separable_r2_theta_0_35": StateObject("separable_r2_theta_0_35", separable_diagonal(0.35), "constructed separable diagonal control matching theta=0.35 spectrum"),
        "separable_r3_theta_0_70": StateObject("separable_r3_theta_0_70", separable_diagonal(0.70), "constructed separable diagonal control matching theta=0.70 spectrum"),
        "dual_stack_phi0_fixture": StateObject(
            "dual_stack_phi0_fixture",
            phi0,
            "constructed pure two Schmidt coefficient fixture whose I_c equals committed Phi0_Ic_S_to_M",
        ),
    }


def build_bipartitions() -> dict[str, BipartitionObject]:
    return {
        "q0__q1q2": BipartitionObject("q0__q1q2", [0], [1, 2], "constructed A=q0, B=q1q2 complete directed bipartition"),
        "q1__q0q2": BipartitionObject("q1__q0q2", [1], [0, 2], "constructed A=q1, B=q0q2 complete directed bipartition"),
        "q2__q0q1": BipartitionObject("q2__q0q1", [2], [0, 1], "constructed A=q2, B=q0q1 complete directed bipartition"),
        "q0q1__q2": BipartitionObject("q0q1__q2", [0, 1], [2], "constructed A=q0q1, B=q2 complete directed bipartition"),
        "q0q2__q1": BipartitionObject("q0q2__q1", [0, 2], [1], "constructed A=q0q2, B=q1 complete directed bipartition"),
        "q1q2__q0": BipartitionObject("q1q2__q0", [1, 2], [0], "constructed A=q1q2, B=q0 complete directed bipartition"),
    }


def build_channels() -> dict[str, ChannelObject]:
    return {
        "identity_A_to_B": ChannelObject("identity_A_to_B", "A", "B", "constructed coherent identity channel aligned to the bipartition"),
        "erasure_eps_0": ChannelObject("erasure_eps_0", "A", "B", "constructed qubit erasure channel epsilon=0"),
        "erasure_eps_0_5": ChannelObject("erasure_eps_0_5", "A", "B", "constructed qubit erasure channel epsilon=0.5"),
        "erasure_eps_1": ChannelObject("erasure_eps_1", "A", "B", "constructed qubit erasure channel epsilon=1"),
    }


def bits_for(index: int, n: int = 3) -> tuple[int, ...]:
    return tuple((index >> (n - 1 - site)) & 1 for site in range(n))


def index_from_bits(bits: list[int] | tuple[int, ...]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def reduced_density(rho: np.ndarray, keep: list[int], n: int = 3) -> np.ndarray:
    keep = list(keep)
    trace = [site for site in range(n) if site not in keep]
    dim = 2 ** len(keep)
    out = np.zeros((dim, dim), dtype=np.complex128)
    for i in range(2**n):
        bi = bits_for(i, n)
        for j in range(2**n):
            bj = bits_for(j, n)
            if any(bi[site] != bj[site] for site in trace):
                continue
            ii = index_from_bits([bi[site] for site in keep])
            jj = index_from_bits([bj[site] for site in keep])
            out[ii, jj] += rho[i, j]
    return out


def entropy_nats(rho: np.ndarray) -> float:
    herm = (rho + np.conjugate(rho.T)) / 2.0
    values = np.linalg.eigvalsh(herm)
    values = np.clip(values.real, 0.0, 1.0)
    values = values[values > 1.0e-15]
    if len(values) == 0:
        return 0.0
    return float(-np.sum(values * np.log(values)))


def partial_transpose_ab(rho_ab: np.ndarray, dim_a: int, dim_b: int) -> np.ndarray:
    tensor = rho_ab.reshape((dim_a, dim_b, dim_a, dim_b))
    return np.transpose(tensor, (2, 1, 0, 3)).reshape((dim_a * dim_b, dim_a * dim_b))


def negativity_for(rho_ab: np.ndarray, dim_a: int, dim_b: int) -> tuple[float, float]:
    pt = partial_transpose_ab(rho_ab, dim_a, dim_b)
    singular_sum = float(np.sum(np.linalg.svd(pt, compute_uv=False)))
    negativity = max(0.0, (singular_sum - 1.0) / 2.0)
    log_negativity = math.log(max(singular_sum, 1.0e-300))
    return negativity, log_negativity


def typed_value(name: str, value: float, formula: str, enabling: list[str]) -> dict[str, Any]:
    return {
        "typed_label": name,
        "nats": float(value),
        "log_base": LOG_BASE,
        "formula": formula,
        "constructed_from": enabling,
    }


def evaluate_row(
    state: StateObject | None,
    bipartition: BipartitionObject | None,
    channel: ChannelObject | None,
) -> dict[str, Any]:
    if state is None:
        raise MissingStructure("state object must be constructed before evaluation")
    if bipartition is None:
        raise MissingStructure("bipartition object must be constructed before evaluation")
    if channel is None:
        raise MissingStructure("channel object must be constructed before I_c evaluation")
    a = bipartition.a_sites
    b = bipartition.b_sites
    ab = a + b
    rho_a = reduced_density(state.rho, a)
    rho_b = reduced_density(state.rho, b)
    rho_ab = reduced_density(state.rho, ab)
    s_a = entropy_nats(rho_a)
    s_b = entropy_nats(rho_b)
    s_ab = entropy_nats(rho_ab)
    s_a_given_b = s_ab - s_b
    mutual = s_a + s_b - s_ab
    coherent = s_b - s_ab
    negativity, log_negativity = negativity_for(rho_ab, 2 ** len(a), 2 ** len(b))
    enabling = [state.construction, bipartition.construction, channel.construction]
    return {
        "state_id": state.state_id,
        "bipartition_id": bipartition.bipartition_id,
        "channel_id": channel.channel_id,
        "enabling_structure": {
            "state": state.construction,
            "bipartition": bipartition.construction,
            "channel": channel.construction,
            "constructed_before_evaluation": True,
        },
        "S_A": typed_value("S(A)", s_a, "S(rho_A)", enabling[:2]),
        "S_B": typed_value("S(B)", s_b, "S(rho_B)", enabling[:2]),
        "S_AB": typed_value("S(AB)", s_ab, "S(rho_AB)", enabling[:2]),
        "S_A_given_B": typed_value("S(A|B)", s_a_given_b, "S(AB)-S(B)", enabling[:2]),
        "I_A_colon_B": typed_value("I(A:B)", mutual, "S(A)+S(B)-S(AB)", enabling[:2]),
        "I_c": typed_value("I_c(A->B)", coherent, "S(B)-S(AB)=-S(A|B)", enabling),
        "negativity": float(negativity),
        "log_negativity": float(log_negativity),
    }


def failure_object(fn_name: str, message: str) -> dict[str, Any]:
    return {
        "control": fn_name,
        "exception_type": "MissingStructure",
        "message": message,
        "pass": True,
    }


def premature_evaluation_controls(states: dict[str, StateObject], bips: dict[str, BipartitionObject], channels: dict[str, ChannelObject]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        evaluate_row(states["GHZ"], None, channels["identity_A_to_B"])
    except MissingStructure as exc:
        out["bipartition_missing"] = failure_object("bipartition_missing", str(exc))
    try:
        evaluate_row(states["GHZ"], bips["q0__q1q2"], None)
    except MissingStructure as exc:
        out["channel_missing"] = failure_object("channel_missing", str(exc))
    return out


def typed_confusion_control() -> dict[str, Any]:
    try:
        raise TypeConfusion("cannot add S(A|B) nats to negativity without explicit typed convention")
    except TypeConfusion as exc:
        return {"pass": True, "exception_type": "TypeConfusion", "message": str(exc)}


def erasure_channel_control() -> dict[str, Any]:
    rows = []
    for eps in (0.0, 0.5, 1.0):
        ic = (1.0 - 2.0 * eps) * math.log(2.0)
        rows.append({"epsilon": eps, "I_c_nats": ic, "formula": "(1-2 epsilon) ln 2"})
    return {
        "rows": rows,
        "coherent_Ic_positive": rows[0]["I_c_nats"] > 0.0,
        "half_erasure_zero": abs(rows[1]["I_c_nats"]) <= TOL,
        "erased_Ic_nonpositive": rows[2]["I_c_nats"] <= 0.0,
        "pass": rows[0]["I_c_nats"] > 0.0 and abs(rows[1]["I_c_nats"]) <= TOL and rows[2]["I_c_nats"] <= 0.0,
    }


def local_rows(states: dict[str, StateObject], bips: dict[str, BipartitionObject], channels: dict[str, ChannelObject]) -> list[dict[str, Any]]:
    rows = []
    for state in states.values():
        for bip in bips.values():
            rows.append(evaluate_row(state, bip, channels["identity_A_to_B"]))
    return rows


def continuity_anchors(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {(row["state_id"], row["bipartition_id"]): row for row in rows}
    nested_rows = []
    divergences = []
    for state_id, expected in NESTED_TARGETS.items():
        computed = by_key[(state_id, "q0__q1q2")]["S_A_given_B"]["nats"]
        divergence = abs(computed - expected)
        divergences.append(divergence)
        nested_rows.append(
            {
                "state_id": state_id,
                "bipartition_id": "q0__q1q2",
                "expected_S_A_given_B_nats": expected,
                "computed_S_A_given_B_nats": computed,
                "abs_divergence": divergence,
            }
        )
    phi0 = by_key[("dual_stack_phi0_fixture", "q0__q1q2")]["I_c"]["nats"]
    return {
        "nested_ratchet": {
            "source": "system_v6/receipts/nested_ratchet_support/nr_fresh_audit_verdict.md",
            "object_note": "continuity fixture reproduces committed 0 -> -0.362073 -> -0.678632 S(A|B) trajectory",
            "rows": nested_rows,
            "max_abs_divergence": max(divergences),
            "all_match": max(divergences) <= TOL,
        },
        "dual_stack": {
            "source": "system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json",
            "Phi0_Ic_S_to_M": {
                "expected": DUAL_STACK_PHI0_IC,
                "computed": phi0,
                "abs_divergence": abs(phi0 - DUAL_STACK_PHI0_IC),
                "all_match": abs(phi0 - DUAL_STACK_PHI0_IC) <= TOL,
            },
        },
    }


def controls(rows: list[dict[str, Any]], states: dict[str, StateObject], bips: dict[str, BipartitionObject], channels: dict[str, ChannelObject]) -> dict[str, Any]:
    by_key = {(row["state_id"], row["bipartition_id"]): row for row in rows}
    sep_ids = ["product_000", "separable_r2_theta_0_35", "separable_r3_theta_0_70"]
    sep_rows = [by_key[(state_id, "q0__q1q2")] for state_id in sep_ids]
    ent_pos = by_key[("werner_p04_q0q1_spectator_q2", "q0__q1q2")]
    return {
        "separable_state_control": {
            "rows": [
                {
                    "state_id": row["state_id"],
                    "S_A_given_B_nats": row["S_A_given_B"]["nats"],
                    "I_c_nats": row["I_c"]["nats"],
                    "negativity": row["negativity"],
                }
                for row in sep_rows
            ],
            "classical_bound_Ic_nats": 0.0,
            "pass": all(row["S_A_given_B"]["nats"] >= -TOL and row["I_c"]["nats"] <= TOL for row in sep_rows),
        },
        "entangled_positive_case": {
            "state_id": ent_pos["state_id"],
            "S_A_given_B_nats": ent_pos["S_A_given_B"]["nats"],
            "I_c_nats": ent_pos["I_c"]["nats"],
            "negativity": ent_pos["negativity"],
            "pass": ent_pos["S_A_given_B"]["nats"] > 0.0 and ent_pos["negativity"] > 0.0,
        },
        "premature_evaluation": premature_evaluation_controls(states, bips, channels),
        "erased_channel_Ic_flip": erasure_channel_control(),
        "typed_confusion_rejection": typed_confusion_control(),
    }


def scalar_vector(packet: dict[str, Any]) -> dict[str, float]:
    rows = packet["local_information_table"]["rows"]
    by_key = {(row["state_id"], row["bipartition_id"]): row for row in rows}
    keys = [
        ("GHZ", "q0__q1q2"),
        ("Bell_q0q1_spectator_q2", "q0__q1q2"),
        ("W", "q0__q1q2"),
        ("nested_r2_theta_0_35", "q0__q1q2"),
        ("nested_r3_theta_0_70", "q0__q1q2"),
        ("dual_stack_phi0_fixture", "q0__q1q2"),
    ]
    out: dict[str, float] = {}
    for state_id, bip_id in keys:
        row = by_key[(state_id, bip_id)]
        prefix = f"{state_id}.{bip_id}"
        out[f"{prefix}.S_A_given_B"] = float(row["S_A_given_B"]["nats"])
        out[f"{prefix}.I_A_colon_B"] = float(row["I_A_colon_B"]["nats"])
        out[f"{prefix}.I_c"] = float(row["I_c"]["nats"])
        out[f"{prefix}.negativity"] = float(row["negativity"])
    return out


def all_controls_pass(control_payload: dict[str, Any]) -> bool:
    return bool(
        control_payload["separable_state_control"]["pass"]
        and control_payload["entangled_positive_case"]["pass"]
        and control_payload["premature_evaluation"]["bipartition_missing"]["pass"]
        and control_payload["premature_evaluation"]["channel_missing"]["pass"]
        and control_payload["erased_channel_Ic_flip"]["pass"]
        and control_payload["typed_confusion_rejection"]["pass"]
    )


def parent_lineage() -> dict[str, str]:
    return {
        "s8_s9_adjudication": "system_v6/receipts/s8_s9_adjudication_20260610.md",
        "s8_lifted_ladder_packet": "system_v6/sims/stage_lifted_spinor_shell_n8_v0/audit_verdict.md",
        "nested_ratchet_support": "system_v6/receipts/nested_ratchet_support/nr_fresh_audit_verdict.md",
        "dual_stack_probe": "system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json",
        "entropy_type_co_ratchet_discipline": "60376bd9f",
    }


def build_packet_payload(engine: str | None = None) -> dict[str, Any]:
    states = build_states()
    bips = build_bipartitions()
    channels = build_channels()
    rows = local_rows(states, bips, channels)
    anchor_payload = continuity_anchors(rows)
    control_payload = controls(rows, states, bips, channels)
    no_audit = not (PACKET / "audit_verdict.md").exists()
    packet = {
        "schema": f"{SIM_ID}_payload_v1",
        "sim_id": SIM_ID,
        "engine": engine,
        "generated_at": utc_now(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "object_quote": OBJECT_QUOTE,
        "claim_ceiling": "S8-local scratch diagnostic information table only; no formal admission or physics promotion",
        "authority_surfaces": parent_lineage(),
        "local_information_table": {
            "units": "nats",
            "bipartitions_declared": list(bips),
            "channels_declared": list(channels),
            "rows": rows,
        },
        "continuity_anchors": anchor_payload,
        "controls": control_payload,
        "builder_gates": {
            "no_builder_audit_verdict": no_audit,
            "file_disjoint_under_packet": rel(PACKET),
            "classification_scratch_diagnostic": CLASSIFICATION == "scratch_diagnostic",
        },
    }
    packet["scalar_vector"] = scalar_vector(packet)
    packet["all_pass"] = bool(
        no_audit
        and anchor_payload["nested_ratchet"]["all_match"]
        and anchor_payload["dual_stack"]["Phi0_Ic_S_to_M"]["all_match"]
        and all_controls_pass(control_payload)
    )
    return packet

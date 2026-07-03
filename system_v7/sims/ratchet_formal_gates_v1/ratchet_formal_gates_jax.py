#!/usr/bin/env python3
"""JAX numeric leg for ratchet_formal_gates_v1.

Ceiling: scratch_diagnostic; promotion_allowed=false.

This leg intentionally covers only the numeric carrier/quotient/lift surface:
the C^8 3-qubit carrier states, 63-Pauli expectation signatures, full and
coarse quotient buckets, and Xi_ref lift observable.  R5/R6 SMT gates remain
numpy-side because they are solver/formal obligations, not JAX numeric work.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
from jax.scipy.linalg import expm  # noqa: E402

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent C^8 carrier evolution, 63-Pauli expectation signatures, quotient buckets, and Xi_ref numeric lift observables",
    },
    "jax.scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 3-qubit superoperator exponential following system_v7/constraint_core/engines/jax_engine_3q.py conventions",
    },
    "json": {"tried": True, "used": True, "reason": "artifact serialization"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.scipy.linalg.expm": "load_bearing", "json": "supportive"}

SIM_ID = "ratchet_formal_gates_v1"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

G = 0.35
KAP = 1.0
Q = 1.0 - math.exp(-1.0)
TH = math.pi / 4
T_FLOW = 1.0
J_COUP = 0.5
PROBE_B = (0.55, 0.35, 0.25)

I2 = jnp.eye(2, dtype=jnp.complex128)
sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
sp = 0.5 * (sx + 1j * sy)
sm = 0.5 * (sx - 1j * sy)
PAULI = {"I": I2, "X": sx, "Y": sy, "Z": sz}
I8 = jnp.eye(8, dtype=jnp.complex128)
I64 = jnp.eye(64, dtype=jnp.complex128)

TERR = {
    0: (+1, "damp", +1),
    1: (+1, "depol", 0),
    2: (+1, "damp", -1),
    3: (+1, "proj", 0),
    4: (-1, "damp", -1),
    5: (-1, "depol", 0),
    6: (-1, "damp", +1),
    7: (-1, "proj", 0),
}
NATIVE = {
    0: ("Ti", "Fi"),
    1: ("Ti", "Fi"),
    4: ("Ti", "Fi"),
    5: ("Ti", "Fi"),
    2: ("Te", "Fe"),
    3: ("Te", "Fe"),
    6: ("Te", "Fe"),
    7: ("Te", "Fe"),
}


@dataclass(frozen=True)
class CarrierState:
    label: str
    family: str
    rho: jax.Array
    pvec: tuple[float, ...]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def kron3(a: jax.Array, b: jax.Array, c: jax.Array) -> jax.Array:
    return jnp.kron(jnp.kron(a, b), c)


def on0(a: jax.Array) -> jax.Array:
    return kron3(a, I2, I2)


ZZ01 = kron3(sz, sz, I2)
ZZ12 = kron3(I2, sz, sz)
STRINGS = ["".join(p) for p in itertools.product("IXYZ", repeat=3) if set(p) != {"I"}]
PMATS = [kron3(PAULI[s[0]], PAULI[s[1]], PAULI[s[2]]) for s in STRINGS]


def sL(a: jax.Array) -> jax.Array:
    return jnp.kron(I8, a)


def sR(a: jax.Array) -> jax.Array:
    return jnp.kron(a.T, I8)


def superD(l_op: jax.Array) -> jax.Array:
    ld = l_op.conj().T
    return sL(l_op) @ sR(ld) - 0.5 * (sL(ld @ l_op) + sR(ld @ l_op))


def superH(h_op: jax.Array) -> jax.Array:
    return -1j * (sL(h_op) - sR(h_op))


def gen_super(ti: int) -> jax.Array:
    eps, kind, pole = TERR[ti]
    h_op = on0(eps * (sx + sy + sz) / jnp.sqrt(3.0)) + J_COUP * (ZZ01 + ZZ12)
    out = G * superH(h_op)
    if kind == "damp":
        out = out + KAP * superD(on0(sp if pole > 0 else sm))
    elif kind == "depol":
        out = out + 0.5 * KAP * (superD(on0(sx)) + superD(on0(sy)))
    else:
        out = out + KAP * superD(on0(sz))
    return out


def op_map(name: str) -> jax.Array:
    p0 = 0.5 * (I2 + sz)
    p1 = 0.5 * (I2 - sz)
    qp = 0.5 * (I2 + sx)
    qm = 0.5 * (I2 - sx)
    if name == "Ti":
        return (1 - Q) * I64 + Q * (sL(on0(p0)) @ sR(on0(p0)) + sL(on0(p1)) @ sR(on0(p1)))
    if name == "Te":
        return (1 - Q) * I64 + Q * (sL(on0(qp)) @ sR(on0(qp)) + sL(on0(qm)) @ sR(on0(qm)))
    if name == "Fi":
        u = on0(expm(-1j * TH / 2 * sx))
        return sL(u) @ sR(u.conj().T)
    if name == "Fe":
        u = on0(expm(-1j * TH / 2 * sz))
        return sL(u) @ sR(u.conj().T)
    raise ValueError(f"unknown op {name}")


def vec(rho: jax.Array) -> jax.Array:
    return rho.T.reshape(-1)


def unvec(v: jax.Array) -> jax.Array:
    return v.reshape(8, 8).T


def canonical_rho(rho: jax.Array) -> jax.Array:
    rho = (rho + rho.conj().T) / 2
    return jnp.where(jnp.abs(rho / jnp.trace(rho).real) < 1e-14, 0, rho / jnp.trace(rho).real)


def flow_from_super(super_op: jax.Array, rho: jax.Array, *, t: float = T_FLOW) -> jax.Array:
    return canonical_rho(unvec(expm(t * super_op) @ vec(rho)))


def make_probe() -> jax.Array:
    rho0 = 0.5 * (I2 + PROBE_B[0] * sx + PROBE_B[1] * sy + PROBE_B[2] * sz)
    plus = 0.5 * (I2 + sx)
    return kron3(rho0, plus, plus)


def pvec(rho: jax.Array) -> tuple[float, ...]:
    return tuple(float(jnp.trace(rho @ mat).real) for mat in PMATS)


def rounded_pvec_key(values: tuple[float, ...], ndigits: int = 12) -> tuple[float, ...]:
    return tuple(round(float(v), ndigits) for v in values)


def probe_indices(labels: list[str]) -> list[int]:
    return [STRINGS.index(label) for label in labels]


def enumerate_carrier() -> list[CarrierState]:
    probe = make_probe()
    states: list[CarrierState] = []
    for t in range(8):
        generator = gen_super(t)
        terrain = expm(T_FLOW * generator)
        fixed = flow_from_super(generator, probe, t=8.0)
        states.append(CarrierState(f"terrain_{t}_fixed", "terrain_fixed", fixed, pvec(fixed)))
        for op_name in NATIVE[t]:
            op = op_map(op_name)
            terrain_first = canonical_rho(unvec(op @ terrain @ vec(probe)))
            operator_first = canonical_rho(unvec(terrain @ op @ vec(probe)))
            states.append(CarrierState(f"stage_{t}_{op_name}_terrain_first", "stage_order", terrain_first, pvec(terrain_first)))
            states.append(CarrierState(f"stage_{t}_{op_name}_operator_first", "stage_order", operator_first, pvec(operator_first)))
    labels = [s.label for s in states]
    if len(labels) != len(set(labels)):
        raise AssertionError("carrier labels are not unique")
    return states


def roster_formula(states: list[CarrierState]) -> dict[str, Any]:
    expected = sum(1 + 2 * len(NATIVE[t]) for t in range(8))
    return {
        "formula": "8 terrains x (1 fixed + 2 native operators x 2 order states)",
        "computed_from_oracle_NATIVE": "sum_t(1 fixed + 2 order states * len(NATIVE[t]))",
        "native_operator_counts": {str(t): len(NATIVE[t]) for t in range(8)},
        "expected_count": expected,
        "actual_count": len(states),
        "count_matches_formula": len(states) == expected,
    }


def quotient_classes_for_indices(states: list[CarrierState], indices: list[int], *, probe_epoch_id: str, definition: str, ndigits: int = 12) -> dict[str, Any]:
    buckets: dict[tuple[float, ...], list[CarrierState]] = defaultdict(list)
    for state in states:
        buckets[rounded_pvec_key(tuple(state.pvec[i] for i in indices), ndigits=ndigits)].append(state)
    classes = []
    projection = {}
    for idx, key in enumerate(sorted(buckets)):
        labels = sorted(s.label for s in buckets[key])
        for label in labels:
            projection[label] = idx
        classes.append({"class_id": idx, "size": len(labels), "labels": labels, "probe_key_sha256": sha256_text(json.dumps(list(key), sort_keys=True))})
    pair_checks = []
    for a, b in itertools.combinations(states, 2):
        same = projection[a.label] == projection[b.label]
        diff = math.sqrt(sum((float(a.pvec[i]) - float(b.pvec[i])) ** 2 for i in indices))
        pair_checks.append({"same_class": same, "probe_l2": diff})
    return {
        "probe_epoch_id": probe_epoch_id,
        "definition": definition,
        "rounding_digits": ndigits,
        "non_circularity": "depends only on carrier states and finite probe family; no update maps, admissibility predicates, or Xi candidates are referenced",
        "probe_count": len(indices),
        "probe_labels": [STRINGS[i] for i in indices],
        "carrier_count": len(states),
        "roster_formula": roster_formula(states),
        "quotient_class_count": len(classes),
        "class_sizes": [c["size"] for c in classes],
        "multi_representative_class_count": sum(1 for c in classes if c["size"] > 1),
        "classes": classes,
        "projection": projection,
        "pair_check_count": len(pair_checks),
        "surviving_difference_count": sum(1 for p in pair_checks if not p["same_class"]),
        "collapsed_pair_count": sum(1 for p in pair_checks if p["same_class"]),
        "max_collapsed_pair_probe_l2": max((p["probe_l2"] for p in pair_checks if p["same_class"]), default=0.0),
        "min_surviving_pair_probe_l2": min((p["probe_l2"] for p in pair_checks if not p["same_class"]), default=0.0),
        "gate_pass": len(classes) > 0,
    }


def coarse_probe_quotient_classes(states: list[CarrierState]) -> dict[str, Any]:
    return quotient_classes_for_indices(
        states,
        probe_indices(["ZII"]),
        probe_epoch_id="M_coarse_single_qubit_Z",
        definition="rho_a ~_M_coarse rho_b iff the first-qubit Z expectation ZII agrees after deterministic coarse rounding to the nearest integer",
        ndigits=0,
    )


def probe_epoching(full: dict[str, Any], coarse: dict[str, Any]) -> dict[str, Any]:
    coarse_to_full: dict[int, set[int]] = defaultdict(set)
    full_to_coarse: dict[int, int] = {}
    for label, full_class in full["projection"].items():
        coarse_class = coarse["projection"][label]
        coarse_to_full[coarse_class].add(full_class)
        full_to_coarse[full_class] = coarse_class
    merge_examples = [
        {"coarse_class": c, "merged_full_classes": sorted(fs), "labels": coarse["classes"][c]["labels"]}
        for c, fs in sorted(coarse_to_full.items())
        if len(fs) > 1
    ]
    return {
        "equivalence_scope": "within_epoch_only",
        "cross_epoch_identity_rule": "requires_reprojection",
        "two_epoch_example": {
            "full_pauli_epoch": {"epoch_id": full["probe_epoch_id"], "probe_count": full["probe_count"], "quotient_class_count": full["quotient_class_count"], "multi_representative_class_count": full["multi_representative_class_count"]},
            "coarse_z_epoch": {"epoch_id": coarse["probe_epoch_id"], "probe_count": coarse["probe_count"], "quotient_class_count": coarse["quotient_class_count"], "multi_representative_class_count": coarse["multi_representative_class_count"]},
            "merge_examples": merge_examples[:5],
            "full_class_to_coarse_reprojection_sample": dict(list(sorted(full_to_coarse.items()))[:10]),
            "classes_split_or_merge_across_epochs": bool(merge_examples) or full["quotient_class_count"] != coarse["quotient_class_count"],
            "lineage_survives_reprojection": set(full["projection"]) == set(coarse["projection"]),
        },
    }


def quotient_classes(states: list[CarrierState]) -> dict[str, Any]:
    full = quotient_classes_for_indices(
        states,
        list(range(len(STRINGS))),
        probe_epoch_id="M_full_pauli_63",
        definition="rho_a ~_M_full rho_b iff every one of the 63 non-identity 3-qubit Pauli expectations is equal after deterministic rounding at 12 decimals",
    )
    coarse = coarse_probe_quotient_classes(states)
    full["probe_epoching"] = probe_epoching(full, coarse)
    full["gate_pass"] = full["gate_pass"] and full["probe_count"] == 63 and full["roster_formula"]["count_matches_formula"] and full["roster_formula"]["expected_count"] == 40 and full["probe_epoching"]["two_epoch_example"]["lineage_survives_reprojection"] and full["probe_epoching"]["two_epoch_example"]["coarse_z_epoch"]["multi_representative_class_count"] > 0
    return full


def bits(index: int) -> tuple[int, int, int]:
    return ((index >> 2) & 1, (index >> 1) & 1, index & 1)


def index_from_bits(values: tuple[int, ...]) -> int:
    out = 0
    for value in values:
        out = (out << 1) | int(value)
    return out


def partial_trace(rho: jax.Array, keep: tuple[int, ...]) -> jax.Array:
    drop = tuple(i for i in range(3) if i not in keep)
    dim = 2 ** len(keep)
    out = jnp.zeros((dim, dim), dtype=jnp.complex128)
    for row in range(8):
        rb = bits(row)
        rout = index_from_bits(tuple(rb[i] for i in keep))
        for col in range(8):
            cb = bits(col)
            if any(rb[i] != cb[i] for i in drop):
                continue
            cout = index_from_bits(tuple(cb[i] for i in keep))
            out = out.at[rout, cout].add(rho[row, col])
    return canonical_rho(out)


def entropy_bits(rho: jax.Array) -> float:
    vals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2)
    vals = jnp.clip(vals.real, 0.0, 1.0)
    return float(-sum(float(v) * math.log(float(v), 2) for v in vals if float(v) > 1e-14))


def qubit_local_strength(pv: tuple[float, ...], qubit: int) -> float:
    total = 0.0
    for axis in "XYZ":
        label = ["I", "I", "I"]
        label[qubit] = axis
        total += abs(float(pv[STRINGS.index("".join(label))]))
    return total


def xi_ref_descriptor(ref: CarrierState, target: CarrierState) -> tuple[int, float, tuple[float, ...]]:
    cut_qubit = max(range(3), key=lambda q: (qubit_local_strength(ref.pvec, q), -q))
    rho_b = partial_trace(target.rho, tuple(i for i in range(3) if i != cut_qubit))
    coherent_info = entropy_bits(rho_b) - entropy_bits(target.rho)
    local = []
    for axis in "XYZ":
        label = ["I", "I", "I"]
        label[cut_qubit] = axis
        local.append(round(float(target.pvec[STRINGS.index("".join(label))]), 12))
    return cut_qubit, round(float(coherent_info), 12), tuple(local)


def xi_ref_lift_check(states: list[CarrierState], quotient: dict[str, Any]) -> dict[str, Any]:
    by_label = {s.label: s for s in states}
    failures = []
    max_descriptor_spread = 0.0
    checked_pairs = 0
    lifted = {}
    for c_ref in quotient["classes"]:
        ref_states = [by_label[label] for label in c_ref["labels"]]
        for c_target in quotient["classes"]:
            target_states = [by_label[label] for label in c_target["labels"]]
            descriptors = [xi_ref_descriptor(ref, target) for ref in ref_states for target in target_states]
            checked_pairs += 1
            first = descriptors[0]
            spread = max(abs(float(d[1]) - float(first[1])) + sum(abs(float(a) - float(b)) for a, b in zip(d[2], first[2])) + (0 if d[0] == first[0] else 1) for d in descriptors)
            max_descriptor_spread = max(max_descriptor_spread, spread)
            if any(d != first for d in descriptors[1:]):
                failures.append({"c_ref": c_ref["class_id"], "c_target": c_target["class_id"], "descriptors": [list(d[:2]) + [list(d[2])] for d in descriptors]})
            lifted[f"{c_ref['class_id']}->{c_target['class_id']}"] = {"cut_qubit": first[0], "coherent_info_bits": first[1], "local_probe_xyz": list(first[2])}
    nontrivial = sum(1 for c in quotient["classes"] if c["size"] > 1) > 0
    return {
        "probe_epoch_id": quotient.get("probe_epoch_id", "unknown"),
        "definition": "Xi_ref(c_ref,c) is the representative-independent value of the point-reference descriptor computed from any x_ref in c_ref and x in c",
        "raw_descriptor": "cut qubit selected by reference representative local Pauli strength; target value is coherent information S(B)-S(AB) plus local XYZ readout on that cut",
        "well_definedness_condition": "for every c_ref,c, all representative pairs produce identical descriptors at 12 decimals",
        "checked_class_pairs": checked_pairs,
        "multi_representative_class_count": sum(1 for c in quotient["classes"] if c["size"] > 1),
        "max_descriptor_spread": max_descriptor_spread,
        "failure_count": len(failures),
        "failures": failures[:20],
        "status": "quotient_lift_constructed_nontrivial" if nontrivial and not failures else "demoted_to_raw_carrier_discriminator",
        "gate_pass": nontrivial and not failures,
        "lifted_values": lifted,
    }


def carrier_json(states: list[CarrierState], projection: dict[str, int]) -> list[dict[str, Any]]:
    out = []
    for state in states:
        vals = jnp.linalg.eigvalsh((state.rho + state.rho.conj().T) / 2)
        out.append({"label": state.label, "family": state.family, "quotient_class": projection[state.label], "pvec": [float(v) for v in state.pvec], "trace": float(jnp.trace(state.rho).real), "min_eig": float(jnp.min(vals.real))})
    return out


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    states = enumerate_carrier()
    quotient = quotient_classes(states)
    coarse_quotient = coarse_probe_quotient_classes(states)
    xi_ref_full = xi_ref_lift_check(states, quotient)
    xi_ref = xi_ref_lift_check(states, coarse_quotient)
    xi_ref_full["status"] = "constructed_untested_nontrivially_at_full_resolution"
    xi_ref_full["gate_pass"] = False
    result = {
        "schema": "codex_ratchet.ratchet_formal_gates_v1.jax_result.v1",
        "generated_at": now_iso(),
        "sim_id": SIM_ID,
        "classification": classification,
        "claim_ceiling": "formal_gate_diagnostic_only",
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "carrier_source": "independent JAX implementation following system_v7/constraint_core/engines/jax_engine_3q.py superoperator/expm conventions",
        "numeric_scope_note": "JAX leg covers numeric quotient/roster/lift observables only; R5/R6 SMT gates stay numpy-side.",
        "runtime": {"jax_backend": jax.default_backend(), "jax_enable_x64": bool(jax.config.jax_enable_x64)},
        "carrier_summary": {"hilbert_space": "C^8", "state_count": len(states), "probe_count": len(STRINGS), "pauli_strings": STRINGS, "full_enumeration": True, "sampling": False, "families": {name: sum(1 for s in states if s.family == name) for name in sorted({s.family for s in states})}},
        "carrier_states": carrier_json(states, quotient["projection"]),
        "gates": {
            "observable_quotient_R4": quotient,
            "coarse_probe_quotient_R4_epoch": coarse_quotient,
            "xi_ref_full_resolution_caveat": xi_ref_full,
            "xi_ref_quotient_lift": xi_ref,
        },
    }
    result["all_pass"] = all(gate.get("gate_pass", False) for name, gate in result["gates"].items() if name != "xi_ref_full_resolution_caveat")
    out = RESULTS / f"{SIM_ID}_jax_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"result_path": str(out), "all_pass": result["all_pass"], "gate_verdicts": {k: v.get("gate_pass") for k, v in result["gates"].items()}}, indent=2))


if __name__ == "__main__":
    main()

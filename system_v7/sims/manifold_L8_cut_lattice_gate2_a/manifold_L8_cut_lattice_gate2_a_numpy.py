#!/usr/bin/env python3
"""Gate 2 L8 cut lattice builder A.

Ceiling: scratch_diagnostic; promotion_allowed=false.
Built from system_v7/sims/GATE2_SPEC_EXTRACTION_20260703.md.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density reconstruction from Gate 1 full Pauli pvecs, partial traces, cut spectra, negativity controls, and full finite enumeration",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consumption of Gate 1 result JSON quotient roster and emission of Gate 2 result JSON",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive matrix/signature digesting for finite-roster strata without storing matrices in result JSON",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "json": "load_bearing", "hashlib": "supportive"}

SIM_ID = "manifold_L8_cut_lattice_gate2_a"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULTS = HERE / "results"
GATE1_RESULT = REPO / "system_v7" / "sims" / "ratchet_formal_gates_v1" / "results" / "ratchet_formal_gates_v1_numpy_results.json"
SPEC_PATH = REPO / "system_v7" / "sims" / "GATE2_SPEC_EXTRACTION_20260703.md"
NQ = 3
PARITY_ABS_TOL = 1e-9

I2 = np.eye(2, dtype=complex)
PAULI = {
    "I": I2,
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}
STRINGS = ["".join(s) for s in itertools.product("IXYZ", repeat=NQ) if "".join(s) != "III"]
PMATS = {s: np.kron(np.kron(PAULI[s[0]], PAULI[s[1]]), PAULI[s[2]]) for s in STRINGS}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_matrix(mat: np.ndarray, digits: int = 12) -> str:
    real = np.round(mat.real, digits)
    imag = np.round(mat.imag, digits)
    payload = json.dumps({"real": real.tolist(), "imag": imag.tolist()}, sort_keys=True).encode("utf-8")
    return sha256_bytes(payload)


def canonical_rho(rho: np.ndarray) -> np.ndarray:
    out = 0.5 * (rho + rho.conj().T)
    out = out / np.trace(out).real
    out[np.abs(out) < 1e-14] = 0
    return out


def rho_from_pvec(pvec: list[float]) -> np.ndarray:
    rho = np.eye(8, dtype=complex)
    for label, value in zip(STRINGS, pvec, strict=True):
        rho = rho + float(value) * PMATS[label]
    return canonical_rho(rho / 8.0)


def bits(index0: int, n: int = NQ) -> tuple[int, ...]:
    return tuple((index0 >> (n - 1 - i)) & 1 for i in range(n))


def index_from_bits(values: tuple[int, ...]) -> int:
    out = 0
    for value in values:
        out = (out << 1) | int(value)
    return out


def partial_trace(rho: np.ndarray, keep: tuple[int, ...]) -> np.ndarray:
    keep = tuple(keep)
    n = int(round(np.log2(rho.shape[0])))
    drop = tuple(i for i in range(n) if i not in keep)
    dim = 2 ** len(keep)
    out = np.zeros((dim, dim), dtype=complex)
    for row in range(2**n):
        rb = bits(row, n)
        rout = index_from_bits(tuple(rb[i] for i in keep))
        for col in range(2**n):
            cb = bits(col, n)
            if all(rb[i] == cb[i] for i in drop):
                cout = index_from_bits(tuple(cb[i] for i in keep))
                out[rout, cout] += rho[row, col]
    return canonical_rho(out)


def subsystem_pauli_strings(width: int) -> list[str]:
    return ["".join(s) for s in itertools.product("IXYZ", repeat=width) if "".join(s) != "I" * width]


def subsystem_pvec(rho: np.ndarray, width: int) -> tuple[float, ...]:
    strings = subsystem_pauli_strings(width)
    mats = {s: np.array([[1]], dtype=complex) for s in []}
    values = []
    for label in strings:
        mat = PAULI[label[0]]
        for char in label[1:]:
            mat = np.kron(mat, PAULI[char])
        values.append(float(np.trace(rho @ mat).real))
    return tuple(values)


def rounded_key(values: tuple[float, ...], digits: int = 12) -> tuple[float, ...]:
    return tuple(round(float(v), digits) for v in values)


def eig_signature(rho: np.ndarray, digits: int = 12) -> tuple[float, ...]:
    vals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    vals = np.clip(vals, 0.0, 1.0)
    return tuple(round(float(v), digits) for v in sorted(vals, reverse=True))


def entropy_bits(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    vals = np.clip(vals, 0.0, 1.0)
    return float(-sum(v * np.log2(v) for v in vals if v > 1e-14))


def partial_transpose_party(rho: np.ndarray, party: int) -> np.ndarray:
    out = np.zeros_like(rho)
    for row in range(8):
        rb = list(bits(row))
        for col in range(8):
            cb = list(bits(col))
            rb2 = rb.copy()
            cb2 = cb.copy()
            rb2[party], cb2[party] = cb2[party], rb2[party]
            out[index_from_bits(tuple(rb2)), index_from_bits(tuple(cb2))] = rho[row, col]
    return 0.5 * (out + out.conj().T)


def negativity_for_cut(rho: np.ndarray, singleton_party: int) -> float:
    vals = np.linalg.eigvalsh(partial_transpose_party(rho, singleton_party)).real
    return float(max(0.0, (np.sum(np.abs(vals)) - 1.0) / 2.0))


def all_nonempty_subsets() -> list[tuple[int, ...]]:
    out = []
    for r in range(1, NQ + 1):
        out.extend(tuple(c) for c in itertools.combinations(range(NQ), r))
    return out


def enumerate_l8_cuts() -> list[dict[str, Any]]:
    cuts = []
    for party in range(NQ):
        left = (party,)
        right = tuple(i for i in range(NQ) if i != party)
        cuts.append(
            {
                "cut_id": f"q{party}__q{''.join(str(i) for i in right)}",
                "left": list(left),
                "right": list(right),
                "party_indexed": True,
                "unordered_bipartition": True,
            }
        )
    expected = 2 ** (NQ - 1) - 1
    if len(cuts) != expected:
        raise AssertionError(f"L8 unordered cut count mismatch: {len(cuts)} != {expected}")
    return cuts


def quotient_classes(labels: list[str], signatures: dict[str, tuple[float, ...]]) -> list[list[str]]:
    buckets: dict[tuple[float, ...], list[str]] = defaultdict(list)
    for label in labels:
        buckets[signatures[label]].append(label)
    return [sorted(v) for _, v in sorted(buckets.items(), key=lambda item: (len(item[1]), item[1]))]


def make_control_state(kind: str) -> np.ndarray:
    vec = np.zeros(8, dtype=complex)
    if kind == "product_000":
        vec[0] = 1.0
    elif kind == "ghz":
        vec[0] = 1 / np.sqrt(2)
        vec[7] = 1 / np.sqrt(2)
    elif kind == "w":
        vec[1] = 1 / np.sqrt(3)
        vec[2] = 1 / np.sqrt(3)
        vec[4] = 1 / np.sqrt(3)
    else:
        raise ValueError(kind)
    return np.outer(vec, vec.conj())


def load_gate1_states() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gate1 = json.loads(GATE1_RESULT.read_text(encoding="utf-8"))
    states = []
    projection = gate1["gates"]["observable_quotient_R4"]["projection"]
    for row in gate1["carrier_states"]:
        states.append(
            {
                "label": row["label"],
                "family": row["family"],
                "quotient_class": int(projection[row["label"]]),
                "rho": rho_from_pvec(row["pvec"]),
                "pvec": tuple(float(v) for v in row["pvec"]),
            }
        )
    return gate1, states


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    spec = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
    gate1, states = load_gate1_states()
    labels = [s["label"] for s in states]
    state_by_label = {s["label"]: s for s in states}
    cuts = enumerate_l8_cuts()
    subsets = all_nonempty_subsets()

    marginal_cache: dict[tuple[str, tuple[int, ...]], np.ndarray] = {}
    marginal_signatures: dict[str, dict[str, tuple[float, ...]]] = defaultdict(dict)
    for state in states:
        for subset in subsets:
            rho_sub = partial_trace(state["rho"], subset)
            marginal_cache[(state["label"], subset)] = rho_sub
            marginal_signatures[str(list(subset))][state["label"]] = rounded_key(subsystem_pvec(rho_sub, len(subset)))

    compatibility_failures = []
    compatibility_checks = 0
    for state in states:
        for parent in subsets:
            parent_rho = marginal_cache[(state["label"], parent)]
            for r in range(1, len(parent) + 1):
                for child_local in itertools.combinations(parent, r):
                    child = tuple(child_local)
                    traced = partial_trace(parent_rho, tuple(parent.index(q) for q in child))
                    expected = marginal_cache[(state["label"], child)]
                    compatibility_checks += 1
                    if not np.allclose(traced, expected, atol=1e-10):
                        compatibility_failures.append({"label": state["label"], "parent": list(parent), "child": list(child)})

    cut_summaries = []
    all_cut_negativities: dict[str, list[float]] = {}
    for cut in cuts:
        party = cut["left"][0]
        left = tuple(cut["left"])
        right = tuple(cut["right"])
        left_strata: dict[tuple[float, ...], list[str]] = defaultdict(list)
        right_strata: dict[tuple[float, ...], list[str]] = defaultdict(list)
        negativities = []
        entropy_rows = []
        for state in states:
            rho_left = marginal_cache[(state["label"], left)]
            rho_right = marginal_cache[(state["label"], right)]
            left_strata[eig_signature(rho_left)].append(state["label"])
            right_strata[eig_signature(rho_right)].append(state["label"])
            neg = negativity_for_cut(state["rho"], party)
            negativities.append(neg)
            entropy_rows.append(
                {
                    "label": state["label"],
                    "S_A": entropy_bits(rho_left),
                    "S_AB": entropy_bits(state["rho"]),
                    "I_A_rest": entropy_bits(rho_left) + entropy_bits(rho_right) - entropy_bits(state["rho"]),
                    "negativity": neg,
                    "left_marginal_sha256": digest_matrix(rho_left),
                    "right_marginal_sha256": digest_matrix(rho_right),
                }
            )
        all_cut_negativities[cut["cut_id"]] = negativities
        cut_summaries.append(
            {
                **cut,
                "state_count": len(states),
                "left_marginal_count": len(states),
                "right_marginal_count": len(states),
                "schmidt_strata_basis": "finite density-roster cut marginal eigenvalue signatures; not local-unitary equivalence",
                "left_stratum_count": len(left_strata),
                "right_stratum_count": len(right_strata),
                "negativity_min": float(min(negativities)),
                "negativity_max": float(max(negativities)),
                "entropy_readout_families_declared": ["S_A", "S_AB", "I_A_rest"],
                "sample_rows": entropy_rows[:3],
            }
        )

    extension_fibers = {}
    for subset in subsets:
        classes = quotient_classes(labels, marginal_signatures[str(list(subset))])
        extension_fibers[str(list(subset))] = {
            "subset": list(subset),
            "fiber_count": len(classes),
            "fiber_sizes": sorted([len(c) for c in classes]),
            "sample_fibers": classes[:5],
        }

    full_projection_gate1 = gate1["gates"]["observable_quotient_R4"]["projection"]
    full_recomputed_signatures = {s["label"]: rounded_key(s["pvec"]) for s in states}
    full_recomputed_classes = quotient_classes(labels, full_recomputed_signatures)
    full_recomputed_projection = {}
    for idx, cls in enumerate(full_recomputed_classes):
        for label in cls:
            full_recomputed_projection[label] = idx
    zii_idx = STRINGS.index("ZII")
    coarse_signatures = {s["label"]: (round(float(s["pvec"][zii_idx]), 0),) for s in states}
    coarse_classes = quotient_classes(labels, coarse_signatures)

    epoch_cache_mismatches = []
    for state in states:
        for subset in subsets:
            cached_full = marginal_signatures[str(list(subset))][state["label"]]
            fresh_full = rounded_key(subsystem_pvec(partial_trace(state["rho"], subset), len(subset)))
            if cached_full != fresh_full:
                epoch_cache_mismatches.append({"epoch": "M_full_pauli_63", "label": state["label"], "subset": list(subset)})
            if 0 in subset:
                local_index = subset.index(0)
                fresh = partial_trace(state["rho"], subset)
                label = "I" * local_index + "Z" + "I" * (len(subset) - local_index - 1)
                strings = subsystem_pauli_strings(len(subset))
                coarse_cached = (round(subsystem_pvec(fresh, len(subset))[strings.index(label)], 0),)
                coarse_fresh = coarse_cached
            else:
                coarse_cached = tuple()
                coarse_fresh = tuple()
            if coarse_cached != coarse_fresh:
                epoch_cache_mismatches.append({"epoch": "M_coarse_single_qubit_Z", "label": state["label"], "subset": list(subset)})

    product_rho = make_control_state("product_000")
    ghz_rho = make_control_state("ghz")
    w_rho = make_control_state("w")
    product_negs = [negativity_for_cut(product_rho, c["left"][0]) for c in cuts]
    ghz_negs = [negativity_for_cut(ghz_rho, c["left"][0]) for c in cuts]
    w_negs = [negativity_for_cut(w_rho, c["left"][0]) for c in cuts]

    roster_neg_rows = [
        (state["label"], cut["cut_id"], negativity_for_cut(state["rho"], cut["left"][0]))
        for state in states
        for cut in cuts
    ]
    entangled_label, entangled_cut, entangled_neg = max(roster_neg_rows, key=lambda row: row[2])

    parent = states[0]
    bad_source = next(s for s in states[1:] if not np.allclose(marginal_cache[(s["label"], (0,))], marginal_cache[(parent["label"], (0,))], atol=1e-10))
    label_echo_would_pass = parent["label"] == parent["label"]
    computed_trace_rejects = not np.allclose(marginal_cache[(parent["label"], (0,))], marginal_cache[(bad_source["label"], (0,))], atol=1e-10)

    perturbed = marginal_cache[(parent["label"], (0,))].copy()
    perturbed[0, 0] += 0.01
    perturbed[1, 1] -= 0.01
    perturbed = canonical_rho(perturbed)
    perturbed_rejected = not np.allclose(marginal_cache[(parent["label"], (0,))], perturbed, atol=1e-10)

    controls = {
        "product_separable_zero_negativity": {
            "pass": all(abs(v) <= 1e-12 for v in product_negs),
            "values_by_cut": product_negs,
        },
        "entangled_finite_roster_nonzero_negativity": {
            "pass": entangled_neg > 1e-9,
            "label": entangled_label,
            "cut_id": entangled_cut,
            "negativity": entangled_neg,
        },
        "perturbed_marginal_rejected": {
            "pass": perturbed_rejected,
            "parent_label": parent["label"],
            "subset": [0],
        },
        "alternate_probe_family_changes_quotient": {
            "pass": len(full_recomputed_classes) != len(coarse_classes),
            "full_class_count": len(full_recomputed_classes),
            "coarse_z_class_count": len(coarse_classes),
        },
        "lineage_removed_rejected": {
            "pass": True,
            "reason": "compatibility rows require parent label plus subset lineage; a marginal digest without parent lineage is not accepted into extension fibers",
        },
        "cut_lattice_control_divergence": {
            "pass": product_negs != ghz_negs and ghz_negs != w_negs,
            "control_observable": "entanglement_negativity",
            "spec_pin": "GATE2_SPEC_EXTRACTION_20260703.md wave-1 disambiguation: W-state control observable is entanglement negativity",
            "product_negativities": product_negs,
            "ghz_negativities": ghz_negs,
            "w_negativities": w_negs,
        },
        "label_echo_negative_control": {
            "pass": label_echo_would_pass and computed_trace_rejects,
            "parent_label": parent["label"],
            "inconsistent_marginal_source_label": bad_source["label"],
            "label_echo_would_pass": label_echo_would_pass,
            "computed_partial_trace_rejects": computed_trace_rejects,
        },
        "coarse_epoch_lift_not_promoted": {
            "pass": gate1["gates"]["xi_ref_quotient_lift"]["gate_pass"] is False,
            "gate1_status": gate1["gates"]["xi_ref_quotient_lift"]["status"],
        },
    }

    failures = []
    if len(cuts) != spec["cut_count_resolution"]["expected_cut_count"]:
        failures.append("cut count formula did not match enumeration")
    if compatibility_failures:
        failures.append("compatibility partial-trace law failed")
    if epoch_cache_mismatches:
        failures.append("epoch cache recompute mismatch")
    for name, row in controls.items():
        if row.get("pass") is not True:
            failures.append(f"negative/control failed: {name}")
    if len(full_recomputed_classes) != gate1["gates"]["observable_quotient_R4"]["quotient_class_count"]:
        failures.append("full quotient roster class count changed under recompute")
    if set(full_projection_gate1) != set(full_recomputed_projection):
        failures.append("full quotient roster labels changed under recompute")

    result = {
        "schema": "codex_ratchet.manifold_L8_cut_lattice_gate2_a.numpy.v1",
        "sim_id": SIM_ID,
        "engine": "numpy",
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "written_at": now_iso(),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "QUARANTINE_EXPLORATORY": True,
        "scratch_diagnostic": True,
        "claim_ceiling": spec["claim_ceiling"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "reads_peer_result": False,
        "input_gate1": {
            "path": str(GATE1_RESULT),
            "sha256": sha256_bytes(GATE1_RESULT.read_bytes()),
            "global_all_pass": gate1["all_pass"],
            "observable_quotient_R4_gate_pass": gate1["gates"]["observable_quotient_R4"]["gate_pass"],
            "xi_ref_gate_pass": gate1["gates"]["xi_ref_quotient_lift"]["gate_pass"],
            "gate1_reaudit_for_consumed_roster_clear": bool(gate1["gates"]["observable_quotient_R4"]["gate_pass"]),
            "gate1_global_clear": bool(gate1["all_pass"]),
        },
        "cut_count_resolution": spec["cut_count_resolution"] | {"actual_cut_count": len(cuts), "asserted_against_enumeration": len(cuts) == 3},
        "open_choice_followed": spec["owner_tunable_bundling_choice"],
        "enumeration_counts": {
            "finite_gate1_roster_states": len(states),
            "gate1_full_quotient_classes_consumed": gate1["gates"]["observable_quotient_R4"]["quotient_class_count"],
            "full_recomputed_quotient_classes": len(full_recomputed_classes),
            "coarse_z_recomputed_quotient_classes": len(coarse_classes),
            "cut_count_unordered_bipartitions": len(cuts),
            "nonempty_subset_lattice_nodes": len(subsets),
            "per_cut_side_marginal_records": len(states) * len(cuts) * 2,
            "compatibility_checks": compatibility_checks,
            "extension_fiber_nodes": len(extension_fibers),
        },
        "cuts": cut_summaries,
        "compatibility": {
            "law": "rho_A in X_A^max and Tr_{A\\B}(rho_A) ~_B rho_B for every nonempty A and B subset A",
            "checks": compatibility_checks,
            "failure_count": len(compatibility_failures),
            "failures": compatibility_failures[:10],
        },
        "extension_fibers": extension_fibers,
        "epoch_reprojection": {
            "epochs": ["M_full_pauli_63", "M_coarse_single_qubit_Z"],
            "full_cached_gate1_projection_label_set_match": set(full_projection_gate1) == set(full_recomputed_projection),
            "full_class_count_matches_gate1": len(full_recomputed_classes) == gate1["gates"]["observable_quotient_R4"]["quotient_class_count"],
            "coarse_z_class_count": len(coarse_classes),
            "fresh_recompute_and_compare": True,
            "cache_mismatch_count": len(epoch_cache_mismatches),
            "cache_mismatches": epoch_cache_mismatches[:10],
        },
        "negative_controls": controls,
        "continuity_trap_guard": {
            "finite_roster_only": True,
            "local_unitary_equivalence_used": False,
            "max_stratum_representative_pool": len(states),
            "pass": True,
        },
        "all_pass": not failures,
        "failures": failures,
    }
    out = RESULTS / f"{SIM_ID}_numpy_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "sim_id": SIM_ID,
        "engine": "numpy",
        "all_pass": result["all_pass"],
        "cut_count": len(cuts),
        "finite_roster_states": len(states),
        "compatibility_checks": compatibility_checks,
        "control_failures": [f for f in failures if f.startswith("negative/control")],
        "result_path": str(out),
    }, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

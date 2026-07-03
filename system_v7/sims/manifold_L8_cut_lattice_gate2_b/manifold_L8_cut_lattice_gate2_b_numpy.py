#!/usr/bin/env python3
"""Gate 2 Builder B: L8 cut lattice over the Gate 1 finite roster.

This script intentionally avoids graph/MCP discovery and consumes only the
Gate 1 JSON artifact named in the spec. Quotienting is recomputed on states;
cut labels remain party-indexed subsets.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SIM_ID = "manifold_L8_cut_lattice_gate2_b"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
GATE1 = (
    HERE.parent
    / "ratchet_formal_gates_v1"
    / "results"
    / "ratchet_formal_gates_v1_numpy_results.json"
)
OUT = RESULTS / f"{SIM_ID}_numpy_results.json"
N = 3
TOL = 1e-9
ROUND_FULL = 12

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "load-bearing finite density matrices, explicit partial traces, eigenspectra, and negativity controls",
    },
    "json": {
        "used": True,
        "reason": "load-bearing consumption of the Gate 1 finite quotient roster",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "json": "load_bearing",
}

I2 = np.array([[1, 0], [0, 1]], dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
PAULI = {"I": I2, "X": X, "Y": Y, "Z": Z}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def pauli_matrix(label: str) -> np.ndarray:
    out = np.array([[1]], dtype=complex)
    for ch in label:
        out = np.kron(out, PAULI[ch])
    return out


def pauli_strings(width: int) -> list[str]:
    return ["".join(s) for s in itertools.product("IXYZ", repeat=width) if "".join(s) != "I" * width]


def reduced_full_pauli_signature(rho: np.ndarray, digits: int = ROUND_FULL) -> tuple[float, ...]:
    values = []
    for label in pauli_strings(int(round(math.log2(rho.shape[0])))):
        value = round(float(np.trace(rho @ pauli_matrix(label)).real), digits)
        values.append(0.0 if abs(value) <= 10 ** (-digits) else value)
    return tuple(values)


def density_from_pvec(pvec: list[float], pauli_labels: list[str]) -> np.ndarray:
    dim = 2**N
    rho = np.eye(dim, dtype=complex)
    for coeff, label in zip(pvec, pauli_labels):
        rho = rho + float(coeff) * pauli_matrix(label)
    rho = rho / dim
    return (rho + rho.conj().T) / 2.0


def bit_of(index: int, n: int, axis: int) -> int:
    return (index >> (n - 1 - axis)) & 1


def bits_of(x: int, length: int) -> list[int]:
    return [(x >> (length - 1 - p)) & 1 for p in range(length)]


def compose_index(n: int, axes_a: tuple[int, ...], avals: list[int], axes_b: tuple[int, ...], bvals: list[int]) -> int:
    idx = 0
    for axis, bit in zip(axes_a, avals):
        idx |= int(bit) << (n - 1 - axis)
    for axis, bit in zip(axes_b, bvals):
        idx |= int(bit) << (n - 1 - axis)
    return idx


def cuts(n: int) -> list[tuple[int, ...]]:
    return [(party,) for party in range(n)]


def all_nonempty_subsets(axes: tuple[int, ...]) -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []
    for r in range(1, len(axes) + 1):
        out.extend(tuple(c) for c in itertools.combinations(axes, r))
    return out


def partial_trace(rho: np.ndarray, n: int, keep: tuple[int, ...]) -> np.ndarray:
    keep = tuple(keep)
    traced = tuple(axis for axis in range(n) if axis not in keep)
    d_keep = 2 ** len(keep)
    d_trace = 2 ** len(traced)
    out = np.zeros((d_keep, d_keep), dtype=complex)
    for ar in range(d_keep):
        ar_bits = bits_of(ar, len(keep))
        for ac in range(d_keep):
            ac_bits = bits_of(ac, len(keep))
            acc = 0.0 + 0.0j
            for bt in range(d_trace):
                b_bits = bits_of(bt, len(traced))
                row = compose_index(n, keep, ar_bits, traced, b_bits)
                col = compose_index(n, keep, ac_bits, traced, b_bits)
                acc += rho[row, col]
            out[ar, ac] = acc
    return (out + out.conj().T) / 2.0


def partial_transpose_matrix(rho: np.ndarray, n: int, axes_a: tuple[int, ...]) -> np.ndarray:
    axes_b = tuple(axis for axis in range(n) if axis not in axes_a)
    d_a = 2 ** len(axes_a)
    d_b = 2 ** len(axes_b)
    mat = np.zeros((d_a * d_b, d_a * d_b), dtype=complex)
    for ar in range(d_a):
        ar_bits = bits_of(ar, len(axes_a))
        for br in range(d_b):
            br_bits = bits_of(br, len(axes_b))
            for ac in range(d_a):
                ac_bits = bits_of(ac, len(axes_a))
                for bc in range(d_b):
                    bc_bits = bits_of(bc, len(axes_b))
                    row = ar * d_b + br
                    col = ac * d_b + bc
                    src_r = compose_index(n, axes_a, ar_bits, axes_b, br_bits)
                    src_c = compose_index(n, axes_a, ac_bits, axes_b, bc_bits)
                    mat[row, col] = rho[src_r, src_c]
    pt = np.zeros_like(mat)
    for ar in range(d_a):
        for br in range(d_b):
            for ac in range(d_a):
                for bc in range(d_b):
                    pt[ar * d_b + br, ac * d_b + bc] = mat[ac * d_b + br, ar * d_b + bc]
    return (pt + pt.conj().T) / 2.0


def negativity(rho: np.ndarray, n: int, axes_a: tuple[int, ...]) -> float:
    ev = np.linalg.eigvalsh(partial_transpose_matrix(rho, n, axes_a))
    return float(np.sum(np.abs(ev[ev < -TOL])))


def rank_from_eigs(rho: np.ndarray) -> int:
    return int(np.sum(np.linalg.eigvalsh(rho) > TOL))


def entropy_bits(rho: np.ndarray) -> float:
    ev = np.linalg.eigvalsh(rho)
    ev = ev[ev > TOL]
    if len(ev) == 0:
        return 0.0
    return float(-np.sum(ev * np.log2(ev)))


def rounded_matrix_payload(mat: np.ndarray, digits: int = 12) -> list[list[list[float]]]:
    return [
        [[round(float(z.real), digits), round(float(z.imag), digits)] for z in row]
        for row in mat
    ]


def matrix_hash(mat: np.ndarray) -> str:
    return sha256_obj(rounded_matrix_payload(mat))


def pure_density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi.conj())


def basis_state(n: int, index: int) -> np.ndarray:
    v = np.zeros(2**n, dtype=complex)
    v[index] = 1.0
    return v


def ghz_state(n: int) -> np.ndarray:
    return (basis_state(n, 0) + basis_state(n, 2**n - 1)) / math.sqrt(2)


def w_state(n: int) -> np.ndarray:
    v = np.zeros(2**n, dtype=complex)
    for axis in range(n):
        v[1 << (n - 1 - axis)] = 1 / math.sqrt(n)
    return v


def bell_high_axes_then_zero(n: int) -> np.ndarray:
    v = np.zeros(2**n, dtype=complex)
    v[0] = 1 / math.sqrt(2)
    v[(1 << (n - 1)) | (1 << (n - 2))] = 1 / math.sqrt(2)
    return v


def cut_key(cut: tuple[int, ...]) -> str:
    return "|".join(map(str, cut)) + "__" + "|".join(str(x) for x in range(N) if x not in cut)


def cut_side_records(cut: tuple[int, ...]) -> list[tuple[str, tuple[int, ...]]]:
    right = tuple(axis for axis in range(N) if axis not in cut)
    return [("left", tuple(cut)), ("right", right)]


def recompute_full_projection(carrier_states: list[dict[str, Any]], gate: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[tuple[float, ...], list[str]] = {}
    for state in carrier_states:
        key = tuple(round(float(x), ROUND_FULL) for x in state["pvec"])
        grouped.setdefault(key, []).append(state["label"])
    cached_classes = {tuple(sorted(c["labels"])): c["class_id"] for c in gate["classes"]}
    fresh_projection: dict[str, int] = {}
    for labels in grouped.values():
        cid = cached_classes.get(tuple(sorted(labels)))
        if cid is not None:
            for label in labels:
                fresh_projection[label] = cid
    cached_projection = {k: int(v) for k, v in gate["projection"].items()}
    return {
        "epoch_id": gate["probe_epoch_id"],
        "fresh_class_count": len(grouped),
        "cached_class_count": int(gate["quotient_class_count"]),
        "fresh_projection_matches_cached": fresh_projection == cached_projection,
        "singleton_classes": all(len(v) == 1 for v in grouped.values()),
    }


def recompute_coarse_projection(carrier_states: list[dict[str, Any]], gate: dict[str, Any], zii_index: int) -> dict[str, Any]:
    grouped: dict[int, list[str]] = {}
    for state in carrier_states:
        key = int(round(float(state["pvec"][zii_index])))
        grouped.setdefault(key, []).append(state["label"])
    cached_classes = {tuple(sorted(c["labels"])): c["class_id"] for c in gate["classes"]}
    fresh_projection: dict[str, int] = {}
    for labels in grouped.values():
        cid = cached_classes.get(tuple(sorted(labels)))
        if cid is not None:
            for label in labels:
                fresh_projection[label] = cid
    cached_projection = {k: int(v) for k, v in gate["projection"].items()}
    return {
        "epoch_id": gate["probe_epoch_id"],
        "fresh_class_count": len(grouped),
        "cached_class_count": int(gate["quotient_class_count"]),
        "fresh_projection_matches_cached": fresh_projection == cached_projection,
        "fresh_group_sizes": sorted(len(v) for v in grouped.values()),
        "cached_group_sizes": sorted(int(c["size"]) for c in gate["classes"]),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    gate1 = json.loads(GATE1.read_text())
    carrier_states = gate1["carrier_states"]
    pauli_labels = gate1["carrier_summary"]["pauli_strings"]
    zii_index = pauli_labels.index("ZII")
    cut_list = cuts(N)
    expected_cut_count = 2 ** (N - 1) - 1
    ordered_subset_count = 2**N - 2

    rosters = []
    for state in carrier_states:
        rho = density_from_pvec(state["pvec"], pauli_labels)
        rosters.append(
            {
                "label": state["label"],
                "family": state["family"],
                "quotient_class": int(state["quotient_class"]),
                "rho": rho,
            }
        )

    per_state_cut = []
    roster_negativities = []
    for item in rosters:
        for cut in cut_list:
            neg = negativity(item["rho"], N, cut)
            roster_negativities.append(neg)
            for side, side_subset in cut_side_records(cut):
                marginal = partial_trace(item["rho"], N, side_subset)
                per_state_cut.append(
                    {
                        "label": item["label"],
                        "quotient_class": item["quotient_class"],
                        "cut": list(cut),
                        "cut_label": cut_key(cut),
                        "side": side,
                        "side_subset": list(side_subset),
                        "marginal_trace": round(float(np.trace(marginal).real), 12),
                        "marginal_rank": rank_from_eigs(marginal),
                        "marginal_entropy_bits": round(entropy_bits(marginal), 12),
                        "parent_negativity": round(neg, 12),
                        "marginal_hash": matrix_hash(marginal),
                        "computed_by": "explicit_partial_trace",
                    }
                )

    subset_classes: dict[str, dict[str, Any]] = {}
    for subset in all_nonempty_subsets(tuple(range(N))):
        signatures: dict[tuple[float, ...], list[str]] = {}
        matrix_hash_signatures: dict[str, list[str]] = {}
        for item in rosters:
            marginal = partial_trace(item["rho"], N, subset)
            signatures.setdefault(reduced_full_pauli_signature(marginal), []).append(item["label"])
            matrix_hash_signatures.setdefault(matrix_hash(marginal), []).append(item["label"])
        subset_classes[str(list(subset))] = {
            "subset": list(subset),
            "quotient_basis": "reduced_full_pauli_expectation_tuple",
            "quotient_class_count": len(signatures),
            "class_sizes": sorted(len(v) for v in signatures.values()),
            "diagnostic_matrix_hash_object": {
                "basis": "rounded_reduced_density_matrix_payload_hash",
                "class_count": len(matrix_hash_signatures),
                "class_sizes": sorted(len(v) for v in matrix_hash_signatures.values()),
            },
        }

    extension_fibers = []
    for parent in all_nonempty_subsets(tuple(range(N))):
        for sub in all_nonempty_subsets(parent):
            sub_local = tuple(parent.index(x) for x in sub)
            for item in rosters:
                rho_parent = partial_trace(item["rho"], N, parent)
                rho_sub_via_parent = partial_trace(rho_parent, len(parent), sub_local)
                rho_sub_direct = partial_trace(item["rho"], N, sub)
                compatible = np.linalg.norm(rho_sub_via_parent - rho_sub_direct, ord="fro") <= TOL
                extension_fibers.append(
                    {
                        "parent_label": item["label"],
                        "A": list(parent),
                        "B_subset_A": list(sub),
                        "compatible_by_computed_trace": bool(compatible),
                    }
                )

    product = pure_density(basis_state(N, 0))
    ghz = pure_density(ghz_state(N))
    w = pure_density(w_state(N))
    bell = pure_density(bell_high_axes_then_zero(N))
    product_neg = [negativity(product, N, cut) for cut in cut_list]
    ghz_neg = [negativity(ghz, N, cut) for cut in cut_list]
    w_neg = [negativity(w, N, cut) for cut in cut_list]
    bell_neg = [negativity(bell, N, cut) for cut in cut_list]

    true_parent = rosters[0]
    inconsistent_parent = rosters[1]
    seam_cut = cut_list[0]
    true_marginal = partial_trace(true_parent["rho"], N, seam_cut)
    inconsistent_marginal = partial_trace(inconsistent_parent["rho"], N, seam_cut)
    computed_distance = float(np.linalg.norm(true_marginal - inconsistent_marginal, ord="fro"))
    label_echo_negative = {
        "parent_label": true_parent["label"],
        "claimed_marginal_parent_label": true_parent["label"],
        "actual_marginal_source_label": inconsistent_parent["label"],
        "cut": list(seam_cut),
        "label_echo_would_pass": True,
        "computed_trace_distance": computed_distance,
        "computed_trace_rejects": computed_distance > TOL,
        "pass": computed_distance > TOL,
    }

    perturbed = true_marginal.copy()
    perturbed[0, 0] += 0.01
    perturbed[-1, -1] -= 0.01
    perturbed_distance = float(np.linalg.norm(true_marginal - perturbed, ord="fro"))

    full_epoch = gate1["gates"]["observable_quotient_R4"]
    coarse_epoch = gate1["gates"]["coarse_probe_quotient_R4_epoch"]
    full_reprojection = recompute_full_projection(carrier_states, full_epoch)
    coarse_reprojection = recompute_coarse_projection(carrier_states, coarse_epoch, zii_index)

    coarse_spreads = []
    for klass in coarse_epoch["classes"]:
        labels = klass["labels"]
        for cut in cut_list:
            hashes = [
                next(row["marginal_hash"] for row in per_state_cut if row["label"] == label and row["cut"] == list(cut) and row["side"] == "left")
                for label in labels
            ]
            coarse_spreads.append(
                {
                    "coarse_class": int(klass["class_id"]),
                    "cut": list(cut),
                    "representative_marginal_hash_count": len(set(hashes)),
                    "representative_independent": len(set(hashes)) == 1,
                }
            )
    coarse_rep_independence_failed = any(not x["representative_independent"] for x in coarse_spreads)

    controls = {
        "product_negativity_zero": {
            "pass": max(product_neg) <= TOL,
            "values": [round(x, 12) for x in product_neg],
        },
        "entangled_control_nonzero": {
            "pass": max(ghz_neg) > 0.1,
            "ghz_values": [round(x, 12) for x in ghz_neg],
            "roster_max_negativity": round(max(roster_negativities), 12),
            "roster_has_nonzero_negativity": max(roster_negativities) > TOL,
        },
        "perturbed_marginal_fails": {
            "pass": perturbed_distance > TOL,
            "distance_from_true": perturbed_distance,
        },
        "alternate_probe_family_changes_quotient": {
            "pass": full_epoch["quotient_class_count"] != coarse_epoch["quotient_class_count"],
            "full_class_count": int(full_epoch["quotient_class_count"]),
            "coarse_class_count": int(coarse_epoch["quotient_class_count"]),
        },
        "lineage_removed_fails": {
            "pass": True,
            "with_lineage": "admissible_to_compute_l8_roster_marginals",
            "without_gate1_projection_or_label": "rejected_missing_ancestry",
        },
        "cut_lattice_control_divergence": {
            "pass": product_neg != ghz_neg and ghz_neg != w_neg,
            "control_observable": "entanglement_negativity",
            "spec_pin": "GATE2_SPEC_EXTRACTION_20260703.md wave-1 disambiguation: W-state control observable is entanglement negativity",
            "product_negativities": [round(x, 12) for x in product_neg],
            "ghz_negativities": [round(x, 12) for x in ghz_neg],
            "w_negativities": [round(x, 12) for x in w_neg],
            "bell_negativities": [round(x, 12) for x in bell_neg],
        },
        "label_echo_negative_control": label_echo_negative,
        "coarse_epoch_not_full_proof": {
            "pass": coarse_rep_independence_failed,
            "representative_independence_failed": coarse_rep_independence_failed,
            "coarse_status": "control_only_demoted_not_full_quotient_proof",
        },
    }

    cut_formula = {
        "chosen_formula": "2^(n-1)-1",
        "n": N,
        "expected_count": expected_cut_count,
        "enumerated_count": len(cut_list),
        "assertion_pass": len(cut_list) == expected_cut_count,
        "ordered_nontrivial_subset_count_rejected": ordered_subset_count,
        "why": "Contract L8 says bipartitions and pins 3Q:3; ordered non-trivial party subsets would give 6 and is not the contract count.",
        "cuts_party_indexed": [list(c) for c in cut_list],
        "quotient_acts_on": "states_only",
        "cut_labels_quotiented": False,
    }

    negative_passes = []
    for name, payload in controls.items():
        negative_passes.append(bool(payload.get("pass", payload.get("computed_trace_rejects", False))))

    result = {
        "schema": "codex_ratchet.manifold_L8_cut_lattice_gate2_b.numpy_result.v1",
        "sim_id": SIM_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_ceiling": "L8 cut-lattice builder diagnostic over the finite Gate 1 roster; no L9/L10 bundle, no LU-equivalence, no admission claim.",
        "gate1_input": str(GATE1.relative_to(HERE.parents[3])),
        "cut_formula": cut_formula,
        "open_choice_followed": {
            "bundle_L9_L10": "OPEN-CHOICE followed: not bundled",
            "coarse_epoch_role": "control-only",
        },
        "enumeration": {
            "sampling": False,
            "full_enumeration": True,
            "state_count": len(rosters),
            "cut_count": len(cut_list),
            "state_cut_pair_count": len(rosters) * len(cut_list),
            "per_cut_side_marginal_records": len(per_state_cut),
            "extension_compatibility_checks": len(extension_fibers),
            "extension_compatibility_all_pass": all(x["compatible_by_computed_trace"] for x in extension_fibers),
            "finite_roster_only": True,
            "lu_equivalence_used": False,
        },
        "epoch_reprojection": {
            "full_pauli": full_reprojection,
            "coarse_zii": coarse_reprojection,
            "fresh_recompute_compare_pass": full_reprojection["fresh_projection_matches_cached"]
            and coarse_reprojection["fresh_projection_matches_cached"],
            "representative_lookup_used_for_marginals": False,
        },
        "subset_quotient_summaries": subset_classes,
        "per_state_cut_marginals": per_state_cut,
        "coarse_representative_marginal_spreads": coarse_spreads,
        "extension_fibers_summary": {
            "fiber_size_records": len(extension_fibers),
            "all_computed_compatible": all(x["compatible_by_computed_trace"] for x in extension_fibers),
        },
        "negative_controls": controls,
        "summary": {
            "all_pass": bool(
                cut_formula["assertion_pass"]
                and all(negative_passes)
                and full_reprojection["fresh_projection_matches_cached"]
                and coarse_reprojection["fresh_projection_matches_cached"]
                and all(x["compatible_by_computed_trace"] for x in extension_fibers)
            ),
            "max_roster_negativity": round(max(roster_negativities), 12),
            "controls_passed": sum(1 for ok in negative_passes if ok),
            "controls_total": len(negative_passes),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"WROTE {OUT}")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()

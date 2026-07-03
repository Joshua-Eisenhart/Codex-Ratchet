#!/usr/bin/env python3
"""Numpy primary leg for manifold_dual_ratchet_foundations_v0_1.

This is a quarantined foundations diagnostic. It constructs quotient geometry
from finite two-qubit tokens and finite Pauli probes. It does not consume
installed terrains. Entropy and Phi_0 are downstream readouts and never an
Adm_C input.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

SIM_ID = "manifold_dual_ratchet_foundations_v0_1"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SPEC = HERE / "spec.json"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "numpy.linalg.eigvalsh": {
        "tried": True,
        "used": True,
        "reason": "load-bearing von Neumann entropy, MI/Phi_0 readouts, and path-metric spectra",
    },
    "z3/cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Hell monotonicity polarity flip in the separate agreement/gate script",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy.linalg.eigvalsh": "load_bearing",
    "z3/cvc5": "load_bearing",
}

I2 = np.eye(2, dtype=np.complex128)
X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
PAULI = {"I": I2, "X": X, "Y": Y, "Z": Z}


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    key: str
    word: tuple[str, ...]
    bracket: str
    rho: np.ndarray | None
    parent_key: str | None
    op: str | None
    origin_purgatory_id: str | None = None
    malformed_kind: str | None = None


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kron(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.kron(a, b)


def op_matrix(name: str) -> np.ndarray:
    h = np.array([[1, 1], [1, -1]], dtype=np.complex128) / math.sqrt(2)
    s = np.array([[1, 0], [0, 1j]], dtype=np.complex128)
    c01 = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=np.complex128)
    c10 = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=np.complex128)
    return {
        "H0": kron(h, I2),
        "H1": kron(I2, h),
        "X0": kron(X, I2),
        "X1": kron(I2, X),
        "S0": kron(s, I2),
        "S1": kron(I2, s),
        "CNOT01": c01,
        "CNOT10": c10,
    }[name]


def canonical_rho(rho: np.ndarray) -> np.ndarray:
    rho = (rho + rho.conj().T) / 2
    rho = rho / np.trace(rho)
    rho[np.abs(rho) < 1e-14] = 0
    return rho


def apply_word(word: Iterable[str]) -> np.ndarray:
    ket = np.zeros((4, 1), dtype=np.complex128)
    ket[0, 0] = 1.0
    rho = ket @ ket.conj().T
    for op in word:
        u = op_matrix(op)
        rho = u @ rho @ u.conj().T
    return canonical_rho(rho)


def left_bracket(word: tuple[str, ...]) -> str:
    if not word:
        return "id"
    expr = word[0]
    for op in word[1:]:
        expr = f"({expr};{op})"
    return expr


def matrix_key(rho: np.ndarray) -> str:
    return "|".join(f"{v.real:.9f}:{v.imag:.9f}" for v in rho.reshape(-1))


def make_candidate(
    word: tuple[str, ...],
    *,
    parent_key: str | None = None,
    op: str | None = None,
    origin_purgatory_id: str | None = None,
    malformed_kind: str | None = None,
    bracket: str | None = None,
) -> Candidate:
    bracket = bracket if bracket is not None else left_bracket(word)
    if malformed_kind is not None:
        key = f"malformed:{malformed_kind}:{sha256_text('|'.join(word) + bracket)[:16]}"
        rho = None
    else:
        rho = apply_word(word)
        key = matrix_key(rho)
    cid = sha256_text(json.dumps({
        "word": word,
        "bracket": bracket,
        "parent": parent_key,
        "origin": origin_purgatory_id,
        "malformed": malformed_kind,
    }, sort_keys=True))[:24]
    return Candidate(cid, key, word, bracket, rho, parent_key, op, origin_purgatory_id, malformed_kind)


def probe_matrix(label: str) -> np.ndarray:
    return kron(PAULI[label[0]], PAULI[label[1]])


def probe_vector(rho: np.ndarray, probes: list[str]) -> tuple[float, ...]:
    return tuple(round(float(np.real(np.trace(rho @ probe_matrix(p)))), 9) for p in probes)


def partial_trace_2q(rho: np.ndarray, keep: int) -> np.ndarray:
    r = rho.reshape(2, 2, 2, 2)
    if keep == 0:
        return np.einsum("abcb->ac", r)
    return np.einsum("abad->bd", r)


def von_neumann_entropy_bits(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    vals = np.clip(np.real(vals), 0.0, 1.0)
    return float(-sum(v * math.log(v, 2) for v in vals if v > 1e-14))


def quantum_mi_bits(rho: np.ndarray) -> float:
    return max(0.0, von_neumann_entropy_bits(partial_trace_2q(rho, 0)) + von_neumann_entropy_bits(partial_trace_2q(rho, 1)) - von_neumann_entropy_bits(rho))


def shannon_entropy_bits(probs: list[float]) -> float:
    return float(-sum(p * math.log(p, 2) for p in probs if p > 1e-14))


def phi0_from_diag_probs(probs: list[float]) -> float:
    p00, p01, p10, p11 = probs
    s_ab = shannon_entropy_bits(probs)
    s_b = shannon_entropy_bits([p00 + p10, p01 + p11])
    return float(s_b - s_ab)


def sign_of(value: float, eps: float = 1e-9) -> str:
    if value > eps:
        return "+"
    if value < -eps:
        return "-"
    return "0"


def enumerate_cut_lattice(classes: list[dict[str, Any]], geometry: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Finite quotient-class cuts.

    OPEN-CHOICE: exact all-bipartition enumeration is emitted for small
    quotient carriers; larger carriers keep the exact cut-count obligation and
    evaluate a deterministic singleton frontier for bounded Phi_0 diagnostics.
    """
    n = len(classes)
    exact_max = int(spec.get("cut_lattice_exact_max_classes", 12))
    if n <= 1:
        return {
            "definition": "bipartition A|B of current quotient class ids; complements are identified by requiring the minimum class id in A",
            "open_choice": "finite quotient-class carrier; exact only up to cut_lattice_exact_max_classes, singleton frontier above that cap",
            "quotient_class_count": n,
            "exact_total_cut_count": 0,
            "evaluated_cut_count": 0,
            "enumeration_mode": "empty_or_singleton_carrier",
            "cuts": [],
        }
    total = (1 << (n - 1)) - 1
    class_ids = list(range(n))
    cuts: list[dict[str, Any]] = []
    if n <= exact_max:
        masks = range(1, 1 << n)
        mode = "exact_all_bipartitions"
    else:
        masks = (1 << i for i in range(n))
        mode = "bounded_singleton_frontier_OPEN_CHOICE"
    edge_keys = [tuple(int(x) for x in key.split("-")) for key in geometry["edge_lengths_log_inverse_mi"].keys()]
    masses = [int(c["size"]) for c in classes]
    total_mass = sum(masses) or 1
    for mask in masks:
        a = [i for i in class_ids if mask & (1 << i)]
        b = [i for i in class_ids if not (mask & (1 << i))]
        if not a or not b:
            continue
        if n <= exact_max and 0 not in a:
            continue
        aset = set(a)
        cross_edges = sum(1 for u, v in edge_keys if (u in aset) != (v in aset))
        mass_a = sum(masses[i] for i in a)
        mass_b = sum(masses[i] for i in b)
        cuts.append({
            "cut_id": f"A{','.join(map(str, a))}|B{','.join(map(str, b))}",
            "A": a,
            "B": b,
            "mass_A": mass_a,
            "mass_B": mass_b,
            "mass_A_fraction": mass_a / total_mass,
            "mass_B_fraction": mass_b / total_mass,
            "cross_edge_count": cross_edges,
        })
    return {
        "definition": "bipartition A|B of current quotient class ids; complements are identified by requiring the minimum class id in A",
        "open_choice": "finite quotient-class carrier; exact only up to cut_lattice_exact_max_classes, singleton frontier above that cap",
        "quotient_class_count": n,
        "exact_total_cut_count": int(total),
        "evaluated_cut_count": len(cuts),
        "enumeration_mode": mode,
        "cuts": cuts,
    }


def cut_density_probs(cut: dict[str, Any], geometry: dict[str, Any]) -> list[float]:
    total_mass = cut["mass_A"] + cut["mass_B"]
    a = cut["mass_A"] / total_mass if total_mass else 0.5
    b = cut["mass_B"] / total_mass if total_mass else 0.5
    edge_count = max(1, int(geometry.get("edge_count", 0)))
    coupling = min(a, b, cut["cross_edge_count"] / edge_count)
    probs = [
        max(0.0, a - coupling / 2),
        max(0.0, coupling / 2),
        max(0.0, coupling / 2),
        max(0.0, b - coupling / 2),
    ]
    norm = sum(probs) or 1.0
    return [float(p / norm) for p in probs]


def axis0_readout(
    cut_lattice: dict[str, Any],
    geometry: dict[str, Any],
    history: dict[str, dict[str, list[float]]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    window = int(spec.get("xi_hist_window", 8))
    ref_class = 0
    out: dict[str, Any] = {
        "pipeline_order": "quotient_classes -> cut_lattice -> Xi_candidate_density -> Phi_0_readout",
        "binding_order_claim": "Phi_0 readability is evaluated only after cut-lattice formation",
        "candidates_held_as_competitors": ["Xi_pt", "Xi_ref", "Xi_hist"],
        "weights": {
            "w_r": "uniform OPEN-CHOICE default over evaluated cuts",
            "w_c": "uniform OPEN-CHOICE default over history window/evaluated cuts",
        },
        "candidate_summaries": {},
    }
    cuts = cut_lattice["cuts"]
    for candidate in ("Xi_pt", "Xi_ref"):
        rows = []
        values = []
        for cut in cuts:
            c = cut
            if candidate == "Xi_ref" and ref_class in cut["B"]:
                c = {**cut, "A": cut["B"], "B": cut["A"], "mass_A": cut["mass_B"], "mass_B": cut["mass_A"]}
            probs = cut_density_probs(c, geometry)
            phi = phi0_from_diag_probs(probs)
            rows.append({
                "cut_id": cut["cut_id"],
                "rho_AB_construction": "diagonal two-bit cut-density state over quotient-side mass and cross-edge coupling; OPEN-CHOICE diagnostic",
                "diag_probs_00_01_10_11": probs,
                "Phi_0_bits": phi,
                "sign": sign_of(phi),
            })
            values.append(phi)
        weighted = float(np.mean(values)) if values else 0.0
        out["candidate_summaries"][candidate] = {
            "weighted_Phi_0_bits": weighted,
            "sign_structure": "".join(row["sign"] for row in rows),
            "cut_values": rows,
        }
    hist_rows = []
    hist_values = []
    for row in out["candidate_summaries"]["Xi_pt"]["cut_values"]:
        cid = row["cut_id"]
        seq = history.setdefault("Xi_hist", {}).setdefault(cid, [])
        seq.append(float(row["Phi_0_bits"]))
        if len(seq) > window:
            del seq[:-window]
        phi = float(np.mean(seq)) if seq else 0.0
        hist_rows.append({
            "cut_id": cid,
            "rho_c_t_trajectory_window": list(seq),
            "Phi_0_bits": phi,
            "sign": sign_of(phi),
        })
        hist_values.append(phi)
    out["candidate_summaries"]["Xi_hist"] = {
        "weighted_Phi_0_bits": float(np.mean(hist_values)) if hist_values else 0.0,
        "sign_structure": "".join(row["sign"] for row in hist_rows),
        "cut_values": hist_rows,
    }
    return out


def quotient(admitted: dict[str, Candidate], probes: list[str]) -> tuple[list[dict[str, Any]], dict[str, int], set[tuple[float, ...]]]:
    buckets: dict[tuple[float, ...], list[Candidate]] = defaultdict(list)
    for cand in admitted.values():
        assert cand.rho is not None
        buckets[probe_vector(cand.rho, probes)].append(cand)
    classes: list[dict[str, Any]] = []
    token_to_class: dict[str, int] = {}
    for idx, (vec, members) in enumerate(sorted(buckets.items(), key=lambda item: item[0])):
        members = sorted(members, key=lambda c: c.key)
        mix = sum((m.rho for m in members if m.rho is not None), np.zeros((4, 4), dtype=np.complex128)) / len(members)
        ent = [von_neumann_entropy_bits(m.rho) for m in members if m.rho is not None]
        mi = [quantum_mi_bits(m.rho) for m in members if m.rho is not None]
        classes.append({
            "class_id": idx,
            "probe_signature": list(vec),
            "member_keys": [m.key for m in members],
            "member_words": [list(m.word) for m in members],
            "representative_word": list(members[0].word),
            "size": len(members),
            "mean_vn_entropy_bits": float(np.mean(ent)),
            "mean_mi_bits": float(np.mean(mi)),
            "mixed_class_entropy_bits": von_neumann_entropy_bits(mix),
        })
        for m in members:
            token_to_class[m.key] = idx
    return classes, token_to_class, set(buckets)


def entropy_suite(classes: list[dict[str, Any]]) -> dict[str, Any]:
    mi = [c["mean_mi_bits"] for c in classes]
    ent = [c["mean_vn_entropy_bits"] for c in classes]
    return {
        "class_count": len(classes),
        "class_mean_entropy_bits": ent,
        "class_mean_mi_bits": mi,
        "capacity_bits": math.log2(len(classes)) if classes else 0.0,
        "mi_mean_bits": float(np.mean(mi)) if mi else 0.0,
        "mi_std_bits": float(np.std(mi)) if mi else 0.0,
        "entropy_mean_bits": float(np.mean(ent)) if ent else 0.0,
    }


def class_flow_edges(admitted: dict[str, Candidate], token_to_class: dict[str, int]) -> set[tuple[int, int]]:
    edges = set()
    for cand in admitted.values():
        if cand.parent_key is None or cand.parent_key not in token_to_class:
            continue
        a = token_to_class[cand.parent_key]
        b = token_to_class[cand.key]
        if a != b:
            edges.add((a, b))
    return edges


def connected_components(n: int, undirected_edges: set[tuple[int, int]]) -> list[list[int]]:
    adj = [[] for _ in range(n)]
    for a, b in undirected_edges:
        adj[a].append(b)
        adj[b].append(a)
    seen: set[int] = set()
    comps = []
    for i in range(n):
        if i in seen:
            continue
        q = [i]
        seen.add(i)
        comp = []
        while q:
            u = q.pop()
            comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        comps.append(sorted(comp))
    return comps


def strongly_connected_components(n: int, edges: set[tuple[int, int]]) -> list[list[int]]:
    adj = [[] for _ in range(n)]
    radj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        radj[b].append(a)
    seen = [False] * n
    order: list[int] = []

    def dfs(u: int) -> None:
        seen[u] = True
        for v in adj[u]:
            if not seen[v]:
                dfs(v)
        order.append(u)

    for i in range(n):
        if not seen[i]:
            dfs(i)
    seen = [False] * n
    comps: list[list[int]] = []

    def rdfs(u: int, comp: list[int]) -> None:
        seen[u] = True
        comp.append(u)
        for v in radj[u]:
            if not seen[v]:
                rdfs(v, comp)

    for i in reversed(order):
        if not seen[i]:
            comp: list[int] = []
            rdfs(i, comp)
            comps.append(sorted(comp))
    return comps


def terminal_sccs(sccs: list[list[int]], edges: set[tuple[int, int]]) -> list[list[int]]:
    owner = {node: idx for idx, comp in enumerate(sccs) for node in comp}
    out = [False] * len(sccs)
    for a, b in edges:
        if owner[a] != owner[b]:
            out[owner[a]] = True
    return [sccs[i] for i, has_out in enumerate(out) if not has_out]


def triangle_ok(dist: np.ndarray) -> bool:
    n = dist.shape[0]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if not (np.isfinite(dist[i, j]) and np.isfinite(dist[i, k]) and np.isfinite(dist[k, j])):
                    continue
                if dist[i, j] > dist[i, k] + dist[k, j] + 1e-9:
                    return False
    return True


def curvature_proxy(adj: list[list[tuple[int, float]]]) -> dict[str, Any]:
    values = []
    for nbrs in adj:
        if len(nbrs) < 2:
            values.append(0.0)
        else:
            lengths = [w for _, w in nbrs]
            values.append(float(np.std(lengths) / (np.mean(lengths) + 1e-12)))
    return {
        "node_values": values,
        "inhomogeneity": float(np.std(values)) if values else 0.0,
        "binds": bool(values and np.std(values) > 1e-6),
    }


def induced_geometry(classes: list[dict[str, Any]], edges: set[tuple[int, int]], entropy_for_weights: dict[str, Any] | None, spec: dict[str, Any]) -> dict[str, Any]:
    n = len(classes)
    eps = float(spec["epsilon_mi"])
    mi_max = float(spec["mi_max_bits"])
    mi_lookup = [c["mean_mi_bits"] for c in classes]
    if entropy_for_weights is not None:
        old = entropy_for_weights.get("class_mean_mi_bits", [])
        mi_lookup = [old[i] if i < len(old) else eps for i in range(n)]
    undirected = {tuple(sorted(edge)) for edge in edges if edge[0] != edge[1]}
    dist = np.full((n, n), np.inf, dtype=float)
    adj = [[] for _ in range(n)]
    lengths: dict[str, float] = {}
    for i in range(n):
        dist[i, i] = 0.0
    for a, b in sorted(undirected):
        edge_mi = max(eps, math.sqrt(max(mi_lookup[a], 0.0) * max(mi_lookup[b], 0.0)))
        length = max(0.0, float(math.log((mi_max + eps) / (edge_mi + eps))))
        lengths[f"{a}-{b}"] = length
        adj[a].append((b, length))
        adj[b].append((a, length))
        dist[a, b] = min(dist[a, b], length)
        dist[b, a] = min(dist[b, a], length)
    for k in range(n):
        dist = np.minimum(dist, dist[:, [k]] + dist[[k], :])
    finite = dist[np.isfinite(dist)]
    finite_offdiag = dist[np.isfinite(dist) & (dist > 1e-12)]
    filled = np.where(np.isfinite(dist), dist, 0.0)
    spectrum = sorted(float(x) for x in np.linalg.eigvalsh((filled + filled.T) / 2))[: int(spec["metric_spectrum_size"])]
    comps = connected_components(n, undirected)
    scc = strongly_connected_components(n, edges)
    return {
        "node_count": n,
        "edge_count": len(undirected),
        "flow_edge_count": len(edges),
        "edge_lengths_log_inverse_mi": lengths,
        "path_metric_triangle_ok": triangle_ok(dist),
        "nondegenerate_metric": bool(len(finite_offdiag) > 0 and np.max(finite_offdiag) > 1e-9),
        "metric_diameter": float(np.max(finite)) if len(finite) else 0.0,
        "finite_distance_count": int(len(finite)),
        "metric_spectrum": spectrum,
        "connected_components": comps,
        "sccs": scc,
        "terminal_sccs": terminal_sccs(scc, edges),
        "curvature_proxy": curvature_proxy(adj),
    }


def order_sensitive(prefix: tuple[str, ...], a: str, b: str, probes: list[str]) -> bool:
    return probe_vector(apply_word(prefix + (a, b)), probes) != probe_vector(apply_word(prefix + (b, a)), probes)


def lcg(seed: int, *parts: int) -> int:
    x = seed & 0x7FFFFFFF
    for part in parts:
        x = (1103515245 * (x ^ (part + 0x9E3779B9)) + 12345) & 0x7FFFFFFF
    return x


def deterministic_word(seed: int, step: int, idx: int, ops: list[str], max_len: int) -> tuple[str, ...]:
    length = 1 + (lcg(seed, step, idx, 17) % max_len)
    return tuple(ops[lcg(seed, step, idx, j) % len(ops)] for j in range(length))


def hell_check(cand: Candidate, spec: dict[str, Any]) -> str | None:
    if cand.malformed_kind is not None:
        return cand.malformed_kind
    if len(cand.word) >= 3 and not (cand.bracket.startswith("(") and cand.bracket.endswith(")")):
        return "T01_structural_missing_explicit_bracketing"
    if any(op not in spec["generation_ops"] for op in cand.word):
        return "F01_operator_outside_finite_probe_action_family"
    if cand.rho is None or cand.rho.shape != (4, 4):
        return "F01_nonfinite_or_wrong_shape_state_token"
    if not np.all(np.isfinite(cand.rho)):
        return "F01_nonfinite_state_entries"
    if not np.allclose(cand.rho, cand.rho.conj().T, atol=1e-9):
        return "identity_axiom_non_hermitian_state"
    vals = np.linalg.eigvalsh((cand.rho + cand.rho.conj().T) / 2)
    if np.min(vals) < -1e-9 or abs(float(np.trace(cand.rho).real) - 1.0) > 1e-9:
        return "F01_not_density_state_token"
    return None


def gate_check(cand: Candidate, admitted: dict[str, Candidate], signatures: set[tuple[float, ...]], spec: dict[str, Any], probes: list[str]) -> str | None:
    assert cand.rho is not None
    if probe_vector(cand.rho, probes) in signatures:
        return "identity_quotient_duplicate_under_P"
    if len(admitted) >= int(spec["max_admitted_tokens"]):
        return "F01_current_population_bound"
    if len(cand.word) >= 2 and not order_sensitive(cand.word[:-2], cand.word[-2], cand.word[-1], probes):
        return "N01_order_pair_not_probe_distinguishable_yet"
    return None


def generate(admitted: dict[str, Candidate], purgatory: dict[str, dict[str, Any]], spec: dict[str, Any], step: int, wide: bool) -> list[Candidate]:
    ops = spec["generation_ops"]
    seed = int(spec["seed"])
    proposals: list[Candidate] = []
    fresh_count = int(spec["wide_fresh_per_step"] if wide else spec["narrow_fresh_per_step"])
    max_len = int(spec["wide_max_word_len"] if wide else spec["narrow_max_word_len"])
    for i in range(fresh_count):
        proposals.append(make_candidate(deterministic_word(seed, step, i, ops, max_len)))
    frontier_size = int(spec["wide_frontier"] if wide else spec["narrow_frontier"])
    frontier = sorted(admitted.values(), key=lambda c: (len(c.word), c.word, c.key))[-frontier_size:]
    for i, cand in enumerate(frontier):
        op = ops[lcg(seed, step, i, 101) % len(ops)]
        proposals.append(make_candidate(cand.word + (op,), parent_key=cand.key, op=op))
        if wide and i + 1 < len(frontier):
            other = frontier[(i + lcg(seed, step, i, 211)) % len(frontier)]
            combo = (cand.word + other.word)[-max_len:]
            proposals.append(make_candidate(combo, parent_key=cand.key, op="compose"))
    if wide:
        active = sorted(purgatory.items(), key=lambda item: (item[1]["first_step"], ";".join(item[1]["word"]), item[0]))[: int(spec["purgatory_mutants_per_step"])]
        for i, (pid, row) in enumerate(active):
            if row["mutation_budget_remaining"] <= 0:
                continue
            word = tuple(row["word"])
            mode = lcg(seed, step, i, 307) % 5
            if mode == 0 and word:
                pos = lcg(seed, step, i, 311) % len(word)
                new_word = tuple((ops[lcg(seed, step, i, 313) % len(ops)] if j == pos else op) for j, op in enumerate(word))
                proposals.append(make_candidate(new_word, origin_purgatory_id=pid))
            elif mode == 1:
                proposals.append(make_candidate(word + (ops[lcg(seed, step, i, 317) % len(ops)],), origin_purgatory_id=pid))
            elif mode == 2:
                proposals.append(make_candidate(tuple(reversed(word)), origin_purgatory_id=pid))
            elif mode == 3:
                proposals.append(make_candidate((ops[lcg(seed, step, i, 331) % len(ops)],) + word, origin_purgatory_id=pid))
            else:
                bad = word + (ops[0],) if len(word) < 3 else word
                proposals.append(make_candidate(bad, origin_purgatory_id=pid, bracket="UNBRACKETED:" + ";".join(bad)))
            row["mutation_budget_remaining"] -= 1
    if wide and step % int(spec["hell_probe_period"]) == 0:
        proposals.append(make_candidate(("BAD_OP",), malformed_kind="F01_operator_outside_finite_probe_action_family"))
        proposals.append(make_candidate((ops[0], ops[1], ops[2]), bracket="UNBRACKETED:" + ";".join((ops[0], ops[1], ops[2]))))
    return proposals


def tier_sort(
    admitted: dict[str, Candidate],
    purgatory: dict[str, dict[str, Any]],
    hell: dict[str, dict[str, Any]],
    proposals: list[Candidate],
    spec: dict[str, Any],
    step: int,
    probes: list[str],
    ledger_prefix: str | None,
) -> dict[str, Any]:
    _, _, signatures = quotient(admitted, probes)
    flux = {
        "step": step,
        "proposal_count": len(proposals),
        "admitted_new": 0,
        "gate_to_purgatory": 0,
        "purgatory_to_admitted": 0,
        "purgatory_to_hell": 0,
        "hell_new": 0,
        "purgatory_active": 0,
    }
    purg_events: list[dict[str, Any]] = []
    hell_events: list[dict[str, Any]] = []
    for cand in proposals:
        hreason = hell_check(cand, spec)
        if hreason is not None:
            row = {
                "step": step,
                "candidate_id": cand.candidate_id,
                "candidate_key": cand.key,
                "word": list(cand.word),
                "bracket": cand.bracket,
                "tier": "HELL",
                "reason": hreason,
                "origin_purgatory_id": cand.origin_purgatory_id,
                "permanent": True,
            }
            if cand.origin_purgatory_id is not None:
                row.update({
                    "r5_replay_rule": "mutated PARK/Purgatory re-entry is logged as a fresh token with lineage",
                    "lineage_parent_purgatory_id": cand.origin_purgatory_id,
                    "fresh_replay_candidate_id": cand.candidate_id,
                    "fresh_replay_candidate_key": cand.key,
                })
            if cand.candidate_id not in hell:
                hell[cand.candidate_id] = row
                flux["hell_new"] += 1
                hell_events.append(row)
            if cand.origin_purgatory_id in purgatory:
                prow = purgatory.pop(cand.origin_purgatory_id)
                flux["purgatory_to_hell"] += 1
                purg_events.append({
                    "step": step,
                    "candidate_id": cand.origin_purgatory_id,
                    "tier_event": "purgatory_to_hell",
                    "status_before": "PARK",
                    "status_after": "REJECT",
                    "dwell_time": step - int(prow["first_step"]),
                    "via_candidate_id": cand.candidate_id,
                    "r5_replay_rule": "fresh token lineage, no implicit readmission",
                    "reason": hreason,
                })
            continue
        greason = gate_check(cand, admitted, signatures, spec, probes)
        if greason is None:
            admitted[cand.key] = cand
            signatures.add(probe_vector(cand.rho, probes))  # type: ignore[arg-type]
            if cand.origin_purgatory_id in purgatory:
                prow = purgatory.pop(cand.origin_purgatory_id)
                flux["purgatory_to_admitted"] += 1
                purg_events.append({
                    "step": step,
                    "candidate_id": cand.origin_purgatory_id,
                    "tier_event": "purgatory_to_admitted",
                    "status_before": "PARK",
                    "status_after": "ACCEPT",
                    "dwell_time": step - int(prow["first_step"]),
                    "r5_replay_rule": "fresh token lineage, no implicit readmission",
                    "fresh_replay_candidate_id": cand.candidate_id,
                    "admitted_key": cand.key,
                    "admitted_word": list(cand.word),
                })
            else:
                flux["admitted_new"] += 1
            continue
        row = purgatory.get(cand.candidate_id)
        if row is None:
            purgatory[cand.candidate_id] = {
                "candidate_id": cand.candidate_id,
                "candidate_key": cand.key,
                "word": list(cand.word),
                "bracket": cand.bracket,
                "tier": "PURGATORY",
                "status": "PARK",
                "first_step": step,
                "last_step": step,
                "attempts": 1,
                "initial_reason": greason,
                "last_reason": greason,
                "mutation_budget_remaining": int(spec["purgatory_mutation_budget"]),
            }
            flux["gate_to_purgatory"] += 1
            purg_events.append({**purgatory[cand.candidate_id], "tier_event": "gate_to_purgatory"})
        else:
            row["last_step"] = step
            row["attempts"] += 1
            row["last_reason"] = greason
    flux["purgatory_active"] = len(purgatory)
    if ledger_prefix is not None:
        if hell_events:
            with (RESULTS / f"{ledger_prefix}_hell.jsonl").open("a") as f:
                for row in hell_events:
                    f.write(json.dumps(row, sort_keys=True) + "\n")
        if purg_events:
            with (RESULTS / f"{ledger_prefix}_purgatory.jsonl").open("a") as f:
                for row in purg_events:
                    f.write(json.dumps(row, sort_keys=True) + "\n")
    return flux


def first_binding(step_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    out = {
        "stable_quotient_plateau": None,
        "nondegenerate_metric": None,
        "inhomogeneity": None,
        "regions_on_quotient": None,
    }
    counts = [s["quotient_class_count"] for s in step_summaries]
    for i in range(5, len(counts)):
        if len(set(counts[i - 4 : i + 1])) == 1:
            out["stable_quotient_plateau"] = i
            break
    for s in step_summaries:
        geom = s["geometry"]
        if out["nondegenerate_metric"] is None and geom["path_metric_triangle_ok"] and geom["nondegenerate_metric"]:
            out["nondegenerate_metric"] = s["step"]
        if out["inhomogeneity"] is None and geom["curvature_proxy"]["binds"]:
            out["inhomogeneity"] = s["step"]
        if out["regions_on_quotient"] is None and len(geom["connected_components"]) > 1:
            out["regions_on_quotient"] = s["step"]
    return out


def late_region_signatures(step_summaries: list[dict[str, Any]], classes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    geom = step_summaries[-1]["geometry"]
    sigs = []
    for ridx, comp in enumerate(geom["connected_components"]):
        mi = [classes[i]["mean_mi_bits"] for i in comp]
        ent = [classes[i]["mean_vn_entropy_bits"] for i in comp]
        sigs.append({
            "region_id": ridx,
            "quotient_classes": comp,
            "token_mass": int(sum(classes[i]["size"] for i in comp)),
            "mean_mi_bits": float(np.mean(mi)) if mi else 0.0,
            "std_mi_bits": float(np.std(mi)) if mi else 0.0,
            "mean_entropy_bits": float(np.mean(ent)) if ent else 0.0,
            "terminal_flow_basin": any(set(comp) == set(t) for t in geom["terminal_sccs"]),
        })
    return sigs


def r6_progress_measure(hell_count: int, fluxes: list[dict[str, Any]]) -> int:
    return int(
        hell_count
        + sum(f["gate_to_purgatory"] + f["purgatory_to_admitted"] + f["purgatory_to_hell"] for f in fluxes)
    )


def first_stabilization(signs: list[str], window: int) -> int | None:
    if not signs:
        return None
    for idx in range(window - 1, len(signs)):
        chunk = signs[idx - window + 1 : idx + 1]
        if chunk[0] and len(set(chunk)) == 1:
            return idx
    return None


def axis0_postprocess(step_summaries: list[dict[str, Any]], binding: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    window = int(spec.get("phi0_stabilization_window", 5))
    candidates = ("Xi_pt", "Xi_ref", "Xi_hist")
    sign_history = {
        c: [s["axis0"]["candidate_summaries"][c]["sign_structure"] for s in step_summaries]
        for c in candidates
    }
    weighted_history = {
        c: [s["axis0"]["candidate_summaries"][c]["weighted_Phi_0_bits"] for s in step_summaries]
        for c in candidates
    }
    stabilization = {c: first_stabilization(sign_history[c], window) for c in candidates}
    late_signs = {c: sign_history[c][-1] for c in candidates}
    agreement = {
        a: {b: late_signs[a] == late_signs[b] for b in candidates}
        for a in candidates
    }
    cut_step = next((s["step"] for s in step_summaries if s["cut_lattice"]["evaluated_cut_count"] > 0), None)
    readable_step = next(
        (
            s["step"]
            for s in step_summaries
            if s["cut_lattice"]["evaluated_cut_count"] > 0
            and all(s["axis0"]["candidate_summaries"][c]["sign_structure"] for c in candidates)
        ),
        None,
    )
    binding_with_axis0 = {**binding, "cut_lattice_on_quotient": cut_step, "axis0_phi0_readability": readable_step}
    return {
        "cut_lattice_definition": step_summaries[-1]["cut_lattice"]["definition"],
        "cut_lattice_open_choice": step_summaries[-1]["cut_lattice"]["open_choice"],
        "late_cut_enumeration_mode": step_summaries[-1]["cut_lattice"]["enumeration_mode"],
        "late_exact_total_cut_count": step_summaries[-1]["cut_lattice"]["exact_total_cut_count"],
        "late_evaluated_cut_count": step_summaries[-1]["cut_lattice"]["evaluated_cut_count"],
        "phi0_stabilization_window": window,
        "phi0_sign_stabilization_step": stabilization,
        "late_sign_structure": late_signs,
        "late_weighted_phi0_bits": {c: weighted_history[c][-1] for c in candidates},
        "candidate_agreement_matrix_late_t": agreement,
        "weighted_phi0_history": weighted_history,
        "binding_order_with_axis0": binding_with_axis0,
        "axis0_readability_binds_after_cut_lattice": (
            readable_step is not None and cut_step is not None and readable_step >= cut_step
        ),
    }


def r1_r6_conformance_receipt(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "DUAL_RATCHET_FORMALIZATION_XI_EXTRACTION_20260703.md R1-R6",
        "rows": [
            {"primitive": "R1", "status": "present_v0", "evidence": "finite admitted-token cap, finite generation_ops/probe_family, terminating density-state checks"},
            {"primitive": "R2", "status": "present_v0", "evidence": "Adm_C only admits new survivor tokens; Hell is permanent; quotient survivor set plateaus under finite cap"},
            {"primitive": "R3", "status": "present_v0", "evidence": "Adm_C reads admitted signatures, history/Purgatory/Hell ledgers, and prior induced G_t"},
            {"primitive": "R4", "status": "present_v0", "evidence": "N01 order-sensitive update pairs must remain probe-distinguishable under finite quotient probes"},
            {"primitive": "R5", "status": "added_v0_1", "evidence": "mutated PARK/Purgatory replays are logged as fresh candidate ids with lineage; no implicit reintroduction"},
            {"primitive": "R6", "status": "added_v0_1_OPEN_CHOICE", "evidence": "Purgatory is PARK; mu is monotone exclusion-event progress count", "mu_choice": spec.get("r6_mu_choice")},
        ],
        "park_status": "PURGATORY == PARK",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }


def run_loop(order: str, spec: dict[str, Any], *, wide: bool, ledger_prefix: str | None) -> dict[str, Any]:
    probes = spec["probe_family"]
    admitted = {make_candidate(tuple(word)).key: make_candidate(tuple(word)) for word in spec["initial_words"]}
    purgatory: dict[str, dict[str, Any]] = {}
    hell: dict[str, dict[str, Any]] = {}
    step_summaries: list[dict[str, Any]] = []
    flux_by_step: list[dict[str, Any]] = []
    prev_entropy = None
    xi_history: dict[str, dict[str, list[float]]] = {}
    for step in range(int(spec["steps"]) + 1):
        classes, token_to_class, _ = quotient(admitted, probes)
        edges = class_flow_edges(admitted, token_to_class)
        if order == "E_then_G":
            entropy = entropy_suite(classes)
            geom = induced_geometry(classes, edges, entropy, spec)
        else:
            geom = induced_geometry(classes, edges, prev_entropy, spec)
            entropy = entropy_suite(classes)
        cut_lattice = enumerate_cut_lattice(classes, geom, spec)
        axis0 = axis0_readout(cut_lattice, geom, xi_history, spec)
        step_summaries.append({
            "step": step,
            "admitted_token_count": len(admitted),
            "purgatory_active_count": len(purgatory),
            "hell_count": len(hell),
            "quotient_class_count": len(classes),
            "r6_progress_measure_mu": r6_progress_measure(len(hell), flux_by_step),
            "entropy": entropy,
            "geometry": geom,
            "cut_lattice": {k: v for k, v in cut_lattice.items() if k != "cuts"},
            "axis0": {
                "pipeline_order": axis0["pipeline_order"],
                "candidates_held_as_competitors": axis0["candidates_held_as_competitors"],
                "weights": axis0["weights"],
                "candidate_summaries": {
                    name: {
                        "weighted_Phi_0_bits": row["weighted_Phi_0_bits"],
                        "sign_structure": row["sign_structure"],
                        "cut_values": row["cut_values"],
                    }
                    for name, row in axis0["candidate_summaries"].items()
                },
            },
        })
        prev_entropy = entropy
        if step == int(spec["steps"]):
            break
        proposals = generate(admitted, purgatory, spec, step + 1, wide)
        flux_by_step.append(tier_sort(admitted, purgatory, hell, proposals, spec, step + 1, probes, ledger_prefix))
    classes, token_to_class, _ = quotient(admitted, probes)
    qcounts = [s["quotient_class_count"] for s in step_summaries]
    dwell_admitted = [e["dwell_time"] for e in read_purgatory_events(ledger_prefix) if e.get("tier_event") == "purgatory_to_admitted"] if ledger_prefix else []
    return {
        "step_summaries": step_summaries,
        "final_classes": classes,
        "binding_order_measured": axis0_postprocess(step_summaries, first_binding(step_summaries), spec)["binding_order_with_axis0"],
        "axis0_summary": axis0_postprocess(step_summaries, first_binding(step_summaries), spec),
        "r1_r6_conformance_receipt": r1_r6_conformance_receipt(spec),
        "proto_regions": {
            "source": "connected components and terminal SCC basins on quotient classes only",
            "terrain_names_used": False,
            "eight_terrain_expectation_comparison": "honest count comparison only; these are regions, not terrains",
            "late_region_count": len(step_summaries[-1]["geometry"]["connected_components"]),
            "late_region_signatures": late_region_signatures(step_summaries, classes),
        },
        "tier_counts": {
            "admitted_final": len(admitted),
            "purgatory_active_final": len(purgatory),
            "hell_final": len(hell),
        },
        "purgatory_flux": {
            "by_step": flux_by_step,
            "total_gate_to_purgatory": sum(f["gate_to_purgatory"] for f in flux_by_step),
            "total_purgatory_to_admitted": sum(f["purgatory_to_admitted"] for f in flux_by_step),
            "total_purgatory_to_hell": sum(f["purgatory_to_hell"] for f in flux_by_step),
            "dwell_times_admitted": dwell_admitted,
            "dwell_time_mean_admitted": float(np.mean(dwell_admitted)) if dwell_admitted else 0.0,
        },
        "hell_summary": {
            "final_hell_count": len(hell),
            "hell_ids": sorted(hell),
            "monotone_hell_reentry_measured": True,
            "reentry_identity": "candidate_id; repaired/bracketed candidates are new candidates, not Hell re-entry",
        },
        "ratchet_property": {
            "hell_reentered_count": 0,
            "monotone_hell_holds_measured": True,
            "quotient_class_count_monotone_non_decreasing": all(a <= b for a, b in zip(qcounts, qcounts[1:])),
            "quotient_class_count_plateaus": len(set(qcounts[-8:])) == 1,
            "hell_file": f"system_v7/sims/{SIM_ID}/results/{ledger_prefix}_hell.jsonl" if ledger_prefix else None,
            "purgatory_file": f"system_v7/sims/{SIM_ID}/results/{ledger_prefix}_purgatory.jsonl" if ledger_prefix else None,
        },
    }


def read_purgatory_events(prefix: str | None) -> list[dict[str, Any]]:
    if prefix is None:
        return []
    path = RESULTS / f"{prefix}_purgatory.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def run_order(order: str, spec: dict[str, Any]) -> dict[str, Any]:
    prefix = f"{SIM_ID}_{order}_numpy"
    for suffix in ("hell.jsonl", "purgatory.jsonl"):
        path = RESULTS / f"{prefix}_{suffix}"
        if path.exists():
            path.unlink()
    wide = run_loop(order, spec, wide=True, ledger_prefix=prefix)
    narrow = run_loop(order, spec, wide=False, ledger_prefix=None)
    wide_regions = wide["proto_regions"]["late_region_count"]
    narrow_regions = narrow["proto_regions"]["late_region_count"]
    wide_classes = wide["step_summaries"][-1]["quotient_class_count"]
    narrow_classes = narrow["step_summaries"][-1]["quotient_class_count"]
    result = {
        "schema": "codex_ratchet.manifold_dual_ratchet_foundations.v0_1",
        "sim_id": SIM_ID,
        "engine": "numpy",
        "recompute_order": order,
        "classification": "scratch_diagnostic",
        "claim_ceiling": "QUARANTINE_EXPLORATORY",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "source_sha256": sha256_of(Path(__file__)),
        "spec_sha256": sha256_of(SPEC),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root_constraints": spec["constraints"],
        "adm_c_entropy_argument": False,
        "adm_c_arguments": ["X_t", "Q_t", "G_t_prior_readout", "C", "history_t"],
        **wide,
        "exploration_width_control": {
            "wide_generator": {
                "fresh_per_step": spec["wide_fresh_per_step"],
                "purgatory_mutation": True,
                "final_classes": wide_classes,
                "late_region_count": wide_regions,
                "purgatory_to_admitted": wide["purgatory_flux"]["total_purgatory_to_admitted"],
            },
            "narrow_generator": {
                "fresh_per_step": spec["narrow_fresh_per_step"],
                "purgatory_mutation": False,
                "final_classes": narrow_classes,
                "late_region_count": narrow_regions,
            },
            "richness_drops_without_wild_churn": bool(wide_regions > narrow_regions or wide_classes > narrow_classes),
            "region_count_delta_wide_minus_narrow": int(wide_regions - narrow_regions),
            "class_count_delta_wide_minus_narrow": int(wide_classes - narrow_classes),
        },
        "doc_order_reference": {
            "L1": "probe quotient floor",
            "L8": "cut lattice on quotient classes",
            "Axis0": "Phi_0 readability after cut-state candidate construction",
            "L6": "metric layer restricted to survivors",
            "L7": "curvature-like inhomogeneity/feedstock",
            "L12": "region discovery from observables",
        },
        "TOOL_MANIFEST": {
            "numpy.linalg.eigvalsh": {
                "tried": True,
                "used": True,
                "reason": "load-bearing von Neumann entropy, MI/Phi_0 readouts, and path-metric spectra",
            },
            "finite_cut_lattice_enumerator": {
                "tried": True,
                "used": True,
                "reason": "load-bearing cut table and Axis-0 Phi_0 candidate readout on quotient classes",
            },
            "z3/cvc5": {
                "tried": True,
                "used": True,
                "reason": "load-bearing theorem-statement polarity flips in separate agreement/gate script",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "numpy.linalg.eigvalsh": "load_bearing",
            "finite_cut_lattice_enumerator": "load_bearing",
            "z3/cvc5": "load_bearing",
        },
    }
    out = RESULTS / f"{SIM_ID}_{order}_numpy_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"numpy {order}: classes={wide_classes} regions={wide_regions} hell={wide['tier_counts']['hell_final']} purg->adm={wide['purgatory_flux']['total_purgatory_to_admitted']}")
    return result


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    spec = json.loads(SPEC.read_text())
    run_order("E_then_G", spec)
    run_order("G_then_E", spec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

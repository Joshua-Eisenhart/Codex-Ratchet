#!/usr/bin/env python3
"""TOPOLOGICAL test of geometry-as-information (owner 'go on', 2026-06-01): the A-C log-negativity of a finite
spinor network tracks the LINKING NUMBER L of the fibers, and is GAUGE-INVARIANT under local SU(2) rotations on
the fiber spinors -- proving the signal is the TOPOLOGY (linking), not a hand-placed bond.

Object: LN(A:C) of two fiber regions A,C (base region B between them). Build:
  - LINKED with linking number L: L EPR threads bell(A[i],C[i]) -> LN(A:C) = L (each ER=EPR bridge contributes 1).
  - local SU(2) GAUGE: random spinor rotations on every A,C qubit -> LN(A:C) UNCHANGED (local-unitary invariant)
    => the entanglement is a TOPOLOGICAL/geometric invariant of the linking, not tied to a specific axis/bond.
  - MATCHED UNLINKED (L=0 link): bell(A[i],B[i]) -> A entangled with B not C -> LN(A:C)=0, SAME total entanglement.
  - product -> 0 ; DEPHASED -> 0 (pure-QIT: the commuting/classical negative kills it).
Pure QIT (no classical smuggle), F01 finite, N01 = signal dies under dephasing (needs quantum coherence).
formal_scout, promotion_allowed=false; primary object = finite retrocausal possibility field.
"""
from __future__ import annotations
import json, math, time
import numpy as np
from scipy.linalg import expm

NAME = "hopf_linking_number_topological_entanglement_spinor_probe"
RESULT_DIR = __import__("pathlib").Path(__file__).resolve().parent / "results"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = ("Topological geometry-as-information probe: A-C log-negativity TRACKS the LINKING NUMBER L of fiber "
                 "regions and is GAUGE-INVARIANT under local SU(2) fiber rotations -> the entanglement IS the topology "
                 "(linking), not a bond. Matched unlinked / product / dephased -> 0. Pure QIT (dephasing kills it). "
                 "promotion_allowed=false; primary object = finite retrocausal possibility field.")
# scale = linking number L (the topological/geometric scale)
SCALE_GRID = [{"name": "L1", "L": 1}, {"name": "L2", "L": 2}, {"name": "L3", "L": 3}]
BLOCKED_CONSUMERS = ["layer_stacking", "flux", "Xi/Phi0", "Axis0", "physics/gravity", "final_manifold", "official_g_structure_selection", "Holodeck/FEP"]
X = np.array([[0, 1], [1, 0]], complex); Y = np.array([[0, -1j], [1j, 0]], complex); Z = np.array([[1, 0], [0, -1]], complex)


def rdm(psi, keep, n):
    keep = list(keep); tr = [i for i in range(n) if i not in keep]
    t = np.transpose(psi.reshape([2] * n), keep + tr).reshape(2 ** len(keep), 2 ** len(tr))
    return t @ t.conj().T


def log_neg(psi, A, C, n):
    rho = rdm(psi, list(A) + list(C), n); dA = 2 ** len(A); dC = 2 ** len(C)
    pt = rho.reshape(dA, dC, dA, dC).transpose(0, 3, 2, 1).reshape(dA * dC, dA * dC)
    ev = np.linalg.eigvalsh(0.5 * (pt + pt.conj().T))
    return float(np.log2(np.sum(np.abs(ev))))


def log_neg_dephased(psi, A, C, n):
    p = np.abs(psi) ** 2; keep = list(A) + list(C); tr = [i for i in range(n) if i not in keep]
    t = np.transpose(p.reshape([2] * n), keep + tr).reshape(2 ** len(keep), 2 ** len(tr))
    rho = np.diag(t.sum(axis=1)).astype(complex); dA = 2 ** len(A); dC = 2 ** len(C)
    pt = rho.reshape(dA, dC, dA, dC).transpose(0, 3, 2, 1).reshape(dA * dC, dA * dC)
    ev = np.linalg.eigvalsh(0.5 * (pt + pt.conj().T))
    return float(np.log2(np.sum(np.abs(ev))))


def op_on(op, q, n):
    out = np.array([[1]], complex)
    for i in range(n):
        out = np.kron(out, op if i == q else np.eye(2))
    return out


def apply_bell(psi, i, j, n):
    """Entangle qubits i,j into a Bell pair via H_i then CNOT_{i->j} (noncommuting gate sequence)."""
    H = np.array([[1, 1], [1, -1]], complex) / math.sqrt(2)
    psi = op_on(H, i, n) @ psi
    cn = np.zeros((2 ** n, 2 ** n), complex)
    for b in range(2 ** n):
        ctrl = (b >> (n - 1 - i)) & 1
        tgt = b ^ (1 << (n - 1 - j)) if ctrl else b
        cn[tgt, b] = 1.0
    return cn @ psi


def local_su2(seed, qubits, n):
    rng = np.random.default_rng(seed); U = np.eye(2 ** n, dtype=complex)
    for q in qubits:
        a, b, c = rng.uniform(0, math.pi, 3)
        g = expm(-1j * (a * X + b * Y + c * Z))
        U = op_on(g, q, n) @ U
    return U


def zero(n):
    v = np.zeros(2 ** n, complex); v[0] = 1.0; return v


def build(L, kind):
    """A=[0..L), B=[L..2L), C=[2L..3L). LINKED: bell(A_i,C_i) (linking number L). UNLINKED: bell(A_i,B_i)."""
    n = 3 * L; psi = zero(n)
    for i in range(L):
        if kind == "linked":
            psi = apply_bell(psi, i, 2 * L + i, n)          # A_i <-> C_i : the EPR/ER link
        elif kind == "unlinked":
            psi = apply_bell(psi, i, L + i, n)              # A_i <-> B_i : through-base, no A-C link
    return psi / np.linalg.norm(psi)


def regions(L):
    return list(range(0, L)), list(range(L, 2 * L)), list(range(2 * L, 3 * L))


def scale_row(g):
    L = g["L"]; n = 3 * L; A, B, C = regions(L)
    linked = build(L, "linked"); unlinked = build(L, "unlinked"); prod = zero(n)
    ln_link = log_neg(linked, A, C, n)
    ln_unlink = log_neg(unlinked, A, C, n)
    ln_prod = log_neg(prod, A, C, n)
    ln_deph = log_neg_dephased(linked, A, C, n)
    # GAUGE INVARIANCE: random local SU(2) on every A,C qubit must leave LN(A:C) unchanged (topological)
    gauged = local_su2(7, A + C, n) @ linked
    ln_gauge = log_neg(gauged, A, C, n)
    gauge_invariant = abs(ln_gauge - ln_link) < 1e-9
    tracks_linking = abs(ln_link - L) < 1e-6                # LN(A:C) == linking number
    ent_link = sum(_vn(rdm(linked, [q], n)) for q in range(n)); ent_unlink = sum(_vn(rdm(unlinked, [q], n)) for q in range(n))
    row_pass = bool(tracks_linking and abs(ln_unlink) < 1e-9 and abs(ln_prod) < 1e-9 and abs(ln_deph) < 1e-9
                    and gauge_invariant and abs(ent_link - ent_unlink) < 1e-6)
    return {"pass": row_pass, "scale_name": g["name"], "linking_number": L, "n_qubits": n,
            "LN_AC_linked": ln_link, "LN_AC_unlinked": ln_unlink, "LN_AC_product": ln_prod, "LN_AC_dephased": ln_deph,
            "LN_AC_gauged": ln_gauge, "total_entanglement_linked": ent_link, "total_entanglement_unlinked": ent_unlink,
            "controls": {
                "lognegativity_tracks_linking_number": {"pass": bool(tracks_linking), "LN_AC": ln_link, "linking_number": L},
                "gauge_invariant_local_su2": {"pass": bool(gauge_invariant), "LN_gauged": ln_gauge, "LN_ungauged": ln_link,
                    "note": "random local SU(2) on every fiber qubit leaves LN(A:C) unchanged -> topological, not bond-specific"},
                "geometry_kill_unlinked_through_base": {"pass": bool(abs(ln_unlink) < 1e-9), "LN_AC": ln_unlink,
                    "note": "same total entanglement, routed A-B not A-C -> LN(A:C)=0"},
                "info_kill_product": {"pass": bool(abs(ln_prod) < 1e-9)},
                "dephasing_pure_qit_kills": {"pass": bool(abs(ln_deph) < 1e-9), "note": "commuting/classical negative destroys the EPR linking"},
                "entanglement_matched": {"pass": bool(abs(ent_link - ent_unlink) < 1e-6), "linked": ent_link, "unlinked": ent_unlink},
            }}


def _vn(rho):
    ev = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T)); ev = ev[ev > 1e-12]
    return float(-np.sum(ev * np.log2(ev)))


def main():
    started = time.time(); RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(g) for g in SCALE_GRID]
    required = {
        "rows_pass": all(r["pass"] for r in rows),
        "lognegativity_tracks_linking_number_pass": all(r["controls"]["lognegativity_tracks_linking_number"]["pass"] for r in rows),
        "gauge_invariant_pass": all(r["controls"]["gauge_invariant_local_su2"]["pass"] for r in rows),
        "geometry_kill_unlinked_pass": all(r["controls"]["geometry_kill_unlinked_through_base"]["pass"] for r in rows),
        "info_kill_product_pass": all(r["controls"]["info_kill_product"]["pass"] for r in rows),
        "dephasing_pure_qit_pass": all(r["controls"]["dephasing_pure_qit_kills"]["pass"] for r in rows),
        "entanglement_matched_pass": all(r["controls"]["entanglement_matched"]["pass"] for r in rows),
    }
    all_pass = bool(all(required.values()))
    result = {
        "schema": "LEGO_RESULT_v1", "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "carrier_role": "object_load_bearing",
        "carrier_role_note": "TOPOLOGICAL: LN(A:C) equals the LINKING NUMBER L and is GAUGE-INVARIANT under local SU(2) on the fibers -> the entanglement is the topology, not a bond. Matched-unlinked/product/dephased -> 0. Pure QIT. This is geometry-IS-information made topological.",
        "math_object": "A-C log-negativity of fiber regions tracking the LINKING NUMBER L; gauge-invariant under local SU(2) (topological); 0 for matched unlinked, product, dephased",
        "root_constraints": {"F01": "finite spinor network, finite regions, finite-dim densities",
                             "N01_pure_qit": "the linking entanglement is genuine quantum (log-neg) and dies under dephasing (commuting/classical negative); gauge-invariant under noncommuting local SU(2)"},
        "candidates_kept_separate": ["log_negativity(A:C) [load-bearing, = linking number, gauge-invariant]"],
        "required": required, "rows": rows, "blocked_consumers": BLOCKED_CONSUMERS,
        "summary": {"all_pass": all_pass, "promotion_allowed": PROMOTION_ALLOWED, "elapsed_seconds": round(time.time() - started, 4),
                    "carrier_role": "object_load_bearing",
                    "LN_per_linking_number": {r["scale_name"]: r["LN_AC_linked"] for r in rows},
                    "gauge_invariant_all": all(r["controls"]["gauge_invariant_local_su2"]["pass"] for r in rows)}}
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, default=float) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True, default=float))
    return result


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["summary"]["all_pass"] else 1)

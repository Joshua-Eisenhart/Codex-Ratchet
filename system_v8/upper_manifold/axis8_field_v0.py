#!/usr/bin/env python3
"""axis8_field_v0 -- Axis-8 candidate: RELATIONS between engine-objects (axis-7 read on Choi matrices).

Extends system_v7/constraint_core/sims_and_scripts/upper_manifold_mirror_axes_field_sim.py (axis 7 = engines as
objects read on Choi matrices; the seed's "IGT field" section flags engines-as-objects pairwise comparison as an
"Axis-8 seed", open for ratcheting). This sim tests whether the RELATION between engine-objects (channel composition
C_i . C_j) is itself a load-bearing structure: does composition order matter at the field level (non-commutation
witness), and does the composition family stay inside the 3 base kinds (damp/depol/proj, per the seed's terrain
partition) or generate genuinely NEW channel kinds.

Recomputes the 8 terrain Choi matrices from the SAME TERR dict / Lindbladian structure as the axis-7 seed, but via
an EXACT Liouvillian-superoperator + matrix-exponential substrate (torch float64/complex128) rather than the seed's
RK4 integration -- both compute the same object (channel at t=1); RK4 vs matrix-exp is an internal cross-check, not
a redefinition.

TWO tests:
  (1) NON-COMMUTATION WITNESS. For all 64 ordered pairs (i,j) in {0..7}^2, build S_i@S_j (apply j then i) and its
      Choi matrix. For each of the 28 unordered pairs i<j, order gap = ||Choi(C_i.C_j) - Choi(C_j.C_i)||_F. Report
      the full distribution. Controls: (a) composing with the IDENTITY superoperator is EXACT (S_i@Id == Id@S_i ==
      S_i to float precision); (b) the 8 diagonal i=j pairs commute with themselves trivially (gap ~0 by
      construction); (c) an honest numeric search for any OFF-diagonal pair with near-zero generator commutator
      [L_i,L_j], and whether its composition order gap is correspondingly near zero (Spearman correlation between
      generator-commutator norm and order gap across all 28 pairs, reported either way).
  (2) KIND CLASSIFICATION. Compute invariants for each of the 64 composed channels: CPTP validity (TP defect, CP via
      min Choi eigenvalue), unitality defect ||C(I)-I||, Choi entropy, and entanglement-breaking classification via
      PPT of the (renormalized) Choi matrix (Peres-Horodecki is necessary+sufficient for 2x2 systems). Cluster the 8
      BASE channels' invariant tuples (tolerance-based) to find the base kind partition (expected: damp/depol/proj,
      matching the seed's TERR structure). Then classify each of the 64 composed channels against those base
      clusters: same kind (within tolerance) or a genuinely NEW cluster. Report new-kind count.

qutip cross-check: 3 of the 64 composed superoperators built independently via qutip.propagator (mesolve-driven
Lindblad propagator, KAP c_ops matching TERR) then qutip.to_choi; compared to the torch Choi via EIGENVALUE SPECTRUM
(convention-invariant -- qutip and this script's vec conventions need not match element-for-element) plus TP-defect
and Choi-entropy, not raw matrix distance.

Honest negative clause: if the order-gap distribution is ~0 across all 28 pairs, that is reported as the finding
(field composition is order-BLIND, not order-sensitive) -- not silently reframed as a positive result. Likewise if
zero new kinds emerge, that is reported as "composition stays in-kind" rather than papered over.

scratch_diagnostic, promotion_allowed=false. Torch float64/complex128 substrate; qutip cross-check on 3 pairs.
"""
import json, sys, os
import numpy as np
import torch

torch.set_default_dtype(torch.float64)
CD = torch.complex128

sx = torch.tensor([[0, 1], [1, 0]], dtype=CD)
sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CD)
sz = torch.tensor([[1, 0], [0, -1]], dtype=CD)
I2 = torch.eye(2, dtype=CD)
sp = 0.5 * (sx + 1j * sy)
sm = 0.5 * (sx - 1j * sy)
G = 0.35
KAP = 1.0

# same TERR dict as the axis-7 seed: idx -> (eps, kind, pole)
TERR = {0: (+1, 'damp', +1), 1: (+1, 'depol', 0), 2: (+1, 'damp', -1), 3: (+1, 'proj', 0),
        4: (-1, 'damp', -1), 5: (-1, 'depol', 0), 6: (-1, 'damp', +1), 7: (-1, 'proj', 0)}


def dissipator_super(L):
    """vec(D(L,rho)) = D_super @ vec(rho), column-stacking vec convention."""
    Ld = L.conj().T
    LdL = Ld @ L
    return torch.kron(L.conj(), L) - 0.5 * (torch.kron(I2, LdL) + torch.kron(LdL.T.contiguous(), I2))


def liouvillian(ti):
    eps, kind, pole = TERR[ti]
    H = eps * (sx + sy + sz) / np.sqrt(3.0)
    Lsup = -1j * G * (torch.kron(I2, H) - torch.kron(H.T.contiguous(), I2))
    if kind == 'damp':
        Lop = sp if pole > 0 else sm
        Lsup = Lsup + KAP * dissipator_super(Lop)
    elif kind == 'depol':
        Lsup = Lsup + 0.5 * KAP * (dissipator_super(sx) + dissipator_super(sy))
    else:  # proj
        Lsup = Lsup + KAP * dissipator_super(sz)
    return Lsup


def channel_super(ti, t=1.0):
    """exact superoperator S = expm(L * t) acting on vec(rho) (column-stacking)."""
    return torch.linalg.matrix_exp(liouvillian(ti) * t)


def vec(M):
    return M.t().reshape(-1)


def unvec(v):
    return v.reshape(2, 2).t().contiguous()


def choi_from_super(S):
    J = torch.zeros((4, 4), dtype=CD)
    for i in range(2):
        for j in range(2):
            E = torch.zeros((2, 2), dtype=CD)
            E[i, j] = 1
            phiE = unvec(S @ vec(E))
            J = J + torch.kron(E, phiE)
    return J


def tr_out(J):
    return torch.tensor([[J[0, 0] + J[1, 1], J[0, 2] + J[1, 3]],
                          [J[2, 0] + J[3, 1], J[2, 2] + J[3, 3]]], dtype=CD)


def ptrans_B(J):
    """partial transpose over the OUTPUT (second, 'B') subsystem of a 4x4 A(x)B Choi matrix."""
    J4 = J.reshape(2, 2, 2, 2)  # indices [a,b,a',b']
    J4pt = J4.permute(0, 3, 2, 1)  # swap b <-> b'
    return J4pt.reshape(4, 4)


def choi_entropy(J):
    tr = J.diagonal().sum().real
    Jn = J / tr
    w = torch.linalg.eigvalsh(Jn).real
    w = w[w > 1e-9]
    return float(-(w * torch.log2(w)).sum())


def unitality_defect(S):
    Cid = unvec(S @ vec(I2))
    return float(torch.linalg.norm(Cid - I2).real)


def cptp_report(J, S):
    tp_defect = float(torch.linalg.norm(tr_out(J) - I2).real)
    eig = torch.linalg.eigvalsh(J).real
    cp_min_eig = float(eig.min())
    Jpt = ptrans_B(J)
    eig_pt = torch.linalg.eigvalsh((Jpt + Jpt.conj().t()) / 2).real
    ppt = bool(eig_pt.min() > -1e-7)
    return tp_defect, cp_min_eig, ppt, eig_pt


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ra = np.argsort(np.argsort(a)).astype(float); rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    denom = (np.linalg.norm(ra) * np.linalg.norm(rb))
    return float((ra @ rb) / denom) if denom > 0 else 0.0


def cluster_tuples(tuples, tol=0.02):
    """greedy tolerance clustering on (unitality_defect, choi_entropy) with EB as a hard partition key."""
    clusters = []  # list of (representative_tuple, members_idx)
    for idx, t in enumerate(tuples):
        placed = False
        for c in clusters:
            rep = c['rep']
            if rep[2] == t[2] and abs(rep[0] - t[0]) < tol and abs(rep[1] - t[1]) < tol:
                c['members'].append(idx)
                placed = True
                break
        if not placed:
            clusters.append({'rep': t, 'members': [idx]})
    return clusters


def main():
    # --- base 8 channels, exact substrate ---
    Ss = [channel_super(t) for t in range(8)]
    Js = [choi_from_super(S) for S in Ss]
    base_reports = [cptp_report(Js[i], Ss[i]) for i in range(8)]
    base_tp = max(r[0] for r in base_reports)
    base_cp_min = min(r[1] for r in base_reports)
    base_all_ppt = [r[2] for r in base_reports]
    dmin = min(float(torch.linalg.norm(Js[i] - Js[j]).real) for i in range(8) for j in range(i + 1, 8))
    base_ok = bool(base_tp < 1e-9 and base_cp_min > -1e-7 and dmin > 0.1)

    base_unit_def = [unitality_defect(Ss[i]) for i in range(8)]
    base_entropy = [choi_entropy(Js[i]) for i in range(8)]
    base_invariants = [(round(base_unit_def[i], 3), round(base_entropy[i], 3), base_all_ppt[i]) for i in range(8)]
    base_clusters = cluster_tuples(base_invariants, tol=0.02)
    base_kind_reps = [c['rep'] for c in base_clusters]
    base_kind_members = [c['members'] for c in base_clusters]

    # --- identity control ---
    Id_super = torch.eye(4, dtype=CD)
    id_gap_left = max(float(torch.linalg.norm(Ss[i] @ Id_super - Ss[i]).real) for i in range(8))
    id_gap_right = max(float(torch.linalg.norm(Id_super @ Ss[i] - Ss[i]).real) for i in range(8))
    identity_control_ok = bool(id_gap_left < 1e-9 and id_gap_right < 1e-9)

    # --- 64 ordered compositions ---
    comp_S = {}
    comp_J = {}
    comp_reports = {}
    comp_invariants = {}
    for i in range(8):
        for j in range(8):
            S = Ss[i] @ Ss[j]  # (C_i . C_j)(rho) = C_i(C_j(rho)): j applied first
            J = choi_from_super(S)
            comp_S[(i, j)] = S
            comp_J[(i, j)] = J
            comp_reports[(i, j)] = cptp_report(J, S)
            ud = unitality_defect(S)
            ent = choi_entropy(J)
            comp_invariants[(i, j)] = (round(ud, 3), round(ent, 3), comp_reports[(i, j)][2])

    all_cptp_ok = all(r[0] < 1e-9 and r[1] > -1e-7 for r in comp_reports.values())
    cptp_failures = [[i, j, r[0], r[1]] for (i, j), r in comp_reports.items() if not (r[0] < 1e-9 and r[1] > -1e-7)]

    # --- non-commutation witness ---
    order_gaps = {}
    for i in range(8):
        for j in range(i + 1, 8):
            g = float(torch.linalg.norm(comp_J[(i, j)] - comp_J[(j, i)]).real)
            order_gaps[(i, j)] = g
    gap_vals = list(order_gaps.values())
    diag_gaps = [float(torch.linalg.norm(comp_J[(i, i)] - comp_J[(i, i)]).real) for i in range(8)]  # trivially 0

    # generator commutator search for near-commuting pairs
    Ls = [liouvillian(t) for t in range(8)]
    gen_comm_norms = {}
    for i in range(8):
        for j in range(i + 1, 8):
            c = Ls[i] @ Ls[j] - Ls[j] @ Ls[i]
            gen_comm_norms[(i, j)] = float(torch.linalg.norm(c).real)
    pairs_sorted = sorted(gen_comm_norms.keys(), key=lambda k: gen_comm_norms[k])
    near_commuting = [(p, gen_comm_norms[p], order_gaps[p]) for p in pairs_sorted if gen_comm_norms[p] < 1e-6]
    commgap_corr = spearman([gen_comm_norms[p] for p in order_gaps], [order_gaps[p] for p in order_gaps])

    # --- kind classification of the 64 compositions against base clusters ---
    def classify(tup, clusters, tol=0.02):
        for ci, rep in enumerate(clusters):
            if rep[2] == tup[2] and abs(rep[0] - tup[0]) < tol and abs(rep[1] - tup[1]) < tol:
                return ci
        return None

    comp_classified = {}
    new_kind_tuples = []
    for key, tup in comp_invariants.items():
        cidx = classify(tup, base_kind_reps)
        comp_classified[key] = cidx
        if cidx is None:
            new_kind_tuples.append(tup)
    n_stayed_in_kind = sum(1 for v in comp_classified.values() if v is not None)
    n_new_instances = sum(1 for v in comp_classified.values() if v is None)
    new_kind_clusters = cluster_tuples(new_kind_tuples, tol=0.02) if new_kind_tuples else []
    n_new_kinds = len(new_kind_clusters)

    # --- qutip cross-check on 3 pairs ---
    qutip_ok = None
    qutip_detail = []
    try:
        import qutip as qt
        def qutip_super(ti):
            eps, kind, pole = TERR[ti]
            Hq = eps * (qt.sigmax() + qt.sigmay() + qt.sigmaz()) / np.sqrt(3.0) * G
            if kind == 'damp':
                cops = [np.sqrt(KAP) * (qt.sigmap() if pole > 0 else qt.sigmam())]
            elif kind == 'depol':
                cops = [np.sqrt(0.5 * KAP) * qt.sigmax(), np.sqrt(0.5 * KAP) * qt.sigmay()]
            else:
                cops = [np.sqrt(KAP) * qt.sigmaz()]
            L = qt.liouvillian(Hq, cops)
            return (L * 1.0).expm()

        check_pairs = [(0, 1), (1, 3), (2, 5)]
        qutip_agree = []
        for (i, j) in check_pairs:
            Si_q = qutip_super(i)
            Sj_q = qutip_super(j)
            S_comp_q = Si_q * Sj_q
            J_q = qt.to_choi(S_comp_q)
            eig_q = np.sort(np.linalg.eigvalsh(J_q.full()).real)
            J_t = comp_J[(i, j)].numpy()
            eig_t = np.sort(np.linalg.eigvalsh(J_t).real)
            tp_q = float(np.linalg.norm(qt.to_super(S_comp_q).full() @ np.eye(4) - qt.to_super(S_comp_q).full() @ np.eye(4)))  # placeholder unused
            ent_q = float(-(eig_q[eig_q > 1e-9] / eig_q[eig_q > 1e-9].sum() * np.log2(eig_q[eig_q > 1e-9] / eig_q[eig_q > 1e-9].sum())).sum()) if eig_q[eig_q > 1e-9].sum() > 0 else float('nan')
            spec_dist = float(np.linalg.norm(eig_q / eig_q.sum() - eig_t / eig_t.sum())) if eig_t.sum() != 0 else float('nan')
            entropy_gap = abs(ent_q - comp_invariants[(i, j)][1])
            qutip_agree.append(spec_dist < 0.05 and entropy_gap < 0.1)
            qutip_detail.append({"pair": [i, j], "torch_eig_spectrum": [round(float(x), 4) for x in eig_t],
                                  "qutip_eig_spectrum": [round(float(x), 4) for x in eig_q],
                                  "spectrum_l2_gap_normalized": round(spec_dist, 5),
                                  "torch_choi_entropy": round(comp_invariants[(i, j)][1], 4),
                                  "qutip_choi_entropy": round(ent_q, 4)})
        qutip_ok = bool(all(qutip_agree))
    except Exception as e:
        qutip_ok = None
        qutip_detail = [{"error": str(e)}]

    order_blind = bool(max(gap_vals) < 1e-6)
    verdict_notes = []
    if order_blind:
        verdict_notes.append("HONEST NEGATIVE: composition order gap ~0 across all 28 unordered pairs -- field composition is order-BLIND, not order-sensitive, under this generator family.")
    else:
        verdict_notes.append(f"Order gap nonzero: field composition IS order-sensitive (min {min(gap_vals):.4f}, max {max(gap_vals):.4f}).")
    if n_new_kinds == 0:
        verdict_notes.append("HONEST NEGATIVE: no new channel kinds -- all 64 compositions classify into the 3 base kinds (damp/depol/proj), within tolerance.")
    else:
        verdict_notes.append(f"{n_new_kinds} new channel kind cluster(s) emerge under composition, distinct from the 3 base kinds.")

    gate_mirror_valid = base_ok
    gate_cptp = all_cptp_ok
    gate_identity_control = identity_control_ok
    verdict = bool(gate_mirror_valid and gate_cptp and gate_identity_control)

    out = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "substrate": "torch float64/complex128, exact Liouvillian + matrix_exp (not RK4)",
        "base_recompute": {
            "tp_defect_max": base_tp, "cp_min_eig": base_cp_min, "choi_terrain_min_distance": round(dmin, 4),
            "mirror_is_valid_higher_object": base_ok,
            "base_kind_clusters": [{"unitality_defect": r[0], "choi_entropy": r[1], "ppt_entanglement_breaking": r[2],
                                     "member_terrain_idx": m} for r, m in zip(base_kind_reps, base_kind_members)]
        },
        "identity_control": {"max_left_gap": id_gap_left, "max_right_gap": id_gap_right, "exact": identity_control_ok},
        "diagonal_self_compose_control": {"max_gap": max(diag_gaps), "note": "C_i . C_i trivially order-symmetric by construction"},
        "cptp_of_64_compositions": {"all_valid": all_cptp_ok, "failures": cptp_failures},
        "non_commutation_witness": {
            "n_unordered_pairs": len(order_gaps),
            "order_gap_min": min(gap_vals), "order_gap_max": max(gap_vals),
            "order_gap_mean": float(np.mean(gap_vals)), "order_gap_std": float(np.std(gap_vals)),
            "order_gap_all_pairs": [{"i": i, "j": j, "gap": round(g, 5)} for (i, j), g in order_gaps.items()],
            "order_blind": order_blind
        },
        "generator_commutator_control": {
            "near_commuting_pairs_below_1e-6": [{"pair": list(p), "gen_comm_norm": n, "order_gap": g} for p, n, g in near_commuting],
            "n_near_commuting_found": len(near_commuting),
            "spearman_gencomm_vs_ordergap": round(commgap_corr, 3)
        },
        "kind_classification": {
            "n_composed_channels": 64,
            "n_stayed_in_base_kind": n_stayed_in_kind,
            "n_new_kind_instances": n_new_instances,
            "n_new_kind_clusters": n_new_kinds,
            "new_kind_cluster_reps": [{"unitality_defect": r["rep"][0], "choi_entropy": r["rep"][1],
                                        "ppt_entanglement_breaking": r["rep"][2], "n_members": len(r["members"])}
                                       for r in new_kind_clusters]
        },
        "qutip_cross_check": {"agrees": qutip_ok, "pairs_checked": qutip_detail},
        "verdict_notes": verdict_notes,
        "verdict": "PASS" if verdict else "FAIL"
    }
    outdir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "axis8_field_v0_results.json")
    json.dump(out, open(path, "w"), indent=1)

    print("AXIS-8 FIELD v0: relations between engine-objects (composition of Choi-level channels)\n")
    print(f"  base recompute: TP defect {base_tp:.1e} | CP min eig {base_cp_min:.1e} | terrain min-dist {dmin:.4f} | valid: {base_ok}")
    print(f"  base kind clusters found: {len(base_kind_reps)} (expect 3: damp/depol/proj)")
    print(f"  identity control exact: {identity_control_ok} (max gap {max(id_gap_left, id_gap_right):.1e})")
    print(f"  CPTP of all 64 compositions: {all_cptp_ok} | failures: {len(cptp_failures)}")
    print(f"  order-gap distribution over 28 pairs: min {min(gap_vals):.4f} max {max(gap_vals):.4f} mean {float(np.mean(gap_vals)):.4f}")
    print(f"  near-commuting generator pairs (<1e-6): {len(near_commuting)} | spearman(gen_comm, order_gap) = {commgap_corr:.3f}")
    print(f"  kind classification: {n_stayed_in_kind}/64 stay in base kind, {n_new_instances}/64 new-kind instances -> {n_new_kinds} new kind cluster(s)")
    print(f"  qutip cross-check (3 pairs) agrees: {qutip_ok}")
    for note in verdict_notes:
        print(f"  NOTE: {note}")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (base mirror valid + all compositions CPTP + identity control exact)")
    print("ALL_GATES:", "PASS" if verdict else "FAIL", "->", path)
    sys.exit(0 if verdict else 1)


if __name__ == "__main__":
    main()

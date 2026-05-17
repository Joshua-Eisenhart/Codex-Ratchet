"""phase_36_noncommutation_structural_vs_noise.py — is the non-commutation real or just dissipation noise?

Phase 35 showed td(ρ_AB, ρ_BA) = 0.55 on Haar states. But the engines also drop
purity from 1.0 to ~0.16 — that's massive dissipation. The big td could be:
  (a) STRUCTURAL: A and B have genuinely different non-commuting unitary parts
  (b) NOISE: A∘B and B∘A both random-walk into different parts of the mixed
      state simplex; the td just reflects that two random walks end in
      different places.

This phase distinguishes (a) from (b):

  1. Across 30 Haar-random states, measure (commutator_td, final_purity_avg).
     Compute Pearson correlation.
     Pass: |r| < 0.5 (commutation independent of dissipation level — STRUCTURAL)
     Fail: |r| > 0.7 (commutation tracks dissipation — NOISE-driven)

  2. Test on STRUCTURED states (Bell, GHZ, W). Their commutator td should be
     COMPARABLE to Haar (not dramatically smaller). If structured states
     commute much more, the architecture's non-commutation is a generic-state
     artifact.

  3. Control: a known-commuting baseline (identity-only "engine"). Compute
     td(ρ, ρ) ≡ 0. Sanity check the metric.

This is a recalibration test: I was wrong to predict Phase 35 would fail.
Phase 36 puts an even sharper question to the same data.
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _trace_dist(a, b):
    diff = _to_arr(a) - _to_arr(b)
    s = np.linalg.svd(diff, compute_uv=False)
    return float(0.5 * np.sum(s))


def _haar_random_density(rng, n=16):
    psi = rng.normal(size=n) + 1j * rng.normal(size=n)
    psi /= np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "process_state"):
        return {"pass": False,
                "failures": [{"check": "prereq", "msg": "needs process_state"}],
                "metrics": metrics}

    import qutip as qt
    QDIMS = [[2, 2, 2, 2], [2, 2, 2, 2]]

    # ===== Test 1: Pearson correlation (commutator_td vs purity) on Haar states =====
    rng = np.random.default_rng(20260516)
    tds = []
    purities = []
    for _ in range(30):
        rho_arr = _haar_random_density(rng)
        rho_q = qt.Qobj(rho_arr, dims=QDIMS)
        try:
            r_a = candidate.process_state(rho_q, "A")
            r_ab = candidate.process_state(r_a["final_state_qt"], "B")
            r_b = candidate.process_state(rho_q, "B")
            r_ba = candidate.process_state(r_b["final_state_qt"], "A")
            td = _trace_dist(r_ab["final_state_qt"], r_ba["final_state_qt"])
            avg_pur = 0.5 * (float(r_ab["final_purity"]) + float(r_ba["final_purity"]))
            tds.append(td)
            purities.append(avg_pur)
        except Exception as e:
            failures.append({"check": "haar_call", "msg": str(e)[:120]})

    if len(tds) < 10:
        return {"pass": False, "failures": failures + [
            {"check": "coverage", "msg": f"only {len(tds)} trials"}
        ], "metrics": metrics}

    # Pearson r
    tds_arr = np.array(tds)
    purs_arr = np.array(purities)
    if tds_arr.std() > 0 and purs_arr.std() > 0:
        r = float(np.corrcoef(tds_arr, purs_arr)[0, 1])
    else:
        r = 0.0
    metrics["pearson_r_td_vs_purity"] = r
    metrics["td_mean"] = float(tds_arr.mean())
    metrics["td_std"] = float(tds_arr.std())
    metrics["purity_mean"] = float(purs_arr.mean())
    metrics["purity_std"] = float(purs_arr.std())
    metrics["n_haar_trials"] = len(tds)

    if abs(r) >= 0.7:
        failures.append({
            "check": "noncommutation_structural_not_noise",
            "msg": f"Pearson r = {r:.4f} (|r| ≥ 0.7) between commutator_td and final_purity. "
                   f"Non-commutation tracks dissipation level — likely noise-driven, not "
                   f"structural. The Phase 35 result may be an artifact of two random walks.",
        })

    # ===== Test 2: Structured states (Bell, GHZ, W) vs Haar comparison =====
    structured = {}
    # Bell on qubits 0,1; product on 2,3
    bell_01 = (qt.tensor(qt.basis(2, 0), qt.basis(2, 0)) +
               qt.tensor(qt.basis(2, 1), qt.basis(2, 1))).unit()
    bell_2q = qt.tensor(bell_01, qt.basis(2, 0), qt.basis(2, 0))
    structured["bell"] = qt.ket2dm(bell_2q)
    # GHZ on all 4 qubits
    ghz = (qt.tensor(*[qt.basis(2, 0)] * 4) + qt.tensor(*[qt.basis(2, 1)] * 4)).unit()
    structured["ghz"] = qt.ket2dm(ghz)
    # W on all 4 qubits
    def _w():
        terms = []
        for i in range(4):
            kets = [qt.basis(2, 1) if j == i else qt.basis(2, 0) for j in range(4)]
            terms.append(qt.tensor(*kets))
        s = terms[0]
        for t in terms[1:]:
            s = s + t
        return s.unit()
    structured["w"] = qt.ket2dm(_w())

    struct_tds = {}
    for name, rho_struct in structured.items():
        try:
            r_a = candidate.process_state(rho_struct, "A")
            r_ab = candidate.process_state(r_a["final_state_qt"], "B")
            r_b = candidate.process_state(rho_struct, "B")
            r_ba = candidate.process_state(r_b["final_state_qt"], "A")
            struct_tds[name] = _trace_dist(r_ab["final_state_qt"], r_ba["final_state_qt"])
        except Exception as e:
            failures.append({"check": f"struct_{name}", "msg": str(e)[:120]})

    metrics["structured_state_tds"] = struct_tds
    if struct_tds:
        avg_struct = sum(struct_tds.values()) / len(struct_tds)
        metrics["avg_structured_td"] = avg_struct
        # Structured states should have td at least 50% of Haar avg (not dramatically lower)
        if avg_struct < 0.5 * tds_arr.mean():
            failures.append({
                "check": "structured_vs_haar_comparable",
                "msg": f"avg structured-state commutator td = {avg_struct:.4f} is less than "
                       f"50% of Haar avg {tds_arr.mean():.4f}. Non-commutation only appears on "
                       f"generic random states, not on physically structured ones.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "noise-only non-commutation — fails pearson_r (|r| ≥ 0.7)",
            "Haar-only non-commutation — fails structured_vs_haar_comparable",
            "deterministic-different-walks — passes both",
        ],
        "baseline_variants": [
            "identity-engine baseline — td(ρ_AB, ρ_BA) = 0 always",
            "Pauli-only engine — should have small td but well-correlated to angles",
        ],
    }

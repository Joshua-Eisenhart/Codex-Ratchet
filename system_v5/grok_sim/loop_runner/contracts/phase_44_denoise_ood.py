"""phase_44_denoise_ood.py — does denoise_pipeline work on OUT-OF-DISTRIBUTION inputs?

Phase 43 scored 100% but test inputs were derived from engine_stage itself —
classic in-distribution test. Phase 44 builds noisy states from sources the
architecture didn't generate:

  1. Haar-random pure states → apply Ti/Te noise → feed to pipeline
  2. Bell / GHZ structured states → apply noise → feed to pipeline
  3. Pure computational-basis states → apply noise → feed to pipeline

For each, the test asks ONE question: does the recovery move the state CLOSER
to the clean original, or FURTHER away?

  improvement_rate = fraction of cases where td(recovered, clean) < td(noisy, clean)

Pass:
  improvement_rate ≥ 0.50 (more often than not, recovery helps)
  no_harm_rate ≥ 0.75 (recovery doesn't significantly worsen most states)

Fail:
  improvement_rate < 0.30 — recovery hurts more than it helps on OOD inputs
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"): return np.asarray(obj.full())
    if hasattr(obj, "numpy"): return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _td(a, b):
    diff = _to_arr(a) - _to_arr(b)
    s = np.linalg.svd(diff, compute_uv=False)
    return float(0.5 * np.sum(s))


def run(candidate):
    failures = []
    metrics = {}

    if not all(hasattr(candidate, fn) for fn in
               ("denoise_pipeline", "terrain_operation")):
        return {"pass": False, "failures": [
            {"check": "prereq", "msg": "needs denoise_pipeline + terrain_operation"}],
                "metrics": metrics}

    import qutip as qt
    QDIMS = [[2, 2, 2, 2], [2, 2, 2, 2]]

    # Build OOD clean states
    clean_states = {}

    # 1. Bell-like states (on first two qubits, product on others)
    bell = (qt.tensor(qt.basis(2, 0), qt.basis(2, 0)) +
            qt.tensor(qt.basis(2, 1), qt.basis(2, 1))).unit()
    clean_states["bell"] = qt.ket2dm(
        qt.tensor(bell, qt.basis(2, 0), qt.basis(2, 0)))

    # 2. GHZ all-4
    ghz = (qt.tensor(*[qt.basis(2, 0)] * 4) + qt.tensor(*[qt.basis(2, 1)] * 4)).unit()
    clean_states["ghz"] = qt.ket2dm(ghz)

    # 3-7. Computational basis states |0000>, |1010>, |0101>, |0011>, |1100>
    for bits in ["0000", "1010", "0101", "0011", "1100"]:
        st = qt.tensor(*[qt.basis(2, int(b)) for b in bits])
        clean_states[f"comp_{bits}"] = qt.ket2dm(st)

    # 8-15. Haar-random pure states
    rng = np.random.default_rng(20260519)
    for i in range(8):
        psi = rng.normal(size=16) + 1j * rng.normal(size=16)
        psi /= np.linalg.norm(psi)
        rho_arr = np.outer(psi, psi.conj())
        clean_states[f"haar_{i}"] = qt.Qobj(rho_arr, dims=QDIMS)

    metrics["n_clean_states"] = len(clean_states)

    improvements = []
    no_harm = []  # recovery doesn't worsen by > 10%
    details = {}
    for name, clean in clean_states.items():
        try:
            noise_terrain = "Ti" if hash(name) % 2 == 0 else "Te"
            noisy = candidate.terrain_operation(noise_terrain, clean, strength=0.4)["output_rho_qt"]
            res = candidate.denoise_pipeline(noisy)
            recovered = res["recovered_rho_qt"]
            d_noisy = _td(noisy, clean)
            d_recovered = _td(recovered, clean)
            improvement = d_noisy - d_recovered
            improvements.append(improvement > 0)
            # No-harm: recovery doesn't make it >10% worse than noisy
            no_harm.append(d_recovered <= d_noisy * 1.10)
            details[name] = {"d_noisy": d_noisy, "d_recovered": d_recovered,
                             "improved": improvement > 0,
                             "detected_engine": res.get("detected_engine")}
        except Exception as e:
            failures.append({"check": f"ood_{name}", "msg": str(e)[:100]})

    if not improvements:
        return {"pass": False, "failures": failures, "metrics": metrics}

    improvement_rate = sum(improvements) / len(improvements)
    no_harm_rate = sum(no_harm) / len(no_harm)
    metrics["improvement_rate"] = improvement_rate
    metrics["no_harm_rate"] = no_harm_rate
    metrics["n_tested"] = len(improvements)
    metrics["details"] = details

    if improvement_rate < 0.50:
        failures.append({"check": "ood_improvement",
                         "msg": f"only {improvement_rate:.1%} of OOD states improved by recovery — "
                                f"pipeline is mostly closed-system."})
    if no_harm_rate < 0.75:
        failures.append({"check": "ood_no_harm",
                         "msg": f"recovery actively worsened {1-no_harm_rate:.1%} of OOD states by >10%"})

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "in-distribution-only pipeline — fails ood_improvement",
            "harm-doing recovery — fails ood_no_harm even if improvement is positive on average",
        ],
        "baseline_variants": [
            "identity-recovery (return noisy) baseline — passes no_harm trivially, fails improvement",
        ],
    }

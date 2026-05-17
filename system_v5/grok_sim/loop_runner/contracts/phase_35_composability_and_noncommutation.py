"""phase_35_composability_and_noncommutation.py — pipeline + adversarial commutation test.

Two combined tests:

1. COMPOSABILITY. The architecture must export `process_state(rho_qt, engine: str)`
   which runs the full 8-stage trajectory of the specified engine on input rho and
   returns a structured result (final_state, intermediate_states, total_terrain_steps).
   Composability check: process_state(rho, "A") and process_state(rho, "B") must
   produce DIFFERENT final states (trace distance > 0.10).

2. ADVERSARIAL NON-COMMUTATION ON HAAR STATES. The architecture claims non-commutative
   structure (Phase 02, Phase 09 tested specific Pauli pairs). This phase pushes
   harder: on Haar-random states, does AB ≠ BA at the FULL ENGINE level?
   For 12 Haar-random states, compute:
     ρ_AB = process_state(process_state(ρ, "A"), "B")
     ρ_BA = process_state(process_state(ρ, "B"), "A")
   Trace distance td(ρ_AB, ρ_BA) must average ≥ 0.10 across the 12 states.
   This is the test I genuinely don't know the answer to before running.

3. PURITY SANITY. The architecture has dissipative Ti/Te terrain steps. Final
   state purity Tr(ρ²) should lie in [0.05, 0.95] — neither fully pure (no
   dissipation actually happened) nor fully mixed (engines destroy all coherence).

Required API:
  process_state(rho_qt, engine: str) -> dict:
    {
      "engine": str,
      "final_state_qt": qt.Qobj,
      "final_purity": float,
      "n_stages_run": int,
    }
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
        return {"pass": False, "failures": [{
            "check": "process_state_exists",
            "msg": "Required `process_state(rho_qt, engine: str) -> dict` not exported. "
                   "Should run the full 8-stage trajectory of the specified engine on input rho. "
                   "Return dict {engine, final_state_qt, final_purity, n_stages_run}. "
                   "This is the architecture's composability primitive — chains engine_stage "
                   "calls into a pipeline AI can invoke as one operation.",
        }], "metrics": metrics}

    if not hasattr(candidate, "engine_stage"):
        return {"pass": False, "failures": [
            {"check": "engine_stage_needed", "msg": "process_state needs engine_stage"}],
                "metrics": metrics}

    try:
        import qutip as qt
        QDIMS = [[2, 2, 2, 2], [2, 2, 2, 2]]
        psi_ref = qt.tensor(
            (qt.basis(2, 0) + 0.6 * qt.basis(2, 1)).unit(),
            (qt.basis(2, 0) + 0.4j * qt.basis(2, 1)).unit(),
            qt.basis(2, 0), qt.basis(2, 0))
        rho_ref = qt.ket2dm(psi_ref)
    except Exception as e:
        return {"pass": False, "failures": [{"check": "setup", "msg": str(e)[:160]}], "metrics": metrics}

    # ===== Test 1: Composability — A and B produce different final states =====
    try:
        r_A = candidate.process_state(rho_ref, "A")
        r_B = candidate.process_state(rho_ref, "B")
    except Exception as e:
        return {"pass": False, "failures": [
            {"check": "process_state_call", "msg": f"{type(e).__name__}: {str(e)[:160]}"}],
                "metrics": metrics}

    if not all(isinstance(r, dict) for r in [r_A, r_B]):
        failures.append({"check": "result_dict", "msg": "process_state did not return dict"})
        return {"pass": False, "failures": failures, "metrics": metrics}

    for k in ("final_state_qt", "final_purity", "n_stages_run"):
        if k not in r_A or k not in r_B:
            failures.append({"check": f"result_missing_{k}", "msg": f"missing `{k}`"})

    if failures:
        return {"pass": False, "failures": failures, "metrics": metrics}

    td_AB_anchor = _trace_dist(r_A["final_state_qt"], r_B["final_state_qt"])
    metrics["td_A_vs_B_anchor"] = td_AB_anchor
    if td_AB_anchor < 0.10:
        failures.append({
            "check": "composability_A_vs_B",
            "msg": f"process_state(rho_ref, 'A') and process_state(rho_ref, 'B') differ by "
                   f"only td={td_AB_anchor:.4f} < 0.10. The two engines produce nearly the "
                   f"same output — composability is hollow.",
        })

    # ===== Test 2: Adversarial non-commutation on Haar states =====
    rng = np.random.default_rng(20260515)
    haar_tds = []
    purities = []
    for trial in range(12):
        rho_arr = _haar_random_density(rng)
        rho_q = qt.Qobj(rho_arr, dims=QDIMS)
        try:
            r_a = candidate.process_state(rho_q, "A")
            r_ab = candidate.process_state(r_a["final_state_qt"], "B")
            r_b = candidate.process_state(rho_q, "B")
            r_ba = candidate.process_state(r_b["final_state_qt"], "A")
            td_comm = _trace_dist(r_ab["final_state_qt"], r_ba["final_state_qt"])
            haar_tds.append(td_comm)
            purities.append(float(r_ab.get("final_purity", 0.0)))
            purities.append(float(r_ba.get("final_purity", 0.0)))
        except Exception as e:
            failures.append({"check": f"haar_trial_{trial}",
                             "msg": f"{type(e).__name__}: {str(e)[:120]}"})

    if not haar_tds:
        return {"pass": False, "failures": failures + [
            {"check": "haar_coverage", "msg": "no successful Haar trials"}
        ], "metrics": metrics}

    avg_haar_td = sum(haar_tds) / len(haar_tds)
    min_haar_td = min(haar_tds)
    metrics["avg_haar_commutator_td"] = avg_haar_td
    metrics["min_haar_commutator_td"] = min_haar_td
    metrics["n_haar_trials"] = len(haar_tds)
    if avg_haar_td < 0.10:
        failures.append({
            "check": "haar_noncommutation",
            "msg": f"on 12 Haar states, avg td(ρ_AB, ρ_BA) = {avg_haar_td:.4f} < 0.10. "
                   f"Engine A and Engine B effectively commute on random states — the "
                   f"non-commutation claim from Phase 02/09 doesn't extend to full-engine "
                   f"composition.",
        })

    # ===== Test 3: Purity sanity =====
    if purities:
        avg_purity = sum(purities) / len(purities)
        min_purity = min(purities)
        max_purity = max(purities)
        metrics["avg_final_purity"] = avg_purity
        metrics["min_final_purity"] = min_purity
        metrics["max_final_purity"] = max_purity
        if avg_purity < 0.05:
            failures.append({"check": "purity_too_mixed",
                             "msg": f"avg final purity {avg_purity:.4f} < 0.05 — engines destroy all coherence"})
        if avg_purity > 0.95:
            failures.append({"check": "purity_too_pure",
                             "msg": f"avg final purity {avg_purity:.4f} > 0.95 — no dissipation actually happened"})

    # Determinism
    try:
        r1 = candidate.process_state(rho_ref, "A")
        r2 = candidate.process_state(rho_ref, "A")
        if _trace_dist(r1["final_state_qt"], r2["final_state_qt"]) > 1e-6:
            failures.append({"check": "process_deterministic", "msg": "non-deterministic"})
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "engines commute on Haar states — fails haar_noncommutation (adversarial)",
            "process_state returns input unchanged — fails composability + purity",
            "process_state fully decoheres to I/16 — fails purity_too_mixed",
        ],
        "baseline_variants": [
            "concatenation of engine_stage(s, 0..7) baseline — passes composability if engine_stage already non-trivial",
        ],
    }

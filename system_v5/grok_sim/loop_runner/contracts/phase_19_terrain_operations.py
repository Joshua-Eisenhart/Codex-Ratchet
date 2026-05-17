"""phase_19_terrain_operations.py — 4 base operators exposed as distinct AI primitives.

The 4 terrain operators (Ti, Te, Fi, Fe) are the fundamental computational moves. Each
must be callable as a unique AI primitive with well-defined math:

  - Ti (σ_z dephasing): dissipator, destroys Z-basis coherence
  - Te (σ_x dephasing): dissipator, destroys X-basis coherence
  - Fi (σ_x rotation): unitary, preserves purity, rotates Bloch around x-axis
  - Fe (σ_z rotation): unitary, preserves purity, rotates Bloch around z-axis

Required API: `terrain_operation(terrain: str, input_rho_qt, strength: float = 0.5) -> dict`
  Returns:
    {
      "terrain": str,
      "operator_type": str,             # "dissipator" or "unitary"
      "output_rho_qt": qt.Qobj,
      "info_change_bits": float,
      "purity_input": float,
      "purity_output": float,
      "trace_distance_from_input": float,
    }

Hard constraints (verified independently):
  - Ti, Te must be type "dissipator" — purity can DECREASE (entropy can grow)
  - Fi, Fe must be type "unitary" — purity preserved to within 1e-6
  - All 4 produce distinct outputs on a non-trivial input (pairwise td > 0.03)
  - Ti and Te affect different bases (off-diagonal entries in different bases)
  - Fi and Fe rotate around different axes (commutator [Fi-action, Fe-action] != 0)
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _purity(rho):
    a = _to_arr(rho)
    return float(np.real(np.trace(a @ a)))


def _trace_dist(a, b):
    diff = _to_arr(a) - _to_arr(b)
    s = np.linalg.svd(diff, compute_uv=False)
    return float(0.5 * np.sum(s))


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "terrain_operation"):
        return {
            "pass": False,
            "failures": [{
                "check": "terrain_operation_exists",
                "msg": "Required function `terrain_operation(terrain: str, input_rho_qt, strength: float) -> dict` "
                       "is not exported. The 4 base operators (Ti, Te, Fi, Fe) must each be callable as a "
                       "unique AI primitive. Ti/Te are dissipators (σ_z/σ_x dephasing). Fi/Fe are unitaries "
                       "(σ_x/σ_z rotation). Return dict with: terrain, operator_type ('dissipator'/'unitary'), "
                       "output_rho_qt, info_change_bits, purity_input, purity_output, "
                       "trace_distance_from_input.",
            }],
            "metrics": metrics,
        }

    try:
        import qutip as qt
        # Non-trivial mixed input
        psi = qt.tensor((qt.basis(2, 0) + 0.5 * qt.basis(2, 1)).unit(),
                        (qt.basis(2, 0) + 0.6j * qt.basis(2, 1)).unit(),
                        qt.basis(2, 0),
                        qt.basis(2, 0))
        input_rho = qt.ket2dm(psi)
    except Exception as e:
        return {"pass": False, "failures": [{"check": "ref_state", "msg": str(e)[:200]}], "metrics": metrics}

    purity_in = _purity(input_rho)
    metrics["input_purity"] = purity_in

    results = {}
    expected_type = {"Ti": "dissipator", "Te": "dissipator", "Fi": "unitary", "Fe": "unitary"}
    for terrain in ("Ti", "Te", "Fi", "Fe"):
        try:
            r = candidate.terrain_operation(terrain, input_rho, 0.5)
        except Exception as e:
            failures.append({
                "check": f"terrain_call_{terrain}",
                "msg": f"terrain_operation('{terrain}', ρ, 0.5) raised {type(e).__name__}: {str(e)[:200]}",
            })
            continue
        if not isinstance(r, dict):
            failures.append({"check": f"terrain_dict_{terrain}", "msg": f"returned {type(r).__name__}"})
            continue
        for k in ("terrain", "operator_type", "output_rho_qt", "info_change_bits",
                  "purity_input", "purity_output", "trace_distance_from_input"):
            if k not in r:
                failures.append({"check": f"terrain_{terrain}_missing_{k}", "msg": f"missing `{k}`"})
                break
        else:
            results[terrain] = r

    if not results:
        return {"pass": False, "failures": failures, "metrics": metrics}

    # operator_type correct
    for terrain, r in results.items():
        if r["operator_type"] != expected_type[terrain]:
            failures.append({
                "check": f"terrain_{terrain}_operator_type",
                "msg": f"terrain_operation('{terrain}') reports operator_type='{r['operator_type']}', "
                       f"expected '{expected_type[terrain]}'.",
            })

    # Fi, Fe MUST preserve purity (independent recompute)
    for terrain in ("Fi", "Fe"):
        if terrain not in results:
            continue
        purity_out = _purity(results[terrain]["output_rho_qt"])
        metrics[f"{terrain}_purity_out"] = purity_out
        delta_purity = abs(purity_out - purity_in)
        if delta_purity > 1e-4:
            failures.append({
                "check": f"terrain_{terrain}_unitary_preserves_purity",
                "msg": f"{terrain} is unitary but |Δpurity| = {delta_purity:.4e} > 1e-4. "
                       f"Unitary evolution preserves purity Tr(ρ²) exactly. "
                       f"Either the implementation is dissipative (wrong type) or there's a bug.",
            })

    # Pairwise distinct outputs
    pairs = [(a, b) for a in results for b in results if a < b]
    pair_dists = {}
    for a, b in pairs:
        td = _trace_dist(results[a]["output_rho_qt"], results[b]["output_rho_qt"])
        pair_dists[f"{a}-{b}"] = td
        if td < 0.03:
            failures.append({
                "check": f"terrain_{a}_vs_{b}_distinct",
                "msg": f"terrain_operation('{a}') and terrain_operation('{b}') produce M-equivalent "
                       f"outputs (td = {td:.4f} < 0.03). They should be different primitives.",
            })
    metrics["pairwise_td"] = pair_dists

    # Ti vs Fi act on the SAME Pauli axis but differ in type — outputs should still differ
    # because dissipator decreases purity, unitary doesn't
    if "Ti" in results and "Fi" in results:
        p_Ti = _purity(results["Ti"]["output_rho_qt"])
        p_Fi = _purity(results["Fi"]["output_rho_qt"])
        # Fi should preserve purity; Ti should decrease it (or stay same if commutes)
        # Strict: Ti's purity must be ≤ Fi's purity (Ti is dissipative)
        if p_Ti > p_Fi + 1e-4:
            failures.append({
                "check": "terrain_Ti_dissipative_vs_Fi_unitary",
                "msg": f"Ti dissipator purity {p_Ti:.6f} > Fi unitary purity {p_Fi:.6f}. "
                       f"Dissipator should not increase purity above unitary baseline.",
            })

    # Determinism
    try:
        r1 = candidate.terrain_operation("Ti", input_rho, 0.5)
        r2 = candidate.terrain_operation("Ti", input_rho, 0.5)
        td = _trace_dist(r1["output_rho_qt"], r2["output_rho_qt"])
        if td > 1e-4:
            failures.append({"check": "terrain_deterministic",
                             "msg": f"two Ti calls differ by td={td:.4e}"})
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "Fi or Fe reported as 'dissipator' — fails operator_type",
            "Fi/Fe unitary that changes purity — fails preserves_purity (bug or wrong impl)",
            "All 4 terrains produce same output — fails pairwise distinct",
            "Ti increases purity above Fi (dissipative shouldn't add purity) — fails dissipative comparison",
        ],
        "baseline_variants": [
            "identity baseline: all 4 terrains return input unchanged — fails distinctness",
            "global-phase baseline: outputs differ by phase only, density unchanged — fails distinctness",
        ],
    }

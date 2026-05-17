"""phase_01_axioms.py — three foundational axiom witnesses via function calls.

Tests:
  1. M-equivalence demo: returns rho_a, rho_b that are NOT element-wise equal but DO share probe class.
  2. Finitude witness: integer that VARIES with truncation parameter.
  3. Non-commutation: trace_distance between A∘B and B∘A applied to a state must be > 1e-3.

NOTE: this phase is HIDDEN from Grok. Grok only sees the public API contract.
The thresholds and graveyard tests below are Opus's private oracle.
"""
import numpy as np


def _check_mequivalence(candidate):
    failures = []
    metrics = {}
    try:
        result = candidate.mequivalence_demo()
    except Exception as e:
        return [{"check": "mequiv_call", "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}], {}

    for key in ("rho_a_qobj", "rho_b_qobj", "are_distinct", "share_probe_class"):
        if key not in result:
            failures.append({"check": f"mequiv_missing_key_{key}", "msg": f"key `{key}` not in mequivalence_demo() return"})
    if failures:
        return failures, metrics

    metrics["are_distinct"] = bool(result["are_distinct"])
    metrics["share_probe_class"] = bool(result["share_probe_class"])

    if not result["are_distinct"]:
        failures.append({
            "check": "mequiv_must_be_distinct",
            "msg": "rho_a and rho_b are element-equal — the demo doesn't show that distinct states can share probe class",
        })
    if not result["share_probe_class"]:
        failures.append({
            "check": "mequiv_must_share_class",
            "msg": "rho_a and rho_b don't share probe class under M_ops — the M-equivalence claim is false",
        })

    # Cross-check independently: if the candidate also exposes probe_class_a/b, verify our reading matches
    if "probe_class_a" in result and "probe_class_b" in result:
        metrics["probe_class_a"] = result["probe_class_a"]
        metrics["probe_class_b"] = result["probe_class_b"]
        independent_share = tuple(result["probe_class_a"]) == tuple(result["probe_class_b"])
        if independent_share != bool(result["share_probe_class"]):
            failures.append({
                "check": "mequiv_independent_recompute",
                "msg": f"share_probe_class reported {result['share_probe_class']} but independent comparison says {independent_share}",
            })
    return failures, metrics


def _check_finitude_witness(candidate):
    """Witness must depend on truncation parameter — same input → same output, different input → different output."""
    failures = []
    metrics = {}
    try:
        w_low = candidate.finite_witness(4)
        w_mid = candidate.finite_witness(8)
        w_high = candidate.finite_witness(16)
    except Exception as e:
        return [{"check": "finitude_call", "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}], {}

    metrics["witness_at_n4"] = w_low
    metrics["witness_at_n8"] = w_mid
    metrics["witness_at_n16"] = w_high

    if not isinstance(w_mid, int):
        failures.append({
            "check": "finitude_witness_int",
            "msg": f"finite_witness(8) returned {type(w_mid).__name__}, expected int",
        })

    # Stability: same input → same output
    w_mid2 = candidate.finite_witness(8)
    metrics["witness_at_n8_repeat"] = w_mid2
    if w_mid != w_mid2:
        failures.append({
            "check": "finitude_stable",
            "msg": f"finite_witness(8) returned {w_mid} then {w_mid2} — not deterministic",
        })

    # Variability: different inputs → different outputs (at least one pair must differ)
    distinct_values = len(set([w_low, w_mid, w_high]))
    if distinct_values < 2:
        failures.append({
            "check": "finitude_varies",
            "msg": f"finite_witness returned same value for n=4,8,16 ({w_low}). Witness must VARY with truncation — otherwise it's a constant, not a witness.",
        })

    return failures, metrics


def _check_noncomm_pair(candidate):
    failures = []
    metrics = {}
    try:
        result = candidate.noncomm_pair()
    except Exception as e:
        return [{"check": "noncomm_call", "msg": f"raised {type(e).__name__}: {str(e)[:300]}"}], {}

    for key in ("rho_seq_AB", "rho_seq_BA", "trace_distance"):
        if key not in result:
            failures.append({"check": f"noncomm_missing_key_{key}", "msg": f"key `{key}` not in noncomm_pair() return"})
    if failures:
        return failures, metrics

    td = float(result["trace_distance"])
    metrics["trace_distance"] = td

    if td < 1e-3:
        failures.append({
            "check": "noncomm_distinguishable",
            "msg": f"trace_distance = {td:.2e} is below threshold 1e-3 — operators may commute or initial state is in their joint eigenspace",
        })

    # Independent verification: recompute trace distance from the returned rhos
    try:
        rho_AB = result["rho_seq_AB"]
        rho_BA = result["rho_seq_BA"]
        # Accept either torch tensor or numpy/qobj
        if hasattr(rho_AB, "numpy"):
            a = rho_AB.detach().cpu().numpy()
            b = rho_BA.detach().cpu().numpy()
        elif hasattr(rho_AB, "full"):
            a = rho_AB.full()
            b = rho_BA.full()
        else:
            a = np.asarray(rho_AB)
            b = np.asarray(rho_BA)
        # Trace distance = 0.5 * trace |A - B| = 0.5 * sum of singular values
        diff = a - b
        s = np.linalg.svd(diff, compute_uv=False)
        td_recomputed = float(0.5 * np.sum(s))
        metrics["trace_distance_independent_recompute"] = td_recomputed
        if abs(td - td_recomputed) > 0.05:
            failures.append({
                "check": "noncomm_recompute_matches",
                "msg": f"reported trace_distance {td:.4f} disagrees with independent recompute {td_recomputed:.4f}",
            })
    except Exception as e:
        failures.append({"check": "noncomm_recompute_call", "msg": f"independent recompute failed: {str(e)[:200]}"})

    return failures, metrics


def run(candidate):
    all_failures = []
    all_metrics = {}

    for name, check_fn in [("mequivalence", _check_mequivalence),
                           ("finitude", _check_finitude_witness),
                           ("noncommutation", _check_noncomm_pair)]:
        f, m = check_fn(candidate)
        all_failures.extend(f)
        all_metrics[name] = m

    return {
        "pass": len(all_failures) == 0,
        "failures": all_failures,
        "metrics": all_metrics,
        "graveyard_companions": [
            "rho_a == rho_b (element-equal) — must fail are_distinct",
            "rho_a, rho_b with DIFFERENT probe classes — must fail share_probe_class",
            "finite_witness(n) constant in n — must fail varies",
            "A∘B = B∘A (commuting operators) — must fail noncomm trace distance",
            "initial state in joint eigenspace of A and B — must fail noncomm",
        ],
        "baseline_variants": [
            "pure-state baseline: |0000><0000| (zero entropy, but should still satisfy axioms)",
            "maximally mixed baseline: I/16 (any unitary leaves it invariant)",
        ],
    }

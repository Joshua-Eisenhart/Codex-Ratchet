"""phase_22_probe_quotient_compression.py — probe-quotient as a lossy compression primitive.

The probe family M defines an equivalence quotient: any two density matrices with the
same probe expectations are M-equivalent. This phase exposes the quotient as a callable
compression operation:
  - Input: 16x16 density matrix (256 complex numbers, but Hermitian + trace-1 → ~120 real DOFs)
  - Output: |M|-vector of probe expectations + a canonical M-class representative

The compression ratio = (degrees of freedom in input) / (size of probe vector).
Recovery distance: how far the canonical representative is from the input under trace distance.

Required API: `probe_quotient_compress(input_rho_qt) -> dict`
  Returns:
    {
      "input_rho_qt": qt.Qobj,
      "probe_vector": list[float],         # |M|-dim representation (lossy compressed)
      "canonical_rho_qt": qt.Qobj,          # M-class representative
      "compression_ratio": float,           # input_DOF / output_DOF
      "recovery_trace_distance": float,    # td(input_rho, canonical_rho)
    }

Constraints:
  - For two M-equivalent inputs (constructed independently), the probe_vector is identical
  - Compression ratio > 1 (output smaller than input)
  - recovery_trace_distance can be > 0 (lossy is OK — that's the point)
  - Deterministic
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "probe_quotient_compress"):
        return {
            "pass": False,
            "failures": [{
                "check": "probe_quotient_compress_exists",
                "msg": "Required function `probe_quotient_compress(input_rho_qt) -> dict` is not exported. "
                       "The probe family M defines an equivalence quotient on density matrices. "
                       "Use this as a callable AI primitive: input a 16×16 density matrix; output "
                       "(a) its probe_vector under M, (b) a canonical M-class representative, "
                       "(c) compression_ratio (input_DOF / output_DOF), (d) recovery_trace_distance.",
            }],
            "metrics": metrics,
        }

    try:
        import qutip as qt
        # Use the candidate's M-equivalent demo states — they should compress identically
        m_demo = candidate.mequivalence_demo()
        rho_a = m_demo["rho_a_qobj"]
        rho_b = m_demo["rho_b_qobj"]
    except Exception as e:
        return {"pass": False,
                "failures": [{"check": "mequiv_demo_for_compression", "msg": str(e)[:200]}],
                "metrics": metrics}

    try:
        result_a = candidate.probe_quotient_compress(rho_a)
        result_b = candidate.probe_quotient_compress(rho_b)
    except Exception as e:
        return {"pass": False,
                "failures": [{"check": "probe_quotient_compress_call", "msg": f"raised {type(e).__name__}: {str(e)[:200]}"}],
                "metrics": metrics}

    for result, label in ((result_a, "a"), (result_b, "b")):
        if not isinstance(result, dict):
            failures.append({"check": f"compression_dict_{label}", "msg": f"returned {type(result).__name__}"})
            continue
        for k in ("probe_vector", "canonical_rho_qt", "compression_ratio", "recovery_trace_distance"):
            if k not in result:
                failures.append({"check": f"compression_{label}_missing_{k}", "msg": f"missing `{k}`"})

    if failures:
        return {"pass": False, "failures": failures, "metrics": metrics}

    # M-equivalent inputs → identical probe vectors
    pv_a = np.asarray(result_a["probe_vector"], dtype=float)
    pv_b = np.asarray(result_b["probe_vector"], dtype=float)
    pv_diff = float(np.max(np.abs(pv_a - pv_b)))
    metrics["mequiv_inputs_probe_diff"] = pv_diff
    if pv_diff > 1e-4:
        failures.append({
            "check": "compression_mequiv_preserves",
            "msg": f"M-equivalent inputs ρ_a, ρ_b (verified in Phase 01) gave different probe vectors: "
                   f"max |Δ| = {pv_diff:.4e}. The quotient compression must produce IDENTICAL probe "
                   f"vectors for M-equivalent inputs by definition.",
        })

    # Compression ratio > 1
    ratio = float(result_a["compression_ratio"])
    metrics["compression_ratio"] = ratio
    if ratio <= 1.0:
        failures.append({
            "check": "compression_ratio_meaningful",
            "msg": f"compression_ratio = {ratio:.4f} ≤ 1. Output not smaller than input — "
                   f"no actual compression. Probe vector should be |M|-dim, input is 16×16 "
                   f"matrix (≥120 real DOFs); ratio should be > 10.",
        })

    # Recovery distance is real-valued non-negative
    rec = float(result_a["recovery_trace_distance"])
    metrics["recovery_distance"] = rec
    if rec < -1e-6 or rec > 1.5:
        failures.append({
            "check": "compression_recovery_in_range",
            "msg": f"recovery_trace_distance = {rec:.4f} not in [0, 1.5]",
        })

    # Determinism
    try:
        r2 = candidate.probe_quotient_compress(rho_a)
        pv_re = np.asarray(r2["probe_vector"], dtype=float)
        if float(np.max(np.abs(pv_a - pv_re))) > 1e-6:
            failures.append({"check": "compression_deterministic",
                             "msg": "two calls returned different probe_vectors"})
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "compression returns input unchanged — fails compression_ratio (ratio = 1)",
            "compression random — fails determinism",
            "compression that distinguishes M-equiv inputs — fails compression_mequiv_preserves",
        ],
        "baseline_variants": [
            "identity baseline (no compression) — ratio = 1, fails",
            "JPEG-style classical compression — wrong domain (not quantum probe-quotient)",
        ],
    }

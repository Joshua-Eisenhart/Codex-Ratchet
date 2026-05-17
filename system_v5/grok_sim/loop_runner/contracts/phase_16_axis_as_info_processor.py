"""phase_16_axis_as_info_processor.py — each of 7 axes is a UNIQUE info-processing primitive.

Required new API: `axis_transform(axis_index: int, input_rho_qt) -> dict`
  Takes axis 0..6 and a 16x16 qutip density matrix.
  Returns:
    {
      "axis_index": int,
      "output_rho_qt": qt.Qobj,             # 16x16 density matrix after axis-specific transformation
      "info_change_bits": float,            # ΔS = S(output) - S(input), in bits
      "trace_distance_from_input": float,
      "fingerprint": list[float],            # vector of probe expectations on output
    }

Each axis must transform a REFERENCE STATE into a UNIQUELY identifiable output:
  - 7 axes → 7 distinct output states (pairwise trace_distance > 0.03)
  - 7 axes → 7 distinct fingerprints (pairwise fingerprint distance > 0.03)
  - 7 axes → 7 distinct information-change signatures

This is the "AI tool set" property — the 7 axes give AI 7 genuinely DIFFERENT computational
primitives. If two axes give the same transformation, the architecture has fewer dimensions
than claimed.
"""
import numpy as np


def _qobj_to_array(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return np.asarray(obj.detach().cpu().numpy()) if hasattr(obj, "detach") else np.asarray(obj.numpy())
    return np.asarray(obj)


def _trace_distance_np(a, b):
    diff = a - b
    s = np.linalg.svd(diff, compute_uv=False)
    return float(0.5 * np.sum(s))


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "axis_transform"):
        return {
            "pass": False,
            "failures": [{
                "check": "axis_transform_exists",
                "msg": "Required function `axis_transform(axis_index: int, input_rho_qt) -> dict` is not exported. "
                       "Each of the 7 axes must be exposable as a distinct information-processing primitive: "
                       "given an input density matrix, axis N transforms it into output_rho_qt that's "
                       "M-distinguishable from outputs of other axes. Return dict with: axis_index, "
                       "output_rho_qt (qt.Qobj 16x16), info_change_bits (float), trace_distance_from_input "
                       "(float), fingerprint (list of probe expectations).",
            }],
            "metrics": metrics,
        }

    # Construct a reference input state (non-trivial mixed state for max sensitivity)
    try:
        import qutip as qt
        psi = qt.tensor((qt.basis(2, 0) + 0.7 * qt.basis(2, 1)).unit(),
                        (qt.basis(2, 0) + 0.5 * qt.basis(2, 1)).unit(),
                        qt.basis(2, 0),
                        (qt.basis(2, 0) + 0.3j * qt.basis(2, 1)).unit())
        input_rho = qt.ket2dm(psi)
    except Exception as e:
        return {
            "pass": False,
            "failures": [{"check": "ref_state_construction",
                          "msg": f"could not construct reference input state: {e}"}],
            "metrics": metrics,
        }

    input_arr = _qobj_to_array(input_rho)
    outputs = {}
    fingerprints = {}
    info_changes = {}

    for axis_idx in range(7):
        try:
            r = candidate.axis_transform(axis_idx, input_rho)
        except Exception as e:
            failures.append({"check": f"axis_transform_axis_{axis_idx}_call",
                             "msg": f"axis_transform({axis_idx}, ρ) raised {type(e).__name__}: {str(e)[:200]}"})
            continue

        if not isinstance(r, dict):
            failures.append({"check": f"axis_transform_axis_{axis_idx}_dict",
                             "msg": f"returned {type(r).__name__}, expected dict"})
            continue

        for key in ("output_rho_qt", "info_change_bits", "trace_distance_from_input", "fingerprint"):
            if key not in r:
                failures.append({"check": f"axis_{axis_idx}_missing_{key}",
                                 "msg": f"axis_transform({axis_idx}) result missing `{key}`"})

        if any(f["check"].startswith(f"axis_{axis_idx}_missing") for f in failures):
            continue

        try:
            out_arr = _qobj_to_array(r["output_rho_qt"])
            outputs[axis_idx] = out_arr
            fingerprints[axis_idx] = [float(x) for x in r["fingerprint"]]
            info_changes[axis_idx] = float(r["info_change_bits"])
        except Exception as e:
            failures.append({"check": f"axis_{axis_idx}_parse_output",
                             "msg": f"could not parse output: {e}"})

    if not outputs:
        return {"pass": False, "failures": failures, "metrics": metrics}

    # Pairwise distinguishability of outputs
    pair_distances = {}
    duplicate_pairs = []
    for i in range(7):
        if i not in outputs:
            continue
        for j in range(i + 1, 7):
            if j not in outputs:
                continue
            td = _trace_distance_np(outputs[i], outputs[j])
            pair_distances[f"Ax{i}-Ax{j}"] = td
            if td < 0.03:
                duplicate_pairs.append((i, j, td))

    metrics["pair_distances"] = pair_distances
    metrics["info_changes"] = info_changes

    if duplicate_pairs:
        for i, j, td in duplicate_pairs:
            failures.append({
                "check": f"axis_distinct_Ax{i}_Ax{j}",
                "msg": f"axis_transform({i}) and axis_transform({j}) produce M-equivalent outputs "
                       f"(trace_distance = {td:.4f} < 0.03). The two axes are not genuinely "
                       f"different information-processing primitives on this input state.",
            })

    # Pairwise fingerprint distance
    fp_pair = {}
    duplicate_fingerprints = []
    for i in range(7):
        if i not in fingerprints:
            continue
        for j in range(i + 1, 7):
            if j not in fingerprints:
                continue
            fi = np.asarray(fingerprints[i])
            fj = np.asarray(fingerprints[j])
            if len(fi) != len(fj):
                failures.append({"check": f"fingerprint_shape_{i}_vs_{j}",
                                 "msg": f"axis {i} fingerprint len {len(fi)}, axis {j} len {len(fj)}"})
                continue
            d = float(np.linalg.norm(fi - fj))
            fp_pair[f"fp_Ax{i}-Ax{j}"] = d
            if d < 0.03:
                duplicate_fingerprints.append((i, j, d))
    metrics["fingerprint_distances"] = fp_pair

    if duplicate_fingerprints:
        for i, j, d in duplicate_fingerprints:
            failures.append({
                "check": f"fingerprint_distinct_Ax{i}_Ax{j}",
                "msg": f"axis {i} and axis {j} have near-identical fingerprints (L2 distance = {d:.4f} < 0.03).",
            })

    # Determinism: same axis_transform twice gives same output
    try:
        a0_r1 = candidate.axis_transform(0, input_rho)
        a0_r2 = candidate.axis_transform(0, input_rho)
        td = _trace_distance_np(_qobj_to_array(a0_r1["output_rho_qt"]),
                                 _qobj_to_array(a0_r2["output_rho_qt"]))
        metrics["axis_0_determinism_td"] = td
        if td > 1e-4:
            failures.append({"check": "axis_transform_deterministic",
                             "msg": f"two calls to axis_transform(0, ρ) gave outputs differing by td={td:.2e}"})
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "axis_transform returns input unchanged — fails all distance > 0.03 checks",
            "all 7 axes apply the same operator — fails pairwise distinctness",
            "axis_transform uses randomness — fails determinism",
            "fingerprint is constant — fails fingerprint distinctness",
        ],
        "baseline_variants": [
            "identity transform baseline — all axes give same output as input, trivially indistinct",
            "random permutation baseline — outputs distinct but not deterministic",
        ],
    }

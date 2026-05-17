"""phase_31_constraint_manifold.py — the constraint manifold must exist BEFORE the axes.

The user's repeated directive: "doesn't the geometric constraint manifold have to be
done before the axes?" This phase forces the architecture to commit to one: the 16
stage trajectories must live on a low-dimensional submanifold of state space, not
fill the ambient 256-dim density-matrix space uniformly.

Test protocol:
  1. Sample K=8 different reference states (varied initial structure)
  2. For each ref state, collect 16 stage-aggregate outputs from engine_stage
  3. Stack into a matrix M of shape (K*16, 256) where each row is a flattened
     (real + imaginary parts) density matrix
  4. Compute SVD; effective rank = number of singular values > 0.01 × σ_max
  5. PASS: effective rank ≤ 40 (real manifold structure; ~16-dim trajectory ×
     ~2 engine variation × ~K reference variation; allows curvature)
     FAIL: effective rank > 80 (no manifold; outputs span ambient space)
  6. Cross-check: a control set of K*16 RANDOM density matrices should have
     effective rank near 256. If candidate's outputs have rank comparable to
     random, no manifold structure exists.
  7. Stage trajectories from DIFFERENT reference states should be similar up to
     a rigid transformation (manifold geometry is intrinsic, not state-dependent).

This catches: "engine_stage produces well-separated points filling the ambient
state space, with no submanifold structure" — i.e., 16 random-direction outputs.
"""
import numpy as np


def _to_arr(obj):
    if hasattr(obj, "full"):
        return np.asarray(obj.full())
    if hasattr(obj, "numpy"):
        return obj.detach().cpu().numpy() if hasattr(obj, "detach") else obj.numpy()
    return np.asarray(obj)


def _flatten_rho(rho_arr):
    """Flatten 16x16 complex density matrix into a 512-dim real vector (real, imag)."""
    arr = rho_arr.astype(complex)
    return np.concatenate([arr.real.flatten(), arr.imag.flatten()])


def _effective_rank(M, threshold_ratio=0.01):
    s = np.linalg.svd(M, compute_uv=False)
    if len(s) == 0 or s[0] == 0:
        return 0
    return int(np.sum(s > threshold_ratio * s[0]))


def _trace_dist(a, b):
    diff = _to_arr(a) - _to_arr(b)
    s = np.linalg.svd(diff, compute_uv=False)
    return float(0.5 * np.sum(s))


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "engine_stage"):
        return {"pass": False,
                "failures": [{"check": "engine_stage_exists", "msg": "see Phase 28."}],
                "metrics": metrics}

    try:
        import qutip as qt
    except Exception as e:
        return {"pass": False, "failures": [{"check": "qutip", "msg": str(e)[:160]}], "metrics": metrics}

    # K=8 reference states with varied structure
    ref_states = []
    np.random.seed(20260513)
    for k in range(8):
        # Build a varied 4-qubit state: random amplitudes
        amps = [(qt.basis(2, 0) + (0.3 + 0.1 * k + 0.05j * (k + 1)) * qt.basis(2, 1)).unit()
                for _ in range(4)]
        psi = qt.tensor(*amps)
        ref_states.append(qt.ket2dm(psi))

    # Collect outputs: K refs × 16 stages × 4 substages → aggregate over substages to 16 per ref
    rows = []  # flattened 16x16 density matrices
    per_ref_aggregates = []  # list of {(engine,stage) -> arr}
    for ref_idx, rho_ref in enumerate(ref_states):
        agg = {}
        for engine in ("A", "B"):
            for s in range(8):
                subs = []
                for sub in range(4):
                    try:
                        r = candidate.engine_stage(engine, s, sub, rho_ref)
                        out = r.get("output_rho_qt") if isinstance(r, dict) else r
                        subs.append(_to_arr(out))
                    except Exception as e:
                        failures.append({"check": f"call_{ref_idx}_{engine}_{s}_{sub}",
                                         "msg": str(e)[:120]})
                if subs:
                    arr = sum(subs) / len(subs)
                    agg[(engine, s)] = arr
                    rows.append(_flatten_rho(arr))
        per_ref_aggregates.append(agg)

    metrics["total_aggregate_samples"] = len(rows)
    if len(rows) < 100:
        return {"pass": False, "failures": failures + [
            {"check": "samples_collected", "msg": f"only {len(rows)} samples"}
        ], "metrics": metrics}

    M = np.array(rows)
    eff_rank = _effective_rank(M, threshold_ratio=0.01)
    s_vals = np.linalg.svd(M, compute_uv=False)
    metrics["effective_rank_eps_0p01"] = eff_rank
    metrics["effective_rank_eps_0p001"] = int(np.sum(s_vals > 0.001 * s_vals[0])) if len(s_vals) else 0
    metrics["top_singular"] = float(s_vals[0]) if len(s_vals) else 0.0
    metrics["matrix_shape"] = list(M.shape)

    if eff_rank > 80:
        failures.append({
            "check": "manifold_low_rank",
            "msg": f"effective rank = {eff_rank} > 80. Stage outputs fill too much of the "
                   f"ambient 512-dim (real+imag) space — no genuine low-dim constraint "
                   f"manifold structure. The 'manifold before axes' commitment is unmet.",
        })

    # Control: random valid density matrices
    rng = np.random.default_rng(42)
    rand_rows = []
    for _ in range(len(rows)):
        A = rng.normal(size=(16, 16)) + 1j * rng.normal(size=(16, 16))
        rho_rand = A @ A.conj().T
        rho_rand /= np.trace(rho_rand).real
        rand_rows.append(_flatten_rho(rho_rand))
    M_rand = np.array(rand_rows)
    rand_rank = _effective_rank(M_rand, threshold_ratio=0.01)
    metrics["control_random_effective_rank"] = rand_rank
    metrics["rank_compression_factor"] = rand_rank / max(eff_rank, 1)

    if eff_rank >= 0.7 * rand_rank:
        failures.append({
            "check": "manifold_vs_random",
            "msg": f"effective rank {eff_rank} is ≥70% of random-density-matrix control "
                   f"({rand_rank}). Candidate doesn't compress the space — same dimensionality "
                   f"as random states means no architectural constraint.",
        })

    # Cross-reference geometry: per-engine 8-step path matrix should be similar
    # across reference states (modulo overall scale).
    if len(per_ref_aggregates) >= 2:
        consistency_dists = []
        for ri in range(len(per_ref_aggregates) - 1):
            agg1 = per_ref_aggregates[ri]
            agg2 = per_ref_aggregates[ri + 1]
            for e in ("A", "B"):
                m1 = np.array([[_trace_dist(agg1[(e, i)], agg1[(e, j)])
                                for j in range(8)] for i in range(8)])
                m2 = np.array([[_trace_dist(agg2[(e, i)], agg2[(e, j)])
                                for j in range(8)] for i in range(8)])
                # Normalize each matrix to unit Frobenius
                n1 = np.linalg.norm(m1, ord="fro") or 1.0
                n2 = np.linalg.norm(m2, ord="fro") or 1.0
                diff = float(np.linalg.norm(m1 / n1 - m2 / n2, ord="fro"))
                consistency_dists.append(diff)
        avg_inconsist = sum(consistency_dists) / len(consistency_dists)
        metrics["avg_cross_ref_pathshape_inconsistency"] = avg_inconsist
        if avg_inconsist > 0.45:
            failures.append({
                "check": "manifold_intrinsic_geometry",
                "msg": f"avg normalized path-shape inconsistency across reference states = "
                       f"{avg_inconsist:.4f} > 0.45. The 8-stage trajectory shape varies wildly "
                       f"with the input state — the manifold is not intrinsic.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "random-direction stages — passes Phase 28/30, fails manifold_low_rank",
            "ambient-spanning outputs — eff_rank ≈ rand_rank, fails manifold_vs_random",
            "state-dependent path shape — fails manifold_intrinsic_geometry",
        ],
        "baseline_variants": [
            "identity baseline: all stages return input — eff_rank tiny, passes trivially",
            "pure dephasing baseline: outputs collapse to diagonals — passes low-rank but fails Phase 28 uniqueness",
        ],
    }

#!/usr/bin/env python3
"""Gap F closure probe: ott Sinkhorn transport on the REAL shipped profile pair.

Gap F (from real_data_integration_results.json): the prior transport-on-real-data
probe recomputed a WRONG pair (tv "59/160", tv_matches_receipt false) and its
Sinkhorn setup had nonzero self-cost. This probe closes the gap:

1. Import the actual sim module (packet166b ontological_finitude_cosmogenesis_
   ratchet_sim.py) and iterate ITS update() dynamics round by round in the
   joint_order_bracket context until the permutation-control pair
   (profile, rotate-by-one) has total variation EXACTLY 137/160 -- the shipped
   receipt value. Scan all contexts/rounds and all cross-context endpoint pairs
   to show which pairs hit that value.
2. Run ott Sinkhorn on that exact pair under the 0/1 discrete ground metric
   (under which optimal transport cost equals total variation), versus
   self-transport. Confirm the marginal Shannon entropy difference is exactly 0
   while transport separates the pair.
3. Cross-check the exact orbit + TV in Julia with Rational{BigInt} arithmetic.

Controls must be able to fail: wrong-round pair, wrong pair, and a perturbed
pair all must MISS 137/160 / zero-entropy-difference, and the perturbed pair's
Sinkhorn cost must miss the target.

classification: tool_lego_fit_probe; promotion_allowed: false.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path

SIM_DIR = Path(
    "/private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/"
    "ae78ff9c-0704-43c0-81b3-af566c1b5861/scratchpad/packet166b/sims_and_scripts"
)
SIM_PATH = SIM_DIR / "ontological_finitude_cosmogenesis_ratchet_sim.py"
SHIPPED_RECEIPT = SIM_DIR / "ontological_finitude_cosmogenesis_ratchet_sim_results.json"
HERE = Path(__file__).resolve().parent
JULIA_BIN = "/opt/homebrew/bin/julia"
JULIA_SCRIPT = HERE / "gap_f_exact_pair_check.jl"
OUT_PATH = HERE / "gap_f_ott_real_pair_results.json"
TARGET_TV = Fraction(137, 160)
PRIOR_FAILED_TV = Fraction(59, 160)  # value the failed gap-F probe reported

sys.path.insert(0, str(SIM_DIR))
import ontological_finitude_cosmogenesis_ratchet_sim as sim  # noqa: E402

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import ott  # noqa: E402
from ott.geometry import geometry  # noqa: E402
from ott.problems.linear import linear_problem  # noqa: E402
from ott.solvers.linear import sinkhorn  # noqa: E402


def rot1(profile: tuple[int, ...]) -> tuple[int, ...]:
    """The sim's entropy_controls() rotation: joint[1:] + joint[:1]."""
    return profile[1:] + profile[:1]


def frac_str(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator}"


def sinkhorn_cost(a_counts, b_counts, cost_matrix, eps):
    a = jnp.asarray(a_counts, dtype=jnp.float64)
    b = jnp.asarray(b_counts, dtype=jnp.float64)
    a = a / a.sum()
    b = b / b.sum()
    geom = geometry.Geometry(cost_matrix=cost_matrix, epsilon=eps)
    solver = sinkhorn.Sinkhorn(threshold=1e-9, max_iterations=200000, lse_mode=True)
    out = solver(linear_problem.LinearProblem(geom, a=a, b=b))
    transport_cost = float(jnp.sum(out.matrix * cost_matrix))
    return transport_cost, bool(out.converged), float(out.reg_ot_cost)


def main() -> int:
    assert jax.config.read("jax_enable_x64"), "JAX_ENABLE_X64=1 required"

    # ---- 1. Re-execute the sim's own dynamics; iterate rounds until TV == 137/160.
    contexts = ("flat", "order_sensitive", "bracket_sensitive", "joint_order_bracket")
    orbits = {name: sim.orbit(sim.INITIAL, name) for name in contexts}

    joint_endpoint = tuple(orbits["joint_order_bracket"]["endpoint"])
    round_trace = []
    rounds_hitting_target = []
    shipped_pair_round = None
    profile = sim.INITIAL
    for round_index in range(0, 32):
        if round_index > 0:
            profile = sim.update(profile, "joint_order_bracket")
        tv_here = sim.total_variation(profile, rot1(profile))
        hit = tv_here == TARGET_TV
        round_trace.append(
            {"round": round_index, "tv_profile_vs_rot1": frac_str(tv_here), "hits_target": hit}
        )
        if hit:
            rounds_hitting_target.append(round_index)
        # the shipped control is computed on the orbit ENDPOINT (a fixed point);
        # TV alone is NOT unique (round 6 also hits 137/160), so the shipped pair
        # is selected by endpoint identity AND target TV, never by TV alone.
        if hit and profile == joint_endpoint and shipped_pair_round is None:
            shipped_pair_round = round_index
        if shipped_pair_round is not None and round_index >= shipped_pair_round + 1:
            break
    assert rounds_hitting_target, "no round reached TV == 137/160"
    assert shipped_pair_round is not None, "endpoint pair never reached TV == 137/160"
    P = joint_endpoint
    Q = rot1(P)
    endpoint_is_fixed_point = sim.update(P, "joint_order_bracket") == P
    tv_value_unique_to_one_profile = len(
        {tuple(orbits["joint_order_bracket"]["history"][k]) for k in rounds_hitting_target
         if k < len(orbits["joint_order_bracket"]["history"])}
    ) == 1

    # ---- scan every shipped pair candidate: (context, round) rot-pairs + endpoint edges
    scan_hits, scan_prior_value_hits, pairs_scanned = [], [], 0
    for name, orb in orbits.items():
        for k, row in enumerate(orb["history"]):
            prof = tuple(row)
            tv_val = sim.total_variation(prof, rot1(prof))
            pairs_scanned += 1
            if tv_val == TARGET_TV:
                scan_hits.append({"kind": "rot1_control", "context": name, "round": k})
            if tv_val == PRIOR_FAILED_TV:
                scan_prior_value_hits.append({"kind": "rot1_control", "context": name, "round": k})
    endpoints = {name: tuple(orb["endpoint"]) for name, orb in orbits.items()}
    for left, right in combinations(contexts, 2):
        tv_val = sim.total_variation(endpoints[left], endpoints[right])
        pairs_scanned += 1
        if tv_val == TARGET_TV:
            scan_hits.append({"kind": "field_edge", "left": left, "right": right})
        if tv_val == PRIOR_FAILED_TV:
            scan_prior_value_hits.append(
                {"kind": "field_edge", "left": left, "right": right,
                 "tv": frac_str(tv_val)}
            )
    hits_only_in_joint_context = len(scan_hits) > 0 and all(
        h["kind"] == "rot1_control" and h["context"] == "joint_order_bracket"
        for h in scan_hits
    )
    distinct_hit_profiles = sorted(
        {tuple(orbits["joint_order_bracket"]["history"][h["round"]])
         for h in scan_hits if h["kind"] == "rot1_control"}
    )

    # ---- compare with the shipped receipt
    shipped = json.loads(SHIPPED_RECEIPT.read_text())
    shipped_ctrl = shipped["controls"]["permutation_blindness_of_scalar_entropy"]
    shipped_tv = shipped_ctrl["total_variation_fraction"]
    shipped_entropy_diff = shipped_ctrl["absolute_entropy_difference"]
    shipped_endpoint = tuple(shipped["constraint_orbits"]["joint_order_bracket"]["endpoint"])

    # ---- 2. entropy identity on the exact pair
    h_p = sim.shannon(P)
    h_q = sim.shannon(Q)
    entropy_diff_float = h_p - h_q
    multiset_equal = sorted(P) == sorted(Q)

    # ---- ott Sinkhorn: 0/1 ground metric (OT cost == total variation), sweep + final
    C = 1.0 - jnp.eye(len(P), dtype=jnp.float64)
    sweep = []
    for eps in (0.1, 0.03, 0.01, 0.003, 0.001):
        cx, convx, regx = sinkhorn_cost(P, Q, C, eps)
        cs, convs, regs = sinkhorn_cost(P, P, C, eps)
        sweep.append(
            {"epsilon": eps,
             "cross_transport_cost": cx, "cross_converged": convx, "cross_reg_ot_cost": regx,
             "self_transport_cost": cs, "self_converged": convs, "self_reg_ot_cost": regs,
             "abs_error_cross_vs_tv": abs(cx - float(TARGET_TV))}
        )
    final = sweep[-1]
    tv_float = float(TARGET_TV)

    # ---- 3. negative controls (each must be ABLE to fail, and must fail here)
    wrong_round_profile = tuple(orbits["joint_order_bracket"]["history"][1])
    tv_wrong_round = sim.total_variation(wrong_round_profile, rot1(wrong_round_profile))
    tv_wrong_pair = sim.total_variation(P, sim.INITIAL)
    perturbed = list(Q)
    perturbed[9] -= 1   # 69 -> 68  (Q side larger than P here)
    perturbed[10] += 1  # 2 -> 3    (Q side smaller than P here)
    perturbed = tuple(perturbed)
    assert sum(perturbed) == sim.BUDGET and min(perturbed) >= 1
    tv_perturbed = sim.total_variation(P, perturbed)
    entropy_diff_perturbed = sim.shannon(P) - sim.shannon(perturbed)
    cpert, convpert, _ = sinkhorn_cost(P, perturbed, C, 0.001)
    entropy_diff_nonperm = abs(sim.shannon(P) - sim.shannon(sim.INITIAL))

    # ---- Julia cross-engine exact recomputation
    jl = subprocess.run(
        [JULIA_BIN, "--startup-file=no", str(JULIA_SCRIPT)],
        capture_output=True, text=True, timeout=300,
    )
    julia_ok = jl.returncode == 0
    julia_report = json.loads(jl.stdout.strip().splitlines()[-1]) if julia_ok else {
        "error": jl.stderr[-2000:]
    }

    checks = {
        "pair_recomputed_from_sim_update_dynamics": shipped_pair_round is not None
        and endpoint_is_fixed_point and P == joint_endpoint,
        "tv_exact_equals_137_160": sim.total_variation(P, Q) == TARGET_TV,
        "tv_matches_shipped_receipt_string": frac_str(sim.total_variation(P, Q)) == shipped_tv,
        "endpoint_matches_shipped_receipt": P == shipped_endpoint,
        "scan_hits_confined_to_joint_context_rot1_controls": hits_only_in_joint_context,
        "shipped_pair_selected_by_endpoint_identity_not_tv_alone": P == shipped_endpoint
        and endpoint_is_fixed_point,
        "entropy_diff_float_exactly_zero": entropy_diff_float == 0.0
        and shipped_entropy_diff == 0.0,
        "entropy_exactly_equal_by_multiset": multiset_equal,
        "sinkhorn_cross_cost_matches_tv_1e9": final["cross_converged"]
        and abs(final["cross_transport_cost"] - tv_float) < 1e-9,
        "sinkhorn_self_cost_zero_1e12": final["self_converged"]
        and final["self_transport_cost"] < 1e-12,
        "sinkhorn_separates_pair_entropy_cannot": (
            final["cross_transport_cost"] - final["self_transport_cost"]
        ) > 0.5,
        "control_wrong_round_tv_differs": tv_wrong_round != TARGET_TV,
        "control_wrong_pair_tv_differs": tv_wrong_pair != TARGET_TV,
        "control_perturbed_tv_differs": tv_perturbed != TARGET_TV,
        "control_perturbed_entropy_diff_nonzero": entropy_diff_perturbed != 0.0,
        "control_perturbed_sinkhorn_cost_misses_target": convpert
        and abs(cpert - tv_float) > 1e-3,
        "control_nonpermutation_entropy_diff_nonzero": entropy_diff_nonperm > 1e-6,
        "julia_ran": julia_ok,
        "julia_tv_confirms_137_160": bool(julia_report.get("tv_equals_137_160", False)),
        "julia_endpoint_matches_python": tuple(julia_report.get("endpoint", ())) == P,
        "julia_fixed_point": bool(julia_report.get("fixed_point", False)),
        "julia_control_wrong_pair_differs": bool(
            julia_report.get("control_wrong_pair_differs", False)
        ),
    }
    all_pass = all(checks.values())

    result = {
        "schema": "stress_battery.gap_f_ott_real_pair.v1",
        "gap": "F",
        "gap_statement": (
            "transport (ott Sinkhorn) exercised on REAL sim data: the exact shipped "
            "permutation-control pair of ontological_finitude_cosmogenesis_ratchet_sim, "
            "recomputed from the sim's own update() dynamics, not synthetic vectors. "
            "Prior probe (real_data_integration_results.json) used a wrong pair "
            "(tv 59/160) and had nonzero self-cost."
        ),
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "claim_ceiling": (
            "tool-lego fit evidence only: ott Sinkhorn under a 0/1 ground metric "
            "independently recovers the exact shipped total variation on the real pair; "
            "no canonical, bridge, QIT, GStack, axis, or nonclassical admission"
        ),
        "all_pass": all_pass,
        "checks": checks,
        "source": {
            "sim_path": str(SIM_PATH),
            "sim_sha256": hashlib.sha256(SIM_PATH.read_bytes()).hexdigest(),
            "shipped_receipt_path": str(SHIPPED_RECEIPT),
            "shipped_total_variation_fraction": shipped_tv,
            "shipped_absolute_entropy_difference": shipped_entropy_diff,
            "pair_definition": (
                "entropy_controls() permutation control: P = joint_order_bracket orbit "
                "endpoint from INITIAL (uniform 10 x 16, budget 160); Q = P[1:] + P[:1]"
            ),
        },
        "pair_search": {
            "context": "joint_order_bracket",
            "round_trace_tv_profile_vs_rot1": round_trace,
            "rounds_where_tv_equals_137_160": rounds_hitting_target,
            "shipped_pair_round": shipped_pair_round,
            "endpoint_is_fixed_point_of_update": endpoint_is_fixed_point,
            "profile_P": list(P),
            "profile_Q_rot1": list(Q),
            "tv_exact": frac_str(sim.total_variation(P, Q)),
            "pairs_scanned": pairs_scanned,
            "scan_hits_137_160": scan_hits,
            "scan_hits_prior_failed_value_59_160": scan_prior_value_hits,
            "nonuniqueness_finding": {
                "tv_value_unique_to_one_profile": tv_value_unique_to_one_profile,
                "distinct_profiles_hitting_137_160": [list(p) for p in distinct_hit_profiles],
                "note": (
                    "TV 137/160 alone does NOT uniquely identify the shipped pair: the "
                    "round-6 pre-convergence profile's rot1 pair also has TV exactly "
                    "137/160. The shipped control is computed on the orbit ENDPOINT "
                    "(constraint_orbits.joint_order_bracket.endpoint, a fixed point), so "
                    "the pair is pinned by endpoint identity plus the TV value."
                ),
            },
        },
        "entropy_identity": {
            "shannon_P_nats": h_p,
            "shannon_Q_nats": h_q,
            "difference_float": entropy_diff_float,
            "difference_exactly_zero_float": entropy_diff_float == 0.0,
            "multisets_equal_hence_exact_real_equality": multiset_equal,
        },
        "ott_sinkhorn": {
            "ott_version": ott.__version__,
            "jax_version": jax.__version__,
            "jax_enable_x64": True,
            "ground_cost": (
                "0/1 discrete metric on the 16 law indices (cost_matrix = 1 - I); "
                "under this metric exact OT cost equals total variation distance, "
                "so the transport cost is value-coupled to the exact fraction 137/160"
            ),
            "solver": "ott.solvers.linear.sinkhorn.Sinkhorn(threshold=1e-9, lse_mode=True)",
            "epsilon_sweep": sweep,
            "final_epsilon": final["epsilon"],
            "cross_transport_cost": final["cross_transport_cost"],
            "self_transport_cost": final["self_transport_cost"],
            "tv_target_float": tv_float,
            "abs_error_cross_vs_tv": final["abs_error_cross_vs_tv"],
        },
        "controls_must_be_able_to_fail": {
            "wrong_round_pair": {
                "description": "round-1 profile vs its rot1 (pre-convergence)",
                "tv": frac_str(tv_wrong_round),
                "differs_from_target": tv_wrong_round != TARGET_TV,
            },
            "wrong_pair": {
                "description": "endpoint P vs uniform INITIAL",
                "tv": frac_str(tv_wrong_pair),
                "differs_from_target": tv_wrong_pair != TARGET_TV,
            },
            "perturbed_pair": {
                "description": "Q with one unit of mass moved (index 9 -> index 10)",
                "profile": list(perturbed),
                "tv": frac_str(tv_perturbed),
                "entropy_difference_float": entropy_diff_perturbed,
                "sinkhorn_cost_eps_0_001": cpert,
                "sinkhorn_converged": convpert,
                "abs_error_vs_137_160": abs(cpert - tv_float),
            },
            "nonpermutation_entropy": {
                "description": "|H(P) - H(uniform INITIAL)| must be nonzero",
                "value_nats": entropy_diff_nonperm,
            },
        },
        "julia_cross_engine": {
            "julia_bin": JULIA_BIN,
            "script": str(JULIA_SCRIPT),
            "arithmetic": "Rational{BigInt}, independent re-implementation of update()",
            "report": julia_report,
        },
        "tool_manifest": {
            "ott": {
                "used": True, "depth": "load_bearing",
                "reason": (
                    "Sinkhorn transport cost under the 0/1 metric independently "
                    "recomputes the exact shipped TV 137/160 to <1e-9 and separates "
                    "the pair (0.85625 vs 0.0) that scalar entropy cannot (diff 0.0); "
                    "gate checks fail if it drifts"
                ),
            },
            "jax": {
                "used": True, "depth": "supportive",
                "reason": "x64 substrate for ott; not itself a verdict source",
            },
            "julia": {
                "used": True, "depth": "load_bearing",
                "reason": (
                    "exact Rational{BigInt} re-derivation of the orbit and TV in a "
                    "second engine; python/julia disagreement fails the gate"
                ),
            },
            "python_fractions": {
                "used": True, "depth": "load_bearing",
                "reason": "exact rational TV; equality to 137/160 is exact, not approximate",
            },
        },
        "interpreters": {
            "python": sys.executable,
            "julia": julia_report.get("julia_version", "unavailable"),
        },
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print("GAP F: ott Sinkhorn transport on the REAL shipped profile pair")
    print(f"  rounds hitting TV 137/160: {rounds_hitting_target}; shipped pair = endpoint at round {shipped_pair_round} (fixed point: {endpoint_is_fixed_point})")
    print(f"  P = {list(P)}")
    print(f"  Q = {list(Q)}")
    print(f"  TV exact = {frac_str(sim.total_variation(P, Q))} (shipped: {shipped_tv})")
    print(f"  entropy difference (float) = {entropy_diff_float} (exactly zero: {entropy_diff_float == 0.0})")
    print(f"  sinkhorn cross cost = {final['cross_transport_cost']:.12f} (|err vs 137/160| = {final['abs_error_cross_vs_tv']:.3e})")
    print(f"  sinkhorn self cost  = {final['self_transport_cost']:.3e}")
    print(f"  julia exact TV confirms: {checks['julia_tv_confirms_137_160']}")
    failed = [k for k, v in checks.items() if not v]
    if failed:
        print("  FAILED CHECKS:", failed)
    print(f"  receipt: {OUT_PATH}")
    print("PASS" if all_pass else "FAIL", "gap_f_ott_real_pair_probe")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

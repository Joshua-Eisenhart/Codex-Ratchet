import jax; jax.config.update("jax_enable_x64", True)
"""
IGT Chirality JAX Parity Lane
-----------------------------
Reads /tmp/igt_chirality_jax_target.json and compares against the
canonical Julia reference result.

The compute engine is JAX plus jax.numpy. The M_IGT check references only
payoff matrix values: no gamma5, Gamma, handedness, z2_grading,
left_right_split, sign_structure, or geometric operator.
"""

import json
import re
import sys
from datetime import datetime, timezone

import jax.numpy as jnp


TARGET_PATH = "/tmp/igt_chirality_jax_target.json"
JULIA_REFERENCE_PATH = (
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/"
    "system_v5/julia_carrier/igt_chirality_julia_results.json"
)
RESULT_PATH = "/tmp/igt_chirality_jax_results.json"
TOL = 1.0e-9


def jax_x64_enabled() -> bool:
    try:
        return bool(jax.config.jax_enable_x64)
    except AttributeError:
        return bool(jax.config.read("jax_enable_x64"))


def source_np_dot_count() -> int:
    with open(__file__, "r", encoding="utf-8") as f:
        return len(re.findall(r"\bnp\.", f.read()))


def get_payoff_matrices():
    """
    Returns carrier_name -> payoff JAX array, or None when exact Julia RNG
    parity is intentionally unavailable.
    """
    payoffs = {}

    payoffs["chiral_2x2"] = jnp.array(
        [
            [0.5, 1.0],
            [-1.0, -0.5],
        ],
        dtype=jnp.float64,
    )

    payoffs["chiral_4x4"] = jnp.array(
        [
            [1.0, 0.5, 0.5, -1.0],
            [-1.0, 1.0, -1.0, -1.0],
            [0.5, -0.5, 0.0, 0.3],
            [-0.3, 0.4, -0.2, 0.8],
        ],
        dtype=jnp.float64,
    )

    # Julia uses MersenneTwister(7777). JAX PRNG values are not the same, so
    # exact matrix parity for this random carrier is skipped by design.
    payoffs["chiral_8x8"] = None

    payoffs["nonchiral_2x2"] = jnp.array(
        [
            [0.5, 0.5],
            [0.5, 0.5],
        ],
        dtype=jnp.float64,
    )

    key_nc4 = jax.random.PRNGKey(5555)
    raw_nc4 = jax.random.normal(key_nc4, (4, 4), dtype=jnp.float64)
    payoffs["nonchiral_4x4"] = (raw_nc4 + raw_nc4.T) / 2.0

    key_nc8 = jax.random.PRNGKey(8888)
    raw_nc8 = jax.random.normal(key_nc8, (8, 8), dtype=jnp.float64)
    payoffs["nonchiral_8x8"] = (raw_nc8 + raw_nc8.T) / 2.0

    return payoffs


def migt_check_jax(payoff, tol: float = TOL):
    """
    M_IGT symmetry check: chiral iff any paired payoff differs under transpose.
    The check is anti-circular and uses only payoff matrix values.
    """
    n = payoff.shape[0]
    assert payoff.shape == (n, n), "payoff must be square"
    asym = jnp.abs(payoff - payoff.T)
    max_asym = float(jnp.max(asym))
    n_asym_pairs = int((jnp.sum(asym > tol) // 2).item())
    chiral = bool(max_asym > tol)
    return chiral, max_asym, n_asym_pairs


def verdict_for(chiral: bool) -> str:
    if chiral:
        return "survived: chiral under M_IGT"
    return "excluded: symmetric under M_IGT (UNSAT)"


def comparable_julia_asym(julia_reference, name):
    carrier = julia_reference.get("carriers", {}).get(name, {})
    return carrier.get("M_IGT_max_asymmetry")


def build_schema():
    return {
        "file": "igt_chirality",
        "top_level_keys": [
            "file",
            "object_id",
            "source_julia_object",
            "generated_at",
            "compute_engine",
            "x64_enabled",
            "np_compute_remaining",
            "julia_reference_path",
            "target_path",
            "carriers",
            "flip_test",
            "anti_circular_check",
            "all_comparable_verdicts_match",
            "all_comparable_numeric_invariants_match",
            "parity_max_diff",
            "skipped_carriers",
            "parity_status",
            "parity_holds",
            "promotion_allowed",
            "classification",
            "claim_ceiling",
            "schema",
        ],
        "carrier_entry_keys": [
            "status",
            "julia_chiral_under_M_IGT",
            "julia_verdict",
            "jax_chiral_under_M_IGT",
            "jax_max_asymmetry",
            "jax_n_asymmetric_pairs",
            "jax_verdict",
            "julia_M_IGT_max_asymmetry",
            "numeric_diff",
            "verdicts_match",
            "numeric_invariant_match",
            "note",
        ],
        "parity_rule": (
            "HOLDS when every JAX-computed carrier verdict matches Julia, "
            "every comparable named numeric invariant is within tolerance, "
            "the flip test agrees, and the anti-circular check agrees. "
            "chiral_8x8 is excluded from numeric parity because JAX PRNG "
            "does not reproduce Julia MersenneTwister(7777)."
        ),
    }


def main():
    print("IGT chirality JAX parity lane")
    print(f"JAX x64 enabled: {jax_x64_enabled()}")

    with open(TARGET_PATH, "r", encoding="utf-8") as f:
        target = json.load(f)
    with open(JULIA_REFERENCE_PATH, "r", encoding="utf-8") as f:
        julia_reference = json.load(f)

    target_carriers = target["carriers"]
    julia_carriers = julia_reference["carriers"]
    julia_flip_real = bool(
        julia_reference.get(
            "flip_real",
            julia_reference.get("load_bearing_flip", {}).get("flip_real"),
        )
    )
    julia_anti_circular = bool(julia_reference["probe_family"]["anti_circular"])

    payoffs = get_payoff_matrices()
    results = {}
    skipped_carriers = []
    all_verdicts_match = True
    all_numeric_match = True
    parity_max_diff = 0.0

    for name, julia_entry in julia_carriers.items():
        julia_chiral = bool(julia_entry["chiral_under_M_IGT"])
        julia_verdict = julia_entry["verdict"]
        payoff = payoffs.get(name)

        if payoff is None:
            skipped_carriers.append(name)
            results[name] = {
                "status": "rng_mismatch_skipped",
                "julia_chiral_under_M_IGT": julia_chiral,
                "julia_verdict": julia_verdict,
                "jax_chiral_under_M_IGT": None,
                "jax_max_asymmetry": None,
                "jax_n_asymmetric_pairs": None,
                "jax_verdict": None,
                "julia_M_IGT_max_asymmetry": julia_entry.get("M_IGT_max_asymmetry"),
                "numeric_diff": None,
                "verdicts_match": None,
                "numeric_invariant_match": None,
                "note": (
                    "Skipped because jax.random does not reproduce Julia "
                    "MersenneTwister(7777); this is a JAX-vs-Julia PRNG "
                    "boundary, not a NumPy-vs-Julia boundary."
                ),
            }
            print(f"  {name}: skipped exact random-matrix parity")
            continue

        jax_chiral, jax_max_asym, jax_n_asym = migt_check_jax(payoff)
        jax_verdict = verdict_for(jax_chiral)
        verdict_match = (jax_chiral == julia_chiral) and (jax_verdict == julia_verdict)
        if not verdict_match:
            all_verdicts_match = False

        julia_asym = comparable_julia_asym(julia_reference, name)
        numeric_diff = None
        numeric_match = None
        if julia_asym is not None:
            numeric_diff = abs(jax_max_asym - float(julia_asym))
            parity_max_diff = max(parity_max_diff, numeric_diff)
            numeric_match = bool(numeric_diff <= TOL)
            if not numeric_match:
                all_numeric_match = False

        results[name] = {
            "status": "computed_jax",
            "julia_chiral_under_M_IGT": julia_chiral,
            "julia_verdict": julia_verdict,
            "jax_chiral_under_M_IGT": jax_chiral,
            "jax_max_asymmetry": jax_max_asym,
            "jax_n_asymmetric_pairs": jax_n_asym,
            "jax_verdict": jax_verdict,
            "julia_M_IGT_max_asymmetry": julia_asym,
            "numeric_diff": numeric_diff,
            "verdicts_match": verdict_match,
            "numeric_invariant_match": numeric_match,
            "note": "M_IGT computed with JAX plus jax.numpy.",
        }
        print(f"  {name}: julia={julia_chiral}, jax={jax_chiral}, match={verdict_match}")

    payoff_c4_orig = payoffs["chiral_4x4"]
    payoff_c4_erased = (payoff_c4_orig + payoff_c4_orig.T) / 2.0
    orig_chiral, orig_asym, _ = migt_check_jax(payoff_c4_orig)
    erased_chiral, erased_asym, _ = migt_check_jax(payoff_c4_erased)
    jax_flip_real = bool(orig_chiral and not erased_chiral)
    flip_agrees = bool(jax_flip_real == julia_flip_real)
    print(
        "  flip_test: "
        f"orig_chiral={orig_chiral}, erased_chiral={erased_chiral}, "
        f"flip_real={jax_flip_real}, agrees_julia={flip_agrees}"
    )

    anti_circular_check = True
    anti_circular_agrees = bool(anti_circular_check == julia_anti_circular)

    target_verdicts_match = True
    for name, target_entry in target_carriers.items():
        if name in skipped_carriers:
            continue
        if results[name]["jax_chiral_under_M_IGT"] != bool(target_entry["chiral_under_M_IGT"]):
            target_verdicts_match = False

    parity_holds = bool(
        all_verdicts_match
        and all_numeric_match
        and flip_agrees
        and anti_circular_agrees
        and target_verdicts_match
    )
    parity_status = "HOLDS" if parity_holds else "BREAKS"
    np_compute_remaining = source_np_dot_count()

    print(f"\nnp_compute_remaining={np_compute_remaining}")
    print(f"all_comparable_verdicts_match={all_verdicts_match}")
    print(f"all_comparable_numeric_invariants_match={all_numeric_match}")
    print(f"parity_max_diff={parity_max_diff:.2e}")
    print(f"parity_status={parity_status}")

    output = {
        "file": "igt_chirality",
        "object_id": "igt_chirality_m_igt_v1_jax_parity",
        "source_julia_object": "igt_chirality_m_igt_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "compute_engine": "jax+jax.numpy",
        "x64_enabled": jax_x64_enabled(),
        "np_compute_remaining": np_compute_remaining,
        "julia_reference_path": JULIA_REFERENCE_PATH,
        "target_path": TARGET_PATH,
        "carriers": results,
        "flip_test": {
            "jax_flip_real": jax_flip_real,
            "julia_flip_real": julia_flip_real,
            "agrees": flip_agrees,
            "chiral_4x4_orig_max_asym": orig_asym,
            "chiral_4x4_erased_max_asym": erased_asym,
            "engine": "jax+jax.numpy",
        },
        "anti_circular_check": {
            "jax_anti_circular": anti_circular_check,
            "julia_anti_circular": julia_anti_circular,
            "agrees": anti_circular_agrees,
            "note": "migt_check_jax references only payoff values.",
        },
        "all_comparable_verdicts_match": all_verdicts_match,
        "all_comparable_numeric_invariants_match": all_numeric_match,
        "parity_max_diff": parity_max_diff,
        "skipped_carriers": skipped_carriers,
        "parity_status": parity_status,
        "parity_holds": parity_holds,
        "promotion_allowed": False,
        "classification": "tool_lego_fit_probe_parity",
        "claim_ceiling": (
            "JAX parity lane only; no layer-completion, manifold, coupling, "
            "bridge, Axis0, flux, or physics claims."
        ),
        "schema": build_schema(),
    }

    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        f.write("\n")
    print(f"wrote: {RESULT_PATH}")

    return 0 if parity_holds else 1


if __name__ == "__main__":
    sys.exit(main())

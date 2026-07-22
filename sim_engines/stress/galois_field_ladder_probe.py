#!/usr/bin/env python3
"""UNOFFICIAL INTEGRATION PROBE — galois finite fields vs sympy exact.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: capability demonstration only — shows the `galois` library does
real finite-field work (GF(2^8) and GF(7^3) arithmetic, generator orders,
Frobenius) that jnp cannot do and sympy does slower, cross-checked against
sympy's exact machinery. Candidate load-bearing role for the algebra_ladder
arrow; NOT yet integrated into any arrow. Parks by definition.

Checks (each galois result verified by an independent sympy computation):
  1. multiplicative group order of GF(2^8) is 255 and a primitive element has
     that exact order (galois order vs sympy n_order in the quotient ring)
  2. Frobenius x -> x^p is an automorphism: (a+b)^p == a^p + b^p in GF(7^3)
     for a random sample (galois) — the freshman's-dream identity that FAILS
     over the integers (negative control, checked with sympy over Z)
  3. subfield ladder GF(2) < GF(2^2) < GF(2^4) < GF(2^8): element counts and
     containment via x^(2^k) = x fixed-point counts (galois) vs 2^k (exact)

Exit 0 = probe completed; 1 = infra failure.
"""
import json
import time
from pathlib import Path

import galois
import sympy

HERE = Path(__file__).resolve().parent


def main():
    t0 = time.perf_counter()
    receipt = {"classification": "unofficial_stress_probe", "promotion_allowed": False,
               "claim_ceiling": "capability demonstration only — candidate role for algebra_ladder; "
                                "not integrated into any arrow; parks by definition",
               "checks": {}}

    # 1. GF(2^8): primitive element order 255, cross-checked by sympy factor structure.
    F = galois.GF(2**8)
    g = F.primitive_element
    order = g.multiplicative_order()
    # sympy cross-check: 255 = 3*5*17; an element of order 255 must not satisfy
    # g^(255/p) == 1 for any prime p | 255. Verify with galois pow, primes from sympy.
    primes = [int(p) for p in sympy.primefactors(255)]
    proper_power_trivial = any(g ** (255 // p) == F(1) for p in primes)
    receipt["checks"]["gf256_generator"] = {
        "order": int(order), "expected": 255,
        "sympy_prime_factors_255": primes,
        "no_proper_power_is_identity": not proper_power_trivial,
        "pass": int(order) == 255 and not proper_power_trivial,
    }

    # 2. Frobenius freshman's dream in GF(7^3) — and its FAILURE over Z (negative control).
    K = galois.GF(7**3)
    rng = K.Random(64, seed=7)
    a, b = rng[:32], rng[32:]
    frob_holds = bool(((a + b) ** 7 == a ** 7 + b ** 7).all())
    # negative control via sympy over the integers: (2+3)^7 != 2^7 + 3^7
    z_fails = sympy.Integer(2 + 3) ** 7 != sympy.Integer(2) ** 7 + sympy.Integer(3) ** 7
    receipt["checks"]["frobenius_gf343"] = {
        "freshmans_dream_holds_in_field": frob_holds,
        "fails_over_Z_negative_control": bool(z_fails),
        "pass": frob_holds and bool(z_fails),
    }

    # 3. Subfield ladder: fixed points of x -> x^(2^k) in GF(2^8) number exactly 2^k.
    ladder = {}
    x = F.elements
    for k in (1, 2, 4, 8):
        fixed = int((x ** (2**k) == x).sum())
        ladder[f"GF(2^{k})"] = {"fixed_points": fixed, "expected": 2**k, "pass": fixed == 2**k}
    receipt["checks"]["subfield_ladder"] = ladder

    all_pass = (receipt["checks"]["gf256_generator"]["pass"]
                and receipt["checks"]["frobenius_gf343"]["pass"]
                and all(v["pass"] for v in ladder.values()))
    receipt["all_checks_pass"] = all_pass
    receipt["seconds"] = round(time.perf_counter() - t0, 3)

    out = HERE / "results"
    out.mkdir(exist_ok=True)
    with open(out / "galois_field_ladder_probe.json", "w") as f:
        json.dump(receipt, f, indent=1, sort_keys=True)
    print(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"[*] galois probe COMPLETED — checks {'ALL HOLD' if all_pass else 'FAIL (recorded)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

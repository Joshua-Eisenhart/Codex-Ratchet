"""phase_98_prime_resonance_via_totient.py — engine-derived prime probe.

This phase used to invite Euler-totient / gcd / factorization leakage. It now
does the opposite: before scoring a candidate's `prime_resonance(n)`, it scans
the candidate source and rejects direct factor, totient, gcd, divisor, coprime,
modulo, or classical primality APIs in the resonance path.

Allowed: use n as a smooth or schedule parameter inside engine/manifold dynamics
and then report a signature vector.
Forbidden: compute arithmetic structure of n and smuggle that into the
signature vector. Classical prime labels, lookup tables, and helper functions
inside the candidate are also forbidden; labels belong in the hidden harness,
not in the generated probe.

The statistical gate remains the same: primes must cluster against a random-label
null with z >= 2 sigma. If the engine-derived signal does not separate primes,
this phase must fail honestly.
"""
import ast
import math
import numpy as np
from pathlib import Path


def _is_prime(n):
    if n < 2:
        return False
    for d in range(2, int(math.isqrt(n)) + 1):
        if n % d == 0:
            return False
    return True


FORBIDDEN_CALLS = {
    "factorint", "factorize", "primefactors", "divisors", "totient",
    "gcd", "isprime", "is_prime", "divisor_count", "euler_phi",
}


def _attr_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def _scan_prime_source_path(path):
    if not path.exists():
        return [{"check": "prime_source_guard", "msg": f"source path unavailable: {path}"}]
    try:
        tree = ast.parse(path.read_text())
    except Exception as e:
        return [{"check": "prime_source_guard_parse", "msg": str(e)[:200]}]

    failures = []
    function_names = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name in sorted(function_names):
        low = name.lower()
        if any(tok in low for tok in ("factor", "totient", "divisor", "coprime")):
            failures.append({
                "check": "prime_source_forbidden_function",
                "msg": f"{path.name} defines `{name}`; Phase 98 forbids factor/totient/divisor helper paths",
            })
        if "prime" in low and low != "prime_resonance":
            failures.append({
                "check": "prime_source_forbidden_label_helper",
                "msg": f"{path.name} defines `{name}`; Phase 98 forbids candidate-side prime label helpers",
            })

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            low = node.id.lower()
            if "prime" in low and low != "prime_resonance":
                failures.append({
                    "check": "prime_source_forbidden_label_name",
                    "msg": f"{path.name} references `{node.id}` at line {node.lineno}; Phase 98 forbids candidate-side prime labels/lookups",
                })
        if isinstance(node, ast.Call):
            name = _attr_name(node.func)
            tail = name.split(".")[-1].lower() if name else ""
            if tail in FORBIDDEN_CALLS:
                failures.append({
                    "check": "prime_source_forbidden_call",
                    "msg": f"{path.name} calls `{name}` at line {node.lineno}; prime signal must be engine-derived",
                })
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            failures.append({
                "check": "prime_source_modulo",
                "msg": f"{path.name} uses modulo at line {node.lineno}; Phase 98 forbids all modular arithmetic in prime probe candidates",
            })
    return failures


def _prime_source_leak_failures(candidate):
    paths = set()
    candidate_path = Path(getattr(candidate, "__file__", ""))
    if candidate_path.exists():
        paths.add(candidate_path)

    fn = getattr(candidate, "prime_resonance", None)
    code = getattr(fn, "__code__", None)
    if code and getattr(code, "co_filename", None):
        fn_path = Path(code.co_filename)
        if fn_path.exists():
            paths.add(fn_path)

    if not paths:
        return [{"check": "prime_source_guard", "msg": "candidate source path unavailable"}]

    failures = []
    for path in sorted(paths):
        failures.extend(_scan_prime_source_path(path))
    return failures


def run(candidate):
    failures = []
    metrics = {}

    if not hasattr(candidate, "prime_resonance"):
        return {
            "pass": False,
            "failures": [{
                "check": "prime_resonance_exists",
                "msg": "Required function `prime_resonance(n: int) -> dict` not exported. RESEARCH "
                       "PROBE: do primes cluster tighter than composites in signature space? "
                       "Use only public engine/manifold dynamics. Do not use prime labels, "
                       "factorization, totient, gcd, divisors, or modulo arithmetic in the candidate.",
            }],
            "metrics": metrics,
        }

    source_failures = _prime_source_leak_failures(candidate)
    if source_failures:
        return {
            "pass": False,
            "failures": source_failures[:10],
            "metrics": {"source_guard_failures": len(source_failures)},
            "graveyard_companions": [
                "factor/totient/gcd signature path — rejected before statistical scoring",
                "modular hash signature — rejected before statistical scoring",
                "candidate-side prime lookup/label helper — rejected before statistical scoring",
            ],
            "baseline_variants": [
                "engine-derived signature with no arithmetic leakage — proceeds to z-score gate",
            ],
        }

    test_range = list(range(2, 17))
    signatures = {}
    for n in test_range:
        try:
            r = candidate.prime_resonance(n)
            sig = np.asarray(r["signature_vector"], dtype=float)
            signatures[n] = sig
        except Exception as e:
            failures.append({"check": f"call_n_{n}", "msg": str(e)[:200]})

    if len(signatures) < 12:
        return {"pass": False, "failures": failures, "metrics": metrics}

    # Distinct signatures: avoid mod-period hashes
    distinct_n = len({tuple(round(float(x), 4) for x in signatures[n]) for n in signatures})
    metrics["distinct_signatures"] = distinct_n
    metrics["total_signatures"] = len(signatures)
    if distinct_n < len(signatures) * 0.7:
        failures.append({
            "check": "signatures_distinct",
            "msg": f"Only {distinct_n} of {len(signatures)} integers have distinct signatures. "
                   f"Need ≥70%. Looks like a mod-period hash.",
        })

    # Pairwise L2 distances
    primes_in_range = [n for n in signatures if _is_prime(n)]
    composites_in_range = [n for n in signatures if not _is_prime(n) and n > 1]
    metrics["primes_in_range"] = primes_in_range
    metrics["composites_in_range"] = composites_in_range

    pp_dists = []
    for i, p1 in enumerate(primes_in_range):
        for p2 in primes_in_range[i + 1:]:
            pp_dists.append(float(np.linalg.norm(signatures[p1] - signatures[p2])))

    pc_dists = []
    for p in primes_in_range:
        for c in composites_in_range:
            pc_dists.append(float(np.linalg.norm(signatures[p] - signatures[c])))

    if not pp_dists or not pc_dists:
        return {"pass": False, "failures": failures + [
            {"check": "insufficient_pairs", "msg": f"PP pairs: {len(pp_dists)}, PC pairs: {len(pc_dists)}"}
        ], "metrics": metrics}

    avg_pp = sum(pp_dists) / len(pp_dists)
    avg_pc = sum(pc_dists) / len(pc_dists)
    ratio = avg_pc / max(avg_pp, 1e-9)
    metrics["avg_prime_prime_distance"] = avg_pp
    metrics["avg_prime_composite_distance"] = avg_pc
    metrics["cluster_advantage_ratio"] = ratio

    # Statistical significance: compare observed ratio against random-label null distribution
    import random
    rng = random.Random(42)
    all_ns = primes_in_range + composites_in_range
    null_ratios = []
    for _ in range(100):
        shuffled = list(all_ns)
        rng.shuffle(shuffled)
        fake_primes = shuffled[:len(primes_in_range)]
        fake_comps = shuffled[len(primes_in_range):]
        pp_f = [float(np.linalg.norm(signatures[a] - signatures[b]))
                for i, a in enumerate(fake_primes) for b in fake_primes[i + 1:]]
        pc_f = [float(np.linalg.norm(signatures[a] - signatures[b]))
                for a in fake_primes for b in fake_comps]
        if pp_f and pc_f:
            avg_pp_f = sum(pp_f) / len(pp_f)
            avg_pc_f = sum(pc_f) / len(pc_f)
            null_ratios.append(avg_pc_f / max(avg_pp_f, 1e-9))
    null_mean = sum(null_ratios) / len(null_ratios)
    null_std = (sum((x - null_mean) ** 2 for x in null_ratios) / len(null_ratios)) ** 0.5
    z_score = (ratio - null_mean) / max(null_std, 1e-9)
    metrics["null_mean"] = null_mean
    metrics["null_std"] = null_std
    metrics["z_score_vs_random"] = z_score

    # Threshold: require z > 2σ (real signal vs noise)
    if z_score < 2.0:
        failures.append({
            "check": "primes_cluster_significant",
            "msg": f"Prime cluster ratio = {ratio:.4f}; random-label null gives {null_mean:.4f} "
                   f"± {null_std:.4f}. Observed z-score = {z_score:.2f}σ (need ≥ 2σ for "
                   f"statistical significance). The 4-5% margin observed is consistent with "
                   f"random-label variance, NOT real prime physics in the engine signature.",
        })

    # Determinism
    try:
        s1 = np.asarray(candidate.prime_resonance(5)["signature_vector"], dtype=float)
        s2 = np.asarray(candidate.prime_resonance(5)["signature_vector"], dtype=float)
        if float(np.max(np.abs(s1 - s2))) > 1e-6:
            failures.append({"check": "deterministic", "msg": "n=5 not deterministic"})
    except Exception:
        pass

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "factor/totient/gcd leakage — rejected by source guard",
            "mod-k hash with k=4 — rejected by source guard or fails distinct_signatures",
            "constant signature — pp ≈ pc, fails 5% margin",
            "random signature — ratio ≈ 1 ± noise, statistically fails 5% margin",
            "true QFT period-finding signature — ratio > 1.5, passes",
        ],
        "baseline_variants": [
            "linear-in-n signature (sig[n] = [n, 0, 0, 0]) — primes spread along axis, no tighter cluster",
        ],
    }

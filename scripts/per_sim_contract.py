#!/usr/bin/env python3
"""
per_sim_contract.py -- enforce the owner's PER-SIM REQUIRED EMISSION PATTERN
(2026-05-29 reframe): tools are the runtime/proof STACK, the sim is a finite
object/map. Every individual sim result JSON must emit the pattern below.

REQUIRED (hard):
  object_id              : names the finite object/map being tested
  finite_map             : domain -> codomain_or_output (both present)
  root_constraints       : F01 (finite distinguishability) + N01 (noncommutation/order) referenced/tested
  backend_primary_result : claim-bearing JAX or Julia-family primary result present
  controls               : >=1 control / negative
  tool_ablations         : >=1 ablation with a numeric outcome_delta != 0
  scale_or_blocker       : an 8/16/32/64 scale ladder OR an explicit resource_blocker string
  blocked_consumers      : names what this sim does NOT yet earn (Xi/Phi0/Axis0/flux/FEP/gravity)

CONDITIONAL (reported, not failed unless --strict): backend crosscheck / mirror delta
  (where representable); PyTorch mirror only as explicit comparison/support;
  MPS / PEPS2D / PEPS3D result (where applicable);
  proof_results z3/cvc5/sympy; geometry/topology results; entropy_as_output.

usage: per_sim_contract.py <result.json> [--strict]
exit 0 if required (and, with --strict, conditional) gates pass; 1 otherwise.
"""
import json
import sys


PRIMARY_BACKEND_TOKENS = (
    "jax",
    "julia",
    "pepskit",
    "tensorkit",
    "itensors",
    "quantumclifford",
)


def _walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk_keys(v)


def _find(d, *subs):
    out = []

    def rec(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if any(s in k.lower() for s in subs):
                    out.append((path + k, v))
                rec(v, path + k + ".")
        elif isinstance(o, list):
            for i, it in enumerate(o):
                rec(it, f"{path}[{i}].")
    rec(d)
    return out


def _nonempty(v):
    if v in (None, "", [], {}, 0):
        return False
    if isinstance(v, str):
        text = v.strip().lower()
        return bool(text) and text not in {"stub", "placeholder", "decorative", "missing", "none", "n/a", "not_applicable"}
    if isinstance(v, dict):
        return any(_nonempty(item) for item in v.values())
    if isinstance(v, (list, tuple, set)):
        return any(_nonempty(item) for item in v)
    return True


def _has_nonzero_ablation(d):
    for _, v in _find(d, "ablation"):
        if isinstance(v, dict):
            for ak, av in v.items():
                cand = av
                if isinstance(av, dict):
                    cand = av.get("delta", av.get("outcome_delta", 0))
                try:
                    if abs(float(cand)) > 1e-12:
                        return True
                except (TypeError, ValueError):
                    pass
    return False


def _has_scale_or_blocker(d):
    for _, v in _find(d, "scale_ladder", "scale_rungs"):
        if isinstance(v, dict):
            rungs = v.get("rungs", v)
            if isinstance(rungs, dict) and rungs:
                return True, "scale ladder present"
    for _, v in _find(d, "resource_blocker", "scale_blocker"):
        if isinstance(v, str) and v.strip():
            return True, f"resource_blocker: {v[:50]!r}"
    return False, "no scale ladder AND no resource_blocker string"


def _has_primary_backend_result(d):
    explicit = _find(d, "backend_primary_result", "primary_backend_result", "claim_bearing_primary_result")
    if any(_nonempty(v) for _, v in explicit):
        return True, "explicit backend_primary_result"

    backend_fields = _find(d, "primary_backend", "claim_backend", "backend", "engine")
    backend_text = " ".join(str(v).lower() for _, v in backend_fields if _nonempty(v))
    primary_named = any(token in backend_text for token in PRIMARY_BACKEND_TOKENS)

    backend_result = _find(
        d,
        "jax_primary",
        "jax_result",
        "jax_engine",
        "julia_primary",
        "julia_result",
        "julia_engine",
        "pepskit_result",
        "pepskit_ctmrg",
        "tensorkit_result",
        "ctmrg_result",
        "peps2d_result",
    )
    if any(_nonempty(v) for _, v in backend_result):
        return True, "JAX/Julia-family result present"

    if primary_named and any(_nonempty(v) for _, v in _find(d, "result_summary", "summary", "all_pass")):
        return True, "primary backend named with result summary"

    legacy_torch = _find(d, "torch_primary", "torch_result", "pytorch_result", "torch_value")
    if any(_nonempty(v) for _, v in legacy_torch):
        return False, "legacy torch result present but no JAX/Julia primary"
    return False, "missing backend_primary_result / JAX or Julia-family primary"


def check(d, strict=False):
    rows = []

    def add(name, ok, why):
        rows.append((name, bool(ok), why))

    # object_id
    oid = _find(d, "object_id", "object_name")
    add("object_id", any(_nonempty(v) for _, v in oid), oid[0][1] if oid else "missing")

    # finite_map: domain + codomain
    fm = _find(d, "finite_map")
    dom = _find(d, "domain")
    cod = _find(d, "codomain", "output_space", "codomain_or_output")
    fm_ok = bool(fm) or (bool(dom) and bool(cod))
    add("finite_map (domain->codomain)", fm_ok, "finite_map block" if fm else f"domain={bool(dom)} codomain={bool(cod)}")

    # root constraints F01 + N01
    keys = " ".join(_walk_keys(d)).lower()
    s = json.dumps(d).lower()
    f01 = ("f01" in s) or ("distinguish" in keys) or ("finite_distinguish" in s)
    n01 = ("n01" in s) or ("noncommut" in keys) or ("commutator" in s) or ("order_sensitive" in s) or ("order_gap" in s)
    add("root_constraints F01+N01", f01 and n01, f"F01={f01} N01={n01}")

    # claim-bearing primary backend
    primary_ok, primary_why = _has_primary_backend_result(d)
    add("backend_primary_result", primary_ok, primary_why)

    # controls
    ctl = _find(d, "control", "negative")
    add("controls/negatives", any(_nonempty(v) for _, v in ctl), f"{len(ctl)} found" if ctl else "missing")

    # ablations
    add("tool_ablations (nonzero delta)", _has_nonzero_ablation(d), "nonzero ablation delta" if _has_nonzero_ablation(d) else "none / all zero")

    # scale or blocker
    sok, swhy = _has_scale_or_blocker(d)
    add("scale_8_16_32_64_or_blocker", sok, swhy)

    # blocked consumers
    bc = _find(d, "blocked_consumer")
    add("blocked_consumers", any(_nonempty(v) for _, v in bc), "present" if bc else "missing (must name Xi/Phi0/Axis0/flux/FEP/gravity not-yet-earned)")

    required_ok = all(ok for _, ok, _ in rows)

    # conditional (reported)
    cond = []
    bm = _find(d, "backend_mirror", "jax_mirror", "julia_mirror", "torch_mirror", "pytorch_mirror")
    bd = _find(d, "backend_delta", "jax_vs_julia", "jax_vs_pytorch", "jax_torch_value_delta", "jax_pytorch_delta", "max_value_delta")
    cond.append(("backend_mirror+delta", bool(bm) and bool(bd)))
    cond.append(("MPS", bool(_find(d, "mps_"))))
    cond.append(("PEPS2D", bool(_find(d, "peps2d"))))
    cond.append(("PEPS3D/spinor-network", bool(_find(d, "peps3d", "spinor_network"))))
    cond.append(("proofs z3/cvc5/sympy", bool(_find(d, "z3", "cvc5", "sympy", "proof_result"))))
    cond.append(("geometry/topology", bool(_find(d, "geometr", "topolog", "clifford", "homolog"))))
    cond.append(("entropy_as_output", bool(_find(d, "entropy", "mutual_info", "negativity"))))

    cond_ok = all(ok for _, ok in cond)
    return rows, cond, required_ok, (required_ok and (cond_ok or not strict))


def main():
    if len(sys.argv) < 2:
        print("usage: per_sim_contract.py <result.json> [--strict]")
        return 2
    strict = "--strict" in sys.argv
    d = json.load(open(sys.argv[1]))
    rows, cond, req_ok, overall = check(d, strict)
    print(f"PER-SIM CONTRACT: {sys.argv[1].split('/')[-1]}")
    print("  REQUIRED:")
    for name, ok, why in rows:
        print(f"    [{'PASS' if ok else 'FAIL'}] {name:<34} {why[:64]}")
    print("  CONDITIONAL (report):")
    for name, ok in cond:
        print(f"    [{'yes ' if ok else 'no  '}] {name}")
    print(f"  required_pass={req_ok}  overall_pass={overall}  (strict={strict})")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())

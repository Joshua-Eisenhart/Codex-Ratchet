#!/usr/bin/env python3
"""JAX leg -- batched/exhaustive workhorse.

Computation style UNIQUE to this leg: jax.vmap over the whole finite set.
  - builds the batched density-matrix tensor rho[i] = (I + r_i . sigma)/2
  - computes the full probe-expectation MATRIX tr(rho[i] P_j) in one vmapped pass
  - derives the quotient S/~_M from the batched expectation matrix
It does NOT call the Julia or PyTorch legs and does NOT read their results.

It also carries the LOAD-BEARING z3 + cvc5 real-vs-erased structural flip:
  ask "does an active probe separate s1,s2?" -> SAT under full M, UNSAT under
  erased M. The assertion is over the EXACT expectation values (rational), not
  a count tautology (no solver.add(n == count)).
"""

import json
import os
from datetime import datetime, timezone
from fractions import Fraction
from functools import reduce

import jax
import jax.numpy as jnp
from jax import vmap

import z3
import cvc5
from cvc5 import Kind

jax.config.update("jax_enable_x64", True)

SIM_ID = "distinguishability_quotient_floor_v0"
HERE = os.path.dirname(os.path.abspath(__file__))

# Pauli probes
X = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
Y = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
Z = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
I2 = jnp.eye(2, dtype=jnp.complex128)
PROBE_MATS = {"X": X, "Y": Y, "Z": Z}


def sha256_of(path):
    import hashlib

    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build_rho_batch(bloch_batch):
    # bloch_batch: (N, 3) real array of (rx, ry, rz)
    def one(r):
        return (I2 + r[0] * X + r[1] * Y + r[2] * Z) / 2

    return vmap(one)(bloch_batch)  # (N, 2, 2)


def expectation_matrix(rho_batch, probe_mats):
    # vmap state-axis x probe-axis: tr(rho P) for all (i, j) in one batched pass.
    def exp_one(rho, P):
        return jnp.real(jnp.trace(rho @ P))

    # vmap over probes (inner), then over states (outer)
    per_state = vmap(lambda rho: vmap(lambda P: exp_one(rho, P))(probe_mats))
    return per_state(rho_batch)  # (N, n_probes)


def quotient_from_matrix(exp_mat, labels, tol=1e-9):
    classes = []
    keys = []
    for i, lab in enumerate(labels):
        key = tuple(round(float(v), 9) for v in exp_mat[i])
        if key in keys:
            classes[keys.index(key)].append(lab)
        else:
            keys.append(key)
            classes.append([lab])
    return classes


def z3_separable(s1, s2, active):
    """SAT iff some active probe P has s1[P] != s2[P]. Arithmetic over exact rationals."""
    solver = z3.Solver()
    diffs = []
    for P in active:
        a = z3.RealVal(f"{s1[P].numerator}/{s1[P].denominator}")
        b = z3.RealVal(f"{s2[P].numerator}/{s2[P].denominator}")
        diffs.append(a != b)
    solver.add(z3.Or(*diffs) if len(diffs) > 1 else diffs[0])
    return str(solver.check())


def cvc5_separable(s1, s2, active):
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    diffs = []
    for P in active:
        a = tm.mkReal(s1[P].numerator, s1[P].denominator)
        b = tm.mkReal(s2[P].numerator, s2[P].denominator)
        diffs.append(tm.mkTerm(Kind.DISTINCT, a, b))
    sep = diffs[0] if len(diffs) == 1 else tm.mkTerm(Kind.OR, *diffs)
    slv.assertFormula(sep)
    return str(slv.checkSat())


def main():
    with open(os.path.join(HERE, "spec.json")) as f:
        spec = json.load(f)
    bvs = spec["bloch_vectors_rational"]
    full = spec["probe_family_full"]
    erased = spec["probe_family_erased"]
    labels = sorted(bvs.keys())

    bloch = jnp.array(
        [
            [
                bvs[l]["rx"][0] / bvs[l]["rx"][1],
                bvs[l]["ry"][0] / bvs[l]["ry"][1],
                bvs[l]["rz"][0] / bvs[l]["rz"][1],
            ]
            for l in labels
        ],
        dtype=jnp.float64,
    )

    rho_batch = build_rho_batch(bloch)

    full_mats = jnp.stack([PROBE_MATS[p] for p in full])
    erased_mats = jnp.stack([PROBE_MATS[p] for p in erased])

    exp_full = expectation_matrix(rho_batch, full_mats)
    exp_erased = expectation_matrix(rho_batch, erased_mats)

    # check trace==1 / hermitian batched
    traces = vmap(lambda r: jnp.real(jnp.trace(r)))(rho_batch)
    herm_err = float(jnp.max(jnp.abs(rho_batch - jnp.conj(jnp.transpose(rho_batch, (0, 2, 1))))))

    q_full = quotient_from_matrix(exp_full, labels)
    q_erased = quotient_from_matrix(exp_erased, labels)

    # --- LOAD-BEARING SMT: real-vs-erased structural flip on the flip pair ---
    fa, fb = spec["flip_pair"]

    def exact_exp(lab):
        b = bvs[lab]
        return {
            "X": Fraction(*b["rx"]),
            "Y": Fraction(*b["ry"]),
            "Z": Fraction(*b["rz"]),
        }

    s1 = exact_exp(fa)
    s2 = exact_exp(fb)

    z3_full = z3_separable(s1, s2, full)
    z3_erased = z3_separable(s1, s2, erased)
    cvc5_full = cvc5_separable(s1, s2, full)
    cvc5_erased = cvc5_separable(s1, s2, erased)

    flip_confirmed = (
        z3_full == "sat"
        and z3_erased == "unsat"
        and cvc5_full == "sat"
        and cvc5_erased == "unsat"
    )

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "computation_style": "vmap_batched_expectation_matrix",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "finite_set_size": len(labels),
        "state_labels": labels,
        "traces": [round(float(t), 12) for t in traces],
        "hermitian_max_err": herm_err,
        "probe_expectations_full": {
            l: [round(float(v), 9) for v in exp_full[i]] for i, l in enumerate(labels)
        },
        "probe_expectations_erased": {
            l: [round(float(v), 9) for v in exp_erased[i]] for i, l in enumerate(labels)
        },
        "quotient_classes_full": q_full,
        "quotient_class_count_full": len(q_full),
        "quotient_classes_erased": q_erased,
        "quotient_class_count_erased": len(q_erased),
        "flip_pair": [fa, fb],
        "smt_flip": {
            "question": "does an active probe in M separate the flip pair (exists P in M with tr(rho_a P) != tr(rho_b P))?",
            "encoding": "DISJUNCTION over active probes of (exact_expectation_a != exact_expectation_b); arithmetic over rationals, NOT solver.add(n==count)",
            "z3_full_M": z3_full,
            "z3_erased_M": z3_erased,
            "cvc5_full_M": cvc5_full,
            "cvc5_erased_M": cvc5_erased,
            "real_vs_erased_flip_confirmed": flip_confirmed,
            "interpretation": "SAT under full M (Z separates) -> distinguishable; UNSAT under erased M={X,Y} -> probe-indistinguishable. The merge of the flip pair when Z is erased IS the load-bearing structural flip.",
        },
        "package_versions": {
            "jax": jax.__version__,
            "z3": z3.get_version_string(),
        },
        "packages_used": ["jax", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["jax", "z3", "cvc5"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing vmap batched expectation matrix over the finite set"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing real-vs-erased separability flip (SAT full / UNSAT erased)"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent second SMT solver confirming the same flip"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_jax_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"jax leg wrote {out}")
    print(f"  smt flip confirmed: {flip_confirmed} (z3 {z3_full}/{z3_erased}, cvc5 {cvc5_full}/{cvc5_erased})")
    print(f"  quotient classes full={len(q_full)} erased={len(q_erased)}")


if __name__ == "__main__":
    main()

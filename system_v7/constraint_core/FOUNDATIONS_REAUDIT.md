# Foundations Re-Audit — 2026-07-02

Triggered by owner request ("reaudit foundations, ensure all is built right") after a
harness-count bookkeeping slip. This is a LIVE-RUN audit: every count below was produced by
actually executing the code this session, not inferred.

## 1. Full audit_engines harness (no --fast, all lanes)

Ran the complete suite in `constraintcore` with jax+julia available for the engines lane:

    39 pass / 0 fail / 0 skip -> GREEN

This is the AUTHORITATIVE count. The `36 pass / 3 skip` figures in the layer changelog are
the `--fast` counts (which skip the 2 JAX sims + the cross-substrate engines lane); both are
correct for their mode. All 39 components verified live:
  - foundations: constraint_core_audit, symbolic (b6=-b0b3, integral F=-4pi), 64-schedule
    (order-blind collapse stays 11), nested_basin (4 attractors), axis0 XOR/sector/gauge,
    terrain differentiation, operator-geometry fusion, 16-stage, access law, nonunitality, chi2
  - engines lane: oracle vs jax+julia GREEN at 1q AND 3q (63-dim Pauli, C^8)
  - proof lane: dual-solver axis laws (z3 & cvc5 agree, control flips), QuTiP cross-check,
    manifold SMT proofs
  - physics bridges (6): Landauer, einselection, Jarzynski/Crooks, quantum speed limit,
    holographic/Bekenstein, decoherence scaling
  - JAX sims: flux_nesting_ablation, manifold_build_ladder

## 2. Cross-check against the repo's own v7 foundation sims

The repo `system_v7/sims/` contains 33 foundation-rung sims with the three-engine structure
(julia + jax + pytorch legs + a separate agreement check). Ran two of the most foundational
in-sandbox to confirm they are live and that the independent formalization agrees with them.

### distinguishability_quotient_floor_v0 (the root axiom a=a iff a~b)
Ran jax + pytorch legs fresh in-sandbox (julia leg blocked by the known registry TLS-intercept;
its committed result JSON was used). The cross-leg agreement check confirms ALL THREE agree:
  - quotient S/~_M: full M = X,Y,Z -> 4 classes; erased M = X,Y -> 3 classes
  - the load-bearing z3 + cvc5 flip: "does an active probe separate s1,s2?" SAT under full M,
    UNSAT under erased M -- a real-vs-erased structural flip over exact rational expectations,
    NOT a count tautology
  - pytorch autograd/jacobian identity ok
This INDEPENDENTLY corroborates the exact erased-control-that-flips methodology used in the
audit_engines proof lane (axis_laws_dual_proof, manifold_laws_smt_proof). Two separate
codebases converged on the same discipline.

### weakest_structure_ladder_gate_v0 (the ratchet's ordering discipline)
Ran the fail-closed validator: PASS (exit 0). It dereferences files (source-sha == result-sha
freshness, no REFUTED/CIRCULAR markers) rather than trusting prose. Honest result: only
`density_rho` reaches evidence-grade; `spinor` and `entropy_von_neumann` are OPEN (their
discriminators were circular or unbuilt). The ratchet correctly REFUSES to over-promote.

## 3. Verdict

Foundations are built right. Nothing is broken; nothing self-promotes. The audit_engines
bundle (39/39 live GREEN) and the repo's own v7 foundation rungs agree on the core invariants
(probe-relative quotient, erased-control flips, weakest-structure ordering). The one blocker
remains Julia strict-carrier packages in-sandbox (registry TLS-intercept) -- a laptop-side
install, not a correctness issue; the repo's committed julia results confirm that leg runs
where the registry is reachable.

## Tools used
python (constraintcore: z3 4.16, cvc5 1.3.4, qutip 5.3, sympy), jax (jaxcarrier + z3/cvc5),
pytorch (torchcarrier), julia 1.10.5 (stdlib only in-sandbox), matplotlib.

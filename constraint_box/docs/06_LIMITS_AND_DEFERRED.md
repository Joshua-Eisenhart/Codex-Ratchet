# Limits, open gaps, and deferred work

## Honest build level

| Component | Level in this archive |
|---|---|
| zero-dependency control kernel | implemented and unit tested |
| strict intake and controller-owned dispatch | implemented and unit tested |
| finite constraints and relative partition ratchet | implemented and unit tested |
| simulation-tier runner | implemented and exercised against local tier environments |
| S1 capability profiles | implemented; results in `receipts/` |
| S2 capability profiles | implemented for JAX/Diffrax/Quimb/Cotengra; Julia external profile deferred |
| S3 capability profiles | implemented for PySINDy/PyDMD/pymdp; optional rivals deferred |
| S4 cloud route | fail-closed declaration; no local NVIDIA execution |
| semantic registry and CR boundary | proposed and unit tested as intake rules |
| Lev adapter | event translation implemented; live LevOS transport not integrated |
| 16-stage engine implementation | not included as active code |
| whole-manifold relational settlement | not implemented |

## ConstraintBox is a probability-improving box

The system reduces common LLM failure modes by limiting what can leave the
box. It does not assume that an LLM becomes honest.

It helps against:

- malformed and ambiguous structured output;
- self-selected verifiers and tolerances;
- missing bounded evidence;
- absent dependencies masked as success;
- one fixture silently changing after a tool update;
- premature branch deletion;
- absolute claims inferred from a finite comparison;
- scalar narratives formed by adding incompatible metrics.

It remains weak against:

- collusion between every implementation and every controller;
- a repository owner changing code, policy, fixtures, and baselines together;
- semantically irrelevant obligations that are nevertheless solved correctly;
- false raw input data;
- an independent process that fabricates operating-system evidence;
- unrestricted mathematical or scientific claims.

## Specific deferred items

1. Implement an independent Julia acceptance worker rather than treating
   `julia` as an external executable.
2. Compile a common bounded solver problem into both Z3 and cvc5 from one
   typed intermediate representation, then add semantic mutation controls.
3. Add a TLA+ refinement mapping from controller events, not only a model
   check of the abstract lifecycle.
4. Add canonical AST and residual-decomposition schemas for PySINDy.
5. Implement per-capability resource limits and per-process peak RSS receipts.
6. Add atomic Arrow/Parquet handoff tests when cross-language arrays are
   introduced.
7. Add S4 container digest, GPU UUID, driver, CUDA, cost, and CPU/GPU parity.
8. Implement the proposed M4–M8 manifold fixtures incrementally.
9. Connect the generic Lev event adapter through a fail-closed external bridge.
10. Put CI policy under repository protections; source hashes alone are not a
    trust root.

## Interpretation rule

Words such as *proved*, *solved*, *oracle*, *canonical*, or *fully integrated*
are not rejected merely because they are words. They require a claim type and
evidence obligations strong enough for their scope. In this package, no
profile has an unrestricted theorem or scientific-truth ceiling.

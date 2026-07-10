# Fabrication Audit

## Verdict

`found_fabrication: false`

A fresh semantic auditor inspected the current spec, both engine sources, both
engine results, the controller, and the post-controller validation result.

## Findings

- No hardcoded scientific ledger or desired verdict was found.
- Julia and JAX independently construct transitions, stable partitions,
  compatible ordered rule-pair version spaces, and three-valued query
  consensus.
- Ordered hypotheses remain ordered; only action-swap-invariant object
  relations are quotiented to unordered rule pairs.
- Current source hashes match the declarations bound into both engine results.
- All 2,655 records match over the complete frozen field set.
- The negative scientific verdict follows from preregistered thresholds; no
  budget was deleted or selected after seeing the result.

The auditor initially read a stale validation JSON while the controller was
being rewritten and correctly flagged the impossible old receipt. It re-read
the newer result after the write completed, verified the corrected source-hash
binding, and withdrew the finding. This race is recorded rather than erased.

## Caveat

Controller mutation attacks establish that field corruption and duplicate rows
are detected. They do not constitute a third independent semantic
implementation. Semantic confidence comes from the independently implemented,
source-bound Julia and JAX lanes plus deterministic controller replays.

The audit supports only the exact finite scratch-diagnostic census. It does not
support learning, general perception, semantic-object authority, QIT, ontology,
physics, life, or consciousness claims.

# UFPO v1 Fabrication Audit

## Audit Result

The packet is red and the red is preserved. No missing PyTorch result was
fabricated, no threshold was weakened, no best-seed rescue was used, and no
post-test source repair was accepted.

## Checks

- The v1 manifest excludes every frozen v0 machine and predictive signature.
- Train, validation, and test object identities are disjoint.
- Pair metadata is controller-only and partitions the fixed test objects.
- Preflights opened no test views and wrote no test result.
- Engine sources were tracked and clean before the seal.
- The seal-contract mismatch found before testing was repaired and all affected
  preflights were rerun before the final seal.
- The first Julia sealed result is retained as a wrong-runtime receipt; it is
  not counted as a scientific failure or silently deleted.
- The canonical Julia result is distinct and passes all local semantic gates.
- The JAX sealed result remains local/pending and does not claim packet green.
- The PyTorch exception occurred after frozen test records were built and
  before a result was written. Its actual cause was an unbatched `ndim=2`
  baseline input sent through a batched `ndim=3` schema assertion. The
  dedicated failure receipt is a manually normalized traceback/time receipt,
  not runner-emitted JSON.
- The controller reports the missing `pytorch_result.json` as fatal and emits
  `all_pass=false`.
- The v1 source is not repaired or rerun after test opening.

## Remaining Risk

The exact Julia/JAX legs verify the finite registry and semantics, not learned
perception. A pre-test `/tmp` preflight suggested weak retrieval and little
separation from temporal shuffle, but that diagnostic was not admitted as a
tracked packet receipt. The sealed test never completed, so no learned test
metric may be inferred.

## Claim Ceiling

`UNSEEN_PREDICTIVE_OBJECT_LEARNING_NOT_ESTABLISHED`

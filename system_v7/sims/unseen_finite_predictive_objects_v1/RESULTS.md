# UFPO v1 Results

## Verdict

`RED_PROCESS_FAILURE_AFTER_SEAL`

The exact finite-object registry and the independent Julia/JAX verification
machinery ran. The scoped PyTorch learner did not produce a sealed result, so
the bounded unseen-object learning/perception claim is not established.

## What Ran

- Registry: 2,367 eligible v1 objects after excluding all v0 machine and
  length-1-through-8 predictive-signature identities; frozen 128/32/32 split.
- Julia preflight: all local exact-semantic gates passed without test/result
  access.
- JAX preflight: all local exhaustive/leakage gates passed without test/result
  access.
- PyTorch preflight: 16 scoped arm/seed train-validation cases completed; no
  test views were opened or generated and no result was written.
- Seal: one shared receipt bound the tracked source set at commit
  `aece37830a96dc45955bbefa1b2b93512d36f068`.
- JAX sealed leg: all local gates passed and the result stayed pending the
  controller.
- Julia first sealed attempt: failed only the required strict-carrier runtime
  gate and was preserved as `julia_wrong_runtime_result.json`.
- Julia canonical sealed leg: all exact-semantic gates passed in
  `system_v5/julia_carrier` with `JULIA_LOAD_PATH='@:@stdlib'`.
- PyTorch sealed leg: opened frozen test records, then failed before training
  or metric completion because the order-2 baseline passed one unbatched
  record (`ndim=2`) through a schema assertion requiring batched tensors
  (`ndim=3`). The failure is independent of the four-view/eight-view split.
- Controller: correctly failed closed because `pytorch_result.json` does not
  exist.

## Scientific Ceiling

Earned:

- a genuinely fresh finite registry with exact predictive objects;
- exact Julia semantic reconstruction and arbitration machinery;
- JAX exact/exhaustive registry, split, view-PRNG, leakage, and solver checks;
- a prospective source seal that exposed a real sealed-path defect;
- evidence that train/validation preflight alone did not cover the frozen
  test-view shape transition.

Not earned:

- supervised retrieval or predictive advantage on unseen test objects;
- learned object perception or creation;
- any QIT engine, 16-stage, four-substage, Axis0, MMM, ontology, FEP, physics,
  life, consciousness, or Leviathan-runtime claim.

PyTorch is not a train-only layer. It is a broad tensor, autograd, graph,
network, differentiable-dynamics, optimization, and optional learning toolkit.
This packet exercised one scoped trainable GRU/DeepSets role and failed in a
baseline schema boundary, not in PyTorch's general capability.

## Retry Rule

Do not patch and rerun v1. The sealed one-shot evaluation was consumed. The
test machine tables were already plaintext in the preregistered manifest; they
were hidden from the model-visible schema, not secret from repo readers. A
valid retry must be v2 with a new namespace, fresh test objects, new manifest,
new seal, and a synthetic pre-seal rehearsal of the exact sealed-test call
graph covering unbatched and batched baseline inputs without using v2 test
records.

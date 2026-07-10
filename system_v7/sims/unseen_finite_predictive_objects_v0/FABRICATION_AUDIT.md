# UFPO v0 Fabrication Audit

Verdict: `found_fabrication_risk=true`; positive learner claim rejected.

## Fatal Findings

1. Learner source was not tracked before sealed-test evaluation. The test run
   cannot prove that the evaluated learner preceded test access.
2. The exact train-mean no-input predictor passes the frozen JS threshold by a
   wide margin. The absolute reconstruction gate is vacuous for this family.
3. The attempted run emitted no atomic PyTorch result after about 31 minutes.
   A running process and a worker report are not evidence.
4. The PyTorch result schema would not have retained per-view predictions,
   embeddings, JS values, or pair decisions, preventing metric-only
   recomputation.
5. The `torch.func.jacrev` erased control uses an identically zero direction
   and its boundary uses zero amplitude. Those outcomes are true by
   construction and cannot gate learned temporal use.

## Claim Limitations

- Training supplies exact predictive targets and same-object identities. This
  is supervised/multi-view metric learning, not unsupervised object discovery.
- K-means receives the true test cardinality of 32. Its ARI and B-cubed scores
  would measure known-K partitioning, not discovery of object count.
- Pair selection matches short horizons while views contain length-128
  trajectories. Pair preference is a challenge diagnostic, not a universal
  hard-negative claim.
- The JAX lane uses Python for registry enumeration/canonicalization and JAX
  load-bearingly for exact batched numerators and views. It is a Python/JAX
  workhorse, not a wholly JAX-authored semantic registry.
- Julia and JAX independently match the same manifest, but v0 has no direct
  result-to-result parity controller over a shared emitted registry digest.

## Controls That Worked

- The preregistration provenance audit caught the Python-registry/Julia-owner
  ambiguity before accepting engine results.
- A fresh semantic audit caught Julia's local `engine_all_pass` being copied to
  packet `all_pass`; the receipt was repaired so packet pass remains false.
- The fail-closed controller rejects the packet independently of any attractive
  future learner metric.

## Required v1 Repairs

- wholly new object namespace, splits, views, seeds, weights, and test result;
- all learner, baseline, evaluator, and metric-recomputation sources tracked in
  one clean seal commit before any test call;
- train-mean and order-2 no-input baselines as primary comparators;
- no oracle K; use leave-one-view-out same-object retrieval;
- temporal shuffle as the load-bearing order test; `jacrev` supportive only;
- per-object and per-pair gates with no median-seed rescue;
- per-view outputs sufficient for metric-only recomputation without retraining.

## Audit Receipts

- Leviathan Sonnet provenance review: `rcpt-4e4c7a0584797158`.
- Fresh exact-engine auditor: `019f4d19-d831-7a60-8b7d-379347dfe009`.
- Fresh learner auditor: `019f4d19-6df9-7500-8b74-6ab77e30e376`.
- Grok 4.5 authenticated advisory call confirmed the same source sealing,
  no-input baseline, oracle-K, temporal-control, and pair-aggregation repairs.

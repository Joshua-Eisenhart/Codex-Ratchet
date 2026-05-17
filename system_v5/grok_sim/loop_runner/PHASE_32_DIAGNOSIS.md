# Phase 32 axis-cliff diagnosis — why strongest cliff lands at position 1

Read-only analysis, no code edits.

## What Phase 32 measures

Builds a 256-row state-matrix `M`: for each (ref_state, engine, stage_idx),
averages the 4 substages and flattens the complex 16×16 density matrix into
a 512-element real vector. `SVD(M)` returns 15 leading singular values.
Pass criterion: consecutive ratio `σ_7 / σ_8` is the LARGEST in positions
1..14 AND ≥ 1.5.

Pass means: the manifold's dominant 7 directions are sharply distinguished
from direction 8 onward — operational evidence for the "7 axes" claim.

## What the current candidate does

`candidate_stage_role_patch_20260514Tlocal.py` is a thin wrapper:

```python
def engine_stage(engine_id, stage_idx, substage_idx, input_rho_qt):
    out = _BASE.engine_stage(engine_id, stage_idx, substage_idx, input_rho_qt)
    rho = out["output_rho_qt"]
    U = _role_unitary(substage_idx)        # ← varies in substage only
    rho2 = U * rho * U.dag()
    ...
```

The "role unitary" is selected only by `substage_idx` (0..3). When Phase 32
averages the 4 substages per (engine, stage), the substage-only variation
collapses. What remains is whatever variation `_BASE.engine_stage` produces
across `(engine_id, stage_idx)`.

## Why the cliff lands at position 1

Cliff at position 1 means `σ_1 / σ_2` dominates — one direction carries
nearly all the variance in `M`. Three plausible causes:

1. **BASE uses one strong generator + small perturbations.** If the base
   `_BASE.engine_stage` applies one dominant rotation G_main scaled by
   stage_idx (so stage 7 is just 7× stage 1 in the same direction), all
   the row variance lives on a 1-D subspace.

2. **Generators are nearly collinear in Frobenius norm.** The 7-axis
   claim requires 7 generators mutually-orthogonal under `Tr(G_i G_j)`.
   If they're built from overlapping Pauli tensors (e.g. all `Z⊗I⊗I⊗I`,
   `I⊗Z⊗I⊗I`, ...), they ARE orthogonal — but if engine_stage applies
   them with very different magnitudes, only the largest contributes.

3. **Engine A and Engine B trace identical paths.** Phase 32 treats them
   as independent rows; if BASE returns the same output for A and B at a
   given stage, they double-count one direction instead of contributing
   distinct ones.

The candidate inherits whichever of (1)(2)(3) holds in the BASE. The
role-unitary patch in the wrapper does not address any of them — it adds
variation only in substage, which the test averages away.

## What a passing engine_stage would look like

The 7-axis cliff is earned when:

- `stage_idx ∈ {0..6}` selects from 7 Frobenius-orthogonal Hermitian
  generators `G_0..G_6` on the 4-qubit carrier (e.g. 7 distinct
  weight-1 Pauli tensors).
- `stage_idx = 7` reuses one of `G_0..G_6` (so the 8th stage is a
  near-duplicate direction → distinct cliff at position 7).
- All applied with comparable α magnitudes so no single direction
  dominates by orders of magnitude.
- Engine A and Engine B differ — e.g. by sign of the generator or by
  an additional Weyl-chirality factor — so they don't collapse to one
  trajectory.
- Substage applies a fast-cancelling 4-cycle (Ti / Te / Fi / Fe per the
  doc) that averages cleanly per stage but doesn't bias any of the 7
  stage directions.

Concretely, choose generators like:
```
G_0 = Z ⊗ I ⊗ I ⊗ I,   G_1 = I ⊗ Z ⊗ I ⊗ I,   G_2 = I ⊗ I ⊗ Z ⊗ I,
G_3 = I ⊗ I ⊗ I ⊗ Z,   G_4 = X ⊗ X ⊗ I ⊗ I,   G_5 = I ⊗ Y ⊗ Y ⊗ I,
G_6 = I ⊗ I ⊗ X ⊗ X,   G_7 = G_0   (degenerate; gives the cliff at 7)
```

Pairwise Tr(G_i G_j) = 0 for i ≠ j among `G_0..G_6` (Pauli strings
on distinct supports / different operator weights). Applied as
`exp(-iα G_k) ρ exp(+iα G_k)` with α ≈ 0.3 across the 7 generators,
the resulting state matrix has rank ≈ 7 in its first-order Taylor
expansion around `input_rho_qt`, and σ_8 drops sharply (the 8th
direction is the second-order correlations between two G_k's).

## What this is NOT

This diagnosis does not yet design the engine_stage that earns Phase 32.
It maps the wall — names what would need to change in the BASE and in
the wrapper to make the cliff land at position 7. Whether to commit
that design is a research call.

## What it implies for the prime probe (Phase 98)

The engine-derived prime probe I just landed (z=−0.71σ) used the
manifold assembly's holonomy + density-transport + Hopf projection as
the signature components. If engine_stage's 7-axis structure were
genuinely orthogonal (Phase 32 pass), the same probe would have 7
independent components per n to draw from. That STILL would not
encode multiplicative-order structure — primes still wouldn't
cluster — but the geometric coverage would be wider.

Phase 32 and Phase 98 are independent in this sense: Phase 32 is about
manifold tangent structure; Phase 98 is about whether ANY engine-
derived signal (regardless of tangent rank) detects primes.

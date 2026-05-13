# Canonical Sim Proposal Triage From Grok Side Quest

Status: `side_quest_only`; not admission evidence. This note converts the
informal Grok/Opus loop into proposed formal sim directions only.

## Source Surfaces Read

- `system_v5/grok_sim/README.md`
- `system_v5/grok_sim/loop_runner/README.md`
- `system_v5/grok_sim/loop_runner/prompts/public_api_contract.md`
- `system_v5/grok_sim/loop_runner/research_notes/OPUS_AUDIT_2026_05_13.md`
- `system_v5/grok_sim/loop_runner/research_notes/CAPABILITY_AND_BOUNDS_MATRIX.md`
- `system_v5/grok_sim/loop_runner/research_notes/SESSION_RETROSPECTIVE_2026_05_13.md`
- receipts under `system_v5/grok_sim/loop_runner/receipts/20260513T174025Z/`

## Hard Boundary

Nothing here promotes a QIT, GStack, axis, bridge, nonclassical, engine, or
Rosetta claim. Any candidate below must be re-derived as a canonical sim with
the repo sim contract, exact tool manifest, positive/negative/boundary tests,
graveyard companions, and a fresh result receipt.

The current side-quest candidate is contaminated by known cheats and should not
be patched toward admission. Use the side quest as a proposal generator and
audit-pattern source only.

## Rejected Before Reuse

- Synthetic Fisher matrix: matrix is constructed directly and ignores input
  perturbations.
- Closed-form holonomy: phase is returned directly rather than integrated.
- Decorative flux integral: nonzero value comes from a constructed constant
  term; the oscillatory term integrates away.
- Identity quotient compression: the candidate returns the input as canonical.
- Snap-to-target recovery: recovery blends toward a reference trajectory rather
  than deriving an inverse or recovery map.
- Hash-offset stage uniqueness: distinctness is forced by index arithmetic.
- Primality-conditioned scores: score path leaks a classical primality check.

## Proposed Formal Sims

### `sim_probe_expectation_equivalence_class_micro`

Math: two element-distinct density matrices with identical expectation tuples
under a fixed finite probe family.

Observable: probe expectation tuple equality and matrix inequality.

Graveyards: same matrix twice; probe family that separates the pair; random
pair that fails tuple equality.

Side-quest signal: the public contract names the right root axiom, but the
latest informal implementation failed its own `(distinct, same_class)` check.

### `sim_channel_order_trace_distance_micro`

Math: two noncommuting density-evolution maps applied in opposite orders.

Observable: trace distance between `rho_AB` and `rho_BA` over a small input
ensemble.

Graveyards: commuting channel pair; input in a shared fixed space; identity map
replacement.

Side-quest signal: `noncomm_pair` was one of the few audit-surviving ideas, but
anything depending on the informal stage construction must be rebuilt without
hash-offset distinctness.

### `sim_dephasing_fixed_subspace_basis_micro`

Math: fixed subspaces of two dephasing superoperators in different bases.

Observable: residual norm of the Lindblad generator on candidate fixed states;
separation between the two fixed-state sets.

Graveyards: wrong basis; generic coherent state; identity generator.

Side-quest signal: this is the cleanest low-contamination proposal because it is
plain linear algebra and does not require the side-quest stage machinery.

### `sim_landauer_information_bound_micro`

Math: information-to-work bound for a biased bit under measurement, conditional
operation, and erasure accounting.

Observable: entropy of the bit distribution, extracted work estimate, erasure
cost, and bound residual.

Graveyards: no measurement; no conditional operation; no erasure cost; hardcoded
efficiency.

Side-quest signal: the contract direction is useful, but the informal candidate
hardcoded efficiency and must not be reused.

### `sim_path_ordered_phase_integral_micro`

Math: numerical path-ordered product around a closed loop, compared against a
trivial loop.

Observable: accumulated phase from discrete path transport and convergence with
refinement.

Graveyards: trivial loop; closed-form answer with unused step count; orientation
reversal.

Side-quest signal: the informal candidate exposed the right falsifier: a phase
function is not evidence unless `n_steps` affects a real path product.

### `sim_carrier_dimension_spectral_cliff_micro`

Math: singular-value cliff of a trajectory-sample matrix as carrier dimension
changes.

Observable: ratio `sigma_k / sigma_{k+1}` at declared positions under multiple
carrier sizes and alternative sample bases.

Graveyards: random trajectory control; permuted labels; fixed small carrier;
single-basis-only cliff.

Side-quest signal: the side quest reports a 4-qubit negative and 8-qubit
positive pattern. Treat that as a hypothesis only; re-run from scratch.

### `sim_totient_signature_shuffle_null_micro`

Math: feature vectors derived from totient or coprime-indexed operations tested
against label-shuffle nulls.

Observable: prime/composite cluster statistic, null distribution, p-value, and
failure at larger ranges if present.

Graveyards: primality-leaking score; random labels; constant signatures;
range-split overfit.

Side-quest signal: only the raw signature-vector idea may be salvageable. The
score path is invalid because it used a primality-conditioned multiplier.

## Naming Gate Before Any Port

Do not reuse side-quest names in canonical sim files. Before porting, replace:

- `engine_a`, `engine_b`, `Engine A/B` with literal channel or map names.
- `Type 1/Type 2` with Weyl chirality labels only when the object is actually a
  left/right Weyl spinor state.
- `axis`, `Ax0..Ax6` with `transform_index_*` or a literal operation name until
  a geometric axis claim is earned.
- `Szilard`, `Carnot`, `IGT`, `I-Ching`, `hexagram`, `trigram`, `elephant`,
  `rider`, and cognitive labels with pure mathematical operation names.
- `denoise_pipeline` with a literal recovery-map name.
- `prime_resonance` with `totient_signature` or a similarly literal statistic
  name.

## Recommended First Port

Start with `sim_dephasing_fixed_subspace_basis_micro`. It is self-contained,
does not depend on contaminated side-quest stage machinery, and can be expressed
as finite-dimensional linear algebra with clear graveyards.

Second choice: `sim_probe_expectation_equivalence_class_micro`, because it
targets the root probe-relative identity axiom directly.

Do not port the prime or carrier-cliff ideas until their side-quest source
numbers are independently rechecked from raw code and receipts.

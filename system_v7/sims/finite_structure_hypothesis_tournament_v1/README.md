# Finite structure hypothesis tournament v1

This packet is a bounded classical tournament over typed finite-structure
presentations. It is the first executable discriminator suggested by the
current anti-thing/MSS proposal; it is not a Ratchet run and it does not select
an ontological root.

The executable object keeps three clocks separate:

1. candidate-internal transitions or kernels;
2. proposal/search motion over candidate states;
3. append-only Ratchet context epochs.

Only the first is present in v1, and only for candidates that explicitly carry
transition semantics. Candidate generation is deterministic finite
enumeration, not search motion. Therefore v1 makes no recurrence, attractor,
basin, Purgatory, or Ratchet-tooth claim.

The frozen source of truth is `spec.json`. Julia Canon and the JAX workhorse
must each construct candidates and permutations directly from that spec. Z3
and cvc5 use separate encoders and every SAT model is replayed without a
solver. PyTorch is deliberately omitted because no learning, autograd, or
graph-network claim exists here.

`J_n` and `C_n` are retained as different typed presentations of the same
universal support data. They count as one class only inside a preorder that
explicitly forgets their semantic difference. Runtime agreement on that
encoding is a control, not independent scientific evidence.

The literal claim ceiling and every blocked consumer are in `spec.json`.

## Current execution status

The current source-backed receipts are green, deterministic, and scratch-only:

- Julia emits 256 registry identities across sizes `1,2,3,4`, with counts
  `6,24,213,13`. Sizes `1..3` are exhaustive for the declared binary-relation
  grammar; size `4` is a named boundary.
- JAX independently reconstructs all 243 exhaustive identities at sizes
  `1..3`. JAX also checks seven named size-4 relation boundaries, but does not
  claim a complete size-4 candidate or MSS mirror.
- The strict controller independently reconstructs candidate identity,
  automorphisms, partitions, viability, raw aliases and duplicate
  representations, all fifteen exhaustive MSS arms, the named size-4
  boundaries, append groups, external gates, entropy readouts, and the SMT
  query vector. It reports zero discrepancies and 57 genuine corruption
  mutations rejected. Julia, JAX, and SMT receipts each carry a recomputable
  core hash, so uncoordinated raw receipt drift fails closed. Those hashes are
  self-consistency bindings, not signatures or proof of authorship; the
  independent semantic oracles, source-backed reruns, and outer receipt chain
  remain necessary against a coordinated rewrite that refreshes a core hash.
- Z3 and cvc5 each run nine exact fixed-carrier queries and independently
  enumerate 26 SAT permutations. Every permutation is replayed by the Python
  structure oracle. A duplicate solver query found by external review was
  removed instead of counted as another control.
- The supplemental standard engine envelope passes the strict source-backed
  validator with tool-intent enforcement.

Current receipt hashes:

| Receipt | SHA-256 |
|---|---|
| Julia | `3a4ef333e633db219f718b95dfdf69a65735eb2b030cd5f4c5d3d1306f750215` |
| JAX | `6baefc8010ca482f289c0d6f1b5021765b1896e32af5b78e83eb3da5bf4e2af3` |
| SMT | `ec15760115210c690334611241ef5551924ae6baba86502839b328f61d14db02` |
| Controller v4 | `aab844321d9994c80e5f3b032504327544dfad33caaa0d8d12119b1bc5d14dce` |
| Standard envelope | `b34ffd6ff115a6b62c3f02544566db042c24c7f132609d7be9a76ef16f61a61c` |

## Exact discriminator outcome

There is no comparator-independent winner. The intersection of the five MSS
frontiers is empty at every tested size.

- `signature_registered` selects the empty-signature class `{U_n}`.
- `stochastic_unbiased` selects `{K0_n}`.
- `K0_n` is the unique common member of every nonempty non-signature frontier,
  but that recurrence is conditional on excluding the signature arm and must
  not be promoted into a universal root.
- The other arms retain plural equivalence classes. Their plurality is the
  result, not a tie that this packet is authorized to break.
- The external gate chain `512 -> 64 -> 8 -> 1` shows
  constraint-conditioned filtering while each survivor stays internally
  unchanged. It does not show dynamics or an attractor.
- Fixed-size `K0_n` has exact state-entropy change zero. Its conditional and
  path entropies are typed readouts, not a drive.

## Anti-teleological interpretation

The strongest licensed philosophical schema uses histories and fibers. Let
`H` be possible global histories, `rho_t` their restriction to a present
slice, `Gamma` independently specified admissibility constraints, and

`F_(Gamma,p) = H_Gamma intersect rho_t^-1(p)`.

Many divergent histories may lie in the same fiber. A present-slice property
constant across that fiber may be explained as an invariant of admissibility,
without the present acting as a final cause. Reverse branching enumerates a
preimage; it does not reverse causation. The current term is therefore
`constraint-conditioned common image/fiber`, not `attractor basin`.

This experiment illustrates one static finite mechanism of that form. It does
not provide evidence that the cosmos is non-teleological. The explanatory
content resides in `Gamma`, so a later claim-bearing experiment must
pre-register `Gamma`, the present property `p`, and every arm inclusion or
exclusion before observing the survivor. Otherwise the desired present can be
smuggled into the constraints after the fact. Moreover, a fiber formed after
choosing `p` only characterizes that chosen present; it does not explain why
`p` occurs. A stronger test must inspect the full image `rho_t(H_Gamma)` and
apply a frozen selection rule before matching any recurrent image to the
observed present.

## Preserved reds and advisory reviews

The initial preregistration failure, first JAX static-scan failure, controller
v1 bypasses, controller v2 bypasses, two initial Sonnet timeouts, the first
large Fable 5/default audit timeout, and interrupted stale Lev run are retained
as red process evidence. They are not included in the current green result.

Grok 4.5 returned `SERIOUS` against the pre-hardening controller; its duplicate
SMT control, missing nested JAX `all_pass`, and size-4 scope findings were
folded into later versions. The final smaller Fable 5/default philosophical
audit returned `REPAIRABLE`: the fiber formulation is coherent, while the
experiment only illustrates it and does not establish a cosmological result.
All external-model reviews are advisory. Their receipt hashes and exact
dispositions are in `results/external_review_manifest.json`.

## July 15 cumulative-pack reconciliation

The supplied July 15 cumulative knowledge pack validates cleanly as an
archive, but its own manifest classifies it as communication and research
orientation rather than canon. It proposes `root_carrier_mss_tournament_v1`
as the next Packet A; that proposal has not run, and this narrower frozen
tournament cannot be relabeled as its execution.

The proposed next contract also needs an amendment before execution. A single
cardinality sweep through `1..5` is not an exhaustive bound for every listed
grammar: total binary operations grow as `n^(n^2)`, free bracketed terms need
a depth bound, and PSD/density-operator spaces require an explicit finite
family or grid. The next packet must freeze grammar-specific exact, quotient,
named-boundary, or sampled envelopes. It must use Julia, JAX, and PyTorch in
their actual claim-bearing roles, but PyTorch should not be wrapped around a
candidate merely to satisfy a tool count. The exact validation, authority
separation, philosophical repair, and operational gaps are recorded in
`results/july15_cumulative_pack_reconciliation.json`.

## Reproduction

From the repository root in the isolated worktree:

```text
env JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v7/sims/finite_structure_hypothesis_tournament_v1/run_julia.jl
/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v7/sims/finite_structure_hypothesis_tournament_v1/run_jax.py --out system_v7/sims/finite_structure_hypothesis_tournament_v1/results/jax_result.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/finite_structure_hypothesis_tournament_v1/run_smt.py --spec system_v7/sims/finite_structure_hypothesis_tournament_v1/spec.json --out system_v7/sims/finite_structure_hypothesis_tournament_v1/results/smt_result.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/finite_structure_hypothesis_tournament_v1/run_controller.py --out system_v7/sims/finite_structure_hypothesis_tournament_v1/results/controller_result.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/sims/finite_structure_hypothesis_tournament_v1/build_standard_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v7/sims/finite_structure_hypothesis_tournament_v1/results/standard_engine_envelope.json --strict-source-backed --require-tool-intent
```

# Wiki Corpus Basins Receipt - 2026-06-11

## Route

- route_id: `wiki-corpus-basins-tier1`
- request: create `~/wiki/codex-ratchet-research/basins/` with standard math,
  alternatives, negatives, and distillate corpus files.
- write_scope:
  - `/Users/joshuaeisenhart/wiki/codex-ratchet-research/basins/**`
  - `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/wiki_corpus_basins_20260611.md`
- git_add_commit: not run
- lev_timetravel: unavailable in this shell (`lev: command not found`)

## Files Written

- `/Users/joshuaeisenhart/wiki/codex-ratchet-research/basins/standard-math.md`
- `/Users/joshuaeisenhart/wiki/codex-ratchet-research/basins/alternatives.md`
- `/Users/joshuaeisenhart/wiki/codex-ratchet-research/basins/negatives.md`
- `/Users/joshuaeisenhart/wiki/codex-ratchet-research/basins/distillate.md`
- `/Users/joshuaeisenhart/wiki/codex-ratchet-research/basins/child-receipt-20260611.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/wiki_corpus_basins_20260611.md`

## Per-File Line Counts

- `alternatives.md`: 108 lines
- `child-receipt-20260611.md`: 88 lines
- `distillate.md`: 78 lines
- `negatives.md`: 107 lines
- `standard-math.md`: 154 lines
- corpus total: 535 lines

## Child Receipts

- Codex child `019eb863-4cf8-7e01-807c-628a9b3bd539` / Harvey:
  source-backed Conley theory and attractor-lattice lane. Returned Conley
  decomposition, attractor-repeller pairs, Morse decompositions, complete
  Lyapunov functions, attracting blocks, and the bounded-distributive-lattice
  caution for Kalies-Mischaikow-Vandervorst.
- Codex child `019eb863-6777-7403-b545-637be36e1861` / Bernoulli:
  source-backed Milnor/riddled/negative-control lane. Returned positive-measure
  Milnor basins, riddled/intermingled basin obstruction, generic affine/linear
  monostability control, nonlinear multistability contrast, and gradient-system
  acyclic/descent control.
- Codex child `019eb863-80dc-7093-8ce5-e55c0f9b09b9` / Bohr:
  source-backed computational lane. Returned Attractors.jl mapper/fraction
  methods, interval/set-oriented approximation cautions, and complete-Lyapunov/
  Morse-rank certificate boundaries.
- Gemini CLI advisory cross-check:
  bounded prompt returned `OK / CORRECT` after quota retries. It agreed with the
  conservative claims on Milnor basins, Conley theory, attractor/block lattices,
  riddled basin obstruction, affine/linear monostability as a generic control,
  and Attractors.jl as numerical unless paired with interval/Conley proof
  machinery.

## Coverage Check

The final corpus includes:

- attractor and basin definitions;
- Conley index, Morse decompositions, Conley's fundamental theorem, and complete
  Lyapunov functions;
- Kalies-Mischaikow-Vandervorst attractor lattice / attracting block structure;
- bounded-distributive-lattice vs Boolean-algebra caution;
- Milnor attractors and measure-theoretic basins;
- fractal, riddled, intermingled, and Wada basin-boundary distinctions;
- interval-box, set-oriented, Attractors.jl, basin-fraction, and
  complete-Lyapunov/Morse-rank computational cautions;
- alternatives: SRB/physical measures, ergodic decomposition, chain recurrence,
  isolating neighborhoods, and trapping regions;
- negatives: affine/linear monostability control, nonlinear multistability
  requirement caveat, gradient descent/no-cycle control, and riddled-basin clean
  decomposition obstruction;
- MMM register / exclusion-language basin criterion in `distillate.md`.

## Verification Commands

- `wc -l ~/wiki/codex-ratchet-research/basins/*.md`
- `find ~/wiki/codex-ratchet-research/basins -maxdepth 1 -type f -print | sort`
- `rg -n "Conley|Morse|complete Lyapunov|attractor lattice|bounded distributive|Boolean|Milnor|riddled|fractal|Attractors.jl|interval|affine|gradient|SRB|chain recurrence|isolating|trapping" ~/wiki/codex-ratchet-research/basins`

## Boundary

No sim, queue movement, admission artifact, git staging, or commit was
performed. The corpus is a research register and does not promote a canonical
Codex Ratchet basin theorem.

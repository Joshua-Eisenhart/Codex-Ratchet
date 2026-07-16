# CLAUDE.md — agent contract for the constraint-core bundle

You are working inside a formal research bundle with strict claim discipline.
Read this whole file before editing anything. It is short on purpose.

> **RATCHET_V0_5_ORDER_OPEN_PROCESS:** `RATCHET_SPEC.md` is the process authority for this bundle. The primitive is
> constrained distinguishability—not objects, `~`, quotients, finite support, a named entropy, geometry, Hilbert space,
> or CA. Gate boundaries, subgates, orders, decompositions, gradients, and weakness relations are proposal populations.
> Do not infer a ladder from serialization order. A surviving entropy–geometry coface gradient drives a tooth; without
> one the process returns to DIG rather than asserting a terminal HOLD. Every MSS result is a search-relative
> provisional frontier. Legacy `EARNED` rows retain only their declared
> fixture-local result; they are not global forcing claims. Run `python3 ratchet/bundle_ratchet_lint.py` after changing any
> claim-bearing front door or generator.

> **RATCHET_V0_6_EXECUTED_MANIFOLD_AUDIT:** Before discussing any manifold layer, read
> `ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md`. L1–L8 pass local rerun, but zero scientific manifold
> layers are admitted. The actual manifold fixture Ratchet earns only a radius-plus-orientation distinction under its
> finite winding demand. Do not restore nested shells as L5 MSS, BKM as unique L6 metric, the L6→L7 full coidentity, or
> Chern sign as physical chirality without new receipts that defeat the audit's explicit counter-results.

> **RATCHET_V0_7_PRESERVATION_COMPLETE_SURFACE:** Your first commands are
> `python3 preservation/verify_preservation.py` and `python3 ratchet/bundle_ratchet_lint.py`. Then read the preservation
> index, complete simulation ledger, exceptional/nonassociative report, attractor-basin report, and actual manifold
> report. Also read `reports/DIRECT_RERUN_RECEIPTS.md` before claiming that a dark script reran here. There are 190
> top-level simulation scripts: 144 registered and 46 unregistered. Never infer absence from
> `run_all.py`, never omit an unregistered receipt, and never treat registration as canon. Julia owns the exceptional
> algebra convention in `julia_canon/`; a real Julia export receipt EXISTS in this build (first executed 2026-07-11
> after an export_canon.jl quoting repair; Python mirror cross-validates).

## What this is
A machine-checked formalization of a constraint-based theory (single-qubit GKSL
dynamics + a layered spec). Everything is `scratch_diagnostic`,
`promotion_allowed=false`. The ratchet earns canon; you do not.

## The two fail-closed commands that matter first
```
python3 preservation/verify_preservation.py
python3 ratchet/bundle_ratchet_lint.py
python3 preservation/bootstrap_project_memory.py
```
The first two must exit 0 before and after any claim-bearing change. The third emits the minimum complete layer/math
snapshot and refuses to run over a stale manifest. Together they verify the complete memory surface and the process
integrity lane. `python3 run_all.py` remains a legacy reproduction lane over 144 registered scripts; the supplied local
receipt is honestly red at 109 pass / 4 fail / 33 skip. Do not edit expectations or hide optional-runtime gaps to make
that aggregate report green.

It also runs the Ratchet process integrity lane. A green harness demonstrates reproducibility and process lint only;
it does not admit a scientific claim.

## Hard rules (violating any of these is the failure mode this file exists to prevent)

1. **Never edit an expected value in `run_all.py` to make a check pass.** A
   mismatch between a sim and its expected value is a FINDING — report it, do
   not resolve it. Same for mismatches between the spec and a sim: divergence
   is data, not a bug to silently harmonize.
2. **Some expected results are honest failures. They must stay failed.**
   - `manifold_build_ladder.py`: `doctrine realized ... : False` — the Axis-0
     entropy doctrine does NOT hold at density level. Making it True is a
     regression, not a fix.
   - `engine_64_schedule_sim.py`: order-blind collapse `11/64` — the collapse
     is the point.
3. **Withdrawn claims — never restore these, even if older text in the corpus
   still asserts them:**
   - the "linear gauge-breaking law, R² = 1.0" (§7o — withdrawn; it was an
     affine identity of a one-step Kraus parametrization);
   - the "threefold convergence" of §7o/§7p/§7q (it is ONE bit — non-unitality
     `L(I) ≠ 0` — read three ways);
   - the flat "16/16 access theorem" of §7s (the earned form is two-tier:
     exact on the 8 dephasing stages, 14/16 under a chirality-neutral probe,
     16/16 only with the sheet Hamiltonian adopted into the loop definition);
   - "χ₂ is closed / Axis-0 reads end-to-end" (§7v — overclaim; χ₂ is earned
     only as a general eigenvector-sector meter. The "V vs V*" demonstration
     read the K-mirror pair, not the a2 pair; the terrain-level decisive test
     fails 2/8–6/8 with ε-contaminated phases. See the §7v audit flag.);
   - "Axis-0 = Axis-1 ⊕ Axis-2, exactly (earned)" (§7m — status is
     ADMISSIBLE CANDIDATE, not identity: the proven direction is parity ⇒
     single readouts fail; the converse has never been tested because the
     parity has never been read. Do not upgrade §7m's status until a
     charge-specific χ₂ passes the terrain-level test.);
   - "Layer 16/17 grounds the axioms externally" (the ten physics bridges are
     theorems of the installed U-1 carrier — they earn realization
     faithfulness, not axiom validation; see the flag in
     docs/PHYSICS_INFO_BRIDGE_INDEX.md);
   - "the §7q null supports fusion" (a null cannot; fusion is settled by the
     containment split + W-covariance §7t, not by the metric null).
4. **Sims are pure math. No labels in code.** Structural indices only
   (`eps, a1, a2, t0..t7, Ti/Te/Fi/Fe`). All naming — terrain names, Jungian
   labels, physics vocabulary ("gauge", "Weyl", "geometric phase") — lives in
   `data_json/rosetta_layer.json` with earned/witness/candidate tiers. Never
   move a label from the rosetta into a sim, and never change a label's tier.
5. **Do not conflate V and W (§7u).** `V = exp(−iH₀s)` is the continuous state
   gauge (commutes with the engine flow; carries the δ=0 degeneracy and
   K = H₀). `W = (σx+σz)/√2` is the discrete pair-duality (swaps Ti↔Te, Fi↔Fe
   exactly; does NOT commute with the flow). They are provably distinct; code
   or text that substitutes one for the other is wrong.
6. **Owner-level open decisions — do not resolve them yourself:**
   - the two-64s tension: §7g's `64 = 2×8×4` (all combos runnable) vs
     §7r's `16 = 8×2` native stages (which makes 64 = 16 stages × 4
     sub-stages, with 48 combos inadmissible). Incompatible counts; flagged
     in the spec; the owner decides.
   - the terrain-level direct/conjugated bit (a2 on terrains): RESOLVED as a
     layer statement (§7w). a2 is realized exactly at the OPERATOR layer (§7t,
     W-covariance) and provably does NOT descend to a terrain-generator
     observable: the ε-even quotient of χ₂ reads the a1 dynamics bit (finite
     check over the 8 generators), and W conjugates the operators but not the
     generators (per-pair residuals 2.112 and 1.990). Do not re-open this as "find the terrain
     meter" — the no-go is the result. What remains genuinely open below.
   - the charge-specific χ₂ at the TERRAIN layer: a no-go (§7w). χ₂ stays an
     earned eigenvector-sector meter, not a2-specific — do not relabel it
     "closed as an a2 meter". §7m therefore reads end-to-end only at the
     operator layer; keep its terrain-layer status ADMISSIBLE CANDIDATE.
   - the P9 admissibility derivation: why exactly 2 operators per terrain.
     CLOSED (2026-07-01, `admissibility_two_operator_sim.py`). Derived from C2:
     a stage needs one dissipative + one unitary generator (Axis-5); of the 4
     candidate pairs the two SAME-basis pairs commute EXACTLY (order-gap 0, so
     the stage collapses — C2 forbids it); the 2 surviving cross-basis pairs
     are Axis-2 (W) conjugates, and each terrain's frame sign selects one =>
     exactly 2, signed. Do not re-open. (The two eliminated pairs are
     {D_z,H_z} and {D_x,H_x}; survivors {D_z,H_x}={Ti,Fi}, {D_x,H_z}={Te,Fe}.)
7. **Comparisons are tolerance-based, never `==`** on floats. Claim grades per
   spec §8: promotable rows need `symbolic_identity` / `closed_form` /
   `finite_exhaustive` routes; float tolerance is `diagnostic_float_nonclaim`.
8. **Do not regenerate figures** unless explicitly asked; `figures/` is
   pre-rendered and matplotlib is deliberately not a requirement.
9. **The coherent axis (1,1,1)/√3 is load-bearing** (P12,
   `axis_loadbearing_n01_sim.py`): with the axis on σz the four Fe stages
   commute exactly with their terrains and 16/16 order sensitivity collapses
   to 12/16. Never change H₀'s axis "for simplicity"; the bundle's two axis
   conventions (σz in engine_type_access_sim, canonical elsewhere) are NOT
   interchangeable for N01 claims.
10. **Determinism:** all stochastic sims are seeded. If you add a sim, seed it
   (`np.random.default_rng(0)`), make it standalone, CWD-independent, print
   its headline invariants to stdout, and add a `run_all.py` entry.
11. **When editing the spec**, corrections are logged visibly (see §7o's
    correction note for the required style) — never silently rewritten. New
    claims get an explicit claim ceiling.
12. **Never put an equivalence relation or object at the root.** A finite probe quotient is a later realization. The
    root is a contextual, potentially partial and history-sensitive constrained-distinguishability relation expressed in
    finite test syntax.
13. **MSS never returns an unscoped unique weakest object.** Freeze a finite candidate grammar, weakening grammar,
    tests, and budget; compute all minimal surviving candidates; retain incomparable members and open weaker attacks.
14. **Evidence history ratchets; model frontiers remain defeasible.** A new weaker survivor demotes a stronger rung and
    reopens descendants without deleting their receipts.
15. **Entropy and geometry are one later distinction-surface presentation.** Do not restore separate claim-bearing
    `G_t` and `E_t` state fields or describe entropy as running on prior geometry.
16. **CA is a candidate family.** Ring, cells, alphabet, locality, parity, synchrony, and update schedule must compete
    with weaker finite transition, rewrite, and evolving-graph presentations.
17. **No surviving gradient, no tooth—but DIG does not stop.** Generate rival drive/readout hypotheses with the
    candidates. Test each by its declared coupling and claim-specific controls. A missing witness yields
    `UNRESOLVED_GATE__DIG_CONTINUES`; it never establishes global flatness.
18. **Strict gates require free exploration and an executable bias flip.** Do not make proposal generation conservative
    because admission is strict. Generate lower/stronger carriers, alternate gradients, weakness orders, negatives, and
    counter-surfaces first. A validator over prewritten receipts is not a Ratchet run. Every run must emit an executed
    trace and a nonempty next dig queue.
19. **Every manifold output must carry a layer state report.** State the prior dependencies, equations, executed
    candidates, behavioral alias count, coface gradient, controls, MSS frontier, failures, and exact claim ceiling.
    `PASS` in a source script is not an admission status.
20. **Search all 196 scripts, not only the 144 registered scripts.** Registration records aggregate execution coverage.
    It says nothing about existence, truth, canon, or whether a hypothesis/negative must be preserved.
21. **Never truncate a complete mathematical inventory.** Human summaries may be short, but the machine ledger must
    name every script and receipt. Exceptional/nonassociative and basin work each require their dedicated state report.
22. **Preserve audit reversals.** In particular, the FEP v1 allocation split used hidden profile-specific learning rates;
    v2's schedule-only result is `no-split`. Do not quote v1 without the retraction.
23. **Julia ownership must be executable and honest.** Fano orientation, multiplication, bracket order, proof tags, and
    structural basin labels live in `julia_canon/`. A Python mirror may cross-check exports but may not be called a Julia
    run. In this build the Julia export EXECUTED (receipt in julia_canon/artifacts/); in runtime-absent environments
    the blocked status remains the honest state.
24. **A missing source is not a clean audit.** Mark it `CLAIM_ONLY__SOURCE_MISSING`, preserve the proposed claim, and
    prevent it from changing current state.
25. **A ZIP is functional project memory only when surfaced.** Every successor must regenerate the preservation
    manifest, complete sim ledger, dedicated math reports, and bundle lint. Physical bytes hidden behind stale front
    doors do not satisfy preservation.
26. **Self-paths must resolve inside the extracted ZIP.** Run `python3 preservation/standalone_path_audit.py`. A saved
    result written through an absent desktop repo path is not a fresh standalone rerun, even if the math completed.

## Map
```
00_START_HERE.md                THE entry point (read first; §5e = bundle map)
RATCHET_SPEC.md                 executable anti-drift process authority
CLAUDE.md                       this file
archive/ORIENTATION.md          SUPERSEDED orientation (provenance only; 00_START_HERE replaces it)
ratchet/                        working engine, executed runs, packets, gradient law,
                                schema, frontier, CA lane, and front-door lint
preservation/                   completeness manifest, anti-amnesia index, executable verifier
reports/                        complete sim ledger, exceptional math state, basin state
julia_canon/                    Julia-owned exceptional algebra source/export boundary
run_all.py                      legacy aggregate harness (144 registered of 190 scripts)
requirements.txt                numpy/scipy/sympy required; jax optional
spec_and_reports/
  CONSTRAINT_CORE_FORMAL_SPEC.md  the spec (§0–§10; manifold arc §7–§7u)
  PURE_MATH_CORE.md               de-jargoned proposition ledger P1–P11
  constraint_core_methods_report.md, geometric_manifold_consolidated.md
sims_and_scripts/               190 standalone top-level scripts; 46 are unregistered but visible
  out/                          scratch output of manifold_build_ladder.py
data_json/                      per-sim result data + rosetta_layer.json
figures/                        pre-rendered PNGs (do not regenerate)
engines/                        REAL-SUBSTRATE LANE: numpy oracle contract
                                (targets.json), JAX/torch/Julia engines,
                                validate_engines.py (own exit code; see
                                engines/README_LAPTOP.md). Saved Julia engine
                                receipts and the new exceptional Julia source
                                have separate provenance/status boundaries.
reference_docs/                 source docs the spec formalizes (provenance
                                tier: source/support, NOT audited claims)
inputs/                         owner's original source spreadsheet
```

## Orientation for the math itself
Read, in order: `archive/ORIENTATION.md` → `spec_and_reports/PURE_MATH_CORE.md`
(compact, label-free, P1–P11) → the spec sections you need. The pure core is
the fastest way to load the actual mathematics without absorbing overlay
vocabulary as if it were structure.

# 05 — Engine stages, loops, and cycles

Status: `exists` (this document) synthesising `passes local rerun`-tier receipts.
Every receipt cited below carries its own ceiling — `scratch_diagnostic` or
`UNOFFICIAL working sim`, `promotion_allowed: false` — and nothing here raises
that ceiling. Figures are read from the committed JSON receipts, not
re-executed in this session; every number below cites its source file.

## Bottom line

All four scripts read clean at their stated gate counts: `julia_manifold_tick.jl`
22/22, `jax_scale_lanes.py` 20/20, `torch_graph_drive.py` 15/15,
`manifold_qit_engines_full.py` 23/23 (all counted directly from the checks
blocks in their receipts; see section 2). But two fresh audits dated
2026-07-20 sit next to this evidence and change how it should be read:
`system_v8/nested_manifold/results/stage64/AUDIT_VERDICT.md` and
`system_v8/nested_manifold/results/RUNGS_ABCE_AUDIT_VERDICT.md`. Their
verdict, confirmed independently below: the raw pass counts are real, but
the 64-slot "engine ontology" itself is mostly unrun scaffold (16 of 64
candidate microsteps ever execute), the tournament that picks those 16 is a
construction identity that cannot fail on its own, and the headline
chirality-flux linearity (R² = 0.982) is a genuine, gated, checked number
that is nonetheless thin — 7 data points, one declared traversal, no
independent replication of the traversal choice itself. No artifact
matching "drop-one, 1920-delta" ablation exists anywhere in the repository;
that figure is addressed directly in section 7.

## 1. Two senses of "engine" in this stack

The word "engine" means two different things across the read set, and they
must not be merged.

- Compute-substrate engine: Julia, JAX, PyTorch — the three numerical
  backends under `system_v8/engine_native/`. Each is its own script, its own
  receipt, its own tool stack.
- Dynamical (chirality) engine: the Left / Right paired state-evolution
  engines that actually run inside `manifold_qit_engines_full.py`. The task
  brief's "E1/E2" and "8 macro-stages / 32 microsteps" language refers to
  this sense, and only `manifold_qit_engines_full.py` (qutip, on a single
  Python process) executes it. E1 = Left sheet, E2 = Right sheet, following
  the file's own `"L"` / `"R"` labels.

Julia, JAX, and PyTorch do not each run their own copy of E1/E2. Julia runs
its own, separately-declared 3-stage GKSL schedule (own constants, own
generators — see section 2). JAX's L14 lane recomputes the *selection*
tournament that decides E1/E2's operators, at scale, but does not run the
60-tick dynamics itself. PyTorch never touches the dynamical engines at all;
it works the drive/capacity side only. Collapsing these into one "the
engine" would misstate what each file does.

## 2. How well each compute-substrate engine computes

| Engine | File | Gates | Precision commitment | Load-bearing tools | What it actually computes |
|---|---|---|---|---|---|
| Julia | `system_v8/engine_native/julia_manifold_tick.jl` | 22/22 (`results/julia_manifold/receipt.json`) | `QuantumOptics.timeevolution.master`, adaptive, reltol 1e-10 / abstol 1e-12; BigInt exact integer arithmetic for the drive (no floating truncation, counts reach 75 decimal digits); independent MPS bond-cut entropy check agrees with `ptrace`/`entropy_vn` to ~1e-15 against a declared 1e-8 gate; outer Schur trace-functional residual = 0.0 exactly | QuantumOptics (state/generator/master/ptrace/entropy_vn), ITensors+ITensorMPS (independent cut check), BigInt (drive), LinearAlgebra (64x64 Liouvillian Schur elimination) | A 30-tick, own-convention 3-stage GKSL tick loop (depolarizing → dephasing → amplitude-damping, 10 ticks each) on a 2-sheet joint qubit pair, plus a Hartley-bits drive, a chi-loop relative-holonomy flux, and an ancilla-nesting Schur reduction |
| JAX | `system_v8/engine_native/jax_scale_lanes.py` | 20/20 (`results/jax_scale/receipt.json`) | float64 throughout; `diffrax.Tsit5` + PID controller, rtol 1e-10/atol 1e-12 (L13) and rtol 1e-9/atol 1e-11 (L15); K1 aligned-pair commutator norm stays ≤4.38e-16 (machine epsilon) across a 1600-point perturbation sweep; dual-SMT (z3 exact rationals + cvc5 QF_NRA) symbolic proof, not floating point | jax.jit/vmap (every lane), diffrax (9216 + 61 GKSL trajectories), z3 + cvc5 (K1 kill-set proof); numpy is control/timing-only everywhere, never load-bearing for a check | Four at-scale lanes: L13 a 16-mode entropy census (rungB grid: 8 generators × 2 sheets, 384 Bloch states × 64 time points, 9216 diffrax trajectories), L14 the 64-slot tournament re-run under 100×20 random frame perturbations, L15/L16 a 3-site × 20-magnitude response field on a 16×16 nested GKSL tower, L5 a 200-pair flux-holonomy sweep |
| PyTorch | `system_v8/engine_native/torch_graph_drive.py` | 15/15 (`results/torch_graph/receipt.json`) | `torch.set_default_dtype(float64)`; Fisher-metric Hessian matches the analytic `diag(1/p)` law to ≤1e-12 on all 9 packets; nested chain-rule identity `g_p = g_P + Σ_g P_g g_(p\|g)` matches to ≤1e-10 on both autograd sides; graph-derived vs direct-set drive counts match by exact integer equality, not tolerance | torch_geometric (prefix-trie and Hamming-1 graphs, Laplacian spectral gap), `torch.func.hessian` (exact Fisher metric and nested-chain autograd) | Not a dynamical engine at all. Builds capacity graphs (prefix trie, Hamming-1 graph) over the 9 source packets, derives a Hartley drive series from graph leaf-counts, computes an exact Fisher information metric and a nested chain-rule identity, then welds its own drive series against Julia's — explicitly marked not directly comparable (see section 6) |

Two precision notes worth carrying forward. First, Julia and JAX both
declare tight, explicit adaptive-ODE tolerances (1e-9 to 1e-12); the
dynamical engines inside `manifold_qit_engines_full.py` (section 3) call
`qt.mesolve(H, rho, [0.0, DT], c_ops=c_ops)` and `qt.steadystate(H, c)` with
no `options=` override, so that lane runs on qutip's library-default
integrator tolerance, undeclared in the script. The physicality gates still
pass there (min eigenvalue > -1e-10, trace error < 1e-9 across every run,
per `full_sim/receipt.json`), so the default is evidently sufficient for
those particular gates, but the precision commitment is a full tier looser
and unpinned compared with the engine-native lane. Second, PyTorch's own
family labels stay neutral (`family_0`..`family_3`, not "Se/Ne/Ni/Si" or any
Jungian/IGT vocabulary) — consistent with the constraint_core doctrine that
sims carry structural indices only and naming lives in a separate rosetta
layer (`system_v7/constraint_core/CLAUDE.md`, rule 4). None of the four
scripts read here violate that discipline.

## 3. E1/E2: what the 8 macro-stages and 32 microsteps compute

Source for the ontology: `system_v7/constraint_core/reference_docs/engine_math/ENGINE_64_SCHEDULE_ATLAS.md`
("Scaffold chart... Not runtime closure. Not final authority. Earned by
chart alignment, not by proof," dated 2026-03-27). Its invariants table
(section 12) declares: 4 terrain families, 8 macro-stages per engine (4
families × 2 loops), 32 microsteps per engine (8 macro-stages × 4 candidate
operators), 64 total microsteps (2 engines × 32).

The only file in the read set that executes this ontology end to end is
`manifold_qit_engines_full.py`, via `system_v8/nested_manifold/stage64_constraint_tournament.py`'s
committed receipt (`results/stage64/receipt.json`). Stage64 realises the
atlas grid exactly: "4 terrain families × 2 sheets × 2 loop fields = 16
stages [total macro-stage realisations across both spinors]; 4 candidate
(D_a, H_b) pairs each = 64 candidates." That is 8 macro-stages per sheet ×
2 sheets = 16, matching the atlas; 4 candidates per macro-stage × 16 = 64
candidates total, matching the atlas's "total microsteps."

Terrain family parameters (`TERRAINS` dict, same in `stage64_constraint_tournament.py`
and `manifold_qit_engines_full.py`):

| Family | omega | gamma | frame_sign |
|---|---|---|---|
| family_0 | 1.0 | 0.20 | +1 |
| family_1 | 0.7 | 0.35 | −1 |
| family_2 | 1.3 | 0.15 | +1 |
| family_3 | 0.9 | 0.50 | −1 |

E1 (Left) and E2 (Right) macro-stage order, with the operating pair each
stage runs, from `full_sim/receipt.json`'s `inputs.left_engine_order` /
`right_engine_order` and `data.operating_pairs`:

| Slot | E1 (Left) stage | Operating pair | E2 (Right) stage | Operating pair |
|---|---|---|---|---|
| 1 | family_0, f+1 | D_z\|H_x | family_3, f−1 | D_x\|H_z |
| 2 | family_1, f+1 | D_x\|H_z | family_2, f−1 | D_z\|H_x |
| 3 | family_2, f+1 | D_z\|H_x | family_1, f−1 | D_x\|H_z |
| 4 | family_3, f+1 | D_x\|H_z | family_0, f−1 | D_z\|H_x |
| 5 | family_0, f−1 | D_z\|H_x | family_3, f+1 | D_x\|H_z |
| 6 | family_1, f−1 | D_x\|H_z | family_2, f+1 | D_z\|H_x |
| 7 | family_2, f−1 | D_z\|H_x | family_1, f+1 | D_x\|H_z |
| 8 | family_3, f−1 | D_x\|H_z | family_0, f+1 | D_z\|H_x |

E2's 8-slot sequence is the exact reverse of E1's (slot *i* of E2 =
slot 9−*i* of E1, same family, same flux, same operator label). This is a
verified structural fact, not an approximation — confirmed by direct
comparison of the two order lists in the receipt. The operating-pair label
itself depends only on the family's `frame_sign` parity (family_0/2 →
`D_z|H_x`, family_1/3 → `D_x|H_z`), not on sheet or flux sign; what
actually differs between a mirrored E1/E2 slot pair is the realised
Hamiltonian sign, `H = s·f·omega·sigma_b` with `s=+1` for E1 and `s=−1` for
E2 — same basis, opposite sign, at each mirrored position.

Nominal vs executed microsteps — this is a precision point worth being
exact about. "32 microsteps per engine" in the atlas is the size of the
*candidate selection grid* (8 macro-stages × 4 candidate operator pairs),
not 32 sequential runtime steps. `manifold_qit_engines_full.py` executes
exactly one `qt.mesolve` GKSL step per macro-stage per tick — 8 executed
generator-steps per engine per full 8-tick cycle, using whichever operator
`stage64`'s tournament already selected. The other 3 candidates per
macro-stage (24 per engine, 48 across both engines) are never stepped by
the runtime; they are selection-time walls, not skipped runtime work. See
section 7 for exactly how many of the 64 are load-bearing in any sense.

## 4. The two loops per engine (outer/inner)

The atlas's own framing (`ENGINE_64_SCHEDULE_ATLAS.md`, sections 0 and 0B):
8 macro-stages per engine split into an inner loop — the Hopf fiber loop,
U(1) fiber circulation, 4 stages — and an outer loop — the lifted base
loop, a horizontal loop on S³, 4 stages. Both loops visit all 4 terrain
families once each; chirality/flux "orients all stages together" without
creating new base stages, per the atlas's own read of the owner source.

This is a chart-level claim, not a runtime-closed one, and the atlas says
so explicitly in its own Hard Non-Claims (section 13): "Ax3 is not closed
by this atlas" and the correlation between outer/inner and the executed
code's own axes (chirality sheet, flux sign) is an open alternative, not a
settled identity. Neither `stage64_constraint_tournament.py` nor
`manifold_qit_engines_full.py` labels anything "outer loop" or "inner
loop" in code; both compute a 4-terrain-family × 2-flux-sign grid (`f =
±1`) and leave the outer/inner identification to the atlas's prose only.
Holding that divergence rather than collapsing it: the atlas's own
strongest documented candidate for the outer/inner split is the executed
`f=+1` / `f=−1` halving (each half sweeps all 4 families once, matching
"4 stages" per loop), but this identification is not proven, and an
equally-live alternative in the atlas's own text is that chirality
(sheet L/R) rather than flux is the outer/inner axis. Do not read section 3's
table as having settled this; it has not.

What is settled, because it is a direct algebraic consequence of the
code (`stage64_constraint_tournament.py::make_candidate`, confirmed against
the receipt's `k1_commutator_norms` and `operating_pairs`): flux sign does
not change which operator basis wins the tournament (K2's argmax runs on
`frame_sign * orient`, independent of sheet and flux; K3's admitted-flux
check reduces to `chi == sheet_s` regardless of `f`, because the circulation
sign scales as `s·f²=s`). Flux sign flips only the sign of the realised
Hamiltonian term at a given family/sheet, not the selection outcome. So
whichever of the two live readings ("f is outer/inner" vs "sheet is
outer/inner") turns out correct, the two `f=±1` visits to the same family
are guaranteed by construction to run the identical operator label with an
inverted Hamiltonian sign — a genuine, receipt-checkable fact, distinct from
the unproven outer/inner-loop identification layered on top of it.

## 5. Engine cycles: the 64 pair-total, opposite order, and order-as-content

The 64 pair-total is the same object as section 3's candidate grid: 16
macro-stage realisations (8 per engine × 2 engines) × 4 candidate
(dissipator, Hamiltonian) pairs each = 64. Of these, `stage64`'s tournament
admits exactly 1 operating pair per macro-stage (16 total), and
`manifold_qit_engines_full.py` runs those 16 across a 60-tick simulation:
both E1 and E2 step every tick (`t = 0..59`), each indexing its own 8-slot
order by `t % 8`, then the two sheets are coupled by a fixed XY pulse
(`U = exp(-i·g_c·(XX+YY)·tau_c)`) once per tick. 60 ticks / 8 = 7 complete
per-engine macro-stage cycles, plus 4 ticks of an eighth, partial cycle.

Opposite-order cycling: verified exactly in section 3's table. E2's macro-
stage sequence is the literal reverse of E1's, not merely "a different"
order.

`U_R(cycle) = U_L(cycle)^{-1}` under interleaving: this claim appears in
the script's own docstring, scoped explicitly to "the unitary level." It is
structurally derivable, not an empirical mystery: because `H = s·f·omega·
sigma_b` and E2 uses `s=-1` at every mirrored slot where E1 uses `s=+1`,
the Hamiltonian at each mirrored slot is exactly negated, so
`exp(-i·H_R·dt) = exp(-i·H_L·dt)^{-1}` exactly at that slot; composing
those factors in reversed order gives the literal group inverse for the
coherent-only idealisation. But the actually-executed per-tick step is a
full `qt.mesolve` with dissipative `c_ops` (the selected jump operator,
scaled by `gamma_eff`), not a bare unitary — a CPTP channel is generally
not invertible as a CPTP channel, so the full per-tick map does not literally
satisfy this identity, only its coherent factor does. No check in
`full_sim/receipt.json` verifies `U_R(cycle)·U_L(cycle) = I` as a matrix
identity; the closest gated evidence is the weaker, scalar
`flux_opposite_sign_every_cycle` check (sign of the per-cycle Pancharatnam
phase is opposite on every one of the 7 complete cycles — true in the main
run). Status: a structurally well-motivated, partially-derivable claim
about the coherent factor only, asserted in prose, not independently gated
as a matrix identity.

Order-is-content, the honest negative: kept at
`system_v8/deep_integration/results/full_sim_run1_receipt_order_flux_negative/receipt.json`.
Under the raw, undeclared `stage64` receipt order (each family's `f=+1`
and `f=-1` stages adjacent), `all_pass: false`, specifically
`flux_opposite_sign_every_cycle: false`,
`flux_split_grows_linearly_r2_ge_0.98_slope_gt_1e-3: false`, and a terrain-
distinctness gate also failing. The docstring's mechanism is geometric:
same-axis, opposite-angle rotations sitting adjacent compose close to the
identity, so both engines' cycle monodromies go near-trivial and the
chirality split degenerates. One caveat found independently while reading
both receipts side by side, not stated in either docstring: run1 also used
a different tick length (`dt=0.5` vs the main run's `0.35`) and a different
coupling strength (`g_c=0.35` vs `0.125`) — the receipted contrast changes
three things at once, not order alone. The geometric argument for why raw
order degenerates monodromy is independently plausible and does not depend
on `dt`/`g_c`, but the specific receipted numbers (R²=0.44 vs R²=0.982)
should be read as "declared traversal + tuned parameters passes; one
earlier raw-order + earlier-parameter configuration failed," not as an
isolated single-variable ablation of order alone.

## 6. Genuine vs by-construction — the 2026-07-20 audits

Two fresh, dated audit files sit next to this evidence and directly bear on
how the above should be read. Both are cited in full below; nothing here
paraphrases past the point of losing the distinctions they draw.

`system_v8/nested_manifold/results/stage64/AUDIT_VERDICT.md`: the `stage64`
receipt's own 11/11 `all_pass` is tainted as a standalone admission — every
gate is a construction identity that cannot fail (K1's "exactly 2 killed of
4" is a fixed diagonal identity of a 2×2 aligned/misaligned commutator
grid, confirmed stable across a 900-combination sweep; K2's "exactly 1
admitted" is a deterministic argmax over 2 survivors; K3's flux-match is
automatic because circulation sign reduces to the sheet sign for both
survivors regardless of flux). The receipt was honestly ceilinged (frame
sign is declared, not derived) but `all_pass=11/11` should not be read as a
tournament having discovered anything by itself. The audit also flags and
corrects a separate stale figure: a "0.885 rad stability" number once
attached to `stage64` is misplaced — `stage64` runs no perturbation sweep at
all. The genuine, can-fail version of that claim lives in
`jax_scale_lanes.py`'s L14 lane instead: `min_breaking_threshold = 1.152`
rad, `median_breaking_threshold = 1.5` rad (the sweep's own ceiling), 320 of
1600 (direction, stage) pairs break somewhere in [1.15, 1.5] rad, 1280
never break inside the tested range, and the aligned-pair commutator norm
stays at ≤4.38e-16 across the entire sweep — corroborated by an independent
symbolic proof (dual z3 + cvc5, exact rationals, 8/8 UNSAT) that the aligned
commutator is exactly zero as algebra, not a floating-point coincidence
(`jax_scale/receipt.json`, `L14_stability` and
`L14_K1_kill_set_structurally_exact_dual_smt`). What is genuinely
evidentiary about `stage64`, per this audit, is not its own 11/11, but (a)
an independently-written JAX recomputation reproducing the same 16
operating pairs at zero perturbation, and (b) that reproduction surviving a
real, non-trivial 1600-point randomised stress test.

The same audit gives a clean verdict, with one explicit caveat, to the
chirality-flux linearity claim central to section 5: "full_sim chirality
split (measured, kept negative proves gates can fail; R² linearity oversold
but honest)." Read plainly: the R²=0.982 number is real, gated, and
computed from an actual executed run, and the kept run1 negative is
independent proof the gate can fail — this is not a rigged test. But it is
thin evidence for a general law: 7 cycle-level data points (56 of 60
ticks), one declared traversal, and its very existence is conditional on
having already picked the traversal that avoids degeneracy (section 5). Do
not cite "R²=0.982" as a proven linear law of the schedule; cite it as "one
declared 60-tick run's per-cycle flux split fits a line well," full stop.

The same audit notes two specific "0-0" decorative controls inside
`jax_scale_lanes.py`, at lines 857-862 (`L15_static_control_flat`, which
computes `eigvalsh(rb0 - rb0)` — an array subtracted from itself, so the
result is the zero matrix by construction, not by any property of the
engine) and lines 976-980 (`L5_flatten_pairs_exactly_zero`, which evaluates
the flux function at `eta1 == eta2`, so the two terms cancel identically
regardless of the flux law). Both checks are legitimate in spirit — the
standard "does the diagnostic read zero on a trivially symmetric input"
control — but structurally cannot fail, so they contribute nothing to the
20/20 gate count's evidentiary weight even though they are counted in it.

`system_v8/nested_manifold/results/RUNGS_ABCE_AUDIT_VERDICT.md`: separately
flags that the "rungB 16-grid: 8 generators × 2 sheets" framing —
`jax_scale_lanes.py`'s own docstring language for its L13 census — overstates
independence. The right sheet is forced to be the conjugate of the left by
construction (confirmed directly in `lane_L13`: `rho0_R = rho0_L.conj()`,
and for the right sheet `H, Ls = -H.conj(), Ls.conj()`), so the 16-mode
table (14 populated, 2 honest gaps) carries 8 independent generator
behaviours mirrored once, not 14 independently-discovered ones. The same
left/right-by-conjugation convention appears in `julia_manifold_tick.jl`'s
own joint Hamiltonian (`op2(H_L, I2m) + op2(I2m, -H_L)`) and jump-operator
bank — it is a repo-wide convention, not an isolated JAX-lane choice, and
should be read that way everywhere the "2 sheets" language appears.

What both audits confirm as genuinely can-fail, kept, and not
by-construction: `full_sim`'s C1-C4 controls (freeze drive, scramble
schedule, erase chirality, decouple engines — each a directional prediction
checked numerically, in `full_sim/receipt.json`); the run1 order-flux
negative itself (section 5); Julia's own freeze-damping metric correction
(the entropy-step gate failed honestly on a first attempt, kept at
`results/julia_manifold_run1_freeze_metric_negative/`, then replaced with a
trace-distance contraction gate that is the principled observable for a
fixed positive trace-preserving map); PyTorch's weld-honesty gate
(`weld_not_falsely_claimed_comparable`, a check written specifically to
force an honest non-claim rather than let two structurally different drive
series be silently treated as comparable); and the JAX L14 perturbation
sweep and dual-SMT proof described above.

One further precedent, found independently in `system_v7/constraint_core`
while locating the atlas (not part of the audit files, but the same failure
mode, caught earlier): `sims_and_scripts/engine_64_schedule_sim.py` carries
a 2026-07-08 self-correction withdrawing its own prior claim that an
order-sensitive readout "lifts uniqueness to 64/64" — the withdrawal notes
that claim counted distinct output signatures across all 64 slots, which
differ automatically because every slot already has a different
terrain/operator; that is distinctness by construction, not evidence that
order does unique work. What survived that correction and is still live:
an order-blind coarse readout collapses 64 slots to 11 distinguishable
classes (kept, an honest failure by design), and a narrower, well-posed
test — holding engine, terrain, and operator fixed and varying only
composition order — finds 16 of 16 tested slots order-carried (non-zero
order gap). The broader 64-slot position-uniqueness question stays
explicitly open (`system_v7`'s own `slot64` probe: 12/32 matched pairs
position-unique, 20 untestable, a named instrument gap, per
`system_v7/constraint_core/CLAUDE.md` rule 6).

## 7. Report back

How many of the 64 microsteps are genuinely load-bearing: no artifact
named or shaped "drop-one, 1920-delta" exists anywhere in this repository.
Searched directly: `drop-one`, `drop_one`, `ablat` (case-insensitive) across
`system_v7` and `system_v8`; the literal token `1920` across the whole repo;
and every audit/AUDIT_VERDICT file touching this ontology. No hit ties any
such figure to the 64-microstep engine grid. `stage_necessity_ablation_sim.py`
in `system_v7/constraint_core` is a real drop-one-style ablation, but it
tests a 16-object perception-binding task, an unrelated object — citing it
here would misattribute it.

What does exist, and answers the underlying question with real numbers,
is `stage64_constraint_tournament.py`'s own deletion test — a genuine
ablation over the same 64-candidate grid, kept in
`results/stage64/receipt.json`:

| Role | Count of 64 | What removing it does |
|---|---|---|
| Operating (selected, executed by `full_sim`) | 16 | Directly load-bearing: this is the dynamics that runs |
| Rejected W-conjugate partner (never executes) | 16 | Selection-load-bearing, not dynamics-load-bearing: deleting it removes K2's comparison, so all 16 stages become under-determined (`deletion_partner_under_determined`: true for all 16) |
| K1-killed (order-blind, zero circulation) | 32 | Provably outcome-inert: deleting a K1-killed wall leaves the operating pair unchanged in all 16 stages (`deletion_killed_wall_outcome_unchanged`: true for all 16) |

So: 16/64 (25%) are the executed dynamics; a further 16/64 matter only to
keep the selection rule determinate, never run themselves, and would break
the tournament's logic (not the physics) if removed; the remaining 32/64
(50%) are demonstrated, by an actual executed deletion test, to be inert —
removing them changes nothing about which operator runs. Caveat carried
from section 6: this deletion test's individual gates are themselves
construction identities of a fixed 2×2 commutator grid (they cannot fail
given the algebra), so "32 are provably inert" is a sound arithmetic fact
about this specific candidate structure, not evidence that the tournament
mechanism itself was ever at risk of failing. It answers "how much of the
64-grid is dead weight" honestly; it does not answer "could the tournament
have picked differently," because it structurally could not.

Which engine-cycle claims are audited genuine vs oversold, summarised from
section 6:

Genuine (survived a check that could have failed): the JAX L14
1600-point perturbation sweep and its 1.152 rad breaking threshold; the
dual z3+cvc5 exact proof of the K1 kill-set; `full_sim`'s C1-C4 controls;
the run1 order-flux negative (with the dt/g_c caveat now attached); Julia's
freeze-damping metric self-correction; PyTorch's weld-honesty gate;
`engine_64_schedule_sim.py`'s 16/16 matched-content order-carriedness
result and its 11-class order-blind collapse.

Oversold or by-construction (real code, real numbers, but cannot fail or
overstates independence): `stage64`'s own 11/11 all_pass as a standalone
"tournament earned this" claim; the chirality-flux R²=0.982 linearity, real
and gated but thin (7 points, one declared traversal, conditional
existence) — cite as one run's fit, not a law; the two 0-0 decorative
controls in `jax_scale_lanes.py` (lines 857-862, 976-980); the "16-mode"
/"rungB 16-grid" framing in both `jax_scale_lanes.py`'s L13 and
`julia_manifold_tick.jl`'s joint Hamiltonian, where the right sheet is
forced to be the left sheet's conjugate by construction, so only 8
generators carry independent content; and the withdrawn 2026-07-08
"64/64 order-sensitive" claim in `system_v7/constraint_core`'s
`engine_64_schedule_sim.py`, kept here as the direct precedent for the same
failure mode the 2026-07-20 audits caught again in v8.

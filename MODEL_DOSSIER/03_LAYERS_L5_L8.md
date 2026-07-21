# Model dossier 03 — constraint-core layers 5 to 8: operators, stage schedule, axes, cuts and Schur co-view

Bottom line. Layers 5 to 8, in the component ledger's own numbering, are: the four
operators and their two-native-per-terrain admissibility law (5); the 16-stage / 64-slot
schedule built from those operators (6); the seven axes read as degrees of freedom over
the whole carrier (7); and entropy read as a co-view of the same distinction surface,
worked out concretely through joint-state cuts and a Schur-complement nesting witness (8).
Layers 5 and 7 carry only the 2026-07-01 ledger grade (`EARNED`, fixture-local scope); no
2026-07-20 fresh-context audit in the materials read for this file touches either one.
Layer 6's own 2026-07-19 executable re-test — `stage64_constraint_tournament.py` — is
`TAINTED` as a standalone admission: all 11 declared gates are construction identities
that cannot fail. Layer 8 splits: the Schur-nesting half (`rungD_schur_nesting.py`) is
`CLEAN`, with three of its four checks genuine and can-fail; the cuts half
(`rungC_joint_cuts.py`) is mixed, two of its six checks by-construction and four genuine.
None of this promotes anything. Every file cited below carries `promotion_allowed: false`
and `formal_admission_allowed: false` in its own receipt, and this dossier adds no new
computation — it compiles and cross-cites what already exists on disk.

## 1. Scope and sources

This file was built for one task: read `system_v7/constraint_core/MODEL_LAYER_LEDGER.md`
layers 5 to 8, plus three `system_v8/nested_manifold` files the task named directly, and
turn the two into one cross-cited reference. Sources read in full this session:

- `system_v7/constraint_core/MODEL_LAYER_LEDGER.md`, lines 1–22 (status key and the two
  standing audit notes), 82–233 (Layer 4 through the start of Layer 10, which covers Layers
  5–8 verbatim plus the immediate Layer-4 substrate and Layer-9/10 forward pointers needed
  to read them correctly), 730–787 (the open-items list, the terrain-level a2 addendum, and
  Layer 0.3's signed coherent-information primitive, which Layer 8's cut functional
  reuses).
- `system_v8/nested_manifold/stage64_constraint_tournament.py` (full file).
- `system_v8/nested_manifold/results/stage64/AUDIT_VERDICT.md` (full file, one paragraph).
- `system_v8/nested_manifold/rungC_joint_cuts.py` (full file).
- `system_v8/nested_manifold/rungD_schur_nesting.py` (full file).
- Read for cross-check, not named in the task but needed to grade rungC honestly and to
  place rungD in its build sequence: `system_v8/nested_manifold/results/stage64/receipt.json`,
  `.../results/rungC/receipt.json`, `.../results/rungD/receipt.json` (all parsed field by
  field, not grepped for strings), `system_v8/nested_manifold/results/RUNGS_ABCE_AUDIT_VERDICT.md`
  (full file), and the opening docstrings of `rungA_carrier_to_flux.py`, `rungB_sheets_sixteen.py`,
  `rungE_response.py` (first ~60 lines each, for grid/lineage context only).
- Read for provenance: `git log` and `git show --stat` against
  `system_v8/nested_manifold/` and `MODEL_LAYER_LEDGER.md`. No sim was re-executed this
  session; every receipt cited below is read from the file already on disk, not
  regenerated. Per this repo's status ladder, that puts every v8 number in this file at
  `runs` (a completed execution, whose output was read directly, field by field) rather
  than `passes local rerun` (which would require this session to have executed the script
  itself). The output directories (`results/stage64/`, `results/rungC/`, `results/rungD/`)
  are guarded by a refuse-to-overwrite check in each script (`if OUT.exists(): raise
  SystemExit(...)`), so a same-session rerun was not attempted; it would first require
  deleting evidence files this dossier depends on.

Two adjacent things are out of scope and are not folded in here. `MODEL_DOSSIER/07_RATCHET_ACTUAL_STATE.md`,
written earlier in the same session by a separate task, covers a different lane entirely —
the `fuel_gate/` → `bridge_action_predictive.py` → `ratchet_contract/gates.py`/`mss.py`
pipeline — and says so explicitly in its own scope section. This file is the "separate,
older lane with its own L1–L8 status report" that document names and deliberately does not
open. Second, the ledger's own `MANIFOLD SPINE RATCHET` sub-ladder (its own L1–L8, built
2026-07-09, geometry-only: probe-quotient floor, density-rank strata, spinor/phase surface,
local Weyl factors, nested-shell Schmidt strata, BKM metric, shell connection, Chern
bundle) is a different, same-numbered object from the component ledger this file
reports on. It is named once, in §2 below, so it is not silently conflated with this file's
Layer 5–8, and is not otherwise expanded here.

## 2. Terminology this file will not silently collapse

The repo's own status-ladder rule (`exists < runs < passes local rerun < canonical by
process`, never imply a higher grade from a lower one) and its anti-collapse rule
(preserve divergent readings; do not merge them for tidiness) both bind this file. Four
naming or construction frictions turned up while reading the cited materials. Each is
named once here and referenced by its tag (T1–T4) below, rather than re-argued every time
it recurs.

T1 — three unrelated "Layer N" ladders share the numerals 5 through 8.
1. The component ledger this file reports on (`MODEL_LAYER_LEDGER.md`'s banner-headed
   `# LAYER 5 —` … `# LAYER 8 —` sections): operators, stage schedule, axes, co-view. This
   is what "Layer 5–8" means everywhere in this file unless stated otherwise.
2. The same ledger file's separate `MANIFOLD SPINE RATCHET` addenda (built 2026-07-09,
   `UP-123` through `UP-127`): L5 = nested-shell Schmidt strata, L6 = the BKM metric, L7 =
   the shell connection / Berry holonomy, L8 = the global bundle / Chern quantization. The
   ledger's own `RATCHET_V0_6_EXECUTED_MANIFOLD_AUDIT` note (lines 17–22) is about this
   ladder, not the component ledger: "L1–L8 pass local rerun, but zero scientific manifold
   layers are admitted. In particular: L5 named-shell MSS is unsupported; radial data
   cannot select BKM uniquely; the L6 marginal entropy object erases L7's phase direction;
   Chern orientation has no implemented physical-chirality bridge." None of that caveat is
   about this file's Layer 5–8; it is quoted here only so a reader who finds it elsewhere in
   the same file does not misapply it to the wrong ladder.
3. `rungC_joint_cuts.py`'s own docstring self-labels its joint-state-cut material `(L7)` —
   a third, v8-era, single-file numbering that names neither the component ledger's Axis
   layer nor the manifold-spine's Berry-holonomy layer. It is read in this file as Layer
   8 material (cuts/Schur co-view), per the task's own framing, not as a claim about either
   older L7.

T2 — at least three unrelated objects in this repo are called "64." (a) The v7 sim
`engine_64_schedule_sim.py` (not read this session; its finding is named and protected by
`system_v7/constraint_core/CLAUDE.md` rule 2, which this dossier has direct access to and
quotes rather than independently re-verifies): an order-blind readout collapses 64 to 11,
and `CLAUDE.md` states plainly that "the collapse is the point" — it must stay a failure,
not be smoothed into a pass. (b) The ledger's own Layer 6.5/6.6 "live-runtime 64 = 2×8×4
slot space" reading, itself flagged `CONTESTED` against a rival chart-atlas 64 = 8×8 reading
and a hexagram 64 = fenced tag family, unresolved as an owner-only decision (`O4`). (c)
`stage64_constraint_tournament.py`'s own executed 16-stage × 4-candidate = 64 tournament
grid (2026-07-19, audited tainted 2026-07-20) — see §5. All three are real, on-disk,
independently addressable objects. None of them is simply "the same 64" as another;
treating them as interchangeable would be exactly the sequence-collapse the project's
kernel rules forbid.

T3 — stage64's own "16 stages" is a different factorization of 16 from the ledger's
"16 stages." Ledger 6.1: 16 = 8 named terrains (`t0`…`t7`) × 2 native operators per
terrain. `stage64_constraint_tournament.py`'s `TERRAINS` list has 4 generic entries
(`family_0`…`family_3`, each carrying its own `omega`/`gamma`/declared frame sign — not the
8 named terrains) × 2 sheets (`L`,`R`) × 2 loop fields (`+1`,`-1`) = 16. Both equal 16;
neither is built from the other. §5 works this through in full.

T4 — stage64's dissipative candidates are relaxation-type, not the dephasing-type
operators Layer 5 names `Ti`/`Te`. Layer 5.1–5.2 name `Ti`/`Te` as sigma_z/sigma_x
dephasing generators. `stage64_constraint_tournament.py`'s own docstring names its `D_a`
as "jump sqrt(gamma) * lowering-in-basis-a" and its code builds the jump operator as
`SM = |0><1|` (a relaxation/lowering operator, commented "decay toward +z" in the source),
W-conjugated for the x-basis version. A lowering jump is the Layer-4 damping-terrain
generator family (`t0`/`t2`/`t4`/`t6`: `damp(sigma+)`/`damp(sigma-)`, non-unital), not
Layer 5's own dephasing pair. Stage64's unitary side does match Layer 5 exactly: its
`H_z`, `H_x` are plain `sigma_z`/`sigma_x`-axis rotation generators, the same form as `Fe`
(sigma_z rotation) and `Fi` (sigma_x rotation). So stage64 re-executes Layer 5's
admissibility logic (commutation-exclusion, Hadamard W-conjugacy, frame-sign selection)
and its unitary generator family exactly, on a different (relaxation-type, Layer-4-style)
dissipative generator family than the one Layer 5 names. §4 and §5 carry this distinction
through rather than treating stage64 as a literal Layer-5 rerun.

Status vocabulary used below runs two systems side by side, deliberately not merged. The
ledger's own grade (`EARNED` / `CANDIDATE` / `OPEN`) is quoted as the ledger states it, with
its own standing caveat carried every time: per the ledger's `RATCHET_V0_5_ORDER_OPEN_PROCESS`
note, "`EARNED` … means the named equation, computation, or fixture behavior was reproduced
at its stated installed scope. It does NOT mean globally forced … or permanently
canonical." Separately, this repo's four-label status ladder (`exists < runs < passes local
rerun < canonical by process`) grades what this session itself did with each artifact.
Verbs follow the harness convention: a check admits, excludes, or is consistent with
a reading; nothing in this file "proves," "causes," or "determines" in the banned sense.

## 3. Summary table

| Layer | Geometry/algebra object + formula | Entropy functional + formula | Formal names | Nicknames/jargon | SIM STATUS (receipt + genuine-vs-tainted, cited) |
|---|---|---|---|---|---|
| 5 — the 4 operators + 2‑native‑per‑terrain law | Two dephasing dissipators and two rotation unitaries on one qubit, built from `{sigma_z, sigma_x}`; `W=(sigma_x+sigma_z)/sqrt2` conjugates the pair `{Ti,Fe}` into `{Te,Fi}` (both same-axis, excluded) and leaves the cross-axis survivors `{Ti,Fi}`, `{Te,Fe}` W-conjugate to each other. See §4. | No dedicated entropy functional at this layer. Carries forward: dissipation rate lambda (`Ti`~0.69, `Te`~0.73) and the non-unitality operator norm `\|\|L(I)\|\|=sqrt2` (4 of 8 terrains), both entropy-production inputs realized downstream (Layer 11). | GKSL dissipator, unitary rotation generator, commutator-exclusion constraint (C2), Hadamard/W-covariance theorem. | `Ti`/`Te`/`Fi`/`Fe` (the ledger's own structural indices, not this file's gloss — see §4), "native operator," "signed Axis‑6/Axis‑2 law." | Ledger `EARNED`, `admissibility_two_operator_sim.py`, dated 2026-07-01 in the ledger header. No 2026-07-20 fresh-context audit in the materials read for this file touches this sim directly. `stage64_constraint_tournament.py` re-executes the same W-conjugacy/exclusion logic on a different dissipator family (T4) and is itself graded in row 6, not here. |
| 6 — the 16 stages and the 64 schedule | 16 = 8 terrains × 2 native ops (ledger 6.1) or 4 terrain families × 2 sheets × 2 loop fields (stage64's own grid, T3); 64 = 16 × 4 candidates, regroupable as 2 engines (sheets) × 32, 32 = 8 macro-stages (family × field) × 4 microsteps (candidate pair). See §5. | No dedicated entropy functional. The layer's own witnesses are algebraic/geometric: GKSL superoperator commutator norm `\|\|[D,H]\|\|_F` and Bloch circulation `(r × dr/dt)·(f·e_b)` evaluated at the dissipative fixed axis. | Mutual-constraint tournament, superoperator commutator, W-conjugate survivor pair, frame-sign admissibility (K2), chirality-consistency check (K3), deletion/counter-probe test. | "Walls" (48 non-operating candidates), "survivors," "operating pair," "macro-stage" (used at two different granularities, T3), "hexagram" (ledger 6.6's own term). | `TAINTED` as a standalone admission. `stage64_constraint_tournament.py`, receipt at `results/stage64/receipt.json` (`all_pass: true`, 11/11 checks), audited in `results/stage64/AUDIT_VERDICT.md` (2026-07-20, commit `a95b859ce`): "All 11 gates are construction identities that CANNOT fail." Full detail and the receipt's own corroborating numbers in §5. |
| 7 — the 7 axes | Axis‑0 through Axis‑6 read as DOF bipartitions over the same carrier. Axis‑1 = `{dissipative: Se,Ni}` \| `{unitary: Ne,Si}` (eigenvalue sector). Axis‑2 = `{direct: Se,Ne}` \| `{conjugated: Ni,Si}` (eigenvector sector). Axis‑6 sign law `b6 = -b0*b3`, 0/8 violations. See §6. | `S(rho) = -Tr[rho log2 rho]` (von Neumann entropy, bits). Axis‑1 (the ledger's own term: "the ENTROPY charge") acts on this functional's eigenvalue sector; Axis‑2 (the "PHASE charge") acts only on eigenvectors and leaves `S(rho)` unchanged — measured residual 2e-15. | Eigenvalue/eigenvector sector split, DOF orthogonality, signed axis law, tense/loop-order reversal (Axis‑4). | "Entropy charge" (Axis‑1), "phase charge" (Axis‑2) — the ledger's own terms. | Ledger `EARNED` (7.1–7.6), same 2026-07-01 fixture-local scope as row 5. No v8 `nested_manifold` rung in the materials read for this file names "the 7 axes" as its own executed object, and no 2026-07-20 fresh audit touches this row. This is an open evidence gap, named as a gap in §7, not filled by inference from rows 6 or 8. |
| 8 — cuts / Schur co-view | `rho_LR` on `C^2 (x) C^2` (rungC); a 4-level GKSL Liouvillian partitioned inner/outer, eliminated exactly by `L_eff = L_II − L_IO·L_OO^-1·L_OI` (rungD, the task's "0.43 witness," measured 0.4273). See §7. | `I(L:R)=S_L+S_R-S_LR` (mutual information); `S(L\|R)=S_LR-S_R` (conditional entropy); `I_c=-S(L\|R)` (coherent information = negative conditional entropy, re-using ledger Layer 0.3's own `I_c=-S(A\|B)` sign convention); `N(rho)=sum\|neg. eigs of rho^T_R\|` (negativity); `Phi0=(1/2)I_c(L\|R)+(1/2)I_c(R\|L)`; `Phi_k=-Tr[D_k(rho_ss) ln(rho_ss)]` (per-channel entropy flux, rungD). Full numbers in §7. | Umegaki relative entropy, GNS/modular Hamiltonian, data-processing inequality, mutual/conditional/coherent information, negativity (Peres–Horodecki/PPT), Schur complement, Liouville superoperator, Bures distance/Uhlmann fidelity. | "Co-view" (ledger's own Layer‑8 title term), "cut" (rungC), "nesting-matters witness," "inner/outer layer," "walls" does not apply here (that is row 6's term only). | Split, not one verdict. `rungD_schur_nesting.py`: `CLEAN` — checks `D1`/`D3`/`V1` genuine and can-fail via the `D2` control; `D4` explicitly excluded from load-bearing status (`results/stage64/AUDIT_VERDICT.md`, 2026-07-20, commit `a95b859ce`). `rungC_joint_cuts.py`: `TAINTED-with-surviving-core` — checks `C4`/`C6` by-construction Schmidt identities (cannot fail); `C1`/`C2`/`C3`/`C5` survived a real attack (`results/RUNGS_ABCE_AUDIT_VERDICT.md`, 2026-07-20, commit `051943694`). Ledger 8.1/8.2 itself: `EARNED`, 2026-07-01, no fresh audit. |

## 4. Layer 5 in full — the 4 operators and the 2‑native‑per‑terrain law

### 4.1 The four generators

| Index | Ledger row | Type | Formula | Reported rate/residual |
|---|---|---|---|---|
| `Ti` | 5.1 | Dissipative, z-basis dephasing | `D[sigma_z](rho) = lambda(sigma_z·rho·sigma_z − rho)` (standard single-jump GKSL dissipator with `L=sqrt(lambda)·sigma_z`) | `lambda ~ 0.69`; "destroys Z-coherence" |
| `Te` | 5.2 | Dissipative, x-basis dephasing | `D[sigma_x](rho) = lambda(sigma_x·rho·sigma_x − rho)` | `lambda ~ 0.73`; "destroys X-coherence" |
| `Fi` | 5.3 | Unitary, x-axis rotation | `R_x(theta)·rho·R_x(theta)^dagger`, `R_x(theta)=exp(-i·theta·sigma_x/2)` | preserves purity (unitary by construction) |
| `Fe` | 5.3 | Unitary, z-axis rotation | `R_z(phi)·rho·R_z(phi)^dagger`, `R_z(phi)=exp(-i·phi·sigma_z/2)` | preserves purity |

The dephasing formula above is the standard textbook expansion of "sigma_z dephasing" /
"sigma_x dephasing" (the ledger names the generator type and reports a fitted rate; it does
not spell the Lindblad form out in the row itself). The rotation formulas are the standard
closed form for the named unitary. Both are stated here as the natural formalization of
what the ledger names, not as independently re-derived numbers; the reported rates
(0.69, 0.73) and residuals below are the ledger's own measured values, not recomputed this
session.

### 4.2 W-covariance (5.4–5.5) and the 2-native law (5.6, "O1 CLOSED")

`W = (sigma_x + sigma_z)/sqrt(2)` (Hadamard, in Pauli form). Conjugation `W(·)W` maps
`Ti <-> Te` and `Fi <-> Fe` to a reported residual of `3.4e-33` / `4.5e-17` (the ledger
reports both numbers on the one row without stating which pair maps to which; not
disambiguated further here). Graded `EARNED (exact)`.

Of the four candidate `(dissipator, unitary)` pairings — `{Ti,Fe}`, `{Ti,Fi}`, `{Te,Fe}`,
`{Te,Fi}` — the two same-axis pairs, `{Ti,Fe}` (both z) and `{Te,Fi}` (both x), commute
exactly: a dissipator and a unitary built from the same Pauli matrix always commute,
since both are functions of one operator. The ledger reports this as a computed fact
(generator commutator 0, operational order-gap `0.00000`), not asserted from the algebra —
constraint C2 (non-commutation must not collapse) then excludes both same-axis pairs. The
two surviving cross-axis pairs — `{Ti,Fi}` (= `{D_z,H_x}`) and `{Te,Fe}` (= `{D_x,H_z}`)
— are themselves W-conjugate (residual `~3e-16`), and each terrain's own declared frame
sign (Axis-2) admits exactly one. The ledger's own line spells the correspondence out
directly: "the 2 survivors (`{D_z,H_x}={Ti,Fi}`, `{D_x,H_z}={Te,Fe}`) are Axis-2 (W)
conjugates." Graded `EARNED (derived from C2)`, closed as open item `O1` on 2026-07-01, sim
`admissibility_two_operator_sim.py` (`system_v7/constraint_core/sims_and_scripts/`).

5.4 ("surface IS the operator") reports a containment residual of `0.00`–`0.12` for
projective/depolarizing terrains and `0.67` in every frame for source-locked (damping)
terrains — read as an irreducible geometric surplus the four operators cannot express, and
carried forward into 6.3's "8-fused / 8-surplus split."

### 4.3 What stage64 does and does not re-execute from this layer (T4, worked through)

`stage64_constraint_tournament.py` builds its own candidate roster from exactly this same
`{z,x}` structure — `JUMP = {"z": SM, "x": W @ SM @ W}` with `W` literally the Hadamard
matrix and `SM = |0><1|` — and its own superoperator-level W-conjugacy check
(`K1_survivors_W_conjugate_exact`) reports the two K1 survivors W-conjugate to `< 1e-12` in
all 16 of its stages, per the receipt. That is a live, independent re-confirmation of the
Layer‑5.5 W-covariance mechanism.

But `SM = |0><1|` is a lowering (relaxation) jump operator, commented "decay toward +z"
in the source — the same generator type as Layer 4's damping terrains (`t0`/`t2`/`t4`/`t6`:
`damp(sigma+)`/`damp(sigma-)`, non-unital), not Layer 5's own `Ti`/`Te` dephasing pair
(which the ledger names explicitly as destroying coherence, not populating a fixed
level). Stage64's unitary side (`H_b = s·f·omega·sigma_b`) does match Layer 5's `Fi`/`Fe`
exactly — a plain rotation generator about the declared axis. So: stage64 re-executes
Layer 5's admissibility logic (exclude same-basis, keep W-conjugate cross-basis
survivors, let a declared sign admit one) and its unitary generator family, on a
different — Layer‑4‑style — dissipative generator family. It is evidence for the shape
of Layer 5's construction, generalized to 16 declared stages; it is not a rerun of `Ti`/`Te`
themselves. Its own status as a tournament is graded in §5, not here, because that is
where the audit's finding actually lands.

One further reading, offered here as this file's own synthesis rather than a claim either
source states directly: 5.6's own language already concedes the outcome is "forced, not
labelled" — i.e., a necessary consequence of C2 once the same-axis/cross-axis split is
fixed, not an open empirical question. Read that way, the 2026-07-20 audit's "construction
identity, cannot fail" verdict on stage64's structurally-identical K1 gate may not
contradict the 07-01 ledger row so much as restate it in the harness's stricter vocabulary.
What the audit is actually critical of is stage64's presentation — "survivors," "walls,"
"tournament," "48 non-operating candidates" — competitive language wrapped around an
outcome that C2 (and, before that, the plain fact that any operator commutes with itself)
already fixed. That reading is not adjudicated by the materials read for this file; it is
offered as one live option, not collapsed onto the other.

### 4.4 Layer 5 SIM STATUS, stated against this repo's status ladder

`admissibility_two_operator_sim.py` exists on disk at
`system_v7/constraint_core/sims_and_scripts/admissibility_two_operator_sim.py`. The ledger
reports it `EARNED` at 2026-07-01, fixture-local scope. This session did not read or
re-execute that file directly (it was not in the task's read list; the ledger's own row
text was read instead). Its status here is therefore `exists` (confirmed on disk this
session) plus the ledger's own quoted `EARNED` grade — not independently re-verified to
`runs` or `passes local rerun` by this session. No file in the 2026-07-20 audit pass
(`stage64/AUDIT_VERDICT.md`, `RUNGS_ABCE_AUDIT_VERDICT.md`) names this sim; that pass's
scope was `system_v8/nested_manifold` only.

## 5. Layer 6 in full — the 16 stages and the 64 schedule

### 5.1 Two different 16s, two different 64s (T2, T3 worked through)

The ledger's own count (6.1): 16 stages = 8 named terrains (`t0 Funnel` … `t7 Citadel`) × 2
native operators per terrain (the pair Layer 5.6 admits). All 16 reported distinct, mean
pairwise separation 4.6. 6.2: an order-blind readout collapses 64 (all four candidate
pairs tried, order-blind) down to 11 distinct outcomes; the order-sensitive (N01,
terrain-first vs operator-first) readout gives 64/64 distinct, with per-stage order gaps
from 0.020 (`t1:Ti`) to 0.459 (`t6:Te`), all strictly positive. 6.4: the coherent axis
`(1,1,1)/sqrt(3)` is reported load-bearing, not a free convention — putting `H0` on plain
`sigma_z` makes the 4 `Fe` stages commute with their terrains (order gap `2e-16`), and 16/16
order-sensitivity collapses to 12/16.

6.5–6.6 report a second, contested 64: "live-runtime `64 = 2×8×4` slot space" (2 Weyl
sheets × 8 terrains × all 4 candidates, before native-selection narrows to 2), set against
a rival chart-atlas reading (`64 = 8×8` index surface with 16 starred, chart-locked
macro-stages) and a hexagram reading (64 = a fenced tag family). The ledger records this as
"RESOLVED BY SOURCE" only in the sense that the source document (`ENGINE_64_SCHEDULE_ATLAS.md`)
declares all three as a genuine three-layer split, not a single number in three
disguises; which reading governs a given downstream claim remains an owner decision (open
item `O4`), not something this file adjudicates.

A third, separate 64 belongs to the v7 sim `engine_64_schedule_sim.py`, not read this
session. `system_v7/constraint_core/CLAUDE.md` (read in full this session, quoted directly
rather than paraphrased) states as a hard rule: "`engine_64_schedule_sim.py`: order-blind
collapse `11/64` — the collapse is the point," listed alongside a warning that "some
expected results are honest failures. They must stay failed." This is not the same 64 as
either of the two above; it is named here only so it is not mistaken for either.

### 5.2 stage64's own grid — the 64 = 2×32 engine ontology

`stage64_constraint_tournament.py` builds a fourth, independently-executed 64, dated
2026-07-19 (commit `7f0477a6b`) and explicitly framed in its own docstring as "owner
hypothesis, executable test" — not a rerun of any of the three 64s above. The grid, quoted
directly from the source (lines 132–140):

```
for (fam, omega, gamma, fsign), sheet, field in itertools.product(
        TERRAINS, ["L", "R"], [+1, -1]):
    ...
    roster = [make_candidate(a, b, omega, gamma, s, field)
              for a, b in itertools.product("zx", "zx")]
```

`TERRAINS` has 4 entries (`family_0`…`family_3`, each carrying its own `omega`, `gamma`,
and declared frame sign). `itertools.product(TERRAINS, ["L","R"], [+1,-1])` gives
`4 × 2 × 2 = 16` "stages" (stage64's own use of the word — a different factorization of 16
than the ledger's 6.1, per T3). Each stage's roster has `itertools.product("zx","zx") = 4`
candidates. Total: `16 × 4 = 64`, matching the receipt's own `"grid"` field: `"4 terrain
families x 2 sheets x 2 loop fields = 16 stages; 4 candidate (D_a, H_b) pairs each = 64
candidates"`.

Regrouped by sheet — the two Weyl sheets are exactly Layer 3's "2 independent engine
types" ("your L and R engines") — the same 64 reads as 2 engines × 32, where
`32 = 8 macro-stages (4 families × 2 loop fields, holding one sheet fixed) × 4 microsteps
(the candidate roster)` per engine, and the "pair total" sums the L-engine's 32 and the
R-engine's 32. This is the identical executed grid, associated `2×(8×4)` instead of
`(4×2×2)×4`; it introduces no new computation and no new claim beyond what the receipt
already records. Note, to keep T3 from re-collapsing here: "macro-stage" in this
regrouping (family × field, 8 of them per engine) is a different granularity from the
ledger's own 6.6 use of "macro-stage" (16 total, chart-atlas-starred) — the same English
word, two different objects, in two different documents.

### 5.3 The tournament battery and its receipt

Three constraints (K1–K3) plus a deletion/counter-probe test, run per stage:

- K1 — commutation kill. Superoperator commutator norm `\|\|[D_hat,H_hat]\|\|_F`. Exactly
  zero (same-axis pair) excludes; the code enforces killed `< 1e-12`, alive `> 1e-3`, with
  no stage landing in the ambiguous middle band.
- K2 — frame-sign selection. Relational: `argmax` of `frame_sign × orientation` over
  the (exactly two) K1 survivors. With fewer than two survivors present, K2 has nothing to
  compare and the stage is recorded `under_determined` — this is the branch the deletion
  test exercises.
- K3 — chirality consistency. The admitted pair's measured Bloch circulation
  `(r × dr/dt)·(f·e_b)` at the dissipative fixed axis must match the declared sheet sign.

Receipt (`system_v8/nested_manifold/results/stage64/receipt.json`, read this session, not
re-executed): `all_pass: true` across all 11 declared checks
(`S_stage_count_16`, `K1_exactly_2_killed_every_stage`,
`K1_killed_are_order_blind_zero_circulation`, `K1_survivors_W_conjugate_exact`,
`K2_exactly_1_admitted_every_stage`, `K2_frame_sign_load_bearing_flip_changes_operator`,
`K3_admitted_flux_matches_sheet_every_stage`, `T_exactly_1_operating_per_stage_16_total`,
`K3_control_field_mismatch_excluded`, `D_partner_deletion_under_determines_all_16`,
`D_walls_enumerated_48`). `k1_survivor_norm_range: [0.4776..., 1.1023...]` (both K1
survivors measurably nonzero in every stage). `wall_role_totals: {killed_K1: 32,
rejected_K2_frame_sign: 16}` (32+16=48, the full non-operating set).
`promotion_allowed: false`, `formal_admission_allowed: false` (receipt fields, both
explicit).

The receipt's own `operating_pairs` data corroborates the audit finding directly rather
than merely asserting it: the admitted pair is a pure function of each stage's declared
`frame_sign` alone. `family_0` and `family_2` (both `fsign=+1`) admit `D_z|H_x` on every
sheet and every field; `family_1` and `family_3` (both `fsign=-1`) admit `D_x|H_z` on
every sheet and every field. Neither the sheet (`L`/`R`) nor the loop field (`+1`/`-1`)
ever changes the outcome in this receipt — of the grid's declared axes, only the
terrain family's sign carries any of the outcome's variance, and that sign is declared
input, not derived.

### 5.4 Audit verdict (2026-07-20)

`system_v8/nested_manifold/results/stage64/AUDIT_VERDICT.md` (full text read this session;
commit `a95b859ce`, "audit(v8): theater hunt — stage64 TAINTED"):

> TAINTED as a standalone admission. All 11 gates are construction identities that CANNOT
> fail: K1 commutation-kills-2 is a 2x2 grid diagonal identity (900-combo sweep:
> killed-count {2} always); K2 frame-sign-admits-1 is argmax{+f,-f}; K3 flux-matches-sheet
> is automatic (circ=+/-2.0 with sign=sheet_s for both survivors); the deletion witness and
> all controls are structural.

The same note flags the receipt's own ceiling as honest on one specific point ("frame sign
declared-not-derived") while still holding `all_pass=11/11` must not be read as a
tournament result. It also flags a separate, unrelated stale-citation risk: a "0.885 rad
stability" figure sometimes attached to stage64 is misattributed — "stage64 contains no
perturbation sweep" — with the genuine measured stability number (`min_break=1.15 rad`)
sourced instead to `jax_scale_lanes.py` line 14, a 1600-point sweep with a dual z3+cvc5 8/8
UNSAT kill-set proof. That file was not read for this dossier; it is named here only as a
pointer, and specifically so `0.885 rad` is not carried into any future citation of Layer
6 by mistake.

## 6. Layer 7 in full — the 7 axes

### 6.1 The seven axes as read in the ledger

| Axis | Ledger row | Bipartition / object | Reported grade |
|---|---|---|---|
| Axis-0 | 7.5 (deferred) | "perceiving" — resolved as a parity, in full, only at Layer 9 | deferred, see Layer 9 (out of scope here) |
| Axis-1 | 7.1 | `{dissipative: Se,Ni}` \| `{unitary: Ne,Si}` — the entropy charge (eigenvalue sector) | `EARNED` |
| Axis-2 | 7.1 | `{direct: Se,Ne}` \| `{conjugated: Ni,Si}` — the phase charge (eigenvector sector), invisible to entropy | `EARNED` |
| Axis-3 | 7.3 | topology | `EARNED` as a structural DOF |
| Axis-4 | 7.3, 7.4 | tense / loop order. Deductive = `UEUE`, Inductive = `EUEU` — the same four substeps, reversed | `EARNED` |
| Axis-5 | 7.3 | operator kernel family | `EARNED` as a structural DOF |
| Axis-6 | 7.3 | signed handedness; sign law `b6 = -b0*b3`, 0/8 violations | `EARNED` |

7.6: the three topology partitions (Axis-0/1/2) are reported mutually orthogonal, with
entropy blind to the frame (Axis-2) at a measured residual of `2e-15`. The ledger's own
heading for this row is "DOFs do not collapse" — read here as the axes' own anti-collapse
requirement, not this file's paraphrase.

### 6.2 The entropy functional this layer actually names

Unlike Layer 5 and Layer 6, Layer 7 names its entropy functional directly: `S(rho) =
-Tr[rho log2 rho]` (von Neumann entropy, bits). 7.1's own language — "Axis-1 … The ENTROPY
charge (eigenvalue sector)" and "Axis-2 … The PHASE charge …, invisible to entropy
(symbolic identity: unitary similarity preserves spectrum)" — states plainly that Axis-1
acts on `S(rho)`'s eigenvalue sector, and Axis-2 acts only on eigenvectors, so a unitary
similarity transform along Axis-2 leaves `S(rho)` numerically unchanged. The `2e-15`
residual in 7.6 is the direct numeric witness of that invariance, not a separate claim.

### 6.3 Layer 7 SIM STATUS

Ledger `EARNED` (7.1–7.6), 2026-07-01, same fixture-local scope and same caveat as Layer 5.
No file in the task's read set, and none found in `system_v8/nested_manifold` under the
names read for context (`rungA_carrier_to_flux.py`, `rungB_sheets_sixteen.py`,
`rungE_response.py`), names "the 7 axes" as its own executed object. `RUNGS_ABCE_AUDIT_VERDICT.md`
does report rungA's "Stokes/monopole/contractible-loop checks" and rungB's "left-sheet
trajectory laws" as having survived a real attack — content that operationally touches
Axis-1 (dissipative/unitary), Axis-2 (direct/conjugated), and Axis-6 (signed handedness)
concepts — but neither rung file names an axis directly, and neither was in this task's
required read set, so this file holds that as an unverified pointer, not a citation for
Layer 7's own status. Layer 7 therefore carries the same evidence gap as Layer 5: no
2026-07-20 fresh-context genuine-vs-tainted verdict exists in the materials read for this
dossier. That gap is itself a finding, named in §8, not inferred away by borrowing Layer 6
or Layer 8's grade.

## 7. Layer 8 in full — cuts and the Schur co-view

Layer 8, as the task frames it, joins two things: the ledger's own "installed co-view
realization" (8.1–8.2, entropy as a Hamiltonian expectation value on the same distinction
surface that supplies the state) and two 2026-07-19 `nested_manifold` executions that make
that co-view concrete — `rungC_joint_cuts.py` (bipartition cuts of a joint state) and
`rungD_schur_nesting.py` (eliminating an enclosing layer to get an effective inner
generator). rungC self-labels its own material `(L7)` in a third, v8-only numbering (T1);
it is read here as this file's Layer 8, per the task's explicit framing, not as a claim
about either older L7.

### 7.1 Ledger 8.1–8.2

> 8.1 Entropy IS a Hamiltonian EARNED. S(rho) = <K_rho> (modular/GNS). S(rho||sigma) =
> <K_sigma - K_rho> >= 0; GNS inner product PSD; DPI monotone (0.340 -> 0.235 under a
> channel). This is a later QIT co-view; entropy does not run on a prior manifold and is
> not root structure.

Written out: with `K_rho := -log(rho)` (the modular/GNS "Hamiltonian"), `Tr[rho·K_rho] =
-Tr[rho·log(rho)] = S(rho)` by definition — this rewrites the ordinary von Neumann entropy
as an expectation value of an operator built from the state itself, rather than a
separately posited functional. The relative-entropy identity follows the same way:
`S(rho||sigma) = Tr[rho(log rho - log sigma)] = Tr[rho(K_sigma - K_rho)] = <K_sigma -
K_rho>`, non-negative by Klein's inequality (the ledger's "GNS inner product PSD"). The
data-processing inequality (relative entropy non-increasing under a CPTP channel) is
reported demonstrated numerically, `0.340 -> 0.235` bits. 8.2: the frame bit (Axis-2)
becomes physically readable only once the dissipative (entropy) sector is active — cross-
referenced in the ledger to Layer 9.4, out of this file's scope.

### 7.2 rungC — joint-state cuts

Carrier: `rho_LR` on `C^2 (x) C^2`. Declared family: `|psi(t)> = cos(t)|01> + sin(t)|10>`,
`t in [0, pi/2]` (product at both endpoints), plus four explicit controls — product pure,
product of maximally-mixed marginals, a classically-correlated mixture, and an asymmetric
product mixture (`0.75|0><0|+0.25|1><1| (x) |1><1|`, which factors and so sits on the
product side of every check despite not looking like one at a glance — the rungC docstring
records that this state was misclassified as non-product on the first run and caught by
a red C1 result, kept as a finding rather than quietly fixed).

A cut is a bipartition readout of `rho_LR`. All entropies are von Neumann, bits:

- `S_L = S(Tr_R[rho_LR])`, `S_R = S(Tr_L[rho_LR])`, `S_LR = S(rho_LR)`.
- Mutual information: `I(L:R) = S_L + S_R - S_LR`.
- Conditional entropy: `S(L|R) = S_LR - S_R`.
- Coherent information (negative conditional entropy): `I_c = -S(L|R) = S_R - S_LR`. This
  is the same sign convention the ledger already committed to at Layer 0.3 ("Signed Axis-0
  primitive," `I_c(A>B) = S(rho_B) - S(rho_AB) = -S(A|B)`, read there as a signed
  entanglement/binding witness) — rungC extends that primitive from a single cut to an
  explicit weighted two-cut family, below, rather than introducing a new sign convention.
- Negativity (Peres–Horodecki/PPT witness): `N(rho) = sum of |negative eigenvalues of
  rho^(T_R)|` (partial transpose on the R factor).
- Chirality split: `DeltaS = S_L - S_R`.
- `Phi0` (the declared two-cut family, weights `w = (1/2, 1/2)`): `Phi0 = w1·I_c(cut L|R) +
  w2·I_c(cut R|L)`.

Six controls (C1–C6), all reported firing in the receipt
(`system_v8/nested_manifold/results/rungC/receipt.json`, read this session, `all_pass:
true` across 14 checks):

- C1 — `I(L:R)=0` iff product, both directions (every product-side member `< 1e-9`;
  every non-product member `> 1e-6`).
- C2 — negativity `>0` exactly on the entangled interior of the pure family; `0` on
  every separable control, including the classically-correlated mixture (`I=1.0` bit,
  `negativity=0` — correlation without entanglement, both numbers recorded together).
- C3 — `Phi0` changes sign across the family: positive on entangled pure members,
  negative on the mixed product control.
- C4 — two joint states built with identical marginals but different `I`: the Bell
  state at `t=pi/4` versus the product of its own marginals. Marginal gap `0.0` (to
  `1e-12`); `I(bell)=2.0` bits versus `I(product)=0.0` bits — a full 2-bit gap despite
  indistinguishable 1-qubit marginals, the maximum possible for a qubit pair. This is the
  receipt's own demonstration that the joint cut carries information the marginals alone
  cannot.
- C5 — "product, no entanglement" control at `t*=pi/3`: before, `I=1.6226` bits,
  negativity `0.4330`; after replacing `rho` with the product of its own marginals,
  `I=-4.4e-16` (machine zero), negativity `-0.0` (machine zero) — both witnesses collapse
  together under the same substitution.
- C6 — chirality split `DeltaS` is exactly `0` on the whole pure family (Schmidt
  symmetry, reported as a structural finding, not weakened), and nonzero (`0.8113`) on the
  asymmetric product-mixture witness, which needs no L–R correlation at all (`I=0` there —
  the split is a marginal-purity fact, not an entanglement fact).

`Phi0` values across the declared pure family, from the receipt: `0` at `t=0` and
`t=pi/2` (product endpoints), rising through `0.2333`, `0.6009`, `0.8916` to a peak of
`1.0000` at `t=pi/4` (maximal entanglement), symmetric back down. `ctrl_product_maxmixed:
Phi0=-1.0` (the family's negative pole). `ctrl_classical_corr: Phi0=0` exactly (1 bit of
classical correlation, but zero coherent information).

### 7.3 rungD — the Schur-complement nesting witness

Carrier: a 4-level system (2 inner levels, 2 outer/auxiliary levels), one GKSL generator
`L` written as a column-stacked, 16-dimensional superoperator on Liouville space. The
Liouville space splits into the inner block `I` (4 components touching only the inner 2
levels) and the outer block `O` (the other 12). The enclosing (outer) layer is eliminated
exactly by the Schur complement:

```
L_eff = L_II - L_IO @ L_OO^-1 @ L_OI
```

— a 4×4 effective generator on the inner sheet alone (`L_II` is 4×4, `L_OO` is 12×12,
`L_IO`/`L_OI` are 4×12/12×4). Two outer constraints, identical inner layer and coupling in
both: `A = {Delta2=1.0, Delta3=1.5, gph=0.1}`, `B = {Delta2=3.0, Delta3=0.5, gph=0.8}`;
shared `{omega=1.0, f_drive=0.4, k_in=0.3, g=0.5, g2=0.35, k_out=0.8}`.

Entropy-flux functional (per dissipative channel `D_k`, evaluated on the stationary state
`rho_ss`, infinite-temperature-bath convention, eigenvalues clipped at `1e-14` before the
log): `Phi_k = -Tr[D_k(rho_ss)·ln(rho_ss)]`. State-space distance functional used
alongside it (not itself an entropy functional): Bures distance `D_B(rho_A,rho_B) =
sqrt(2(1 - sqrt(F(rho_A,rho_B))))`, Uhlmann fidelity `F = (Tr[sqrt(sqrt(rho_A)·rho_B·
sqrt(rho_A))])^2`.

Five checks, receipt (`system_v8/nested_manifold/results/rungD/receipt.json`, read this
session, `all_pass: true` across `D1`, `D2`, `D3`, `V1`, `D4`):

- D1 — `L_II` (the inner block, before elimination) is byte-identical between
  constraints A and B (`max abs diff: 0.0`), while `L_eff` (after elimination) differs by
  Frobenius norm `0.4273` — the task's "0.43 witness." The outer-layer difference reaches
  the inner generator only through the Schur term; it is not present in the inner block
  directly.
- D2 (uncoupled control, `g=g2=0`) — `L_eff` collapses to `L_II` exactly (`max abs
  diff: 0.0`, `L_OI` max abs `0.0`): the Schur term is genuinely coupling-mediated, and the
  machinery can output an honest zero when the coupling is cut. This is the control that
  makes D1 a can-fail claim rather than an assumed one.
- D3 — the Schur-reduced inner fixed point (the kernel of `L_eff`, hermitized and
  trace-normalized) moves a Bures distance of `0.19705` between constraint A and B, from
  the outer layer alone.
- V1 (exact-elimination cross-check) — the Schur-kernel inner state matches the actual
  inner 2×2 block of the full 16-dimensional Liouvillian's own stationary state to `max abs
  diff: 9.3e-17` (A) / `2.2e-16` (B) — machine precision. The elimination identity holds
  exactly, not approximately, for both constraints.
- D4 (flattening control) — trivially folding the two outer levels into the inner sheet
  (`|2>-><|1>`, `|3>-><|0>` applied to every Hamiltonian term and jump operator) changes the
  measured steady-state entropy flux through the inner decay channel from `-0.036378`
  (nested) to `-0.035404` (flattened), `abs diff: 0.000974`. The check technically fires
  (above the `1e-6` threshold), but is explicitly excluded from load-bearing status by the
  audit below — carried forward as a caveat here, not silently dropped.

### 7.4 Audit verdicts for Layer 8's two halves

`rungD` — CLEAN, per `system_v8/nested_manifold/results/stage64/AUDIT_VERDICT.md`
(2026-07-20, commit `a95b859ce`): "rungD central nesting claim D1/D3/V1 (genuine, can-fail
via D2; D4 flatten = weak non-normalized fold, do not cite as load-bearing)." Three of four
checks read as genuine can-fail witnesses; the fourth is named and excluded, not hidden.

`rungC` — TAINTED-with-surviving-core, per
`system_v8/nested_manifold/results/RUNGS_ABCE_AUDIT_VERDICT.md` (2026-07-20, commit
`051943694`): "BY-CONSTRUCTION (cannot fail, each paired with a real discriminator): …
rungC C4+C6 (Schmidt identities)." C4's "identical marginals" fact and C6's "`DeltaS=0` on
the pure family" fact are both Schmidt-decomposition identities for a 2-qubit pure state —
necessary consequences of the state family's own structure, not contingent discoveries.
The same verdict separately reports: "SURVIVED THE ATTACK (can-fail, verified by probe): …
rungC mutual-info/negativity iff-oracles (fired red on first run, kept)" — C1, C2, C3, and
C5, corroborated by the rungC docstring's own account of the asymmetric-mixture
misclassification caught on its first run (§7.2). Ledger 8.1/8.2 itself carries the ledger's
own `EARNED`, 2026-07-01, no fresh audit — the same evidence-gap status as Layers 5 and 7.

## 8. Verdict — genuine vs tainted, by layer, cited

- Layer 5 (operators + 2-native law). Ledger `EARNED`
  (`admissibility_two_operator_sim.py`, 2026-07-01). No 2026-07-20 fresh-context audit in
  the materials read for this file touches this sim. Open evidence gap, not a tainted
  finding — the two are different things and this file does not conflate them.
- Layer 6 (16 stages / 64 schedule). `TAINTED` as a standalone admission.
  `system_v8/nested_manifold/stage64_constraint_tournament.py`, receipt
  `results/stage64/receipt.json` (`all_pass: true`, 11/11), audited in
  `results/stage64/AUDIT_VERDICT.md` (2026-07-20, commit `a95b859ce`): all 11 gates are
  construction identities that cannot fail. The receipt's own `operating_pairs` data
  corroborates this directly (§5.3): the outcome is a pure function of declared frame sign,
  invariant to sheet and loop field.
- Layer 7 (the 7 axes). Ledger `EARNED` (7.1–7.6, 2026-07-01). Same open evidence gap
  as Layer 5 — no 2026-07-20 fresh audit in the materials read for this file names "the 7
  axes" as its own object.
- Layer 8 (cuts / Schur co-view). Split, cited at the level each half earns
  separately. `rungD_schur_nesting.py`: `CLEAN` — `D1`/`D3`/`V1` genuine and can-fail via
  the `D2` control; `D4` named and excluded from load-bearing status
  (`results/stage64/AUDIT_VERDICT.md`, 2026-07-20, commit `a95b859ce`). `rungC_joint_cuts.py`:
  mixed — `C4`/`C6` by-construction Schmidt identities (cannot fail); `C1`/`C2`/`C3`/`C5`
  survived a real attack (`results/RUNGS_ABCE_AUDIT_VERDICT.md`, 2026-07-20, commit
  `051943694`). Ledger 8.1/8.2: `EARNED`, 2026-07-01, no fresh audit.

Two layers (5 and 7) have real receipts behind their `EARNED` grade but have not been run
through the same 2026-07-20 fresh-context adversarial pass that produced Layer 6 and Layer
8's verdicts. That is a genuine gap in this dossier's evidence, not a presumption either
way about what such a pass would find — naming it is the honest close, not a soft one.

## 9. Open items

1. No 2026-07-20-style fresh-context audit exists yet, in the materials read for this
   file, for `admissibility_two_operator_sim.py` (Layer 5) or for any sim naming "the 7
   axes" directly (Layer 7). Closing this gap would put Layers 5 and 7 on the same footing
   as Layers 6 and 8 rather than leaving them one grade behind on an older, unaudited
   basis.
2. The two-64s tension (ledger 6.6, item `O4`) remains an explicit owner-only decision, not
   resolved by this file or by stage64's own (separately tainted) 64.
3. `jax_scale_lanes.py`'s `min_break=1.15 rad` figure, named in `stage64/AUDIT_VERDICT.md`
   as the genuine stability number that `0.885 rad` is sometimes wrongly attached to, was
   not read for this dossier and is not verified here — a pointer only.
4. rungA's Stokes/monopole content and rungB's left-sheet trajectory laws, both reported
   surviving a real attack in `RUNGS_ABCE_AUDIT_VERDICT.md`, operationally touch Axis-1/2/6
   concepts without naming them. Whether that content should be read into Layer 7's status
   is an open question this file leaves open rather than answers by inference.

## 10. Citation index

- `system_v7/constraint_core/MODEL_LAYER_LEDGER.md` — lines 1–22, 82–233, 730–787.
- `system_v7/constraint_core/CLAUDE.md` — quoted directly (Layer‑6 `engine_64_schedule_sim.py`
  rule).
- `system_v7/constraint_core/sims_and_scripts/admissibility_two_operator_sim.py` — path
  confirmed on disk; not read this session.
- `system_v8/nested_manifold/stage64_constraint_tournament.py` — full file read.
- `system_v8/nested_manifold/results/stage64/receipt.json` — parsed field by field.
- `system_v8/nested_manifold/results/stage64/AUDIT_VERDICT.md` — full file read; commit
  `a95b859ce`.
- `system_v8/nested_manifold/rungC_joint_cuts.py` — full file read.
- `system_v8/nested_manifold/results/rungC/receipt.json` — parsed field by field.
- `system_v8/nested_manifold/rungD_schur_nesting.py` — full file read.
- `system_v8/nested_manifold/results/rungD/receipt.json` — parsed field by field.
- `system_v8/nested_manifold/results/RUNGS_ABCE_AUDIT_VERDICT.md` — full file read; commit
  `051943694`.
- `system_v8/nested_manifold/rungA_carrier_to_flux.py`,
  `system_v8/nested_manifold/rungB_sheets_sixteen.py`,
  `system_v8/nested_manifold/rungE_response.py` — docstrings only (first ~60 lines each),
  for grid/lineage context.
- Build commits (`git log`, this session): rungA `a16bed1e2`; rungs B–E
  `0b463871f`; stage64 + `manifold_one.py` `7f0477a6b`; stage64 audit `a95b859ce`; rungs
  A/B/C/E audit `051943694`.
- `MODEL_DOSSIER/07_RATCHET_ACTUAL_STATE.md` — read for house convention and explicit
  scope-fencing; a different lane, not folded in here.

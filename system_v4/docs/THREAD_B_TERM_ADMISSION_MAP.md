# Thread B Term Admission Map

**Date:** 2026-03-29
**Status:** Proto-ratchet owner packet for Thread-B-safe term admission of entropy and axis-math vocabulary. This is an upstream staging surface, not a kernel commit.

---

## 1. Scope

This file answers one bounded question:

**Given the current B-thread constraint ratchet, which entropy and axis-math vocabulary can be staged as `MATH_DEF`, `TERM_DEF`, `LABEL_DEF`, or candidate `CANON_PERMIT`, which must stay quarantined, and which should remain label-only for now?**

Frozen dependencies:

- geometry branch is frozen
- `Ax0` kernel / bridge / cut doctrine is frozen
- favored QIT/Hopf/Weyl realization remains downstream of the root handoff

This file does **not**:

- admit terms into Thread B directly
- declare evidence tokens already satisfied
- reopen geometry, bridge, or cut ranking

---

## 2. Pipeline Contract

| Stage | Boot meaning | Use here |
|---|---|---|
| `MATH_DEF` | declare the mathematical object family and its domain/codomain/invariants | first step for any serious math term |
| `TERM_DEF` | bind a literal term to one `MATH_DEF` | needed before term use |
| `LABEL_DEF` | attach human-facing labels to an admitted term | use for terrain/overlay language |
| `CANON_PERMIT` | allow a term into canonical use only with explicit evidence token | only for the most stable vocabulary |

TERM registry states:

- `QUARANTINED`
- `MATH_DEFINED`
- `TERM_PERMITTED`
- `LABEL_PERMITTED`
- `CANONICAL_ALLOWED`

Important fences:

- domain/metaphor words enter only through `TERM_DEF` / `LABEL_DEF`
- rebinding a term to a different `MATH_DEF` triggers `TERM_DRIFT`
- undefined terms trigger `UNDEFINED_TERM_USE`
- derived-only primitive use triggers `DERIVED_ONLY_PRIMITIVE_USE`
- glyph-heavy shorthand may trigger `GLYPH_NOT_PERMITTED`

---

## 3. Entropy Vocabulary

| Literal term | Bound math family | Proposed pipeline state | Evidence needed before `CANONICAL_ALLOWED` | Note |
|---|---|---|---|---|
| `von_neumann_entropy` | single-state mixedness functional \(S(\rho)\) | `TERM_PERMITTED` | explicit sim evidence if promoted beyond diagnostic use | late-derived diagnostic, not base admissibility |
| `mutual_information` | total-correlation functional \(I(A:B)\) | `TERM_PERMITTED` | evidence if promoted as more than guardrail diagnostic | useful companion, unsigned |
| `conditional_entropy` | cut entropy \(S(A|B)\) | `TERM_PERMITTED` | evidence that the cut family is well-typed in the live stack | cut-dependent |
| `coherent_information` | signed cut functional \(I_c(A\rangle B)\) | `TERM_PERMITTED` | explicit evidence on the admitted cut/bridge family before canonical use | strongest simple `Ax0` candidate, still downstream |
| `relative_entropy` | comparison functional \(D(\rho\|\sigma)\) | `MATH_DEFINED` | reference-family evidence and use-case lock | useful but reference-dependent |
| `refinement_entropy` | refinement/path ordering functional family | `MATH_DEFINED` | separate contract/evidence if elevated beyond descriptive branch | upstream descriptive family, not kernel canon |
| `path_entropy` | refinement/path cost family | `MATH_DEFINED` | path-law evidence if any path semantics are promoted | no path law by default |
| `boundary_bookkeeping_delta` | shell/reconstruction comparison proxy | `QUARANTINED` | explicit bridge/shell evidence | proxy, not doctrine |
| `mi_distribution_entropy` | entropy of MI-weight distribution | `QUARANTINED` | explicit diagnostic evidence and use-case constraint | proxy spread measure |

Entropy rule:

- signed cut-based functionals can be staged as terms
- proxy or reference-heavy families should stay `QUARANTINED` or merely `MATH_DEFINED`
- none of these are allowed to define admissibility by themselves

---

## 4. Axis-Math Vocabulary

| Literal term | Bound math family | Proposed pipeline state | Evidence needed before `CANONICAL_ALLOWED` | Note |
|---|---|---|---|---|
| `unitary_branch` | terrain-generator unitary family | `TERM_PERMITTED` | generator-family evidence if promoted as kernel vocabulary | Ax1-side, not Ax5 |
| `proper_cptp_branch` | terrain-generator proper CPTP family | `TERM_PERMITTED` | same | Ax1-side |
| `direct_representation` | direct evolution branch | `TERM_PERMITTED` | representation-family evidence if promoted | Ax2-side |
| `conjugated_representation` | unitary-conjugated representation branch | `TERM_PERMITTED` | same | Ax2-side |
| `fiber_loop` | density-stationary loop family | `TERM_PERMITTED` | geometry evidence if promoted into kernel vocabulary | Ax3 geometry-backed |
| `base_loop` | density-traversing loop family | `TERM_PERMITTED` | same | Ax3 geometry-backed |
| `loop_order_unitary_first` | `U E U E` loop word | `TERM_PERMITTED` | `AX4_LOOP_ORDERING_NONCOMMUTATIVE` evidence satisfied | Ax4 family — evidence emitted |
| `loop_order_nonunitary_first` | `E U E U` loop word | `TERM_PERMITTED` | `AX4_UEUE_EUEU_DISTINCT` evidence satisfied | Ax4 family — evidence emitted |
| `dephasing_kernel` | nonunitary dephasing operator family | `TERM_PERMITTED` | operator-ledger evidence if promoted | Ax5 family |
| `rotation_kernel` | unitary rotation operator family | `TERM_PERMITTED` | same | Ax5 family |
| `operator_precedence_up` | `J o T_tau` precedence branch | `MATH_DEFINED` | derivation/evidence if promoted | Ax6 derived |
| `operator_precedence_down` | `T_tau o J` precedence branch | `MATH_DEFINED` | same | Ax6 derived |
| `coherent_information_axis0` | `Ax0` kernel shorthand for `I_c` on a live cut family | `QUARANTINED` | bridge and cut evidence together | avoid premature kernel/doctrine collapse |
| `xi_hist` | history bridge family | `QUARANTINED` | strict bridge evidence token | still open bridge family |
| `xi_ref` | point-reference bridge family | `QUARANTINED` | strict bridge evidence token | strongest pointwise discriminator, not doctrine |
| `shell_interior_boundary_cut` | doctrine-facing cut family | `QUARANTINED` | strict shell/cut evidence | strongest doctrine-facing cut family, still open |

Axis rule:

- stable math families can be `TERM_PERMITTED`
- still-open bridge/cut objects stay `QUARANTINED`
- derived branches should usually be `MATH_DEFINED` first, not prematurely term-central

---

## 5. Label-Only Vocabulary

These should remain `LABEL_DEF`-level or overlay-only for now:

| Literal | Proposed status | Why |
|---|---|---|
| `Se`, `Ne`, `Ni`, `Si` | `LABEL_PERMITTED` only | terrain labels should not outrank the bound math families |
| `inner`, `outer` | `LABEL_PERMITTED` only | engine-indexed/overlay language; source-tight geometry is `fiber/base` |
| `white`, `black` | `LABEL_PERMITTED` only | overlay/color language |
| `Hopf`, `Weyl` as doctrine shortcuts | `LABEL_PERMITTED` only | favored realization labels, not root consequences |
| `vortex`, `funnel`, `pit`, `hill`, `spiral`, `cannon`, `source`, `citadel` | `LABEL_PERMITTED` only | human-facing terrain language, not kernel terms |

Label rule:

- label permission is not the same thing as mathematical admission
- overlay language must stay downstream of the term-bound math families

---

## 6. Proposed Evidence Strategy

| Family | Suggested evidence gate before canonical use |
|---|---|
| entropy kernels tied to `Ax0` | live bridge + live cut evidence on the same family |
| geometry-backed loop terms | geometry probe evidence confirming fiber/base behavior |
| operator / loop-order terms | operator-ledger or loop-order evidence |
| bridge and cut families | strict bridge/cut bakeoff evidence |
| overlay labels | no direct canonical-evidence path; remain labels unless later retooled |

This is a staging strategy only. It does not invent admitted evidence tokens.

### 6.1 Existing evidence-shape anchors

These do **not** mean the terms are already canonically allowed. They mean the repo already contains `SIM_EVIDENCE v1` emitter shapes that later permit work can bind to instead of inventing empty evidence channels.

| Family | Existing evidence-shape anchor | Read |
|---|---|---|
| trajectory / correlation metrics | [run_axis0_traj_corr_metrics.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/sims/simpy/run_axis0_traj_corr_metrics.py) | existing evidence-emitter shape for Axis-0 trajectory correlation signals |
| history / operator reconstruction | [run_axis0_historyop_rec_suite_v1.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/sims/simpy/run_axis0_historyop_rec_suite_v1.py) | existing multi-block evidence-emitter shape for history-facing Axis-0 tests |
| boundary bookkeeping proxy | [run_axis0_boundary_bookkeep_sweep_v2.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/sims/simpy/run_axis0_boundary_bookkeep_sweep_v2.py) | existing evidence-emitter shape for boundary bookkeeping deltas |

Evidence-shape rule:

- reuse existing `SIM_EVIDENCE v1` shapes where possible
- do not treat “existing evidence emitter” as “already admitted term”
- evidence binding comes after stable `MATH_DEF` and `TERM_DEF`, not before

---

## 7. Do Not Smooth

- Do not let `TERM_PERMITTED` read as `CANONICAL_ALLOWED`.
- Do not let favored realization labels become root-level term doctrine.
- Do not let entropy terms define admissibility.
- Do not let open bridge/cut families appear more settled just because they have names.
- Do not let label-permitted terrain language outrank the math branches it names.

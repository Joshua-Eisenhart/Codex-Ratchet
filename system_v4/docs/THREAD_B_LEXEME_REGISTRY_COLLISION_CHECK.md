# Thread B Lexeme Registry Collision Check

**Date:** 2026-03-29
**Lane:** Thread-B/export worker (Claude Code)
**Source:** THREAD_B_STAGING_VALIDATION_PACKET.md §6, task 1
**Input:** THREAD_B_LEXEME_ADMISSION_CANDIDATES.md (Tier 1–4)
**Registry checked against:** THREAD_B_TERM_ADMISSION_MAP.md (§3 entropy vocabulary, §4 axis-math vocabulary, §5 label-only vocabulary)

---

## 1. Scope

Formal conflict/collision check of every lexeme candidate literal against the existing Thread B term registry. This check answers:

- **Hard collision**: lexeme literal matches an existing term token exactly — blocks admission
- **Soft collision**: lexeme literal and existing term token share semantic territory but differ as strings — must fence; does not block but requires a subordination note
- **Shadow risk**: lexeme admission could inflate the apparent admission level of a quarantined term — flag and fence

This check does NOT advance any lexeme to admitted status. It clears the path or identifies the fences.

---

## 2. Tier 1 — Root-Earned

| Lexeme | Existing registry entry? | Finding |
|---|---|---|
| `finite_carrier` | None | CLEAR |
| `noncommutative_composition` | None | CLEAR |
| `finite_scalar_encoding` | None | CLEAR |
| `Non_commutativity` | None | CLEAR — but see naming note §4 |

**Tier 1 verdict: 0 hard collisions, 0 soft collisions. Naming inconsistency flagged.**

---

## 3. Tier 2 — QIT Basin

| Lexeme | Existing registry entry? | Finding |
|---|---|---|
| `density_matrix` | None as term token (referenced as concept) | CLEAR |
| `bipartite_density_matrix` | None | CLEAR |
| `CPTP_channel` | Nearest: `proper_cptp_branch` (TERM_PERMITTED) | SOFT COLLISION — see §5.1 |
| `Lindblad_generator` | None | CLEAR |
| `Unitary_commutator` | Nearest: `unitary_branch` (TERM_PERMITTED) | SOFT SHADOW — see §5.2 |
| `CPTP_semigroup` | None | CLEAR |
| `Channel_composition` | None | CLEAR |
| `Non_commutativity` | None | CLEAR — duplicate of Tier 1; see naming note §4 |

**Tier 2 verdict: 0 hard collisions. 2 soft collisions flagged (CPTP_channel / Unitary_commutator).**

---

## 4. Tier 3 — Geometry Realization

| Lexeme | Existing registry entry? | Finding |
|---|---|---|
| `S3_carrier` | None | CLEAR |
| `Hopf_fiber` | `Hopf` is LABEL_PERMITTED (label-only) | SOFT SHADOW — see §5.3 |
| `horizontal_lift_loop` | Nearest: `fiber_loop`, `base_loop` (TERM_PERMITTED) | SOFT SHADOW — see §5.4 |
| `Weyl_sheet` | `Weyl` is LABEL_PERMITTED (label-only) | SOFT SHADOW — see §5.3 |
| `Interaction_unitary` | None | CLEAR |
| `interaction_picture_equivalence` | None | CLEAR |
| `Rotating_frame` | None | CLEAR |

**Tier 3 verdict: 0 hard collisions. 3 soft shadows flagged (Hopf_fiber, horizontal_lift_loop, Weyl_sheet).**

---

## 5. Tier 4 — Entropy Functional

| Lexeme | Existing registry entry? | Finding |
|---|---|---|
| `basis_invariant` | None | CLEAR |
| `signed_cut_functional` | Nearest: `shell_interior_boundary_cut` (QUARANTINED), `xi_ref` (QUARANTINED) | SOFT SHADOW — see §5.5 |
| `coherent_information_relation` | `coherent_information` (TERM_PERMITTED), `coherent_information_axis0` (QUARANTINED) | SOFT COLLISION — see §5.6 |
| `density_derivative` | None | CLEAR |

**Tier 4 verdict: 0 hard collisions. 2 soft collisions / shadows flagged.**

---

## 6. Collision Analysis Detail

### §5.1 — `CPTP_channel` vs `proper_cptp_branch`

`proper_cptp_branch` (TERM_PERMITTED, Ax1-side) names the terrain-generator CPTP family as a branch class. `CPTP_channel` is a Tier 2 QIT-basin lexeme naming the mathematical object itself (the map). These are different things: branch vs object.

**Resolution:** Admit `CPTP_channel` as lexeme with a subordination note: "`CPTP_channel` is the math object; `proper_cptp_branch` is the branch classification. Do not conflate." No admission blocker.

### §5.2 — `Unitary_commutator` vs `unitary_branch`

`unitary_branch` (TERM_PERMITTED, Ax1-side) names the U/NU branch class. `Unitary_commutator` names the generator -i[H, rho]. Same semantic area (unitary evolution) but the lexeme is an operator form, not a branch classification.

**Resolution:** Admit `Unitary_commutator` as lexeme with a note: "generator form only; does not elevate `unitary_branch` to canonical status." No admission blocker.

### §5.3 — `Hopf_fiber`, `Weyl_sheet` vs `Hopf`, `Weyl` (LABEL_PERMITTED)

`Hopf` and `Weyl` are label-permitted — overlay language that must not outrank the bound math families. The lexemes `Hopf_fiber` and `Weyl_sheet` are more specific geometry terms (the fiber and sheet objects respectively) at REALIZATION_ADMITTED level.

**Resolution:** Admit as geometry-realization lexemes with explicit fence: "lexeme admission at REALIZATION_ADMITTED does not elevate `Hopf` or `Weyl` above LABEL_PERMITTED." REALIZATION_ADMITTED fence already present in the candidates doc. No admission blocker.

### §5.4 — `horizontal_lift_loop` vs `fiber_loop`, `base_loop`

`fiber_loop` and `base_loop` are TERM_PERMITTED term tokens at the axis-math level. `horizontal_lift_loop` is the Tier 3 geometry-realization lexeme naming the specific Hopf-connection horizontal lift. It is strictly more specific (one geometric realization of `base_loop`) and sits downstream of the term.

**Resolution:** Admit `horizontal_lift_loop` as REALIZATION_ADMITTED with a subordination note: "`horizontal_lift_loop` is one geometric realization of `base_loop`; it does not replace or elevate `base_loop`." No admission blocker.

### §5.5 — `signed_cut_functional` vs QUARANTINED cut families

`shell_interior_boundary_cut` and `xi_ref` are QUARANTINED. `signed_cut_functional` is a Tier 4 lexeme naming the functional form. The lexeme is further upstream (the abstract functional class) vs the specific quarantined cut families (specific doctrine choices).

**Resolution:** Admit `signed_cut_functional` as LEXEME_ADMITTED_WITH_FENCE (already marked this way in candidates doc) with an explicit fence: "lexeme admission does not advance any specific cut family (shell_interior_boundary_cut, xi_ref) toward doctrine." No admission blocker.

### §5.6 — `coherent_information_relation` vs `coherent_information` / `coherent_information_axis0`

This is the highest-risk soft collision. `coherent_information` is TERM_PERMITTED. `coherent_information_axis0` is QUARANTINED. `coherent_information_relation` is a Tier 4 lexeme naming the identity I_c(A>B) = -S(A|B).

The risk: admitting this lexeme could make the `coherent_information` entry appear more stable, or could create a path for the quarantined `coherent_information_axis0` to appear less quarantined.

**Resolution:** Admit `coherent_information_relation` only with a hard fence: "This lexeme names the abstract mathematical identity only. It does not admit the `coherent_information` term to canonical use, and it does not move `coherent_information_axis0` out of quarantine. The identity is downstream of the cut doctrine, which remains open." The existing LEXEME_ADMITTED_WITH_FENCE status in the candidates doc is correct. **No admission blocker, but fence must be preserved verbatim when cited.**

---

## 7. Naming Inconsistency

`Non_commutativity` (capital N) appears in two places:
- Tier 1 block in THREAD_B_LEXEME_ADMISSION_CANDIDATES.md (STATUS: ROOT_EARNED)
- Tier 2 block, bottom (STATUS: ROOT_EARNED)

This is a duplicate definition with inconsistent capitalization relative to `noncommutative_composition` (lowercase n).

**Recommendation:** Keep one canonical entry with lowercase `non_commutativity` (consistent with other lexemes). The Tier 2 duplicate should be removed from THREAD_B_LEXEME_ADMISSION_CANDIDATES.md to avoid registry confusion. Not a blocker, but should be fixed before formal registry submission.

---

## 8. Summary

| Tier | Hard collisions | Soft collisions / shadows | Naming issues | Verdict |
|---|---|---|---|---|
| 1 — Root-Earned | 0 | 0 | 1 (Non_commutativity capitalization) | CLEAR with naming fix |
| 2 — QIT Basin | 0 | 2 (CPTP_channel, Unitary_commutator) | 1 (duplicate Non_commutativity) | CLEAR with subordination notes |
| 3 — Geometry Realization | 0 | 3 (Hopf_fiber, horizontal_lift_loop, Weyl_sheet) | 0 | CLEAR with REALIZATION_ADMITTED fences |
| 4 — Entropy Functional | 0 | 2 (signed_cut_functional, coherent_information_relation) | 0 | CLEAR with hard fences — coherent_information_relation highest risk |

**Overall verdict: 0 hard collisions. All 4 tiers may proceed to registry as lexeme candidates. Soft collisions require subordination notes and fences (all already documented in THREAD_B_LEXEME_ADMISSION_CANDIDATES.md). One naming fix recommended before submission.**

---

## 9. Required Action Before Registry Submission

1. Fix `Non_commutativity` → `non_commutativity` (or remove the Tier 2 duplicate entry) in THREAD_B_LEXEME_ADMISSION_CANDIDATES.md
2. Add subordination notes on `CPTP_channel` and `Unitary_commutator` entries (§5.1, §5.2)
3. Preserve hard fence on `coherent_information_relation` verbatim (§5.6)
4. Verify REALIZATION_ADMITTED fence on all Tier 3 lexemes is visible in any export surface that cites them

---

## 10. Do Not Smooth

- Do not treat 0 hard collisions as admission approval.
- Do not let soft-collision fences be dropped when the lexemes are cited in later export wrappers.
- Do not let `coherent_information_relation` be cited without its hard fence.
- This check covers THREAD_B_TERM_ADMISSION_MAP.md only. If Thread B has other registry surfaces not in this repo, the check must be re-run against those.

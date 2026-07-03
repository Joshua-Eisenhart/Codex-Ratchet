# MSS and the Rung Climb — Foundations DRAFT (2026-06-15)

**Status:** DRAFT, multi-model-grounded (7-model fleet, wf w1a8hu1g0, 2026-06-15), NOT canon-by-process. This formalizes the governing selection rule (MSS) and the bottom-up rung climb the rest of the program is supposed to follow. It supersedes the loose "build order" as a *hypothesis*: the build order is not assumed — at each rung we record only what is **forced**, and we mark everything else **installed**. Cross-refs: [[entropic_monism_one_distinguishability_process_DRAFT_20260614]] (entropy = typed readout), [[ratchet_definition_and_emergence_spec_DRAFT_20260614]] (the ratchet is a *supplied* update structure, see §4), root_axioms_v0_1_DRAFT.

---

## 0. The two things this doc fixes

1. **MSS is the selection rule for the whole climb**, and was being dropped. State it once, apply it at every rung.
2. **The "build order" was being treated as established.** It is a hypothesis. The only honest move is: at each rung, separate *what finite probe data forces* from *what a supplied constraint/update installs*.

---

## 1. Root and MSS (stated precisely)

**Root.** The only primitive is `~`, probe-relative indistinguishability on a **finite** support `X` under a probe/constraint family `P` (each probe a function `X → finite value set`). `x ~_P y` iff every probe in `P` agrees on `x,y`. Identity is **derived**: `a = a` iff `a ~ b` is settled by `P`. Constraints **exclude** what cannot persist; they do not generate. Entropy is a **readout**, never primitive.

**MSS (Minimal Survivable Structure) — the governing rule.** Admit ONLY the **weakest** structure that (a) **survives** the active constraints and (b) **still evolves** (can distinguish / compose / continue / be killed). Nothing stronger — a measure, a state-functional `ω`, non-commutativity, an operator algebra, complex amplitudes, a density matrix `ρ`, geometry — is admitted **unless a lower admissible closure FORCES it** ("installed, not forced"). **"Presume the least" is itself the implicit constraint.** MSS is NOT Occam (Occam can pick a *dead* minimal thing; MSS requires an *evolvable* survivor) and NOT a root axiom — it is an admission meta-gate. Keep `Min(Surv(C))` **plural**: hold incomparable survivor branches live (anti-collapse at the base).

**⚠️ Load-bearing caveat the fleet forced (§3).** Clause (b) "still evolves" **smuggles dynamics**. Static exclusion on a finite set forces only the quotient and its Boolean structure; any *update / transition / time* is a **supplied** ingredient, not a derived one. MSS is sound as a selection rule **only if** "evolves" is read as "is killable / compositional under a *supplied* update family `U`," never as "generates its own dynamics." See §4.

---

## 2. The rung climb — each rung: forced object · the test · the flip-control · installed boundary

A rung counts only if the rung below it is done. Each rung's test is **"compute it + a control that flips it."**

### Rung 0 — the probe quotient `Q = X/~_P` · **FORCED (fleet 7/7)**
- **Forced object:** the finite partition `Q = X/~_P` with the canonical projection `q: X → Q` (= the probe-outcome fingerprint table). **No numbers, order, algebra, metric, measure, dynamics, `ω`, non-commutativity, or Hilbert structure.**
- **Test:** compute `Q`. **Flip-control:** erase one probe → classes **merge**; add one → classes **split**. (This is the GOLD 1q sim, `distinguishability_quotient_floor_v0`.)
- **Installed boundary:** everything above is NOT forced here.

### Rung 0.5 — Boolean structure / counting · **HELD FORK (do not collapse)**
- The Boolean lattice of `P`-invariant subsets: readings split on whether it is *forced* (needed to compose exclusions) or merely a *derived/dual* representation of `Q`.
- **Counting / cardinality:** CONTESTED. One reading says integer cardinalities are the first forced step; others deny fiber multiplicities under strict nominalism unless primitive individuals of `X` are already admitted (the **individuation objection**, §3). Mark as an open fork; do not assume numbers are forced.

### Rung 1 — admissibility / survivors · forced **only once a constraint `C` is supplied**
- **Forced object (given `C`):** the survivor sub-partition `{ classes of Q surviving C }`.
- **Test:** which classes survive `C`. **Flip-control:** relax `C` → more survive.
- **Note:** requires SUPPLYING `C` (datum beyond `P`). Still static/Boolean → **commutes**.

### Rung 2 — order / non-commutativity · forced **only by supplied update operations**
- **Forced object (given two updates `A,B`):** an order-dependent survivor structure **iff** `∃` class with `(B∘A) ≠ (A∘B)` on `Q`.
- **Test:** compute both composites on `Q`. **Flip-control:** the fixed-reference / static version commutes (a near-tautology — set intersection).
- **Critical:** static exclusions **commute**. Non-commutativity is **installed** via a supplied update family that does not descend to `Q`. (This is exactly where `survivor_set_running_mean_threshold_noncommutation_v0` landed: the order-dependence needed a *supplied* non-local rule; it did not fall out of the static structure. Fleet-confirmed.)

### Rung 3 — state-functional `ω` · **installed** unless weight/frequency/probability data is part of the constraints
- **Test:** enumerate all admissible `ω` consistent with the probe table; if more than one, `ω` is **installed**, not forced.

### Rung 4 — algebra / `ρ` / complex / Hilbert · **INSTALLED, never forced by finite probe data (fleet 7/7)**
- Forced only if an added closure (sign / phase / lift / holonomy / chirality) demands it — the **spinor-as-closure-witness** path — which is itself a *supplied* constraint, not probe data. This **settles the Reading A / Reading B fork toward B**: the bare quotient is the floor; `ρ` is installed.

### Later — geometry, entropy
- **geometry = nested survivor structure** (recomputed per carve). **entropy = distinguishability accounting** — a typed, layer-licensed READOUT, never raw at the foundation (see [[entropic_monism_one_distinguishability_process_DRAFT_20260614]]).

---

## 3. Fleet grounding (wf w1a8hu1g0, 7 independent models, 2026-06-15)

Models: codex2-high, codex2-medium, gemini-3.1-pro, deepseek-v4-pro, qwen3.7-max, glm-5.1, kimi-k2.6. Arbiter: codex2-high.

**Unanimous:**
- **Rung 0 = the bare probe quotient `X/~_P`** (7/7).
- **`ρ` / complex / Hilbert = INSTALLED, not forced** (7/7).
- Finite probe data alone forces **no** carrier stronger than `Q`; `ω`, non-commutativity, `ρ` enter only with **extra supplied constraint/update data**.

**Convergent critiques (load-bearing — fold into the doctrine, do not dismiss):**
1. **MSS smuggles dynamics.** "Survives / evolves / killable" covertly installs a state-update rule + time that static exclusion does not force. → §1 caveat, §4.
2. **The weakness ordering is itself installed.** MSS presupposes an ordering of "weaker/stronger" among structures that is not forced by the probe data.
3. **Individuation / ontology objection.** Starting from a set `X` with probes-as-functions already presupposes primitive individuation: cardinality / entropy presuppose distinct elements *grouped*, not *constituted*, by `~_P`.

**Held divergences (preserved):** Boolean lattice forced vs derived; counting forced vs not; whether supplied persistence can force a minimal transition/history structure (readings 1,2,4 yes-with-data; 3,5,6 warn dynamics is installed).

**Best discriminating test (fleet synthesis).** For any proposed stronger carrier `S` over `Q`: reduce `S` to its quotient-level observable invariant, then enumerate all non-isomorphic `S`-extensions compatible with the same probe table **and** the supplied constraints. **If two non-isomorphic carriers give the same quotient behavior, `S` is installed; `S` is forced only if every admissible compatible extension is isomorphic at the observable quotient level.** For non-commutativity: forced only after supplied updates `A,B` have unequal composites on `Q`.

---

## 4. Consequence for the ratchet

The ratchet ("finite ordered exclusion with memory") is **NOT forced by the quotient**. Its order, its update operations, and its memory are **supplied** structure (an installed update family `U` + a supplied memory). This is consistent with — and explains — the emergence-sim result: order-dependence required a supplied non-local rule and did not emerge from static distinguishability. So the honest claim is: *given* a supplied update family, MSS selects the weakest survivor tower; the ratchet is the **installed dynamics on top of the forced static floor**, not a consequence of the floor. The [[ratchet_definition_and_emergence_spec_DRAFT_20260614]]'s R3 (state/history-dependence) is exactly this supplied ingredient.

---

## 5. The sim ladder (owner sim targets → rungs)

From the LevOS bridge packet `08_CODEX_RATCHET_MATH_BRIDGE` (owner's own articulation: root = constraint on distinguishability; MSS = admit minimal survivors; ratchet = finite ordered exclusion with memory; geometry = nested survivor structure; entropy = distinguishability accounting):

| Rung | Sim target |
|---|---|
| 0 (quotient + entropy floor) | `entropy_geometry_coratchet_floor_v0` (entropy ratchets from first support; von-Neumann blocked until earned) |
| 0.5 (presentation consistency) | `finite_ring_checkerboard_support_three_presentation_consistency_v0` |
| 1–2 (survivors + order) | `survivor_set_running_mean_threshold_noncommutation_v0` (built), `geometric_constraint_ratchet_on_ring_support_v0` |
| 3–4 (forced vs installed carrier) | `forced_or_installed_carrier_comparison_v0` (quotient vs `ω` vs `ρ` vs spinor) — the direct discriminator |
| 4 (spinor closure-witness) | `spinor_quotient_freedom_discriminator_v0` (lift admitted only when quotient-erased distinctions are load-bearing) |

---

## 6. Open / next

- The base-sim `forced_or_installed_carrier_comparison_v0` should now be **buildable**: the fleet gives the verdict to reproduce mechanically (rung0 = quotient, `ρ` = installed) and the discriminating test in §3. The prior `finite_distinguishability_quotient_forced_or_installed_carrier_v0` failed because its verdict was predetermined; this one has the fleet's enumeration test as the mechanism.
- Resolve (or keep forking) Rung 0.5: is counting forced? Is the Boolean lattice rung-0 or derived?
- Fold the §1 dynamics-smuggling caveat into the completeness contract and the ratchet spec.

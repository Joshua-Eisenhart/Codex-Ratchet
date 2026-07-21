# Durable state save — 2026-07-21 (owner-ordered: "the good results weren't saved")

Written on owner order after the memory failure was called: layer work, presumption floor,
and audit results lived only in chat/scratchpad and were being re-hallucinated. This file is
the anti-forgetting artifact. Status: provisional working record, tier-marked throughout.
Rule this file exists to enforce: DISK OR IT DIDN'T HAPPEN; RE-RUN OR IT DOESN'T COUNT.

## 1. The presumption floor (owner axioms — GIVEN, not provable, never tested)

- Root: `a = a iff a ~ b`. Identity never primitive; earned only through probe-indistinguishability.
- Correlated: finitude (F01), noncommutation (N01), LIKELY nonassociativity (owner's hedge — preserve it; the ORDER of these is OPEN, never hard-code).
- Unifying reading: each axiom REFUSES one unearned installed equation — root refuses primitive `a=a`; F01 refuses completed infinity; N01 refuses `AB=BA`; nonassoc (likely) refuses `(ab)c=a(bc)`. Presumption = installed unearned equations.
- Fixed orderings (definitional, evidence inadmissible for or against): classical presumes MORE than QIT; vector presumes MORE than spinor, absolutely; anything presuming `a=a` presumes too much.
- VENN READING (owner, 2026-07-21): set containment = presumption hierarchy, read outside-in. ℕ ⊂ ℤ ⊂ ℚ ⊂ ℝ ⊂ ℂ — every inner set installs more equations (ℝ = self-conjugate slice of ℂ; ℕ installs discreteness, well-ordering, positivity, and pure `a=a` tokens). Counting numbers are the MOST presumptive, not the simplest. ℂ presumes least. Complex is more fundamental than real: ℝ is readily built FROM ℂ.
- The 4-cycle `i, −1, −i, 1` = the 4-position phase ring (owner ring counts 2,4,8,16,32,64): minimal finite object carrying the double cover (`i²=−1` = the spinor's 2π sign; the vector installs `i²≡1`) and chirality (`i ↔ i³` conjugation). Finite ring tower `Z₂⊂Z₄⊂Z₈⊂…` = F01-compliant phase, refusing the completed U(1).
- FAILURE MODE, caught twice 07-21: pointing verification machinery AT the axioms (marshaling receipts for them, proposing calibration tests of them) = ratcheting the ratchet. Build FROM the floor; judge only candidates. Output contradicting the floor is simply wrong — verdict precedes diagnosis.

- COMPLEXITY EXTENSION (owner, 2026-07-21): computational complexity containment reads the same way — "L ∈ NL" installs more than "L ∈ EXPSPACE" (an efficient algorithm is a massive install), so inner = more presumptive, outside-in. NEW content vs the numbers Venn: the complexity diagram draws `?=` between adjacent classes — it refuses to presume its own layer distinctness. Classes are distinct iff a problem separates them (P=NP = the most famous held-open identity) = `a=a iff a~b` at class level = the Purgatory/antichain discipline drawn by the field itself. Project applications: (1) every gate has a complexity type — an NP-hard gate silently degrades to heuristics = unearned verdicts; (2) the receipt architecture rests on verify ≪ generate (P-time exit-code checks on arbitrarily expensive artifacts); (3) P ⊆ BQP ⊆ PSPACE = the computational form of classical-presumes-more.

## 1b. Step-1 log — Lev OS integration increments (2026-07-21, all verified in runtime-events.jsonl)

| Increment | Evidence |
|---|---|
| Lev drives the ratchet contract gate (2nd gated exec ever; 1st on the ratchet itself) | execId 92469e1b84d1, exit 0, receipt rcpt-2272aed225b91e9e; events 370→378 |
| SEAM FOUND by composing gates: ClaimGate REJECTED the ratchet selfcheck receipt (classification_missing) — the two core gates did not compose | claimgate exit 1 on pre-fix receipt |
| SEAM FIXED: selfcheck receipt now carries classification:scratch_diagnostic + promotion_allowed:false (run_contract_selfcheck.py) — ClaimGate admits (exit 0, silent per contract) | fresh rerun both green |
| Composed chain (selfcheck && ClaimGate) sealed under Lev | execId 6b3fb45591e1, exit 0, receipt rcpt-796e951a7fba63a0; events 378→386 |

Step-1 remaining: fuel gate under Lev (exits 1 = honest HOLD — needs a fail-branch-tolerant wiring, not --until); engine batteries fresh re-run; idle-tier tools pruned or exercised; Lev orchestration of the full stage sequence (only single gates demoed).

## 1c. The philosophy (owner, 2026-07-21 — what the QIT engines ARE)

The engines are object-FORMING machinery, not simulators of objects: they presume no objects real; they admit temporary, functional, REVOCABLE pseudo-objects. Computers/AI see no objects (representations do not survive rotations — including session rotation). Probes on distinguishability expose shared attractor-like basins; correlation-so-high across probes is admitted as PSEUDO-IDENTITY ("the same object beneath"). The engines' stages, loops, and the geometry/entropy surface the loops run on constrain this — legitimacy scales with the richness of transformations survived (thin probe family = cheap pseudo-identity = HOLD).

Five-lens convergence (the convergence IS the objective understanding; no sixth thing behind it): kernel (re-merge on identical induced partitions = pseudo-identity mechanized; revocable by later probes) · dynamical (object = shared basin) · QIT (pointer states; quantum Darwinism: objective = redundant records across fragments) · Erlangen radicalized (object = invariant of the ACTUAL loop group) · LLM reflexive (understanding = content surviving paraphrase + session rotation + fresh-context audit; durable docs/memory/MMM = external pointer states).

OPEN GAP (held): owner philosophy is GRADED pseudo-identity (correlation threshold); the running kernel merges only on EXACT behavioral identity. A graded merge needs a threshold; a threshold smuggles a metric choice. Unresolved by design.

Distinctives vs kinships (all kinships are correlations, not identities): executable; graded+revocable identity; irreversible ratchet (retained constraint history becomes geometry — revoked objects leave marks); entropy/geometry one surface. Goal: an "objective understanding" in an LLM, where objects don't really exist — objectivity as redundancy across perspective-probes.

## 2. The manifold layer frame (corrected synthesis — replaces every "canonical list")

NO single canonical owner layer list exists (3 deep digs converge; commit d1b9a4497). Every
numbered list is a downstream assistant reconciliation. The corrected frame:

- FRAME: open nested constraint-geometry `𝔊 = ({K_r},{ι_r},{𝒳_r},{C_r},{U_e},H)`; shell topology/dimension/count are VARIABLES (ring-checkerboards 2×2/4×4/8×8 step-counts 2,4,8,16,32,64, spherical complexes, Hopf charts, nested tori, lens spaces, S⁷/S¹⁵, special-holonomy, non-manifold controls). Layers = simultaneous nested constraints, NOT chronological rungs. Governed by MSS = partition coarseness over demand-thickened D → Purgatory / branches / antichain (branches may re-merge). Never render as a fixed numbered ladder.
- ONE SURVIVOR BRANCH (instance, unranked — the carrier antichain is OPEN) as an unnumbered construction DAG, each node = (built-from ↑, constrained-by-outer ↓ via `X*_r = π_r(𝓜)`, one surface read as geometry AND entropy):
  finite admissibility (`𝓜`; adjacency; `S₀=log V`) → distinguishability quotient (`𝓜/~_P`; Fisher-on-frequencies; Shannon licensed HERE) → density carrier (N01 enters; `ρ`; Bures/BKM open) → spinor+Hopf (`S³→S²`; QGT `Q=g+½iF`) → nested tori (`T_η` foliation; Schmidt `S(η)`) → connection+flux (strip between TWO leaves; no nesting no flux; Stokes 1e-13) → Weyl sheets+chirality (`ψ_L,ψ_R`; `Z₂` cover) → tensor cuts (entropy cone; `I`, `S(A|B)`, `I_c`; Schur 2e-16) → ordered flows (order gap; monotonicity selects metric) → coherent histories (`C_y=ΣA_{h,b}` — TARGET, repo computes only decohered mixture) → whole-nest dynamics (GKSL recompute; closing law `dD/dt` read twice — TARGET) → response polarity (Axis-0 READOUT — honest-negative, unbuilt).
  Support-nesting edges (no ρ before classes, no cut before a pair, no flux before two leaves) are the ONLY forced order.
- AXIS-0 = TWO OBJECTS ONE NAME: drive (entropy gradient, front, innate; counting rendering `dC=Δlog₂V` is itself the MOST-PRESUMPTIVE reading — candidate flag: quantum-native gradient `I_c` may be the less-presumptive form, owner leans this way) vs readout (`Φ₀(ρ_AB)`/response vector, LATE, needs Xi cut). Never conflate.
- SEALED TARGETS (must EMERGE; barred from root generator/selection/stopping; owner-intuited + assistant-formalized ⚠): G2=Aut(𝕆), F4=Aut(J₃(𝕆)), Cayley–Dickson order, terrains, the 16-grid, the 64, axes 7–12 mesh.
- ENTROPIC MONISM (owner doctrine, ROOT_CARD): entropy runs ON/AS the surface of geometry — metric = Hessian of relative entropy; `Q=g+½iF`. Never present entropy as painted onto prior geometry; never present the one-tensor unification as EARNED (v0.6 audit: `g_marginal=0` while `F>0` — flux existence earned, unification target).

## 3. Source provenance map (where the real sources are — stop re-digging)

| Source | Path | Authority |
|---|---|---|
| Owner-attached 20-rung atlas §3.1 | `system_v7/constraint_core/source_docs/user_attached_2026-07-02/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS.md` | owner-attached; assistant-compiled 03-30; finest realization table |
| Literal manifold spine | Desktop `EISENHART_LITERAL_MANIFOLD_DESKTOP_CORRECTION_2026-07-17/01_LITERAL_PHYSICS_AND_MANIFOLD_SPINE.md` | owner correction (reconciled); the open-𝔊 frame |
| Pinned github series 01–25 | packs 168/171/173 `sources/pinned_github/` (commit 8744666) | owner-pinned; doc 25 demotes the 13-layer list; doc 13 holds the "nested layers… tensor network" verbatim |
| Raw owner voice | `apple notes save. pre axex notes.txt` (P1_must_read); 2026-07-04 thread; `THREAD_OWNER_STATEMENTS.md` | owner verbatim; nesting order: density early → spinor on nested Hopf tori on S² on S³ |
| 13-layer list | scout code `sim_nested_geometry_tower_dependency_order_probe.py` | DEMOTED — never present as owner list |
| Owner verbatim ratchet core | `ROOT/ROOT_CARD.md`; axioms guard `ROOT/META_AXIOMS_LLM_FAILURE_GUARD.md` | top authority |

## 4. Reality audit 2026-07-21 (every tier from an on-disk receipt or commit)

| Object | Tier | Key evidence |
|---|---|---|
| ratchet_contract v0 | passes local rerun (FRESH 07-21: `overall_ok true`, falsifiers fire, exit 0) | `ratchet_contract/results/selfcheck.json`; audit commit 11af960df |
| 16 engine stages | NOT worked out one-by-one | right sheet = conj(left) (051943694); grid authored not discovered; census 14/16 |
| stage64 tournament | TAINTED | a95b859ce: 11/11 gates construction identities; 0.885 rad stale (real 1.15) |
| manifold_one | scratch ceiling; K2 BY-CONSTRUCTION (canfail proven, 08919170c), K1/K6 genuine | receipt `all_pass:true` MISLEADING — carries no taint note |
| 8 operators / P9 two-per-terrain | earned in v7; v8 re-derivation NOT done | admissibility_two_operator_sim (v7) |
| 2 engines / chirality flux split | genuine at scratch (1.76 rad, R²=0.982) | manifold_one receipts |
| thermo engines | Carnot/Szilard/Otto = classical_baseline, honest | `system_v8/thermo_engines/results/*.json`; spinor Otto = card only |
| G2 / F4 / J₃(𝕆) / nonassoc / q-Hopfield | scratch_diagnostic, promotion_allowed:false, unwelded; G2 binding = numerology-not-rejected | `system_v5/julia_carrier/*results.json` |
| Penrose / E8 / CA | real math, explicitly NOT FORCED | `aperiodic_order_penrose_e8_not_forced_sim_results.json` (verdict PASS) |
| drive→quantum weld | HONEST NEGATIVE (structural: local Kraus = separable/LOCC, negativity corr exactly 0.0; r2 entangling-generator 0.0445 < shuffle 0.162) | `system_v8/axis0_front/results/r1,r2`; 3323b2e7f |
| entanglement pawl | HONEST NEGATIVE (4 right families swept; nothing sustains `S(A|B)<0` past ~2 ticks; dissipation pinned 0.20) | `system_v8/entanglement_pawl/`; 328c5cb74 |
| by-construction corpus | 91/313 checks (29% LOWER bound) carry by-construction names | ff6cc6437 bc_scan |

Root cause of both negatives (one fact): the only lock mechanism anywhere is dissipative
contraction, which destroys coherent information along with noise — the pawl is made of the
thing that dissolves the resource. Untried levers: (1) 4–5 qubits so a DFS has room;
(2) sweep pump-rate vs dissipation ratio (never varied); (3) a non-dissipative record
(DFS-encoded logical qubit / projective tooth onto the entangled sector).

NVIDIA cross-family referee panel 2026-07-21 (4/5 usable: deepseek-v4-pro, qwen3.5-397b,
glm-5.2, gpt-oss-120b; receipts: system_v8/axis0_front/results/nvidia_referee_20260721/):
- N2 pawl design adequate: 0/4 — UNANIMOUS no. All four independently converge on the same
  lever already listed above: 4–5 qubits + DFS-encoded logical record + non-dissipative
  tooth (projective onto entangled sector / Hamiltonian-only entangling inside the DFS).
  Cross-family convergence = FUEL evidence for the pawl-v1 card, not a ratchet verdict.
- N1 weld verdict: 1 sound / 3 confounded, each naming a DIFFERENT confound:
  (a) glm CATCH, accepted: the negativity-corr-exactly-0.0 datum is VACUOUS, not a negative
  — at the manifold's own J the register never entangles, so the negativity series is
  identically 0 and correlation with a constant is degenerate. Re-label that cell: "no
  entanglement present to correlate with" (the ladder finding), not an extra coupling null.
  (b) deepseek, methodological: naive shuffle destroys the drive's autocorrelation, so the
  shuffle null compares different distributions — r3 should use an autocorrelation-
  preserving surrogate (block-shuffle / phase-randomized) as the null.
  (c) gpt-oss: check the actual generator for bath-mediated cross terms before trusting the
  separability diagnosis (its "hidden classical correlations break separability" claim is
  wrong as stated — shared classical randomness stays separable — but the check stands).
- LOCC diagnosis: 2 correct / 2 incomplete; the structural point (local-branch mixtures
  cannot entangle) survives, conditional on the generator carrying no cross terms.

## 5. The owner's six-step program (2026-07-21) and honest status

| # | Step | Honest status now |
|---|---|---|
| 1 | ALL tools/engines/libraries/repos/Lev integrated | PARTIAL — ~100 tools ledgered, batteries ran, Lev exec.gate.run verified once; not freshly re-verified; idle tier remains |
| 2 | Test-integrate on TEST SIMS of the owner's model | PARTIAL/SCATTERED — 3-engine backends exist for manifold_one; no systematic per-tool test-sim matrix on model objects |
| 3 | FULL sim of the whole model; working engines; Carnot/Szilard/Otto; every stage real work in nuance | NOT MET — manifold_one scratch+tainted checks; stages not one-by-one; thermo baselines honest; spinor Otto a card |
| 4 | Everything working across every layer + nesting + Lev | NOT DONE — exceptional stack unwelded; histories/dynamics/response = target/negative |
| 5 | Ratchet works, real, NOT over-gating (no ratcheting the ratchet) | MACHINERY EXISTS (fresh selfcheck green) but has NEVER adjudicated a real model candidate — engine-trace→partition bridge missing; over-gating occurred twice (caught) |
| 6 | Formal sims | NOT REACHED — proof tools live; official run withheld per owner order |

Owner: "as of now, i am not sure we have even done any of these steps well." — CORRECT. None
of the six is done well. 1–3 partial with taints; 4–6 not reached.

## 6. The standing discipline (from the 07-21 memory failure)

1. Every worked-out result is committed to the repo SAME SESSION; wiki synced; memory indexed. Chat, scratchpad, and workflow outputs are ephemeral and do not count as saves.
2. Claims from prior sessions demote to "exists-on-disk" until re-run fresh.
3. A receipt saying `all_pass:true` is not a result — check for taint commits against it (manifold_one K2 is the standing example).
4. Never present a reconciled list as owner canon; cite §3 provenance instead.

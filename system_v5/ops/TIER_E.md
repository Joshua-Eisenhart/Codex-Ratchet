# Historical Tier E Proposal — Composed Axis0 Candidate

Status: historical/postponed proposal. This file is not current Axis0 admission
authority. Current v5 formal-scout/readiness status keeps Axis0 open and denies
final manifold, real-basin, Axis0 theorem, bridge, engine, physics, and
Holodeck promotion unless a later explicit promotion manifest and current
validators say otherwise.

> Historical worker preamble from the old plan, not current Codex instruction:
> spawned Claude workers received Block B from `~/wiki/harness/SALIENCE_PREAMBLE.md`.


Runs after Tier D (boundary UNSAT certificates). L3 + owner collaboration — research tier, NOT a low-reasoning mechanical job.

Preconditions:
- Tier D gate GREEN: 4 boundary UNSAT certificates re-verified at `~/wiki/projects/codex-ratchet/tier_d_audit.md`
- Harness primers 02, 06, 07 read (constraint admissibility, coupling order, UNSAT primacy)
- Tier B shell-local reports for all 5 layers present
- Tool-pair integrations from Tier A DONE (z3+sympy, sympy+PyG, PyG+torch, Clifford+sympy, cvc5+sympy, TopoNetX+PyG)

## Objective

Build a candidate composed Axis0: ∇I_c lifted through the full composed-manifold
proposal, not flat 3-qubit Hilbert.

Replace the flat-substrate `classical_baseline` Axis 0 result (`I_c = 0.647`) with a candidate composed run on:

```
π = Pauli ∘ Flux ∘ Weyl ∘ Hopf ∘ G-stack
```

simultaneously constrained at each layer per the historical Tier D proposal.

## Why this tier is NOT for low-reasoning Hermes

1. Composition operator π has no canonical form in literature — requires research judgment on:
   - which Hopf fibration class (S¹→S³→S⁷) carries the Weyl spinor
   - which G-stack root system admits that Hopf class (from D1 UNSAT set)
   - how flux orientation couples through spinor chirality (from D3)
   - how Pauli axes project onto flux-carrier basis (from D4)
2. Gradient lift through pullbacks is geometric; no boilerplate SIM_TEMPLATE can dictate it.
3. Emergence testing requires holding multiple surviving candidates simultaneously per harness/09.

Opus (L3) drafts each step. Owner confirms judgment calls. Hermes executes only the mechanical scaffolding slices.

## Ordered slices

### E1 — Composition operator π in sympy (symbolic skeleton)
- Scaffold at `system_v4/probes/axis0_composition_scaffold.py` (Opus provides)
- Symbolic `π` maps states at each layer through admissibility predicates from D1-D4
- No numerical eval yet — pure symbolic
- Gate: `π(|000⟩_substrate)` symbolically evaluates to a typed expression on the composed manifold

### E2 — Layer-pullback gradient lift
- Define `∇I_c` on the composed manifold using PyG autograd + sympy symbolic differentiation
- Recover classical ∇I_c at the flat-substrate limit (sanity check, not canonical claim)
- Per-layer gradient contribution reported separately (G-stack, Hopf, Weyl, Flux, Pauli terms)
- Gate: gradient defined, limit-check passes, manifold-native gradient differs measurably from flat

### E3 — Simultaneous admission run
- Execute `π` with all 4 boundary predicates enforced simultaneously (per harness/06 constraint_manifold_simultaneous)
- NOT a sequential ladder — each layer's admissibility predicate is active throughout
- Use z3/cvc5 (load-bearing) to verify no admissibility violation during evaluation
- Gate: engine runs without predicate violation; result JSON includes per-layer admission trace

### E4 — Candidate composed Axis0 sim
- `system_v4/probes/axis0_canonical_composed.py`
- Full SIM_TEMPLATE compliance
- proposed classification in the historical plan was `canonical`; current use requires fresh repo authority and validators before any such label is admitted
- `TOOL_INTEGRATION_DEPTH` with ≥3 load-bearing tools (z3 OR cvc5 for predicates, sympy for composition, torch/PyG for gradient)
- Positive: I_c > 0 admitted at some composed point
- Negative: UNSAT certificate that flat-substrate I_c > 0 CANNOT be substrate-invariant (ties back to D-tier exclusions)
- Boundary: degenerate Hopf class on trivial G-stack → I_c = 0 as expected floor

### E5 — Emergence test
- Per harness/06 step 5: what property appears only when all layers simultaneously active?
- Candidate: "I_c gradient requires the composed manifold" — if ∇I_c collapses to the flat limit under any single-layer collapse, emergence is real
- If no emergence found → Axis 0 may be reducible; report honestly
- Gate: emergence property identified OR formally ruled out (both are valid outcomes)

### E6 — Orthogonality re-verification against composed Axis 0
- Re-run `orthogonality_axis0_axis{1,2,4,5,6}_sim.py` against composed Axis 0, not flat
- Expect some prior orthogonalities to break — that's signal, not bug
- Report the orthogonality matrix change
- Gate: orthogonality matrix rebuilt

### E7 — Memory + doctrine updates
- Update memory `project_axis0_status.md` only if a fresh admitted result exists; do not replace flat-substrate claims from this historical proposal alone
- Update `CLAUDE.md` Phase 7 table to reflect actual migration state
- Reflect composed vs flat distinction in `~/wiki/concepts/axis0.md`

## Judgment gates owned by owner

- E1: which Hopf fibration class is admissible on the chosen G-stack root system (multiple survive D1; pick one or hold multiple)
- E2: whether gradient normalization uses flat-manifold volume or composed-manifold volume
- E4: what constitutes a "meaningful" I_c threshold on the composed manifold
- E5: interpretation of emergence result

## Anti-patterns (critical for E)

- Collapsing multiple surviving Hopf/Weyl candidates into one "the correct composed Axis 0" — per harness/09, preserve divergence
- Treating E4 `classification: canonical` as final truth about ontology — per harness/02, it's a surviving candidate under the E-tier constraint set
- Forward-evolving ∇I_c without backward-admissibility check at each layer — per harness/02, these are separate and must not be conflated
- Using numpy directly for gradient — per `feedback_no_fallbacks`, geometry must be computed through Clifford/PyG/torch_ga, not flat linear algebra

## Reporting

- `~/wiki/projects/codex-ratchet/tier_e.md` gate evidence
- `~/wiki/projects/codex-ratchet/tier_e_emergence.md` emergence result (positive or negative)
- `~/wiki/projects/codex-ratchet/tier_e_orthogonality.md` rebuilt matrix
- Opus summarizes in <200 words for owner; owner confirms gate transitions

## Post-gate: Tier F launches

Per `system_v5/ops/TIER_F.md`, axes 1-6 inherit Tier B/C/D/E legos. Re-verification, not re-construction.

# A2 ALT-MODEL MINING PLAYBOOK (for Pro / high-quality mining)
# Status: WORKING_SPEC (noncanonical). This is a process artifact.
# Updated: 2026-03-01

## Objective

Use strong external mining (e.g., ChatGPT Pro) to expand **many related models** (Carnot/Szilard/FEP/etc.) into:

1) **multiple non-smoothed narratives** (steelman + devils + rescue paths),
2) **explicit classical graveyard** (what is classical residue, why it fails, how it is detected),
3) **QIT/operatorized candidates** (explicitly labeled overlays, not canon),
4) **ratchet branch plans** (what terms to target, what negative classes to force, what sims to bind).

This is not “summarize a theory.” It is “turn a theory into ratchetable fuel with explicit failure surfaces.”

## Non-smoothing rules (hard)

- Do not reconcile contradictions; preserve them as separate artifacts.
- Do not collapse variants; keep branch families explicit.
- Do not “fix” the model by inventing missing premises; if missing, log as a gap.
- Any claim that smells like time/trajectory/teleology/commutation/continuum/ontology must be tagged.

## Output artifact set (minimum)

For each **source model** (e.g., “Carnot engine”, “Szilard engine”, “FEP/Active Inference”, “Eisenhart TOE physics overlay”):

### 1) TOPIC_CONTEXT_MAP
- What the model is trying to do (intent).
- What it assumes (premises).
- What it optimizes/claims (targets).
- Key terms (with stable names).
- Contradictions/tensions (explicit).

### 2) CLASSICAL_RESIDUE_GRAVEYARD
Create an explicit table of “classical residues” with:
- residue_id (long explicit name)
- residue_kind (time/commutation/continuum/ontology/teleology/probability/etc.)
- minimal quote or locator (if available)
- failure mode under constraints (what should kill it)
- negative_class mapping (NEG_* token expected)
- minimal rescue transform (operator rewrite or boundary tag)

### 3) QIT_OVERLAY_CONVERSION
Produce **multiple conversion variants** (do not pick one):
- Variant A (minimal operatorization)
- Variant B (strong QIT overlay)
- Variant C (boundary-only / probe-only)

Each variant must include:
- operator-order declarations (explicit noncommutation)
- explicit “NO TIME SEMANTICS” policy or declared optional time-lens
- explicit ontology firewall (“candidate overlay only”)

### 4) RATCHET_BRANCH_PLAN
Turn the above into a concrete branch plan:
- Target term list (explicit long names)
- Promotion tier guesses (T0..T6)
- Required negative sims (by NEG_* class)
- Required rescue lineage (RESCUE_FROM required count)
- SIM observables (what to measure; what counts as pass/fail)

### 5) CROSSLINKS (optional but valuable)
Map overlaps between models:
- shared residues (same failure pattern)
- shared operator rewrites
- shared candidate terms/sims

## Naming policy (important)

Names are defs. Prefer long explicit names over short labels.

- Use file/folder names that encode: model, lane, view, version.
- Use stable term ids (snake_case) that include the implied definition.

## Recommended mining roles (one run can emit all)

- ROLE_STEELMAN: strongest coherent version without adding new premises
- ROLE_DEVIL_TIME: force primitive time language into explicit residues
- ROLE_DEVIL_COMMUTATION: force commutation swaps and show order sensitivity
- ROLE_DEVIL_CONTINUUM: force infinite/continuous assumptions into residues
- ROLE_DEVIL_ONTOLOGY: force implicit Hilbert/probability/trajectory “givens” into residues
- ROLE_RESCUER: minimal operator rewrites and boundary tags
- ROLE_PACKAGER: ratchet branch plan + term/sim lists

## Integration points (where results go)

- A2 brain: update `system_v3/a2_state/MODEL_CONTEXT.md` and `system_v3/a2_state/INTENT_SUMMARY.md` with links to new lanes and discovered residues.
- A1 sandbox: convert branch plan to strategy packets (still noncanonical).
- Ratchet: only after conversion to B-grammar and explicit negative sim bindings.


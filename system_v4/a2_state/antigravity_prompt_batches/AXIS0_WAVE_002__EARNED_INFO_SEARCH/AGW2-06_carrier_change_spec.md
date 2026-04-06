# AGW2-06 Carrier Change Specification

## Recommended Model
Strong technical + architecture model (Sonnet or Gemini High)

## Background
AGM-02 (Wave 001) closed the matched-marginal lane with a critical caveat:

> "The matched-marginal lane requires a different carrier (different engine marginals), not a different construction over the existing marginals."
> "Any new sim run must re-run Phase 5A before claiming the matched-marginal lane is open."

The current carrier: two-engine, 8-stage, 4-operator engine running across inner/clifford/outer torus configurations. Its marginals are locally product states. Phase 5A confirms from the optimization side: max marginal-preserving MI = product state (≈ 10⁻¹⁵) across all 12 certified blocks.

Separately: the i-scalar doctrine gap (T1 homeostatic, T2 not-allostatic) also points to the carrier not architecturally separating engine types on the Weyl/chirality axis.

## Task
Specify exactly what carrier change would re-open the matched-marginal lane. Do not run yet — produce a precise, falsifiable spec that can be handed to Codex for implementation.

**Part 1: Audit what "carrier" consists of**
Read `engine_core.py` and `hopf_manifold.py` to identify the exact parameters that define the current carrier:
- Stage count and type sequence
- Operator family (4 operators)
- Initial state distribution
- Torus configuration (η values)
- Engine type (T1 vs T2)

**Part 2: Specify 3 candidate carrier changes**

For each, state:
- What exactly changes (parameter-level)
- Why this change is predicted to produce non-product marginals
- What Phase 5A would need to show for the lane to be re-opened (concrete threshold)
- Risk of introducing new injection artifacts

Candidates to consider:
1. **Multi-stage correlated initialization**: initialize L and R from correlated rather than independent seeds
2. **Non-Markovian stage coupling**: introduce explicit L/R coupling terms in the stage operators (currently the engine runs L and R independently and builds the joint state as a product)
3. **Clifford-only carrier**: run the engine exclusively at η = π/4, which the Phase 6 probe showed is the only geometry where T2 produces allostatic Option D — may have different marginal structure

**Part 3: Select and formally specify the best candidate**

Write a formal carrier change spec:
- Exact parameter changes to `engine_core.py` (or a new wrapper `engine_core_v2.py`)
- The Phase 5A re-run command to validate
- The falsification condition: if Phase 5A on the new carrier returns `product_seed` again in all blocks, that carrier is also closed

## Read
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/engine_core.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/hopf_manifold.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_phase5a_marginal_preserving.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_phase5a_results.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_phase6_clifford_anomaly.json`

## Write

**Return:**
`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/AXIS0_WAVE_002__EARNED_INFO_SEARCH/returns/AGW2-06_carrier_change_spec__return.md`

**Optionally also write** a stub `engine_core_v2.py` or a patch spec doc if the carrier change is well-defined enough.

## Required return sections

- `Current carrier parameters` (exact values from engine_core.py)
- `Three candidate changes with rationale`
- `Selected best candidate with formal spec`
- `Phase 5A re-run command for the new carrier`
- `Falsification condition`

## Anti-smoothing rule
Do not write "a different carrier might help." Either identify the mechanical reason why the current carrier produces product marginals and specify what structural change would break that, or report that no such change is identifiable and the lane needs a different theoretical approach.

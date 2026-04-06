# AGW2-02 i-Scalar Doctrine Gap Attack

## Recommended Model
Opus or strong synthesis model

## Background
The i-scalar sweep (just run, results available) selected **Option C (coherent info)** as the canonical functional with composite score 0.833. But the **doctrine T1/T2 polarity split is absent**:

- T1 homeostatic fraction: 100%
- T2 allostatic fraction: 0%
- Both engine types are uniformly homeostatic under Option C at all ε and all tori.

The doctrine target requires T1 homeostatic AND T2 allostatic. This gap is NOT closed by any composite of C + α·D (Phase 6 Clifford confirms best α = 0.0, no improvement).

The only clean T1/T2 split in the dataset appears in Option D at ε = 0.01 on Clifford for T2 only. Option D is noisy overall (72.2% sign consistency).

## Task
Attack this doctrine gap honestly. Read the actual results and determine:

1. **Is the T1/T2 doctrine split a real requirement or a heuristic?** The typing comes from Grok Unified Physics (T1 = L-handed/cooling/homeostatic bias, T2 = R-handed/heating/allostatic bias). Audit whether the engine's actual architectural difference between T1 and T2 predicts this polarity split or whether the doctrine is an external label pasted onto the engine.

2. **What would a T2-allostatic result actually mean for the bridge problem?** If T2 produces allostatic A0 under some perturbation, what does that tell us about the bridge between T1 and T2 states? Is the T1/T2 polarity distinction load-bearing for Axis 0 closure or is it a side-concern?

3. **Is the doctrine gap a carrier problem or a functional problem?** If we change to a carrier where T2 has measurably different marginals from T1, would Option C split? The current engine produces T1 and T2 with nearly equal |A0_C| (ratio 0.993). What would need to change in the engine for the ratio to exceed 1.2?

4. **What is the honest controller read on i-scalar selection?** Given the gap: should Option C still be promoted as canonical, promoted with a formal caveat, or kept as "strongest available monotone without doctrine closure"?

## Read
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_iscalar_sweep_results.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_phase6_clifford_anomaly.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/engine_core.py` (lines covering engine_type parameter and what differs between T1 and T2)
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.3.md`

## Write
`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/AXIS0_WAVE_002__EARNED_INFO_SEARCH/returns/AGW2-02_iscalar_doctrine_gap__return.md`

## Required return sections

- `What the T1/T2 architectural difference actually is` (from engine_core.py, not doctrine prose)
- `Whether the doctrine polarity target is earned or imposed`
- `Whether the gap is carrier-structural or functional`
- `Controller recommendation on i-scalar promotion` (with exact wording for the state card entry)
- `What would change the verdict` (concrete falsifier)

## Anti-smoothing rule
Do not write "the gap is a future concern." Either the polarity split is required for doctrine closure or it is not. State which, and why, with the engine architecture as evidence.

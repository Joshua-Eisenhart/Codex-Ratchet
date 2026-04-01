# AGW2-05 FEP/67-33 Adversarial Test

## Recommended Model
Opus or strong synthesis with code ability

## Background
AGM-07 (Wave 001) reported that the brain synthesis has mapped the 67/33 (Bell/History) split to the FEP structure (Prior/Likelihood update) — i.e., the 67% Bell injection acts as the prior, and the 33% history aggregation acts as the likelihood update. This framing has NOT been adversarially tested. AGM-08 explicitly flagged: "Promoting it without a targeted adversarial test would violate the earned-vs-constructed standard this wave was designed to enforce."

There is an existing probe: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_fep_compression_framing.py`

## Task

**Part 1: Run the existing FEP compression framing probe**

```
python3 /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_fep_compression_framing.py
```

Read its output carefully. Determine what it actually tests vs. what FEP requires.

**Part 2: Adversarial test design and execution**

The FEP framing claims: the 67/33 split IS the Bayesian Prior/Likelihood structure of the engine. To adversarially test this:

1. **Alter the split**: Run experiments with Bell weight ∈ {0.10, 0.33, 0.50, 0.67, 0.90} and check whether the winning bridge (max MI under constructive search) tracks the split ratio or is insensitive to it. If the FEP framing is real, the bridge should be maximally informative at the ratio that best balances Prior and Likelihood — not at an arbitrary maximum.

2. **Null hypothesis**: The 67/33 is a parameter, not a structure. Any ratio that maximizes raw MI wins because the Singlet Bell state is being injected regardless of the "FEP" interpretation.

3. **Discrimination criterion**: If the MI vs. split_ratio curve is flat or monotone, the FEP claim is a restatement of "more injection = more MI." If it has a non-trivial optimum near 67/33 that cannot be explained by raw injection level, the FEP framing is earning some structural weight.

**Either extend `sim_axis0_fep_compression_framing.py` or write a new probe** `sim_axis0_phase8_fep_adversarial.py` that runs this split sweep and saves results.

**Part 3: Verdict on FEP promotion**

Based on the results: should "FEP as literal cosmology (Prediction-First)" be promoted from brain synthesis to `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`? State the exact controller decision with the numbers.

## Read
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_fep_compression_framing.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/docs/ENTROPIC_MONISM_ORIGIN_AND_COSMOLOGY.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_phase4_final_bridge.py` (for the Bell injection structure)
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/axis0_phase4_results.json`

## Write

**Probe (if new):** `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_axis0_phase8_fep_adversarial.py`

**Return:**
`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/antigravity_prompt_batches/AXIS0_WAVE_002__EARNED_INFO_SEARCH/returns/AGW2-05_fep_adversarial_test__return.md`

## Required return sections

- `What the existing FEP probe actually tests` (vs. what FEP requires)
- `Split sweep results` (actual MI values per split ratio)
- `Does MI peak at 67/33 or is the curve monotone/flat`
- `FEP promotion verdict` (promote / hold / kill framing)
- `What would change the verdict`

## Anti-smoothing rule
The FEP framing is either structurally load-bearing or it is a narrative overlay. The split sweep result is the arbiter. Do not write "compatible with FEP" — either the curve has a structure that FEP predicts or it does not.

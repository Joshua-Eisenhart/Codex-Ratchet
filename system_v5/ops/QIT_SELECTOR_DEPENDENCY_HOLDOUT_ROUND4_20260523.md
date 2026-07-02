# QIT Selector, Dependency, And Holdout Round 4 - 2026-05-23

Status: local Codex controller run with native review agents and fresh-rerun
validation.

This round followed the review of the first bounded-layer wave. The review
found that the bounded flux scaffold had the right declared stack shape, but
the carrier-to-geometry dependency was numerically degenerate. It also found
that the shell-cut positive was mostly a conditional-mutual-information style
response, not an Axis0 admission; and that IGT/Holodeck scouts needed proper
payoff/held-out tests instead of label separation or same-target reconstruction.

## Review Receipts

Native review lanes completed:

- bounded-layer flux review:
  - scaffold shape is correct: carrier -> geometry -> operator -> closure;
  - current candidate is negative/nonrobust;
  - `all_pass=true` means receipt validity, not scientific survival;
  - next minimal gate is numeric layer-dependency ablation.
- shell-cut response review:
  - finite QIT shell-cut fixture is meaningful;
  - structured response survives the first fixture;
  - signal is mostly CMI-style response;
  - negative coherent information is not established;
  - path entropy did not move.
- IGT/Holodeck review:
  - repaired scouts are structurally valid formal scouts;
  - IGT state sweep is not full population/game dynamics;
  - Holodeck memory ablation is a normalized evidence-update fixture, not a
    full CPTP world process;
  - next minimal gates are QIT payoff selectors and held-out hypothesis-bank
    prediction.

## New Scouts

### 1. Layer-Dependency Flux Ablation

Script:

`system_v5/ops/formal_scouts/sim_layer_dependency_flux_ablation_probe.py`

Result:

`system_v5/ops/formal_scouts/results/layer_dependency_flux_ablation_probe_results.json`

Purpose:

- tighten flux testing so every dependency must be numerically load-bearing:
  carrier-to-geometry, geometry-to-operator, operator-to-closure, and
  closure-to-current;
- run separate `E1` / `E2` cases at 3 and 8 qubits over 6 seeds each;
- compare live stack against carrier-erased, product-geometry,
  detached-operator, order-erased, and closure-bypass controls.

Result:

- `candidate_status = open_or_nonrobust_layer_dependency_flux`
- `case_count = 24`
- `dependency_count = 0`
- `dependency_rate = 0.0`
- `survival_count = 0`
- `survival_rate = 0.0`
- `mean_live_minus_best_control = -0.0511369713`

Reading:

The tightened flux dependency test is a clean negative. The current dense
layered construction does not yet make the layer chain numerically
load-bearing, and live flux loses to controls.

### 2. QIT Payoff Selector Strategy Probe

Script:

`system_v5/ops/formal_scouts/sim_qit_payoff_selector_strategy_probe.py`

Result:

`system_v5/ops/formal_scouts/results/qit_payoff_selector_strategy_probe_results.json`

Purpose:

- map traditional selectors into finite QIT readouts:
  - `maximax = argmax_i max_j utility[i,j]`
  - `maximin = argmax_i min_j utility[i,j]`
  - `minimax = argmin_i max_j damage[i,j]`
  - `minimin = argmin_i min_j damage[i,j]`
- use 16 strategy rows;
- compute utility/damage from finite channel composition readouts:
  target pull, coherence, order gap, entropy cost, and trace-distance damage;
- compare against commuting and label-scramble controls.

Result:

- `candidate_status = open_or_nonrobust_qit_selector_strategy`
- `seed_count = 12`
- `survival_count = 0`
- `survival_rate = 0.0`
- `minimin_specialization_rate = 0.0`

Reading:

The selector translation is now executable, but this first formulation does not
produce stable noncommuting strategy advantages. Minimin is represented as a
real QIT selector, but it did not show the specialized-power signature in this
fixture.

### 3. Science Hypothesis-Bank Holdout Probe

Script:

`system_v5/ops/formal_scouts/sim_science_hypothesis_bank_holdout_probe.py`

Result:

`system_v5/ops/formal_scouts/results/science_hypothesis_bank_holdout_probe_results.json`

Purpose:

- convert the Holodeck/science-method idea into a finite empirical loop:
  hypotheses -> instrument choice -> Born-rule observation -> posterior update
  -> held-out prediction;
- test against wrong-bank, shuffled-observation, passive-prior, and product-bank
  controls;
- require held-out predictive gain instead of same-target reconstruction.

Result:

- `candidate_status = open_or_nonrobust_hypothesis_bank_holdout`
- `seed_count = 24`
- `survival_count = 0`
- `survival_rate = 0.0`
- `mean_heldout_gain = -0.0008884018`
- `max_heldout_gain = 0.0`

Reading:

The science-method conversion is executable, but this static four-hypothesis
bank does not beat controls on held-out prediction. This is a useful negative:
the current toy hypothesis bank is not yet a world engine.

### 4. Shell-Cut Response Stress Probe

Script:

`system_v5/ops/formal_scouts/sim_shell_cut_response_stress_probe.py`

Result:

`system_v5/ops/formal_scouts/results/shell_cut_response_stress_probe_results.json`

Purpose:

- stress the only live round-3 candidate family;
- run 4-qubit and 6-qubit graph-state shell cuts;
- vary graph rewires over 8 seeds;
- compare structured response against product, local-basis, and shell-relabel
  controls;
- keep Axis0 open.

Result:

- `candidate_status = open_or_nonrobust_shell_cut_stress`
- `case_count = 16`
- `survival_count = 10`
- `survival_rate = 0.625`
- `mean_conditional_mutual_information_abs_response = 0.7601611482`
- `mean_path_entropy_abs_response = 0.0283709403`

Reading:

The shell-cut response family remains the most promising candidate area, but it
does not pass the stress threshold. CMI carries most of the signal. Path entropy
is no longer exactly dead in the stress fixture, but it is still small.

## Seven-Scout Validation

Fresh-rerun validated scouts:

1. `sim_stage_capability_state_sweep_probe.py`
2. `sim_shell_cut_axis0_response_probe.py`
3. `sim_holodeck_science_world_memory_ablation_probe.py`
4. `sim_bounded_layered_flux_geometry_probe.py`
5. `sim_layer_dependency_flux_ablation_probe.py`
6. `sim_qit_payoff_selector_strategy_probe.py`
7. `sim_science_hypothesis_bank_holdout_probe.py`
8. `sim_shell_cut_response_stress_probe.py`

Validation:

- filename lint: `all_pass=true`;
- fresh-rerun validation: `all_pass=true`;
- all seven receipts passed formal-scout contract checks.

Important distinction:

`all_pass=true` means the formal scout receipt is structurally valid. It does
not mean the candidate survived. Scientific survival is carried by
`candidate_status`, `candidate_survived`, survival rates, margins, and controls.

## Updated Bottom Line

Current positives:

- the shell-cut response family has one finite 4-qubit structured/product
  contrast fixture and a partial 4/6-qubit stress signal worth continuing;
- the QIT translations for flux-layer dependency, IGT selectors, and Holodeck
  science method are now executable as bounded formal scouts.

Current negatives:

- bounded-layer flux scalar: killed/nonrobust;
- layer-dependency flux: killed/nonrobust, with no passing dependency cases;
- IGT stage sweep: nonrobust;
- QIT selector strategy map: nonrobust;
- Holodeck same-target world-memory ablation: nonrobust;
- held-out science hypothesis bank: nonrobust.
- shell-cut stress: partial signal but still nonrobust at `10/16`.

Claim ceiling:

- no final Axis0;
- no final flux;
- no final IGT/game theory;
- no final Holodeck/world engine;
- no physics, gravity, Standard Model, Yang-Mills, Riemann, or unification
  admission.

## Next Gates

1. Shell-cut stress suite:
   - seed sweep, graph rewires, local-unitary controls, shell relabel controls,
     process-history path entropy, and 6-qubit nested shell extension.
2. Flux rescue/falsifier:
   - replace scalar flux with current-through-cut observable;
   - use MPS/process tensor before 16-qubit runs;
   - require every layer dependency to pass before final readout is scored.
3. IGT game theory:
   - move from single-carrier strategy composition to two-character carriers
     with separate local states/memories;
   - then run selector stability and population dynamics.
4. Holodeck science:
   - replace static four-hypothesis bank with process-tensor memory or an
     updating finite world grid;
   - add multi-step active instrument selection.

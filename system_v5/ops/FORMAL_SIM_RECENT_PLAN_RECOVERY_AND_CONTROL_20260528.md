# Formal Sim Recent Plan Recovery And Control - 2026-05-28

Status: active recovery/control surface. This is not a sim admission, not a
Wizard FULL receipt, not Axis0/FEP/flux/physics proof, and not final manifold
completion.

## What Went Wrong

The plan was not missing. The current thread lost the active plan by letting
later interesting continuations become the priority.

The correct recent plan was:

```text
make the independent manifold layer legos first
make variants/depth/stress for each layer
only then test stacking/order/composition
```

The drifted replacement plan was:

```text
M_RPF post-stack
bond5/bond6 escalation
Wolfram integrated stress
Axis0/FEP/physics-adjacent continuation
```

Those later packets are useful as bounded receipts, adapters, controls, or
future comparison material. They are not allowed to control the formal sim
priority while the layer-depth/variant factory remains open.

## Current Authority Stack For This Plan

Read these before any formal sim continuation:

```text
AGENTS.md
CODEX.md
system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
system_v5/docs/LLM_CONTROLLER_CONTRACT.md
system_v5/docs/LEGO_SIM_CONTRACT.md
system_v5/ops/FORMAL_SIM_LAYER_LEGO_CAMPAIGN_CONTINUATION_GOAL_20260526.md
system_v5/ops/FORMAL_SIM_LAYER_LEGO_FACTORY_V43_REPAIR_GOAL_20260528.md
system_v5/ops/FORMAL_SIM_ACTUAL_LAYER_FACTORY_STANDARD_20260528.md
system_v5/ops/LAYER_LEGO_FACTORY_SHELL_GRADIENT_ALIGNMENT_20260528.md
system_v5/ops/formal_scouts/layer_lego_plan_drift_audit_20260528.json
system_v5/ops/formal_scouts/layer_lego_factory_v43_object_packet_20260528.json
system_v5/docs/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md
system_v5/docs/RETROCAUSAL_POSSIBILITY_FIELD_SIM_AND_WIZARD_METHOD_20260526.md
```

## Current Recovered Truth

From the current repo artifacts:

```text
formal_layer_lego_campaign_matrix_20260526.json:
  continuation_required = true
  L0-L5 = passed_candidate_finite_scope
  L6 = queued_next_after_L5_gate
  L7/L8 = blocked_pending_L6_gate

formal_layer_campaign_contract_alignment_audit_20260526.json:
  L0-L8 have fresh finite-scope rerun receipts
  those receipts are compact layer-lego scouts only
  they are not full manifold layers
  they are not stacked geometry
  they are not final manifold admission

layer_lego_plan_drift_audit_20260528.json:
  verdict = proper_plan_existed_then_priority_drifted
  compact L0-L8 finite-scope receipts exist
  compact L0-L8 are not final layers
  L4/L5/L7 depth-variant packet exists
  layer-depth/variant campaign is not complete
  post-stack/bond/Wolfram receipts do not control next priority
  stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, final manifold stay locked
```

Therefore the next formal run must not trust any one old status surface. It
must first reconcile the current layer estate into a repaired matrix.

## Active Object To Preserve

The primary object is:

```text
ManifoldLayerLegoFactoryCampaign
```

Meaning:

```text
independent source-native manifold layer legos
-> depth/variant/stress rows
-> pass/fail/kill/block/resource-block classification
-> exact continuation to next independent layer row
-> only later stacking/order/composition
```

This object is protected by:

```text
system_v5/ops/formal_scouts/layer_lego_factory_v43_object_packet_20260528.json
```

Wizard v4.3 is a guard for object preservation. It is not the work itself.

## Shell-Gradient Correction

The layer factory must now carry the shell-gradient correction:

```text
literal spherical possibility shells
-> boundary bookkeeping
-> future refinements on the shell
-> inward compression into present
-> outward information record as past
-> entropy/correlation readouts derived from that process
-> survivor geometry
```

Where any layer invokes shell, future possibility, Axis0, FEP, gravity, or
flux, it must preserve:

```text
Sigma_r(x)
i/r shell order
Omega_r(x)
j/k future-fuzz indices
future-inward orientation
past-outward record orientation
rho_Br
rho_IrBr
compatibility weights
compression into rho_present
outward record
readout provenance
```

Axis0 remains downstream:

```text
A0_raw = (
  Delta H_Omega,
  Delta S_B,
  Delta K,
  order_gap,
  chirality_sheet
)

Phi0 = discovered projection(A0_raw)
```

So `entropy`, `I_c`, `logZ`, `logZ + I_c`, `FEP`, `PEPS3D`, `Wolfram`, or
`Axis0` labels are not allowed to become the object.

## The Actual Execution Loop

The next formal run must do this, in order:

1. Validate the v4.3 object packets:

```text
python3 scripts/wizard_v4_3_object_preservation.py validate --input system_v5/ops/formal_scouts/layer_lego_factory_v43_object_packet_20260528.json
python3 scripts/wizard_v4_3_object_preservation.py validate --input system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json
```

2. Build or update:

```text
system_v5/ops/formal_scouts/layer_lego_factory_repair_matrix_20260528.json
system_v5/ops/formal_scouts/layer_lego_factory_continuation_20260528.json
```

3. Reconcile these current artifacts inside that matrix:

```text
formal_layer_lego_campaign_matrix_20260526.json
formal_layer_campaign_contract_alignment_audit_20260526.json
FORMAL_SIM_ACTUAL_LAYER_FACTORY_STANDARD_20260528.md
formal_layer_campaign_completion_audit_20260526.json
formal_layer_L0... through formal_layer_L8... receipts/results
results/l4_l5_l7_depth_variant_bond_sweep_probe_results.json
layer_lego_plan_drift_audit_20260528.json
layer_lego_factory_v43_object_packet_20260528.json
```

4. Do not rerun L4/L5/L7 depth work if current validation says it is fresh.

5. Select the next independent per-layer depth/variant row not covered by the
   repaired matrix.

6. Build or block exactly one bounded layer packet.

7. Validate:

```text
python3 scripts/lint_sim_contract.py <touched scout files>
python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun <touched result files>
python3 scripts/wizard_v4_3_object_preservation.py validate --input system_v5/ops/formal_scouts/layer_lego_factory_v43_object_packet_20260528.json
git diff --check
```

8. Update the repaired matrix and continuation.

9. Continue to the next independent layer row. Do not stop because one packet
   passed.

## Required Row Fields

Each layer row must include:

```text
layer_id
variant_id
finite_map
domain
codomain_or_output
F01 finite carrier/probe/operator/path witness
N01 noncommuting/order-sensitive witness
PEPS3D K=(V,E,F,C)
torch-native spinor or spinor-derived density where applicable
quaternionic map/invariant where quaternion language appears
source-native spinor/PEPS3D checks
shell-gradient fields where claimed
QIT entropy/readouts tied to finite action where defined
tool manifest/depth
non-vacuous ablation_outcome_delta
8/16/32/64 stress or resource_blocked rung
controls
blocked_consumers
status
next_action
receipt paths
```

## Required Controls

Use the relevant subset:

```text
order-erased control
label-erased control
dense-closure control
NumPy/classical adapter block
PEPS3D label-only control
spinor phase erased
Hopf fiber/base erased
left/right Weyl sheet erased
shell radius/order erased
future-inward/past-outward orientation erased
Omega_r scrambled while counts are preserved
scalar entropy primary
FEP decorative label
Axis0 scalar proxy
Wolfram/ruliad primary-object substitution
post-stack continuation before layer matrix exhausted
```

## Demotion Rules

Demote or block any continuation that does this before the layer factory matrix
is exhausted:

```text
post-stack as active priority
bond5/bond6 as active priority
Wolfram integrated stress as active priority
Axis0/FEP/flux/physics/final manifold as active priority
compact finite-scope receipts marked terminal
scalar entropy passing after shell direction removed
PEPS3D label without source-native spinor carrier
```

## Allowed Salvage

These are allowed only as support for one bounded layer row:

```text
M_RPF fields and controls
Wizard v4.3 object preservation
source-native spinor/PEPS3D runtime design
Wolfram/multiway branch generator
QIT-FEP adapter
post-stack/bond stress receipts
```

They cannot replace the layer-lego factory.

## Stop Conditions

Valid stop:

```text
owner stops
runtime/context exhaustion after exact continuation artifact is written
all layer-depth/variant rows are passed, killed, blocked_with_receipt,
resource_blocked, or queued/running with exact continuation
hard resource blocker applies to every remaining independent layer row
```

Invalid stop:

```text
one scout passed
one validator passed
one matrix says green
post-stack ran
bond5 ran
Wolfram ran
Axis0/FEP proxy passed
no next row chosen
```

## Copy-Paste Short Prompt

Use the long prompt in:

```text
system_v5/ops/FORMAL_SIM_LAYER_LEGO_FACTORY_V43_REPAIR_GOAL_20260528.md
```

If a shorter prompt is needed:

```text
You are in /Users/joshuaeisenhart/Desktop/Codex Ratchet. Restore and continue the formal manifold layer-lego factory. Read AGENTS.md, CODEX.md, the three process docs, system_v5/ops/FORMAL_SIM_RECENT_PLAN_RECOVERY_AND_CONTROL_20260528.md, system_v5/ops/FORMAL_SIM_LAYER_LEGO_FACTORY_V43_REPAIR_GOAL_20260528.md, system_v5/ops/LAYER_LEGO_FACTORY_SHELL_GRADIENT_ALIGNMENT_20260528.md, and the current L0-L8 source/result/ledger files. First validate the layer factory v4.3 object packet and RPF v4.3 object packet. Build/update layer_lego_factory_repair_matrix_20260528.json and layer_lego_factory_continuation_20260528.json. Reconcile compact L0-L8 receipts, the L4/L5/L7 depth packet, and the drift audit. Do not choose post-stack, bond5/bond6, Wolfram, Axis0, flux, FEP/Holodeck, physics, or final manifold unless the repaired matrix proves every layer-depth/variant row is passed/killed/blocked/resource_blocked/queued. Select the next independent per-layer depth/variant row, build or block exactly one bounded layer packet, validate lint/fresh-rerun/v4.3/git diff, update matrix and continuation, and keep going. Every shell/Axis0/FEP/gravity/flux-facing row must preserve Sigma_r, i/r, Omega_r, j/k fuzz, future-inward and past-outward orientation, rho_Br, rho_IrBr, compatibility weights, compression, outward record, and readout provenance. Axis0 is downstream A0_raw before Phi0, not entropy/I_c/logZ. FEP is derived prediction/evidence/posterior compression, not an imported label.
```

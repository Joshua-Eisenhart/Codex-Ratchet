# Long-Running Goal: M_RPF Bond-5 And Wolfram-Upgrade Stress Campaign

Status: launch goal for the formal TUI. This is a continuation of the current
M_RPF(C) formal-scout lane, not a new theory lane and not final manifold
admission.

## Current Truth To Preserve

The post-stack tranche from `FORMAL_SIM_M_RPF_POST_STACK_LONG_RUNNING_GOAL_20260527.md`
completed. Do not duplicate it unless validation says a result is stale or
contradictory.

Current accepted bounded receipts:

```text
system_v5/ops/formal_scouts/results/m_rpf_post_stack_stress_probe_results.json
system_v5/ops/formal_scouts/results/m_rpf_post_stack_variant_stress_probe_results.json
system_v5/ops/formal_scouts/results/m_rpf_post_stack_adversarial_object_audit_probe_results.json
system_v5/ops/formal_scouts/results/m_rpf_post_stack_minimality_order_necessity_probe_results.json
system_v5/ops/formal_scouts/m_rpf_post_stack_tranche_progress_20260528.json
system_v5/ops/formal_scouts/m_rpf_post_stack_continuation_selector_20260528.json
```

Current bounded Wolfram-style adapter receipts, also not promotion evidence:

```text
system_v5/ops/formal_scouts/results/wolfram_multiway_shell_adapter_fit_probe_results.json
system_v5/ops/formal_scouts/results/wolfram_multiway_shell_usefulness_deep_probe_results.json
system_v5/ops/formal_scouts/results/wolfram_toe_feature_adapter_matrix_probe_results.json
system_v5/ops/formal_scouts/results/wolfram_hypergraph_peps3d_support_fit_probe_results.json
system_v5/ops/formal_scouts/results/wolfram_shell_toolkit_scale_probe_results.json
system_v5/ops/formal_scouts/results/aligned_model_adapter_matrix_shell_probe_results.json
```

Source-native runtime design input to preserve inside this goal:

```text
/Users/joshuaeisenhart/Desktop/source-native-spinor-peps3d-runtime-design.md
```

That design is source context for this launch prompt. Because it may not be
synced into the current online repo, do not rely on the path alone. The runtime
requirements below restate the parts that must govern this goal.

Known current next bounded map:

```text
M_RPF_post_stack_bond5_admission_micro_probe
```

Known operational issue to check first: the monitor heartbeat can be stale if an
old daemon is still running. Before using monitor state, run the monitor once or
restart only the stale monitor process. Do not treat monitor hygiene as manifold
evidence.

## Primary Object

Keep the primary object first-class:

```text
M_RPF(C) = finite PEPS3D-anchored Retrocausal Possibility Field constraint
manifold over finite shell/event carriers.
```

The claim-bearing carrier is not a density matrix by itself. A valid source-
native runtime packet must preserve:

```text
finite K = (V, E, F, C) site/bond/face/cell support
local spinor state psi_v with complex phase
spinor-derived density rho_v as readout, not root carrier
Hopf fiber/base distinction
L/R Weyl sheet sign
terrain generator/action
local operator/channel action
PEPS3D locality and bounded bond provenance
QIT cut/readout tied to a finite carrier action
```

Reject any packet that passes only through row labels, scalar entropy, a Bloch
adapter, dense-state closure, density-only carrier, unsupported flux, or Axis0
as root geometry.

Required object order in every packet:

```text
Omega_r future/refinement branches
-> compatibility weights
-> ordered adapters A0..A8 or explicitly named subset/variant
-> compression map C
-> rho_present / rho_present_stack / rho_present_stress
-> outward_record / outward_record_stack / outward_record_stress
-> derived readouts
```

Wolfram/ruliad/multiway/branchial graph machinery is an adapter family only. It
may help generate, quotient, stress, or audit `Omega_r`; it must not replace
`M_RPF(C)` as the object.

Wolfram translation rule for this goal:

```text
Useful Wolfram-style machinery:
  finite hypergraph rewriting, multiway branching, branchial quotient,
  causal-record controls, observer/coarse-grain stress.

Rejected Wolfram primitives:
  deterministic rule-time as primary, crisp single-rule firing as physics,
  ruliad-as-canon, causal graph time as primitive.

Eisenhart shell replacement:
  rho_{r-dr}(x) = sum_{h in Omega_r(x)} w_h K_h rho_r(x) K_h^dagger
```

In this framing, a crisp Wolfram rewrite is only a degenerate `j=k=1` slice of
the shell possibility system.

## Locked Consumers

Keep these locked through the whole goal unless a later explicit user goal opens
them:

```text
flux
Xi/Phi0
Axis0
Holodeck/FEP
physics/gravity proof
IGT/game theory
axes7-12
PEPS3D closure theorem
final manifold admission
```

## Required Campaign

Continue until every packet below has either a result receipt or an exact blocker
and the continuation artifact names the next admissible finite M_RPF(C) packet.
Do not stop because one packet passes, one validator passes, or one prompt is
written.

### Packet 0: Current-State Reconciliation

Validate current state without broad reruns:

```text
- object packet validates under wizard_v4_3_object_preservation.py
- post-stack packets 1-4 validate as existing results
- monitor reports active_preserved after one fresh monitor check or explicit stale-daemon repair
- Wolfram-style adapter receipts are present and remain promotion_allowed=false
- continuation/matrix agree that bond5 is the next bounded map
- source-native runtime design constraints are restated in the result or blocker
```

If any contradiction appears, repair the artifact or write a blocker before
running new scouts.

### Packet 1: Bond-5 Admission Or Blocker

Run or block exactly this map:

```text
M_RPF_post_stack_bond5_admission :
  (K, event_x, Sigma_r(x), Omega_r, spinor payload psi_v,
   spinor-derived rho_v, Hopf/Weyl/terrain/operator metadata,
   compatibility weights, ordered adapters A0..A8, compression C,
   bond_dim candidate 5)
  ->
  (bond5 admission table, resource residuals, object-order residuals,
   spinor-phase/fiber/sheet/locality residuals, failed controls,
   blocked consumers)
```

Required output if runnable:

```text
system_v5/ops/formal_scouts/sim_m_rpf_post_stack_bond5_admission_micro_probe.py
system_v5/ops/formal_scouts/results/m_rpf_post_stack_bond5_admission_micro_probe_results.json
```

If bond 5 requires dense closure, drops PEPS3D anchor provenance, erases
row-local adapter provenance, collapses spinor phase, collapses Hopf fiber/base,
collapses L/R Weyl sign, demotes terrain/operator actions to labels, or cannot
run within resource bounds, write a blocker and continue to Packet 2 with bond 4
as the bounded maximum.

### Packet 2: Wolfram-Upgrade Function Micro-Probes

Turn the existing Wolfram-style scouts into tool-function receipts, not theory
claims. Each micro-probe must have one tool/function surface, one bounded target,
one positive, one negative, one boundary case, and one demotion condition.

Targets:

```text
rustworkx: branchial/multiway reachability and order-gap graph function
XGI: hyperedge branch-incidence support function
TopoNetX: PEPS3D cell/face support consistency function
GUDHI: branch filtration/persistence stress function
SymPy: rewrite-rule invariant or shell-order identity
z3/cvc5: admissible rewrite/control impossibility or nonpromotion gate
PyG: graph-native PEPS3D support/message route if available
PyTorch: branch density, compatibility weights, compression, readouts
Clifford: spinor/chirality compatibility if used by the branch support
```

If a tool cannot change the claim, record why. Do not import tools decoratively.
Do not call the Wolfram runtime present unless an actual Wolfram/Mathematica
runtime is found and a real command is executed; otherwise record
`wolfram_runtime_available=false`.

### Packet 3: Wolfram-Adapter Integrated Stress

Run a bounded comparison using the admissible Packet 2 tool functions:

```text
W_MRPF_integrated_stress :
  (M_RPF post-stack carrier, finite rewrite family R, branchial quotient Q,
   PEPS3D support K, source-native spinor payload, Hopf/Weyl/terrain/operator
   metadata, compatibility weights, compression C)
  ->
  (rho_present_with_W, outward_record_with_W, baseline_without_W,
   spinor/locality preservation table, delta table, failed controls,
   blocked consumers)
```

Compare at:

```text
site counts: 8 / 16 / 32 / 64
bond dims: 4 and bond5 only if Packet 1 admitted it
shell counts: 2 / 3 / 4 where feasible
branch counts: at least 64 / 128 / 256 if resources allow
```

The pass condition is not "Wolfram helps." The pass condition is narrower:
Wolfram-style machinery changes or constrains branch structure in a measurable
way while preserving the M_RPF object order, source-native spinor/PEPS3D carrier
requirements, and proxy-control collapse.

### Packet 4: Negative And Proxy Controls

Controls must include:

```text
Wolfram/ruliad primary-object substitution
branchial graph primary-object substitution
deterministic rule-time only
naive branch tree without quotient
label-only substage
density-only carrier
Bloch-sphere adapter
spinor phase erased
Hopf fiber/base erased
L/R Weyl sign erased
terrain/operator action replaced by row name
Omega scramble
compatibility-weight uniformization
shell orientation erased
compression before compatibility weights
PEPS3D anchor erased
scalar entropy primary
Axis0 proxy promotion
FEP/Holodeck proxy promotion
flux proxy promotion
Axis0 as root geometry
dense closure
forward-shadow only
```

If any proxy passes as the object, mark the packet strict-false, preserve the
falsifier, repair the next candidate, and continue.

### Packet 5: Row-Wise Weakest-Link Repair

Use residuals from Packets 1-4 to choose one weakest row or adapter family from
L0-L8. Run exactly one bounded repair or blocker for that weakest link.

Do not choose by narrative priority. Choose by the largest residual, weakest
control collapse, missing tool-function receipt, or resource blocker.

### Packet 6: Cross-Model Alignment Audit

Audit whether the Wolfram upgrades are actually useful transform machinery for
Joshua's shell model, and audit whether the source-native spinor/PEPS3D runtime
requirements are actually being used or merely recited.

Required outcomes:

```text
keep: useful finite branch-generation, multiway quotient, branchial/hypergraph support, or causal-invariance-like controls
strip: deterministic rule-time as primary, ruliad-as-canon, observer-physics promotion, non-shell branch semantics
block: any claim to physics/gravity, Axis0, FEP, flux, Xi/Phi0, or final manifold
```

Output a machine-readable audit artifact naming what is kept, stripped, blocked,
and what finite map should run next.

The audit must explicitly state whether the carrier remained:

```text
true spinor network: yes/no
density-only adapter: rejected or leaked
Hopf fiber/base preserved: yes/no
L/R Weyl sign preserved: yes/no
terrain/operator action load-bearing: yes/no
PEPS3D site/bond/face/cell locality preserved: yes/no
Wolfram machinery adapter-only: yes/no
Axis0/Eye/FEP later-reader boundary preserved: yes/no
```

### Packet 7: Continuation Selector

Write a continuation artifact. It must choose one exact next bounded map from:

```text
bond5 repair or bond6 blocker/admission
Wolfram function receipt repair
row-specific weakest-link repair
branch-count/shell-count scale stress
tool-function micro-probe for a missing tool surface
explicit blocker if no finite M_RPF-preserving packet remains
```

Do not write terminal completion unless every packet above has either a receipt
or an exact blocker and no next finite M_RPF-preserving map remains.

## Validation After Each Packet

Use the repo interpreter from the Makefile. Run only relevant checks:

```bash
PYTHON scripts/wizard_v4_3_object_preservation.py validate --input system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json
PYTHON scripts/lint_sim_contract.py <touched scout files>
PYTHON system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun <touched result files>
PYTHON system_v5/ops/formal_scouts/monitor_retrocausal_shell_field_v43.py --once
git diff --check -- <touched files>
```

## Stop Conditions

Allowed stop states only:

```text
1. Packets 0-7 are complete with receipts/blockers and continuation updated.
2. Runtime/resource exhaustion occurs after writing the current packet receipt or blocker and a continuation artifact.
3. A hard contradiction in current artifacts blocks all finite M_RPF-preserving next moves; write exact blocker.
```

Not allowed as stop reasons:

```text
one green scout
one green validator
one monitor repair
one prompt or candidate artifact written
bond5 pass/fail alone
Wolfram adapter pass/fail alone
```

## Reporting

Report only:

```text
finite maps run or blocked
result paths
max sites/bond/shell/branch counts
which controls collapsed
whether M_RPF object order was preserved
whether Wolfram machinery stayed adapter-only
remaining locked consumers
exact next bounded map or blocker
Wizard route truth: FULL only if actual FULL topology ran; otherwise PARTIAL/BLOCKED
```

# Long-Running Goal: Continue M_RPF(C) Through Post-Stack Stress

Status: launch goal for the formal TUI. This supersedes short one-packet
instructions. It is not a request for a single scout.

## Goal

Continue the finite Retrocausal Shell Constraint Manifold campaign from the
current repo state.

Active object:

```text
M_RPF(C)
  = finite PEPS3D-anchored geometric constraint manifold
    whose local cells/shells carry retrocausal shell-field structure
    under active constraint family C.
```

The run must keep working until it completes the full post-stack tranche below
or writes a precise blocker and immediately selects the next admissible bounded
M_RPF(C) packet. Do not stop because one validator passes, one monitor mismatch
is repaired, one candidate artifact is written, or one scout runs.

## Current State To Preserve

Known current state:

```text
M_RPF_stack_0_8 ran and passed as bounded cross-row order-closure evidence.
Result:
  system_v5/ops/formal_scouts/results/m_rpf_cross_row_order_closure_probe_results.json

Monitor mismatch was repaired:
  system_v5/ops/formal_scouts/monitor_retrocausal_shell_field_v43.py
  now reports active_preserved with M_RPF result reports.

Next candidate exists:
  system_v5/ops/formal_scouts/m_rpf_post_stack_stress_candidate_or_blocker_20260527.json
```

Do not rerun `M_RPF_stack_0_8` unless validation says stale. Start from the
post-stack candidate.

## Non-Negotiable Object Order

Every new scout must preserve this order:

```text
Omega_r future/refinement branches
-> compatibility weights
-> ordered adapters A0..A8 or explicitly named subset/variant
-> compression map C
-> rho_present / rho_present_stack / rho_present_stress
-> outward_record / outward_record_stack / outward_record_stress
-> derived readouts
```

Forward evolution, scalar entropy, FEP, Axis0, flux, and PEPS3D labels are not
the primary object. They may appear only as controls, adapters, or derived
readouts with blocked promotion.

## Required Tranche

Complete this tranche in order. A failed packet is useful, but it must produce a
receipt or blocker and the run must continue to the next admissible item.

### Packet 1: Run Or Block M_RPF_post_stack_stress

Use the existing candidate:

```text
M_RPF_post_stack_stress :
  (K, event_x, Sigma_r(x), Omega_r, rho_omega, compatibility weights,
   ordered adapters A0..A8, compression C, finite stress family S)
  ->
  (rho_present_stress, outward_record_stress, survivor tuple, residuals,
   N01 gaps, failed controls, resource blockers, blocked consumers)
```

If it can run, write:

```text
system_v5/ops/formal_scouts/sim_m_rpf_post_stack_stress_probe.py
system_v5/ops/formal_scouts/results/m_rpf_post_stack_stress_probe_results.json
```

If it cannot run, write a blocker artifact with the exact missing finite map,
resource, or provenance failure and immediately select Packet 2 or a narrower
bounded alternative.

### Packet 2: Variant Stress

Stress the object across finite variants without unlocking downstream:

```text
site shapes: 8 / 16 / 32 / 64 where feasible
bond dims: existing max plus one bounded attempt if resources allow
shell counts: at least 2 and 3; add 4 only if cheap
adapter variants: full A0..A8, local drop-one, adjacent swap, and held-out order
```

Required controls:

```text
Omega scramble
compatibility-weight uniformization
compression-before-weights
shell-orientation erased
PEPS3D anchor erased
scalar-entropy primary
Axis0 proxy promotion
FEP/Holodeck proxy promotion
dense closure
forward-shadow only
```

### Packet 3: Adversarial Object-Preservation Audit

Write or run an audit whose job is to break the apparent pass. It must check
whether the scout is actually measuring M_RPF(C), or merely measuring:

```text
PEPS3D labels
entropy readouts
adapter order artifacts
Axis0/FEP/flux proxies
forward-time evolution
dense-state closure
monitor/reporting hygiene
```

If any proxy survives as if it were the object, mark the packet strict-false,
keep the falsifier, and repair the next candidate before continuing.

### Packet 4: Minimality / Order Necessity

Test whether each required part of the M_RPF object is load-bearing:

```text
event_x
Sigma_r(x)
radius/order r
future-inward orientation
past-outward record orientation
Omega_r
rho_omega
compatibility weights
compression C
rho_present
outward_record
PEPS3D K=(V,E,F,C)
torch-native spinor or spinor-derived density
N01 order witness
```

If a part can be removed without collapse, record it as a model repair issue.
Do not smooth it into a pass.

### Packet 5: Continuation Selector

Write the next continuation artifact. It must not say terminal complete unless
all four packets above have either run or produced precise blockers.

The continuation must name the next bounded map from one of these categories:

```text
post-stack stress repair
deeper variant stress
row-specific repair for the weakest L0-L8 adapter
tool/function micro-probe needed by a failed M_RPF packet
blocked-reason artifact if no finite M_RPF-preserving packet remains
```

## Tool And Scale Requirements

Use the repo Python from the Makefile. Use PyTorch as the claim-bearing numeric
surface. Use non-PyTorch tools only when they can change, constrain, or certify
the actual claim.

Expected relevant tool surfaces:

```text
PyTorch/autograd: densities, compression, order gaps, readouts
PyG: graph-native PEPS3D carrier or adapter routing where relevant
rustworkx: finite graph/order/adapter dependency checks
XGI: hyperedge/multiway shell or adapter family checks where relevant
TopoNetX: cell/face/boundary consistency where relevant
GUDHI: filtration/persistence stress where relevant
Clifford: spinor/quaternion/chirality compatibility where relevant
SymPy: symbolic sanity or identity checks
z3/cvc5: structural gates, nonpromotion gates, impossibility/minimality
```

If a tool is omitted, state why it could not change this packet. Do not import a
tool decoratively.

## Locked Consumers

Keep these locked after every packet unless a later explicit user goal opens
them:

```text
flux
Xi/Phi0
Axis0
Holodeck/FEP
physics/gravity proof
IGT/game theory
axes7-12
final manifold admission
```

Passing post-stack stress is still not final stacking closure unless the result
proves closure under the declared finite variants and controls.

## Required Validation After Each Packet

Run only relevant narrow checks, not broad queue churn:

```bash
PYTHON scripts/wizard_v4_3_object_preservation.py validate --input system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json
PYTHON scripts/lint_sim_contract.py <touched scout files>
PYTHON system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun <touched result files>
PYTHON system_v5/ops/formal_scouts/monitor_retrocausal_shell_field_v43.py --once
git diff --check -- <touched files>
```

Replace `PYTHON` with the interpreter from the Makefile.

## Stop Conditions

Do not stop for green validation alone.

Allowed stop states:

```text
1. Packets 1-5 are all complete with receipts/blockers and continuation updated.
2. A hard runtime/resource blocker prevents every remaining finite M_RPF(C)
   packet; write a blocker with exact missing dependency and next admissible
   lower micro-probe.
3. The owner explicitly stops or redirects the run.
```

If a packet passes quickly, continue to the next packet. If a packet fails, keep
the falsifier and continue to the next admissible bounded repair or blocker.

## Output Contract

Report only:

```text
what finite M_RPF(C) map was run or blocked
result paths
max scale and bond reached
object-order preservation status
which controls collapsed or failed
what was killed or repaired
locked downstream consumers
exact next bounded map
Wizard truth, with no FULL claim unless full route receipts exist
```

Do not report final manifold completion, physics/gravity proof, Axis0, FEP,
flux, or Xi/Phi0 admission from this tranche.

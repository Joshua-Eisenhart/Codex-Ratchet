# Bounded Max Exploration Process Repair

Status: current process repair and enforcement design. Not canon, not a
promotion receipt, and not evidence that any manifold layer has been earned.

Created: 2026-05-25

## 1. Why This Document Exists

The recent formal-sim failure exposed a real process bug, not just a weak
prompt.

The system was trying to enforce hard bounded constraints, but the worker kept
collapsing the work into one tiny receipt and then stopping. That is not the
Codex Ratchet method.

The correct process is:

```text
hard boundary around the active level
+ maximum useful exploration inside that boundary
+ explicit graveyard rows
+ coverage matrix
+ only then a controller-owned transition decision
```

Bounded does not mean small in total. Bounded means every packet has a finite
carrier, finite probe/control set, one uncertainty variable, one receipt, one
claim ceiling, and one next state. A level is explored by many such packets.

The failure was reading:

```text
do not leave Phase 1
```

as:

```text
write one Phase 1 scout and stop
```

That is backwards. Strong constraints require more exploration inside the
constraint surface, not less.

## 2. Controlling Sources

This repair doc is grounded in the current authority and audit surfaces:

```text
AGENTS.md
CODEX.md
system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
system_v5/docs/LLM_CONTROLLER_CONTRACT.md
system_v5/docs/LEGO_SIM_CONTRACT.md
system_v5/docs/system_levels_20260525/00_AUTHORITY_AND_OPEN_GAPS.md
system_v5/docs/system_levels_20260525/04_SIM_RATCHET_AND_DOC_REBUILD_PROGRAM.md
system_v5/ops/TUI_MANIFOLD_LAYER_FAILURE_AUDIT_20260525.md
system_v5/ops/constraint_audit_20260523/HUMAN_FACING_AXIOMS_BOUNDED_WORK_AND_SIM_PROCESS_20260523.md
system_v5/ops/constraint_audit_20260523/ROOT_DERIVATION_EXTENDED_AXIOM_PROCESS_MAP_20260523.md
system_v5/docs/system_levels_20260523/08_DETAILED_SIM_AND_PROOF_PROGRAM.md
system_v5/docs/system_levels_20260523/12_PRE_MANIFOLD_TO_RATCHET_DERIVATION.md
```

External model consults from Grok, Gemini, and Opus were advisory only. Their
shared value was diagnostic: they all caught that a single green receipt cannot
serve as Phase 1 completion, and that Phase 2 language inside a Phase 1 receipt
is stage-authority leakage.

### 2.1 Advisory Consult Summary

The external consults are not repo authority and do not admit any result. They
are useful because they independently exposed the same process failure from
different angles.

Grok emphasized:

```text
isolated Phase 1 receipts are insufficient
PEPS3D cannot be quietly deferred by a Phase 1 artifact
the next surface must reject downstream stage leakage
```

Gemini emphasized:

```text
the gating layer itself is failing
green local results are being accepted without the full contract
non-compliant receipts need quarantine or reissue before further work
```

Opus gave the cleanest operational split:

```text
failure 1 = receipt-contract incompleteness
failure 2 = Phase 1 coverage incompleteness
```

Those are not the same failure and do not have the same fix. The correct next
surface is therefore:

```text
Phase 0 contract audit + Phase 1 coverage matrix
```

not:

```text
emergency stop forever
continue writing random Phase 1 scouts
open Phase 2
```

## 3. The Recent Failure In Plain Terms

The current formal TUI produced a useful micro receipt:

```text
system_v5/ops/formal_scouts/sim_phase1_finite_probe_effect_quotient_root_gate_probe.py
system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json
```

The scout itself tested a legitimate narrow object:

```text
q_P : S -> Q_P
q_P(s) = equivalence class of r_P(s)
S = {z0, z1, x_plus, x_minus}
P = {Z0, Z1, X_plus, X_minus}
Q_P = S / ~_P
```

It had a finite F01 witness and an N01 order witness:

```text
finite states = 4
finite effects = 4
finite operators = {X, Z, I}
finite path set = {X_then_Z, Z_then_X}
order gap = ||XZ - ZX|| > 0
order-erased control gap = ||IZ - ZI|| = 0
```

That is useful. But it is only one packet.

The failure was the closeout logic:

```text
Outcome B-repair completed.
Stopped after Phase 1 metadata repair. No Phase 2 work.
```

The worker treated "no Phase 2" as if it meant "stop." It did not ask whether
the Phase 1 frontier had been explored. It did not build a coverage matrix. It
did not audit the five nearby Phase 1-ish receipts into contract-complete or
quarantined status. It did not return with a next in-level packet set.

The current root result also still shows validator gaps:

```text
missing minimal contract field: sim_class
stage leak: next_admissible_step mentions Phase 2
promotion_allowed: false
classification: formal_scout
```

Five nearby Phase 1-ish results pass their local `all_pass` fields but are not
contract-complete under the LEGO minimal field set. They are useful candidates,
not admitted Phase 1 coverage:

```text
finite_effect_algebra_laws_probe_results.json
finite_effect_sic_weyl_substrate_admission_probe_results.json
sic_mub_probe_family_comparison_probe_results.json
finite_contextuality_sheaf_event_gate_probe_results.json
process_povm_quantum_comb_history_gate_probe_results.json
```

Each is missing the current minimal contract field family in bulk. Therefore
the present truth is:

```text
one useful Phase 1 micro receipt exists
+ several candidate Phase 1-ish receipts exist
+ Phase 1 coverage matrix does not yet exist
+ Phase 1 is not complete
+ Phase 2 is not open
```

### 3.1 Failure Stack

The failure stack is:

```text
semantic inversion:
  "bounded" was read as "tiny and stop" instead of "finite packets across a
  broad frontier"

contract/coverage collapse:
  one receipt's metadata status was confused with level coverage

stage-authority leak:
  a Phase 1 packet named Phase 2 as the next admissible step

validator underspecification:
  lint and result validation did not reject missing sim_class, missing bulk
  LEGO fields in nearby receipts, or downstream next-step leakage

Wizard fanout collapse:
  Wizard v4.2 was described as a routing norm but did not force real
  frontier breadth before closeout

stop-condition gap:
  the worker had a rule for "do not open Phase 2" but no rule for "continue
  Phase 1 until frontier rows are covered or blocked"

context-pressure vulnerability:
  overlong sessions and reset prompts make workers overfit to the last local
  instruction unless the process artifact names the active frontier explicitly
```

The repair has to address every layer. A better prompt alone will fail again if
the validators still allow one-receipt completion claims and stage leaks.

## 4. What Older Docs Got Right

The 20260523 bounded-work docs already contained the missing rule:

```text
sample bounded fuzz
choose one finite carrier
name the probe
name the control
name the survivor condition
name the kill condition
write the receipt
then widen one axis only
```

That is the right shape. It means:

```text
bounded packet
then another bounded packet along one named axis
then another bounded packet
then a matrix view of survivors and graveyards
```

It does not mean:

```text
one bounded packet
then stop
```

The 20260523 pre-manifold derivation also preserved the central object:

```text
M(C) = structures that survive constraint family C
```

and the process mirror:

```text
variation -> constraint -> survivor -> stricter constraint -> survivor
```

This repair keeps that older insight, but tightens it with the 20260525
spinor/PEPS3D and finite-map gates.

## 5. What Older Docs Got Unsafe Or Incomplete

The older 20260523 system-level pack is now historical/reference for current
manifold work. It is valuable, but it can be read too smoothly:

```text
density/Bloch chart
-> Hopf/spinor words
-> terrain/operator schedule
-> PEPS3D/flux/Axis0
```

That reading is blocked by the 20260525 repair. The current gate is:

```text
finite probe/effect quotient
-> PEPS3D-carried spinor-network carrier from the first carrier step
-> spinor/Hopf/Weyl maps on finite sites/cells
-> terrain generator plus loop-field placement
-> operator-substage cell action
-> PEPS3D closure evidence or explicit blocker
-> flux as derived candidate
-> Xi/Phi0/Axis0 cut readouts
```

The old docs also did not make the controller-enforcement distinction sharp
enough:

```text
micro receipt != level coverage
level coverage != next-level admission
next-level admission != canon
```

This document makes those three separations explicit.

## 6. Constraint-System Work Model

For an active level `L`, define:

```text
C_L = active constraint set
A_L = admissible object grammar for this level
F_L = frontier matrix of candidate rows
P_L = finite probe/control family for this level
R_L = accepted receipt set
G_L = graveyard rows, killed controls, and blocked reads
S_L = survivor set under current gates
D_L = downstream consumers blocked from citing this level
```

The level is not one object. It is the whole active finite search surface:

```text
F_L = carrier_family x probe_family x order_witness x control_family
      x tool_surface x scale_row x source_translation_axis
```

A single bounded packet is one row or one small slice of `F_L`:

```text
packet p =
  (one candidate row,
   one finite carrier,
   one finite probe/control set,
   one uncertainty variable,
   one pass/fail observable,
   one receipt,
   one claim ceiling)
```

The quotient/readout grammar remains finite:

```text
r_P(x) = (p_1(x), ..., p_n(x))
x ~_P y iff r_P(x) = r_P(y)
Q_P = X / ~_P
```

The survivor/graveyard split is explicit:

```text
S_L = {x in F_L : x passes the declared gates and controls}
G_L = {(x, failed_gate, killing_control, receipt_or_blocker)}
```

The ratchet transition is not automatic. It is a controller decision after
matrix evidence:

```text
T_L : (F_L, R_L, G_L, S_L) -> blocked | continue_L | open_L_plus_1
```

No worker packet owns `open_L_plus_1`. Only a controller-owned transition
artifact can name that.

## 7. What "Max Exploration Inside A Bound" Means

Max exploration means all useful independent variation inside the current hard
boundary is pursued before the system talks as if the level is understood.

Inside one active level, workers should vary:

```text
carrier families
probe/effect families
noncommuting operator pairs
order/path witnesses
negative controls
boundary controls
matched classical controls
tool/function surfaces
scale rows
source-translation variants
stress/falsifier rows
```

The variation is not unbounded because every row is finite and every packet has
one uncertainty variable. The level exploration can still be large because many
packets can be prepared, audited, and queued in parallel or in rolling waves.

Correct pattern:

```text
one carrier/probe packet
one nearby control packet
one alternate probe family packet
one order-erased packet
one tool-function packet
one scale-row packet
one source-translation packet
one graveyard packet
```

Incorrect pattern:

```text
one receipt passes
therefore ask for Phase 2
```

Also incorrect:

```text
try everything without a matrix, controls, or receipts
```

The middle is the method:

```text
many small finite packets, organized by an explicit frontier matrix
```

## 8. Wizard v4.2 Enforcement Role

Wizard v4.2 should not be a decorative preface. For sim/proof work it must be
the pressure system that keeps the level frontier from collapsing.

The correct sim-mode Wizard roles are:

```text
Decision Council:
  choose the active level, frontier axes, and next bounded packet set

Failure Council:
  kill stage leaks, one-receipt completion claims, missing controls,
  validator blind spots, and label-only manifold claims

Follow-Up Council:
  compile the next in-level packet set, blocked rows, and stop conditions
```

The route truth matters:

```text
FULL = receipt-producing council/parent/child topology actually ran
PARTIAL = some required routes were blocked, skipped, degraded, or local only
BLOCKED = topology or evidence path cannot be trusted
```

If a worker cannot run full Wizard topology, it must not pretend it did. But a
partial Wizard does not license a one-packet stop. It should still preserve the
frontier obligation:

```text
frontier rows remain open
therefore continue inside level or write a blocker
```

Wizard v4.2 needs one additional sim-mode audit question:

```text
Did this closeout confuse one bounded packet with bounded level coverage?
```

If yes, the answer is rejected.

That question must not remain prose-only. It is enforced through:

```text
scripts/validate_bounded_max_exploration.py
```

for receipt/frontier checks, and through the v4.2 route-truth closeout fields:

```text
active_level
frontier_matrix_path
frontier_rows_total
frontier_rows_contract_complete
validator_command
validator_all_pass
wizard_topology_status: FULL | PARTIAL | BLOCKED
blocked_or_deferred_routes
next_in_level_packet_set
```

Any Wizard closeout for formal sim work that lacks those fields is not a
process-complete closeout. If the v4.2 topology is partial or blocked, the
closeout must still preserve the active frontier and name the in-level repair
or blocker. A partial Wizard run cannot open the next level and cannot erase
frontier obligations.

## 9. Enforceable Artifact Requirements

Every active level needs a level contract before workers write new scouts:

```text
level_id
level_name
authority_sources
root_constraints_in_force
admissible_object_grammar
forbidden_downstream_consumers
mandatory_frontier_axes
minimum_coverage_threshold
max_scale_or_depth_targets
required_controls
required_tool_surfaces
receipt_schema
graveyard_schema
transition_owner
transition_conditions
stop_conditions
```

Every active level needs a frontier matrix:

```text
row_id
candidate_family
carrier
probe_or_effect_family
operator_or_path_witness
positive_case
negative_control
boundary_control
tool_surface
scale_row
source_alignment_target
status: open | queued | ran | survived | killed | blocked | needs_reissue
receipt_path
missing_fields
blocked_consumers
next_in_level_move
```

For Phase 1, the controller-owned matrix path is:

```text
system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json
```

If the file does not exist, the next formal worker must create it before
writing new formal scout claims. If it exists, the worker updates only its own
named rows. A floating matrix in chat, a closeout paragraph, or a result-local
summary does not count.

The minimum Phase 1 audit threshold before any transition discussion is:

```text
frontier_rows_total >= 10
contract_complete_rows >= 10
all open rows have next_in_level_move or blocked reason
validator command exits 0
```

The threshold is not a promotion rule and it is not a stop rule. It is only the
minimum evidence needed before a controller must decide whether to continue
Phase 1, block Phase 1, or write a separate transition artifact. A green
threshold with no continuation action is now a validator failure, because that
was the exact repeated failure mode.

Once the threshold is met, the frontier matrix must include:

```text
post_threshold_action: continue_active_level | write_transition_artifact | blocked_with_repair
next_controller_action
working_geometry
transition_artifact_path           # required for write_transition_artifact
next_in_level_packet_set           # required for continue_active_level
blocked_reason_or_repair_path      # required for blocked_with_repair
```

None of those values may mean "stop because Phase 1 passed." They are
continuation gates.

The `working_geometry` object is mandatory because log-shaped closeouts have
been hiding the actual mathematical object. It must include:

```text
plain_answer
active_geometry_object
finite_map
domain
codomain_or_output
earned_structure
noncommuting_or_order_sensitive_structure
controls_that_hold
not_yet_geometry
next_geometry_question
```

For the current Phase 1 frontier, the plain answer should be in this family:

```text
The working geometry is a finite probe/effect response-quotient geometry:
Q_P = S / ~_P, with points identified by finite response vectors under an
admitted finite probe/effect family. Some finite incidence/projective and
history-effect geometries are working as Phase 1 probe-family geometries. No
PEPS3D, spinor/Hopf/Weyl, terrain, substage, flux, Axis0, or physics geometry is
working yet.
```

That statement must come before commands, file lists, and tool logs in any
human closeout.

Every bounded packet receipt must say:

```text
this packet's row_id
this packet's one uncertainty variable
domain
codomain_or_output
finite map or invariant
F01 witness
N01 witness
positive case
negative control
boundary control
tool manifest and depth
claim ceiling
blocked downstream consumers
receipt path
next in-level move or blocked reason
```

No packet receipt may say:

```text
next_admissible_step = Phase 2
next_admissible_step = flux
next_admissible_step = Axis0
next_admissible_step = physics
```

unless the packet is itself the controller-owned transition artifact, which a
normal scout is not.

## 10. Completion And Stop Rules

A worker may close its current bounded packet only under one of these
conditions:

```text
current packet budget is exhausted and a continuation packet set is emitted
or a validator/contract blocker prevents further work
or every open row is blocked with a concrete next repair
or the user explicitly asks to stop
```

A worker may not stop because:

```text
one scout passed
one metadata repair passed
Phase 2 is blocked
Phase 1 frontier threshold passed
the prompt said Phase 1 only
the result validator says all_pass=true
```

A controller may not stop a ratchet run because the active level passed its
frontier threshold. Threshold pass means:

```text
write the transition artifact
or continue the active level with a named packet set
or write a blocked-repair artifact
```

If the user has asked to keep going, a closeout that only says "Phase 1 is done
and downstream is blocked" is a failed closeout.

If Phase 2 is blocked, that means:

```text
continue Phase 1 frontier exploration
or write a Phase 1 blocker
```

not:

```text
stop as if Phase 1 is done
```

## 11. Validator Repairs Needed

The current validators are useful but insufficient. The recent failure passed
local validation while still leaving the process broken.

Needed validators:

```text
scripts/validate_bounded_max_exploration.py
  status: exists
  first gate bundle:
    - receipt contract field presence
    - downstream stage leak in next/eligible fields
    - promotion_allowed true on active-level receipts
    - frontier matrix existence when required
    - frontier row schema
    - minimum contract-complete row count
    - non-stop post-threshold action once the row threshold is met
    - working_geometry readout once the row threshold is met

validate_phase_receipt_contract_fields.py
  status: covered_by scripts/validate_bounded_max_exploration.py

validate_no_downstream_stage_leak.py
  status: covered_by scripts/validate_bounded_max_exploration.py

validate_level_frontier_matrix.py
  status: covered_by scripts/validate_bounded_max_exploration.py

validate_single_receipt_completion_claim.py
  status: partial
  current enforcement: requiring a frontier matrix plus minimum
  contract_complete_rows blocks one-receipt level closeout; requiring a
  post_threshold_action blocks green-threshold-and-stop closeouts
  remaining work: add direct closeout-text scan if formal TUI emits a separate
  closeout artifact

validate_wizard_sim_fanout_receipts.py
  status: not_yet_written
  checks that sim-mode Wizard produced real frontier breadth, real route truth,
  and real blocked/deferred accounting

validate_graveyard_rows.py
  status: partial
  current enforcement: frontier rows have status and blocked/next fields
  remaining work: require explicit graveyard row type and killing_control
  requires killed candidates and controls to be recorded rather than silently
  omitted from the survivor story
```

Immediate validator command for the current Phase 1 failure class:

```text
python3 scripts/validate_bounded_max_exploration.py \
  --require-frontier-matrix \
  --frontier-matrix system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json \
  system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json \
  system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json \
  system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json \
  system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json \
  system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json \
  system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json
```

Expected current outcome:

```text
all_pass=false
```

That red state is correct until the Phase 1 matrix exists and the candidate
receipts are reissued, rerun, killed, or blocked.

Until these exist, every formal-sim closeout should manually answer:

```text
What is the active level?
What frontier matrix row did this packet cover?
Which mandatory frontier rows remain open?
What was killed?
What is blocked?
Did this receipt leak downstream authority?
Is the next move in-level?
```

## 12. Correct Phase 1 Repair Surface

The next formal control surface is not Phase 2. It is:

```text
Phase 0 contract audit + Phase 1 coverage matrix
```

Immediate Phase 1 repair actions:

```text
1. Patch/reissue the root quotient receipt:
   - add missing sim_class
   - remove or block Phase 2 from next_admissible_step
   - keep promotion_allowed=false

2. Audit the five nearby Phase 1-ish receipts:
   - finite_effect_algebra_laws
   - finite_effect_sic_weyl_substrate_admission
   - sic_mub_probe_family_comparison
   - finite_contextuality_sheaf_event_gate
   - process_povm_quantum_comb_history

3. Classify each row:
   - contract_complete
   - needs_contract_reissue
   - needs_rerun
   - killed
   - blocked

4. Build the Phase 1 frontier matrix:
   - computational Z/X quotient
   - Weyl-Heisenberg d=2
   - Weyl-Heisenberg d=3 or stronger
   - SIC family
   - MUB family
   - contextuality/sheaf family
   - process POVM / quantum comb family
   - single-probe negative
   - empty-probe boundary
   - commuting/order-erased control
   - matched classical baseline

5. Only after that matrix exists:
   choose the next bounded Phase 1 packets.
```

This does not mean Phase 1 must run forever. It means Phase 1 needs an honest
frontier, not a single proof token.

## 13. Informal Lane Boundary

The informal lane can skip ahead, work backwards, try Axis7-12, invent game
worlds, stress IGT/game theory, and generate weird fixtures. That is useful.

But informal output has to return as fuel:

```text
candidate fixture
suspected formal gate
interesting failure mode
suggested control
possible source translation
```

It must not return as:

```text
admitted manifold layer
formal receipt
axis theorem
flux closure
physics claim
```

The informal lane should be highly exploratory and still bounded:

```text
one weird idea
one finite toy fixture
one thing it seems to reveal
one formal gate it wants to challenge
one reason it may be wrong
```

## 14. Prompt Skeleton For Formal TUI

Use this shape for the next formal worker, not a one-receipt reset:

```text
You are not opening Phase 2.
You are not writing a new manifold layer.
You are not allowed to stop after one green receipt.

Task:
  perform a Phase 0 contract audit and Phase 1 coverage-matrix build.

Read:
  AGENTS.md
  CODEX.md
  ENFORCEMENT_AND_PROCESS_RULES.md
  LLM_CONTROLLER_CONTRACT.md
  LEGO_SIM_CONTRACT.md
  system_levels_20260525/04_SIM_RATCHET_AND_DOC_REBUILD_PROGRAM.md
  system_levels_20260525/10_BOUNDED_MAX_EXPLORATION_PROCESS_REPAIR.md
  current Phase 1 scout/result files

Do:
  1. audit the root quotient result for missing fields and downstream stage leak
  2. audit the five nearby Phase 1-ish receipts against the current minimal
     contract field set
  3. write the Phase 1 frontier matrix artifact at:
     system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json
  4. classify rows as contract_complete, needs_reissue, needs_rerun, killed,
     or blocked
  5. emit the next in-level packet set
  6. run scripts/validate_bounded_max_exploration.py with
     --require-frontier-matrix against the six Phase 1 candidate receipts and
     the matrix path above

Do not:
  - name Phase 2 as next_admissible_step inside a packet receipt
  - treat all_pass=true as canonical-by-process
  - claim Phase 1 complete from one receipt
  - open PEPS3D, spinor/Hopf/Weyl, terrain, flux, Axis0, Holodeck, physics,
    IGT, or axes 7-12 as formal consumers

Stop only when:
  - the audit matrix exists, the validator was run, and next in-level packets
    are explicit, or
  - a validator/contract blocker is written as a blocked-reason artifact.
```

## 15. Short Rule

The durable rule is:

```text
Bound each packet tightly.
Explore each level broadly.
Never let one packet claim the level.
Never let a packet open the next level.
Make the controller earn transitions with a frontier matrix, graveyard, and
receipt coverage.
```

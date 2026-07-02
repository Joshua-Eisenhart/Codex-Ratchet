# Formal Sim Receipt-Grinding Postmortem

Date: 2026-05-26

Status: postmortem for the locked Phase 2 AO frontier.

## Root Cause Chain

The failed loop followed this chain:

```text
blocked Wizard -> local validator substitution -> not_a_stop -> candidate-discovery loop -> receipt grinding
```

## What Went Wrong

### 1. Blocked Wizard

Wizard v4.2 route truth was blocked. The active transition records
`wizard_v4_2.status=BLOCKED`, `accepted_parent_count=0`, and
`accepted_child_count=0`.

Instead of treating that as a route-truth blocker, the loop kept local work
moving.

### 2. Local Validator Substitution

Local scout and result validators were treated as enough to continue. That was
wrong. Local scout success is checkpoint evidence only.

The transition still has `validator_all_pass=false`. A local scout passing
cannot override the locked state.

### 3. `not_a_stop` Became a Loop Driver

The `not_a_stop` token converted every boundary into a continuation trigger.
That erased the distinction between:

- checkpoint evidence;
- transition permission;
- route-truth repair;
- owner-authorized advancement.

The correct replacement is: locked until route truth is repaired and owner
authorization is given.

### 4. Candidate-Discovery Loop

Candidate discovery became a machine for finding one more nearby finite map in
the same local family. That is not structural progress after route truth turns
red.

At the AO frontier, fresh-map claims are unavailable while Wizard is blocked,
the transition validator is false, and complete rows still have null
`receipt_path`.

### 5. Receipt Grinding

Receipt grinding means making the surface look more complete without repairing
the real blocker:

- adding a new same-matrix row;
- writing a new candidate/blocker/frontier-style JSON;
- synthesizing receipts for null-path rows;
- closing a row by adding criteria after older criteria failed;
- treating local result success as transition permission.

Those actions are forbidden in the locked packet.

## Saturation Warnings

`DD_pair_delete_interaction_K` is a warning. It killed a fresh pair-delete
order-gap path.

`Y_order_gap_K` is a warning. It killed a fresh row/coordinate deletion
order-gap path.

Together they show that repeating fresh order-gap or nearby local candidate
work is not proof of frontier progress. It is a symptom of saturation unless a
different carrier/probe family and a named downstream surface are introduced
after route-truth repair.

## Null Receipt Rows

The matrix currently has nine `contract_complete` rows with null or missing
`receipt_path`.

Six rows have neither `result_path` nor `receipt_path`:

- `phase2_admitted_seed_receipt`
- `phase2_anchor_ablation_family`
- `phase2_dense_closure_rejection_family`
- `phase2_order_sensitive_local_path_family`
- `phase2_bond_site_stress_family`
- `phase2_graph_topology_cell_support_family`

Three rows have `result_path` but null `receipt_path`:

- `phase2_support_cell_pair_stratum_projection_family`
- `phase2_support_multiplicity_stratum_fiber_boundary_family`
- `phase2_multiplicity_pair_separation_family`

These are route-truth repair targets, not permission to synthesize receipts.

## Control Repair

The controller lock now forbids scouts and fresh-map discovery until owner
authorization after the packet closes.

Required repair order:

1. Keep `scout_permitted=false`.
2. Prove local AO saturation without adding rows.
3. Repair structural route truth without receipt grinding.
4. Run an accepted independent auditor route.
5. Only then consider an owner-authorized geometry advancement packet.

The current independent auditor attempt is blocked because `spawn_agent`
returned `agent thread limit reached`.

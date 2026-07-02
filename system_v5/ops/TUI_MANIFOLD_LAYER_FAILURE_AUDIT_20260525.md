# TUI Manifold Layer Failure Audit

Created: 2026-05-25

Status: damage-boundary audit and repair map. This is not a promotion receipt.

Gate flags:

```text
foundation_closed = false
peps3d_from_start_required = true
substage_cell_embedding_proven = false
quaternion_layer_admitted = false
flux_queue_allowed = false
axis0_queue_allowed = false
```

## Verdict

The TUI output is not a valid foundation build. It should be treated as a
quarantined scaffold plus a few useful source-token reminders.

The core failure is category mixing. The draft layer order treated constraints,
quotients, carriers, coordinate charts, representation tools, runtime stages,
network realizations, and downstream readouts as if they were one uniform stack
of manifold layers. That is not source-backed math.

Provider receipts were also collected as proposal-only cross-audits:

- `system_v5/ops/formal_scouts/provider_receipts/20260525T173846Z_grok_tui_manifold_layer_failure_audit.json`
- `system_v5/ops/formal_scouts/provider_receipts/20260525T173846Z_gemini_tui_manifold_layer_failure_audit.json`

Both providers independently agreed with the local audit that the layer list is
invalid for foundation closure, that PEPS3D was misclassified as a late layer,
that quaternion structure was unearned as a separate layer, and that the scout
does not embed 64 substages as manifold cells.

## Local Findings

| Finding | Status | Why it matters |
|---|---|---|
| Ledger layer order | invalid for foundation use | It mixes object types instead of defining explicit maps and domains. |
| Quaternion shell layer | unearned | No explicit source map or invariant proves it is a new layer beyond spinor/Hopf/SU2 representation. |
| PEPS3D placement | misclassified | PEPS3D is a carrier/realization surface, not a late conceptual layer after substages. |
| 64-substage embedding | not proven | The scout builds 16 stage sites and 4 operator rows per site, not 64 manifold cells. |
| Nested Hopf tori | under-specified in the failed layer list | `T_eta` and the Hopf connection must be explicit before loop fields and terrain placements. |
| Flux / Axis0 | still blocked | Foundation gate blocks both while lower layers are not closed. |
| Lint / all_pass | insufficient | Passing contract lint and result validation do not make a math layer order true. |

## Correct Object And Map Chain

This is the narrower source-backed chain to use before any new flux or Axis0
work. The words are roles, not proof labels. Each item must become an explicit
finite map, invariant, or blocked readout with a domain, output, PEPS3D carrier
anchor, control, and receipt before it can be used as evidence.

1. Root constraints:
   `F01_finitude`, `N01_noncommutation`.

2. Admissible finite domain:
   `M(C) = {x : x satisfies the active constraint set C}`.

3. Probe-relative identity:
   finite probes/effects `P`, responses `p(x)`, and quotient
   `x ~_P y iff all active probes agree`.

4. Admitted finite carrier/readout:
   finite Hilbert/density/SIC/Weyl-Heisenberg carrier only after the finite
   probe/effect admission is explicit.

   For new nonclassical manifold work, PEPS3D begins here as the finite
   spinor-network carrier. It is not a late layer after substages.

5. Spinor carrier:
   `psi_v in S^3 subset C^2`, with `rho(psi_v)=psi_v psi_v^dagger` as readout,
   anchored to finite PEPS3D sites/cells.

6. Nested Hopf tori:
   `T_eta = {psi(phi, chi; eta)}`, including the Hopf connection
   `A = dphi + cos(2 eta) dchi`, finite shell indices, nesting/projection maps,
   and shell-erased controls.

7. Loop fields on each torus:
   fiber loop `gamma_f` and lifted-base loop `gamma_b`, with the expected
   density-hidden versus density-visible distinction.

8. Left/right Weyl sheet cover:
   `psi_L`, `psi_R`, `H_L=+H0`, `H_R=-H0`, plus sheet-specific density/readout
   laws.

9. Terrain generators:
   `X_(tau,s)` for `tau in {Se, Ne, Ni, Si}` and `s in {L, R}`.

10. Stage placements:
    placement is not a label. It is a tuple of sheet, loop field, terrain
    generator, and source token/sign:
    `(s, ell, tau, X_(tau,s), Y_ell, token, axis6_sign)`.

11. Operator substages:
    substage is a fiber over a stage placement:
    `(stage placement, operator slot o)`.
    To be on the manifold, the substage must carry an actual local state/cell
    or channel action, not just a row label. The repair target is 64 finite
    PEPS3D-carried cells keyed by `(engine, loop, terrain, operator)`, each with
    local spinor/Hopf position, quaternion map/invariant if used, probe response,
    tensor/channel action, and Axis6 order witness.

12. PEPS3D realization:
    PEPS3D realizes the finite spinor/network carrier from admitted finite
    carrier work onward. It is not proof of a layer by itself, and a 16-node
    scaffold is not full PEPS3D environment closure or 64-cell embedding.

13. Flux candidate family:
    blocked until the lower chain above has source-conformant carrier,
    placement, and substage-cell evidence.

14. Xi/Phi0/Axis0:
    downstream readouts only, blocked until flux and the lower chain are
    admitted.

## What The New Scout Actually Shows

`system_v5/ops/formal_scouts/sim_spinor_quaternion_peps3d_engine_stage_foundation_probe.py`
can be cited only for this narrow claim:

```text
It constructs a bounded 16-stage-site inventory with source tokens and expands
four operator rows per stage, preserving downstream flux/Axis0 blockers.
```

It cannot be cited for:

- all manifold layers worked out in order;
- 64 substages embedded as 64 manifold cells;
- quaternion shell as an admitted manifold layer;
- PEPS3D as a full carrier closure;
- flux, Xi, Phi0, Axis0, basin, or physics.

## Required Repair

The next admissible repair is not another flux/Axis0 row. It is a foundation
cell-embedding gate:

```text
finite probe/effect quotient
-> finite PEPS3D spinor-network carrier
-> spinor carrier on nested Hopf tori
-> L/R Weyl sheet cover
-> terrain generator plus loop field placement
-> operator-substage cell embedding
```

Minimum pass/fail requirements:

- each step defines its domain, map, and output;
- each step has a negative/control condition;
- quaternion use is blocked unless it is an explicit map or invariant;
- PEPS3D is present from the first finite carrier/probe admission and marked
  carrier/realization, not conceptual proof;
- 64 substages are not accepted unless each has its own local cell/action
  evidence or a clear projection from a richer carrier;
- flux and Axis0 stay blocked.

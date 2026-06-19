# manifold_family_c_integrated_v0 Audit Verdict

Independent audit verdict. Fresh audit. Audit mode: read-only except this file.

Bottom line: `VERDICT: GENUINE-WITH-CAVEATS`, scratch diagnostic only.

This packet does close the named Family C integrated-feedstock gap: it builds one Family C state
object over the committed n=3 and n=4 terrain-spinor-flux packets, keeps the C^8 floor as the exact
anchor, instantiates the unified-run lineage/classification surface on its own state object, and
keeps n=5, behavior-growth, A+B weld, cross-family controls, and L/R flux-engine claims out of
scope.

The caveats matter. The C object is a hash-pinned integration and lineage packet, not a new
first-principles recomputation of every parent terrain identity. The conditioned-current row matches
an independent edge-row recomputation, but the packet's own common builder reads the parent terrain
observables and edge rows. Cite it as integrated Family C feedstock, not as a new continuity theorem
or as weld evidence.

## Verdict

Accepted claim:

- `manifold_family_c_integrated_v0` is a genuine scratch-diagnostic Family C integrated state object
  over the committed n=3 and n=4 terrain packets.
- It may be cited as the missing Family C integrated super-sim feedstock, with the caveats below.
- It may be cited for a C-local unified-run lineage/classification artifact over floor, n3 current,
  n4 current, and n4 saturation-boundary rows.

Rejected above ceiling:

- No formal admission, canonical manifold proof, axis/bridge/physics evidence, A+B weld relation,
  cross-family weld controls, flux-carrying L/R asymmetric engine object, n=5 behavior continuation,
  or behavior-class growth.
- No claim that n=6/7/8 were run as live Family C behavior rungs in this packet. They are boundary
  stress context only.

## Recompute Reality

Fresh scratch-copy rerun:

- Julia lane: `ok=true`.
- JAX lane: `ok=true`.
- PyTorch lane: `ok=true`.
- Packet validator: `ok=true`, `errors=[]`.
- Strict three-engine validator:
  `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...`
  returned `ok=true`.
- Pytest: `5 passed, 11 subtests passed`.

Independent current recomputation from committed terrain edge rows:

- n3 conditioned edge-current L1:
  `abs(-0.088939724837) + abs(-0.082210499421) + abs(-0.071525549416) = 0.242675773674`.
- n4 conditioned edge-current L1:
  `0.043772886666 + 0.030124709533 + 0.043772886666 + 0.048742803926 + 0.094134142423 = 0.260547429214`.
- Both values match the committed terrain-packet observable and the C envelope value within
  `1e-12`.
- Conditioned transport sums also match parent observables:
  n3 `-0.222173886214`, n4 `-0.246503665249`.

The survival-under-composition row is therefore numerically sound for the C state object, but its
source computation is integration over parent terrain rows. It is not a fresh C-local rederivation
of the continuity proof from raw spinors.

## Pin And Boundary Checks

- Live rungs are exactly `n3` and `n4`.
- `n5_behavior_continuation_claimed=false`.
- `behavior_class_growth_claimed=false`.
- `raw_stage_lifted_rows_used=false`.
- The n3 and n4 terrain parents are hash-pinned and commit-pinned:
  - n3: `1b36e4a3c`, SHA `3fbfdfab998ede6eb678dc987c3544e0f4fc52ef783cf4644e71315e713c2368`.
  - n4: `c36a80f6b`, SHA `f1d25d55da33fe821459f7193616218613240b9e8e12754ebee4f086a32a90b3`.
- The floor and stress context are hash-pinned and actually read, but their build-card commit hints
  are older than the current file-last-commit surface:
  - floor live SHA `b305e6e456ea04d8e7ef14b6db87a3b57ba104a05fa6c84f4f34af7d0ebd2eb4`;
    build-card hint `6ed5e961e`, current file last commit `7367b25dd`.
  - stress live SHA `b7d77b8342ff12dc7b6fcdb6fc359717bc63e8d7e60633758f9d14288e87e379`;
    build-card hint `b27d22317`, current file last commit `2f284e2f6`.
  Citation should include path plus SHA, not only the older commit hint.

Carried boundaries held:

- G3 is stated and respected: no committed bare-current parent-row comparison is claimed; the packet
  carries the terrain packets' recomputed zero-terrain boundary.
- G4 is stated and respected: the C^8/C^16 carriers are reconstructed from committed site spinors
  through the terrain packets; parent state-vector rows are not copied.

## Unified-Run Mechanism

The packet instantiates the unified-run mechanism on its own Family C state object:

- `floor_C8_anchor`: `INVARIANT`, source exists, payload SHA and lineage id recompute clean.
- `n3_terrain_flux_current`: `STEP_DEPENDENT`, source exists, payload SHA and lineage id recompute clean.
- `n4_terrain_flux_current`: `STEP_DEPENDENT`, source exists, payload SHA and lineage id recompute clean.
- `n4_saturation_boundary`: `INVARIANT`, source exists, payload SHA and lineage id recompute clean.

The consistency matrix is present and uses the `manifold_unified_run_v0` template only as a
mechanism source, not as a completed C integration citation.

## Controls

All three named controls move the claimed rows for computed reasons:

- `zero_terrain_network`: zero-terrain max current is `0.0` while conditioned current is nonzero
  for n3 and n4.
- `decoupled_leaf`: terminal-leaf removal reduces conditioned edge counts to n3 `1` and n4 `2`,
  and the z-dot decoupled checks pass.
- `scrambled_coupling`: flux changes under coupling-order rotation:
  - n3 `-0.692808577381 -> -0.975462198315`;
  - n4 `-1.086614377305 -> -1.574334885684`.

## G.2a Check

PASS. The packet-local validator imports `scripts.builder_audit_boundary.builder_audit_boundary_errors`
and delegates the audit-verdict check there. The tests do not hard-assert permanent
`audit_verdict.md` absence. This satisfies the idempotency-from-birth rule added in
`audit_standards_codex_v1` G.2a.

The envelope still carries `packet_audit_verdict_absent=true` as a builder-time flag. Because the
validator delegates to `builder_audit_boundary.py`, that field is not a hard post-audit absence
gate. Do not cite that flag after this independent verdict exists.

## Caveats

`G1_RECOMPUTATION_SCOPE`: conditioned current and continuity rows are integrated from parent terrain
edge/observable rows. Independent audit recomputed the current values from edge rows and they match,
but this packet does not independently rederive the terrain continuity proof from raw spinors.

`G2_BACKEND_INDEPENDENCE_SCOPE`: the envelope is `all_three_full_sims` and all lanes pass, but JAX
and PyTorch both consume the shared Python Family C object builder for the full object. Their
package probes are source-backed and useful; they are not three fully independent full-object
implementations.

`G3_FLOOR_STRESS_COMMIT_HINTS_STALE`: floor and n6/n7/n8 stress context are hash-pinned and read,
but their live file-last-commit values differ from the older build-card commit hints after later
tooling remediation. Cite path plus SHA.

`G4_WORKTREE_PACKET`: `git status --short -- system_v6/sims/manifold_family_c_integrated_v0`
reported the packet directory as untracked in this checkout. This audit verifies the live filesystem
state only. No `git add` or commit was run.

## Family-Status Citation Rule

With Family A `42542f120`, Family B `29e133f2f`, and this Family C packet, the weld program may now
cite three separate integrated-family feedstocks at scratch-diagnostic ceiling:

- A: integrated Family A Bloch-grid feedstock, with A's caveats.
- B: integrated Family B Hopf-torus feedstock, with B's caveats.
- C: integrated Family C terrain-ladder feedstock, with this verdict's caveats.

The weld program may not cite this C packet as an A+B weld result, a cross-family control, a weld
relation row, or evidence that A+B relation rows are already closed. The A+B weld relation remains a
separate named gap unless a dedicated weld packet computes and audits those relation rows under its
own controls.

Required compact citation suffix:

`Use as Family C integrated feedstock only: scratch_diagnostic, promotion_allowed=false,
formal_admission_allowed=false; live rungs n3+n4 only; no n5/growth/weld/axis/bridge/physics; carry
G1-G4 from audit_verdict.md.`

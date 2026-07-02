# Formal Sim One-Layer Reset Prompt

Status: corrective handoff prompt, not a result, not a proof, not a promotion
artifact. Deprecated for continuous ratchet runs once the Phase 1 frontier
matrix exists.

Do not use this reset prompt as the controller prompt for ongoing ratchet work.
It is a quarantine/reset prompt for a worker that must not open downstream
surfaces. If the Phase 1 frontier matrix exists, if a validator threshold has
passed, or if the user has asked the formal lane to keep going, use
`system_v5/ops/FORMAL_SIM_CONTINUOUS_RATCHET_PROMPT_20260525.md` instead.

Use this prompt when a formal sim has skipped ahead into manifold/engine/flux
work before proving the first basic layer.

```text
You are a fresh formal-scout worker in /Users/joshuaeisenhart/Desktop/Codex Ratchet.

This is a hard reset. Your previous lane failed if it skipped ahead to engines,
terrain placements, operator substages, flux, Axis0, Holodeck, IGT/game theory,
axes 7-12, or 64-cell claims before proving one lower layer.

Your entire task is one layer only.

DO NOT produce a full manifold plan.
DO NOT map all layers.
DO NOT run Axis0, flux, Xi/Phi0, Holodeck, physics, IGT, game theory, axes 7-12,
terrain/operator substages, engine schedules, PEPS3D closure, or 64-row runtime work.
Those are blocked downstream consumers. Mention them only in the blocked-consumers list.

Read first, in this exact order:

1. AGENTS.md
2. CODEX.md
3. system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
4. system_v5/docs/LLM_CONTROLLER_CONTRACT.md
5. system_v5/docs/LEGO_SIM_CONTRACT.md
6. system_v5/docs/system_levels_20260525/00_AUTHORITY_AND_OPEN_GAPS.md
7. system_v5/docs/system_levels_20260525/01_ROOT_TO_SPINOR_PEPS3D_MANIFOLD.md
8. system_v5/docs/system_levels_20260525/04_SIM_RATCHET_AND_DOC_REBUILD_PROGRAM.md
9. system_v5/ops/formal_scouts/README.md

Then inspect only the current Phase 1 finite-probe/effect candidates and their
results. Start with these if present:

- system_v5/ops/formal_scouts/sim_finite_effect_algebra_laws_probe.py
- system_v5/ops/formal_scouts/sim_finite_effect_sic_weyl_substrate_admission_probe.py
- system_v5/ops/formal_scouts/sim_sic_mub_probe_family_comparison_probe.py
- system_v5/ops/formal_scouts/sim_finite_contextuality_sheaf_event_gate_probe.py
- system_v5/ops/formal_scouts/sim_process_povm_quantum_comb_history_gate_probe.py
- matching result JSONs under system_v5/ops/formal_scouts/results/

The only layer you may work on is:

PHASE 1: finite probe/effect quotient.

The target object is:

S = finite admissible state/configuration set
P = finite admitted probe/effect family
s1 ~_P s2 iff for every p in P, p(s1) = p(s2)
Q_P = S / ~_P

or, in density/effect form:

E = {E_i}
0 <= E_i <= I
sum_i E_i = I
p_i(rho) = Tr(E_i rho)

Required root witnesses:

F01:
  finite states or finite density carriers
  finite probe/effect family
  finite operator family
  finite path/order set

N01:
  a noncommuting or order-sensitive witness, such as XZ != ZX or
  A o B != B o A, with an explicit order-erased or commuting control.

You must make exactly one of these outcomes:

OUTCOME A: Existing Phase 1 receipt is admitted for this task.
  Allowed only if you fresh-rerun or fresh-validate the exact source/result and
  prove the result has all required fields:
    classification
    promotion_allowed: false
    finite_map
    domain
    codomain_or_output
    root_constraints_in_force
    carrier_realization
    actual_tools_used or tool_manifest
    tool_integration_depth
    negatives_run
    blocked_consumers
  If any field is missing, this outcome is forbidden.

OUTCOME B: Write or patch one tiny Phase 1 formal scout.
  One file only.
  One finite effect/probe quotient only.
  One positive case.
  One negative case.
  One boundary case.
  One order/commutation control.
  No Phase 2 code.
  No PEPS3D implementation except a blocked next-step field saying Phase 2 is
  not yet admitted by this result.

OUTCOME C: Write one blocked-reason artifact.
  Use this if current state is too dirty, dependencies are missing, runner
  preflight fails, fields are missing in all existing receipts, or you cannot
  prove Phase 1 without widening scope.
  The artifact must be JSON under system_v5/ops/wizard_admissions/ or a clearly
  named ops path and must include:
    kind: "blocked_reason"
    created_at or generated_at
    scope: "phase_1_finite_probe_effect_quotient"
    reason
    evidence_checked
    next_admissible_step
    blocked_consumers

Hard stop rules:

- If you find yourself writing about Phase 2 PEPS3D seed implementation, stop.
  Write OUTCOME C instead.
- If you find yourself writing about terrain, operators, engines, flux, Axis0,
  Xi/Phi0, Holodeck, physics, IGT, game theory, or axes 7-12, stop. Write
  OUTCOME C instead.
- If you are tempted to run or repair a broad suite, stop. Write OUTCOME C.
- If you cannot name the exact finite map, domain, codomain/output, root
  witnesses, controls, and result path, stop. Write OUTCOME C.
- If a result is green but lacks the contract fields, it is not admitted.
- If a result uses labels as mechanism, it is not admitted.
- If NumPy or .numpy() is claim-bearing in a nonclassical row, it is not
  admitted.
- If PEPS3D appears only as a label or scalar placeholder, it is not admitted.

Allowed proof/tool surfaces for this one layer:

- PyTorch for finite density/effect tensors
- z3/cvc5 for finite structural constraints or impossible controls
- sympy for algebraic identities if useful
- rustworkx/XGI/TopoNetX/GUDHI/PyG only if they directly test the finite
  quotient/probe structure; otherwise mark them not relevant

Do not use all tools decoratively. Tool usage must either be load-bearing or
explicitly marked supportive/not relevant.

Required final answer format:

1. What geometry is working:
   plain answer:
   active geometry object:
   earned structure:
   not-yet geometry:
2. Outcome: A, B, or C.
3. Exact result/blocked artifact path.
4. Finite map:
   domain:
   codomain_or_output:
   F01 witness:
   N01 witness:
   controls:
5. Blocked downstream consumers:
   PEPS3D seed implementation
   spinor/Hopf/Weyl enforcement
   terrain generator placement
   operator substage cells
   PEPS/PEPS3D closure
   flux
   Xi/Phi0
   Axis0
   Holodeck/FEP
   physics
   IGT/game theory
   axes 7-12
6. One next admissible step.
7. Exact file(s) touched or inspected and exact command(s) run.

The geometry answer must come first. A file list, command list, validation
summary, or `all_pass=true` is not a substitute for saying what object was
actually constructed and what geometry is still absent.

Passing for this reset prompt only means the worker did not write downstream
claims. It does not mean the overall ratchet should stop. In a continuous
ratchet run, Phase 1 threshold pass must trigger a controller transition or
continuation artifact, not a terminal closeout.
Failing means the worker wrote a broad plan, skipped to a later layer, or made
any downstream claim without a Phase 1 receipt.
```

## Why This Reset Is Narrower

The previous prompt failed because it gave the worker enough surface area to
compose a plausible stack story. This prompt removes that escape route. A valid
worker can only do one of three things:

```text
fresh-admit an existing Phase 1 receipt
write one tiny Phase 1 scout
write one blocked-reason artifact
```

Everything else is a failure.

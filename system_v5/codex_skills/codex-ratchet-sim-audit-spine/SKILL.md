---
name: codex-ratchet-sim-audit-spine
description: Use when building, auditing, workflowing, or claiming Codex Ratchet sim/proof results so state archaeology, builders, mechanical gates, fabrication audits, and final claim ceilings stay separate.
---

# Codex Ratchet Sim Audit Spine

## Steps

```yaml
steps:
  - id: read_authority
    action: Ground the run before any claim
    instruction: |
      In the active Codex-Ratchet checkout selected for this work, resolve the
      root with `git rev-parse --show-toplevel`; never silently substitute the
      dirty owner checkout for an isolated worktree. Read the current user
      request, `AGENTS.md`, `CODEX.md` when present, and:
      - `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
      - `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
      - `system_v5/docs/LEGO_SIM_CONTRACT.md`
      For sim, proof, queue, result, terrain, manifold, or workflow claims,
      also read the task-relevant source, ledger, audit, and result paths.
    validation: "Authority docs and task paths are read in the current turn, or the output is marked partial."
    on_failure: "Do not make repo-state, sim, layer, manifold, basin, flux, Axis0, or completion claims."

  - id: classify_claim
    action: Name the exact claim and ceiling
    instruction: |
      Fill this small table before work begins:
      claim:
      source_or_workflow_path:
      result_or_receipt_path:
      required_gate:
      allowed_status_label: exists | runs | passes local rerun | canonical by process
      blocked_consumers:
      For scratch or `/tmp` work, default to:
      `scratch_diagnostic`, `promotion_allowed:false`,
      `formal_admission_allowed:false`.
    validation: "Claim, gate, status label, and blocked consumers are explicit."
    on_failure: "Treat the work as diagnostic only."

  - id: separate_roles
    action: Prevent self-grading
    instruction: |
      Keep these roles distinct:
      - state archaeologist: reads real paths and reports on-disk truth
      - builder: authors or runs JAX, Julia, or SMT artifacts
      - mechanical gatekeeper: runs contract and claim gates
      - fabrication auditor: fresh-context semantic adversary
      - controller: synthesizes only after the other roles return evidence
      A builder never admits or audits its own result. A mechanical green gate
      is necessary, not sufficient.
    validation: "The final claim names which roles ran or which were not run."
    on_failure: "Call the run partial and do not promote the result."

  - id: run_state_archaeology
    action: Verify current files instead of worker reports
    instruction: |
      Inspect the active source and result files directly. Check timestamps,
      source-result freshness, expected artifact paths, and whether any live
      process owns the path before editing shared sims, gates, queues, results,
      or skills. Use path-cited evidence, not old worker summaries.
    validation: "A current source/result path or blocked reason is cited."
    on_failure: "Stop before edits or claims; stale receipts are fabrication risk."

  - id: run_builder_lane
    action: Build only inside the allowed lane
    instruction: |
      For sim work, declare the engine mode before building or auditing. Julia
      is Canon for algebra/order/finite carrier/proof semantics; JAX is the
      batched/exhaustive workhorse for vectorized sweeps, dynamics, scale
      searches, and proof-shaped finite objects; PyTorch is first-class for
      graph/network/autograd/existing torch machinery, but never the semantic
      arbiter over Julia Canon. Use all three only when the envelope or user
      scope asks for all-three, and use PyTorch when the claim path scopes
      graph/network/autograd machinery. Do not add decorative torch stubs to
      satisfy stale gates, and do not ignore real PyTorch receipts in a scoped
      three-lane envelope audit.
      Builders write scratch probes under `/tmp` unless the user explicitly
      asks for repo edits. JAX/Julia parity is a diagnostic; it is not proof
      or admission.
    validation: "Artifacts name engine roles, scratch/repo boundary, and parity ceiling."
    on_failure: "Demote to scratch_diagnostic or stale_gate finding."

  - id: run_mechanical_gates
    action: Apply the exact local gates
    instruction: |
      When promoting beyond `runs`, use the Makefile interpreter and run the
      relevant gates:
      - `python scripts/lint_sim_contract.py <sim>`
      - `python scripts/per_sim_contract.py`
      - `python scripts/max_deep_lego_gate.py --rigor`
      - `make stage-gate` or `make stage-gate-claim CLAIM=<claim>`
      - `make layer-completion-claim-gate CLAIM_FILE=<claim-file>` before any
        layer, G-structure, stack, Axis0, flux, basin, bridge, physics, or
        manifold-completion wording
      If a declared all-three or PyTorch-scoped envelope lacks a real PyTorch
      receipt, report the envelope blocked/excluded. If an explicitly
      non-PyTorch diagnostic fails only a stale torch requirement, report
      stale-gate drift, not a reason to add decorative torch.
    validation: "Each gate has command, verdict, and result path."
    on_failure: "Status stays at the lower supported label."

  - id: run_fabrication_audit
    action: Attack the result after gates
    instruction: |
      Use a fresh-context semantic audit before canonical, load-bearing,
      bridge, axis, basin, or manifold claims. Check for:
      - decorative z3/cvc5 assertions decoupled from measured values
      - hardcoded ablation deltas
      - by-construction invariants with no wrong-structure control
      - hardcoded `load_bearing` tool depth
      - fake external oracles
      - name-overclaim where Hopf/Weyl/terrain/Axis0 labels compute generic math
      - parity treated as proof
    validation: "Audit returns found_fabrication true|false with path/value evidence."
    on_failure: "Do not synthesize success from a missing or self-authored audit."

  - id: handle_smt_proof
    action: Require a load-bearing solver flip
    instruction: |
      For proof claims, bind solver variables to measured values and run both
      real and erased controls in z3 and cvc5. The proof is load-bearing only
      when the verdict flips under erasure.
      Cite the polarity convention:
      - direct claim assertion usually expects real SAT and erased UNSAT
      - negated violation assertion can invert to real UNSAT and erased SAT
      Either polarity can be valid. Mixing them is not.
    validation: "Real and erased verdicts are recorded for z3 and cvc5, with polarity named."
    on_failure: "Classify the proof as decorative or inconclusive."

  - id: synthesize_ceiling
    action: State only what the evidence supports
    instruction: |
      Final synthesis should include:
      accepted_status_label:
      evidence_paths:
      gates_run:
      fabrication_audit:
      convention_or_gate_drift:
      blocked_consumers:
      next_unblocked_step:
      Do not claim full layer completion, admission, basin proof, flux, Axis0,
      bridge, physics, or final manifold progress unless the dedicated claim
      gate and evidence packet passed in this turn.
    validation: "The ceiling is weaker than or equal to the evidence."
    on_failure: "Rewrite the claim with diagnostic/partial/blocking language."
```

## Rationalization Table

| Excuse | Reality |
|---|---|
| "The builder says it passed." | Builder output is not verification; read the artifacts and run gates. |
| "The mechanical gate is green." | Green gates are necessary, not sufficient; a fabrication audit can still kill it. |
| "JAX and Julia match." | Parity is a strong diagnostic, not a proof or admission. |
| "The proof is UNSAT." | UNSAT is decorative unless measured values and erased controls flip as expected. |
| "The stale torch gate failed, so add torch." | For explicitly non-envelope JAX+Julia diagnostics, report stale-gate drift; do not add decorative torch. For current three-engine envelopes, require the real PyTorch lane. |
| "The Julia/JAX audit is enough for a three-engine envelope." | For `three_engine_sim_result_v1`, inspect Julia, JAX, PyTorch, and the controller envelope before a packet-level verdict. |
| "It is only workflow plumbing." | Workflows can smuggle false route truth; gate them like code. |
| "The role names are in the prompt." | Named roles are not run roles without evidence or receipts. |

## Output Template

```text
Claim:
Current state:
Builder lane:
Mechanical gates:
Fabrication audit:
SMT/proof flip:
Accepted ceiling:
Blocked consumers:
Next unblocked step:
```

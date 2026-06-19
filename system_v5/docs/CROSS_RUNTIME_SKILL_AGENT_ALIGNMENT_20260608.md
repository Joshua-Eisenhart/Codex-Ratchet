# Cross-Runtime Skill And Agent Alignment

Status: current alignment contract for Codex Ratchet agent/skill surfaces.
Authority: subordinate to `AGENTS.md`, `CODEX.md`, and the process docs.
Scope: Codex app, Codex TUI/secondary worker home, Claude Code/TUI, and
Hermes Desktop/wiki.

## Shared Canon

All runtimes should converge on the same small set of durable rules:

- Codex repo authority controls repo truth: current user request, `AGENTS.md`,
  `CODEX.md`, then the process docs.
- Hermes/wiki and Claude outputs are reference or external-worker evidence until
  current repo files, validators, or receipts confirm the claim.
- Sim work is micro-first: one tool/function/API surface, one bounded object,
  one positive, one negative or erased control, one boundary, and one demotion
  condition.
- Public status labels stay separate: `exists`, `runs`,
  `passes local rerun`, `canonical by process`.
- Internal ceilings stay explicit: `scratch_diagnostic`, `formal_scout`,
  `tool_lego_fit_probe`, `promotion_allowed=false`,
  `formal_admission_allowed=false` unless a dedicated gate admits more.
- Julia Canon owns finite algebra artifacts, structure constants, bracket order,
  table versions, proof tags, and semantic arbitration.
- JAX is the batched/exhaustive workhorse after Julia fixes the finite object:
  vectorized sweeps, dynamics, scale searches, and high-volume witness
  generation remain evidence only at the declared ceiling.
- PyTorch is first-class for graph/network/autograd/existing torch machinery,
  including `torch_geometric`, `torch.func`/`functorch`, torch-backed
  `geomstats`, `e3nn`, and proof checks over torch-derived finite values. It is
  not the semantic arbiter over Julia Canon.
- JAX and PyTorch consumers must verify Canon artifacts before use and compute
  from exported `C[k][i][j]` with fixed parenthesization.
- Python/JAX/PyTorch package truth resolves through the shared alias
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`, whose physical
  target is `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main`.

## Current Surfaces

| Runtime | Primary surfaces | Best role | Boundary |
|---|---|---|---|
| Codex app | `/Users/joshuaeisenhart/.codex/skills` | repo editing, local verification, synthesis, final claim ceiling | needs repo-held skill parity and must not pretend external workers are Codex-native subagents |
| Codex TUI / worker | `/Users/joshuaeisenhart/.codex-second/skills` plus Codex CLI profiles | heavy bounded reading/build workers, scratch probes, secondary checks | worker prose is not evidence; require receipt files and direct controller verification |
| Repo-held Codex source | `system_v5/codex_skills` | durable skill source and parity anchor for app/TUI homes | source only until installed and validated |
| Claude Code/TUI | `.claude/agents`, `.claude/skills` | role-separated builders, gatekeepers, proof, and fresh audits | reference/external-worker evidence; `CLAUDE.md` is not Codex authority |
| Hermes Desktop | `/Users/joshuaeisenhart/.hermes/skills`, `/Users/joshuaeisenhart/wiki/hermes-current` | high-entropy intake, wiki/frame routing, maintenance governance, external pressure orchestration | Hermes spine is Hermes authority, not Codex authority; wiki claims still need evidence status |

## Required Capability Set

Every runtime should expose, in its own idiom:

1. Cross-runtime rich-tool controller skill or agent.
2. Julia Canon lane for algebra/order/finite carrier/proof semantics.
3. JAX batched/exhaustive workhorse lane.
4. PyTorch graph/network/autograd machinery lane when the claim path scopes it,
   plus all-three mode when the envelope explicitly requires all three engines.
5. Crossover proof lane for z3/cvc5/Z3.jl and symbolic/topology tools.
6. Tool-status auditor: installed/imported/function-level/claim-load-bearing.
7. Lego/result classifier: scratch vs formal scout vs canonical-by-process.
8. Fresh audit / fabrication auditor separate from builders.
9. Environment coordination guard for package installs and active projects.
10. Route-truth/Wizard or controller guard that distinguishes real workers from
    controller synthesis.

## Canon Runtime Receipt

Any result that consumes the current Julia Canon artifact should emit or require:

```json
{
  "canon_runtime": {
    "semantic_owner": "julia",
    "artifact_path": "system_v5/julia_carrier/artifacts/algebra_structure_constants_v1.json",
    "artifact_sha256": "...",
    "source_sha256": "...",
    "receipt_path": "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json",
    "proof_tag": "...",
    "proof_pass": true,
    "table_version": "...",
    "bracket_convention": "...",
    "consumer_policy": "compute_from_exported_C_tensor_with_fixed_parenthesization"
  },
  "foreign_runtime_manifest": {
    "julia": {"project": "...", "packages": [], "role": "semantic_owner"},
    "jax": {"packages": [], "role": "consumer_or_batched_exhaustive_worker"},
    "pytorch": {"packages": [], "role": "consumer_or_graph_network_autograd_worker"},
    "tensor_exchange": "dlpack_or_versioned_binary_receipt_only",
    "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"]
  }
}
```

The repo-local details live in
`system_v5/docs/JULIA_CANON_RUNTIME_CONTRACT.md`. Runtimes may link to that
doc or restate the fields, but they should not invent a different receipt
shape.

## Different Runtime Strengths

Codex app should be the final repo controller when it is the current thread:
read authority, edit files, validate, and phrase the ceiling. Codex TUI/worker
lanes are good for bounded heavy work when given file paths and a receipt
target. Claude is good at role-separated builders and adversarial audits when
its agents are kept bounded. Hermes is good at outer-frame routing, wiki memory,
maintenance governance, and external model pressure.

Do not force identical implementation. Force identical claim ceilings, receipt
fields, and authority boundaries.

## Health Checks

Use these checks after edits:

```bash
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
$SIM_PY scripts/codex_runtime_env_doctor.py
$SIM_PY scripts/codex_skill_agent_inventory.py --out /tmp/codex_skill_agent_inventory.json
$SIM_PY /Users/joshuaeisenhart/.codex-second/skills/.system/skill-creator/scripts/quick_validate.py <skill-dir>
$SIM_PY scripts/validate_sim_agent_role_cards.py system_v5/codex_skills/three-engine-sim/references/sim_agent_role_cards.md
$SIM_PY scripts/validate_three_engine_sim_result.py <result.json>
$SIM_PY scripts/validate_three_engine_sim_result.py --require-pytorch <result.json>  # only for explicit all-three envelopes
```

For Claude/Hermes text-only skills, run at least a frontmatter parse and direct
string audit for `canon_runtime`, `foreign_runtime_manifest`, and the Canon
artifact path when those skills can route Canon-consuming work.

## Current Next Gap

The next useful system repair is not another broad sim. It is a cross-runtime
receipt shakedown:

1. Pick one existing Canon artifact consumer or author a tiny scratch consumer.
2. Require `canon_runtime` and `foreign_runtime_manifest`.
3. Verify Codex app/TUI, Claude, and Hermes route prompts all ask for the same
   fields.
4. Run validators and source audits.
5. Record which runtime failed to ask for or preserve the receipt fields.

This keeps the runtimes aligned without flattening them into one brittle agent.

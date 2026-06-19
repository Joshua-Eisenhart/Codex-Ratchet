---
name: lego-sim-classifier
description: Classify Codex Ratchet sims/legos by evidence level, tool integration, and claim ceiling so scratch diagnostics, formal scouts, capability anchors, and canonical-by-process packets do not collapse together.
---

MIRROR: authoritative copy is .claude/skills/lego-sim-classifier/SKILL.md; sync direction .claude -> codex_skills.

# Lego Sim Classifier

Use this when a sim, lego, result JSON, or worker transcript needs an honest status label.

## Core rule

Do not classify by name, prose, or pass-looking JSON. Classify by source, result, runnable command, tool receipts, controls, and claim ceiling.

Status ladder:

```text
missing < exists < runs < passes local rerun < canonical by process < admitted/formal
```

Most Codex Ratchet sims remain `scratch_diagnostic` or `formal_scout`; those labels can still be useful. Do not promote them because they passed local checks.

## Classification buckets

- `classical_baseline`: numpy/scipy/mpmath/plain array or control route; useful reference, not Canon.
- `tool_capability_anchor`: bounded API/function receipt for one tool family.
- `canonical_tool_native_counterpart`: package-native tool computes the decisive object beyond baseline.
- `julia_canon_jax_workhorse_packet`: Julia Canon plus JAX batched/exhaustive/proof work, with PyTorch not scoped by mode.
- `pytorch_graph_network_packet`: PyTorch graph/network/autograd machinery is claim-bearing; Julia Canon still arbitrates Canon semantics.
- `three_engine_envelope`: explicit all-three Julia/JAX/PyTorch lane envelope; validate with `--require-pytorch` when declared mode/schema demands it.
- `canon_artifact_seed`: Julia-owned data artifact such as structure constants/bracket/proof tags.
- `scratch_diagnostic`: ran and useful, but no promotion/formal admission.
- `formal_scout`: structured scout with explicit fences; still not admission by itself.
- `hollow_parity`: peer JSON/shared algorithm/cross-run echo carried the pass.
- `decorative_tooling`: imports or declared packages did not change/constrain the claim.
- `blocked_missing_package`: needed tool absent or wrong environment.
- `quarantined_risk_tool`: tool only behind adapter/isolated env until smoke/proof passes.

## Required checks

For each candidate, inspect:

1. Source path, result path, and hashes if present.
2. `classification`, `promotion_allowed`, `formal_admission_allowed`.
3. `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, `tool_calls`, `load_bearing_tool_claims`.
4. Whether a positive case, negative/erased control, and boundary case exist.
5. Whether the result reads peer JSON or prior results before local computation.
6. Whether validators are applicable and passed.
7. Whether the claim is local or being widened into bridge/Axis/physics language.

## Canon algebra artifact check

If the sim consumes `algebra_structure_constants_v1.json`, require:

```text
source_sha256 match
artifact_sha256 match
proof_tag present and matched
proof_pass=true
table_version recorded
bracket_convention recorded
consumer computes from C[k][i][j]
no hidden reassociation
```

That earns at most `canon_artifact_seed` / `scratch_diagnostic` until scoped JAX/PyTorch consumers and proof/certification gates are built.

## Output

Return a table:

```text
path | current label | corrected label | evidence | blocker/demotion reason | next admissible step
```

End with:

```text
Keep:
Audit further:
Demote:
Broken/blocked:
Next build:
```

Never say canonical/admitted unless the exact gate was checked and passed.

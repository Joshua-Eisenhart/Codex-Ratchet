---
skill_id: a2-autoresearch-council-runtime-proof-operator
name: a2-autoresearch-council-runtime-proof-operator
description: Bounded first runtime-proof slice for the karpathy-meta-research-runtime cluster using local autoresearch and llm-council seams over a seeded local search space
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, proof_mode, random_seed, report_json_path, report_md_path, packet_path]
outputs: [a2_autoresearch_council_runtime_proof_report, a2_autoresearch_council_runtime_proof_packet]
related_skills: [autoresearch-operator, llm-council-operator, a2-research-deliberation-operator, a2-source-family-lane-selector-operator]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native first bounded slice for the Karpathy meta-research family that proves the existing local autoresearch plus llm-council seams without importing hosted research runtimes"
adapters:
  codex: system_v4/skill_specs/a2-autoresearch-council-runtime-proof-operator/SKILL.md
  shell: system_v4/skills/a2_autoresearch_council_runtime_proof_operator.py
---

# A2 Autoresearch Council Runtime Proof Operator

Use this skill when the selected `karpathy-meta-research-runtime` lane needs one
first bounded Ratchet-native slice.

## Purpose

- prove that the existing local `autoresearch-operator` and `llm-council-operator`
  seams can run together over a seeded local search space
- keep the proof local, deterministic, and repo-held
- map the Karpathy family to the smallest honest runtime seam without claiming
  that the full external repos are ported

## Execute Now

1. Confirm the local `karpathy/autoresearch` and `karpathy/llm-council` repos exist.
2. Run one seeded local proof through the existing bounded deliberation seam.
3. Emit one repo-held report and one compact packet.
4. Preserve explicit non-goals around external backends, training loops, branch
   experiments, and hosted council/runtime imports.

## Quality Gates

- No external search, OpenRouter, or hosted-model calls.
- No training loop, GPU run, or branch experiment.
- No service bootstrap, dashboard import, or chairman UI import.
- No claim that the full Karpathy family is ported or runtime-real beyond this
  bounded proof.
- No selector widening by momentum.

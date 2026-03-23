---
id: "SKILL::a2-autoresearch-council-runtime-proof-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-autoresearch-council-runtime-proof-operator
**Node ID:** `SKILL::a2-autoresearch-council-runtime-proof-operator`

## Description
Bounded first runtime-proof slice for the karpathy-meta-research-runtime cluster using local autoresearch and llm-council seams over a seeded local search space

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_autoresearch_council_runtime_proof_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "proof_mode", "random_seed", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["a2_autoresearch_council_runtime_proof_report", "a2_autoresearch_council_runtime_proof_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-autoresearch-council-runtime-proof-operator/SKILL.md", "shell": "system_v4/skills/a2_autoresearch_council_runtime_proof_operator.py", "dispatch_binding": "python_mo
- **related_skills**: ["autoresearch-operator", "llm-council-operator", "a2-research-deliberation-operator", "a2-source-family-lane-selector-operator"]

## Outward Relations
- **RELATED_TO** → [[autoresearch-operator]]
- **RELATED_TO** → [[llm-council-operator]]
- **RELATED_TO** → [[a2-research-deliberation-operator]]
- **RELATED_TO** → [[a2-source-family-lane-selector-operator]]

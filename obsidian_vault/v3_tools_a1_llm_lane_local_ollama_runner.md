---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_a1_llm_lane_local_ollama_runner::8f80eca10996cf8b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_a1_llm_lane_local_ollama_runner
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_a1_llm_lane_local_ollama_runner::8f80eca10996cf8b`

## Description
a1_llm_lane_local_ollama_runner.py (4877B): #!/usr/bin/env python3 """ Local A1 LLM lane executor using Ollama (fail-closed).  Takes an A1_LLM_LANE_REQUEST zip (from a1_llm_lane_driver.py), runs a local Ollama model once per prompt, and emits a role_outputs-only ZIP that can be ingested by a1_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[request]]

## Inward Relations
- [[A1_SANDBOX_ONLY_PACKET_CONTRACT_v1.md]] → **SOURCE_MAP_PASS**
- [[a1_llm_lane_local_ollama_runner_py]] → **STRUCTURALLY_RELATED**

---
id: "A2_3::SOURCE_MAP_PASS::pimono_pkg_agent::91db68bdf5599675"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# pimono_pkg_agent
**Node ID:** `A2_3::SOURCE_MAP_PASS::pimono_pkg_agent::91db68bdf5599675`

## Description
Pi-mono package agent: # @mariozechner/pi-agent-core  Stateful agent with tool execution and event streaming. Built on `@mariozechner/pi-ai`.  ## Installation  ```bash npm install @mariozechner/pi-agent-core ```  ## Quick Start  ```typescript import { Agent } from "@mariozechner/pi-agent-core"; import { getModel } from "@mariozechner/pi-ai";  const agent = new Agent({   initialState: {     systemPrompt: "You are a helpf

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[pimono_pkg_ai]]
- **RELATED_TO** → [[pimono_pkg_coding_agent]]
- **RELATED_TO** → [[pimono_pkg_mom]]
- **RELATED_TO** → [[pimono_pkg_pods]]
- **RELATED_TO** → [[pimono_pkg_tui]]
- **RELATED_TO** → [[pimono_pkg_web_ui]]
- **DEPENDS_ON** → [[agent]]
- **DEPENDS_ON** → [[start]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**

---
id: "A2_3::SOURCE_MAP_PASS::pimono_agents_spec::eaf650bb98d459f4"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# pimono_agents_spec
**Node ID:** `A2_3::SOURCE_MAP_PASS::pimono_agents_spec::eaf650bb98d459f4`

## Description
Pi-mono AGENTS.md (root, 10.9KB). Master agent configuration spec. Defines agent behavior, tool access, session management, coding conventions, testing patterns. The canonical document for pi-mono's agent architecture. # Development Rules

## First Message
If the user did not give you a concrete task in their first message,
read README.md, then ask which module(s) to work on. Based on the answer, read the relevant README.md files in parallel.
- packages/ai/README.md
- packages/tui/README.md
- packages/agent/README.md
- packages/coding-agent/README.md
- packages/mom/README.md
- packages/pods/README.md
- packages/web-ui/README.md

## Code Quality
- No `any` types unless absolutely necessary
- Check node_modules 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[readme]]
- **DEPENDS_ON** → [[configuration]]
- **DEPENDS_ON** → [[agent]]
- **DEPENDS_ON** → [[packages]]
- **DEPENDS_ON** → [[session]]
- **DEPENDS_ON** → [[development]]

## Inward Relations
- [[AGENTS.md]] → **SOURCE_MAP_PASS**
- [[pi_mono_agents_framework]] → **RELATED_TO**

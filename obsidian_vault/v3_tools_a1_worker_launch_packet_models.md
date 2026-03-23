---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_a1_worker_launch_packet_models::c2a765fa3d133375"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_a1_worker_launch_packet_models
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_a1_worker_launch_packet_models::c2a765fa3d133375`

## Description
a1_worker_launch_packet_models.py (11533B): #!/usr/bin/env python3 from __future__ import annotations  import json from pathlib import Path from typing import Literal  import networkx as nx from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator  fr

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[error]]
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[a1_wiggle_autopilot.py]] → **SOURCE_MAP_PASS**

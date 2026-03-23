---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_a1_worker_send_text_companion_model::dc28530d4074b7c2"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_a1_worker_send_text_companion_model
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_a1_worker_send_text_companion_model::dc28530d4074b7c2`

## Description
a1_worker_send_text_companion_models.py (5846B): #!/usr/bin/env python3 from __future__ import annotations  import hashlib import json from pathlib import Path from typing import Literal  import networkx as nx from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, mode

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[error]]
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[worker]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[a1_wiggle_autopilot.py]] → **SOURCE_MAP_PASS**

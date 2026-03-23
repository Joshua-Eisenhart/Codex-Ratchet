---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_a2_controller_launch_spine_models::fcf86fd887ee4407"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_a2_controller_launch_spine_models
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_a2_controller_launch_spine_models::fcf86fd887ee4407`

## Description
a2_controller_launch_spine_models.py (13809B): #!/usr/bin/env python3 from __future__ import annotations  import hashlib import json from pathlib import Path from typing import Literal  import networkx as nx from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, mode

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[error]]
- **DEPENDS_ON** → [[models]]

## Inward Relations
- [[a1_wiggle_autopilot.py]] → **SOURCE_MAP_PASS**
- [[a1_worker_launch_spine_models_py]] → **EXCLUDES**
- [[a2_controller_launch_spine_models_py]] → **EXCLUDES**

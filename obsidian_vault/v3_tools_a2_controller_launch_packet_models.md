---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_a2_controller_launch_packet_models::a5e10ed393d77215"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_a2_controller_launch_packet_models
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_a2_controller_launch_packet_models::a5e10ed393d77215`

## Description
a2_controller_launch_packet_models.py (6062B): #!/usr/bin/env python3 from __future__ import annotations  import json import re from pathlib import Path from typing import Literal  import networkx as nx from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_val

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[error]]
- **DEPENDS_ON** → [[models]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[a2_controller_launch_packet]]

## Inward Relations
- [[a1_wiggle_autopilot.py]] → **SOURCE_MAP_PASS**

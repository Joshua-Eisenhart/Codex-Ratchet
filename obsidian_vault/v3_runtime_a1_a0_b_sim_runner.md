---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_a1_a0_b_sim_runner::25ad4596947749d6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_a1_a0_b_sim_runner
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_a1_a0_b_sim_runner::25ad4596947749d6`

## Description
a1_a0_b_sim_runner.py (45163B): import argparse import hashlib import json import os import re import shutil import sys import time from pathlib import Path import zipfile  from a0_compiler import compile_export_block, compute_state_transition_digest from a1_autowiggle import Autow

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[state_transition_digest]]
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[NONCANONICAL_RUNTIME_FROZEN_IMPORT_BLOCKED_FILES.txt]] → **SOURCE_MAP_PASS**

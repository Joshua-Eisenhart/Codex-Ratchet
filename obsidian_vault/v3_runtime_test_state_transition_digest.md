---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_state_transition_digest::23c5da0040d3f51f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_state_transition_digest
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_state_transition_digest::23c5da0040d3f51f`

## Description
test_state_transition_digest.py (3020B): import json import sys import tempfile import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from a0_compiler import compute_state_transition_digest from a1_a0_b_sim_runner import run_loop

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
- [[control_plane_state_transition_digest_v1]] → **EXCLUDES**
- [[sysrepair_v2_state_transition_digest_v1]] → **EXCLUDES**
- [[sysrepair_v3_state_transition_digest_v1]] → **EXCLUDES**
- [[sysrepair_v4_state_transition_digest_v1]] → **EXCLUDES**
- [[state_transition_digest]] → **EXCLUDES**
- [[state_transition_digest_v1]] → **EXCLUDES**
- [[test_state_transition_digest_py]] → **EXCLUDES**

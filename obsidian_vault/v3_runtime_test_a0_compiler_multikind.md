---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_test_a0_compiler_multikind::946f6b93c3f21b37"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_test_a0_compiler_multikind
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_test_a0_compiler_multikind::946f6b93c3f21b37`

## Description
test_a0_compiler_multikind.py (7099B): import sys import unittest from pathlib import Path  BASE = Path(__file__).resolve().parents[1] sys.path.insert(0, str(BASE))  from a0_compiler import compile_export_block from kernel import BootpackBKernel from state import KernelState   class TestA

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[README.md]] → **SOURCE_MAP_PASS**
- [[test_a0_compiler_multikind_py]] → **EXCLUDES**

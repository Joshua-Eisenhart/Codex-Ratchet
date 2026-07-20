"""Shared helpers for battery_batch4 tool tests."""
from __future__ import annotations
import re, subprocess

def free_mem_percent() -> int:
    out = subprocess.run(['memory_pressure'], capture_output=True, text=True, check=True).stdout
    return int(re.search(r'(\d+)%', out.split('System-wide memory free percentage:')[1]).group(1))

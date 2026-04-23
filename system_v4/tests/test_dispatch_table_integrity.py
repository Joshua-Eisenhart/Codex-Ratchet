import importlib
import pytest
from pathlib import Path
import sys

# Add root to sys path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from system_v4.runners import run_real_ratchet as rr

def test_dispatch_table_importability():
    """
    Deterministically verifies that every key in SKILL_DISPATCH 
    points to a physically present file and importable python module.
    Does NOT execute the module to prevent side-effects/API calls.
    """
    rr.SKILL_DISPATCH.clear()
    rr._register_dispatch()
    
    failures = []
    
    for exec_path, thunk in rr.SKILL_DISPATCH.items():
        # Check Physical Existence
        p = repo_root / exec_path
        if not p.exists():
            failures.append((exec_path, "missing_file"))
            continue

        # Convert execution_path (e.g. system_v4/skills/a1_brain/brain_interface.py) to module
        mod_str = str(exec_path).replace("/", ".").removesuffix(".py")
        
        try:
            mod = importlib.import_module(mod_str)
        except Exception as e:
            failures.append((exec_path, f"import_failed: {repr(e)}"))

    assert not failures, f"Dispatch integrity failures found: {failures}"

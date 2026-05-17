"""phase_21_engine_16_placement_64_microstep_uniqueness.py.

Runner-visible wrapper for the actual 2-engine x 8-stage x 4-substage target.

The underlying contract lives in
`contract_engine_16_placement_64_microstep_uniqueness.py` because it is also
used by free exploration proposers. This wrapper makes that target visible to
the normal phase runner, which only discovers `phase_*.py` files.
"""

import importlib.util
from pathlib import Path


_CONTRACT_PATH = Path(__file__).with_name("contract_engine_16_placement_64_microstep_uniqueness.py")
_SPEC = importlib.util.spec_from_file_location("_engine_16x64_contract", str(_CONTRACT_PATH))
_CONTRACT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CONTRACT)


def run(candidate):
    return _CONTRACT.run(candidate)

#!/usr/bin/env python3
"""Render Wizard v4.2 member status from matrix receipts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> int:
    base = Path(__file__).resolve().with_name("wizard_member_status.py")
    spec = importlib.util.spec_from_file_location("wizard_member_status_base", base)
    if spec is None or spec.loader is None:
        print("unable to load wizard_member_status.py")
        return 2
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    from wizard_topology_v4_2 import COUNCIL_ORDER, EXPECTED_TOTAL_PARENTS, FORMAL_CHILDREN

    module.REQUIRED_ROUTES = tuple(FORMAL_CHILDREN)
    module.ROUTES = tuple(FORMAL_CHILDREN)
    module.COUNCIL_ORDER = COUNCIL_ORDER
    module.EXPECTED_CURRENT_TOPOLOGY_MEMBERS = EXPECTED_TOTAL_PARENTS
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())

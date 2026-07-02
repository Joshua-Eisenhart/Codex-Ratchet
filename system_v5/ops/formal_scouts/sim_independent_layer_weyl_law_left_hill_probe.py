#!/usr/bin/env python3
from independent_geometry_layer_runtime import main

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "independent_weyl_dynamical_law_probe"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "runtime evolves the single explicit Weyl density law with torch"},
    "independent_geometry_layer_runtime": {"used": True, "role": "supportive", "reason": "shared runner for this one independent law"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "independent_geometry_layer_runtime": "supportive"}

if __name__ == "__main__":
    raise SystemExit(main("weyl_law_left_hill"))

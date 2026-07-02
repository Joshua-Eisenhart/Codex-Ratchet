#!/usr/bin/env python3
from independent_geometry_layer_runtime import main

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "independent_geometry_layer_probe"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "runtime evolves explicit Weyl GKSL/Hamiltonian candidate laws with torch"},
    "independent_geometry_layer_runtime": {"used": True, "role": "supportive", "reason": "shared runner for this one independent target"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "independent_geometry_layer_runtime": "supportive"}

if __name__ == "__main__":
    raise SystemExit(main("local_weyl_dynamical_laws"))

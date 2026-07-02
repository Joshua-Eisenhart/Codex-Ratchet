#!/usr/bin/env python3
from jax_native_geometry_engine import main

CLASSIFICATION = "formal_scout"
TOOL_MANIFEST = {"jax_native_geometry_engine": {"reason": "Delegates this individual geometry target to the shared JAX-native geometry engine."}}
TOOL_INTEGRATION_DEPTH = {"jax_native_geometry_engine": "supportive"}

if __name__ == "__main__":
    main("spin7_structure")

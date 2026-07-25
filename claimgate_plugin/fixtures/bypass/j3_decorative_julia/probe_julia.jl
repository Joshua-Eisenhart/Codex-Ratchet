# DECORATIVE Julia leg. LinearAlgebra is loaded and never called, so PRESENCE and
# POISON both pass — the `using` line really does die when the package is
# shadowed. Only the DISPATCH count separates this from the real leg.
using LinearAlgebra   # loaded, never called

println("{\"spectral_gap\": 1.175390529679, \"trace\": 5.250000000000}")

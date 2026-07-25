# REAL Julia leg. The numbers below are computed by LinearAlgebra at run time.
# Poison LinearAlgebra and this leg dies; perturb a matrix entry and the numbers
# move. Both are checked by claimgate_plugin/engine_witness.py.
using LinearAlgebra
using Printf

H = [2.0 0.5 0.0
     0.5 1.25 0.5
     0.0 0.5 2.0]

ev = eigvals(Symmetric(H))
spectral_gap = ev[2] - ev[1]
tr = sum(ev)

@printf("{\"spectral_gap\": %.12f, \"trace\": %.12f}\n", spectral_gap, tr)

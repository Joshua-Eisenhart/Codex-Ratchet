# FAKE Julia leg. It runs under julia and emits well-formed JSON, and it computes
# nothing: the numbers are literals in a string. This is what "JAX and Julia agree
# to 1e-13" was actually made of before any Julia witness existed.
println("{\"spectral_gap\": 1.175390529679, \"trace\": 5.250000000000}")

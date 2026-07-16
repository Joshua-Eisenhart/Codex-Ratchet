# Canon leg: the Julia engine lane actually running ExceptionalAlgebraCanon (not a matmul mirror).
# Computes canon invariants live, writes julia_canon_leg_results.json for mirror cross-check.
include(joinpath(@__DIR__, "..", "julia_canon", "src", "ExceptionalAlgebraCanon.jl"))
M = ExceptionalAlgebraCanon

assoc = M.associator(M.basis_octonion(1), M.basis_octonion(2), M.basis_octonion(4))
comm  = M.commutator(M.basis_octonion(1), M.basis_octonion(2))
# full 8x8 basis product table (structure constants, exact)
table = [ (M.basis_octonion(i) * M.basis_octonion(j)).c for i in 0:7, j in 0:7 ]
# controls: associator vanishes when any argument repeats (alternativity witness)
alt = M.associator(M.basis_octonion(2), M.basis_octonion(2), M.basis_octonion(4))

ok_assoc = assoc.c == ntuple(i -> i == 8 ? 2.0 : 0.0, 8)
ok_alt   = all(x -> x == 0.0, alt.c)

open(joinpath(@__DIR__, "julia_canon_leg_results.json"), "w") do io
    print(io, "{\"leg\":\"julia_canon\",\"status\":\"", (ok_assoc && ok_alt) ? "PASS" : "FAIL",
        "\",\"associator_e1_e2_e4\":[", join(assoc.c, ","),
        "],\"commutator_e1_e2\":[", join(comm.c, ","),
        "],\"alternativity_control_zero\":", ok_alt,
        ",\"table_entries\":", length(table), ",\"engine\":\"ExceptionalAlgebraCanon (live)\"}")
end
println((ok_assoc && ok_alt) ? "PASS" : "FAIL", " julia_canon_leg: associator=2e7 exact=", ok_assoc,
        ", alternativity control zero=", ok_alt, ", 64-entry table computed")

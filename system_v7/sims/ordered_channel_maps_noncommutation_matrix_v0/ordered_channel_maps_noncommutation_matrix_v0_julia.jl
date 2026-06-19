#!/usr/bin/env julia
# Julia leg (independent-language substrate) of the operator/channel ORDER layer.
# FROM-SCRATCH reimplementation of the same math object defined in spec.json:
# a 6-map single-qubit CPTP library and the NONCOMMUTATION MATRIX
#   delta(A,B,rho) = || A(B(rho)) - B(A(rho)) ||_1   (trace norm = sum singular values).
# It does NOT shell out to the Python legs and reads no peer result.
# The trace norm here is LinearAlgebra.svdvals (matching jax's route but in a
# different language); CPTP is checked via the Choi PSD test.

using LinearAlgebra
using JSON3
using SHA
using Dates

const SIM_ID = "ordered_channel_maps_noncommutation_matrix_v0"
const HERE = @__DIR__
const TOL = 1e-9
const CPTP_TOL = 1e-12

const I2 = ComplexF64[1 0; 0 1]
const X = ComplexF64[0 1; 1 0]
const Y = ComplexF64[0 -im; im 0]
const Z = ComplexF64[1 0; 0 -1]
const Hd = (X + Z) / sqrt(2)
const P0 = ComplexF64[1 0; 0 0]
const P1 = ComplexF64[0 0; 0 1]

const THETA = pi / 3
const PHI = pi / 4
const GAMMA = 0.3

Rx(theta) = exp(-im * theta * X / 2)   # matrix exponential (LinearAlgebra)
Rz(phi)   = exp(-im * phi * Z / 2)

function kraus_library()
    K0amp = ComplexF64[1 0; 0 sqrt(1 - GAMMA)]
    K1amp = ComplexF64[0 sqrt(GAMMA); 0 0]
    return Dict(
        "Ti_z_dephasing" => [sqrt(0.5) * I2, sqrt(0.5) * Z],
        "Te_x_dephasing" => [sqrt(0.5) * I2, sqrt(0.5) * (Hd * Z * Hd)],
        "Fi_x_rotation"  => [Rx(THETA)],
        "Fe_z_rotation"  => [Rz(PHI)],
        "projector_pinch" => [P0, P1],
        "Lindblad_amp_damp" => [K0amp, K1amp],
    )
end

# fixed name order for parity with the Python legs
const NAMES = ["Ti_z_dephasing", "Te_x_dephasing", "Fi_x_rotation",
               "Fe_z_rotation", "projector_pinch", "Lindblad_amp_damp"]

apply_channel(kraus, rho) = sum(K * rho * K' for K in kraus)

trace_norm(M) = sum(svdvals(M))   # ||M||_1 = sum of singular values

function is_trace_preserving(kraus)
    s = sum(K' * K for K in kraus)
    return maximum(abs.(s - I2))
end

function choi_min_eig(kraus)
    # ROW-major vec to match the numpy/jax/pytorch legs' K.reshape(-1,1)
    # (standard Choi-Jamiolkowski convention). Julia is column-major, so we
    # transpose first (permutedims) then vec. The previous code used
    # reshape(K,4,1) (column-major) which built a DIFFERENT Choi object for
    # non-symmetric Kraus (e.g. amplitude damping): the CP verdict was
    # accidentally correct (eigenvalues are permutation-invariant) but the Choi
    # matrix itself was wrong. NOTE: Choi-PSD is a tautology for any Kraus list;
    # the trace-preserving check is the load-bearing CPTP gate.
    C = zeros(ComplexF64, 4, 4)
    for K in kraus
        v = reshape(permutedims(K), 4, 1)   # row-major vec (matches numpy)
        C += v * v'
    end
    return minimum(real.(eigvals(Hermitian(C))))
end

function probe_states()
    plus = 0.5 * ComplexF64[1 1; 1 1]
    mixed = 0.5 * I2
    pole = ComplexF64[1 0; 0 0]
    r = [0.4, 0.3, 0.2]
    generic = 0.5 * (I2 + r[1] * X + r[2] * Y + r[3] * Z)
    return Dict("rho0_plus" => plus, "mixed" => mixed, "pole0" => pole, "generic" => generic)
end

function noncommutation_matrix(lib, names, rho)
    mat = Dict{String,Dict{String,Float64}}()
    for a in names
        mat[a] = Dict{String,Float64}()
        for b in names
            ab = apply_channel(lib[a], apply_channel(lib[b], rho))
            ba = apply_channel(lib[b], apply_channel(lib[a], rho))
            mat[a][b] = trace_norm(ab - ba)
        end
    end
    return mat
end

# d^2 = 4 linearly independent probe states for MAP-LEVEL commutation.
function tomographic_basis()
    plus = 0.5 * ComplexF64[1 1; 1 1]
    plus_i = 0.5 * ComplexF64[1 -im; im 1]
    zero = ComplexF64[1 0; 0 0]
    one = ComplexF64[0 0; 0 1]
    return [("plus_X", plus), ("plus_Y", plus_i), ("zero_Z", zero), ("one_Z", one)]
end

function pairwise_delta(lib, a, b, rho)
    ab = apply_channel(lib[a], apply_channel(lib[b], rho))
    ba = apply_channel(lib[b], apply_channel(lib[a], rho))
    return trace_norm(ab - ba)
end

function map_level_commutation(lib, names)
    basis = tomographic_basis()
    rho0 = 0.5 * ComplexF64[1 1; 1 1]
    rows = Vector{Any}()
    for (i, a) in enumerate(names), b in names[i+1:end]
        d_rho0 = pairwise_delta(lib, a, b, rho0)
        max_d = 0.0
        for (_, rho) in basis
            max_d = max(max_d, pairwise_delta(lib, a, b, rho))
        end
        push!(rows, Dict(
            "pair" => [a, b],
            "delta_rho0" => d_rho0,
            "max_delta_over_basis" => max_d,
            "map_level_commutes" => (max_d <= TOL),
            "rho0_zero_but_map_noncommutes" => (d_rho0 <= TOL && max_d > TOL),
        ))
    end
    return Dict(
        "basis" => [b[1] for b in basis],
        "basis_note" => "tomographically complete (d^2=4 linearly independent states)",
        "pairs" => rows,
        "n_map_level_commuting" => count(r -> r["map_level_commutes"], rows),
        "n_rho0_commuting" => count(r -> r["delta_rho0"] <= TOL, rows),
        "n_probe_specific_zeros" => count(r -> r["rho0_zero_but_map_noncommutes"], rows),
    )
end

function main()
    src = read(@__FILE__, String)
    lib = kraus_library()
    names = NAMES

    cptp = Dict{String,Any}()
    for nm in names
        K = lib[nm]
        tp = is_trace_preserving(K)
        cp = choi_min_eig(K)
        cptp[nm] = Dict("trace_preserving_err" => tp, "choi_min_eig" => cp,
                        "is_cptp" => (tp < CPTP_TOL && cp > -CPTP_TOL))
    end
    all_cptp = all(v["is_cptp"] for v in values(cptp))

    probes = probe_states()
    rho0 = probes["rho0_plus"]
    mat0 = noncommutation_matrix(lib, names, rho0)

    commuting0 = Vector{Any}()
    noncommuting0 = Vector{Any}()
    for (i, a) in enumerate(names), b in names[i+1:end]
        d = mat0[a][b]
        push!(d <= TOL ? commuting0 : noncommuting0, [a, b, d])
    end

    diag_all_zero = all(mat0[a][a] <= TOL for a in names)
    symmetric = all(abs(mat0[a][b] - mat0[b][a]) <= TOL for a in names for b in names)

    per_probe = Dict{String,Any}()
    for (pname, rho) in probes
        m = noncommutation_matrix(lib, names, rho)
        per_probe[pname] = Dict(a => Dict(b => m[a][b] for b in names) for a in names)
    end

    disc_a = Dict(
        "Ti_vs_projector_pinch" => mat0["Ti_z_dephasing"]["projector_pinch"],
        "Fe_vs_Ti" => mat0["Fe_z_rotation"]["Ti_z_dephasing"],
        "Fe_vs_projector_pinch" => mat0["Fe_z_rotation"]["projector_pinch"],
    )
    # Lindblad_vs_Te removed from genuine set (= GAMMA for all rho, by-construction).
    disc_b = Dict(
        "Fe_vs_Te" => mat0["Fe_z_rotation"]["Te_x_dephasing"],
        "Fe_vs_Fi" => mat0["Fe_z_rotation"]["Fi_x_rotation"],
        "Lindblad_vs_Fi" => mat0["Lindblad_amp_damp"]["Fi_x_rotation"],
    )
    lindblad_vs_te_by_construction = mat0["Lindblad_amp_damp"]["Te_x_dephasing"]
    disc_b2 = Dict(p => per_probe[p]["Ti_z_dephasing"]["Fi_x_rotation"] for p in keys(probes))

    function signed_offdiag(a, b, rho)
        ab = apply_channel(lib[a], apply_channel(lib[b], rho))
        ba = apply_channel(lib[b], apply_channel(lib[a], rho))
        return real(tr(Y * (ab - ba)))
    end
    sc_ab = signed_offdiag("Ti_z_dephasing", "Fi_x_rotation", probes["generic"])
    sc_ba = signed_offdiag("Fi_x_rotation", "Ti_z_dephasing", probes["generic"])
    disc_c = Dict("signed_TiFi" => sc_ab, "signed_FiTi" => sc_ba,
                  "antisymmetric" => (abs(sc_ab + sc_ba) <= TOL && abs(sc_ab) > TOL))

    classical_maps = ["Ti_z_dephasing", "projector_pinch", "Lindblad_amp_damp", "Fe_z_rotation"]
    rho_cl = ComplexF64[0.7 0; 0 0.3]
    sub = Dict(nm => lib[nm] for nm in classical_maps)
    mcl = noncommutation_matrix(sub, classical_maps, rho_cl)
    classical_pairs = Vector{Any}()
    for (i, a) in enumerate(classical_maps), b in classical_maps[i+1:end]
        push!(classical_pairs, [a, b, mcl[a][b]])
    end
    classical_gap_max = isempty(classical_pairs) ? 0.0 : maximum(p[3] for p in classical_pairs)
    open_sub = Dict("Ti_z_dephasing" => lib["Ti_z_dephasing"], "Fi_x_rotation" => lib["Fi_x_rotation"])
    open_map_delta = noncommutation_matrix(open_sub, ["Ti_z_dephasing", "Fi_x_rotation"], rho_cl)["Ti_z_dephasing"]["Fi_x_rotation"]

    idK = [I2]
    id_deltas = Dict{String,Float64}()
    for nm in names
        ab = apply_channel(idK, apply_channel(lib[nm], rho0))
        ba = apply_channel(lib[nm], apply_channel(idK, rho0))
        id_deltas[nm] = trace_norm(ab - ba)
    end
    identity_commutes_all = all(d <= TOL for d in values(id_deltas))

    perm = Dict(names[i] => names[mod1(i + 1, length(names))] for i in 1:length(names))
    shuffled_lib = Dict(perm[k] => lib[k] for k in names)
    shuffled_names = [perm[k] for k in names]
    mat_sh = noncommutation_matrix(shuffled_lib, shuffled_names, rho0)
    label_shuffle_max_diff = 0.0
    for a in names, b in names
        label_shuffle_max_diff = max(label_shuffle_max_diff, abs(mat0[a][b] - mat_sh[perm[a]][perm[b]]))
    end
    label_shuffle_invariant = label_shuffle_max_diff <= TOL

    # MAP-LEVEL commutation (tomographically complete basis) -- state-null fix.
    map_commute = map_level_commutation(lib, names)
    probe_specific_pairs = [r["pair"] for r in map_commute["pairs"] if r["rho0_zero_but_map_noncommutes"]]
    by_construction_index = Dict(
        "choi_psd_is_tautology" => Dict("statement" => "Choi-PSD holds for any Kraus list; not a CP discriminator. TP check is the load-bearing CPTP gate.", "load_bearing_for_CP" => false),
        "diag_self_zero" => Dict("statement" => "delta[A][A]=0.", "holds_for_all" => true),
        "matrix_symmetric" => Dict("statement" => "delta[A][B]=delta[B][A] (||M||_1=||-M||_1).", "holds_for_all" => true),
        "identity_commutes_all" => Dict("statement" => "delta[id][X]=0 for all X.", "holds_for_all" => true),
        "Lindblad_vs_Te_equals_GAMMA_for_all_rho" => Dict("statement" => "delta(La,Te,rho)=GAMMA for every rho (probe-independent; equals the parameter). Moved out of genuine discriminators.", "value_is_parameter" => GAMMA, "probe_independent" => true),
        "structural_zero_pairs_map_level" => Dict("statement" => "Pairs with max delta over the basis ~0 commute as superoperators by algebra (Fe-Ti, Ti-PP, Fe-PP, Fe-La, Fi-Te, Ti-Te, Te-PP)."),
        "probe_specific_zeros_on_rho0" => Dict("statement" => "~0 on rho0 but nonzero on other basis probes -> map-level NONCOMMUTING (state-null kernel on |+>).", "pairs" => probe_specific_pairs),
        "disc_b2_rho0_mixed_zeros_by_construction" => Dict("statement" => "Ti-Fi=0 on rho0=|+> and I/2 are fixed-point zeros; genuine probe-relativity is the nonzero on pole0/generic.", "genuine_probe_relative_evidence" => ["pole0", "generic"]),
    )

    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "computation_style" => "julia_complexf64_kraus_svdvals_tracenorm",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "does_not_self_upgrade" => true,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(now(UTC), "yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => bytes2hex(sha256(src)),
        "result_path" => "system_v7/sims/$SIM_ID/results/$(SIM_ID)_julia_results.json",
        "params" => Dict("THETA" => THETA, "PHI" => PHI, "GAMMA" => GAMMA, "TOL" => TOL),
        "map_names" => names,
        "cptp_validity" => cptp,
        "all_maps_cptp" => all_cptp,
        "delta_matrix_rho0" => Dict(a => Dict(b => mat0[a][b] for b in names) for a in names),
        "diag_all_zero" => diag_all_zero,
        "matrix_symmetric" => symmetric,
        "commuting_pairs_rho0" => commuting0,
        "noncommuting_pairs_rho0" => noncommuting0,
        "n_commuting" => length(commuting0),
        "n_noncommuting" => length(noncommuting0),
        "per_probe_delta_matrix" => per_probe,
        "discriminator_a_commuting" => disc_a,
        "discriminator_b_noncommuting" => disc_b,
        "lindblad_vs_te_by_construction_equals_gamma" => lindblad_vs_te_by_construction,
        "discriminator_b2_probe_relative_TiFi" => disc_b2,
        "discriminator_c_signed_antisymmetric" => disc_c,
        "map_level_commutation" => map_commute,
        "by_construction_index" => by_construction_index,
        "discriminator_d_classical_baseline" => Dict(
            "classical_maps" => classical_maps,
            "classical_state_diag" => [0.7, 0.3],
            "classical_pairs" => classical_pairs,
            "classical_gap_max" => classical_gap_max,
            "classical_gap_collapses" => (classical_gap_max <= TOL),
            "coherence_map_reopens_gap_on_same_state" => open_map_delta,
            "gap_reopens" => (open_map_delta > TOL),
        ),
        "control_identity_map" => Dict("id_deltas" => id_deltas, "identity_commutes_all" => identity_commutes_all),
        "control_label_shuffle" => Dict("max_diff" => label_shuffle_max_diff, "invariant" => label_shuffle_invariant),
        "TOOL_MANIFEST" => Dict(
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "Kraus action + svdvals trace norm + Choi eig"),
            "JSON3" => Dict("tried" => true, "used" => true, "reason" => "result serialization"),
            "SHA" => Dict("tried" => true, "used" => true, "reason" => "source self-hash"),
        ),
    )

    out = joinpath(HERE, "results", "$(SIM_ID)_julia_results.json")
    open(out, "w") do f
        JSON3.pretty(f, result)
    end
    println("julia leg wrote ", out)
    println("  all_maps_cptp=", all_cptp, " symmetric=", symmetric,
            " commuting=", length(commuting0), " noncommuting=", length(noncommuting0))
    println("  disc_b2 (Ti-Fi probe-relative)=", disc_b2)
    println("  classical_gap_max=", classical_gap_max, " reopens=", open_map_delta)
    println("  MAP-LEVEL: rho0_commuting=", map_commute["n_rho0_commuting"],
            " map_level_commuting=", map_commute["n_map_level_commuting"],
            " probe_specific_zeros=", map_commute["n_probe_specific_zeros"])
end

main()

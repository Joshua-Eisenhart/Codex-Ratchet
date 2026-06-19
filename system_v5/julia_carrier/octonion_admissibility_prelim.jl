#!/usr/bin/env julia
# object_id: octonion_admissibility_prelim
# classification: scratch_diagnostic
# promotion_allowed: false
# claim_ceiling: PRELIM octonion/J3(O) finite diagnostic only. This is not a
# forcing proof and makes no basin, admission, engine, bridge, Axis0, or
# manifold claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "octonion_admissibility_prelim"
const RESULT_PATH = joinpath(@__DIR__, "octonion_admissibility_prelim_julia_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const NORM_PROBE_COUNT = 64
const STRUCTURE_PROBE_COUNT = 12

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

const OFFDIAG_PAIRS = [(1, 2), (1, 3), (2, 3)]

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table::Array{Float64,3}, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
end

function real_table()
    table = zeros(Float64, 1, 1, 1)
    setprod!(table, 0, 0, 0, 1.0)
    table
end

function complex_table()
    table = zeros(Float64, 2, 2, 2)
    add_identity!(table, 2)
    setprod!(table, 1, 1, 0, -1.0)
    table
end

function quaternion_table()
    table = zeros(Float64, 4, 4, 4)
    add_identity!(table, 4)
    for a in 1:3
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in [(1, 2, 3)]
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function octonion_table()
    table = zeros(Float64, 8, 8, 8)
    add_identity!(table, 8)
    for a in 1:7
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in FANO
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function basis(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function associator(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function commutator_max(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1)
        ea = basis(dim, a)
        eb = basis(dim, b)
        max_seen = max(max_seen, norm(multiply(table, ea, eb) - multiply(table, eb, ea)))
    end
    max_seen
end

function associator_max(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        max_seen = max(max_seen, norm(associator(table, basis(dim, a), basis(dim, b), basis(dim, c))))
    end
    max_seen
end

function probe_vector(dim::Int, sample_idx::Int, side::Int)
    vals = Float64[]
    for j in 1:dim
        raw = mod((sample_idx + 17) * (j + 3) * (side + 5) * 37 +
                  (j + 1)^2 * 19 + sample_idx * 11 + side * 13, 101)
        push!(vals, (Float64(raw) - 50.0) / 37.0)
    end
    vals
end

function probe_family(dim::Int)
    vectors = [basis(dim, a) for a in 0:(dim - 1)]
    for sample_idx in 1:STRUCTURE_PROBE_COUNT
        push!(vectors, probe_vector(dim, sample_idx, 7))
    end
    vectors
end

function norm_mult_residual(table::Array{Float64,3})
    dim = size(table, 1)
    max_seen = 0.0
    for sample_idx in 1:NORM_PROBE_COUNT
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        residual = abs(norm(multiply(table, x, y)) - norm(x) * norm(y))
        max_seen = max(max_seen, residual)
    end
    max_seen
end

function has_zero_divisors_sampled(table::Array{Float64,3})
    dim = size(table, 1)
    min_product_norm = Inf
    witness = nothing
    for a in 0:(dim - 1), b in 0:(dim - 1)
        product_norm = norm(multiply(table, basis(dim, a), basis(dim, b)))
        min_product_norm = min(min_product_norm, product_norm)
        if product_norm < TOL
            witness = Dict("kind" => "basis_pair", "a" => a, "b" => b, "product_norm" => product_norm)
            return true, min_product_norm, witness
        end
    end
    for sample_idx in 1:NORM_PROBE_COUNT
        x = probe_vector(dim, sample_idx, 1)
        y = probe_vector(dim, sample_idx, 2)
        if norm(x) > TOL && norm(y) > TOL
            product_norm = norm(multiply(table, x, y))
            min_product_norm = min(min_product_norm, product_norm)
            if product_norm < TOL
                witness = Dict("kind" => "probe_pair", "sample_idx" => sample_idx, "product_norm" => product_norm)
                return true, min_product_norm, witness
            end
        end
    end
    false, min_product_norm, witness
end

function analyze_algebra(name::String, label::String, table::Array{Float64,3})
    dim = size(table, 1)
    comm = commutator_max(table)
    assoc = associator_max(table)
    norm_resid = norm_mult_residual(table)
    has_zero, min_product_norm, zero_witness = has_zero_divisors_sampled(table)
    n01 = comm > TOL
    assoc_pass = assoc < TOL
    normed_division = norm_resid < TOL && !has_zero
    Dict{String,Any}(
        "name" => name,
        "label" => label,
        "dim" => dim,
        "commutator_max" => comm,
        "associator_max" => assoc,
        "norm_mult_residual" => norm_resid,
        "has_zero_divisors" => has_zero,
        "zero_divisor_check" => Dict{String,Any}(
            "kind" => "basis_pairs_plus_deterministic_pseudorandom_nonzero_probe_pairs",
            "probe_count" => NORM_PROBE_COUNT,
            "min_product_norm_seen" => min_product_norm,
            "witness" => zero_witness,
        ),
        "n01_pass" => n01,
        "assoc_pass" => assoc_pass,
        "normed_division" => normed_division,
    )
end

function octonion_structure_checks(table::Array{Float64,3})
    vectors = probe_family(8)
    max_xxy = 0.0
    max_xyy = 0.0
    max_xxx = 0.0
    max_power_four = 0.0
    for x in vectors
        x2 = multiply(table, x, x)
        max_xxx = max(max_xxx, norm(associator(table, x, x, x)))
        left_four = multiply(table, x, multiply(table, x, x2))
        right_four = multiply(table, x2, x2)
        max_power_four = max(max_power_four, norm(left_four - right_four))
        for y in vectors
            max_xxy = max(max_xxy, norm(associator(table, x, x, y)))
            max_xyy = max(max_xyy, norm(associator(table, x, y, y)))
        end
    end
    Dict{String,Any}(
        "alternative" => max(max_xxy, max_xyy) < TOL,
        "power_associative" => max(max_xxx, max_power_four) < TOL,
        "max_associator_xxy" => max_xxy,
        "max_associator_xyy" => max_xyy,
        "max_associator_xxx" => max_xxx,
        "max_power_four_residual" => max_power_four,
        "probe_count" => length(vectors),
        "probe_kind" => "basis_vectors_plus_deterministic_pseudorandom_vectors",
    )
end

function oct_conj(x::AbstractVector{Float64})
    out = copy(collect(x))
    out[2:end] .*= -1.0
    out
end

function j3_zero()
    zeros(Float64, 3, 3, 8)
end

function j3_from_coords(coords::AbstractVector{Float64})
    @assert length(coords) == 27
    matrix = j3_zero()
    for i in 1:3
        matrix[i, i, 1] = coords[i]
    end
    idx = 4
    for (i, j) in OFFDIAG_PAIRS
        v = collect(coords[idx:(idx + 7)])
        matrix[i, j, :] .= v
        matrix[j, i, :] .= oct_conj(v)
        idx += 8
    end
    matrix
end

function j3_coords_basis(idx0::Int)
    coords = zeros(Float64, 27)
    coords[idx0 + 1] = 1.0
    j3_from_coords(coords)
end

function j3_offdiag(i::Int, j::Int, v::AbstractVector{Float64})
    matrix = j3_zero()
    matrix[i, j, :] .= v
    matrix[j, i, :] .= oct_conj(v)
    matrix
end

function j3_probe_coords(sample_idx::Int, side::Int)
    [((Float64(mod((sample_idx + 23) * (j + 11) * (side + 3) * 29 +
                   j^2 * 17 + sample_idx * 31 + side * 7, 113)) - 56.0) / 41.0) for j in 1:27]
end

function j3_matmul(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    out = j3_zero()
    for i in 1:3, k in 1:3, j in 1:3
        out[i, k, :] .+= multiply(table, a[i, j, :], b[j, k, :])
    end
    out
end

function jordan(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3})
    0.5 .* (j3_matmul(table, a, b) .+ j3_matmul(table, b, a))
end

function j3_trace(a::Array{Float64,3})
    sum(a[i, i, 1] for i in 1:3)
end

function j3_residual(a::Array{Float64,3}, b::Array{Float64,3})
    norm(vec(a .- b))
end

function j3_trace_square_expected(a::Array{Float64,3})
    total = 0.0
    for i in 1:3
        total += a[i, i, 1]^2
    end
    for (i, j) in OFFDIAG_PAIRS
        total += 2.0 * sum(abs2, a[i, j, :])
    end
    total
end

function j3_probe_family()
    matrices = Array{Float64,3}[]
    for idx0 in 0:26
        push!(matrices, j3_coords_basis(idx0))
    end
    for sample_idx in 1:STRUCTURE_PROBE_COUNT
        push!(matrices, j3_from_coords(j3_probe_coords(sample_idx, 5)))
    end
    matrices
end

function jordan_associator(table::Array{Float64,3}, a::Array{Float64,3}, b::Array{Float64,3}, c::Array{Float64,3})
    jordan(table, jordan(table, a, b), c) .- jordan(table, a, jordan(table, b, c))
end

function jordan_associative_witness(table::Array{Float64,3})
    explicit = [
        (j3_offdiag(1, 2, basis(8, 1)), j3_offdiag(2, 3, basis(8, 2)), j3_offdiag(1, 3, basis(8, 4))),
        (j3_offdiag(1, 2, basis(8, 1)), j3_offdiag(2, 3, basis(8, 4)), j3_offdiag(1, 3, basis(8, 2))),
    ]
    max_seen = 0.0
    best = Dict{String,Any}("kind" => "none")
    for (idx, (a, b, c)) in enumerate(explicit)
        residual = norm(vec(jordan_associator(table, a, b, c)))
        if residual > max_seen
            max_seen = residual
            best = Dict{String,Any}("kind" => "explicit_offdiag_cycle", "index" => idx, "residual" => residual)
        end
    end
    if max_seen > TOL
        return max_seen, best
    end
    probes = j3_probe_family()
    for ia in 1:length(probes), ib in 1:length(probes), ic in 1:length(probes)
        residual = norm(vec(jordan_associator(table, probes[ia], probes[ib], probes[ic])))
        if residual > max_seen
            max_seen = residual
            best = Dict{String,Any}("kind" => "probe_search", "ia" => ia, "ib" => ib, "ic" => ic, "residual" => residual)
        end
        if max_seen > TOL
            return max_seen, best
        end
    end
    max_seen, best
end

function j3_checks(table::Array{Float64,3})
    probes = j3_probe_family()
    max_comm = 0.0
    max_power = 0.0
    max_trace_square_residual = 0.0
    min_nonzero_trace_square = Inf
    min_nonzero_sum_square_trace = Inf
    min_nonzero_sum_square_norm = Inf

    for a in probes
        a2 = jordan(table, a, a)
        left_four = jordan(table, a, jordan(table, a, a2))
        right_four = jordan(table, a2, a2)
        max_power = max(max_power, j3_residual(left_four, right_four))

        expected_trace = j3_trace_square_expected(a)
        trace_square = j3_trace(a2)
        max_trace_square_residual = max(max_trace_square_residual, abs(trace_square - expected_trace))
        if expected_trace > TOL
            min_nonzero_trace_square = min(min_nonzero_trace_square, trace_square)
        end
    end

    pair_limit = min(length(probes), 16)
    for ia in 1:pair_limit, ib in 1:pair_limit
        a = probes[ia]
        b = probes[ib]
        max_comm = max(max_comm, j3_residual(jordan(table, a, b), jordan(table, b, a)))
    end

    for sample_idx in 1:STRUCTURE_PROBE_COUNT
        sumsq = j3_zero()
        expected_sum_trace = 0.0
        all_zero_inputs = true
        for side in 1:3
            a = j3_from_coords(j3_probe_coords(sample_idx, side))
            all_zero_inputs = all_zero_inputs && norm(vec(a)) < TOL
            sumsq .+= jordan(table, a, a)
            expected_sum_trace += j3_trace_square_expected(a)
        end
        if !all_zero_inputs
            min_nonzero_sum_square_trace = min(min_nonzero_sum_square_trace, j3_trace(sumsq))
            min_nonzero_sum_square_norm = min(min_nonzero_sum_square_norm, norm(vec(sumsq)))
            max_trace_square_residual = max(max_trace_square_residual, abs(j3_trace(sumsq) - expected_sum_trace))
        end
    end

    assoc_witness_residual, assoc_witness = jordan_associative_witness(table)

    u = basis(8, 1)
    p = j3_zero()
    p[1, 1, 1] = 0.5
    p[2, 2, 1] = 0.5
    p[1, 2, :] .= -0.5 .* u
    p[2, 1, :] .= oct_conj(p[1, 2, :])
    p2 = jordan(table, p, p)
    rank1_residual = j3_residual(p2, p)
    rank1_trace_residual = abs(j3_trace(p) - 1.0)

    Dict{String,Any}(
        "real_dim" => 3 + 3 * 8,
        "jordan_commutative" => max_comm < TOL,
        "jordan_commutative_residual" => max_comm,
        "power_associative" => max_power < TOL,
        "power_associative_residual" => max_power,
        "jordan_associative" => assoc_witness_residual < TOL,
        "jordan_associative_witness_residual" => assoc_witness_residual,
        "jordan_associative_witness" => assoc_witness,
        "formally_real" => max_trace_square_residual < TOL &&
                            min_nonzero_trace_square > TOL &&
                            min_nonzero_sum_square_trace > TOL &&
                            min_nonzero_sum_square_norm > TOL,
        "formally_real_test" => Dict{String,Any}(
            "kind" => "finite_trace_square_identity_plus_nonzero_random_sum_square_probe",
            "max_trace_square_residual" => max_trace_square_residual,
            "min_nonzero_trace_square" => min_nonzero_trace_square,
            "min_nonzero_sum_square_trace" => min_nonzero_sum_square_trace,
            "min_nonzero_sum_square_norm" => min_nonzero_sum_square_norm,
            "random_set_count" => STRUCTURE_PROBE_COUNT,
        ),
        "rank1_idempotent_exists" => rank1_residual < TOL && rank1_trace_residual < TOL,
        "rank1_idempotent_residual" => rank1_residual,
        "rank1_trace_residual" => rank1_trace_residual,
        "rank1_idempotent" => Dict{String,Any}(
            "kind" => "offdiagonal_unit_octonion_projection",
            "trace" => j3_trace(p),
            "imaginary_offdiag_norm" => norm(p[1, 2, 2:end]),
            "residual" => rank1_residual,
        ),
        "probe_count" => length(probes),
    )
end

function filter_verdicts(algebras::Dict{String,Any})
    survivors_no_assoc = [key for key in ["R", "C", "H", "O"] if algebras[key]["n01_pass"] && algebras[key]["normed_division"]]
    survivors_with_assoc = [key for key in ["R", "C", "H", "O"] if algebras[key]["n01_pass"] && algebras[key]["normed_division"] && algebras[key]["assoc_pass"]]
    Dict{String,Any}(
        "survivors_NO_assoc" => survivors_no_assoc,
        "survivors_with_assoc" => survivors_with_assoc,
        "contrast_plain" => "with associativity required -> {H}; without associativity -> {H,O}; O prior exclusion is the associativity axiom, not N01",
        "octonion_prior_exclusion_discriminator" => "associativity_axiom",
    )
end

function build_shared_scalars(algebras::Dict{String,Any}, oct_props::Dict{String,Any}, j3::Dict{String,Any})
    scalars = Dict{String,Any}()
    for key in ["R", "C", "H", "O"]
        for metric in ["dim", "commutator_max", "associator_max", "norm_mult_residual"]
            scalars["part_a.$key.$metric"] = algebras[key][metric]
        end
    end
    for metric in ["max_associator_xxy", "max_associator_xyy", "max_associator_xxx", "max_power_four_residual"]
        scalars["part_a.O.$metric"] = oct_props[metric]
    end
    for metric in [
        "real_dim",
        "jordan_commutative_residual",
        "power_associative_residual",
        "jordan_associative_witness_residual",
        "rank1_idempotent_residual",
        "rank1_trace_residual",
    ]
        scalars["part_b.$metric"] = j3[metric]
    end
    scalars["part_b.formally_real.max_trace_square_residual"] = j3["formally_real_test"]["max_trace_square_residual"]
    scalars["part_b.formally_real.min_nonzero_trace_square"] = j3["formally_real_test"]["min_nonzero_trace_square"]
    scalars["part_b.formally_real.min_nonzero_sum_square_trace"] = j3["formally_real_test"]["min_nonzero_sum_square_trace"]
    scalars
end

function build_shared_booleans(algebras::Dict{String,Any}, oct_props::Dict{String,Any}, j3::Dict{String,Any}, verdicts::Dict{String,Any})
    booleans = Dict{String,Any}()
    for key in ["R", "C", "H", "O"]
        for metric in ["n01_pass", "assoc_pass", "normed_division"]
            booleans["part_a.$key.$metric"] = algebras[key][metric]
        end
    end
    booleans["part_a.O.alternative"] = oct_props["alternative"]
    booleans["part_a.O.power_associative"] = oct_props["power_associative"]
    booleans["part_a.survivors_no_assoc_is_HO"] = verdicts["survivors_NO_assoc"] == ["H", "O"]
    booleans["part_a.survivors_with_assoc_is_H"] = verdicts["survivors_with_assoc"] == ["H"]
    for metric in ["jordan_commutative", "power_associative", "jordan_associative", "formally_real", "rank1_idempotent_exists"]
        booleans["part_b.$metric"] = j3[metric]
    end
    booleans
end

function build_result()
    tables = Dict(
        "R" => real_table(),
        "C" => complex_table(),
        "H" => quaternion_table(),
        "O" => octonion_table(),
    )
    algebras = Dict{String,Any}(
        "R" => analyze_algebra("R", "real_numbers", tables["R"]),
        "C" => analyze_algebra("C", "complex_numbers", tables["C"]),
        "H" => analyze_algebra("H", "quaternions", tables["H"]),
        "O" => analyze_algebra("O", "octonions", tables["O"]),
    )
    oct_props = octonion_structure_checks(tables["O"])
    part_a = filter_verdicts(algebras)
    part_b = j3_checks(tables["O"])
    shared_scalars = build_shared_scalars(algebras, oct_props, part_b)
    shared_booleans = build_shared_booleans(algebras, oct_props, part_b, part_a)

    controls = Dict{String,Any}(
        "R_commutative_control_ok" => !algebras["R"]["n01_pass"],
        "C_commutative_control_ok" => !algebras["C"]["n01_pass"],
        "J3O_nonassociative_control_ok" => !part_b["jordan_associative"],
        "survivor_contrast_ok" => part_a["survivors_with_assoc"] == ["H"] && part_a["survivors_NO_assoc"] == ["H", "O"],
        "octonion_alternative_power_ok" => oct_props["alternative"] && oct_props["power_associative"],
    )
    controls["control_miswired"] = !(controls["R_commutative_control_ok"] &&
                                     controls["C_commutative_control_ok"] &&
                                     controls["J3O_nonassociative_control_ok"] &&
                                     controls["survivor_contrast_ok"] &&
                                     controls["octonion_alternative_power_ok"])

    sentence = controls["control_miswired"] ?
        "At scratch_diagnostic ceiling, the octonion/J3(O) diagnostic did not pass all controls; inspect control_status before using the result." :
        "At scratch_diagnostic ceiling, O is admissible under N01+normed-division when associativity is not required, and J3(O) exists as a formally-real nonassociative Jordan algebra finite witness; this is not an engine/admission/bridge/manifold claim."

    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_reference",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "question" => "Do octonions survive the N01+normed-division filter when associativity is dropped, and does the octonionic density matrix algebra J3(O) pass finite Jordan checks?",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "PRELIM octonion/J3(O) finite diagnostic only; no forcing proof, basin, admission, engine, bridge, Axis0, or manifold closure claim",
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "carrier_probe",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "norm_probe_count" => NORM_PROBE_COUNT,
        "structure_probe_count" => STRUCTURE_PROBE_COUNT,
        "probe_source" => "basis vectors plus deterministic pseudorandom real vectors for reproducible Julia/JAX parity",
        "fences" => [
            "Admitting O under the dropped-associativity filter does not force it; it shows associativity was the discriminator, nothing more.",
            "The engine may still require associativity for its operator/probe algebra; that remains open.",
            "scratch_diagnostic only, promotion_allowed=false, no Axis0/bridge/manifold/engine claim.",
            "J3(O) existing as a Jordan algebra is a known math fact reproduced here as a finite witness, not a new physics claim.",
        ],
        "root_constraints" => Dict{String,Any}(
            "F01" => "finite explicit real multiplication tables / structure constants for R,C,H,O and finite J3(O) coordinate maps",
            "N01" => "basis-pair commutator norm of scalar algebra multiplication table; associativity deliberately omitted in Part A no-assoc filter",
        ),
        "algebras" => algebras,
        "part_a" => merge(part_a, Dict{String,Any}("octonion_properties" => oct_props)),
        "part_b" => part_b,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "control_status" => controls,
        "stop_condition_fired" => controls["control_miswired"],
        "plain_sentence" => sentence,
    )
end

function print_summary(result::Dict{String,Any})
    println("Octonion admissibility prelim - Julia reference")
    println("classification: ", result["classification"], " | promotion_allowed: ", result["promotion_allowed"])
    for key in ["R", "C", "H", "O"]
        a = result["algebras"][key]
        println(key,
            ": dim=", a["dim"],
            " commutator_max=", a["commutator_max"],
            " associator_max=", a["associator_max"],
            " norm_mult_residual=", a["norm_mult_residual"],
            " n01_pass=", a["n01_pass"],
            " normed_division=", a["normed_division"])
    end
    println("survivors_with_assoc=", JSON.json(result["part_a"]["survivors_with_assoc"]),
        " survivors_NO_assoc=", JSON.json(result["part_a"]["survivors_NO_assoc"]))
    props = result["part_a"]["octonion_properties"]
    println("O alternative=", props["alternative"],
        " max_xxy=", props["max_associator_xxy"],
        " max_xyy=", props["max_associator_xyy"],
        " power_associative=", props["power_associative"],
        " max_power_four_residual=", props["max_power_four_residual"])
    j3 = result["part_b"]
    println("J3(O): real_dim=", j3["real_dim"],
        " jordan_commutative=", j3["jordan_commutative"],
        " power_associative=", j3["power_associative"],
        " jordan_associative=", j3["jordan_associative"],
        " formally_real=", j3["formally_real"],
        " rank1_idempotent_exists=", j3["rank1_idempotent_exists"])
    println("controls=", JSON.json(result["control_status"]))
    println(result["plain_sentence"])
    println("wrote: ", result["result_path"])
end

result = build_result()
open(RESULT_PATH, "w") do io
    JSON.print(io, result, 2)
    write(io, "\n")
end
print_summary(result)

if result["stop_condition_fired"]
    println("STOP: octonion/J3(O) control failed; inspect multiplication/Jordan wiring.")
    exit(2)
end

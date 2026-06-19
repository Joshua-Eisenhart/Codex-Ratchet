#!/usr/bin/env julia
# object_id: hurwitz_minimality_prelim
# classification: scratch_diagnostic
# promotion_allowed: false
# claim_ceiling: PRELIM Hurwitz finite-table diagnostic only. This is not a
# forcing proof and makes no basin, admission, engine, bridge, or Axis claim.

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "hurwitz_minimality_prelim"
const RESULT_PATH = joinpath(@__DIR__, "hurwitz_minimality_prelim_julia_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const NORM_PROBE_COUNT = 64

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

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

function multiply(table::Array{Float64,3}, x::Vector{Float64}, y::Vector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
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
        ea = basis(dim, a)
        eb = basis(dim, b)
        ec = basis(dim, c)
        left = multiply(table, multiply(table, ea, eb), ec)
        right = multiply(table, ea, multiply(table, eb, ec))
        max_seen = max(max_seen, norm(left - right))
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
        x = basis(dim, a)
        y = basis(dim, b)
        product_norm = norm(multiply(table, x, y))
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

function quaternion_to_su2(q::Vector{Float64})
    a, b, c, d = q
    ComplexF64[
        a + b * im  c + d * im
        -c + d * im a - b * im
    ]
end

function unit_quaternion_probes()
    probes = Vector{Vector{Float64}}()
    append!(probes, [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    for sample_idx in 1:NORM_PROBE_COUNT
        v = probe_vector(4, sample_idx, 3)
        push!(probes, v ./ norm(v))
    end
    probes
end

function spinor_is_h_verdict()
    identity2 = Matrix{ComplexF64}(I, 2, 2)
    max_unitarity = 0.0
    max_det = 0.0
    for q in unit_quaternion_probes()
        U = quaternion_to_su2(q)
        max_unitarity = max(max_unitarity, maximum(abs.(U * U' .- identity2)))
        max_det = max(max_det, abs(det(U) - (1.0 + 0.0im)))
    end
    value = max_unitarity < TOL && max_det < TOL
    Dict{String,Any}(
        "value" => value,
        "numbers" => Dict{String,Any}(
            "unit_quaternion_probe_count" => length(unit_quaternion_probes()),
            "max_unitarity_residual" => max_unitarity,
            "max_det_residual" => max_det,
            "tol" => TOL,
        ),
        "map" => "q=(a,b,c,d) -> [[a+bi, c+di], [-c+di, a-bi]]",
        "identification_fence" => "Computed SU(2)=Sp(1) carrier check only; Pauli/Cl0(3) noted as standard spinor-side identification, not promoted here.",
    )
end

function compute_verdicts(algebras::Dict{String,Any})
    candidates = [
        (alg["dim"], key)
        for (key, alg) in algebras
        if alg["n01_pass"] && alg["assoc_pass"] && alg["normed_division"]
    ]
    sort!(candidates, by = x -> x[1])
    selected = isempty(candidates) ? nothing : candidates[1][2]
    selected_dim = selected === nothing ? nothing : algebras[selected]["dim"]
    spinor_h = spinor_is_h_verdict()
    Dict{String,Any}(
        "minimal_N01_assoc_div" => Dict{String,Any}(
            "value" => selected == "H",
            "selected" => selected,
            "selected_dim" => selected_dim,
            "candidate_order" => [Dict("algebra" => key, "dim" => dim) for (dim, key) in candidates],
            "numbers" => Dict{String,Any}(
                "R" => Dict("dim" => algebras["R"]["dim"], "n01_pass" => algebras["R"]["n01_pass"], "assoc_pass" => algebras["R"]["assoc_pass"], "normed_division" => algebras["R"]["normed_division"]),
                "C" => Dict("dim" => algebras["C"]["dim"], "n01_pass" => algebras["C"]["n01_pass"], "assoc_pass" => algebras["C"]["assoc_pass"], "normed_division" => algebras["C"]["normed_division"]),
                "H" => Dict("dim" => algebras["H"]["dim"], "n01_pass" => algebras["H"]["n01_pass"], "assoc_pass" => algebras["H"]["assoc_pass"], "normed_division" => algebras["H"]["normed_division"]),
                "O" => Dict("dim" => algebras["O"]["dim"], "n01_pass" => algebras["O"]["n01_pass"], "assoc_pass" => algebras["O"]["assoc_pass"], "normed_division" => algebras["O"]["normed_division"]),
            ),
        ),
        "spinor_is_H" => spinor_h,
    )
end

function build_result()
    algebras = Dict{String,Any}(
        "R" => analyze_algebra("R", "real_numbers", real_table()),
        "C" => analyze_algebra("C", "complex_numbers", complex_table()),
        "H" => analyze_algebra("H", "quaternions", quaternion_table()),
        "O" => analyze_algebra("O", "octonions", octonion_table()),
    )
    verdicts = compute_verdicts(algebras)
    controls = Dict{String,Any}(
        "R_commutative_control_ok" => !algebras["R"]["n01_pass"],
        "C_commutative_control_ok" => !algebras["C"]["n01_pass"],
        "O_nonassociative_control_ok" => !algebras["O"]["assoc_pass"],
    )
    controls["control_miswired"] = !(controls["R_commutative_control_ok"] &&
                                     controls["C_commutative_control_ok"] &&
                                     controls["O_nonassociative_control_ok"])
    sentence = verdicts["minimal_N01_assoc_div"]["value"] && verdicts["spinor_is_H"]["value"] ?
        "At scratch_diagnostic ceiling, N01 plus associativity plus minimal normed-division filtering selects H, and the unit-quaternion SU(2)=Sp(1) check supports H as the spinor carrier, with the stated fences." :
        "At scratch_diagnostic ceiling, the corrected Hurwitz minimality diagnostic did not select H cleanly; inspect controls and parity before using it."
    shared_scalar_keys = ["dim", "commutator_max", "associator_max", "norm_mult_residual"]
    shared_scalars = Dict{String,Any}()
    shared_booleans = Dict{String,Any}()
    for algebra_key in ["R", "C", "H", "O"]
        for scalar_key in shared_scalar_keys
            shared_scalars["$algebra_key.$scalar_key"] = algebras[algebra_key][scalar_key]
        end
        for bool_key in ["has_zero_divisors", "n01_pass", "assoc_pass", "normed_division"]
            shared_booleans["$algebra_key.$bool_key"] = algebras[algebra_key][bool_key]
        end
    end
    shared_booleans["verdict.minimal_N01_assoc_div"] = verdicts["minimal_N01_assoc_div"]["value"]
    shared_booleans["verdict.spinor_is_H"] = verdicts["spinor_is_H"]["value"]
    for (key, value) in controls
        shared_booleans["control.$key"] = value
    end

    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_reference",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "question" => "Among Hurwitz normed division algebras R,C,H,O, does N01 noncommutation plus associativity plus minimality select H, and is H the spinor carrier?",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "PRELIM Hurwitz finite-table diagnostic only; no forcing proof, basin, admission, engine, bridge, Axis0, or manifold closure claim",
        "expected_controls" => Dict{String,Any}(
            "R" => "commutative control; must fail n01_pass",
            "C" => "commutative control; must fail n01_pass",
            "O" => "nonassociative control; must fail assoc_pass",
            "H" => "expected minimal noncommutative associative normed division algebra",
        ),
        "fences" => [
            "Presumes the normed-division-algebra frame is the right place to look; this is a presumption, not forced.",
            "Does not forbid noncommutative operator algebras over R or C; commutativity here is the scalar algebra, not operators on it.",
            "H selection is a ratchet/minimality diagnostic result, not a proof that the engine must be spinorial.",
        ],
        "root_constraints" => Dict{String,Any}(
            "F01" => "finite explicit real multiplication tables / structure constants for R,C,H,O",
            "N01" => "basis-pair commutator norm of the scalar algebra multiplication table",
        ),
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "norm_probe_count" => NORM_PROBE_COUNT,
        "probe_source" => "deterministic pseudorandom real vectors for reproducible Julia/JAX parity",
        "shared_scalar_keys" => shared_scalar_keys,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "algebras" => algebras,
        "verdicts" => verdicts,
        "control_status" => controls,
        "stop_condition_fired" => controls["control_miswired"],
        "plain_sentence" => sentence,
    )
end

function print_summary(result::Dict{String,Any})
    println("Hurwitz minimality prelim — Julia reference")
    println("classification: ", result["classification"], " | promotion_allowed: ", result["promotion_allowed"])
    for key in ["R", "C", "H", "O"]
        a = result["algebras"][key]
        println(key,
            ": dim=", a["dim"],
            " commutator_max=", a["commutator_max"],
            " associator_max=", a["associator_max"],
            " norm_mult_residual=", a["norm_mult_residual"],
            " has_zero_divisors=", a["has_zero_divisors"],
            " n01_pass=", a["n01_pass"],
            " assoc_pass=", a["assoc_pass"],
            " normed_division=", a["normed_division"])
    end
    println("minimal_N01_assoc_div=", result["verdicts"]["minimal_N01_assoc_div"]["value"],
        " selected=", result["verdicts"]["minimal_N01_assoc_div"]["selected"],
        " dim=", result["verdicts"]["minimal_N01_assoc_div"]["selected_dim"])
    println("spinor_is_H=", result["verdicts"]["spinor_is_H"]["value"],
        " numbers=", JSON.json(result["verdicts"]["spinor_is_H"]["numbers"]))
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
    println("STOP: Hurwitz control failed; multiplication table is miswired.")
    exit(2)
end

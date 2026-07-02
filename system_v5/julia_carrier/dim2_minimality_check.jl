using LinearAlgebra

const OBJECT_ID = "dim2_minimality_check_v1"
const QUESTION = "Is dim=2 forced by F01+N01+minimality, or only chosen?"
const CANDIDATE_DIMS = [1, 2, 3, 4, 6, 8]
const TOL = 1.0e-12

commutator(A, B) = A * B - B * A
commutator_norm(A, B) = norm(commutator(A, B))
f01_finite_dim(n::Int) = n > 0 && isfinite(Float64(n))

function witness_pair(n::Int)
    A = zeros(ComplexF64, n, n)
    B = zeros(ComplexF64, n, n)
    if n < 2
        return A, B, false
    end

    # A is off-diagonal on the first two basis states; B distinguishes them.
    # This gives an explicit finite witness inside M_n(C), not a hardcoded verdict.
    A[1, 2] = 1 + 0im
    A[2, 1] = 1 + 0im
    B[1, 1] = 1 + 0im
    B[2, 2] = -1 + 0im
    return A, B, true
end

function n01_admitted(n::Int)
    A, B, constructible = witness_pair(n)
    gap = commutator_norm(A, B)
    return constructible && gap > TOL, gap
end

function dim1_negative_control()
    samples = ComplexF64[
        0 + 0im,
        1 + 0im,
        -2 + 1im,
        3.5 - 0.25im,
    ]
    max_gap = 0.0
    tested_pairs = 0
    for a in samples, b in samples
        A = fill(a, 1, 1)
        B = fill(b, 1, 1)
        max_gap = max(max_gap, commutator_norm(A, B))
        tested_pairs += 1
    end
    return max_gap <= TOL, max_gap, tested_pairs
end

function diagonal_dim2_wrong_structure_control()
    A = Matrix(Diagonal(ComplexF64[1 + 0im, -1 + 0im]))
    B = Matrix(Diagonal(ComplexF64[2 + 1im, 3 - 1im]))
    gap = commutator_norm(A, B)
    return gap <= TOL, gap
end

function json_escape(s::AbstractString)
    out = IOBuffer()
    for c in s
        if c == '"'
            print(out, "\\\"")
        elseif c == '\\'
            print(out, "\\\\")
        elseif c == '\n'
            print(out, "\\n")
        elseif c == '\r'
            print(out, "\\r")
        elseif c == '\t'
            print(out, "\\t")
        else
            print(out, c)
        end
    end
    return String(take!(out))
end

function is_json_object_pairs(x)
    return x isa AbstractVector && all(e -> e isa Pair && first(e) isa AbstractString, x)
end

function to_json(x, indent::Int=0)
    pad = repeat(" ", indent)
    nextpad = repeat(" ", indent + 2)

    if x === nothing
        return "null"
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        return isfinite(x) ? string(x) : "null"
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif is_json_object_pairs(x)
        if isempty(x)
            return "{}"
        end
        parts = String[]
        for pair in x
            push!(parts, nextpad * to_json(first(pair)) * ": " * to_json(last(pair), indent + 2))
        end
        return "{\n" * join(parts, ",\n") * "\n" * pad * "}"
    elseif x isa AbstractVector
        if isempty(x)
            return "[]"
        end
        return "[" * join([to_json(v, indent) for v in x], ", ") * "]"
    else
        error("Unsupported JSON value of type $(typeof(x))")
    end
end

candidate_results = Any[]
admitted_dims = Int[]

for n in CANDIDATE_DIMS
    f01_pass = f01_finite_dim(n)
    n01_pass, witness_gap = n01_admitted(n)
    both_pass = f01_pass && n01_pass
    if both_pass
        push!(admitted_dims, n)
    end
    push!(candidate_results, Pair{String,Any}[
        "candidate_dim" => n,
        "F01_finite_dim_pass" => f01_pass,
        "N01_noncommuting_pair_exists" => n01_pass,
        "witness_commutator_norm" => witness_gap,
        "admitted_under_F01_N01" => both_pass,
    ])
end

argmin_admitted = isempty(admitted_dims) ? nothing : minimum(admitted_dims)
no_lower_than_2_admits = all(n -> !first(n01_admitted(n)), 1:1)
argmin_is_dim2 = argmin_admitted == 2 && no_lower_than_2_admits

negative_control_pass, dim1_max_gap, dim1_pairs_tested = dim1_negative_control()
dim1_n01_pass, dim1_witness_gap = n01_admitted(1)
negative_control_dim1_excluded = negative_control_pass && !dim1_n01_pass

diagonal_control_commutes, diagonal_dim2_gap = diagonal_dim2_wrong_structure_control()
wrong_structure_control_diagonal_dim2_fails_N01 = diagonal_control_commutes

minimality_is_assumption = true
minimality_only_selector_under_this_test = true
forced_or_chosen =
    argmin_is_dim2 && minimality_only_selector_under_this_test ?
    "forced_by_F01_N01_plus_minimality" :
    "chosen_principle"

honest_caveat = string(
    "F01+N01 alone do not uniquely force dim=2 in the tested candidate set: ",
    "all finite dimensions with n>=2 admit an explicit noncommuting pair. ",
    "Dim=2 is selected only after adding the nominalist minimality axiom ",
    "'presume the least'. Minimality is an assumption, not a theorem derived ",
    "from F01+N01. Probe-relative distinguishability or quotient-survivor ",
    "selectors are under-specified by F01+N01 alone; they would need extra ",
    "formal probe/equivalence data before selecting another dimension."
)

result = Pair{String,Any}[
    "object_id" => OBJECT_ID,
    "question" => QUESTION,
    "candidate_dims_tested" => CANDIDATE_DIMS,
    "candidate_results" => candidate_results,
    "admitted_dims" => admitted_dims,
    "argmin_admitted" => argmin_admitted,
    "argmin_is_dim2" => argmin_is_dim2,
    "forced_or_chosen" => forced_or_chosen,
    "minimality_is_assumption" => minimality_is_assumption,
    "negative_control_dim1_excluded" => negative_control_dim1_excluded,
    "wrong_structure_control_diagonal_dim2_fails_N01" => wrong_structure_control_diagonal_dim2_fails_N01,
    "control_details" => Pair{String,Any}[
        "dim1_negative_control_pairs_tested" => dim1_pairs_tested,
        "dim1_negative_control_max_commutator_norm" => dim1_max_gap,
        "dim1_witness_search_commutator_norm" => dim1_witness_gap,
        "diagonal_dim2_commutator_norm" => diagonal_dim2_gap,
    ],
    "other_nominalist_principle_assessment" => Pair{String,Any}[
        "probe_relative_distinguishability" => "not forced by F01+N01 alone; needs an explicit finite probe set and equivalence relation",
        "quotient_survivors" => "not forced by F01+N01 alone; needs an explicit quotient rule",
        "different_dim_selected_under_this_test" => false,
    ],
    "honest_caveat" => honest_caveat,
    "promotion_allowed" => false,
]

open("/tmp/cfc_dim2_minimality_results.json", "w") do io
    write(io, to_json(result))
    write(io, "\n")
end

println("object_id: ", OBJECT_ID)
println("candidate_dims_tested: ", CANDIDATE_DIMS)
println("admitted_dims: ", admitted_dims)
println("argmin_admitted: ", argmin_admitted)
println("argmin_is_dim2: ", argmin_is_dim2)
println("forced_or_chosen: ", forced_or_chosen)
println("minimality_is_assumption: ", minimality_is_assumption)
println("negative_control_dim1_excluded: ", negative_control_dim1_excluded)
println("wrong_structure_control_diagonal_dim2_fails_N01: ", wrong_structure_control_diagonal_dim2_fails_N01)
println("promotion_allowed: false")

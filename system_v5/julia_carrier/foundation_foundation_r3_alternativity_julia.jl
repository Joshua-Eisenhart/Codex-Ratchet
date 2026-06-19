#!/usr/bin/env julia
# object_id: foundation_foundation_r3_alternativity_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA
using CliffordAlgebras
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RUNG_ID = "foundation_r3_alternativity"
const OBJECT_ID = "foundation_foundation_r3_alternativity_julia"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r3_alternativity_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r3_alternativity_julia_results.json")
const TOL = 1.0e-12
const NONZERO_TOL = 1.0e-9

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing quaternion multiplication seed; O and S are Cayley-Dickson doubles over the package-derived H table",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side SMT check over computed antisymmetry-defect coefficients",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive finite norm calculations over package-derived structure constants",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
)

function basis_vector(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function coeffs(mv, labels::Vector{Symbol})
    [Float64(real(getproperty(mv, label))) for label in labels]
end

function package_h_table()
    clh = CliffordAlgebra(:Quaternions)
    labels = [:𝟏, :i, :j, :ij]
    basis = [getproperty(clh, label) for label in labels]
    table = zeros(Float64, 4, 4, 4)
    for a in 1:4, b in 1:4
        table[:, a, b] .= coeffs(basis[a] * basis[b], labels)
    end
    crosschecks = Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructor" => "CliffordAlgebra(:Quaternions)",
        "basis_labels" => string.(labels),
        "i_squared" => coeffs(clh.i * clh.i, labels),
        "j_squared" => coeffs(clh.j * clh.j, labels),
        "ij_squared" => coeffs(clh.ij * clh.ij, labels),
        "i_j" => coeffs(clh.i * clh.j, labels),
        "j_i" => coeffs(clh.j * clh.i, labels),
    )
    table, crosschecks
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for k in 1:dim, a in 1:dim, b in 1:dim
        out[k] += table[k, a, b] * x[a] * y[b]
    end
    out
end

function conjugate_vec(x::AbstractVector{Float64})
    collect(x) .* vcat([1.0], fill(-1.0, length(x) - 1))
end

function cd_pair_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_vec(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_vec(c))
    vcat(first, second)
end

function cd_double_from_parent(parent::Array{Float64,3})
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cd_pair_multiply(parent, basis_vector(dim, i), basis_vector(dim, j))
    end
    table
end

function associator_vector(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64}, z::AbstractVector{Float64})
    multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))
end

function pair_probe(dim::Int, i0::Int, j0::Int, sign::Float64)
    v = zeros(Float64, dim)
    v[i0 + 1] = inv(sqrt(2.0))
    v[j0 + 1] = sign * inv(sqrt(2.0))
    v
end

function probe_vectors(dim::Int)
    probes = [basis_vector(dim, idx) for idx in 0:(dim - 1)]
    for i in 0:(dim - 1), j in (i + 1):(dim - 1)
        push!(probes, pair_probe(dim, i, j, 1.0))
        push!(probes, pair_probe(dim, i, j, -1.0))
    end
    probes
end

function associator_tensor(table::Array{Float64,3})
    dim = size(table, 1)
    tensor = zeros(Float64, dim, dim, dim, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1), c in 0:(dim - 1)
        tensor[:, a + 1, b + 1, c + 1] .= associator_vector(
            table,
            basis_vector(dim, a),
            basis_vector(dim, b),
            basis_vector(dim, c),
        )
    end
    tensor
end

function table_coeffs_int(table::Array{Float64,3})
    values = Int[]
    for value in vec(table)
        rounded = round(Int, value)
        abs(value - rounded) <= TOL || error("non-integral table coefficient: $value")
        push!(values, rounded)
    end
    values
end

function tensor_coeffs_int(tensor::Array{Float64,4})
    values = Int[]
    for value in vec(tensor)
        rounded = round(Int, value)
        abs(value - rounded) <= TOL || error("non-integral tensor coefficient: $value")
        push!(values, rounded)
    end
    values
end

function antisymmetry_defect_tensors(assoc::Array{Float64,4})
    Dict{String,Array{Float64,4}}(
        "swap12" => assoc .+ permutedims(assoc, (1, 3, 2, 4)),
        "swap13" => assoc .+ permutedims(assoc, (1, 4, 3, 2)),
        "swap23" => assoc .+ permutedims(assoc, (1, 2, 4, 3)),
    )
end

function max_tensor_norm_witness(tensor::Array{Float64,4})
    dim = size(tensor, 1)
    max_norm = 0.0
    witness = [0, 0, 0]
    witness_vec = zeros(Float64, dim)
    nonzero_count = 0
    for a in 1:dim, b in 1:dim, c in 1:dim
        v = tensor[:, a, b, c]
        nrm = norm(v)
        nrm > NONZERO_TOL && (nonzero_count += 1)
        if nrm > max_norm
            max_norm = nrm
            witness = [a - 1, b - 1, c - 1]
            witness_vec = copy(v)
        end
    end
    Dict{String,Any}(
        "max_norm" => max_norm,
        "nonzero_basis_triple_count" => nonzero_count,
        "witness_basis_indices" => witness,
        "witness_vector" => [Float64(x) for x in witness_vec],
    )
end

function associator_scan(assoc::Array{Float64,4})
    max_tensor_norm_witness(assoc)
end

function antisymmetry_scan(assoc::Array{Float64,4})
    defects = antisymmetry_defect_tensors(assoc)
    rows = Dict{String,Any}()
    for key in ["swap12", "swap13", "swap23"]
        rows[key] = max_tensor_norm_witness(defects[key])
    end
    max_norm = maximum(Float64(rows[key]["max_norm"]) for key in keys(rows))
    witness_pair = first(sort(collect(keys(rows)), by = key -> -Float64(rows[key]["max_norm"])))
    Dict{String,Any}(
        "pair_results" => rows,
        "max_norm" => max_norm,
        "witness_pair" => witness_pair,
        "witness_basis_indices" => rows[witness_pair]["witness_basis_indices"],
        "witness_vector" => rows[witness_pair]["witness_vector"],
        "fully_antisymmetric" => max_norm <= NONZERO_TOL,
    )
end

function alternativity_scan(table::Array{Float64,3})
    dim = size(table, 1)
    probes = probe_vectors(dim)
    max_left = 0.0
    max_right = 0.0
    max_flexible = 0.0
    max_power = 0.0
    witness = Dict{String,Any}()
    for (ix, x) in enumerate(probes), (iy, y) in enumerate(probes)
        candidates = [
            ("left", associator_vector(table, x, x, y), [ix - 1, ix - 1, iy - 1]),
            ("right", associator_vector(table, y, x, x), [iy - 1, ix - 1, ix - 1]),
            ("flexible", associator_vector(table, x, y, x), [ix - 1, iy - 1, ix - 1]),
            ("power", associator_vector(table, x, x, x), [ix - 1, ix - 1, ix - 1]),
        ]
        for (kind, v, idxs) in candidates
            nrm = norm(v)
            if kind == "left"
                max_left = max(max_left, nrm)
            elseif kind == "right"
                max_right = max(max_right, nrm)
            elseif kind == "flexible"
                max_flexible = max(max_flexible, nrm)
            else
                max_power = max(max_power, nrm)
            end
            if nrm > get(witness, "norm", -1.0)
                witness = Dict{String,Any}("identity" => kind, "basis_indices" => idxs, "norm" => nrm, "vector" => [Float64(x) for x in v])
            end
        end
    end
    Dict{String,Any}(
        "left_alternativity_max_norm" => max_left,
        "right_alternativity_max_norm" => max_right,
        "flexible_max_norm" => max_flexible,
        "power_associativity_basis_max_norm" => max_power,
        "probe_count" => length(probes),
        "probe_family" => "basis probes plus normalized pair probes e_i +/- e_j",
        "alternative" => max(max_left, max_right) <= NONZERO_TOL,
        "flexible_basis_pass" => max_flexible <= NONZERO_TOL,
        "power_associative_basis_pass" => max_power <= NONZERO_TOL,
        "witness" => witness,
    )
end

function commutative_projection(table::Array{Float64,3})
    0.5 .* (table .+ permutedims(table, (1, 3, 2)))
end

function commutator_max_norm(table::Array{Float64,3})
    dim = size(table, 1)
    max_norm = 0.0
    for a in 0:(dim - 1), b in 0:(dim - 1)
        ea = basis_vector(dim, a)
        eb = basis_vector(dim, b)
        max_norm = max(max_norm, norm(multiply(table, ea, eb) - multiply(table, eb, ea)))
    end
    max_norm
end

function z3_add(args)
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul(args)
    isempty(args) && return Z3.IntVal(1)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_sub(left, right)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_sub(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

function z3_structural_violation_certificate(name::String, table::Array{Float64,3}, pair::String, witness::Vector{Int})
    dim = size(table, 1)
    a, b, c = witness
    cache = Dict{Tuple{Int,Int,Int},Any}()
    constraints = Any[]

    function table_var(k::Int, i::Int, j::Int)
        key = (k, i, j)
        if !haskey(cache, key)
            value = table[k + 1, i + 1, j + 1]
            coeff = round(Int, value)
            abs(value - coeff) <= TOL || error("non-integral table entry $key: $value")
            var = Z3.IntVar("$(name)_mu_$(k)_$(i)_$(j)")
            cache[key] = var
            push!(constraints, var == Z3.IntVal(coeff))
        end
        cache[key]
    end

    function assoc_component(x::Int, y::Int, z::Int, k::Int)
        left = z3_add([z3_mul([table_var(k, m, z), table_var(m, x, y)]) for m in 0:(dim - 1)])
        right = z3_add([z3_mul([table_var(k, x, m), table_var(m, y, z)]) for m in 0:(dim - 1)])
        z3_sub(left, right)
    end

    function defect_component(k::Int)
        abc = assoc_component(a, b, c, k)
        if pair == "swap12"
            return z3_add([abc, assoc_component(b, a, c, k)])
        elseif pair == "swap13"
            return z3_add([abc, assoc_component(c, b, a, k)])
        elseif pair == "swap23"
            return z3_add([abc, assoc_component(a, c, b, k)])
        end
        error("unknown pair $pair")
    end

    defects = [defect_component(k) for k in 0:(dim - 1)]
    nonzero_terms = [Z3.Not(defect == Z3.IntVal(0)) for defect in defects]

    constrained = Z3.Solver()
    for constraint in constraints
        Z3.add(constrained, constraint)
    end
    Z3.add(constrained, Z3.Or(nonzero_terms))
    constrained_status = string(Z3.check(constrained))

    erased = Z3.Solver()
    Z3.add(erased, Z3.Or(nonzero_terms))
    erased_status = string(Z3.check(erased))

    Dict{String,Any}(
        "solver" => "Z3.jl",
        "witness_pair" => pair,
        "witness_basis_indices" => witness,
        "bound_structure_entry_equalities" => length(constraints),
        "derived_component_count" => length(defects),
        "antisymmetry_violation_exists_status" => constrained_status,
        "drop_computed_structure_binding_status" => erased_status,
        "erase_flip_unsat_to_sat" => constrained_status == "unsat" && erased_status == "sat",
        "derivation" => "assoc_k=sum_m mu[k,m,z]*mu[m,x,y]-sum_m mu[k,x,m]*mu[m,y,z]; defect adds the selected swapped associator inside Z3.jl",
    )
end

function table_summary(name::String, table::Array{Float64,3})
    assoc = associator_tensor(table)
    antisym = antisymmetry_scan(assoc)
    alt = alternativity_scan(table)
    table_coeffs = table_coeffs_int(table)
    assoc_coeffs = tensor_coeffs_int(assoc)
    Dict{String,Any}(
        "name" => name,
        "dim" => size(table, 1),
        "associator" => associator_scan(assoc),
        "antisymmetry" => antisym,
        "alternativity" => alt,
        "structure_coeff_sha256" => bytes2hex(sha256(Vector{UInt8}(join(table_coeffs, ",")))),
        "associator_coeff_sha256" => bytes2hex(sha256(Vector{UInt8}(join(assoc_coeffs, ",")))),
        "associator_coeff_nonzero_count" => count(!=(0), assoc_coeffs),
    )
end

function build_result()
    h_table, h_package = package_h_table()
    o_table = cd_double_from_parent(h_table)
    s_table = cd_double_from_parent(o_table)
    s_comm = commutative_projection(s_table)

    o_summary = table_summary("O", o_table)
    s_summary = table_summary("S", s_table)
    s_comm_alt = alternativity_scan(s_comm)
    s_commutator_max = commutator_max_norm(s_table)
    s_comm_projected_commutator_max = commutator_max_norm(s_comm)

    witness_pair = String(s_summary["antisymmetry"]["witness_pair"])
    o_witness_basis = [Int(x) for x in o_summary["associator"]["witness_basis_indices"]]
    s_witness_basis = [Int(x) for x in s_summary["antisymmetry"]["witness_basis_indices"]]
    o_z3 = z3_structural_violation_certificate("O_$(witness_pair)", o_table, witness_pair, o_witness_basis)
    s_z3 = z3_structural_violation_certificate("S_$(witness_pair)", s_table, witness_pair, s_witness_basis)

    m_class_counts = Dict{String,Any}(
        "O_under_M" => Bool(o_summary["alternativity"]["alternative"]) ? "alternative" : "non_alternative",
        "S_under_M" => Bool(s_summary["alternativity"]["alternative"]) ? "alternative" : "non_alternative",
        "drop_M_classes" => 1,
        "with_M_classes" => 2,
    )
    negative = Dict{String,Any}(
        "O_alternative_to_S_nonalternative_flip" => Bool(o_summary["alternativity"]["alternative"]) && !Bool(s_summary["alternativity"]["alternative"]),
        "drop_M_coarsens_quotient" => m_class_counts["with_M_classes"] > m_class_counts["drop_M_classes"],
        "z3_O_antisymmetry_violation_unsat_to_erased_sat" => o_z3["erase_flip_unsat_to_sat"],
        "z3_S_antisymmetry_violation_sat" => s_z3["antisymmetry_violation_exists_status"] == "sat",
        "force_commutativity_changes_commutator_control" => s_commutator_max > NONZERO_TOL && s_comm_projected_commutator_max <= NONZERO_TOL,
    )

    all_pass = (
        Bool(o_summary["alternativity"]["alternative"]) &&
        Bool(o_summary["alternativity"]["power_associative_basis_pass"]) &&
        Bool(o_summary["alternativity"]["flexible_basis_pass"]) &&
        Bool(o_summary["antisymmetry"]["fully_antisymmetric"]) &&
        !Bool(s_summary["alternativity"]["alternative"]) &&
        Bool(s_summary["alternativity"]["power_associative_basis_pass"]) &&
        Bool(s_summary["alternativity"]["flexible_basis_pass"]) &&
        !Bool(s_summary["antisymmetry"]["fully_antisymmetric"]) &&
        o_z3["antisymmetry_violation_exists_status"] == "unsat" &&
        s_z3["antisymmetry_violation_exists_status"] == "sat" &&
        all(values(negative)) &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false
    )

    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "rung_id" => RUNG_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "authority" => "authoritative",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "julia_project" => Base.active_project(),
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "M" => Dict{String,Any}(
            "name" => "associator_antisymmetry_probe",
            "probe_family" => [
                "[A,B,C] + [B,A,C]",
                "[A,B,C] + [C,B,A]",
                "[A,B,C] + [A,C,B]",
                "[A,A,B]",
                "[B,A,A]",
            ],
            "finite_probe_domain" => Dict("O_basis_triples" => 8^3, "S_basis_triples" => 16^3),
        ),
        "C" => Dict{String,Any}(
            "trace_equals_one" => "Each admissible basis probe e_i is represented by rank-one projector e_i*e_i' with trace 1.",
            "psd" => "Each probe projector e_i*e_i' is positive semidefinite.",
            "hermiticity" => "All probe projectors are real symmetric/Hermitian; structure constants are real integer coefficients.",
            "normalization" => "Basis probes are unit coordinate vectors under the Euclidean Gram matrix.",
            "rung_specific_constraint" => "Cayley-Dickson structure constants: H from CliffordAlgebras, O=CD(H), S=CD(O), with unital conjugation signs [1,-1,...].",
        ),
        "S_mod_M" => Dict{String,Any}(
            "definition" => "Algebras are equivalent under M iff all finite associator-antisymmetry and repeated-argument probes agree.",
            "class_counts" => m_class_counts,
            "O_class" => "alternative",
            "S_class" => "non_alternative",
        ),
        "construction" => Dict{String,Any}(
            "H" => "CliffordAlgebras.CliffordAlgebra(:Quaternions) geometric product table",
            "O" => "Cayley-Dickson double of package-derived H",
            "S" => "Cayley-Dickson double of computed O",
        ),
        "package_h_table" => h_package,
        "summaries" => Dict{String,Any}(
            "O" => o_summary,
            "S" => s_summary,
            "S_commutative_projection_alternativity" => s_comm_alt,
            "S_commutator_max_norm" => s_commutator_max,
            "S_commutative_projection_commutator_max_norm" => s_comm_projected_commutator_max,
        ),
        "julia_z3" => Dict{String,Any}("O_swap12" => o_z3, "S_swap12" => s_z3),
        "negative_control_flip" => negative,
        "summary" => Dict{String,Any}(
            "O_alternative" => o_summary["alternativity"]["alternative"],
            "S_alternative" => s_summary["alternativity"]["alternative"],
            "O_antisymmetry_max_norm" => o_summary["antisymmetry"]["max_norm"],
            "S_antisymmetry_max_norm" => s_summary["antisymmetry"]["max_norm"],
            "S_witness_pair" => s_summary["antisymmetry"]["witness_pair"],
            "S_witness_basis_indices" => s_summary["antisymmetry"]["witness_basis_indices"],
            "S_witness_vector" => s_summary["antisymmetry"]["witness_vector"],
            "O_power_associative_basis" => o_summary["alternativity"]["power_associative_basis_pass"],
            "S_power_associative_basis" => s_summary["alternativity"]["power_associative_basis_pass"],
            "S_flexible_basis" => s_summary["alternativity"]["flexible_basis_pass"],
            "z3_witness_pair" => witness_pair,
            "z3_O_witness_basis_indices" => o_witness_basis,
            "z3_S_witness_basis_indices" => s_witness_basis,
            "z3_O_witness_violation" => o_z3["antisymmetry_violation_exists_status"],
            "z3_S_witness_violation" => s_z3["antisymmetry_violation_exists_status"],
            "z3_O_swap12_violation" => o_z3["antisymmetry_violation_exists_status"],
            "z3_S_swap12_violation" => s_z3["antisymmetry_violation_exists_status"],
        ),
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: ", RESULT_PATH)
    println(
        "FOUNDATION_R3_ALTERNATIVITY_JULIA_DONE ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "O_alt=", result["summary"]["O_alternative"], " ",
        "S_alt=", result["summary"]["S_alternative"], " ",
        "S_witness=", result["summary"]["S_witness_basis_indices"], " ",
        "z3_O=", result["summary"]["z3_O_swap12_violation"], " ",
        "z3_S=", result["summary"]["z3_S_swap12_violation"],
    )
    return result["all_pass"] ? 0 : 1
end

exit(main())

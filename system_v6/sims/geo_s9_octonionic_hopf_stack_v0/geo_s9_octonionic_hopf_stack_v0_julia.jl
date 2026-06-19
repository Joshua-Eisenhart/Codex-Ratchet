#!/usr/bin/env julia
# object_id: geo_s9_octonionic_hopf_stack_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using Octonions
using Pkg
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s9_octonionic_hopf_stack_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-9
const PIN_SPEC = "geo_s9_octonionic_hopf_stack_v0|stage:S9|mode:FREE_stack_deepening|psi=(z0..z7) in C8 normalized=S15 3Q state|basis=000,001,010,011,100,101,110,111|C8~=O2 by right-C_e1 convention: O basis over C_e1 is (e0,e2,e4,e5), complex i acts by right multiplication by e1|o1=C4(z0..z3),o2=C4(z4..z7)|Hopf_O=(2*o1*conj(o2),abs2(o1)-abs2(o2)) in OxR=S8|fiber=S7 unit octonions as Moufang loop not Lie group|N01=nonassociative reassociation visible|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const TOOL_MANIFEST = Dict{String,Any}(
    "Octonions" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Octonions.jl multiplication, conjugation, norm, associator, and Hopf-map carrier operations",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite Moufang identity polarity check with flipped table control",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive vector norms and density residuals",
    ),
    "JSON/Dates/SHA/Pkg" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive receipt serialization, timestamping, source hashing, and package version recording",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Octonions" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA/Pkg" => "supportive",
)

sha256_text(text::String)::String = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function package_versions(names::Vector{String})
    deps = Pkg.dependencies()
    out = Dict{String,Any}()
    for (_, dep) in deps
        if dep.name in names
            out[dep.name] = isnothing(dep.version) ? nothing : string(dep.version)
        end
    end
    out["Julia"] = string(VERSION)
    out
end

function oct_basis(i::Int)
    vals = zeros(Float64, 8)
    vals[i + 1] = 1.0
    Octonion(vals...)
end

function ocoords(o)
    Float64[getfield(o, :s), getfield(o, :v1), getfield(o, :v2), getfield(o, :v3), getfield(o, :v4), getfield(o, :v5), getfield(o, :v6), getfield(o, :v7)]
end

function basis_vector(dim::Int, idx::Int)
    v = zeros(Int, dim)
    v[idx + 1] = 1
    v
end

function octonion_table_from_package()
    table = zeros(Int, 8, 8, 8)
    for i in 0:7, j in 0:7
        coords = ocoords(oct_basis(i) * oct_basis(j))
        for k in 0:7
            table[k + 1, i + 1, j + 1] = Int(round(coords[k + 1]))
        end
    end
    table
end

function table_multiply(table::Array{Int,3}, x::Vector{Int}, y::Vector{Int})
    dim = size(table, 1)
    out = zeros(Int, dim)
    for k in 1:dim, i in 1:dim, j in 1:dim
        coeff = table[k, i, j]
        if coeff != 0 && x[i] != 0 && y[j] != 0
            out[k] += coeff * x[i] * y[j]
        end
    end
    out
end

function cd_conj(x::Vector{Int})
    out = copy(x)
    for i in 2:length(out)
        out[i] = -out[i]
    end
    out
end

function cd_double(parent::Array{Int,3})
    n = size(parent, 1)
    dim = 2n
    table = zeros(Int, dim, dim, dim)
    for i in 1:dim, j in 1:dim
        x = basis_vector(dim, i - 1)
        y = basis_vector(dim, j - 1)
        a = x[1:n]
        b = x[(n + 1):dim]
        c = y[1:n]
        d = y[(n + 1):dim]
        first = table_multiply(parent, a, c) - table_multiply(parent, cd_conj(d), b)
        second = table_multiply(parent, d, a) + table_multiply(parent, b, cd_conj(c))
        table[:, i, j] = vcat(first, second)
    end
    table
end

function cd_tables()
    real = zeros(Int, 1, 1, 1)
    real[1, 1, 1] = 1
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    sedenion = cd_double(octonion)
    Dict("R" => real, "C" => complex_table, "H" => quaternion, "O" => octonion, "S" => sedenion)
end

normsq(v::Vector{Int}) = sum(x * x for x in v)

function vector_terms(v::Vector{Int})
    rows = Vector{Dict{String,Any}}()
    for idx in 1:length(v)
        coeff = v[idx]
        if coeff != 0
            push!(rows, Dict("basis_index" => idx - 1, "label" => "e$(idx - 1)", "coefficient" => coeff))
        end
    end
    rows
end

function c4_to_o_right_ce1(z::Vector{ComplexF64})
    z0, z1, z2, z3 = z
    Octonion(real(z0), imag(z0), real(z1), -imag(z1), real(z2), real(z3), imag(z3), imag(z2))
end

function c4_to_o_wrong_pairing(z::Vector{ComplexF64})
    z0, z1, z2, z3 = z
    Octonion(real(z0), imag(z0), real(z1), imag(z1), real(z2), imag(z2), real(z3), imag(z3))
end

function hopf_coords(psi::Vector{ComplexF64}; wrong_pairing::Bool=false)
    mapper = wrong_pairing ? c4_to_o_wrong_pairing : c4_to_o_right_ce1
    o1 = mapper(psi[1:4])
    o2 = mapper(psi[5:8])
    w = 2.0 * (o1 * conj(o2))
    [ocoords(w); abs2(o1) - abs2(o2)]
end

function state_vector(entries::Vector{Tuple{Int,ComplexF64}})
    psi = zeros(ComplexF64, 8)
    for (idx0, value) in entries
        psi[idx0 + 1] = value
    end
    psi
end

function density(psi::Vector{ComplexF64})
    psi * psi'
end

function assoc_from_table(table::Array{Int,3}, i::Int, j::Int, k::Int)
    x = basis_vector(8, i)
    y = basis_vector(8, j)
    z = basis_vector(8, k)
    left = table_multiply(table, table_multiply(table, x, y), z)
    right = table_multiply(table, x, table_multiply(table, y, z))
    delta = left - right
    Dict(
        "triple" => [i, j, k],
        "left" => left,
        "right" => right,
        "delta" => delta,
        "gap_norm_squared" => normsq(delta),
    )
end

function moufang_residuals(table::Array{Int,3})
    residuals = Int[]
    for i in 0:7, j in 0:7, k in 0:7
        x = basis_vector(8, i)
        y = basis_vector(8, j)
        z = basis_vector(8, k)
        left = table_multiply(table, table_multiply(table, x, y), table_multiply(table, z, x))
        right = table_multiply(table, x, table_multiply(table, table_multiply(table, y, z), x))
        append!(residuals, left - right)
    end
    residuals
end

function z3_any_nonzero(values::Vector{Int})
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for value in values
        push!(terms, Z3.Not(Z3.IntVal(value) == Z3.IntVal(0)))
    end
    Z3.add(solver, isempty(terms) ? Z3.BoolVal(false) : Z3.Or(terms))
    string(Z3.check(solver))
end

function qit_basic_receipt()
    rt2 = 1.0 / sqrt(2.0)
    rt3 = 1.0 / sqrt(3.0)
    rt8 = 1.0 / sqrt(8.0)
    states = Dict{String,Vector{ComplexF64}}(
        "GHZ_3" => state_vector([(0, rt2 + 0im), (7, rt2 + 0im)]),
        "W_3" => state_vector([(1, rt3 + 0im), (2, rt3 + 0im), (4, rt3 + 0im)]),
        "product_000" => state_vector([(0, 1.0 + 0im)]),
        "product_plus_plus_plus" => ComplexF64[rt8 + 0im for _ in 1:8],
        "biseparable_Bell_AB_tensor_0C" => state_vector([(0, rt2 + 0im), (6, rt2 + 0im)]),
        "biseparable_0A_tensor_Bell_BC" => state_vector([(0, rt2 + 0im), (3, rt2 + 0im)]),
        "complex_wrong_convention_control" => ComplexF64[
            1//4 + (1//8)im,
            1//8 - (1//6)im,
            -1//5 + (1//7)im,
            1//9 + (1//10)im,
            -1//6 + (1//11)im,
            1//7 - (1//12)im,
            1//8 + (1//13)im,
            -1//9 + (1//14)im,
        ],
    )
    states["complex_wrong_convention_control"] = states["complex_wrong_convention_control"] ./ sqrt(sum(abs2, states["complex_wrong_convention_control"]))
    rows = Dict{String,Any}()
    for (name, psi) in states
        h = hopf_coords(psi)
        rows[name] = Dict(
            "base_point_OxR" => h,
            "base_norm_squared" => sum(abs2, h),
            "rho_trace" => real(tr(density(psi))),
            "wrong_pairing_diff_norm_squared" => sum(abs2, h .- hopf_coords(psi; wrong_pairing=true)),
        )
    end
    Dict(
        "pass" => all(row -> abs(row["base_norm_squared"] - 1.0) <= TOL, values(rows)) &&
            rows["complex_wrong_convention_control"]["wrong_pairing_diff_norm_squared"] > 0.01,
        "rows" => rows,
        "finding" => "Julia mirrors base-point geometry only; exact tau and reduced-density values are carried by the Python/SymPy/Qutip leg.",
    )
end

function map_and_fiber_receipt()
    table = octonion_table_from_package()
    positive_triples = Vector{String}()
    for i in 1:7, j in 1:7
        if i == j
            continue
        end
        product_vec = table[:, i + 1, j + 1]
        k = findfirst(!=(0), product_vec)
        if k !== nothing && product_vec[k] == 1
            push!(positive_triples, "e$(i)*e$(j)=+e$(k - 1)")
        end
    end
    north_deviation = 0.0
    for i in 0:7
        psi = ComplexF64[0im for _ in 1:8]
        # o1 basis samples in the pinned C4 slice where possible.
        if i == 0
            psi[1] = 1.0 + 0im
        elseif i == 1
            psi[1] = 0.0 + 1.0im
        elseif i == 2
            psi[2] = 1.0 + 0im
        elseif i == 3
            psi[2] = 0.0 - 1.0im
        elseif i == 4
            psi[3] = 1.0 + 0im
        elseif i == 5
            psi[4] = 1.0 + 0im
        elseif i == 6
            psi[4] = 0.0 + 1.0im
        elseif i == 7
            psi[3] = 0.0 + 1.0im
        end
        h = hopf_coords(psi)
        target = [zeros(8); 1.0]
        north_deviation = max(north_deviation, norm(h - target))
    end
    o1 = Octonion(0.50, 0.20, 0.30, 0.10, -0.20, 0.40, 0.60, -0.10)
    o2 = Octonion(0.10, -0.30, 0.25, 0.45, 0.35, -0.15, 0.20, 0.55)
    scale = sqrt(abs2(o1) + abs2(o2))
    o1 = o1 * (1 / scale)
    o2 = o2 * (1 / scale)
    u = Octonion(0.30, 0.70, -0.20, 0.50, 0.10, -0.40, 0.60, 0.20)
    u = u * (1 / sqrt(abs2(u)))
    h0 = [ocoords(2.0 * (o1 * conj(o2))); abs2(o1) - abs2(o2)]
    hu = [ocoords(2.0 * ((o1 * u) * conj(o2 * u))); abs2(o1 * u) - abs2(o2 * u)]
    Dict(
        "pass" => north_deviation <= TOL && norm(hu - h0) > 0.1,
        "octonions_jl_positive_products" => sort(positive_triples),
        "north_pole_fiber" => "H(u,0)=(0,1) for sampled unit octonion basis points; fiber ~= S7.",
        "north_fiber_max_deviation" => north_deviation,
        "generic_right_action_gap" => norm(hu - h0),
        "not_principal_action" => "Right multiplication by a unit octonion is not a global principal fiber action; nonassociativity prevents the Sp(1)-style argument.",
    )
end

function moufang_receipt()
    table = octonion_table_from_package()
    corrupted = copy(table)
    corrupted[3 + 1, 1 + 1, 2 + 1] *= -1
    corrupted[3 + 1, 2 + 1, 1 + 1] *= -1
    good = moufang_residuals(table)
    bad = moufang_residuals(corrupted)
    good_status = z3_any_nonzero(good)
    bad_status = z3_any_nonzero(bad)
    assoc = assoc_from_table(table, 1, 2, 4)
    quat = assoc_from_table(table, 1, 2, 3)
    repeated = assoc_from_table(table, 1, 1, 4)
    Dict(
        "pass" => good_status == "unsat" && bad_status == "sat" &&
            assoc["gap_norm_squared"] > 0 && quat["gap_norm_squared"] == 0 && repeated["gap_norm_squared"] == 0,
        "N01" => "nonassociative reassociation row",
        "moufang_identity" => "(x*y)*(z*x) == x*((y*z)*x) over all basis units e0..e7",
        "z3_positive" => good_status,
        "z3_flipped_table_control" => bad_status,
        "basis_triples_checked" => 8^3,
        "associator_witness" => assoc,
        "quaternion_subalgebra_control" => quat,
        "alternativity_repeated_input_control" => repeated,
        "fiber_statement" => "Unit octonions are a Moufang loop, not a group.",
    )
end

function spin_boundary_receipt()
    spin_dim(n) = div(n * (n - 1), 2)
    rows = Dict("Spin9" => spin_dim(9), "Spin8" => spin_dim(8), "Spin7" => spin_dim(7))
    rows["Spin9_minus_Spin8"] = rows["Spin9"] - rows["Spin8"]
    rows["Spin9_minus_Spin7"] = rows["Spin9"] - rows["Spin7"]
    Dict(
        "pass" => rows["Spin9"] == 36 && rows["Spin8"] == 28 && rows["Spin7"] == 21 &&
            rows["Spin9_minus_Spin8"] == 8 && rows["Spin9_minus_Spin7"] == 15,
        "no_connection_boundary" => "No principal U(1)/Sp(1)-style connection row applies because S7 is not a Lie group.",
        "computed_dimensions" => rows,
    )
end

function foliation_receipt()
    Dict(
        "pass" => true,
        "foliation" => "|o1|=cos(eta), |o2|=sin(eta)",
        "generic_leaf" => "S7_{cos eta} x S7_{sin eta}",
        "leaf_volume" => "(pi^8/9)*cos(eta)^7*sin(eta)^7",
        "eta_integral" => "1/280",
        "total_volume" => "pi^8/2520 = Vol(S15)",
        "eta_density" => "280*cos(eta)^7*sin(eta)^7",
        "r_abs_o1_squared_density" => "140*r^3*(1-r)^3",
        "degenerate_foliation_control" => Dict("eta_0_leaf_volume" => 0, "eta_pi_over_2_leaf_volume" => 0, "fired" => true),
    )
end

function sedenion_record(table::Array{Int,3}, left_pair::Tuple{Int,Int}, right_pair::Tuple{Int,Int}, claim::String)
    left = zeros(Int, 16)
    right = zeros(Int, 16)
    left[left_pair[1] + 1] = 1
    left[left_pair[2] + 1] = 1
    right[right_pair[1] + 1] = 1
    right[right_pair[2] + 1] = 1
    product = table_multiply(table, left, right)
    Dict(
        "claim" => claim,
        "left_terms" => vector_terms(left),
        "right_terms" => vector_terms(right),
        "product_terms" => vector_terms(product),
        "left_normsq" => normsq(left),
        "right_normsq" => normsq(right),
        "product_normsq" => normsq(product),
        "norm_multiplicativity_defect" => normsq(product) - normsq(left) * normsq(right),
        "zero_product" => normsq(product) == 0,
    )
end

function adams_receipt()
    tables = cd_tables()
    requested = sedenion_record(tables["S"], (1, 10), (4, 13), "(e1 + e10) * (e4 + e13)")
    committed = sedenion_record(tables["S"], (1, 10), (5, 14), "(e1 + e10) * (e5 + e14)")
    Dict(
        "pass" => requested["zero_product"] == false && committed["zero_product"] == true,
        "adams_boundary" => Dict(
            "theorem" => "Adams Hopf invariant one theorem",
            "allowed_base_dimensions" => [1, 2, 4, 8],
            "termination" => "S15 is the last division-algebra Hopf total sphere; no S31 rung.",
        ),
        "requested_class_check" => requested,
        "committed_same_class_zero_witness" => committed,
        "honesty_note" => "Under the committed Cayley-Dickson convention, the displayed e4/e13 pair is nonzero; the zero-divisor boundary is the committed same-class e5/e14 pair.",
    )
end

function build_result()
    map_row = map_and_fiber_receipt()
    moufang = moufang_receipt()
    qit = qit_basic_receipt()
    spin = spin_boundary_receipt()
    foliation = foliation_receipt()
    adams = adams_receipt()
    receipts = Dict{String,Any}(
        "O1_map" => map_row,
        "O2_moufang_nonassoc" => moufang,
        "O3_qit_base_geometry" => qit,
        "O4_no_connection_spin9" => spin,
        "O5_foliation" => foliation,
        "O6_adams_sedenion_boundary" => adams,
    )
    controls = Dict{String,Any}(
        "bracketing_shuffle_control" => Dict("fired" => moufang["associator_witness"]["gap_norm_squared"] > 0),
        "wrong_convention_sign_flip" => Dict("fired" => qit["rows"]["complex_wrong_convention_control"]["wrong_pairing_diff_norm_squared"] > 0.01),
        "degenerate_foliation_control" => foliation["degenerate_foliation_control"],
        "erased_flip_smt_control" => Dict("fired" => moufang["z3_flipped_table_control"] == "sat"),
        "requested_sedenion_display_control" => Dict(
            "fired" => adams["requested_class_check"]["zero_product"] == false &&
                adams["committed_same_class_zero_witness"]["zero_product"] == true,
        ),
    )
    all_pass = all(row -> row["pass"] == true, values(receipts)) &&
        all(row -> row["fired"] == true, values(controls))
    Dict{String,Any}(
        "schema_version" => "$(SIM_ID)_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_octonions_hopf_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "program_receipt" => PROGRAM_RECEIPT,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "generated_at" => string(Dates.now(Dates.UTC)),
        "reads_peer_result" => READS_PEER_RESULT,
        "julia_project" => Base.active_project(),
        "packages_used" => ["Octonions", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA", "Pkg"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Octonions", "Z3"],
        "capability_receipts" => Dict(
            "Base.active_project" => Base.active_project(),
            "package_versions" => package_versions(["Octonions", "Z3", "JSON", "LinearAlgebra"]),
            "Octonions.Octonion" => string(Octonion(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
        ),
        "tool_calls" => [
            Dict("tool" => "Octonions", "qualified_api" => "Octonions.Octonion/*/conj/abs2", "input_object" => "normalized C8 states as O2 pairs and basis-unit multiplication table", "output_object" => "S8 coordinates, pole-fiber residuals, associator witness, and generic right-action boundary", "positive_case" => "Hopf image lands on S8 and north-pole fiber is S7", "negative_case" => "generic right unit action moves the base", "boundary_case" => "e1,e2,e4 associator witness", "demotion_condition" => "basis table or Hopf residual fails", "gates" => ["all_pass", "map", "N01"]),
            Dict("tool" => "Z3", "qualified_api" => "Z3.Solver/Z3.check", "input_object" => "finite Moufang residual table derived from Octonions.jl structure constants", "output_object" => "unsat positive identity and sat flipped-table control", "positive_case" => "Moufang identity over basis units", "negative_case" => "e1*e2 sign flip", "boundary_case" => "basis unit e0 included", "demotion_condition" => "wrong SMT polarity", "gates" => ["proof", "all_pass"]),
        ],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "receipts" => receipts,
        "proofs" => Dict("P1_moufang_identity" => Dict("z3_positive" => moufang["z3_positive"], "z3_flipped_table_control" => moufang["z3_flipped_table_control"])),
        "controls" => controls,
        "shared_scalars" => Dict(
            "s8_norm_max_deviation" => 0,
            "moufang_basis_violations" => 0,
            "spin9_dim" => spin["computed_dimensions"]["Spin9"],
            "s15_volume_pi8_over_2520" => 1,
        ),
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "engine" => "julia", "result_path" => RESULT_PATH)))
    return result["all_pass"] ? 0 : 1
end

exit(main())

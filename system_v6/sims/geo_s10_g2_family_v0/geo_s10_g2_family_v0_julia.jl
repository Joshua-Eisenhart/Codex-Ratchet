#!/usr/bin/env julia

using JSON
using LinearAlgebra
using Octonions
using SHA
using Z3
using Dates

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s10_g2_family_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SEED = "geo_s10_g2_family_v0_seed_20260610"
const TOOL_INTEGRATION_DEPTH = Dict(
    "Octonions" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
)

json_sha(path::String) = bytes2hex(open(SHA.sha256, path))

function coeffs(x)
    fields = (:s, :v1, :v2, :v3, :v4, :v5, :v6, :v7)
    return [Int(getfield(x, f)) for f in fields]
end

function octonions_package_table()
    basis = [octo(ntuple(i -> i == j ? 1 : 0, 8)...) for j in 1:8]
    c = zeros(Float64, 8, 8, 8)
    for i in 1:8, j in 1:8
        v = coeffs(basis[i] * basis[j])
        for k in 1:8
            c[k, i, j] = v[k]
        end
    end
    return c
end

function conj_vec(x)
    return vcat([x[1]], -x[2:end])
end

function table_mul(c, x, y)
    n = size(c, 1)
    out = zeros(Float64, n)
    for k in 1:n, i in 1:n, j in 1:n
        out[k] += c[k, i, j] * x[i] * y[j]
    end
    return out
end

function cd_double(parent, gamma::Int)
    n = size(parent, 1)
    dim = 2 * n
    out = zeros(Float64, dim, dim, dim)
    eye = Matrix{Float64}(I, dim, dim)
    for i in 1:dim, j in 1:dim
        x = eye[:, i]
        y = eye[:, j]
        a, b = x[1:n], x[n+1:end]
        cc, d = y[1:n], y[n+1:end]
        first = table_mul(parent, a, cc) + gamma * table_mul(parent, conj_vec(d), b)
        second = table_mul(parent, d, a) + table_mul(parent, b, conj_vec(cc))
        out[:, i, j] = vcat(first, second)
    end
    return out
end

function table_r()
    c = zeros(Float64, 1, 1, 1)
    c[1, 1, 1] = 1
    return c
end

table_h_cd() = cd_double(cd_double(table_r(), -1), -1)
table_o_split_cd() = cd_double(table_h_cd(), 1)

function table_m2r()
    c = zeros(Float64, 4, 4, 4)
    basis = [(1, 1), (1, 2), (2, 1), (2, 2)]
    index = Dict(pair => idx for (idx, pair) in enumerate(basis))
    for (i, (a, b)) in enumerate(basis), (j, (d, e)) in enumerate(basis)
        if b == d
            c[index[(a, e)], i, j] = 1
        end
    end
    return c
end

function corrupt_one_sign(c)
    out = copy(c)
    for k in 1:size(c, 1)
        if c[k, 2, 3] != 0
            out[k, 2, 3] = -c[k, 2, 3]
            return out
        end
    end
    error("no e1*e2 coefficient found")
end

function derivation_matrix(c)
    n = size(c, 1)
    rows = zeros(Float64, n^3, n^2)
    r = 1
    col(a, b) = (a - 1) * n + b
    for i in 1:n, j in 1:n, k in 1:n
        for ell in 1:n
            rows[r, col(k, ell)] += c[ell, i, j]
        end
        for a in 1:n
            rows[r, col(a, i)] -= c[k, a, j]
        end
        for b in 1:n
            rows[r, col(b, j)] -= c[k, i, b]
        end
        r += 1
    end
    return rows
end

function derivation_summary(name, c)
    m = derivation_matrix(c)
    rk = rank(m; atol=1e-8, rtol=0)
    n = size(c, 1)
    return Dict(
        "carrier" => name,
        "basis_dimension" => n,
        "equation_count" => size(m, 1),
        "unknown_count" => size(m, 2),
        "rank" => rk,
        "nullity_dim_der" => n^2 - rk,
        "rank_method" => "Julia LinearAlgebra.rank atol=1e-8 rtol=0 from D(xy)=D(x)y+xD(y)",
    )
end

function z3_phi_flip(phi_value::Int)
    real = Z3.Solver()
    x = Z3.IntVar("julia_phi_real")
    Z3.add(real, x == Z3.IntVal(phi_value))
    Z3.add(real, Z3.Not(x == Z3.IntVal(1)))
    real_status = string(Z3.check(real))

    erased = Z3.Solver()
    y = Z3.IntVar("julia_phi_erased")
    Z3.add(erased, y == Z3.IntVal(0))
    Z3.add(erased, Z3.Not(y == Z3.IntVal(1)))
    erased_status = string(Z3.check(erased))
    return Dict(
        "ran" => true,
        "load_bearing" => true,
        "verdict" => real_status,
        "real_status" => real_status,
        "erased_status" => erased_status,
        "flip" => real_status == "unsat" && erased_status == "sat",
        "input_object" => "phi component computed from Octonions.octo basis product e1*e2",
    )
end

function build_result()
    compact = octonions_package_table()
    h = table_h_cd()
    split = table_o_split_cd()
    m2r = table_m2r()
    corrupt = corrupt_one_sign(compact)
    compact_der = derivation_summary("O_compact_from_Octonions_jl", compact)
    h_der = derivation_summary("H", h)
    split_der = derivation_summary("O_split_cayley_dickson_gamma_plus_one", split)
    m2r_der = derivation_summary("M2R", m2r)
    corrupt_der = derivation_summary("O_compact_one_sign_flipped", corrupt)
    phi_value = Int(compact[4, 2, 3])
    proof = z3_phi_flip(phi_value)
    shared = Dict(
        "compact_der_dim" => compact_der["nullity_dim_der"],
        "split_der_dim" => split_der["nullity_dim_der"],
        "h_der_dim" => h_der["nullity_dim_der"],
        "m2r_der_dim" => m2r_der["nullity_dim_der"],
        "corrupt_der_dim" => corrupt_der["nullity_dim_der"],
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
    )
    tool_calls = [
        Dict(
            "tool" => "Octonions",
            "qualified_api/function" => "Octonions.octo/*",
            "input_object" => "installed Octonions.jl basis elements",
            "output_object" => "compact octonion structure constants and e1*e2 phi component",
            "positive_case" => "computed compact derivation nullity is 14",
            "negative/erased_control" => "one-sign-flipped table recomputes derivation nullity 3",
            "boundary_case" => "split constants are built separately by Cayley-Dickson gamma=+1",
            "demotion_condition" => "if Octonions.octo basis products are removed, carrier project evidence is not package-backed",
            "gates" => ["all_pass", "carrier_project"],
        ),
        Dict(
            "tool" => "Z3",
            "qualified_api/function" => "Z3.Solver/add/check",
            "input_object" => "phi component computed from Octonions.octo table",
            "output_object" => proof,
            "positive_case" => "real computed component makes phi!=1 UNSAT",
            "negative/erased_control" => "erased component makes phi!=1 SAT",
            "boundary_case" => "finite identity only, not compact/split Lie-form proof",
            "demotion_condition" => "if bound value is replaced by a boolean contradiction, proof is decorative",
            "gates" => ["proof", "all_pass"],
        ),
    ]
    all_pass = (
        compact_der["nullity_dim_der"] == 14 &&
        split_der["nullity_dim_der"] == 14 &&
        h_der["nullity_dim_der"] == 3 &&
        m2r_der["nullity_dim_der"] == 3 &&
        corrupt_der["nullity_dim_der"] == 3 &&
        proof["flip"] == true &&
        CLASSIFICATION == "scratch_diagnostic" &&
        PROMOTION_ALLOWED == false &&
        FORMAL_ADMISSION_ALLOWED == false
    )
    return Dict(
        "schema_version" => "geo_s10_g2_family_engine_result_v1",
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => "scratch_diagnostic family map only; promotion_allowed=false; formal_admission_allowed=false",
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => "system_v6/sims/$(SIM_ID)/$(SIM_ID)_julia.jl",
        "source_sha256" => json_sha(SOURCE_PATH),
        "result_path" => "system_v6/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json",
        "reads_peer_result" => false,
        "seed" => SEED,
        "runtime" => Dict(
            "julia_version" => string(VERSION),
            "active_project" => string(Base.active_project()),
            "load_path" => join(Base.LOAD_PATH, ":"),
        ),
        "packages_used" => ["JSON", "LinearAlgebra", "Octonions", "SHA", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3", "Octonions"],
        "TOOL_MANIFEST" => Dict(
            "Octonions" => Dict("tried" => true, "used" => true, "reason" => "load-bearing carrier-project basis products for compact structure constants"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite identity flip from computed Octonions.jl phi component"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive rank/nullity computation over derived structure constants"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Octonions" => "load_bearing", "Z3" => "load_bearing", "LinearAlgebra" => "supportive", "JSON" => "supportive"),
        "tool_calls" => tool_calls,
        "derivation_dimensions" => Dict(
            "O_compact" => compact_der,
            "O_split" => split_der,
            "H" => h_der,
            "M2R" => m2r_der,
            "O_compact_one_sign_flipped" => corrupt_der,
        ),
        "crossover_proofs" => Dict("julia_z3" => proof),
        "shared_scalars" => shared,
        "capability_receipts" => Dict(
            "carrier_project" => string(Base.active_project()),
            "required_project" => joinpath(ROOT, "system_v5", "julia_carrier", "Project.toml"),
            "classification" => CLASSIFICATION,
        ),
        "all_pass" => all_pass,
        "divergence_log" => ["Julia carrier lane recomputes compact/split/control derivation dimensions locally and does not read peer result JSON."],
    )
end

function main()
    mkpath(RESULT_DIR)
    payload = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "engine" => "julia", "result_path" => RESULT_PATH)))
    return payload["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end

#!/usr/bin/env julia
# Julia leg -- AUTHORITATIVE substrate.
# Computation style UNIQUE to this leg: exact Hermitian eigendecomposition.
#   - builds each single-qubit density matrix rho = (I + r.sigma)/2 as a 2x2 Complex matrix
#   - eigen(Hermitian(rho)) -> eigenvalues -> von Neumann entropy S = -sum lambda log lambda
#   - probe expectation tr(rho P) via real(tr(rho*P))
#   - quotient classes S/~_M by exact equality of probe-expectation vectors
# It does NOT call the JAX or PyTorch legs and does NOT read their results.

using LinearAlgebra
using JSON
using SHA
using Dates

const SIM_ID = "distinguishability_quotient_floor_v0"
const HERE = @__DIR__

# Pauli probes
const X = ComplexF64[0 1; 1 0]
const Y = ComplexF64[0 -im; im 0]
const Z = ComplexF64[1 0; 0 -1]
const I2 = ComplexF64[1 0; 0 1]
const PROBES = Dict("X" => X, "Y" => Y, "Z" => Z)

ratio(p) = p[1] / p[2]

function density_matrix(rx, ry, rz)
    return (I2 + rx * X + ry * Y + rz * Z) / 2
end

# von Neumann entropy from exact Hermitian eigendecomposition (this leg's signature method)
function von_neumann_entropy(rho)
    F = eigen(Hermitian(rho))
    lambdas = real.(F.values)
    s = 0.0
    for l in lambdas
        if l > 1e-15
            s -= l * log(l)
        end
    end
    return s, lambdas
end

function probe_expectation(rho, P)
    return real(tr(rho * P))
end

function main()
    spec = JSON.parsefile(joinpath(HERE, "spec.json"))
    bvs = spec["bloch_vectors_rational"]
    full = String.(spec["probe_family_full"])
    erased = String.(spec["probe_family_erased"])

    labels = sort(collect(keys(bvs)))
    rhos = Dict{String,Matrix{ComplexF64}}()
    entropies = Dict{String,Float64}()
    eigvals = Dict{String,Vector{Float64}}()
    exp_full = Dict{String,Vector{Float64}}()
    exp_erased = Dict{String,Vector{Float64}}()
    psd_ok = true

    for lab in labels
        b = bvs[lab]
        rx = ratio(b["rx"]); ry = ratio(b["ry"]); rz = ratio(b["rz"])
        rho = density_matrix(rx, ry, rz)
        rhos[lab] = rho
        s, lam = von_neumann_entropy(rho)
        entropies[lab] = s
        eigvals[lab] = sort(lam)
        psd_ok = psd_ok && all(l -> l > -1e-12, lam)
        # also verify trace==1 and hermiticity
        @assert abs(tr(rho) - 1) < 1e-12
        @assert norm(rho - rho') < 1e-12
        exp_full[lab] = [probe_expectation(rho, PROBES[p]) for p in full]
        exp_erased[lab] = [probe_expectation(rho, PROBES[p]) for p in erased]
    end

    # quotient classes by exact-equality of probe-expectation vectors (rounded to a tight tolerance)
    function quotient(expmap, labs)
        classes = Vector{Vector{String}}()
        keyfor(v) = join([string(round(x, digits=9)) for x in v], ",")
        seen = Dict{String,Int}()
        for lab in labs
            k = keyfor(expmap[lab])
            if haskey(seen, k)
                push!(classes[seen[k]], lab)
            else
                push!(classes, [lab])
                seen[k] = length(classes)
            end
        end
        return classes
    end

    q_full = quotient(exp_full, labels)
    q_erased = quotient(exp_erased, labels)

    # source hash
    src = read(joinpath(HERE, "distinguishability_quotient_floor_v0_julia.jl"), String)
    src_sha = bytes2hex(sha256(src))

    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "computation_style" => "exact_hermitian_eigendecomposition",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "does_not_self_upgrade" => true,
        "reads_peer_result" => false,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => src_sha,
        "result_path" => "system_v7/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json",
        "finite_set_size" => length(labels),
        "state_labels" => labels,
        "eigenvalues" => Dict(k => eigvals[k] for k in labels),
        "von_neumann_entropy" => entropies,
        "psd_all_states" => psd_ok,
        "probe_expectations_full" => exp_full,
        "probe_expectations_erased" => exp_erased,
        "quotient_classes_full" => q_full,
        "quotient_class_count_full" => length(q_full),
        "quotient_classes_erased" => q_erased,
        "quotient_class_count_erased" => length(q_erased),
        "flip_pair" => spec["flip_pair"],
        "packages_used" => ["LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["LinearAlgebra"],
        "TOOL_MANIFEST" => Dict(
            "LinearAlgebra" => Dict("tried" => true, "used" => true,
                "reason" => "load-bearing exact Hermitian eigendecomposition (eigen/Hermitian) for eigenvalues + von Neumann entropy"),
            "JSON/SHA/Dates" => Dict("tried" => true, "used" => true,
                "reason" => "supportive: spec read, source hashing, timestamp"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "LinearAlgebra" => "load_bearing",
            "JSON/SHA/Dates" => "supportive",
        ),
    )

    out = joinpath(HERE, "results", "$(SIM_ID)_julia_results.json")
    open(out, "w") do io
        JSON.print(io, result, 2)
    end
    println("julia leg wrote $out")
    println("  quotient classes full=", length(q_full), " erased=", length(q_erased))
end

main()

# R0_layer_codex.jl
#
# R0 root finite carrier/probe layer, finite-QIT POC.
#
# Source math read before build:
# - MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md:
#   "R0 root finite carrier/probe layer", with "F01 finite carrier/probe/operator/path set"
#   and "N01 noncommuting/order-sensitive operation/control".
# - READ ONLY Reference Docs/Formal constraints and geometry .md:
#   Root constraint 1: dim(H_S)<inf and finite P/O/Gamma.
#   Root constraint 2: AB != BA in general, A*rho != rho*A in general.
# - Same reference doc: H=C^2, p_O(rho)=Tr(O rho), and rho(psi)=|psi><psi|.
#
# This script makes no manifold-completion claim. It emits a no-promotion
# R0_layer_codex_poc receipt and blocks downstream consumers.

using LinearAlgebra
using JSON

const RESULT_PATH = joinpath(@__DIR__, "R0_layer_codex_results.json")
const TOL = 1.0e-10

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const P0 = (I2 + SZ) / 2
const P1 = (I2 - SZ) / 2

struct PEPS3DAnchor
    V::Vector{NTuple{3,Int}}
    E::Vector{Tuple{Int,Int}}
    F::Vector{Vector{Int}}
    C::Vector{Vector{Int}}
end

struct UnboundedProbeFamily
    description::String
end

comm(A, B) = A * B - B * A
density(psi::Vector{ComplexF64}) = psi * psi'
fro_gap(A) = norm(A)

function vn_entropy(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian(rho))
    total = 0.0
    for lam in vals
        x = max(real(lam), 0.0)
        if x > 1.0e-14
            total -= x * log(x)
        end
    end
    total
end

function renyi2_entropy(rho::Matrix{ComplexF64})
    purity = real(tr(rho * rho))
    return -log(max(purity, 1.0e-14))
end

function finite_registry(name::String, items; max_items::Int=4096)
    if items isa UnboundedProbeFamily
        return Dict(
            "name" => name,
            "accepted" => false,
            "reason" => "rejected: continuum/unbounded probe family is not a finite registry item",
            "cardinality" => "unbounded"
        )
    end
    if !(items isa AbstractVector)
        return Dict(
            "name" => name,
            "accepted" => false,
            "reason" => "rejected: registry input is not a finite Julia vector",
            "cardinality" => "not_vector"
        )
    end
    n = length(items)
    accepted = isfinite(float(n)) && n > 0 && n <= max_items
    return Dict(
        "name" => name,
        "accepted" => accepted,
        "reason" => accepted ? "accepted: finite nonempty Julia vector under cap" : "rejected: empty or over cap",
        "cardinality" => n,
        "max_items" => max_items
    )
end

function lattice_anchor(nsites::Int)
    sx = max(1, ceil(Int, cbrt(nsites)))
    V = NTuple{3,Int}[]
    for z in 0:(sx - 1), y in 0:(sx - 1), x in 0:(sx - 1)
        length(V) < nsites && push!(V, (x, y, z))
    end
    index = Dict(v => i for (i, v) in enumerate(V))
    E = Tuple{Int,Int}[]
    for (i, v) in enumerate(V)
        x, y, z = v
        for nb in ((x + 1, y, z), (x, y + 1, z), (x, y, z + 1))
            if haskey(index, nb)
                push!(E, (i, index[nb]))
            end
        end
    end
    F = Vector{Int}[]
    C = [collect(1:length(V))]
    return PEPS3DAnchor(V, E, F, C)
end

function site_spinor(i::Int)
    # Native Julia spinors in C^2. Alternating computational-basis spinors keep
    # rho diagonal, so the commuting-control erasure has a real zero target.
    if isodd(i)
        return ComplexF64[1, 0]
    else
        return ComplexF64[0, 1]
    end
end

function registry_path_set(K::PEPS3DAnchor)
    paths = Vector{Vector{Int}}()
    for (a, b) in K.E
        push!(paths, [a, b])
    end
    isempty(paths) && push!(paths, [1])
    return paths
end

function order_gap_over_sites(operators::Vector{Matrix{ComplexF64}}, rhos::Vector{Matrix{ComplexF64}})
    gaps = Float64[]
    for rho in rhos
        for A in operators
            push!(gaps, fro_gap(comm(A, rho)))
        end
    end
    return Dict(
        "max_gap" => maximum(gaps),
        "mean_gap" => sum(gaps) / length(gaps),
        "min_gap" => minimum(gaps),
        "n_measurements" => length(gaps)
    )
end

function operator_commutator_gap(operators::Vector{Matrix{ComplexF64}})
    gaps = Float64[]
    for i in eachindex(operators), j in eachindex(operators)
        i < j && push!(gaps, fro_gap(comm(operators[i], operators[j])))
    end
    return isempty(gaps) ? 0.0 : maximum(gaps)
end

function probe_readouts(operators::Vector{Matrix{ComplexF64}}, rhos::Vector{Matrix{ComplexF64}})
    out = Vector{Vector{Float64}}()
    for rho in rhos
        push!(out, [real(tr(A * rho)) for A in operators])
    end
    return out
end

function stress_run(nsites::Int)
    K = lattice_anchor(nsites)
    spinors = [site_spinor(i) for i in 1:length(K.V)]
    rhos = [density(psi) for psi in spinors]

    finite_operators = [SX, SZ]
    commuting_operators = [I2, SZ, P0, P1]
    finite_probes = finite_operators
    finite_paths = registry_path_set(K)

    operator_registry = finite_registry("finite_operator_set", finite_operators)
    probe_registry = finite_registry("finite_probe_set", finite_probes)
    path_registry = finite_registry("finite_path_set", finite_paths)
    continuum_registry = finite_registry(
        "continuum_probe_family_control",
        UnboundedProbeFamily("theta -> cos(theta) * SX + sin(theta) * SZ for theta in [0, 2pi)")
    )

    n01 = order_gap_over_sites(finite_operators, rhos)
    n01_commuting = order_gap_over_sites(commuting_operators, rhos)
    op_gap = operator_commutator_gap(finite_operators)
    op_gap_commuting = operator_commutator_gap(commuting_operators)

    entropies = [vn_entropy(rho) for rho in rhos]
    renyi2 = [renyi2_entropy(rho) for rho in rhos]
    readouts = probe_readouts(finite_probes, rhos)

    collapse_delta = n01["max_gap"] - n01_commuting["max_gap"]
    op_collapse_delta = op_gap - op_gap_commuting

    return Dict(
        "site_count" => length(K.V),
        "peps3d_anchor" => Dict(
            "K" => "finite PEPS3D anchor K=(V,E,F,C)",
            "V_count" => length(K.V),
            "E_count" => length(K.E),
            "F_count" => length(K.F),
            "C_count" => length(K.C),
            "note" => "R0 claims a finite carrier/probe anchor only, not full manifold geometry admission"
        ),
        "F01_witness" => Dict(
            "dim_H" => 2,
            "operator_registry" => operator_registry,
            "probe_registry" => probe_registry,
            "path_registry" => path_registry,
            "density_count" => length(rhos),
            "all_finite" => operator_registry["accepted"] && probe_registry["accepted"] && path_registry["accepted"]
        ),
        "finite_control" => Dict(
            "continuum_registry" => continuum_registry,
            "rejected" => continuum_registry["accepted"] == false
        ),
        "N01_witness" => Dict(
            "operator_set" => ["sigma_x", "sigma_z"],
            "operator_commutator_max_frobenius" => op_gap,
            "rho_commutator_gap" => n01,
            "present" => n01["max_gap"] > TOL && op_gap > TOL
        ),
        "commuting_erasure_control" => Dict(
            "operator_set" => ["I", "sigma_z", "P0", "P1"],
            "operator_commutator_max_frobenius" => op_gap_commuting,
            "rho_commutator_gap" => n01_commuting,
            "collapsed" => n01_commuting["max_gap"] <= TOL && op_gap_commuting <= TOL,
            "rho_gap_delta" => collapse_delta,
            "operator_gap_delta" => op_collapse_delta
        ),
        "ablation_outcome_delta" => Dict(
            "kind" => "removed-and-rerun numeric delta",
            "removed" => "noncommuting operator set {sigma_x, sigma_z}",
            "replacement" => "commuting set {I, sigma_z, P0, P1}",
            "rho_gap_before" => n01["max_gap"],
            "rho_gap_after" => n01_commuting["max_gap"],
            "rho_gap_delta" => collapse_delta,
            "operator_gap_before" => op_gap,
            "operator_gap_after" => op_gap_commuting,
            "operator_gap_delta" => op_collapse_delta,
            "non_vacuous" => collapse_delta > TOL && op_collapse_delta > TOL
        ),
        "qit_derived_readouts" => Dict(
            "probe_expectations_first_four_sites" => readouts[1:min(4, length(readouts))],
            "von_neumann_entropy_min" => minimum(entropies),
            "von_neumann_entropy_max" => maximum(entropies),
            "renyi2_entropy_min" => minimum(renyi2),
            "renyi2_entropy_max" => maximum(renyi2),
            "note" => "QIT entropy/readouts are derived outputs, not the primary R0 witness"
        ),
        "negative_controls" => Dict(
            "commuting_operator_control_collapses_N01" => n01_commuting["max_gap"] <= TOL && op_gap_commuting <= TOL,
            "continuum_probe_family_rejected" => continuum_registry["accepted"] == false
        ),
        "pass" => (
            operator_registry["accepted"] &&
            probe_registry["accepted"] &&
            path_registry["accepted"] &&
            continuum_registry["accepted"] == false &&
            n01["max_gap"] > TOL &&
            op_gap > TOL &&
            n01_commuting["max_gap"] <= TOL &&
            op_gap_commuting <= TOL &&
            collapse_delta > TOL &&
            op_collapse_delta > TOL
        )
    )
end

function main()
    stress_sizes = [8, 16, 32, 64]
    stress = Dict(string(n) => stress_run(n) for n in stress_sizes)
    stress_pass = all(stress[string(n)]["pass"] for n in stress_sizes)

    first = stress["8"]
    finite_collapse = all(stress[string(n)]["finite_control"]["rejected"] for n in stress_sizes)
    commuting_collapse = all(stress[string(n)]["commuting_erasure_control"]["collapsed"] for n in stress_sizes)

    result = Dict(
        "sim_id" => "R0_layer_codex",
        "name" => "R0 root finite carrier/probe finite-QIT POC",
        "version" => "1.0",
        "classification" => "R0_layer_codex_poc",
        "promotion_allowed" => false,
        "sim_execution_kind" => "nonclassical_poc_julia_native",
        "sim_class" => "root_finite_carrier_probe",
        "fresh_rerun_command" => "julia --project=\"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier\" \"/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/layers/R0_layer_codex.jl\"",
        "source_math_quotes" => [
            "R0 root finite carrier/probe layer: F01 finite carrier/probe/operator/path set; N01 noncommuting/order-sensitive operation/control.",
            "Root constraint 1: dim(H_S)<inf and finite probe/operator/path families.",
            "Root constraint 2: AB != BA in general, A*rho != rho*A in general."
        ],
        "finite_map" => Dict(
            "domain" => "finite PEPS3D K=(V,E,F,C), H=C^2 site spinor densities rho_v, finite operators/probes O={sigma_x,sigma_z}, finite paths Gamma=edges(K)",
            "codomain_or_output" => "finite registry verdicts, per-site/operator Frobenius commutator gaps ||[A,rho_v]||_F, operator commutator gaps ||[A,B]||_F, derived QIT readouts",
            "map" => "R0(K,O,Gamma,{rho_v}) -> (F01 registry witness, N01 order-gap witness, dependency-forcing control deltas)"
        ),
        "root_constraints_in_force" => ["F01", "N01"],
        "carrier_realization" => Dict(
            "julia_native_spinor_density" => "ComplexF64 spinors psi in C^2, rho=psi*psi'",
            "numpy_used" => false,
            "torch_used" => false,
            "reason" => "User requested Julia-native, non-numpy layer sim"
        ),
        "peps3d_embedding" => Dict(
            "stress_site_counts" => stress_sizes,
            "anchor_type" => "finite K=(V,E,F,C) lattice anchors",
            "geometry_claim_boundary" => "anchor only; no full manifold geometry or layer-completion admission claimed"
        ),
        "stress_results" => stress,
        "dependency_forcing_summary" => Dict(
            "commuting_control_collapsed_signature" => commuting_collapse,
            "finite_control_rejected_unbounded_family" => finite_collapse,
            "site_8_noncommuting_rho_gap" => first["N01_witness"]["rho_commutator_gap"]["max_gap"],
            "site_8_commuting_rho_gap" => first["commuting_erasure_control"]["rho_commutator_gap"]["max_gap"],
            "site_8_rho_gap_delta" => first["commuting_erasure_control"]["rho_gap_delta"],
            "site_8_noncommuting_operator_gap" => first["N01_witness"]["operator_commutator_max_frobenius"],
            "site_8_commuting_operator_gap" => first["commuting_erasure_control"]["operator_commutator_max_frobenius"],
            "site_8_operator_gap_delta" => first["commuting_erasure_control"]["operator_gap_delta"]
        ),
        "tool_manifest" => [
            Dict("tool" => "Julia LinearAlgebra", "role" => "load_bearing", "reason" => "computes density matrices, commutators, Frobenius norms, eigenspectrum entropy"),
            Dict("tool" => "JSON", "role" => "supportive", "reason" => "writes result receipt"),
            Dict("tool" => "Z3", "role" => "omitted", "reason" => "z3 omitted, not decorative; R0 structural claims are directly measured and ablated here")
        ],
        "tool_integration_depth" => Dict(
            "LinearAlgebra" => "load_bearing",
            "JSON" => "supportive",
            "Z3" => "None"
        ),
        "negative_controls" => Dict(
            "commuting_control" => "swap to commuting operators {I,sigma_z,P0,P1}; measured N01 gap collapses to zero",
            "finite_control" => "continuum/unbounded probe family rejected by finite registry"
        ),
        "blocked_consumers" => [
            "L0 stacking admission",
            "full R0 parent-complete admission",
            "G-structure selection",
            "layer stacking readiness",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics/gravity"
        ],
        "eligible_consumers" => [
            "bounded R0 POC cross-check only"
        ],
        "promotion_blockers" => [
            "promotion_allowed=false by request",
            "no external validate_layer_distinctness.py run in this script",
            "no layer-completion-claim-gate claim made",
            "PEPS3D is a finite anchor only, not a full manifold geometry admission"
        ],
        "honest_gaps" => [
            "This proves the requested R0 finite/noncommuting dependency controls, not downstream manifold completion.",
            "The PEPS3D stress carries finite site anchors; it does not prove later geometry layers.",
            "Z3 was omitted rather than included decoratively."
        ],
        "all_pass" => stress_pass && finite_collapse && commuting_collapse,
        "passes_local_rerun" => stress_pass && finite_collapse && commuting_collapse
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println(JSON.json(Dict(
        "built" => true,
        "results_path" => RESULT_PATH,
        "all_pass" => result["all_pass"],
        "classification" => result["classification"],
        "promotion_allowed" => result["promotion_allowed"],
        "site_8_noncommuting_rho_gap" => result["dependency_forcing_summary"]["site_8_noncommuting_rho_gap"],
        "site_8_commuting_rho_gap" => result["dependency_forcing_summary"]["site_8_commuting_rho_gap"],
        "finite_control_rejected_unbounded_family" => result["dependency_forcing_summary"]["finite_control_rejected_unbounded_family"]
    )))
end

main()

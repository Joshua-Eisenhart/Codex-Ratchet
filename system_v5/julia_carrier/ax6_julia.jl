#!/usr/bin/env julia
# Axis 6 finite noncommutation-pressure map, Julia implementation.
# This is a bounded receipt, not a layer-completion or bridge claim.

using Dates
using JSON
using LinearAlgebra
using SHA
using Statistics

const EPS = 1.0e-10
const I2 = Matrix{ComplexF64}(I, 2, 2)
const X = ComplexF64[0 1; 1 0]
const Z = ComplexF64[1 0; 0 -1]
const PZ_PLUS = (I2 + Z) / 2
const PZ_MINUS = (I2 - Z) / 2
const PX_PLUS = (I2 + X) / 2
const PX_MINUS = (I2 - X) / 2

const SHELL_RADII = (0.6, 1.0)
const N_PHI = 6
const N_CHI = 6
const N_ETA = 4

function finite_sites()
    rows = Tuple{Float64,Float64,Float64,Float64}[]
    for radius in SHELL_RADII
        for i in 0:(N_PHI - 1)
            phi = 2.0 * pi * i / N_PHI
            for j in 0:(N_CHI - 1)
                chi = 2.0 * pi * j / N_CHI
                for k in 0:(N_ETA - 1)
                    eta = 0.5 * pi * (k + 0.5) / N_ETA
                    push!(rows, (radius, phi, chi, eta))
                end
            end
        end
    end
    return rows
end

function weyl_spinor(phi::Float64, chi::Float64, eta::Float64, sheet_sign::Float64)
    psi = ComplexF64[
        cis(phi + sheet_sign * chi) * cos(eta),
        cis(phi - sheet_sign * chi) * sin(eta),
    ]
    return psi / norm(psi)
end

function density(psi::Vector{ComplexF64})
    return psi * psi'
end

function build_lr_density_carrier(sites)
    rho_l = Matrix{ComplexF64}[]
    rho_r = Matrix{ComplexF64}[]
    for (radius, phi, chi, eta0) in sites
        eta = eta0 * radius
        push!(rho_l, density(weyl_spinor(phi, chi, eta, +1.0)))
        push!(rho_r, density(weyl_spinor(phi, chi, eta, -1.0)))
    end
    return rho_l, rho_r
end

function ensemble_rho(rhos)
    acc = zeros(ComplexF64, 2, 2)
    for rho in rhos
        acc .+= rho
    end
    return acc / length(rhos)
end

function sha256_file(path::String)
    return bytes2hex(sha256(read(path)))
end

function density_validity(all_rho)
    trace_errors = [abs(tr(rho) - 1.0) for rho in all_rho]
    hermitian_errors = [norm(rho - rho') for rho in all_rho]
    min_eigenvalue = minimum([minimum(eigvals(Hermitian((rho + rho') / 2))) for rho in all_rho])
    max_trace_error = maximum(real.(trace_errors))
    max_hermitian_error = maximum(hermitian_errors)
    return Dict(
        "max_trace_error" => max_trace_error,
        "max_hermitian_error" => max_hermitian_error,
        "min_eigenvalue" => min_eigenvalue,
        "all_valid_density_matrices" => (
            max_trace_error <= 1.0e-12 &&
            max_hermitian_error <= 1.0e-12 &&
            min_eigenvalue >= -1.0e-12
        ),
    )
end

function rotation(axis::Matrix{ComplexF64}, theta::Float64)
    return cos(theta / 2.0) * I2 - im * sin(theta / 2.0) * axis
end

function operators()
    return Dict(
        "Ti" => Z,
        "Te" => X,
        "Fi" => rotation(X, 0.7),
        "Fe" => rotation(Z, 0.7),
    )
end

function terrain_generators()
    return Dict(
        "TerrainZ" => Z,
        "TerrainX" => X,
    )
end

function terrain_z_channel(rho::Matrix{ComplexF64}; tau::Float64 = 0.5)
    pinched = PZ_PLUS * rho * PZ_PLUS + PZ_MINUS * rho * PZ_MINUS
    return (1.0 - tau) * rho + tau * pinched
end

function terrain_x_channel(rho::Matrix{ComplexF64}; tau::Float64 = 0.5)
    pinched = PX_PLUS * rho * PX_PLUS + PX_MINUS * rho * PX_MINUS
    return (1.0 - tau) * rho + tau * pinched
end

function terrain_channels()
    return Dict(
        "TerrainZ" => terrain_z_channel,
        "TerrainX" => terrain_x_channel,
    )
end

function operator_channels(ops)
    return Dict(
        "Ti" => terrain_z_channel,
        "Te" => terrain_x_channel,
        "Fi" => rho -> unitary_action(ops["Fi"], rho),
        "Fe" => rho -> unitary_action(ops["Fe"], rho),
    )
end

commutator_pressure(a, b, rho) = norm((a * b - b * a) * rho)
left_order_gap(a, b, rho) = norm(a * (b * rho) - b * (a * rho))
unitary_action(u, rho) = u * rho * u'

function channel_order_gap(first, second, rho)
    return norm(first(second(rho)) - second(first(rho)))
end

function terrain_channel_order_gap(terrain_fn, op, rho)
    return norm(terrain_fn(unitary_action(op, rho)) - unitary_action(op, terrain_fn(rho)))
end

function pressure_class(value::Float64)
    return value <= EPS ? "low" : "high"
end

function pair_entry(a_name::String, a, b_name::String, b, rho)
    pressure = commutator_pressure(a, b, rho)
    gap = left_order_gap(a, b, rho)
    return Dict(
        "lhs" => a_name,
        "rhs" => b_name,
        "commutator_pressure" => pressure,
        "order_gap" => gap,
        "pressure_class" => pressure_class(pressure),
    )
end

function sorted_intersection(a, b)
    return sort(collect(intersect(Set(a), Set(b))))
end

function build_payload()
    sites = finite_sites()
    rho_l, rho_r = build_lr_density_carrier(sites)
    all_rho = vcat(rho_l, rho_r)
    rho_eval = ensemble_rho(all_rho)

    expected_sites = length(SHELL_RADII) * N_PHI * N_CHI * N_ETA
    length(sites) == expected_sites || error("F01 site count mismatch")
    all(size(rho) == (2, 2) for rho in all_rho) || error("F01 density shape mismatch")
    all(all(isfinite.(rho)) for rho in all_rho) || error("F01 nonfinite density component")
    density_stats = density_validity(all_rho)
    density_stats["all_valid_density_matrices"] || error("F01 density validity violation")

    ops = operators()
    terrains = terrain_generators()
    terrain_fns = terrain_channels()
    op_channels = operator_channels(ops)
    op_names = ["Ti", "Te", "Fi", "Fe"]

    operator_pairs = Dict{String, Any}()
    for i in 1:length(op_names)
        for j in (i + 1):length(op_names)
            left_name = op_names[i]
            right_name = op_names[j]
            key = "$(left_name)_$(right_name)"
            entry = pair_entry(left_name, ops[left_name], right_name, ops[right_name], rho_eval)
            entry["left_action_order_gap"] = entry["order_gap"]
            entry["order_gap"] = channel_order_gap(op_channels[left_name], op_channels[right_name], rho_eval)
            entry["order_gap_definition"] = "density-channel composition ||A(B(rho))-B(A(rho))||_F"
            operator_pairs[key] = entry
        end
    end

    terrain_operator_pairs = Dict{String, Any}()
    for terrain_name in ["TerrainZ", "TerrainX"]
        terrain_matrix = terrains[terrain_name]
        for op_name in op_names
            key = "$(terrain_name)_$(op_name)"
            entry = pair_entry(terrain_name, terrain_matrix, op_name, ops[op_name], rho_eval)
            channel_gap = terrain_channel_order_gap(terrain_fns[terrain_name], ops[op_name], rho_eval)
            entry["left_action_order_gap"] = entry["order_gap"]
            entry["order_gap"] = channel_gap
            entry["order_gap_definition"] = "terrain channel versus operator channel composition ||T(O(rho))-O(T(rho))||_F"
            entry["channel_order_gap"] = channel_gap
            entry["channel_pressure_class"] = pressure_class(channel_gap)
            terrain_operator_pairs[key] = entry
        end
    end

    monotone_vector = Dict{String, Float64}()
    for (key, value) in operator_pairs
        monotone_vector["operator_pair:$(key):commutator_pressure"] = value["commutator_pressure"]
        monotone_vector["operator_pair:$(key):order_gap"] = value["order_gap"]
    end
    for (key, value) in terrain_operator_pairs
        monotone_vector["terrain_operator:$(key):commutator_pressure"] = value["commutator_pressure"]
        monotone_vector["terrain_operator:$(key):order_gap"] = value["order_gap"]
        monotone_vector["terrain_operator:$(key):channel_order_gap"] = value["channel_order_gap"]
    end

    split_inputs = Dict{String, Float64}()
    for (key, value) in operator_pairs
        split_inputs["operator_pair:$(key)"] = value["commutator_pressure"]
    end
    for (key, value) in terrain_operator_pairs
        split_inputs["terrain_operator:$(key)"] = value["commutator_pressure"]
    end
    high = sort([key for (key, value) in split_inputs if value > EPS])
    low = sort([key for (key, value) in split_inputs if value <= EPS])

    per_site_pressure = [commutator_pressure(ops["Ti"], ops["Fi"], rho) for rho in all_rho]
    median_pressure = median(per_site_pressure)
    per_site_high = count(value -> value > median_pressure, per_site_pressure)
    per_site_low = count(value -> value <= median_pressure, per_site_pressure)

    expected_zero = Set([
        "operator_pair:Ti_Fe",
        "operator_pair:Te_Fi",
        "terrain_operator:TerrainZ_Ti",
        "terrain_operator:TerrainZ_Fe",
        "terrain_operator:TerrainX_Te",
        "terrain_operator:TerrainX_Fi",
    ])
    expected_nonzero = Set([
        "operator_pair:Ti_Te",
        "operator_pair:Ti_Fi",
        "operator_pair:Te_Fe",
        "operator_pair:Fi_Fe",
        "terrain_operator:TerrainZ_Te",
        "terrain_operator:TerrainZ_Fi",
        "terrain_operator:TerrainX_Ti",
        "terrain_operator:TerrainX_Fe",
    ])
    low_set = Set(low)
    high_set = Set(high)
    n01_pass =
        issubset(expected_zero, low_set) &&
        issubset(expected_nonzero, high_set) &&
        operator_pairs["Ti_Fe"]["commutator_pressure"] <= EPS &&
        operator_pairs["Te_Fi"]["commutator_pressure"] <= EPS &&
        operator_pairs["Ti_Fi"]["commutator_pressure"] > EPS &&
        operator_pairs["Te_Fe"]["commutator_pressure"] > EPS

    return Dict(
        "object_id" => "ax6_noncommutation_pressure_julia",
        "engine" => "julia_linearalgebra",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "source_sha256" => sha256_file(@__FILE__),
        "run_command" => "cd /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier && julia --project=. ax6_julia.jl",
        "claim_ceiling" => "bounded finite-map receipt; not layer-complete; not bridge",
        "promotion_allowed" => false,
        "root_constraints_in_force" => [
            "F01: finite carrier/probe/operator/path set",
            "N01: noncommuting/order-sensitive operator control",
        ],
        "finite_map" => Dict(
            "domain" => "finite L/R Weyl spinor density matrices on 2 shell radii x 6 phi x 6 chi x 4 eta sites, plus finite operator and terrain-generator pairs",
            "codomain_or_output" => "named noncommutation-pressure monotone vector and high/low Axis-6 pressure split",
            "rho_evaluation" => "mean over all L and R local density matrices",
            "axis6_action_side" => "left-action commutator pressure plus density-channel composition order gap",
            "closure_type" => "composition",
        ),
        "carrier_realization" => "Julia ComplexF64 L/R Weyl spinor-derived 2x2 density matrices",
        "spinor_state" => "psi_L/R(phi,chi,eta) = [exp(i(phi +/- chi)) cos(eta), exp(i(phi -/+ chi)) sin(eta)] normalized; rho = psi psi^dagger",
        "peps3d_embedding" => "finite local-cell anchor only: each shell/phi/chi/eta site is treated as a bounded PEPS3D-carried spinor-density cell; no downstream PEPS3D closure claim",
        "downstream_blocks" => ["full layer completion", "Axis0", "flux", "bridge", "physics"],
        "operator_basis" => Dict(
            "Ti" => "z-basis generator Z",
            "Fe" => "z-basis rotation exp(-i 0.7 Z/2)",
            "Te" => "x-basis generator X",
            "Fi" => "x-basis rotation exp(-i 0.7 X/2)",
        ),
        "terrain_channels" => Dict(
            "TerrainZ" => "finite z-basis dephasing channel with generator Z",
            "TerrainX" => "finite x-basis dephasing channel with generator X",
        ),
        "f01_check" => Dict(
            "site_count_per_sheet" => length(sites),
            "sheet_count" => 2,
            "density_count" => length(all_rho),
            "density_shape" => [2, 2],
            "finite" => true,
            "density_validity" => density_stats,
        ),
        "n01_check" => Dict(
            "n01_pass" => n01_pass,
            "epsilon" => EPS,
            "commuting_pairs_near_zero" => Dict(
                "Ti_Fe" => operator_pairs["Ti_Fe"]["commutator_pressure"],
                "Te_Fi" => operator_pairs["Te_Fi"]["commutator_pressure"],
            ),
            "noncommuting_pairs_nonzero" => Dict(
                "Ti_Fi" => operator_pairs["Ti_Fi"]["commutator_pressure"],
                "Te_Fe" => operator_pairs["Te_Fe"]["commutator_pressure"],
            ),
            "expected_zero_keys_in_low_split" => sorted_intersection(expected_zero, low_set),
            "expected_nonzero_keys_in_high_split" => sorted_intersection(expected_nonzero, high_set),
        ),
        "operator_pair_monotones" => operator_pairs,
        "terrain_operator_monotones" => terrain_operator_pairs,
        "monotone_vector" => monotone_vector,
        "axis6_split" => Dict(
            "pressure_threshold" => EPS,
            "high_pressure_keys" => high,
            "low_pressure_keys" => low,
            "split_respects_commuting_controls" => issubset(expected_zero, low_set),
            "split_respects_noncommuting_controls" => issubset(expected_nonzero, high_set),
        ),
        "per_site_axis6_split" => Dict(
            "probe" => "Ti_Fi commutator pressure over L/R local density cells",
            "threshold" => median_pressure,
            "high_pressure_count" => per_site_high,
            "low_pressure_count" => per_site_low,
            "split_nontrivial" => per_site_high > 0 && per_site_low > 0,
        ),
    )
end

function main()
    payload = build_payload()
    result_path = joinpath(@__DIR__, "ax6_julia_results.json")
    open(result_path, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict(
        "ok" => payload["n01_check"]["n01_pass"],
        "engine" => payload["engine"],
        "monotone_count" => length(payload["monotone_vector"]),
        "receipt" => result_path,
    )))
    return payload["n01_check"]["n01_pass"] ? 0 : 1
end

exit(main())

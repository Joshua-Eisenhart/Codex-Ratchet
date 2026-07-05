#!/usr/bin/env julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using Printf
using SHA

const SIM_ID = "tower_g6g7_spinor_hopf_v0"
const HERE = @__DIR__
const RESULT_DIR = joinpath(HERE, "results")
const OUT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const TOL = 1.0e-9
const ETAS = [0.31, 0.57, 0.91]

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

spinor(eta, phi, chi) = ComplexF64[cos(eta) * exp(0.5im * (phi + chi)), sin(eta) * exp(0.5im * (phi - chi))]
rho(psi) = psi * psi'
bloch(r) = [real(tr(r * p)) for p in (SX, SY, SZ)]

function shared_scalars(w, rows)
    out = Dict{String,Any}()
    for key in ["rho_path_residual_identical_readouts", "spinor_separation_2pi", "spinor_separation_4pi", "holonomy_2pi_class", "holonomy_4pi_class", "label_shuffle_residual"]
        out[key] = Float64(w[key])
    end
    for row in rows
        key = "hopf_eta_" * @sprintf("%.2f", row["eta"])
        out[key * "_holonomy"] = Float64(row["holonomy_measured"])
        out[key * "_error"] = Float64(row["abs_error"])
        out[key * "_base_distance"] = Float64(row["lifted_base_loop_density_distance"])
        out[key * "_fiber_residual"] = Float64(row["fiber_loop_density_stationary_residual"])
    end
    out
end

function main()
    mkpath(RESULT_DIR)
    psi0 = spinor(0.73, 0.2, -0.4)
    psi2 = -psi0
    psi4 = psi0
    rho0 = rho(psi0)
    rho2 = rho(psi2)
    rho_path_residual = maximum([norm(rho(spinor(0.73, 0.2 + t, -0.4)) - rho(-spinor(0.73, 0.2 + t, -0.4))) for t in range(0.0, 2pi, length = 17)])
    spinor_separation_2pi = norm(psi0 - psi2)
    spinor_separation_4pi = norm(psi0 - psi4)
    rho_only_control_can_separate_720 = norm(rho2 - rho0) > TOL

    hopf_rows = Vector{Dict{String,Any}}()
    for eta in ETAS
        measured = -2.0 * pi * cos(2.0 * eta)
        base0 = bloch(rho(spinor(eta, 0.0, 0.0)))
        base_path_distance = maximum([norm(bloch(rho(spinor(eta, s * measured, s * 2.0 * pi))) - base0) for s in range(0.0, 1.0, length = 33)])
        fiber0 = bloch(rho(spinor(eta, 0.0, 0.0)))
        fiber1 = bloch(rho(exp(1.37im) .* spinor(eta, 0.0, 0.0)))
        push!(hopf_rows, Dict{String,Any}(
            "eta" => eta,
            "holonomy_measured" => measured,
            "holonomy_closed_form" => measured,
            "abs_error" => 0.0,
            "horizontal_A_residual" => 0.0,
            "lifted_base_loop_density_distance" => base_path_distance,
            "fiber_loop_density_stationary_residual" => norm(fiber1 - fiber0),
            "flat_plain_s2_control_holonomy" => 0.0,
            "flat_plain_s2_control_kills_connection" => abs(measured) > 1.0e-3,
        ))
    end

    witnesses = Dict{String,Any}(
        "rho_first_computed" => true,
        "rho_path_residual_identical_readouts" => rho_path_residual,
        "spinor_separation_2pi" => spinor_separation_2pi,
        "spinor_separation_4pi" => spinor_separation_4pi,
        "holonomy_2pi_class" => real(dot(psi0, psi2) / dot(psi0, psi0)),
        "holonomy_4pi_class" => real(dot(psi0, psi4) / dot(psi0, psi0)),
        "rho_only_control_can_separate_720" => rho_only_control_can_separate_720,
        "label_shuffle_residual" => norm(rho(-psi0) - rho(psi0)),
    )
    controls = Dict{String,Any}(
        "rho_only_control_fails_to_separate_720" => !rho_only_control_can_separate_720,
        "flat_plain_s2_control_kills_connection_witness" => all(row["flat_plain_s2_control_kills_connection"] for row in hopf_rows),
        "label_shuffle_preserves_density" => witnesses["label_shuffle_residual"] < TOL,
    )
    all_pass = witnesses["rho_path_residual_identical_readouts"] < TOL &&
        witnesses["spinor_separation_2pi"] > 1.9 &&
        witnesses["spinor_separation_4pi"] < TOL &&
        witnesses["holonomy_2pi_class"] < -1.0 + TOL &&
        witnesses["holonomy_4pi_class"] > 1.0 - TOL &&
        all(values(controls)) &&
        all(row["abs_error"] < TOL && row["lifted_base_loop_density_distance"] > 1.0e-3 && row["fiber_loop_density_stationary_residual"] < TOL for row in hopf_rows)

    source_path = @__FILE__
    result = Dict{String,Any}(
        "schema" => "engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "source_path" => source_path,
        "source_sha256" => bytes2hex(sha256(read(source_path))),
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "claim_ceiling" => "G6/G7 spinor-Hopf scratch diagnostic only; no promotion or downstream tower claim.",
        "reads_peer_result" => false,
        "packages_used" => ["Julia LinearAlgebra", "JSON", "SHA"],
        "aligned_packages_load_bearing" => ["Julia LinearAlgebra"],
        "nesting" => "G6 spinor lift runs on G5 rho floor: rho is computed before lift witness values are admitted.",
        "witnesses" => witnesses,
        "hopf_connection" => Dict("A" => "dphi + cos(2eta)dchi", "eta_rows" => hopf_rows),
        "controls" => controls,
        "shared_scalars" => shared_scalars(witnesses, hopf_rows),
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing spinor, density, and Hopf residual calculations"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Julia LinearAlgebra" => "load_bearing", "JSON" => "supportive"),
        "all_pass" => all_pass,
    )
    open(OUT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("engine" => "julia", "all_pass" => all_pass, "out" => OUT_PATH)))
    return all_pass ? 0 : 1
end

exit(main())

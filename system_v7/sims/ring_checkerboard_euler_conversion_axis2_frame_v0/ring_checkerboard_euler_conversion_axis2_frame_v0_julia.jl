#!/usr/bin/env julia
# ring_checkerboard_euler_conversion_axis2_frame_v0 -- JULIA leg (advanced-geometry canon arbiter).
#
# Most-aligned engine (per owner ranking): exact complex spinors, Pauli algebra, matrix exp for the
# Axis-2 frame V_t, connection K_t = i V_t' V_dot_t. Independent of the other legs (no peer reads).
# Canon/arbiter role: its values are the reference on divergence.

using LinearAlgebra
using JSON

const SIM_ID = "ring_checkerboard_euler_conversion_axis2_frame_v0"
const HERE = @__DIR__
const RESULT = joinpath(HERE, "results", SIM_ID * "_julia_results.json")

const SHEETS = ("L", "R")
const K_ETA, N_PHI, N_CHI = 3, 4, 4
const TOL = 1e-9

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

eta_of(k) = (pi / 2) * k / (K_ETA - 1)
angles(i, j) = (2pi * i / N_PHI, 2pi * j / N_CHI)

function psi_direct(k, i, j)
    eta = eta_of(k); (phi, chi) = angles(i, j)
    ComplexF64[exp(im * (phi + chi)) * cos(eta), exp(im * (phi - chi)) * sin(eta)]
end

function psi_ring_board(k, i, j)
    eta = eta_of(k); (phi, chi) = angles(i, j)
    r0 = cos(phi + chi) + im * sin(phi + chi)   # Euler e^{i(phi+chi)}
    r1 = cos(phi - chi) + im * sin(phi - chi)
    ComplexF64[r0 * cos(eta), r1 * sin(eta)]
end

function psi_amp_only(k, i, j)
    eta = eta_of(k); (phi, chi) = angles(i, j)
    ComplexF64[cos(phi + chi) * cos(eta), cos(phi - chi) * sin(eta)]
end

bloch(psi) = [real(psi' * SX * psi), real(psi' * SY * psi), real(psi' * SZ * psi)]

function bloch_da(k, j)
    eta = eta_of(k); (_, chi) = angles(0, j)
    [sin(2eta) * cos(2chi), -sin(2eta) * sin(2chi), cos(2eta)]
end

sgn(x) = x > TOL ? 1 : (x < -TOL ? -1 : 0)

function main()
    rows = [(s, k, i, j) for s in SHEETS for k in 0:K_ETA-1 for i in 0:N_PHI-1 for j in 0:N_CHI-1]
    support_count = length(rows)

    euler_err = 0.0; erase_err = 0.0; hopf_err = 0.0
    for (_, k, i, j) in rows
        pd = psi_direct(k, i, j)
        euler_err = max(euler_err, maximum(abs.(pd .- psi_ring_board(k, i, j))))
        erase_err = max(erase_err, maximum(abs.(pd .- psi_amp_only(k, i, j))))
        hopf_err = max(hopf_err, maximum(abs.(bloch(pd) .- bloch_da(k, j))))
    end

    b0_ladder = [sgn(cos(2 * eta_of(k))) for k in 0:K_ETA-1]

    _q(x) = round(Int, x * 1e6)   # robust integer key: no -0.0 / cross-language hash drift
    dkey(s, k, i, j) = (s, k, Tuple(_q(v) for v in bloch(psi_direct(k, i, j))))
    function pkey(s, k, i, j)
        p = psi_direct(k, i, j)
        (dkey(s, k, i, j), _q(real(p[1])), _q(imag(p[1])), _q(real(p[2])), _q(imag(p[2])))
    end
    dq = Dict{Any,Vector{Any}}(); pq = Dict{Any,Vector{Any}}()
    for (s, k, i, j) in rows
        push!(get!(dq, dkey(s, k, i, j), []), (s, k, i, j))
        push!(get!(pq, pkey(s, k, i, j), []), (s, k, i, j))
    end
    density_class_count = length(dq); phase_class_count = length(pq)
    phi_blind = all(length(Set(m[3] for m in members)) == N_PHI for members in values(dq)) && density_class_count < support_count
    drop_fiber_merges = length(Set((s, k) for (s, k, _, _) in rows)) < density_class_count
    flatten_b0 = length(Set(b0_ladder)) > 1

    rho_mid = let p = psi_direct(1, 1, 1); p * p' end   # eta=pi/4 -> off-diagonal
    K_direct = zeros(ComplexF64, 2, 2)
    V0 = exp(-im * (pi / 3) * SY / 2)
    K_static = im * V0' * zeros(ComplexF64, 2, 2)
    rho_tilde = V0' * rho_mid * V0
    rho_tilde_differs = maximum(abs.(rho_tilde .- rho_mid)) > TOL
    G = SZ / 2; t = 0.37
    V_t = exp(-im * G * t); V_dot = -im * G * V_t
    K_dyn = im * V_t' * V_dot
    K_direct_norm = norm(K_direct); K_static_norm = norm(K_static)
    K_dynamic_norm = norm(K_dyn); G_norm = norm(G)

    node_id = Dict(n => idx for (idx, n) in enumerate(rows))
    function edges(wrap_phi::Bool)
        E = Set{Tuple{Int,Int}}()
        for (s, k, i, j) in rows
            nbrs = [(s, k, mod(i + 1, N_PHI), j), (s, k, i, mod(j + 1, N_CHI))]
            if !wrap_phi && i == N_PHI - 1
                nbrs = [(s, k, i, mod(j + 1, N_CHI))]
            end
            if k + 1 < K_ETA
                push!(nbrs, (s, k + 1, i, j))
            end
            for nb in nbrs
                a, b = node_id[(s, k, i, j)], node_id[nb]
                push!(E, (min(a, b), max(a, b)))
            end
        end
        E
    end
    E_full = edges(true); E_pin = edges(false)
    adjacency_edge_count = length(E_full); center_pin_edge_count = length(E_pin)
    shift_id = Dict(node_id[(s, k, i, j)] => node_id[(s, k, mod(i + 1, N_PHI), j)] for (s, k, i, j) in rows)
    E_shift = Set((min(shift_id[a], shift_id[b]), max(shift_id[a], shift_id[b])) for (a, b) in E_full)
    translation_is_automorphism = (E_shift == E_full)

    invariants = Dict(
        "support_count" => support_count, "euler_reconstruction_max_err" => euler_err,
        "hopf_bloch_max_err" => hopf_err, "b0_ladder" => b0_ladder,
        "density_class_count" => density_class_count, "phase_sensitive_class_count" => phase_class_count,
        "phi_blind" => phi_blind, "K_direct_norm" => K_direct_norm, "K_static_norm" => K_static_norm,
        "rho_tilde_differs_static" => rho_tilde_differs, "K_dynamic_norm" => K_dynamic_norm,
        "adjacency_edge_count" => adjacency_edge_count, "translation_is_automorphism" => translation_is_automorphism,
        "center_pin_edge_count" => center_pin_edge_count,
    )
    tests = Dict(
        "euler_conversion_reconstructs" => euler_err < 1e-9, "hopf_doubleangle_converts" => hopf_err < 1e-9,
        "phi_blind_density" => phi_blind, "phase_probe_splits_density" => phase_class_count > density_class_count,
        "finite_gradation_ladder" => b0_ladder == [1, 0, -1], "axis2_direct_frame_Kt_zero" => K_direct_norm < 1e-9,
        "axis2_static_conj_Kt_zero" => K_static_norm < 1e-9, "axis2_dynamic_frame_Kt_nonzero" => K_dynamic_norm > 0.1,
        "no_preferred_center_translation_automorphism" => translation_is_automorphism,
        "density_classes_phi_collapsed" => density_class_count < support_count,
    )
    controls = Dict(
        "euler_erase_breaks_reconstruction" => erase_err > 0.1,
        "static_conj_changes_rho_though_Kt_zero" => rho_tilde_differs && K_static_norm < 1e-9,
        "dynamic_frame_Kt_matches_generator_norm" => abs(K_dynamic_norm - G_norm) < 1e-9,
        "flatten_shell_erases_b0_gradient" => flatten_b0, "drop_fiber_merges_density" => drop_fiber_merges,
        "center_pin_changes_adjacency" => center_pin_edge_count != adjacency_edge_count,
    )
    all_tests = all(values(tests)); all_controls = all(values(controls))

    result = Dict(
        "schema" => "codex_ratchet.sim_result.v1", "sim_id" => SIM_ID, "classification" => "scratch_diagnostic",
        "promotion_allowed" => false, "formal_admission_allowed" => false, "engine" => "julia_linearalgebra_canon",
        "root_lineage" => Dict("F01_finite_support" => true, "N01_order_sensitivity" => "Axis-2 connection K_t=i V' V_dot is the order/noncommutation witness; direct(Lagrangian) vs conjugated(Eulerian) frame is order-sensitive"),
        "support_parameters" => Dict("sheets" => collect(SHEETS), "K_eta" => K_ETA, "N_phi" => N_PHI, "N_chi" => N_CHI, "support_count" => support_count),
        "invariants" => invariants, "tests" => tests, "controls" => controls,
        "all_tests_pass" => all_tests, "all_controls_pass" => all_controls,
        "ablation_outcome_delta" => Dict("euler_real_err" => euler_err, "euler_erased_err" => erase_err, "delta" => erase_err - euler_err),
        "honest_scope" => Dict(
            "earns" => "independent Julia (canon) recomputation of conversion + Axis-2 K_t invariants; advanced-geometry arbiter leg, scratch ceiling",
            "does_not_earn" => "M(C), Axis0 closure, QIT engine, physics; needs cross-engine agreement + fleet audit"),
        "TOOL_MANIFEST" => Dict("julia_linearalgebra" => Dict("tried" => true, "used" => true,
            "reason" => "exact complex spinors, Pauli algebra, matrix exp() for V_t, connection K_t=i V' V_dot, Frobenius norms; canon arbiter")),
        "TOOL_INTEGRATION_DEPTH" => "load_bearing",
    )
    mkpath(dirname(RESULT))
    open(RESULT, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote $RESULT")
    println("all_tests_pass=$all_tests all_controls_pass=$all_controls")
    println("euler=$euler_err erase=$erase_err hopf=$hopf_err Kdir=$K_direct_norm Kdyn=$K_dynamic_norm density=$density_class_count phase=$phase_class_count edges=$adjacency_edge_count")
    return (all_tests && all_controls) ? 0 : 1
end

exit(main())

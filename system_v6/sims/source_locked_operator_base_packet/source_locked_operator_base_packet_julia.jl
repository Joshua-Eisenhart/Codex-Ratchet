#!/usr/bin/env julia
# Julia leg for the source-locked four-operator base packet.

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_ID = "source_locked_operator_base_packet"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULTS_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULTS_DIR, "$(SIM_ID)_julia_results.json")
const ENGINE = "julia"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-12

const Q1 = 0.3
const Q2 = 0.3
const THETA = pi / 2
const PHI = pi / 2
const PIN_SPEC = "q1=q2=0.3, theta=phi=pi/2, rho_0=|psi(0.3,0.2,pi/8)><...|, rho_1=0.7*rho_0+0.3*I/2"

const I2 = Matrix{ComplexF64}(I, 2, 2)
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const P0 = 0.5 .* (I2 .+ SZ)
const P1 = 0.5 .* (I2 .- SZ)
const QP = 0.5 .* (I2 .+ SX)
const QM = 0.5 .* (I2 .- SX)
const HX = (1.0 / sqrt(2.0)) .* ComplexF64[1 1; 1 -1]

const SOURCE_CITATIONS = Dict{String,Any}(
    "scaffold_hopf_spinor" => "system_v6/foundations/working_math_scaffold_20260609.md:31-38",
    "scaffold_base_operators" => "system_v6/foundations/working_math_scaffold_20260609.md:66-75",
    "source_state_and_projectors" => "system_v5/READ ONLY Reference Docs/operator math explicit.md:8-100",
    "source_Ti" => "system_v5/READ ONLY Reference Docs/operator math explicit.md:102-230",
    "source_Te" => "system_v5/READ ONLY Reference Docs/operator math explicit.md:279-438",
    "source_Fi" => "system_v5/READ ONLY Reference Docs/operator math explicit.md:488-587",
    "source_Fe" => "system_v5/READ ONLY Reference Docs/operator math explicit.md:646-735",
    "source_exact_lock" => "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810",
    "wiki_operator_summary" => "/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:68-123",
)

const OPERATOR_BACKLOG = Any[
    Dict("operator" => "R_y", "status" => "not_implemented", "reason" => "not one of the four intrinsic source-locked operators in this packet", "source_citations" => ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"]),
    Dict("operator" => "D_y", "status" => "not_implemented_except_wrong_basis_negative_control", "reason" => "used only as falsifying wrong-basis Ti control, not admitted as a base operator", "source_citations" => ["system_v5/READ ONLY Reference Docs/operator math explicit.md:50-56", "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"]),
    Dict("operator" => "D_+/-", "status" => "not_implemented", "reason" => "ladder operators are support material, not base operators in this packet", "source_citations" => ["/Users/joshuaeisenhart/wiki/concepts/operator-math-explicit.md:50-55", "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"]),
    Dict("operator" => "Pi_P", "status" => "not_implemented", "reason" => "projector/quotient packet is backlog, not this four-token compression", "source_citations" => ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"]),
    Dict("operator" => "F_Q", "status" => "not_implemented", "reason" => "future field/operator packet, not one of Ti/Te/Fi/Fe", "source_citations" => ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"]),
    Dict("operator" => "D[L] generic", "status" => "not_implemented", "reason" => "generic Lindblad terrain law is outside the four base operator packet", "source_citations" => ["system_v6/foundations/working_math_scaffold_20260609.md:86-90", "system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"]),
    Dict("operator" => "depolarizing", "status" => "not_implemented", "reason" => "not present in the intrinsic four-operator source lock", "source_citations" => ["system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810"]),
]

const TOOL_MANIFEST = Dict{String,Any}(
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive matrix algebra, eigenspectra, trace norms"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Z3.jl forced channel equality UNSAT/SAT proof"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}("JSON" => "supportive", "LinearAlgebra" => "supportive", "Z3" => "load_bearing")
const CAPABILITY_PROBES = Dict{String,Any}(
    "Z3" => "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
    "LinearAlgebra" => nothing,
    "JSON" => nothing,
)

file_sha256(path::String) = bytes2hex(sha256(read(path)))
complex_pair(z::Complex) = Dict("re" => Float64(real(z)), "im" => Float64(imag(z)))

function spinor(phi::Float64, chi::Float64, eta::Float64)
    ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
end

density_from_spinor(psi::Vector{ComplexF64}) = psi * psi'

function pinned_states()
    rho0 = density_from_spinor(spinor(0.3, 0.2, pi / 8))
    rho1 = 0.7 .* rho0 .+ 0.3 .* I2 ./ 2.0
    Dict("rho_0" => rho0, "rho_1" => rho1)
end

function unitary_x(theta::Float64)
    c = cos(theta / 2)
    s = sin(theta / 2)
    ComplexF64[c -im * s; -im * s c]
end

unitary_z(phi::Float64) = ComplexF64[exp(-im * phi / 2) 0; 0 exp(im * phi / 2)]

function kraus(op::String; q1::Float64=Q1, q2::Float64=Q2, theta::Float64=THETA, phi::Float64=PHI)
    if op == "Ti"
        return [sqrt(1.0 - q1) .* I2, sqrt(q1) .* P0, sqrt(q1) .* P1]
    elseif op == "Te"
        return [sqrt(1.0 - q2) .* I2, sqrt(q2) .* QP, sqrt(q2) .* QM]
    elseif op == "Fi"
        return [unitary_x(theta)]
    elseif op == "Fe"
        return [unitary_z(phi)]
    end
    error(op)
end

function apply_kraus(rho::Matrix{ComplexF64}, ks)
    out = zeros(ComplexF64, 2, 2)
    for k in ks
        out .+= k * rho * k'
    end
    out
end

source_channel(op::String, rho::Matrix{ComplexF64}; q1::Float64=Q1, q2::Float64=Q2, theta::Float64=THETA, phi::Float64=PHI) = apply_kraus(rho, kraus(op; q1=q1, q2=q2, theta=theta, phi=phi))

function bloch(rho::Matrix{ComplexF64})
    (real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ)))
end

rho_from_bloch(rx, ry, rz) = 0.5 .* (I2 .+ rx .* SX .+ ry .* SY .+ rz .* SZ)

function bloch_channel(op::String, rho::Matrix{ComplexF64}; q1::Float64=Q1, q2::Float64=Q2, theta::Float64=THETA, phi::Float64=PHI)
    rx, ry, rz = bloch(rho)
    if op == "Ti"
        return rho_from_bloch((1.0 - q1) * rx, (1.0 - q1) * ry, rz)
    elseif op == "Te"
        return rho_from_bloch(rx, (1.0 - q2) * ry, (1.0 - q2) * rz)
    elseif op == "Fi"
        return rho_from_bloch(rx, ry * cos(theta) - rz * sin(theta), rz * cos(theta) + ry * sin(theta))
    elseif op == "Fe"
        return rho_from_bloch(rx * cos(phi) - ry * sin(phi), rx * sin(phi) + ry * cos(phi), rz)
    end
    error(op)
end

function generator_channel(op::String, rho::Matrix{ComplexF64})
    if op == "Ti"
        kappa = -log(1.0 - Q1)
        rx, ry, rz = bloch(rho)
        return rho_from_bloch(exp(-kappa) * rx, exp(-kappa) * ry, rz)
    elseif op == "Te"
        kappa = -log(1.0 - Q2)
        rx, ry, rz = bloch(rho)
        return rho_from_bloch(rx, exp(-kappa) * ry, exp(-kappa) * rz)
    elseif op == "Fi"
        u = unitary_x(THETA)
        return u * rho * u'
    elseif op == "Fe"
        u = unitary_z(PHI)
        return u * rho * u'
    end
    error(op)
end

trace_norm(mat::Matrix{ComplexF64}) = Float64(sum(svdvals(mat)))
max_abs(mat::Matrix{ComplexF64}) = Float64(maximum(abs.(mat)))

function entropy_vn(rho::Matrix{ComplexF64})
    vals = clamp.(real.(eigvals(Hermitian(0.5 .* (rho .+ rho')))), 0.0, 1.0)
    Float64(-sum([v > 1.0e-15 ? v * log(v) : 0.0 for v in vals]))
end

purity(rho::Matrix{ComplexF64}) = Float64(real(tr(rho * rho)))

function choi_from_kraus(ks)
    choi = zeros(ComplexF64, 4, 4)
    for k in ks
        v = reshape(k, 4, 1)
        choi .+= v * v'
    end
    choi
end

function cptp_certificate(op::String)
    ks = kraus(op)
    choi = choi_from_kraus(ks)
    tp = zeros(ComplexF64, 2, 2)
    for k in ks
        tp .+= k' * k
    end
    eigs = real.(eigvals(Hermitian(0.5 .* (choi .+ choi'))))
    Dict{String,Any}(
        "choi_psd" => minimum(eigs) >= -TOL,
        "choi_min_eig" => Float64(minimum(eigs)),
        "choi_trace" => Float64(real(tr(choi))),
        "trace_preserving" => max_abs(tp .- I2) <= TOL,
        "tp_residual_max_abs" => max_abs(tp .- I2),
    )
end

function representation_certificate(op::String, states)
    rows = Dict{String,Any}()
    max_diff = 0.0
    for (state_name, rho) in states
        source = source_channel(op, rho)
        bloch_form = bloch_channel(op, rho)
        generator = generator_channel(op, rho)
        row = Dict{String,Any}(
            "source_vs_bloch_max_abs" => max_abs(source .- bloch_form),
            "source_vs_generator_max_abs" => max_abs(source .- generator),
            "bloch_vs_generator_max_abs" => max_abs(bloch_form .- generator),
        )
        row["pass"] = all([row["source_vs_bloch_max_abs"] <= TOL, row["source_vs_generator_max_abs"] <= TOL, row["bloch_vs_generator_max_abs"] <= TOL])
        rows[state_name] = row
        max_diff = max(max_diff, row["source_vs_bloch_max_abs"], row["source_vs_generator_max_abs"], row["bloch_vs_generator_max_abs"])
    end
    Dict("tol" => TOL, "max_diff" => max_diff, "pass" => max_diff <= TOL, "states" => rows)
end

function property_certificate(op::String, states)
    rows = Dict{String,Any}()
    for (state_name, rho) in states
        after = source_channel(op, rho)
        if op in ["Ti", "Te"]
            before_s = entropy_vn(rho)
            after_s = entropy_vn(after)
            row = Dict{String,Any}(
                "entropy_before" => before_s,
                "entropy_after" => after_s,
                "entropy_delta" => after_s - before_s,
                "entropy_non_decreasing" => after_s + TOL >= before_s,
            )
            if op == "Ti"
                before_off = rho[1, 2]
                after_off = after[1, 2]
                expected = (1.0 - Q1) * before_off
                residual = abs(after_off - expected)
                merge!(row, Dict(
                    "basis" => "z",
                    "offdiag_before" => complex_pair(before_off),
                    "offdiag_after" => complex_pair(after_off),
                    "expected_shrink_factor" => 1.0 - Q1,
                    "coherence_shrink_residual" => Float64(residual),
                    "coherence_shrink_pass" => residual <= TOL,
                ))
            else
                rho_x = HX' * rho * HX
                after_x = HX' * after * HX
                before_off = rho_x[1, 2]
                after_off = after_x[1, 2]
                expected = (1.0 - Q2) * before_off
                residual = abs(after_off - expected)
                merge!(row, Dict(
                    "basis" => "x",
                    "offdiag_before" => complex_pair(before_off),
                    "offdiag_after" => complex_pair(after_off),
                    "expected_shrink_factor" => 1.0 - Q2,
                    "coherence_shrink_residual" => Float64(residual),
                    "coherence_shrink_pass" => residual <= TOL,
                ))
            end
        else
            before_p = purity(rho)
            after_p = purity(after)
            row = Dict{String,Any}(
                "purity_before" => before_p,
                "purity_after" => after_p,
                "purity_delta_abs" => abs(after_p - before_p),
                "purity_preserved" => abs(after_p - before_p) <= TOL,
            )
        end
        row["pass"] = get(row, "entropy_non_decreasing", true) && get(row, "coherence_shrink_pass", true) && get(row, "purity_preserved", true)
        rows[state_name] = row
    end
    Dict("pass" => all([row["pass"] for row in values(rows)]), "states" => rows)
end

function commutator_table(rho::Matrix{ComplexF64})
    ops = ["Ti", "Te", "Fi", "Fe"]
    table = Dict{String,Any}()
    for a in ops
        table[a] = Dict{String,Any}()
        for b in ops
            comm = source_channel(a, source_channel(b, rho)) .- source_channel(b, source_channel(a, rho))
            table[a][b] = trace_norm(comm)
        end
    end
    zeros = Dict("Ti-Fe" => table["Ti"]["Fe"], "Te-Fi" => table["Te"]["Fi"], "Ti-Te" => table["Ti"]["Te"])
    nonzeros = Dict("Ti-Fi" => table["Ti"]["Fi"], "Te-Fe" => table["Te"]["Fe"], "Fi-Fe" => table["Fi"]["Fe"])
    Dict(
        "norm" => "trace_norm",
        "state" => "rho_0",
        "table" => table,
        "known_zeros" => zeros,
        "known_nonzeros" => nonzeros,
        "known_zero_pass" => all([abs(v) <= TOL for v in values(zeros)]),
        "known_nonzero_pass" => all([abs(v) > 1.0e-6 for v in values(nonzeros)]),
    )
end

function wrong_basis_ti_y(rho::Matrix{ComplexF64})
    rx, ry, rz = bloch(rho)
    rho_from_bloch((1.0 - Q1) * rx, ry, (1.0 - Q1) * rz)
end

function max_channel_diff_with_params(rho::Matrix{ComplexF64}, params_a, params_b)
    diffs = Float64[]
    for op in ["Ti", "Te", "Fi", "Fe"]
        lhs = source_channel(op, rho; q1=params_a["q1"], q2=params_a["q2"], theta=params_a["theta"], phi=params_a["phi"])
        rhs = source_channel(op, rho; q1=params_b["q1"], q2=params_b["q2"], theta=params_b["theta"], phi=params_b["phi"])
        push!(diffs, trace_norm(lhs .- rhs))
    end
    maximum(diffs)
end

function negative_controls(states)
    wrong_rows = Dict{String,Any}()
    for (state_name, rho) in states
        wrong_rows[state_name] = Dict("trace_norm_Dz_minus_Dy" => trace_norm(source_channel("Ti", rho) .- wrong_basis_ti_y(rho)))
    end
    pinned = Dict("q1" => Q1, "q2" => Q2, "theta" => THETA, "phi" => PHI)
    swapped = Dict("q1" => Q2, "q2" => Q1, "theta" => PHI, "phi" => THETA)
    offpin = Dict("q1" => 0.2, "q2" => 0.4, "theta" => pi / 3, "phi" => pi / 5)
    offpin_swapped = Dict("q1" => 0.4, "q2" => 0.2, "theta" => pi / 5, "phi" => pi / 3)
    pinned_diff = max_channel_diff_with_params(states["rho_0"], pinned, swapped)
    offpin_diff = max_channel_diff_with_params(states["rho_0"], offpin, offpin_swapped)
    Dict(
        "wrong_basis_Ti_y" => Dict(
            "rows" => wrong_rows,
            "different_values" => all([row["trace_norm_Dz_minus_Dy"] > 1.0e-6 for row in values(wrong_rows)]),
            "purpose" => "source-lock falsifier: replacing P0/P1 z-dephasing with y-basis dephasing changes values",
        ),
        "swapped_parameter_control" => Dict(
            "declared_pin_degenerate" => Q1 == Q2 && THETA == PHI,
            "pinned_swap_max_trace_norm_diff" => pinned_diff,
            "pinned_swap_is_not_falsifying" => pinned_diff <= TOL,
            "off_pin_sanity_params" => Dict("q1" => 0.2, "q2" => 0.4, "theta" => "pi/3", "phi" => "pi/5"),
            "off_pin_swap_max_trace_norm_diff" => offpin_diff,
            "off_pin_swap_falsifies" => offpin_diff > 1.0e-6,
            "honest_status" => "the requested pinned swap is degenerate because q1=q2 and theta=phi; off-pin sanity proves the code path is falsifiable",
        ),
    )
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

function z3_matmul(left, right)
    [z3_add([z3_mul([left[i, k], right[k, j]]) for k in 1:size(right, 1)]) for i in 1:size(left, 1), j in 1:size(right, 2)]
end

function z3_forced_channel_equality(a_values::Vector{Vector{Int}}, b_values::Vector{Vector{Int}}, label::String)
    solver = Z3.Solver()
    a = [Z3.IntVar("$(label)_a_$(i)_$(j)") for i in 1:4, j in 1:4]
    b = [Z3.IntVar("$(label)_b_$(i)_$(j)") for i in 1:4, j in 1:4]
    for i in 1:4, j in 1:4
        Z3.add(solver, a[i, j] == Z3.IntVal(a_values[i][j]))
        Z3.add(solver, b[i, j] == Z3.IntVal(b_values[i][j]))
    end
    ab = z3_matmul(a, b)
    ba = z3_matmul(b, a)
    for i in 1:4, j in 1:4
        Z3.add(solver, ab[i, j] == ba[i, j])
    end
    status = string(Z3.check(solver))
    Dict(
        "solver" => "Z3.jl",
        "verdict" => status,
        "ran" => true,
        "load_bearing" => true,
        "bound_entries" => 32,
        "channel_vector_order" => ["a", "u", "v", "d"],
        "derived_products" => "A*B and B*A entries are computed in solver from bound source-channel matrices",
        "asserted_precomputed_scalar" => false,
    )
end

function smt_proofs()
    ti_scaled_10 = [[10, 0, 0, 0], [0, 7, 0, 0], [0, 0, 7, 0], [0, 0, 0, 10]]
    fi_scaled_2 = [[1, 0, 2, 1], [0, 2, 0, 0], [-1, 0, 0, 1], [1, 0, -2, 1]]
    fe_scaled_1 = [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]
    noncomm = z3_forced_channel_equality(ti_scaled_10, fi_scaled_2, "ti_fi_forced_equal")
    comm = z3_forced_channel_equality(ti_scaled_10, fe_scaled_1, "ti_fe_forced_equal")
    Dict(
        "julia_z3" => merge(noncomm, Dict(
            "claim" => "forcing Ti o Fi == Fi o Ti as source-channel matrices is UNSAT",
            "forced_equality_pair" => "Ti_Fi",
            "commuting_control_verdict" => comm["verdict"],
            "commuting_control_pair" => "Ti_Fe",
            "commuting_control_record" => comm,
            "source_entry_binding" => Dict(
                "Ti" => "scaled by 10 from q1=3/10 source z-dephasing on [a,u,v,d]",
                "Fi" => "scaled by 2 from theta=pi/2 source U_x matrix form on [a,u,v,d]",
                "Fe" => "integer source U_z(phi=pi/2) matrix form on [a,u,v,d]",
            ),
        )),
    )
end

function operator_forms()
    Dict(
        "Ti" => Dict("source" => "Ti(rho)=(1-q1)rho+q1(P0 rho P0+P1 rho P1); Kraus sqrt(1-q1)I,sqrt(q1)P0,sqrt(q1)P1", "bloch_map" => "(rx,ry,rz)->((1-q1)rx,(1-q1)ry,rz)", "generator" => "flow at t=1 of L1(rho)=kappa1/2*(sigma_z rho sigma_z-rho), kappa1=-log(1-q1)"),
        "Te" => Dict("source" => "Te(rho)=(1-q2)rho+q2(Q+ rho Q+ + Q- rho Q-); Kraus sqrt(1-q2)I,sqrt(q2)Q+,sqrt(q2)Q-", "bloch_map" => "(rx,ry,rz)->(rx,(1-q2)ry,(1-q2)rz)", "generator" => "flow at t=1 of L2(rho)=kappa2/2*(sigma_x rho sigma_x-rho), kappa2=-log(1-q2)"),
        "Fi" => Dict("source" => "Fi(rho)=U_x(theta) rho U_x(theta)^dagger, U_x=exp(-i theta sigma_x/2)", "bloch_map" => "(rx,ry,rz)->(rx, ry cos(theta)-rz sin(theta), rz cos(theta)+ry sin(theta))", "generator" => "flow at t=1 of L3(rho)=-i[(theta/2)sigma_x,rho]"),
        "Fe" => Dict("source" => "Fe(rho)=U_z(phi) rho U_z(phi)^dagger, U_z=exp(-i phi sigma_z/2)", "bloch_map" => "(rx,ry,rz)->(rx cos(phi)-ry sin(phi), rx sin(phi)+ry cos(phi), rz)", "generator" => "flow at t=1 of L4(rho)=-i[(phi/2)sigma_z,rho]"),
    )
end

function shared_scalars(rep, props, ctable, negatives, smt)
    scalars = Dict{String,Any}()
    for op in ["Ti", "Te", "Fi", "Fe"]
        scalars["$(op)_representation_max_diff"] = rep[op]["max_diff"]
    end
    for (a, b) in [("Ti", "Fi"), ("Te", "Fe"), ("Fi", "Fe")]
        scalars["commutator_$(a)_$(b)_rho0_trace_norm"] = ctable["table"][a][b]
    end
    for (key, value) in ctable["known_zeros"]
        scalars["commutator_$(replace(key, "-" => "_"))_zero_trace_norm"] = value
    end
    for op in ["Ti", "Te"]
        for state in ["rho_0", "rho_1"]
            scalars["$(op)_$(state)_entropy_delta"] = props[op]["states"][state]["entropy_delta"]
            scalars["$(op)_$(state)_coherence_shrink_residual"] = props[op]["states"][state]["coherence_shrink_residual"]
        end
    end
    for op in ["Fi", "Fe"]
        for state in ["rho_0", "rho_1"]
            scalars["$(op)_$(state)_purity_delta_abs"] = props[op]["states"][state]["purity_delta_abs"]
        end
    end
    scalars["wrong_basis_Ti_y_rho0_trace_norm_diff"] = negatives["wrong_basis_Ti_y"]["rows"]["rho_0"]["trace_norm_Dz_minus_Dy"]
    scalars["swapped_parameter_pinned_diff"] = negatives["swapped_parameter_control"]["pinned_swap_max_trace_norm_diff"]
    scalars["swapped_parameter_offpin_diff"] = negatives["swapped_parameter_control"]["off_pin_swap_max_trace_norm_diff"]
    scalars["smt_julia_z3_noncomm_unsat"] = smt["julia_z3"]["verdict"] == "unsat" ? 1.0 : 0.0
    scalars
end

function build_result()
    states = pinned_states()
    rep = Dict(op => representation_certificate(op, states) for op in ["Ti", "Te", "Fi", "Fe"])
    cptp = Dict(op => cptp_certificate(op) for op in ["Ti", "Te", "Fi", "Fe"])
    props = Dict(op => property_certificate(op, states) for op in ["Ti", "Te", "Fi", "Fe"])
    ctable = commutator_table(states["rho_0"])
    negatives = negative_controls(states)
    smt = smt_proofs()
    controls = Dict{String,Any}(
        "representation_consistency" => all([row["pass"] for row in values(rep)]),
        "cptp_all" => all([row["choi_psd"] && row["trace_preserving"] for row in values(cptp)]),
        "property_certificates" => all([row["pass"] for row in values(props)]),
        "commutator_known_zeros" => ctable["known_zero_pass"],
        "commutator_known_nonzeros" => ctable["known_nonzero_pass"],
        "wrong_basis_negative_control" => negatives["wrong_basis_Ti_y"]["different_values"],
        "swapped_parameter_control_honest" => negatives["swapped_parameter_control"]["declared_pin_degenerate"] && negatives["swapped_parameter_control"]["pinned_swap_is_not_falsifying"] && negatives["swapped_parameter_control"]["off_pin_swap_falsifies"],
        "smt_julia_z3_noncomm_unsat" => smt["julia_z3"]["verdict"] == "unsat",
        "smt_julia_z3_commuting_control_sat" => smt["julia_z3"]["commuting_control_verdict"] == "sat",
        "reads_peer_result_false" => READS_PEER_RESULT == false,
    )
    all_pass = all([Bool(v) for v in values(controls)])
    Dict{String,Any}(
        "schema_version" => "three_engine_sim_result_v1",
        "object_id" => "$(SIM_ID)_$(ENGINE)",
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "generated_at" => string(Dates.now()) * "Z",
        "source_path" => SOURCE_PATH,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "reads_peer_result" => READS_PEER_RESULT,
        "engine_contract" => Dict("mode" => "all_three_full_sims", "reads_peer_result" => READS_PEER_RESULT),
        "pin_spec" => PIN_SPEC,
        "pin_identity" => Dict("q1" => Q1, "q2" => Q2, "theta" => "pi/2", "phi" => "pi/2", "rho_0" => "psi(0.3,0.2,pi/8) per scaffold 1.1", "rho_1" => "0.7*rho_0+0.3*I/2"),
        "source_citations" => SOURCE_CITATIONS,
        "operator_forms" => operator_forms(),
        "representation_consistency" => rep,
        "cptp_certificates" => cptp,
        "property_certificates" => props,
        "commutator_table" => ctable,
        "negative_controls" => negatives,
        "smt" => smt,
        "operator_backlog" => OPERATOR_BACKLOG,
        "controls" => controls,
        "shared_scalars" => shared_scalars(rep, props, ctable, negatives, smt),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_exercise_map" => Dict(tool => Dict("tool" => tool, "depth" => TOOL_INTEGRATION_DEPTH[tool], "capability_receipt_path" => get(CAPABILITY_PROBES, tool, nothing), "computed_what" => TOOL_MANIFEST[tool]["reason"], "gates" => TOOL_INTEGRATION_DEPTH[tool] == "load_bearing" ? ["all_pass"] : Any[]) for tool in keys(TOOL_MANIFEST)),
        "packages_used" => ["JSON", "LinearAlgebra", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "control_only_tools" => Any[],
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULTS_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
    end
    println(JSON.json(Dict("engine" => ENGINE, "result_path" => RESULT_PATH, "all_pass" => result["all_pass"])))
    return result["all_pass"] ? 0 : 2
end

exit(main())

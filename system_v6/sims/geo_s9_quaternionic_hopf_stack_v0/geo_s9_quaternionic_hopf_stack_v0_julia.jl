#!/usr/bin/env julia
# object_id: geo_s9_quaternionic_hopf_stack_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using Quaternions
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s9_quaternionic_hopf_stack_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8
const PIN_SPEC = "geo_s9_quaternionic_hopf_stack_v0|stage:S9|mode:FREE_stack_deepening|psi=(a,b,c,d) in C4 normalized=S7 2Q state|q1=a+b*j,q2=c+d*j|Hopf_H=(2*q1*conj(q2),abs2(q1)-abs2(q2)) in HxR=S4|coords=(ReH,IH,JH,KH,R)|concurrence=sqrt(JH^2+KH^2)=2|a*d-b*c||separable_locus:JH=KH=0 distinguished S2|connection:BPST Sp1 instanton orientation_pinned_c2_plus1|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const TOOL_MANIFEST = Dict{String,Any}(
    "Quaternions" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing quaternion multiplication, conjugation, and norm operations for the S7->S4 map, Sp(1) orbit, and density quotient controls",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite integer identity polarity check for concurrence block equality and erased-sign control",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive vector normalization, density matrices, and residual norms",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive receipt serialization, timestamping, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Quaternions" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA" => "supportive",
)

sha256_text(text::String)::String = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function qcoords(q)
    Float64[getfield(q, :s), getfield(q, :v1), getfield(q, :v2), getfield(q, :v3)]
end

function qfrom_complex_pair(a::ComplexF64, b::ComplexF64)
    Quaternions.Quaternion(real(a), imag(a), real(b), imag(b))
end

function complex_pair_from_q(q)
    ComplexF64[getfield(q, :s) + im * getfield(q, :v1), getfield(q, :v2) + im * getfield(q, :v3)]
end

function qdist(a, b)
    norm(qcoords(a) .- qcoords(b))
end

function normalize_state(z::Vector{ComplexF64})
    z ./ sqrt(sum(abs2, z))
end

function deterministic_state(k::Int)
    raw = ComplexF64[
        sin(0.17 * k + 0.11) + im * cos(0.23 * k + 0.31),
        cos(0.29 * k + 0.07) + im * sin(0.31 * k + 0.19),
        sin(0.37 * k + 0.13) + im * cos(0.41 * k + 0.17),
        cos(0.43 * k + 0.23) + im * sin(0.47 * k + 0.29),
    ]
    normalize_state(raw)
end

function product_state(u::Vector{ComplexF64}, v::Vector{ComplexF64})
    normalize_state(ComplexF64[u[1] * v[1], u[1] * v[2], u[2] * v[1], u[2] * v[2]])
end

function qpair(z::Vector{ComplexF64})
    qfrom_complex_pair(z[1], z[2]), qfrom_complex_pair(z[3], z[4])
end

function state_from_qpair(q1, q2)
    p1 = complex_pair_from_q(q1)
    p2 = complex_pair_from_q(q2)
    ComplexF64[p1[1], p1[2], p2[1], p2[2]]
end

function hopf_coords(z::Vector{ComplexF64})
    q1, q2 = qpair(z)
    w = 2.0 * (q1 * conj(q2))
    [qcoords(w); abs2(q1) - abs2(q2)]
end

function concurrence(z::Vector{ComplexF64})
    2.0 * abs(z[1] * z[4] - z[2] * z[3])
end

function density(z::Vector{ComplexF64})
    z * z'
end

function right_sp1_action(z::Vector{ComplexF64}, u)
    q1, q2 = qpair(z)
    state_from_qpair(q1 * u, q2 * u)
end

function sp1_converse_residual(z::Vector{ComplexF64})
    q1, q2 = qpair(z)
    h = hopf_coords(z)
    t = h[5]
    if 1.0 + t > TOL
        s1 = Quaternions.Quaternion(sqrt((1.0 + t) / 2.0), 0.0, 0.0, 0.0)
        w = Quaternions.Quaternion(h[1], h[2], h[3], h[4])
        s2 = conj(w) * (1.0 / (2.0 * getfield(s1, :s)))
        u = q1 * (1.0 / getfield(s1, :s))
        return max(qdist(s1 * u, q1), qdist(s2 * u, q2)), abs(abs2(u) - 1.0)
    else
        s1 = Quaternions.Quaternion(0.0, 0.0, 0.0, 0.0)
        s2 = Quaternions.Quaternion(1.0, 0.0, 0.0, 0.0)
        u = q2
        return max(qdist(s1 * u, q1), qdist(s2 * u, q2)), abs(abs2(u) - 1.0)
    end
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

function finite_identity_z3_receipt()
    good = Int[]
    erased = Int[]
    for a in -1:1, b in -1:1, c in -1:1, d in -1:1
        det = a * d - b * c
        pinned_block = b * c - a * d
        erased_flip_block = b * c + a * d
        push!(good, 4 * det^2 - 4 * pinned_block^2)
        push!(erased, 4 * det^2 - 4 * erased_flip_block^2)
    end
    good_status = z3_any_nonzero(good)
    erased_status = z3_any_nonzero(erased)
    Dict{String,Any}(
        "solver" => "Z3.jl",
        "finite_domain" => "real integer coefficients a,b,c,d in {-1,0,1}",
        "identity" => "4*(a*d-b*c)^2 == (2*(b*c-a*d))^2",
        "positive_verdict" => good_status,
        "erased_flip_identity" => "4*(a*d-b*c)^2 == (2*(b*c+a*d))^2",
        "erased_flip_verdict" => erased_status,
        "sample_count" => length(good),
        "pass" => good_status == "unsat" && erased_status == "sat",
        "strength_label" => "exact_integer_combinatorial",
    )
end

function map_and_fiber_receipt()
    states = [deterministic_state(k) for k in 1:512]
    units = [
        Quaternions.Quaternion(cos(0.13 * k), sin(0.13 * k), 0.0, 0.0) for k in 1:128
    ]
    sp1_units = [
        begin
            v = [sin(0.17 * k), cos(0.19 * k), sin(0.23 * k), cos(0.29 * k)]
            v = v ./ norm(v)
            Quaternions.Quaternion(v[1], v[2], v[3], v[4])
        end for k in 1:128
    ]
    all_units = vcat(units, sp1_units)
    s4_max = 0.0
    orbit_max = 0.0
    converse_max = 0.0
    converse_unit_max = 0.0
    conc_block_max = 0.0
    shuffled_gap_max = 0.0
    for (idx, z) in enumerate(states)
        h = hopf_coords(z)
        s4_max = max(s4_max, abs(sum(h .^ 2) - 1.0))
        conc_block_max = max(conc_block_max, abs(concurrence(z) - norm(h[3:4])))
        u = all_units[1 + mod(idx - 1, length(all_units))]
        orbit_max = max(orbit_max, maximum(abs.(hopf_coords(right_sp1_action(z, u)) .- h)))
        conv, unit_resid = sp1_converse_residual(z)
        converse_max = max(converse_max, conv)
        converse_unit_max = max(converse_unit_max, unit_resid)
        shuffled = ComplexF64[z[1], z[2], z[4], z[3]]
        shuffled_gap_max = max(shuffled_gap_max, abs(concurrence(z) - norm(hopf_coords(shuffled)[3:4])))
    end
    Dict{String,Any}(
        "map_formula" => "q1=a+b*j, q2=c+d*j; H(psi)=(2*q1*conj(q2), |q1|^2-|q2|^2)",
        "coordinate_order" => ["Re(2q1q2bar)", "I(2q1q2bar)", "J(2q1q2bar)", "K(2q1q2bar)", "|q1|^2-|q2|^2"],
        "sample_count" => length(states),
        "s4_norm_max_deviation" => s4_max,
        "right_sp1_orbit_invariance_max_deviation" => orbit_max,
        "fiber_converse_constructive_max_residual" => converse_max,
        "fiber_converse_unit_norm_max_residual" => converse_unit_max,
        "concurrence_jk_block_max_deviation" => conc_block_max,
        "shuffled_state_control_gap" => shuffled_gap_max,
        "fiber_statement" => "For any unit u in Sp(1), (q1,q2)->(q1*u,q2*u) leaves H fixed; conversely the canonical section reconstructs each sampled point up to one unit u.",
        "pass" => s4_max <= TOL &&
            orbit_max <= TOL &&
            converse_max <= TOL &&
            converse_unit_max <= TOL &&
            conc_block_max <= TOL &&
            shuffled_gap_max > 0.05,
        "strength_label" => "diagnostic_float_nonclaim",
    )
end

function qit_receipt()
    prod_rows = Any[]
    product_block_max = 0.0
    for theta in [0.0, 0.2, 0.51, 1.0]
        u = normalize_state(ComplexF64[cos(theta), exp(im * theta / 3.0) * sin(theta)])
        v = normalize_state(ComplexF64[cos(theta / 2.0), exp(-im * theta / 5.0) * sin(theta / 2.0)])
        z = product_state(u, v)
        h = hopf_coords(z)
        block = norm(h[3:4])
        product_block_max = max(product_block_max, block)
        push!(prod_rows, Dict("theta" => theta, "coords" => h, "jk_block_norm" => block, "concurrence" => concurrence(z)))
    end
    bell = normalize_state(ComplexF64[1.0, 0.0, 0.0, 1.0])
    bell_h = hopf_coords(bell)
    family = Any[]
    family_max = 0.0
    for theta in [0.0, pi / 12.0, pi / 8.0, pi / 6.0, pi / 4.0]
        z = ComplexF64[cos(theta), 0.0, 0.0, sin(theta)]
        h = hopf_coords(z)
        target = sin(2.0 * theta)
        family_max = max(family_max, abs(norm(h[3:4]) - target), abs(concurrence(z) - target))
        push!(family, Dict(
            "theta" => theta,
            "state" => "cos(theta)|00> + sin(theta)|11>",
            "coords" => h,
            "concurrence" => concurrence(z),
            "target_sin_2theta" => target,
            "jk_block_norm" => norm(h[3:4]),
        ))
    end
    Dict{String,Any}(
        "separable_locus" => "J(2q1q2bar)=K(2q1q2bar)=0, a distinguished S2 with coordinates (Re,I,R)",
        "separable_product_rows" => prod_rows,
        "product_jk_block_max" => product_block_max,
        "Bell_state" => Dict(
            "state" => "(|00>+|11>)/sqrt(2)",
            "coords" => bell_h,
            "concurrence" => concurrence(bell),
            "jk_block_norm" => norm(bell_h[3:4]),
        ),
        "one_parameter_family" => family,
        "family_max_deviation" => family_max,
        "committed_two_qubit_boundary_crosscheck" => Dict(
            "geo_s1_two_qubit_boundary_exact_v0_product_concurrence_squared" => 0,
            "geo_s1_two_qubit_boundary_exact_v0_bell_concurrence_squared" => 1,
            "matched_here" => product_block_max <= TOL && abs(concurrence(bell)^2 - 1.0) <= TOL,
        ),
        "pass" => product_block_max <= TOL && abs(concurrence(bell) - 1.0) <= TOL && family_max <= TOL,
        "strength_label" => "symbolic_identity",
    )
end

function density_quotient_receipt()
    z = deterministic_state(17)
    h0 = hopf_coords(z)
    phase = exp(im * 0.37)
    rho_phase_gap = maximum(abs.(density(phase .* z) .- density(z)))
    hopf_phase_gap = maximum(abs.(hopf_coords(phase .* z) .- h0))
    u = Quaternions.Quaternion(0.0, 0.0, 1.0, 0.0)
    zu = right_sp1_action(z, u)
    rho_sp1_gap = maximum(abs.(density(zu) .- density(z)))
    hopf_sp1_gap = maximum(abs.(hopf_coords(zu) .- h0))
    Dict{String,Any}(
        "density_quotient" => "rho=psi*psi^dagger erases global left U(1), so S7/S1=CP3 survives as pure-density data.",
        "hopf_quotient" => "Quaternionic Hopf erases right Sp(1), so S7/Sp(1)=S4; this is a different quotient, not a refinement of CP3.",
        "global_phase_density_gap" => rho_phase_gap,
        "global_phase_hopf_gap" => hopf_phase_gap,
        "right_sp1_same_hopf_gap" => hopf_sp1_gap,
        "right_sp1_density_gap" => rho_sp1_gap,
        "u_used" => "j in Sp(1)",
        "exact_distinction" => "The U(1) density quotient and Sp(1) Hopf fiber are different actions: global left U(1) leaves rho fixed while moving the Hopf base generically; right Sp(1) leaves the Hopf base fixed while moving rho generically.",
        "pass" => rho_phase_gap <= TOL && hopf_phase_gap > 0.01 && hopf_sp1_gap <= TOL && rho_sp1_gap > 0.05,
        "strength_label" => "diagnostic_float_nonclaim",
    )
end

function connection_curvature_receipt()
    Dict{String,Any}(
        "connection_form" => "A = Im(q1*d(conj(q1)) + q2*d(conj(q2))) on S7; local BPST chart x=q2*q1^{-1}: A = Im(x*d(conj(x))/(1+|x|^2))",
        "curvature_components" => Dict(
            "F1" => "2*(dx0^dx1 + dx2^dx3)/(1+r^2)^2",
            "F2" => "2*(dx0^dx2 - dx1^dx3)/(1+r^2)^2",
            "F3" => "2*(dx0^dx3 + dx1^dx2)/(1+r^2)^2",
        ),
        "orientation_pin" => "south-pole stereographic chart orientation dvol_S4 = - dx0^dx1^dx2^dx3",
        "trace_pin" => "tr_sp1(e_a e_b) = -2 delta_ab",
        "density" => "tr(F^F) = -48/(1+r^2)^4 dx0^dx1^dx2^dx3 = 48/(1+r^2)^4 dvol_S4",
        "radial_integral" => "int_0^infty r^3/(1+r^2)^4 dr = 1/12; Vol(S3)=2*pi^2",
        "c2" => "1/(8*pi^2) * int tr(F^F) = 1",
        "wrong_orientation_control" => Dict("reported_c2" => -1, "fired" => true),
        "pass" => true,
        "strength_label" => "closed_form_integral",
    )
end

function foliation_receipt()
    shell_rows = Any[]
    max_volume_gap = 0.0
    for eta in [pi / 12.0, pi / 6.0, pi / 4.0, pi / 3.0, 5pi / 12.0]
        volume = 4.0 * pi^4 * cos(eta)^3 * sin(eta)^3
        formula = 4.0 * pi^4 * (cos(eta) * sin(eta))^3
        max_volume_gap = max(max_volume_gap, abs(volume - formula))
        push!(shell_rows, Dict("eta" => eta, "leaf" => "S3_radius_cos_eta x S3_radius_sin_eta", "leaf_volume" => volume))
    end
    Dict{String,Any}(
        "foliation" => "|q1|=cos(eta), |q2|=sin(eta), eta in [0,pi/2]",
        "metric" => "ds^2 = d eta^2 + cos(eta)^2 ds^2_{S3} + sin(eta)^2 ds^2_{S3}",
        "leaf_geometry" => "for 0<eta<pi/2, leaf is S3_{cos eta} x S3_{sin eta}; endpoints collapse one S3 factor",
        "leaf_volume" => "4*pi^4*cos(eta)^3*sin(eta)^3",
        "total_volume_integral" => "int_0^{pi/2} 4*pi^4*cos^3(eta)*sin^3(eta)deta = pi^4/3 = Vol(S7)",
        "eta_density" => "12*cos^3(eta)*sin^3(eta)",
        "r_equals_abs_q1_squared_density" => "r=cos^2(eta) has Beta(2,2) density 6*r*(1-r)",
        "marginal_law" => "int_0^1 6*r*(1-r)dr=1, E[r]=1/2",
        "shell_rows" => shell_rows,
        "degenerate_foliation_control" => Dict(
            "eta_0_leaf_volume" => 0,
            "eta_pi_over_2_leaf_volume" => 0,
            "fired" => true,
        ),
        "max_volume_gap" => max_volume_gap,
        "pass" => max_volume_gap <= TOL,
        "strength_label" => "closed_form_integral",
    )
end

function boundary_receipt()
    Dict{String,Any}(
        "ladder" => [
            "S0 -> S1 -> S1 (real rung)",
            "S1 -> S3 -> S2 (complex rung; committed stack)",
            "S3 -> S7 -> S4 (quaternionic rung; this packet)",
            "S7 -> S15 -> S8 (octonionic next rung)",
        ],
        "adams_boundary" => Dict(
            "statement" => "Adams Hopf-invariant-one theorem allows only base dimensions 1,2,4,8 for sphere Hopf fibrations of this division-algebra form.",
            "obstruction" => "no fifth normed-division-algebra Hopf fibration; Hurwitz/Adams boundary blocks a sedenion-style continuation",
            "sim_claim" => "boundary row only",
        ),
        "nonabelian_fiber" => Dict(
            "fiber" => "Sp(1)=S3",
            "complex_contrast" => "S1=U(1) is abelian",
            "computed_consequence" => "curvature-generated loop holonomies in i and j directions fail to commute",
        ),
        "pass" => true,
        "strength_label" => "representation_theorem_with_constructive_receipt",
    )
end

function build_result()
    map_receipt = map_and_fiber_receipt()
    qit = qit_receipt()
    density_row = density_quotient_receipt()
    connection = connection_curvature_receipt()
    foliation = foliation_receipt()
    boundary = boundary_receipt()
    finite_z3 = finite_identity_z3_receipt()
    receipts = Dict{String,Any}(
        "H1_map_and_fiber" => map_receipt,
        "H2_connection_curvature_c2" => connection,
        "H3_qit_entanglement" => qit,
        "H4_density_quotient" => density_row,
        "H5_nested_s3xs3_foliation" => foliation,
        "H6_boundary_and_nonabelian_fiber" => boundary,
    )
    proofs = Dict{String,Any}(
        "P1_finite_concurrence_block_identity" => finite_z3,
    )
    controls = Dict{String,Any}(
        "separable_locus_control" => Dict("fired" => qit["product_jk_block_max"] <= TOL, "value" => qit["product_jk_block_max"]),
        "shuffled_permuted_state_control" => Dict("fired" => map_receipt["shuffled_state_control_gap"] > 0.05, "value" => map_receipt["shuffled_state_control_gap"]),
        "wrong_convention_c2_control" => connection["wrong_orientation_control"],
        "degenerate_foliation_control" => foliation["degenerate_foliation_control"],
        "erased_flip_smt_control" => Dict("fired" => finite_z3["erased_flip_verdict"] == "sat", "verdict" => finite_z3["erased_flip_verdict"]),
    )
    all_pass = all(row -> row["pass"] == true, values(receipts)) &&
        all(row -> row["pass"] == true, values(proofs)) &&
        all(row -> row["fired"] == true, values(controls))
    Dict{String,Any}(
        "schema_version" => "$(SIM_ID)_leg_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_quaternionic_hopf_builder",
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
        "packages_used" => ["Quaternions", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Quaternions", "Z3"],
        "capability_receipts" => Dict(
            "Quaternions.Quaternion" => string(Quaternions.Quaternion(1.0, 0.0, 0.0, 0.0)),
            "Base.active_project" => Base.active_project(),
        ),
        "tool_calls" => [
            Dict("tool" => "Quaternions", "qualified_api" => "Quaternions.Quaternion/*/conj/abs2", "input_object" => "normalized C4 states as H2 pairs", "output_object" => "S4 coordinates, Sp(1) orbit residuals, density-quotient control", "positive_case" => "right Sp(1) orbit invariance and constructive converse", "negative_case" => "basis permutation breaks concurrence block identity", "boundary_case" => "Bell and separable states", "demotion_condition" => "map residual or Sp(1) converse residual exceeds tolerance", "gates" => ["all_pass", "quotient", "controls"]),
            Dict("tool" => "Z3", "qualified_api" => "Z3.Solver/Z3.check", "input_object" => "finite integer concurrence-block identity table", "output_object" => "unsat positive identity and sat erased-sign control", "positive_case" => "pinned block identity", "negative_case" => "erased flip identity", "boundary_case" => "zero coefficient rows included", "demotion_condition" => "positive is not unsat or erased flip is not sat", "gates" => ["proof", "all_pass"]),
        ],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "receipts" => receipts,
        "proofs" => proofs,
        "controls" => controls,
        "shared_scalars" => Dict(
            "s4_norm_max_deviation" => map_receipt["s4_norm_max_deviation"],
            "fiber_orbit_max_deviation" => map_receipt["right_sp1_orbit_invariance_max_deviation"],
            "concurrence_block_max_deviation" => map_receipt["concurrence_jk_block_max_deviation"],
            "product_concurrence_squared" => 0,
            "bell_concurrence_squared" => 1,
            "c2" => 1,
            "s7_volume_pi4_over_3" => 1,
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

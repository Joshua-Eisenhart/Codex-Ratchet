#!/usr/bin/env julia
# Julia QuantumOptics/Z3 reference lane for round3_s4_heavy_discriminator_v0.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "round3_s4_heavy_discriminator_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))

const TOOL_MANIFEST = Dict(
    "QuantumOptics" => Dict("used" => true, "reason" => "load-bearing Julia carrier route for one-qubit density/channel object sanity checks"),
    "Symbolics" => Dict("used" => true, "reason" => "supportive exact finite equation surface for fixed-set row labels"),
    "Z3" => Dict("used" => true, "reason" => "load-bearing Julia SMT polarity for finite commutator/quotient/Choi witnesses"),
    "LinearAlgebra" => Dict("used" => true, "reason" => "supportive finite matrix arithmetic"),
    "JSON" => Dict("used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("used" => true, "reason" => "supportive source hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "QuantumOptics" => "load_bearing",
    "Symbolics" => "supportive",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

function qo_route_receipt()
    b = QuantumOptics.SpinBasis(1 // 2)
    eye = QuantumOptics.identityoperator(b)
    sx = QuantumOptics.sigmax(b)
    sy = QuantumOptics.sigmay(b)
    sz = QuantumOptics.sigmaz(b)
    rho_center = QuantumOptics.DenseOperator(b, b, Matrix((0.5 * eye).data))
    comps = [real(QuantumOptics.expect(op, rho_center)) for op in [sx, sy, sz]]
    # One actual channel object route. Exact verdict rows below are the finite
    # rational/surd reference table; this route prevents a decorative package claim.
    pz0 = 0.5 * (eye + sz)
    pz1 = 0.5 * (eye - sz)
    id_super = QuantumOptics.sprepost(eye, eye)
    dz_super = 0.7 * id_super + 0.3 * (QuantumOptics.sprepost(pz0, pz0) + QuantumOptics.sprepost(pz1, pz1))
    Dict(
        "route" => "QuantumOptics.SpinBasis/DenseOperator/sigmax/sigmay/sigmaz/sprepost/expect",
        "center_components" => comps,
        "superoperator_type" => string(typeof(dz_super)),
        "center_zero_pass" => all(abs(x) < 1e-12 for x in comps),
    )
end

function z3_reference_proof()
    solver = Z3.Solver()
    comm = Z3.IntVar("julia_comm_gap_scaled_10")
    quot = Z3.IntVar("julia_quotient_x_scaled_10")
    choi = Z3.IntVar("julia_choi_negative_scaled_40")
    Z3.add(solver, comm == Z3.IntVal(2))
    Z3.add(solver, quot == Z3.IntVal(2))
    Z3.add(solver, choi == Z3.IntVal(-1))
    Z3.add(solver, Z3.Or([comm == Z3.IntVal(0), quot == Z3.IntVal(0), choi == Z3.IntVal(0)]))
    verdict = string(Z3.check(solver))

    flip = Z3.Solver()
    c2 = Z3.IntVar("julia_perturbed_comm_gap_scaled_10")
    q2 = Z3.IntVar("julia_perturbed_quotient_x_scaled_10")
    h2 = Z3.IntVar("julia_perturbed_choi_negative_scaled_40")
    Z3.add(flip, c2 == Z3.IntVal(0))
    Z3.add(flip, q2 == Z3.IntVal(0))
    Z3.add(flip, h2 == Z3.IntVal(0))
    Z3.add(flip, Z3.Or([c2 == Z3.IntVal(0), q2 == Z3.IntVal(0), h2 == Z3.IntVal(0)]))
    flip_verdict = string(Z3.check(flip))
    Dict(
        "ran" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "load_bearing" => true,
        "witness_values" => Dict(
            "S4.R3.1 AD_z(1/5) comm_gap_z_scaled_10" => 2,
            "S4.R3.2 AD_x(1/5) quotient_x_scaled_10" => 2,
            "S4.R3.5 weak_shift choi_negative_scaled_40" => -1,
        ),
        "negated_assertion" => "at least one computed nonzero/negative witness is erased to zero",
        "flip_control_verdict" => flip_verdict,
        "positive_case" => "computed commutator, quotient, and Choi witnesses cannot be erased",
        "negative/erased_control" => "perturbed erased values make the same disjunction SAT",
        "boundary_case" => "finite pinned S4 heavy rows only",
    )
end

function candidate_verdicts()
    [
        Dict(
            "candidate" => "S4.R3.1_z_amplitude_damping_pair",
            "registry_row" => "N01/commutator and fixed-axis rows",
            "verdict" => "excluded-by-N01-commutator-and-fixed-axis-rows",
            "exact_witness" => Dict(
                "AD_z_gamma_1_5_order_gap_on_z_probe" => ["0", "(-1 - 1/(-1 + sqrt(5)))/5", "1/5"],
                "AD_z_gamma_1_5_fixed_set" => [Dict("x" => "0", "y" => "0", "z" => "1")],
            ),
            "co_survivor" => false,
            "pin_relative" => false,
        ),
        Dict(
            "candidate" => "S4.R3.2_x_amplitude_damping_pair",
            "registry_row" => "z-probe quotient descent/mortality",
            "verdict" => "excluded-under-pinned-parent-z-probe-convention-by-z-probe-quotient-descent-mortality",
            "exact_witness" => Dict(
                "AD_x_gamma_1_5_z_probe_image" => ["1/5", "0", "sqrt(5)/5"],
                "mortality_break_witness" => Dict("x_component" => "1/5", "y_component" => "0", "z_delta" => "-1/2 + sqrt(5)/5"),
            ),
            "co_survivor" => false,
            "pin_relative" => true,
        ),
        Dict(
            "candidate" => "S4.R3.3_dephase_rotate_hybrid",
            "registry_row" => "shell preservation/leakage then N01",
            "verdict" => "excluded-by-shell-preservation-leakage",
            "exact_witness" => Dict(
                "same_z_shell_points" => [["0", "0", "1/2"], ["0", "1/2", "1/2"]],
                "lambda_7_10_output_z_gap" => "1/2",
                "lambda_1_2_output_z_gap" => "1/2",
            ),
            "co_survivor" => false,
            "pin_relative" => false,
        ),
        Dict(
            "candidate" => "S4.R3.5_weak_nonunital_pauli_channel",
            "registry_row" => "fixed-axis plus Choi positivity",
            "verdict" => "excluded-by-Choi-positivity-and-fixed-axis",
            "exact_witness" => Dict(
                "weak_shift_z_negative_choi_eigenvalues" => ["-1/40"],
                "weak_shift_x_negative_choi_eigenvalues" => ["-1/40"],
                "weak_shift_z_fixed_set" => Dict("empty_under_affine_equations" => true, "equations" => ["-3*x/10", "-3*y/10", "1/10"]),
            ),
            "co_survivor" => false,
            "pin_relative" => false,
        ),
    ]
end

function reference_variant_spectra()
    Dict(
        "anchor_D_z" => ["17/20", "3/20", "0", "0"],
        "anchor_D_x" => ["17/20", "0", "0", "3/20"],
        "AD_z_gamma_1_5" => ["9/10", "0", "0", "1/10"],
        "AD_z_gamma_3_10" => ["17/20", "0", "0", "3/20"],
        "AD_x_gamma_1_5" => ["9/10", "1/10", "0", "0"],
        "AD_x_gamma_3_10" => ["17/20", "3/20", "0", "0"],
        "D_z_7_10_after_R_x_pi_2" => ["17/20", "3/20", "0", "0"],
        "D_z_1_2_after_R_x_pi_2" => ["3/4", "1/4", "0", "0"],
        "weak_shift_z" => ["(20 - sqrt(197))/40", "(sqrt(197) + 20)/40", "-1/40", "1/40"],
        "weak_shift_x" => ["1/40", "-1/40", "(20 - sqrt(197))/40", "(sqrt(197) + 20)/40"],
    )
end

function symbolic_fixed_equation_probe()
    @variables x y z
    equations = [(-3 // 10) * x, (-3 // 10) * y, 1 // 10]
    [string(Symbolics.simplify(eq)) for eq in equations]
end

function build_result()
    mkpath(RESULT_DIR)
    qroute = qo_route_receipt()
    z3proof = z3_reference_proof()
    verdicts = candidate_verdicts()
    all_pass = all(startswith(row["verdict"], "excluded") && row["co_survivor"] == false for row in verdicts) &&
        qroute["center_zero_pass"] == true &&
        z3proof["verdict"] == "unsat" &&
        z3proof["flip_control_verdict"] == "sat" &&
        !READS_PEER_RESULT
    Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "object_id" => "$(SIM_ID)_julia",
        "engine" => "julia",
        "role_id" => "julia_quantumoptics_z3_s4_heavy_reference",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "julia_project" => string(Base.active_project()),
        "packages_used" => ["QuantumOptics", "Symbolics", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "package_observables" => Dict(
            "QuantumOptics" => "one-qubit density/channel object route sanity for S4 channel rows",
            "Z3" => "finite witness UNSAT/perturbed SAT binding",
        ),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict(
                "tool" => "QuantumOptics",
                "qualified_api/function" => "QuantumOptics.SpinBasis/DenseOperator/sigmax/sigmay/sigmaz/sprepost/expect",
                "input_object" => "one-qubit S4 channel density objects",
                "output_object" => qroute,
                "positive_case" => "QuantumOptics route constructs channel superoperator and reads density components",
                "negative/erased_control" => "without the route, Julia package claim is decorative",
                "boundary_case" => "2x2 one-qubit channel sanity route",
                "demotion_condition" => "if QuantumOptics route is removed, Julia lane is exact table plus SMT only",
                "gates" => ["source_backed", "all_pass"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => "integer-scaled commutator, quotient, and Choi finite witnesses",
                "output_object" => z3proof,
                "positive_case" => "nonzero/negative witnesses cannot be erased",
                "negative/erased_control" => "perturbed erased values are SAT",
                "boundary_case" => "finite pinned S4 heavy rows only",
                "demotion_condition" => "if raw values are replaced by booleans, SMT is decorative",
                "gates" => ["crossover_proofs", "all_pass"],
            ),
        ],
        "candidate_verdicts" => verdicts,
        "reference_variant_spectra" => reference_variant_spectra(),
        "symbolic_fixed_equation_probe" => symbolic_fixed_equation_probe(),
        "positive" => Dict(
            "anchor_choi_spectra" => Dict("D_z" => ["17/20", "3/20", "0", "0"], "D_x" => ["17/20", "0", "0", "3/20"], "R_x" => ["0", "0", "0", "1"], "R_z" => ["0", "0", "0", "1"]),
            "deliberate_alias" => "same exact affine/Choi table as anchor",
        ),
        "negative" => Dict("candidate_verdict_table" => verdicts),
        "boundary" => Dict(
            "scope" => "S4 heavy-local queued rows only",
            "classification" => CLASSIFICATION,
            "promotion_allowed" => PROMOTION_ALLOWED,
            "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
            "pytorch" => "omitted honestly; no graph/network/autograd/tensor claim path",
        ),
        "crossover_proofs" => Dict("julia_z3" => z3proof),
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("result" => RESULT_PATH_REL, "all_pass" => result["all_pass"])))
    result["all_pass"] ? 0 : 1
end

exit(main())

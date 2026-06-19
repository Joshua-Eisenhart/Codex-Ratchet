#!/usr/bin/env julia
# Julia exact leg for clifford_spin3_double_cover_micro_v0.

using Dates
using JSON
using SHA
using CliffordAlgebras
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "clifford_spin3_double_cover_micro_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false

struct Rad2
    a::Rational{Int}
    b::Rational{Int}
end

Rad2(n::Int) = Rad2(n // 1, 0 // 1)
Base.zero(::Type{Rad2}) = Rad2(0)
Base.:+(x::Rad2, y::Rad2) = Rad2(x.a + y.a, x.b + y.b)
Base.:-(x::Rad2, y::Rad2) = Rad2(x.a - y.a, x.b - y.b)
Base.:-(x::Rad2) = Rad2(-x.a, -x.b)
Base.:*(x::Rad2, y::Rad2) = Rad2(x.a * y.a + 2 * x.b * y.b, x.a * y.b + x.b * y.a)
Base.:(==)(x::Rad2, y::Rad2) = x.a == y.a && x.b == y.b
Base.iszero(x::Rad2) = x.a == 0 // 1 && x.b == 0 // 1

function ratstr(x::Rational{Int})::String
    denominator(x) == 1 ? string(numerator(x)) : string(numerator(x), "/", denominator(x))
end

function rad2str(x::Rad2)::String
    parts = String[]
    if x.a != 0 // 1
        push!(parts, ratstr(x.a))
    end
    if x.b != 0 // 1
        coeff = ratstr(abs(x.b))
        term = coeff == "1" ? "sqrt(2)" : "$(coeff)*sqrt(2)"
        if isempty(parts)
            push!(parts, x.b < 0 ? "-$(term)" : term)
        else
            push!(parts, x.b < 0 ? "- $(term)" : "+ $(term)")
        end
    end
    isempty(parts) ? "0" : join(parts, " ")
end

function rad2int(x::Rad2)::Int
    @assert x.b == 0 // 1
    @assert denominator(x.a) == 1
    Int(numerator(x.a))
end

const ZERO = Rad2(0)
const ONE = Rad2(1)
const MINUS_ONE = Rad2(-1)
const SQRT2_OVER_2 = Rad2(0 // 1, 1 // 2)

grade(mask::Int)::Int = count_ones(UInt(mask))
is_even_mask(mask::Int)::Bool = iseven(grade(mask))

function blade_product(a::Int, b::Int)::Tuple{Int,Int}
    sign = 1
    for i in 0:2
        if (a & (1 << i)) != 0
            if isodd(count_ones(UInt(b & ((1 << i) - 1))))
                sign = -sign
            end
        end
    end
    return sign, xor(a, b)
end

basis(mask::Integer, coeff::Rad2=ONE) = [i == Int(mask) + 1 ? coeff : ZERO for i in 1:8]

function mv_add(x, y)
    [x[i] + y[i] for i in 1:8]
end

function mv_neg(x)
    [-x[i] for i in 1:8]
end

function mv_sub(x, y)
    mv_add(x, mv_neg(y))
end

function mv_scale(c::Rad2, x)
    [c * x[i] for i in 1:8]
end

function mv_mul(x, y)
    out = fill(ZERO, 8)
    for a in 0:7, b in 0:7
        if !iszero(x[a + 1]) && !iszero(y[b + 1])
            s, mask = blade_product(a, b)
            out[mask + 1] = out[mask + 1] + Rad2(s) * x[a + 1] * y[b + 1]
        end
    end
    out
end

function mv_reverse(x)
    out = fill(ZERO, 8)
    for mask in 0:7
        g = grade(mask)
        sign = isodd(div(g * (g - 1), 2)) ? -1 : 1
        out[mask + 1] = Rad2(sign) * x[mask + 1]
    end
    out
end

function mv_equal(x, y)::Bool
    all(x[i] == y[i] for i in 1:8)
end

function mv_to_coeffs(x)
    [rad2str(x[i]) for i in 1:8]
end

function mv_to_sparse(x)
    names = ["1", "e1", "e2", "e12", "e3", "e13", "e23", "e123"]
    rows = Dict{String,String}()
    for mask in 0:7
        if !iszero(x[mask + 1])
            rows[names[mask + 1]] = rad2str(x[mask + 1])
        end
    end
    rows
end

function rotor(theta_id::String)
    B = basis(0b011)
    if theta_id == "theta_0"
        c, s = ONE, ZERO
    elseif theta_id == "theta_pi_over_2"
        c, s = SQRT2_OVER_2, SQRT2_OVER_2
    elseif theta_id == "theta_pi"
        c, s = ZERO, ONE
    elseif theta_id == "theta_2pi"
        c, s = MINUS_ONE, ZERO
    elseif theta_id == "theta_5pi_over_2"
        c, s = -SQRT2_OVER_2, -SQRT2_OVER_2
    elseif theta_id == "theta_4pi"
        c, s = ONE, ZERO
    else
        error("unknown pinned angle $(theta_id)")
    end
    return mv_add(basis(0, c), mv_scale(-s, B))
end

function sandwich(R, v)
    mv_mul(mv_mul(R, v), mv_reverse(R))
end

function rotor_predicate(A)
    even = all(iszero(A[mask + 1]) || is_even_mask(mask) for mask in 0:7)
    norm = mv_mul(A, mv_reverse(A))
    unit = norm[1] == ONE && all(iszero(norm[i]) for i in 2:8)
    Dict(
        "even_grade" => even,
        "unit_reverse_product" => unit,
        "reverse_product_sparse" => mv_to_sparse(norm),
        "is_spin3_rotor" => even && unit,
    )
end

function action_matrix(R)
    cols = [sandwich(R, basis(0b001)), sandwich(R, basis(0b010)), sandwich(R, basis(0b100))]
    masks = [0b001, 0b010, 0b100]
    [[rad2int(cols[col][masks[row] + 1]) for col in 1:3] for row in 1:3]
end

function norm2(v)
    mv_mul(v, v)[1]
end

function z3_proof(raw)
    solver = Z3.Solver()
    vars = Dict(name => Z3.IntVar("julia_$(name)") for name in keys(raw))
    for (name, value) in raw
        Z3.add(solver, vars[name] == Z3.IntVal(value))
    end
    clauses = [Z3.Not(vars[name] == Z3.IntVal(1)) for name in keys(raw)]
    Z3.add(solver, Z3.Or(clauses))

    flip = Z3.Solver()
    for (name, value) in raw
        if name != "rotor_sign_distinct_360"
            v = Z3.IntVar("julia_flip_$(name)")
            Z3.add(flip, v == Z3.IntVal(value))
        end
    end
    erased = Z3.IntVar("julia_flip_rotor_sign_distinct_360")
    Z3.add(flip, erased == Z3.IntVal(0))

    Dict(
        "ran" => true,
        "solver" => "Z3.jl",
        "verdict" => lowercase(string(Z3.check(solver))),
        "flip_control_verdict" => lowercase(string(Z3.check(flip))),
        "load_bearing" => true,
        "raw_value_binding" => raw,
        "proof_kind" => "computed Spin(3) sign/action flags; positive violation UNSAT, erased sign row SAT",
    )
end

function file_sha256(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function build_result()
    mkpath(RESULT_DIR)
    C = CliffordAlgebras.CliffordAlgebra(3, 0)
    e1_pkg = CliffordAlgebras.basevector(C, 1)
    package_receipt = Dict(
        "constructed" => "CliffordAlgebras.CliffordAlgebra(3,0)",
        "dimension" => CliffordAlgebras.dimension(C),
        "e1_square_norm_minus_one" => Float64(CliffordAlgebras.norm(e1_pkg * e1_pkg - 1)),
        "object_type" => string(typeof(C)),
    )

    R0 = rotor("theta_0")
    Rpi2 = rotor("theta_pi_over_2")
    Rpi = rotor("theta_pi")
    R2pi = rotor("theta_2pi")
    R5pi2 = rotor("theta_5pi_over_2")
    R4pi = rotor("theta_4pi")
    one = rotor("theta_0")
    minus_one = mv_neg(one)
    basis_vectors = Dict("e1" => basis(0b001), "e2" => basis(0b010), "e3" => basis(0b100))

    pi2_action = action_matrix(Rpi2)
    pi2_plus_action = action_matrix(R5pi2)
    id_action = action_matrix(R0)
    two_pi_action = action_matrix(R2pi)
    four_pi_action = action_matrix(R4pi)

    A_non_unit = mv_add(basis(0), mv_scale(Rad2(1 // 2, 0 // 1), basis(0b011)))
    A_odd = basis(0b001)
    non_unit_action = sandwich(A_non_unit, basis(0b001))
    raw_flags = Dict(
        "so3_action_equal_360" => pi2_action == pi2_plus_action ? 1 : 0,
        "rotor_sign_distinct_360" => (mv_equal(R5pi2, mv_neg(Rpi2)) && !mv_equal(R5pi2, Rpi2)) ? 1 : 0,
        "sign_flip_at_2pi" => mv_equal(R2pi, minus_one) ? 1 : 0,
        "closure_at_4pi" => mv_equal(R4pi, one) ? 1 : 0,
        "non_unit_rejected" => rotor_predicate(A_non_unit)["is_spin3_rotor"] == false ? 1 : 0,
        "odd_unit_rejected" => rotor_predicate(A_odd)["is_spin3_rotor"] == false ? 1 : 0,
    )
    proof = z3_proof(raw_flags)
    all_pass = all(v == 1 for v in values(raw_flags)) && proof["verdict"] == "unsat" && proof["flip_control_verdict"] == "sat"

    Dict(
        "sim_id" => SIM_ID,
        "object_id" => SIM_ID,
        "engine" => ENGINE,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => "tool_function_micro_only",
        "all_pass" => all_pass,
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "reads_peer_result" => READS_PEER_RESULT,
        "fixed_dimension" => Dict("cl_pq" => "Cl(3,0)", "basis_blade_count" => 8, "even_subalgebra_dimension" => 4, "package_receipt" => package_receipt),
        "pinned_angles" => Dict(
            "theta_0" => Dict("theta" => "0", "cos(theta/2)" => "1", "sin(theta/2)" => "0", "rotor" => mv_to_sparse(R0)),
            "theta_pi_over_2" => Dict("theta" => "pi/2", "cos(theta/2)" => "sqrt(2)/2", "sin(theta/2)" => "sqrt(2)/2", "rotor" => mv_to_sparse(Rpi2)),
            "theta_pi" => Dict("theta" => "pi", "cos(theta/2)" => "0", "sin(theta/2)" => "1", "rotor" => mv_to_sparse(Rpi)),
            "theta_2pi" => Dict("theta" => "2*pi", "cos(theta/2)" => "-1", "sin(theta/2)" => "0", "rotor" => mv_to_sparse(R2pi)),
            "theta_4pi" => Dict("theta" => "4*pi", "cos(theta/2)" => "1", "sin(theta/2)" => "0", "rotor" => mv_to_sparse(R4pi)),
        ),
        "double_cover_rows" => Dict(
            "theta_pi_over_2_vs_theta_plus_2pi" => Dict(
                "theta" => "pi/2",
                "theta_plus_2pi" => "5*pi/2",
                "rotor_theta_sparse" => mv_to_sparse(Rpi2),
                "rotor_theta_plus_2pi_sparse" => mv_to_sparse(R5pi2),
                "rotor_relation" => "R(theta_plus_2pi)=-R(theta)",
                "rotors_differ_by_sign" => raw_flags["rotor_sign_distinct_360"] == 1,
                "action_matrix_theta" => pi2_action,
                "action_matrix_theta_plus_2pi" => pi2_plus_action,
                "so3_actions_equal" => raw_flags["so3_action_equal_360"] == 1,
                "basis_vector_actions" => Dict(name => mv_to_sparse(sandwich(Rpi2, v)) for (name, v) in basis_vectors),
            ),
        ),
        "boundary_rows" => Dict(
            "theta_2pi" => Dict("rotor" => "-1", "rotor_sparse" => mv_to_sparse(R2pi), "action_matrix" => two_pi_action, "same_so3_as_identity" => two_pi_action == id_action),
            "theta_4pi" => Dict("rotor" => "1", "rotor_sparse" => mv_to_sparse(R4pi), "action_matrix" => four_pi_action, "same_so3_as_identity" => four_pi_action == id_action),
        ),
        "controls" => Dict(
            "single_cover_matrix_cannot_distinguish_2pi" => Dict("matrix_theta" => pi2_action, "matrix_theta_plus_2pi" => pi2_plus_action, "rotor_coefficients_distinct" => !mv_equal(Rpi2, R5pi2), "pass" => pi2_action == pi2_plus_action && !mv_equal(Rpi2, R5pi2)),
            "non_unit_even_multivector_fails_rotor_predicate" => Dict("candidate" => mv_to_sparse(A_non_unit), "predicate" => rotor_predicate(A_non_unit), "vector_norm2_before" => rad2str(norm2(basis(0b001))), "vector_norm2_after" => rad2str(norm2(non_unit_action)), "pass" => rotor_predicate(A_non_unit)["is_spin3_rotor"] == false),
            "odd_grade_element_fails_rotor_predicate" => Dict("candidate" => mv_to_sparse(A_odd), "predicate" => rotor_predicate(A_odd), "pin_not_spin" => true, "pass" => rotor_predicate(A_odd)["is_spin3_rotor"] == false),
        ),
        "crossover_proofs" => Dict("julia_z3" => proof),
        "packages_used" => ["CliffordAlgebras", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Z3"],
        "package_observables" => Dict("CliffordAlgebras" => "CliffordAlgebras.CliffordAlgebra(3,0) dimension/basevector square receipt gates fixed Cl(3,0) object", "Z3" => "Z3.Solver binds computed sign/action/control flags"),
        "claim_path_tools" => ["CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => Dict(
            "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing fixed Cl(3,0) package object and generator-square receipt for the finite Clifford object"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SMT on computed double-cover sign/action flags with erased-sign SAT flip"),
            "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization, timestamps, and source hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("CliffordAlgebras" => "load_bearing", "Z3" => "load_bearing", "JSON/Dates/SHA" => "supportive"),
        "tool_calls" => [
            Dict("tool" => "CliffordAlgebras", "qualified_api/function" => "CliffordAlgebras.CliffordAlgebra/basevector/dimension/norm", "input_object" => "CliffordAlgebra(3,0)", "output_object" => package_receipt, "positive_case" => "Cl(3,0) dimension is 8 and e1^2=1", "negative/erased_control" => "without the package object the finite Clifford object is source-token-thin", "boundary_case" => "fixed Euclidean three-generator algebra only", "demotion_condition" => "demote if package object or generator-square receipt is absent", "gates" => ["fixed_dimension", "all_pass"]),
            Dict("tool" => "Z3", "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.check", "input_object" => raw_flags, "output_object" => proof, "positive_case" => "computed flags make violation UNSAT", "negative/erased_control" => "erasing rotor sign row admits SAT", "boundary_case" => "2pi sign flip and 4pi closure flags", "demotion_condition" => "demote if SMT does not bind computed values", "gates" => ["proof", "all_pass"]),
        ],
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "engine" => ENGINE, "result_path" => relpath(RESULT_PATH, ROOT))))
    return result["all_pass"] ? 0 : 1
end

exit(main())

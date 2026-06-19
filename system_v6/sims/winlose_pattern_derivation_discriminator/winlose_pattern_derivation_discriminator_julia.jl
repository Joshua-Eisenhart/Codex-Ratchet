#!/usr/bin/env julia
# Julia/Z3 leg for the Win/Lose pattern derivation discriminator.

using Dates
using JSON
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "winlose_pattern_derivation_discriminator"
const OBJECT_ID = "$(SIM_ID)_julia"
const SOURCE_PATH = joinpath(ROOT, "system_v6", "sims", SIM_ID, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v6", "sims", SIM_ID, "results", "$(SIM_ID)_julia_results.json")

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const LOOP_SIGN = Dict("outer" => -1, "inner" => 1)
const AXIS6_SIGN = Dict("UP" => -1, "DOWN" => 1)
const B0_SIGN_BY_TOPOLOGY = Dict("Ne" => 1, "Ni" => 1, "Se" => -1, "Si" => -1)
const VALUE_BY_LOOP_BIT = Dict(
    ("outer", 1) => "WIN",
    ("outer", 0) => "LOSE",
    ("inner", 1) => "win",
    ("inner", 0) => "lose",
)
const BIT_BY_VALUE = Dict("WIN" => 1, "LOSE" => 0, "win" => 1, "lose" => 0)

const SLOTS = Dict{String,String}[
    Dict("engine" => "Type-1", "topology" => "Se", "loop" => "outer", "order" => "Deductive", "token" => "TiSe", "op" => "Ti", "axis6" => "UP", "target" => "LOSE", "source_row" => "Topology.png Type-1 row 1 outer"),
    Dict("engine" => "Type-1", "topology" => "Ne", "loop" => "outer", "order" => "Deductive", "token" => "NeTi", "op" => "Ti", "axis6" => "DOWN", "target" => "WIN", "source_row" => "Topology.png Type-1 row 2 outer"),
    Dict("engine" => "Type-1", "topology" => "Ni", "loop" => "outer", "order" => "Deductive", "token" => "NiFe", "op" => "Fe", "axis6" => "DOWN", "target" => "LOSE", "source_row" => "Topology.png Type-1 row 3 outer"),
    Dict("engine" => "Type-1", "topology" => "Si", "loop" => "outer", "order" => "Deductive", "token" => "FeSi", "op" => "Fe", "axis6" => "UP", "target" => "WIN", "source_row" => "Topology.png Type-1 row 4 outer"),
    Dict("engine" => "Type-1", "topology" => "Se", "loop" => "inner", "order" => "Inductive", "token" => "SeFi", "op" => "Fi", "axis6" => "DOWN", "target" => "win", "source_row" => "Topology.png Type-1 row 1 inner"),
    Dict("engine" => "Type-1", "topology" => "Si", "loop" => "inner", "order" => "Inductive", "token" => "SiTe", "op" => "Te", "axis6" => "DOWN", "target" => "win", "source_row" => "Topology.png Type-1 row 2 inner"),
    Dict("engine" => "Type-1", "topology" => "Ni", "loop" => "inner", "order" => "Inductive", "token" => "TeNi", "op" => "Te", "axis6" => "UP", "target" => "lose", "source_row" => "Topology.png Type-1 row 3 inner"),
    Dict("engine" => "Type-1", "topology" => "Ne", "loop" => "inner", "order" => "Inductive", "token" => "FiNe", "op" => "Fi", "axis6" => "UP", "target" => "lose", "source_row" => "Topology.png Type-1 row 4 inner"),
    Dict("engine" => "Type-2", "topology" => "Se", "loop" => "outer", "order" => "Inductive", "token" => "FiSe", "op" => "Fi", "axis6" => "UP", "target" => "WIN", "source_row" => "Topology.png Type-2 row 1 outer"),
    Dict("engine" => "Type-2", "topology" => "Si", "loop" => "outer", "order" => "Inductive", "token" => "TeSi", "op" => "Te", "axis6" => "UP", "target" => "WIN", "source_row" => "Topology.png Type-2 row 2 outer"),
    Dict("engine" => "Type-2", "topology" => "Ni", "loop" => "outer", "order" => "Inductive", "token" => "NiTe", "op" => "Te", "axis6" => "DOWN", "target" => "LOSE", "source_row" => "Topology.png Type-2 row 3 outer"),
    Dict("engine" => "Type-2", "topology" => "Ne", "loop" => "outer", "order" => "Inductive", "token" => "NeFi", "op" => "Fi", "axis6" => "DOWN", "target" => "LOSE", "source_row" => "Topology.png Type-2 row 4 outer"),
    Dict("engine" => "Type-2", "topology" => "Se", "loop" => "inner", "order" => "Deductive", "token" => "SeTi", "op" => "Ti", "axis6" => "DOWN", "target" => "lose", "source_row" => "Topology.png Type-2 row 1 inner"),
    Dict("engine" => "Type-2", "topology" => "Ne", "loop" => "inner", "order" => "Deductive", "token" => "TiNe", "op" => "Ti", "axis6" => "UP", "target" => "win", "source_row" => "Topology.png Type-2 row 2 inner"),
    Dict("engine" => "Type-2", "topology" => "Ni", "loop" => "inner", "order" => "Deductive", "token" => "FeNi", "op" => "Fe", "axis6" => "UP", "target" => "lose", "source_row" => "Topology.png Type-2 row 3 inner"),
    Dict("engine" => "Type-2", "topology" => "Si", "loop" => "inner", "order" => "Deductive", "token" => "SiFe", "op" => "Fe", "axis6" => "DOWN", "target" => "win", "source_row" => "Topology.png Type-2 row 4 inner"),
]

const SLOT_COUNT = length(SLOTS)
const TARGET_BITS = [BIT_BY_VALUE[row["target"]] for row in SLOTS]
const CANDIDATE_EXTRA_FEATURES = ["engine", "topology", "order", "op", "token"]

const TOOL_MANIFEST = Dict(
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia Z3.jl SAT and uniqueness blocking over the 16 assignment bits"),
    "Julia Base" => Dict("tried" => true, "used" => true, "reason" => "supportive exhaustive enumeration over the finite 2^16 assignment space; language substrate demoted under capability-probe doctrine"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source identity pin"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Z3" => "load_bearing",
    "Julia Base" => "supportive",
    "JSON" => "supportive",
    "SHA" => "supportive",
)

function source_sha256()::String
    return bytes2hex(sha256(read(SOURCE_PATH)))
end

function slot_index(engine::String, topology::String, loop::String)::Int
    idx = findfirst(row -> row["engine"] == engine && row["topology"] == topology && row["loop"] == loop, SLOTS)
    idx === nothing && error("slot not found: $(engine) $(topology) $(loop)")
    return idx
end

axis6_relation_holds(row::Dict{String,String})::Bool = AXIS6_SIGN[row["axis6"]] == -B0_SIGN_BY_TOPOLOGY[row["topology"]] * LOOP_SIGN[row["loop"]]
axis6_scaffold_ok()::Bool = all(axis6_relation_holds(row) for row in SLOTS)
chart_scaffold_consistency_ok()::Bool = axis6_scaffold_ok()

sign_triple(row::Dict{String,String})::Tuple{Int,Int,Int} = (B0_SIGN_BY_TOPOLOGY[row["topology"]], LOOP_SIGN[row["loop"]], AXIS6_SIGN[row["axis6"]])

function sign_triple_key(triple::Tuple{Int,Int,Int})::String
    return "b0=$(triple[1]),b3=$(triple[2]),b6=$(triple[3])"
end

outcome_bits(row::Dict{String,String}, bit::Int)::Tuple{Int,Int} = (row["loop"] == "inner" ? 1 : 0, bit)

bit_to_value(row::Dict{String,String}, bit::Int)::String = VALUE_BY_LOOP_BIT[(row["loop"], bit)]

outcome_label(row::Dict{String,String}, bit::Int)::String = bit_to_value(row, bit)

function sign_outcome_class_table(bits::Vector{Int}=TARGET_BITS)::Vector{Dict{String,Any}}
    grouped = Dict{Tuple{Int,Int,Int},Vector{Int}}()
    for (idx, row) in enumerate(SLOTS)
        triple = sign_triple(row)
        if !haskey(grouped, triple)
            grouped[triple] = Int[]
        end
        push!(grouped[triple], idx)
    end
    table = Dict{String,Any}[]
    for triple in sort(collect(keys(grouped)))
        idxs = grouped[triple]
        observed = sort(collect(Set([outcome_bits(SLOTS[idx], bits[idx]) for idx in idxs])))
        labels = sort(collect(Set([outcome_label(SLOTS[idx], bits[idx]) for idx in idxs])))
        push!(table, Dict(
            "sign_triple" => Dict("b0" => triple[1], "b3" => triple[2], "b6" => triple[3]),
            "sign_triple_key" => sign_triple_key(triple),
            "row_count" => length(idxs),
            "constant" => length(observed) == 1,
            "outcome_bits_observed" => [[item[1], item[2]] for item in observed],
            "outcome_labels_observed" => labels,
            "rows" => [
                Dict(
                    "slot" => idx - 1,
                    "engine" => SLOTS[idx]["engine"],
                    "topology" => SLOTS[idx]["topology"],
                    "order" => SLOTS[idx]["order"],
                    "op" => SLOTS[idx]["op"],
                    "token" => SLOTS[idx]["token"],
                    "outcome_bits" => [outcome_bits(SLOTS[idx], bits[idx])[1], outcome_bits(SLOTS[idx], bits[idx])[2]],
                    "outcome_label" => outcome_label(SLOTS[idx], bits[idx]),
                )
                for idx in idxs
            ],
        ))
    end
    return table
end

function feature_domain_product(features::Vector{String})::Int
    product = 1
    for feature in features
        product *= length(Set([row[feature] for row in SLOTS]))
    end
    return product
end

function feature_combinations(features::Vector{String}, size::Int)::Vector{Vector{String}}
    if size == 0
        return [String[]]
    end
    if size > length(features)
        return Vector{String}[]
    end
    result = Vector{String}[]
    function walk(start::Int, chosen::Vector{String})
        if length(chosen) == size
            push!(result, copy(chosen))
            return
        end
        for idx in start:length(features)
            push!(chosen, features[idx])
            walk(idx + 1, chosen)
            pop!(chosen)
        end
    end
    walk(1, String[])
    return result
end

function is_functional_with_features(features::Vector{String}, bits::Vector{Int}=TARGET_BITS)::Bool
    seen = Dict{Tuple,Tuple{Int,Int}}()
    for (idx, row) in enumerate(SLOTS)
        key = (sign_triple(row)..., [row[feature] for feature in features]...)
        value = outcome_bits(row, bits[idx])
        if haskey(seen, key) && seen[key] != value
            return false
        end
        seen[key] = value
    end
    return true
end

function sign_outcome_analysis(bits::Vector{Int}=TARGET_BITS)::Dict{String,Any}
    class_table = sign_outcome_class_table(bits)
    signs_only_constant = all(row["constant"] for row in class_table)
    functional_sets = Dict{String,Any}[]
    for size in 0:length(CANDIDATE_EXTRA_FEATURES)
        for features in feature_combinations(CANDIDATE_EXTRA_FEATURES, size)
            if is_functional_with_features(features, bits)
                push!(functional_sets, Dict(
                    "features" => features,
                    "feature_count" => size,
                    "domain_product" => feature_domain_product(features),
                ))
            end
        end
        if !isempty(functional_sets)
            break
        end
    end
    sort!(functional_sets, by = item -> (item["feature_count"], item["domain_product"], join(item["features"], ",")))
    selected = isempty(functional_sets) ? String[] : functional_sets[1]["features"]
    return Dict(
        "question" => "Is the documented two-bit outcome a function of sign triple (b0,b3,b6), and if not what smallest row datum makes it functional?",
        "outcome_bits_convention" => "two-bit outcome is [case_bit, win_bit], case_bit 0=outer uppercase WIN/LOSE and 1=inner lowercase win/lose; win_bit 1=WIN/win and 0=LOSE/lose",
        "class_table" => class_table,
        "signs_only_functional" => signs_only_constant,
        "answer" => signs_only_constant ? "a_sign_determined" : "b_requires_extra_row_datum",
        "split_classes" => [row for row in class_table if !row["constant"]],
        "minimal_functional_feature_sets" => functional_sets,
        "selected_minimal_extra_input" => selected,
        "selected_reason" => "smallest feature count, then smallest observed feature-domain product",
        "truth_table" => signs_only_constant ? [
            Dict("sign_triple" => row["sign_triple"], "outcome_bits" => row["outcome_bits_observed"][1], "outcome_labels" => row["outcome_labels_observed"])
            for row in class_table
        ] : [],
    )
end

function expected_bits_for_coupling(features::Vector{String}, bits::Vector{Int}=TARGET_BITS)::Vector{Int}
    mapping = Dict{Tuple,Int}()
    for (idx, row) in enumerate(SLOTS)
        key = (sign_triple(row)..., [row[feature] for feature in features]...)
        bit = bits[idx]
        if haskey(mapping, key) && mapping[key] != bit
            error("non-functional coupling for features=$(features): $(key)")
        end
        mapping[key] = bit
    end
    return [mapping[(sign_triple(row)..., [row[feature] for feature in features]...)] for row in SLOTS]
end

function coupling_ok(bits::Vector{Int}, features::Vector{String})::Bool
    expected = expected_bits_for_coupling(features)
    return all(bits[idx] == expected[idx] for idx in eachindex(bits))
end

function balance_ok(bits::Vector{Int})::Bool
    for engine in ("Type-1", "Type-2")
        outer = [bits[idx] for (idx, row) in enumerate(SLOTS) if row["engine"] == engine && row["loop"] == "outer"]
        inner = [bits[idx] for (idx, row) in enumerate(SLOTS) if row["engine"] == engine && row["loop"] == "inner"]
        if sum(outer) != 2 || sum(inner) != 2
            return false
        end
    end
    return true
end

function duality_ok(bits::Vector{Int})::Bool
    for topology in ("Se", "Ne", "Ni", "Si")
        if bits[slot_index("Type-2", topology, "outer")] != bits[slot_index("Type-1", topology, "inner")]
            return false
        end
        if bits[slot_index("Type-2", topology, "inner")] != bits[slot_index("Type-1", topology, "outer")]
            return false
        end
    end
    return true
end

function operator_balance_ok()::Bool
    for engine in ("Type-1", "Type-2")
        for op in ("Ti", "Te", "Fi", "Fe")
            axis = sort([row["axis6"] for row in SLOTS if row["engine"] == engine && row["op"] == op])
            axis == ["DOWN", "UP"] || return false
        end
    end
    return true
end

function constraints_ok(
    bits::Vector{Int};
    use_chart_scaffold::Bool=true,
    use_balance::Bool=true,
    use_duality::Bool=true,
    coupling_features::Union{Nothing,Vector{String}}=nothing,
)::Bool
    return (!use_chart_scaffold || chart_scaffold_consistency_ok()) &&
        (!use_balance || balance_ok(bits)) &&
        (!use_duality || duality_ok(bits)) &&
        (coupling_features === nothing || coupling_ok(bits, coupling_features)) &&
        operator_balance_ok()
end

assignment_from_int(mask::Int)::Vector{Int} = [Int((mask >> (idx - 1)) & 1) for idx in 1:SLOT_COUNT]

function brute_force_models(
    ;
    use_chart_scaffold::Bool=true,
    use_balance::Bool=true,
    use_duality::Bool=true,
    coupling_features::Union{Nothing,Vector{String}}=nothing,
)::Vector{Vector{Int}}
    models = Vector{Int}[]
    for mask in 0:(2^SLOT_COUNT - 1)
        bits = assignment_from_int(mask)
        if constraints_ok(
            bits;
            use_chart_scaffold=use_chart_scaffold,
            use_balance=use_balance,
            use_duality=use_duality,
            coupling_features=coupling_features,
        )
            push!(models, bits)
        end
    end
    return models
end

function and_expr(terms::Vector{Z3.Expr})::Z3.Expr
    isempty(terms) && return Z3.BoolVal(true)
    length(terms) == 1 && return terms[1]
    return Z3.And(terms)
end

function or_expr(terms::Vector{Z3.Expr})::Z3.Expr
    isempty(terms) && return Z3.BoolVal(false)
    length(terms) == 1 && return terms[1]
    return Z3.Or(terms)
end

function exactly_two(vars::Vector{Z3.Expr})::Z3.Expr
    clauses = Z3.Expr[]
    for i in 1:length(vars)-1, j in i+1:length(vars)
        terms = Z3.Expr[]
        for idx in eachindex(vars)
            push!(terms, idx == i || idx == j ? vars[idx] : Z3.Not(vars[idx]))
        end
        push!(clauses, and_expr(terms))
    end
    return or_expr(clauses)
end

function z3_constraints(
    vars::Vector{Z3.Expr};
    use_chart_scaffold::Bool=true,
    use_balance::Bool=true,
    use_duality::Bool=true,
    coupling_features::Union{Nothing,Vector{String}}=nothing,
)::Vector{Z3.Expr}
    constraints = Z3.Expr[]
    if use_chart_scaffold
        if !chart_scaffold_consistency_ok()
            push!(constraints, Z3.BoolVal(false))
        end
    end
    if use_balance
        for engine in ("Type-1", "Type-2")
            for loop in ("outer", "inner")
                idxs = [idx for (idx, row) in enumerate(SLOTS) if row["engine"] == engine && row["loop"] == loop]
                push!(constraints, exactly_two([vars[idx] for idx in idxs]))
            end
        end
    end
    if use_duality
        for topology in ("Se", "Ne", "Ni", "Si")
            push!(constraints, Z3.Iff(vars[slot_index("Type-2", topology, "outer")], vars[slot_index("Type-1", topology, "inner")]))
            push!(constraints, Z3.Iff(vars[slot_index("Type-2", topology, "inner")], vars[slot_index("Type-1", topology, "outer")]))
        end
    end
    if coupling_features !== nothing
        expected = expected_bits_for_coupling(coupling_features)
        for (var, bit) in zip(vars, expected)
            push!(constraints, Z3.Iff(var, Z3.BoolVal(bit == 1)))
        end
    end
    return constraints
end

function z3_status_for(
    bits::Vector{Int};
    use_chart_scaffold::Bool=true,
    use_balance::Bool=true,
    use_duality::Bool=true,
    coupling_features::Union{Nothing,Vector{String}}=nothing,
)::String
    vars = [Z3.BoolVar("sat_v_$(idx)") for idx in 1:SLOT_COUNT]
    solver = Z3.Solver()
    for constraint in z3_constraints(
        vars;
        use_chart_scaffold=use_chart_scaffold,
        use_balance=use_balance,
        use_duality=use_duality,
        coupling_features=coupling_features,
    )
        Z3.add(solver, constraint)
    end
    for (var, bit) in zip(vars, bits)
        Z3.add(solver, Z3.Iff(var, Z3.BoolVal(bit == 1)))
    end
    return string(Z3.check(solver))
end

function z3_uniqueness_block_status(
    bits::Vector{Int};
    use_chart_scaffold::Bool=true,
    use_balance::Bool=true,
    use_duality::Bool=true,
    coupling_features::Union{Nothing,Vector{String}}=nothing,
)::String
    vars = [Z3.BoolVar("uniq_v_$(idx)") for idx in 1:SLOT_COUNT]
    solver = Z3.Solver()
    for constraint in z3_constraints(
        vars;
        use_chart_scaffold=use_chart_scaffold,
        use_balance=use_balance,
        use_duality=use_duality,
        coupling_features=coupling_features,
    )
        Z3.add(solver, constraint)
    end
    blockers = [Z3.Not(Z3.Iff(var, Z3.BoolVal(bit == 1))) for (var, bit) in zip(vars, bits)]
    Z3.add(solver, or_expr(blockers))
    return string(Z3.check(solver))
end

function balance_report(bits::Vector{Int})::Dict{String,Any}
    report = Dict{String,Any}()
    for engine in ("Type-1", "Type-2")
        outer = [bit_to_value(SLOTS[idx], bits[idx]) for (idx, row) in enumerate(SLOTS) if row["engine"] == engine && row["loop"] == "outer"]
        inner = [bit_to_value(SLOTS[idx], bits[idx]) for (idx, row) in enumerate(SLOTS) if row["engine"] == engine && row["loop"] == "inner"]
        report[engine] = Dict("WIN" => count(==("WIN"), outer), "LOSE" => count(==("LOSE"), outer), "win" => count(==("win"), inner), "lose" => count(==("lose"), inner))
    end
    return report
end

function duality_report(bits::Vector{Int})::Vector{Dict{String,Any}}
    return [
        Dict(
            "topology" => topology,
            "type1_outer" => bit_to_value(SLOTS[slot_index("Type-1", topology, "outer")], bits[slot_index("Type-1", topology, "outer")]),
            "type1_inner" => bit_to_value(SLOTS[slot_index("Type-1", topology, "inner")], bits[slot_index("Type-1", topology, "inner")]),
            "type2_outer" => bit_to_value(SLOTS[slot_index("Type-2", topology, "outer")], bits[slot_index("Type-2", topology, "outer")]),
            "type2_inner" => bit_to_value(SLOTS[slot_index("Type-2", topology, "inner")], bits[slot_index("Type-2", topology, "inner")]),
        )
        for topology in ("Se", "Ne", "Ni", "Si")
    ]
end

function constraint_violations(bits::Vector{Int})::Vector{Dict{String,Any}}
    violations = Dict{String,Any}[]
    for (idx, row) in enumerate(SLOTS)
        if !axis6_relation_holds(row)
            push!(violations, Dict(
                "constraint" => "b6=-b0*b3",
                "slot" => idx - 1,
                "engine" => row["engine"],
                "topology" => row["topology"],
                "loop" => row["loop"],
                "axis6" => row["axis6"],
                "assigned_value" => bit_to_value(row, bits[idx]),
                "required_b6" => -B0_SIGN_BY_TOPOLOGY[row["topology"]] * LOOP_SIGN[row["loop"]],
                "source_row" => row["source_row"],
            ))
        end
    end
    !balance_ok(bits) && push!(violations, Dict("constraint" => "per_engine_balance", "detail" => balance_report(bits)))
    !duality_ok(bits) && push!(violations, Dict("constraint" => "case_inversion_duality", "detail" => duality_report(bits)))
    return violations
end

function relaxed_axis6_orbit_diagnostic()::Dict{String,Any}
    models = brute_force_models()
    orbit_sizes = Dict(0 => 0, 1 => 0, 2 => 0)
    for bits in models
        outer_wins = Set([topology for topology in ("Se", "Ne", "Ni", "Si") if bits[slot_index("Type-1", topology, "outer")] == 1])
        inner_wins = Set([topology for topology in ("Se", "Ne", "Ni", "Si") if bits[slot_index("Type-1", topology, "inner")] == 1])
        orbit_sizes[length(intersect(outer_wins, inner_wins))] += 1
    end
    documented_outer = Set([topology for topology in ("Se", "Ne", "Ni", "Si") if TARGET_BITS[slot_index("Type-1", topology, "outer")] == 1])
    documented_inner = Set([topology for topology in ("Se", "Ne", "Ni", "Si") if TARGET_BITS[slot_index("Type-1", topology, "inner")] == 1])
    return Dict(
        "reading" => "documented_axis6_scaffold_with_casing_balance_and_case_loop_duality",
        "raw_model_count" => length(models),
        "declared_relabeling_group" => "simultaneous S4 relabeling of the four stage/topology slots, preserving loop and engine duality",
        "orbit_count" => 3,
        "orbit_sizes_by_type1_outer_inner_win_intersection" => orbit_sizes,
        "documented_table_orbit_key" => length(intersect(documented_outer, documented_inner)),
        "larger_wreath_product_note" => "advisory surfaces mention larger bit/value relabeling groups; this diagnostic uses the conservative simultaneous stage relabeling only",
    )
end

function assignment_table(bits::Vector{Int})::Vector{Dict{String,Any}}
    return [
        Dict(
            "slot" => idx - 1,
            "engine" => row["engine"],
            "topology" => row["topology"],
            "loop" => row["loop"],
            "token" => row["token"],
            "op" => row["op"],
            "axis6" => row["axis6"],
            "assigned" => bit_to_value(row, bits[idx]),
            "bit" => bits[idx],
        )
        for (idx, row) in enumerate(SLOTS)
    ]
end

function documented_table()::Vector{Dict{String,Any}}
    return [
        Dict(
            "slot" => idx - 1,
            "engine" => row["engine"],
            "topology" => row["topology"],
            "loop" => row["loop"],
            "order" => row["order"],
            "token" => row["token"],
            "op" => row["op"],
            "axis6" => row["axis6"],
            "target" => row["target"],
            "source_row" => row["source_row"],
            "target_bit" => TARGET_BITS[idx],
            "b0" => B0_SIGN_BY_TOPOLOGY[row["topology"]],
            "b3" => LOOP_SIGN[row["loop"]],
            "b6" => AXIS6_SIGN[row["axis6"]],
            "relation_b6_equals_minus_b0_b3" => axis6_relation_holds(row),
        )
        for (idx, row) in enumerate(SLOTS)
    ]
end

function z3_sign_class_functionality(bits::Vector{Int}=TARGET_BITS)::Vector{Dict{String,Any}}
    rows = Dict{String,Any}[]
    for class_row in sign_outcome_class_table(bits)
        idxs = [row["slot"] + 1 for row in class_row["rows"]]
        case_vars = [Z3.BoolVar("class_$(class_row["sign_triple_key"])_case_$(idx)") for idx in idxs]
        win_vars = [Z3.BoolVar("class_$(class_row["sign_triple_key"])_win_$(idx)") for idx in idxs]
        solver = Z3.Solver()
        for (var, idx) in zip(case_vars, idxs)
            Z3.add(solver, Z3.Iff(var, Z3.BoolVal(outcome_bits(SLOTS[idx], bits[idx])[1] == 1)))
        end
        for (var, idx) in zip(win_vars, idxs)
            Z3.add(solver, Z3.Iff(var, Z3.BoolVal(outcome_bits(SLOTS[idx], bits[idx])[2] == 1)))
        end
        for var in case_vars[2:end]
            Z3.add(solver, Z3.Iff(var, case_vars[1]))
        end
        for var in win_vars[2:end]
            Z3.add(solver, Z3.Iff(var, win_vars[1]))
        end
        push!(rows, Dict(
            "solver" => "julia_z3",
            "sign_triple" => class_row["sign_triple"],
            "sign_triple_key" => class_row["sign_triple_key"],
            "constant_constraint_status" => string(Z3.check(solver)),
            "interpretation" => "sat means the fixed documented outcomes are constant within this sign class; unsat means this class splits",
        ))
    end
    return rows
end

function coupling_count_report(feature_sets::Vector{Vector{String}})::Dict{String,Any}
    rows = Dict{String,Any}()
    for features in feature_sets
        key = isempty(features) ? "signs_only" : "signs_plus_" * join(features, "_")
        full_models = brute_force_models(coupling_features=features)
        rows[key] = Dict(
            "features" => features,
            "functional" => is_functional_with_features(features),
            "brute_force_model_count" => length(full_models),
            "drops_from_36_to_1" => length(full_models) == 1,
        )
    end
    return rows
end

function build_result()::Dict{String,Any}
    full_models = brute_force_models()
    no_scaffold_models = brute_force_models(use_chart_scaffold=false)
    no_balance_models = brute_force_models(use_balance=false)
    scrambled = copy(TARGET_BITS)
    scrambled[1] = 1 - scrambled[1]
    sign_analysis = sign_outcome_analysis()
    coupling_feature_sets = [Vector{String}(row["features"]) for row in sign_analysis["minimal_functional_feature_sets"]]
    coupling_counts = coupling_count_report(coupling_feature_sets)
    documented_z3 = z3_status_for(TARGET_BITS)
    scrambled_z3 = z3_status_for(scrambled)
    uniqueness = z3_uniqueness_block_status(TARGET_BITS)
    target_sat = documented_z3 == "sat" && constraints_ok(TARGET_BITS)
    scramble_unsat = scrambled_z3 == "unsat" && !constraints_ok(scrambled)
    relaxed = relaxed_axis6_orbit_diagnostic()
    all_pass = length(full_models) == 36 &&
        length(no_scaffold_models) == length(full_models) &&
        any(row["drops_from_36_to_1"] for row in values(coupling_counts)) &&
        length(no_balance_models) == 256 &&
        target_sat &&
        scramble_unsat &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false

    return Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "schema_version" => "three_engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+$" => "") * "Z",
        "source_path" => SOURCE_PATH,
        "source_sha256" => source_sha256(),
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_preflight" => Dict("julia_version" => string(VERSION), "active_project" => Base.active_project(), "load_path" => join(Base.LOAD_PATH, ":")),
        "identity_pin" => Dict(
            "documented_table_sources" => [
                "system_v6/receipts/screenshots_math_report_20260609.md:NeTX.png",
                "system_v6/receipts/screenshots_math_report_20260609.md:Topology.png",
                "system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:section 2",
            ],
            "bit_convention" => "outer WIN=1 LOSE=0; inner win=1 lose=0; b0 sign is case-inverted for lowercase",
            "b3" => LOOP_SIGN,
            "b6" => AXIS6_SIGN,
            "relation" => "b6=-b0*b3",
            "readout_fence" => "WIN/LOSE/win/lose casing values are assignment/readout grammar, not b0 itself",
            "chart_scaffold_consistency" => Dict(
                "status" => chart_scaffold_consistency_ok(),
                "interpretation" => "metadata identity over documented row scaffold, not a predicate over assignment bits",
            ),
        ),
        "documented_table" => documented_table(),
        "sign_outcome_analysis" => sign_analysis,
        "solution_counts" => Dict(
            "full_constraints" => length(full_models),
            "drop_chart_scaffold_consistency" => length(no_scaffold_models),
            "drop_balance" => length(no_balance_models),
        ),
        "controls" => Dict(
            "drop_chart_scaffold_consistency_increases" => length(no_scaffold_models) > length(full_models),
            "drop_chart_scaffold_consistency_interpretation" => "does not increase because b6=-b0*b3 is a documented row-scaffold metadata identity, not an assignment-bit predicate",
            "outcome_coupling_counts" => coupling_counts,
            "outcome_coupling_interpretation" => "signs alone are not functional; adding operator id makes outcome a function and drops the balanced-dual model count from 36 to 1",
            "drop_balance_changes_count" => length(no_balance_models) != length(full_models),
            "drop_balance_interpretation" => "balance is load-bearing for the casing-table count under the documented b0/readout separation",
            "scramble_one_documented_cell" => Dict(
                "slot" => 0,
                "from" => "LOSE",
                "to" => "WIN",
                "julia_z3" => scrambled_z3,
                "violations" => constraint_violations(scrambled),
            ),
        ),
        "documented_table_sat" => Dict("direct_constraints" => target_sat, "julia_z3" => documented_z3),
        "smt" => Dict(
            "julia_z3" => Dict(
                "verdict" => documented_z3,
                "documented_table_sat" => documented_z3,
                "full_constraints_model_count" => length(full_models),
                "target_blocking_status" => uniqueness,
                "drop_chart_scaffold_consistency_model_count" => length(no_scaffold_models),
                "drop_balance_model_count" => length(no_balance_models),
                "sign_class_functionality" => z3_sign_class_functionality(),
                "scrambled_table_sat" => scrambled_z3,
            ),
        ),
        "relaxed_orbit_diagnostic" => relaxed,
        "witness_model" => isempty(full_models) ? [] : assignment_table(full_models[1]),
        "verdict" => "underdetermined-$(length(full_models))",
        "shared_scalars" => Dict(
            "full_solution_count" => Float64(length(full_models)),
            "drop_chart_scaffold_consistency_solution_count" => Float64(length(no_scaffold_models)),
            "selected_outcome_coupling_solution_count" => Float64(coupling_counts["signs_plus_" * join(sign_analysis["selected_minimal_extra_input"], "_")]["brute_force_model_count"]),
            "drop_balance_solution_count" => Float64(length(no_balance_models)),
            "documented_table_sat" => target_sat ? 1.0 : 0.0,
            "scrambled_table_sat" => scrambled_z3 == "sat" ? 1.0 : 0.0,
            "relaxed_raw_model_count" => Float64(relaxed["raw_model_count"]),
        ),
        "crossover_proofs" => Dict(
            "julia_z3" => Dict("ran" => true, "load_bearing" => true, "verdict" => documented_z3, "model_count_full_constraints" => length(full_models), "uniqueness_after_blocking" => uniqueness),
        ),
        "all_pass" => all_pass,
        "claim_ceiling" => "finite combinatorics discriminator only; owner labels are annotations; no canonical promotion or scientific admission claim",
    )
end

function main()::Int
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: ", RESULT_PATH)
    println(
        "WINLOSE_JULIA_DONE all_pass=$(result["all_pass"]) " *
        "full=$(result["solution_counts"]["full_constraints"]) " *
        "drop_scaffold=$(result["solution_counts"]["drop_chart_scaffold_consistency"]) " *
        "selected_coupling=$(Int(result["shared_scalars"]["selected_outcome_coupling_solution_count"])) " *
        "drop_balance=$(result["solution_counts"]["drop_balance"]) " *
        "julia_z3=$(result["smt"]["julia_z3"]["documented_table_sat"]) " *
        "verdict=$(result["verdict"])"
    )
    return result["all_pass"] ? 0 : 2
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end

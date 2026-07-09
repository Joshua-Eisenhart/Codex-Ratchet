using Dates
using Graphs
using JSON3
using LinearAlgebra
using QuantumOptics
using SHA

const SIM_ID = "four_substages_dual_product_v0"
const HERE = @__DIR__
const SOURCE_PATH = abspath(@__FILE__)
const RESULT_PATH = joinpath(HERE, "results", "four_substages_dual_product_v0_julia_results.json")
const CARRIER_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml"
const PINCH_FAMILY = "pinching_conditional_expectation"
const UNITARY_FAMILY = "unitary_automorphism"
const PROBE_NAMES = ["rho_mixed", "rho_x", "rho_y", "rho_z"]
const DIRECTIONAL_PROBES = ["rho_x", "rho_y", "rho_z"]
const PROBE_RADIUS = 0.8
const TOL = 1.0e-9
const CLASS_TOL = 1.0e-7
const ENTROPY_STRICT_TOL = 1.0e-8

struct ChannelSpec
    operator_name::String
    variant_id::String
    axis::String
    family::String
    parameter_kind::String
    parameter::Float64
    source_licensed::Bool
end

struct ProductCell
    name::String
    axis::String
    family::String
    source_licensed::Bool
end

function sha256_file(path::String)::String
    open(path, "r") do io
        bytes2hex(SHA.sha256(io))
    end
end

clean_real(x::Real) = abs(Float64(x)) < 1.0e-14 ? 0.0 : Float64(x)

function complex_payload(value::Number)
    z = ComplexF64(value)
    Dict("re" => clean_real(real(z)), "im" => clean_real(imag(z)))
end

function matrix_payload(matrix::AbstractMatrix)
    [
        [complex_payload(matrix[i, j]) for j in 1:size(matrix, 2)]
        for i in 1:size(matrix, 1)
    ]
end

function sorted_complex_payload(values)
    ordered = sort(
        ComplexF64.(collect(values));
        by=z -> (round(real(z); digits=12), round(imag(z); digits=12)),
    )
    [complex_payload(value) for value in ordered]
end

function qit_objects()
    basis = QuantumOptics.SpinBasis(1 // 2)
    identity = QuantumOptics.identityoperator(basis)
    axes = Dict(
        "x" => QuantumOptics.sigmax(basis),
        "y" => QuantumOptics.sigmay(basis),
        "z" => QuantumOptics.sigmaz(basis),
    )
    Dict("basis" => basis, "identity" => identity, "axes" => axes)
end

function probe_states(qit)
    identity = qit["identity"]
    axes = qit["axes"]
    Dict(
        "rho_mixed" => identity / 2,
        "rho_x" => (identity + PROBE_RADIUS * axes["x"]) / 2,
        "rho_y" => (identity + PROBE_RADIUS * axes["y"]) / 2,
        "rho_z" => (identity + PROBE_RADIUS * axes["z"]) / 2,
    )
end

function entropy_nats(operator)::Float64
    dense = QuantumOptics.DenseOperator(
        operator.basis_l,
        operator.basis_r,
        Matrix(operator.data),
    )
    clean_real(real(QuantumOptics.entropy_vn(dense)))
end

function density_spectrum(operator)
    matrix = Matrix(operator.data)
    hermitian = Hermitian((matrix + matrix') / 2)
    sort(clean_real.(real.(LinearAlgebra.eigvals(hermitian))))
end

function bloch_readout(operator, qit)
    Dict(
        axis => clean_real(real(QuantumOptics.expect(qit["axes"][axis], operator)))
        for axis in ["x", "y", "z"]
    )
end

function probe_catalog(probes, qit)
    [
        Dict(
            "name" => name,
            "density_matrix" => matrix_payload(Matrix(probes[name].data)),
            "bloch_readout" => bloch_readout(probes[name], qit),
            "entropy_nats" => entropy_nats(probes[name]),
            "density_spectrum" => density_spectrum(probes[name]),
        )
        for name in PROBE_NAMES
    ]
end

function probe_coordinate_matrix(probes, qit)
    hcat(
        [
            Float64[
                real(QuantumOptics.tr(probes[name])),
                real(QuantumOptics.expect(qit["axes"]["x"], probes[name])),
                real(QuantumOptics.expect(qit["axes"]["y"], probes[name])),
                real(QuantumOptics.expect(qit["axes"]["z"], probes[name])),
            ]
            for name in PROBE_NAMES
        ]...,
    )
end

function channel_for(spec::ChannelSpec, qit)
    identity = qit["identity"]
    axis_operator = qit["axes"][spec.axis]
    identity_channel = QuantumOptics.sprepost(identity, identity)

    if spec.family == PINCH_FAMILY
        projector_plus = (identity + axis_operator) / 2
        projector_minus = (identity - axis_operator) / 2
        endpoint =
            QuantumOptics.sprepost(projector_plus, projector_plus) +
            QuantumOptics.sprepost(projector_minus, projector_minus)
        return (1 - spec.parameter) * identity_channel + spec.parameter * endpoint, nothing
    elseif spec.family == UNITARY_FAMILY
        unitary =
            cos(spec.parameter / 2) * identity -
            im * sin(spec.parameter / 2) * axis_operator
        channel = QuantumOptics.sprepost(unitary, QuantumOptics.dagger(unitary))
        return channel, unitary
    end

    error("unknown family $(spec.family)")
end

function action_record(superoperator, probe_name::String, input, qit)
    output = superoperator * input
    spectrum_before = density_spectrum(input)
    spectrum_after = density_spectrum(output)
    entropy_before = entropy_nats(input)
    entropy_after = entropy_nats(output)
    trace_output = clean_real(real(QuantumOptics.tr(output)))
    min_eigenvalue = minimum(spectrum_after)
    Dict(
        "probe" => probe_name,
        "input_density_matrix" => matrix_payload(Matrix(input.data)),
        "output_density_matrix" => matrix_payload(Matrix(output.data)),
        "input_bloch" => bloch_readout(input, qit),
        "output_bloch" => bloch_readout(output, qit),
        "action_frobenius_norm" => clean_real(LinearAlgebra.norm(Matrix(output.data - input.data))),
        "entropy_before_nats" => entropy_before,
        "entropy_after_nats" => entropy_after,
        "entropy_delta_nats" => clean_real(entropy_after - entropy_before),
        "spectrum_before" => spectrum_before,
        "spectrum_after" => spectrum_after,
        "spectrum_linf_delta" => clean_real(maximum(abs.(spectrum_after .- spectrum_before))),
        "trace_output" => trace_output,
        "minimum_output_eigenvalue" => min_eigenvalue,
        "density_valid" => abs(trace_output - 1.0) <= TOL && min_eigenvalue >= -TOL,
    )
end

function pinching_algebra_laws(superoperator, spec::ChannelSpec, qit)
    identity = qit["identity"]
    axis_operator = qit["axes"][spec.axis]
    basis = [identity, qit["axes"]["x"], qit["axes"]["y"], qit["axes"]["z"]]
    fixed_algebra = [identity, axis_operator]
    bimodule_residuals = Float64[]

    for fixed in fixed_algebra, candidate in basis
        left = superoperator * (fixed * candidate) - fixed * (superoperator * candidate)
        right = superoperator * (candidate * fixed) - (superoperator * candidate) * fixed
        push!(bimodule_residuals, LinearAlgebra.norm(Matrix(left.data)))
        push!(bimodule_residuals, LinearAlgebra.norm(Matrix(right.data)))
    end

    supermatrix = ComplexF64.(Matrix(superoperator.data))
    idempotence_residual = LinearAlgebra.norm(supermatrix * supermatrix - supermatrix)
    unital_residual = LinearAlgebra.norm(Matrix((superoperator * identity - identity).data))
    endpoint = abs(spec.parameter - 1.0) <= TOL
    pass =
        endpoint &&
        idempotence_residual <= TOL &&
        unital_residual <= TOL &&
        maximum(bimodule_residuals) <= TOL
    Dict(
        "law" => "conditional expectation onto the axis commutant",
        "full_strength_endpoint" => endpoint,
        "idempotence_residual" => clean_real(idempotence_residual),
        "unital_residual" => clean_real(unital_residual),
        "max_fixed_algebra_bimodule_residual" => clean_real(maximum(bimodule_residuals)),
        "pass" => pass,
    )
end

function automorphism_algebra_laws(unitary, qit)
    identity = qit["identity"]
    basis = [identity, qit["axes"]["x"], qit["axes"]["y"], qit["axes"]["z"]]
    transform(operator) = unitary * operator * QuantumOptics.dagger(unitary)
    multiplicativity_residuals = Float64[]
    star_residuals = Float64[]

    for left in basis, right in basis
        residual = transform(left * right) - transform(left) * transform(right)
        push!(multiplicativity_residuals, LinearAlgebra.norm(Matrix(residual.data)))
    end
    for operator in basis
        residual =
            transform(QuantumOptics.dagger(operator)) -
            QuantumOptics.dagger(transform(operator))
        push!(star_residuals, LinearAlgebra.norm(Matrix(residual.data)))
    end

    unital_residual = LinearAlgebra.norm(Matrix((transform(identity) - identity).data))
    pass =
        maximum(multiplicativity_residuals) <= TOL &&
        maximum(star_residuals) <= TOL &&
        unital_residual <= TOL
    Dict(
        "law" => "inner star-automorphism",
        "max_multiplicativity_residual" => clean_real(maximum(multiplicativity_residuals)),
        "max_star_preservation_residual" => clean_real(maximum(star_residuals)),
        "unital_residual" => clean_real(unital_residual),
        "pass" => pass,
    )
end

function measured_family(singular_values, entropy_deltas)
    has_contraction = minimum(singular_values) < 1.0 - CLASS_TOL
    entropy_non_decreasing = minimum(entropy_deltas) >= -TOL
    entropy_strict_somewhere = maximum(entropy_deltas) > ENTROPY_STRICT_TOL
    singular_isometry = maximum(abs.(singular_values .- 1.0)) <= CLASS_TOL
    entropy_preserved = maximum(abs.(entropy_deltas)) <= CLASS_TOL

    if has_contraction && entropy_non_decreasing && entropy_strict_somewhere
        return PINCH_FAMILY
    elseif singular_isometry && entropy_preserved
        return UNITARY_FAMILY
    end
    "ambiguous"
end

function analyze_channel(spec::ChannelSpec, qit, probes)
    superoperator, unitary = channel_for(spec, qit)
    supermatrix = ComplexF64.(Matrix(superoperator.data))
    singular_values = sort(clean_real.(LinearAlgebra.svdvals(supermatrix)); rev=true)
    eigenvalues = LinearAlgebra.eigvals(supermatrix)
    actions = [action_record(superoperator, name, probes[name], qit) for name in PROBE_NAMES]
    action_by_probe = Dict(String(row["probe"]) => row for row in actions)
    entropy_deltas = Float64[row["entropy_delta_nats"] for row in actions]
    spectrum_deltas = Float64[row["spectrum_linf_delta"] for row in actions]
    fixed_residuals = Dict(
        replace(name, "rho_" => "") => Float64(action_by_probe[name]["action_frobenius_norm"])
        for name in DIRECTIONAL_PROBES
    )
    fixed_axes = sort([axis for (axis, residual) in fixed_residuals if residual <= CLASS_TOL])
    axis_measured = length(fixed_axes) == 1 ? only(fixed_axes) : "ambiguous"
    family_measured = measured_family(singular_values, entropy_deltas)
    signature_admissible = axis_measured != "ambiguous" && family_measured != "ambiguous"
    signature_key = signature_admissible ? "$(axis_measured)|$(family_measured)" : "ambiguous"
    algebra_laws = if spec.family == PINCH_FAMILY
        pinching_algebra_laws(superoperator, spec, qit)
    else
        automorphism_algebra_laws(unitary, qit)
    end

    record = Dict{String,Any}(
        "operator_name" => spec.operator_name,
        "variant_id" => spec.variant_id,
        "declared_axis" => spec.axis,
        "declared_family" => spec.family,
        "parameter_kind" => spec.parameter_kind,
        "parameter" => spec.parameter,
        "source_licensed" => spec.source_licensed,
        "measured_axis" => axis_measured,
        "measured_family" => family_measured,
        "structural_signature" => signature_key,
        "structural_signature_admissible" => signature_admissible,
        "fixed_directional_probe_residuals" => fixed_residuals,
        "fixed_directional_probes" => fixed_axes,
        "finite_density_actions" => actions,
        "entropy_delta_summary_nats" => Dict(
            "minimum" => clean_real(minimum(entropy_deltas)),
            "maximum" => clean_real(maximum(entropy_deltas)),
            "maximum_absolute" => clean_real(maximum(abs.(entropy_deltas))),
            "non_decreasing_on_spanning_probes" => minimum(entropy_deltas) >= -TOL,
            "strict_on_at_least_one_spanning_probe" => maximum(entropy_deltas) > ENTROPY_STRICT_TOL,
        ),
        "density_spectrum_summary" => Dict(
            "maximum_linf_delta" => clean_real(maximum(spectrum_deltas)),
            "preserved_on_all_spanning_probes" => maximum(spectrum_deltas) <= CLASS_TOL,
        ),
        "superoperator_spectrum" => sorted_complex_payload(eigenvalues),
        "superoperator_singular_values" => singular_values,
        "superoperator_numerical_rank" => count(value -> value > CLASS_TOL, singular_values),
        "superoperator_idempotence_residual" => clean_real(LinearAlgebra.norm(supermatrix * supermatrix - supermatrix)),
        "superoperator_isometry_residual" => clean_real(LinearAlgebra.norm(supermatrix' * supermatrix - Matrix{ComplexF64}(I, 4, 4))),
        "superoperator_abs_determinant" => clean_real(abs(LinearAlgebra.det(supermatrix))),
        "algebra_laws" => algebra_laws,
        "all_density_outputs_valid" => all(Bool(row["density_valid"]) for row in actions),
        "declared_axis_matches_measurement" => axis_measured == spec.axis,
        "declared_family_matches_measurement" => family_measured == spec.family,
    )
    (; spec, record, supermatrix)
end

function structural_groups(items)
    groups = Dict{String,Vector{String}}()
    for item in items
        key = String(item.record["structural_signature"])
        push!(get!(groups, key, String[]), item.spec.variant_id)
    end
    Dict(key => sort(members) for (key, members) in groups)
end

function exact_superoperator_groups(items)
    representatives = Matrix{ComplexF64}[]
    members = Vector{Vector{String}}()
    for item in items
        match_index = findfirst(
            index -> LinearAlgebra.norm(item.supermatrix - representatives[index]) <= CLASS_TOL,
            eachindex(representatives),
        )
        if match_index === nothing
            push!(representatives, item.supermatrix)
            push!(members, [item.spec.variant_id])
        else
            push!(members[match_index], item.spec.variant_id)
        end
    end
    Dict(
        "class_$(index)" => sort(group)
        for (index, group) in enumerate(members)
    )
end

function compact_channel_record(item)
    record = item.record
    Dict(
        "operator_name" => record["operator_name"],
        "variant_id" => record["variant_id"],
        "declared_axis" => record["declared_axis"],
        "declared_family" => record["declared_family"],
        "parameter_kind" => record["parameter_kind"],
        "parameter" => record["parameter"],
        "measured_axis" => record["measured_axis"],
        "measured_family" => record["measured_family"],
        "structural_signature" => record["structural_signature"],
        "structural_signature_admissible" => record["structural_signature_admissible"],
        "entropy_delta_summary_nats" => record["entropy_delta_summary_nats"],
        "density_spectrum_summary" => record["density_spectrum_summary"],
        "superoperator_singular_values" => record["superoperator_singular_values"],
        "superoperator_numerical_rank" => record["superoperator_numerical_rank"],
    )
end

coordinate_distance(left::ProductCell, right::ProductCell) =
    Int(left.axis != right.axis) + Int(left.family != right.family)

function build_product_graph(cells::Vector{ProductCell}; allow_diagonal::Bool=false)
    graph = Graphs.SimpleGraph(length(cells))
    edge_records = Dict{String,Any}[]
    for left in 1:(length(cells) - 1), right in (left + 1):length(cells)
        distance = coordinate_distance(cells[left], cells[right])
        allowed = distance == 1 || (allow_diagonal && distance == 2)
        if allowed
            Graphs.add_edge!(graph, left, right)
            changed = String[]
            cells[left].axis != cells[right].axis && push!(changed, "axis")
            cells[left].family != cells[right].family && push!(changed, "family")
            push!(edge_records, Dict(
                "source" => cells[left].name,
                "target" => cells[right].name,
                "coordinate_distance" => distance,
                "changed_coordinates" => changed,
                "mss_edge" => distance == 1,
            ))
        end
    end
    graph, edge_records
end

function permutations_of(values::Vector{Int})
    length(values) <= 1 && return [copy(values)]
    output = Vector{Vector{Int}}()
    for index in eachindex(values)
        head = values[index]
        tail_input = [values[j] for j in eachindex(values) if j != index]
        for tail in permutations_of(tail_input)
            push!(output, vcat(head, tail))
        end
    end
    output
end

function oriented_hamiltonian_cycles(graph)
    vertex_count = Graphs.nv(graph)
    vertex_count < 3 && return Vector{Vector{Int}}()
    cycles = Vector{Vector{Int}}()
    for tail in permutations_of(collect(2:vertex_count))
        sequence = vcat(1, tail)
        path_edges_exist = all(
            Graphs.has_edge(graph, sequence[index], sequence[index + 1])
            for index in 1:(vertex_count - 1)
        )
        closes = Graphs.has_edge(graph, sequence[end], sequence[1])
        path_edges_exist && closes && push!(cycles, sequence)
    end
    cycles
end

cycle_key(sequence, cells) = join((cells[index].name for index in sequence), "|")

function cycles_modulo_reversal(oriented_cycles, cells)
    canonical = Dict{String,Vector{Int}}()
    for sequence in oriented_cycles
        reversed = vcat(sequence[1], reverse(sequence[2:end]))
        forward_key = cycle_key(sequence, cells)
        reverse_key = cycle_key(reversed, cells)
        selected = forward_key <= reverse_key ? sequence : reversed
        canonical[min(forward_key, reverse_key)] = selected
    end
    sort(collect(values(canonical)); by=sequence -> cycle_key(sequence, cells))
end

function sequence_payload(sequence, cells)
    names = [cells[index].name for index in sequence]
    Dict(
        "vertices_modulo_rotation" => names,
        "closed_sequence" => join(vcat(names, names[1]), "-"),
        "cycle_length_edges" => length(names),
    )
end

function graph_analysis(cells::Vector{ProductCell}; allow_diagonal::Bool=false)
    graph, edge_records = build_product_graph(cells; allow_diagonal=allow_diagonal)
    oriented = oriented_hamiltonian_cycles(graph)
    sort!(oriented; by=sequence -> cycle_key(sequence, cells))
    undirected = cycles_modulo_reversal(oriented, cells)
    Dict(
        "vertices" => [
            Dict(
                "name" => cell.name,
                "axis" => cell.axis,
                "family" => cell.family,
                "source_licensed" => cell.source_licensed,
            )
            for cell in cells
        ],
        "vertex_count" => Graphs.nv(graph),
        "edge_count" => Graphs.ne(graph),
        "degree_sequence" => sort(Graphs.degree(graph)),
        "allow_diagonal_jumps" => allow_diagonal,
        "edge_rule" => allow_diagonal ? "coordinate distance 1 or 2" : "MSS coordinate distance exactly 1",
        "edges" => edge_records,
        "rotation_anchor" => isempty(cells) ? nothing : cells[1].name,
        "oriented_cycles_modulo_rotation_count" => length(oriented),
        "oriented_cycles_modulo_rotation" => [sequence_payload(sequence, cells) for sequence in oriented],
        "cycles_modulo_rotation_and_reversal_count" => length(undirected),
        "cycles_modulo_rotation_and_reversal" => [sequence_payload(sequence, cells) for sequence in undirected],
        "minimum_closed_hamiltonian_cycle_length" => isempty(oriented) ? nothing : minimum(length.(oriented)),
        "simple_cycle_minimum_vertex_rule" => 3,
    )
end

function erase_coordinate(cells::Vector{ProductCell}, coordinate::String)
    output = ProductCell[]
    seen = Set{String}()
    if coordinate == "axis"
        for cell in cells
            cell.family in seen && continue
            push!(seen, cell.family)
            push!(output, ProductCell("family:$(cell.family)", "erased", cell.family, cell.source_licensed))
        end
    elseif coordinate == "family"
        for cell in cells
            cell.axis in seen && continue
            push!(seen, cell.axis)
            push!(output, ProductCell("axis:$(cell.axis)", cell.axis, "erased", cell.source_licensed))
        end
    else
        error("unknown coordinate $(coordinate)")
    end
    output
end

function variant_specs()
    output = ChannelSpec[]
    core_coordinates = [
        ("Ti", "z", PINCH_FAMILY),
        ("Te", "x", PINCH_FAMILY),
        ("Fi", "x", UNITARY_FAMILY),
        ("Fe", "z", UNITARY_FAMILY),
    ]
    pinch_strengths = [0.35, 0.70, 1.00]
    rotation_angles = [pi / 7, pi / 3, 2pi / 3]
    for (operator_name, axis, family) in core_coordinates
        parameters = family == PINCH_FAMILY ? pinch_strengths : rotation_angles
        kind = family == PINCH_FAMILY ? "pinching_strength" : "rotation_angle_radians"
        for (index, parameter) in enumerate(parameters)
            push!(output, ChannelSpec(
                operator_name,
                "$(operator_name)_variant_$(index)",
                axis,
                family,
                kind,
                parameter,
                true,
            ))
        end
    end
    output
end

function main()
    qit = qit_objects()
    probes = probe_states(qit)
    probe_matrix = probe_coordinate_matrix(probes, qit)
    probe_rank = count(value -> value > TOL, LinearAlgebra.svdvals(probe_matrix))

    core_specs = [
        ChannelSpec("Ti", "Ti", "z", PINCH_FAMILY, "pinching_strength", 1.0, true),
        ChannelSpec("Te", "Te", "x", PINCH_FAMILY, "pinching_strength", 1.0, true),
        ChannelSpec("Fi", "Fi", "x", UNITARY_FAMILY, "rotation_angle_radians", pi / 3, true),
        ChannelSpec("Fe", "Fe", "z", UNITARY_FAMILY, "rotation_angle_radians", pi / 3, true),
    ]
    core_items = [analyze_channel(spec, qit, probes) for spec in core_specs]
    core_by_name = Dict(item.spec.operator_name => item for item in core_items)
    core_groups = structural_groups(core_items)

    y_specs = [
        ChannelSpec("Yp_control", "Yp_control", "y", PINCH_FAMILY, "pinching_strength", 1.0, false),
        ChannelSpec("Yu_control", "Yu_control", "y", UNITARY_FAMILY, "rotation_angle_radians", pi / 3, false),
    ]
    y_items = [analyze_channel(spec, qit, probes) for spec in y_specs]
    with_y_items = vcat(core_items, y_items)

    variants = [analyze_channel(spec, qit, probes) for spec in variant_specs()]
    variant_structural_groups = structural_groups(variants)
    variant_exact_groups = exact_superoperator_groups(variants)

    identity_boundaries = [
        analyze_channel(ChannelSpec("Ti", "pinching_strength_zero", "z", PINCH_FAMILY, "pinching_strength", 0.0, false), qit, probes),
        analyze_channel(ChannelSpec("Fe", "rotation_angle_zero", "z", UNITARY_FAMILY, "rotation_angle_radians", 0.0, false), qit, probes),
    ]
    identity_boundary_distance = LinearAlgebra.norm(
        identity_boundaries[1].supermatrix - identity_boundaries[2].supermatrix,
    )

    graph_order = ["Ti", "Fe", "Fi", "Te"]
    core_cells = [
        ProductCell(
            name,
            String(core_by_name[name].record["measured_axis"]),
            String(core_by_name[name].record["measured_family"]),
            true,
        )
        for name in graph_order
    ]
    core_graph = graph_analysis(core_cells; allow_diagonal=false)
    diagonal_graph = graph_analysis(core_cells; allow_diagonal=true)
    erased_axis_graph = graph_analysis(erase_coordinate(core_cells, "axis"); allow_diagonal=false)
    erased_family_graph = graph_analysis(erase_coordinate(core_cells, "family"); allow_diagonal=false)
    removed_cell_graphs = [
        Dict(
            "removed_cell" => core_cells[index].name,
            "graph" => graph_analysis([cell for (j, cell) in enumerate(core_cells) if j != index]; allow_diagonal=false),
        )
        for index in eachindex(core_cells)
    ]
    y_cells = vcat(
        core_cells,
        [
            ProductCell(
                item.spec.operator_name,
                String(item.record["measured_axis"]),
                String(item.record["measured_family"]),
                false,
            )
            for item in y_items
        ],
    )
    y_graph = graph_analysis(y_cells; allow_diagonal=false)

    expected_core_signatures = Set([
        "z|$(PINCH_FAMILY)",
        "x|$(PINCH_FAMILY)",
        "x|$(UNITARY_FAMILY)",
        "z|$(UNITARY_FAMILY)",
    ])
    measured_core_signatures = Set(keys(core_groups))
    core_oriented_sequences = Set(
        join(row["vertices_modulo_rotation"], "-")
        for row in core_graph["oriented_cycles_modulo_rotation"]
    )
    expected_oriented_sequences = Set(["Ti-Fe-Fi-Te", "Ti-Te-Fi-Fe"])

    checks = Dict{String,Bool}(
        "strict_carrier_project" => normpath(String(Base.active_project())) == normpath(CARRIER_PROJECT),
        "strict_load_path" => get(ENV, "JULIA_LOAD_PATH", "") == "@:@stdlib" && Base.LOAD_PATH == ["@", "@stdlib"],
        "spanning_probe_rank_is_four" => probe_rank == 4,
        "all_core_density_outputs_valid" => all(Bool(item.record["all_density_outputs_valid"]) for item in core_items),
        "source_label_axis_family_mapping_recovered" => all(
            Bool(item.record["declared_axis_matches_measurement"]) &&
            Bool(item.record["declared_family_matches_measurement"])
            for item in core_items
        ),
        "four_measured_signature_cells" => length(core_groups) == 4 && measured_core_signatures == expected_core_signatures,
        "pinching_entropy_non_decreasing_and_strict_somewhere" => all(
            Bool(item.record["entropy_delta_summary_nats"]["non_decreasing_on_spanning_probes"]) &&
            Bool(item.record["entropy_delta_summary_nats"]["strict_on_at_least_one_spanning_probe"])
            for item in core_items if item.spec.family == PINCH_FAMILY
        ),
        "pinching_conditional_expectation_laws" => all(
            Bool(item.record["algebra_laws"]["pass"])
            for item in core_items if item.spec.family == PINCH_FAMILY
        ),
        "unitary_entropy_and_density_spectrum_preserved" => all(
            Float64(item.record["entropy_delta_summary_nats"]["maximum_absolute"]) <= CLASS_TOL &&
            Bool(item.record["density_spectrum_summary"]["preserved_on_all_spanning_probes"])
            for item in core_items if item.spec.family == UNITARY_FAMILY
        ),
        "unitary_automorphism_laws" => all(
            Bool(item.record["algebra_laws"]["pass"])
            for item in core_items if item.spec.family == UNITARY_FAMILY
        ),
        "erase_axis_leaves_two_family_classes" => length(unique(item.record["measured_family"] for item in core_items)) == 2,
        "erase_family_leaves_two_axis_classes" => length(unique(item.record["measured_axis"] for item in core_items)) == 2,
        "add_y_axis_yields_six_classes" => length(structural_groups(with_y_items)) == 6,
        "parameter_variants_quotient_to_four_structural_classes" => length(variant_structural_groups) == 4,
        "parameter_variants_remain_exactly_distinct_before_structural_quotient" => length(variant_exact_groups) == length(variants),
        "identity_parameter_boundary_collapses_axis_signature" => identity_boundary_distance <= TOL && all(
            !Bool(item.record["structural_signature_admissible"])
            for item in identity_boundaries
        ),
        "mss_core_graph_is_four_cycle" => core_graph["vertex_count"] == 4 && core_graph["edge_count"] == 4 && core_graph["degree_sequence"] == [2, 2, 2, 2],
        "mss_core_cycle_length_four" => core_graph["minimum_closed_hamiltonian_cycle_length"] == 4,
        "mss_core_orientations_match_forward_and_reverse" => core_oriented_sequences == expected_oriented_sequences,
        "mss_core_unique_modulo_rotation_and_reversal" => core_graph["cycles_modulo_rotation_and_reversal_count"] == 1,
        "erase_either_coordinate_kills_simple_hamiltonian_cycle" => erased_axis_graph["cycles_modulo_rotation_and_reversal_count"] == 0 && erased_family_graph["cycles_modulo_rotation_and_reversal_count"] == 0,
        "remove_any_cell_kills_hamiltonian_cycle" => all(
            row["graph"]["cycles_modulo_rotation_and_reversal_count"] == 0
            for row in removed_cell_graphs
        ),
        "forbid_diagonal_unique_allow_diagonal_nonunique" => core_graph["cycles_modulo_rotation_and_reversal_count"] == 1 && diagonal_graph["cycles_modulo_rotation_and_reversal_count"] == 3,
        "add_y_axis_changes_cycle_to_length_six_and_nonunique" => y_graph["minimum_closed_hamiltonian_cycle_length"] == 6 && y_graph["cycles_modulo_rotation_and_reversal_count"] > 1,
    )
    all_pass = all(values(checks))

    runtime_command =
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no " *
        "--project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier " *
        SOURCE_PATH
    source_sha256 = sha256_file(SOURCE_PATH)
    timestamp = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")

    result = Dict{String,Any}(
        "schema" => "codex_ratchet.four_substages_dual_product_v0.julia_result.v1",
        "sim_id" => SIM_ID,
        "name" => "Conditional axis-family product and MSS cycle diagnostic",
        "version" => "0.1.0",
        "engine" => "julia_canon",
        "classification" => "scratch_diagnostic",
        "promotion_status" => "diagnostic_only",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "stage_movement_allowed" => false,
        "reads_peer_result" => false,
        "data_or_artifact_dependencies" => String[],
        "runner_registration" => "not_registered_by_request",
        "written_at" => timestamp,
        "source_path" => SOURCE_PATH,
        "source_sha256" => source_sha256,
        "result_path" => RESULT_PATH,
        "accepted_status_label" => all_pass ? "passes local rerun" : "runs",
        "purpose" => "Test the conditional product of source-selected axes x,z with pinching/conditional-expectation and unitary-automorphism families on a finite one-qubit density carrier, then test the induced MSS product graph.",
        "scientific_question" => "Do package-evaluated finite channel signatures form four axis-family quotient cells under the source restriction, and does the resulting 2x2 one-coordinate-change graph conditionally carry one four-cell Hamiltonian cycle?",
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_carrier_operator_algebra_scratch_probe",
        "tier" => 1,
        "root_constraints_in_force" => Dict(
            "F01_finitude" => "one qubit, four spanning density probes, finite channel and graph enumerations",
            "N01_noncommutation" => "not promoted here; the bounded claim is family/axis distinction and graph adjacency, not an engine noncommutation proof",
        ),
        "source_authority" => [
            Dict(
                "path" => "system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md",
                "licensed_content" => "Ti=z conditional expectation, Te=x conditional expectation, Fi=x inner automorphism, Fe=z inner automorphism",
            ),
            Dict(
                "path" => "system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md",
                "licensed_content" => "Axis-5 family split and exact four density-matrix channel maps",
            ),
            Dict(
                "path" => "system_v5/READ ONLY Reference Docs/operator math explicit.md",
                "licensed_content" => "explicit projectors and x/z unitary matrices",
            ),
            Dict(
                "path" => "system_v5/ops/CLAUDE_SCIENCE_94_95_ENGINE_STATE_AUDIT_20260709.md",
                "licensed_content" => "four-substage and 16x4 claims remain unearned pending independent ratchets",
            ),
        ],
        "premises" => Dict(
            "source_axis_selection" => ["x", "z"],
            "source_axis_selection_is_assumed_complete_for_this_probe" => true,
            "operator_family_selection" => [PINCH_FAMILY, UNITARY_FAMILY],
            "operator_family_selection_is_assumed_complete_for_this_probe" => true,
            "nontrivial_parameter_domain" => "pinching strength q>0 and rotation angle not congruent to 0 modulo 2pi",
            "mss_graph_rule" => "connect cells iff exactly one of axis or family changes",
            "cycle_convention" => "simple undirected Hamiltonian cycle, at least three vertices; oriented sequences quotient rotation, then optionally reversal",
            "hamiltonian_word_scope" => "graph-theoretic cycle only, not Hamiltonian quantum time evolution",
        ),
        "carrier" => Dict(
            "hilbert_space" => "C^2",
            "density_space" => "D(C^2)",
            "probe_radius" => PROBE_RADIUS,
            "spanning_probe_names" => PROBE_NAMES,
            "probe_coordinate_order" => ["trace", "expect_x", "expect_y", "expect_z"],
            "probe_coordinate_matrix" => [collect(probe_matrix[row, :]) for row in 1:size(probe_matrix, 1)],
            "probe_rank" => probe_rank,
            "entropy_units" => "nats",
            "probes" => probe_catalog(probes, qit),
        ),
        "operator_family_definitions" => Dict(
            PINCH_FAMILY => Dict(
                "path" => "Phi_axis,q = (1-q) id + q E_axis",
                "endpoint" => "q=1 is the Hilbert-Schmidt conditional expectation onto span{I,sigma_axis}",
                "quotient_rule" => "nonzero strengths with contraction and strict entropy gain on at least one spanning probe share one family coordinate",
            ),
            UNITARY_FAMILY => Dict(
                "path" => "Phi_axis,theta(rho) = U_axis(theta) rho U_axis(theta)^dagger",
                "endpoint" => "inner star-automorphism generated by sigma_axis",
                "quotient_rule" => "nonidentity angles with singular values one and density-spectrum preservation share one family coordinate",
            ),
        ),
        "four_signature_cells" => [item.record for item in core_items],
        "four_signature_quotient" => Dict(
            "class_count" => length(core_groups),
            "classes" => core_groups,
            "label_mapping" => Dict(
                "Ti" => "z x pinching/conditional expectation",
                "Te" => "x x pinching/conditional expectation",
                "Fi" => "x x unitary automorphism",
                "Fe" => "z x unitary automorphism",
            ),
            "derivation_rule" => "axis is the unique fixed directional probe; family is inferred from entropy delta plus superoperator singular behavior",
        ),
        "quotient_controls" => Dict(
            "erase_axis" => Dict(
                "class_count" => length(unique(item.record["measured_family"] for item in core_items)),
                "surviving_coordinate" => "family",
            ),
            "erase_family" => Dict(
                "class_count" => length(unique(item.record["measured_axis"] for item in core_items)),
                "surviving_coordinate" => "axis",
            ),
            "add_y_axis" => Dict(
                "source_licensed" => false,
                "channel_records" => [item.record for item in y_items],
                "class_count" => length(structural_groups(with_y_items)),
                "classes" => structural_groups(with_y_items),
                "meaning" => "six rather than four shows that four depends on the source restriction to axes x,z",
            ),
            "duplicate_strength_angle_variants" => Dict(
                "variant_count" => length(variants),
                "variant_records" => [compact_channel_record(item) for item in variants],
                "exact_superoperator_class_count" => length(variant_exact_groups),
                "exact_superoperator_classes" => variant_exact_groups,
                "structural_class_count" => length(variant_structural_groups),
                "structural_classes" => variant_structural_groups,
                "meaning" => "nonzero strength/angle changes alter exact maps but quotient to the same four measured axis-family cells",
            ),
            "identity_parameter_boundary" => Dict(
                "records" => [compact_channel_record(item) for item in identity_boundaries],
                "superoperator_distance" => clean_real(identity_boundary_distance),
                "meaning" => "q=0 and theta=0 meet at identity, erase the unique fixed axis, and are excluded from the four-cell quotient",
            ),
        ),
        "mss_product_graph" => Dict(
            "core_forbid_diagonal" => core_graph,
            "core_allow_diagonal_control" => diagonal_graph,
            "erase_axis_coordinate_control" => erased_axis_graph,
            "erase_family_coordinate_control" => erased_family_graph,
            "remove_each_cell_controls" => removed_cell_graphs,
            "add_y_axis_control" => y_graph,
            "conditional_derivation" => "Given complete source-selected 2x2 cells and MSS one-coordinate adjacency, the graph is C4 and has the two orientations Ti-Fe-Fi-Te and Ti-Te-Fi-Fe modulo rotation, one cycle modulo reversal.",
            "premise_boundary" => "The source-selected vertex set and its completeness are premises. Allowing diagonal jumps or adding y removes the unique four-cycle conclusion; removing a cell or erasing a coordinate removes the simple Hamiltonian cycle.",
        ),
        "checks" => checks,
        "all_pass" => all_pass,
        "allowed_claim" => "Conditional on the declared source axis/family completeness premises and MSS adjacency, the finite Julia carrier yields four measured structural cells and one graph-theoretic four-cycle modulo rotation and reversal.",
        "non_claims" => [
            "This diagnostic does not prove sequential substages.",
            "This diagnostic does not prove a 16x4 schedule or the necessity/completeness of any 16 macro slots.",
            "This diagnostic does not prove personalities, perception, intelligences, or engines.",
            "The graph-theoretic Hamiltonian cycle is not Hamiltonian quantum dynamics and no channel sequence is executed as an engine stage here.",
            "The source selection and completeness of axes x,z and the two operator-algebra families are premises, not outputs of this diagnostic.",
            "The y-axis control shows that four is conditional on the source axis restriction rather than a universal QIT count.",
        ],
        "eligible_consumers" => [
            "bounded source-selection falsification",
            "future independent geometry/entropy survivor ratchets as a hypothesis fixture",
        ],
        "blocked_consumers" => [
            "sequential four-substage admission",
            "16x4 schedule admission",
            "personality or intelligence claims",
            "Type-1 or Type-2 engine claims",
            "Axis0, manifold, bridge, or ontology promotion",
        ],
        "promotion_blockers" => [
            "source axis and family completeness are assumed",
            "no independent geometry and entropy ratchets emitted these cells",
            "no sequential composition or held-out task ablation ran",
            "no fabrication audit or admission gate ran",
        ],
        "required_negatives" => [
            "erase axis coordinate",
            "erase family coordinate",
            "add y axis",
            "duplicate nonzero strengths and angles",
            "identity parameter boundary",
            "remove each graph cell",
            "allow diagonal graph jumps",
        ],
        "negatives_run" => [
            "erase axis -> two quotient classes and no simple graph cycle",
            "erase family -> two quotient classes and no simple graph cycle",
            "add y -> six quotient classes and nonunique length-six cycles",
            "duplicate strengths/angles -> four structural classes from distinct exact maps",
            "q=0 and theta=0 -> identity boundary with ambiguous axis",
            "remove any cell -> no Hamiltonian cycle",
            "allow diagonal jumps -> three cycles modulo reversal instead of one",
        ],
        "julia" => Dict(
            "ran" => true,
            "semantic_owner" => "julia",
            "source_path" => SOURCE_PATH,
            "project" => Base.active_project(),
            "load_path_environment" => get(ENV, "JULIA_LOAD_PATH", ""),
            "base_load_path" => Base.LOAD_PATH,
            "strict_project_ok" => checks["strict_carrier_project"],
            "strict_load_path_ok" => checks["strict_load_path"],
            "startup_file_contract" => "--startup-file=no in recorded command",
            "run_command" => runtime_command,
            "version" => string(VERSION),
            "executable" => joinpath(Sys.BINDIR, "julia"),
            "packages_used" => ["QuantumOptics", "Graphs", "LinearAlgebra", "JSON3", "Dates", "SHA"],
            "package_versions" => Dict(
                "QuantumOptics" => string(Base.pkgversion(QuantumOptics)),
                "Graphs" => string(Base.pkgversion(Graphs)),
                "JSON3" => string(Base.pkgversion(JSON3)),
            ),
            "aligned_packages_load_bearing" => ["QuantumOptics", "Graphs"],
            "reads_peer_result" => false,
        ),
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing finite density operators, Pauli axes, superoperator channel action, expectation values, and von Neumann entropy gates",
            ),
            "Graphs" => Dict(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing MSS product graphs, adjacency checks, degree/edge counts, and exhaustive Hamiltonian-cycle gate",
            ),
            "LinearAlgebra" => Dict(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing density and superoperator eigenspectra, singular values, ranks, determinants, and residuals",
            ),
            "JSON3" => Dict(
                "tried" => true,
                "used" => true,
                "reason" => "supportive result receipt serialization only",
            ),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "QuantumOptics" => "load_bearing",
            "Graphs" => "load_bearing",
            "LinearAlgebra" => "load_bearing",
            "JSON3" => "supportive",
        ),
        "tool_calls" => [
            Dict(
                "tool" => "QuantumOptics",
                "qualified_api/function" => "QuantumOptics.SpinBasis/identityoperator/sigmax/sigmay/sigmaz/sprepost/expect/entropy_vn",
                "input_object" => "one-qubit DenseOperator spanning probes and axis-indexed pinching/unitary maps",
                "output_object" => "finite channel outputs, fixed-axis residuals, Bloch expectations, and entropy deltas",
                "positive_case" => "x,z crossed with the two measured operator-algebra families yields Ti,Te,Fi,Fe",
                "negative/erased_control" => "erasing axis or family collapses four classes to two; q=0/theta=0 erases the axis signature",
                "boundary_case" => "adding package-evaluated y pinching and rotation yields six classes",
                "demotion_condition" => "demote if QuantumOptics action or entropy calls fail, density outputs are invalid, pinching decreases entropy, or unitary maps change density spectra",
                "gates" => ["all_pass", "four_signature_cells", "quotient"],
            ),
            Dict(
                "tool" => "Graphs",
                "qualified_api/function" => "Graphs.SimpleGraph/Graphs.add_edge!/Graphs.has_edge/Graphs.nv/Graphs.ne/Graphs.degree",
                "input_object" => "measured axis-family cells with MSS coordinate-distance adjacency",
                "output_object" => "finite graph edges, degrees, and exhaustive closed Hamiltonian-cycle enumerations",
                "positive_case" => "the source-premised 2x2 graph has one C4 cycle modulo reversal and two orientations modulo rotation",
                "negative/erased_control" => "coordinate erasure or removal of any cell eliminates the simple Hamiltonian cycle",
                "boundary_case" => "diagonal jumps create three cycles modulo reversal; adding y creates nonunique length-six cycles",
                "demotion_condition" => "demote the conditional cycle claim if MSS adjacency is not C4, the forward/reverse sequences are absent, or a removal control retains a cycle",
                "gates" => ["all_pass", "mss_product_graph", "cycle_quotient"],
            ),
            Dict(
                "tool" => "LinearAlgebra",
                "qualified_api/function" => "LinearAlgebra.eigvals/svdvals/det/norm",
                "input_object" => "density matrices, 4x4 channel superoperators, and algebra-law residuals",
                "output_object" => "density spectra, superoperator spectra/singular values, ranks, and numerical law checks",
                "positive_case" => "pinching contracts singular directions while unitary automorphisms have all singular values one",
                "negative/erased_control" => "distinct nonzero parameter variants remain distinct exact superoperators before quotient",
                "boundary_case" => "zero-strength pinching and zero-angle rotation coincide as identity",
                "demotion_condition" => "demote if spectral/singular behavior does not separate the declared families",
                "gates" => ["all_pass", "spectra", "quotient"],
            ),
        ],
        "roles" => Dict(
            "state_archaeology" => "authority and source paths read before authoring",
            "builder" => "this Julia source",
            "mechanical_gatekeeper" => "in-file finite checks only",
            "fabrication_auditor" => "not run",
            "controller_admission" => "not run",
        ),
        "artifacts_emitted" => [SOURCE_PATH, RESULT_PATH],
        "witness_trace_id" => "$(SIM_ID):$(source_sha256[1:16])",
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, result)
        write(io, "\n")
    end

    println(JSON3.write(Dict(
        "sim_id" => SIM_ID,
        "all_pass" => all_pass,
        "result_path" => RESULT_PATH,
        "signature_class_count" => length(core_groups),
        "core_cycle_length" => core_graph["minimum_closed_hamiltonian_cycle_length"],
        "core_oriented_cycles_modulo_rotation" => [
            row["closed_sequence"] for row in core_graph["oriented_cycles_modulo_rotation"]
        ],
        "core_cycles_modulo_reversal" => core_graph["cycles_modulo_rotation_and_reversal_count"],
        "y_axis_class_count" => length(structural_groups(with_y_items)),
    )))
    all_pass || exit(1)
end

main()

# ratchet_order_test.jl
# =====================================================================
# Pairwise noncommutative-order ratchet harness (A.B vs B.A), F01+N01 driven,
# with independent collapse-controls (erase order / phase / chirality / carrier
# -> the order gap collapses). Emits the surviving-order graph (the ratchet).
#
# STATUS (read before trusting any number this prints):
#   This is a SCAFFOLD, not a parent-complete nesting receipt. It runs the real
#   AB-vs-BA finite harness over finite carrier maps, but the per-layer maps are
#   STUBBED with the current best-available finite layer objects. No pair is
#   admitted as a real pairwise nesting test, because the parent-completion gate
#   is not yet met (see PARENT-COMPLETION below and the printed real_graph_status).
#
# ANTI-HALLUCINATION CONTRACT:
#   Every governing equation/rule used here is quoted VERBATIM from the two named
#   docs with a file+section+line cite, collected in DOC_QUOTES below. Anything
#   the docs assert but this scaffold does NOT yet implement is listed in GAPS,
#   not silently faked.
#
# Governing docs (verbatim quotes carried in DOC_QUOTES):
#   system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md
#   system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md
#
# Runtime: bare Julia 1.12 (LinearAlgebra + Printf + Dates are stdlib). JSON is
#   used if resolvable (run with `julia --project=system_v5/julia_carrier`); if
#   not, a minimal built-in JSON emitter is used so the file still runs and still
#   writes a receipt under bare `julia ratchet_order_test.jl`.
# =====================================================================

using LinearAlgebra
using Printf
using Dates

const THIS_DIR    = @__DIR__
const RESULT_PATH = joinpath(THIS_DIR, "ratchet_order_test_results.json")

# Below this, an order gap counts as "collapsed" (matches R0_layer.jl GAP_FLOOR).
const GAP_FLOOR = 1.0e-6
const TOL       = 1.0e-9

# ---------------------------------------------------------------------
# VERBATIM doc quotes (anti-hallucination ledger). Each `quote` is copied
# character-for-character from a page actually read in this build.
# ---------------------------------------------------------------------
const DOC_QUOTES = [
    Dict(
        "file"    => "system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
        "section" => "Corrected Program",
        "lines"   => "18-20",
        "quote"   => "`A then B != B then A`, and **the surviving order is the ratchet** — irreversible survivor\nstructure that accumulates because order matters. The \"correct order\" is the order that\n**survives** the finite noncommutative tests, not the order that sounds natural from labels.",
    ),
    Dict(
        "file"    => "system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
        "section" => "What Allows Stacking",
        "lines"   => "143-152",
        "quote"   => "First stacking test is pairwise only:\n\nLayer A then Layer B   vs   Layer B then Layer A\n\nA∘B == B∘A                      -> no ratchet at that pair\nA∘B != B∘A and controls collapse -> real order pressure at that pair",
    ),
    Dict(
        "file"    => "system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
        "section" => "What Allows Stacking",
        "lines"   => "138-140",
        "quote"   => "an N01 order gap inside EACH parent\ncontrols proving the gap collapses when order/phase/chirality/carrier is erased\ntool receipts showing the interface is real",
    ),
    Dict(
        "file"    => "system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
        "section" => "Construction Dependency / below-terrain carrier objects",
        "lines"   => "202-205",
        "quote"   => "K=(V,E,F,C);  psi_v in S^3 subset C^2;  T_eta_k = {(e^{i phi} cos eta_k, e^{i chi} sin eta_k)}\npi_H(psi) = psi^dag sigma psi in S^2;   A_Hopf = d phi + cos(2 eta) d chi\nrho_{v,L,k}=psi_{v,L,k} psi_{v,L,k}^dag;  rho_{v,R,k}=...;  H_L=+H0, H_R=-H0",
    ),
    Dict(
        "file"    => "system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
        "section" => "Terrain Layer Standard (L10)",
        "lines"   => "222-223",
        "quote"   => "order test (after basins exist):  Delta_{a,b,s}(rho)=|| Phi_a Phi_b rho - Phi_b Phi_a rho ||_1\nratchet schedule:     d(Phi_D(rho), Phi_I(rho)) > delta with work/readout change + wrong-order controls failing",
    ),
    Dict(
        "file"    => "system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md",
        "section" => "Stage 2 - Pairwise Nested-Layer Test",
        "lines"   => "180-185",
        "quote"   => "NestedPairTest_Li_Lj:\n  (completed parent Li, completed parent Lj, common carrier projection P,\n   admissible nesting orders [Li then Lj, Lj then Li], controls)\n  -> paired output signatures, survivor sets, entropy/readout deltas,\n     order gaps, failed controls, blockers",
    ),
    Dict(
        "file"    => "system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md",
        "section" => "Stage 2 - Pairwise Nested-Layer Test (required preflight)",
        "lines"   => "188-198",
        "quote"   => "carrier compatibility:\n  same PEPS3D K or explicit projection between carriers\nspinor compatibility:\n  spinor payloads or spinor-derived densities map without dense closure\nreadout compatibility:\n  QIT readouts have shared cut/provenance\nblocked consumers:\n  stacking/flux/Xi/Phi0/Axis0/FEP/physics remain blocked unless explicitly opened",
    ),
    Dict(
        "file"    => "system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md",
        "section" => "Stage 1 - Intrinsic Order Test (stop condition)",
        "lines"   => "165-170",
        "quote"   => "Stop condition:\n\nif the order gap survives commuting or order-erased controls, the test is\ninvalid and must be repaired before any nesting test",
    ),
    Dict(
        "file"    => "system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md",
        "section" => "Enforcement Rule",
        "lines"   => "295-296",
        "quote"   => "If `parent_completion_status` is missing, stale, or only `bounded_scout`, the\norder/nesting test is blocked.",
    ),
    Dict(
        "file"    => "system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md",
        "section" => "Stage 0 - Parent Completion Audit (completion_status enum)",
        "lines"   => "118-124",
        "quote"   => "completion_status:\n  incomplete\n  complete_for_intrinsic_order_test\n  complete_for_pairwise_nesting_test\n  complete_for_multi_layer_nesting_test",
    ),
]

# Claims the docs make that this scaffold does NOT yet implement for real.
# These are honest GAPS, not faked. Anything not on a page I read goes here.
const GAPS = [
    "Real per-layer maps are NOT imported. The layer .jl files are scripts that " *
    "run main() and write receipts; they do not export a callable finite map " *
    "psi -> psi'. Until each layer exports an admitted map, the maps here are STUBBED.",
    "No layer result carries parent_completion_status (all rows report MISSING). " *
    "Per the Enforcement Rule quote, every pair is therefore BLOCKED for the real " *
    "pairwise nesting test. This scaffold runs the harness shape only.",
    "PEPS3D K=(V,E,F,C) carrier and the explicit finite projection P between " *
    "carriers (gate Stage-2 preflight) are NOT built here. The carrier is a single " *
    "2-component spinor payload + finite phase/chirality/anchor metadata.",
    "The Hopf carrier objects quoted at stack-doc lines 202-205 (T_eta_k, pi_H, " *
    "A_Hopf, rho_{v,s,k}, H_L=+H0/H_R=-H0) are NOT instantiated as the live carrier; " *
    "they are quoted as the target the real maps must act on.",
    "Trace-distance ||.||_1 from stack-doc line 222 is the doc's order metric; this " *
    "scaffold reports a finite-signature L2 gap AND a density trace-distance gap, but " *
    "the density is the stub psi psi^dag, not a real layer-emitted rho.",
    "Stage 1 intrinsic order test per parent is NOT run here as a precondition; the " *
    "gate requires it before Stage 2. This file is the Stage-2 *shape* only.",
]

# ---------------------------------------------------------------------
# Layer registry. Each row points at the current best-available finite layer
# object (source + result) and is marked real-vs-stub by its result receipt.
# Filenames verified to exist on disk in this directory at build time.
# ---------------------------------------------------------------------
struct LayerSpec
    id::String
    label::String
    source_file::String
    result_file::String
end

const LAYER_ROWS = LayerSpec[
    LayerSpec("R0",  "root finite carrier/probe",              "R0_layer.jl",            "R0_layer_results.json"),
    LayerSpec("L0",  "finite response/effect/path quotient",   "L0_layer.jl",            "L0_layer_results.json"),
    LayerSpec("L1",  "spinor/density carrier",                 "L1_layer.jl",            "L1_layer_results.json"),
    LayerSpec("L2",  "S3 spinor carrier",                      "L2_layer.jl",            "L2_layer_results.json"),
    LayerSpec("L3",  "S2 projective/Hopf base",                "L3_layer.jl",            "L3_layer_results.json"),
    LayerSpec("L4",  "Hopf fibration S3->S2 U(1)",             "L4_layer.jl",            "L4_layer_results.json"),
    LayerSpec("L5",  "nested Hopf tori / torus leaf family",   "L5_layer.jl",            "L5_layer_results.json"),
    LayerSpec("L6",  "connection / holonomy geometry",         "L6_layer.jl",            "L6_layer_results.json"),
    LayerSpec("L7",  "Weyl spinor bundle",                     "L7_layer.jl",            "L7_layer_results.json"),
    LayerSpec("L8",  "chirality orientation cover",            "L8_layer.jl",            "L8_layer_results.json"),
    LayerSpec("L9",  "Clifford / quaternion module",           "L9_layer.jl",            "L9_layer_codex_results.json"),
    LayerSpec("L10", "terrain / channel / generator",          "L10_layer.jl",           "L10_layer_results.json"),
    LayerSpec("L11", "operator-substage local cell",           "L11_layer.jl",           "L11_layer_codex_results.json"),
    LayerSpec("L12", "entropy / cut / communication",          "L12_layer.jl",           "L12_layer_results.json"),
    LayerSpec("L13", "gluing / groupoid / dynamic transition", "L13_layer_codex.jl",     "L13_layer_codex_results.json"),
]

# ---------------------------------------------------------------------
# Minimal JSON: prefer the JSON package; fall back to a built-in emitter so the
# file runs under bare `julia` with no project env. Reading layer receipts is
# done by the same path (package if present, else a tiny scalar extractor).
# ---------------------------------------------------------------------
const HAVE_JSON = let ok = false
    try
        @eval import JSON
        ok = true
    catch
        ok = false
    end
    ok
end

# Built-in JSON serializer (objects, arrays, strings, numbers, bools, nothing).
function json_emit(io::IO, x, indent::Int)
    pad  = "  "^indent
    pad2 = "  "^(indent + 1)
    if x isa AbstractDict
        isempty(x) && (print(io, "{}"); return)
        println(io, "{")
        ks = collect(keys(x))
        for (i, k) in enumerate(ks)
            print(io, pad2, json_str(string(k)), ": ")
            json_emit(io, x[k], indent + 1)
            println(io, i < length(ks) ? "," : "")
        end
        print(io, pad, "}")
    elseif x isa AbstractVector
        isempty(x) && (print(io, "[]"); return)
        println(io, "[")
        for (i, v) in enumerate(x)
            print(io, pad2)
            json_emit(io, v, indent + 1)
            println(io, i < length(x) ? "," : "")
        end
        print(io, pad, "]")
    elseif x isa AbstractString
        print(io, json_str(x))
    elseif x isa Bool
        print(io, x ? "true" : "false")
    elseif x === nothing || x === missing
        print(io, "null")
    elseif x isa Integer
        print(io, string(x))
    elseif x isa Real
        print(io, isfinite(x) ? @sprintf("%.12g", x) : "null")
    else
        print(io, json_str(string(x)))
    end
end

function json_str(s::AbstractString)
    buf = IOBuffer()
    print(buf, '"')
    for c in s
        if c == '"';      print(buf, "\\\"")
        elseif c == '\\'; print(buf, "\\\\")
        elseif c == '\n'; print(buf, "\\n")
        elseif c == '\r'; print(buf, "\\r")
        elseif c == '\t'; print(buf, "\\t")
        else;             print(buf, c)
        end
    end
    print(buf, '"')
    return String(take!(buf))
end

function write_json(path::String, obj)
    open(path, "w") do io
        if HAVE_JSON
            Base.invokelatest(getfield(Main, :JSON).print, io, obj, 2)
            write(io, "\n")
        else
            json_emit(io, obj, 0)
            write(io, "\n")
        end
    end
end

# Extract a scalar field from a layer receipt without a full JSON parser when
# the package is missing. Returns the raw token string, or nothing.
function grep_scalar(text::AbstractString, key::AbstractString)
    m = match(Regex("\"" * key * "\"\\s*:\\s*(true|false|null|\"[^\"]*\"|-?[0-9.eE+]+)"), text)
    m === nothing && return nothing
    tok = m.captures[1]
    if tok == "true";  return true
    elseif tok == "false"; return false
    elseif tok == "null";  return nothing
    elseif startswith(tok, "\""); return String(tok[2:end-1])
    else; return tok
    end
end

# Read the layer receipt and classify the layer object as real vs stub for the
# ratchet's purposes. Two flags drive everything downstream:
#   source_present     : the result receipt exists and parses (object exists)
#   parent_complete    : parent_completion_status is a real Stage-2+ value
function read_layer_status(spec::LayerSpec)
    rpath = joinpath(THIS_DIR, spec.result_file)
    if !isfile(rpath)
        return (source_present = false, all_pass = nothing,
                parent_completion_status = "MISSING_RESULT_FILE",
                classification = "missing", parent_complete = false)
    end
    all_pass = nothing
    pcs = "MISSING"
    classification = "unknown"
    if HAVE_JSON
        d = try
            Base.invokelatest(getfield(Main, :JSON).parsefile, rpath)
        catch
            Dict{String,Any}()
        end
        all_pass = get(d, "all_pass", nothing)
        pcs = string(get(d, "parent_completion_status", "MISSING"))
        classification = string(get(d, "classification", "unknown"))
    else
        text = read(rpath, String)
        all_pass = grep_scalar(text, "all_pass")
        pcsv = grep_scalar(text, "parent_completion_status")
        pcs = pcsv === nothing ? "MISSING" : string(pcsv)
        clv = grep_scalar(text, "classification")
        classification = clv === nothing ? "unknown" : string(clv)
    end
    parent_complete = pcs in (
        "complete_for_pairwise_nesting_test",
        "complete_for_multi_layer_nesting_test",
    )
    return (source_present = true, all_pass = all_pass,
            parent_completion_status = pcs, classification = classification,
            parent_complete = parent_complete)
end

# ---------------------------------------------------------------------
# CARRIER + F01/N01 DRIVER
#
# F01 (finite carrier/probe/operator/path set): the carrier is a finite-data
# object -- a normalized 2-component ComplexF64 spinor payload psi in S^3 ⊂ C^2
# plus finite metadata (phase, chirality sign, carrier anchor) -- and the path
# set is the two admissible nesting words {A then B, B then A}. The density
# rho = psi psi^dag follows the stack-doc carrier line
#   rho_{v,L,k}=psi_{v,L,k} psi_{v,L,k}^dag   (lines 202-205).
#
# N01 (noncommuting/order-sensitive operation): each layer is stubbed with a
# finite 2x2 noncommuting operator + a phase twist + a chirality flip, so that
# A.B and B.A land on different carrier signatures. The order gap is the
# doc metric in spirit:
#   Delta = || Phi_a Phi_b rho - Phi_b Phi_a rho ||_1   (stack-doc line 222),
# reported here both as a finite-signature L2 gap and a density trace-distance.
#
# COLLAPSE CONTROLS are INDEPENDENT (this is the key design fix): erasing phase
# leaves the carrier matrix and chirality intact, etc. Each control zeroes ONE
# signature channel so we can see which channel carries the order gap, matching
# "controls proving the gap collapses when order/phase/chirality/carrier is
# erased" (stack-doc lines 138-140) treated as four separable knobs.
# ---------------------------------------------------------------------
mutable struct CarrierState
    payload::Vector{ComplexF64}   # psi in S^3 ⊂ C^2 (normalized)
    phase::Float64                # accumulated U(1) phase (Hopf-fiber proxy)
    chirality::Int                # +1 / -1 (L/R Weyl sheet proxy)
    carrier_anchor::String        # carrier-identity tag; "erased" kills the map
    order_trace::Vector{String}
end

struct LayerMap
    spec::LayerSpec
    matrix::Matrix{ComplexF64}    # noncommuting 2x2 op (N01 stub)
    phase_twist::Float64          # U(1) phase increment (Hopf-fiber proxy)
    chirality_flip::Bool          # flips the L/R sheet sign
    real_map::Bool                # true only when a real parent map is wired
end

struct ControlFlags
    erase_order::Bool      # symmetrize the word -> A.B and B.A become identical
    erase_phase::Bool      # zero the phase channel
    erase_chirality::Bool  # pin chirality to +1
    erase_carrier::Bool    # collapse the matrix action to identity
end
const NO_ERASE = ControlFlags(false, false, false, false)

# Distinct noncommuting 2x2 operators (Pauli/Hadamard/phase/rotation family).
# These STUB the layer maps; real_map stays false until a parent map is imported.
function pauli_family()
    X = ComplexF64[0 1; 1 0]
    Y = ComplexF64[0 -im; im 0]
    Z = ComplexF64[1 0; 0 -1]
    H = (1 / sqrt(2)) * ComplexF64[1 1; 1 -1]
    S = ComplexF64[1 0; 0 im]
    R = ComplexF64[cos(0.37)+0im -sin(0.37); sin(0.37) cos(0.37)]
    return [X, Y, Z, H, S, R, X*S, H*S, S*H, X*H, Y*H, Z*S, R*X, R*Y, R*Z]
end

function build_layer_maps(specs::Vector{LayerSpec})
    mats = pauli_family()
    maps = LayerMap[]
    for (idx, spec) in enumerate(specs)
        M = mats[mod1(idx, length(mats))]
        push!(maps, LayerMap(spec, M, 0.07 * idx, isodd(idx), false))
    end
    return maps
end

function initial_state()
    raw = ComplexF64[1.0 + 0.0im, 0.31 + 0.17im]
    psi = raw ./ norm(raw)
    return CarrierState(psi, 0.23, 1, "finite_spinor_payload_S3_C2", String[])
end

copy_state(s::CarrierState) =
    CarrierState(copy(s.payload), s.phase, s.chirality, s.carrier_anchor, copy(s.order_trace))

# Apply one layer map to the carrier under the given control flags. Each control
# zeroes exactly ONE channel; they do not bleed into each other.
function apply_layer(s::CarrierState, lm::LayerMap, ctrl::ControlFlags)
    t = copy_state(s)
    M     = ctrl.erase_carrier   ? Matrix{ComplexF64}(I, 2, 2) : lm.matrix
    twist = ctrl.erase_phase     ? 0.0                          : lm.phase_twist
    flip  = ctrl.erase_chirality ? false                        : lm.chirality_flip

    t.payload = M * t.payload
    nrm = norm(t.payload)
    nrm > 0 && (t.payload ./= nrm)

    # phase channel: a global U(1) factor carried in metadata (Hopf-fiber proxy)
    if !ctrl.erase_phase
        t.payload .*= exp(im * twist)
        t.phase = mod(t.phase + twist, 2pi)
    else
        t.phase = 0.0
    end

    # chirality channel
    if ctrl.erase_chirality
        t.chirality = 1
    elseif flip
        t.chirality = -t.chirality
    end

    # carrier-identity channel
    t.carrier_anchor = ctrl.erase_carrier ? "erased" : s.carrier_anchor

    push!(t.order_trace, lm.spec.id)
    return t
end

# Run a two-layer word. erase_order symmetrizes the schedule so A.B and B.A
# become the SAME word (averaged), which must drive the order gap to ~0.
function run_word(first::LayerMap, second::LayerMap, ctrl::ControlFlags)
    s0 = initial_state()
    if ctrl.erase_order
        # order-erased control: apply the average of both single-step maps twice,
        # so the schedule no longer distinguishes A-then-B from B-then-A.
        avg = LayerMap(first.spec,
                       (first.matrix .+ second.matrix) ./ 2,
                       (first.phase_twist + second.phase_twist) / 2,
                       false, false)
        return apply_layer(apply_layer(s0, avg, NO_ERASE), avg, NO_ERASE)
    end
    return apply_layer(apply_layer(s0, first, ctrl), second, ctrl)
end

# Finite signature vector (F01 readout channels), and the L2 gap between two.
function signature(s::CarrierState)
    return [
        real(s.payload[1]), imag(s.payload[1]),
        real(s.payload[2]), imag(s.payload[2]),
        s.phase,
        Float64(s.chirality),
        s.carrier_anchor == "erased" ? 0.0 : 1.0,
    ]
end
sig_gap(a::CarrierState, b::CarrierState) = norm(signature(a) .- signature(b))

# Density rho = psi psi^dag and trace distance ||rho_a - rho_b||_1 = sum |eig|.
density(s::CarrierState) = s.payload * adjoint(s.payload)
function trace_distance(a::CarrierState, b::CarrierState)
    D = density(a) - density(b)
    return sum(abs, eigvals(Hermitian((D + adjoint(D)) / 2)))
end

# ---------------------------------------------------------------------
# Pairwise test for one (A, B): AB vs BA, base gap + four independent controls.
# A surviving ratchet edge requires: base order gap > floor AND every collapse
# control drives the gap to ~0 (the stop-condition guard from gate lines 165-170:
# an order gap that survives commuting/order-erased controls is INVALID).
# ---------------------------------------------------------------------
function pair_result(a::LayerMap, b::LayerMap, a_complete::Bool, b_complete::Bool)
    ab = run_word(a, b, NO_ERASE)
    ba = run_word(b, a, NO_ERASE)
    base_sig_gap = sig_gap(ab, ba)
    base_td_gap  = trace_distance(ab, ba)

    function ctrl_gap(c::ControlFlags)
        return (sig = sig_gap(run_word(a, b, c), run_word(b, a, c)),
                td  = trace_distance(run_word(a, b, c), run_word(b, a, c)))
    end
    g_order = ctrl_gap(ControlFlags(true,  false, false, false))
    g_phase = ctrl_gap(ControlFlags(false, true,  false, false))
    g_chir  = ctrl_gap(ControlFlags(false, false, true,  false))
    g_carr  = ctrl_gap(ControlFlags(false, false, false, true))

    controls = Dict(
        "erase_order"     => Dict("sig_gap" => g_order.sig, "trace_distance" => g_order.td),
        "erase_phase"     => Dict("sig_gap" => g_phase.sig, "trace_distance" => g_phase.td),
        "erase_chirality" => Dict("sig_gap" => g_chir.sig,  "trace_distance" => g_chir.td),
        "erase_carrier"   => Dict("sig_gap" => g_carr.sig,  "trace_distance" => g_carr.td),
    )
    # "controls collapse" = order-erased and carrier-erased gaps vanish. Phase and
    # chirality are reported but may legitimately not zero the gap alone (the gap
    # can live in the matrix channel); the binding collapse is order + carrier.
    order_collapses   = g_order.sig <= GAP_FLOOR
    carrier_collapses = g_carr.sig  <= GAP_FLOOR
    controls_collapse = order_collapses && carrier_collapses

    # Scaffold edge: noncommutativity present AND the invalidating controls
    # collapse (so the gap is real order pressure, not a control artifact).
    scaffold_survives = base_sig_gap > GAP_FLOOR && controls_collapse

    # Real edge: the scaffold survives AND both parents pass the parent-completion
    # gate AND both maps are real. None today (see GAPS / parent table).
    real_gate_open = a_complete && b_complete && a.real_map && b.real_map
    real_survives  = scaffold_survives && real_gate_open

    return Dict(
        "pair"               => [a.spec.id, b.spec.id],
        "labels"             => [a.spec.label, b.spec.label],
        "source_files"       => [a.spec.source_file, b.spec.source_file],
        "result_files"       => [a.spec.result_file, b.spec.result_file],
        "AB_trace"           => ab.order_trace,
        "BA_trace"           => ba.order_trace,
        "base_order_gap_sig" => base_sig_gap,
        "base_order_gap_trace_distance" => base_td_gap,
        "controls"           => controls,
        "order_control_collapses"   => order_collapses,
        "carrier_control_collapses" => carrier_collapses,
        "controls_collapse"  => controls_collapse,
        "scaffold_survives"  => scaffold_survives,
        "maps_are_real"      => [a.real_map, b.real_map],
        "real_gate_open"     => real_gate_open,
        "real_survives"      => real_survives,
        "real_run_status"    => real_gate_open ?
            "ready_for_real_parent_maps" :
            "blocked_missing_parent_completion_or_real_map",
    )
end

# ---------------------------------------------------------------------
function main()
    specs   = LAYER_ROWS
    maps    = build_layer_maps(specs)
    status  = [read_layer_status(s) for s in specs]
    complete = [st.parent_complete for st in status]

    layer_table = Vector{Any}()
    for (i, s) in enumerate(specs)
        st = status[i]
        push!(layer_table, Dict(
            "id"             => s.id,
            "label"          => s.label,
            "source_file"    => joinpath("layers", s.source_file),
            "result_file"    => joinpath("layers", s.result_file),
            "source_present" => st.source_present,
            "all_pass"       => st.all_pass,
            "classification" => st.classification,
            "parent_completion_status" => st.parent_completion_status,
            "parent_complete_for_pairwise" => st.parent_complete,
            "map_status"     => maps[i].real_map ? "real_parent_map_wired" :
                                "STUBBED_pending_parent_completion",
        ))
    end

    pairs = Vector{Any}()
    for i in 1:(length(maps) - 1), j in (i + 1):length(maps)
        push!(pairs, pair_result(maps[i], maps[j], complete[i], complete[j]))
    end

    scaffold_edges = [p["pair"] for p in pairs if p["scaffold_survives"]]
    real_edges     = [p["pair"] for p in pairs if p["real_survives"]]
    n_complete     = count(complete)

    result = Dict(
        "artifact"          => "ratchet_order_test",
        "generated_at"      => string(now()),
        "language"          => "julia",
        "classification"    => "scaffold_only",
        "promotion_allowed" => false,
        "claim_ceiling"     =>
            "F01/N01 pairwise A.B-vs-B.A order harness with independent erase " *
            "order/phase/chirality/carrier controls. Layer maps are STUBBED. No " *
            "pair is admitted as a real pairwise nesting test: every layer's " *
            "parent_completion_status is missing, so the gate's Enforcement Rule " *
            "blocks the real test. Surviving-order graph below is SCAFFOLD-ONLY.",
        "f01_witness" => Dict(
            "finite_carrier" => "normalized 2-component ComplexF64 spinor psi in S^3 subset C^2 + finite metadata",
            "probe_channels" => ["payload re/im", "phase", "chirality sign", "carrier anchor"],
            "path_set"       => ["A then B", "B then A"],
            "density"        => "rho = psi psi^dag (2x2 PSD trace-1)",
        ),
        "n01_witness" => Dict(
            "operators"   => "distinct noncommuting 2x2 maps per layer (Pauli/Hadamard/phase/rotation stubs)",
            "order_gap"   => "||sig(A(B(psi))) - sig(B(A(psi)))|| and ||rho_AB - rho_BA||_1",
            "controls"    => ["erase_order", "erase_phase", "erase_chirality", "erase_carrier"],
            "metric_note" => "trace-distance ||.||_1 follows stack-doc line 222 Delta metric",
        ),
        "doc_quotes" => DOC_QUOTES,
        "gaps"       => GAPS,
        "parent_completion" => Dict(
            "gate_rule" => "If parent_completion_status is missing, stale, or only " *
                           "bounded_scout, the order/nesting test is blocked. " *
                           "(NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md, Enforcement Rule)",
            "layers_with_pairwise_completion" => n_complete,
            "all_blocked" => n_complete == 0,
        ),
        "layer_table"        => layer_table,
        "pairs_tested"       => length(pairs),
        "surviving_order_graph_scaffold" => scaffold_edges,
        "surviving_order_graph_real"     => real_edges,
        "real_graph_status"  => isempty(real_edges) ?
            "blocked_no_pair_has_parent_completion_status" : "has_real_ready_edges",
        "required_parent_complete_layers_for_full_real_ratchet" => [s.id for s in specs],
        "pair_results"       => pairs,
        "blocked_consumers"  => [
            "layer_stacking_admission", "flux", "Xi", "Phi0",
            "Axis0", "FEP", "physics", "final_manifold_admission",
        ],
    )

    write_json(RESULT_PATH, result)

    println("ratchet_order_test")
    println("  json_backend:            ", HAVE_JSON ? "JSON package" : "builtin emitter")
    println("  result_path:             ", RESULT_PATH)
    println("  classification:          scaffold_only")
    println("  pairs_tested:            ", length(pairs))
    println("  scaffold_surviving_edges:", length(scaffold_edges))
    println("  real_surviving_edges:    ", length(real_edges))
    println("  layers_pairwise_complete:", n_complete, " / ", length(specs))
    println("  real_graph_status:       ", result["real_graph_status"])
    println("  GAPS (not implemented):  ", length(GAPS))
    println("  required_parent_complete_layers_for_full_real_ratchet:")
    println("    ", join([s.id for s in specs], ", "))
end

main()

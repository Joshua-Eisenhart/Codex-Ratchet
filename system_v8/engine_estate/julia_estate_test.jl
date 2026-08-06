# julia_estate_test.jl — v8 engine-estate probe, Julia phase (authoritative substrate)
# Ceiling: working-sim evidence only. promotion_allowed: false. NOT proof-level.
# Each section exercises one installed package on real manifold content and
# prints CHECK lines computed from numbers, never from prose.

using JSON3, Dates, LinearAlgebra, Printf

const RESULTS = Dict{String,Any}(
    "phase" => "julia",
    "date" => string(now()),
    "julia_version" => string(VERSION),
    "promotion_allowed" => false,
    "claim_ceiling" => "runs + passes-listed-checks in this session; not canonical",
    "sections" => Dict{String,Any}(),
)

function record!(name, status, checks, timing; note="")
    RESULTS["sections"][name] = Dict(
        "status" => status, "checks" => checks, "seconds" => round(timing; digits=2), "note" => note)
end

macro section(name, body)
    quote
        local t0 = time()
        local nm = $(esc(name))
        println("\n=== ", nm, " ===")
        try
            local checks = $(esc(body))
            local ok = all(last.(collect(checks)) .== true)
            record!(nm, ok ? "PASS" : "FAIL", Dict(checks), time() - t0)
            for (k, v) in checks
                println("CHECK ", nm, " :: ", k, " => ", v ? "PASS" : "FAIL")
            end
        catch err
            record!(nm, "BLOCKED", Dict{String,Bool}(), time() - t0; note=sprint(showerror, err))
            println("BLOCKED ", nm, " :: ", sprint(showerror, err))
        end
    end
end

binent(p) = (p <= 0 || p >= 1) ? 0.0 : -p*log(p) - (1-p)*log(1-p)  # nats

# ---------------------------------------------------------------------------
# 1. QuantumOptics — L8 sheet generators: GKSL amplitude damping + depolarizing
#    Laws checked: p_e(t)=exp(-γt); S_vN = h(p_e) (nats); depolarizing
#    ρ(t)=I/2 + exp(-γt)(ρ0 - I/2) so S = h((1+e^{-γt})/2) → ln 2 monotonically.
# ---------------------------------------------------------------------------
@section "quantumoptics_gksl_L8" begin
    using QuantumOptics
    b = SpinBasis(1//2)
    γ = 1.0
    T = collect(range(0.0, 4.0; length=41))
    H = 0.0 * sigmaz(b)                        # pure dissipative sheet
    ρ0 = dm(spinup(b))                          # excited state

    # amplitude damping
    _, ρt = timeevolution.master(T, ρ0, H, [sqrt(γ)*sigmam(b)])
    pe = [real(expect(dm(spinup(b)), ρ)) for ρ in ρt]
    S  = [real(entropy_vn(ρ)) for ρ in ρt]
    dev_p = maximum(abs.(pe .- exp.(-γ .* T)))
    dev_S = maximum(abs.(S .- binent.(exp.(-γ .* T))))
    @printf("amp-damp: max|p_e - e^{-γt}| = %.3e, max|S - h(p)| = %.3e\n", dev_p, dev_S)

    # depolarizing
    Js = [sqrt(γ/4)*sigmax(b), sqrt(γ/4)*sigmay(b), sqrt(γ/4)*sigmaz(b)]
    _, ρtd = timeevolution.master(T, ρ0, H, Js)
    Sd = [real(entropy_vn(ρ)) for ρ in ρtd]
    Sd_law = binent.((1 .+ exp.(-γ .* T)) ./ 2)
    dev_Sd = maximum(abs.(Sd .- Sd_law))
    mono = all(diff(Sd) .> -1e-9)
    @printf("depol: max|S - law| = %.3e, S(end) = %.6f (ln2 = %.6f)\n", dev_Sd, Sd[end], log(2))

    ["amp_damp_population_law_1e-6"  => dev_p < 1e-6,
     "amp_damp_entropy_law_1e-6"    => dev_S < 1e-6,
     "depol_entropy_law_1e-6"       => dev_Sd < 1e-6,
     "depol_entropy_monotone"       => mono,
     "depol_endpoint_near_ln2"      => abs(Sd[end] - log(2)) < 0.02]
end

# ---------------------------------------------------------------------------
# 2. QuantumClifford — L6 stabilizer content: GHZ built by Clifford circuit
#    equals canonical GHZ; Schmidt/stabilizer cut entropy across 1|23 = 1 bit.
# ---------------------------------------------------------------------------
@section "quantumclifford_ghz_L6" begin
    using QuantumClifford
    s = one(Stabilizer, 3)                     # |000>
    apply!(s, sHadamard(1)); apply!(s, sCNOT(1, 2)); apply!(s, sCNOT(2, 3))
    same = canonicalize!(copy(s)) == canonicalize!(copy(ghz(3)))
    # qualified: QuantumOptics also exports entanglement_entropy (name clash)
    ee1  = QuantumClifford.entanglement_entropy(copy(s), 1:1, Val(:clip))   # bits
    ee2  = QuantumClifford.entanglement_entropy(copy(s), 1:2, Val(:clip))
    ee_prod = QuantumClifford.entanglement_entropy(one(Stabilizer, 3), 1:1, Val(:clip))
    println("circuit==ghz(3): ", same, "; EE(1|23)=", ee1, " EE(12|3)=", ee2,
            " EE(product)=", ee_prod)
    ["circuit_state_equals_ghz" => same,
     "cut_1v23_entropy_1bit"    => ee1 == 1,
     "cut_12v3_entropy_1bit"    => ee2 == 1,
     "product_state_entropy_0"  => ee_prod == 0]
end

# ---------------------------------------------------------------------------
# 3. CliffordAlgebras — L10 gamma5 grading in Cl(4,0):
#    γ5 = e1e2e3e4 squares to +1 and anticommutes with every generator.
# ---------------------------------------------------------------------------
@section "cliffordalgebras_gamma5_L10" begin
    using CliffordAlgebras
    ca = CliffordAlgebra(4)
    gs = (ca.e1, ca.e2, ca.e3, ca.e4)
    γ5 = ca.e1 * ca.e2 * ca.e3 * ca.e4
    sq = γ5 * γ5
    sq_ok = scalar(sq) == 1 && all(==(0), CliffordAlgebras.coefficients(sq - ca.𝟏 * 1))
    anti_ok = all(all(==(0), CliffordAlgebras.coefficients(γ5*g + g*γ5)) for g in gs)
    # grading: γ5-commutant — even bivectors commute with γ5
    biv_ok = all(all(==(0), CliffordAlgebras.coefficients(γ5*bv - bv*γ5))
                 for bv in (ca.e1e2, ca.e1e3, ca.e2e3, ca.e1e4, ca.e3e4))
    println("γ5² = ", sq, "; anticommutes with all eᵢ: ", anti_ok,
            "; commutes with bivectors: ", biv_ok)
    ["gamma5_squares_to_plus1"        => sq_ok,
     "gamma5_anticommutes_generators" => anti_ok,
     "gamma5_commutes_bivectors"      => biv_ok]
end

# ---------------------------------------------------------------------------
# 4. Grassmann — independent exterior-algebra cross-check of the same grading:
#    in Λ(V₄) with signature ++++ the pseudoscalar squares to +1 and 1-vectors
#    anticommute.
# ---------------------------------------------------------------------------
@section "grassmann_pseudoscalar_L10" begin
    # @basis expands at lowering time, so this section runs via include_string.
    # Qualified Grassmann.basis"" needed: QuantumClifford also exports S"" (clash).
    include_string(Main, """
    using Grassmann
    Grassmann.basis"++++"                  # defines v, v1..v4, v12, ..., v1234
    let ps2 = v1234 * v1234,
        anti = v1*v2 + v2*v1,
        mixed = v12 * v34 - v1234          # e12∧e34 = e1234 in ++++
        println("v1234² = ", ps2, "; v1v2+v2v1 = ", anti, "; v12*v34-v1234 = ", mixed)
        ["pseudoscalar_squares_to_plus1" => iszero(ps2 - 1),
         "one_vectors_anticommute"       => iszero(anti),
         "bivector_product_is_pseudoscalar" => iszero(mixed)]
    end
    """)
end

# ---------------------------------------------------------------------------
# 5. ITensors/ITensorMPS — L7 cut content: Schmidt decomposition across a
#    3-site MPS. GHZ across any cut: Schmidt values {1/2,1/2}, S = ln 2.
#    Product state control: S = 0.
# ---------------------------------------------------------------------------
@section "itensors_schmidt_cut_L7" begin
    using ITensors, ITensorMPS
    sites = siteinds("Qubit", 3)
    A = zeros(2, 2, 2); A[1,1,1] = 1/sqrt(2); A[2,2,2] = 1/sqrt(2)   # GHZ
    ψ = MPS(A, sites; cutoff=1e-14)
    function cut_spectrum(ψ, b)
        ψo = orthogonalize(ψ, b)
        inds_left = b == 1 ? (siteind(ψo, 1),) :
                    (linkinds(ψo, b-1)..., siteind(ψo, b))
        _, Sm, _ = svd(ψo[b], inds_left...)
        [Sm[i, i]^2 for i in 1:dim(Sm, 1)]
    end
    p1 = cut_spectrum(ψ, 1)                  # cut 1|23
    p2 = cut_spectrum(ψ, 2)                  # cut 12|3
    ent(p) = -sum(x -> x < 1e-14 ? 0.0 : x*log(x), p)
    ψprod = MPS(sites, "0")
    pp = cut_spectrum(ψprod, 1)
    @printf("GHZ cut1 spectrum %s S=%.6f; cut2 S=%.6f; product S=%.6f (ln2=%.6f)\n",
            string(round.(p1; digits=6)), ent(p1), ent(p2), ent(pp), log(2))
    ["ghz_schmidt_values_half_half" => length(p1) == 2 && all(abs.(p1 .- 0.5) .< 1e-10),
     "ghz_cut1_entropy_ln2"         => abs(ent(p1) - log(2)) < 1e-10,
     "ghz_cut2_entropy_ln2"         => abs(ent(p2) - log(2)) < 1e-10,
     "product_cut_entropy_zero"     => ent(pp) < 1e-12]
end

# ---------------------------------------------------------------------------
# 6. Attractors — L13 basin content: bistable map (Euler of ẋ = x - x³),
#    attractors near x = ±1, symmetric grid → basin fractions ≈ 1/2 each.
#    NOTE: extract_attractors/basins_of_attraction are broken in this install
#    (Attractors v1.37.0 references `referenced_sciml_model`, removed from the
#    installed DynamicalSystemsBase) — mapped basins via direct mapper labels.
# ---------------------------------------------------------------------------
@section "attractors_bistable_basins_L13" begin
    using Attractors, StaticArrays
    f(u, p, n) = SVector(u[1] + 0.1*(u[1] - u[1]^3), 0.5*u[2])
    ds = DeterministicIteratedMap(f, SVector(0.5, 0.0))
    grid = (range(-2.0, 2.0; length=81), range(-1.0, 1.0; length=21))
    mapper = AttractorsViaRecurrences(ds, grid)
    labels = Dict{Int,Int}()
    lab_of = Dict{Tuple{Float64,Float64},Int}()
    for x in grid[1], y in grid[2]
        x == 0.0 && continue                  # separatrix line, excluded
        l = mapper(SVector(x, y))
        labels[l] = get(labels, l, 0) + 1
        lab_of[(x, y)] = l
    end
    ks = sort(collect(keys(labels)))
    total = sum(values(labels))
    fracs = [labels[k]/total for k in ks]
    # attractor side check: all x>0 initial conditions share one label, x<0 the other
    lpos = unique([lab_of[(x, y)] for x in grid[1] if x > 0 for y in grid[2]])
    lneg = unique([lab_of[(x, y)] for x in grid[1] if x < 0 for y in grid[2]])
    println("labels found: ", ks, " fractions: ", round.(fracs; digits=4),
            " pos-side labels: ", lpos, " neg-side labels: ", lneg)
    ["two_attractors_found"        => length(ks) == 2,
     "basins_symmetric_half_half"  => all(abs.(fracs .- 0.5) .< 0.02),
     "positive_side_single_basin"  => length(lpos) == 1,
     "negative_side_single_basin"  => length(lneg) == 1,
     "basins_disjoint"             => length(lpos) == 1 && length(lneg) == 1 && lpos[1] != lneg[1]]
end

# ---------------------------------------------------------------------------
# 7. Octonions — L10 octonion-adjacent control: norm composition holds,
#    associativity fails on a concrete witness (nonassociativity is real).
# ---------------------------------------------------------------------------
@section "octonions_nonassoc_L10" begin
    using Octonions
    e = [Octonion([i == j ? 1.0 : 0.0 for j in 1:8]...) for i in 1:8]
    a, b, c = e[2], e[3], e[5]
    assoc_defect = abs((a*b)*c - a*(b*c))
    x = Octonion(randn(8)...); y = Octonion(randn(8)...)
    comp_defect = Base.abs(abs(x*y) - abs(x)*abs(y))
    println("|(e1e2)e4 - e1(e2e4)| = ", assoc_defect, "; |‖xy‖-‖x‖‖y‖| = ", comp_defect)
    ["norm_composition_holds_1e-12" => comp_defect < 1e-12,
     "nonassociativity_witnessed"   => assoc_defect > 1.0]
end

# ---------------------------------------------------------------------------
# receipt
# ---------------------------------------------------------------------------
using Pkg
deps = Pkg.dependencies()
wanted = ["QuantumOptics", "QuantumClifford", "CliffordAlgebras", "Grassmann",
          "ITensors", "ITensorMPS", "Attractors", "Octonions", "Z3", "JSON3"]
RESULTS["package_versions"] = Dict(
    d.name => string(d.version) for (_, d) in deps if d.name in wanted)

npass = count(s -> s["status"] == "PASS", values(RESULTS["sections"]))
nfail = count(s -> s["status"] == "FAIL", values(RESULTS["sections"]))
nblocked = count(s -> s["status"] == "BLOCKED", values(RESULTS["sections"]))
RESULTS["summary"] = Dict("pass" => npass, "fail" => nfail, "blocked" => nblocked)
RESULTS["known_breakage"] = Dict(
    "Attractors.extract_attractors" =>
        "UndefVarError referenced_sciml_model (Attractors v1.37.0 vs installed DynamicalSystemsBase); core mapper labels work, worked around")

outdir = get(ENV, "ENGINE_ESTATE_RESULTS_DIR", joinpath(@__DIR__, "results", "julia"))
mkpath(outdir)
outfile = joinpath(outdir, "receipt.json")
open(outfile, "w") do io
    JSON3.pretty(io, RESULTS)
end
println("\n=== SUMMARY: pass=", npass, " fail=", nfail, " blocked=", nblocked, " ===")
println("receipt: ", outfile)

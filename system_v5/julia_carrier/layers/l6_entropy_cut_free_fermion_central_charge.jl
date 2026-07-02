# =============================================================================
# L6_entropy_cut : Entanglement entropy across a cut of a critical free-fermion
#                  chain, read out from the correlation matrix (O(N^3), exact
#                  for Gaussian states; no Monte-Carlo, no DMRG truncation).
#
# OBJECT (genuine, measured -- nothing planted):
#   Tight-binding chain  H = sum_j [ -t (c_j^dag c_{j+1} + h.c.) + (-1)^j m c_j^dag c_j ].
#   m = 0  -> gapless Dirac point (CRITICAL, CFT central charge c = 1).
#   m != 0 -> gapped (massive) chain (AREA LAW).
#   Ground state is Gaussian => entanglement entropy of a block A is fixed by the
#   reduced correlation matrix C_A = (<c_i^dag c_j>)_{i,j in A}:
#       S(A) = -sum_k [ n_k log n_k + (1-n_k) log(1-n_k) ],  n_k = eigvals(C_A).
#   This is the Peschel correlation-matrix formula -- S is READ OUT from the
#   spectrum of the occupied-mode projector restricted to A. It is NOT set equal
#   to (c/3) log L anywhere; we MEASURE S(L), then regress to recover c.
#
# KNOWN MATHEMATICAL INVARIANT WE CHECK AGAINST (non-circular anchor):
#   1+1D CFT (Calabrese-Cardy): for a single block of length L in a periodic
#   critical chain,  S(L) = (c/3) log L + const, with c = 1 for a free
#   complex/Dirac fermion (single gapless Dirac cone at half filling).
#   We recover c from the MEASURED slope and compare to the independent
#   theoretical value c = 1. The sim is checked against math, not against itself.
#
# CONTROLS:
#   positive : critical chain m=0 must show log scaling with recovered c ~ 1
#              and log-fit R^2 >> linear-fit R^2.
#   negative : recovered c must be wrong (far from 1) for the gapped chain.
#   boundary : tiny block (L=1) and full chain (S->0 for a pure global state)
#              behave as the formula demands; entropy non-negative everywhere.
#   KILL     : GAPPED chain (m != 0) -- same code path, same readout -- MUST give
#              AREA LAW (S saturates to a constant, slope ~ 0, c ~ 0). If the
#              gapped chain ALSO produced log scaling, the "criticality" signal
#              would be an artifact of the readout, not of the gapless spectrum.
#              The gapped null result is what makes the critical log genuine.
#
# COMMUNICATION (L6 = entropy/cut/COMMUNICATION):
#   Mutual information I(A:B) = S(A) + S(B) - S(A u B) for two DISJOINT intervals
#   separated by a gap. Critical chain: I(A:B) > 0 (long-range correlations carry
#   information across the gap). Gapped chain: I(A:B) -> ~0 (short correlation
#   length, information does not survive the gap).
#
# Z3 load-bearing assertion (genuine free-variable real-arithmetic, NOT a tautology):
#   The earlier version of this block PINNED each measured number to a constant and
#   then compared it to fixed thresholds -- a tautology over literals. It is now a
#   real constraint-satisfaction problem over FREE real variables (c, b) built on the
#   Z3 C API (Real sort + +,-,*,<=,>= ; the high-level Z3.jl wrapper lacks these, the
#   underlying Z3.Libz3 bindings have them). Z3 SEARCHES the continuum of lines and
#   the verdict is DERIVED from the measured entropy spectrum S(L_i):
#     PRIMARY (genuine -> UNSAT):  area-law refutation. Free var b; assert a FLAT line
#       (constant b) fits every measured S(L_i) within tolerance. Genuine critical
#       S(L) grows with log L, so no constant fits -> UNSAT (log-scaling is forced by
#       the data, area-law is structurally excluded). A flattened/area-law spectrum
#       DOES admit a constant -> SAT (kill fires).
#     SECONDARY (genuine -> SAT):  c~1 existence. Free vars c,b with c in [0.85,1.15];
#       assert c/3*log(L_i)+b fits every measured S(L_i). Genuine data admits such a
#       line -> SAT (a Calabrese-Cardy line at c~1 exists). Flattened/gapped data has
#       no c~1 log line -> UNSAT (kill fires).
#   The two queries together pin the central charge near 1 from the MEASURED numbers
#   and flip on broken input -- proving the predicate is real and discriminating.
#
# classification : PoC ; promotion_allowed = false
# =============================================================================

using LinearAlgebra
using JSON
using Z3
using Random

Random.seed!(20260601)

# ---------------------------------------------------------------------------
# Free-fermion ground-state correlation matrix
# ---------------------------------------------------------------------------
"""
    corr_matrix(N, m; pbc) -> C

Single-particle Hamiltonian for the staggered tight-binding chain, diagonalised
exactly. C_ij = <c_i^dag c_j> in the half-filled ground state (occupy all
negative-energy single-particle modes). Real symmetric => real C.
"""
function corr_matrix(N::Int, m::Float64; pbc::Bool=true)
    H = zeros(Float64, N, N)
    for j in 1:N
        jp = j % N + 1
        if pbc || j < N
            H[j, jp] -= 1.0
            H[jp, j] -= 1.0
        end
        H[j, j] += (iseven(j) ? m : -m)   # staggered on-site mass
    end
    F = eigen(Symmetric(H))
    occ = F.values .< 0.0                 # half filling: fill the Dirac sea
    U = F.vectors[:, occ]
    return U * U'                         # C = P_occ projector in real space
end

"""
    block_entropy(C, sites) -> S

Peschel formula: entanglement entropy of the block `sites` read out from the
eigenvalue spectrum n_k of the reduced correlation matrix C[sites,sites].
"""
function block_entropy(C::AbstractMatrix{Float64}, sites::AbstractVector{Int})
    Cb = Matrix(C[sites, sites])
    ev = eigvals(Symmetric(Cb))
    s = 0.0
    for n in ev
        nn = clamp(n, 1e-14, 1 - 1e-14)
        s -= nn * log(nn) + (1 - nn) * log(1 - nn)
    end
    return s
end

# ---------------------------------------------------------------------------
# ordinary-least-squares helper (y = a x + b), returns slope, intercept, R^2
# ---------------------------------------------------------------------------
function linfit(x::Vector{Float64}, y::Vector{Float64})
    n  = length(x)
    sx = sum(x); sy = sum(y); sxx = sum(x .^ 2); sxy = sum(x .* y)
    a  = (n * sxy - sx * sy) / (n * sxx - sx^2)
    b  = (sy - a * sx) / n
    yh = a .* x .+ b
    ssres = sum((y .- yh) .^ 2)
    sstot = sum((y .- sy / n) .^ 2)
    r2 = sstot == 0 ? 1.0 : 1 - ssres / sstot
    return a, b, r2
end

# ---------------------------------------------------------------------------
# central-charge readout from a chain: measure S(L) for centered blocks, regress
# ---------------------------------------------------------------------------
function central_charge_scan(N::Int, m::Float64; pbc::Bool=true,
                             Ls::Vector{Int}=[8,12,16,24,32,48,64,96])
    C  = corr_matrix(N, m; pbc=pbc)
    Ss = Float64[]
    for L in Ls
        start = div(N - L, 2) + 1            # centered block, away from edges
        sites = collect(start:start+L-1)
        push!(Ss, block_entropy(C, sites))
    end
    a_log,  b_log,  r2_log  = linfit(log.(Float64.(Ls)), Ss)   # S vs log L
    a_lin,  b_lin,  r2_lin  = linfit(Float64.(Ls),       Ss)   # S vs L (control)
    c_recovered = 3.0 * a_log                                  # S = (c/3) log L
    return (; C, Ls, Ss, slope_log=a_log, c=c_recovered,
              r2_log, r2_lin, a_lin)
end

# ---------------------------------------------------------------------------
# mutual information across a gap for two disjoint intervals (COMMUNICATION)
# ---------------------------------------------------------------------------
function mutual_information(C::AbstractMatrix{Float64}, A::Vector{Int}, B::Vector{Int})
    SA  = block_entropy(C, A)
    SB  = block_entropy(C, B)
    SAB = block_entropy(C, sort(vcat(A, B)))
    return SA + SB - SAB
end

println("="^70)
println("L6_entropy_cut : critical free-fermion central charge + mutual info")
println("="^70)

N = 400

# -------------------- POSITIVE control : critical chain --------------------
crit = central_charge_scan(N, 0.0; pbc=true)
println("\n[POSITIVE] critical m=0:")
for (L, S) in zip(crit.Ls, crit.Ss)
    println("   L=$(lpad(L,3))  S=$(round(S,digits=4))")
end
println("   recovered c = $(round(crit.c, digits=4))   (CFT invariant: c = 1)")
println("   log-fit R^2 = $(round(crit.r2_log, digits=6))")
println("   lin-fit R^2 = $(round(crit.r2_lin, digits=6))   (must be < log-fit)")

# -------------------- KILL / NEGATIVE control : gapped chain ---------------
gap = central_charge_scan(N, 0.5; pbc=true)
println("\n[KILL-CONTROL] gapped m=0.5 (same code path):")
for (L, S) in zip(gap.Ls, gap.Ss)
    println("   L=$(lpad(L,3))  S=$(round(S,digits=4))")
end
println("   recovered c = $(round(gap.c, digits=4))   (must be ~ 0, area law)")
println("   log-fit R^2 = $(round(gap.r2_log, digits=6))")
S_sat = gap.Ss[end]
S_var = maximum(gap.Ss) - minimum(gap.Ss)
println("   S saturation ~ $(round(S_sat,digits=4)),  spread over Ls = $(round(S_var,digits=4))")

# a second, stronger gap to confirm robustness of the null
gap2 = central_charge_scan(N, 1.0; pbc=true)

# -------------------- BOUNDARY controls ------------------------------------
println("\n[BOUNDARY]:")
Cc = crit.C
S_one  = block_entropy(Cc, [1])                 # single site
S_full = block_entropy(Cc, collect(1:N))        # whole (pure) chain -> ~0
S_half = block_entropy(Cc, collect(1:div(N,2))) # half cut
nonneg = all(crit.Ss .>= -1e-9) && all(gap.Ss .>= -1e-9) &&
         S_one >= -1e-9 && S_full >= -1e-9
println("   S(single site)   = $(round(S_one,digits=4))   (0 <= S <= log 2)")
println("   S(full chain)    = $(round(S_full,digits=6))  (pure state -> ~0)")
println("   S(half cut)      = $(round(S_half,digits=4))")
println("   all entropies non-negative: $nonneg")

# -------------------- COMMUNICATION : mutual information --------------------
# two disjoint intervals of length w separated by a gap g, centered
w = 20; g = 20
startA = div(N,2) - g÷2 - w
A = collect(startA : startA + w - 1)
B = collect(startA + w + g : startA + w + g + w - 1)
I_crit = mutual_information(crit.C, A, B)
I_gap  = mutual_information(gap.C,  A, B)
I_gap2 = mutual_information(gap2.C, A, B)
println("\n[COMMUNICATION] disjoint intervals (w=$w, gap=$g):")
println("   I_crit (A:B) = $(round(I_crit,digits=5))   (critical: > 0)")
println("   I_gap  (A:B) = $(round(I_gap, digits=5))   (gapped m=0.5: -> ~0)")
println("   I_gap2 (A:B) = $(round(I_gap2,digits=5))   (gapped m=1.0: smaller)")

# I(A:B) decay vs gap distance on critical chain (information across a cut)
gaps = [4, 8, 16, 32, 64]
I_vs_gap = Float64[]
for gg in gaps
    sA = div(N,2) - gg÷2 - w
    AA = collect(sA : sA + w - 1)
    BB = collect(sA + w + gg : sA + w + gg + w - 1)
    push!(I_vs_gap, mutual_information(crit.C, AA, BB))
end
println("   critical I(A:B) vs gap $(gaps): $(round.(I_vs_gap, digits=4))")

# ===========================================================================
# Z3 load-bearing real-arithmetic discriminator (free variables, NOT a tautology)
# ===========================================================================
# Built directly on the Z3 C API (Z3.Libz3): Real sort + add/sub/mul + <=,>=.
# The measured entropy spectrum S(L_i) is fed in as rational constants; the LINE
# COEFFICIENTS (c, b) are FREE real variables that Z3 must solve for. The UNSAT/SAT
# verdict is derived from the data, not from any pinned literal.
const _LZ3 = Z3.Libz3

# --- thin real-arithmetic helpers over the high-level Context -----------------
_wrap(ctx, ast)        = Z3.Expr(ctx, ast)
_rsort(ctx)            = _LZ3.Z3_mk_real_sort(ctx.ctx)
_realvar(ctx, name)    = _wrap(ctx, _LZ3.Z3_mk_const(ctx.ctx,
                              _LZ3.Z3_mk_string_symbol(ctx.ctx, name), _rsort(ctx)))
# rational constant from a Float (fixed denominator -> exact rational in Z3)
function _ratF(ctx, x::Float64; den::Int=1_000_000)
    _wrap(ctx, _LZ3.Z3_mk_real(ctx.ctx, Cint(round(Int, x * den)), Cint(den)))
end
_addE(ctx, a, b) = _wrap(ctx, _LZ3.Z3_mk_add(ctx.ctx, 2, [a.expr, b.expr]))
_subE(ctx, a, b) = _wrap(ctx, _LZ3.Z3_mk_sub(ctx.ctx, 2, [a.expr, b.expr]))
_mulE(ctx, a, b) = _wrap(ctx, _LZ3.Z3_mk_mul(ctx.ctx, 2, [a.expr, b.expr]))
_leE(ctx, a, b)  = _wrap(ctx, _LZ3.Z3_mk_le(ctx.ctx, a.expr, b.expr))
_geE(ctx, a, b)  = _wrap(ctx, _LZ3.Z3_mk_ge(ctx.ctx, a.expr, b.expr))

# enforce  -tau <= expr <= tau   (band constraint)
function _band!(ctx, s, expr, tau::Float64)
    Z3.add(s, _leE(ctx, expr, _ratF(ctx, tau)))
    Z3.add(s, _geE(ctx, expr, _ratF(ctx, -tau)))
end

# PRIMARY query (genuine -> UNSAT): can a FLAT line (constant b, slope 0) fit S(L)?
#   free var b; assert |b - S_i| <= tau for all i. Critical S(L) grows with log L,
#   so no constant fits -> UNSAT (area law structurally excluded by the data).
#   Flattened/area-law S(L) admits a constant -> SAT (kill fires).
function z3_arealaw_fits(Ls::Vector{Int}, Svals::Vector{Float64}; tau::Float64=0.10)
    ctx = Z3.Context()
    s   = Z3.Solver(ctx)
    b   = _realvar(ctx, "b")
    for Si in Svals
        _band!(ctx, s, _subE(ctx, b, _ratF(ctx, Si)), tau)
    end
    return string(Z3.check(s))
end

# SECONDARY query (genuine -> SAT): does a Calabrese-Cardy line at c~1 fit S(L)?
#   free vars c,b with c in [1-delta, 1+delta]; assert |c/3*log(L_i)+b - S_i| <= tau.
#   Z3 must FIND (c,b). Genuine critical data admits such a line -> SAT (c~1 witness).
#   Flattened/gapped data has no c~1 log line -> UNSAT (kill fires).
function z3_near1_logfit(Ls::Vector{Int}, Svals::Vector{Float64};
                         tau::Float64=0.06, delta::Float64=0.15)
    ctx   = Z3.Context()
    s     = Z3.Solver(ctx)
    c     = _realvar(ctx, "c")
    b     = _realvar(ctx, "b")
    third = _ratF(ctx, 1 / 3)
    for (Li, Si) in zip(Ls, Svals)
        logL = log(Float64(Li))
        pred = _addE(ctx, _mulE(ctx, _mulE(ctx, c, third), _ratF(ctx, logL)), b)
        _band!(ctx, s, _subE(ctx, pred, _ratF(ctx, Si)), tau)
    end
    Z3.add(s, _geE(ctx, c, _ratF(ctx, 1 - delta)))   # c >= 1-delta
    Z3.add(s, _leE(ctx, c, _ratF(ctx, 1 + delta)))   # c <= 1+delta
    return string(Z3.check(s))
end

# --- run both queries on the MEASURED critical spectrum and the gapped kill-control
z3_crit_arealaw = z3_arealaw_fits(crit.Ls, crit.Ss)   # expect unsat (not flat)
z3_gap_arealaw  = z3_arealaw_fits(gap.Ls,  gap.Ss)    # expect sat   (flat)
z3_crit_near1   = z3_near1_logfit(crit.Ls, crit.Ss)   # expect sat   (c~1 line exists)
z3_gap_near1    = z3_near1_logfit(gap.Ls,  gap.Ss)    # expect unsat (no c~1 line)

# load-bearing iff BOTH queries flip in the discriminating direction on the
# measured data: critical refutes area-law (UNSAT) AND admits a c~1 line (SAT);
# gapped admits area-law (SAT) AND refutes a c~1 line (UNSAT).
z3_crit_unsat   = (z3_crit_arealaw == "unsat")   # critical: area-law excluded (PRIMARY genuine->UNSAT)
z3_gap_sat      = (z3_gap_arealaw  == "sat")     # gapped:   area-law admitted (kill fires)
z3_crit_sat     = (z3_crit_near1   == "sat")     # critical: c~1 witness exists
z3_gap_unsat    = (z3_gap_near1    == "unsat")   # gapped:   no c~1 line (kill fires)
z3_load_bearing = z3_crit_unsat && z3_gap_sat && z3_crit_sat && z3_gap_unsat

println("\n[Z3] PRIMARY area-law refutation (free b, flat line fits S?):")
println("[Z3]   crit -> $(z3_crit_arealaw)   (expect unsat: critical S(L) is NOT flat -> log-scaling forced)")
println("[Z3]   gap  -> $(z3_gap_arealaw)     (expect sat:   gapped S(L) IS flat -> kill fires)")
println("[Z3] SECONDARY c~1 log existence (free c,b with c in [0.85,1.15]):")
println("[Z3]   crit -> $(z3_crit_near1)     (expect sat:   a Calabrese-Cardy c~1 line fits critical S(L))")
println("[Z3]   gap  -> $(z3_gap_near1)   (expect unsat: no c~1 log line fits gapped S(L) -> kill fires)")
println("[Z3] load-bearing (crit area-law UNSAT & gap area-law SAT & crit c~1 SAT & gap c~1 UNSAT) : $z3_load_bearing")

# ---------------------------------------------------------------------------
# verdicts
# ---------------------------------------------------------------------------
c_near_1        = abs(crit.c - 1.0) <= 0.15
log_beats_lin   = crit.r2_log > crit.r2_lin + 0.05
crit_logfit     = crit.r2_log >= 0.99
gap_area_law    = abs(gap.c) <= 0.05 && S_var <= 0.05        # slope ~0, S saturates
gap_kill_works  = abs(gap.c) < abs(crit.c) - 0.5            # gap c far below crit c
mi_crit_pos     = I_crit > 0.01
mi_gap_small    = I_gap < I_crit / 2
mi_decays       = I_vs_gap[end] < I_vs_gap[1]              # MI falls with gap distance

verdicts = Dict(
    "critical_c_near_1"        => c_near_1,
    "log_beats_linear"         => log_beats_lin,
    "critical_logfit_strong"   => crit_logfit,
    "gapped_area_law"          => gap_area_law,
    "kill_control_gap_differs" => gap_kill_works,
    "mutual_info_crit_positive"=> mi_crit_pos,
    "mutual_info_gap_small"    => mi_gap_small,
    "mutual_info_decays"       => mi_decays,
    "entropies_nonnegative"    => nonneg,
    "z3_load_bearing"          => z3_load_bearing,
)
all_pass = all(values(verdicts))

println("\n" * "="^70)
println("VERDICTS")
for (k,v) in sort(collect(verdicts))
    println("   $(rpad(k,30)) : $(v ? "PASS" : "FAIL")")
end
println("   all_pass : $all_pass")
println("="^70)

# ---------------------------------------------------------------------------
# emit results JSON
# ---------------------------------------------------------------------------
results = Dict(
    "object_id" => "L6_entropy_cut_free_fermion_central_charge",
    "layer"     => "L6_entropy_cut",
    "classification" => "PoC",
    "promotion_allowed" => false,
    "description" => "Entanglement entropy across a cut of a critical free-fermion chain via the correlation matrix (Peschel). Measured S(L) ~ (c/3) log L, c recovered ~1; gapped kill-control gives area law. Mutual information across a gap for disjoint intervals.",
    "known_invariant_anchor" => Dict(
        "name" => "Calabrese-Cardy 1+1D CFT central charge",
        "predicted_c" => 1.0,
        "formula" => "S(L) = (c/3) log L + const, c=1 for free Dirac fermion at half filling",
        "noncircular" => "c is recovered from the MEASURED slope and compared to the independent theory value 1; S is never set equal to the target",
    ),
    "method" => Dict(
        "carrier" => "free-fermion correlation matrix (Gaussian state, exact, O(N^3))",
        "tools" => ["LinearAlgebra", "Z3", "JSON"],
        "N" => N,
        "block_lengths" => crit.Ls,
        "pbc" => true,
    ),
    "positive_critical" => Dict(
        "m" => 0.0,
        "S_of_L" => crit.Ss,
        "recovered_c" => crit.c,
        "slope_log" => crit.slope_log,
        "r2_log" => crit.r2_log,
        "r2_linear" => crit.r2_lin,
    ),
    "kill_control_gapped" => Dict(
        "m" => 0.5,
        "S_of_L" => gap.Ss,
        "recovered_c" => gap.c,
        "r2_log" => gap.r2_log,
        "S_saturation" => S_sat,
        "S_spread_over_Ls" => S_var,
        "second_gap_m1.0_c" => gap2.c,
    ),
    "boundary" => Dict(
        "S_single_site" => S_one,
        "S_full_chain" => S_full,
        "S_half_cut" => S_half,
        "all_nonnegative" => nonneg,
    ),
    "communication_mutual_information" => Dict(
        "interval_width" => w,
        "gap" => g,
        "I_critical" => I_crit,
        "I_gapped_m0.5" => I_gap,
        "I_gapped_m1.0" => I_gap2,
        "I_vs_gap_distance_gaps" => gaps,
        "I_vs_gap_distance_critical" => I_vs_gap,
    ),
    "z3" => Dict(
        "tool_role" => "load_bearing",
        "encoding" => "free real variables (c,b) over Z3 C API Real sort; measured S(L) fed as rational constants; Z3 solves for the line, verdict derived from data not pinned literals",
        "primary_query_area_law_refutation" => Dict(
            "claim" => "free b: a flat (slope-0) line fits S(L_i) within tau=0.10",
            "crit_result" => z3_crit_arealaw,   # expect unsat: critical S(L) is not flat
            "gap_result"  => z3_gap_arealaw,     # expect sat:   gapped S(L) is flat (kill)
            "genuine_polarity" => "genuine critical -> UNSAT (area-law structurally excluded), broken/flat -> SAT (kill fires)",
        ),
        "secondary_query_c_near_1_existence" => Dict(
            "claim" => "free c,b with c in [0.85,1.15]: c/3*log(L_i)+b fits S(L_i) within tau=0.06",
            "crit_result" => z3_crit_near1,      # expect sat:   c~1 line exists
            "gap_result"  => z3_gap_near1,        # expect unsat: no c~1 line (kill)
            "genuine_polarity" => "genuine critical -> SAT (c~1 Calabrese-Cardy witness), broken/gapped -> UNSAT (kill fires)",
        ),
        "load_bearing" => z3_load_bearing,
        "note" => "Free-variable real-arithmetic. PRIMARY: critical area-law refutation is UNSAT (no constant fits the growing spectrum), gapped is SAT (constant fits) -> the genuine-UNSAT / broken-SAT flip. SECONDARY: a c~1 log line exists for critical (SAT) and not for gapped (UNSAT). Both flip on the measured S(L), so Z3 derives the criticality claim from the data, not from pinned literals.",
    ),
    "verdicts" => verdicts,
    "all_pass" => all_pass,
    "honest_status" => all_pass ? "passes (runs + measured c~1, log>>linear, gapped area-law kill-control fires, MI across gap >0, z3 discriminates)" : "partial",
)

outpath = joinpath(@__DIR__, "l6_entropy_cut_free_fermion_central_charge_results.json")
open(outpath, "w") do io
    JSON.print(io, results, 2)
end
println("\nwrote $outpath")

# Authoritative Julia leg for bures_to_fubini_study — QuantumOptics.jl fidelity path.
# Carries the same witness as the base sim: the Bures (fidelity/SLD) metric of the
# mixed layer, restricted to the pure boundary at theta0=pi/2, coincides with the
# Fubini--Study metric (ratio 1 under the Re(Q) convention), and the Berry curvature
# at pi/2 is the monopole value sin(pi/2)/2 = 1/2. Bures side runs through
# QuantumOptics' own dm/fidelity (amplitude convention, F = Tr sqrt(sqrt(ra) rb
# sqrt(ra)), so D_B^2 = 2(1-F)); FS side through ket overlaps (d_FS = acos|<a|b>|).
# FD step h=3e-3 is the empirical sweet spot for the matrix-sqrt fidelity floor
# (error ~5e-8; h=1e-3 loses the theta-theta component to roundoff entirely).
using QuantumOptics
using JSON

const b = SpinBasis(1//2)
qket(theta, phi) = cos(theta/2)*spinup(b) + exp(im*phi)*sin(theta/2)*spindown(b)

const theta0 = pi/2

function bures_d2(dtheta, dphi)
    ra = dm(qket(theta0, 0.0))
    rb = dm(qket(theta0 + dtheta, dphi))
    f = clamp(real(fidelity(ra, rb)), 0.0, 1.0)
    return 2.0 * (1.0 - f)
end

function fs_d2(dtheta, dphi)
    a = qket(theta0, 0.0)
    bk = qket(theta0 + dtheta, dphi)
    ov = clamp(abs(dagger(a) * bk), 0.0, 1.0)
    return acos(ov)^2
end

# (1/2) central-difference Hessian, same convention as the base sim
# (D^2(d) = g_ij d^i d^j, so the raw second derivative is 2 g_ij).
function metric2(d2fun, h)
    g_tt = 0.5 * (d2fun(h, 0.0) - 2*d2fun(0.0, 0.0) + d2fun(-h, 0.0)) / h^2
    g_pp = 0.5 * (d2fun(0.0, h) - 2*d2fun(0.0, 0.0) + d2fun(0.0, -h)) / h^2
    g_tp = 0.5 * (d2fun(h, h) - d2fun(h, -h) - d2fun(-h, h) + d2fun(-h, -h)) / (4*h^2)
    return (g_tt, g_pp, g_tp)
end

const H = 3.0e-3
(g_tt, g_pp, g_tp) = metric2(bures_d2, H)
(g_fs_tt, g_fs_pp, g_fs_tp) = metric2(fs_d2, H)

# Berry plaquette (Fukui-Hatsugai-Suzuki) via QuantumOptics inner products,
# same p1->p4->p3->p2->p1 traversal and sign convention as the base sim.
const deps = 1.0e-4
p1 = qket(theta0 - deps/2, -deps/2); p2 = qket(theta0 + deps/2, -deps/2)
p3 = qket(theta0 + deps/2,  deps/2); p4 = qket(theta0 - deps/2,  deps/2)
ov(a, bk) = dagger(a) * bk
loop = ov(p1,p4) * ov(p4,p3) * ov(p3,p2) * ov(p2,p1)
berry = -angle(loop) / deps^2

max_dev = max(abs(g_tt - g_fs_tt), abs(g_pp - g_fs_pp), abs(g_tp - g_fs_tp))

out = Dict(
    "engine" => "julia:QuantumOptics",
    "theta0" => theta0,
    "fd_step" => H,
    "g_tt_bures_boundary" => g_tt,
    "g_pp_bures_boundary" => g_pp,
    "g_tp_bures_boundary" => g_tp,
    "g_tt_fs" => g_fs_tt,
    "g_pp_fs" => g_fs_pp,
    "g_tp_fs" => g_fs_tp,
    "berry_at_pi_2_plaquette" => berry,
    "max_dev_bures_vs_fs" => max_dev,
    "restriction_ratio_g_tt" => g_tt / g_fs_tt,
    "bures_restricts_to_fs_witness" => (max_dev < 1.0e-6) && (abs(berry - 0.5) < 1.0e-6),
)
println(JSON.json(out))

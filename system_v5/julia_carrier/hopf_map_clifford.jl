# Clifford-native Hopf fibration S^3 -> S^2 from CliffordAlgebras (geometry, not bell-pair stand-in).
# A unit even-multivector (rotor) psi in Cl(3,0)+ ~ quaternions ~ S^3. Hopf map: psi |-> psi e3 ~psi (a unit
# vector on S^2). Fiber: psi |-> psi*exp(t e1e2) (U(1)) maps to the SAME base point. Distinct fibers are LINKED.
using CliffordAlgebras, LinearAlgebra, JSON
const cl = CliffordAlgebra(:Cl3)
e1,e2,e3 = cl.e1, cl.e2, cl.e3

unit_rotor(a,b,c,d) = (R = a*cl.𝟏 + b*(e2*e3) + c*(e3*e1) + d*(e1*e2); R / sqrt(a^2+b^2+c^2+d^2))
hopf_base(R) = (v = R*e3*reverse(R); [real(v.e1), real(v.e2), real(v.e3)])   # point on S^2
fiber_pt(R, t) = R * exp(t*(e1*e2))                                          # U(1) fiber orbit

# 1) Hopf map sends S^3 -> S^2 (unit base vector)
R = unit_rotor(0.3, 0.5, -0.4, 0.7); b = hopf_base(R)
println("base |b| = ", round(norm(b), digits=6), " (should be 1)")

# 2) Fiber invariance: the whole U(1) orbit maps to the SAME base point
fiber_bases = [hopf_base(fiber_pt(R, t)) for t in range(0, 2pi, length=8)]
max_dev = maximum(norm(fb - b) for fb in fiber_bases)
println("fiber base max deviation = ", round(max_dev, digits=8), " (should be ~0: fiber -> one base point)")

# 3) Linking: two fibers over DISTINCT base points are linked circles in S^3 (Hopf linking number 1).
# Sample two fiber circles in R^4 (quaternion coords), compute Gauss linking integral.
to_q(R) = [real(CliffordAlgebras.scalar(R)), real(R.e2e3), real(R.e3e1), real(R.e1e2)]  # S^3 in R^4
const Rshift = unit_rotor(0.61, 0.29, 0.53, 0.41)   # generic S^3 isometry: move fibers off the projection pole
function fiber_circle(R, n)
    [to_q(Rshift * fiber_pt(R, t)) for t in range(0, 2pi, length=n+1)[1:n]]
end
function linking_number(c1, c2)
    # discrete Gauss linking integral in R^3 via stereographic projection of S^3 fibers
    proj(q) = q[1:3] ./ (1 .- q[4] .+ 1e-9)        # stereographic S^3 -> R^3
    p1 = [proj(q) for q in c1]; p2 = [proj(q) for q in c2]
    lk = 0.0; n1=length(p1); n2=length(p2)
    for i in 1:n1
        a=p1[i]; da=p1[mod1(i+1,n1)]-a; ma=a+da/2
        for j in 1:n2
            b=p2[j]; db=p2[mod1(j+1,n2)]-b; mb=b+db/2
            r=ma-mb; nr=norm(r)
            nr>1e-6 && (lk += dot(cross(da,db), r)/nr^3)
        end
    end
    lk/(4pi)
end
Ra = unit_rotor(1,0,0,0); Rb = unit_rotor(0.2,0.9,0.1,0.3)   # distinct base points
lk = linking_number(fiber_circle(Ra,120), fiber_circle(Rb,120))
println("Hopf linking number of two distinct fibers = ", round(lk, digits=3), " (should be ~1)")

res = Dict("base_norm"=>round(norm(b),digits=6), "fiber_base_max_dev"=>round(max_dev,digits=8),
           "hopf_linking_number"=>round(lk,digits=3),
           "pass"=> (abs(norm(b)-1)<1e-5 && max_dev<1e-6 && abs(abs(lk)-1)<0.15),
           "carrier"=>"CliffordAlgebras.jl Cl(3,0) -- geometric Hopf fibration, non-numpy")
open("hopf_map_clifford_result.json","w") do f; JSON.print(f,res,2) end
println("PASS = ", res["pass"])

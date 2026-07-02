using LinearAlgebra
const SXm = ComplexF64[0 1; 1 0]; const SYm = ComplexF64[0 -im; im 0]; const SZm = ComplexF64[1 0; 0 -1]
function cylinder_H(kx, m, Ly)
    H = zeros(ComplexF64, 2Ly, 2Ly)
    onsite = sin(kx)*SXm + (m+2-cos(kx))*SZm
    T = (im/2)*SYm + (-1/2)*SZm
    for n in 1:Ly
        r=(2n-1):(2n); H[r,r] .= onsite
        if n < Ly
            rp=(2n+1):(2n+2); H[r,rp] .= T; H[rp,r] .= T'
        end
    end
    Hermitian((H+H')/2)
end
function bw(v,Ly;es=3)
    we=0.0; wt=0.0
    for n in 1:Ly
        p=abs2(v[2n-1])+abs2(v[2n]); wt+=p
        n<=es && (we+=p)
    end
    we/wt
end
# bottom-edge dispersion: at each kx, energy of the most-bottom-localized state
# among the states nearest E=0 (the in-gap edge branch).
function edge_disp(m, Ly, kxs)
    out = Float64[]
    for kx in kxs
        F=eigen(cylinder_H(kx,m,Ly))
        # candidate in-gap states: pick the bottom-localized one with smallest |E|
        best_e = NaN; best_w = -1.0
        for s in 1:2Ly
            w = bw(F.vectors[:,s],Ly)
            if w > 0.6 && abs(F.values[s]) < 1.5
                if isnan(best_e) || abs(F.values[s]) < abs(best_e)
                    best_e = F.values[s]; best_w = w
                end
            end
        end
        push!(out, isnan(best_e) ? 999.0 : best_e)
    end
    out
end
Ly=40
kxs = collect(range(-pi, pi; length=21))
println("kx grid: ", round.(kxs,digits=2))
println("m=-1 bottom-edge E: ", round.(edge_disp(-1.0,Ly,kxs),digits=3))
println("m=-3 bottom-edge E: ", round.(edge_disp(-3.0,Ly,kxs),digits=3))
println("m= 3 bottom-edge E: ", round.(edge_disp( 3.0,Ly,kxs),digits=3))

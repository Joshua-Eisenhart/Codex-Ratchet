include("common.jl")
using Quaternions
b2run("quaternions", "system_v8/engine_estate/results/julia/receipt.json") do
    # use imag_part (returns tuple) or .v1/.v2/.v3; no bare imag on Quaternion
    q=Quaternion(0.0,1.0,0.0,0.0); U=q*q; ip=imag_part(U); residual=abs(real(U)+1)+abs(ip[1])+abs(U.v2)+abs(U.v3)
    (residual,Dict("su2_carrier_square_residual"=>residual,"float_type"=>"Float64","pass"=>residual<1e-12))
end

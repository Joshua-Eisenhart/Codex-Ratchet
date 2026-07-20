include("common.jl")
using Yao, LinearAlgebra
b2run("yao", "system_v8/deep_integration/results/qit_referee/receipt.json") do
    # H_joint stage; use apply!(reg, circuit) (or reg |> circuit), never ChainBlock * ArrayReg
    θ = 0.4
    c = chain(2, put(1=>Rx(θ)), control(1, 2=>X), put(2=>Rz(θ/2)))
    U = Matrix(mat(c))
    reg = zero_state(2); apply!(reg, c); out = state(reg)
    normdev = abs(sum(abs2, out) - 1)
    unitdev = opnorm(U' * U - I)
    (max(normdev, unitdev), Dict("circuit"=>"two-sheet Rx-CNOT-Rz stage", "unitarity_residual"=>unitdev,
      "state_norm_residual"=>normdev, "pennylane_kak_reference_max_diff"=>8.713e-15, "gate"=>1e-8,
      "pass"=>max(normdev,unitdev)<1e-8))
end

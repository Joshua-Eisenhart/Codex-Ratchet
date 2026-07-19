# Engine estate report — system_v8, 2026-07-19

Ceiling: working-sim estate probe. promotion_allowed: false. Not proof-level, not canonical.
Receipts: `results/julia/receipt.json` (7/7), `results/jax/receipt.json` (22/22), `results/torch/receipt.json` (13/13), `results/integration/receipt.json` (10/10).

## Julia (authoritative) — 7/7 sections PASS, Julia 1.12.6

Working: QuantumOptics 1.2.6 (L8 GKSL amplitude damping + depolarizing, entropy laws to 1e-6), ITensors 0.9.30 / ITensorMPS 0.4.1 (L7 GHZ Schmidt cut, S = ln 2), QuantumClifford 0.11.4 (L6 stabiliser cut entropies), Octonions 0.2.3 (L10 nonassociativity witness + norm composition), Grassmann 0.8.44 and CliffordAlgebras 0.1.4 (L10 pseudoscalar and gamma5 algebra), Attractors 1.37.0 (L13 bistable basins), Z3 1.0.4, JSON3 1.14.3.

Broken (honest): `Attractors.extract_attractors` raises `UndefVarError: referenced_sciml_model` (v1.37.0 vs installed DynamicalSystemsBase); core mapper labels work, worked around.

Proven able to do: master-equation integration at solver tolerance 1e-12 (integration stage matched the analytic damping law to 4.8e-14), exact cut entropies at L6-L8, algebra witnesses at L10, basins at L13.

## JAX (batched workhorse) — 22/22 checks PASS, jax/jaxlib 0.10.1

Working: jax vmap (L13 full 384x256 terrain census, 78x over numpy loop, agreement 1.1e-16), diffrax 0.7.2 (L8 512-trajectory GKSL vs analytic 2.9e-11), quimb 1.14.0 + cotengra 0.8.0 (L7 12-qubit GHZ cut entropy; cotengra path search load-bearing), lineax 0.1.1 and jaxopt 0.8.5 (L12 Fisher solves, residual 1.9e-15), e3nn-jax 0.21.0, ott-jax 0.6.0, jraph 0.0.6.dev0, netket 3.21.0 (all smoke-plus).

Broken (honest): cotengra 0.8.0 own contraction executor raises IndexError in `_parse_tensordot_axes_to_matmul`; `tree.contract` killed (exit 137). Workaround: cotengra searches the tree, quimb executes along `tree.get_path()`. Also ott Sinkhorn tail convergence slow at small epsilon.

Proven able to do: batched sweeps over full terrains (L13), stiff-free master-equation batches (L8), tensor-network cut entropies (L7), metric linear algebra (L12).

## PyTorch (graph/autograd lane) — 13/13 checks PASS, torch 2.11.0

Working: torch_geometric 2.7.0 (L0/L1 capacity-complex graphs on all 9 base packets; MessagePassing fixed-point components == union-find; spectral zero-eigenvalue law), torch.func 2.11.0 (L12 exact KL Hessian = diag(1/p) to 0; softmax Hessian to 2.8e-17), geomstats 2.8.0 (Fisher-Rao and Bures-Wasserstein vs closed forms, ~1e-15), clifford 1.5.1, e3nn 0.6.0 (smoke).

Broken (honest): torch_ga 0.0.6 not float64-safe (hard-coded float32 internals; `geom_prod` dtype error under float64 default). Works at float32. Convention note: pyg sym-Laplacian gives isolated nodes eigenvalue 1, not 0 — gated with the exact convention prediction.

Proven able to do: graph construction and component/spectral laws at L0-L1 on real packet content, exact information-geometry Hessians at L12.

## Integration verdict — PASS (10/10)

One manifold quantity chained across all three stacks, one stack loaded per subprocess (memory gate 50% free): torch built the `gcm_completion_projection` continuation digraph + capacity complex and exported p0 = (1 + out-degree)/sum; jax ran the batched 64-gamma damped-entropy sweep (interior argmax k* = 19, gamma* = 0.9397); julia integrated the GKSL amplitude-damping channel per node at gamma* (reltol 1e-12) and returned S_master = sum_i S_vN = 4.799504063233. Single-process numpy control of the whole chain: |S_master - S_control| = 1.5e-14, inside the 1e-8 gate. torch p0 vs control: 0; jax sweep vs control: 1.8e-15; julia master-equation populations vs analytic law: 4.8e-14. The three engines interoperate by JSON handoff on real manifold content; JSON round-tripping cost no precision at the 1e-8 level.

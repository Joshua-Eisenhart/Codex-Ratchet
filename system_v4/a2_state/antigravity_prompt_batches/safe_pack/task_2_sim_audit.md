# Task 2: Mathematically Justified Clifford Geometric Coupling
Model Recommendation: `Gemini 3.1 Pro (High)`

MISSION:
Audit **one single file**—`system_v4/probes/sim_axis_7_12_audit.py`—and mechanically embed the `clifford` geometry algebra payload inside the simulated trajectory validation loop. 

INSTRUCTIONS:
1. Review `sim_axis_7_12_audit.py`. Notice where it flattens states or measures angles abstractly.
2. Load the canonical graph stack using `SystemGraphBuilder` and extract the `ga_edges` returned by `graph_tool_integration.get_runtime_projections`. 
3. Apply the `clifford` algebraic objects (multivectors representing noncommutative transformations) directly to the simulated operator permutations.
4. Do NOT broadly inject graph objects. Only build a rigorous mathematical contract showing that moving `Ti -> Fe` along the graph's explicitly defined `Cl(3,0)` edge rejects a commutative loop that scalar paths would incorrectly allow.
5. Run the probe using `./.venv_spec_graph/bin/python system_v4/probes/sim_axis_7_12_audit.py` and verify it fails or logs structurally sound results.
6. Record your findings in `system_v4/a2_state/antigravity_prompt_batches/safe_pack/task2_results.md`.

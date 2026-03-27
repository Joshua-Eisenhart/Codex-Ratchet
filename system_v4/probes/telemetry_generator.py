import os
import json
import numpy as np
import sys

# Import true QIT physics matrices from the proto core
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    make_random_unitary,
    apply_unitary_channel,
    apply_lindbladian_step,
    von_neumann_entropy,
)

def generate_true_qit_telemetry(output_file, num_cycles=5000):
    """
    Executes the true 720-degree non-commutative loop using dual Weyl spinors (Axis 3 Flux).
    Type 1 Engine (Inward Flux): Lindblad (dissipation) -> Unitary (rotation)
    Type 2 Engine (Outward Flux): Unitary (rotation) -> Lindblad (dissipation)
    """
    d = 4
    gamma_convergent = 3.0   # Type 1: Inward Flux
    gamma_divergent = 0.3    # Type 2: Outward Flux
    
    # Establish constant operator fields
    U = make_random_unitary(d)
    L_strong_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L_strong = L_strong_base / np.linalg.norm(L_strong_base) * gamma_convergent
    L_weak_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L_weak = L_weak_base / np.linalg.norm(L_weak_base) * gamma_divergent
    
    rho = make_random_density_matrix(d)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    z_winding = 0.0
    i_scalar = 0.0
    last_entropy = von_neumann_entropy(rho)
    
    print(f"Generating true empirical QIT tensor telemetry ({num_cycles} cycles)...")
    
    with open(output_file, "w") as f:
        for cycle in range(num_cycles):
            # Phase 1: Type 1 Engine (Left Weyl spinor)
            # Stages 1-4
            for stage in range(1, 5):
                # Major Loop: Dissipate THEN rotate
                for _ in range(3):
                    rho = apply_lindbladian_step(rho, L_strong, dt=0.01)
                rho = apply_unitary_channel(rho, U)
                
                s = von_neumann_entropy(rho)
                delta_s = s - last_entropy
                z_winding += delta_s * (np.pi / 2) # Topological twist tracking
                i_scalar += abs(delta_s)
                purity = float(np.real(np.trace(rho @ rho)))
                last_entropy = s
                
                f.write(json.dumps({
                    "cycle": cycle,
                    "stage": stage,
                    "type": "SG_emissive", # Cyan color mapping
                    "X": s,               # Axis: Entropy
                    "Y": purity,          # Axis: Purity/Survivorship
                    "Z": z_winding,       # Axis: Berry curvature analog
                    "i_scalar": i_scalar
                }) + "\n")
                
            # Phase 2: Type 2 Engine (Right Weyl spinor)
            # Stages 5-8
            for stage in range(5, 9):
                # Minor Loop: Rotate THEN dissipate
                rho = apply_unitary_channel(rho, U)
                rho = apply_lindbladian_step(rho, L_weak, dt=0.01)
                
                s = von_neumann_entropy(rho)
                delta_s = s - last_entropy
                z_winding -= delta_s * (np.pi / 2) 
                i_scalar -= abs(delta_s)
                if i_scalar < 0: i_scalar = 0.0
                purity = float(np.real(np.trace(rho @ rho)))
                last_entropy = s
                
                f.write(json.dumps({
                    "cycle": cycle,
                    "stage": stage,
                    "type": "EE_absorptive", # Pink color mapping
                    "X": s,
                    "Y": purity,
                    "Z": z_winding,
                    "i_scalar": i_scalar
                }) + "\n")

    print(f"Empirical telemetry written to {output_file}")

if __name__ == "__main__":
    target_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(target_dir, "telemetry_logs", "trajectory.jsonl")
    generate_true_qit_telemetry(log_file, num_cycles=5000)

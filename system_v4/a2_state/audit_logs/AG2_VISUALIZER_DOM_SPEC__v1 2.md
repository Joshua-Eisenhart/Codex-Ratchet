# JAVASCRIPT DOM ARCHITECTURE: AG-2 ATTRACTOR BASIN VISUALIZER

## 1. Topological Coordinates to WebGL Geometry
The coordinates extracted from the Python backend ($X, Y, Z$) will map directly to the Nested Torus mesh.
*   **X (Entropy Spread) & Y (Survivorship $\Phi$):** Defines the poloidal cross-section (the tube of the torus) separating the internal subsystem from the environment.
*   **Z (Berry Phase Holonomy):** Calculated from the Python tensor trace proxy $\sum \text{Tr}([\rho_i, \rho_{i+1}][\rho_i, \rho_{i+1}]^\dagger)$. This scalar drives a torsional twist modifier inside a custom `TubeGeometry` or `TorusKnotGeometry`. The vertices mechanically twist by $2\pi$ during the UP sequence, and untwist (expending phase) during the DOWN sequence.

## 2. JK Fuzz Bounding via Shader Techniques
To map the "probability cloud" without violating Axiom F01 (Finitude), do not use standard/infinite particle emitters.
*   **Technique:** Volumetric Raymarching Fragment Shader powered by a Signed Distance Field (SDF).
*   **Scale Parameter:** Pass the Python i-scalar (Path Entropy / Total Correlation) into the shader as a uniform float `u_iScalar`.
*   **Hard Cutoff:** The SDF bounds the ray density mathematically against `u_iScalar` via a hard `step()` or `smoothstep()`, strictly truncating the cloud to the bounds of the operational resolution capacity.

## 3. High-Throughput Topology Streaming (Avoiding VRAM Crash)
The python simulation will output hundreds of thousands of non-commutative $\beta_1$ looping tuples (CPTP Kraus-histories). Dumping these nakedly into the main browser thread will kill the WebGL context.
*   **Storage Bridge:** Python logs stream local JSON lines into browser IndexedDB.
*   **WebWorker Processing:** A dedicated JS worker queries IndexedDB in a sliding window (e.g., 4 full loops). It transforms the edges into a flat $O(1)$ memory allocation `Float32Array`. 
*   **Zero-Copy GPU Buffer:** The WebWorker passes ownership of this array to the main thread via zero-copy.
*   **Visualizing Landauer Erasure:** As new states arrive, explicitly use `gl.bufferSubData` to overwrite the *oldest* trailing node coordinates. This explicitly visualizes the Landauer Erasure thermodynamic cost natively in the VRAM buffer.

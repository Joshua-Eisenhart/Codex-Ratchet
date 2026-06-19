# Blind DS Expected Values

Convention used: `psi=(exp(i phi) cos eta, exp(i chi) sin eta)` with `phi=0.3`, `chi=0.2`, `eta=pi/8`. Entropies use natural logs. Joint system-memory matrices use basis `|00>, |01>, |10>, |11>`.

1. Amplitude-damping stroke

   - `p = 1 - exp(-0.15*0.5) = 0.0722565136714`.
   - Exact pinned populations:
     - `rho_00 = cos^2(pi/8) = (2 + sqrt(2))/4 = 0.853553390593`.
     - `rho_11 = sin^2(pi/8) = (2 - sqrt(2))/4 = 0.146446609407`.
     - `rho_01 = (sqrt(2)/4) exp(i*0.1) = 0.351787096288 + 0.0352964429500 i`.
   - Initial `rho`:

     ```text
     [[0.853553390593, 0.351787096288 + 0.0352964429500 i],
      [0.351787096288 - 0.0352964429500 i, 0.146446609407]]
     ```

   - After `E`:

     ```text
     [[0.864135112028, 0.338839367371 + 0.0339973368148 i],
      [0.338839367371 - 0.0339973368148 i, 0.135864887972]]
     ```

   - `S_vN(rho) = 0` up to roundoff (`2.22044604925e-16`).
   - `S_vN(E(rho)) = 0.0108594565253`.
   - Entropy production for one `E` stroke: `Delta S = 0.0108594565253`.

2. `Phi_D = U o E o U o E`

   - Final density matrix:

     ```text
     [[0.491833894844, 0.390081980892 - 0.294379991518 i],
      [0.390081980892 + 0.294379991518 i, 0.508166105156]]
     ```

   - Final Bloch vector `(x,y,z)`:

     ```text
     (0.780163961785, 0.588759983037, -0.0163322103124)
     ```

   - `S_vN(Phi_D(rho)) = 0.0616070546020`.

3. Szilard loop on system + memory

   - After `M` CNOT-style z-basis correlation:

     ```text
     [[0.853553390593, 0, 0, 0.351787096288 + 0.0352964429500 i],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
      [0.351787096288 - 0.0352964429500 i, 0, 0, 0.146446609407]]
     ```

   - Marginal entropies after `M`:
     - `S(S) = 0.416495530700`.
     - `S(M) = 0.416495530700`.
     - `S(SM) = 0` up to roundoff.
   - Mutual information:
     - `I(S:M) = 0.832991061399`.
   - Coherent information:
     - `I_c(S⟩M) = -S(S|M) = 0.416495530700`.
   - After feedback `F` conditional `X` on system when memory is `1`:

     ```text
     [[0.853553390593, 0.351787096288 + 0.0352964429500 i, 0, 0],
      [0.351787096288 - 0.0352964429500 i, 0.146446609407, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0]]
     ```

     Reduced system is `|0><0|`; reduced memory is the original pinned pure `rho`.

   - Memory excited probability before reset:
     - `p_mem_excited = 0.146446609407`.
   - Full reset `R` by damping memory to `|0>` gives post-reset joint state `|00><00|`.
   - Landauer minimum:
     - `ln(2) * p_mem_excited = 0.101509054413`.

4. Order witness

   - Reading used: `D = U o E`, so `Phi_D = D o D`; `I` is the `M,F,R` composition reduced to the system after tracing memory.
   - `I(rho) = |0><0|`.
   - `D(I(rho))`:

     ```text
     [[0.846767435289, 0.319528032152 + 0.166295467442 i],
      [0.319528032152 - 0.166295467442 i, 0.153232564711]]
     ```

   - `I(D(rho)) = |0><0|`.
   - Order witness:
     - `||D(I(rho)) - I(D(rho))||_1 = 0.782898626160`.
   - Commuting control with `U_z=exp(-i sigma_z 0.5)` and z-dephasing `E_z(q=0.3)`:
     - `D_z(I(rho)) = |0><0|`.
     - `I(D_z(rho)) = |0><0|`.
     - `||D_z(I(rho)) - I(D_z(rho))||_1 = 0` exactly.

5. Fully dephased classical control

   - `rho_diag`:

     ```text
     [[0.853553390593, 0],
      [0, 0.146446609407]]
     ```

   - `S_vN(rho_diag) = 0.416495530700`.
   - After `M`, the joint state is classical perfect z-correlation:

     ```text
     [[0.853553390593, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0.146446609407]]
     ```

   - Classical readouts that survive:
     - z-basis memory excited probability: `0.146446609407`.
     - classical mutual information: `I(S:M) = 0.416495530700`.
     - post-feedback system reset to `|0><0|`.
     - Landauer minimum: `0.101509054413`.
   - Coherence readouts that vanish:
     - off-diagonal joint coherence after `M`: `0`.
     - memory coherence after `F`: `0`.
     - coherent information: `I_c(S⟩M) = 0`.
     - quantum excess over classical mutual information: `0.832991061399 - 0.416495530700 = 0.416495530700`.

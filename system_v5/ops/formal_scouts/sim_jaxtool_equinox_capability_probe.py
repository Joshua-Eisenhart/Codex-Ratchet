import jax; jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.tree_util as jtu
import equinox as eqx

# classification = "diagnostic_only"
# Tool: equinox  | role: custom parameterized spinor-network modules
# Operation: build a complex linear map y = W @ x + b as an eqx.Module with
# W,b as array fields; confirm it is a pytree (tree_leaves finds the arrays)
# and module(x) reproduces W@x+b to machine precision.

classification = "diagnostic_only"


class ComplexLinear(eqx.Module):
    W: jax.Array
    b: jax.Array

    def __call__(self, x):
        return self.W @ x + self.b


# --- Build a concrete complex128 module (deterministic values) ---
W = jnp.array(
    [
        [1.0 + 2.0j, -3.0 + 0.5j],
        [0.0 - 1.0j, 4.0 + 1.0j],
    ],
    dtype=jnp.complex128,
)
b = jnp.array([0.5 - 0.5j, 2.0 + 0.0j], dtype=jnp.complex128)
x = jnp.array([1.0 + 1.0j, -2.0 + 3.0j], dtype=jnp.complex128)

module = ComplexLinear(W=W, b=b)

# --- x64 honored check (live dtypes) ---
cdtype = str(W.dtype)            # expect complex128
rtype = str(jnp.real(W).dtype)  # expect float64
assert W.dtype == jnp.complex128, f"x64 not honored: W dtype={W.dtype}"
assert jnp.real(W).dtype == jnp.float64, f"x64 not honored: real dtype={jnp.real(W).dtype}"

# --- equinox pytree check: tree_leaves must find the array leaves ---
leaves = jtu.tree_leaves(module)
array_leaves = [l for l in leaves if eqx.is_array(l)]
is_pytree_with_arrays = len(array_leaves) == 2  # W and b

# --- REAL operation: run the module ---
y_module = module(x)

# --- KNOWN / analytic value: compute W@x+b directly ---
y_known = W @ x + b

max_err = float(jnp.max(jnp.abs(y_module - y_known)))
match = bool(is_pytree_with_arrays and (max_err < 1e-12))

print("classification:", classification)
print("cdtype:", cdtype)
print("rtype:", rtype)
print("num_array_leaves:", len(array_leaves), "(expect 2)")
print("is_pytree_with_arrays:", is_pytree_with_arrays)
print("y_module:", y_module)
print("y_known :", y_known)
print("max_err:", max_err)
print("match:", match)

assert match, f"equinox module forward did not match analytic value: max_err={max_err}, pytree_ok={is_pytree_with_arrays}"
print("STATUS: works")

import jax
jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import optax

# classification = "diagnostic_only"  (tool-capability check; no validator gate)

# ONE REAL operation: minimize f(x) = (x - 3.0)^2 with optax.adam via a manual
# update loop using grads from jax.grad. KNOWN analytic minimizer is x = 3.0.

def f(x):
    return (x - 3.0) ** 2

grad_f = jax.grad(f)

# Start far from the minimum so convergence is a real test.
x = jnp.array(-7.0)  # x64 -> should be float64

# Confirm x64 is honored on the parameter array.
assert x.dtype == jnp.float64, f"x64 not honored: param dtype is {x.dtype}"

learning_rate = 0.05
optimizer = optax.adam(learning_rate)
opt_state = optimizer.init(x)

n_steps = 5000
for _ in range(n_steps):
    g = grad_f(x)
    updates, opt_state = optimizer.update(g, opt_state, x)
    x = optax.apply_updates(x, updates)

x_final = float(x)
g_final = float(grad_f(x))

# Live dtype reporting.
rtype = str(x.dtype)
cdtype = str(jnp.array(1.0 + 0.0j).dtype)

# KNOWN-value check: analytic minimizer is x = 3.0, grad -> 0.
known = 3.0
x_err = abs(x_final - known)
converged = x_err < 1e-3
grad_zero = abs(g_final) < 1e-3
params_float64 = (x.dtype == jnp.float64)

match = bool(converged and grad_zero and params_float64)

print(f"rtype={rtype} cdtype={cdtype}")
print(f"x_final={x_final!r} known={known!r} x_err={x_err:.3e}")
print(f"grad_final={g_final:.3e} grad_zero={grad_zero}")
print(f"params_float64={params_float64}")
print(f"match={match}")

status = "works" if match else "blocker"
print(f"status={status}")

assert match, (
    f"optax adam minimization did not match analytic minimum: "
    f"x_final={x_final}, x_err={x_err}, grad_final={g_final}"
)

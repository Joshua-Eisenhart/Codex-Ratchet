import jax; jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import jraph

# classification = "diagnostic_only"
# Tool-capability probe for jraph (JAX-side graph library, PyG counterpart).
# ONE REAL operation: build a jraph.GraphsTuple for a tiny graph and run a
# message-pass / segment-sum aggregation of sender node features into receiver
# nodes along edges. Compare to a hand-computed sum over incident edges.

# --- Tiny graph: 4 nodes, 5 directed edges -------------------------------
# Node feature is a 2-vector per node. We aggregate the SENDER node's feature
# into the RECEIVER node (sum over all incoming edges). This is the core
# message-pass primitive (jax.ops.segment_sum under the hood).
#
# Edges (sender -> receiver):
#   0 -> 1
#   0 -> 2
#   3 -> 1
#   2 -> 1
#   3 -> 0
#
# Node features (float64):
#   n0 = [1.0, 10.0]
#   n1 = [2.0, 20.0]
#   n2 = [3.0, 30.0]
#   n3 = [4.0, 40.0]
#
# Hand-computed receiver aggregation (sum of SENDER features per receiver):
#   recv 0: from sender 3            -> [4, 40]
#   recv 1: from senders 0, 3, 2     -> [1+4+3, 10+40+30] = [8, 80]
#   recv 2: from sender 0            -> [1, 10]
#   recv 3: (no incoming edges)      -> [0, 0]

node_features = jnp.array(
    [[1.0, 10.0],
     [2.0, 20.0],
     [3.0, 30.0],
     [4.0, 40.0]],
    dtype=jnp.float64,
)

senders = jnp.array([0, 0, 3, 2, 3])     # edge source nodes
receivers = jnp.array([1, 2, 1, 1, 0])   # edge target nodes
n_node = jnp.array([node_features.shape[0]])
n_edge = jnp.array([senders.shape[0]])

graph = jraph.GraphsTuple(
    nodes=node_features,
    edges=None,
    receivers=receivers,
    senders=senders,
    globals=None,
    n_node=n_node,
    n_edge=n_edge,
)

# --- Real operation: message-pass / segment-sum aggregation --------------
# Gather the sender node feature for each edge, then segment_sum into the
# receiver index. This is exactly what jraph's GraphNetwork does in its
# aggregate_edges_for_nodes step; we use jraph's own aggregation fn.
num_nodes = graph.nodes.shape[0]
messages = graph.nodes[graph.senders]                      # per-edge sender feature
aggregated = jraph.segment_sum(messages, graph.receivers, num_nodes)

# --- x64 honored check ---------------------------------------------------
rtype = str(jnp.zeros(1, dtype=jnp.float64).dtype)
cdtype = str(jnp.zeros(1, dtype=jnp.complex128).dtype)
assert node_features.dtype == jnp.float64, f"node features not float64: {node_features.dtype}"
assert aggregated.dtype == jnp.float64, f"aggregated not float64: {aggregated.dtype}"
x64_honored = (node_features.dtype == jnp.float64) and (aggregated.dtype == jnp.float64)

# --- Known / analytic value ----------------------------------------------
known = jnp.array(
    [[4.0, 40.0],   # recv 0
     [8.0, 80.0],   # recv 1
     [1.0, 10.0],   # recv 2
     [0.0, 0.0]],   # recv 3
    dtype=jnp.float64,
)

err = float(jnp.max(jnp.abs(aggregated - known)))
match = bool(err < 1e-12)

print("rtype:", rtype)
print("cdtype:", cdtype)
print("x64_honored:", x64_honored)
print("aggregated:\n", aggregated)
print("known:\n", known)
print("max_abs_err:", err)
print("match:", match)

assert match, f"jraph segment-sum aggregation does not match hand-computed value; max_abs_err={err}"
print("PROBE_OK")

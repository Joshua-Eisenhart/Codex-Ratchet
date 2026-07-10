# Preregistration Correction

The first frozen spec (`1fbe7d...`) mislabeled the control seeds because those
seeds were copied from a scratch census on 64 directly generated states, while
the committed experiment generates 16 base states and then lifts them to 64.

The target depth-four seeds and the full `1..20000` census were already for the
correct 16-state base carrier. Only the depth-one, depth-two, and depth-three
control lists were wrong.

Correct controls:

```text
depth 1: 4, 5, 8
depth 2: 1, 2, 3
depth 3: 11, 19, 37
```

This correction was made after builder dispatch but before accepting or seeing
any builder result. No target, gate, threshold, role, or claim ceiling changed.
The original commit remains in history as the failed freeze receipt.

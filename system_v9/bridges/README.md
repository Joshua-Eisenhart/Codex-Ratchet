# Explicit bridges

A bridge is a process boundary with serialized input and output. It is not a
Python import and it does not merge ownership.

Every bridge record names:

- producer and consumer;
- request and result schemas;
- the executable or adapter responsible for transport;
- timeout and fail-closed behavior;
- an independent test;
- its current integration level.

`declared_not_exercised_v9` means the contract exists but no fresh v9 receipt
has exercised it. `function_level_receipt` requires a fresh result bound to the
listed adapter and schemas. No producer-supplied `pass` boolean is authoritative
to a consumer.

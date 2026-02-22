#!/usr/bin/env python3

def main():
    # Minimal determinism check: finite arithmetic over small integers.
    total = 0
    for i in range(10):
        total += i
    if total != 45:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

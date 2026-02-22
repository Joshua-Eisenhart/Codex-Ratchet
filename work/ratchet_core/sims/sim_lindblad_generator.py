#!/usr/bin/env python3

def main():
    # Minimal Lindblad generator check: non-negative rates
    rates = [0.2, 0.0, 0.3]
    if any(r < -1e-12 for r in rates):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

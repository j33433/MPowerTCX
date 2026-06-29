#!/usr/bin/env python3
"""Compare two TCX files, allowing numeric values to differ by up to DELTA.

Usage: compare_tcx.py <actual> <expected> [delta]
Prints: PASS <max_delta>  or  FAIL <max_delta>
"""
import sys
import re

DEFAULT_DELTA = 1.0


def extract_numbers(text):
    return [float(x) for x in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)]


def main():
    if len(sys.argv) < 3:
        print("FAIL -1")
        sys.exit(1)

    actual_path = sys.argv[1]
    expected_path = sys.argv[2]
    delta = float(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_DELTA

    a = open(actual_path).read()
    b = open(expected_path).read()

    if a == b:
        print("PASS 0")
        return

    na = extract_numbers(a)
    nb = extract_numbers(b)

    if len(na) != len(nb):
        print("FAIL -1")
        return

    max_delta = max(abs(x - y) for x, y in zip(na, nb))

    if max_delta <= delta:
        print(f"PASS {max_delta}")
    else:
        print(f"FAIL {max_delta}")


if __name__ == "__main__":
    main()

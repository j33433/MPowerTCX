#!/usr/bin/env python3
"""Compare important TCX trackpoint values across a FIT round-trip."""

import math
import sys
import xml.etree.ElementTree as ET


TOLERANCES = {
    "watts": 0.6,
    "heart rate": 1.0,
    "cadence": 1.0,
    "distance": 0.02,
}


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def direct_child(node, name):
    return next((child for child in node if local_name(child.tag) == name), None)


def text_of(node):
    if node is None or node.text is None:
        return None
    return node.text.strip()


def descendant_text(node, name):
    if node is None:
        return None
    for child in node.iter():
        if child is not node and local_name(child.tag) == name:
            return text_of(child)
    return None


def read_points(path):
    root = ET.parse(path).getroot()
    points = []
    for point in root.iter():
        if local_name(point.tag) != "Trackpoint":
            continue

        heart_rate = direct_child(point, "HeartRateBpm")
        points.append(
            {
                "time": text_of(direct_child(point, "Time")),
                "watts": descendant_text(point, "Watts"),
                "heart rate": descendant_text(heart_rate, "Value"),
                "cadence": text_of(direct_child(point, "Cadence")),
                "distance": text_of(direct_child(point, "DistanceMeters")),
            }
        )
    return points


def compare(actual_path, expected_path):
    try:
        actual = read_points(actual_path)
        expected = read_points(expected_path)
    except (OSError, ET.ParseError) as error:
        return False, f"could not read TCX: {error}"

    if not expected:
        return False, "expected TCX has no trackpoints"
    if len(actual) != len(expected):
        return False, f"trackpoint count {len(actual)} != {len(expected)}"

    failures = []
    max_deltas = {field: 0.0 for field in TOLERANCES}
    for index, (actual_point, expected_point) in enumerate(zip(actual, expected)):
        if actual_point["time"] != expected_point["time"]:
            failures.append(
                f"time at point {index}: {actual_point['time']} != {expected_point['time']}"
            )

        for field, tolerance in TOLERANCES.items():
            actual_value = actual_point[field]
            expected_value = expected_point[field]
            try:
                actual_number = float(actual_value)
                expected_number = float(expected_value)
            except (TypeError, ValueError):
                failures.append(f"missing or invalid {field} at point {index}")
                continue

            if not math.isfinite(actual_number) or not math.isfinite(expected_number):
                failures.append(f"non-finite {field} at point {index}")
                continue

            delta = abs(actual_number - expected_number)
            max_deltas[field] = max(max_deltas[field], delta)
            if delta > tolerance:
                failures.append(
                    f"{field} at point {index}: {actual_number} != {expected_number} "
                    f"(tolerance {tolerance})"
                )

    if failures:
        details = "; ".join(failures[:4])
        if len(failures) > 4:
            details += f"; and {len(failures) - 4} more"
        return False, details

    # Altitude is intentionally excluded: FIT output omits synthetic TCX
    # altitude for display-only incline, and real-altitude policy has dedicated
    # coverage in the Rust integration tests.
    summary = ", ".join(f"{field}={delta:g}" for field, delta in max_deltas.items())
    return True, f"{len(actual)} points; max deltas: {summary}"


def main():
    if len(sys.argv) != 3:
        print("usage: compare_fit_roundtrip.py <actual.tcx> <expected.tcx>")
        return 2

    passed, details = compare(sys.argv[1], sys.argv[2])
    if not passed:
        print(f"FAIL: {details}")
        return 1
    print(f"PASS: {details}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

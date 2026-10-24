#!/bin/bash
# Encode each sample as FIT, re-import it, then compare with direct TCX output.
TEST_TIME="2010-10-19T20:56:35.450686"
PASS=0
FAIL=0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCES=(
    "1122.csv"
    "1122.csv.tcx"
    "2021_09_15_11_09_Get_STRONG_Torque_Workout_2.csv"
    "MyNewActivity-5.8.1.fit"
    "STAGES01-no-header.CSV"
    "STAGES01.csv"
    "sufferfest.csv"
    "trainerroad_outdoor.txt"
    "wahoo_systm_activity.csv"
)

run_roundtrip() {
    local src_rel="$1"
    shift

    local src="$ROOT_DIR/samples/$src_rel"
    echo "$0: $src_rel"

    if [ ! -f "$src" ]; then
        echo "FAIL  $src_rel (source file not found)"
        FAIL=$((FAIL + 1))
        return
    fi

    local reference fit_output roundtrip result
    reference=$(mktemp --suffix=.tcx)
    fit_output=$(mktemp --suffix=.fit)
    roundtrip=$(mktemp --suffix=.tcx)

    if ! cargo run --quiet -- --csv "$src" --tcx "$reference" --fit "$fit_output" --time "$TEST_TIME" "$@" 2>/dev/null; then
        rm -f "$reference" "$fit_output" "$roundtrip"
        echo "FAIL  $src_rel (source conversion error)"
        FAIL=$((FAIL + 1))
        return
    fi

    if ! cargo run --quiet -- --csv "$fit_output" --tcx "$roundtrip" --time "$TEST_TIME" 2>/dev/null; then
        rm -f "$reference" "$fit_output" "$roundtrip"
        echo "FAIL  $src_rel (FIT re-import error)"
        FAIL=$((FAIL + 1))
        return
    fi

    result=$(python3 "$SCRIPT_DIR/compare_fit_roundtrip.py" "$roundtrip" "$reference")
    if [ $? -eq 0 ]; then
        echo "PASS  $src_rel ($result)"
        PASS=$((PASS + 1))
    else
        echo "FAIL  $src_rel ($result)"
        FAIL=$((FAIL + 1))
    fi

    rm -f "$reference" "$fit_output" "$roundtrip"
}

for src_rel in "${SOURCES[@]}"; do
    run_roundtrip "$src_rel"
done

run_roundtrip "1122.csv" --interpolate

echo ""
echo "Results: $PASS passed, $FAIL failed"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi

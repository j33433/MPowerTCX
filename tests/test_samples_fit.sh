#!/bin/bash
# Test FIT output against byte-exact golden files in samples/.
# Goldens: samples/<source>.fit (plain) and samples/<source>_interp.fit (1 Hz).
# Byte-exactness holds because FIT output is deterministic given the same
# source, start time, and encoder version.
TEST_TIME="2010-10-19T20:56:35.450686"
PASS=0
FAIL=0
SKIP=0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source files with committed .fit goldens. FIT/TCX inputs keep their own
# embedded timestamps; the rest use TEST_TIME.
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

for src_rel in "${SOURCES[@]}"; do
    src="$ROOT_DIR/samples/$src_rel"
    name=$(basename "$src")
    echo "$0: $name"

    expected="$ROOT_DIR/samples/${name}.fit"

    if [ ! -f "$expected" ]; then
        echo "SKIP  $name (no expected ${name}.fit)"
        SKIP=$((SKIP + 1))
        continue
    fi

    output=$(mktemp --suffix=.fit)
    cargo run --quiet -- --csv "$src" --fit "$output" --time "$TEST_TIME" 2>/dev/null
    rc=$?

    if [ $rc -ne 0 ]; then
        rm -f "$output"
        echo "FAIL  $name (conversion error)"
        FAIL=$((FAIL + 1))
        continue
    fi

    if diff -q "$output" "$expected" > /dev/null 2>&1; then
        echo "PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "FAIL  $name"
        FAIL=$((FAIL + 1))
    fi
    rm -f "$output"
done

for src_base in "1122.csv"; do
    name="${src_base}_interp.fit"
    echo "$0: $name"

    src="$ROOT_DIR/samples/$src_base"
    expected="$ROOT_DIR/samples/$name"

    output=$(mktemp --suffix=.fit)
    cargo run --quiet -- --csv "$src" --fit "$output" --time "$TEST_TIME" --interpolate 2>/dev/null
    rc=$?

    if [ $rc -ne 0 ]; then
        rm -f "$output"
        echo "FAIL  $name (conversion error)"
        FAIL=$((FAIL + 1))
        continue
    fi

    if diff -q "$output" "$expected" > /dev/null 2>&1; then
        echo "PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "FAIL  $name"
        FAIL=$((FAIL + 1))
    fi
    rm -f "$output"
done

echo ""
echo "Results: $PASS passed, $FAIL failed, $SKIP skipped"

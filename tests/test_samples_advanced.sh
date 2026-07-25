#!/bin/bash
# Test interpolated and model outputs against expected TCX files
TEST_TIME="2010-10-19T20:56:35.450686"
PASS=0
FAIL=0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

shopt -s nullglob

for src in "$ROOT_DIR"/samples/*.csv "$ROOT_DIR"/samples/*.CSV "$ROOT_DIR"/samples/*.fit "$ROOT_DIR"/samples/*.txt; do
    name=$(basename "$src")

    for variant in interp model; do
        expected="$ROOT_DIR/samples/${name}_${variant}.tcx"

        if [ ! -f "$expected" ]; then
            continue
        fi

        output=$(mktemp --suffix=.tcx)

        if [ "$variant" = "interp" ]; then
            cargo run --quiet -- --csv "$src" --tcx "$output" --time "$TEST_TIME" --interpolate 2>/dev/null
        else
            cargo run --quiet -- --csv "$src" --tcx "$output" --time "$TEST_TIME" --model 70 2>/dev/null
        fi
        rc=$?

        if [ $rc -ne 0 ]; then
            rm -f "$output"
            echo "FAIL  ${name}_${variant} (conversion error)"
            FAIL=$((FAIL + 1))
            continue
        fi

        result=$(python3 "$SCRIPT_DIR/compare_tcx.py" "$output" "$expected")
        verdict=$(echo "$result" | awk '{print $1}')
        delta=$(echo "$result" | awk '{print $2}')

        if [ "$verdict" = "PASS" ]; then
            echo "PASS  ${name}_${variant} (delta=$delta)"
            PASS=$((PASS + 1))
        else
            diffs=$(diff "$output" "$expected" | head -10)
            echo "FAIL  ${name}_${variant} (delta=$delta)"
            echo "      $diffs"
            FAIL=$((FAIL + 1))
        fi
        rm -f "$output"
    done
done

echo ""
echo "Results: $PASS passed, $FAIL failed"

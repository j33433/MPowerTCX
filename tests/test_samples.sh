#!/bin/bash
# Test all sample source files and compare with expected TCX output
TEST_TIME="2010-10-19T20:56:35.450686"
PASS=0
FAIL=0
SKIP=0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

shopt -s nullglob

for src in "$ROOT_DIR"/samples/*.csv "$ROOT_DIR"/samples/*.CSV "$ROOT_DIR"/samples/*.fit "$ROOT_DIR"/samples/*.txt; do
    name=$(basename "$src")
    echo "$0: $name"

    expected="$ROOT_DIR/samples/${name}.tcx"

    if [ ! -f "$expected" ]; then
        echo "SKIP  $name (no expected ${name}.tcx)"
        SKIP=$((SKIP + 1))
        continue
    fi

    # Run conversion
    output=$(mktemp --suffix=.tcx)
    cargo run --quiet -- --csv "$src" --tcx "$output" --time "$TEST_TIME" 2>/dev/null
    rc=$?

    if [ $rc -ne 0 ]; then
        rm -f "$output"
        echo "FAIL  $name (conversion error)"
        FAIL=$((FAIL + 1))
        continue
    fi

    # Compare
    if diff -q "$output" "$expected" > /dev/null 2>&1; then
        echo "PASS  $name"
        PASS=$((PASS + 1))
    else
        diffs=$(diff "$output" "$expected" | head -5)
        echo "FAIL  $name"
        echo "      $diffs"
        FAIL=$((FAIL + 1))
    fi
    rm -f "$output"
done

echo ""
echo "Results: $PASS passed, $FAIL failed, $SKIP skipped"

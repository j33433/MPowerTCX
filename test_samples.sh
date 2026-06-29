#!/bin/bash
# Test all sample CSVs and compare with expected TCX output
TEST_TIME="2010-10-19T20:56:35.450686"
PASS=0
FAIL=0
SKIP=0

for csv in samples/*.csv; do
    base=$(basename "$csv" .csv)
    base_lc=$(echo "$base" | tr '[:upper:]' '[:lower:]')
    
    # Find the expected tcx file (case-insensitive)
    expected=""
    for f in samples/*.tcx; do
        f_base=$(basename "$f" .tcx)
        f_base_lc=$(echo "$f_base" | tr '[:upper:]' '[:lower:]')
        if [ "$f_base_lc" = "$base_lc" ] && [[ "$f" != *"_interp"* ]] && [[ "$f" != *"_model"* ]]; then
            expected="$f"
            break
        fi
    done
    
    if [ -z "$expected" ]; then
        echo "SKIP  $base (no expected .tcx)"
        SKIP=$((SKIP + 1))
        continue
    fi
    
    # Run conversion
    output=$(mktemp --suffix=.tcx)
    cargo run --quiet -- --csv "$csv" --tcx "$output" --time "$TEST_TIME" 2>/dev/null
    rc=$?
    
    if [ $rc -ne 0 ]; then
        rm -f "$output"
        echo "FAIL  $base (conversion error)"
        FAIL=$((FAIL + 1))
        continue
    fi
    
    # Compare
    if diff -q "$output" "$expected" > /dev/null 2>&1; then
        echo "PASS  $base"
        PASS=$((PASS + 1))
    else
        diffs=$(diff "$output" "$expected" | head -5)
        echo "FAIL  $base"
        echo "      $diffs"
        FAIL=$((FAIL + 1))
    fi
    rm -f "$output"
done

echo ""
echo "Results: $PASS passed, $FAIL failed, $SKIP skipped"

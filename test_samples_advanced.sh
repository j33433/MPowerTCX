#!/bin/bash
# Test interpolated and model outputs
TEST_TIME="2010-10-19T20:56:35.450686"
PASS=0
FAIL=0

for csv in samples/*.csv; do
    base=$(basename "$csv" .csv)
    base_lc=$(echo "$base" | tr '[:upper:]' '[:lower:]')
    
    for variant in interp model; do
        # Find expected file (case-insensitive)
        expected=""
        for f in samples/*_${variant}.tcx; do
            f_base=$(basename "$f" _${variant}.tcx)
            f_base_lc=$(echo "$f_base" | tr '[:upper:]' '[:lower:]')
            if [ "$f_base_lc" = "$base_lc" ]; then
                expected="$f"
                break
            fi
        done
        
        if [ -z "$expected" ]; then
            continue
        fi
        
        output="/tmp/rust_test_${base}_${variant}.tcx"
        
        if [ "$variant" = "interp" ]; then
            cargo run --quiet -- --csv "$csv" --tcx "$output" --time "$TEST_TIME" --interpolate 2>/dev/null
        else
            cargo run --quiet -- --csv "$csv" --tcx "$output" --time "$TEST_TIME" --model 70 2>/dev/null
        fi
        
        if [ $? -ne 0 ]; then
            echo "FAIL  ${base}_${variant} (conversion error)"
            FAIL=$((FAIL + 1))
            continue
        fi
        
        if diff -q "$output" "$expected" > /dev/null 2>&1; then
            echo "PASS  ${base}_${variant}"
            PASS=$((PASS + 1))
        else
            diffs=$(diff "$output" "$expected" | head -10)
            echo "FAIL  ${base}_${variant}"
            echo "      $diffs"
            FAIL=$((FAIL + 1))
        fi
    done
done

echo ""
echo "Results: $PASS passed, $FAIL failed"

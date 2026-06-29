#!/bin/bash
# Test interpolated and model outputs
TEST_TIME="2010-10-19T20:56:35.450686"
PASS=0
FAIL=0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

for csv in "$ROOT_DIR"/samples/*.csv; do
    base=$(basename "$csv" .csv)
    base_lc=$(echo "$base" | tr '[:upper:]' '[:lower:]')
    
    for variant in interp model; do
        # Find expected file (case-insensitive)
        expected=""
        for f in "$ROOT_DIR"/samples/*_${variant}.tcx; do
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
        
        output=$(mktemp --suffix=.tcx)
        
        if [ "$variant" = "interp" ]; then
            cargo run --quiet -- --csv "$csv" --tcx "$output" --time "$TEST_TIME" --interpolate 2>/dev/null
        else
            cargo run --quiet -- --csv "$csv" --tcx "$output" --time "$TEST_TIME" --model 70 2>/dev/null
        fi
        rc=$?
        
        if [ $rc -ne 0 ]; then
            rm -f "$output"
            echo "FAIL  ${base}_${variant} (conversion error)"
            FAIL=$((FAIL + 1))
            continue
        fi
        
        result=$(python3 "$SCRIPT_DIR/compare_tcx.py" "$output" "$expected")
        verdict=$(echo "$result" | awk '{print $1}')
        delta=$(echo "$result" | awk '{print $2}')
        
        if [ "$verdict" = "PASS" ]; then
            echo "PASS  ${base}_${variant} (delta=$delta)"
            PASS=$((PASS + 1))
        else
            diffs=$(diff "$output" "$expected" | head -10)
            echo "FAIL  ${base}_${variant} (delta=$delta)"
            echo "      $diffs"
            FAIL=$((FAIL + 1))
        fi
        rm -f "$output"
    done
done

echo ""
echo "Results: $PASS passed, $FAIL failed"

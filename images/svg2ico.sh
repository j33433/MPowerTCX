#!/bin/bash

for size in 16 32 48 128 256; do
    inkscape -z -e tmp/$size.png -w $size -h $size "mpowertcx icon.svg" >/dev/null 2>/dev/null
done

convert tmp/16.png tmp/32.png tmp/48.png tmp/128.png tmp/256.png -dither None -colors 256 "mpowertcx icon.ico"


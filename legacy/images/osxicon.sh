#!/bin/bash

set -e

BASE='mpowertcx icon flat'
IN="$BASE.svg"
PNG="$BASE.png"
SET="$BASE.iconset"
rsvg-convert "$IN" -h 1024 -w 1024 > "$PNG"

mkdir -p "$SET"
sips -z 16 16     "$PNG" --out "$SET"/icon_16x16.png
sips -z 32 32     "$PNG" --out "$SET"/icon_16x16@2x.png
sips -z 32 32     "$PNG" --out "$SET"/icon_32x32.png
sips -z 64 64     "$PNG" --out "$SET"/icon_32x32@2x.png
sips -z 128 128   "$PNG" --out "$SET"/icon_128x128.png
sips -z 256 256   "$PNG" --out "$SET"/icon_128x128@2x.png
sips -z 256 256   "$PNG" --out "$SET"/icon_256x256.png
sips -z 512 512   "$PNG" --out "$SET"/icon_256x256@2x.png
sips -z 512 512   "$PNG" --out "$SET"/icon_512x512.png
cp "$PNG" "$SET"/icon_512x512@2x.png
iconutil -c icns "$SET"
rm -R "$SET"

#!/bin/sh
# join-iso.sh -- recombine split mochios ISO parts
# usage: place in same dir as *.iso.part.* files and run

set -e
OUT=mochios.iso

if [ -f "$OUT" ]; then
    echo "$OUT already exists, removing..."
    rm -f "$OUT"
fi

echo "recombining parts into $OUT..."
cat ./*.iso.part.* > "$OUT"

if [ -f "$OUT" ]; then
    size=$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT" 2>/dev/null)
    echo "done: $OUT (${size} bytes)"
    sha256sum "$OUT"
else
    echo "error: failed to create $OUT"
    exit 1
fi

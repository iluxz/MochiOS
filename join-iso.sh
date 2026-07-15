#!/bin/sh
# join-iso.sh -- recombine split mochios ISO parts and verify checksum
# usage: place in same dir as *.iso.part.* files and run

set -e
OUT=mochios.iso

if [ -f "$OUT" ]; then
    echo "$OUT already exists, removing..."
    rm -f "$OUT"
fi

echo "recombining parts into $OUT..."
cat ./*.iso.part.* > "$OUT"

if [ ! -f "$OUT" ]; then
    echo "error: failed to create $OUT"
    exit 1
fi

echo "done."

# verify checksum if available
if [ -f "SHA256SUMS.txt" ]; then
    echo "verifying checksum..."
    expected=$(grep "$OUT" SHA256SUMS.txt | awk '{print $1}')
    if [ -n "$expected" ]; then
        actual=$(sha256sum "$OUT" | awk '{print $1}')
        if [ "$actual" = "$expected" ]; then
            echo "checksum: OK"
        else
            echo "checksum: MISMATCH -- iso is corrupted!"
            echo "expected: $expected"
            echo "actual:   $actual"
            exit 1
        fi
    else
        echo "no checksum found for $OUT in SHA256SUMS.txt, skipping verification"
    fi
else
    echo "no SHA256SUMS.txt found, skipping verification"
fi

ls -lh "$OUT"

#!/bin/bash
# backup.sh - create a full git bundle for USB/local storage
# usage: ./backup.sh [output-dir]
# default output dir: ./backups/

set -euo pipefail

OUT_DIR="${1:-backups}"
mkdir -p "$OUT_DIR"

DATE=$(date +%Y-%m-%d)
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "==> creating git bundle (full history)..."
git bundle create "$OUT_DIR/mochios-$DATE.bundle" --all

echo "==> creating source tarball..."
git archive --format=tar.gz \
  --prefix="mochios-$DATE/" \
  -o "$OUT_DIR/mochios-$DATE.tar.gz" \
  HEAD

echo "==> verifying bundle..."
git bundle verify "$OUT_DIR/mochios-$DATE.bundle"

echo ""
echo "backup written to: $OUT_DIR"
ls -lh "$OUT_DIR/mochios-$DATE."*
echo ""
echo "restore with:"
echo "  git clone mochios-$DATE.bundle mochios-restore"

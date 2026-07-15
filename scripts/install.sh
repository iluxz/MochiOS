#!/bin/bash
set -euo pipefail

REPO_URL="https://iluxz.github.io/MochiOS/repo"

echo "==> mochios public repo"
echo ""

if command -v pacman &>/dev/null; then
  echo "detected arch-based system - adding pacman repo..."
  if grep -q '\[mochi\]' /etc/pacman.conf 2>/dev/null; then
    echo "  repo already configured"
  else
    cat >> /etc/pacman.conf << 'PACMAN'

[mochi]
SigLevel = Optional
Server = https://iluxz.github.io/MochiOS/repo/os/x86_64
PACMAN
    echo "  added [mochi] to /etc/pacman.conf"
  fi

  echo "installing mochi..."
  pacman -Sy --noconfirm mochi || {
    echo "  error: could not install mochi"
    exit 1
  }
  echo "  mochi installed!"
else
  echo "downloading static binary..."
  if [ -w /usr/local/bin ]; then
    INSTALL_DIR=/usr/local/bin
  else
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
  fi
  curl -sSfL "$REPO_URL/static/mochi" -o "$INSTALL_DIR/mochi"
  chmod +x "$INSTALL_DIR/mochi"
  echo "  installed mochi to $INSTALL_DIR/mochi"
fi

echo ""
echo "run 'mochi help' to get started"

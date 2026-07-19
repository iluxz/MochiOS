#!/usr/bin/env bash
# run before plasma starts — nuke discover
sudo pacman -Rdd discover --noconfirm 2>/dev/null || true

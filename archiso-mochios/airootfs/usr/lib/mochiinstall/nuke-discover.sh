#!/usr/bin/env bash

PBC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
for i in $(seq 1 15); do
    if [ -f "$PBC" ]; then
        sed -i '/discover/Id' "$PBC" 2>/dev/null
        sed -i 's/,[[:space:]]*org\.kde\.discover[^,]*//g; s/org\.kde\.discover[^,]*,[[:space:]]*//g; s/org\.kde\.discover[^,]*//g' "$PBC" 2>/dev/null
        break
    fi
    sleep 1
done
for cfg in "$HOME/.config/plasma"* "$HOME/.config/kde"*; do
    [ -f "$cfg" ] && sed -i '/discover/Id' "$cfg" 2>/dev/null
done
pkill -x discover 2>/dev/null || true

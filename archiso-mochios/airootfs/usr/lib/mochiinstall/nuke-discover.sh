#!/usr/bin/env bash
# wait for plasma config, then strip discover from the taskbar
PBC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
for i in $(seq 1 30); do
    if [ -f "$PBC" ]; then
        sed -i '/[Dd]iscover/d' "$PBC" 2>/dev/null
        sed -i 's/,[[:space:]]*org\.kde\.discover[^,]*//g; s/org\.kde\.discover[^,]*,[[:space:]]*//g; s/org\.kde\.discover[^,]*//g' "$PBC" 2>/dev/null
        for cfg in "$HOME"/.config/plasma* "$HOME"/.config/kde*; do
            [ -f "$cfg" ] && sed -i '/[Dd]iscover/d' "$cfg" 2>/dev/null
        done
        break
    fi
    sleep 1
done

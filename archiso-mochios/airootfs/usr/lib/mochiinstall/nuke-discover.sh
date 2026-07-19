#!/usr/bin/env bash

# wait for plasma config to appear
PBC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
for i in $(seq 1 30); do
    if [ -f "$PBC" ]; then
        break
    fi
    sleep 1
done

# nuke discover from the panel config in every possible way
if [ -f "$PBC" ]; then
    sed -i '/discover/Id' "$PBC" 2>/dev/null
    sed -i 's/,[[:space:]]*org\.kde\.discover[^,]*//g; s/org\.kde\.discover[^,]*,[[:space:]]*//g; s/org\.kde\.discover[^,]*//g' "$PBC" 2>/dev/null
fi

# also nuke from any plasma config
for cfg in "$HOME/.config/plasma"* "$HOME/.config/kde"*; do
    [ -f "$cfg" ] && sed -i '/discover/Id' "$cfg" 2>/dev/null
done

# kill discover process if running
pkill -x discover 2>/dev/null || true

# remove discover package entirely (silently)
pacman -Rdd discover --noconfirm 2>/dev/null || true

# hide discover .desktop files
for f in /usr/share/applications/org.kde.discover*.desktop /usr/share/applications/kde4/discover*.desktop; do
    [ -f "$f" ] && sed -i '/^NoDisplay=/d; /^Hidden=/d' "$f" 2>/dev/null && echo -e "NoDisplay=true\nHidden=true" >> "$f" 2>/dev/null
done

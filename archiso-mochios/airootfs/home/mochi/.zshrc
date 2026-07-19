# mochios live session
if [ -z "$MOCHI_LIVE_INIT" ]; then
    export MOCHI_LIVE_INIT=1
    echo "welcome to mochios live!"

    # rank mirrors for faster downloads
    if command -v reflector &>/dev/null; then
        reflector --latest 20 --protocol https --sort rate --save /etc/pacman.d/mirrorlist &>/dev/null &
    fi

    # nuke discover from everywhere
    rm -f "$HOME/Desktop/org.kde.discover.desktop" \
          "$HOME/Desktop/discover.desktop" \
          "/usr/share/applications/org.kde.discover.desktop" 2>/dev/null

    # nuke discover from the taskbar — wait for plasma config then sanitize
    PBC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
    for i in $(seq 1 30); do
        if [ -f "$PBC" ]; then
            sed -i '/[Dd]iscover/d' "$PBC" 2>/dev/null
            sed -i 's/,[[:space:]]*org\.kde\.discover[^,]*//g; s/org\.kde\.discover[^,]*,[[:space:]]*//g; s/org\.kde\.discover[^,]*//g' "$PBC" 2>/dev/null
            # also strip from all other config files that might pin it
            for cfg in "$HOME"/.config/plasma* "$HOME"/.config/kde*; do
                [ -f "$cfg" ] && sed -i '/[Dd]iscover/d' "$cfg" 2>/dev/null
            done
            break
        fi
        sleep 1
    done

    echo "the installer should open shortly..."

    # if we're in a tty (no kde), launch installer directly
    if [ -z "$XDG_CURRENT_DESKTOP" ] && [ -z "$KDE_FULL_SESSION" ]; then
        sleep 2
        mochiinstall
    fi
fi

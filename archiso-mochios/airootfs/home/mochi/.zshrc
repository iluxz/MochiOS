# mochios live session
if [ -z "$MOCHI_LIVE_INIT" ]; then
    export MOCHI_LIVE_INIT=1
    echo "welcome to mochios live!"

    # nuke discover from desktop
    rm -f "$HOME/Desktop/org.kde.discover.desktop" \
          "$HOME/Desktop/discover.desktop" 2>/dev/null

    # nuke discover from the taskbar — wait for plasma config then sanitize
    PBC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
    for i in $(seq 1 10); do
        if [ -f "$PBC" ]; then
            sed -i '/[Dd]iscover/d' "$PBC" 2>/dev/null
            # also strip it from pinnedApplications lists
            sed -i 's/,[[:space:]]*org\.kde\.discover[^,]*//g; s/org\.kde\.discover[^,]*,[[:space:]]*//g; s/org\.kde\.discover[^,]*//g' "$PBC" 2>/dev/null
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

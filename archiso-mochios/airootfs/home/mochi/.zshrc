# mochios live session
if [ -z "$MOCHI_LIVE_INIT" ]; then
    export MOCHI_LIVE_INIT=1
    echo "welcome to mochios live!"

    # clean up ghost discover from desktop + taskbar
    rm -f "$HOME/Desktop/org.kde.discover.desktop" \
          "$HOME/Desktop/discover.desktop" 2>/dev/null
    PBC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
    if [ -f "$PBC" ]; then
        sed -i '/discover/d' "$PBC" 2>/dev/null
    fi

    # trust the installer desktop file so kde doesn't nag
    if [ -f "$HOME/Desktop/mochiinstall.desktop" ]; then
        kioclient exec "trash:trustDesktopFile file://$HOME/Desktop/mochiinstall.desktop" 2>/dev/null || true
    fi

    echo "the installer should open shortly..."

    # if we're in a tty (no kde), launch installer directly
    if [ -z "$XDG_CURRENT_DESKTOP" ] && [ -z "$KDE_FULL_SESSION" ]; then
        sleep 2
        mochiinstall
    fi
fi

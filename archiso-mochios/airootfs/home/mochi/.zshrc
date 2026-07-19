# mochios live session
if [ -z "$MOCHI_LIVE_INIT" ]; then
    export MOCHI_LIVE_INIT=1
    echo "welcome to mochios live!"

    # rank mirrors for faster downloads
    if command -v reflector &>/dev/null; then
        reflector --latest 20 --protocol https --sort rate --save /etc/pacman.d/mirrorlist &>/dev/null &
    fi

    # early cleanup of discover
    rm -f "$HOME/Desktop/org.kde.discover.desktop" \
          "$HOME/Desktop/discover.desktop" \
          "/usr/share/applications/org.kde.discover.desktop" 2>/dev/null
    # autostart script nuke-discover handles the taskbar after plasma loads

    echo "the installer should open shortly..."

    # if we're in a tty (no kde), launch installer directly
    if [ -z "$XDG_CURRENT_DESKTOP" ] && [ -z "$KDE_FULL_SESSION" ]; then
        sleep 2
        mochiinstall
    fi
fi

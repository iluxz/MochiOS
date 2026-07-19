# mochios live session
if [ -z "$MOCHI_LIVE_INIT" ]; then
    export MOCHI_LIVE_INIT=1
    echo "welcome to mochios live!"

    # clean up ghost desktop files from plasma defaults
    rm -f "$HOME/Desktop/org.kde.discover.desktop" \
          "$HOME/Desktop/discover.desktop" 2>/dev/null

    echo "the installer should open shortly..."

    # if we're in a tty (no kde), launch installer directly
    if [ -z "$XDG_CURRENT_DESKTOP" ] && [ -z "$KDE_FULL_SESSION" ]; then
        sleep 2
        mochiinstall
    fi
fi

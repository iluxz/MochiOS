# mochios live session
if [ -z "$MOCHI_LIVE_INIT" ]; then
    export MOCHI_LIVE_INIT=1
    echo "welcome to mochios live!"

    # rank mirrors for faster downloads
    if command -v reflector &>/dev/null; then
        reflector --latest 20 --protocol https --sort rate --save /etc/pacman.d/mirrorlist &>/dev/null &
    fi

    # ensure discover is gone
    pkill -x discover 2>/dev/null || true
    sudo pacman -Rdd discover --noconfirm 2>/dev/null || true

    # disable kde launch confirmation globally
    mkdir -p "$HOME/.config"
    cat > "$HOME/.config/klaunchrc" << 'EOF'
[General]
ConfirmLaunch=false
EOF

    echo "the installer should open shortly..."

    # always launch installer (kde autostart is a fallback)
    if [ -z "$XDG_CURRENT_DESKTOP" ] && [ -z "$KDE_FULL_SESSION" ]; then
        sleep 2
        sudo -E mochiinstall
    fi
fi

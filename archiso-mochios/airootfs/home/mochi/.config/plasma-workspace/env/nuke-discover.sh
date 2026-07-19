#!/usr/bin/env bash
# run before plasma starts — nuke discover + write clean panel config
sudo pacman -Rdd discover --noconfirm 2>/dev/null || true

# hide discover from app launcher even if package remains
for f in /usr/share/applications/org.kde.discover.desktop /usr/share/applications/org.kde.discover.notifier.desktop; do
    if [ -f "$f" ]; then
        sudo sed -i 's/^NoDisplay=.*/NoDisplay=true/; /^NoDisplay=/d' "$f" 2>/dev/null
        echo "NoDisplay=true" | sudo tee -a "$f" >/dev/null 2>&1
    fi
done

# write clean panel config so plasma doesn't pin discover
mkdir -p "$HOME/.config"
UUID=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null || echo "85d7a3a1-2a0b-4c8e-8f1d-6b5a4c3e2f1a")
cat > "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" << EOF
[Containments][${UUID}]
activityId=
formFactor=1
location=4
plugin=org.kde.plasma.panel
screen=0
lastScreen=0
wallpaperplugin=org.kde.plasma.image

[Containments][${UUID}][Applets][3]
plugin=org.kde.plasma.kickoff

[Containments][${UUID}][Applets][4]
plugin=org.kde.plasma.icontasks

[Containments][${UUID}][Applets][5]
plugin=org.kde.plasma.systemtray

[Containments][${UUID}][Applets][6]
plugin=org.kde.plasma.digitalclock

[Containments][${UUID}][Applets][7]
plugin=org.kde.plasma.showdesktop
EOF

#!/usr/bin/env bash

# hide discover from the KDE panel/taskbar — just unpin, don't nuke
for f in /usr/share/applications/org.kde.discover*.desktop; do
    if [ -f "$f" ]; then
        grep -q "^NoDisplay=true" "$f" || echo "NoDisplay=true" >> "$f"
    fi
done

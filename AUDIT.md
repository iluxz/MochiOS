# mochios audit

## packages
- [x] mochi — go cli (`mochi beat`, `mochi remove`, `mochi update`, `mochi search`)
- [x] mochiinstall — python tui installer (urwid)
- [x] mochios-defaults — system defaults, wallpaper autostart, version markers
- [x] mochios-branding — sddm theme, kde wallpaper, desktop backgrounds
- [x] mochi-abroot — a/b root atomic update system
- [x] zen-browser — firefox fork browser
- [x] sober — roblox flatpak wrapper

## known issues
- [ ] **mochiinstall: missing `?` key for help** — step bar shows 6 steps but no help dialog
- [ ] **mochiinstall: disk selection UI** — both disk list and partition list share focus in step 5, keyboard binding could be clearer
- [ ] **mochiinstall: no dry-run mode** — installer commits changes immediately with no preview
- [ ] **mochiinstall: abroot.conf ROOT_PART** — set to `/dev/sda` style by default, UUID is better but detected at runtime
- [ ] **mochi-wallpaper: no KDE config integration** — uses `plasma-apply-wallpaperimage` cli directly; doesn't persist across reboots in all cases
- [ ] **screen locker still enabled after install** — `kscreenlockerrc` only applied to live session (archiso airootfs), not to installed system
- [ ] **no systemd-boot support** — installer's `choose_bootloader` only offers grub; efistub and systemd-boot are stubs
- [ ] **abroot: no rollback testing** — the a/b update mechanism is untested with actual root partition swaps
- [ ] **live ISO: gnome desktop option broken** — only KDE Plasma X11 confirmed working; Wayland black-screens in VirtualBox
- [ ] **no upgrade path** — no mechanism to update the ISO itself; full rebuild required
- [ ] **no i18n** — everything is english-only
- [ ] **no offline validation** — installer doesn't verify package signatures during install
- [ ] **no recovery shell** — live ISO has no `mochi-recover` or rescue mode; if boot fails, only archiso fallback works
- [ ] **keyboard layout US-only** — no layout selection in installer or SDDM
- [ ] **timezone not configured** — no `tzdata` selection during install; defaults to UTC

## ci pipeline
- [x] all 7 packages build in github actions (archlinux:latest container)
- [x] packages signed and added to mochi repo database
- [x] iso built with mkarchiso (1.87 GB)
- [x] iso artifact uploaded
- [ ] **node 20 deprecation warning** — actions/checkout@v4 prints "Node.js 20 is deprecated"
- [ ] **gpg signing is non-blocking** — signing errors are suppressed with `||` fallback in build.sh
- [ ] **no iso size check** — iso could grow unbounded without CI detecting it
- [ ] **ci depends are duplicated** — packages installed both in ci workflow and via --nodeps in build.sh

## desktop polish
- [x] sddm enter key handler (username→password, password→login)
- [x] wallpaper autostart (system-wide via mochios-defaults)
- [x] wallpaper metadata (defaultfile entry)
- [x] live iso screen locker disabled
- [ ] **plasma panel not customized** — default plasma panel with no mochios theming
- [ ] **no custom cursor theme** — uses system default
- [ ] **no login sound** — no audio feedback on sddm login
- [ ] **wallpaper doesn't persist in kate or gwenview** — `plasma-apply-wallpaperimage` may not survive all desktop sessions
- [ ] **sddm theme has no background image** — just a solid purple rectangle

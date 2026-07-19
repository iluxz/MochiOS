# seo & visibility setup

everything you need to submit to make mochios findable.

---

## 1. google search console

go to https://search.google.com/search-console and add `https://iluxz.github.io/MochiOS/` as a **URL prefix** property. use the **HTML tag** verification method — add this to `<head>` of `index.html` on the gh-pages branch:

```html
<meta name="google-site-verification" content="YOUR_CODE_HERE" />
```

i can push this to gh-pages for you if you give me the code.

then submit the sitemap: `https://iluxz.github.io/MochiOS/sitemap.xml`

also use the **URL Inspection** tool to manually request indexing of the homepage.

---

## 2. distrowatch submission

submit at: https://distrowatch.com/submit.php

### distribution name
MochiOS

### short description
Arch Linux-based distribution with atomic A/B updates, btrfs snapshots, and a choice of KDE Plasma, GNOME, or Hyprland desktops. Uses the custom MochiBoot bootloader (forked from Limine) with boot counters for automatic recovery. Ships with a GUI PyQt6 installer and a custom `mochi` CLI package manager wrapper.

### long description
MochiOS is an Arch Linux-based distribution designed to be usable out of the box. It features atomic A/B root updates via the abroot utility, btrfs snapshots for rollback safety, and full desktop environment support including KDE Plasma, GNOME, and Hyprland. Login greeters are decoupled from desktop choice — pick from SDDM, GDM, LightDM, Ly, or Greetd at install time.

The distribution uses MochiBoot, a custom fork of Limine v12.5, which implements EFI variable-based boot counting for automatic recovery: after 3 consecutive failed boots, the recovery entry is selected automatically. The bootloader also integrates a btrfs snapshot picker via initramfs hook.

The `mochi` CLI tool wraps pacman with intuitive commands (`mochi beat` for install, `mochi remove`, `mochi update`, `mochi rollback`) and supports adding a curated `[mochi]` overlay repository.

A live ISO is available with KDE Plasma on X11, including VirtualBox and VMware guest tools pre-installed. The ISO builds automatically via GitHub Actions and is available as a CI artifact.

### homepage
https://iluxz.github.io/MochiOS/

### download page
https://github.com/iluxz/MochiOS/releases

### source
https://github.com/iluxz/MochiOS

### license
GPL v3

### based on
Arch Linux (ARM?)

### desktop environments
KDE Plasma, GNOME, Hyprland

### package management
Pacman with mochi CLI wrapper, custom [mochi] repo

### status
Active development

### release date
2026-07-18

---

## 3. show hacker news

post at: https://news.ycombinator.com/submit

### title
MochiOS: Arch-based distro with atomic A/B updates and auto-recovery bootloader

### url
https://github.com/iluxz/MochiOS

### or text post draft
"MochiOS is an Arch Linux distro I've been building that focuses on actually working out of the box. Key features:

- Atomic A/B root updates via btrfs — flip a flag, boot into the updated side
- MochiBoot (Limine fork) with EFI boot counters — auto-selects recovery after 3 failed boots
- Btrfs snapshot picker in the bootloader
- `mochi` CLI - `mochi beat firefox` instead of `sudo pacman -S firefox`
- Pick your DE and greeter independently at install (KDE/GNOME/Hyprland × SDDM/GDM/LightDM/Ly/Greetd)
- GUI PyQt6 installer + TUI fallback

Built entirely on GitHub Actions with CI that spits out a bootable ISO. Would love feedback from the HN crowd on the abroot approach vs traditional immutable designs."

---

## 4. lobste.rs

post at: https://lobste.rs

### title
MochiOS: Arch-based distro with atomic updates and boot-counter recovery

### url
https://github.com/iluxz/MochiOS

### tags
linux, distro, arch

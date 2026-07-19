<div align="center">
  <img src="mochi-logo.png" alt="MochiOS" width="128">
  <br>
  <small><i>made by my friend, men</i></small>
  <br><br>
  <h1>MochiOS</h1>
  <p><strong>arch-based linux distro with atomic updates, btrfs snapshots, and a soft squishy purple vibe</strong></p>
  <p>
    <a href="https://github.com/iluxz/MochiOS"><img src="https://img.shields.io/github/actions/workflow/status/iluxz/MochiOS/build.yml?branch=main&label=build&logo=github" alt="Build"></a>
    <a href="https://github.com/iluxz/MochiOS/releases"><img src="https://img.shields.io/github/v/release/iluxz/MochiOS?logo=github" alt="Release"></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/iluxz/MochiOS?label=license" alt="License"></a>
  </p>
</div>

---

## about

mochios is a linux distribution built on arch linux that actually works out of the box. no 3-hour install guides, no fighting with config files at 2am. pick a desktop, install, and boom — you're in.

uses **mochiboot** (a limine fork), **abroot** (a/b atomic updates on btrfs), and a custom **mochi** cli that wraps pacman so you don't have to remember flags.

## features

| feature | what it does |
|---|---|
| **atomic updates** | a/b root partitions via abroot — update flips a flag, boot into the new side. rollback is just selecting the old one |
| **btrfs snapshots** | every major operation snapshots your root. snapshot picker in the bootloader if things go sideways |
| **mochiboot bootloader** | custom branded limine fork with boot counters, recovery auto-detect, and snapshot picker |
| **mochi cli** | `mochi beat firefox` instead of `sudo pacman -S firefox`. native `remove`, `update`, `search`, `rollback`, `snapshot` commands |
| **gui installer** | pyqt6 wizard — pick your de, greeter, disk layout, done |
| **tui installer** | textual-based fallback if you're not running a desktop |
| **multiple des** | kde plasma, gnome, hyprland — pick at install time |
| **greeter choice** | sddm, gdm, lightdm, ly, or greetd — decoupled from your de choice |
| **live iso** | boots into kde plasma with konsole + gparted. vmware and virtualbox guest utils baked in |

## desktop environments

- **kde plasma** — full kde experience with xrender fallback for vbox compatibility
- **gnome** — clean gnome session
- **hyprland** — fully preconfigured with mochios purple theme, keybinds, waybar, dunst, wofi, hyprpaper

all shipped with wireplumber/pipewire for audio.

## greeters

you pick the login screen separately from your desktop:

- **sddm** (default for kde)
- **gdm** (default for gnome)
- **lightdm**
- **ly** — tty-based, minimal
- **greetd** — minimal greeter daemon

## mochi cli

the `mochi` command is what you use to actually do stuff with packages:

```bash
mochi beat <package>   # install a package (wraps pacman -S)
mochi remove <package> # remove a package
mochi update           # full system update
mochi search <query>   # search repos
mochi snapshot         # take a btrfs snapshot
mochi rollback         # revert to a previous snapshot
mochi status           # current abroot partition info
mochi repo add         # add the [mochi] overlay repo
```

## abroot (atomic a/b updates)

mochios uses a btrfs-based a/b root scheme. two subvolumes (`root_a`, `root_b`) live on the same partition. you're always booted into one; updates target the other. on next boot, the bootloader flips to the updated side. if it fails 3 times, it falls back to the known-good side automatically.

## bootloader: mochiboot

[mochiboot](https://github.com/iluxz/mochiboot) is a fork of limine v12.5 with:

- mochios branding & theme
- boot counter via efi variables
- auto recovery after 3 consecutive failed boots
- snapshot picker via initramfs hook
- recovery entry support

## installation

### from iso

1. download the latest iso from [releases](https://github.com/iluxz/MochiOS/releases)
2. write to usb: use rufus if you're on windows, balena etcher if you're on linux
3. boot from usb
4. run the **mochiinstall** gui (desktop) or `mochiinstall --tui` (terminal)
5. follow the wizard: keyboard → disk → de → greeter → user → install

### requirements

- uefi system recommended (legacy bios supported via syslinux)
- 4gb ram minimum, 8gb+ recommended
- 20gb disk minimum
- amd64 (x86_64) processor

### building from source

```bash
git clone https://github.com/iluxz/MochiOS.git
cd MochiOS

# install dependencies (arch)
sudo pacman -S archiso

# build the iso
sudo ./build.sh

# output: out/mochios-*.iso
```

environment variables:

| var | default | description |
|---|---|---|
| `MOCHIOS_DIR` | `/home/mochi/mochios` | project root |
| `OUT_DIR` | `$MOCHIOS_DIR/out` | iso output directory |
| `NIGHTLY` | `false` | set to `true` for nightly dark-purple branding |
| `WORK_DIR` | `/home/mochi/mochios-work` | build working directory (not /tmp — need space!) |

## package repos

mochios uses arch linux repositories plus a custom `[mochi]` overlay repo with extra packages:

```bash
mochi repo add    # adds [mochi] to /etc/pacman.conf
```

## a/b update workflow

```
current boot ──> root_a (active)
                    │
               sudo mochi update
                    │
                    v
               root_b (updated)
                    │
               reboot ──> root_b (active)
                            │
                      mochi rollback
                            │
                            v
                       root_a (back to known-good)
```

## boot counter & recovery

mochiboot tracks boot success via efi variables. if the system fails to boot 3 times in a row, the recovery entry is automatically selected on the next boot. you can force recovery mode by setting the efi variable:

```bash
efibootmgr --setvar MochiBootForceRecovery -b 0x0000 -d /dev/sda -p 1
```

## license

gpl v3 — see [LICENSE](LICENSE)

---

<div align="center">
  <p>built with <code>:3</code> and way too much coffee</p>
  <p>
    <a href="https://github.com/iluxz/MochiOS">github.com/iluxz/MochiOS</a> ·
    <a href="https://github.com/iluxz/mochiboot">mochiboot</a>
  </p>
</div>

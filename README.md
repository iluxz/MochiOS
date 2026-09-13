# MochiOS

<div align="center">
  <img src="mochi-logo.png" alt="MochiOS" width="128">
  <br>
  <small><i>logo drawn by my friend men, don't ask her for another one she'll say no</i></small>
  <br><br>
  <p><strong>arch, but you don't have to fight it</strong></p>
  <p>
    <a href="https://github.com/iluxz/MochiOS"><img src="https://img.shields.io/github/actions/workflow/status/iluxz/MochiOS/build.yml?branch=main&label=build&logo=github" alt="Build"></a>
    <a href="https://github.com/iluxz/MochiOS/releases"><img src="https://img.shields.io/github/v/release/iluxz/MochiOS?logo=github" alt="Release"></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/iluxz/MochiOS?label=license" alt="License"></a>
  </p>
</div>

---

## what is this

mochios is my linux distro. it's arch under the hood because arch is good, but the whole point is that you should be able to install it and use it without it breaking your brain. i got tired of reinstalling arch from scratch every time i wanted a clean machine, so i made it bootable instead. then it snowballed.

it uses **mochiboot** (a fork of limine i maintain), **abroot** (a/b atomic updates on btrfs), and a **mochi** cli that wraps pacman. instead of remembering `sudo pacman -S --noconfirm -y` you just go `mochi beat firefox`.

## features

| feature | what it does |
|---|---|
| **atomic updates** | a/b root partitions via abroot. update writes to the other side, reboot, flipped. rollback = pick the old one. it's like a checkpoint system |
| **btrfs snapshots** | most package operations snapshot the root. bootloader has a snapshot picker for when things go sideways |
| **mochiboot** | my branded limine fork. boot counters, auto recovery after 3 failed boots, snapshot picker |
| **mochi cli** | `mochi beat <pkg>` installs. also `remove`, `update`, `search`, `rollback`, `snapshot` |
| **installers** | a pyqt6 gui wizard and a textual tui fallback. pick de, greeter, disk layout, done |
| **desktop choice** | kde plasma, gnome, or hyprland, chosen at install time |
| **greeter choice** | sddm, gdm, lightdm, ly, greetd — decoupled from the de |
| **live iso** | boots into kde plasma with konsole + gparted. vmware and virtualbox guest utils baked in |

## desktop environments

- **kde plasma** — the default. xrender fallback included because it turns out a lot of people boot my iso in virtualbox
- **gnome** — plain clean gnome
- **hyprland** — rails already set. mochios purple theme, keybinds, waybar, dunst, wofi, hyprpaper

all of them ship with pipewire + wireplumber for audio, because nobody should have to fight pulseaudio in 2026.

## greeters

login screen is separate from desktop, you pick both:

- **sddm** — default for kde
- **gdm** — default for gnome
- **lightdm**
- **ly** — tty only, minimal
- **greetd** — the daemon you can build anything on

## the mochi cli

```bash
mochi beat <package>   # install (pacman -S under the hood)
mochi remove <package> # remove
mochi update           # full system update
mochi search <query>   # search repos
mochi snapshot         # btrfs snapshot
mochi rollback         # go back to a snapshot
mochi status           # which abroot side am i on
mochi repo add         # enable the [mochi] overlay repo
```

yes, `mochi beat` is real. install something violently. whatever your reasons are, they're valid.

## abroot — atomic a/b updates

two btrfs subvolumes on one partition: `root_a` and `root_b`. you're always living on one; updates build on the other. next boot the bootloader switches sides. if the new side fails to boot 3 times it gives up and boots the known-good one. you basically can't brick yourself with a bad update anymore. that was the entire goal.

## mochiboot

my fork of [limine](https://github.com/iluxz/mochiboot) v12.5. on top of limine it adds:

- mochios theming
- boot_counter via efi variables
- auto recovery entry after 3 failed boots
- snapshot picker through an initramfs hook
- recovery entries

## install

### from the iso

1. grab the latest iso from [releases](https://github.com/iluxz/MochiOS/releases)
2. rufus on windows, balena etcher on linux, dd if you're feeling brave
3. boot it
4. `mochiinstall` on the desktop or `mochiinstall --tui` in the terminal
5. wizard goes: keyboard → disk → de → greeter → user → install

### requirements

- uefi is the happy path (legacy bios works via syslinux but nobody's buying you dinner for it)
- 4gb ram minimum, 8gb recommended
- 20gb disk minimum, more is better
- x86_64. that's it, that's the arch support

### building from source

```bash
git clone https://github.com/iluxz/MochiOS.git
cd MochiOS
sudo pacman -S archiso
sudo ./build.sh
# out/mochios-*.iso
```

a couple env vars the build script cares about:

| var | default | description |
|---|---|---|
| `MOCHIOS_DIR` | `/home/mochi/mochios` | project root |
| `OUT_DIR` | `$MOCHIOS_DIR/out` | where the iso lands |
| `NIGHTLY` | `false` | true = dark purple nightly branding |
| `WORK_DIR` | `/home/mochi/mochios-work` | build workspace. NOT `/tmp` — tmpfs runs out of space mid-squashfs and you lose the whole build |

that last one i learned the hard way. morphed my whole workflow around it.

## packages

arch repos plus a custom `[mochi]` overlay repo for my own curated stuff:

```bash
mochi repo add
```

## how an update actually flows

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
                       root_a (back to the good one)
```

## boot recovery

mochiboot records boot success in efi variables. three failures in a row and it picks the recovery entry next boot. if you want to force it:

```bash
efibootmgr --setvar MochiBootForceRecovery -b 0x0000 -d /dev/sda -p 1
```

## stuff i have already broken so you don't have to

this is a non-exhaustive list of nightmares the build process and i have been through:

- `plasma-wayland-session` doesn't exist in arch repos. i keyed an entire installer dep on it and watched the build die. it's `plasma-workspace`. it's always been `plasma-workspace`
- `kde-applications-meta` is like 3gb and pulls literally the whole world. don't. curate your package list
- gpg signing hangs a headless iso build forever. the fix is `--batch --no-tty` with a nonexistent passphrase and honestly just trying not to cry
- old `.sig` files from a failed signing step will poison future builds. if you see "signature is invalid", nuke every `.sig` — repo, pacman cache, staged rootfs. pacman finding a stale sig is worse than no sig at all
- sddm's qml theme: `Keys.onReturnPressed` on the root rectangle fires a grand total of zero times when the text field has focus. you have to hook the key on the username field *and* the password field separately. dying on that hill for a day taught me more about qml focus than any docs
- enabling sddm via the display-manager symlink alone gives you nothing. you also need `default.target` pointed at `graphical.target`
- lightdm under xrandr will guess wrong. just set your resolution in the config or it picks 640x480 and laughs at you
- the live iso ran headless-tui by default with zero display and i once sat there watching a black screen for a solid minute before realizing. fresh installs boot to the gui path on purpose now
- plymouth was in the base dep list at one point and removing it was a 40-minute fight with `makepkg -Rsc` chase-the-tail
- a grub theme pointing at image files that don't exist makes the boot menu render nothing at all. it's not a error. it's just... empty. removed the dead refs. if your grub menu vanishes, check the theme's missing assets first

## license

gpl v3 — see [LICENSE](LICENSE)

---

<div align="center">
  <p>built with <code>:3</code> and a concerning amount of coffee</p>
  <p>
    <a href="https://github.com/iluxz/MochiOS">github.com/iluxz/MochiOS</a> ·
    <a href="https://github.com/iluxz/mochiboot">mochiboot</a>
  </p>
</div>
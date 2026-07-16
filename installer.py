"""mochios real installer backend"""

import subprocess
import os
import re
import shutil
import time
from pathlib import Path

CUSTOM_EXTRAS = {"sober", "zen-browser"}


def run(cmd, check=True, capture=False, timeout=None, input_data=None):
    opts = dict(timeout=timeout, check=check)
    if capture:
        opts["capture_output"] = True
        opts["text"] = True
    if input_data is not None:
        opts["input"] = input_data
        opts["text"] = True
    r = subprocess.run(cmd, **opts)
    return r


def abortable_run(cmd, abort_flag, check=True, timeout=None):
    import select as _select
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out_lines = []
    poll = _select.poll()
    poll.register(proc.stdout, _select.POLLIN)
    deadline = None if timeout is None else time.time() + timeout
    while True:
        if abort_flag and abort_flag():
            proc.kill()
            proc.wait()
            raise RuntimeError("installation aborted")
        remaining = None
        if deadline is not None:
            remaining = deadline - time.time()
            if remaining <= 0:
                proc.kill()
                proc.wait()
                raise subprocess.TimeoutExpired(cmd, timeout, "".join(out_lines))
        poll_ms = min(int((remaining or 0.5) * 1000), 1000)
        events = poll.poll(poll_ms) if not proc.stdout.closed else []
        if events:
            line = proc.stdout.readline()
            if line:
                out_lines.append(line)
        if proc.poll() is not None:
            break
    for line in proc.stdout:
        out_lines.append(line)
    proc.wait()
    out = "".join(out_lines)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, out)
    return out


def wait_for_device(dev, timeout=5):
    for _ in range(timeout * 10):
        if Path(dev).exists():
            try:
                fd = os.open(dev, os.O_RDONLY)
                os.close(fd)
                return True
            except OSError:
                pass
        time.sleep(0.1)
    return False


def retry_cmd(cmd, lfn, max_retries=5, delay=2, **kwargs):
    for attempt in range(max_retries):
        try:
            return run(cmd, capture=True, **kwargs)
        except subprocess.TimeoutExpired:
            lfn(f"[red]{cmd[0]} timed out (attempt {attempt+1}/{max_retries})[/]")
            if attempt < max_retries - 1:
                lfn(f"retrying {cmd[0]} (attempt {attempt+2}/{max_retries})...")
                time.sleep(delay)
            else:
                raise
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or "(no output)")
            err = err.strip()[-200:]
            lfn(f"[red]{cmd[0]} failed (attempt {attempt+1}/{max_retries}): {err}[/]")
            if attempt < max_retries - 1:
                lfn(f"retrying {cmd[0]} (attempt {attempt+2}/{max_retries})...")
                time.sleep(delay)
            else:
                raise


def select_disk(disk):
    if not disk or not disk.startswith("/dev/"):
        raise ValueError(f"invalid disk: {disk}")
    return disk


def part_suffix(disk):
    return "p" if "nvme" in disk or "mmcblk" in disk or "nbd" in disk else ""


def partition_disk(disk, lfn):
    if not shutil.which("sgdisk"):
        raise RuntimeError("sgdisk not found, install gptfdisk")
    lfn(f"partitioning {disk}...")
    run(["sgdisk", "-Z", disk])
    run(["sgdisk", "-n", "1:0:+1M", "-t", "1:ef02", "-c", "1:BIOSBOOT", disk])
    run(["sgdisk", "-n", "2:0:+1G", "-t", "2:ef00", "-c", "2:EFI", disk])
    run(["sgdisk", "-n", "3:0:+2G", "-t", "3:8200", "-c", "3:SWAP", disk])
    run(["sgdisk", "-n", "4:0:0", "-t", "4:8300", "-c", "4:MOCHIOS", disk])
    run(["sync"])
    run(["udevadm", "settle", "--timeout=10"], check=False)
    if shutil.which("partprobe"):
        run(["partprobe", disk])
    run(["udevadm", "settle", "--timeout=10"], check=False)
    time.sleep(1)
    sep = part_suffix(disk)
    parts = [f"{disk}{sep}{n}" for n in (1, 2, 3, 4)]
    for p in parts:
        if not wait_for_device(p, timeout=10):
            raise RuntimeError(f"partition {p} did not appear after partitioning")
    return parts


def format_efi(part, lfn):
    lfn(f"formatting EFI {part}...")
    retry_cmd(["mkfs.fat", "-F", "32", "-n", "EFI", part], lfn, timeout=30)


def format_swap(part, lfn):
    lfn(f"formatting swap {part}...")
    retry_cmd(["mkswap", "-L", "SWAP", part], lfn, timeout=30)


def format_btrfs(part, lfn):
    lfn(f"formatting root {part} as btrfs...")
    retry_cmd(["mkfs.btrfs", "-f", "-L", "MOCHIOS", part], lfn, timeout=120)


def setup_btrfs(root_part, target, lfn):
    lfn("creating btrfs subvolumes...")
    tmp = "/mnt/btrfs_tmp"
    os.makedirs(tmp, exist_ok=True)
    run(["mount", "-o", "subvol=/", root_part, tmp])
    for sv in ["root_a", "root_b", "home", "snapshots", "var", "cache"]:
        run(["btrfs", "subvolume", "delete", f"{tmp}/{sv}"], check=False)
        run(["btrfs", "subvolume", "create", f"{tmp}/{sv}"])
    run(["umount", tmp])

    lfn("mounting btrfs subvolumes...")
    os.makedirs(target, exist_ok=True)
    run(["mount", "-o", "compress=zstd,subvol=root_a", root_part, target])
    os.makedirs(f"{target}/boot", exist_ok=True)
    os.makedirs(f"{target}/home", exist_ok=True)
    os.makedirs(f"{target}/var", exist_ok=True)
    os.makedirs(f"{target}/var/cache", exist_ok=True)
    run(["mount", "-o", "compress=zstd,subvol=home", root_part, f"{target}/home"])
    run(["mount", "-o", "compress=zstd,subvol=var", root_part, f"{target}/var"])
    run(["mount", "-o", "compress=zstd,subvol=cache", root_part, f"{target}/var/cache"])


def pacstrap_base(target, lfn, de="kde", bootloader="limine", kernels=None, extra_pkgs=None, abort_flag=None):
    if kernels is None:
        kernels = ["linux"]
    lfn("installing base system...")

    kernel_pkgs = []
    for k in kernels:
        kernel_pkgs.append(k)
        kernel_pkgs.append(k + "-headers")

    base = [
        "base", "base-devel",
        *kernel_pkgs,
        "linux-firmware",
        "btrfs-progs", "snapper", "sudo", "vim", "nano",
        "networkmanager", "dhcpcd", "openssh", "reflector",
        "sbctl",
        "man-db", "man-pages", "zsh", "git", "flatpak",
    ]
    de_pkgs = {
        "kde": ["plasma-desktop", "plasma-workspace", "kdeplasma-addons",
                "kwin", "konsole", "dolphin", "kate", "gwenview",
                "sddm", "kwallet-pam", "breeze", "breeze-gtk",
                "pipewire", "pipewire-pulse", "wireplumber", "kpipewire",
                "plasma-nm"],
        "gnome": ["gnome", "gnome-extra", "gdm"],
        "none": [],
    }
    bl_pkgs = {
        "limine": ["limine"],
        "grub": ["grub"],
    }
    pkgs = base + de_pkgs.get(de, []) + bl_pkgs.get(bootloader, []) + (extra_pkgs or [])
    abortable_run(["pacstrap", "-K", target] + pkgs, abort_flag, timeout=900)


def configure_system(target, config, lfn, efi_uuid, swap_uuid, root_uuid):
    hostname = config.get("hostname", "mochios")
    username = config.get("username", "mochi")
    password = config.get("password", "mochi")
    de = config.get("de", "kde")
    bootloader = config.get("bootloader", "limine")
    kernels = config.get("kernels", ["linux"])
    disk = config.get("disk", "")

    lfn("configuring system...")
    t = Path(target)

    (t / "etc/hostname").write_text(f"{hostname}\n")
    hosts = f"127.0.0.1\tlocalhost\n::1\t\tlocalhost\n127.0.1.1\t{hostname}.local\t{hostname}\n"
    (t / "etc/hosts").write_text(hosts)
    (t / "etc/locale.conf").write_text("LANG=en_US.UTF-8\n")

    locale = t / "etc/locale.gen"
    locale.write_text(locale.read_text().replace("#en_US.UTF-8 UTF-8", "en_US.UTF-8 UTF-8"))

    def ch(cmd, to=120, check=True):
        return run(["arch-chroot", target] + cmd, check=check, timeout=to)

    ch(["locale-gen"])
    ch(["ln", "-sf", "/usr/share/zoneinfo/UTC", "/etc/localtime"])
    ch(["hwclock", "--systohc"])
    ch(["mkinitcpio", "-P"], to=300)

    lfn("writing fstab...")
    fstab = (
        f"UUID={efi_uuid} /boot vfat rw,noatime,fmask=0022,dmask=0022 0 2\n"
        f"UUID={swap_uuid} swap swap defaults 0 0\n"
        f"UUID={root_uuid} /mnt/btrfs btrfs rw,noatime,compress=zstd,subvolid=5 0 0\n"
        f"UUID={root_uuid} / btrfs rw,noatime,compress=zstd,subvol=root_a 0 0\n"
        f"UUID={root_uuid} /home btrfs rw,noatime,compress=zstd,subvol=home 0 0\n"
        f"UUID={root_uuid} /var btrfs rw,noatime,compress=zstd,subvol=var 0 0\n"
        f"UUID={root_uuid} /var/cache btrfs rw,noatime,compress=zstd,subvol=cache 0 0\n"
    )
    (t / "etc/fstab").write_text(fstab)
    os.makedirs(f"{target}/mnt/btrfs", exist_ok=True)
    ch(["systemctl", "daemon-reload"])

    (t / "etc/abroot.conf").write_text(
        f"ROOT_PART=\"UUID={root_uuid}\"\n"
        f"BTRFS_MOUNT=\"/mnt/btrfs\"\n"
        f"ACTIVE_ROOT=\"root_a\"\n"
        f"NEXT_ROOT=\"root_b\"\n"
    )

    lfn("enabling multilib repo...")
    pmconf = t / "etc/pacman.conf"
    pmtext = pmconf.read_text()
    if not re.search(r'^\[multilib\]', pmtext, re.MULTILINE):
        pmtext += "\n[multilib]\nInclude = /etc/pacman.d/mirrorlist\n"
        pmconf.write_text(pmtext)

    lfn(f"creating user {username}...")
    ch(["useradd", "-m", "-G", "wheel,storage,power,audio,video", "-s", "/bin/zsh", username])
    run(["arch-chroot", target, "chpasswd"], input_data=f"{username}:{password}\nroot:{password}\n", timeout=30)

    (t / "etc/sudoers.d/10-mochi").write_text("%wheel ALL=(ALL:ALL) ALL\n")

    ch(["systemctl", "enable", "NetworkManager"])
    ch(["systemctl", "enable", "sshd"])

    dm = "sddm" if de == "kde" else "gdm" if de == "gnome" else None
    if dm:
        ch(["systemctl", "enable", dm])
        ch(["systemctl", "set-default", "graphical.target"])

    lfn("importing mochios signing key...")
    key_src = "/usr/share/mochios/mochios-key.pub"
    key_dst = f"{target}/usr/share/mochios/mochios-key.pub"
    if os.path.exists(key_src):
        os.makedirs(f"{target}/usr/share/mochios", exist_ok=True)
        shutil.copy2(key_src, key_dst)
        ch(["pacman-key", "--add", "/usr/share/mochios/mochios-key.pub"], check=False)
        ch(["pacman-key", "--lsign-key", "signing@mochios.dev"], check=False)
        lfn("  mochios key imported and trusted")
    else:
        lfn("  [yellow]mochios key not found, skipping[/]")

    if bootloader == "limine":
        install_limine(target, disk, root_uuid, lfn, ch, kernels=kernels)
    elif bootloader == "grub":
        install_grub(target, disk, root_uuid, lfn, ch, kernels=kernels)

    lfn("signing boot files with sbctl...")
    keydir = t / "var/lib/sbctl/keys/db"
    keydir.mkdir(parents=True, exist_ok=True)
    live_keydir = Path("/var/lib/sbctl/keys/db")
    for kf in ["db.key", "db.pem"]:
        src = live_keydir / kf
        if src.exists():
            shutil.copy(src, keydir / kf)
            (keydir / kf).chmod(0o600)
    sign_targets = [f"/boot/vmlinuz-{k}" for k in kernels]
    if bootloader == "limine":
        sign_targets += ["/boot/limine/limine-bios.sys", "/boot/EFI/BOOT/BOOTX64.EFI"]
    elif bootloader == "grub":
        sign_targets += ["/boot/EFI/BOOT/BOOTX64.EFI"]
    signed = 0
    for efifile in sign_targets:
        efipath = t / efifile.lstrip("/")
        if efipath.exists():
            r = ch(["sbctl", "sign", "--save", efifile], check=False)
            if r.returncode == 0:
                signed += 1
    if signed == len(sign_targets):
        lfn(f"  sbctl: {signed}/{len(sign_targets)} files signed")
    elif signed > 0:
        lfn(f"  [yellow]sbctl: {signed}/{len(sign_targets)} files signed (some missing/errors)[/]")
    else:
        lfn(f"  [red]sbctl: no files signed (check sbctl installation)[/]")

    lfn("enrolling secure boot keys into firmware...")
    r = ch(["sbctl", "enroll-keys", "--microsoft"], check=False)
    if r.returncode == 0:
        lfn("  secure boot keys enrolled (Microsoft keys included)")
    else:
        lfn("  [yellow]could not enroll keys (not UEFI or efivars not available) - enroll manually after reboot with 'sbctl enroll-keys --microsoft'[/]")


def get_uuid(part):
    return run(["blkid", "-s", "UUID", "-o", "value", part], capture=True, check=True).stdout.strip()


def install_limine(target, disk, root_uuid, lfn, ch, kernels=None):
    if kernels is None:
        kernels = ["linux"]
    lfn("installing limine...")

    config_lines = ["TIMEOUT=5", "VERBOSE=no", ""]
    for k in kernels:
        vmlinuz = f"/boot/vmlinuz-{k}"
        label = f"MOCHIOS ({k})" if len(kernels) > 1 else "MOCHIOS"
        config_lines.append(f":{label}")
        config_lines.append("    PROTOCOL=linux")
        config_lines.append(f"    KERNEL_PATH={vmlinuz}")
        config_lines.append(f"    CMDLINE=root=UUID={root_uuid} rootflags=subvol=root_a rw quiet loglevel=3")
        config_lines.append("")

    config = "\n".join(config_lines)

    lfn("installing limine (bios)...")
    limine_dir = Path(target) / "boot" / "limine"
    limine_dir.mkdir(parents=True, exist_ok=True)
    (limine_dir / "limine.conf").write_text(config)
    ch(["limine", "bios-install", disk], to=30, check=False)
    ch(["cp", "/usr/share/limine/limine-bios.sys", "/boot/limine/limine-bios.sys"], to=30)

    lfn("installing limine (uefi)...")
    efi_dir = Path(target) / "boot" / "EFI" / "BOOT"
    efi_dir.mkdir(parents=True, exist_ok=True)
    (efi_dir / "limine.conf").write_text(config)
    ch(["cp", "/usr/share/limine/BOOTX64.EFI", "/boot/EFI/BOOT/BOOTX64.EFI"], to=30)
    if Path("/usr/share/limine/BOOTIA32.EFI").exists():
        ch(["cp", "/usr/share/limine/BOOTIA32.EFI", "/boot/EFI/BOOT/BOOTIA32.EFI"], to=30)


def install_grub(target, disk, root_uuid, lfn, ch, kernels=None):
    if kernels is None:
        kernels = ["linux"]
    lfn("installing grub...")

    grub_def = Path(target) / "etc/default/grub"
    grub_text = grub_def.read_text() if grub_def.exists() else ""
    new_grub_text = []
    for line in grub_text.split("\n"):
        if line.startswith("GRUB_CMDLINE_LINUX="):
            new_grub_text.append('GRUB_CMDLINE_LINUX="rootflags=subvol=root_a"')
        else:
            new_grub_text.append(line)
    if "GRUB_CMDLINE_LINUX=" not in grub_text:
        new_grub_text.append('GRUB_CMDLINE_LINUX="rootflags=subvol=root_a"')
    grub_def.write_text("\n".join(new_grub_text))

    ch(["grub-install", "--target=x86_64-efi", "--efi-directory=/boot", "--bootloader-id=MOCHIOS", "--removable"])
    ch(["grub-install", "--target=i386-pc", disk])
    ch(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])


def cleanup_mounts(target):
    import subprocess as _sp
    for mp in [f"{target}/var/cache", f"{target}/var", f"{target}/home", f"{target}/boot", target]:
        _sp.run(["umount", "-l", mp], capture_output=True, check=False, timeout=10)
    _sp.run(["umount", "-l", "/mnt/btrfs_tmp"], capture_output=True, check=False, timeout=10)


def do_install(target="/mnt/mochios", config=None, log_fn=None, abort_flag=None):
    if log_fn is None:
        log_fn = print
    if config is None:
        config = {}

    mounts_cleanup_needed = False
    try:
        if abort_flag and abort_flag():
            raise RuntimeError("installation aborted")
        log_fn("starting mochios installation...")
        disk = select_disk(config.get("disk"))
        bios_part, efi_part, swap_part, root_part_p = partition_disk(disk, log_fn)
        mounts_cleanup_needed = True

        if abort_flag and abort_flag():
            raise RuntimeError("installation aborted")
        format_efi(efi_part, log_fn)
        format_swap(swap_part, log_fn)
        format_btrfs(root_part_p, log_fn)

        if abort_flag and abort_flag():
            raise RuntimeError("installation aborted")
        setup_btrfs(root_part_p, target, log_fn)

        efi_uuid = get_uuid(efi_part)
        swap_uuid = get_uuid(swap_part)
        root_uuid = get_uuid(root_part_p)

        run(["swapon", swap_part], check=False)
        run(["mount", efi_part, f"{target}/boot"])

        extra_all = config.get("extra_pkgs", []) or []
        repo_extra = [p for p in extra_all if isinstance(p, str) and p not in CUSTOM_EXTRAS]
        custom_extra = [p for p in extra_all if isinstance(p, str) and p in CUSTOM_EXTRAS]

        pacstrap_base(target, log_fn, de=config.get("de", "kde"), bootloader=config.get("bootloader", "limine"), kernels=config.get("kernels", ["linux"]), extra_pkgs=repo_extra, abort_flag=abort_flag)

        log_fn("relaxing SigLevel for custom packages...")
        pmconf_path = f"{target}/etc/pacman.conf"
        pmconf_orig = None
        if os.path.exists(pmconf_path):
            with open(pmconf_path) as f:
                pmconf_orig = f.read()
            with open(pmconf_path, "w") as f:
                f.write(pmconf_orig.replace("SigLevel = Required DatabaseOptional", "SigLevel = Optional TrustAll"))
        else:
            log_fn("  [yellow]no pacman.conf found in chroot[/]")

        log_fn("installing mochi packages from ISO...")
        pkg_src = "/opt/mochi-pkgs"
        pkg_tmp = f"{target}/tmp/mochi-pkgs"
        os.makedirs(pkg_tmp, exist_ok=True)
        pkgs = []
        if os.path.isdir(pkg_src):
            for f in sorted(os.listdir(pkg_src)):
                if f.endswith(".pkg.tar.zst") and "-debug-" not in f:
                    shutil.copy2(os.path.join(pkg_src, f), os.path.join(pkg_tmp, f))
                    pkgs.append(f"/tmp/mochi-pkgs/{f}")
            if pkgs:
                run(["arch-chroot", target, "pacman", "-U", "--noconfirm"] + pkgs, timeout=300)
                log_fn(f"  installed {len(pkgs)} mochi packages")
            else:
                log_fn("  [yellow]no mochi packages found to install[/]")
        else:
            log_fn("  [yellow]/opt/mochi-pkgs not found, installing binaries manually[/]")
            for src, dst in [("/usr/bin/mochi", f"{target}/usr/bin/mochi"), ("/usr/bin/abroot", f"{target}/usr/bin/abroot")]:
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    log_fn(f"  copied {src}")

        if custom_extra:
            optional_src = "/opt/mochi-optional-pkgs"
            if os.path.isdir(optional_src):
                extra_files = []
                for f in os.listdir(optional_src):
                    if f.endswith(".pkg.tar.zst") and "-debug-" not in f:
                        for want in custom_extra:
                            if f.startswith(want + "-"):
                                shutil.copy2(os.path.join(optional_src, f), os.path.join(pkg_tmp, f))
                                extra_files.append(f"/tmp/mochi-pkgs/{f}")
                                break
                if extra_files:
                    run(["arch-chroot", target, "pacman", "-U", "--noconfirm"] + extra_files, timeout=300)
                    log_fn(f"  installed {len(extra_files)} optional packages")
            else:
                log_fn(f"  [yellow]/opt/mochi-optional-pkgs not found[/]")

        shutil.rmtree(pkg_tmp, ignore_errors=True)

        if pmconf_orig is not None:
            log_fn("restoring pacman.conf SigLevel...")
            with open(pmconf_path, "w") as f:
                f.write(pmconf_orig)

        configure_system(target, config, log_fn, efi_uuid, swap_uuid, root_uuid)
        run(["swapoff", swap_part], check=False)
        log_fn("installation complete!")
        mounts_cleanup_needed = False
        return True

    except subprocess.CalledProcessError as e:
        log_fn(f"[red]Command failed: {' '.join(e.cmd)}[/]")
        log_fn(f"[red]Return code: {e.returncode}[/]")
        if e.stdout:
            log_fn(f"[dim]stdout: {e.stdout.strip()[-500:]}[/]")
        if e.stderr:
            log_fn(f"[red]stderr: {e.stderr.strip()[-500:]}[/]")
        return False
    except subprocess.TimeoutExpired as e:
        log_fn(f"[red]Command timed out after {e.timeout}s: {' '.join(e.cmd)}[/]")
        if e.output:
            out = e.output
            if isinstance(out, bytes):
                out = out.decode(errors="replace")
            log_fn(f"[dim]output: {out.strip()[-500:]}[/]")
        return False
    except Exception as e:
        import traceback
        log_fn(f"[red]Error: {e}[/]")
        log_fn(f"[dim]{traceback.format_exc()[-500:]}[/]")
        return False
    finally:
        if mounts_cleanup_needed:
            log_fn("[yellow]cleaning up mounts after failure...[/]")
            cleanup_mounts(target)

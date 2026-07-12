#!/bin/bash
# build-mochios.sh - build the mochios live ISO
set -euo pipefail

# error handler: prints line number and command that failed
trap 'echo "::error::build.sh failed at line $LINENO (exit code $?)"; tail -20 build.log 2>/dev/null | sed "s/^/::error::/" || true' ERR

# check for archiso
if ! command -v mkarchiso &>/dev/null; then
  echo "error: mkarchiso not found. install archiso package."
  exit 1
fi

MOCHIOS_DIR="${MOCHIOS_DIR:-/home/mochi/mochios}"
REPO_DIR="${REPO_DIR:-$MOCHIOS_DIR/repo}"
OUT_DIR="${OUT_DIR:-$MOCHIOS_DIR/out}"
ISO_DIR="${ISO_DIR:-$MOCHIOS_DIR/archiso-mochios}"
WORK_DIR="${WORK_DIR:-/home/mochi/mochios-work}"
SIGN_KEY="${SIGN_KEY:-signing@mochios.dev}"
GNUPGHOME="${GNUPGHOME:-/home/mochi/.mochios-gnupg}"
GNUPG() { gpg --homedir "$GNUPGHOME" "$@"; }

sign_pkg() {
  local pkg="$1"
  echo "==> signing $(basename "$pkg")..."
  rm -f "${pkg}.sig"
  GNUPG --detach-sign --local-user "$SIGN_KEY" "$pkg"
}

echo "==> cleaning work dir..."
rm -rf "$WORK_DIR"

_get_pkgver() {
  local pkgbuild="$1"
  grep -oP '^pkgver=\K.*' "$pkgbuild" | head -1
}

mkdir -p "$REPO_DIR/os/x86_64"

echo "==> rebuilding mochi pkg..."
cd "$MOCHIOS_DIR/pkgbuilds/mochi"
pkgver=$(_get_pkgver PKGBUILD)
tar czf "mochi-$pkgver.tar.gz" -C "$MOCHIOS_DIR/mochi" .
sudo -u mochi makepkg -cf --noconfirm
cp "$MOCHIOS_DIR/pkgbuilds/mochi"/mochi-[0-9]*.pkg.tar.zst "$REPO_DIR/os/x86_64/"

echo "==> rebuilding mochiinstall pkg..."
cd "$MOCHIOS_DIR/pkgbuilds/mochiinstall"
pkgver=$(_get_pkgver PKGBUILD)
tar czf "mochiinstall-$pkgver.tar.gz" -C "$MOCHIOS_DIR" \
  mochiinstall_wrapper installer.py mochiinstall_app.py mochi_ascii.py
sudo -u mochi makepkg -cf --noconfirm
cp "$MOCHIOS_DIR/pkgbuilds/mochiinstall"/mochiinstall-[0-9]*.pkg.tar.zst "$REPO_DIR/os/x86_64/"

echo "==> rebuilding mochios-branding pkg..."
cd "$MOCHIOS_DIR/pkgbuilds/mochios-branding"
pkgver=$(_get_pkgver PKGBUILD)
tar czf "mochios-branding-$pkgver.tar.gz" -C "$MOCHIOS_DIR/pkgbuilds/mochios-branding" --exclude="mochios-branding-$pkgver.tar.gz" usr
sudo -u mochi makepkg -cf --noconfirm
cp "$MOCHIOS_DIR/pkgbuilds/mochios-branding"/mochios-branding-[0-9]*.pkg.tar.zst "$REPO_DIR/os/x86_64/"

echo "==> rebuilding mochi-abroot pkg..."
cd "$MOCHIOS_DIR/pkgbuilds/mochi-abroot"
pkgver=$(_get_pkgver PKGBUILD)
tar czf "mochi-abroot-$pkgver.tar.gz" -C "$MOCHIOS_DIR/pkgbuilds/mochi-abroot" --exclude="mochi-abroot-$pkgver.tar.gz" --exclude='pkg' --exclude='src' abroot.sh abroot.conf
sudo -u mochi makepkg -cf --noconfirm
cp "$MOCHIOS_DIR/pkgbuilds/mochi-abroot"/mochi-abroot-[0-9]*.pkg.tar.zst "$REPO_DIR/os/x86_64/"

echo "==> signing packages..."
for pattern in \
  "$REPO_DIR/os/x86_64/"mochi-[0-9]*.pkg.tar.zst \
  "$REPO_DIR/os/x86_64/"mochiinstall-[0-9]*.pkg.tar.zst \
  "$REPO_DIR/os/x86_64/"mochi-abroot-[0-9]*.pkg.tar.zst \
  "$REPO_DIR/os/x86_64/"mochios-branding-[0-9]*.pkg.tar.zst; do
  for pkg in $pattern; do
    [ -f "$pkg" ] && sign_pkg "$pkg"
  done
done

echo "==> updating repo..."
cd "$REPO_DIR"
rm -f os/x86_64/mochi.db.tar.zst.lck
rm -f os/x86_64/mochi.db.tar.zst.sig
GNUPGHOME="$GNUPGHOME" repo-add --sign os/x86_64/mochi.db.tar.zst os/x86_64/mochi-[0-9]*.pkg.tar.zst
GNUPGHOME="$GNUPGHOME" repo-add --sign os/x86_64/mochi.db.tar.zst os/x86_64/mochiinstall-[0-9]*.pkg.tar.zst
GNUPGHOME="$GNUPGHOME" repo-add --sign os/x86_64/mochi.db.tar.zst os/x86_64/mochi-abroot-[0-9]*.pkg.tar.zst
GNUPGHOME="$GNUPGHOME" repo-add --sign os/x86_64/mochi.db.tar.zst os/x86_64/mochios-branding-[0-9]*.pkg.tar.zst

echo "==> staging public key for ISO..."
if [ -f "$REPO_DIR/pubkey/mochios-key.pub" ]; then
  mkdir -p "$ISO_DIR/airootfs/usr/share/mochios"
  cp "$REPO_DIR/pubkey/mochios-key.pub" "$ISO_DIR/airootfs/usr/share/mochios/"
else
  echo "  [yellow]public key not found at $REPO_DIR/pubkey/mochios-key.pub, skipping[/]"
fi

echo "==> staging mochi packages for installer..."
mkdir -p "$ISO_DIR/airootfs/opt/mochi-pkgs"
for pkg in mochi mochiinstall mochi-abroot mochios-branding; do
  cp "$REPO_DIR/os/x86_64/"$pkg-[0-9]*.pkg.tar.zst "$ISO_DIR/airootfs/opt/mochi-pkgs/"
done

echo "==> staging optional packages for installer..."
mkdir -p "$ISO_DIR/airootfs/opt/mochi-optional-pkgs"
echo "  (no optional packages configured)"

echo "==> stamping build date into mochios-release..."
BUILD_DATE=$(date +%Y-%m-%d)
sed -i "s/@BUILD_DATE@/$BUILD_DATE/" "$ISO_DIR/airootfs/etc/mochios-release"

echo "==> staging secure boot keys..."
SB_KEY_SRC="$MOCHIOS_DIR/secure-boot"
SB_KEY_DST="$ISO_DIR/airootfs/var/lib/sbctl/keys/db"
if [ -f "$SB_KEY_SRC/db.key" ] && [ -f "$SB_KEY_SRC/db.crt" ]; then
  mkdir -p "$SB_KEY_DST"
  cp "$SB_KEY_SRC/db.key" "$SB_KEY_DST/db.key"
  cp "$SB_KEY_SRC/db.crt" "$SB_KEY_DST/db.pem"
  chmod 600 "$SB_KEY_DST/db.key"
  echo "  secure boot keys staged"
else
  echo "  [yellow]secure boot keys not found, sbctl will generate on first boot[/]"
fi

echo "==> building iso..."
mkdir -p "$OUT_DIR"
mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$ISO_DIR"

echo "==> iso built at $OUT_DIR"
ls -lh "$OUT_DIR"/*.iso

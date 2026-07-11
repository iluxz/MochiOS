#!/bin/bash
# abroot - A/B root atomic update manager for mochios
# manages two root subvolumes (root_a, root_b) on btrfs

set -euo pipefail

CONF="${CONF:-/etc/abroot.conf}"

if [ -f "$CONF" ]; then
  source "$CONF"
fi

ROOT_PART="${ROOT_PART:-/dev/mapper/mochios-root}"
BTRFS_MOUNT="${BTRFS_MOUNT:-/mnt/btrfs}"
ACTIVE_ROOT="${ACTIVE_ROOT:-root_a}"
NEXT_ROOT="${NEXT_ROOT:-root_b}"

mount_btrfs() {
  if ! mountpoint -q "$BTRFS_MOUNT"; then
    mkdir -p "$BTRFS_MOUNT"
    mount "$ROOT_PART" "$BTRFS_MOUNT"
  fi
}

mount_chroot() {
  local target="$1"
  mkdir -p "$target"
  mount --bind "$BTRFS_MOUNT/$NEXT_ROOT" "$target"
  mount --bind /dev "$target/dev"
  mount --bind /proc "$target/proc"
  mount --bind /sys "$target/sys"
  if mountpoint -q /boot 2>/dev/null; then
    mkdir -p "$target/boot"
    mount --bind /boot "$target/boot"
  fi
}

umount_chroot() {
  local target="$1"
  umount "$target/dev" 2>/dev/null || true
  umount "$target/proc" 2>/dev/null || true
  umount "$target/sys" 2>/dev/null || true
  umount "$target/boot" 2>/dev/null || true
  umount "$target" 2>/dev/null || true
}

status() {
  mount_btrfs
  echo "active:  $ACTIVE_ROOT"
  echo "next:    $NEXT_ROOT"
  echo "---"
  btrfs subvolume list "$BTRFS_MOUNT" 2>/dev/null || true
  echo "---"
  ls "$BTRFS_MOUNT/snapshots/" 2>/dev/null || echo "no snapshots"
}

deploy() {
  mount_btrfs

  local snapshot="$BTRFS_MOUNT/snapshots/$(date +%Y%m%d_%H%M%S)_$ACTIVE_ROOT"
  mkdir -p "$BTRFS_MOUNT/snapshots"
  echo "creating snapshot: $(basename "$snapshot")"
  btrfs subvolume snapshot -r "$BTRFS_MOUNT/$ACTIVE_ROOT" "$snapshot"

  echo "updating $NEXT_ROOT..."
  btrfs subvolume delete "$BTRFS_MOUNT/$NEXT_ROOT" 2>/dev/null || true
  btrfs subvolume snapshot "$BTRFS_MOUNT/$ACTIVE_ROOT" "$BTRFS_MOUNT/$NEXT_ROOT"

  local target="/mnt/next"
  mount_chroot "$target"

  echo "running pacman in $NEXT_ROOT..."
  if [ $# -eq 0 ]; then
    arch-chroot "$target" pacman --noconfirm -Syu
  else
    arch-chroot "$target" pacman --noconfirm -S "$@"
  fi

  umount_chroot "$target"
  echo "update deployed to $NEXT_ROOT"
  echo "reboot and select $NEXT_ROOT to apply"
}

rollback() {
  mount_btrfs
  local latest
  latest=$(ls -t "$BTRFS_MOUNT/snapshots/" 2>/dev/null | head -1)
  if [ -z "$latest" ]; then
    echo "no snapshots found"
    exit 1
  fi
  echo "rolling back to: $latest"
  echo "WARNING: this will DELETE the current $ACTIVE_ROOT subvolume"
  if [ "${1:--}" != "-f" ] && [ "${1:--}" != "--force" ]; then
    read -rp "are you sure? [y/N] " confirm
    case "$confirm" in
      [yY]*) ;;
      *) echo "rollback cancelled"; exit 1 ;;
    esac
  fi
  btrfs subvolume delete "$BTRFS_MOUNT/$ACTIVE_ROOT"
  btrfs subvolume snapshot "$BTRFS_MOUNT/snapshots/$latest" "$BTRFS_MOUNT/$ACTIVE_ROOT"
  echo "rolled back to $latest"
}

case "${1:-status}" in
  status)
    status
    ;;
  deploy)
    shift
    deploy "$@"
    ;;
  rollback)
    shift
    rollback "$@"
    ;;
  list-snapshots|snapshot)
    mount_btrfs
    echo "snapshots:"
    ls -lt "$BTRFS_MOUNT/snapshots/" 2>/dev/null || echo "no snapshots"
    ;;
  *)
    echo "usage: abroot {status|deploy|rollback|snapshot}"
    exit 1
    ;;
esac

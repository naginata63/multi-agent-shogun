#!/bin/bash
# Safer NVMe migration Phase 4+5 script
# 前提:
# - Clonezilla Live を UEFI モードで起動済み
# - /dev/nvme0n1p1 = 新 EFI (FAT32, esp)
# - /dev/nvme0n1p2 = 新 root (ext4, sde4 から Clonezilla 済み)
# - /dev/sde4 = 旧 root は接続したまま残す

set -euo pipefail

NVME_DISK="/dev/nvme0n1"
NVME_EFI="/dev/nvme0n1p1"
NVME_ROOT="/dev/nvme0n1p2"
OLD_ROOT="/dev/sde4"
MNT="/mnt"

cleanup() {
  set +e
  mountpoint -q "$MNT/dev/pts" && umount "$MNT/dev/pts"
  mountpoint -q "$MNT/dev" && umount "$MNT/dev"
  mountpoint -q "$MNT/proc" && umount "$MNT/proc"
  mountpoint -q "$MNT/sys" && umount "$MNT/sys"
  mountpoint -q "$MNT/run" && umount "$MNT/run"
  mountpoint -q "$MNT/boot/efi" && umount "$MNT/boot/efi"
  mountpoint -q "$MNT" && umount "$MNT"
}
trap cleanup EXIT

need_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "ERROR: sudo/root で実行してください" >&2
    exit 1
  fi
}

need_root

echo "=========================================="
echo " NVMe 移行 Phase 4+5 安全版"
echo "=========================================="
echo "対象:"
echo "  新 EFI : $NVME_EFI"
echo "  新 root: $NVME_ROOT"
echo "  旧 root: $OLD_ROOT  ※これは変更しない"
echo ""

if [ ! -d /sys/firmware/efi ]; then
  echo "ERROR: Live USB が UEFI モードで起動していません。UEFI: USB から起動し直してください。" >&2
  exit 1
fi

for d in "$NVME_EFI" "$NVME_ROOT" "$OLD_ROOT"; do
  if [ ! -b "$d" ]; then
    echo "ERROR: $d が見つかりません。lsblkでデバイス名を確認してください。" >&2
    exit 1
  fi
done

ROOT_TYPE=$(blkid -s TYPE -o value "$NVME_ROOT" || true)
EFI_TYPE=$(blkid -s TYPE -o value "$NVME_EFI" || true)
if [ "$ROOT_TYPE" != "ext4" ]; then
  echo "ERROR: $NVME_ROOT は ext4 ではありません。現在: ${ROOT_TYPE:-unknown}" >&2
  exit 1
fi
if [ "$EFI_TYPE" != "vfat" ]; then
  echo "ERROR: $NVME_EFI は vfat/FAT32 ではありません。現在: ${EFI_TYPE:-unknown}" >&2
  exit 1
fi

if mount | grep -q "^$NVME_ROOT "; then
  echo "ERROR: $NVME_ROOT が既にマウントされています。" >&2
  exit 1
fi
if mountpoint -q "$MNT"; then
  echo "ERROR: $MNT が既にマウントポイントです。" >&2
  exit 1
fi

echo "現在のディスク状態:"
lsblk -f "$NVME_DISK" /dev/sde || true
echo ""
echo "このスクリプトは以下を実施します:"
echo "  1) $NVME_ROOT を e2fsck + resize2fs で拡張"
echo "  2) $NVME_ROOT のUUIDを新規生成して、$OLD_ROOT とのUUID重複を解消"
echo "  3) 新rootの /etc/fstab の / と /boot/efi を新UUIDへ更新"
echo "  4) chrootでGRUBを $NVME_EFI にインストール"
echo "  5) update-grub と update-initramfs -u -k all を実行"
echo ""
read -rp "Phase 1-3完了済みなら y で続行 > " confirm
if [ "$confirm" != "y" ]; then
  echo "中断"
  exit 1
fi

echo "==== Phase 4: filesystem check + resize ===="
e2fsck -fy "$NVME_ROOT"
resize2fs "$NVME_ROOT"
e2fsck -fy "$NVME_ROOT"

echo "==== UUID重複対策: NVMe root UUIDを新規生成 ===="
OLD_NVME_ROOT_UUID=$(blkid -s UUID -o value "$NVME_ROOT")
tune2fs -U random "$NVME_ROOT"
e2fsck -fy "$NVME_ROOT"
NEW_ROOT_UUID=$(blkid -s UUID -o value "$NVME_ROOT")
NEW_EFI_UUID=$(blkid -s UUID -o value "$NVME_EFI")

echo "旧 NVMe root UUID: $OLD_NVME_ROOT_UUID"
echo "新 NVMe root UUID: $NEW_ROOT_UUID"
echo "新 EFI UUID      : $NEW_EFI_UUID"

if [ -z "$NEW_ROOT_UUID" ] || [ -z "$NEW_EFI_UUID" ]; then
  echo "ERROR: UUID取得に失敗しました。" >&2
  exit 1
fi

echo "==== Phase 5-A: mount ===="
mount "$NVME_ROOT" "$MNT"
mkdir -p "$MNT/boot/efi" "$MNT/proc" "$MNT/sys" "$MNT/dev" "$MNT/dev/pts" "$MNT/run"
mount "$NVME_EFI" "$MNT/boot/efi"
mount --bind /proc "$MNT/proc"
mount --bind /sys "$MNT/sys"
mount --bind /dev "$MNT/dev"
mount --bind /dev/pts "$MNT/dev/pts"
mount --bind /run "$MNT/run"

echo "==== Phase 5-B: fstab更新 ===="
FSTAB="$MNT/etc/fstab"
if [ ! -f "$FSTAB" ]; then
  echo "ERROR: $FSTAB がありません。Clonezilla rootコピーが失敗している可能性があります。" >&2
  exit 1
fi
cp "$FSTAB" "$MNT/etc/fstab.bak.migration"

if grep -Eq '^[[:space:]]*UUID=[^[:space:]]+[[:space:]]+/[[:space:]]+' "$FSTAB"; then
  sed -i -E "s|^[[:space:]]*UUID=[^[:space:]]+([[:space:]]+/[[:space:]]+)|UUID=$NEW_ROOT_UUID\1|" "$FSTAB"
else
  echo "ERROR: fstabに UUID=... / のroot行が見つかりません。手動確認してください。" >&2
  echo "--- fstab ---" >&2
  cat "$FSTAB" >&2
  exit 1
fi

if grep -Eq '^[[:space:]]*[^#[:space:]]+[[:space:]]+/boot/efi[[:space:]]+' "$FSTAB"; then
  sed -i -E "s|^[[:space:]]*[^#[:space:]]+([[:space:]]+/boot/efi[[:space:]]+)|UUID=$NEW_EFI_UUID\1|" "$FSTAB"
else
  echo "UUID=$NEW_EFI_UUID /boot/efi vfat umask=0077 0 1" >> "$FSTAB"
fi

echo "更新後 fstab:"
cat "$FSTAB"

echo "==== Phase 5-C: chroot + grub-install ===="
chroot "$MNT" /bin/bash <<'CHROOT_EOF'
set -euo pipefail
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu --recheck /dev/nvme0n1
update-grub
update-initramfs -u -k all
CHROOT_EOF

echo "==== Phase 5-D: boot files確認 ===="
find "$MNT/boot/efi/EFI" -maxdepth 3 -type f | sort | sed 's#^#/##' | head -50 || true

echo ""
echo "=========================================="
echo "完了。次は再起動してBIOSで ubuntu/NVMe を最優先にしてください。"
echo "起動後確認: df / が /dev/nvme0n1p2、df /boot/efi が /dev/nvme0n1p1"
echo "=========================================="

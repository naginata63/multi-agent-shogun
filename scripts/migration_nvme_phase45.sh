#!/bin/bash
# NVMe 移行 Phase 4 + Phase 5 自動化スクリプト
# 使い方 (clonezilla live USB の terminal):
#   wget https://raw.githubusercontent.com/naginata63/multi-agent-shogun/main/scripts/migration_nvme_phase45.sh
#   sudo bash migration_nvme_phase45.sh
#
# 前提:
#   - Phase 1-3 完了済 (gparted で nvme0n1p1=EFI 512M / nvme0n1p2=ext4 root 1.8T 作成・clonezilla で sde4 → nvme0n1p2 クローン済)
#   - 旧 SSD (sde) は接続済 (取り外していない)
#
# 実施内容:
#   Phase 4: resize2fs で nvme0n1p2 を 1.8T 領域に拡張
#   Phase 5: chroot で grub-install + fstab 更新 (新 EFI UUID 自動反映)

set -e

NVME_ROOT="/dev/nvme0n1p2"
NVME_EFI="/dev/nvme0n1p1"
MNT="/mnt"

echo "=========================================="
echo "  NVMe 移行 Phase 4+5 自動化スクリプト"
echo "=========================================="
echo ""
echo "対象:"
echo "  新 root: $NVME_ROOT"
echo "  新 EFI : $NVME_EFI"
echo ""
echo "実行前確認:"
echo "  - Phase 1-3 (gparted + clonezilla) 完了していますか? (y で続行)"
read -p "> " confirm
[ "$confirm" != "y" ] && { echo "中断"; exit 1; }
echo ""

# ============================================================
# Phase 4: ファイルシステム拡張
# ============================================================
echo "==== Phase 4: ファイルシステム拡張 ===="

echo "[4.1] e2fsck -fy $NVME_ROOT (拡張前チェック)"
e2fsck -fy "$NVME_ROOT"

echo "[4.2] resize2fs $NVME_ROOT (1.8T 拡張)"
resize2fs "$NVME_ROOT"

echo "[4.3] e2fsck -fy $NVME_ROOT (拡張後チェック)"
e2fsck -fy "$NVME_ROOT"

echo "✅ Phase 4 完了"
echo ""

# ============================================================
# Phase 5: chroot で grub-install + fstab 更新
# ============================================================
echo "==== Phase 5: chroot で grub-install + fstab 更新 ===="

# 5-A. マウント準備
echo "[5-A] mount 準備"
mount "$NVME_ROOT" "$MNT"
mkdir -p "$MNT/boot/efi"
mount "$NVME_EFI" "$MNT/boot/efi"
for f in proc sys dev dev/pts run; do
  mount --bind "/$f" "$MNT/$f"
done

# 5-B. UUID 確認 + fstab 自動書換
echo "[5-B] UUID 確認 + fstab 書換"
NEW_EFI_UUID=$(blkid -s UUID -o value "$NVME_EFI")
echo "  新 EFI UUID: $NEW_EFI_UUID"

if [ -z "$NEW_EFI_UUID" ]; then
  echo "❌ EFI UUID 取得失敗・スクリプト中断"
  exit 1
fi

# fstab の /boot/efi 行の UUID を新 EFI UUID に書換 (sed)
# 形式: UUID=ABCD-1234 /boot/efi vfat ...
if grep -qE '^[^#]*\s+/boot/efi\s' "$MNT/etc/fstab"; then
  cp "$MNT/etc/fstab" "$MNT/etc/fstab.bak.migration"
  sed -i -E "s|^UUID=[A-Fa-f0-9-]+(\s+/boot/efi\s)|UUID=$NEW_EFI_UUID\1|" "$MNT/etc/fstab"
  echo "  ✅ fstab /boot/efi 行を新 UUID に更新"
  echo "  (バックアップ: /mnt/etc/fstab.bak.migration)"
else
  echo "  ⚠️ fstab に /boot/efi 行が見つからず・手動確認推奨"
fi

# 5-C. chroot で grub-install + update-grub + update-initramfs
echo "[5-C] chroot で grub-install"
chroot "$MNT" /bin/bash <<'CHROOT_EOF'
set -e
echo "  > grub-install --efi-directory=/boot/efi --bootloader-id=ubuntu /dev/nvme0n1"
grub-install --efi-directory=/boot/efi --bootloader-id=ubuntu /dev/nvme0n1
echo "  > update-grub"
update-grub
echo "  > update-initramfs -u"
update-initramfs -u
echo "  ✅ chroot 内処理完了"
CHROOT_EOF

# 5-D. アンマウント
echo "[5-D] アンマウント"
umount -R "$MNT" 2>&1 || {
  echo "  逆順 umount を試行..."
  for p in dev/pts dev sys proc run boot/efi; do
    umount "$MNT/$p" 2>/dev/null || true
  done
  umount "$MNT" 2>/dev/null || true
}

echo ""
echo "=========================================="
echo "✅ Phase 4 + 5 完了"
echo ""
echo "次の手順:"
echo "  1. live USB を取り外して再起動"
echo "  2. 起動時 F2/Del で BIOS に入る"
echo "  3. Boot Order で 'ubuntu' (NVMe) を最上位に"
echo "  4. 保存して再起動"
echo "  5. 起動後: df / で /dev/nvme0n1p2 確認"
echo "=========================================="

# PC 換装 NVMe 移行作業手順 — 2026-05-04 (C 案: 完全再構築)

## 背景

- PC 換装で旧 SATA SSD (sde) を新 PC へ物理移植
- 換装時 clonezilla で sde → nvme0n1 にクローン済 (16:00 頃)
- ただし boot loader が sde 優先のままで現在も `/dev/sde4` (SATA) から起動中
- NVMe (nvme0n1) を root にすれば体感速度 5-10 倍向上見込み

## 殿の方針確定 (2026-05-05)

- **C 案 (完全再構築) 採用**: 「時間かかってもややこしくない方法がいい」殿命
- 理由: A 案 (p3 移動) / B 案 (p1 流用) は EFI 操作が複雑・C 案は「全削除 → 新規 2 個作る」で最もシンプル

## 現状 → 移行後の比較

| | 現状 NVMe (sde クローン) | 移行後 NVMe |
|--|------|--------|
| p1 | 128M (MSR Windows 残骸) | **削除 → 新 EFI 512M に** |
| p2 | 767.5G NTFS (写真重複・sde2 にあり) | **削除** |
| p3 | 513M `/boot/efi` | **削除** |
| p4 | 976.6G ext4 root クローン | **削除** |
| 新 p1 | — | **EFI System Partition (FAT32 / 512M)** |
| 新 p2 | — | **/ (ext4 root / 約 1.8T)** ← 1.7T 級単一 root 達成 |

## 完了形

- nvme0n1 = EFI 512M + root 1.8T (シンプル 2 partition)
- sde = 旧 SATA SSD として残置 (写真 sde2 + 旧 root sde4 維持・将来取り外し別途)
- 写真ライブラリ (sde2) 経由でアクセス可能

## 作業手順 (clonezilla live USB 1 セッションで完結)

### Phase 1: 起動準備 (作業前)

| # | 操作 | 主体 |
|---|------|------|
| 1.1 | cdp 漫画完了 + 全エージェント停止 + cron 一時停止 | 将軍/殿 |
| 1.2 | 22:20 手動バックアップ完了確認 (/mnt/backup 558G・5/4 22:20) ✅ | 既済 |
| 1.3 | shutdown → clonezilla live USB ブート | 殿 |

### Phase 2: gparted で NVMe 完全再構築

⚠️ **致命的注意**: gparted で必ず `/dev/nvme0n1` を選択。間違えて `/dev/sde` を選ぶと旧 root も消失する。

| # | 操作 |
|---|------|
| 2.1 | gparted 起動 → 右上のドライブ選択メニューで **`/dev/nvme0n1` (1.9T)** を確認・選択 |
| 2.2 | nvme0n1p1 / p2 / p3 / p4 を**全部右クリック → Delete**(swap 等あれば全部) |
| 2.3 | 「Apply」前に **partition 全部 unallocated** であることを目視 |
| 2.4 | unallocated 領域に新規 partition 1 作成: `New` → `File system: fat32` → Size: **512 MiB** → ラベル `EFI` → Apply |
| 2.5 | 残り unallocated 領域に新規 partition 2 作成: `New` → `File system: ext4` → Size: 残り全部 (約 1.8T) → ラベル `root` → Apply |
| 2.6 | 新 nvme0n1p1 (EFI) を右クリック → `Manage Flags` → **`boot` + `esp` チェック**して Apply |
| 2.7 | gparted 終了・両 partition の UUID を確認 (gparted の Information で表示・後で fstab/grub に必要) |

### Phase 3: clonezilla で sde4 → nvme0n1p2 root クローン

| # | 操作 |
|---|------|
| 3.1 | clonezilla メニュー → `device-device` → `parts_to_local_part` |
| 3.2 | Source: `/dev/sde4` (旧 root) |
| 3.3 | Target: `/dev/nvme0n1p2` (新 root・1.8T) |
| 3.4 | Beginner mode・既定設定で実行 |
| 3.5 | 完了時間目安: 30-60 分 (~580G コピー) |
| 3.6 | クローン完了後、sde4 の中身が nvme0n1p2 に block-level コピーされる |

### 🚀 Phase 4+5 まとめて自動実行 (推奨・楽な方法・安全版 v2)

clonezilla live USB の terminal で **2 行だけ**打てば全自動:

```bash
wget https://raw.githubusercontent.com/naginata63/multi-agent-shogun/main/scripts/migration_nvme_phase45.sh
sudo bash migration_nvme_phase45.sh
```

#### 📋 安全版 v2 (2026-05-05・SHA256 `e349a791...5da9c3`) の機能

実行前チェック:
- ✅ **UEFI モード確認** (`/sys/firmware/efi` 存在チェック・Legacy BIOS なら即エラー停止)
- ✅ **デバイス存在確認** (nvme0n1p1 / nvme0n1p2 / sde4 が block device として存在)
- ✅ **ファイルシステム種別確認** (nvme0n1p1=vfat / nvme0n1p2=ext4)
- ✅ **mount 状態確認** (nvme0n1p2 や /mnt が既使用なら即エラー停止)
- ✅ **lsblk 表示**で殿に現状確認させる
- ✅ **「y で続行」プロンプト** で殿確認

実行内容:
- Phase 4: e2fsck → resize2fs → e2fsck (1.8T 拡張)
- **🚨 UUID 重複対策 (致命的問題の解消)**: `tune2fs -U random /dev/nvme0n1p2` で **新 root UUID 生成** → sde4 と別 UUID になる
- Phase 5-A: mount (root + EFI + bind proc/sys/dev/dev-pts/run)
- Phase 5-B: fstab 自動書換 (`/` 行 + `/boot/efi` 行を **両方とも新 UUID へ**・元 fstab.bak.migration バックアップ)
- Phase 5-C: chroot → `grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu --recheck /dev/nvme0n1` → update-grub → **update-initramfs -u -k all** (`-k all` で全カーネル更新)
- Phase 5-D: boot files 確認 (find で grub install 結果表示)
- 終了時: cleanup trap で **失敗時も確実 umount** (障害時の手動 fallback 不要)

⚠️ **前提**: Phase 1-3 (gparted + clonezilla) 完了済 + UEFI モードで Live USB 起動済 + sde4 残置 (touch しない・保険用)

---

### 🆘 wget 失敗時の救済策

⚠️ **以前ここにあった手動 1 ブロックは削除しました** (root UUID 重複対策が含まれていなかったため危険)。

wget 失敗時は **下記の「USB 1 本完結」案を使用してください**。USB の第 2 partition に migration_nvme_phase45.sh 安全版を保管 → live USB から実行で同じ効果を達成。

---

### 💡 推奨: clonezilla USB の空き領域に script 保管 (1 本完結)

殿の発想 (2026-05-05): **clonezilla USB 自体に script 入れておけば 1 本で完結**。ネット不要・別 USB 不要。

#### 事前準備 (殿の通常 PC で 1 度だけ)

clonezilla USB は ISO 部分が read-only ゆえ、**USB の空き領域に第 2 partition (ext4 または fat32) を作る**。

##### 方法 A: gparted で USB に第 2 partition 追加

```bash
# 1. clonezilla USB を挿す
# 2. lsblk で USB の device 名確認 (例 /dev/sdb)
lsblk

# 3. gparted 起動
sudo gparted /dev/sdb
```

gparted GUI:
- USB のデバイスを選択 (右上ドロップダウン)
- 末尾の **未割り当て (unallocated) 領域**を右クリック → New
- File system: **ext4**・Label: `migration_data`・Size: 残り全部 (1GB あれば十分)
- Apply

##### script 保管

```bash
# USB の第 2 partition が /dev/sdb2 (gparted の output で確認) として
sudo mount /dev/sdb2 /media/murakami/migration_data
sudo cp /home/murakami/multi-agent-shogun/scripts/migration_nvme_phase45.sh /media/murakami/migration_data/
sudo cp /home/murakami/multi-agent-shogun/work/pc_migration_20260504/migration_plan.md /media/murakami/migration_data/
sudo umount /media/murakami/migration_data
```

これで USB に **clonezilla + 移行 script + 手順書 md** 全部入った 1 本の USB が完成。

#### 移行作業時 (clonezilla live USB ブート後)

```bash
# USB の第 2 partition を mount (live USB の中で USB 自身を別マウント)
sudo mkdir -p /mnt/usb
sudo lsblk           # USB のデバイス名確認 (例 /dev/sda2)
sudo mount /dev/sda2 /mnt/usb

# script 実行
sudo bash /mnt/usb/migration_nvme_phase45.sh
```

ネット繋がっていなくても OK・GitHub アクセス不要・全制御下。

#### 殿のスマホで md を見たい場合

`migration_plan.md` も USB 第 2 partition に入っているゆえ、
- 別 PC から USB を読む (殿が他 PC 持っているなら)
- live USB 内の vim / less で `/mnt/usb/migration_plan.md` を開いて読む
- 事前に殿のスマホに md を保存しておく (Termux や Markor アプリで読む)

---

### 🔄 USB メモリ別持ち込み案 (clonezilla USB 1 本では難しい場合)

clonezilla USB が ISO 焼き直し済 + 第 2 partition 作成不可の場合・別 USB メモリで対応:

```bash
# 殿の通常 PC で別 USB に保管
cp /home/murakami/multi-agent-shogun/scripts/migration_nvme_phase45.sh /media/murakami/<別USB>/
```

clonezilla live USB ブート後・別 USB を追加で刺す:

```bash
sudo mkdir -p /mnt/usb
sudo mount /dev/sdX1 /mnt/usb     # X は別 USB のデバイス名 (lsblk で確認)
sudo bash /mnt/usb/migration_nvme_phase45.sh
```

---

### Phase 4: ファイルシステム拡張 (sde4 サイズ → 1.8T へ) — 手動コマンド版 (参考)

> ⚠️ **以降は clonezilla GUI ではなく live USB の「ターミナル (黒い画面)」で操作**。
>
> **ターミナルの開き方 (clonezilla live USB)**:
> 1. clonezilla クローン完了画面で `Choose mode` メニュー → `Enter command line prompt` (シェルに入る)
> 2. もしくは Exit メニューで `Choose Y to enter command line` を選ぶ
> 3. プロンプト `user@debian:~$` が出れば成功
>
> 全コマンドは **スマホで本 md を見ながら**、PC のターミナルにコピペで OK (タイプミス防止)。

#### コマンド (順番に 1 行ずつ実行)

```bash
# 4.1 整合性チェック (拡張前)
sudo e2fsck -f /dev/nvme0n1p2
# 期待出力: 「clean, X/Y files, ...」エラーなし
# もし「force rewrite?」と聞かれたら y で進む

# 4.2 ファイルシステムを 1.8T に拡張
sudo resize2fs /dev/nvme0n1p2
# 期待出力: 「The filesystem on /dev/nvme0n1p2 is now ... blocks long.」

# 4.3 拡張後の整合性チェック
sudo e2fsck -f /dev/nvme0n1p2
# 期待出力: clean

# 4.4 確認: サイズが 1.8T になっているか
sudo blkid /dev/nvme0n1p2
df -h /dev/nvme0n1p2 2>/dev/null || echo "(まだ未マウントゆえ df は次 phase で)"
```

### Phase 5: chroot で grub-install + fstab 更新

> 同じターミナル内で続行。chroot = 「新しい root の中で操作する」モード。

#### 5-A. マウント準備 (chroot するための下準備)

```bash
# 5-A-1. 新 root を /mnt にマウント
sudo mount /dev/nvme0n1p2 /mnt

# 5-A-2. 新 EFI を /mnt/boot/efi にマウント (boot/efi dir があるはず・clonezilla クローン由来)
sudo mount /dev/nvme0n1p1 /mnt/boot/efi
# もし「No such file or directory」なら: sudo mkdir -p /mnt/boot/efi してからもう一度

# 5-A-3. proc/sys/dev を bind mount (chroot 内で必要)
for f in proc sys dev dev/pts run; do
  sudo mount --bind /$f /mnt/$f
done
```

#### 5-B. UUID 確認 + fstab 書換

```bash
# 5-B-1. 新 EFI と新 root の UUID を取得
sudo blkid /dev/nvme0n1p1
# 出力例: /dev/nvme0n1p1: UUID="ABCD-1234" TYPE="vfat" ...
# → ここの UUID="ABCD-1234" を控える (新 EFI UUID)

sudo blkid /dev/nvme0n1p2
# 出力例: /dev/nvme0n1p2: UUID="99c1fa6d-..." TYPE="ext4" ...
# 🚨 ここで sde4 と同 UUID = UUID重複 (致命的) → 新 UUID 生成必須

# 5-B-2. 🚨 NVMe root UUID 新規生成 (UUID重複対策・必須)
sudo tune2fs -U random /dev/nvme0n1p2
sudo e2fsck -fy /dev/nvme0n1p2
sudo blkid /dev/nvme0n1p2     # 新 root UUID を控える

# 5-B-3. fstab 確認 + 編集 (root と /boot/efi 両方 UUID 書換)
sudo nano /mnt/etc/fstab
# nano 編集モードで:
#   (a) /boot/efi の行: 古い EFI UUID を新 EFI UUID (5-B-1) に書換
#   (b) / (root) の行: 古い root UUID を新 root UUID (5-B-2) に書換
#   Ctrl+O で保存・Enter・Ctrl+X で終了
```

#### 5-C. chroot に入って grub-install

```bash
# 5-C-1. chroot 突入
sudo chroot /mnt /bin/bash

# 5-C-2. (chroot 内) grub-install で 新 EFI に bootloader 書込
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu --recheck /dev/nvme0n1
# 期待出力: 「Installation finished. No error reported.」

# 5-C-3. (chroot 内) grub.cfg 再生成
update-grub
# 期待出力: Linux イメージ + initrd を見つけて grub.cfg 生成

# 5-C-4. (chroot 内) initramfs 再生成 — -k all で全カーネル更新 (live USB chroot 必須)
update-initramfs -u -k all
# 期待出力: update-initramfs: Generating /boot/initrd.img-...

# 5-C-5. (chroot 内) chroot から exit
exit
# 元のプロンプトに戻る
```

#### 5-D. アンマウント (chroot 後始末)

```bash
# 5-D-1. すべてアンマウント
sudo umount -R /mnt
# エラーが出る場合は逆順で:
#   sudo umount /mnt/dev/pts /mnt/dev /mnt/sys /mnt/proc /mnt/run /mnt/boot/efi /mnt
```

### Phase 6: 起動順変更 + 再起動

| # | 操作 |
|---|------|
| 6.1 | live USB 終了 → 再起動 |
| 6.2 | 起動時 F2 / Del で BIOS 設定 |
| 6.3 | Boot Order で **`ubuntu` (NVMe) を最上位**に・旧 sde 起動エントリは下位 or Disabled |
| 6.4 | BIOS 保存して再起動 |
| 6.5 | NVMe Linux 起動確認 |

### Phase 7: 起動後検証

```bash
df /                                  # /dev/nvme0n1p2 と表示されること
df /boot/efi                          # /dev/nvme0n1p1 と表示されること
df -h /                               # サイズが ~1.8T と表示されること (現状 1T → 拡張済)
sudo blkid /dev/nvme0n1p1             # FAT32 EFI
sudo blkid /dev/nvme0n1p2             # ext4 root
sudo blkid /dev/sde4                  # 旧 root: UUIDは旧UUIDのままでOK・復旧保険として温存
                                       # NVMe側 nvme0n1p2 が tune2fs -U random で別UUIDになっているゆえ重複なし
```

### Phase 8: 後片付け

- cron / agent 再開
- 8773 サーバー自動起動確認 (@reboot 30 秒後)
- 旧 sde は物理取り外しせず・写真 sde2 維持・将来別判断

## 復旧手順 (NVMe 起動失敗時)

1. 再起動 → BIOS で **起動順を sde 優先**に戻す
2. 旧 root (sde4) で起動 → 元の状態に復帰
3. NVMe p2 のクローン破損が原因なら clonezilla 再実行
4. grub 設定不整合が原因なら live USB 経由で grub-install 再実行

## 旧 root バックアップ

- `/mnt/backup/multi-agent-shogun/full` (22:20 完了・558G)
- `/mnt/backup` 自体は `sdb2` で sde からも NVMe からも独立アクセス可

## 確定方針 (殿選択)

- **C 案 (完全再構築) 確定** (2026-05-05・「時間かかってもややこしくない」殿命)
- 写真 (sde2 378G) は sde 維持で保持・NVMe 移行で消失なし
- nvme0n1p2 空き 767.5G は当面ノータッチ (本案では p2 領域も含めて全部 root に統合・空き領域なし)
- 旧 sde 物理取り外しは別日

## 参考ファイル

- `mount_snapshot.txt` — 作業前の lsblk / df / fstab スナップショット
- `migration_plan.md` — 本ファイル (C 案完全再構築)

## 進捗

- [ ] cdp 漫画完了待ち
- [ ] エージェント・cron 停止
- [ ] live USB ブート
- [ ] gparted で NVMe 全削除 + 新 EFI 512M + 新 root 1.8T 作成
- [ ] EFI に boot+esp フラグ
- [ ] clonezilla で sde4 → nvme0n1p2 クローン
- [ ] resize2fs で 1.8T 拡張
- [ ] chroot + grub-install + fstab 更新
- [ ] BIOS 起動順 NVMe 優先
- [ ] 通常起動 → NVMe 確認
- [ ] エージェント・cron 再開

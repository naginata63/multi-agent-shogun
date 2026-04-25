---
name: master-telop-two-stage
description: |
  動画MIX (4視点等) でテロップを後加工する標準ワークフロー。master.mp4 (テロップなし) と with_telop.mp4 (drawtext後加工) の二段保存方式。
  テロップミス時に master から再drawtextで取り返し可能。4視点合成の再実行を不要にする。
  「master/telop二段」「動画にテロップ後加工」「マスター動画+テロップ別」「master_telop」「テロップ二段」「master telop」で起動。
  Do NOT use for: 漫画ショート (panels JSONベース→/manga-shortを使え)。Do NOT use for: 表情ショート (別workflow→/expression-short-workflowを使え)。
argument-hint: "[master.mp4_path] [output_dir]"
allowed-tools: Bash, Read
---

# /master-telop-two-stage — master/telop二段生成スキル

## North Star

テロップミス時に4視点合成を再実行する無駄を恒久撲滅し、master.mp4 + with_telop.mp4 二段保存を全動画作成で標準適用する。

## 手順

**全手順の詳細は `shared_context/procedures/master_telop_two_stage.md` を参照せよ。本スキルは同ファイルの薄いwrapperである。重複定義はしない。**

### Step 1: master.mp4 生成

4視点シーン切替MIXの標準手順に従い、**テロップなし(drawtextフィルタを使わない)** で出力する。

```bash
# 各seg独立MIX (テロップdrawtextフィルタを含めない)
ffmpeg -i seg1_synced.mp4 ... -c:v h264_nvenc -preset p4 seg1_master.mp4

# concat結合
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy master.mp4
```

### Step 2: with_telop.mp4 後加工

master.mp4 に drawtext 1passでテロップを重ねる。**過去動画と同一のdrawtextパラメータを使用** (フォーマット参照ルール)。

```bash
ffmpeg -i master.mp4 \
  -vf "drawtext=fontfile=/path/to/font.ttf:text='...':fontsize=36:fontcolor=white:x=w-tw-20:y=20:box=1:boxcolor=black@0.5" \
  -c:v h264_nvenc -preset p4 -c:a copy with_telop.mp4
```

### Step 3: テロップミス時の取り返し

master.mp4 から再drawtextのみ。**4視点合成の再実行は禁止**。

```bash
ffmpeg -i master.mp4 \
  -vf "drawtext=...修正後パラメータ..." \
  -c:v h264_nvenc -preset p4 -c:a copy with_telop_v2.mp4
```

## 重要ルール

1. **ffmpegはh264_nvenc必須** — libx264 (CPU) 禁止 (cmd_761教訓)
2. **master.mp4は最低30日保管** — テロップ修正可能性のため。削除は殿の許可が必要
3. **元素材テロップチェック必須** — 元動画に既存テロップ・ロゴが焼き込まれていないか確認
4. **過去フォーマット参照** — 最新のアップ済 with_telop 動画から drawtext パラメータを抽出し統一
5. **命名規則**: `{day}_master.mp4`, `{day}_with_telop.mp4`, `{day}_with_telop_v2.mp4`

## 参照

- 詳細手順: `shared_context/procedures/master_telop_two_stage.md`
- 過去資産: `projects/dozle_kirinuki/work/20260415_*/multi/day5_zephyrus_with_telop.mp4`

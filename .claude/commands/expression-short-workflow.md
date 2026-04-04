---
name: expression-short-workflow
description: |
  表情ショート（ゲーム画面+立ち絵+セリフ表示）の制作ワークフロー。
  区間選定→セリフ表確定→構成JSON確定→レンダリング→公開の5段階。
  「表情ショート制作」「S1ショート」「/expression-short-workflow」で起動。
argument-hint: "[video_id] [start_time] [end_time]"
allowed-tools: Bash, Read, Edit, Write
---

# /expression-short-workflow — 表情ショート制作ワークフロー

## North Star

ゲーム画面+立ち絵（表情切替）+セリフ表示のショート動画を、最少リテイクで制作する。

## 全体フロー

```
Phase 1: 区間選定 ──→ 殿OK
Phase 2: セリフ表作成 → 殿OK（確定するまでPhase 3に進むな）
Phase 3: 構成JSON確定 → 殿OK
Phase 4: レンダリング → 殿確認
Phase 5: 公開 ────→ 完了
```

**鉄則: セリフ表を確定してからJSONを作る。JSONを確定してからレンダリング。戻りを最小化。**

---

## Phase 1: 区間選定

1. 元動画のSTT（話者ラベル付き）で分ごとの話者分布を確認
2. 殿が区間を選ぶ（例: 3:48-4:53）
3. 選んだ区間のメインスピーカーとアクセントカラーを決定

**アウトプット**: 区間（開始-終了）+ メインスピーカー

---

## Phase 2: セリフ表作成

1. 選んだ区間のSTT + YouTube字幕を並べて殿に提示
2. 殿がセリフを編集:
   - 話者修正（STTの話者ラベルは参考。殿が正しい）
   - 不要セリフ削除
   - セリフ追加・分割・改行
   - 表示タイミング調整
3. **セリフ表を完全に確定してからPhase 3に進む**
4. 小出し修正しない。殿の指摘をまとめてから反映

**アウトプット**: 確定セリフ一覧（#, 秒数, 話者, セリフ）

---

## Phase 3: 構成JSON確定

確定セリフ表から input-props JSON を1回で作成:

```json
{
  "videoPath": "clip_1080p.mp4",
  "durationInFrames": 1959,
  "hookText": "フックテキスト",
  "hookDurationSec": 999,
  "mainSpeaker": "orafu",
  "accentColor": "#54C3F1",
  "subtitles": [
    {"text": "セリフ", "startSec": 1.6, "endSec": 4.6, "speaker": "qnly"}
  ],
  "tachieSlots": [
    {"path": "qnly_surprise_r1_bust_rgba.png", "side": "left", "startSec": 0, "endSec": 6.6},
    {"path": "orafu_surprise_r2_bust_rgba.png", "side": "right", "startSec": 0, "endSec": 65.3}
  ]
}
```

立ち絵ルール:
- 左側: セリフの話者に切替。メインスピーカーが喋ってる時は直前の立ち絵を維持
- 右側: メインスピーカー固定。場面に応じて表情切替
- 表情は expression/ と selected/bust/ から選択

**殿に構成表（セリフ+表情セット）を提示して最終確認。OKが出てからPhase 4。**

**アウトプット**: input-props-vN.json

---

## Phase 4: レンダリング

1. 元動画から1080pクリップ切り出し（ffmpeg -c:v copy）
   - 360p禁止。必ず1080p
2. Remotionレンダリング（**必ず.mp4出力。.mov禁止**）
   ```bash
   npx remotion render remotion.ts ShortsOverlay out/overlay.mp4 --props=input-props-vN.json
   ```
3. ffmpeg h264_nvencで音声合成
   ```bash
   ffmpeg -i out/overlay.mp4 -i public/clip_1080p.mp4 -map 0:v -map 1:a -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k -shortest out/final.mp4
   ```
4. YouTube非公開アップ
5. 殿確認 → 修正があればJSONだけ変えて再レンダリング

**アウトプット**: 最終動画 + YouTube URL

---

## Phase 5: 公開

1. タイトル設定
2. 説明欄設定（元動画リンク+ハッシュタグ）
3. CTAコメント投稿（`youtube_uploader.py comment VIDEO_ID`、公開後のみ）
4. ダッシュボード更新

---

## Remotion技術メモ

### 現在の構成
- remotion-overlay/ にプロジェクト一式
- ShortsComposition.tsx: メインコンポーネント
- GameScreen.tsx: ゲーム画面（y=420, h=850）。**muted必須**（音声二重防止）
- HookTelop.tsx: フック（y=240）。hookDurationSec=999で常時表示
- SubtitleTrack.tsx: セリフ（ゲーム画面下端オーバーレイ）
  - whiteSpace: pre-line で \n 改行対応済み
  - maxWidth: 1050
- MultiTachieOverlay.tsx: 時間帯別立ち絵切替
- SubHookTelop.tsx: サブフック（現在非表示）

### 既知の問題
- **Remotion内蔵ffmpegはlibx264(CPU)**。nvenc未対応。→ 最終エンコードは自前ffmpeg h264_nvencで
- **.mov出力はProRes無圧縮で1.4GB**。必ず.mp4で出力
- **nvenc対応調査が未完了**。対応できればメモリ問題は大幅改善する見込み

### 追加機能でのスクリプト修正
- 新しいReactコンポーネント追加等はOK
- ただし**セリフ・立ち絵・タイミング等のデータはJSON外出し**。スクリプト内にハードコードするな

---

## アンチパターン

| NG | 理由 | 正しくは |
|----|------|---------|
| セリフ確定前にレンダリング | リテイク地獄 | Phase 2完了まで進むな |
| 修正を小出しに送る | 足軽のコンテキスト溢れ | まとめて1回で |
| .mov出力 | 1.4GB | .mp4で出力 |
| 360pクリップ | 低画質 | 1080pで切り出し |
| GameScreen muted忘れ | 音声二重 | muted必須 |
| データをスクリプトにハードコード | 修正のたびにスクリプト変更 | JSON外出し |

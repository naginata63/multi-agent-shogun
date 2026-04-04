---
name: manga-short-workflow
description: |
  漫画ショート制作の全体ワークフロー。候補選定→時間選定→クリップ化→漫画作成→合成の5段階。
  各段階で殿の確認を挟む。既存スキル（/collective-select, /manga-short）を活用する。
  「漫画ショートワークフロー」「漫画制作フロー」「/manga-short-workflow」で起動。
argument-hint: "[video_id]"
allowed-tools: Bash, Read, Edit, Write
---

# /manga-short-workflow — 漫画ショート制作ワークフロー

## North Star

候補選定から完成動画まで、既存スキルを活用して最短・最少リテイクで漫画ショートを制作する。

## 全体フロー

```
Phase 1: 候補選定 ──→ 殿OK
Phase 2: 時間選定 ──→ 殿OK
Phase 3: クリップ化 ─→ 殿OK
Phase 4: 漫画作成 ──→ 殿OK
Phase 5: 合成+公開 ─→ 完了
```

**鉄則: 各Phaseで殿OKを取ってから次に進む。戻りを最小化する。**

---

## Phase 1: 候補選定

**使うスキル**: `/collective-select`

1. 素材準備（STT+字幕+コメント）
2. 集合知5人分析（Claude3+GPT1+Gemini1）
3. 結果をダッシュボードに掲載
4. **殿が選ぶ** → どのシーンを漫画ショートにするか決定

**アウトプット**: シーン名+大まかな時間範囲

---

## Phase 2: 時間選定

1. 選定シーンのSRT（話者ラベル付き）を詳細表示
2. YouTube字幕も参照して自然な日本語のセリフを確認
3. 殿と構成表（composition.md）を作成:
   - パネル数・各パネルの時間・話者・セリフ・演出
   - director_notes（場面の文脈・感情）
   - キャラ感情の流れ
4. **殿OK** → composition.md確定

**アウトプット**: composition.md（確定版）

**注意**:
- 構成表は殿との対話で作る。将軍が勝手に決めない
- セリフの話者は殿が知っている。STTの話者ラベルは参考程度
- 時間はショート内秒数（0:00開始）で表記

---

## Phase 3: クリップ化

1. composition.mdの時間に基づいてffmpegで元動画からクリップ切り出し
2. SE（鳩時計等）がある場合はassets/bgm/sfx/から取得
3. 全クリップを結合してpreview.mp4を作成
4. YouTube非公開アップ
5. **殿が確認** → 時間調整があればクリップ再切り出し

**アウトプット**: peterpan_clips/p1.mp4〜pN.mp4 + preview.mp4

**注意**:
- SEのURLを推測するな。WebFetchで確認してからDL
- クリップのコーデックを統一（全部同じcodecでないとconcat時に音声が壊れる）

---

## Phase 4: 漫画作成

**使うスキル**: `/manga-short`

1. composition.mdからpanels JSONを作成:
   - meta: video_id, short_title, estimated_duration_sec
   - panels: id, title, speaker, line, characters, start_sec, duration_sec, scene_desc, director_notes, situation
2. 背景リファレンス画像があれば殿から受け取る
3. `/manga-short` でPNG生成

**アウトプット**: panel_01.png〜panel_NN.png

**鉄則**:
- **新しいスクリプトを作るな**。`generate_manga_short.py` + panels JSONで動かす
- 修正はpanels JSONだけ変える
- キャラリファレンス画像（selected/{member}.png）を必ずGeminiに渡す
- member_profiles.yamlのappearanceを参照（ゴーグル/サングラス/メガネ区別）
- スマホフレーム禁止
- 背景リファレンスがあれば毎パネル渡す
- composition.mdが唯一の入力。足軽が勝手にscene_descを変えるな

---

## Phase 5: 合成+公開

1. 各パネル: PNG（静止画映像）+ クリップ（音声）→ ffmpegで合成
   ```bash
   ffmpeg -loop 1 -i panel.png -i clip.mp4 -map 0:v -map 1:a -c:v h264_nvenc -preset p4 -pix_fmt yuv420p -shortest -y panel_video.mp4
   ```
2. 全panel_video.mp4をconcat
3. YouTube非公開アップ
4. **殿確認** → OKなら説明欄+CTAコメント設定→公開

**アウトプット**: 最終動画 + YouTube URL

**注意**:
- ffmpegは必ずh264_nvenc（GPU）。libx264禁止
- Remotionは使わない（メモリ8GB消費+libx264問題）
- .mov禁止。必ず.mp4

---

## アンチパターン（やってはいけないこと）

| NG | 理由 | 正しくは |
|----|------|---------|
| 修正のたびに新スクリプト作成 | 14本乱立して管理不能 | panels JSONだけ修正 |
| 既存スキルを使わない | 車輪の再発明 | /manga-short を使う |
| 修正を小出しに送る | 足軽のコンテキスト溢れ | まとめて1回で送る |
| テキストだけでキャラ説明 | 外見が一致しない | リファレンス画像を渡す |
| composition.mdなしで開始 | 構成がブレる | 殿と構成表を先に確定 |
| SEのURLを推測 | 間違ったSEがDLされる | WebFetchで確認 |

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
Phase 2: 時間選定 ──→ 【clip_editor_server】で殿が頭尻を詰める → 書き出し
Phase 3: クリップ化 ─→ 殿OK
Phase 4: 漫画作成 ──→ 殿OK (誤植は【serif-fix】)
Phase 5: 合成+公開 ─→ 【panel_sync_editor】でコマ送り時刻を殿が調整 → 完了
```

**鉄則: 各Phaseで殿OKを取ってから次に進む。戻りを最小化する。**

## 🖥 殿が直接触る編集アプリ（必ずこれを使え・手作業で決め打つな）

| アプリ | いつ | 起動 | 何ができる |
|--------|------|------|-----------|
| **clip_editor_server.py** | Phase 2-3 | `python3 scripts/clip_editor_server.py --project <名> --port 810X` | 元動画から**カットの頭尻を±0.1秒で詰める**・その場試聴・書き出し(NVENC)。設定は `work/editor/<名>.json` |
| **panel_sync_editor.py** | Phase 5 | `python3 scripts/panel_sync_editor.py --port 8096 [--segs --panels --audio]` | 音を聞きながら**コマ送り時刻**を調整→segs.json書き戻し→再ビルド |
| **/serif-fix** (skill) | Phase 4後 | スキル起動 | 吹き出し内**セリフの誤植差し替え**(flood fill→serif_replace→QCループ) |

### clip_editor_server の要点
- **`yt_mode: true` を設定JSONに入れる** → YouTube iframe再生になり端末が重い元動画を読まない（**入れ忘れると「再生できない」と言われる**・2026-08-26事故）
- 設定JSON: `{"src":..., "outdir":..., "yt_mode":true, "cuts":[{"id","lo","hi","desc","on","yt":"<video_id>"}]}`
- 殿が書き出すと `outdir/<project>_edit.mp4` ができる。**この書き出し結果がPhase 3の入力**（AIが時間を決め直すな）

---

## Phase 1: 候補選定

**使うスキル**: `/collective-select`

1. 素材準備（STT+字幕+コメント）
2. 集合知5人分析（Claude系+GPT系。**Geminiは使うな**=脱Gemini 2026-08-22殿。ローカルLLM/Claude/codexで代替）
3. 結果をダッシュボードに掲載
4. **殿が選ぶ** → どのシーンを漫画ショートにするか決定

**アウトプット**: シーン名+大まかな時間範囲

---

## Phase 2: 時間選定

0. **時間の確定は `clip_editor_server` で殿が行う**（AIが秒を決め打つな）。初期カットだけ置いてURLをntfyで送り、殿が頭尻を詰めて書き出す
1. **セリフ表は「編集後の成果物」のSTT語境界から機械生成**: `qwen_stt.py`（Qwen3-ASR語単位）+ `speaker_id.py`（ECAPA・Demucs分離後の`vocals_full.wav`に対して・`venv/bin/python`で実行）。手書き転記も**元動画時刻からの引き算も禁止**
   - **カット構成JSON(`work/editor/<project>.json`)のcuts順序を必ず読め** — 殿はオチの断片を先頭に置くループ構成を使う（JSON順=結合順）。読まずに作ると全行ズレ+冒頭欠落（2026-08-26事故）
   - STTの誤変換を捨てる前にその時刻を実クリップで確認（誤変換は"存在の証拠"）。表の1行目と最終行は実クリップと突き合わせてから殿に出す
2. **画面の焼き込みテロップと必ず擦り合わせよ（最優先の一次ソース・2026-08-26殿指摘）**
   - 本家が付けたテロップは**セリフが正確**なうえ、**話者カラー帯＋アイコンで話者まで判る**（ドズル#C80000/ぼん#733C93/おんりー#FCC700/おらふ#54C3F1/MEN#EB6D9A/ネコおじ#787878・`context/telop_style_guide.md`）
   - 手順: `ffmpeg -vf "fps=2,crop=1920:200:0:800"` でテロップ帯を全区間スキャン → 帯が出ているコマをローカルVLM(Qwen2.5-VL)か目視で読む → **STT語句・ECAPA話者判定より画面テロップを優先**して確定
   - 実例: ECAPAが unknown だった「おらふのおっちゃん！」は、テロップのピンク帯＋アイコンで **おおはらMEN** と即断できた
3. YouTube字幕は**粗い当たり付け専用**（STT誤変換の実例: 弓矢→「有明」/30本→「三十歩」）
4. **優先順位: 画面テロップ > STT語境界(時刻) > ECAPA話者判定 > YouTube字幕**
2.5. **シーン(場面)は必ず実フレームを見て書け・セリフからの類推禁止（2026-08-26殿指摘）**
   - 各パネル代表時刻のフレームを `ffmpeg -ss <t> -frames:v 1` で抜き、**何が映っているかを自分の目で確認**してから scene_desc を書く
   - 確認項目: ①左上バッジ=**誰のPOVか** ②**キャラが画面に映っているか**（多くの回はゲーム画面のみでキャラは映らない） ③地形・時間帯・特徴物 ④焼き込みテロップ
   - 事故例: 実映像は全編おらふくんPOVのネザー岩肌だったのに、セリフから「装備を出し合う2人」「駆け寄る2人」と憶測で書いた
   - **元ネタ・小ネタは殿に聞け**（例: 「声もださずに」=カイジ鉄骨渡りの石田のおっちゃん）。パロディを外すと笑いが死ぬ
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
- **生成は codex CLI 一本**（Gemini/Vertex禁止・2026-08-08殿）。実行前に `unset OPENAI_API_KEY`
- キャラの**三面図**（`assets/dozle_jp/character/3views/{member}_3views.png`）を必ずrefに渡す。外見はプロンプトに書くな（三面図に全面委任）
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
3. **コマ送りのズレは `panel_sync_editor.py` で殿が調整** → segs.json書き戻し → 再ビルド（ffmpeg組み直しを待たずに合わせられる）
4. YouTube非公開アップ
5. **殿確認** → OKなら説明欄+CTAコメント設定→公開

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
| **編集アプリを使わずAIが秒を決める** | 殿の感覚とズレて何度も戻る | clip_editor(頭尻)・panel_sync_editor(コマ送り)を起動して殿に渡す |
| clip_editorで`yt_mode`未設定 | 端末が1GB超の動画を読めず「再生できない」 | 設定JSONに`yt_mode:true`+各cutに`yt`(video_id) |

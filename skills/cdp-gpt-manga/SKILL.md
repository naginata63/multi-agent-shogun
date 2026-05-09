---
name: cdp-gpt-manga
description: |
  ドズル社漫画ショート用 CDP ChatGPT 画像生成ワークフロー。
  構造化 panels JSON → simple array 変換 → cdp_chatgpt_image_poc.py 起動 を一貫実行。
  3面図のみ参照・自然言語で表情指示・背景描写は director_notes 内で文字描写。
  「CDP GPT 漫画」「漫画 CDP GPT」「panels GPT 生成」「ChatGPT で漫画」「/cdp-gpt-manga」で起動。
  Do NOT use for: Gemini 経由の漫画生成 (それは /cdp-manga-gen を使え)。
  Do NOT use for: 漫画 panels JSON 自体の作成 (それは別タスク・本スキルは生成のみ)。
---

# CDP ChatGPT 漫画パネル生成スキル

## 用途

構造化 panels JSON (manga_short workflow 形式・`{meta, panels[...]}`) を入力に、
CDP 経由で ChatGPT WebUI を操作して漫画パネル画像を生成する。

## 前提条件

- Chrome ログイン済 (chatgpt.com)
- DISPLAY=:0 (X11)
- panels JSON は **構造化形式** (manga_composition_knowledge.md 準拠):
  - `meta.common_rules` / `meta.character_positions`
  - `panels[].id` / `characters` / `lines` / `shot_type` / `is_climax` / `scene_desc` / `situation` / `director_notes` / `ref_images`
- ref_images は **3面図 (`*_3views.png`) と komawari template のみ** (殿命 2026-05-09)
- 表情は **director_notes 内の自然言語**で記述 (smile_r1 等のコード使用禁止)
- 背景は director_notes 内に **文字で具体描写** (bg_*.png ref 不要・ただし共通ルールで全 panel 統一せよ)

## ワークフロー (2 ステップ)

### Step 1: 構造化 → CDP simple array 変換

```bash
python3 projects/dozle_kirinuki/scripts/panels_to_cdp_simple.py \
  <input_structured.json> [output_cdp.json]
```

- 出力省略時: `<input dir>/panels_chatgpt_cdp_<basename>.json`
- 変換内容: 添付説明 + scene_desc + situation + director_notes + セリフ + 共通ルール の連結
- selected sprite 自動追加なし (殿命「3面図のみ」遵守)

### Step 2: CDP ChatGPT で生成

```bash
cd projects/dozle_kirinuki
python3 scripts/cdp_chatgpt_image_poc.py \
  --panels-json <output_cdp.json> \
  --out work/<work_dir>/output/cdp_gpt
```

- 推定時間: 1 panel あたり ~60秒・6 panel で ~6分
- 出力: `<out>/chatgpt_<timestamp>_<panel_id>_00.png` (各 panel)
- 1 セッション内で連続生成 (state.json で resume 可)

## panels JSON 必須要素 (作成時の自己チェック)

manga_composition_knowledge.md の Section 7 チェックリスト準拠:

| 項目 | 確認ポイント |
|---|---|
| director_notes | 自然言語の表情描写・ポーズ具体・禁止事項・背景描写・セリフ配置 |
| 配置一貫性 | character_positions で全 panel 同位置維持 |
| バストアップ | 全身禁止 (framing 明記) |
| 2コマ比率 | 20-40% 推奨 (S2/D1/T2 等の komawari template 利用) |
| 感情アーク | 段階変化 (同表情 3 連続禁止) |
| climax | 1 作品で 1-2 回 |
| ref_images | 3 面図 + 必要なら komawari template のみ |

## 実例 (cmd 1085 / 0504 声真似MOB)

入力: `work/20260504_声真似したMOBを持ってこい！【マイクラ】/panels_manga_koemane.json`

```bash
python3 projects/dozle_kirinuki/scripts/panels_to_cdp_simple.py \
  work/20260504_声真似したMOBを持ってこい！【マイクラ】/panels_manga_koemane.json
# → panels_chatgpt_cdp_koemane.json 自動生成

python3 projects/dozle_kirinuki/scripts/cdp_chatgpt_image_poc.py \
  --panels-json work/20260504_声真似したMOBを持ってこい！【マイクラ】/panels_chatgpt_cdp_koemane.json \
  --out work/20260504_声真似したMOBを持ってこい！【マイクラ】/output/cdp_gpt
```

## 関連スキル

- `/cdp-manga-gen` (Gemini 経由・selected sprite 利用): cdp_manga_panel.py 経由・**3面図 only ルール適用前**
- `/manga-short` (動画化まで一貫): panels JSON 作成→画像→動画
- `/manga-short-workflow` (殿の確認をはさむ全体ワークフロー)

## 禁止事項

- ❌ ref_images に selected sprite (smile_r1.png 等) を入れる (殿命「3面図のみ」)
- ❌ director_notes に表情コード (smug_r2 等) を生で書く (自然言語で具体描写せよ)
- ❌ panels_to_cdp_simple.py を経由せず構造化 JSON を直接 cdp_chatgpt_image_poc.py に渡す (mismatch で動かぬ)
- ❌ 背景指示なしで生成 (panel が浮く・必ず director_notes 内に文字描写)
- ❌ 1 panel ずつ別セッションで生成 (一貫性低下・1 セッション連続生成が正)

## トラブルシュート

| 症状 | 原因/対処 |
|---|---|
| `len(panels)` エラー | 構造化 JSON を直接渡している → Step 1 変換必須 |
| 30分以上応答なし | Chrome ログイン切れ → 手動ログイン後 `--resume <state.json>` |
| キャラ顔が違う | ref_images に対象キャラの 3views 入っているか確認 |
| 背景が違う | director_notes / common_rules で背景描写明記 |
| セリフ位置が UI 被り | director_notes でセリフ配置を「中央〜上部 70%」明記 |

# panel_review.html 作成手順（cmd_1350）

## 作業ディレクトリ
/home/murakami/multi-agent-shogun

## 成果物一覧
1. `projects/dozle_kirinuki/scripts/panel_review_gen.py` — HTMLジェネレータ（新規）
2. `projects/dozle_kirinuki/scripts/generate_panel_candidates.py` — 中間JSON出力追加（改修）
3. `scripts/dashboard/server.py` — `/api/load_raw_candidates` エンドポイント追加（必要な場合）

---

## Step1: generate_panel_candidates.py 改修

Gemini構成表テキストのパース結果を `panels_odai_XX_raw.json` として保存する機能を追加。

### 中間JSONフォーマット
```json
{
  "scene": "odai_04_hayakunenasai",
  "title": "タイトル",
  "rows": [
    {"id": 1, "timestamp": "0:01", "speaker": "oo_men", "text": "早く寝なさい！"},
    {"id": 2, "timestamp": "0:05", "speaker": "dozle", "text": "はーい"}
  ]
}
```

### 保存場所
`--output` に指定したJSONと同ディレクトリに `panels_odai_XX_raw.json` として保存（`_raw.json` サフィックスで区別）。

---

## Step2: panel_review_gen.py 作成

### 使い方
```bash
python3 projects/dozle_kirinuki/scripts/panel_review_gen.py <raw_json_path>
```
→ 同ディレクトリに `panel_review.html` を出力

### HTMLの構造
- 1行 = [≡ドラッグハンドル] [タイムスタンプ(非編集)] [話者ドロップダウン] [セリフテキスト] [＋] [−]
- 下部: [＋行を追加] ボタン
- 最下部: [JSON生成（panels_check用）] ボタン + 保存先パス表示

### 話者ドロップダウンの選択肢
`dozle`, `bon`, `qnly`, `orafu`, `oo_men`, `nekooji`, `不明`

### ドラッグ&ドロップ（ライブラリ不要）
- HTML5 Drag and Drop API をベースに実装
- スマホタッチ対応: `touchstart` / `touchmove` / `touchend` イベントで同等機能を実装
- ≡ハンドル部分をドラッグ開始点とする

### JSON生成ロジック（panels JSON変換）
ボタン押下時に以下のルールで panels JSON を生成:
- 連続する同一話者の行 → 1パネルにまとめる（serifを結合）
- 2人交互の掛け合い行 → shot_type: T2_B（2コマ）
- 単独発言 → shot_type: S2
- 表情コード自動推定:
  - セリフに「！」「怒」「ダメ」→ angry_r2
  - 「？」「え」「驚」→ surprise_r2
  - それ以外 → smile_r1
- director_notes: 空文字("")でOK
- ref_images: `assets/dozle_jp/character/selected/{character}_{expr}_rgba.png`
- common_rules: 固定テンプレート（panels_check_gen.pyのCOMMON_RULES定数を流用）

### POST /api/save_panels_json
panels JSON の保存は既存エンドポイントをそのまま利用。
`server.py` に `/api/load_raw_candidates?path=...` も追加:
- 指定パスの `_raw.json` を読み込んで返す（プロジェクト外は403）

---

## テスト手順
1. `generate_panel_candidates.py` で `_raw.json` が生成されることを確認（dry-run可）
2. `panel_review_gen.py` を `_raw.json` で実行 → `panel_review.html` が生成されること
3. `python3 -c "import ast; ast.parse(open('panel_review.html').read())"` は不要。HTMLなので構文確認は `grep -c '<html>' panel_review.html` で存在確認のみでOK
4. git commit & push

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽1号、subtask_1350a完了。panel_review.html+generate_panel_candidates.py改修報告。" \
  report_completed ashigaru1
```

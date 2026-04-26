# パネル生成パイプライン修正手順（cmd_1353）

## 修正1: panel_review_gen.py — ボタン名変更

`panel_review_gen.py` 内の「JSON生成」ボタンのラベルを「パネル候補生成」に変更。
（HTML文字列内の該当箇所を検索して置換）

## 修正2: generate_panel_candidates.py — _raw.json自動出力追加

### 出力ファイル追加
panels JSON（`panels_odai_XX.json`）と同じディレクトリに `panels_odai_XX_raw.json` を自動出力。

### _raw.json生成ロジック
`gemini_raw_odai_XX.txt`（既存の Gemini 生テキスト出力）から 🗣️ 行を抽出してパース:

**パターン1**: `[MM:SS] 🗣️ 話者名: 「セリフ」`
**パターン2**: `[MM:SS] 🗣️ 話者名: セリフ`（「」なし）

話者名→キー変換:
- ドズル→dozle, ぼんじゅうる→bon, おんりー→qnly, おらふくん→orafu
- おおはらMEN→oo_men, ネコおじ→nekooji
- それ以外/複数→不明

### _raw.json フォーマット（panel_review_gen.py 互換）
```json
{
  "rows": [
    {"id": 1, "timestamp": "0:05", "speaker": "dozle", "text": "セリフ内容"},
    ...
  ]
}
```

### 実装箇所
- `generate_panel_candidates.py` に `parse_raw_to_rows(raw_text)` 関数を追加
- panels JSON 保存直後に `_raw.json` を同ディレクトリに保存

## テスト
1. dry-run で `_raw.json` が出力されることを確認（`--dry-run` オプション使用）
2. `panel_review_gen.py` 実行後の HTML 内に「パネル候補生成」が含まれること: `grep -c 'パネル候補生成' panel_review.html`
3. git commit & push

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽1号、subtask_1353a完了。ボタン名変更+_raw.json自動出力追加報告。" \
  report_completed ashigaru1
```

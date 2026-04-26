# panel_review.html ファイル選択UI追加手順（cmd_1351）

## 対象ファイル
- `projects/dozle_kirinuki/scripts/panel_review_gen.py`
- `scripts/dashboard/server.py`（既存 `/api/list_panels_json` を流用）

## 作業前確認
1. `panel_review_gen.py` を Read し、現在の HTML 生成構造（ページ上部、JS初期化部分）を確認する
2. `server.py` の `/api/list_panels_json` の返却フォーマットを確認する（再利用できるか）

## 実装仕様

### ファイル選択ドロップダウン（ページ最上部）
- ページ上部に「ファイルを選択」セレクト + [読み込み] ボタンを配置
- `fetch('/api/list_panels_json')` でファイル一覧を取得（`_raw.json` と通常 `panels_*.json` を両方含む）
- スマホ対応: `min-height: 44px`、フォントサイズ `1rem` 以上

### ファイル読み込みフロー
1. ドロップダウンでファイルを選択 → [読み込み] ボタン押下
2. `fetch('/api/load_raw_candidates?path=...')` でJSONを取得
3. ファイルフォーマット自動判定:
   - `rows` フィールドがある → そのまま使用（_raw.json形式）
   - `panels` フィールドがある → 下記変換ロジックで rows 形式に変換（panels_*.json形式）
4. rows データで画面を再描画（既存の `renderRows()` 等を呼び出す）
5. 保存先パスも読み込んだファイルパスに連動更新

### panels JSON → rows 変換ロジック（JS内）
```javascript
function panelsToRows(panels) {
  const rows = [];
  panels.forEach((panel, idx) => {
    const speaker = panel.characters ? panel.characters[0] : '不明';
    const text = panel.lines ? panel.lines.join(' ') : '';
    const timestamp = panel.start_sec ? formatSec(panel.start_sec) : '';
    rows.push({ id: idx + 1, timestamp, speaker, text });
  });
  return rows;
}
```

### /api/list_panels_json の拡張（必要な場合）
- 既存エンドポイントが `_raw.json` を含めない場合は `server.py` 側で `_raw.json` も列挙するよう修正
- または新エンドポイント `/api/list_all_jsons` を追加（`panels_*.json` + `*_raw.json` を両方返す）

## テスト
1. `panel_review_gen.py` を既存 `_raw.json` で実行 → HTML生成確認
2. HTML内にファイル選択ドロップダウンが含まれることを `grep -c 'list_panels_json' panel_review.html` で確認
3. git commit & push

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽1号、subtask_1351a完了。panel_review.htmlファイル選択UI追加報告。" \
  report_completed ashigaru1
```

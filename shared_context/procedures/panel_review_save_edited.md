# panel_review.html 保存ボタン追加手順（cmd_1356）

## 対象ファイル
- `projects/dozle_kirinuki/scripts/panel_review_gen.py`
- `scripts/dashboard/server.py`（`/api/list_panels_json` の _edited.json 対応）

## 修正1: panel_review_gen.py — 保存ボタン追加

### ボタン配置
ページ上部のファイル選択UIの隣に「💾 保存」ボタンを追加。

### 保存処理（JS）
```javascript
async function saveEdited() {
  const rows = getCurrentRows();
  const savePath = SAVE_PATH.replace(/_raw\.json$/, '_edited.json')
                             .replace(/panels_([^/]+)\.json$/, 'panels_$1_edited.json');
  // _edited.json のパスを生成
  const response = await fetch('/api/save_panels_json', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path: savePath, data: {rows}})
  });
  const result = await response.json();
  if (result.status === 'ok') showStatus('💾 保存完了: ' + savePath);
}
```

保存先パス生成ルール:
- `panels_odai_05_raw.json` → `panels_odai_05_edited.json`
- `panels_odai_05.json` → `panels_odai_05_edited.json`

### SAVE_PATH 変数
`panel_review_gen.py` が HTML 生成時に `SAVE_PATH` JS変数を埋め込む（既存実装を流用）。

## 修正2: panel_review_gen.py — 読み込み優先順の変更

`/api/list_panels_json` で取得したファイル一覧の表示優先順:
**_edited.json > _raw.json > panels.json**

具体的には `/api/list_panels_json` のファイル一覧ドロップダウンで `_edited.json` を先頭に表示するか、
または画面初期読み込み時に `_edited.json` が存在すれば自動読み込みするロジックを追加。

## 修正3: server.py — /api/list_panels_json に _edited.json 追加

既存の `/api/list_panels_json` エンドポイントが `_edited.json` も列挙するよう確認・修正。
（すでに `_raw.json` を含めるよう改修済みなら `_edited.json` も同様に含まれるはず）

## テスト
1. `grep -c '保存\|saveEdited\|_edited' panel_review.html` で実装確認
2. git commit & push

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽1号、subtask_1356a完了。panel_review.html保存ボタン追加報告。" \
  report_completed ashigaru1
```

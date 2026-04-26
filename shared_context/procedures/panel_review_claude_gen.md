# panel_review.html Claude Opus 4.6 パネル候補生成組み込み手順（cmd_1354）

## 対象ファイル
- `scripts/dashboard/server.py` — `/api/generate_panels_llm` エンドポイント追加
- `projects/dozle_kirinuki/scripts/panel_review_gen.py` — ボタン押下時のAPI呼び出し追加

## 作業前確認
1. `projects/dozle_kirinuki/context/panel_candidate_prompt.txt` を Read し、プロンプト全文・表情コードテーブル・director_notes書き方を把握
2. `assets/dozle_jp/character/selected/` のファイル一覧を取得（表情コード存在チェック用）
3. `server.py` の既存APIエンドポイント構造を確認

---

## Step1: server.py に POST /api/generate_panels_llm 追加

### リクエストボディ (JSON)
```json
{
  "rows": [{"speaker": "dozle", "text": "セリフ", "timestamp": "0:05"}, ...],
  "gemini_context": "【シーン一覧】...",
  "scene_name": "odai_04_hayakunenasai",
  "title": "早く寝なさい！",
  "save_path": "work/.../panels_odai_04.json"
}
```

### 処理フロー
1. `assets/dozle_jp/character/selected/` をスキャンして利用可能な表情ファイル一覧を取得
2. `panel_candidate_prompt.txt` を読み込む
3. 以下のプロンプトを組み立てる（下記参照）
4. Claude CLI を subprocess で呼び出す:
   ```python
   result = subprocess.run(
       ["/home/murakami/.local/bin/claude", "-p", prompt, "--model", "claude-opus-4-6"],
       capture_output=True, text=True, timeout=120
   )
   ```
5. 出力から JSON を抽出（```json ... ``` ブロックを優先、なければ全体をパース試行）
6. ref_images の存在チェック → 存在しないものはフォールバック適用
7. 結果を `save_path` に保存
8. `{"status": "ok", "panels": [...]}` を返却

### Claudeに渡すプロンプト
```
あなたはドズル社漫画ショートの構成作家です。
以下の書き起こし（殿レビュー済み）とシーン情報から、漫画パネルのJSONを生成してください。

## 書き起こし（話者+セリフ）
{rows を "MM:SS 話者: セリフ" 形式でテキスト化}

## シーン情報（Gemini動画解析）
{gemini_context}

## タイトル・シーン名
タイトル: {title}
シーン: {scene_name}

## 出力形式（必須）
panels JSONフォーマットで出力。```json で囲むこと。

{panel_candidate_prompt.txt の後半（パネルJSONスキーマ・director_notes・shot_typeルール・表情コードテーブル部分）}

## 使用可能な表情ファイル
以下のファイルのみ使用可（存在しないファイルは絶対に使わないこと）:
{ファイルリストを改行区切りで列挙}

## 共通ルール
全キャラクターの身長はだいたい同じくらいに描くこと。
【最重要】おおはらMENは必ずゴーグルを目を覆うように装着して描け。
ぼんじゅうるはサングラス必須。おんりーは丸メガネ必須。
デフォルメ・SD・ちびキャラ禁止。武器・盾・バケツ禁止。
```

### 表情フォールバックテーブル
存在チェックで失敗した場合:
- `{char}_smile_r1_rgba.png` が存在すればそれを使用
- それも存在しなければ `ref_images: []` に設定

---

## Step2: panel_review_gen.py 修正

「パネル候補生成」ボタン押下時のJS処理を変更:

```javascript
async function generatePanelCandidates() {
  const rows = getCurrentRows();  // 現在のrows取得
  const geminiContext = '...';    // ページ読み込み時にサーバーから取得または変数に持つ
  const response = await fetch('/api/generate_panels_llm', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({rows, gemini_context: geminiContext, scene_name: SCENE_NAME, title: TITLE, save_path: SAVE_PATH})
  });
  const result = await response.json();
  if (result.status === 'ok') {
    alert('パネル候補生成完了！panels_check.htmlで確認してください。');
  }
}
```

gemini_context の取得方法:
- `save_path` のディレクトリにある `gemini_raw_*.txt` を `/api/load_raw_candidates` 等で取得
- または panel_review_gen.py 生成時に `GEMINI_CONTEXT` JS変数として埋め込む（推奨）

---

## テスト
1. dry-run: server.py に新エンドポイントが追加されているか確認（`grep -c 'generate_panels_llm' scripts/dashboard/server.py`）
2. Claude CLI の実行確認: `which claude` でパスが `/home/murakami/.local/bin/claude` であること
3. git commit & push

## 報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo \
  "足軽1号、subtask_1354a完了。Claude Opus 4.6パネル候補生成API組み込み報告。" \
  report_completed ashigaru1
```

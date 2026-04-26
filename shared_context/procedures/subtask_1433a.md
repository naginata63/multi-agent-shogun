# subtask_1433a 手順: Gemini部分再解析機能実装

## 概要
panel_review.html に「🔄 Gemini再解析」ボタンを追加し、殿が編集した行の周辺だけ Gemini Vision で再解析する仕組みを実装。

## 対象ファイル
1. `projects/dozle_kirinuki/scripts/panel_review_gen.py` (Phase A)
2. `scripts/dashboard/server.py` (Phase B)
3. `projects/dozle_kirinuki/scripts/generate_panel_candidates.py` (Phase C/D)

## Step 1: advisor() 実装前確認
必須。実装方針を固める前に呼ぶこと。

## Step 2: 現状把握 (Read)
- panel_review_gen.py: L750-820 付近 (generatePanelCandidates関数、saveEdited関数)
- server.py: L1020-1060 付近 (_jobs dict、/api/job_status ハンドラ)
- server.py: L1430-1470 付近 (既存 suggest_director_notes エンドポイント)
- generate_panel_candidates.py: argparse部分 (冒頭〜L100)、Geminiプロンプト生成部分

## Step 3: Phase A - panel_review_gen.py UIボタン追加
L329付近「パネル候補生成」ボタンの右に「🔄 Gemini再解析」ボタン追加。

JS関数 `reanalyzeWithGemini()` を追加:
1. `rows` と `loadedRows` (saveEdited後の状態) を比較して編集行を抽出
   - `loadedRows` がない場合はアラート「先に💾保存してください」
2. 編集行が0件ならアラート「編集行がありません」
3. 各編集行の timestamp ±60秒で time_range を計算（重複はマージ）
4. POST `/api/regenerate_partial_with_gemini`:
   ```json
   {
     "panels_path": "<savePath>",
     "clip_path": "<clipPath>",
     "target_ranges": [[start1, end1], [start2, end2]],
     "edited_rows": [{"timestamp": 13.5, "speaker": "bon", "text": "何してんだよ！！"}, ...]
   }
   ```
5. job_id 受信 → 3秒間隔で `/api/job_status?id={job_id}` ポーリング
6. ボタンはdisabled+spinner表示（完了/失敗まで）
7. 完了: 結果ファイル名表示

`loadedRows` 変数: saveEdited完了時に `loadedRows = JSON.parse(JSON.stringify(rows))` でスナップショット保存。

## Step 4: Phase B - server.py 新エンドポイント
`/api/regenerate_partial_with_gemini` POST ハンドラ追加:

```python
elif self.path == '/api/regenerate_partial_with_gemini':
    # リクエスト読み込み
    body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
    panels_path = body['panels_path']
    clip_path = body['clip_path']
    target_ranges = body['target_ranges']  # [[12,72], [120,180]]
    edited_rows = body['edited_rows']
    
    # edited_rows を一時ファイルに保存
    import tempfile, uuid
    job_id = str(uuid.uuid4())
    tmp_edited = f'/tmp/edited_rows_{job_id}.json'
    with open(tmp_edited, 'w') as f:
        json.dump(edited_rows, f, ensure_ascii=False)
    
    # ranges文字列: "12-72,120-180"
    ranges_str = ','.join(f'{int(s)}-{int(e)}' for s, e in target_ranges)
    
    # 出力パス: panels_xxx_partial_v2.json
    output_path = panels_path.replace('.json', '_partial_v2.json')
    
    # 非同期実行
    _jobs[job_id] = {'status': 'running', 'output': None, 'error': None}
    
    def run_job():
        try:
            result = subprocess.Popen(
                ['python3', GENERATE_PANELS_SCRIPT,
                 '--clip', clip_path,
                 '--partial-ranges', ranges_str,
                 '--edited-rows-json', tmp_edited,
                 '--respect-edits',
                 '--output', output_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = result.communicate()
            if result.returncode == 0:
                _jobs[job_id] = {'status': 'done', 'output': output_path, 'error': None}
            else:
                _jobs[job_id] = {'status': 'error', 'output': None, 'error': stderr.decode()[:500]}
        except Exception as e:
            _jobs[job_id] = {'status': 'error', 'output': None, 'error': str(e)}
    
    import threading
    threading.Thread(target=run_job, daemon=True).start()
    
    resp = json.dumps({'job_id': job_id}).encode()
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.send_header('Content-Length', str(len(resp)))
    self.end_headers()
    self.wfile.write(resp)
```

`GENERATE_PANELS_SCRIPT` = `os.path.join(BASE_DIR, 'projects/dozle_kirinuki/scripts/generate_panel_candidates.py')`

## Step 5: Phase C - generate_panel_candidates.py 新引数追加
argparse に以下を追加:
```python
parser.add_argument('--partial-ranges', type=str, default=None,
                    help='部分再解析範囲 "12-72,120-180" (秒)')
parser.add_argument('--edited-rows-json', type=str, default=None,
                    help='殿レビュー済み行データJSON (話者+セリフ尊重)')
parser.add_argument('--respect-edits', action='store_true',
                    help='edited-rows を絶対尊重モード')
```

Gemini プロンプトに注入（`--edited-rows-json` が指定された場合）:
```
# 【最重要】殿レビュー済み行データ（絶対尊重）

以下の行は殿（人間レビュアー）が話者とセリフを確認・修正したものです。
**絶対に話者を書き換えないでください。新規話者推測も禁止。**

{edited_rows_text}

タイムスタンプは目安です（誤差60秒程度）。
動画を見て、上記セリフを言っている場面を特定し、
その前後でpanelsを再生成してください。
```

## Step 6: Phase D - 部分マージロジック
generate_panel_candidates.py に `merge_partial_panels()` ヘルパー追加:
- ベース: 既存 panels_xxx.json をロード
- 新規生成 panels（指定範囲のみ）を取得
- マージ: 新規 panels の start_sec が target_ranges と重なるものは置換
- 残りは既存維持
- 出力: `--output` 指定パス (panels_xxx_partial_v2.json)

## Step 7: テスト（コストかかるため最小限）
- `python3 generate_panel_candidates.py --help` で新引数が表示されることを確認
- argparse: `--partial-ranges "0-60" --edited-rows-json /dev/null --respect-edits` でparse確認
- server.py の新エンドポイント: `curl -X POST http://127.0.0.1:8770/api/regenerate_partial_with_gemini -d '{...}'` → job_id返却確認（サーバー再起動済みが前提。未再起動なら旧コードサーバーで確認不可）
- **実際のGemini呼出テストは不要**（API課金発生のため）

## Step 8: advisor() 完了前確認

## Step 9: git commit & push

## Step 10: 完了報告
```bash
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo '足軽1号、subtask_1433a完了。Gemini再解析ボタン実装済み。' report_completed ashigaru1
bash /home/murakami/multi-agent-shogun/scripts/ntfy.sh '✅ cmd_1433完了: Gemini部分再解析 + 殿レビュー尊重プロンプト追加'
```

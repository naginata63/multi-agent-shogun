# DingTalk QC 複数ログ集約手順 (cmd_1364)

## 対象ファイル
`scripts/dashboard/server.py`（既存ファイルへの修正のみ）

## 現状
- `_get_dingtalk_qc_stats()` が `work/dingtalk_qc/qc_log.jsonl` のみ読んでいる（L561付近）
- `work/dingtalk_qc/qc_log_9222.jsonl`・`qc_log_9223.jsonl` が無視されている

## 修正手順

1. `scripts/dashboard/server.py` を読み、`_get_dingtalk_qc_stats()` 関数を特定する
2. 関数を以下の方針で修正：
   - `glob.glob("work/dingtalk_qc/qc_log*.jsonl")` で全ファイル取得
   - 各ファイルを走査して confirmed/skipped/error/total を合算
   - `sources` キーにファイル別件数を追加（例: `{"qc_log.jsonl": 7547, "qc_log_9222.jsonl": 390, ...}`）
3. フロントHTMLのdingtalk-panel部分（L789付近）に `sources` 内訳表示を追加
   - 例: `<div class="sources">内訳: main=7547, 9222=390, 9223=339</div>`

## テスト

```bash
curl http://192.168.2.7:8770/api/dashboard | python3 -m json.tool | grep -A20 "dingtalk_qc"
```
- `total` が全ファイル合算値であること
- `sources` に各ファイルの件数が含まれること

## 完了処理

```bash
git add scripts/dashboard/server.py
git commit -m "feat(cmd_1364): DingTalk QC複数ログ集約対応（qc_log*.jsonl全ファイル合算）"
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽1号、subtask_1364a完了。total合算値とsources内訳を報告。" report_completed ashigaru1
```

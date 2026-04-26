# localhost:8080 AIコメント復旧手順 (cmd_1365)

## 対象
`projects/dozle_kirinuki/analytics/dashboard/` 配下

## 現状
- `analysis_history.json` に 4/13 エントリあり
- `data.json` の `analysis_history` も 22件（最新4/13）
- `video_analysis` の最終更新は 3/23（約3週間前）
- フロント: `index.html` の `renderAnalysis()` (L550-567)

## 調査・修正手順

1. `projects/dozle_kirinuki/analytics/dashboard/index.html` を読み、`renderAnalysis()` のロジック確認
2. `projects/dozle_kirinuki/analytics/dashboard/data.json` の `analysis_history` 構造を確認
3. index.html が期待するキー名と data.json のキー名が一致するか照合
4. 不一致があれば index.html の参照キーを修正（またはdata.json再生成）
5. `scripts/generate_dashboard.py` の存在を確認し、データ再生成が必要なら実行

## テスト

```bash
curl http://localhost:8080/ | grep -c "AI分析"
curl http://localhost:8080/data.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('analysis_history',[])))"
```

## 完了処理

```bash
git add projects/dozle_kirinuki/analytics/dashboard/
git commit -m "fix(cmd_1365): localhost:8080 AIコメント表示復旧"
bash /home/murakami/multi-agent-shogun/scripts/inbox_write.sh karo "足軽2号、subtask_1365a完了。原因と修正内容を報告。" report_completed ashigaru2
```
